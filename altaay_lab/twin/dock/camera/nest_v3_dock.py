#!/usr/bin/env python3
"""Nest v3 dock: full seat and full bumper as the two belly halves.

Sim pass only. The mat strip and the stop window are in cad/nest_v3/layout.py.
"""
import json
import math
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
from altaay_lab.cad.nest_v3 import layout as LY
from altaay_lab.twin.dock.camera import camera_dock as CD

# Same bridge drop as the belly-insert study. Cited parts, calc only there.
V_BRIDGE = 0.0277
# DMP3018SFV, 12 milliohm max at -10 V (cited, Diodes product page).
# The gate is driven to about -15 V, which is more than -10 V and inside +/-25 V.
RDS_SW = 0.012


def enable():
    CD.NEST_V3 = True
    CD.BELLY = False
    CD.NEST_XS = LY.XS
    CD.NEST_W = LY.W
    CD.NEST_TX_LO = LY.TX_CMD_LO
    CD.NEST_TX_HI = LY.TX_CMD_HI
    CD.BELLY_GEOM = score_geom
    CD.BELLY_SCORE = score_charge
    CD.BELLY_AFTER = resettle_cases


def _pair_force(sim, a, b):
    total = 0.0
    mj = sim.mujoco
    for i in range(sim.data.ncon):
        con = sim.data.contact[i]
        fr = np.zeros(6)
        mj.mj_contactForce(sim.model, sim.data, i, fr)
        fn = float(fr[0])
        if fn <= 0.0:
            continue
        n1 = CD._geom_name(sim, con.geom1)
        n2 = CD._geom_name(sim, con.geom2)
        names = {n1, n2}
        if a in names and b in names:
            total += fn
    return total


def score_geom(x, y, yaw):
    """x, y, yaw are the trunk. The strip test uses trunk x."""
    c, s = math.cos(yaw), math.sin(yaw)
    seat = (x + c * CD.SEAT_X, y + s * CD.SEAT_X)
    sun = math.hypot(seat[0], seat[1]) * 1000.0
    yaw_err = abs(math.degrees(CD.wrap(yaw - math.pi)))
    # Also accept a sit that faces the wall (180 deg from the room).
    yaw_wall = abs(math.degrees(CD.wrap(yaw)))
    facing = min(yaw_err, yaw_wall)
    kind, seat_p, bump_p = LY.classify(x, yaw, grow=0.0)
    meet = kind == "ok" and facing < 20.0
    return dict(
        contacts_meet=bool(meet),
        plus=1 if meet else 0,
        minus=1 if meet else 0,
        seat_offset_mm=round(sun, 1),
        seat_x_mm=round(seat[0] * 1000.0, 1),
        seat_y_mm=round(seat[1] * 1000.0, 1),
        yaw_err_deg=round(yaw_err, 1),
        stripe_margin_mm=None,
        align_mm=round(sun, 1),
        nest_kind=kind,
        seat_pad=seat_p,
        bump_pad=bump_p,
        trunk_x_mm=round(x * 1000.0, 1),
    )


def score_charge(sim, x, y, yaw, geom):
    kind, seat_p, bump_p = LY.classify(x, yaw, grow=0.0)
    fs_r = _pair_force(sim, "sit_seat_face", "pad_rear") if sim is not None else 0.0
    fs_f = _pair_force(sim, "sit_seat_face", "pad_front") if sim is not None else 0.0
    fb_r = _pair_force(sim, "sit_bumper_face", "pad_rear") if sim is not None else 0.0
    fb_f = _pair_force(sim, "sit_bumper_face", "pad_front") if sim is not None else 0.0
    short = kind == "short" or (fs_r > 0.05 and fs_f > 0.05) or (fb_r > 0.05 and fb_f > 0.05)
    # Force that is on the pad the geometry assigns to that half.
    def on_pad(pad, fr, ff):
        if pad == "rear":
            return fr
        if pad == "front":
            return ff
        return 0.0
    f_seat = on_pad(seat_p, fs_r, fs_f)
    f_bump = on_pad(bump_p, fb_r, fb_f)
    # Rear pad is plus, front pad is minus. Report the two pole forces.
    plus_f = 0.0
    minus_f = 0.0
    if seat_p == "rear":
        plus_f += f_seat
    elif seat_p == "front":
        minus_f += f_seat
    if bump_p == "rear":
        plus_f += f_bump
    elif bump_p == "front":
        minus_f += f_bump
    rs = CD.r_of_force(f_seat) if seat_p in ("rear", "front") else None
    rb = CD.r_of_force(f_bump) if bump_p in ("rear", "front") else None
    r_contact = None if rs is None or rb is None else rs + rb
    r_series = None if r_contact is None else r_contact + CD.R_WIRE_OHM
    i_a = CD.I_SET_A if r_series is not None else 0.0
    v_sw = i_a * RDS_SW
    v_chip = None if r_series is None else CD.V_NEST - i_a * r_series - V_BRIDGE - v_sw
    both = f_seat >= CD.F_MIN_N and f_bump >= CD.F_MIN_N
    charging = bool(
        geom and not short and r_series is not None and both
        and v_chip is not None and CD.V_IN_MIN <= v_chip <= CD.V_IN_MAX
    )
    return dict(
        charging=charging,
        well_force_n=[round(f_seat, 3), round(f_bump, 3)],
        pole_force_n=[round(plus_f, 3), round(minus_f, 3)],
        contact_loss=bool(geom and not both),
        short=bool(short),
        r_contact_ohm=None if r_contact is None else round(r_contact, 4),
        v_charger=None if v_chip is None else round(v_chip, 3),
        i_charge_a=round(CD.I_SET_A if charging else 0.0, 3),
        f_min_n=round(CD.F_MIN_N, 3),
        half_force_n=[round(f_seat, 3), round(f_bump, 3)],
    )


