#!/usr/bin/env python3
"""Run C joint currents on the 3S P45B wire rail, then the knee-heat and breaker clocks.

Reads these files from the open branches. It does not copy them into this branch:
  origin/cursor/system-voltage-f426  altaay_lab/problems/system_voltage.py
  origin/cursor/knee-heat-chafe-2401 altaay_lab/problems/knee_heat_chafe.py

The walk is the em_twin sheet walk (problems/sts12.py 12 V patch, run C policy).
The winner rail is PR 85: 3S Molicel P45B, ST-3215-C018, pack wired to the servos,
Castle body off the trunk. CPU only. No retrain. Nothing is bought. D61 is not edited.

  ODM_PLAYGROUND=<Open_Duck_Playground at b9be205> python3 altaay_lab/problems/runc_joint_current.py all

Outputs (repo paths):
  altaay_lab/problems/runc_joint_current.json
  altaay_lab/problems/RUNC_JOINT_CURRENT.md
"""
import json
import os
import subprocess
import sys
import textwrap
import time
import types

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(LAB, ".."))
SCRATCH = os.environ.get("RUNC_SCRATCH", os.path.join(__import__("tempfile").gettempdir(), "runc_joint"))
SV_REF = "origin/cursor/system-voltage-f426"
KH_REF = "origin/cursor/knee-heat-chafe-2401"
SV_PATH = "altaay_lab/problems/system_voltage.py"
KH_PATH = "altaay_lab/problems/knee_heat_chafe.py"
T_STATS = 4.0
ILIM_A = (7.23, 7.77, 8.13, 8.54, 9.07)
# Same blanking corners as knee_heat_chafe.eFuse_check: 600 nF, dV 0.7 to 1.3 V, I 2.8 to 1.4 uA.
BLANK_SHORT_S = 600.0 * 0.7 / 2.8 / 1000.0
BLANK_LONG_S = 600.0 * 1.3 / 1.4 / 1000.0
FAST_TRIP = 2.10


def r6(x):
    if x is None:
        return None
    return round(float(x), 6)


def r3(x):
    if x is None:
        return None
    return round(float(x), 3)


def git_show(ref, path):
    return subprocess.check_output(["git", "show", "%s:%s" % (ref, path)], cwd=REPO, text=True)


def git_sha(ref):
    return subprocess.check_output(["git", "rev-parse", ref], cwd=REPO, text=True).strip()


def load_branch_module(ref, relpath, name):
    src = git_show(ref, relpath)
    mod = types.ModuleType(name)
    mod.__file__ = os.path.join(REPO, relpath)
    mod.__dict__["__file__"] = mod.__file__
    sys.modules[name] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def extract_sv_setup(mod, src):
    """The seat, piece, and rail tables inside system_voltage.sim_main."""
    lines = src.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith("def sim_main"))
    body = []
    for ln in lines[start + 1:]:
        if ln.startswith("def ") or ln.startswith("if __name__"):
            break
        body.append(ln)
    text = textwrap.dedent("\n".join(body))
    a = text.index("c1 = np.array")
    b = text.index("base = ET.model_folder")
    ns = dict(mod.__dict__)
    exec(text[a:b], ns)
    return ns["pieces"], ns["extra"], ns["cells"]


def install_mass_patches():
    """Same two process-local patches as system_voltage.sim_main.

    JPI is a signal pad with a null cut, so its wire mass is 0. The gauge line
    is the bead-lead case that file already treats as 0 g. Repo files stay as they are.
    """
    import inspect
    import json as _json
    import yaml
    import mass_budget as MB

    src = inspect.getsource(MB.wires)
    old = 'raise RuntimeError("gauge " + g)'
    new = 'mass = 0.0; srcs = "[L] board or bead lead, 0 g in this walk model"'
    if old not in src:
        raise RuntimeError("mass_budget.wires gauge line moved; the PR 85 patch no longer applies")
    exec(compile(src.replace(old, new), MB.__file__, "exec"), MB.__dict__)
    _load = _json.load

    def _load_seat(fh, *a, **k):
        data = _load(fh, *a, **k)
        if isinstance(data, dict) and "cable_ends" in data and not getattr(_load_seat, "done", False):
            _load_seat.done = True
            nl = yaml.safe_load(open(os.path.join(LAB, "wiring", "netlist.yaml"), encoding="utf-8"))
            have = {e["id"].split(".")[0] for e in data["cable_ends"]}
            need = set()
            for w in nl["wires"]:
                need.add(w["from"].split(".")[0])
                need.add(w["to"].split(".")[0])
            missing = sorted(need - have)
            for cid in missing:
                data["cable_ends"].append(dict(id=cid + ".1", link="trunk_assembly", p_world0=[0.0, 0.0, 0.0]))
            _load_seat.missing = missing
        return data

    _json.load = _load_seat
    return _load_seat


def patch_trunk(path, pieces, sv):
    """PR 85 `_patch_trunk` updates an in-memory tree and returns the new mass.

    It does not write the file. MuJoCo then loads the unpatched inertial, which is why
    the Castle-on and Castle-off walks printed the same speed. This write is the same
    shift (`system_voltage._shift`) followed by a save.
    """
    import xml.etree.ElementTree as ETXML
    tree = ETXML.parse(path)
    for body in tree.getroot().iter("body"):
        if body.get("name") != "trunk_assembly":
            continue
        inert = body.find("inertial")
        m = float(inert.get("mass"))
        c = np.array([float(x) for x in inert.get("pos").split()])
        f = [float(x) for x in inert.get("fullinertia").split()]
        I = np.array([[f[0], f[3], f[4]], [f[3], f[1], f[5]], [f[4], f[5], f[2]]])
        m2, c2, I2 = sv._shift(I, m, c, pieces)
        inert.set("mass", f"{m2:.9g}")
        inert.set("pos", " ".join(f"{x:.9g}" for x in c2))
        inert.set("fullinertia", " ".join(
            f"{x:.9g}" for x in (I2[0, 0], I2[1, 1], I2[2, 2], I2[0, 1], I2[0, 2], I2[1, 2])
        ))
        tree.write(path)
        return dict(
            mass_before_kg=round(m, 4), mass_after_kg=round(m2, 4),
            com_before_m=[round(float(x), 5) for x in c],
            com_after_m=[round(float(x), 5) for x in c2],
        )
    raise RuntimeError("trunk missing")


def trunk_xml(path):
    import xml.etree.ElementTree as ETXML
    tree = ETXML.parse(path)
    for body in tree.getroot().iter("body"):
        if body.get("name") != "trunk_assembly":
            continue
        inert = body.find("inertial")
        return dict(mass_kg=float(inert.get("mass")), pos_m=[float(x) for x in inert.get("pos").split()])
    raise RuntimeError("trunk missing")


def mujoco_trunk(et, folder):
    et.AM._ASSET_DIR[0] = folder
    scene = os.path.join(folder, "scene_flat_terrain_backlash.xml")
    m = et.MI.MjInfer(scene, et.CB.REF, et.CB.ONNX, standing=False)
    bid = m.model.body("trunk_assembly").id
    return dict(
        trunk_mass_kg=float(m.model.body_mass[bid]),
        subtree_mass_kg=float(m.model.body_subtreemass[bid]),
        nbody=int(m.model.nbody),
    )


