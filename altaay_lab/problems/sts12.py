#!/usr/bin/env python3
"""12 V STS3215 (ST-3215-C018) on a 3S P45B pack, same em_twin sheet walk.

The 7.4 V sheet constants stay in servo_sts3215.py. This script sets the 12 V
stall, the 12 V stall current, and the no-load speed for the duration of the
run, and it feeds the two voltage sources as 1.5 cells each so the pack is 3S.
The BEC set point is raised above the pack so the servos see the pack minus the
existing dropout, not 7.2 V.

Sim pass only. Nothing is bought.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(LAB, "twin", "electromech"))
sys.path.insert(0, os.path.join(LAB, "sim"))
os.environ.setdefault("TWIN_EM_SCRATCH", os.path.join(__import__("tempfile").gettempdir(), "twin_em"))

import em_twin as ET  # noqa: E402
import p45b  # noqa: E402
import servo_sts3215 as SV  # noqa: E402

# Feetech product page for ST-3215-C018, read 2026-11-12:
# https://www.feetech.cn/en/525603
# stall 30 kg.cm at 12 V, stall current 2.7 A at 12 V, no-load 0.222 s/60 deg at 12 V,
# no-load current 180 mA at 12 V, weight 55 +/- 1 g, operating range printed as 4-14 V.
KGFCM = 0.0980665
TAU_12 = 30.0 * KGFCM
I_STALL_12 = 2.7
V_12 = 12.0
W0_12 = (np.pi / 3.0) / 0.222
# The sheet mode scales damping with torque, which keeps the BAM no-load speed.
# Extra damping puts that speed on the 12 V sheet. Same 0.068 and 0.56 the servo file uses.
W0_BAM = (SV.TAU_MAX_TRAIN - 0.068) / 0.56
SPEED_K = W0_BAM / W0_12

SV.TAU_SHEET = TAU_12
SV.SHEET_SCALE = TAU_12 / SV.TAU_MAX_TRAIN
SV.V_TRAIN = V_12
SV.I_STALL_SHEET = I_STALL_12
SV.KT_SHEET = TAU_12 / I_STALL_12
SV.R_SHEET = V_12 / I_STALL_12

_INIT = SV.ServoBank.__init__


def _init(self, model, mode="bam", i_q=SV.I_Q, v_uvp=SV.V_UVP):
    _INIT(self, model, mode=mode, i_q=i_q, v_uvp=v_uvp)
    if mode == "sheet":
        self.m.dof_damping[self.dadr] *= SPEED_K
        self.m.dof_frictionloss[self.dadr] *= SPEED_K


SV.ServoBank.__init__ = _init


class Pack3S(p45b.P45B):
    """Two solver sources, each carrying 1.5 cells, so the string is 3S."""

    def v_cell(self, qm, i, dt=None):
        return 1.5 * p45b.P45B.v_cell(self, qm, i, dt)

    def slope(self, qm, i):
        return 1.5 * p45b.P45B.slope(self, qm, i)

    def ocv(self, qm):
        return 1.5 * p45b.P45B.ocv(self, qm)


ET.CELLS["p45b3"] = Pack3S

KNEES = ("left_knee", "right_knee")


def knees_of(r):
    names = list(r["names"])
    bins = r.get("_bins") or {}
    vmin = bins.get("V_min")
    t_end = (r.get("_binsp") or {}).get("t_end")
    if vmin is None or t_end is None or len(t_end) == 0:
        return {}
    fall = r["falls"][0] if r["falls"] else 1e9
    use = np.asarray(t_end) <= fall + 0.05
    if not np.any(use):
        use = np.ones(len(t_end), bool)
    out = {}
    for n in KNEES:
        i = names.index(n)
        out[n] = round(float(vmin[use, i].min()), 3)
    bp = r["_binsp"]
    out["i_pack_peak_A"] = round(float(np.asarray(bp["i_pack_max"])[use].max()), 3)
    out["v_bec_out_min_V"] = round(float(np.asarray(bp["v_bec_out_min"])[use].min()), 3)
    return out


def one(corner):
    r = ET.run(
        mass="ours", walk="backlash", cmd=(0.15, 0.0, 0.0), dur=20.0,
        supply="net", corner=corner, extra=dict(BEC_V=16.0),
        cell="p45b3", q0=0.0, servo_mode="sheet", guard=None,
        keep_full=False, stop_on_fall=True, t_stats=0.0, label="sts12",
    )
    return dict(
        label="sim pass only",
        corner=corner,
        fall_s=r["falls"] or "none",
        dur_s=r["dur_s"],
        gait=r["gait"],
        pack=r.get("pack"),
        knees=knees_of(r),
    )


def main():
    doc = dict(
        label="sim pass only",
        sheet=dict(
            part="ST-3215-C018",
            source="https://www.feetech.cn/en/525603",
            stall_kgcm=30.0,
            stall_Nm=round(TAU_12, 3),
            stall_A=I_STALL_12,
            no_load_s_per_60deg=0.222,
            no_load_rad_s=round(W0_12, 3),
            model_no_load_rad_s=round(W0_BAM / SPEED_K, 3),
            kt_Nm_per_A=round(TAU_12 / I_STALL_12, 4),
            r_stall_ohm=round(V_12 / I_STALL_12, 3),
            sheet_scale=round(TAU_12 / SV.TAU_MAX_TRAIN, 4),
            speed_damping_factor=round(SPEED_K, 4),
        ),
        corners={c: one(c) for c in ("typical", "high-side")},
    )
    path = os.path.join(HERE, "sts12.json")
    json.dump(doc, open(path, "w"), indent=1)
    print("wrote", path)
    for c, row in doc["corners"].items():
        print(c, "fall", row["fall_s"], "dur", row["dur_s"], "knees", row["knees"],
              "pack_i_max", (row["pack"] or {}).get("i_max"))


if __name__ == "__main__":
    main()
