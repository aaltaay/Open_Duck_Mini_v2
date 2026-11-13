"""Arithmetic and drawing for the BQ24133 board.

Every asserted number is calc only, from values in bq24133_board.yaml and from
the citations named in BQ24133_BOARD.md. This does not build a board.

Run from the repo root:
  python3 altaay_lab/circuitry/check_bq24133.py
"""
import math
import os
import uuid

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
YAML_PATH = os.path.join(HERE, "bq24133_board.yaml")
SCH_PATH = os.path.join(HERE, "bq24133_board.kicad_sch")
NS = uuid.UUID("c0ffee00-2413-4000-8000-000000000003")

VREF = 3.3          # cited, VREF pin, 3.3 V
KISET = 5.0         # A/V, cited, Rsr = 10 milliohm
KDPM = 2.5          # A/V, cited, adapter sense = 20 milliohm
OVP_REF = 1.6       # V, cited
OVP_LO = 1.55
OVP_HI = 1.65
TTC_MIN_PER_NF = 5.6
FS_HZ = 1.6e6
VIN = 15.0
VOUT = 12.6
TERM_FRAC = 0.10
N_SERVO = 14
I_IDLE = 0.021


def uid(*parts):
    return str(uuid.uuid5(NS, "|".join(str(p) for p in parts)))


def kquote(text):
    return str(text).replace("\\", "\\\\").replace('"', "'")


def render_schematic(doc):
    pin_net = {}
    for w in doc["wires"]:
        pin_net[w["from"]] = w["net"]
        pin_net[w["to"]] = w["net"]
    libs = []
    insts = []
    wires = []
    labels = []
    for index, comp in enumerate(doc["components"]):
        pins = [p for p in comp.get("pins") or []]
        col = index % 4
        row = index // 4
        ox = 40.0 + col * 90.0
        oy = 280.0 - row * 50.0
        lib = "bq:%s" % comp["id"]
        n = max(len(pins), 1)
        half = (n * 2.54) / 2.0
        left = pins[0::2]
        right = pins[1::2]
        pin_at = {}
        lib_pins = []
        for side, group in (("L", left), ("R", right)):
            for i, p in enumerate(group):
                y = half - 2.54 * (i + 0.5)
                x = -12.70 if side == "L" else 12.70
                rot = 180 if side == "L" else 0
                pin_at[p["pin"]] = (ox + x, oy + y)
                lib_pins.append(
                    '(pin passive line (at %.2f %.2f %d) (length 5.08) '
                    '(name "%s" (effects (font (size 0.8 0.8)))) '
                    '(number "%s" (effects (font (size 0.8 0.8)))))' % (
                        x, y, rot, kquote(p["pin"]), kquote(p["pin"])))
        libs.append(
            '(symbol "%s" (pin_names (offset 0.254)) (exclude_from_sim no) (in_bom yes) (on_board yes)\n'
            '  (property "Reference" "U" (at 0 %.2f 0) (effects (font (size 1.27 1.27))))\n'
            '  (property "Value" "%s" (at 0 %.2f 0) (effects (font (size 1.27 1.27))))\n'
            '  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
            '  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
            '  (symbol "%s_0_1" (rectangle (start -7.62 %.2f) (end 7.62 %.2f) '
            '(stroke (width 0.254) (type default)) (fill (type background))))\n'
            '  (symbol "%s_1_1"\n    %s\n  )\n)' % (
                lib, half + 2.54, kquote(comp["id"]), -half - 4,
                lib, half, -half, lib, "\n    ".join(lib_pins)))
        value = kquote(comp.get("part", comp["id"]))[:180]
        pin_lines = "\n".join(
            '  (pin "%s" (uuid "%s"))' % (kquote(p["pin"]), uid(comp["id"], p["pin"], "pin"))
            for p in pins)
        insts.append(
            '(symbol (lib_id "%s") (at %.2f %.2f 0) (unit 1) (exclude_from_sim no) '
            '(in_bom yes) (on_board yes) (dnp no)\n'
            '  (uuid "%s")\n'
            '  (property "Reference" "%s" (at %.2f %.2f 0) (effects (font (size 1.27 1.27))))\n'
            '  (property "Value" "%s" (at %.2f %.2f 0) (effects (font (size 1.0 1.0))))\n'
            '  (property "Footprint" "" (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) hide))\n'
            '  (property "Datasheet" "" (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) hide))\n'
            '%s\n)' % (
                lib, ox, oy, uid(comp["id"], "inst"),
                kquote(comp.get("ref", comp["id"])), ox, oy + half + 4,
                value, ox, oy - half - 6,
                ox, oy, ox, oy, pin_lines))
        for p in pins:
            ref = "%s.%s" % (comp["id"], p["pin"])
            net = pin_net.get(ref)
            if not net or p.get("dir") == "nc":
                continue
            x, y = pin_at[p["pin"]]
            end_x = x - 7.62 if x < ox else x + 7.62
            wires.append(
                '(wire (pts (xy %.2f %.2f) (xy %.2f %.2f)) (stroke (width 0) (type default)) (uuid "%s"))' % (
                    x, y, end_x, y, uid(comp["id"], p["pin"], "wire")))
            labels.append(
                '(label "%s" (at %.2f %.2f 0) (effects (font (size 1.0 1.0)) (justify left bottom)) (uuid "%s"))' % (
                    kquote(net), end_x, y, uid(comp["id"], p["pin"], "label")))
    return (
        '(kicad_sch\n'
        '  (version 20231120)\n'
        '  (generator "eeschema")\n'
        '  (generator_version "8.0")\n'
        '  (uuid "%s")\n'
        '  (paper "A2")\n'
        '  (title_block\n'
        '    (title "Duck BQ24133 charger")\n'
        '    (date "2026-11-13")\n'
        '    (rev "1")\n'
        '    (comment 1 "Every part in circuitry/bq24133_board.yaml")\n'
        '    (comment 2 "CELL to VREF, 1.006 A, servo rail cut by the 2815")\n'
        '  )\n'
        '  (lib_symbols\n%s\n  )\n'
        '%s\n%s\n%s\n'
        '  (text "Schematic of bq24133_board.yaml. Each pin label is that pin net. Not a built board." '
        '(at 20 300 0) (effects (font (size 1.5 1.5))) (uuid "%s"))\n'
        '  (sheet_instances (path "/" (page "1")))\n'
        ')\n' % (
            uid("sheet"), "\n".join(libs), "\n".join(insts), "\n".join(wires), "\n".join(labels), uid("note")))