def limb_index(names):
    return {
        "left_leg": [i for i, n in enumerate(names) if str(n).startswith("left_")],
        "right_leg": [i for i, n in enumerate(names) if str(n).startswith("right_")],
        "neck_and_head": [i for i, n in enumerate(names) if str(n).startswith("neck_") or str(n).startswith("head_")],
    }


def excursion_stats(series, dt, thresholds):
    out = {}
    for thr in thresholds:
        above = series > thr
        d = np.diff(np.concatenate([[0], above.astype(np.int8), [0]]))
        starts = np.where(d == 1)[0]
        ends = np.where(d == -1)[0]
        lengths = (ends - starts) * dt
        longest = float(lengths.max()) if len(lengths) else 0.0
        buckets = {"under_50ms": 0, "50_to_150ms": 0, "150ms_to_long_blanking": 0, "over_long_blanking": 0}
        for L in lengths:
            if L < 0.050:
                buckets["under_50ms"] += 1
            elif L < BLANK_SHORT_S:
                buckets["50_to_150ms"] += 1
            elif L < BLANK_LONG_S:
                buckets["150ms_to_long_blanking"] += 1
            else:
                buckets["over_long_blanking"] += 1
        out[str(thr)] = dict(
            time_above_s=r6(float(above.sum()) * dt),
            longest_s=r6(longest),
            n_excursions=int(len(lengths)),
            buckets=buckets,
            trips_short_blanking=bool(longest + 1e-9 >= BLANK_SHORT_S),
            trips_long_blanking=bool(longest + 1e-9 >= BLANK_LONG_S),
        )
    return out


def reduce_run(r):
    dt = float(r["dt"])
    n = len(r["_full"]["Im"])
    k0 = min(n, int(round(T_STATS / dt)))
    im = np.asarray(r["_full"]["Im"][k0:n], float)
    isup = np.asarray(r["_full"]["Isup"][k0:n], float)
    ip = np.asarray(r["_fullp"]["i_pack"][k0:n], float)
    names = [str(x) for x in r["names"]]
    if len(im) == 0:
        raise RuntimeError("walk ended before the 4 s stats window")
    im_rms = np.sqrt(np.mean(im * im, axis=0))
    im_peak = np.max(np.abs(im), axis=0)
    is_rms = np.sqrt(np.mean(isup * isup, axis=0))
    is_peak = np.max(isup, axis=0)
    hot = int(np.argmax(im_rms))
    joints = []
    for i, name in enumerate(names):
        joints.append(dict(
            joint=name,
            motor_rms_A=r6(im_rms[i]),
            motor_peak_A=r6(im_peak[i]),
            supply_rms_A=r6(is_rms[i]),
            supply_peak_A=r6(is_peak[i]),
        ))
    groups = limb_index(names)
    branches = {}
    for g, idx in groups.items():
        series = isup[:, idx].sum(axis=1)
        w = max(1, int(round(0.100 / dt)))
        c100 = np.convolve(series, np.ones(w) / w, mode="valid") if len(series) >= w else series
        peak = float(series.max())
        branches[g] = dict(
            label="sim pass only",
            mean_A=r6(series.mean()),
            rms_A=r6(np.sqrt(np.mean(series * series))),
            peak_A=r6(peak),
            max_100ms_A=r6(float(np.max(c100))),
            fast_trip_A=r6(FAST_TRIP * ILIM_A[-1]),
            above=excursion_stats(series, dt, ILIM_A),
            samples=int(len(series)),
            dt_s=dt,
        )
    # First minute of the stats window, and the last minute, for the long duty.
    def seg_rms(t_a, t_b):
        i0 = int(round(max(0.0, t_a - T_STATS) / dt))
        i1 = int(round(max(0.0, t_b - T_STATS) / dt))
        i1 = min(len(im), max(i0 + 1, i1))
        return r6(np.sqrt(np.mean(im[i0:i1, hot] ** 2))), r6(float(ip[i0:i1].mean()))

    dur = float(r["dur_s"])
    first = seg_rms(T_STATS, T_STATS + 60.0)
    last = seg_rms(max(T_STATS, dur - 60.0), dur) if dur > 70 else first
    g = r["gait"]
    log = np.asarray(r["_log"], float)
    pose = []
    if len(log):
        for t_want in (5.0, 10.0, 20.0, 40.0, 60.0):
            if t_want > float(log[-1, 0]) + 0.05:
                continue
            i = int(np.argmin(np.abs(log[:, 0] - t_want)))
            pose.append(dict(t_s=r3(log[i, 0]), x_m=r6(log[i, 1]), y_m=r6(log[i, 2]), z_m=r6(log[i, 3])))
    bins = r["_bins"]
    binsp = r["_binsp"]
    return dict(
        label="sim pass only",
        cmd_m_s=float(r["cmd"][0]),
        corner=r["corner"],
        dur_s=r["dur_s"],
        fall_s=r["falls"] or "none",
        wall_s=r["wall_s"],
        vx_m_s=None if g.get("vx") is None else float(g["vx"]),
        track_lin=None if g.get("track_lin") is None else float(g["track_lin"]),
        pack_em_twin=r.get("pack"),
        pack_window=dict(
            t0_s=T_STATS,
            i_mean_A=r6(float(ip.mean())),
            i_rms_A=r6(float(np.sqrt(np.mean(ip * ip)))),
            i_max_A=r6(float(ip.max())),
            n=int(len(ip)),
        ),
        hottest_joint=names[hot],
        hottest_motor_rms_A=r6(im_rms[hot]),
        hottest_motor_peak_A=r6(im_peak[hot]),
        joints=joints,
        branches=branches,
        first_minute_hot_motor_rms_A=first[0],
        first_minute_pack_mean_A=first[1],
        last_minute_hot_motor_rms_A=last[0],
        last_minute_pack_mean_A=last[1],
        pose=pose,
        servo_im_rms_check=[r6(x) for x in r["servo"]["Im_rms"]],
        bin_pack=dict(
            t_end=np.asarray(binsp["t_end"], float),
            im=np.asarray(bins["Im_rms"], float),
            isup=np.asarray(bins["Isup_mean"], float),
            i_pack=np.asarray(binsp["i_pack_mean"], float),
            i_pack_rms=np.asarray(binsp["i_pack_rms"], float),
            i_bec=np.asarray(binsp["i_bec_out_mean"], float),
            i_bec_rms=np.asarray(binsp["i_bec_out_rms"], float),
            v_bec=np.asarray(binsp["v_bec_out_mean"], float),
            v_bus=np.asarray(binsp["v_bus_mean"], float),
        ),
    )


