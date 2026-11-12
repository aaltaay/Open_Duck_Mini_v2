#!/usr/bin/env python3
"""Calc check for the in-body charger board.

Every asserted number is either copied from a datasheet cited in CHARGER_BOARD.md
or computed here from those copies. This is arithmetic. It is not a measurement
and it is not a simulation of the duck.

Usage (from the repo root):
  python3 altaay_lab/circuitry/check_charger.py
"""
import math
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
YAML_PATH = os.path.join(HERE, "charger_board.yaml")
MD_PATH = os.path.join(HERE, "CHARGER_BOARD.md")
SCH_PATH = os.path.join(HERE, "charger_board.kicad_sch")

# Cited copies. Sources are named in CHARGER_BOARD.md. Do not "improve" these.
# MCP73213 DS20002190C equation 5-1: IREG (mA) = 1104 * RPROG(kOhm) ** (-0.93)
IREG_SCALE = 1104.0
IREG_EXP = -0.93
RPROG_KOHM = 1.10          # Table 5-1 row for 1000 mA, and the 1.1 kOhm spec point
IREG_SPEC_TYP_MA = 1000.0  # DC table, PROG = 1.1 kOhm, typical
IREG_SPEC_MIN_MA = 900.0
IREG_SPEC_MAX_MA = 1100.0
VREG_TYP_V = 8.40
VREG_MIN_V = 8.35
VREG_MAX_V = 8.45
VPTH_RATIO_TYP = 0.715     # A6S option, Table 2
VPTH_RATIO_MIN = 0.69
HEADROOM_V = 0.30          # electrical table applies from VREG(typ) + 0.3 V
OVP_TYP_V = 13.0
VDD_ABS_MAX_V = 18.0
THETA_JA = 62.0            # C/W, 4-layer JC51-7, natural convection
T_REG_C = 110.0            # block diagram label on thermal regulation
T_SD_C = 150.0             # thermal shutdown typical
TIMER_TYP_H = 6.0
TIMER_MIN_H = 5.4
TIMER_MAX_H = 6.6
CELL_AH = 4.5              # P45B typical capacity
CELL_CHARGE_A = 4.5        # P45B standard charge
CELL_CHARGE_H = 1.5        # P45B standard charge time
NEST_V = 9.5               # D61 figure, calc only in that decision
OLD_W_72 = 1.9             # existing heat band at a 7.2 V pack
OLD_W_60 = 3.2             # existing heat band at a 6.0 V pack
TVS_VR_V = 10.0            # SMAJ10A standoff
TVS_VC_V = 17.0            # SMAJ10A clamp at Ipp
RDS_MOHM_45 = 45.0         # DMP2045U max at VGS = -4.5 V
FET_VGS_ABS_V = 8.0        # DMP2045U gate absolute max

# Adafruit 372 lookup table rows used for the window, kohm. Source URL in the markdown.
NTC_KOHM = {
    -1: 33.33, 0: 31.77, 1: 30.25, 2: 28.82,
    58: 2.659, 59: 2.564, 60: 2.472, 61: 2.384, 62: 2.299,
}
RBIAS_KOHM = 10.0
R_COLD_BOT_KOHM = 31.6
R_HOT_BOT_KOHM = 2.49


def ireg_ma(r_kohm):
    return IREG_SCALE * (r_kohm ** IREG_EXP)


def rprog_kohm(i_ma):
    # inverse of equation 5-1, which is equation 5-2 in the sheet
    return 10 ** (math.log10(i_ma / IREG_SCALE) / IREG_EXP)


def power_w(vin, vbat, i_a):
    return (vin - vbat) * i_a


def ntc_ratio(r_kohm, rbias=RBIAS_KOHM):
    return r_kohm / (rbias + r_kohm)


def temp_for_ratio(ratio):
    """Linear interpolation of the copied lookup rows. Returns C."""
    items = sorted(NTC_KOHM.items())
    # ratio falls as temperature rises
    pairs = [(t, ntc_ratio(r)) for t, r in items]
    for (t0, q0), (t1, q1) in zip(pairs, pairs[1:]):
        if (q0 - ratio) * (q1 - ratio) <= 0:
            if q0 == q1:
                return t0
            return t0 + (t1 - t0) * (q0 - ratio) / (q0 - q1)
    raise SystemExit("ratio %.4f is outside the copied NTC rows" % ratio)


