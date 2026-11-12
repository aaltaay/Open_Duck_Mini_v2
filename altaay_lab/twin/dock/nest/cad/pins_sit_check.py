#!/usr/bin/env python3
"""pins_sit_check.py: the torque-off sit on the mat with the CHOSEN pins (not the assumed ones of NEST_SIM.md). sim pass only.

The harness is dock/natural/sim/nestlib.py and the method is sim/pins_effect.py (both only read): the duck stands on the
mat at the sun, sits by the SIT.md path, torque off, 10 s rest, then stands up. Only the pin model is replaced here:
  travel (proud height)  seat 3.0 mm, bumper 7.5 mm                       (this CAD)
  force                  0.42 N at first touch, +0.144 N per mm            (QA Technology 100-40 standard spring, index)
Cases: the mat as a plane (the trusted model) and as the 5 mm height field (the model that left the bumper 2.7 to 6.0 mm
up in NEST_SIM.md 2.7). 3 mat frictions x 4 seeds each. No tip friction, rigid mat, as in NEST_SIM.md.

  NEST_SCRATCH=<scratch with model/> PYTHONDONTWRITEBYTECODE=1 python3 pins_sit_check.py     -> pins_sit_check.json
"""
import json
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(os.path.dirname(HERE), "sim")
sys.path.insert(0, SIM)
PROUD = dict(seat=0.0030, bump=0.0075)
F0, K = 0.42, (1.58 - 0.42) / 8.05e-3          # N, N per m
CASES = {"chosen pins, mat as a plane": dict(), "chosen pins, mat as height field": dict(surface="field")}


def patch():
    import mujoco
    import nestlib as NL
    NL.PIN_L = dict(PROUD)

    def pins(self, apply=False):
        dd = self.data
        if apply:
            dd.qfrc_applied[:] = 0
        if self.pin_body is None:
            return {}
        R = dd.xmat[self.trunk].reshape(3, 3)
        p = dd.xpos[self.trunk]
        A = R @ self.pin_axis
        out = {}
        for nm, pb in self.pin_body.items():
            Lp = PROUD[nm[:4]]
            P = p + R @ np.array(pb)
            if A[2] > -0.3:
                out[nm] = dict(xy=[float(P[0]), float(P[1])], comp=0.0, F=0.0)
                continue
            h = 0.0
            for _ in range(2):
                s = (P[2] - h) / (-A[2])
                tip = P + A * s
                h = NL.MAT_H if (self.has_mat and NL.on_mat(tip[0], tip[1])) else 0.0
            s = (P[2] - h) / (-A[2])
            tip = P + A * s
            comp = float(np.clip(Lp - s, 0.0, Lp))
            F = (F0 + K * comp) if (Lp - s) > 0 else 0.0
            if apply and self.pins_on and F > 0:
                mujoco.mj_applyFT(self.model, dd, np.array([0, 0, F]), np.zeros(3), np.array([tip[0], tip[1], h]), self.trunk, dd.qfrc_applied)
            out[nm] = dict(xy=[float(tip[0]), float(tip[1])], comp=comp, F=float(F), gap=float(s))
        return out
    NL.Sim.pins = pins
    return NL


