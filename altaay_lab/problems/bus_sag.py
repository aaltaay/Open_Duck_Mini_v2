#!/usr/bin/env python3
"""Free electrical changes on the sheet-stall walk. sim pass only.

Reused, not rewritten:
  twin/electromech/em_twin.py run()
  twin/electromech/power_net.py and sim/power_fix.py option ab
  wiring/netlist.yaml cuts, and the route-worst lengths already written on those wires
  sim/power_path_sim.py copper table and the 22 AWG kit-lead option
  twin/electromech/p45b.py and the cited 15 mOhm / 7 mOhm lines
  twin/electrical/ELECTRICAL_TWIN.md 470 uF class used there as an assumption

The Mini-SPOX terminal cited in the harness note takes 22 to 28 AWG. A 16 AWG
plug is not that part. The 16 AWG case below is the long run in 16 AWG (already
a gauge on the duck) plus a 50 mm 22 AWG tail for that terminal.

  python3 altaay_lab/problems/bus_sag.py
Writes bus_sag.json next to this file.
"""
import copy
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
EM = os.path.join(LAB, "twin", "electromech")
SIM = os.path.join(LAB, "sim")
sys.path.insert(0, EM)
sys.path.insert(0, SIM)
os.environ.setdefault("TWIN_EM_SCRATCH", os.path.join(__import__("tempfile").gettempdir(), "twin_em"))

import em_twin as ET  # noqa: E402
import p45b  # noqa: E402
import power_fix as PF  # noqa: E402
import power_net as PN  # noqa: E402
import power_path_sim as PPS  # noqa: E402

# Route worst, from the netlist wire source line (cut = route worst + slack).
# SP4: 348 mm. SP5: 377 mm. Cited there, not a new route.
ROUTE_WORST_MM = {"L": 348.0, "R": 377.0}
TAIL_22_MM = 50.0
# 14 x 470 uF is the assumption already in ELECTRICAL_TWIN.md for the servo bus.
# One of those at each knee is the bulk cap tested here. ESR 0 is the best case
# for that capacitor, not a measured part.
CAP_F = 470e-6
DT = 0.002
KNEES = ("left_knee", "right_knee")


def copper(awg, mm):
    return PPS.CU[awg] * mm / 1000.0


def fresh_lengths():
    d = PPS.netlist_lengths()
    # drop the file hash so the json stays small if a caller prints d
    return d


def apply_lengths(d):
    PF._NET["v"] = d


def shorter(d):
    for side, mm in ROUTE_WORST_MM.items():
        awg = d["feeds"][side]["v"][0]
        d["feeds"][side]["v"] = (awg, mm)
        d["feeds"][side]["g"] = (awg, mm)


def thicker_feed(d):
    """Long run in 16 AWG, 50 mm of 22 AWG left for the cited 22-to-28 terminal."""
    for side in ("L", "R"):
        cut = float(d["feeds"][side]["v"][1])
        route = max(cut - TAIL_22_MM, 0.0)
        r = copper(16, route) + copper(22, TAIL_22_MM)
        eq = r / PPS.CU[16] * 1000.0
        d["feeds"][side]["v"] = (16, eq)
        d["feeds"][side]["g"] = (16, eq)


def knee_star(d):
    """Land the existing second feed on the knee, at the knee-injection length already in power_fix."""
    for side, name in (("L", "left_knee"), ("R", "right_knee")):
        mm = float(PF.INJ_KNEE_MM[side])
        awg = d["feeds"][side]["v"][0]
        d["feeds"][side]["servo"] = name
        d["feeds"][side]["v"] = (awg, mm)
        d["feeds"][side]["g"] = (awg, mm)


def chain_ohms(kit_awg, contact):
    """Copper plus contacts from the splice to the knee, one conductor, no parallel feed. calc only."""
    d = fresh_lengths()
    r = copper(*d["sp_v"]["L"]) + contact
    # hops before the knee: indices 0, 1, 2 are yaw, roll, pitch. The knee hop is index 3.
    for mm in d["hop_mm"]["L"][:3]:
        r += copper(kit_awg, mm) + 2 * contact + PPS.P["R_servo_pcb"]
    return r


class _Cap(object):
    """Backward-Euler companion of a shunt capacitor at each knee port.

    i = (C/dt) * (v - v_prev). The first step stores the solved port voltage
    and draws nothing, so the part is already charged and there is no inrush.
    A smaller C is a smaller conductance. ESR is 0.
    """

    def __init__(self, farads):
        self.C = farads
        self.v_prev = None
        self.idx = None

    def wrap(self, servo_current):
        cap = self
        g = cap.C / DT

        def wrapped(vs):
            i = np.array(servo_current(vs), float)
            if cap.idx is None or cap.v_prev is None:
                return i
            vs = np.asarray(vs, float)
            i = i.copy()
            i[cap.idx] += g * (vs[cap.idx] - cap.v_prev)
            return i

        def slope(vs):
            cur, d = servo_current.slope(vs)
            d = np.array(d, float).copy()
            if cap.idx is not None and cap.v_prev is not None:
                for k in cap.idx:
                    d[k] += g
            return wrapped(vs), d

        wrapped.slope = slope
        return wrapped


_SOLVE = PN.Net.solve
_CAP = _Cap(0.0)


def _solve(self, servo_current, vcell=None, qm=None, tol=1e-7, maxit=40):
    if _CAP.C <= 0:
        return _SOLVE(self, servo_current, vcell=vcell, qm=qm, tol=tol, maxit=maxit)
    if _CAP.idx is None:
        _CAP.idx = [PN.NAMES.index(n) for n in KNEES]
    wrapped = _CAP.wrap(servo_current)
    y = _SOLVE(self, wrapped, vcell=vcell, qm=qm, tol=tol, maxit=maxit)
    _CAP.v_prev = np.array(y[self.osv], float)[_CAP.idx].copy()
    return y