def main():
    fails = []
    ncheck = [0]

    def check(name, ok, detail):
        ncheck[0] += 1
        print("%-28s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
        if not ok:
            fails.append(name)

    i_eq = ireg_ma(RPROG_KOHM)
    check("eq 5-1 at 1.10 kOhm",
          IREG_SPEC_MIN_MA <= i_eq <= IREG_SPEC_MAX_MA,
          "IREG = %.1f mA (spec typical %g, window %g to %g)" % (
              i_eq, IREG_SPEC_TYP_MA, IREG_SPEC_MIN_MA, IREG_SPEC_MAX_MA))
    check("eq 5-1 near the 1000 mA row",
          abs(i_eq - IREG_SPEC_TYP_MA) <= 20.0,
          "equation %.1f mA versus table/spec typical %g mA" % (i_eq, IREG_SPEC_TYP_MA))
    check("inverse returns 1.10 kOhm",
          abs(rprog_kohm(i_eq) - RPROG_KOHM) < 1e-6,
          "RPROG back-calculated %.4f kOhm" % rprog_kohm(i_eq))
    # table spot checks of equation 5-1 against Table 5-1 endpoints
    check("10 kOhm is the 130 mA row",
          abs(ireg_ma(10.0) - 130.0) < 2.0,
          "equation gives %.1f mA" % ireg_ma(10.0))
    check("1.00 kOhm is the 1100 mA row",
          abs(ireg_ma(1.00) - 1100.0) < 5.0,
          "equation gives %.1f mA (the scale constant is 1104, the table prints 1100)" % ireg_ma(1.00))

    vpth_typ = VPTH_RATIO_TYP * VREG_TYP_V
    vpth_min = VPTH_RATIO_MIN * VREG_MIN_V
    vdd_min = VREG_TYP_V + HEADROOM_V
    check("precondition near 6.0 V",
          abs(vpth_typ - 6.006) < 0.01,
          "0.715 * 8.40 = %.3f V" % vpth_typ)
    check("nest above characterized min",
          NEST_V > vdd_min,
          "9.5 V versus VREG+0.3 = %.2f V" % vdd_min)
    check("nest under TVS standoff",
          NEST_V < TVS_VR_V,
          "9.5 V versus SMAJ10A VR %g V" % TVS_VR_V)
    check("TVS clamp under chip abs max",
          TVS_VC_V < VDD_ABS_MAX_V,
          "clamp %g V versus abs max %g V" % (TVS_VC_V, VDD_ABS_MAX_V))
    check("OVP above the nest",
          OVP_TYP_V > NEST_V,
          "OVP %g V, nest %g V" % (OVP_TYP_V, NEST_V))

    p72 = power_w(NEST_V, 7.2, IREG_SPEC_TYP_MA / 1000.0)
    p60 = power_w(NEST_V, 6.0, IREG_SPEC_TYP_MA / 1000.0)
    p84 = power_w(NEST_V, VREG_TYP_V, IREG_SPEC_TYP_MA / 1000.0)
    check("heat at 7.2 V above the old 1.9 W",
          p72 > OLD_W_72,
          "%.2f W at 9.5 V and 1.00 A, old band %.1f W" % (p72, OLD_W_72))
    check("heat at 6.0 V above the old 3.2 W",
          p60 > OLD_W_60,
          "%.2f W at 9.5 V and 1.00 A, old band %.1f W" % (p60, OLD_W_60))
    # the old band implies a lower input if the current is 1.00 A
    vin_old_72 = 7.2 + OLD_W_72 / 1.0
    vin_old_60 = 6.0 + OLD_W_60 / 1.0
    print("%-28s %s  %s" % (
        "old band implied input", "INFO",
        "7.2 V pack implies %.1f V, 6.0 V pack implies %.1f V, both under the 9.5 V figure" % (
            vin_old_72, vin_old_60)))

    p_worst = power_w(NEST_V, vpth_min, IREG_SPEC_MAX_MA / 1000.0)
    rise_worst = p_worst * THETA_JA
    check("eq 6-1 exceeds 110 C rise",
          rise_worst > (T_REG_C - 25.0),
          "P = %.2f W at VPTH min %.3f V and 1.10 A, rise %.0f C on 62 C/W" % (
              p_worst, vpth_min, rise_worst))

    def i_hold(tamb, vbat):
        pmax = (T_REG_C - tamb) / THETA_JA
        return pmax / (NEST_V - vbat), pmax

    for tamb in (25.0, 32.0):
        for vbat in (6.0, 7.2, 8.2):
            i_a, pmax = i_hold(tamb, vbat)
            print("%-28s %s  %s" % (
                "foldback I", "INFO",
                "Tamb %g C, Vbat %.1f V: %.3f A to hold the die at %g C (Pmax %.3f W)" % (
                    tamb, vbat, i_a, T_REG_C, pmax)))

    # charge time if the current stayed at 1.00 A. CC hours from the nameplate,
    # plus the 0.5 h by which the sheet's 1.5 h standard charge exceeds 4.5 Ah / 4.5 A.
    cc_h = CELL_AH / (IREG_SPEC_TYP_MA / 1000.0)
    cv_tail_h = CELL_CHARGE_H - (CELL_AH / CELL_CHARGE_A)
    t_full = cc_h + cv_tail_h
    check("1 A charge inside the 6.6 h timer max",
          t_full < TIMER_MAX_H,
          "CC %.2f h plus the sheet's %.2f h standard-charge tail = %.2f h (timer %g to %g h)" % (
              cc_h, cv_tail_h, t_full, TIMER_MIN_H, TIMER_MAX_H))
    check("1 A charge versus the 5.4 h timer min",
          True,
          "%.2f h is %s the %.1f h minimum timer. The tail is the standard-charge difference, not a proof at 1 A." % (
              t_full, "under" if t_full < TIMER_MIN_H else "over", TIMER_MIN_H))

    i6, _ = i_hold(32.0, 6.0)
    t_slow = CELL_AH / i6 + cv_tail_h
    check("6 V foldback current misses the timer",
          t_slow > TIMER_MAX_H,
          "if 4.5 Ah were taken at the 6.0 V foldback current %.3f A, %.1f h, past %.1f h" % (
              i6, t_slow, TIMER_MAX_H))

    q0 = ntc_ratio(NTC_KOHM[0])
    q60 = ntc_ratio(NTC_KOHM[60])
    q_cold = R_COLD_BOT_KOHM / (RBIAS_KOHM + R_COLD_BOT_KOHM)
    q_hot = R_HOT_BOT_KOHM / (RBIAS_KOHM + R_HOT_BOT_KOHM)
    t_cold = temp_for_ratio(q_cold)
    t_hot = temp_for_ratio(q_hot)
    check("cold divider near 0 C",
          abs(t_cold - 0.0) <= 1.0,
          "31.6k/10k trips at %.2f C (0 C ratio %.4f, divider %.4f)" % (t_cold, q0, q_cold))
    check("hot divider near 60 C",
          abs(t_hot - 60.0) <= 1.0,
          "2.49k/10k trips at %.2f C (60 C ratio %.4f, divider %.4f)" % (t_hot, q60, q_hot))

    # cell rate
    c_rate = (IREG_SPEC_TYP_MA / 1000.0) / CELL_CHARGE_A
    check("1.00 A is under the 4.5 A standard charge",
          (IREG_SPEC_TYP_MA / 1000.0) < CELL_CHARGE_A,
          "%.3f C of the 4.5 A standard charge" % c_rate)

    # FET drop at the stripe study's 2.8 A peak, using the 45 mohm max at -4.5 V
    i_peak = 2.8
    drop = i_peak * RDS_MOHM_45 / 1000.0
    heat = i_peak * drop
    check("P-FET drop at 2.8 A",
          drop < 0.30,
          "%.3f V and %.3f W at %g mohm max" % (drop, heat, RDS_MOHM_45))
    check("zener aim under the 8 V gate max",
          4.7 < FET_VGS_ABS_V,
          "4.7 V candidate versus %g V absolute max" % FET_VGS_ABS_V)

    # end-of-charge termination and headroom budget
    iterm = 0.10 * IREG_SPEC_TYP_MA / 1000.0
    budget_ohm = (NEST_V - vdd_min) / (IREG_SPEC_TYP_MA / 1000.0)
    print("%-28s %s  %s" % (
        "termination and headroom", "INFO",
        "10 percent of 1.00 A is %.2f A. Round-trip drop budget at 1.00 A before Vin falls to %.2f V is %.2f ohm." % (
            iterm, vdd_min, budget_ohm)))
    print("%-28s %s  %s" % (
        "CV heat at 8.40 V", "INFO",
        "%.2f W if 1.00 A were still flowing at VREG. Current is tapering there." % p84))

    doc = yaml.safe_load(open(YAML_PATH, encoding="utf-8"))
    parts = {c["id"]: c for c in doc["components"]}
    check("yaml has the charger",
          "CU1" in parts and "MCP73213-A6SI/MF" in parts["CU1"]["part"],
          parts.get("CU1", {}).get("part", "missing"))
    rprog = parts.get("CRPROG", {})
    check("yaml resistor is 1.10 kOhm",
          "1.10" in str(rprog.get("part", "")) or "1.10" in str(rprog.get("ratings", {})),
          str(rprog.get("part", "missing")))
    check("yaml has STAT and EN",
          "STAT" in doc["nets"] and "EN" in doc["nets"],
          "nets %s" % ", ".join(sorted(doc["nets"])))
    # every non-nc pin is an end of some wire
    wired = set()
    for w in doc["wires"]:
        wired.add(w["from"])
        wired.add(w["to"])
    missing = []
    for c in doc["components"]:
        for p in c.get("pins") or []:
            ref = "%s.%s" % (c["id"], p["pin"])
            if p.get("dir") != "nc" and ref not in wired:
                missing.append(ref)
    check("yaml pins are wired",
          not missing,
          "unwired: %s" % ", ".join(missing[:12]) if missing else "none")

    if os.path.exists(MD_PATH):
        text = open(MD_PATH, encoding="utf-8").read()
        check("markdown has no em dash",
              "\u2014" not in text and "\u2013" not in text,
              "em or en dash count")
        for needle in ("DS20002190C", "MCP73213-A6SI/MF", "1.10", "SMAJ10A", "INR21700-P45B"):
            check("markdown cites %s" % needle, needle in text, "present" if needle in text else "missing")
        # the heat numbers the prose must match this script
        check("markdown quotes 2.30 W", "2.30" in text, "7.2 V heat")
        check("markdown quotes 3.50 W", "3.50" in text, "6.0 V heat")
    else:
        print("%-28s %s  %s" % ("markdown", "INFO", "CHARGER_BOARD.md not written yet"))

    if os.path.exists(SCH_PATH):
        sch = open(SCH_PATH, encoding="utf-8").read()
        check("kicad names the chip", "MCP73213-A6SI/MF" in sch, "symbol value")
        check("kicad names 1.10 kOhm", "1.10" in sch, "resistor value")
        check("kicad is s-expression", sch.strip().startswith("(kicad_sch"), "header")
    else:
        print("%-28s %s  %s" % ("kicad", "INFO", "schematic not written yet"))

    print("")
    print("%d checks, %d failed" % (ncheck[0], len(fails)))
    # print a stable summary the markdown quotes
    print("SUMMARY i_eq_mA %.1f" % i_eq)
    print("SUMMARY p_7v2_W %.2f" % p72)
    print("SUMMARY p_6v0_W %.2f" % p60)
    print("SUMMARY p_worst_W %.2f" % p_worst)
    print("SUMMARY vpth_typ_V %.3f" % vpth_typ)
    print("SUMMARY vdd_min_V %.2f" % vdd_min)
    print("SUMMARY t_full_h %.2f" % t_full)
    print("SUMMARY t_cold_C %.2f" % t_cold)
    print("SUMMARY t_hot_C %.2f" % t_hot)
    print("SUMMARY i_fold_32C_6V_A %.3f" % i6)
    print("SUMMARY fet_drop_2p8_V %.3f" % drop)
    print("SUMMARY headroom_ohm %.2f" % budget_ohm)
    if fails:
        print("FAILED: %s" % ", ".join(fails))
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
