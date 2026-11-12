#!/usr/bin/env python3
"""calib.py: the numbers the nest controller needs, measured in the same sim. sim pass only.
  step 1 (pins)  one sit on the flat floor (mu 0.8) without pins: where the seat block and the bumper are lowest, in the trunk body frame
                 -> the 4 pin positions (y +/-10 mm) and the pin axis (vertical in the settled sit). Writes calib.json.
  step 2 (turn)  standing on the mat near the sun centre (start there, a short forward burst, stop): turn on the spot at +1.0 and -1.0 until the true yaw has changed by 180 deg minus a lead,
                 zero command, settle march, feet-together stop, sit, torque off. Logged in the heading frame at the turn start:
                 the shift of the standing trunk (turn + stop), the yaw overshoot, the shift from the standing trunk to the
                 seat pins after torque off. 10 seeds x mat mu 0.6 / 0.8 / 1.0 x 6.0 / 7.2 V per direction.
  PYTHONDONTWRITEBYTECODE=1 python3 calib.py pins|turn
"""
import json
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nestlib as N  # noqa: E402
import mujoco  # noqa: E402

LEAD = np.radians(float(os.environ.get("LEAD_DEG", "0")))


def lowest_patch(s, g):
    md, dd = s.model, s.data
    mid = md.geom_dataid[g]
    a, n = md.mesh_vertadr[mid], md.mesh_vertnum[mid]
    V = md.mesh_vert[a:a + n] @ dd.geom_xmat[g].reshape(3, 3).T + dd.geom_xpos[g]
    low = V[V[:, 2] < V[:, 2].min() + 0.001]
    return low, float(V[:, 2].min())


def pins_job(_=None):
    s = N.Sim(seed=0, x0=-0.10, y0=0.0, yaw0=np.pi, mu_floor=0.8, pins_on=False, mat=False, wall=False)   # flat floor, as sit_contacts.py
    s.pin_body = None
    for _ in range(100):
        s.step((0, 0, 0))
    s.settle()
    s.sit_down(t_off=10.0)
    dd = s.data
    R = dd.xmat[s.trunk].reshape(3, 3)
    p = dd.xpos[s.trunk].copy()
    h = R[:, 0].copy(); h[2] = 0; h /= np.linalg.norm(h)
    l_ = np.array([-h[1], h[0], 0.0])
    out = {}
    info = {}
    for nm, g in (("seat", s.g_seat), ("bump", s.g_bump)):
        low, zmin = lowest_patch(s, g)
        xf = (low[:, :2] - p[:2]) @ h[:2]
        xc = 0.5 * (xf.min() + xf.max())
        info[nm] = dict(lowest_z_above_floor_mm=round(zmin * 1000, 2), x_heading_frame_mm=round(xc * 1000, 1))
        for tag, sg in (("L", 1), ("R", -1)):
            w = p + h * xc + l_ * sg * N.PIN_Y
            w[2] = zmin
            out["%s_%s" % (nm, tag)] = (R.T @ (w - p)).tolist()
    axis = (R.T @ np.array([0, 0, -1.0])).tolist()
    (x, y, yaw), z, up = s.trunk_pose()
    info["trunk"] = dict(z_mm=round(z * 1000, 1), pitch_deg=round(float(np.degrees(np.arcsin(np.clip(R[2, 0], -1, 1)))), 2))
    info["contacts_N_no_pins"] = {k: round(v, 2) for k, v in s.contact_forces().items() if v > 0.01}
    return dict(pin_body=out, pin_axis=axis, pins_info=info)