PN.Net.solve = _solve


def knees_of(r):
    names = list(r["names"])
    bins = r.get("_bins") or {}
    vmin = bins.get("V_min")
    vmean = bins.get("V_mean")
    sat = bins.get("sat_frac")
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
        out[n] = dict(
            V_min=round(float(vmin[use, i].min()), 3),
            V_mean=round(float(vmean[use, i].mean()), 3),
            sat_mean=round(float(sat[use, i].mean()), 3),
        )
    return out


def one(name, corner, mutate=None, extra=None, cap=0.0, q0=0.0, cell_mode="steady"):
    d = fresh_lengths()
    if mutate:
        mutate(d)
    apply_lengths(d)
    _CAP.C = cap
    _CAP.v_prev = None
    _CAP.idx = None
    print("RUN", name, corner, flush=True)
    r = ET.run(
        mass="ours", walk="backlash", cmd=(0.15, 0.0, 0.0), dur=20.0,
        supply="net", corner=corner, extra=extra, cell="p45b", q0=q0,
        servo_mode="sheet", cell_mode=cell_mode, guard=None, keep_full=False,
        stop_on_fall=True, t_stats=0.0, label=name,
    )
    g = r["gait"]
    row = dict(
        name=name, corner=corner, label="sim pass only",
        falls_s=r["falls"], dur_s=r["dur_s"],
        track_lin=None if g.get("track_lin") is None else round(g["track_lin"], 3),
        vx_m_s=None if g.get("vx") is None else round(g["vx"], 4),
        knees=knees_of(r),
        pack=r.get("pack"),
        wall_s=r["wall_s"],
    )
    print(" ", row["falls_s"] or "none", row["knees"], flush=True)
    return row


def sag_table():
    """2S terminal sag on the discharge figure. calc only."""
    c = p45b.P45B()
    rows = []
    for label, v in (("full, ocv at 0 mAh", None), ("end, ocv 3.30 V/cell", 3.30)):
        q = 0.0 if v is None else c.q_at_ocv(v)
        ocv = c.ocv(q)
        for i in (2.0, 5.0, 10.0):
            vt = c.v_steady(q, i)
            rows.append(dict(
                where=label, q_mAh=round(q, 1), i_pack_A=i,
                ocv_cell_V=round(ocv, 3), terminal_cell_V=round(vt, 3),
                sag_pack_V=round(2.0 * (ocv - vt), 3),
                label="calc only, discharge figure, not a pulse measurement",
            ))
    return rows


def main():
    hops_typ = chain_ohms(24, 0.005)
    hops_hi = chain_ohms(26, 0.020)
    base = fresh_lengths()
    feed_22 = {s: copper(*base["feeds"][s]["v"]) for s in ("L", "R")}
    feed_short = {s: copper(22, ROUTE_WORST_MM[s]) for s in ("L", "R")}
    feed_16 = {}
    for s in ("L", "R"):
        cut = float(base["feeds"][s]["v"][1])
        route = max(cut - TAIL_22_MM, 0.0)
        feed_16[s] = copper(16, route) + copper(22, TAIL_22_MM)
    info = dict(
        chain_to_knee_one_conductor_ohm=dict(typical_24awg_5mohm=round(hops_typ, 4), high_side_26awg_20mohm=round(hops_hi, 4)),
        feed_copper_ohm=dict(cut_22awg={s: round(v, 4) for s, v in feed_22.items()},
                             route_worst_22awg={s: round(v, 4) for s, v in feed_short.items()},
                             awg16_plus_50mm_22={s: round(v, 4) for s, v in feed_16.items()}),
        cap_F=CAP_F,
        cap_tau_s_at_0p5_ohm=round(0.5 * CAP_F, 6),
        cap_note="470 uF at each knee port, ESR 0. Backward Euler: i = (C/dt)*(v - v_prev). The first step stores the port voltage and draws nothing. The 0.235 ms figure is R C at 0.5 ohm, not the model.",
        inj_knee_mm=PF.INJ_KNEE_MM,
    )
    print(json.dumps(info, indent=1), flush=True)
    rows = []
    corners = ("typical", "high-side")
    cases = [
        ("as built", None, None, 0.0, 0.0, "steady"),
        ("hops 22 AWG", None, dict(kit_awg=22), 0.0, 0.0, "steady"),
        ("feeds at route worst", shorter, None, 0.0, 0.0, "steady"),
        ("16 AWG feed plus 22 AWG tail", thicker_feed, None, 0.0, 0.0, "steady"),
        ("star feed to the knee", knee_star, None, 0.0, 0.0, "steady"),
        ("470 uF at each knee", None, None, CAP_F, 0.0, "steady"),
        ("cell AC 7 mOhm", None, None, 0.0, 0.0, "ac"),
        ("end of discharge", None, None, 0.0, p45b.P45B().q_at_ocv(3.30), "steady"),
    ]

    def combo(d):
        knee_star(d)
        thicker_feed(d)

    cases.append(("hops 22 plus short 16 AWG knee star", combo, dict(kit_awg=22), 0.0, 0.0, "steady"))
    for name, mut, extra, cap, q0, mode in cases:
        for corner in corners:
            rows.append(one(name, corner, mut, extra, cap, q0, mode))
    doc = dict(label="sim pass only", info=info, sag=sag_table(), rows=rows)
    path = os.path.join(HERE, "bus_sag.json")
    json.dump(doc, open(path, "w"), indent=1)
    print("wrote", path, flush=True)


if __name__ == "__main__":
    main()
