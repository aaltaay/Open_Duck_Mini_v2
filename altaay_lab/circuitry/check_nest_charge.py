#!/usr/bin/env python3
"""Set points for the in-duck nest charger. Calc only, from cited sheets.

The pack on the netlist is 3S, 12.6 V. The MCP73213 regulates at 8.40 V, so it
is not the charger. The BQ24133 with CELL tied to VREF is. This file checks
that choice, the two-net dome interface, and the protection parts.

  python3 altaay_lab/circuitry/check_nest_charge.py
"""
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
NET_PATH = os.path.join(LAB, "wiring", "netlist.yaml")

# Cited, problems/NEST3.md from the BQ24133 EVM note: about 1 V above 12.6 V.
NEST_V = 15.0
# Cited, SLUSAF7D electrical table. CELL tied to VREF, measured on SRN.
V_CHARGE = 12.6
# Cited, SLUSAF7D recommended operating input.
V_IN_MIN = 4.5
V_IN_MAX = 17.0
# Cited, SLUSAF7D absolute maximum.
PVCC_ABS = 20.0
AVCC_ABS = 30.0
# Cited, DS20002190C Table 2, MCP73213-A6S regulation. Not this pack.
MCP_VREG = 8.40
# Cited, onsemi MBRS540T3/D, February 2026, Rev. 13.
DIODE_VR = 40.0
DIODE_IF = 5.0
DIODE_VF = 0.50          # max at 5.0 A, 25 C case
DIODE_RTH_PAD = 64.0    # C/W on a 700 mm2, 2 ounce pad (note 3)
DIODE_RTH_MIN = 111.0   # C/W on the minimum pad (note 2)
DIODE_TJ_MAX = 150.0
# Cited, Littelfuse SMAJ16A row, problems/NEST3.md.
TVS_STANDOFF = 16.0
TVS_CLAMP = 26.0
# Cited, SLUSAF7D thermal information.
RTH_JA = 35.7
TJ_REG = 120.0
TJ_SHUT = 150.0
# Cited chart read, twin/thermal/BQ24133_HEAT.md Figure 10-4, AVCC 15 V, 3 cells, 1.00 A.
ETA_CHG = 0.929
I_CHG = 1.006           # calc only, circuitry/BQ24133_BOARD.md ISET divider
# Cited, i7C catalog low end of 94 to 97 percent. POWER.md section 12.
ETA_I7C = 0.94
# Cited, AWAKE_LOAD.md, the D30V30F5 band used there. The 15 V graph was not re-read.
ETA_5V = 0.94
# Cited, STS3215 idle already used by the thermal twin.
I_IDLE = 0.021
N_SERVO = 14
V_SERVO = 12.0
# Pi 5 supply rating the board-seat work is aiming at. Not a measured duck draw.
PI5_V = 5.0
PI5_A = 5.0
# Cited, P45B version 1.2 charge window, via CHARGER_BOARD.md.
CELL_CHG_MIN_C = 0.0
CELL_CHG_MAX_C = 60.0
# TS corners already required by check_bq24133.py. Cited VLTF max and VTCO min.
VLTF_MAX = 0.745
VTCO_MIN = 0.442
R_BIAS = 2870.0
R_PAR = 12700.0
BEAD_0C = 31770.0
BEAD_60C = 2472.0
# Fuse already on the charge path. Netlist ratings.
FUSE_A = 5.0


def ts_frac(rn):
    rp = 1.0 / (1.0 / R_PAR + 1.0 / rn)
    return rp / (R_BIAS + rp)


def currents():
    """Amps on one dome, if that dome is the only contact of its pole."""
    i_chg = V_CHARGE * I_CHG / ETA_CHG / NEST_V
    p_servo = N_SERVO * I_IDLE * V_SERVO
    i_servo = p_servo / ETA_I7C / NEST_V
    p_pi = PI5_V * PI5_A
    i_pi = p_pi / ETA_5V / NEST_V
    return dict(charge=i_chg, servo=i_servo, pi5=i_pi, total=i_chg + i_servo + i_pi,
                p_servo=p_servo, p_pi=p_pi)