def worker(spec):
    os.environ["ODM_PLAYGROUND"] = spec["playground"]
    os.environ["ODM_ONNX"] = spec["onnx"]
    os.environ["TWIN_EM_SCRATCH"] = spec["scratch"]
    os.environ.setdefault("ODM_SCRATCH", os.path.join(spec["scratch"], "models"))
    for v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ.setdefault(v, "1")
    sys.path.insert(0, os.path.join(LAB, "problems"))
    sys.path.insert(0, os.path.join(LAB, "twin", "electromech"))
    sys.path.insert(0, os.path.join(LAB, "sim"))
    import sts12  # noqa: F401  12 V sheet patch and the 3S pack
    import em_twin as ET

    folder = spec["folder"]
    ET.model_folder = lambda mass, dst=folder: dst
    t0 = time.time()
    r = ET.run(
        mass="ours",
        walk="backlash",
        cmd=(spec["cmd"], 0.0, 0.0),
        dur=spec["dur"],
        supply="net",
        corner=spec["corner"],
        extra=spec["extra"],
        cell="p45b3",
        q0=0.0,
        servo_mode="sheet",
        guard=None,
        keep_full=True,
        stop_on_fall=True,
        t_stats=T_STATS,
        label=spec["tag"],
        progress=0.0,
    )
    reduced = reduce_run(r)
    reduced["tag"] = spec["tag"]
    reduced["model"] = spec["model"]
    reduced["wall_total_s"] = round(time.time() - t0, 1)
    bins = reduced.pop("bin_pack")
    os.makedirs(spec["scratch"], exist_ok=True)
    np.savez_compressed(os.path.join(spec["scratch"], spec["tag"] + "_bins.npz"), **bins)
    # Pose path for the mass comparison. Not copied into the repo JSON.
    log = np.asarray(r["_log"], float)
    if len(log):
        np.savez_compressed(
            os.path.join(spec["scratch"], spec["tag"] + "_xy.npz"),
            t=log[:, 0], x=log[:, 1], y=log[:, 2],
        )
    path = os.path.join(spec["scratch"], spec["tag"] + ".json")
    json.dump(reduced, open(path, "w"), indent=1)
    print(
        spec["tag"],
        "fall", reduced["fall_s"],
        "vx", None if reduced["vx_m_s"] is None else round(reduced["vx_m_s"], 6),
        "hot", reduced["hottest_joint"], reduced["hottest_motor_rms_A"],
        "pack_max", reduced["pack_window"]["i_max_A"],
        "wall", reduced["wall_total_s"],
        flush=True,
    )
    return path


def prepare():
    if not os.environ.get("ODM_PLAYGROUND"):
        raise SystemExit("Set ODM_PLAYGROUND to an Open_Duck_Playground checkout at b9be205")
    os.environ.setdefault("ODM_ONNX", os.path.join(HERE, "retrain_sts12", "sts12_runC_policy.onnx"))
    os.environ.setdefault("TWIN_EM_SCRATCH", os.path.join(SCRATCH, "twin"))
    os.environ.setdefault("ODM_SCRATCH", os.path.join(SCRATCH, "twin", "models"))
    os.makedirs(SCRATCH, exist_ok=True)
    for v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ.setdefault(v, "1")
    sys.path.insert(0, os.path.join(LAB, "problems"))
    sys.path.insert(0, os.path.join(LAB, "twin", "electromech"))
    sys.path.insert(0, os.path.join(LAB, "sim"))
    sv_src = git_show(SV_REF, SV_PATH)
    sv = load_branch_module(SV_REF, SV_PATH, "system_voltage_pr85")
    pieces, extra, _cells = extract_sv_setup(sv, sv_src)
    hook = install_mass_patches()
    import sts12  # noqa: F401
    import em_twin as ET
    import shutil
    base = ET.model_folder("ours")
    base_xml = trunk_xml(os.path.join(base, "open_duck_mini_v2_backlash.xml"))
    print("baseline trunk", base_xml, "unseated", getattr(hook, "missing", None), flush=True)
    # 200 g sits at the pre-cell trunk COM so the check is a mass change, not a new part seat.
    com0 = np.array(base_xml["pos_m"])
    builds = {
        "wire": pieces["E_3S_C018_wire"],
        "castle_kept": pieces["F_3S_C018_buck12"],
        "plus_200g": list(pieces["E_3S_C018_wire"]) + [(0.200, com0)],
    }
    folders = {}
    seen = {}
    for key, pcs in builds.items():
        dst = os.path.join(ET.AM.SCR, "models", "runc_" + key)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(base, dst)
        moved = None
        for name in ("open_duck_mini_v2.xml", "open_duck_mini_v2_backlash.xml"):
            moved = patch_trunk(os.path.join(dst, name), pcs, sv)
        mj = mujoco_trunk(ET, dst)
        folders[key] = dst
        seen[key] = dict(xml=moved, mujoco=mj, xml_file=trunk_xml(os.path.join(dst, "open_duck_mini_v2_backlash.xml")))
        print(key, "xml", moved["mass_after_kg"], "mujoco", round(mj["trunk_mass_kg"], 6), flush=True)
    wire_extra = extra["E_3S_C018_wire"]
    patch_fn = sv_src.split("def _patch_trunk", 1)[1].split("\ndef ", 1)[0]
    meta = dict(
        pr85_patch_writes_file=("tree.write" in patch_fn) or (".write(" in patch_fn),
        baseline_trunk=base_xml,
        models=seen,
        extra=wire_extra,
        folders=folders,
        bec_removed_g=sv.BEC_REMOVED_G,
        sv_sha=git_sha(SV_REF),
        unseated=getattr(hook, "missing", None),
    )
    json.dump(meta, open(os.path.join(SCRATCH, "prepare.json"), "w"), indent=1, default=float)
    return meta


def job_list(meta, which):
    extra = meta["extra"]
    folders = meta["folders"]
    common = dict(playground=os.environ["ODM_PLAYGROUND"], onnx=os.environ["ODM_ONNX"], scratch=SCRATCH, extra=extra)
    jobs = []

    def add(model, cmd, corner, dur, tag):
        jobs.append(dict(common, model=model, folder=folders[model], cmd=cmd, corner=corner, dur=dur, tag=tag))

    if which in ("smoke",):
        add("wire", 0.15, "typical", 5.0, "smoke_wire_0.15_typical")
        return jobs
    if which in ("walks", "all", "mass"):
        for cmd in (0.15, 0.25, 0.40):
            for corner in ("typical", "high-side"):
                add("wire", cmd, corner, 60.0, "wire_%g_%s_60s" % (cmd, corner))
        add("castle_kept", 0.15, "typical", 60.0, "castle_kept_0.15_typical_60s")
        add("plus_200g", 0.15, "typical", 20.0, "plus200g_0.15_typical_20s")
    if which in ("long", "all"):
        for corner in ("typical", "high-side"):
            add("wire", 0.15, corner, 600.0, "wire_0.15_%s_600s" % corner)
        add("wire", 0.40, "typical", 600.0, "wire_0.4_typical_600s")
    if which == "mass":
        jobs = [j for j in jobs if j["model"] != "wire" or (j["cmd"] == 0.15 and j["corner"] == "typical" and j["dur"] == 60.0)]
    return jobs


def run_jobs(jobs):
    import multiprocessing as mp
    if os.environ.get("RUNC_SERIAL") == "1" or len(jobs) == 1:
        return [worker(j) for j in jobs]
    n = int(os.environ.get("RUNC_JOBS", "3"))
    ctx = mp.get_context("spawn")
    with ctx.Pool(min(n, len(jobs))) as pool:
        return pool.map(worker, jobs)


def load_reduced(tag):
    return json.load(open(os.path.join(SCRATCH, tag + ".json")))


def path_delta(tag_a, tag_b):
    a = np.load(os.path.join(SCRATCH, tag_a + "_xy.npz"))
    b = np.load(os.path.join(SCRATCH, tag_b + "_xy.npz"))
    n = min(len(a["t"]), len(b["t"]))
    d = np.hypot(a["x"][:n] - b["x"][:n], a["y"][:n] - b["y"][:n])
    def at(t):
        i = int(np.argmin(np.abs(a["t"][:n] - t)))
        return dict(t_s=r3(a["t"][i]), dx_m=r6(a["x"][i] - b["x"][i]), dy_m=r6(a["y"][i] - b["y"][i]), dist_m=r6(d[i]))
    return dict(max_dist_m=r6(float(d.max())), at_10s=at(10.0), at_20s=at(20.0) if a["t"][n - 1] >= 19 else None,
                n=int(n))


