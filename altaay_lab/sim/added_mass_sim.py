"""Stock BEST_WALK_ONNX_2 policy on the robot we will build (sim pass only).

1. Builds a copy of the Playground MJCF in the scratch folder where every body's inertial (mass, centre of mass,
   full inertia) is replaced by the sum of its parts in our build (sim/mass_budget.py, task 1). That sum holds the
   lab-only parts at their audit/placements.json seats, the screws, inserts and wires, and our sliced part masses.
   The lab-only parts are also drawn as visual boxes (no collision, no mass of their own) so their seats can be seen.
2. Runs the cases of sim/current_budget.py (stand, forward, turn, side, backlash, rough backlash, 15 N pushes) on the
   trained model ("stock") and on our build ("ours") with the policy unchanged, the same control loop
   (upstream MjInfer, unmodified, accelerometer bias removed as in current_budget.py) and the same seeds.
3. Margin sweep on our build: trunk mass +10 %, +20 % and up, trunk centre of mass moved forward and back.
4. Push sweep: one lateral or fore-aft push per run at 8 gait phases and rising force, stock against ours.

Usage (from the repo root):
  ODM_PLAYGROUND=<Open_Duck_Playground at b9be205> ODM_SCRATCH=<scratch folder> nice -n 10 python3 altaay_lab/sim/added_mass_sim.py [all|cases|sweep|push|png]
Outputs in ODM_SCRATCH/added_mass: the model copies, results.json, traces (npz) for sim/runtime_thermal.py, and the
plots written to altaay_lab/sim/*.png (each under 500 kB).
"""
import os, sys, json, copy, time, types
import xml.etree.ElementTree as ET
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../.."))
PG = os.environ.get("ODM_PLAYGROUND", "/home/user/upstream/Open_Duck_Playground")
SCR = os.path.join(os.environ.get("ODM_SCRATCH", "/tmp/odm_added_mass"), "added_mass")
os.makedirs(SCR, exist_ok=True)
os.environ.setdefault("ODM_OUT", os.path.join(SCR, "current_budget_out"))
os.environ.setdefault("ODM_ONNX", os.path.join(REPO, "BEST_WALK_ONNX_2.onnx"))
sys.path.insert(0, HERE)
import mujoco
import current_budget as CB          # upstream MjInfer import, stubs, electrical model, summary (unmodified lab file)
import mass_budget as MB
MI = CB.MI
SRC_XML = os.path.join(PG, "playground/open_duck_mini_v2/xmls")
ROBOT_FILES = ("open_duck_mini_v2.xml", "open_duck_mini_v2_backlash.xml")

# ---------------------------------------------------------------------------------------------------------------
# Model copies
# ---------------------------------------------------------------------------------------------------------------
_ASSET_DIR = [None]
def _get_assets():
    """same as the stub in current_budget.py, but reads the variant folder (xml files) plus the upstream meshes"""
    assets = {}
    for f in os.listdir(os.path.join(SRC_XML, "assets")):
        assets[f] = open(os.path.join(SRC_XML, "assets", f), "rb").read()
    d = _ASSET_DIR[0] or SRC_XML
    for f in os.listdir(d):
        if f.endswith(".xml"): assets[f] = open(os.path.join(d, f), "rb").read()
    return assets
CB.base.get_assets = _get_assets
sys.modules["playground.open_duck_mini_v2.base"].get_assets = _get_assets

def fmt(v): return " ".join(f"{x:.9g}" for x in v)

