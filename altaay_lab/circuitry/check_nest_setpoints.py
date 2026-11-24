#!/usr/bin/env python3
"""Set points for the two-net nest, checked against the cited limits.

Run from the repo root:
  python3 altaay_lab/circuitry/check_nest_setpoints.py

Labels: calc only on the arithmetic, cited on the limits. A sim is not this
script. Exit 0 when every installed set point is inside its limit and the
MCP73213 is not the charger on this 3S pack.
"""
from __future__ import annotations

import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
NETLIST = os.path.join(LAB, "wiring", "netlist.yaml")

# Cited, problems/NEST3.md and twin/electromech/power_net.py. Same literal the
# power-limit scan already requires.
NEST_V = 15.0

# Calc only, circuitry/BQ24133_BOARD.md ISET divider. Same number as the netlist.
I_CHG = 1.006

# Cited, SLUSAF7D, verify/part_limits.yaml bq24133.
BQ_I_MIN = 0.6
BQ_I_MAX = 2.5
BQ_V_MIN = 4.5
BQ_V_MAX = 17.0
BQ_PVCC_ABS = 20.0
BQ_AVCC_ABS = 30.0
BQ_VREG = 12.6

# Cited, P45B version 1.2, via CHARGER_BOARD.md and part_limits.
CELL_V = 4.2
CELL_I_MAX = 13.5
CELL_I_STD = 4.5
CELL_T_MAX = 60.0
N_CELL = 3

# Cited, PCM-L04S30-566, part_limits pcm_l04s30.
BMS_V = 12.6
BMS_I_CHG = 20.0

# Cited, netlist F2, Littelfuse 0287005.PXCN.
FUSE_A = 5.0
FUSE_V = 32.0

# Cited, Vishay SS32-SS36, document 88751, 23 Apr 2020. SS33 column.
SS_VRRM = 30.0
SS_IF = 3.0
SS_VF_3A = 0.50

# Cited, SMAJ16A, problems/NEST3.md. Rim clamp. Not a PVCC voltage.
TVS_STANDOFF = 16.0
TVS_CLAMP = 26.0
TVS_I_CLAMP = 15.4

# Cited, SLVSFC9C. TPS259470A, adjustable OVLO.
EFUSE_IN_ABS = 28.0
EFUSE_IN_REC = 23.0
EFUSE_OVLO_LO = 1.183
EFUSE_OVLO_TYP = 1.20
EFUSE_OVLO_HI = 1.223
EFUSE_OVLO_PIN_REC = 1.5
EFUSE_OVLO_PIN_ABS = 6.5
EFUSE_T_OVLO_US = 1.2
EFUSE_RON_MOHM = 45.0
EFUSE_ILIM_MIN = 1.800
EFUSE_IFT_TYP = 22.2
R_OV_TOP = 140e3
R_OV_BOT = 10e3
R_UV_TOP = 90.9e3
R_UV_BOT = 10e3

# Cited, SLVSED3A. TVS1400 on the eFuse output.
DUCK_VRWM = 14.0
DUCK_VBR_MIN = 16.2
DUCK_VBR_MAX = 17.8
# Highest cited clamp maximum at a current above the 22.2 A fast-trip typical.
# 19.3 V max at 35 A, 125 C, input starting at the standoff. 18.8 V max at 43 A, 27 C.
DUCK_CLAMP = 19.3
DUCK_CLAMP_I = 35.0

# Cited, Littelfuse RXEF series. RXEF185 row and the 60 C rerating.
PTC_HOLD_20 = 1.85
PTC_HOLD_60 = 1.17
PTC_HOLD_70 = 1.00
PTC_TRIP = 3.70
PTC_RMAX = 0.12

# Cited, Pololu 2815, circuitry/SERVO_RAIL.md. 13 milliohm max at a 4.5 V gate.
SW_MOHM = 13.0
SW_V_MAX = 40.0

# Calc only, NEST_V2.md, both 22 AWG poles.
WIRE_OHM = 0.038

# Bench ceiling, BENCH_CONTACT.md. Not a measurement on this foil.
CONTACT_V = 0.10

# EVM note, problems/NEST3.md. 1 V above the 12.6 V regulation.
HEADROOM = 1.0

# Cited, DS20002190C via CHARGER_BOARD.md. The 2S part. Not installed.
MCP_VREG = 8.40
MCP_VREC_MAX = 13.0
MCP_OVP = 13.0
MCP_I_LO = 0.900
MCP_I_HI = 1.100

# Signature divider. 47.5 k and 4.99 k, 1 percent. Window 1.20 V to 1.65 V.
R_BIAS = 47500.0
R_SIG = 4990.0
WIN_LO = 1.20
WIN_HI = 1.65
# Cited, LM393BIDR, the 4 mV offset already copied in CHARGER_BOARD.md.
LM_OFFSET = 0.004