def mass_report(meta):
    off = load_reduced("wire_0.15_typical_60s")
    on = load_reduced("castle_kept_0.15_typical_60s")
    heavy = load_reduced("plus200g_0.15_typical_20s")
    d_on = path_delta("wire_0.15_typical_60s", "castle_kept_0.15_typical_60s")
    d_heavy = path_delta("wire_0.15_typical_60s", "plus200g_0.15_typical_20s")
    mj_off = meta["models"]["wire"]["mujoco"]["trunk_mass_kg"]
    mj_on = meta["models"]["castle_kept"]["mujoco"]["trunk_mass_kg"]
    xml_off = meta["models"]["wire"]["xml"]["mass_after_kg"]
    xml_on = meta["models"]["castle_kept"]["xml"]["mass_after_kg"]
    reached = abs(mj_off - xml_off) < 1e-4 and abs(mj_on - xml_on) < 1e-4
    dvx = abs(off["vx_m_s"] - on["vx_m_s"])
    di = abs(off["pack_window"]["i_mean_A"] - on["pack_window"]["i_mean_A"])
    dimax = abs(off["pack_window"]["i_max_A"] - on["pack_window"]["i_max_A"])
    same_path = d_on["max_dist_m"] < 1e-6
    heavy_same = d_heavy["max_dist_m"] < 1e-6
    if not reached:
        verdict = "BLOCKER. The patched trunk mass and the MuJoCo body mass disagree, so the walk did not carry the edit."
    elif same_path:
        verdict = (
            "The MuJoCo trunk mass differs by the Castle removal, and the 60 s pose still matches. "
            "The mass edit is in the model file and in the loaded body, and it does not move this walk."
        )
    elif dvx < 5e-5 and di < 5e-4 and dimax < 5e-4:
        verdict = (
            "The Castle mass reached MuJoCo. Speed and mean current stay inside the four printed digits. "
            "The pose does move, below that printed step."
        )
    else:
        verdict = (
            "The Castle mass reached MuJoCo, and this rerun moves speed or current at the printed digits. "
            "The earlier match does not repeat."
        )
    if heavy_same and reached:
        verdict += " A further 200 g at the original trunk COM also leaves the 20 s pose unchanged."
    elif reached and not heavy_same:
        verdict += " A further 200 g at the original trunk COM does move the 20 s pose, so the walker is reading trunk mass."
    return dict(
        label="sim pass only",
        pr85_patch_writes_file=bool(meta.get("pr85_patch_writes_file")),
        verdict=verdict,
        castle_removed_g=r3(meta["bec_removed_g"]),
        xml_wire_kg=xml_off,
        xml_castle_kept_kg=xml_on,
        mujoco_wire_kg=r6(mj_off),
        mujoco_castle_kept_kg=r6(mj_on),
        mujoco_minus_xml_wire_kg=r6(mj_off - xml_off),
        mujoco_minus_xml_castle_kg=r6(mj_on - xml_on),
        mass_reached_mujoco=reached,
        vx_wire=r6(off["vx_m_s"]),
        vx_castle_kept=r6(on["vx_m_s"]),
        dvx=r6(dvx),
        i_mean_wire_A=off["pack_window"]["i_mean_A"],
        i_mean_castle_kept_A=on["pack_window"]["i_mean_A"],
        di_mean_A=r6(di),
        i_max_wire_A=off["pack_window"]["i_max_A"],
        i_max_castle_kept_A=on["pack_window"]["i_max_A"],
        di_max_A=r6(dimax),
        pose_vs_castle_kept=d_on,
        pose_vs_plus200g=d_heavy,
        plus200g_mujoco_kg=r6(meta["models"]["plus_200g"]["mujoco"]["trunk_mass_kg"]),
        plus200g_vx=r6(heavy["vx_m_s"]),
        plus200g_i_mean_A=heavy["pack_window"]["i_mean_A"],
        plus200g_i_max_A=heavy["pack_window"]["i_max_A"],
        baseline_trunk_kg=r6(meta["baseline_trunk"]["mass_kg"]),
        baseline_com_m=[r6(x) for x in meta["baseline_trunk"]["pos_m"]],
        published_pr85_vx=0.1183,
        published_pr85_i_max_A=8.114,
        wire_vs_published_dvx=r6(abs(off["vx_m_s"] - 0.1183)),
        wire_vs_published_di_max=r6(abs(off["pack_window"]["i_max_A"] - 8.114)),
    )


def load_bins(tag):
    d = np.load(os.path.join(SCRATCH, tag + "_bins.npz"))
    t = np.asarray(d["t_end"], float)
    return dict(
        t=t,
        im=np.asarray(d["im"], float),
        isup=np.asarray(d["isup"], float),
        i_pack=np.asarray(d["i_pack"], float),
        i_pack_rms=np.asarray(d["i_pack_rms"], float),
        i_bec=np.asarray(d["i_bec"], float),
        i_bec_rms=np.asarray(d["i_bec_rms"], float),
        v_bec=np.asarray(d["v_bec"], float),
        v_bus=np.asarray(d["v_bus"], float),
    )


def steady_bins(s, fall):
    t = s["t"]
    use = (t >= T_STATS) & (t <= (1e9 if fall == "none" else float(fall) + 0.05))
    if not np.any(use):
        use = np.ones(len(t), bool)
    return {k: (v[use] if hasattr(v, "__len__") else v) for k, v in s.items()}


