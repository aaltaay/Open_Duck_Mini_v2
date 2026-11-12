#!/usr/bin/env python3
"""pins_effect.py: do the 4 belly spring pins change the sit? sim pass only.
The duck stands on the mat near the sun (facing the room), settles, sits by the SIT.md path, torque off, 10 s rest.
Cases: pins off / pins on (0.6 to 1.4 N each, est) / pins at twice the force; mat friction 0.6, 0.8, 1.0; 4 seeds each.
Also the same sit with the mat kept as the height field (5 mm cells) instead of the plane, pins on: a contact-model check.
Logged (mean of the last 0.5 s): force on the seat block, the bumper and each sole, each pin's force and compression, the
gap from the pin base to the mat, trunk height and pitch, which joints rest on their stops, and the seat shift against
the standing pose.
  PYTHONDONTWRITEBYTECODE=1 python3 pins_effect.py     -> pins_effect.json
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

CASES = {"pins off": dict(pins_on=False), "pins on": dict(pins_on=True), "pins x2 force": dict(pins_on=True, pin_scale=2.0),
         "pins on, mat as height field": dict(pins_on=True, surface="field"), "pins off, mat as height field": dict(pins_on=False, surface="field")}


def job(a):
    name, mu, seed = a
    kw = dict(CASES[name])
    surf = kw.pop("surface", None)
    rng = np.random.default_rng(900 + seed)
    s = N.Sim(seed=seed, x0=-0.126 + rng.uniform(-0.01, 0.01), y0=rng.uniform(-0.01, 0.01), yaw0=np.pi, mu_mat=mu, volt=7.2, wall=False, **kw)
    if surf:
        s.force_surface = surf
    for _ in range(100):
        s.step((0, 0, 0))
    if s.fallen:                 # the start pose on the mat sometimes throws the duck before any command: not a result
        return dict(case=name, mu=mu, seed=seed, start_artefact=True)
    st = s.settle()
    p0, _, _ = s.trunk_pose()
    s.sit_down(t_off=10.0)
    acc, n = {}, 250
    for _ in range(n):
        s._phys()
        for k, v in s.contact_forces().items():
            acc[k] = acc.get(k, 0.0) + v / n
    pins = s.pins()
    p, z, up = s.trunk_pose()
    R = s.data.xmat[s.trunk].reshape(3, 3)
    seat = np.mean([pins["seat_L"]["xy"], pins["seat_R"]["xy"]], 0)
    c, sn = np.cos(p0[2]), np.sin(p0[2])
    d = seat - p0[:2]
    out = dict(case=name, mu=mu, seed=seed, surface=s.sit_surface, fell=bool(s.fallen), contacts_N={k: round(v, 3) for k, v in acc.items() if v > 0.005},
               pins={k: dict(F=round(v["F"], 3), comp_mm=round(v["comp"] * 1000, 2), gap_mm=round(v.get("gap", 0) * 1000, 2)) for k, v in pins.items()},
               trunk_z_above_mat_mm=round((z - N.MAT_H) * 1000, 2), pitch_deg=round(float(np.degrees(np.arcsin(np.clip(R[2, 0], -1, 1)))), 2),
               stops=s.joints_on_stops(), sit_shift_mm=[round(float(d[0] * c + d[1] * sn) * 1000, 1), round(float(-d[0] * sn + d[1] * c) * 1000, 1)])
    # stand up again: do the pins change the rise?
    s.stand_up()
    _, z2, up2 = s.trunk_pose()
    out.update(stood=bool(not s.fallen and z2 > 0.15 and up2 > 0.9))
    return out


if __name__ == "__main__":
    J = [(c, mu, sd) for c in CASES for mu in (0.6, 0.8, 1.0) for sd in range(4)]
    with Pool(int(os.environ.get("JOBS", "4"))) as p:
        R = p.map(job, J)
    S = {}
    for c in CASES:
        rr = [r for r in R if r["case"] == c and not r.get("start_artefact")]
        g = lambda f: [f(r) for r in rr]  # noqa: E731
        m_ = lambda v: [round(float(np.mean(v)), 2), round(float(np.min(v)), 2), round(float(np.max(v)), 2)]  # noqa: E731
        S[c] = dict(n=len(rr), start_artefacts_dropped=sum(bool(r.get("start_artefact")) for r in R if r["case"] == c), falls=sum(r["fell"] for r in rr), stood_up=sum(r["stood"] for r in rr),
                    seat_block_N=m_(g(lambda r: r["contacts_N"].get("sit_seat_trunk_assembly_1_collision", 0.0))),
                    bumper_block_N=m_(g(lambda r: r["contacts_N"].get("sit_bumper_trunk_assembly_1_collision", 0.0))),
                    soles_N=m_(g(lambda r: r["contacts_N"].get("left_foot_bottom_tpu", 0.0) + r["contacts_N"].get("right_foot_bottom_tpu", 0.0))),
                    seat_pin_N=m_(g(lambda r: 0.5 * (r["pins"]["seat_L"]["F"] + r["pins"]["seat_R"]["F"]))),
                    bump_pin_N=m_(g(lambda r: 0.5 * (r["pins"]["bump_L"]["F"] + r["pins"]["bump_R"]["F"]))),
                    seat_pin_comp_mm=m_(g(lambda r: 0.5 * (r["pins"]["seat_L"]["comp_mm"] + r["pins"]["seat_R"]["comp_mm"]))),
                    bump_pin_comp_mm=m_(g(lambda r: 0.5 * (r["pins"]["bump_L"]["comp_mm"] + r["pins"]["bump_R"]["comp_mm"]))),
                    seat_gap_mm=m_(g(lambda r: 0.5 * (r["pins"]["seat_L"]["gap_mm"] + r["pins"]["seat_R"]["gap_mm"]))),
                    bump_gap_mm=m_(g(lambda r: 0.5 * (r["pins"]["bump_L"]["gap_mm"] + r["pins"]["bump_R"]["gap_mm"]))),
                    trunk_z_above_mat_mm=m_(g(lambda r: r["trunk_z_above_mat_mm"])), pitch_deg=m_(g(lambda r: r["pitch_deg"])),
                    joints_on_stops=m_(g(lambda r: len(r["stops"]))), all_4_pins_touch=sum(all(v["F"] > 0 for v in r["pins"].values()) for r in rr),
                    sit_shift_fwd_mm=m_(g(lambda r: r["sit_shift_mm"][0])))
        print(c, json.dumps(S[c]))
    json.dump(dict(label="sim pass only", note="[mean, min, max] over the sits of 3 mat frictions x 4 seeds (start artefacts dropped); pin forces are computed for every case, applied only when pins are on",
                   pin_model=dict(F0_N=N.PIN_F0, F1_N=N.PIN_F1, travel_mm={k: v * 1000 for k, v in N.PIN_L.items()}), summary=S, runs=R),
              open(os.path.join(HERE, "pins_effect.json"), "w"), indent=1)
