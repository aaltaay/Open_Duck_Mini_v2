#!/usr/bin/env python3
"""One blind dock that stacks three studies that already exist. sim pass only.

Reused, not redesigned:
  twin/dock/closeup/close_run.py          wall card, mode "marker". Same 540 seeds,
                                          same walk law, same camera rule.
  twin/dock/nest/sim/nestlib.py           the nest world and the sit.
  twin/dock/nest/sim/v3                   two 1 mm steps, aim 20 mm at 7.2 V.
  twin/dock/nest/cad/nestcad_lib.py       rim depth 50 mm, felt ends 6 mm from the wall.
                                          The older sim rim is 72 mm and the felt ended 22 mm out.
  feet/deep/harness.py                    soft contact solref 0.05 1 and solimp 0.6 0.9 0.01.
                                          That file's soft floor is not a felt grade.
  twin/dock/flush/FLUSH_CONTACTS.md       the flush window this scores, section 6.
  twin/dock/closeup/score.py              the same box test.

The felt grade stays the contact twin's BLOCKER. Nothing here is a new mat or a new card.

  PYTHONDONTWRITEBYTECODE=1 python3 dock_sim.py marker 30
  python3 dock_sim.py sink
NEST_SCRATCH and ODM_PLAYGROUND are the ones the nest sim already uses.
"""
import os
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
CLOSE = os.path.join(LAB, "twin", "dock", "closeup")
CAD = os.path.join(LAB, "twin", "dock", "nest", "cad")
sys.path.insert(0, CLOSE)
sys.path.insert(0, CAD)

import nestcad_lib as NESTCAD  # noqa: E402
import close_run as CR  # noqa: E402
import nestlib as NL  # noqa: E402

# Feet harness, soft=True. Cited from that file, not refit.
SOFT_SOLREF = (0.05, 1.0)
SOFT_SOLIMP = (0.6, 0.9, 0.01, 0.5, 2.0)


def apply_cad():
    """Put the published nest CAD sizes into the existing sim globals."""
    rim_m = NESTCAD.RIM["depth"] / 1000.0
    back_m = NESTCAD.MAT_BACK / 1000.0
    top_m = NESTCAD.TOP_R / 1000.0
    tread_m = (NESTCAD.BASE_R - NESTCAD.TOP_R) / 1000.0
    if abs(NL.MAT_R - top_m) > 1e-6 or abs(NL.TREAD - tread_m) > 1e-6:
        raise SystemExit("nest sim mat radii are not the CAD radii")
    if abs(NL.RIM_H - NESTCAD.RIM["height"] / 1000.0) > 1e-6:
        raise SystemExit("nest sim rim height is not the CAD height")
    if abs(NL.RIM_HALF - NESTCAD.RIM["half_len"] / 1000.0) > 1e-6:
        raise SystemExit("nest sim rim length is not the CAD length")
    NL.RIM_D1 = rim_m
    NL.MAT_BACK = back_m


def _soften(sim):
    md = sim.model
    for g in (getattr(sim, "g_mat", -1), getattr(sim, "g_matplane", -1)):
        if g is None or g < 0:
            continue
        md.geom_solref[g] = SOFT_SOLREF
        md.geom_solimp[g] = SOFT_SOLIMP


_orig = NL.Sim.__init__


def _init(self, *a, **k):
    _orig(self, *a, **k)
    _soften(self)


NL.Sim.__init__ = _init
apply_cad()


def sink():
    """How far one sole sinks on this contact. sim pass only. Not a felt measurement."""
    import numpy as np
    os.environ["NEST_EDGE"] = "steps"
    os.environ["NEST_WALL_X"] = "0.190"
    NL.WALL_X = 0.190
    s = NL.Sim(seed=0, x0=-0.05, y0=0.0, yaw0=np.pi, mu_mat=0.8, mu_floor=0.6, volt=7.2)
    s.policy_on = False
    qa = np.array(s.m.actuator_joint_qpos_addr).ravel()
    s.data.ctrl[:] = np.array(s.data.qpos[qa], float).ravel()
    for _ in range(500):
        s._phys()
    pen = []
    if s.data.ncon:
        for i in range(s.data.ncon):
            dist = float(s.data.contact[i].dist)
            if dist < 0:
                pen.append(-dist * 1000.0)
    sole_z = [float(s.data.xpos[b][2]) for b in s.feet]
    print("soft contact reused from the feet harness")
    print("sole body z m", [round(z, 4) for z in sole_z])
    print("deepest contact penetration mm", None if not pen else round(max(pen), 3))
    print("mat thickness mm", NL.MAT_H * 1000.0, "CAD felt stack mm", 2.0 * NESTCAD.FELT_T)
    print("label: sim pass only. Felt grade remains BLOCKER.")


def main():
    mode = sys.argv[1]
    if mode == "sink":
        sink()
        return
    n = int(sys.argv[2])
    only = int(sys.argv[3]) if len(sys.argv) > 3 else None
    if mode != "marker":
        raise SystemExit("mode is marker or sink")
    os.environ["NEST_EDGE"] = "steps"
    os.environ["NEST_WALL_X"] = "0.190"
    J = CR.configs(n, "marker", 0.190, 20.0, only)
    t = time.time()
    R = []
    jobs = int(os.environ.get("JOBS", "4"))
    from multiprocessing import Pool
    with Pool(jobs, maxtasksperchild=4) as p:
        for i, r in enumerate(p.imap_unordered(CR.job, J, chunksize=1)):
            R.append(r)
            if r.get("error"):
                print("ERR", r.get("cfg"), r["error"], flush=True)
            if (i + 1) % 20 == 0 or (i + 1) == len(J):
                print("marker", i + 1, "/", len(J), "%.0f s" % (time.time() - t), flush=True)
    R.sort(key=lambda r: r.get("cfg", {}).get("seed", 0))
    doc = dict(
        label="sim pass only",
        reused=[
            "twin/dock/closeup/close_run.py mode marker",
            "twin/dock/nest/cad/nestcad_lib.py rim 50 mm and felt back cut 6 mm",
            "twin/dock/nest/sim two 1 mm steps, aim 20 mm at 7.2 V, sun 190 mm",
            "feet/deep/harness.py soft solref 0.05 1, solimp 0.6 0.9 0.01",
            "twin/dock/flush/FLUSH_CONTACTS.md section 6 window",
        ],
        felt_grade="BLOCKER, contact twin. This solref is the feet harness soft floor, not a grade.",
        mode="marker",
        wall_x_m=0.190,
        aim_mm_right_at_7v2=20.0,
        edge="steps",
        rim_depth_mm=NESTCAD.RIM["depth"],
        mat_back_mm=NESTCAD.MAT_BACK,
        runs=R,
    )
    path = os.path.join(HERE, "dock_runs.json")
    import json
    json.dump(doc, open(path, "w"))
    print("wrote", len(R), path, "%.0f s" % (time.time() - t))


if __name__ == "__main__":
    main()