def run_thermal():
    kh = load_branch_module(KH_REF, KH_PATH, "knee_heat_chafe_pr86")
    import twin_thermal as TT
    names = list(TT.NAMES)
    assert limb_index(names) == kh.groups_of(names)
    # Prefer the 10 min log when it exists. The 60 s log is the short duty.
    series = []
    for tag, role in (
        ("wire_0.15_typical_600s", "0.15 m/s typical, 10 min"),
        ("wire_0.15_high-side_600s", "0.15 m/s high-side, 10 min"),
        ("wire_0.15_typical_60s", "0.15 m/s typical, 60 s"),
        ("wire_0.15_high-side_60s", "0.15 m/s high-side, 60 s"),
        ("wire_0.25_typical_60s", "0.25 m/s typical, 60 s"),
        ("wire_0.4_typical_60s", "0.40 m/s typical, 60 s"),
        ("wire_0.4_high-side_60s", "0.40 m/s high-side, 60 s"),
        ("wire_0.4_typical_600s", "0.40 m/s typical, 10 min"),
    ):
        if os.path.exists(os.path.join(SCRATCH, tag + "_bins.npz")):
            series.append((tag, role))
    rows = []
    for tag, role in series:
        doc = load_reduced(tag)
        s = steady_bins(load_bins(tag), doc["fall_s"])
        # build_12v multiplies motor current by Kt_7.4/Kt_12 because its CSV is the 7.4 V log.
        # This log is already the 12 V sheet. Divide first so the multiply lands on the logged amp.
        s_in = dict(s)
        s_in["im"] = np.asarray(s["im"], float) / kh.I_SCALE
        sts = dict(
            i_mean=float(np.nanmean(s["i_pack"])),
            i_rms=float(np.nanmean(s["i_pack_rms"])),
            bus_mean=float(np.nanmean(s["v_bus"])),
            bec_out_mean=float(np.nanmean(s["v_bec"])),
        )
        primary = tag in ("wire_0.15_typical_600s", "wire_0.15_typical_60s", "wire_0.15_high-side_600s", "wire_0.15_high-side_60s")
        # One 10 min series is the design case. Skip the 60 s twin of the same corner when the 10 min file exists.
        if tag.endswith("_60s") and os.path.exists(os.path.join(SCRATCH, tag.replace("_60s", "_600s") + "_bins.npz")):
            if tag not in ("wire_0.15_typical_60s",):
                continue
        plan = [("cont70_25", 70.0, 25.0, None, 90 * 60.0)]
        if primary:
            plan += [
                ("cont70_32", 70.0, 32.0, None, 90 * 60.0),
                ("cont200_25", 200.0, 25.0, None, 90 * 60.0),
                ("guard_25", 70.0, 25.0, dict(stop=55.0, resume=45.0, rest="off"), 90 * 60.0),
                ("guard_32", 70.0, 32.0, dict(stop=55.0, resume=45.0, rest="off"), 90 * 60.0),
            ]
        if tag == "wire_0.15_typical_600s" or (tag == "wire_0.15_typical_60s" and not os.path.exists(os.path.join(SCRATCH, "wire_0.15_typical_600s_bins.npz"))):
            plan.append(("cont70_25_drop0p3", 70.0, 25.0, None, 90 * 60.0))
        for name, t_cut, room, guard, t_end in plan:
            drop = 0.3 if name.endswith("drop0p3") else 0.0
            old = kh.V_DROP
            kh.V_DROP = drop
            try:
                heats, c, tbin, meta = kh.build_12v(s_in, sts, 1.0, t_cut, True)
            finally:
                kh.V_DROP = old
            jr = names.index("right_knee")
            logged = float(np.nan_to_num(s["im"][0, jr]))
            if abs(meta["right_knee_I_rms_first_bin_A"] - round(logged, 3)) > 0.002:
                raise RuntimeError("thermal current did not land on the log: %s vs %s" % (meta["right_knee_I_rms_first_bin_A"], logged))
            nbin = len(tbin)
            span = float(tbin[-1] - tbin[0]) if nbin > 1 else 0.1

            def sched(t, tbin=tbin, nbin=nbin, span=span, guard=guard):
                x = float(tbin[0]) + (t % span if span > 0 else 0.0)
                return int(np.clip(np.searchsorted(tbin, x), 0, nbin - 1))

            sim = TT.simulate(sched, heats, None, c, room, t_end=t_end, dt=0.5, guard=guard, record=1.0)
            row = kh.summarize(sim, heats, c, "%s_%s" % (tag, name))
            row["series"] = role
            row["tag"] = tag
            row["case"] = name
            row["room_C"] = room
            row["bec_drop_V"] = drop
            row["current_scale"] = "1. Logged 12 V sheet current. The Kt scale is inverted around build_12v so it is applied once and cancels."
            row["minutes_to_right_reading_55C"] = kh._cross(sim["t"], sim["Ts"][:, jr], 55.0)
            row["minutes_to_right_body_49C"] = kh._cross(sim["t"], sim["Tb"][:, jr], 49.0)
            row["minutes_to_right_body_62C"] = kh._cross(sim["t"], sim["Tb"][:, jr], 62.0)
            hot_j = int(np.argmax(sim["max_Ts"]))
            row["hottest_reading_joint"] = names[hot_j]
            row["hottest_reading_C"] = round(float(sim["max_Ts"][hot_j]), 2)
            row["minutes_to_hottest_reading_55C"] = kh._cross(sim["t"], sim["Ts"][:, hot_j], 55.0)
            row["minutes_to_hottest_reading_60C"] = kh._cross(sim["t"], sim["Ts"][:, hot_j], 60.0)
            n10 = min(len(sim["t"]), 600)
            row["reading_rise_last_10min_C"] = round(float(sim["Ts"][-1, jr] - sim["Ts"][-n10, jr]), 3)
            row["body_rise_last_10min_C"] = round(float(sim["Tb"][-1, jr] - sim["Tb"][-n10, jr]), 3)
            row["reading_end_C"] = round(float(sim["Ts"][-1, jr]), 2)
            row["body_end_C"] = round(float(sim["Tb"][-1, jr]), 2)
            # Drop the per-servo maps. The summary fields are the result.
            row.pop("bodies_C", None)
            row.pop("readings_C", None)
            row.pop("meta", None)
            rows.append(row)
            print(
                tag, name,
                "read", row["right_knee_reading_max_C"],
                "body", row["right_knee_body_max_C"],
                "t55", row["minutes_to_right_reading_55C"],
                "t60", row["minutes_to_right_reading_60C"],
                "walk", row["walk_share"],
                flush=True,
            )
    return dict(sha=git_sha(KH_REF), i_scale=kh.I_SCALE, rows=rows)


def fC(x):
    if x is None:
        return "does not cross in the run"
    return "%.2f min" % x