def write_variant(name, links, boxes=()):
    """links: {body: MB.Mass} replacing the inertials; boxes: visual boxes (body, centre m, size m, rgba)"""
    d = os.path.join(SCR, "models", name); os.makedirs(d, exist_ok=True)
    for f in os.listdir(SRC_XML):
        if f.endswith(".xml") and f not in ROBOT_FILES:
            open(os.path.join(d, f), "wb").write(open(os.path.join(SRC_XML, f), "rb").read())
    for rf in ROBOT_FILES:
        tree = ET.parse(os.path.join(SRC_XML, rf)); root = tree.getroot()
        for body in root.iter("body"):
            nm = body.get("name")
            if nm in links:
                x = links[nm]; inert = body.find("inertial")
                for k in list(inert.attrib): del inert.attrib[k]
                I = x.I
                inert.set("pos", fmt(x.c)); inert.set("mass", f"{x.m:.9g}")
                inert.set("fullinertia", fmt([I[0, 0], I[1, 1], I[2, 2], I[0, 1], I[0, 2], I[1, 2]]))
            for (bn, c, size, rgba) in boxes:
                if nm == bn:
                    g = ET.SubElement(body, "geom"); g.set("type", "box"); g.set("class", "visual"); g.set("pos", fmt(c))
                    g.set("size", fmt(np.array(size) / 2)); g.set("rgba", rgba); g.set("contype", "0"); g.set("conaffinity", "0")
        tree.write(os.path.join(d, rf))
    return d

def model_check(d, scene="scene_flat_terrain.xml"):
    _ASSET_DIR[0] = d
    m = mujoco.MjModel.from_xml_string(open(os.path.join(d, scene)).read(), assets=_get_assets())
    return m

def variants(B=None):
    """returns {name: (folder, description)}"""
    B = B or MB.build_budget()
    stock = MB.model_inertials()
    ours = B["links"]
    pl = {p["id"]: p for p in json.load(open(os.path.join(REPO, "altaay_lab/audit/placements.json")))}
    boxes = [("trunk_assembly", np.array(p["center_mm"]) / 1000, np.array(p["dims_xyz_mm"]) / 1000, "0.85 0.1 0.1 1") for p in pl.values()]
    out = {"stock": (write_variant("stock", stock), "trained MJCF inertials, written back unchanged (check)"),
           "ours": (write_variant("ours", ours, boxes), "our build, mass_budget.py")}
    def mod(fn):
        L = {k: copy.deepcopy(v) for k, v in ours.items()}; fn(L); return L
    for pct in (10, 20, 30, 40, 50, 60):
        def f(L, pct=pct):
            t = L["trunk_assembly"]; t.m *= 1 + pct / 100; t.I = t.I * (1 + pct / 100)
        out[f"ours_trunk+{pct}%"] = (write_variant(f"ours_trunk+{pct}", mod(f), boxes), f"our build, trunk mass and inertia x{1 + pct / 100:.2f}")
    for dx in (-30, -20, -17.5, -15, -12.5, -10, -5, 5, 10, 20, 30):
        def f(L, dx=dx):
            L["trunk_assembly"].c = L["trunk_assembly"].c + np.array([dx / 1000, 0, 0])
        out[f"ours_trunkCoM{dx:+g}mm"] = (write_variant(f"ours_trunkcom{dx:+g}", mod(f), boxes), f"our build, trunk CoM moved {dx:+g} mm in x (+ is forward)")
    return out