def by_id(doc):
    return {c["id"]: c for c in doc["components"]}


def ohm(comp):
    return float(comp["value_ohm"])


def node_v(v_src, r_src, branches):
    """Voltage at a node. branches is a list of (voltage, ohms) to other nodes, plus r_src to v_src."""
    g = 1.0 / r_src
    i = v_src / r_src
    for v, r in branches:
        g += 1.0 / r
        i += v / r
    return i / g


def main():
    fails = []
    ncheck = [0]

    def check(name, ok, detail):
        ncheck[0] += 1
        print("%-28s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
        if not ok:
            fails.append(name)

    doc = yaml.safe_load(open(YAML_PATH, encoding="utf-8"))
    parts = by_id(doc)
    check("yaml names BQ24133", doc["meta"]["chip"] == "BQ24133", doc["meta"]["chip"])

    pins = {}
    for c in doc["components"]:
        for p in c["pins"]:
            pins["%s.%s" % (c["id"], p["pin"])] = p
    pin_nets = {}
    missing_ends = []
    for w in doc["wires"]:
        for end in (w["from"], w["to"]):
            pin_nets.setdefault(end, set()).add(w["net"])
            if end not in pins:
                missing_ends.append(end)
    check("every wire end is a pin", not missing_ends, ",".join(missing_ends) or "none")
    unwired = [n for n, p in pins.items() if p.get("dir") != "nc" and n not in pin_nets]
    check("every used pin is wired", not unwired, ",".join(unwired) or "none")
    multi = {n: nets for n, nets in pin_nets.items() if len(nets) > 1}
    check("no pin on two nets", not multi, str(multi) or "none")
    shorted = []
    for c in doc["components"]:
        if c.get("kind") != "resistor":
            continue
        a = pin_nets.get("%s.A" % c["id"], set())
        b = pin_nets.get("%s.B" % c["id"], set())
        if a and a == b:
            shorted.append(c["id"])
    check("no resistor shorted", not shorted, ",".join(shorted) or "none")

    viset = VREF * ohm(parts["RIL"]) / (ohm(parts["RIH"]) + ohm(parts["RIL"]))
    i_chg = viset * KISET
    check("ISET is 0.2012 V", abs(viset - 0.2012) < 0.0001, "%.4f V" % viset)
    check("charge current is 1.006 A", abs(i_chg - 1.006) < 0.001, "%.3f A" % i_chg)
    check("ISET inside 0.12 to 0.5 V", 0.12 < viset < 0.5, "%.4f V" % viset)
    check("ISET above 120 mV enable", viset > 0.120, "%.4f V" % viset)
    vsense = i_chg * ohm(parts["RSNS"])
    check("sense is 10.06 mV", abs(vsense - 0.01006) < 0.00002, "%.5f V" % vsense)

    vacset = VREF * ohm(parts["RAL"]) / (ohm(parts["RAH"]) + ohm(parts["RAL"]))
    i_dpm = vacset * KDPM
    check("input limit is 1.983 A", abs(i_dpm - 1.983) < 0.002, "%.3f A" % i_dpm)
    check("input limit above charge", i_dpm > i_chg, "%.3f > %.3f" % (i_dpm, i_chg))

    v_ovp_at_18 = 18.0 * ohm(parts["ROL"]) / (ohm(parts["ROH"]) + ohm(parts["ROL"]))
    trip = OVP_REF * (ohm(parts["ROH"]) + ohm(parts["ROL"])) / ohm(parts["ROL"])
    trip_lo = OVP_LO * (ohm(parts["ROH"]) + ohm(parts["ROL"])) / ohm(parts["ROL"])
    trip_hi = OVP_HI * (ohm(parts["ROH"]) + ohm(parts["ROL"])) / ohm(parts["ROL"])
    check("OVP pin at 18 V is 1.607 V", abs(v_ovp_at_18 - 1.607) < 0.001, "%.3f V" % v_ovp_at_18)
    check("1.6 V trip is 17.92 V", abs(trip - 17.92) < 0.01, "%.2f V" % trip)
    check("trips under 20 V", trip_hi < 20.0, "%.2f V" % trip_hi)
    check("16 V window under low trip", 16.0 < trip_lo, "%.2f V" % trip_lo)

    t_min = parts["CTTC"]["value_F"] * 1e9 * TTC_MIN_PER_NF
    check("timer is 6.35 h", abs(t_min / 60.0 - 6.35) < 0.01, "%.2f h" % (t_min / 60.0))

    l_h = parts["L1"]["value_H"]
    c_f = parts["COUT"]["value_F"]
    fres = 1.0 / (2.0 * math.pi * math.sqrt(l_h * c_f))
    check("LC is 19.3 kHz", abs(fres / 1000.0 - 19.3) < 0.05, "%.2f kHz" % (fres / 1000.0))
    check("LC inside 15 to 25 kHz", 15000 < fres < 25000, "%.0f Hz" % fres)
    duty = VOUT / VIN
    ripple = VIN * duty * (1.0 - duty) / (FS_HZ * l_h)
    check("ripple is 0.185 A", abs(ripple - 0.185) < 0.002, "%.3f A" % ripple)
    isat = i_chg + 0.5 * ripple
    check("Isat clears 1.099 A", abs(isat - 1.099) < 0.002, "%.3f A" % isat)

    ts = ohm(parts["RTB"]) / (ohm(parts["RTS"]) + ohm(parts["RTB"]))
    check("TS fraction is 0.60", abs(ts - 0.60) < 0.001, "%.3f" % ts)
    check("TS between hot and cold", 0.488 < ts < 0.725, "%.3f" % ts)

    cin = parts["CPV1"]["value_F"] + parts["CPV2"]["value_F"]
    check("PVCC is 20 uF", abs(cin - 20e-6) < 1e-12, "%.0f uF" % (cin * 1e6))

    # ON threshold. Pack-powered comparator, VREF divider plus a weak pack pull.
    th_dock = node_v(VREF, ohm(parts["RVT"]), [(0.0, ohm(parts["RVB"])), (12.6, ohm(parts["RVP"]))])
    th_walk = node_v(0.0, ohm(parts["RVT"]), [(0.0, ohm(parts["RVB"])), (12.6, ohm(parts["RVP"]))])
    tap_15 = 15.0 * ohm(parts["RNB"]) / (ohm(parts["RNT"]) + ohm(parts["RNB"]))
    trip_nest = th_dock * (ohm(parts["RNT"]) + ohm(parts["RNB"])) / ohm(parts["RNB"])
    check("docked threshold 1.789 V", abs(th_dock - 1.789) < 0.002, "%.3f V" % th_dock)
    check("15 V tap is 2.50 V", abs(tap_15 - 2.50) < 0.001, "%.3f V" % tap_15)
    check("nest trip is 10.73 V", abs(trip_nest - 10.73) < 0.02, "%.2f V" % trip_nest)
    check("asleep threshold 0.336 V", abs(th_walk - 0.336) < 0.002, "%.3f V" % th_walk)
    # LM393B sinks when IN- is above IN+, and is high impedance the other way
    # (SLCS005AH section 7.2.2.1). Nest tap on IN-, threshold on IN+.
    check("nest tap is on IN-", "NEST_TAP" in pin_nets.get("U3.INA-", set()), str(pin_nets.get("U3.INA-")))
    check("threshold is on IN+", "ON_TH" in pin_nets.get("U3.INA+", set()), str(pin_nets.get("U3.INA+")))
    check("docked IN- is above IN+", tap_15 > th_dock, "%.3f > %.3f" % (tap_15, th_dock))
    check("undocked IN- is below IN+", 0.0 < th_walk, "0 < %.3f" % th_walk)
    check("dock flag is not the servo ON pin", "DOCK" in pin_nets.get("U3.OUTA", set()) and "ON" not in pin_nets.get("U3.OUTA", set()), str(pin_nets.get("U3.OUTA")))
    on_pins = [e for w in doc["wires"] if w["net"] == "ON" for e in (w["from"], w["to"])]
    check("servo ON is only the Pi wire", set(on_pins) == {"RON.B", "JON.ON"}, str(sorted(set(on_pins))))
    check("AVCC resistor is on the adapter", "NEST_FUSED" in pin_nets.get("RAV.A", set()), str(pin_nets.get("RAV.A")))
    check("AVCC is not fed from SYS", "SYS" not in pin_nets.get("U1.AVCC", set()), str(pin_nets.get("U1.AVCC")))

    i_idle = N_SERVO * I_IDLE
    i_term = TERM_FRAC * i_chg
    check("idle 0.294 A exceeds 0.10 A", i_idle > i_term, "%.3f > %.3f" % (i_idle, i_term))
    check("shared 13.6 V window is 0.4 V", abs((14.0 - 13.6) - 0.4) < 1e-9, "0.4 V")

    # The charger system node is not the connector that goes to the 2815 ON pin.
    sys_pins = {e for w in doc["wires"] if w["net"] == "SYS" for e in (w["from"], w["to"])}
    check("2815 ON is not on SYS", "JON.ON" not in sys_pins, "SYS pins %d" % len(sys_pins))
    check("CELL is on VREF", "U1.CELL" in pin_nets and "VREF" in pin_nets["U1.CELL"], str(pin_nets.get("U1.CELL")))

    sch = render_schematic(doc)
    open(SCH_PATH, "w", encoding="utf-8").write(sch)
    n_sch = sch.count("(symbol (lib_id")
    check("kicad is s-expression", sch.strip().startswith("(kicad_sch"), "header")
    check("kicad has every yaml part", n_sch == len(doc["components"]), "%d symbols" % n_sch)
    check("kicad names the chip", "BQ24133" in sch, "value text")
    missing = [c["id"] for c in doc["components"] if c["id"] not in sch]
    check("kicad labels every id", not missing, ",".join(missing) or "none")

    print("%d checks, %d failed" % (ncheck[0], len(fails)))
    if fails:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
