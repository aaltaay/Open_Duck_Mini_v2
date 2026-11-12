#!/usr/bin/env python3
"""Where the knee-voltage dip goes, on one as-built sheet walk. sim pass only.

Reuses twin/electromech/em_twin.py and the as-built network. Records the solver
outputs and splits the drop at the sample where the left knee is lowest.
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
import power_fix as PF  # noqa: E402
import power_net as PN  # noqa: E402
import power_path_sim as PPS  # noqa: E402

LOG = []
_SOLVE = PN.Net.solve


def _solve(self, servo_current, vcell=None, qm=None, tol=1e-7, maxit=40):
    y = _SOLVE(self, servo_current, vcell=vcell, qm=qm, tol=tol, maxit=maxit)
    ocv = None
    if self.cell_model is not None and qm is not None:
        ocv = float(self.cell_model.ocv(qm))
    vs = y[self.osv]
    i_srv = np.array(servo_current(vs), float)
    row = dict(ocv=ocv, i_srv=i_srv)
    for n in self.out_names:
        row[n] = float(y[self.o[n]])
    LOG.append(row)
    return y


PN.Net.solve = _solve


def edges(corner):
    p = PF.params(corner, PF.OPTIONS["ab"], PF.CORNERS[corner])
    plus, loads, _ = PF.servo_net(PF.OPTIONS["ab"], p)
    minus = PF.minus_edges(PF.OPTIONS["ab"], p)
    return p, plus, minus, loads


def budget(corner):
    LOG.clear()
    r = ET.run(
        mass="ours", walk="backlash", cmd=(0.15, 0.0, 0.0), dur=8.0,
        supply="net", corner=corner, cell="p45b", q0=0.0, servo_mode="sheet",
        guard=None, keep_full=False, stop_on_fall=True, t_stats=0.0, label="budget",
    )
    names = PN.NAMES
    ik = names.index("left_knee")
    vk = np.array([row["v_left_knee"] for row in LOG])
    j = int(vk.argmin())
    s = LOG[j]
    p, plus, minus, loads = edges(corner)
    pe = {e[0]: e[3] for e in plus}
    me = {e[0]: e[3] for e in minus}
    # currents at that sample
    def I(name):
        return s.get("i_" + name)

    bus_i = np.array([row["i_bout"] for row in LOG])
    pack_i = np.array([row["i_pack"] for row in LOG])
    out = dict(
        label="sim pass only",
        corner=corner,
        fall_s=r["falls"],
        n_samples=len(LOG),
        at_left_knee_min=dict(
            t_s=round((j + 1) * 0.002, 3),
            ocv_cell_V=None if s["ocv"] is None else round(s["ocv"], 3),
            ocv_pack_V=None if s["ocv"] is None else round(2 * s["ocv"], 3),
            v_pack_V=round(s["v_pack"], 3),
            v_bus_V=round(s["v_bus"], 3),
            v_bec_in_V=round(s["v_bin"], 3),
            v_bec_out_V=round(s["v_out"], 3),
            v_left_knee_V=round(s["v_left_knee"], 3),
            v_right_knee_V=round(s["v_right_knee"], 3),
            i_pack_A=round(s["i_pack"], 3),
            i_bus_A=round(s["i_bout"], 3),
            i_left_knee_A=round(float(s["i_srv"][ik]), 3),
        ),
        peaks=dict(
            i_pack_A=round(float(pack_i.max()), 3),
            i_bus_A=round(float(bus_i.max()), 3),
            label="sim pass only, maximum sample on this walk up to the fall",
        ),
        resistors_ohm=dict(
            note="plus-side edge resistance as the as-built net builds it",
            lead=round(pe["lead"], 4),
            sp_L=round(pe["sp_L"], 4),
            hop_left_hip_roll=round(pe["hop_left_hip_roll"], 4),
            hop_left_hip_pitch=round(pe["hop_left_hip_pitch"], 4),
            hop_left_knee=round(pe["hop_left_knee"], 4),
            inj_L=round(pe.get("inj_L", 0), 4),
            ground_lead=round(me["lead"], 4),
            ground_sp_L=round(me.get("sp_L", 0), 4),
        ),
        assumptions=dict(
            R_contact_ohm=p["R_contact"],
            R_holder_ohm=p["R_holder"],
            R_servo_pcb_ohm=p["R_servo_pcb"],
            kit_awg=p["kit_awg"],
            BEC_V=p["BEC_V"],
            BEC_DROP=p["BEC_DROP"],
            BEC_EFF=p["BEC_EFF"],
            R_cell_in_net_ohm="1e-9 when the P45B model supplies the terminal volts",
        ),
        branch_A={k: round(I(k), 3) for k in (
            "lead", "sp_L", "hop_left_hip_roll", "hop_left_hip_pitch", "hop_left_knee", "inj_L", "n_lead", "n_sp_L")},
    )
    # drops that are differences of recorded voltages
    a = out["at_left_knee_min"]
    out["drops_V"] = dict(
        cell_ocv_to_pack_terminal=round(a["ocv_pack_V"] - a["v_pack_V"], 3),
        pack_terminal_to_switched_bus=round(a["v_pack_V"] - a["v_bus_V"], 3),
        switched_bus_to_bec_out=round(a["v_bus_V"] - a["v_bec_out_V"], 3),
        bec_out_to_left_knee=round(a["v_bec_out_V"] - a["v_left_knee_V"], 3),
        seven_point_four_to_knee=round(7.4 - a["v_left_knee_V"], 3),
    )
    return out


def stripped(corner):
    """Holder, fuse, and XT30 near zero, dropout 0, efficiency 1. Same sheet walk."""
    extra = dict(R_holder=1e-4, R_fuse=1e-4, R_xt30=1e-4, BEC_DROP=0.0, BEC_EFF=1.0)
    r = ET.run(
        mass="ours", walk="backlash", cmd=(0.15, 0.0, 0.0), dur=20.0,
        supply="net", corner=corner, extra=extra, cell="p45b", q0=0.0,
        servo_mode="sheet", guard=None, keep_full=False, stop_on_fall=True,
        t_stats=0.0, label="strip",
    )
    pk = r.get("pack") or {}
    return dict(
        label="sim pass only",
        corner=corner,
        fall_s=r["falls"],
        i_pack_max_A=pk.get("i_max"),
        bus_min_V=pk.get("bus_min"),
        bec_out_min_V=pk.get("bec_out_min"),
    )


def main():
    doc = dict(
        label="sim pass only",
        corners={c: budget(c) for c in ("typical", "high-side")},
        unmeasured_drops_removed={c: stripped(c) for c in ("typical", "high-side")},
    )
    path = os.path.join(HERE, "volt_budget.json")
    json.dump(doc, open(path, "w"), indent=1)
    print("wrote", path)


if __name__ == "__main__":
    main()