# ---------------------------------------------------------------------------------------------------------------
# Run (copy of current_budget.run with extra logging: base pose and velocity at 50 Hz)
# ---------------------------------------------------------------------------------------------------------------
def run(folder, scene, schedule, dur, pushes=None, start_dz=0.0, seed=None, xy_range=0.0):
    _ASSET_DIR[0] = folder
    m = MI.MjInfer(os.path.join(folder, scene), CB.REF, CB.ONNX, standing=False)
    if start_dz:                       # raise the start pose (the upstream home pose puts the soles 10.7 mm into the floor)
        m.data.qpos[m._floating_base_qpos_addr + 2] += start_dz
    if seed is not None:               # seeds: joint start angles + U(-0.03, 0.03) rad (the training qpos0 jitter, randomize.py), start x, y
        rng = np.random.default_rng(seed)
        qa = np.array(m.actuator_joint_qpos_addr).ravel()
        m.data.qpos[qa] += rng.uniform(-0.03, 0.03, len(qa))
        m.data.qpos[m._floating_base_qpos_addr:m._floating_base_qpos_addr + 2] += rng.uniform(-xy_range, xy_range, 2)
    mujoco.mj_forward(m.model, m.data)
    if CB.ACC_OFFSET_FIX:
        _ga = m.get_accelerometer
        def _ga_fixed(d, _ga=_ga):
            a = np.array(_ga(d), dtype=float); a[0] -= 1.3; return a
        m.get_accelerometer = _ga_fixed
    model, data = m.model, m.data
    fb = m._floating_base_qpos_addr; qv = m.actuator_qvel_addr
    trunk = model.body("trunk_assembly").id
    nsteps = int(dur / m.sim_dt)
    F = np.zeros((nsteps, model.nu)); W = np.zeros((nsteps, model.nu))
    log = []; falls, fallen, counter = [], False, 0
    for k in range(nsteps):
        t = (k + 1) * m.sim_dt
        data.xfrc_applied[:] = 0
        if pushes:
            for (t0, t1, fvec) in pushes:
                if t0 <= t < t1: data.xfrc_applied[trunk, :3] = fvec
        mujoco.mj_step(model, data)
        counter += 1
        if counter % m.decimation == 0:
            m.commands = schedule(t)
            m.imitation_i += 1.0 * m.phase_frequency_factor
            m.imitation_i = m.imitation_i % m.PRM.nb_steps_in_period
            ph = m.imitation_i / m.PRM.nb_steps_in_period * 2 * np.pi
            m.imitation_phase = np.array([np.cos(ph), np.sin(ph)])
            obs = m.get_obs(data, m.commands)
            action = m.policy.infer(obs)
            m.last_last_last_action = m.last_last_action.copy()
            m.last_last_action = m.last_action.copy()
            m.last_action = action.copy()
            m.motor_targets = m.default_actuator + action * m.action_scale
            if MI.USE_MOTOR_SPEED_LIMITS:
                m.motor_targets = np.clip(m.motor_targets,
                    m.prev_motor_targets - m.max_motor_velocity * (m.sim_dt * m.decimation),
                    m.prev_motor_targets + m.max_motor_velocity * (m.sim_dt * m.decimation))
                m.prev_motor_targets = m.motor_targets.copy()
            data.ctrl = m.motor_targets.copy()
            pos = data.qpos[fb:fb + 3].copy(); quat = data.qpos[fb + 3:fb + 7].copy()
            R = np.zeros(9); mujoco.mju_quat2Mat(R, quat); R = R.reshape(3, 3); upz = R[2, 2]
            if (pos[2] < 0.10 or upz < 0.5) and not fallen:
                fallen = True; falls.append(round(t, 2))
            if fallen and pos[2] > 0.13 and upz > 0.8: fallen = False
            yaw = np.arctan2(R[1, 0], R[0, 0]); pitch = np.arcsin(-np.clip(R[2, 0], -1, 1)); roll = np.arctan2(R[2, 1], R[2, 2])
            com = data.subtree_com[trunk].copy()
            log.append((t, pos[0], pos[1], pos[2], yaw, pitch, roll, com[0], com[1], com[2], float(fallen)))
        F[k] = data.actuator_force; W[k] = data.qvel[qv]
    return dict(F=F, W=W, names=list(m.actuator_names), dt=m.sim_dt, falls=falls, log=np.array(log))

