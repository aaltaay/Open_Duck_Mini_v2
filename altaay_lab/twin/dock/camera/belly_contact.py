#!/usr/bin/env python3
"""Belly halves as the charging contact. Sim pass only.

The mat is the approved nest v2 field: 20 mm copper, 5 mm felt, period 25 mm.
D61 is not edited. The gold domes stay in camera_dock.py until this flag is on.

Two stainless inserts sit on the seat bottom (sit_cad.json, z -66 mm), flush
with that CAD face. The plastic seat is 0.9 mm higher, so nothing stands out
past the CAD shell. The bumper is 3 mm lower in the body, so it is raised 4 mm
and stays off the mat. A full-width metal half of the 80 mm seat would cross
a plus stripe and a minus stripe. The inserts are narrow so they cannot.

Labels in the printed note: sim pass only, calc only, CAD check only, cited.
"""
import json
import math
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..")))
from altaay_lab.twin.dock.camera import camera_dock as CD

# Insert size, metres. Half extents live on CD.BELLY_HALF.
# Full size 6.0 mm along the stripe (body x) and 2.2 mm across it (body y).
# Centers 25 mm apart, one stripe period, so they fall on opposite poles
# when both are on copper. The gap of bare PETG between them is 22.8 mm.
INSERT_LX = 0.0060
INSERT_LY = 0.0022
INSERT_SEP = 0.0250
INSERT_T = 0.0005  # plate thickness, calc only, not the collision box height

# 304 resistivity 72 microohm-cm at 20 C. Upmet 304 datasheet.
RHO_304 = 72e-8  # ohm m
# Density 7.90 g/cm3. Sandmeyer Alloy 304/304L sheet.
RHO_MASS_304 = 7.90
# PETG 1.27 g/cm3. The structure note cites the Prusa generic PETG profile.
RHO_PETG = 1.27

# LM74610-Q1 table: MOSFET on for 98 percent of the cycle, body diode the rest.
# CSD18532Q5B in that table: 3.3 mohm at 4.5 V, diode 0.53 V at 2 A (hot).
DUTY_MOS = 0.98
RDS_OHM = 0.0033
VF_DIODE = 0.53
N_FETS = 2  # one high leg and one low leg of the bridge


def _no_dash(text):
    if "\u2014" in text or "\u2013" in text:
        raise SystemExit("belly text has a dash that is not a hyphen")
    return text


def corners(x, y, yaw, bx, by, hx, hy):
    """World x and world y of the four corners of one insert. Calc only."""
    c, s = math.cos(yaw), math.sin(yaw)
    wxs, wys = [], []
    for dx in (-hx, hx):
        for dy in (-hy, hy):
            px, py = bx + dx, by + dy
            wxs.append(x + c * px - s * py)
            wys.append(y + s * px + c * py)
    return min(wxs), max(wxs), min(wys), max(wys)


def stripe_of(wy0, wy1):
    """'P' or 'M' if the whole span sits in one conductor, else 'short' or 'miss'."""
    period, stripe = CD.PERIOD, CD.STRIPE
    k0 = int(math.floor(wy0 / period)) - 1
    k1 = int(math.floor(wy1 / period)) + 1
    touched = []
    full = None
    for k in range(k0, k1 + 1):
        a = k * period
        b = a + stripe
        if wy1 > a + 1e-9 and wy0 < b - 1e-9:
            touched.append("P" if k % 2 == 0 else "M")
        if wy0 >= a - 1e-9 and wy1 <= b + 1e-9:
            full = "P" if k % 2 == 0 else "M"
    if "P" in touched and "M" in touched:
        return "short"
    return full if full else "miss"


def pair_at(x, y, yaw, hx, hy, sep=INSERT_SEP):
    """One label per insert: P, M, miss, short, or off (past the foil in x)."""
    out = []
    for by in (-0.5 * sep, 0.5 * sep):
        wx0, wx1, wy0, wy1 = corners(x, y, yaw, CD.BELLY_X, by, hx, hy)
        on = (CD.FIELD_X0 < wx0) and (wx1 < CD.FIELD_X1) and max(abs(wy0), abs(wy1)) < 0.280
        if not on:
            out.append("off")
        else:
            out.append(stripe_of(wy0, wy1))
    return out


