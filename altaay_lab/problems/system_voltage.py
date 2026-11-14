#!/usr/bin/env python3
"""System voltage and pack comparison. Calc first, then the run C walk on the short list.

The calc does not retrain and does not need the playground. The walk reuses em_twin and the
12 V sheet patch in problems/sts12.py. It does not edit that file, and it does not set the
Castle output to 16 V.

Usage:
  python3 altaay_lab/problems/system_voltage.py calc
  ODM_PLAYGROUND=<Open_Duck_Playground at b9be205> python3 altaay_lab/problems/system_voltage.py sim

Outputs (repo paths, small JSON):
  altaay_lab/problems/system_voltage_calc.json
  altaay_lab/problems/system_voltage_sim.json
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(LAB, "twin", "electromech"))
sys.path.insert(0, os.path.join(LAB, "sim"))

import p30b  # noqa: E402
import p45b  # noqa: E402
import power_net as PN  # noqa: E402

KGFCM = 0.0980665
# Feetech ST-3215-C018 page, https://www.feetech.cn/en/525603
C018_TAU = 30.0 * KGFCM
C018_I = 2.7
C018_V = 12.0
C018_W0 = (math.pi / 3.0) / 0.222
C018_MASS_G = 55.0
# Feetech STS3215 C001 sheet lines already used in servo_sts3215.py
C001_TAU = 19.5 * KGFCM
C001_V = 7.4
C001_W0 = (math.pi / 3.0) / 0.192
# Feetech STS3250 page, SERVO_UPGRADE_OPTIONS.md [F5]
S3250_TAU = 50.0 * KGFCM
S3250_V = 12.0
S3250_W0 = (math.pi / 3.0) / 0.133
S3250_MASS_G = 74.5
# Robotis XM430-W350-T, shop page. Case does not match the duck horn.
XM_TAU = 4.10
XM_V = 12.0
XM_W0 = 46.0 * 2.0 * math.pi / 60.0

# Annealed copper, ohm/m, the table in sim/power_path_sim.py
CU = {16: 13.17e-3, 20: 33.31e-3, 22: 52.96e-3, 24: 84.22e-3, 26: 133.9e-3}

# Comparison current for the discharge tables. FIT3 records 5.144 A mean at 0.15 m/s
# on the old policy. 5.00 A is the round comparison point, calc only.
I_CMP = 5.0
# Items mass_budget.py seats on the BEC. The wire rail takes them off at that seat.
# 29.0 g is the user guide without wires. Leads, tape, and the two output splices are that file's lines.
BEC_BODY_G = 29.0
BEC_LEADS_G = 4.6
BEC_TAPE_G = 0.047 * 0.033 * 1.1e-3 * 0.8 * 1e6
BEC_SPLICE_G = 2 * 0.5
BEC_REMOVED_G = BEC_BODY_G + BEC_LEADS_G + BEC_TAPE_G + BEC_SPLICE_G
# Figure 10-4, chart read in twin/thermal/BQ24133_HEAT.md. AVCC 15 V, 3 cells, 1.00 A.
BQ_ETA_3S_15V = 0.929
P5 = 5.0
REG_EFF = 0.85
BEC_EFF = 0.85
BEC_DROP = 0.3

# Grown bay, BAY.md and FIT3. Two 22.2 mm sleeves.
BAY_Y_MM = 43.75
BAY_X_MM = 25.45          # -144.45 minus -119.0, the published section
SLEEVE_21700_MM = 22.2
CELL_CLEAR_MM = 0.25      # the radial clearance BAY.md uses on the P45B

CELLS = {
    "P45B": dict(
        name="Molicel INR-21700-P45B",
        source="https://www.molicel.com/wp-content/uploads/INR21700P45B_1.2_Product-Data-Sheet-of-INR-21700-P45B-80109.pdf",
        ah=4.5, wh=16.2, v_nom=3.6, v_chg=4.2, v_cut=2.5,
        i_cont=45.0, i_chg_std=4.5, i_chg_max=13.5,
        r_dc=0.015, r_ac=0.007, mass_g=70.0, dia_mm=21.55, h_mm=70.15,
        price=9.99, price_note="BOM line 6, out of stock 2026-11-04",
        curve="p45b", un38="product page lists a UN test report. The welded pack summary is not that report.",
    ),
    "P50B": dict(
        name="Molicel INR-21700-P50B",
        source="https://www.molicel.com/wp-content/uploads/Product-Data-Sheet-of-INR-21700-P50B-80122.pdf",
        ah=5.0, wh=18.0, v_nom=3.6, v_chg=4.2, v_cut=2.5,
        i_cont=60.0, i_chg_std=5.0, i_chg_max=25.0,
        r_dc=0.0128, r_ac=0.0065, mass_g=71.0, dia_mm=21.55, h_mm=70.15,
        price=11.99, price_note="BATTERY_STUDY.md, in stock 2026-11-04, same sleeve",
        curve=None, un38="product page lists a UN test report. The welded pack summary is not that report.",
    ),
    "P30B": dict(
        name="Molicel INR-18650-P30B",
        source="https://www.molicel.com/wp-content/uploads/Product-Data-Sheet-of-INR-18650-P30B-80111-2.pdf",
        ah=3.0, wh=10.8, v_nom=3.6, v_chg=4.2, v_cut=2.5,
        i_cont=30.0, i_chg_std=3.0, i_chg_max=9.0,
        r_dc=0.017, r_ac=0.008, mass_g=47.0, dia_mm=18.6, h_mm=65.2,
        price=8.99, price_note="BATTERY_STUDY.md, in stock 2026-11-04",
        curve="p30b",
        un38="https://www.18650batterystore.com/cdn/shop/files/Molicel-P30B-18650-UN38.3-test-report.pdf cell summary. The welded pack is a separate battery.",
    ),
    "50S": dict(
        name="Samsung 50S 21700",
        source="BATTERY_STUDY.md section 8.2, resistance not found on a sheet opened there",
        ah=5.0, wh=18.0, v_nom=3.6, v_chg=4.2, v_cut=2.5,
        i_cont=25.0, i_chg_std=None, i_chg_max=None,
        r_dc=None, r_ac=None, mass_g=72.0, dia_mm=21.55, h_mm=70.15,
        price=9.99, price_note="BATTERY_STUDY.md, in stock 2026-11-04. Diameter not re-opened: treated as the same 21700 sleeve.",
        curve=None, un38="BLOCKER. No test summary was opened for this cell in this pass.",
    ),
}

SERVOS = {
    "C001": dict(tau=C001_TAU, v=C001_V, w0=C001_W0, mass_g=55.0, i_stall=2.5,
                 v_min_page=4.0, v_max_page=7.4, v_min_alt=6.0, v_max_alt=7.4,
                 note="C001 sheet 6 to 7.4 V typical, input down to 4 V and the over-voltage line at 8 V in servo_sts3215.py"),
    "C018": dict(tau=C018_TAU, v=C018_V, w0=C018_W0, mass_g=C018_MASS_G, i_stall=C018_I,
                 v_min_page=4.0, v_max_page=14.0, v_min_alt=6.0, v_max_alt=12.6,
                 note="page 4 to 14 V adopted, Waveshare 6 to 12.6 V adopted, PDF 12.0 V only not adopted"),
    "STS3250": dict(tau=S3250_TAU, v=S3250_V, w0=S3250_W0, mass_g=S3250_MASS_G, i_stall=4.2,
                    v_min_page=6.0, v_max_page=12.0, v_min_alt=9.0, v_max_alt=12.6,
                    note="page 6 to 12 V and the wiki 9 to 12.6 V disagree. Both are cited in SERVO_UPGRADE_OPTIONS.md"),
}


def r3(x):
    if x is None:
        return None
    return round(float(x), 3)


def r2(x):
    if x is None:
        return None
    return round(float(x), 2)


def pack_path_ohm(extra):
    """Series ohms from the cell top to the BEC input, both conductors, typical corner.

    The cell model already contains the cell ohms, so Rc1 and Rc2 are not in this sum.
    Holder, fuse and XT30 ohms are the existing assumptions in sim/power_path_sim.py.
    """
    cir, _nodes, _probes, p = PN.circuit_text("typical", extra)
    keep = ("Rhp", "Rhn", "Rp1", "Rp2", "Rbms", "Rp6", "Rp7", "Rsw", "Rp9", "Rp8", "Rp10p", "Rp10n")
    ohm = {}
    for line in cir.splitlines():
        t = line.split()
        if t and t[0] in keep:
            ohm[t[0]] = float(t[3])
    return ohm, p, sum(ohm.values())


def fit_cells(is_21700, n):
    """How n cells sit in the published two-sleeve section. Calc only, except the FIT3 line."""
    if n <= 2 and is_21700:
        return "fits the grown two-cell bay (BAY.md)"
    if n <= 2 and not is_21700:
        return "fits the grown two-cell bay. An 18650 is smaller than the 22.2 mm sleeve."
    if n == 3 and is_21700:
        return "fits only with the FIT3 single-cell blister (CAD check only, 12.36 mm)"
    if n == 3 and not is_21700:
        return "the FIT3 blister was cut for a 22.2 mm circle. An 18.6 mm cell fits inside that circle."
    # 4 cells: 2 by 2. 21700 sleeve pitch 22.2 mm. 18650 pitch is the cell plus 0.4 mm radial.
    pitch = 22.2 if is_21700 else 19.4
    span = 2.0 * pitch
    if span > BAY_Y_MM or span > BAY_X_MM:
        return "does not fit. A 2 by 2 block of %.1f mm pitch is %.1f mm, and the section is %.2f mm by %.2f mm. BLOCKER for CAD" % (
            pitch, span, BAY_Y_MM, BAY_X_MM)
    return "fits the published section on this rectangle check"


def cylinder_cm3(dia_mm, h_mm, n):
    r = dia_mm / 20.0
    return n * math.pi * r * r * (h_mm / 10.0)


class PackCurve:
    def __init__(self, kind):
        self.kind = kind
        if kind == "p45b":
            self.base = p45b.P45B()
        elif kind == "p30b":
            self.base = p30b.P30B()
        else:
            self.base = None

    def v_cell(self, qm_cell, i_cell):
        spec = None
        if self.base is None:
            return None
        return self.base.v_steady(min(qm_cell, float(self.base.q[-1]) - 1.0), i_cell)

    def ocv(self, qm_cell):
        if self.base is None:
            return None
        return self.base.ocv(min(qm_cell, float(self.base.q[-1]) - 1.0))

    def q_cap(self, ah):
        if self.base is None:
            return ah * 1000.0
        return float(self.base.q_cap)


def rail_v(mode, v_in, vset, drop):
    if v_in <= 0:
        return 0.0
    if mode == "wire":
        return v_in
    if mode == "buck":
        return min(vset, max(v_in - drop, 0.0))
    if mode == "hold":
        # buck-boost that holds vset while the input is above 6 V. No part is cited at the walk current.
        return vset if v_in >= 6.0 else 0.0
    raise ValueError(mode)


# Architectures. parallel is 1 unless named.
# mode wire: no series regulator. buck: Castle equation. hold: ideal hold, part missing.
ARCH = [
    dict(id="A_2S_C001_buck72", cells="P45B", ns=2, np=1, servo="C001", mode="buck", vset=7.2,
         title="2S P45B, C001, Castle buck at 7.2 V",
         why="The as-built rail. POWER.md. The sheet walk falls."),
    dict(id="B_2S_C001_hold74", cells="P45B", ns=2, np=1, servo="C001", mode="hold", vset=7.4,
         title="2S P45B, C001, buck-boost held at 7.4 V",
         why="POWER_FIX option 5. No cited module carries the walk current."),
    dict(id="C_2S_C018_hold12", cells="P45B", ns=2, np=1, servo="C018", mode="hold", vset=12.0,
         title="2S P45B, C018, boost held at 12.0 V",
         why="A 2S pack cannot buck up to 12 V. Pololu S13V25F12 is 2.5 A."),
    dict(id="D_2S2P_P30B_C001", cells="P30B", ns=2, np=2, servo="C001", mode="buck", vset=7.2,
         title="2S2P P30B, C001, Castle buck at 7.2 V",
         why="BATTERY_STUDY already stacked this and recorded more falls. The bay does not hold four cells."),
    dict(id="E_3S_C018_wire", cells="P45B", ns=3, np=1, servo="C018", mode="wire", vset=None,
         title="3S P45B, C018, straight from the pack",
         why="No series regulator. Full charge is 12.6 V."),
    dict(id="F_3S_C018_buck12", cells="P45B", ns=3, np=1, servo="C018", mode="buck", vset=12.0,
         title="3S P45B, C018, Castle set to 12.0 V",
         why="The corrected setpoint. 16 V is outside 4.9 V to 12.5 V."),
    dict(id="G_3S_P30B_buck12", cells="P30B", ns=3, np=1, servo="C018", mode="buck", vset=12.0,
         title="3S P30B, C018, Castle set to 12.0 V",
         why="Same rail, smaller cell, digitized curve."),
    dict(id="H_3S_P50B_wire", cells="P50B", ns=3, np=1, servo="C018", mode="wire", vset=None,
         title="3S P50B, C018, straight from the pack",
         why="Same sleeve as the P45B. No digitized discharge curve, so no walk."),
    dict(id="I_3S_50S_wire", cells="50S", ns=3, np=1, servo="C018", mode="wire", vset=None,
         title="3S Samsung 50S, C018, straight from the pack",
         why="Same sleeve class. DC resistance was not on a sheet opened here."),
    dict(id="J_3S_STS3250_buck12", cells="P45B", ns=3, np=1, servo="STS3250", mode="buck", vset=12.0,
         title="3S P45B, STS3250 on all 14, Castle at 12.0 V",
         why="Same case, higher torque. The run C policy is not this servo."),
    dict(id="K_4S_P30B_buck12", cells="P30B", ns=4, np=1, servo="C018", mode="buck", vset=12.0,
         title="4S P30B, C018, Castle buck at 12.0 V",
         why="The pack stays above 12 V for most of the discharge. The bay and the 15 V nest do not."),
    dict(id="L_4S_P45B_buck12", cells="P45B", ns=4, np=1, servo="C018", mode="buck", vset=12.0,
         title="4S P45B, C018, Castle buck at 12.0 V",
         why="Same idea with the larger cell. Four 21700s do not fit."),
    dict(id="M_XM430", cells="P45B", ns=3, np=1, servo="XM430", mode="buck", vset=12.0,
         title="3S P45B, Dynamixel XM430-W350, buck at 12.0 V",
         why="Higher torque at 12 V. The case is 28.5 x 46.5 x 34 mm, not the duck horn."),
]


def bms_for(ns):
    if ns == 2:
        return dict(part="Tenergy 32175", r=0.025, i_work=10.0, i_trip=22.0, i_tol=5.0,
                    price=22.99, note="cited ceiling 25 mOhm, trip 22 A plus or minus 5 A")
    if ns == 3:
        return dict(part="Tenergy 32007", r=0.030, i_work=9.0, i_trip=17.0, i_tol=4.0,
                    price=23.99, note="cited ceiling 30 mOhm, working 9 A, trip 17 A plus or minus 4 A. Not yet the netlist part.")
    return dict(part=None, r=0.030, i_work=None, i_trip=None, i_tol=None, price=None,
                note="BLOCKER. No 4S board was opened. The path reuses the 3S 30 mOhm ceiling so the ohms are not optimistic.")


def converters(a):
    """One row per stage. Efficiency is cited, assumed, or BLOCKER."""
    rows = []
    if a["mode"] == "wire":
        rows.append(dict(stage="servo rail", part="none, pack straight through the harness",
                         eff="1, a wire", loss="I2R of the harness only",
                         limit="no clamp"))
    elif a["mode"] == "buck":
        rows.append(dict(stage="servo rail", part="Castle CC BEC Pro 010-0004-01, set to %.1f V" % a["vset"],
                         eff="0.85 assumption. Castle publishes none. BLOCKER until TEST_PLAN 4.1",
                         loss="dropout 0.3 V times current when the input is under the setpoint plus 0.3 V, else (1/0.85 - 1) times output power",
                         limit="output 4.9 V to 12.5 V cited. 15 A continuous at 2S to 4S with 5 mph air, 20 A peak. Minimum input BLOCKER."))
    else:
        rows.append(dict(stage="servo rail", part="no cited buck-boost at this current",
                         eff="0.90 is the POWER_FIX option 5 assumption, not a measurement",
                         loss="BLOCKER, no part",
                         limit="Pololu S13V25F12 is 12 V at 2.5 A typical, input 2.8 V to 22 V, https://www.pololu.com/product/4984 . The walk bus is above 2.5 A."))
    rows.append(dict(stage="Pi Zero 2 W, camera, 2x SG90, amp",
                     part="Pololu D30V30F5, item 4892, 5 V",
                     eff="sim uses 0.85. AWAKE_LOAD cites a 94 to 97 percent graph. That graph was not re-read at this pack voltage. BLOCKER for the point.",
                     loss="5 W branch in the sim, so 0.88 W at 0.85",
                     limit="input 5 V to 45 V cited. Output 5 V at 4 percent."))
    rows.append(dict(stage="IMU, touch, ToF, foot pull-ups",
                     part="the Pi Zero 2 W 3.3 V rail",
                     eff="BLOCKER. The regulator topology is not in the product brief copied here.",
                     loss="about 45 mA typical, 3.3 V, under 0.2 W even at half efficiency",
                     limit="Pi 3.3 V pin limit is BLOCKER, POWER.md section 10"))
    rows.append(dict(stage="charger, docked, not in the walk",
                     part="TI BQ24133, nest 15.0 V, charge 1.006 A",
                     eff="0.929 at 1.00 A, AVCC 15 V, 3 cells, Figure 10-4 chart read in twin/thermal/BQ24133_HEAT.md. The trace does not print the battery voltage.",
                     loss="Vbat times current times (1/0.929 - 1). Not (15 V minus pack) times current.",
                     limit="recommended input 4.5 V to 17 V. 3 cells regulate 12.6 V."))
    return rows


def charge_row(cell, ns):
    v_reg = ns * cell["v_chg"]
    i_chg = 1.006
    # nest must sit about 1 V over regulation, NEST3 from the EVM note, and under 17 V
    need = v_reg + 1.0
    ok = need <= 17.0 and 15.0 + 1e-9 >= need and 15.0 <= 17.0
    if cell["ah"] is None:
        return dict(ok=False, hours=None, why="BLOCKER, capacity")
    cc_h = cell["ah"] / i_chg
    # CHARGER_BOARD adds 0.50 h for the standard-charge tail versus a pure CC fill. Same adder here.
    hours = cc_h + 0.50
    why = "CC %.2f h at 1.006 A plus 0.50 h tail, the adder in CHARGER_BOARD.md" % cc_h
    if not ok:
        why = "BLOCKER. %dS regulates at %.1f V. The EVM note wants the supply about 1 V above that (%.1f V). The nest is 15.0 V and the BQ24133 recommended top is 17 V." % (ns, v_reg, need)
        hours = None
    # Switcher loss. (nest minus pack) times current is the linear-regulator formula and is not used.
    # Figure 10-4 was read at 15 V in and 3 cells. A 2S row on this 15 V nest has no matching trace.
    # A 4S charge is already blocked, so it has no loss either.
    heat = None
    heat_nom = None
    heat_note = "BLOCKER. Figure 10-4 was not read for this cell count on a 15 V input."
    if ok and ns == 3:
        # same chart-read efficiency at 12.6 V and at 10.8 V, as BQ24133_HEAT.md, because the trace
        # does not print the battery voltage
        heat = v_reg * i_chg * (1.0 / BQ_ETA_3S_15V - 1.0)
        heat_nom = (ns * cell["v_nom"]) * i_chg * (1.0 / BQ_ETA_3S_15V - 1.0)
        heat_note = "calc only from eta 0.929 at 1.00 A. Current here is 1.006 A. Loss at 3.0 V per cell is BLOCKER: the figure was not read there."
    return dict(ok=ok, hours=None if hours is None else round(hours, 2), why=why,
                heat_end_W=None if heat is None else round(heat, 3),
                heat_nominal_W=None if heat_nom is None else round(heat_nom, 3),
                heat_low_W=None,
                heat_note=heat_note,
                eta=BQ_ETA_3S_15V if ok and ns == 3 else None,
                v_reg=round(v_reg, 2))


def servo_at(servo, v):
    if servo == "XM430":
        return dict(tau=XM_TAU * v / XM_V, w0=XM_W0 * v / XM_V, v=v)
    s = SERVOS[servo]
    return dict(tau=s["tau"] * v / s["v"], w0=s["w0"] * v / s["v"], v=v)


def in_window(servo, v):
    if servo == "XM430":
        return 10.0 <= v <= 14.8
    s = SERVOS[servo]
    return (s["v_min_page"] <= v <= s["v_max_page"]) and (s["v_min_alt"] - 1e-6 <= v <= s["v_max_alt"] + 1e-9)


def analyze(a):
    cell = CELLS[a["cells"]]
    bms = bms_for(a["ns"])
    curve = PackCurve(cell["curve"])
    extra = {}
    if bms["r"] is not None:
        extra["R_bms"] = bms["r"]
    if a["mode"] == "wire":
        extra.update(BEC_V=30.0, BEC_DROP=0.0, BEC_EFF=1.0)
    elif a["mode"] == "buck":
        extra.update(BEC_V=a["vset"], BEC_DROP=BEC_DROP, BEC_EFF=BEC_EFF)
    else:
        extra.update(BEC_V=a["vset"], BEC_DROP=a["vset"] - 6.0, BEC_EFF=0.90)
    ohms, _p, r_path = pack_path_ohm(extra)
    # nameplate full charge, no load, path drop 0
    v_oc_full = a["ns"] * cell["v_chg"]
    v_rail_full = rail_v(a["mode"], v_oc_full, a["vset"] or 0.0, 0.0 if a["mode"] == "wire" else (0.0 if a["mode"] == "hold" else BEC_DROP))
    # digitized OCV at 0 mAh when we have a curve
    ocv0 = curve.ocv(0.0)
    v_oc_curve = None if ocv0 is None else a["ns"] * ocv0
    if v_oc_curve is not None:
        v_rail_curve = rail_v(a["mode"], v_oc_curve, a["vset"] or 0.0, 0.0 if a["mode"] != "buck" else BEC_DROP)
    else:
        v_rail_curve = None

    # discharge at I_CMP through the pack. Parallel cells share it.
    fracs = [0.0, 0.25, 0.50, 0.75, 0.90]
    qcap = curve.q_cap(cell["ah"])
    rows = []
    i_cell = I_CMP / a["np"]
    for f in fracs:
        qm = f * qcap
        if curve.base is None:
            # nameplate R only. OCV is a straight line from 4.2 to 3.3 at 90 percent, labeled as that line.
            voc = cell["v_chg"] - f * (cell["v_chg"] - 3.3)
            if cell["r_dc"] is None:
                vt = None
            else:
                vt = voc - i_cell * cell["r_dc"]
        else:
            voc = curve.ocv(qm)
            vt = curve.v_cell(qm, i_cell)
        if vt is None:
            rows.append(dict(soc=round(1 - f, 2), v_cell=None, v_rail=None, tau=None, w0=None, note="BLOCKER, no resistance"))
            continue
        v_pack = a["ns"] * vt
        v_in = v_pack - I_CMP * r_path
        vr = rail_v(a["mode"], v_in, a["vset"] or 0.0, BEC_DROP if a["mode"] == "buck" else 0.0)
        sv = servo_at(a["servo"], vr) if a["servo"] != "XM430" else servo_at("XM430", vr)
        rows.append(dict(
            soc=round(1 - f, 2),
            v_cell=r3(vt), v_pack=r3(v_pack), v_bec_in=r3(v_in), v_rail=r3(vr),
            tau_Nm=r3(sv["tau"]), w0_rad_s=r3(sv["w0"]),
            in_adopted_window=bool(in_window(a["servo"], vr)) if a["servo"] != "XM430" else bool(in_window("XM430", vr)),
        ))

    wh = a["ns"] * a["np"] * cell["wh"]
    mass_cells = a["ns"] * a["np"] * cell["mass_g"]
    if a["servo"] == "XM430":
        mass_servo = 14 * 82.0
        servo_delta = mass_servo - 14 * 55.0
    else:
        mass_servo = 14 * SERVOS[a["servo"]]["mass_g"]
        servo_delta = mass_servo - 14 * 55.0
    # baseline body in the mass budget already has 2x P45B and 14x 55 g servos and the BEC
    mass_delta = (mass_cells - 2 * 70.0) + servo_delta
    if a["mode"] == "wire":
        # the walk model seats 29 g plus the leads, tape, and two output splices. Not the 40 g Horizon figure.
        mass_delta -= BEC_REMOVED_G
    vol = cylinder_cm3(cell["dia_mm"], cell["h_mm"], a["ns"] * a["np"])
    ch = charge_row(cell, a["ns"])
    price_cells = None if cell["price"] is None else round(a["ns"] * a["np"] * cell["price"], 2)
    # ORDER.md C018 line is 14 * 20.63 = 288.82. Deltas from that bill (3x P45B, C018, BEC kept, 3S BMS).
    base_cells = 3 * 9.99
    base_servo = 14 * 20.63
    base_bms = 23.99
    base_bec = 54.95
    if a["servo"] == "C001":
        servo_price = 14 * 19.00
    elif a["servo"] == "C018":
        servo_price = 14 * 20.63
    elif a["servo"] == "STS3250":
        servo_price = 14 * 73.99
    else:
        servo_price = 14 * 269.90
    bec_price = 0.0 if a["mode"] == "wire" else base_bec
    bms_price = bms["price"]
    cost = None
    if price_cells is not None and bms_price is not None:
        cost = round((price_cells - base_cells) + (servo_price - base_servo) + (bms_price - base_bms) + (bec_price - base_bec), 2)
    elif price_cells is not None and bms_price is None:
        cost = None
    i2r_5a = (I_CMP ** 2) * r_path
    cell_heat_5a = a["ns"] * (i_cell ** 2) * (cell["r_dc"] or 0.0)
    fit = fit_cells(cell["dia_mm"] > 20.0, a["ns"] * a["np"])
    ship = "PI 967 Section II, at or under 100 Wh, passenger aircraft allowed, cited IATA lithium battery guidance and the FAA chart" if wh <= 100 else "over 100 Wh, PI 967 Section I, passenger still allowed up to 5 kg but it is a fully regulated battery"
    gates = []
    if "does not fit" in fit or "BLOCKER" in fit:
        gates.append("fit")
    if a["mode"] == "hold":
        gates.append("no converter part at the current")
    if a["servo"] == "XM430":
        gates.append("case does not fit the horn")
    if a["id"] == "A_2S_C001_buck72":
        gates.append("cited sim: the sheet walk falls, problems/STALL.md and problems/BUS_SAG.md")
    if a["servo"] == "STS3250":
        gates.append("run C was not trained on this servo, walk not run")
    if bms["part"] is None:
        gates.append("no cited 4S protection board")
    if not ch["ok"]:
        gates.append("nest cannot finish the charge")
    if cell["r_dc"] is None:
        gates.append("cell resistance BLOCKER")
    if cell["curve"] is None:
        gates.append("no digitized discharge curve, walk not run")
    if wh > 100:
        gates.append("over 100 Wh")
    # full-charge rail versus the adopted window
    if a["servo"] != "XM430" and not in_window(a["servo"], v_rail_full):
        gates.append("full-charge voltage outside the adopted window")
    # STS3250 wiki vs page: 12.6 straight would fail the page. buck at 12.0 is on the page max.
    return dict(
        id=a["id"], title=a["title"], why=a["why"],
        cell=cell["name"], ns=a["ns"], np=a["np"], servo=a["servo"], mode=a["mode"], vset=a["vset"],
        fit=fit, wh=round(wh, 2), mass_cells_g=round(mass_cells, 1), mass_delta_g=round(mass_delta, 1),
        volume_cm3=round(vol, 1),
        v_nameplate_pack=round(v_oc_full, 2), v_rail_at_nameplate=r3(v_rail_full),
        v_curve_pack=None if v_oc_curve is None else r3(v_oc_curve),
        v_rail_at_curve_rest=None if v_rail_curve is None else r3(v_rail_curve),
        r_path_mohm=round(r_path * 1000.0, 2),
        r_parts_mohm={k: round(v * 1000.0, 2) for k, v in ohms.items()},
        i2r_path_5A_W=round(i2r_5a, 3),
        cell_i2r_5A_W=round(cell_heat_5a, 3),
        discharge_at_5A=rows,
        bms=bms, charge=ch, cost_delta_usd=cost, ship=ship,
        converters=converters(a),
        hard_gates=gates,
        bec_model_note=("BEC_V 30 with drop 0 and efficiency 1 is a wire in the existing solver. It is not a Castle setpoint."
                        if a["mode"] == "wire" else
                        "Buck uses the existing min(setpoint, input minus 0.3 V) equation and efficiency 0.85."
                        if a["mode"] == "buck" else
                        "Hold mode is not a part. The 0.90 efficiency is the old option 5 assumption."),
    )


def calc_main():
    doc = dict(
        label="calc only, except numbers copied from a cited sim",
        compare_current_A=I_CMP,
        compare_current_note="5.00 A pack, every architecture, so the voltage column is the same current. Not a walk.",
        bec_16V="invalid. Castle output stops at 12.5 V. This file does not use 16 V.",
        check_power_limits="altaay_lab/verify/check_power_limits.py is not on this branch. Pull request 84 is open and was not merged, so that check was not run.",
        rows=[analyze(a) for a in ARCH],
    )
    # sanity
    assert abs(doc["rows"][4]["v_nameplate_pack"] - 12.6) < 1e-9
    assert abs(doc["rows"][4]["wh"] - 48.6) < 1e-9
    assert C018_TAU > 2.9 and C018_TAU < 3.0
    path = os.path.join(HERE, "system_voltage_calc.json")
    json.dump(doc, open(path, "w"), indent=1)
    print("wrote", os.path.relpath(path, LAB))
    for row in doc["rows"]:
        rail = row["discharge_at_5A"][2]["v_rail"]
        print(row["id"], "gates", row["hard_gates"] or "none", "50% rail", rail, "Wh", row["wh"], "d$", row["cost_delta_usd"])


# --------------------------------------------------------------------------------------------- sim
SIM_IDS = ("E_3S_C018_wire", "F_3S_C018_buck12", "K_4S_P30B_buck12")


def _shift(I, m, c, pieces):
    m2 = m + sum(dm for dm, _p in pieces)
    c2 = (m * c + sum(dm * p for dm, p in pieces)) / m2

    def about(mass, point):
        r = point - c2
        return mass * ((r @ r) * np.eye(3) - np.outer(r, r))

    I2 = I + about(m, c)
    for dm, p in pieces:
        I2 = I2 + about(dm, p)
    return m2, c2, I2


def _patch_trunk(path, pieces):
    import xml.etree.ElementTree as ETXML
    tree = ETXML.parse(path)
    for body in tree.getroot().iter("body"):
        if body.get("name") != "trunk_assembly":
            continue
        inert = body.find("inertial")
        m = float(inert.get("mass"))
        c = np.array([float(x) for x in inert.get("pos").split()])
        f = [float(x) for x in inert.get("fullinertia").split()]
        I = np.array([[f[0], f[3], f[4]], [f[3], f[1], f[5]], [f[4], f[5], f[2]]])
        m2, c2, I2 = _shift(I, m, c, pieces)
        inert.set("mass", f"{m2:.9g}")
        inert.set("pos", " ".join(f"{x:.9g}" for x in c2))
        inert.set("fullinertia", " ".join(f"{x:.9g}" for x in (I2[0, 0], I2[1, 1], I2[2, 2], I2[0, 1], I2[0, 2], I2[1, 2])))
        return dict(mass_before_kg=round(m, 4), mass_after_kg=round(m2, 4),
                    com_before_m=[round(float(x), 5) for x in c],
                    com_after_m=[round(float(x), 5) for x in c2])
    raise RuntimeError("trunk missing")


def sim_main():
    os.environ.setdefault("ODM_PLAYGROUND", os.environ.get("ODM_PLAYGROUND", ""))
    if not os.environ["ODM_PLAYGROUND"]:
        raise SystemExit("Set ODM_PLAYGROUND to an Open_Duck_Playground checkout at b9be205")
    os.environ.setdefault("ODM_ONNX", os.path.join(HERE, "retrain_sts12", "sts12_runC_policy.onnx"))
    os.environ.setdefault("TWIN_EM_SCRATCH", os.path.join(__import__("tempfile").gettempdir(), "twin_em_sv"))
    import json as _json
    import shutil
    import em_twin as ET
    import sts12  # patches the 12 V sheet. Does not run a walk.
    import inspect
    import mass_budget as MB
    _src = inspect.getsource(MB.wires)
    _src = _src.replace(
        'raise RuntimeError("gauge " + g)',
        'mass = 0.0; srcs = "[L] board or bead lead, 0 g in this walk model"',
    )
    exec(compile(_src, MB.__file__, "exec"), MB.__dict__)

    # mass_budget.wires() raises KeyError on a netlist end that cables3d.json does not seat.
    # JPI is a signal pad (cut length null, so the wire mass is 0). Seat any such end at the
    # trunk origin for this process only. The repo files are not edited.
    _load = _json.load

    def _load_seat(fh, *a, **k):
        data = _load(fh, *a, **k)
        if isinstance(data, dict) and "cable_ends" in data and not getattr(_load_seat, "done", False):
            _load_seat.done = True
            import yaml
            nl = yaml.safe_load(open(os.path.join(LAB, "wiring", "netlist.yaml"), encoding="utf-8"))
            have = {e["id"].split(".")[0] for e in data["cable_ends"]}
            need = set()
            for w in nl["wires"]:
                need.add(w["from"].split(".")[0])
                need.add(w["to"].split(".")[0])
            missing = sorted(need - have)
            for cid in missing:
                data["cable_ends"].append(dict(id=cid + ".1", link="trunk_assembly", p_world0=[0.0, 0.0, 0.0]))
            _load_seat.missing = missing
        return data

    _json.load = _load_seat

    # seats, metres, trunk frame. Two-cell axes from BAY.md. Rear axis from FIT3 / bay3.py.
    c1 = np.array([-0.1331, -0.00935, 0.0315])
    c2 = np.array([-0.1331, 0.0122, 0.0315])
    rear = np.array([-0.15251, 0.001425, 0.0315])
    # 4S seats are NOT a CAD check. One diameter behind the pair, same y.
    back1 = np.array([-0.15251, -0.00935, 0.0315])
    back2 = np.array([-0.15251, 0.0122, 0.0315])
    # audit/placements.json bec_pro center, trunk frame, metres
    bec = np.array([-0.0645, -0.0005, -0.0098])
    pieces = {
        # third cell in, Castle body, output leads, tape, and JB+/JB- out
        "E_3S_C018_wire": [(0.070, rear), (-BEC_REMOVED_G / 1000.0, bec)],
        "F_3S_C018_buck12": [(0.070, rear)],
        # model already has 2 x 70 g. Four P30B are 188 g. Delta +48 g, split as -23 g on each existing cell and +47 g on two rear seats.
        "K_4S_P30B_buck12": [(-0.023, c1), (-0.023, c2), (0.047, back1), (0.047, back2)],
    }
    cells = {
        "E_3S_C018_wire": ("p45b", 3),
        "F_3S_C018_buck12": ("p45b", 3),
        "K_4S_P30B_buck12": ("p30b", 4),
    }
    extra = {
        "E_3S_C018_wire": dict(BEC_V=30.0, BEC_DROP=0.0, BEC_EFF=1.0, R_bms=0.030),
        "F_3S_C018_buck12": dict(BEC_V=12.0, BEC_DROP=0.3, BEC_EFF=0.85, R_bms=0.030),
        "K_4S_P30B_buck12": dict(BEC_V=12.0, BEC_DROP=0.3, BEC_EFF=0.85, R_bms=0.030),
    }
    base = ET.model_folder("ours")
    print("unseated wire ends treated as zero-length at the trunk:", getattr(_load_seat, "missing", []), flush=True)
    folders = {}
    for key, pcs in pieces.items():
        dst = os.path.join(ET.AM.SCR, "models", "sv_" + key)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(base, dst)
        moved = None
        for name in ("open_duck_mini_v2.xml", "open_duck_mini_v2_backlash.xml"):
            moved = _patch_trunk(os.path.join(dst, name), pcs)
        folders[key] = (dst, moved)

    def factory(kind, ns):
        base_cls = p45b.P45B if kind == "p45b" else p30b.P30B
        scale = ns / 2.0

        class P(base_cls):
            def v_cell(self, qm, i, dt=None):
                return scale * base_cls.v_cell(self, qm, i, dt)

            def slope(self, qm, i):
                return scale * base_cls.slope(self, qm, i)

            def ocv(self, qm):
                return scale * base_cls.ocv(self, qm)

        return P

    for key, (kind, ns) in cells.items():
        ET.CELLS[key] = factory(kind, ns)

    def chain_current(r):
        names = list(r["names"])
        bins = r["_bins"]["Isup_mean"]
        bp = r["_binsp"]
        fall = r["falls"][0] if r["falls"] else 1e9
        use = np.asarray(bp["t_end"]) <= fall + 0.05
        if not np.any(use):
            use = np.ones(len(bp["t_end"]), bool)
        groups = {
            "SP1_left": ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle"],
            "SP2_right": ["right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"],
            "SP3_neck": ["neck_pitch", "head_pitch", "head_yaw", "head_roll"],
        }
        out = {}
        for g, joints in groups.items():
            idx = [names.index(n) for n in joints]
            series = bins[use][:, idx].sum(1)
            out[g + "_100ms_mean_max_A"] = round(float(series.max()), 3)
        knee = {}
        vmin = r["_bins"]["V_min"]
        for n in ("left_knee", "right_knee"):
            knee[n] = round(float(vmin[use, names.index(n)].min()), 3)
        return out, knee

    rows = []
    cmds = [0.15, 0.40]
    dur = float(os.environ.get("SV_DUR", "60"))
    only = [x for x in os.environ.get("SV_ONLY", "").split(",") if x]
    run_ids = tuple(only) if only else SIM_IDS
    for key in run_ids:
        dst, moved = folders[key]
        ET.model_folder = lambda mass, dst=dst: dst
        for cmd in cmds:
            for corner in ("typical", "high-side"):
                r = ET.run(
                    mass="ours", walk="backlash", cmd=(cmd, 0.0, 0.0), dur=dur,
                    supply="net", corner=corner, extra=extra[key],
                    cell=key, q0=0.0, servo_mode="sheet", guard=None,
                    keep_full=False, stop_on_fall=True, t_stats=4.0, label=key,
                )
                chains, knees = chain_current(r)
                g = r["gait"]
                pack = r.get("pack") or {}
                rows.append(dict(
                    label="sim pass only",
                    id=key, cmd_m_s=cmd, corner=corner, dur_s=r["dur_s"],
                    fall_s=r["falls"] or "none",
                    vx_m_s=None if g.get("vx") is None else round(g["vx"], 4),
                    track_lin=None if g.get("track_lin") is None else round(g["track_lin"], 3),
                    knees=knees,
                    pack=pack,
                    chains=chains,
                    trunk=moved,
                    q_end_mAh=r["q_end_mAh"],
                    wall_s=r["wall_s"],
                    extra_note=dict(BEC_V=extra[key]["BEC_V"], BEC_DROP=extra[key]["BEC_DROP"], BEC_EFF=extra[key]["BEC_EFF"]),
                    bec_removed_g=round(BEC_REMOVED_G, 2) if key == "E_3S_C018_wire" else 0.0,
                ))
                print(key, cmd, corner, rows[-1]["fall_s"], rows[-1]["vx_m_s"], knees, pack.get("i_max"), pack.get("i_mean"), flush=True)
    # sanity against the published run C 0.15 typical speed 0.108 m/s on the buck-dropout rig
    buck = [x for x in rows if x["id"] == "F_3S_C018_buck12" and x["cmd_m_s"] == 0.15 and x["corner"] == "typical"]
    if buck and buck[0]["vx_m_s"] is not None:
        if not (0.05 <= buck[0]["vx_m_s"] <= 0.20):
            print("SANITY: 0.15 m/s typical speed is outside 0.05 to 0.20. Published run C is 0.108.", flush=True)
    path = os.path.join(HERE, "system_voltage_sim.json")
    if only and os.path.exists(path):
        old = json.load(open(path))
        rows = [r for r in old["rows"] if r["id"] not in set(only)] + rows
    doc = dict(
        label="sim pass only",
        onnx="problems/retrain_sts12/sts12_runC_policy.onnx",
        sheet="sts12.py 12 V C018 sheet patch, not re-fit",
        mujoco="3.3.4",
        bec_setpoint_note="F and K use 12.0 V. E uses a wire (efficiency 1, drop 0). None use 16 V.",
        bec_removed_g=round(BEC_REMOVED_G, 3),
        bec_removed_note="E subtracts the mass-budget Castle (29.0 g cited, no wires), output leads 4.6 g, tape, and JB+ JB- at the bec_pro seat. F and K keep that mass.",
        rows=rows,
    )
    json.dump(doc, open(path, "w"), indent=1)
    print("wrote", os.path.relpath(path, LAB))


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "calc"
    if step == "calc":
        calc_main()
    elif step == "sim":
        sim_main()
    else:
        raise SystemExit("calc or sim")