def gait_stats(res, cmd, t0=4.0):
    """velocity tracking, torso pitch and roll, torques; all after t0 (s)"""
    L = res["log"]; sel = L[:, 0] >= t0
    if sel.sum() < 10: return {}
    t, x, y, z, yaw, pitch, roll = [L[sel, i] for i in range(7)]
    yw = np.unwrap(yaw)
    dt = t[-1] - t[0]
    # velocity in the heading frame, averaged over the window (robot frame at each sample)
    vxw = np.gradient(x, t); vyw = np.gradient(y, t)
    vx = np.cos(yw) * vxw + np.sin(yw) * vyw; vy = -np.sin(yw) * vxw + np.cos(yw) * vyw
    wz = (yw[-1] - yw[0]) / dt
    k0 = int(round(t0 / res["dt"]))
    Fh = res["F"][k0:]; sat = (np.abs(Fh) >= 3.229).mean(0)
    out = dict(vx=float(vx.mean()), vy=float(vy.mean()), wz=float(wz), cmd=list(cmd[:3]),
               pitch_mean_deg=float(np.degrees(pitch.mean())), pitch_rms_deg=float(np.degrees(np.sqrt(((pitch - pitch.mean()) ** 2).mean()))),
               pitch_max_abs_deg=float(np.degrees(np.abs(pitch).max())), roll_mean_deg=float(np.degrees(roll.mean())),
               roll_rms_deg=float(np.degrees(np.sqrt(((roll - roll.mean()) ** 2).mean()))), roll_max_abs_deg=float(np.degrees(np.abs(roll).max())),
               z_min=float(z.min()), z_mean=float(z.mean()),
               torque_rms=dict(zip(res["names"], np.round(np.sqrt((Fh ** 2).mean(0)), 4).tolist())),
               torque_max=dict(zip(res["names"], np.round(np.abs(Fh).max(0), 4).tolist())),
               sat_frac=dict(zip(res["names"], np.round(sat, 4).tolist())))
    if cmd[0] or cmd[1]:
        vc = np.hypot(cmd[0], cmd[1]); out["track_lin"] = float(np.hypot(out["vx"], out["vy"]) / vc)
    if cmd[2]: out["track_yaw"] = float(wz / cmd[2])
    return out

# the current_budget.py cases, plus the rough-terrain walk with the start raised 23 mm: at the upstream home pose the soles
# start up to 20.6 mm inside the 0 to 10 mm heightfield, the robot is thrown over at 0.28 s and never walks (stock and ours)
CASES = [(c[0], c[1], c[2], c[3], c[4], 0.0) for c in CB.CASES] + [
    ("walk_rough_backlash_raised_start", "scene_rough_terrain_backlash.xml", CB.sched_const([0.15, 0, 0.0, 0, 0, 0, 0]), 30.0, None, 0.023)]
CMD = {"stand_in_place": [0, 0, 0], "walk_forward_0.15": [0.15, 0, 0], "turn_1.0": [0, 0, 1.0], "walk_side_0.2": [0, 0.2, 0],
       "walk_backlash": [0.15, 0, 0], "walk_rough_backlash": [0.15, 0, 0], "walk_pushes": [0.15, 0, 0], "walk_rough_backlash_raised_start": [0.15, 0, 0]}

def protection_stats(res, kt=CB.KTS[0]):
    """servo self-protection checks (Feetech C001 spec 7-11: over 2 A for 2 s cuts torque; over 80 % of stall for 2 s;
    over 70 C cuts torque): longest continuous time above 2 A and above 80 % duty per joint, max 2 s mean |I|"""
    I, P = CB.electrical(res["F"], res["W"], kt); dt = res["dt"]; k0 = int(round(CB.SKIP_S / dt)); I = np.abs(I[k0:])
    Rm = kt / CB.KT_OVER_R; u = np.abs(np.clip(res["F"][k0:] * Rm / kt, -CB.VIN, CB.VIN)) / CB.VIN
    def longest(mask):
        best = cur = 0
        for v in mask:
            cur = cur + 1 if v else 0; best = max(best, cur)
        return best * dt
    n2 = int(round(2.0 / dt))
    out = {}
    for j, nm in enumerate(res["names"]):
        out[nm] = dict(longest_over_2A_s=round(longest(I[:, j] > 2.0), 3), longest_over_80pct_duty_s=round(longest(u[:, j] > 0.8), 3),
                       max_2s_mean_A=round(float(CB.movavg(I[:, j], n2).max()), 3) if len(I) > n2 else None)
    return out