def meets(labels):
    return ("P" in labels) and ("M" in labels) and ("short" not in labels) and ("off" not in labels)


def sweep(hx, hy, sep=INSERT_SEP, yaw_max=20.0, yaw_step=1.0, phase_mm=0.25):
    """Every stripe phase, every heading in the dock gate. Calc only."""
    phases = np.arange(0.0, CD.PERIOD, phase_mm / 1000.0)
    yaws = np.arange(-yaw_max, yaw_max + 1e-6, yaw_step)
    n = 0
    ok = short = miss = 0
    for a in yaws:
        yaw = math.pi + math.radians(float(a))
        for p in phases:
            n += 1
            # Trunk y is the phase. At yaw pi the insert midpoint maps to trunk y.
            labels = pair_at(0.020, float(p), yaw, hx, hy, sep)
            if "short" in labels:
                short += 1
            elif meets(labels):
                ok += 1
            else:
                miss += 1
    return dict(n=n, ok=ok, short=short, miss=miss,
                ok_frac=ok / n if n else 0.0, short_frac=short / n if n else 0.0)


def pick_report():
    """The size in the model, the print-high size, and a few neighbours. Calc only."""
    hx, hy = INSERT_LX / 2.0, INSERT_LY / 2.0
    # Print +0.3 mm grows each full side, so each half-extent grows 0.15 mm.
    hx_hi, hy_hi = hx + 0.00015, hy + 0.00015
    rows = []
    for name, a, b in (
        ("nominal", hx, hy),
        ("print_high_0.3mm", hx_hi, hy_hi),
        ("print_low_is_same_footprint", hx - 0.00015, hy - 0.00015),
    ):
        s = sweep(a, b)
        s["name"] = name
        s["lx_mm"] = round(2 * a * 1000.0, 2)
        s["ly_mm"] = round(2 * b * 1000.0, 2)
        rows.append(s)
    # World-y extent at 20 deg, the smear that could bridge the 5 mm gap.
    def extent(a, b, deg):
        th = math.radians(deg)
        return (abs(math.sin(th)) * 2 * a + abs(math.cos(th)) * 2 * b) * 1000.0
    gap_mm = (INSERT_SEP - INSERT_LY) * 1000.0
    return dict(
        rows=rows,
        extent_0_mm=round(extent(hx, hy, 0.0), 2),
        extent_14_mm=round(extent(hx, hy, 14.0), 2),
        extent_20_mm=round(extent(hx, hy, 20.0), 2),
        extent_20_print_high_mm=round(extent(hx_hi, hy_hi, 20.0), 2),
        gap_mm=round(gap_mm, 2),
        sep_mm=INSERT_SEP * 1000.0,
    )


def mass_note():
    """Grams, calc only, from the cited densities and the CAD bumper box."""
    vol_mm3 = 2.0 * (INSERT_LX * 1000.0) * (INSERT_LY * 1000.0) * (INSERT_T * 1000.0)
    steel_g = vol_mm3 / 1000.0 * RHO_MASS_304
    # Dock-model boxes, not the CAD cylinder. Seat face 32 by 80 mm raised 0.9 mm,
    # bumper box 24 by 60 mm raised 4 mm. The CAD bumper is a 12 mm radius cylinder,
    # so a real 4 mm cap is smaller than this box. This number is the box upper bound.
    inserts = 2.0 * (INSERT_LX * 1000.0) * (INSERT_LY * 1000.0)
    seat_cut = (32.0 * 80.0 - inserts) * 0.9
    bump_cut = 24.0 * 60.0 * 4.0
    petg_g = (seat_cut + bump_cut) / 1000.0 * RHO_PETG
    # Bulk resistance of one plate, thickness 0.5 mm, area the footprint.
    area = INSERT_LX * INSERT_LY
    r_one = RHO_304 * INSERT_T / area
    return dict(
        steel_g=round(steel_g, 3),
        petg_cut_g=round(petg_g, 2),
        net_g=round(steel_g - petg_g, 2),
        r_one_ohm=r_one,
        r_two_ohm=2 * r_one,
    )


