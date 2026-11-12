#!/usr/bin/env python3
"""Build the harness wire list from wiring/netlist.yaml.

Reuses the netlist, the D36 connector families, and the charger-board pins.
Does not edit the netlist. Numbers in the output are either copied from the
netlist or marked calc only, CAD check only, cited, or BLOCKER.
"""
import os

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
NET_PATH = os.path.join(LAB, "wiring", "netlist.yaml")
OUT = os.path.join(HERE, "WIRES.md")

# Molex KK 254, series chart https://www.molex.com/en-us/products/series-chart/2695
# and the 2-circuit sheet (part 0022012027). Friction-ramp housings.
# The chart prints 22012027; the sheet prints 0022012027. Same number.
KK_HOUSING = {
    2: "0022012027",
    3: "0022012037",
    5: "0022012057",
}
KK_CONTACT = "08-50-0114"  # 2759 brass, 22 to 30 AWG, 2.5 A, insulation 1.57 mm max
SPOX_HOUSING = "50-37-5033"
SPOX_CONTACT = "08-70-1040"  # 22 to 28 AWG, 3.0 A on 22 AWG, recorded in CABLE_MAP.md


def load():
    with open(NET_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def pin_of(comps, ref):
    comp_id, pin = ref.split(".", 1)
    c = comps[comp_id]
    for p in c.get("pins") or []:
        if str(p["pin"]) == pin:
            return c, p
    return c, None


def awg_of(gauge):
    if isinstance(gauge, str) and gauge.endswith(" AWG") and gauge.split()[0].isdigit():
        return int(gauge.split()[0])
    return None


def fmt_a(v):
    if v is None:
        return None
    if v >= 0.1:
        return "%g" % v
    return "%.4g" % v


def main():
    net = load()
    comps = {c["id"]: c for c in net["components"]}
    cables = {c["id"]: c for c in net["cables"]}
    wires = [w for w in net["wires"] if cables[w["cable"]].get("status", "active") == "active"]

    # Pi header: which cable owns the one crimp on a shared pin.
    # 08-50-0114 is one conductor. A second wire is spliced to that one.
    pi_hits = {}
    for w in wires:
        for ref in (w["from"], w["to"]):
            if ref.startswith("PI.") and ref.split(".", 1)[1].isdigit():
                pi_hits.setdefault(ref, []).append(w)

    owner_rank = ["D2", "D5", "D10", "D3", "D4", "D6", "D7", "D14", "D13", "D16", "D22", "D8", "D9"]

    def owner_cable(ref):
        hits = pi_hits.get(ref, [])
        crimpable = []
        for w in hits:
            g = awg_of(w["gauge"])
            if g is not None and 22 <= g <= 30:
                crimpable.append(w["cable"])
        for c in owner_rank:
            if c in crimpable:
                return c
        return crimpable[0] if crimpable else None

    # Housing groups. Positions are the order along one header row.
    # D2 covers odd pins 1, 3, 5, 7, 9. Pin 7 stays empty (GPIO4 is not used).
    d2_pos = {"PI.1": 1, "PI.3": 2, "PI.5": 3, "PI.9": 5}
    eye_pos = {"PI.16": 1, "PI.18": 2, "PI.20": 3}  # pin 16 is D6, pin 18 and 20 are D5
    # Charger pins are not in this netlist. They are added after the loop.

    wago = {
        ("P14", "G.S"): "WAGO 221-415 port 1, ground lever",
        ("P10", "G.S"): "WAGO 221-415 port 2, ground lever",
        ("P13", "G.S"): "WAGO 221-415 port 3, ground lever",
        ("P16", "G.S"): "WAGO 221-415 port 4, ground lever",
        ("P9", "VSW.S"): "WAGO 221-413 port 1, switched plus lever",
        ("P10", "VSW.S"): "WAGO 221-413 port 2, switched plus lever",
        ("P13", "VSW.S"): "WAGO 221-413 port 3, switched plus lever",
        ("P11", "SPV.S"): "WAGO 221-415 port 1, servo plus lever",
        ("SP1", "SPV.S"): "WAGO 221-415 port 2, servo plus lever",
        ("SP2", "SPV.S"): "WAGO 221-415 port 3, servo plus lever",
        ("SP3", "SPV.S"): "WAGO 221-415 port 4, servo plus lever",
        ("SP4", "SPV.S"): "WAGO 221-413 port 2, servo plus small lever",
        ("SP5", "SPV.S"): "WAGO 221-413 port 3, servo plus small lever",
        ("P11", "SPG.S"): "WAGO 221-415 port 1, servo ground lever",
        ("SP1", "SPG.S"): "WAGO 221-415 port 2, servo ground lever",
        ("SP2", "SPG.S"): "WAGO 221-415 port 3, servo ground lever",
        ("SP3", "SPG.S"): "WAGO 221-415 port 4, servo ground lever",
        ("SP4", "SPG.S"): "WAGO 221-413 port 2, servo ground small lever",
        ("SP5", "SPG.S"): "WAGO 221-413 port 3, servo ground small lever",
    }

    gaps = []
    lines = []

    def add_gap(kind, text):
        gaps.append((kind, text))

    def end_text(w, ref, end):
        """Return (plain text, kind) for one end. kind is used by the gauge check."""
        c, p = pin_of(comps, ref)
        label = ""
        if p is None:
            add_gap("FIX", "%s %s has no pin on %s." % (w["cable"], ref, c["id"]))
            return ("BLOCKER: %s is not a pin on %s." % (ref, c["id"]), "missing")
        if "[I]" in str(p.get("source", "")) and ref not in getattr(end_text, "_seen", set()):
            end_text._seen = getattr(end_text, "_seen", set())
            if ref not in end_text._seen:
                end_text._seen.add(ref)
                add_gap("BLOCKER", "%s label is not checked on the part (%s)." % (ref, p.get("source")))
        name = p.get("name") or p.get("label")
        base = "%s pin %s (%s)" % (c.get("ref") or c["id"], p["pin"], name)

        key = (w["cable"], ref)
        if key in wago:
            part = c.get("part") or ""
            conn = ((c.get("groups") or {}).get(p.get("group") or "", {}) or {}).get("connector") or ""
            if "WAGO" not in part and "WAGO" not in conn:
                add_gap("FIX", "%s at %s was a solder splice with no part number. It is now %s." % (
                    w["cable"], ref, wago[key]))
            return (base + ". " + wago[key] + ". No separate contact: the lever clamps the bare wire.", "wago")

        if ref.startswith("PI.") and ref.split(".")[1].isdigit():
            g = awg_of(w["gauge"])
            own = owner_cable(ref)
            if g == 20:
                add_gap("FIX", "%s %s is 20 AWG. Molex 08-50-0114 takes 22 to 30 AWG only (cited). "
                        "Solder it to the header pin, as docs/assembly_guide.md does." % (w["cable"], ref))
                return (base + ". Solder to the header pin. Not a KK crimp: 20 AWG is outside 22 to 30 AWG "
                        "(cited, Molex 08-50-0114 sheet).", "solder20")
            if w["gauge"] in ("resistor lead", "SG90 lead"):
                return (base + ". Solder. This lead is not a 22 to 30 AWG wire, so it does not go in 08-50-0114.", "partlead")
            if own and w["cable"] != own and g is not None and 22 <= g <= 30:
                add_gap("FIX", "%s and %s both landed on %s. One 08-50-0114 takes one wire. "
                        "%s keeps the contact. %s is spliced to it." % (own, w["cable"], ref, own, w["cable"]))
                return (base + ". No second contact. Solder this wire to the %s wire on the same pin "
                        "(heat shrink). 26 AWG is below the WAGO 221 minimum of 24 AWG (cited)." % own, "splice26")
            if ref in d2_pos and w["cable"] == "D2":
                pos = d2_pos[ref]
                return (base + ". KK 254 housing %s position %d, contact %s." % (
                    KK_HOUSING[5], pos, KK_CONTACT), "kk")
            chg_pos = {"PI.29": 1, "PI.31": 2}
            if ref in chg_pos and w["cable"] == "CE":
                return (base + ". KK 254 housing %s position %d, contact %s." % (
                    KK_HOUSING[2], chg_pos[ref], KK_CONTACT), "kk")
            if ref in eye_pos and w["cable"] in ("D5", "D6"):
                # pin 20 owner is D5. D6 signal is pin 16, which is position 1 of the eye housing.
                if ref == "PI.16" and w["cable"] == "D6":
                    return (base + ". KK 254 housing %s position 1, contact %s." % (
                        KK_HOUSING[3], KK_CONTACT), "kk")
                if w["cable"] == "D5" and ref in ("PI.18", "PI.20"):
                    return (base + ". KK 254 housing %s position %d, contact %s." % (
                        KK_HOUSING[3], eye_pos[ref], KK_CONTACT), "kk")
            if "KK 254" in str(end):
                add_gap("FIX", "%s %s was a KK socket, but a 1-circuit friction-ramp part was not on the "
                        "Molex 2695 chart opened this pass. Solder to the header pin." % (w["cable"], ref))
                return (base + ". Solder to the header pin. A 1-circuit friction-ramp housing was not on the "
                        "series chart (the chart rows opened start at 2 circuits).", "solder1")
            return (base + ". Solder to the header pin (one wire, no 1-circuit locked housing on the chart).", "solder1")

        if "50-37-5033" in str(end) or "08-70-1040" in str(end):
            return (base + ". Mini-SPOX housing %s, contact %s. Latch on one side." % (
                SPOX_HOUSING, SPOX_CONTACT), "spox")
        if "5264" in str(end):
            return (base + ". Molded 5264 plug on the kit cable. Contact is part of that plug. Gauge not published.", "kit")
        if "XT30" in str(end):
            return (base + ". Amass XT30U solder cup. The shell is the key. No separate crimp contact.", "xt30")
        if "USB" in str(end) or "FPC" in str(end):
            return (base + ". The bought cable's own plug (" + str(end) + ").", "bought")
        if "WAGO" in str(end):
            return (base + ". " + str(end) + ".", "wago")
        if end in ("splice",) or (isinstance(end, str) and "splice" in end and "WAGO" not in end):
            return (base + ". Solder splice, heat shrink. Pin is " + ref + ". "
                    "Not a plug. 26 AWG cannot use WAGO 221, and the 221 pocket pack is already "
                    "used by the ground, switched-plus, and servo levers.", "splicesold")
        if isinstance(end, str) and end:
            return (base + ". " + end + ".", "partpad")
        add_gap("BLOCKER", "%s %s has no end treatment." % (w["cable"], ref))
        return (base + ". BLOCKER: no end treatment in the netlist.", "missing")

    def check(w, kinds):
        g = awg_of(w["gauge"])
        peak = w.get("i_peak_a")
        fall = w.get("i_fall_a")
        bits = []
        if w["gauge"] == "board" and w.get("cut_mm") == 0:
            bits.append("Soldered on the charger board (cut 0 mm). Not a free wire and not an AWG.")
        elif w["gauge"] in ("kit cable", "BEC lead", "SG90 lead", "USB 2.0 cable", "FPC ribbon",
                            "holder lead", "resistor lead", "board"):
            bits.append("BLOCKER for a gauge number: the netlist leaves this as \"%s\"." % w["gauge"])
        elif g is None:
            bits.append("BLOCKER: gauge \"%s\" is not an AWG." % w["gauge"])
        else:
            bits.append("Gauge %d AWG is the netlist value." % g)
        if "kk" in kinds:
            if g is not None and (g < 22 or g > 30):
                bits.append("FAIL vs cited Molex 08-50-0114 wire range 22 to 30 AWG.")
            elif g is not None:
                bits.append("Inside 22 to 30 AWG (cited, Molex 08-50-0114 / 2759 sheet).")
            if peak is not None:
                margin = 2.5 - peak
                bits.append("Peak %s A vs 2.5 A brass rating (cited, Molex 2759 catalog). Margin %s A (calc only)." % (
                    fmt_a(peak), fmt_a(margin)))
                if peak > 2.5:
                    bits.append("FAIL: peak is over 2.5 A.")
            bits.append("Insulation maximum 1.57 mm (cited, same 08-50-0114 sheet). "
                        "The 26 AWG outside diameter 1.5 mm plus or minus 0.1 mm is marked [I] in "
                        "sim/mass_budget.py and was not re-opened. BLOCKER for a sure fit.")
        if "spox" in kinds and g == 22:
            if peak is not None:
                margin = 3.0 - peak
                bits.append("Peak %s A vs 3.0 A on 22 AWG (cited, Molex 5263 figure recorded in CABLE_MAP.md, "
                            "read 2026-11-02). Margin %s A (calc only)." % (fmt_a(peak), fmt_a(margin)))
                if peak > 3.0:
                    bits.append("FAIL: peak is over 3.0 A.")
            else:
                bits.append("No peak in the netlist for this data wire. The 22 AWG contact is the one already used "
                            "on the power leads (3.0 A cited).")
        if "wago" in kinds and g is not None:
            if g < 12 or g > 24:
                bits.append("FAIL: WAGO 221 is 24 to 12 AWG (cited, 221-413 and 221-415 sheets).")
            else:
                bits.append("Inside 24 to 12 AWG (cited, WAGO 221-413 / 221-415).")
            top = peak if peak is not None else fall
            if fall is not None and (top is None or fall > top):
                top = fall
            if top is not None:
                bits.append("Highest netlist current on this wire %s A vs UL 20 A (cited, WAGO 221-413 sheet, "
                            "use group). Margin %s A (calc only)." % (fmt_a(top), fmt_a(20 - top)))
                if top > 20:
                    bits.append("FAIL: current is over 20 A.")
        if "xt30" in kinds:
            bits.append("XT30 continuous rating is marked [I] on BOM line 12. The Amass sheet was not opened "
                        "this pass. BLOCKER for a cited amp rating of the shell.")
        if "solder20" in kinds or (g == 16 and "wago" not in kinds and "xt30" not in kinds):
            bits.append("A wire-ampacity sheet for this silicone was not opened this pass. BLOCKER for the "
                        "copper's own amp rating. The gauge stays the netlist gauge.")
        if not bits:
            bits.append("No connector amp limit applies at this end. Gauge stays the netlist value.")
        return " ".join(bits)

    # Header
    lines.append("# Wire list")
    lines.append("")
    lines.append("Built by `wiring/harness/make_harness.py` from `wiring/netlist.yaml`. "
                 "Every active conductor in that file is below. The charger cable and the flush wells "
                 "are after the netlist list, because they are not in the netlist yet.")
    lines.append("")
    lines.append("Part numbers reused, not drawn up here:")
    lines.append("")
    lines.append("- Mini-SPOX housing 50-37-5033 and contact 08-70-1040, already BOM lines 21 and 22, "
                 "for every servo plug.")
    lines.append("- KK 254 contact 08-50-0114, already BOM line 22b. Brass, 22 to 30 AWG, 2.5 A, "
                 "insulation 1.57 mm maximum. Cited from the Molex 2759 sheet "
                 "(https://www.newbue.sg/datasheets/f5/08-50-0114.pdf) and the 2759 catalog page "
                 "(https://storage.sea.com.ua/tech_info/molex/MX2759.pdf).")
    lines.append("- KK 254 friction-ramp housings from the Molex 2695 series chart "
                 "(https://www.molex.com/en-us/products/series-chart/2695): "
                 "2 circuits 0022012027, 3 circuits 0022012037, 5 circuits 0022012057. "
                 "The 2-circuit datasheet prints 0022012027 "
                 "(https://asset.conrad.com/media10/add/160267/c1/-/en/002447773DS00/tehnicni-podatki-2447773-molex-ohisje-kabelske-vticnice-skupno-stevilo-polov-2-osnovna-mreza-254-mm-22012027-1-kos-bag.pdf). "
                 "The chart prints the same parts as 22012027, 22012037 and 22012057.")
    lines.append("- WAGO 221-413 (3 ports) and 221-415 (5 ports), already BOM line 26b. "
                 "24 to 12 AWG, strip 11 mm, UL 20 A. Cited from the 221-413 sheet "
                 "(https://susacdn.azureedge.net/specsheets/Wago/221-413.pdf) and the 221-415 sheet "
                 "(https://www.mouser.com/datasheet/2/737/221_415-1928680.pdf).")
    lines.append("- Amass XT30U, already BOM line 12, for the battery plug and the neck plug on cable P13.")
    lines.append("")
    lines.append("A new distribution board is not added. The WAGO levers already on that BOM line are the "
                 "distribution nodes. One 221 body has at most 5 ports (cited). The servo plus node and the "
                 "servo ground node each have 6 wires, so each uses one 221-415 and one 221-413. "
                 "The ground node G uses one 221-415 (4 wires). The switched plus node VSW uses one 221-413 "
                 "(3 wires). That is 3 of 221-415 and 3 of 221-413, which is the pocket pack already on BOM "
                 "line 26b (calc only: 1+1+1 and 1+1+1). The 221-412 pieces in that pack are not needed.")
    lines.append("")
    lines.append("The sixth port is a short jumper of the same 16 AWG between port 5 of the 221-415 and "
                 "port 1 of the 221-413. Strip 11 mm each end (cited). The free length between the two "
                 "clamps was not measured. BLOCKER for a pre-cut length. Cut it when the two levers sit "
                 "side by side.")
    lines.append("")
    lines.append("Jumper current, servo plus, is the sum of the SP4 and SP5 peaks because those two wires "
                 "are the only loads on the small lever. 1.98 A + 2.11 A = 4.09 A (calc only, from the "
                 "netlist peaks). 4.09 A is under the cited 20 A. Use 16 AWG for the jumper, the same gauge "
                 "as P11, not 22 AWG: 4.09 A is over the 3.0 A Mini-SPOX figure, and this jumper is a WAGO "
                 "joint, not a Mini-SPOX joint. The ground jumper is the same sum on the black side.")
    lines.append("")

    # Group wires
    order = []
    by = {}
    for w in wires:
        by.setdefault(w["cable"], []).append(w)
        if w["cable"] not in order:
            order.append(w["cable"])

    n_fix_marks = 0
    for cid in order:
        cb = cables[cid]
        joints = cb.get("joints") or []
        lines.append("## Cable %s" % cid)
        lines.append("")
        lines.append(cb.get("desc") or "")
        lines.append("")
        if joints:
            lines.append("Joints: %s." % ", ".join(joints))
            lines.append("")
            lines.append("Flex: the netlist already sets the twist lay where a lay fits "
                         "(NASA-STD-8739.4A 7.2.16 to 7.2.18, recorded on the cable). "
                         "A flex-cycle number for this silicone was not published. "
                         "BLOCKER for a cycle life. Same gap already recorded for the knee loop.")
        else:
            lines.append("Joints: none. This cable does not cross a moving joint.")
        lines.append("")
        poly = cb.get("polyline_mm")
        if poly:
            lines.append("Route polyline %s mm is the netlist figure from cables3d (CAD check only)." % poly)
        else:
            lines.append("Route polyline is empty in the netlist. BLOCKER for a new route measurement. "
                         "The cut below is the netlist cut, where one is set.")
        lines.append("")
        for i, w in enumerate(by[cid], 1):
            a, ka = end_text(w, w["from"], w["ends"][0])
            b, kb = end_text(w, w["to"], w["ends"][1])
            lines.append("### %s wire %d" % (cid, i))
            lines.append("")
            lines.append("- From: %s" % w["from"])
            lines.append("- To: %s" % w["to"])
            if w.get("branch"):
                lines.append("- Branch: %s" % w["branch"])
            lines.append("- Net: %s" % w["net"])
            lines.append("- From end: %s" % a)
            lines.append("- To end: %s" % b)
            lines.append("- Gauge and current: %s" % check(w, {ka, kb}))
            lines.append("- Color: %s" % w.get("color"))
            cut = w.get("cut_mm")
            if cut is None and cb.get("no_route") and cid == "NT":
                lines.append("- Cut: BLOCKER. BAY.md names the valley seat and gives no length. "
                             "cables3d has no route for this cable.")
            elif cut is None and cb.get("no_route"):
                lines.append("- Cut: BLOCKER. cables3d has no route for this cable. "
                             "The charger board has no seat (CHARGER_BOARD.md). "
                             "D13 worst route is 542 mm (CAD check only, cables3d/CABLES_3D.md) "
                             "and that wire is GPIO26 to the switch, not this one.")
            elif cut is None:
                lines.append("- Cut: BLOCKER. The netlist has no cut length.")
            elif cut == 0:
                lines.append("- Cut: 0 mm in the netlist, which means the parts are soldered together with no free wire.")
            else:
                extra = ""
                if poly and cut > poly:
                    extra = " The cut is %s mm longer than the polyline (calc only). That difference is the slack already in the netlist cut, not a new loop." % fmt_a(cut - poly)
                lines.append("- Cut: %s mm, from the netlist.%s" % (fmt_a(cut), extra))
            if w.get("i_mean_a") is not None or w.get("i_peak_a") is not None or w.get("i_fall_a") is not None:
                lines.append("- Netlist current, mean / peak / fall: %s / %s / %s A. The source on the wire says where that current came from (sim pass only unless that source says otherwise)." % (
                    fmt_a(w.get("i_mean_a")), fmt_a(w.get("i_peak_a")), fmt_a(w.get("i_fall_a"))))
            lines.append("")

    lines.append("## Flush wells")
    lines.append("")
    lines.append("Source: `twin/dock/flush/FLUSH_CONTACTS.md`. Five gold wells in the seat. "
                 "No new wire crosses a joint (that file, line 3 of the belly column). "
                 "The diode part is not chosen in that file. This harness does not pick one and does not draw a circuit.")
    lines.append("")
    lines.append("Each well is one conductor. Near end: solder to that well. "
                 "Far end: BLOCKER, no connector and no pin, because the board it would land on was not chosen. "
                 "Do not connect these wires. Positions of the five wells are the ones in that file "
                 "(y = -24, -12, 0, +12, +24 mm in the seat patch). Length: BLOCKER. "
                 "That file says the nest lead lengths were not copied.")
    lines.append("")
    add_gap("BLOCKER", "Five flush-well wires have a near end (solder to the well) and no far pin or connector.")

    lines.append("## What has no pin, and what was done")
    lines.append("")
    # de-duplicate gaps while keeping order
    seen = set()
    fix_n = blk_n = 0
    for kind, text in gaps:
        if text in seen:
            continue
        seen.add(text)
        if kind == "FIX":
            fix_n += 1
        else:
            blk_n += 1
        lines.append("- %s: %s" % (kind, text))
    lines.append("")
    lines.append("Counted here: %d FIX lines, %d BLOCKER lines, after dropping repeated wording (calc only, a count of this list)." % (
        fix_n, blk_n))
    lines.append("")
    lines.append("Wires read from the netlist: %d (calc only, a count of active rows)." % len(wires))
    lines.append("")

    # The eye housing assigns D6 pin 16. D6 ground and D7 ground splice to D5. Make sure those
    # were described. They are handled by owner_cable: pin 20 owner is D5 (rank). D6 and D7
    # on pin 20 become splice26. D6 on pin 16 is not in d2 and the special case returns kk.
    # Good.

    text = "\n".join(lines) + "\n"
    if "\u2014" in text or "\u2013" in text:
        raise SystemExit("em or en dash in output")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print("wires", len(wires), "fix", fix_n, "blocker", blk_n, "out", os.path.relpath(OUT, LAB))


if __name__ == "__main__":
    main()
