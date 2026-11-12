#!/usr/bin/env python3
"""Fold-back charge time for the charger already drawn. Calc only.

Reused, not redesigned:
  altaay_lab/circuitry/check_charger.py     the MCP73213 numbers copied from DS20002190C
  altaay_lab/circuitry/CHARGER_BOARD.md     the 6.0 V fold-back question this answers
  altaay_lab/twin/electromech/p45b.py       the digitized P45B discharge figure, version 1.2

This is not a charge curve from the cell sheet. The sheet's standard charge is 4.5 A.
The voltage here is that discharge figure's zero-current end, plus I times the sheet's
15 mOhm DC pulse. A real charge sits above that voltage, so these hours are long.

No new part and no new board. Run from the repo root:
  python3 altaay_lab/problems/foldback.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(LAB, "twin", "electromech"))
sys.path.insert(0, os.path.join(LAB, "circuitry"))

import check_charger as C  # noqa: E402
from p45b import P45B  # noqa: E402

# Sheet DC pulse, cited in p45b.py from the P45B sheet, version 1.2. Not the figure's slope.
R_DC_OHM = 0.015
PRE_FRAC = 0.10
PRE_TIMER_H = 32.0 / 60.0
CELL = P45B()


def i_and_v(q_mah, ireg_a, pmax_w, r_ohm, vpth_v):
    """One operating point. Returns amps, pack volts, and which limit set the current."""
    ocv = CELL.ocv(q_mah)
    i_pre = PRE_FRAC * ireg_a
    v_pre = 2.0 * (ocv + i_pre * r_ohm)
    # The chip picks precondition from the terminal it sees at the small current.
    # A fast-charge current is not flowing yet, so it cannot lift the pin over the line.
    if v_pre < vpth_v:
        return i_pre, v_pre, "precondition"
    i = ireg_a
    limit = "program"
    for _ in range(12):
        vpack = 2.0 * (ocv + i * r_ohm)
        if vpack < vpth_v:
            i = PRE_FRAC * ireg_a
            limit = "precondition"
            vpack = 2.0 * (ocv + i * r_ohm)
            break
        head = C.NEST_V - vpack
        ith = pmax_w / head if head > 0.05 else 0.0
        icv = max(0.0, (C.VREG_TYP_V / 2.0 - ocv) / r_ohm)
        i2 = min(ireg_a, ith, icv)
        if i2 == ireg_a:
            limit = "program"
        elif i2 == ith:
            limit = "foldback"
        else:
            limit = "taper"
        if abs(i2 - i) < 1e-4:
            i = i2
            break
        i = i2
    return i, 2.0 * (ocv + i * r_ohm), limit


def integrate(q_start, ireg_a, pmax_w, r_ohm, vpth_v, dq=5.0):
    """Walk q down toward 0 mAh. dq is mAh per step. Returns hours and a few marks."""
    q = float(q_start)
    t_h = 0.0
    t_pre = 0.0
    pre_fault = False
    seen = {}
    while q > 0.5:
        step = min(dq, q)
        i, v, limit = i_and_v(q - 0.5 * step, ireg_a, pmax_w, r_ohm, vpth_v)
        if i < 1e-4:
            break
        dt = (step / 1000.0) / i
        t_h += dt
        if limit == "precondition":
            t_pre += dt
            if t_pre > PRE_TIMER_H and not pre_fault:
                pre_fault = True
        if limit == "taper" and i <= PRE_FRAC * ireg_a:
            break
        q -= step
        if int(round(v * 10)) not in seen and limit != "precondition":
            seen[int(round(v * 10))] = (round(t_h, 3), round(i, 3), limit)
    i_end, v_end, lim_end = i_and_v(max(q, 0.0), ireg_a, pmax_w, r_ohm, vpth_v)
    return dict(
        hours=t_h,
        pre_h=t_pre,
        pre_fault=pre_fault,
        q_left_mah=q,
        v_end=v_end,
        i_end=i_end,
        limit_end=lim_end,
        marks=seen,
    )


def main():
    cell = CELL
    print("figure q_end_mAh %.1f  q_cap_1C_mAh %.1f  ocv_at_0_V %.3f" % (
        cell.q_end, cell.q_cap, cell.ocv(0.0)))
    print("label: calc only, discharge figure plus 15 mOhm, not a charge curve")

    # The published constant-current bound, so this file and CHARGER_BOARD.md stay on the same sum.
    pmax32 = (C.T_REG_C - 32.0) / C.THETA_JA
    i6 = pmax32 / (C.NEST_V - 6.0)
    cc_h = C.CELL_AH / (C.IREG_SPEC_TYP_MA / 1000.0)
    tail_h = C.CELL_CHARGE_H - (C.CELL_AH / C.CELL_CHARGE_A)
    frozen = C.CELL_AH / i6 + tail_h
    print("frozen 6.0 V foldback %.3f A, 4.5 Ah plus 0.50 h tail = %.2f h (the 13 h line)" % (i6, frozen))
    print("1.00 A nameplate fill %.2f h plus %.2f h tail = %.2f h" % (cc_h, tail_h, cc_h + tail_h))

    starts = []
    for name, vcell in (("walk stop 3.30 V/cell", 3.30),
                        ("nominal 3.60 V/cell", 3.60),
                        ("charger 6.0 V pack", 3.00),
                        ("figure low end", 2.80)):
        starts.append((name, vcell, cell.q_at_ocv(vcell)))

    vpth = C.VPTH_RATIO_TYP * C.VREG_TYP_V
    rows = []
    for tamb in (25.0, 32.0):
        pmax = (C.T_REG_C - tamb) / C.THETA_JA
        for ireg_ma in (C.IREG_SPEC_MIN_MA, C.IREG_SPEC_TYP_MA, C.IREG_SPEC_MAX_MA):
            ireg = ireg_ma / 1000.0
            for name, vcell, q in starts:
                r = integrate(q, ireg, pmax, R_DC_OHM, vpth)
                r.update(tamb=tamb, ireg_a=ireg, pmax_w=pmax, name=name,
                         vcell=vcell, q_mah=q, vpth=vpth)
                rows.append(r)
                flag = " PRECONDITION TIMER" if r["pre_fault"] else ""
                print("Tamb %g C  Ireg %.2f A  %-22s  q %.0f mAh  %.2f h  end %.2f V %s%s" % (
                    tamb, ireg, name, q, r["hours"], r["v_end"], r["limit_end"], flag))

    # How warm the cited board can be before the 6.6 h max is missed, from the walk stop, at 1.00 A.
    q_walk = cell.q_at_ocv(3.30)
    print("theta sweep, walk stop, Ireg 1.00 A, 32 C room is the reference power shape")
    for theta in (40, 50, 62, 80, 100, 120, 150):
        # Hold the 32 C room and vary theta, which is the open trunk question.
        pmax = (C.T_REG_C - 32.0) / theta
        r = integrate(q_walk, 1.0, pmax, R_DC_OHM, vpth)
        print("  theta %g C/W  Pmax %.3f W  %.2f h  %s 6.6 h  %s 5.4 h" % (
            theta, pmax, r["hours"],
            "inside" if r["hours"] < C.TIMER_MAX_H else "past",
            "inside" if r["hours"] < C.TIMER_MIN_H else "past"))

    # Sanity: the frozen current matches the charger note's 0.359 A.
    if abs(i6 - 0.359) > 0.002:
        raise SystemExit("foldback current at 6.0 V and 32 C is %.3f A, charger note is 0.359 A" % i6)
    if abs(frozen - 13.0) > 0.3:
        raise SystemExit("frozen hours %.2f are not the note's about 13 h" % frozen)
    print("sanity: 0.359 A and about 13 h match CHARGER_BOARD.md")
    return rows


if __name__ == "__main__":
    main()