def run_seeds(V, names=("stock", "ours"), nseed=6):
    """repeat each case with seeds 1..nseed (joint start jitter; rough terrain also a random start x, y within 2 m)"""
    out = {}
    for vn in names:
        out[vn] = {}
        for label, scene, sch, dur, pushes, dz in CASES:
            if label in ("stand_in_place", "walk_rough_backlash"): continue
            rows = []
            for sd in range(1, nseed + 1):
                res = run(V[vn][0], scene, sch, dur, pushes, dz, seed=sd, xy_range=2.0 if "rough" in label else 0.0)
                g = gait_stats(res, CMD[label]); fl = [f for f in res["falls"] if f > 1.0]
                rows.append(dict(seed=sd, falls=fl, first_fall_s=fl[0] if fl else None, track_lin=g.get("track_lin"), track_yaw=g.get("track_yaw"),
                                 vx=g.get("vx"), vy=g.get("vy"), wz=g.get("wz"), pitch_mean_deg=g.get("pitch_mean_deg"), roll_rms_deg=g.get("roll_rms_deg")))
            nf = sum(1 for r in rows if r["falls"]); ok = [r for r in rows if not r["falls"]]
            tr = [r["track_lin"] if r["track_lin"] is not None else r["track_yaw"] for r in ok]
            out[vn][label] = dict(runs=rows, n=len(rows), n_fell=nf, track_mean=float(np.mean(tr)) if tr else None,
                                  track_min=float(np.min(tr)) if tr else None, track_max=float(np.max(tr)) if tr else None)
            print(f"seeds {vn:6s} {label:34s} fell {nf}/{len(rows)} first falls {[r['first_fall_s'] for r in rows]} track {out[vn][label]['track_mean']}", flush=True)
    return out

def run_cases(names=("stock", "ours"), V=None, save_traces=True):
    V = V or variants()
    results = {}
    for vn in names:
        folder = V[vn][0]; results[vn] = {}
        for label, scene, sch, dur, pushes, dz in CASES:
            t = time.time(); res = run(folder, scene, sch, dur, pushes, dz)
            s = CB.summarize(dict(F=res["F"], W=res["W"], names=res["names"], dt=res["dt"], falls=res["falls"]), label); s.pop("_trace_bus_A", None)
            s["gait"] = gait_stats(res, CMD[label]); s["protection"] = protection_stats(res)
            results[vn][label] = s
            if save_traces:
                os.makedirs(os.path.join(SCR, "traces", vn), exist_ok=True)
                np.savez_compressed(os.path.join(SCR, "traces", vn, f"trace_{label}.npz"), F=res["F"].astype(np.float32), W=res["W"].astype(np.float32),
                                    names=np.array(res["names"]), dt=res["dt"], log=res["log"].astype(np.float32))
            k = s["per_kt"][str(CB.KTS[0])]; g = s["gait"]
            print(f"{vn:24s} {label:22s} falls {s['falls']} bus mean {k['bus_A_mean']:.2f} A 100ms {k['bus_A_max_window'].get('100ms')} "
                  f"vx {g.get('vx', 0):+.3f} vy {g.get('vy', 0):+.3f} wz {g.get('wz', 0):+.2f} pitch {g.get('pitch_mean_deg', 0):+.1f}+-{g.get('pitch_rms_deg', 0):.1f} "
                  f"roll rms {g.get('roll_rms_deg', 0):.1f} ({time.time() - t:.1f} s)", flush=True)
    return results

SWEEP_CASES = ("walk_forward_0.15", "turn_1.0", "walk_side_0.2", "walk_backlash", "walk_rough_backlash_raised_start", "walk_pushes")
def run_sweep(V=None):
    V = V or variants(); out = {}
    keys = [k for k in V if k.startswith("ours_")]
    for vn in keys:
        out[vn] = {}
        for label, scene, sch, dur, pushes, dz in CASES:
            if label not in SWEEP_CASES: continue
            res = run(V[vn][0], scene, sch, dur, pushes, dz)
            k = CB.summarize(dict(F=res["F"], W=res["W"], names=res["names"], dt=res["dt"], falls=res["falls"]), label)["per_kt"][str(CB.KTS[0])]
            g = gait_stats(res, CMD[label])
            out[vn][label] = dict(falls=res["falls"], bus_A_mean=k["bus_A_mean"], bus_A_100ms=k["bus_A_max_window"].get("100ms"),
                                  vx=g.get("vx"), vy=g.get("vy"), wz=g.get("wz"), track_lin=g.get("track_lin"), track_yaw=g.get("track_yaw"),
                                  pitch_mean_deg=g.get("pitch_mean_deg"), pitch_rms_deg=g.get("pitch_rms_deg"), roll_rms_deg=g.get("roll_rms_deg"),
                                  knee_sat=max(g["sat_frac"]["left_knee"], g["sat_frac"]["right_knee"]) if g else None)
            print(f"{vn:24s} {label:22s} falls {res['falls']} bus {k['bus_A_mean']:.2f} vx {g.get('vx', 0):+.3f} wz {g.get('wz', 0):+.2f} "
                  f"pitch {g.get('pitch_mean_deg', 0):+.1f} knee sat {out[vn][label]['knee_sat']}", flush=True)
    return out