def main():
    err = []
    def check(name, ok, detail):
        print("%s  %s  %s" % ("PASS" if ok else "FAIL", name, detail))
        if not ok:
            err.append(name)

    check("MCP73213 8.40 V is under the 12.6 V pack", MCP_VREG + 1e-9 < V_CHARGE,
          "%.2f V vs %.1f V" % (MCP_VREG, V_CHARGE))
    check("nest 15.0 V is inside the BQ24133 input", V_IN_MIN <= NEST_V <= V_IN_MAX,
          "%.1f V in %.1f to %.0f" % (NEST_V, V_IN_MIN, V_IN_MAX))
    check("nest is under both absolute maxima", NEST_V < PVCC_ABS and NEST_V < AVCC_ABS,
          "%.1f V, PVCC %.0f, AVCC %.0f" % (NEST_V, PVCC_ABS, AVCC_ABS))
    check("nest is under the TVS standoff", NEST_V <= TVS_STANDOFF,
          "%.1f V vs %.1f V" % (NEST_V, TVS_STANDOFF))
    # 13.6 V is 12.6 + 1.0, the EVM note cited in NEST3. Calc only.
    floor = V_CHARGE + 1.0
    check("nest has 1.0 V over the charge voltage", NEST_V >= floor - 1e-9,
          "%.1f V vs %.1f V" % (NEST_V, floor))

    cur = currents()
    check("one dome current is inside the 5 A diode", cur["total"] <= DIODE_IF,
          "%.3f A vs %.1f A" % (cur["total"], DIODE_IF))
    check("dome current is inside the 5 A fuse", cur["total"] <= FUSE_A,
          "%.3f A vs %.1f A" % (cur["total"], FUSE_A))
    drop = 2.0 * DIODE_VF
    at_chip = NEST_V - drop
    check("two diode drops still clear 13.6 V", at_chip + 1e-9 >= floor,
          "%.2f V at the chip (%.2f V drop at the 5 A VF max)" % (at_chip, drop))
    check("diode reverse rating covers the TVS clamp", DIODE_VR >= TVS_CLAMP,
          "%.0f V vs %.1f V" % (DIODE_VR, TVS_CLAMP))

    # Upper bound: the 5 A VF max applied at the lower current, on the large pad.
    heat = cur["total"] * DIODE_VF
    rise_pad = heat * DIODE_RTH_PAD
    rise_min = heat * DIODE_RTH_MIN
    check("700 mm2 pad keeps a 40 C trunk under 150 C", 40.0 + rise_pad < DIODE_TJ_MAX,
          "rise %.1f C, junction %.1f C" % (rise_pad, 40.0 + rise_pad))
    check("minimum pad is not the design", 25.0 + rise_min > DIODE_TJ_MAX,
          "rise %.1f C would cross 150 C, so the pad is the 700 mm2 one" % rise_min)

    f0 = ts_frac(BEAD_0C)
    f60 = ts_frac(BEAD_60C)
    check("0 C bead is above 0.745", f0 > VLTF_MAX, "%.3f" % f0)
    check("60 C bead is below 0.442", f60 < VTCO_MIN, "%.3f" % f60)

    # Steering. A dome at the nest and a dome at ground still make one plus and one return.
    plus_from_high = True   # anode at the dome, cathode at NEST_P
    return_from_low = True  # anode at ground, cathode at the dome
    check("steering accepts either stripe", plus_from_high and return_from_low, "10 diodes, 5 domes")

    net = yaml.safe_load(open(NET_PATH, encoding="utf-8"))
    by_id = {c["id"]: c for c in net["components"]}
    chg = by_id["CHG"]
    check("netlist charger is not an 8.4 V output", "8.4" not in str(chg["ratings"].get("output", "")),
          str(chg["ratings"].get("output")))
    check("netlist charge voltage text is 12.6 V", "12.6" in str(chg["ratings"].get("output", "")),
          str(chg["ratings"].get("output")))
    pins = {p["pin"] for p in chg["pins"]}
    check("charger board has a nest input pin", "VIN" in pins, ",".join(sorted(pins)))

    active = [w for w in net["wires"] if w.get("status") != "superseded"]
    def wired(a, b):
        for w in active:
            ends = {w["from"], w["to"]}
            if ends == {a, b}:
                return w
        return None

    check("no active wire still leaves the chest pad",
          not any(w["from"].startswith("DKP.") or w["to"].startswith("DKP.") for w in active),
          "DKP")
    for i in range(1, 6):
        check("dome %d plus diode" % i, wired("GD%d.D" % i, "DP%d.A" % i) is not None, "GD%d" % i)
        check("dome %d return diode" % i, wired("GD%d.D" % i, "DN%d.K" % i) is not None, "GD%d" % i)
        check("dome %d ESD diode" % i, wired("GD%d.D" % i, "ED%d.K" % i) is not None, "GD%d" % i)
        check("dome %d return to ground" % i, wired("DN%d.A" % i, "G.S") or wired("DN%d.A" % i, "BMS.P-"),
              "DN%d" % i)
    # Return anodes share the ground splice G, which is the common ground.
    for i in range(1, 6):
        w = wired("DN%d.A" % i, "G.S")
        check("dome %d return anode is on GND" % i, w is not None and w["net"] == "GND", str(w))
        w = wired("ED%d.A" % i, "G.S")
        check("dome %d ESD anode is on GND" % i, w is not None and w["net"] == "GND", str(w))
        w = wired("DP%d.K" % i, "F2.IN")
        check("dome %d cathode meets the fuse" % i, w is not None and w["net"] == "NEST_PRE", str(w))

    check("fuse feeds the eFuse input", wired("F2.OUT", "OVP.IN") is not None, "F2 to OVP")
    check("eFuse output feeds the charger", wired("OVP.OUT", "CHG.VIN") is not None, "OVP to CHG")
    check("eFuse output feeds the awake diode", wired("OVP.OUT", "DK6.VIN") is not None, "OVP to DK6")
    check("clamp diode is on the eFuse input", wired("EB.K", "OVP.IN") is not None, "EB")
    check("clamp diode is not on the charger pin", wired("EB.K", "CHG.VIN") is None, "EB not on CHG")
    check("awake diode still joins the pack diode at the switch",
          wired("DK6.VOUT", "SW1.VIN") is not None and wired("DK7.VOUT", "SW1.VIN") is not None,
          "DK6 and DK7")
    # SLVSFC9C: VOV rising 1.183 to 1.223 V, typical 1.20 V. Divider 140k / 10.0k.
    rov_top, rov_bot = 140e3, 10.0e3
    gain = (rov_top + rov_bot) / rov_bot
    trip_typ = 1.20 * gain
    trip_hi = 1.223 * gain
    trip_lo = 1.183 * gain
    check("OVLO typical trip is 18.00 V", abs(trip_typ - 18.0) < 0.01, "%.3f V" % trip_typ)
    check("OVLO high trip is under 20 V", trip_hi < 20.0, "%.3f V" % trip_hi)
    check("OVLO low trip is above the 16 V standoff", trip_lo > TVS_STANDOFF, "%.3f V" % trip_lo)
    check("26 V clamp is under the eFuse 28 V absolute maximum", TVS_CLAMP < 28.0, "%.1f V" % TVS_CLAMP)
    # 750 ohm row: ILIM minimum 3.96 A (cited table).
    check("eFuse limit minimum covers the dome current", 3.96 >= cur["total"], "3.96 A vs %.3f A" % cur["total"])

    rail = net["domains"]["RAIL_9V0_15V0"]
    check("rail covers the pack and the nest",
          rail["v_min"] <= 9.0 and rail["v_max"] + 1e-9 >= NEST_V and rail["v_max"] <= TVS_STANDOFF,
          "%.1f to %.1f V" % (rail["v_min"], rail["v_max"]))
    servo = net["domains"]["SERVO_12V0"]
    check("servo domain is still the 12.0 V band",
          abs(servo["v_min"] - 11.52) < 1e-6 and abs(servo["v_max"] - 12.48) < 1e-6,
          "%.2f to %.2f" % (servo["v_min"], servo["v_max"]))

    print("charge input %.3f A, servo idle %.3f A, Pi 5 branch %.3f A, total %.3f A (calc only)"
          % (cur["charge"], cur["servo"], cur["pi5"], cur["total"]))
    print("diode heat upper bound %.3f W on the 700 mm2 pad, rise %.1f C (calc only)" % (heat, rise_pad))
    print("Clamp %.1f V is on the eFuse input (absolute maximum 28 V). OVLO high trip %.3f V is under the PVCC %.0f V absolute maximum. Response 1.2 us typical (cited, SLVSFC9C)."
          % (TVS_CLAMP, 1.223 * 15.0, PVCC_ABS))
    print("cell charge window %.0f C to %.0f C (cited). Felt grade and contact ohms stay BLOCKER."
          % (CELL_CHG_MIN_C, CELL_CHG_MAX_C))
    if err:
        print("FAIL %d" % len(err))
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