def v_bridge(i_a):
    """Volts dropped in the two bridge legs. Calc only from the cited 98 percent and 3.3 mohm."""
    if i_a <= 0.0:
        return 0.0
    mos = N_FETS * i_a * RDS_OHM
    dio = N_FETS * VF_DIODE
    return DUTY_MOS * mos + (1.0 - DUTY_MOS) * dio


def enable():
    CD.BELLY = True
    CD.BELLY_HALF = (INSERT_LX / 2.0, INSERT_LY / 2.0, 0.0005)
    CD.BELLY_YS = (-0.5 * INSERT_SEP, 0.5 * INSERT_SEP)
    CD.BELLY_GEOM = score_geom
    CD.BELLY_SCORE = score_belly
    CD.BELLY_AFTER = resettle_cases


def score_geom(x, y, yaw):
    """Same keys the dock table already prints, plus the two insert labels."""
    hx, hy = INSERT_LX / 2.0, INSERT_LY / 2.0
    labels = pair_at(x, y, yaw, hx, hy)
    c, s = math.cos(yaw), math.sin(yaw)
    seat = (x + c * CD.SEAT_X, y + s * CD.SEAT_X)
    sun = math.hypot(seat[0], seat[1]) * 1000.0
    yaw_err = abs(math.degrees(CD.wrap(yaw - math.pi)))
    # Margin: how far the worse insert sits inside its 20 mm foil, in mm.
    margins = []
    for by, lab in zip((-0.5 * INSERT_SEP, 0.5 * INSERT_SEP), labels):
        if lab not in ("P", "M"):
            continue
        _, _, wy0, wy1 = corners(x, y, yaw, CD.BELLY_X, by, hx, hy)
        mid = 0.5 * (wy0 + wy1)
        k = math.floor(mid / CD.PERIOD)
        a = k * CD.PERIOD
        b = a + CD.STRIPE
        margins.append(min(wy0 - a, b - wy1) * 1000.0)
    pair = min(margins) if margins else None
    return dict(
        contacts_meet=bool(meets(labels)),
        plus=labels.count("P"),
        minus=labels.count("M"),
        seat_offset_mm=round(sun, 1),
        seat_x_mm=round(seat[0] * 1000.0, 1),
        seat_y_mm=round(seat[1] * 1000.0, 1),
        yaw_err_deg=round(yaw_err, 1),
        stripe_margin_mm=round(pair, 2) if pair is not None else None,
        align_mm=round(sun, 1),
    )


def _forces(sim):
    out = []
    for i in range(2):
        name = "belly_%d" % i
        out.append(CD.contact_force(sim, lambda n, name=name: n == name))
    return out


def _other_forces(sim):
    return dict(
        bumper=round(CD.contact_force(sim, lambda n: n == "sit_bumper_face"), 3),
        seat=round(CD.contact_force(sim, lambda n: n == "sit_seat_face"), 3),
    )