def write_md(doc):
    L = []
    A = L.append
    A("# Run C joint current")
    A("")
    A("Written 2026-11-13. CPU only. The walk is the em_twin sheet walk with the run C policy and the 12 V ST-3215-C018 patch in `problems/sts12.py`. The rail is the PR 85 winner: 3S Molicel P45B wired to the servos, Castle off the trunk. The thermal cases call `knee_heat_chafe.py` from the open knee-heat branch. This note does not copy those scripts. D61 was not edited. Nothing was bought. The policy was not retrained.")
    A("")
    A("Every walk figure is sim pass only. A temperature from the thermal twin is sim pass only. Arithmetic on those currents, and the blanking comparison, are calc only. A datasheet figure is cited. A missing measurement is BLOCKER.")
    A("")
    A("Script: `altaay_lab/problems/runc_joint_current.py`. Numbers: `altaay_lab/problems/runc_joint_current.json`.")
    A("")
    A("## What was logged")
    A("")
    A("Run C had pack current and knee volts. It did not keep a per-servo current. The knee-heat note therefore scaled an older backlash session by Kt, and it marked a run C knee amp BLOCKER. This pass keeps the motor current and the supply current that `em_twin.py` already computes on each 2 ms step.")
    A("")
    A("Commands are 0.15, 0.25, and 0.40 m/s, typical and high-side corners, 60 s, no fall in the runs below. The longer duty is the same command held for 10 min. Stats start at 4 s, the same window as the pack figures in the electromechanical twin. The logged amps are the post-step sheet law (`servo_sts3215.electrical`), which is the series the twin already reports as motor RMS and supply current.")
    A("")
    mass = doc["mass"]
    A("Baseline trunk before the third cell, from the mass budget after the same JPI seat PR 85 uses: %.4f kg (sim pass only). That matches the 1.0654 kg figure PR 85 records." % mass["baseline_trunk_kg"])
    A("")
    A("## Per-joint current")
    A("")
    A("Motor current is the sheet winding current. Supply current is what the limb wire carries, idle included. The hottest joint is the one with the highest motor RMS, because copper heat follows that square.")
    A("")
    A("| Command | Corner | Length | Hottest joint | Motor RMS A | Motor peak A | Pack mean A | Pack peak A | Speed m/s |")
    A("|---|---|---|---|---|---|---|---|---|")
    for row in doc["walks"]:
        if row["model"] != "wire":
            continue
        A("| %.2f | %s | %.0f s | %s | %.3f | %.3f | %.3f | %.3f | %.4f |" % (
            row["cmd_m_s"], row["corner"], row["dur_s"], row["hottest_joint"],
            row["hottest_motor_rms_A"], row["hottest_motor_peak_A"],
            row["pack_window"]["i_mean_A"], row["pack_window"]["i_max_A"], row["vx_m_s"]))
    A("")
    A("All of those rows are sim pass only. The 0.15 m/s typical pack peak is the check against PR 85, which printed 8.114 A and 0.1183 m/s. This run is %.3f A and %.4f m/s (sim pass only)." % (
        doc["wire_0.15_typical_60s"]["pack_window"]["i_max_A"], doc["wire_0.15_typical_60s"]["vx_m_s"]))
    A("")
    A("Normal walk, 0.15 m/s, both corners, 60 s. Amps are sim pass only.")
    A("")
    A("| Joint | Typ motor RMS | Typ motor peak | Typ supply RMS | Typ supply peak | High motor RMS | High motor peak | High supply peak |")
    A("|---|---|---|---|---|---|---|---|")
    typ = {j["joint"]: j for j in doc["wire_0.15_typical_60s"]["joints"]}
    high = {j["joint"]: j for j in doc["wire_0.15_highside_60s"]["joints"]}
    hot_name = doc["wire_0.15_typical_60s"]["hottest_joint"]
    for name in typ:
        a, b = typ[name], high[name]
        mark = name
        A("| %s | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f |" % (
            mark, a["motor_rms_A"], a["motor_peak_A"], a["supply_rms_A"], a["supply_peak_A"],
            b["motor_rms_A"], b["motor_peak_A"], b["supply_peak_A"]))
    A("")
    A("Hottest joint on the 0.15 m/s typical walk: %s, motor RMS %.3f A, motor peak %.3f A (sim pass only). At 0.40 m/s typical the hottest joint is the left knee." % (
        hot_name, typ[hot_name]["motor_rms_A"], typ[hot_name]["motor_peak_A"]))
    long = doc.get("long_note")
    if long:
        A("")
        A(long)
    A("")
    A("## Knee heat on these currents")
    A("")
    A("The thermal twin is the PR 86 model: `twin_thermal.simulate`, the C018 stall-line split that file uses (winding 3.753 ohm, an assumption, the page does not print a winding resistance), the C001 21 mA idle, friction omitted, central corner, torque cut 70 C unless a row says the cut is off. `build_12v` multiplies by Kt 7.4 V over Kt 12 V because its input was a 7.4 V log. These amps are already the 12 V sheet, so the script divides by that factor first. The product is the logged current. A check on the first bin refuses a run that does not land on the log.")
    A("")
    A("The winner has no Castle, so the 0.30 V drop in that file is set to 0 for these rows. One comparison row puts the 0.30 V drop back. The knee is outside the trunk. PR 86 already found that trunk vents do not move the knee.")
    A("")
    A("PLA and PETG do not change the sim temperature. They change the limit the case is compared with. PLA low edge 49 C is cited (SD3D, ASTM D648, the thermal note). PETG 62 C at 1.8 MPa is cited (Bambu PETG HF, the knee-heat note). The C018 page opened for this lab does not print an operating temperature. Using the C001 60 C line and the 70 C torque-off on the C018 is BLOCKER, the same open item as PR 86.")
    A("")
    A("| Series | Case | Room | Reading max | Case max | Time to reading 55 C | Time to reading 60 C | Time to case 49 C | Time to case 62 C | Case at 90 min | Walk share | Rise last 10 min |")
    A("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for row in doc["thermal"]["rows"]:
        A("| %s | %s | %.0f C | %.2f C | %.2f C | %s | %s | %s | %s | %.2f C | %.3f | %.3f C |" % (
            row["series"], row["case"], row["room_C"],
            row["right_knee_reading_max_C"], row["right_knee_body_max_C"],
            fC(row["minutes_to_right_reading_55C"]), fC(row["minutes_to_right_reading_60C"]),
            fC(row["minutes_to_right_body_49C"]), fC(row["minutes_to_right_body_62C"]),
            row["body_end_C"], row["walk_share"], row["body_rise_last_10min_C"]))
    A("")
    A("Temperatures and the walk share are sim pass only. The blank comparison with PR 86 is the guard row: that note reported a walk share of 0.388 at 25 C and 0.201 at 32 C on the Kt-scaled old log (sim pass only). The shares in the table are the same guard, 55 C stop and 45 C resume, torque off while sitting, on the run C current.")
    A("")
    A("A case near 28 C at 90 min, on a row whose reading hit 70 C or 200 C, is the cool-down after that cut unloads the servo. The case max is the peak before the cool-down. On a guard row the 70 C cut does not fire, so the 90 min case is one sample of the walk-and-rest cycle and the case max is the peak of that cycle.")
    A("")
    A(doc["heat_note"])
    A("")
    knee = typ["right_knee"]["motor_rms_A"]
    scale = doc["thermal"].get("i_scale") or 0.702
    A("Right-knee motor RMS on the 0.15 m/s typical 60 s walk is %.3f A (sim pass only). The knee-heat note's 12 V shape was a 1.447 A log times the Kt scale %.3f, which is %.2f A (calc only). This knee draws more than that shape, which is why the clock is shorter and the walk share is lower." % (knee, scale, 1.447 * scale))
    A("")
    A("## The 36 g Castle check")
    A("")
    A("PR 85 removed the Castle from the wire-rail body (%.2f g: 29.0 g cited body, 4.6 g leads, tape, and the two output splices) and printed the same speed and the same current to four digits as the wire walk that still carried that mass. The trunk field in that JSON did change, from 1.1354 kg to 1.0994 kg." % mass["castle_removed_g"])
    A("")
    A("The cause is in `system_voltage._patch_trunk`. It parses the MJCF, edits the trunk inertial on the in-memory tree, and returns the new mass. It never writes the tree back to the file (`pr85_patch_writes_file` is %s). MuJoCo loads the scene with `from_xml_string` and the asset dictionary, so it kept the unpatched trunk, 1.0654 kg, for both rows. The identical digits are the same model walked twice. This pass writes the inertial, checks that the loaded body mass matches the file, and walks again. The electrical extra stays the wire rail for both bodies. A third body adds 200 g at the original trunk COM and walks 20 s." % mass["pr85_patch_writes_file"])
    A("")
    A("| Body | XML trunk kg | MuJoCo trunk kg | Speed m/s | Pack mean A | Pack peak A |")
    A("|---|---|---|---|---|---|")
    A("| Wire, Castle off | %.4f | %.6f | %.6f | %.6f | %.6f |" % (
        mass["xml_wire_kg"], mass["mujoco_wire_kg"], mass["vx_wire"], mass["i_mean_wire_A"], mass["i_max_wire_A"]))
    A("| Wire electrical, Castle mass kept | %.4f | %.6f | %.6f | %.6f | %.6f |" % (
        mass["xml_castle_kept_kg"], mass["mujoco_castle_kept_kg"], mass["vx_castle_kept"], mass["i_mean_castle_kept_A"], mass["i_max_castle_kept_A"]))
    plus_xml = doc.get("models", {}).get("plus_200g", {}).get("xml", {}).get("mass_after_kg")
    A("| Wire plus 200 g | %s | %.6f | %.6f | %.6f | %.6f |" % (
        "" if plus_xml is None else "%.4f" % plus_xml,
        mass["plus200g_mujoco_kg"], mass["plus200g_vx"], mass["plus200g_i_mean_A"], mass["plus200g_i_max_A"]))
    A("")
    A("Pose difference, wire against Castle kept, over the shared samples: max planar distance %.6f m. At 10 s the distance is %.6f m (sim pass only)." % (
        mass["pose_vs_castle_kept"]["max_dist_m"], mass["pose_vs_castle_kept"]["at_10s"]["dist_m"]))
    A("")
    A("Pose difference, wire against the 200 g body, over the shared 20 s: max planar distance %.6f m (sim pass only)." % mass["pose_vs_plus200g"]["max_dist_m"])
    A("")
    A(mass["verdict"] + " Sim pass only.")
    A("")
    A("## Breaker, per limb")
    A("")
    A("Three TPS259827ONRGE devices, one per limb, ahead of the feed split. That is the PR 86 candidate. Left is the five left servos, right is the five right servos, neck and head are the four head servos. The current is the sum of supply currents at 2 ms. RILIM 182 ohm is cited at ILIM 7.23 A to 9.07 A over temperature (SLVSFE7, the knee-heat note). The 600 nF timer's short corner is 150 ms and the long corner is 557 ms (calc only, C times dV over I, the cited 0.7 V to 1.3 V and 2.8 uA to 1.4 uA). A limb trips on that corner when its longest stay above the threshold is at least that long. Fast trip is 210 percent of ILIM, typical, cited. At the hot maximum that is 19.05 A (calc only).")
    A("")
    A("The 100 ms moving average is recorded and is not used as a pulse width.")
    A("")
    A("| Command | Corner | Length | Branch | Peak A | Max 100 ms A | Longest above 7.23 A | Longest above 9.07 A | Time above 7.23 A |")
    A("|---|---|---|---|---|---|---|---|---|")
    for row in doc["walks"]:
        if row["model"] != "wire":
            continue
        for br, st in row["branches"].items():
            A("| %.2f | %s | %.0f s | %s | %.3f | %.3f | %.3f s | %.3f s | %.3f s |" % (
                row["cmd_m_s"], row["corner"], row["dur_s"], br, st["peak_A"], st["max_100ms_A"],
                st["above"]["7.23"]["longest_s"], st["above"]["9.07"]["longest_s"], st["above"]["7.23"]["time_above_s"]))
    A("")
    A(doc["breaker_note"])
    A("")
    A("## Sanity checks")
    A("")
    for line in doc["sanity"]:
        A("- " + line)
    A("")
    A("## Still BLOCKER")
    A("")
    A("- C018 operating temperature and torque-off current are not on the page this lab opened. The 60 C line, the 70 C cut, and the 21 mA idle are the C001 sheet.")
    A("- C018 winding resistance is not printed. The 3.753 ohm split is the PR 86 assumption.")
    A("- Creep of the knee sheets at the structure-twin stress is still open. The HDT comparison is the cited temperature, not a creep clearance.")
    A("- Whether 600 nF is under the TPS25982 startup limit on ITIMER. The knee-heat note could not extract that equation cleanly.")
    A("- Which Pi pin reads the power-good output.")
    A("- A 1 ohm nick on the pack lead ahead of the three limb devices still sits under the 15 A fuse. This pass does not re-score that path.")
    A("")
    text = "\n".join(L) + "\n"
    if "\u2014" in text or "\u2013" in text:
        raise RuntimeError("em dash in the note")
    path = os.path.join(HERE, "RUNC_JOINT_CURRENT.md")
    open(path, "w").write(text)
    return path


def breaker_note(walks):
    """Normal walk is the 0.15 m/s command. Jog is 0.40 m/s."""
    def pick(cmd, corner, dur):
        hits = [w for w in walks if w["model"] == "wire" and abs(w["cmd_m_s"] - cmd) < 1e-9 and w["corner"] == corner and abs(w["dur_s"] - dur) < 1.0]
        return hits[0] if hits else None

    top = None
    any_over = False
    for label, cmd, dur in (("normal walk", 0.15, 60.0), ("normal walk, 10 min", 0.15, 600.0), ("0.25 m/s", 0.25, 60.0), ("0.40 m/s jog", 0.40, 60.0), ("0.40 m/s jog, 10 min", 0.40, 600.0)):
        for corner in ("typical", "high-side"):
            row = pick(cmd, corner, dur)
            if row is None:
                continue
            for br, st in row["branches"].items():
                if st["above"]["7.23"]["time_above_s"] > 0:
                    any_over = True
                item = (st["peak_A"], label, corner, br)
                if top is None or item[0] > top[0]:
                    top = item
    if top is None:
        return "No limb trace was recorded."
    if any_over:
        return "At least one limb sample is above 7.23 A. The table has the duration. Sim pass only currents. The trip call is calc only."
    return (
        "No limb sample in these walks is above 7.23 A. The highest limb peak is %.3f A, on the %s, %s, %s (sim pass only). "
        "That peak is under the cited ILIM window, 7.23 A to 9.07 A, so the 600 nF timer does not start. "
        "A normal walk does not trip this breaker, and the 0.40 m/s jog does not trip it either. "
        "The 100 ms average is not the basis of that call. Calc only against the cited limits, on sim pass only currents."
        % top
    )


def heat_note(rows):
    def find(tag_part, case):
        hits = [r for r in rows if tag_part in r["tag"] and r["case"] == case]
        return hits[0] if hits else None

    # Prefer 10 min typical as the design series.
    tag = "600s" if any("typical_600s" in r["tag"] and r["tag"].startswith("wire_0.15") for r in rows) else "60s"
    g25 = find("wire_0.15_typical_%s" % tag, "guard_25")
    g32 = find("wire_0.15_typical_%s" % tag, "guard_32")
    c25 = find("wire_0.15_typical_%s" % tag, "cont70_25")
    c32 = find("wire_0.15_typical_%s" % tag, "cont70_32")
    c200 = find("wire_0.15_typical_%s" % tag, "cont200_25")
    c200h = find("wire_0.15_high-side_%s" % tag, "cont200_25")
    drop = find("wire_0.15_typical_%s" % tag, "cont70_25_drop0p3")
    bits = []
    if c25:
        petg = "The case does not reach 62 C in that 25 C run."
        if c25["minutes_to_right_body_62C"] is not None:
            petg = "The case reaches 62 C at %s." % fC(c25["minutes_to_right_body_62C"])
        bits.append(
            "Without the rest rule, cut still at 70 C, 25 C room: the right-knee reading reaches 55 C at %s and 60 C at %s. The case reaches 49 C at %s and peaks at %.2f C. %s After the cut unloads the knee the case cools, and at 90 min it is %.2f C (sim pass only)."
            % (fC(c25["minutes_to_right_reading_55C"]), fC(c25["minutes_to_right_reading_60C"]),
               fC(c25["minutes_to_right_body_49C"]), c25["right_knee_body_max_C"], petg, c25["body_end_C"])
        )
    if c32:
        bit32 = "The 32 C room with the same cut peaks the case at %.2f C." % c32["right_knee_body_max_C"]
        if c32["minutes_to_right_body_62C"] is not None:
            bit32 += " It reaches 62 C at %s." % fC(c32["minutes_to_right_body_62C"])
        bits.append(bit32 + " Sim pass only.")
    if c200:
        bits.append(
            "With the torque cut raised to 200 C on the typical corner, the reading reaches %.2f C and the case peaks at %.2f C (sim pass only). That stand-in cut then unloads the servo."
            % (c200["right_knee_reading_max_C"], c200["right_knee_body_max_C"])
        )
    if c200h:
        bits.append(
            "The high-side corner with the same 200 C stand-in ends at a %.2f C case, last-10-min rise %.3f C, reading max %.2f C (sim pass only). That is the balance this model reaches when the sheet cut is not allowed to hide it."
            % (c200h["body_end_C"], c200h["body_rise_last_10min_C"], c200h["right_knee_reading_max_C"])
        )
    if g25 and g32:
        bits.append(
            "The 55/45 guard, on the %s current, walks %.1f percent of the 90 min at 25 C and %.1f percent at 32 C (sim pass only). PR 86 reported 38.8 percent and 20.1 percent on the Kt-scaled old log."
            % ("10 min" if tag == "600s" else "60 s", 100.0 * g25["walk_share"], 100.0 * g32["walk_share"])
        )
        bits.append(
            "Guard case peak is %.2f C at 25 C and %.2f C at 32 C (sim pass only). The 90 min samples are %.2f C and %.2f C, and the last 10 min move those samples by %.3f C and %.3f C. The 32 C guard is still climbing at 90 min. Both peaks are above the cited 49 C PLA edge and under the cited 62 C PETG point."
            % (g25["right_knee_body_max_C"], g32["right_knee_body_max_C"],
               g25["body_end_C"], g32["body_end_C"],
               g25["body_rise_last_10min_C"], g32["body_rise_last_10min_C"])
        )
    if drop and c25:
        bits.append(
            "Putting the 0.30 V Castle drop back leaves the case peak at %.2f C against %.2f C on the wire (sim pass only). The knee number does not move with that trunk drop."
            % (drop["right_knee_body_max_C"], c25["right_knee_body_max_C"])
        )
    return " ".join(bits)


def long_note(walks):
    bits = []
    for row in walks:
        if row["model"] != "wire" or row["dur_s"] < 500:
            continue
        bits.append(
            "%.2f m/s %s, 10 min: hottest joint %s, motor RMS %.3f A over the whole window, %.3f A in the first minute, %.3f A in the last minute, pack mean %.3f A then %.3f A (sim pass only)."
            % (row["cmd_m_s"], row["corner"], row["hottest_joint"], row["hottest_motor_rms_A"],
               row["first_minute_hot_motor_rms_A"], row["last_minute_hot_motor_rms_A"],
               row["first_minute_pack_mean_A"], row["last_minute_pack_mean_A"])
        )
    if not bits:
        return ""
    return "Longer duty, the command held for 10 min. " + " ".join(bits)


def sanity_lines(doc):
    w = doc["wire_0.15_typical_60s"]
    lines = []
    lines.append("0.15 m/s typical speed %.4f m/s and pack peak %.3f A, against PR 85 0.1183 m/s and 8.114 A (sim pass only)." % (
        w["vx_m_s"], w["pack_window"]["i_max_A"]))
    # Motor RMS from this reduction against em_twin's own accumulator.
    joints = w["joints"]
    chk = w["servo_im_rms_check"]
    err = max(abs(a["motor_rms_A"] - b) for a, b in zip(joints, chk))
    lines.append("Per-joint motor RMS matches em_twin's own accumulator within %.6f A (sim pass only)." % err)
    falls = [row["tag"] for row in doc["walks"] if row["fall_s"] != "none"]
    lines.append("Falls: %s." % ("none" if not falls else ", ".join(falls)))
    base = doc["mass"]["baseline_trunk_kg"]
    lines.append("Baseline trunk %.4f kg against the PR 85 figure 1.0654 kg (sim pass only)." % base)
    mj = doc["mass"]["mujoco_minus_xml_wire_kg"]
    lines.append("MuJoCo trunk mass minus the patched XML mass on the wire body: %.6f kg." % mj)
    lines.append(
        "PR 85 printed 0.1183 m/s and 8.114 A from the unpatched 1.0654 kg trunk. This 0.15 m/s walk is the written 1.0994 kg trunk: speed differs by %.4f m/s and pack peak by %.3f A (sim pass only)."
        % (abs(w["vx_m_s"] - 0.1183), abs(w["pack_window"]["i_max_A"] - 8.114))
    )
    return lines


def assemble():
    meta = json.load(open(os.path.join(SCRATCH, "prepare.json")))
    tags = []
    for name in sorted(os.listdir(SCRATCH)):
        if name.endswith(".json") and not name.startswith("smoke") and name not in ("prepare.json", "thermal.json", "runc_joint_current.json"):
            tags.append(name[:-5])
    walks = [load_reduced(t) for t in tags]
    # Stable order.
    walks.sort(key=lambda r: (r["model"], r["cmd_m_s"], r["corner"], r["dur_s"]))
    by = {r["tag"]: r for r in walks}
    thermal = json.load(open(os.path.join(SCRATCH, "thermal.json"))) if os.path.exists(os.path.join(SCRATCH, "thermal.json")) else {"rows": [], "sha": None}
    doc = dict(
        label="sim pass only, calc only, or cited, per section",
        sv_sha=meta["sv_sha"],
        kh_sha=thermal.get("sha"),
        bec_removed_g=meta["bec_removed_g"],
        wire_extra=meta["extra"],
        unseated_ends=meta.get("unseated"),
        models={k: v for k, v in meta["models"].items()},
        walks=walks,
        mass=mass_report(meta),
        thermal=thermal,
    )
    doc["wire_0.15_typical_60s"] = by["wire_0.15_typical_60s"]
    doc["wire_0.15_highside_60s"] = by["wire_0.15_high-side_60s"]
    doc["long_note"] = long_note(walks)
    doc["heat_note"] = heat_note(thermal["rows"])
    doc["breaker_note"] = breaker_note(walks)
    doc["sanity"] = sanity_lines(doc)
    # Drop bulky pose lists from the repo JSON. The mass report keeps the distances.
    for row in doc["walks"]:
        row.pop("pose", None)
    out = os.path.join(HERE, "runc_joint_current.json")
    json.dump(doc, open(out, "w"), indent=1)
    md = write_md(doc)
    print("wrote", os.path.relpath(out, REPO), os.path.relpath(md, REPO), "json_bytes", os.path.getsize(out), flush=True)
    return doc


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    if step in ("smoke", "walks", "long", "all", "mass"):
        meta = prepare()
        # prepare() imported em_twin in this process. Workers are fresh processes.
        which = "walks" if step == "all" else step
        jobs = job_list(meta, which)
        if step == "all":
            jobs = job_list(meta, "walks")
        run_jobs(jobs)
        if step == "all":
            run_jobs(job_list(meta, "long"))
        if step == "smoke":
            print(load_reduced("smoke_wire_0.15_typical"))
            return
    if step in ("thermal", "all"):
        thermal = run_thermal()
        json.dump(thermal, open(os.path.join(SCRATCH, "thermal.json"), "w"), indent=1)
    if step in ("assemble", "all", "thermal", "walks", "long", "mass"):
        if step == "thermal" or os.path.exists(os.path.join(SCRATCH, "wire_0.15_typical_60s.json")):
            assemble()


if __name__ == "__main__":
    main()