def resettle_cases(sim):
    """Print and a felt dent. Not part of the dock clock. Sim pass only."""
    cases = (("print_low", 0.0003), ("print_high", -0.0003), ("felt_dent", 0.0004))
    saved_q = sim.data.qpos.copy()
    saved_t = float(sim.t)
    saved_record = bool(sim.record)
    nframes = len(sim.frames)
    sim.record = False
    mj = sim.mujoco
    names = ("sit_seat_face", "sit_bumper_face")
    saved_z = []
    try:
        for name in names:
            gid = mj.mj_name2id(sim.model, mj.mjtObj.mjOBJ_GEOM, name)
            saved_z.append((gid, float(sim.model.geom_pos[gid][2])))
        rows = []
        for name, dz in cases:
            sim.data.qpos[:] = saved_q
            sim.data.qvel[:] = 0.0
            sim.t = saved_t
            for gid, z0 in saved_z:
                sim.model.geom_pos[gid][2] = z0 + dz
            mj.mj_forward(sim.model, sim.data)
            sim.torque_off(0.8)
            x, y, yaw, _, _ = sim.true_pose()
            geom = score_geom(x, y, yaw)
            elec = score_charge(sim, x, y, yaw, geom["contacts_meet"])
            rows.append(dict(
                name=name, dz_mm=round(dz * 1000.0, 2),
                meet=geom["contacts_meet"], charging=elec["charging"],
                pole_force_n=elec["pole_force_n"], half_force_n=elec["half_force_n"],
                v_charger=elec["v_charger"], short=elec["short"],
            ))
        return rows
    finally:
        for gid, z0 in saved_z:
            sim.model.geom_pos[gid][2] = z0
        sim.data.qpos[:] = saved_q
        sim.data.qvel[:] = 0.0
        sim.t = saved_t
        sim.record = saved_record
        if len(sim.frames) > nframes:
            del sim.frames[nframes:]
        mj.mj_forward(sim.model, sim.data)


def probe_sit():
    """One placed sit in the window, and one facing the wall. Not a dock rate."""
    enable()
    os.environ.setdefault("MUJOCO_GL", "osmesa")
    sim = CD.DockSim(seed=0, light=1.0, record=False)
    try:
        target = CD._sit_targets(sim.model, sim.m)
        gain = sim.model.actuator_gainprm.copy()
        bias = sim.model.actuator_biasprm.copy()
        rows = []
        for name, tx, yaw in (
            ("room", -0.24, math.pi),
            ("wall", -0.16, 0.0),
        ):
            sim.model.actuator_gainprm[:] = gain
            sim.model.actuator_biasprm[:] = bias
            sim.fallen = False
            sim.sitting = False
            CD._place(sim, tx, 0.05, yaw)
            sim.go_pose(target, 2.0, sitting=True)
            sim.torque_off(1.0)
            x, y, yaw2, z, up = sim.true_pose()
            geom = score_geom(x, yaw2 and x, yaw2)
            # score_geom signature is (x, y, yaw)
            geom = score_geom(x, y, yaw2)
            elec = score_charge(sim, x, y, yaw2, geom["contacts_meet"])
            rows.append(dict(
                name=name, up=round(up, 3), z=round(z, 3),
                kind=geom["nest_kind"], tx=round(x, 3),
                halves=elec["half_force_n"], charging=elec["charging"],
                v=elec["v_charger"], short=elec["short"],
            ))
            print(json.dumps(rows[-1]), flush=True)
        return rows
    finally:
        sim.close()


def _min_z(sim, gid):
    pos = sim.data.geom_xpos[gid]
    rot = sim.data.geom_xmat[gid].reshape(3, 3)
    hs = sim.model.geom_size[gid]
    z = 1e9
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            for sz in (-1.0, 1.0):
                p = pos + rot @ (hs * np.array([sx, sy, sz]))
                z = min(z, float(p[2]))
    return z