def run_com_back(V=None, dxs=(-10, -12.5, -15, -17.5, -20, -30)):
    """backward trunk CoM shifts: is the early fall a standing instability or the start drop (soles start 10.7 mm in the floor)?
    stand 10 s and walk forward 12 s, upstream start and a start raised 12 mm, seeds none and 1 to 3"""
    V = V or variants(); out = {}
    for dx in dxs:
        vn = f"ours_trunkCoM{dx:+g}mm"; out[vn] = {}
        for start, dz in (("upstream start", 0.0), ("start raised 12 mm", 0.012)):
            for label, cmd, dur in (("stand", [0, 0, 0], 10.0), ("walk_forward", [0.15, 0, 0], 12.0)):
                fl = []
                for sd in (None, 1, 2, 3):
                    res = run(V[vn][0], "scene_flat_terrain.xml", CB.sched_const(cmd + [0, 0, 0, 0]), dur, None, dz, seed=sd)
                    fl.append(res["falls"][0] if res["falls"] else None)
                out[vn][f"{label}, {start}"] = fl
                print(f"com back {vn:22s} {label:12s} {start:20s} falls at {fl}", flush=True)
    return out

def run_push_sweep(V=None, forces=(6, 9, 12, 15, 18, 21, 24), nphase=8):
    """one 0.1 s push per run on the trunk at t = 6 s + phase, walking forward 0.15 m/s, 10 s runs; fall = fell within 4 s after the push"""
    V = V or variants(); out = {}
    period = None
    for vn in ("stock", "ours"):
        out[vn] = {}
        for dirn, vec in (("left", (0, 1, 0)), ("right", (0, -1, 0)), ("forward", (1, 0, 0)), ("back", (-1, 0, 0))):
            for f in forces:
                nf = 0; times = []
                for ph in range(nphase):
                    t0 = 6.0 + ph * 0.54 / nphase      # gait period 0.54 s (SERVO_DEEP_DIVE.md section 5, reference motion)
                    res = run(V[vn][0], "scene_flat_terrain.xml", CB.sched_const([0.15, 0, 0, 0, 0, 0, 0]), 10.0,
                              [(t0, t0 + 0.1, tuple(f * np.array(vec, float)))])
                    fell = [x for x in res["falls"] if x >= t0]
                    nf += 1 if fell else 0
                out[vn][f"{dirn}_{f}N"] = nf / nphase
                print(f"push {vn:6s} {dirn:8s} {f:3d} N: fall fraction {nf}/{nphase}", flush=True)
    return out