def fail(msg):
    print("FAIL", msg)
    return 1


def main():
    bad = 0
    net = yaml.safe_load(open(NETLIST, encoding="utf-8"))
    chg = next(c for c in net["components"] if c["id"] == "CHG")
    i_net = float(chg["ratings"]["i_charge_a"])
    v_net = float(chg["ratings"]["v_nest"])
    if abs(i_net - I_CHG) > 1e-9:
        bad += fail("netlist charge current %.3f A is not %.3f A" % (i_net, I_CHG))
    if abs(v_net - NEST_V) > 1e-9:
        bad += fail("netlist nest %.3f V is not %.1f V" % (v_net, NEST_V))
    if "BQ24133" not in chg["part"]:
        bad += fail("CHG is not the BQ24133")
    if "MCP73213" in chg["part"]:
        bad += fail("CHG part line names the MCP73213")
    pins = {p["pin"] for p in chg["pins"]}
    if "VIN" not in pins:
        bad += fail("CHG has no VIN pin for the nest")

    if not (BQ_I_MIN <= I_CHG <= BQ_I_MAX):
        bad += fail("1.006 A is outside the BQ24133 fast-charge range")
    if I_CHG > CELL_I_MAX or I_CHG > CELL_I_STD:
        bad += fail("1.006 A is above a P45B charge current")
    if abs(N_CELL * CELL_V - BQ_VREG) > 1e-9 or abs(BQ_VREG - BMS_V) > 1e-9:
        bad += fail("pack charge voltage is not 12.6 V")
    if I_CHG > BMS_I_CHG:
        bad += fail("charge current is above the BMS charge rating")
    if I_CHG > FUSE_A or NEST_V > FUSE_V:
        bad += fail("nest is outside the 5 A fuse")
    if I_CHG > SS_IF:
        bad += fail("charge current is above the SS33 average current")
    if not (BQ_V_MIN <= NEST_V <= BQ_V_MAX) or NEST_V > BQ_PVCC_ABS or NEST_V > BQ_AVCC_ABS:
        bad += fail("nest voltage is outside the BQ24133 input limits")
    if NEST_V > TVS_STANDOFF:
        bad += fail("15 V nest is above the SMAJ16A standoff")
    if TVS_CLAMP > SS_VRRM or TVS_CLAMP > SW_V_MAX or TVS_CLAMP > EFUSE_IN_ABS:
        bad += fail("rim TVS clamp is above a part on that node")
    # Every cited clamp has to sit under the lowest absolute maximum on its node.
    # The 26.0 V rim clamp is not on PVCC. Putting it there fails this check.
    nodes = (
        ("rim and eFuse input", (TVS_CLAMP,), (SS_VRRM, SW_V_MAX, EFUSE_IN_ABS)),
        ("eFuse output and PVCC", (DUCK_CLAMP, DUCK_VBR_MAX), (BQ_PVCC_ABS,)),
    )
    for name, clamps, limits in nodes:
        worst = max(clamps)
        limit = min(limits)
        if worst > limit + 1e-9:
            bad += fail("%s clamp %.1f V is above the %.1f V absolute maximum on that node" % (name, worst, limit))
    if max((TVS_CLAMP,)) <= min((BQ_PVCC_ABS,)) + 1e-9:
        bad += fail("the guard accepted a 26 V clamp on the 20 V PVCC pin")
    chg_pin = next(p for p in chg["pins"] if p["pin"] == "VIN")
    chg_dom = net["domains"][chg_pin["domain"]]
    if float(chg_dom["v_max"]) >= BQ_PVCC_ABS or float(chg_dom["v_max"]) >= TVS_CLAMP:
        bad += fail("CHG.VIN domain reaches the 26 V clamp or the 20 V absolute maximum")
    gain = (R_OV_TOP + R_OV_BOT) / R_OV_BOT
    trip_lo = EFUSE_OVLO_LO * gain
    trip_typ = EFUSE_OVLO_TYP * gain
    trip_hi = EFUSE_OVLO_HI * gain
    if trip_hi >= BQ_PVCC_ABS:
        bad += fail("OVLO high trip %.3f V is not under the PVCC absolute maximum" % trip_hi)
    if trip_lo <= TVS_STANDOFF:
        bad += fail("OVLO low trip %.3f V is inside the 16.0 V window" % trip_lo)
    if abs(trip_typ - 18.0) > 0.01:
        bad += fail("OVLO typical trip is not 18.00 V")
    ugain = (R_UV_TOP + R_UV_BOT) / R_UV_BOT
    uv_hi = EFUSE_OVLO_HI * ugain
    if uv_hi >= BQ_VREG + HEADROOM:
        bad += fail("UVLO high trip %.3f V is above the 13.6 V floor, so the eFuse can stay off in the window" % uv_hi)
    if EFUSE_ILIM_MIN <= I_CHG:
        bad += fail("ILIM minimum is not above the charge current")
    if DUCK_CLAMP_I < EFUSE_IFT_TYP:
        bad += fail("duck TVS clamp current is under the eFuse fast-trip typical")
    if TVS_STANDOFF >= DUCK_VBR_MIN:
        bad += fail("the 16.0 V window is at or above the duck TVS breakdown minimum")
    ovlo_at_16 = TVS_STANDOFF * R_OV_BOT / (R_OV_TOP + R_OV_BOT)
    ovlo_at_26 = TVS_CLAMP * R_OV_BOT / (R_OV_TOP + R_OV_BOT)
    if ovlo_at_16 > EFUSE_OVLO_PIN_REC:
        bad += fail("OVLO pin at the window top is above the 1.5 V recommended maximum")
    if ovlo_at_26 > EFUSE_OVLO_PIN_ABS:
        bad += fail("OVLO pin at the 26 V clamp is above the 6.5 V absolute maximum")
    if NEST_V > EFUSE_IN_REC or TVS_CLAMP > EFUSE_IN_ABS:
        bad += fail("eFuse input is outside its cited input limits")

    # MCP73213 cannot be this charger. 1.006 A would have fit its current band.
    if not (MCP_I_LO <= I_CHG <= MCP_I_HI):
        bad += fail("record: 1.006 A is outside the MCP73213 1.10 kOhm band")
    if NEST_V <= MCP_VREC_MAX and NEST_V <= MCP_OVP and abs(BQ_VREG - MCP_VREG) < 1e-6:
        bad += fail("MCP73213 limits would accept this pack, and the note says they do not")
    if NEST_V <= MCP_OVP:
        bad += fail("15 V nest is not above the MCP73213 over-voltage trip")
    if abs(BQ_VREG - MCP_VREG) < 1e-6:
        bad += fail("12.6 V matches the MCP73213 8.40 V option")

    diode = 2.0 * SS_VF_3A
    ptc = PTC_RMAX * I_CHG
    switch = (SW_MOHM * 1e-3) * I_CHG
    wire = WIRE_OHM * I_CHG
    contacts = 2.0 * CONTACT_V
    efuse = (EFUSE_RON_MOHM * 1e-3) * I_CHG
    arrived = NEST_V - diode - ptc - switch - wire - contacts - efuse
    floor = BQ_VREG + HEADROOM
    if arrived > TVS_STANDOFF + 1e-9:
        bad += fail("stacked input %.3f V is above the %.1f V standoff" % (arrived, TVS_STANDOFF))
    if arrived < BQ_VREG:
        bad += fail("stacked input %.3f V is under the 12.6 V pack" % arrived)
    if I_CHG > PTC_HOLD_60:
        bad += fail("charge current is above the RXEF185 hold at 60 C")
    if I_CHG >= PTC_TRIP:
        bad += fail("charge current trips the RXEF185")
    if PTC_HOLD_70 >= I_CHG:
        bad += fail("the 70 C hold should be under 1.006 A, and the cell sheet stops at 60 C")

    v_nom = NEST_V * R_SIG / (R_BIAS + R_SIG)
    v_lo = NEST_V * (R_SIG * 0.99) / (R_BIAS * 1.01 + R_SIG * 0.99)
    v_hi = NEST_V * (R_SIG * 1.01) / (R_BIAS * 0.99 + R_SIG * 1.01)
    if not (WIN_LO + LM_OFFSET < v_lo and v_hi < WIN_HI - LM_OFFSET):
        bad += fail("signature window does not hold the 1 percent corners")
    v_open = NEST_V
    v_short = 0.0
    if WIN_LO <= v_open <= WIN_HI or WIN_LO <= v_short <= WIN_HI:
        bad += fail("an open or a short sits inside the signature window")

    cables = {c["id"]: c for c in net["cables"]}
    if "NEST" not in cables or cables["NEST"].get("status") != "nest":
        bad += fail("cable NEST is not status nest")
    if cables["NEST"].get("no_route") is not True:
        bad += fail("cable NEST must stay no_route so the older sheets are not forced")
    wires = net["wires"]
    def live(a, b):
        for w in wires:
            ends = {w["from"], w["to"]}
            if ends == {a, b} and w.get("cable") == "NEST" and w.get("status") != "superseded":
                return True
        return False
    for pair in (
        ("JNW.1", "BR1.D1"),
        ("JNW.2", "BR1.D2"),
        ("JNW.3", "BR1.D3"),
        ("JNW.4", "BR1.D4"),
        ("JNW.5", "BR1.D5"),
        ("RSIG.1", "BR1.P"),
        ("RSIG.2", "BR1.N"),
        ("BR1.P", "PTC1.A"),
        ("PTC1.B", "F2.IN"),
        ("F2.OUT", "OVP.IN"),
        ("OVP.OUT", "CHG.VIN"),
        ("OVP.OUT", "TVS1.K"),
        ("TVS1.A", "OVP.GND"),
        ("ROV.2", "OVP.OVLO"),
        ("RUV.2", "OVP.EN"),
        ("RIL.1", "OVP.ILM"),
        ("BR1.N", "BMS.P-"),
        ("JFO.S", "DK8.VIN"),
        ("DK8.VOUT", "J5IN.S"),
    ):
        if not live(*pair):
            bad += fail("missing nest wire %s to %s" % pair)
    br = next(c for c in net["components"] if c["id"] == "BR1")
    diodes = {(row["a"], row["b"]) for row in br.get("internal") or [] if row.get("kind") == "diode"}
    for i in range(1, 6):
        if ("D%d" % i, "P") not in diodes or ("D%d" % i, "N") not in diodes:
            bad += fail("BR1.D%d is missing an SS33 to P or to N" % i)
    # The 5 V pin stays on the pack, and P13 is not moved.
    u3 = next(c for c in net["components"] if c["id"] == "U3")
    vin = next(p for p in u3["pins"] if p["pin"] == "VIN")
    if vin["domain"] != "PACK_9V0_12V6":
        bad += fail("U3 VIN domain changed. The 5 V interface stays on the pack domain")
    p13 = [w for w in wires if w.get("cable") == "P13" and w.get("to") == "U3.VIN"]
    if len(p13) != 1 or p13[0]["from"] != "VSW.S":
        bad += fail("P13 no longer runs from VSW to U3.VIN")
    # Chest SYS must not be a live feed into the servo switch.
    for w in wires:
        if {w["from"], w["to"]} == {"DK6.VOUT", "SW1.VIN"} and w.get("status") != "superseded":
            bad += fail("DK6 still feeds the servo switch")
    j5 = next((c for c in net["components"] if c["id"] == "J5IN"), None)
    if j5 is None:
        bad += fail("J5IN is missing")
    else:
        pin = j5["pins"][0]
        if pin["domain"] != "PACK_9V0_12V6":
            bad += fail("J5IN is not on the pack domain")

    print("charge %.3f A (calc only) inside BQ24133 %.1f A to %.1f A, P45B %.1f A, BMS %.0f A, fuse %.0f A, SS33 %.1f A" % (
        I_CHG, BQ_I_MIN, BQ_I_MAX, CELL_I_MAX, BMS_I_CHG, FUSE_A, SS_IF))
    print("nest %.1f V inside BQ24133 %.1f V to %.1f V. MCP73213 regulates %.2f V and trips at %.0f V, so it is not installed." % (
        NEST_V, BQ_V_MIN, BQ_V_MAX, MCP_VREG, MCP_OVP))
    print("stacked input %.3f V (calc only), EVM note %.1f V, standoff %.1f V" % (arrived, floor, TVS_STANDOFF))
    if arrived < floor - 1e-9:
        print("NOTE stacked input is %.3f V under the %.1f V EVM note after the eFuse %.0f mOhm maximum is added to the other maximums"
              % (floor - arrived, floor, EFUSE_RON_MOHM))
    print("OVLO trip %.3f V typical, %.3f V to %.3f V, response %.1f us typical (cited)"
          % (trip_typ, trip_lo, trip_hi, EFUSE_T_OVLO_US))
    print("duck TVS clamp %.1f V at %.0f A is under the PVCC %.0f V absolute maximum. Recommended standoff %.0f V is under the %.1f V set point. Breakdown minimum %.1f V is above the %.1f V window."
          % (DUCK_CLAMP, DUCK_CLAMP_I, BQ_PVCC_ABS, DUCK_VRWM, NEST_V, DUCK_VBR_MIN, TVS_STANDOFF))
    print("rim clamp %.1f V at %.1f A stays on the eFuse input. Absolute maximum %.0f V. Recommended maximum %.0f V."
          % (TVS_CLAMP, TVS_I_CLAMP, EFUSE_IN_ABS, EFUSE_IN_REC))
    print("signature %.3f V nominal, corners %.3f V to %.3f V, window %.2f V to %.2f V" % (
        v_nom, v_lo, v_hi, WIN_LO, WIN_HI))
    if bad:
        print("%d FAIL" % bad)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