def walk_clearance(seconds=20.0):
    enable()
    os.environ.setdefault("MUJOCO_GL", "osmesa")
    sim = CD.DockSim(seed=1, light=1.0, record=False)
    try:
        CD._place(sim, -0.6, 0.4, math.pi)
        mj = sim.mujoco
        ids = [
            mj.mj_name2id(sim.model, mj.mjtObj.mjOBJ_GEOM, n)
            for n in ("sit_seat_face", "sit_bumper_face")
        ]
        clear = 1.0
        worst = None
        scraped = False
        while sim.t < seconds and not sim.fallen:
            cmd = (0.0, 0.0, 0.0) if sim.t < 0.8 else (0.20, 0.0, 0.0)
            sim.step_policy(cmd, capture=False, blur=False)
            for gid in ids:
                p = sim.data.geom_xpos[gid]
                z = _min_z(sim, gid)
                on_mat = abs(p[0] + 0.0315) <= 0.2155 and abs(p[1]) <= 0.280
                gnd = 0.002 if on_mat else 0.0
                c = z - gnd
                if c < clear:
                    clear = c
                    worst = dict(
                        name=mj.mj_id2name(sim.model, mj.mjtObj.mjOBJ_GEOM, gid),
                        z_mm=round(z * 1000, 2), t=round(sim.t, 2),
                    )
            if _pair_force(sim, "sit_seat_face", "pad_rear") + _pair_force(sim, "sit_bumper_face", "pad_front") > 0.05:
                scraped = True
        return dict(seconds=seconds, fell=bool(sim.fallen), scraped=scraped,
                    min_clear_mm=round(clear * 1000.0, 2), worst=worst)
    finally:
        sim.close()


def _font():
    for root, _d, files in os.walk("/usr/share/fonts"):
        for name in files:
            if name in ("DejaVuSans.ttf", "LiberationSans-Regular.ttf", "Inter-Regular.ttf"):
                return os.path.join(root, name)
    return None


def write_clip(frames, path):
    if not frames:
        return None
    os.makedirs(os.path.dirname(path), exist_ok=True)
    h, w = frames[0].shape[:2]
    font = _font()
    caption = "drawtext=text='sim pass only':fontsize=32:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=10:x=28:y=28"
    if font:
        caption += ":fontfile='%s'" % font
    cmd = [
        "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", "%dx%d" % (w, h), "-r", "8", "-i", "-",
        "-an", "-vf", caption, "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "30", "-preset", "veryfast", "-movflags", "+faststart", path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for fr in frames:
            proc.stdin.write(np.ascontiguousarray(fr).tobytes())
        proc.stdin.close()
    except BrokenPipeError:
        pass
    err = proc.stderr.read().decode("utf-8", "replace")
    proc.wait()
    if proc.returncode != 0 or not os.path.isfile(path):
        raise SystemExit("video encode failed: " + err[-400:])
    if os.path.getsize(path) > 5_000_000:
        raise SystemExit("video over 5 MB")
    return path


def run_batch(n=40, jobs=1):
    enable()
    os.environ.setdefault("MUJOCO_GL", "osmesa")
    starts = (list(CD.STARTS) + list(CD.STARTS_NEW))[:n]
    rows = []
    if jobs > 1:
        import multiprocessing as mp
        ctx = mp.get_context("spawn")
        with ctx.Pool(jobs) as pool:
            for row, _fr in pool.imap_unordered(_one, starts):
                rows.append(row)
                print("seed %d %s charge %s halves %s tx %s" % (
                    row["seed"], row["reason"], row.get("charging"),
                    row.get("half_force_n"), row.get("trunk_x_mm")), flush=True)
        rows.sort(key=lambda r: r["seed"])
    else:
        for seed, x, y, yaw_deg, light in starts:
            row, _fr = CD.run_one(seed, x, y, math.radians(yaw_deg), light, record=False, limit_s=70.0)
            rows.append(row)
            print("seed %d %s charge %s" % (row["seed"], row["reason"], row.get("charging")), flush=True)
    return rows


def _one(spec):
    seed, x, y, yaw_deg, light = spec
    enable()
    os.environ.setdefault("MUJOCO_GL", "osmesa")
    return CD.run_one(seed, x, y, math.radians(yaw_deg), light, record=False, limit_s=70.0)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--probe" in argv:
        print(json.dumps(probe_sit(), indent=1))
        return 0
    if "--walk" in argv:
        print(json.dumps(walk_clearance(20.0), indent=1))
        return 0
    n = 40
    if "--seeds" in argv:
        n = int(argv[argv.index("--seeds") + 1])
    jobs = 4 if "--jobs" not in argv else int(argv[argv.index("--jobs") + 1])
    rows = run_batch(n=n, jobs=jobs)
    summary = CD.summarize(rows)
    summary["shorts"] = sum(1 for r in rows if r.get("short"))
    summary["cases"] = {}
    for name in ("print_low", "print_high", "felt_dent"):
        got = [c for r in rows for c in (r.get("belly_cases") or []) if c["name"] == name]
        summary["cases"][name] = dict(
            n=len(got),
            charge=sum(1 for c in got if c["charging"]),
            short=sum(1 for c in got if c["short"]),
        )
    out = os.path.join(HERE, "out", "nest_v3_batch.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(dict(summary=summary, rows=rows), f, indent=1)
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