# ---------------------------------------------------------------------------------------------------------------
def plots(results, sweep, push):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    # 1. traces: forward walk, stock against ours
    fig, axs = plt.subplots(3, 1, figsize=(8.5, 6.2), sharex=True)
    for vn, col in (("stock", "#4a6fa5"), ("ours", "#c0392b")):
        for label, ls in (("walk_forward_0.15", "-"),):
            d = np.load(os.path.join(SCR, "traces", vn, f"trace_{label}.npz")); L = d["log"]
            axs[0].plot(L[:, 0], np.degrees(L[:, 5]), ls, color=col, lw=0.9, label=f"{vn}")
            axs[1].plot(L[:, 0], np.degrees(L[:, 6]), ls, color=col, lw=0.9)
            I, P = CB.electrical(d["F"].astype(float), d["W"].astype(float), CB.KTS[0]); bus = np.clip(P, 0, None).sum(1) / CB.VIN
            t = np.arange(len(bus)) * float(d["dt"])
            axs[2].plot(t[:len(CB.movavg(bus, 50))] + 0.05, CB.movavg(bus, 50), color=col, lw=0.9)
    axs[0].set_ylabel("torso pitch (deg)"); axs[1].set_ylabel("torso roll (deg)"); axs[2].set_ylabel("servo bus A\n(100 ms avg)")
    axs[2].set_xlabel("time (s)"); axs[0].legend(fontsize=8, loc="upper right")
    axs[0].set_title("Walk forward 0.15 m/s, stock model against our build (sim pass only)", fontsize=9)
    for a in axs: a.grid(alpha=0.3); a.tick_params(labelsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "added_mass_forward_walk.png"), dpi=80); plt.close(fig)
    # 2. margin sweep
    fig, axs = plt.subplots(1, 2, figsize=(9.5, 3.6))
    ks = [k for k in sweep if "trunk+" in k]; xs = [0] + [int(k.split("+")[1].rstrip("%")) for k in ks]
    for label, col in (("walk_forward_0.15", "#4a6fa5"), ("walk_backlash", "#c0392b"), ("walk_rough_backlash_raised_start", "#7d3c98"), ("turn_1.0", "#1e8449")):
        base = results["ours"][label]
        y = [base["gait"].get("track_lin", base["gait"].get("track_yaw"))] + [sweep[k][label]["track_lin"] or sweep[k][label]["track_yaw"] for k in ks]
        fl = [bool(base["falls"])] + [bool([f for f in sweep[k][label]["falls"] if f > 1.0]) for k in ks]
        axs[0].plot(xs, y, "o-", color=col, ms=3, lw=1, label=label)
        for xx, yy, ff in zip(xs, y, fl):
            if ff: axs[0].plot(xx, yy, "x", color="k", ms=7)
    axs[0].set_xlabel("extra trunk mass on our build (%)"); axs[0].set_ylabel("tracking (measured / command)"); axs[0].legend(fontsize=7); axs[0].grid(alpha=0.3)
    ks = sorted([k for k in sweep if "CoM" in k], key=lambda k: float(k.split("CoM")[1].rstrip("mm")))
    xs = [float(k.split("CoM")[1].rstrip("mm")) for k in ks]
    for label, col in (("walk_forward_0.15", "#4a6fa5"), ("walk_backlash", "#c0392b"), ("walk_rough_backlash_raised_start", "#7d3c98"), ("turn_1.0", "#1e8449")):
        y = [sweep[k][label]["pitch_mean_deg"] for k in ks]; fl = [bool([f for f in sweep[k][label]["falls"] if f > 1.0]) for k in ks]
        axs[1].plot(xs, y, "o-", color=col, ms=3, lw=1, label=label)
        for xx, yy, ff in zip(xs, y, fl):
            if ff: axs[1].plot(xx, yy, "x", color="k", ms=7)
    axs[1].set_xlabel("trunk CoM shift on our build (mm, + forward)"); axs[1].set_ylabel("mean torso pitch (deg)"); axs[1].grid(alpha=0.3)
    fig.suptitle("Margin sweep (x = fell), sim pass only", fontsize=9); fig.tight_layout(); fig.savefig(os.path.join(HERE, "added_mass_margin_sweep.png"), dpi=80); plt.close(fig)
    # 3. push sweep
    if push:
        fig, axs = plt.subplots(1, 4, figsize=(11, 2.8), sharey=True)
        for a, dirn in zip(axs, ("left", "right", "forward", "back")):
            for vn, col in (("stock", "#4a6fa5"), ("ours", "#c0392b")):
                ks = [k for k in push[vn] if k.startswith(dirn + "_")]; xs = [int(k.split("_")[1].rstrip("N")) for k in ks]
                a.plot(xs, [push[vn][k] for k in ks], "o-", color=col, ms=3, lw=1, label=vn)
            a.set_title(f"push to the {dirn}" if dirn in ("left", "right") else f"push {dirn}", fontsize=8); a.set_xlabel("force (N) for 0.1 s", fontsize=8); a.grid(alpha=0.3)
            a.tick_params(labelsize=7)
        axs[0].set_ylabel("fall fraction (8 phases)", fontsize=8); axs[0].legend(fontsize=7)
        fig.tight_layout(); fig.savefig(os.path.join(HERE, "added_mass_push_sweep.png"), dpi=80); plt.close(fig)