def score_belly(sim, x, y, yaw, geom):
    """Force on each insert, then the chip window. Not a hardware charge."""
    labels = pair_at(x, y, yaw, INSERT_LX / 2.0, INSERT_LY / 2.0)
    forces = _forces(sim) if sim is not None else [0.0, 0.0]
    plus_r, minus_r = [], []
    plus_f = minus_f = 0.0
    loss = []
    for fn, lab in zip(forces, labels):
        rr = CD.r_of_force(fn) if lab in ("P", "M") else None
        if lab == "P":
            plus_f += fn
            if rr is not None:
                plus_r.append(rr)
            elif fn < CD.F_MIN_N:
                loss.append("plus")
        elif lab == "M":
            minus_f += fn
            if rr is not None:
                minus_r.append(rr)
            elif fn < CD.F_MIN_N:
                loss.append("minus")
        elif lab == "short":
            loss.append("short")
    rp, rm = CD._parallel(plus_r), CD._parallel(minus_r)
    r_contact = None if rp is None or rm is None else rp + rm
    bulk = mass_note()["r_two_ohm"]
    r_series = None if r_contact is None else r_contact + CD.R_WIRE_OHM + bulk
    i_a = CD.I_SET_A if r_series is not None else 0.0
    v_diode = v_bridge(i_a) if r_series is not None else 0.0
    v_chip = None if r_series is None else CD.V_NEST - i_a * r_series - v_diode
    both_force = plus_f >= CD.F_MIN_N and minus_f >= CD.F_MIN_N
    charging = bool(
        geom
        and not ("short" in labels)
        and r_series is not None
        and both_force
        and CD.V_IN_MIN <= v_chip <= CD.V_IN_MAX
    )
    heat = None if r_contact is None else (CD.I_SET_A if charging else 0.0) ** 2 * r_contact
    return dict(
        charging=charging,
        well_force_n=[round(f, 3) for f in forces],
        pole_force_n=[round(plus_f, 3), round(minus_f, 3)],
        belly_labels=labels,
        contact_loss=bool(loss) or (geom and not both_force),
        short=bool("short" in labels),
        r_contact_ohm=None if r_contact is None else round(r_contact, 4),
        r_series_ohm=None if r_series is None else round(r_series, 4),
        v_diode=round(v_diode, 4),
        v_charger=None if v_chip is None else round(v_chip, 3),
        i_charge_a=round(CD.I_SET_A if charging else 0.0, 3),
        heat_w=None if heat is None else round(heat, 4),
        f_min_n=round(CD.F_MIN_N, 3),
        others=_other_forces(sim) if sim is not None else None,
    )


def _shift_inserts(sim, dz):
    mj = sim.mujoco
    ids = []
    for i in range(2):
        gid = mj.mj_name2id(sim.model, mj.mjtObj.mjOBJ_GEOM, "belly_%d" % i)
        ids.append(gid)
        sim.model.geom_pos[gid][2] += dz
    return ids


def resettle_cases(sim):
    """Reprint and a local felt dent, from the settled sit. Sim pass only.

    The walk is not repeated. The pose is the one the camera dock just sat.
    Print low lifts the inserts 0.3 mm. Print high lowers them 0.3 mm.
    The dent lifts them 0.4 mm, the gold-dome dent estimate, and it is not a
    measurement of this felt.
    """
    cases = (
        ("print_low", 0.0003),
        ("print_high", -0.0003),
        ("felt_dent", 0.0004),
    )
    saved_q = sim.data.qpos.copy()
    saved_z = []
    mj = sim.mujoco
    for i in range(2):
        gid = mj.mj_name2id(sim.model, mj.mjtObj.mjOBJ_GEOM, "belly_%d" % i)
        saved_z.append((gid, float(sim.model.geom_pos[gid][2])))
    rows = []
    for name, dz in cases:
        sim.data.qpos[:] = saved_q
        sim.data.qvel[:] = 0.0
        for gid, z0 in saved_z:
            sim.model.geom_pos[gid][2] = z0 + dz
        mj.mj_forward(sim.model, sim.data)
        sim.torque_off(0.8)
        x, y, yaw, _, _ = sim.true_pose()
        geom = score_geom(x, y, yaw)
        elec = score_belly(sim, x, y, yaw, geom["contacts_meet"])
        rows.append(dict(
            name=name,
            dz_mm=round(dz * 1000.0, 2),
            meet=geom["contacts_meet"],
            charging=elec["charging"],
            pole_force_n=elec["pole_force_n"],
            v_charger=elec["v_charger"],
            short=elec["short"],
            labels=elec["belly_labels"],
            contact_loss=elec["contact_loss"],
        ))
    for gid, z0 in saved_z:
        sim.model.geom_pos[gid][2] = z0
    sim.data.qpos[:] = saved_q
    sim.data.qvel[:] = 0.0
    mj.mj_forward(sim.model, sim.data)
    return rows