def turn_job(a):
    wz, seed, mu, volt = a
    rng = np.random.default_rng(5000 + seed)
    s = N.Sim(seed=seed, x0=rng.uniform(-0.03, 0.05), y0=rng.uniform(-0.03, 0.03), yaw0=np.radians(rng.uniform(-5, 5)), mu_mat=mu, volt=volt,
              wall=False)
    for _ in range(50):
        s.step((0, 0, 0))
    for _ in range(40):                 # a short forward burst and a stop, as at the end of the walk-on
        s.step((0.15, 0, 0))
    for _ in range(100):
        s.step((0, 0, 0))
    p0, _, _ = s.trunk_pose()          # the turn spot: near the sun centre, the whole turn on the mat
    yaw_prev, acc = p0[2], 0.0
    c, sn = np.cos(p0[2]), np.sin(p0[2])
    nturn = 0
    p = p0
    if s.fallen:
        return dict(wz=wz, seed=seed, mu=mu, volt=volt, fell=True, fell_before_turn=True, fall_t=s.tfall, resteps=0)
    while abs(acc) < np.pi - LEAD and nturn < 600 and not s.fallen:
        s.step((0, 0, wz))
        nturn += 1
        p, _, _ = s.trunk_pose()
        acc += N.wrap(p[2] - yaw_prev)
        yaw_prev = p[2]
    p1 = p.copy(); acc1 = acc
    if s.fallen:
        return dict(wz=wz, seed=seed, mu=mu, volt=volt, fell=True, fell_before_turn=False, fall_t=s.tfall, turn_s=nturn * 0.02, resteps=0)
    st = s.settle()
    p2, _, _ = s.trunk_pose()
    acc += N.wrap(p2[2] - yaw_prev)

    def loc(q):
        d = q[:2] - p0[:2]
        return [float(d[0] * c + d[1] * sn) * 1000, float(-d[0] * sn + d[1] * c) * 1000]
    if s.fallen:
        return dict(wz=wz, seed=seed, mu=mu, volt=volt, fell=True, fell_before_turn=False, fall_t=s.tfall, turn_s=nturn * 0.02, resteps=0)
    out = dict(wz=wz, seed=seed, mu=mu, volt=volt, turn_start_xy=[float(p0[0]), float(p0[1])], turn_s=nturn * 0.02, fell=s.fallen, at_cmd_end_mm=loc(p1), stand_mm=loc(p2), yaw_at_cmd_end_deg=float(np.degrees(acc1)),
               yaw_stand_deg=float(np.degrees(acc)), stagger_mm=st["stagger_mm"], stagger_before_mm=st["stagger_before_stance_mm"], resteps=st["resteps"])
    if s.fallen:
        return out
    s.sit_down(t_off=3.0)
    pins = s.pins()
    seat = np.mean([pins["seat_L"]["xy"], pins["seat_R"]["xy"]], 0)
    bump = np.mean([pins["bump_L"]["xy"], pins["bump_R"]["xy"]], 0)
    p3, _, up = s.trunk_pose()
    c2, s2 = np.cos(p2[2]), np.sin(p2[2])
    d = seat - p2[:2]
    out.update(seat_mm=loc(np.r_[seat, 0]), sit_shift_in_stand_frame_mm=[float(d[0] * c2 + d[1] * s2) * 1000, float(-d[0] * s2 + d[1] * c2) * 1000],
               sit_yaw_change_deg=float(np.degrees(N.wrap(np.arctan2(bump[1] - seat[1], bump[0] - seat[0]) - p2[2]))), sit_up=up,
               pinF={k: round(v["F"], 2) for k, v in pins.items()}, fell=s.fallen)
    return out


def stats(v):
    v = np.array(v, float)
    return dict(mean=round(float(v.mean()), 1), sd=round(float(v.std()), 1), min=round(float(v.min()), 1), max=round(float(v.max()), 1))


if __name__ == "__main__":
    what = sys.argv[1]
    cal = N.load_cal()
    if what == "pins":
        cal.update(pins_job())
        cal["label"] = "sim pass only"
        json.dump(cal, open(N.CAL_FILE, "w"), indent=1)
        print(json.dumps(cal, indent=1))
    if what == "turn":
        J = [(wz, sd, mu, v) for wz in (1.0, -1.0) for mu in (0.6, 0.8, 1.0) for v in (6.0, 7.2) for sd in range(10)]
        with Pool(4) as p:
            R = p.map(turn_job, J, chunksize=4)
        S = {}
        for wz in (1.0, -1.0):
            for key, sel in [("all", lambda r: True)] + [("mu%.1f" % mu, lambda r, mu=mu: r["mu"] == mu) for mu in (0.6, 0.8, 1.0)] + \
                            [("V%.1f" % v, lambda r, v=v: r["volt"] == v) for v in (6.0, 7.2)]:
                rr = [r for r in R if r["wz"] == wz and sel(r)]
                ok = [r for r in rr if not r["fell"] and "seat_mm" in r]
                if not ok:
                    S["%+.0f %s" % (wz, key)] = dict(n=len(rr), falls=len(rr)); continue
                S["%+.0f %s" % (wz, key)] = dict(
                    n=len(rr), start_artefact_falls_before_any_command=sum(bool(r.get("fell_before_turn")) for r in rr),
                    falls=sum(r["fell"] and not r.get("fell_before_turn") for r in rr), turn_s=stats([r["turn_s"] for r in ok]),
                    stand_fwd_mm=stats([r["stand_mm"][0] for r in ok]), stand_left_mm=stats([r["stand_mm"][1] for r in ok]),
                    yaw_stand_deg=stats([r["yaw_stand_deg"] for r in ok]), yaw_coast_deg=stats([r["yaw_stand_deg"] - r["yaw_at_cmd_end_deg"] for r in ok]),
                    seat_fwd_mm=stats([r["seat_mm"][0] for r in ok]), seat_left_mm=stats([r["seat_mm"][1] for r in ok]),
                    sit_shift_fwd_mm=stats([r["sit_shift_in_stand_frame_mm"][0] for r in ok]), sit_shift_left_mm=stats([r["sit_shift_in_stand_frame_mm"][1] for r in ok]),
                    sit_yaw_change_deg=stats([r["sit_yaw_change_deg"] for r in ok]), stagger_mm=stats([r["stagger_mm"] for r in ok]), stagger_before_mm=stats([r["stagger_before_mm"] for r in ok]), resteps=int(sum(r["resteps"] for r in ok)))
                print("%+.0f %s" % (wz, key), json.dumps(S["%+.0f %s" % (wz, key)]))
        json.dump(dict(label="sim pass only", lead_deg=float(np.degrees(LEAD)), summary=S, runs=R), open(os.path.join(HERE, "calib_turn.json"), "w"), indent=1)