def job(a):
    name, mu, seed = a
    NL = patch()
    kw = dict(CASES[name])
    surf = kw.pop("surface", None)
    rng = np.random.default_rng(900 + seed)
    s = NL.Sim(seed=seed, x0=-0.126 + rng.uniform(-0.01, 0.01), y0=rng.uniform(-0.01, 0.01), yaw0=np.pi, mu_mat=mu, volt=7.2, wall=False, pins_on=True)
    if surf:
        s.force_surface = surf
    for _ in range(100):
        s.step((0, 0, 0))
    if s.fallen:
        return dict(case=name, mu=mu, seed=seed, start_artefact=True)
    s.settle()
    s.sit_down(t_off=10.0)
    acc, n = {}, 250
    for _ in range(n):
        s._phys()
        for k, v in s.contact_forces().items():
            acc[k] = acc.get(k, 0.0) + v / n
    pins = s.pins()
    p, z, up = s.trunk_pose()
    R = s.data.xmat[s.trunk].reshape(3, 3)
    out = dict(case=name, mu=mu, seed=seed, surface=s.sit_surface, fell=bool(s.fallen), contacts_N={k: round(v, 3) for k, v in acc.items() if v > 0.005},
               pins={k: dict(F=round(v["F"], 3), comp_mm=round(v["comp"] * 1000, 2), gap_mm=round(v.get("gap", 0) * 1000, 2)) for k, v in pins.items()},
               trunk_z_above_mat_mm=round((z - NL.MAT_H) * 1000, 2), pitch_deg=round(float(np.degrees(np.arcsin(np.clip(R[2, 0], -1, 1)))), 2),
               stops=s.joints_on_stops())
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
        S[c] = dict(n=len(rr), start_artefacts_dropped=sum(bool(r.get("start_artefact")) for r in R if r["case"] == c), falls=sum(r["fell"] for r in rr),
                    stood_up=sum(r["stood"] for r in rr),
                    seat_block_N=m_(g(lambda r: r["contacts_N"].get("sit_seat_trunk_assembly_1_collision", 0.0))),
                    soles_N=m_(g(lambda r: r["contacts_N"].get("left_foot_bottom_tpu", 0.0) + r["contacts_N"].get("right_foot_bottom_tpu", 0.0))),
                    seat_pin_N=m_(g(lambda r: 0.5 * (r["pins"]["seat_L"]["F"] + r["pins"]["seat_R"]["F"]))),
                    bump_pin_N=m_(g(lambda r: 0.5 * (r["pins"]["bump_L"]["F"] + r["pins"]["bump_R"]["F"]))),
                    total_pin_N=m_(g(lambda r: sum(v["F"] for v in r["pins"].values()))),
                    seat_pin_comp_mm=m_(g(lambda r: 0.5 * (r["pins"]["seat_L"]["comp_mm"] + r["pins"]["seat_R"]["comp_mm"]))),
                    bump_pin_comp_mm=m_(g(lambda r: 0.5 * (r["pins"]["bump_L"]["comp_mm"] + r["pins"]["bump_R"]["comp_mm"]))),
                    seat_block_lift_mm=m_(g(lambda r: 0.5 * (r["pins"]["seat_L"]["gap_mm"] + r["pins"]["seat_R"]["gap_mm"]))),
                    bumper_gap_mm=m_(g(lambda r: 0.5 * (r["pins"]["bump_L"]["gap_mm"] + r["pins"]["bump_R"]["gap_mm"]))),
                    min_bump_pin_comp_mm=round(float(min(min(r["pins"]["bump_L"]["comp_mm"], r["pins"]["bump_R"]["comp_mm"]) for r in rr)), 2),
                    max_bump_pin_comp_mm=round(float(max(max(r["pins"]["bump_L"]["comp_mm"], r["pins"]["bump_R"]["comp_mm"]) for r in rr)), 2),
                    pitch_deg=m_(g(lambda r: r["pitch_deg"])), joints_on_stops=m_(g(lambda r: len(r["stops"]))),
                    all_4_pins_touch=sum(all(v["F"] > 0 for v in r["pins"].values()) for r in rr))
        print(c, json.dumps(S[c]))
    json.dump(dict(label="sim pass only", note="[mean, min, max] over the sits (3 mat frictions x 4 seeds, start artefacts dropped); harness sim/nestlib.py, only the pin model replaced",
                   pin_model=dict(F_first_touch_N=F0, N_per_mm=round(K / 1000, 4), proud_mm={k: v * 1000 for k, v in PROUD.items()}), summary=S, runs=R),
              open(os.path.join(HERE, "pins_sit_check.json"), "w"), indent=1)