def probe():
    """One limp sit on the bumper, several stripe phases. Not a dock rate."""
    enable()
    os.environ.setdefault("MUJOCO_GL", "egl")
    sim = CD.DockSim(seed=0, light=1.0, record=False)
    try:
        target = CD._sit_targets(sim.model, sim.m)
        gain = sim.model.actuator_gainprm.copy()
        bias = sim.model.actuator_biasprm.copy()
        rows = []
        for phase_mm in (0.0, 2.5, 5.0, 10.0, 12.5, 18.0, 22.0):
            sim.model.actuator_gainprm[:] = gain
            sim.model.actuator_biasprm[:] = bias
            sim.fallen = False
            sim.sitting = False
            CD._place(sim, CD.BELLY_X, phase_mm / 1000.0, math.pi)
            sim.go_pose(target, 2.0, sitting=True)
            sim.torque_off(1.0)
            x, y, yaw, z, up = sim.true_pose()
            geom = score_geom(x, y, yaw)
            elec = score_belly(sim, x, y, yaw, geom["contacts_meet"])
            rows.append(dict(
                phase_mm=phase_mm, z=round(z, 4), up=round(up, 3),
                labels=elec["belly_labels"], meet=geom["contacts_meet"],
                forces=elec["well_force_n"], poles=elec["pole_force_n"],
                charging=elec["charging"], v=elec["v_charger"],
                others=elec["others"], short=elec["short"],
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


def _ground_z(x, y):
    """Mat top is 2.00 mm inside the upper felt. Off the mat the floor is 0."""
    # mat_top box: pos -0.0315, 0, 0.0015, size 0.2155, 0.280, 0.0005
    if abs(x + 0.0315) <= 0.2155 and abs(y) <= 0.280:
        return 0.002
    return 0.0


def walk_clearance(seconds=20.0):
    """Run D, inserts in the model. Min clearance of the belly metal. Sim pass only."""
    enable()
    os.environ.setdefault("MUJOCO_GL", "egl")
    sim = CD.DockSim(seed=1, light=1.0, record=False)
    try:
        CD._place(sim, -0.6, 0.4, math.pi)
        mj = sim.mujoco
        ids = [mj.mj_name2id(sim.model, mj.mjtObj.mjOBJ_GEOM, "belly_%d" % i) for i in range(2)]
        ids.append(mj.mj_name2id(sim.model, mj.mjtObj.mjOBJ_GEOM, "sit_bumper_face"))
        ids.append(mj.mj_name2id(sim.model, mj.mjtObj.mjOBJ_GEOM, "sit_seat_face"))
        clear = 1.0
        worst = None
        scraped = False
        n = 0
        while sim.t < seconds and not sim.fallen:
            cmd = (0.0, 0.0, 0.0) if sim.t < 0.8 else (0.20, 0.0, 0.0)
            sim.step_policy(cmd, capture=False, blur=False)
            n += 1
            for gid in ids:
                p = sim.data.geom_xpos[gid]
                z = _min_z(sim, gid)
                g = _ground_z(float(p[0]), float(p[1]))
                c = z - g
                if c < clear:
                    clear = c
                    worst = dict(z_mm=round(z * 1000, 2), ground_mm=round(g * 1000, 2),
                                 t=round(sim.t, 2),
                                 name=mj.mj_id2name(sim.model, mj.mjtObj.mjOBJ_GEOM, gid))
            f = sum(_forces(sim))
            if f > 0.05:
                scraped = True
        x, y, yaw, z, up = sim.true_pose()
        return dict(
            seconds=seconds, steps=n, fell=bool(sim.fallen),
            min_clear_mm=round(clear * 1000.0, 2),
            worst=worst, scraped=scraped,
            end=[round(x, 3), round(y, 3), round(z, 3)],
        )
    finally:
        sim.close()


def _font():
    """A sans file ffmpeg can draw. None if this machine has none."""
    for root, _dirs, files in os.walk("/usr/share/fonts"):
        for name in files:
            if name in ("DejaVuSans.ttf", "LiberationSans-Regular.ttf", "Inter-Regular.ttf"):
                return os.path.join(root, name)
    return None


def write_clip(frames, path):
    """720p-or-whatever the frames are, under 5 MB, caption on the picture."""
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
        "-an", "-vf", caption,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "30",
        "-preset", "veryfast", "-movflags", "+faststart", path,
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


def run_batch(n=40, record=False, jobs=1):
    enable()
    os.environ.setdefault("MUJOCO_GL", "egl")
    if record:
        os.environ["CAM_DOCK_W"] = "1280"
        os.environ["CAM_DOCK_H"] = "720"
    starts = list(CD.STARTS) + list(CD.STARTS_NEW)
    starts = starts[:n]
    rows = []
    ok_fr = bad_fr = None
    if jobs > 1 and not record:
        import multiprocessing as mp
        ctx = mp.get_context("spawn")
        with ctx.Pool(jobs) as pool:
            for row, _fr in pool.imap_unordered(_one_star, [(s, False) for s in starts]):
                rows.append(row)
                print("seed %d %s charge %s poles %s" % (
                    row["seed"], row["reason"], row.get("charging"), row.get("pole_force_n")), flush=True)
        rows.sort(key=lambda r: r["seed"])
    else:
        for seed, x, y, yaw_deg, light in starts:
            want = record and (ok_fr is None or bad_fr is None)
            row, frames = CD.run_one(seed, x, y, math.radians(yaw_deg), light, record=want, limit_s=70.0)
            rows.append(row)
            print("seed %d %s charge %s poles %s v %s" % (
                row["seed"], row["reason"], row.get("charging"), row.get("pole_force_n"), row.get("v_charger")),
                  flush=True)
            if record and frames:
                if row.get("charging") and ok_fr is None:
                    ok_fr = frames
                elif (not row.get("charging")) and bad_fr is None:
                    bad_fr = frames
    return rows, ok_fr, bad_fr


def _one_star(item):
    spec, record = item
    seed, x, y, yaw_deg, light = spec
    enable()
    os.environ.setdefault("MUJOCO_GL", "egl")
    return CD.run_one(seed, x, y, math.radians(yaw_deg), light, record=record, limit_s=70.0)


def summarize_cases(rows):
    out = {}
    for name in ("print_low", "print_high", "felt_dent"):
        got = [c for r in rows for c in (r.get("belly_cases") or []) if c["name"] == name]
        out[name] = dict(
            n=len(got),
            charge=sum(1 for c in got if c["charging"]),
            meet=sum(1 for c in got if c["meet"]),
            short=sum(1 for c in got if c["short"]),
        )
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--sweep" in argv:
        rep = dict(pick=pick_report(), mass=mass_note(), v_bridge_at_1a=round(v_bridge(CD.I_SET_A), 4))
        print(json.dumps(rep, indent=1))
        return 0
    if "--probe" in argv:
        print(json.dumps(probe(), indent=1))
        return 0
    if "--walk" in argv:
        sec = 20.0
        if "--seconds" in argv:
            sec = float(argv[argv.index("--seconds") + 1])
        print(json.dumps(walk_clearance(sec), indent=1))
        return 0
    n = 40
    if "--seeds" in argv:
        n = int(argv[argv.index("--seeds") + 1])
    record = "--videos" in argv
    jobs = 1
    if "--jobs" in argv:
        jobs = int(argv[argv.index("--jobs") + 1])
    rows, ok_fr, bad_fr = run_batch(n=n, record=record, jobs=jobs)
    summary = CD.summarize(rows)
    summary["cases"] = summarize_cases(rows)
    summary["shorts"] = sum(1 for r in rows if r.get("short"))
    summary["contact_loss"] = sum(1 for r in rows if r.get("contact_loss"))
    out_dir = os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "belly_batch.json"), "w", encoding="utf-8") as f:
        json.dump(dict(summary=summary, rows=rows, sweep=pick_report(), mass=mass_note()), f, indent=1)
    vid = os.path.join(CD.LAB, "twin", "out", "videos")
    if ok_fr:
        write_clip(ok_fr, os.path.join(vid, "belly_charge.mp4"))
        print("wrote belly_charge.mp4", len(ok_fr))
    if bad_fr:
        write_clip(bad_fr, os.path.join(vid, "belly_charge_fail.mp4"))
        print("wrote belly_charge_fail.mp4", len(bad_fr))
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