def seats_png(B=None):
    """top and side view of the trunk (printed shells as grey points) with the lab-only part seats (red boxes) and the
    trunk centre of mass, trained against ours. Drawn with matplotlib: this container has no OpenGL for MuJoCo renders."""
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; import trimesh
    B = B or MB.build_budget(); u = B["urdf"]; stock = MB.model_inertials()
    pts = []
    for v in u.link_map["trunk_assembly"].visuals:
        fn = os.path.basename(v.geometry.mesh.filename)
        if not fn.startswith(("body_", "trunk_", "battery")): continue
        m = trimesh.load(os.path.join(MB.URDF_DIR, fn), force="mesh"); m.apply_transform(v.origin)
        pts.append(m.sample(4000) * 1000)
    P = np.vstack(pts)
    pl = json.load(open(os.path.join(REPO, "altaay_lab/audit/placements.json")))
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
    for ax, (i, j, li, lj) in zip(axs, ((0, 1, "x (mm, + forward)", "y (mm, + left)"), (0, 2, "x (mm, + forward)", "z (mm, + up)"))):
        ax.scatter(P[:, i], P[:, j], s=0.2, c="#bbbbbb")
        for p in pl:
            c = np.array(p["center_mm"]); d = np.array(p["dims_xyz_mm"])
            ax.add_patch(plt.Rectangle((c[i] - d[i] / 2, c[j] - d[j] / 2), d[i], d[j], fill=False, ec="#c0392b", lw=1.2))
            ax.text(c[i], c[j], p["id"].replace("_", " "), fontsize=6, ha="center", va="center", color="#c0392b")
        for x, mk, col, lab in ((stock["trunk_assembly"], "^", "#4a6fa5", "trunk CoM, trained"), (B["links"]["trunk_assembly"], "^", "#c0392b", "trunk CoM, ours")):
            ax.plot(x.c[i] * 1000, x.c[j] * 1000, mk, color=col, ms=8, label=lab)
        ax.set_xlabel(li); ax.set_ylabel(lj); ax.set_aspect("equal"); ax.grid(alpha=0.3)
    axs[0].legend(fontsize=7, loc="upper right"); axs[0].set_title("trunk from above", fontsize=9); axs[1].set_title("trunk from the left side", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "added_mass_lab_parts.png"), dpi=80); plt.close(fig)

def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    V = variants()
    for vn in ("stock", "ours"):
        mm = model_check(V[vn][0])
        print(vn, "total mass", round(float(mm.body_subtreemass[1]), 4), "kg")
    path = os.path.join(SCR, "results.json")
    steps = dict(cases=lambda: run_cases(("stock", "ours"), V), seeds=lambda: run_seeds(V), sweep=lambda: run_sweep(V),
                 com_back=lambda: run_com_back(V), push=lambda: run_push_sweep(V))
    R = {}
    for k in steps:                                   # one file per step, so steps can run one at a time or in parallel
        f = os.path.join(SCR, f"results_{k}.json")
        if os.path.exists(f): R[k] = json.load(open(f))
    for k, fn in steps.items():
        if what in ("all", k, "comback" if k == "com_back" else k):
            R[k] = fn(); json.dump(R[k], open(os.path.join(SCR, f"results_{k}.json"), "w"), indent=1, default=float)
    json.dump(R, open(path, "w"), indent=1, default=float)
    if what in ("all", "png") and "cases" in R and "sweep" in R:
        plots(R["cases"], R["sweep"], R.get("push"))
        seats_png()
    print("wrote", path)

if __name__ == "__main__":
    main()
