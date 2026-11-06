"""Every-part BOM for the Open Duck Mini v2 altaay-lab build.

build() makes one row per distinct physical item that goes into (or is used to build) the robot:
printed parts, servos by joint, horns, electronics and power parts, every fastener spec, every cable,
connectors and wire, consumables and tools. Each row says how many the robot uses, where they go,
which viewer nodes show them, which BOM.md purchase line supplies them, and whether that line covers
the quantity. Nothing here is a new source of truth: quantities come from the CAD (viewer nodes,
altaay_lab/fasteners/fasteners.json), the netlist (wiring/netlist.yaml) and print/parts.csv; purchase
data comes from BOM.md.

Called by viewer/make_viewer_data.py; with --write-bom it also writes altaay_lab/BOM_FULL.md and
altaay_lab/bom_full.csv (text only, small).
"""
import csv
import io
import json
import os
import re
from collections import Counter, OrderedDict, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
REPO = os.path.dirname(LAB)

STATUS_ORDER = ["MISSING", "SHORT", "CHECK", "bought", "in kit", "printed", "made", "tool"]


# ------------------------------------------------------------------------------------------ BOM.md
def md_tables(path):
    out, section = [], ""
    lines = open(path, encoding="utf-8").read().splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("#"):
            section = ln.lstrip("#").strip()
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|\s*:?-{2,}", lines[i + 1]):
            header = [c.strip() for c in ln.strip().strip("|").split("|")]
            rows = []
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split(" | ")]
                rows.append(dict(zip(header, cells)))
                i += 1
            out.append(dict(section=section, header=header, rows=rows))
            continue
        i += 1
    return out


def bom_lines(path=os.path.join(LAB, "BOM.md")):
    """BOM.md purchase lines by line id, with every column."""
    out = OrderedDict()
    for t in md_tables(path):
        if t["header"][:2] != ["#", "Item"] or "Need" not in t["header"]:
            continue
        for r in t["rows"]:
            r = dict(r)
            r["section"] = t["section"]
            out[r["#"]] = r
    return out


def fnum(s):
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(s or ""))
    return float(m.group(1)) if m else None


def capacity(line):
    """What the Buy quantity of a line holds, in the unit the rows count. None when not countable."""
    buy, pack = fnum(line.get("Buy")), (line.get("Pack") or "").strip().lower()
    if buy is None:
        return None, ""
    if pack in ("1", "each", "") or re.fullmatch(r"\d+", pack) and float(pack) == buy:
        return buy, "pcs"
    if re.fullmatch(r"\d+", pack):              # e.g. Buy 1, Pack 180: 1 pack of 180 pieces
        return buy * float(pack) if buy < float(pack) else buy, "pcs"
    m = re.fullmatch(r"(\d+) pairs?", pack)
    if m:
        return buy * float(m.group(1)), "pairs"
    m = re.fullmatch(r"(\d+(?:\.\d+)?) ?ft", pack)
    if m:
        return buy * float(m.group(1)) * 0.3048, "m"
    m = re.fullmatch(r"(\d+(?:\.\d+)?) ?yd", pack)
    if m:
        return buy * float(m.group(1)) * 0.9144, "m"
    m = re.fullmatch(r"(\d+(?:\.\d+)?) ?kg", pack)
    if m:
        return buy * float(m.group(1)) * 1000.0, "g"
    if pack in ("kit", "7 pc"):
        return buy, "kit"
    return None, pack


# ------------------------------------------------------------------------------------------ netlist
# component id -> (section, item, line, viewer part keys, how it is supplied)
COMP = {
    "BMS": ("Electronics and power", "2S protection board (BMS)", "8", ["bms_tenergy", "bms_cad"], "bought"),
    "CHG": ("Electronics and power", "USB-C 2S charge board", "11", ["charger"], "bought"),
    "XT30": ("Electronics and power", "XT30U connector pair (mated)", "12", ["xt30"], "bought"),
    "SW1": ("Electronics and power", "Main power switch, Pololu 2813 (D30)", "10", ["mosfet_switch"], "bought"),
    "CTL": ("Electronics and power", "Control button, NKK MB2011LS1W01-BB (D30, D38)", "10b", ["power_switch"], "bought"),
    "TOF": ("Electronics and power", "Cliff ToF, Adafruit 5396 VL53L4CD (D54)", "5b", ["tof_cliff"], "bought"),
    "U1": ("Electronics and power", "Servo regulator, Castle CC BEC Pro at 7.2 V", "L1", ["bec_pro"], "bought"),
    "U2": ("Electronics and power", "Servo bus adapter, Waveshare (A)", "2", ["adapter"], "bought"),
    "U3": ("Electronics and power", "5 V regulator, Pololu D30V30F5", "9", ["reg_5v"], "bought"),
    "PI": ("Electronics and power", "Raspberry Pi Zero 2 W", "3", ["pi", "head_board"], "bought"),
    "BNO": ("Electronics and power", "IMU, Adafruit BNO055 2472", "5", ["imu"], "bought"),
    "AMP": ("Expression (head)", "I2S amplifier, Adafruit MAX98357A", "E2", ["amp"], "bought"),
    "SPK": ("Expression (head)", "Speaker, Same Sky CMS0361KLX", "E1", ["speaker", "speaker_stand", "speaker_interface"], "bought"),
    "CAM": ("Expression (head)", "Raspberry Pi Camera Module 3", "E6", ["camera"], "bought"),
}
GROUPED = {  # several netlist components -> one row
    "foot_switch": ("Electronics and power", "Foot contact switch, Omron SS-01 (SS-10 fallback)", "13", ["foot_switch"],
                    ["FSL1", "FSL2", "FSR1", "FSR2"]),
    "pullup": ("Electronics and power", "Foot switch pull-up, 2.2 kOhm 1/4 W", "13b", [], ["RFL", "RFR"]),
    "led": ("Expression (head)", "1 W LED bead (2 eyes, 1 projector)", "E3", ["led"], ["LEDL", "LEDR", "LEDP"]),
    "led_r": ("Expression (head)", "LED resistor, 100 ohm 1/4 W", "E3b", [], ["RL", "RR", "RP"]),
    "touch": ("Expression (head)", "Touch board, Adafruit MPR121 1982 (D51)", "E9", ["tch_h", "tch_b"], ["TCHH", "TCHB"]),
    "pads": ("Expression (head)", "Touch pad, copper foil Adafruit 1127 (D51)", "E10", [], ["PH1", "PH2", "PB1"]),
}
SPLICE_KINDS = ("splice",)

# Build needs that no CAD part or netlist pin shows: (item, BOM.md name pattern, spec, why, kind)
REQUIRED = [
    ("Solder wire, rosin core", r"\bsolder (wire|spool)|\bsolder\b.*rosin|rosin core",
     "about %(n)d solder joints and splice ends in the netlist", "wiring/netlist.yaml wire ends: splices, pads, cups, header holes", "consumable"),
    ("Cable ties, small nylon", r"cable tie|zip tie", "about 100 mm",
     "MOUNTING.md: cable tie at the servo power splices and the USB slack coil", "consumable"),
    ("USB-C PD supply for the soldering iron", r"(PD|power delivery).*(supply|charger|adapter)|(supply|charger|adapter).*\bPD\b",
     "powers the Pinecil V2 (BOM T1)", "BOM.md T1: needs a USB-C PD supply", "tool"),
    ("USB-C supply to charge the robot", r"charg.*(wall|supply|adapter)|(wall|power) (adapter|supply).*charg",
     "feeds the USB-C 2S charge board (BOM 11)", "netlist CHG: USB-C input", "tool"),
    ("Multimeter with continuity beep", r"multimeter", "TEST_PLAN.md section 0", "TEST_PLAN.md section 0, sections 2 to 12", "tool"),
    ("Bench DC supply with current limit", r"bench.*(supply)|(power supply).*(current limit|bench)|DC power supply",
     "TEST_PLAN.md section 0: first power always current limited", "TEST_PLAN.md sections 4, 5, 7, 8", "tool"),
    ("Digital calipers", r"caliper", "TEST_PLAN.md section 0", "TEST_PLAN.md section 0 and the coupon checks", "tool"),
    ("Load for the regulator tests", r"electronic load|power resistor|load resistor",
     "TEST_PLAN.md section 4 and 5 input sweeps", "TEST_PLAN.md sections 4 and 5", "tool"),
]

def uses_tie(t):
    """True for a retention item that is closed with a nylon cable tie (the BOM cable tie line): a free-air tie
    around the bundle, a tie through an adhesive tie mount or through a hole of a printed part, and any gap."""
    k = str(t.get("kind") or "").lower()
    return bool(t.get("gap")) or any(w in k for w in ("cable tie", "tie mount", "printed feature"))


# wire gauge -> BOM wire line
WIRE_LINE = {"16 AWG": "L5", "20 AWG": "23", "22 AWG": "24", "26 AWG": "25"}
PER_COLOUR_M = 25 * 0.3048          # every wire line is 25 ft per colour (BOM.md lines L5, 23, 24, 25)


# ------------------------------------------------------------------------------------------ heat shrink rule
SLEEVE_RULE = ("one sleeve per splice; one per solder joint outside a splice where a wire meets a part's flying lead or two "
               "flying leads meet (holder, BEC, resistor and LED leads); one over each XT30 solder cup (HARNESS_BUILD 'heat "
               "shrink over the cup'); one cap on each cut lead wire the netlist says to insulate. None on board pads, "
               "holes, header pins, plugs, sockets and screw terminals; switch terminals, lugs and tabs get one only if "
               "copper shows (HARNESS_BUILD 'heat shrink if bare'), not counted")
OWN_LEAD = {"resistor lead": "resistor", "BEC lead": "regulator", "SG90 lead": "servo"}   # wire gauge -> kind of its part
LED_RES = {"LEDL": "R1", "LEDR": "R2", "LEDP": "R3"}       # blueprint/make_scene_extras.py names the LED joints by R1 to R3


def sleeve_joints(netlist):
    """Every heat shrink sleeve the netlist calls for, by SLEEVE_RULE. One dict per sleeve: id (the scene_extras.json
    item id that draws it: splice-<name>, hs-XT30-Fp, hs-P10-BEC-INp, hs-U1-OUT1S, hs-R1-LED; new ones hs-<cable>-<pin>),
    kind (splice, wire to lead, lead to lead, XT30 cup, cap), name, cables, pins (COMP.PIN at the joint), gauges (of
    the wires at it), part (the component whose lead or cup it is), note."""
    comps = {c["id"]: c for c in netlist["components"]}
    act = {c["id"] for c in netlist["cables"] if c.get("status", "active") == "active"}
    wires = [w for w in netlist["wires"] if w["cable"] in act]
    out = OrderedDict()

    def group_of(pin):
        comp, p = (pin.split(".", 1) + [""])[:2]
        c = comps.get(comp) or {}
        g = next((x.get("group") for x in c.get("pins") or [] if x.get("pin") == p), None)
        gr = (c.get("groups") or {}).get(g) or {}
        return c, gr.get("connector") or "", gr.get("note") or ""

    for c in netlist["components"]:                       # 1. splices: one sleeve over each
        if c.get("kind") != "splice":
            continue
        at = [(w, s) for w in wires for s in ("from", "to") if w[s].split(".")[0] == c["id"]]
        if at:
            out["splice-" + c["id"]] = dict(kind="splice", name=c["id"], cables=sorted({w["cable"] for w, _ in at}),
                                            pins=[c["id"] + ".S"], gauges=[w["gauge"] for w, _ in at], part=c["id"],
                                            note="%d wire ends" % len(at))
    for w in wires:                                       # 2. cups and joints on flying leads, outside splices
        ends = (w.get("ends") or []) + ["", ""]
        own = None                                        # the part whose own lead this wire is (no joint at that end)
        if w.get("gauge") in OWN_LEAD:
            own = next((w[s].split(".")[0] for s in ("from", "to")
                        if (comps.get(w[s].split(".")[0]) or {}).get("kind") == OWN_LEAD[w["gauge"]]), None)
        elif w.get("color") == "holder lead":
            own = next((w[s].split(".")[0] for s, e in zip(("from", "to"), ends) if "holder lead" in e.lower()), None)
        for s, e in zip(("from", "to"), ends):
            pin, el = w[s], e.lower()
            comp = pin.split(".")[0]
            if "splice" in el:
                continue
            if "xt30" in el:
                jid = "hs-%s%s" % (pin.replace(".", "-")[:-1], "p" if pin.endswith("+") else "n")
                out[jid] = dict(kind="XT30 cup", name=pin, cables=[w["cable"]], pins=[pin], gauges=[w["gauge"]], part=comp,
                                note="netlist end '%s'" % e)
                continue
            c, conn, gnote = group_of(pin)
            if "lead" not in conn.lower() or "header" in el or comp == own:
                continue
            kind = "lead to lead" if (w.get("gauge") in OWN_LEAD or w.get("color") == "holder lead") else "wire to lead"
            if kind == "lead to lead" and c.get("kind") == "led" and comp in LED_RES:
                jid = "hs-%s-LED" % LED_RES[comp]
            elif w["cable"] == "P10" and comp == "U1":
                jid = "hs-P10-BEC-IN%s" % ("p" if pin.endswith("+") else "n")
            else:
                tag = pin.replace(".", "-")
                tag = tag[:-1] + "p" if tag.endswith("+") else (tag[:-1] + "n" if tag.endswith("-") else tag)
                jid = "hs-%s-%s" % (w["cable"], tag)
            other = w["to" if s == "from" else "from"]
            out[jid] = dict(kind=kind, name=pin, cables=[w["cable"]], pins=[pin], gauges=[w["gauge"]], part=comp,
                            other=other, note="netlist end '%s' on %s (%s)%s" % (e, pin, conn, ("; " + gnote) if gnote else ""))
    for c in netlist["components"]:                       # 3. caps on cut lead wires the netlist insulates
        for p in c.get("pins") or []:
            if p.get("dir") == "nc" and "insulate" in str(p.get("source", "")).lower():
                jid = "hs-%s-%s" % (c["id"], p["pin"])
                out[jid] = dict(kind="cap", name="%s.%s" % (c["id"], p["pin"]), cables=[], pins=["%s.%s" % (c["id"], p["pin"])],
                                gauges=[], part=c["id"], note="netlist %s.%s %s, source '%s'" % (c["id"], p["pin"], p.get("name", ""), p.get("source", "")))
    return [dict(id=k, **v) for k, v in out.items()]


def end_kind(e):
    e = (e or "").lower()
    if "50-37-5033" in e:
        return "molex"
    if "5264 plug" in e:
        return "kit_plug"
    if "xt30" in e:
        return "xt30"
    if "splice" in e:
        return "splice"
    if "solder" in e or "header pin" in e or "resistor lead" in e or "led lead" in e:
        return "solder"
    return "other"


# ------------------------------------------------------------------------------------------ rows
def _row(**k):
    base = dict(id="", section="", item="", spec="", qty=0, unit="pcs", spare=0, where="", nodes=[], line="",
                status="", note="", source="")
    base.update(k)
    return base


def build(nodes, sub_labels, netlist, bom, parts_csv, fasteners=None, cables3d=None, link_sub=None, ties=None):
    """nodes: manifest nodes (id -> record). sub_labels: subassembly id -> label. netlist: parsed netlist.yaml.
    bom: bom_lines(). parts_csv: rows of print/parts.csv. fasteners / cables3d: lists of records or None."""
    link_sub = link_sub or {}
    rows = []
    by_part = defaultdict(list)
    for nid, r in nodes.items():
        by_part[r.get("part")].append(nid)

    def where_of(ids, counts=True):
        c = Counter(sub_labels.get(nodes[i].get("sub"), nodes[i].get("sub") or "?") for i in ids if i in nodes)
        if not counts:
            return ", ".join(sorted(c))
        return ", ".join("%s %d" % (k, v) if v > 1 else k for k, v in sorted(c.items()))

    # 1. printed parts --------------------------------------------------------------------------
    for n, pr in enumerate(parts_csv, 1):
        stem = pr["stl"].replace(".stl", "")
        ids = [i for i in by_part.get(stem, []) if nodes[i].get("category") in ("pla", "tpu")]
        rec = nodes[ids[0]] if ids else {}
        mat = pr["material"]
        q = int(pr["qty"])
        found = len(ids)
        rows.append(_row(id="P%02d" % n, section="Printed parts", item=rec.get("label") or stem.replace("_", " "),
                         spec="print/%s, %s%s%s" % (pr["stl"], rec.get("material") or mat,
                                                    ", %.1f g" % rec["grams"] if rec.get("grams") else "",
                                                    ", %.2f h each" % rec["hours"] if rec.get("hours") else ""),
                         qty=q, spare=int(pr.get("spare") or 0), where=where_of(ids), nodes=ids,
                         line="28" if mat.upper() == "TPU" else "27",
                         status="printed" if found == q else "CHECK",
                         note=("" if found == q else "CAD shows %d, parts.csv says %d" % (found, q)) +
                              (("; " if found != q else "") + pr["why"] if pr.get("why") else ""),
                         source="[L] print/parts.csv, CAD instances in the viewer"))
    ant = by_part.get("antenna", [])
    if ant:
        rows.append(_row(id="P%02d" % (len(parts_csv) + 1), section="Printed parts", item="Antenna rod (optional)",
                         spec="URDF antenna.stl, PLA, 1.8 g for 2 (print/PRINT_PLAN.md optional part)", qty=len(ant),
                         where=where_of(ant), nodes=ant, line="27", status="printed",
                         note="In the CAD but not in print/: export from the URDF mesh (PRINT_PLAN.md)", source="[L] print/PRINT_PLAN.md"))

    # 2. servos and horns -----------------------------------------------------------------------
    netlist_comps = {c["id"]: c for c in netlist["components"]}
    joints = OrderedDict()
    for nid, r in nodes.items():
        if r.get("servo"):
            joints.setdefault(r["servo"], []).append(nid)
    for n, (j, ids) in enumerate(sorted(joints.items(), key=lambda kv: nodes[kv[1][0]].get("servo_id") or 0), 1):
        sid = nodes[ids[0]].get("servo_id")
        case = [i for i in ids if not nodes[i]["part"].startswith("horn")]
        # the model is the one the netlist names for this ID (D32: STS3250-C002 on both knees, BOM line 1b)
        part = str(((netlist_comps or {}).get("SV%s" % sid) or {}).get("part") or "")
        if "STS3250" in part:
            item, spec, line = ("Feetech STS3250-C002, ID %s, %s" % (sid, j.replace("_", " ")),
                                "50 kg.cm, same outline, 25T horn and 5264 ports as the C001 (BOM line 1b, D32)", "1b")
        else:
            item, spec, line = ("Feetech STS3215 C001, ID %s, %s" % (sid, j.replace("_", " ")),
                                "7.4 V 1:345; ships with 1 horn set, 1 x 15 cm 5264 cable and a screw bag (BOM line 1)", "1")
        rows.append(_row(id="S%02d" % n, section="Servos", item=item, spec=spec,
                         qty=1, where=where_of(case, counts=False), nodes=ids, line=line, status="bought",
                         source="[U] Runtime IDs (WIRING.md section 2), CAD; model from wiring/netlist.yaml"))
    for key, label in (("horn_drive", "Servo horn, drive side"), ("horn_idle", "Servo horn, idle side")):
        ids = by_part.get(key, [])
        if ids:
            rows.append(_row(id="S%02d" % (len(joints) + (1 if key == "horn_drive" else 2)), section="Servos", item=label,
                             spec="comes with each STS3215 (BOM line 1)", qty=len(ids), where=where_of(ids), nodes=ids,
                             line="1", status="in kit", source="[L] CAD; [U] BOM line 1"))
    sg = by_part.get("sg90", [])
    rows.append(_row(id="S%02d" % (len(joints) + 3), section="Servos", item="SG90-class antenna servo",
                     spec="Miuzei 9 g, lead 250 mm; tab and horn screws from its bag", qty=max(2, len(sg)),
                     where=where_of(sg) or "Head", nodes=sg, line="14", status="bought", source="[L] CAD, netlist SGL SGR"))

    # 3. electronics and power ------------------------------------------------------------------
    comps = {c["id"]: c for c in netlist["components"]}
    n_e = 0

    def e_row(item, line, keys, comp_ids, section, qty=None, spec=None, status="bought", note=""):
        nonlocal n_e
        n_e += 1
        ids = [i for k in keys for i in by_part.get(k, [])]
        regions = sorted({comps[c].get("region", "").replace("_", " ") for c in comp_ids if c in comps})
        wh = where_of(ids)
        if "Not yet placed" in wh or not wh:
            wh = ", ".join(x for x in [wh and "not placed in the CAD", ", ".join(regions)] if x)
        rows.append(_row(id="E%02d" % n_e, section=section, item=item,
                         spec=spec or "; ".join(comps[c]["part"] for c in comp_ids[:1] if c in comps),
                         qty=qty if qty is not None else len(comp_ids), where=wh,
                         nodes=ids, line=line, status=status, note=note,
                         source="[L] wiring/netlist.yaml %s" % ", ".join(comp_ids)))

    e_row("Li-ion cell, Molicel INR21700-P45B", "6", ["cell"], ["PACK"], "Electronics and power", qty=2,
          spec="21700, 4.5 Ah, 2 in series, spot-welded 2S1P pack (D44)")
    e_row("2S1P pack build: nickel strip, sleeve, fish paper, 16 AWG leads", "7", ["holder"], ["PACK"], "Electronics and power", qty=1,
          spec="no holder (D44); pack leads used for P1 and P2 if 120 mm or longer")
    for cid in ("BMS", "CHG", "XT30", "SW1", "CTL", "U1", "U2", "U3", "PI", "BNO", "TOF"):
        sec, item, line, keys, st = COMP[cid]
        e_row(item, line, keys, [cid], sec, qty=1)
    e_row("Inline fuse holder, Littelfuse FHAC0001ZXJ", "L3", ["fuse_holder"], ["F1"], "Electronics and power", qty=1,
          spec="ATO 20 A holder, 16 AWG leads")
    e_row("Fuse, Littelfuse 0287015.PXCN ATO 15 A", "L4", [], ["F1"], "Electronics and power", qty=1, spec="sits in the L3 holder")
    e_row("microSD card, SanDisk Ultra 32 GB", "4", [], ["PI"], "Electronics and power", qty=1, spec="in the Pi")
    for key, (sec, item, line, keys, cids) in GROUPED.items():
        e_row(item, line, keys, cids, sec, qty=len(cids))
    for cid in ("AMP", "SPK", "CAM"):
        sec, item, line, keys, st = COMP[cid]
        e_row(item, line, keys, [cid], sec, qty=1)
    for item, line, keys, cids, spec in (
            ("Chest contact pad, 4 strips", "DK1", ["dock_pad"], ["DKP"], None),
            ("Charge input ideal diode, Pololu 5382", "DK2", ["dock_dk2"], ["DK2"], None),
            ("Charge path fuse holder, Littelfuse FHAC0001ZXJ", "DK3", ["dock_f2"], ["F2"], "ATO holder for the 5 A charge fuse"),
            ("Fuse, Littelfuse 0287005.PXCN ATO 5 A", "DK4", [], ["F2"], "sits in the DK3 holder"),
            ("Cell NTC and wake branch parts", "DK5", [], ["RT1", "WK1"], "10 k NTC B3950; 3.9 V zener, diode, 10 k; 100 k across DK2"),
            ("Dock supply ideal diode, Pololu 5382", "DK6", ["dock_dk6"], ["DK6"], None),
            ("Pack side ideal diode, Pololu 5383", "DK7", ["dock_dk7"], ["DK7"], None)):
        e_row(item, line, keys, cids, "Electronics and power", qty=1, spec=spec)
    e_row("Eye glass disc, 29.6 x 1.85 mm", "E4", [], [], "Expression (head)", qty=2, spec="one per eye (not modelled)")
    e_row("Projector reflector, Aurorad S5 20 x 15 mm", "E5", [], [], "Expression (head)", qty=1,
          spec="in flash_reflector_interface (not modelled)")
    e_row("Game controller, Xbox Wireless (Bluetooth)", "15", [], [], "Electronics and power", qty=1,
          spec="off-robot: the Runtime drives the walk from it")

    # 4. fasteners ------------------------------------------------------------------------------
    n_f = 0
    if fasteners:
        groups = OrderedDict()
        for f in fasteners:
            groups.setdefault((f.get("line") or "", f["spec"]), []).append(f)
        for (line, spec), fs in sorted(groups.items(), key=lambda kv: (kv[0][1])):
            n_f += 1
            ids = [f["node"] for f in fs if f.get("node")]
            supplied = Counter(f.get("supplied") or "bought" for f in fs).most_common(1)[0][0]
            where = Counter(sub_labels.get(link_sub.get(f.get("link"), f.get("sub")), f.get("sub") or f.get("link") or "?")
                            for f in fs)
            rows.append(_row(id="F%02d" % n_f, section="Fasteners", item=spec, spec=fs[0].get("desc", ""), qty=len(fs),
                             where=", ".join("%s %d" % kv for kv in sorted(where.items())), nodes=ids, line=line,
                             status=supplied, note=fs[0].get("note", ""), source="[L] altaay_lab/fasteners/fasteners.json"))
        # washers under the screw heads (fasteners.json 'washer': the eye screws, D21 note); the 3D washer discs of
        # viewer/scene_extras.json link to this row by its item name, the BOM.md line's Item
        wsh = [f for f in fasteners if f.get("washer")]
        if wsh:
            w0 = wsh[0]["washer"]
            lw = w0.get("line") or ""
            n_f += 1
            where = Counter(sub_labels.get(link_sub.get(f.get("link"), f.get("sub")), f.get("sub") or f.get("link") or "?")
                            for f in wsh for _ in range(int(f["washer"].get("n", 1))))
            rows.append(_row(id="F%02d" % n_f, section="Fasteners", item=(bom.get(lw) or {}).get("Item") or "Flat washer",
                             spec=w0.get("spec", ""), qty=sum(int(f["washer"].get("n", 1)) for f in wsh),
                             where=", ".join("%s %d" % kv for kv in sorted(where.items())), nodes=[], line=lw, status="bought",
                             note="%d under each of the %d screw heads that have one (%s)" % (
                                 int(w0.get("n", 1)), len(wsh), ", ".join(sorted({f["spec"] for f in wsh}))),
                             source="[L] altaay_lab/fasteners/fasteners.json"))
    ins = by_part.get("insert", [])
    n_f += 1
    rows.append(_row(id="F%02d" % n_f, section="Fasteners", item="M3 heat-set insert, CNC Kitchen M3 x 5.7",
                     spec="D1 4.6 mm into a 4.0 mm bore", qty=len(ins), where=where_of(ins), nodes=ins, line="16",
                     status="bought", source="[L] audit/sites.json bores, viewer"))
    brg = by_part.get("bearing", [])
    n_f += 1
    rows.append(_row(id="F%02d" % n_f, section="Fasteners", item="Ball bearing 6804ZZ 20 x 32 x 7",
                     spec="press into the 32.19 mm seats", qty=len(brg), where=where_of(brg), nodes=brg, line="18",
                     status="bought", source="[L] CAD"))

    # 5. cables, connectors, wire ----------------------------------------------------------------
    wires_by_cable = defaultdict(list)
    for w in netlist["wires"]:
        wires_by_cable[w["cable"]].append(w)
    c3 = {c["id"]: c for c in (cables3d or [])}
    n_c = 0
    molex_housings, crimps, solder_ends, splice_ends, kit_used = set(), 0, 0, 0, 0
    wire_m = defaultdict(float)
    for cab in netlist["cables"]:
        if cab.get("status") != "active":
            continue
        ws = wires_by_cable.get(cab["id"], [])
        gauges = Counter(w["gauge"] for w in ws)
        kinds = Counter(end_kind(e) for w in ws for e in (w.get("ends") or []))
        lines, status = [], "made"
        if "kit cable" in gauges:
            lines, status = ["1"], "in kit"
            kit_used += 1
        elif "USB 2.0 cable" in gauges:
            lines, status = ["20"], "bought"
        elif "FPC ribbon" in gauges:
            lines, status = ["E7"], "bought"
        for g in gauges:
            if g in WIRE_LINE:
                lines.append(WIRE_LINE[g])
            if g.startswith("SG90 lead"):
                lines.append("14")
            if g == "BEC lead":
                lines.append("L1")
        if kinds.get("molex"):
            lines += ["21", "22"]
        if kinds.get("xt30"):
            lines.append("12")
        if kinds.get("splice") or kinds.get("solder"):
            lines.append("26")
        for w in ws:
            for side, e in zip(("from", "to"), w.get("ends") or []):
                k = end_kind(e)
                if k == "molex":
                    pin = w[side]
                    comp, grp = pin.split(".")[0], (pin.split(".")[1] if "." in pin else "")
                    molex_housings.add((comp, grp))
                    crimps += 1
                elif k == "splice":
                    splice_ends += 1
                elif k in ("solder", "xt30"):
                    solder_ends += 1
            if w["gauge"] in WIRE_LINE and w.get("color") != "holder lead":   # holder leads ship with line 7
                wire_m[(w["gauge"], w.get("color"))] += (w.get("cut_mm") or 0) / 1000.0
        cuts = sorted({w.get("cut_mm") for w in ws if w.get("cut_mm")})
        n_c += 1
        c3r = c3.get(cab["id"], {})
        rows.append(_row(id="C%02d" % n_c, section="Cables", item="%s: %s" % (cab["id"], cab["desc"]),
                         spec="%d wire%s, %s, cut %s mm" % (len(ws), "s" if len(ws) != 1 else "",
                                                            ", ".join("%s x%d" % kv for kv in gauges.items()),
                                                            "/".join(str(int(c)) for c in cuts) or "?"),
                         qty=1, unit="cable", where=", ".join(cab.get("regions") or []) + (
                             (" (crosses " + ", ".join(cab["joints"]) + ")") if cab.get("joints") else ""),
                         nodes=list(c3r.get("nodes") or ([c3r["node"]] if c3r.get("node") else [])), line=", ".join(OrderedDict.fromkeys(lines)),
                         status=status, note=c3r.get("check", ""), source="[L] wiring/netlist.yaml"))
    n_c += 1
    rows.append(_row(id="C%02d" % n_c, section="Connectors and wire", item="Servo kit cable, 15 cm 5264-3P",
                     spec="one ships with each STS3215 (14 in all)", qty=kit_used, line="1", status="in kit",
                     note="%d used, %d spare" % (kit_used, 14 - kit_used), source="[L] netlist kit cables"))
    # heat shrink: one sleeve per joint of SLEEVE_RULE, counted from the netlist; the 3D view draws each one (scene_extras
    # items, plus the sleeves make_viewer_data.py places from cables3d.json), and every drawn node names its joint
    joints = sleeve_joints(netlist)
    jk = Counter(j["kind"] for j in joints)
    sl_nodes = [n for n in by_part.get("splice", []) + by_part.get("heat_shrink", []) if nodes[n].get("sleeve")]
    drawn = Counter(nodes[n]["sleeve"] for n in sl_nodes)
    want = {j["id"] for j in joints}
    miss = sorted(want - set(drawn))
    extra = sorted(k for k in drawn if k not in want) + sorted(k for k, v in drawn.items() if v > 1 and k in want)
    cond = [j["id"] for j in joints if "120 mm or longer" in j.get("note", "")]
    hs_note = ("%s (wiring/netlist.yaml). The 3D view draws %d of the %d%s%s.%s" % (
        SLEEVE_RULE, len(sl_nodes), len(joints), (", not drawn: " + ", ".join(miss)) if miss else "",
        ("; drawn with no joint or twice: " + ", ".join(extra)) if extra else "",
        (" The %d holder lead joints (%s) go away if the holder leads reach the BMS (120 mm or longer, netlist PACK note)."
         % (len(cond), ", ".join(cond))) if cond else ""))
    hs = (len(joints), "one sleeve per joint: %d splices, %d wire to lead, %d lead to lead, %d XT30 solder cups, %d caps on "
                       "cut lead wires" % (jk["splice"], jk["wire to lead"], jk["lead to lead"], jk["XT30 cup"], jk["cap"]),
          hs_note, "[L] wiring/netlist.yaml (viewer/bom_full.py sleeve_joints)", sl_nodes)
    for item, line, q, unit, spec, note, src, ids in (
            ("Mini-SPOX housing, Molex 50-37-5033", "21", len(molex_housings), "pcs", "3 pos 2.5 mm, mates the servo sockets",
             "", "[L] netlist wire ends", []),
            ("Mini-SPOX crimp terminal, Molex 08-70-1040", "22", crimps, "pcs", "22 to 28 AWG", "", "[L] netlist wire ends", []),
            ("Heat shrink pieces (splices and solder joints)", "26", hs[0], "pcs", hs[1], hs[2], hs[3], hs[4])):
        n_c += 1
        rows.append(_row(id="C%02d" % n_c, section="Connectors and wire", item=item, spec=spec, qty=q, unit=unit, line=line,
                         nodes=list(ids), status="CHECK" if line == "26" and (miss or extra) else "bought", note=note,
                         source=src))
    for (g, col), m in sorted(wire_m.items()):
        n_c += 1
        rows.append(_row(id="C%02d" % n_c, section="Connectors and wire", item="Wire %s %s" % (g, col),
                         spec="silicone stranded; sum of netlist cut lengths", qty=round(m, 2), unit="m",
                         line=WIRE_LINE[g], status="bought", source="[L] netlist cut_mm"))

    # 6. items the build needs that the CAD and netlist do not show: found in BOM.md by name, else MISSING
    n_k = 0
    n_solder = solder_ends + splice_ends
    for item, pat, spec, why, kind in REQUIRED:
        hit = [lid for lid, b in bom.items() if re.search(pat, b["Item"], re.I)]   # item name only, specs mention other parts
        n_k += 1
        sec = "Tools" if kind == "tool" else "Consumables and other"
        rows.append(_row(id="K%02d" % n_k, section=sec, item=item, spec=spec % dict(n=n_solder) if "%(n)" in spec else spec,
                         qty=1, unit="", line=hit[0] if hit else "", status=("tool" if kind == "tool" else "bought") if hit else "MISSING",
                         note=why, source="[L] %s" % why))

    # 6b. ties, adhesive mounts and printed guides placed along the cables (cables3d.json retention). Every retention
    # item that uses a tie counts on the cable tie row; mounts and guides are parts, so they also get a row of their
    # own. A tie through an existing printed feature needs no other part.
    if ties:
        tied = [t for t in ties if uses_tie(t)]
        tie_row = next((r for r in rows if r["item"].startswith("Cable ties")), None)
        if tie_row is not None and tied:
            gaps = sum(1 for t in tied if t["gap"])
            kinds = ", ".join("%d %s" % (v, k) for k, v in sorted(Counter(t["kind"] for t in tied).items()))
            tie_row.update(qty=len(tied), unit="pcs", nodes=[t["node"] for t in tied],
                           note=tie_row["note"] + "; %d placed along the cables in the 3D view, one per retention item "
                                                  "(%s)%s" % (len(tied), kinds, ", %d at gaps" % gaps if gaps else ""))
        for (kind, line), n in sorted(Counter((t["kind"], t["line"]) for t in ties).items()):
            if "cable tie" in kind or "feature" in kind or not line:
                continue            # on the cable tie row only: no other part (a drilled tie-hole pair is not a part)
            sel = [t for t in ties if t["kind"] == kind and t["line"] == line]
            gaps = sum(1 for t in sel if t["gap"])
            n_k += 1
            item = {"34": "Adhesive tie mount MB3A", "34b": "Adhesive tie mount ABM1M-AT-C"}.get(line, kind[0].upper() + kind[1:])
            rows.append(_row(id="K%02d" % n_k, section="Consumables and other", item=item,
                             spec="placed along the cables (altaay_lab/cables3d)", qty=len(sel), nodes=[t["node"] for t in sel],
                             line=line, status="printed" if line == "27" else "bought",
                             note="%d at places where the CAD has no feature" % gaps if gaps else "",
                             source="[L] altaay_lab/cables3d/cables3d.json retention"))

    # 7. consumables and tools from BOM.md that no row used yet ---------------------------------
    used = Counter()
    for r in rows:
        for l in re.split(r",\s*", r["line"]):
            if l:
                used[l] += 1
    for lid, b in bom.items():
        sec = b["section"]
        if lid in used:
            continue
        n_k += 1
        kind = "tool" if sec.startswith("Tools") or sec.startswith("Test equipment") else "bought"
        rows.append(_row(id="K%02d" % n_k, section="Tools" if kind == "tool" else "Consumables and other",
                         item=b["Item"], spec=b.get("Spec", ""), qty=b.get("Need", ""), unit="", line=lid, status=kind,
                         source="[U] BOM.md line %s" % lid))

    # attach purchase data and coverage
    need_by_line = defaultdict(float)
    for r in rows:
        if r["status"] in ("bought",) and r["line"] and "," not in r["line"] and isinstance(r["qty"], (int, float)):
            need_by_line[r["line"]] += r["qty"]
    for r in rows:
        first = re.split(r",\s*", r["line"])[0] if r["line"] else ""
        b = bom.get(first)
        if not r["line"]:
            r["status"] = "MISSING"
        elif b is None:
            r["status"] = "MISSING"
            r["note"] = (r["note"] + "; " if r["note"] else "") + "BOM.md has no line %s" % first
        else:
            r.update(supplier=b.get("Supplier", ""), link=b.get("Link", ""), buy=b.get("Buy", ""), pack=b.get("Pack", ""),
                     line_cost=b.get("Line $", ""))
    for lid, need in need_by_line.items():
        b = bom.get(lid)
        if not b:
            continue
        cap, unit = capacity(b)
        if cap is None or unit not in ("pcs", "pairs"):
            continue
        if need > cap + 1e-9:
            for r in rows:
                if r["line"] == lid and r["status"] == "bought":
                    r["status"] = "SHORT"
                    r["note"] = (r["note"] + "; " if r["note"] else "") + "line %s buys %g, the robot uses %g" % (lid, cap, need)
    # wire per colour against 25 ft per colour
    for r in rows:
        if r["section"] == "Connectors and wire" and r["unit"] == "m" and r["qty"] > PER_COLOUR_M:
            r["status"] = "SHORT"
            r["note"] = "more than the 25 ft per colour in the line"
    return rows


def coverage(rows, bom):
    """Per BOM line: rows that use it, and lines no row uses."""
    use = defaultdict(list)
    for r in rows:
        for l in re.split(r",\s*", r["line"]):
            if l:
                use[l].append(r["id"])
    return {lid: use.get(lid, []) for lid in bom}


# ------------------------------------------------------------------------------------------ docs
def write_docs(rows, bom, stamp, out_dir=LAB):
    cols = ["id", "section", "item", "spec", "qty", "unit", "spare", "where", "line", "supplier", "buy", "pack",
            "line_cost", "link", "status", "note", "source"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in cols})
    with open(os.path.join(out_dir, "bom_full.csv"), "w", encoding="utf-8", newline="") as fh:
        fh.write(buf.getvalue())

    st = Counter(r["status"] for r in rows)
    secs = OrderedDict()
    for r in rows:
        secs.setdefault(r["section"], []).append(r)
    pieces = sum(r["qty"] for r in rows if isinstance(r["qty"], (int, float)) and r["unit"] in ("pcs", "cable"))
    L = ["# BOM_FULL: every part in the robot", "",
         "Generated %s by altaay_lab/viewer/make_viewer_data.py --write-bom (module viewer/bom_full.py). Do not edit by hand: "
         "change the sources (CAD, print/parts.csv, wiring/netlist.yaml, fasteners/fasteners.json, BOM.md) and re-run." % stamp, "",
         "One row per distinct item that goes into the robot or is used to build it. Qty is what the robot uses "
         "(measured in the CAD, the netlist or the fastener schedule). The Line column is the BOM.md purchase line "
         "that supplies it, so prices and links live in one place (BOM.md). The exploded 3D view shows every row "
         "that is modelled (tab \"Every part\").", "",
         "Status: bought = a BOM.md line buys it and covers the quantity; in kit = ships with another bought item; "
         "printed = from the filament lines; made = made from wire and connectors; tool = used to build; "
         "SHORT = the line buys less than the robot uses; MISSING = no purchase line; CHECK = counts disagree.", "",
         "| Section | Rows | Pieces | Status |", "|---|---|---|---|"]
    for sec, rs in secs.items():
        pc = sum(r["qty"] for r in rs if isinstance(r["qty"], (int, float)) and r["unit"] in ("pcs", "cable"))
        L.append("| %s | %d | %s | %s |" % (sec, len(rs), int(pc) if pc else "", ", ".join(
            "%s %d" % (k, v) for k, v in sorted(Counter(r["status"] for r in rs).items(), key=lambda kv: STATUS_ORDER.index(kv[0]) if kv[0] in STATUS_ORDER else 99))))
    L += ["| **All** | %d | %d | %s |" % (len(rows), int(pieces), ", ".join("%s %d" % (k, st[k]) for k in STATUS_ORDER if st.get(k))), ""]
    bad = [r for r in rows if r["status"] in ("MISSING", "SHORT", "CHECK")]
    L += ["## Needs action (%d)" % len(bad), ""]
    if bad:
        L += ["| ID | Item | Qty | Status | Note |", "|---|---|---|---|---|"]
        for r in bad:
            L.append("| %s | %s | %s %s | %s | %s |" % (r["id"], r["item"], r["qty"], r["unit"] if r["unit"] != "pcs" else "", r["status"], r["note"]))
    else:
        L.append("None: every row is covered by a purchase line, a kit, the filament or the tool list.")
    L.append("")
    for sec, rs in secs.items():
        L += ["## %s" % sec, "", "| ID | Item | Spec | Qty | Where | Line | Supplier | Status | Note |", "|---|---|---|---|---|---|---|---|---|"]
        for r in rs:
            q = r["qty"]
            qs = ("%g" % q if isinstance(q, (int, float)) else str(q)) + ("" if r["unit"] in ("pcs", "") else " " + r["unit"])
            if r.get("spare"):
                qs += " (+%d spare)" % r["spare"]
            L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                r["id"], r["item"].replace("|", "/"), (r["spec"] or "").replace("|", "/"), qs, r["where"] or "",
                r["line"], r.get("supplier", ""), r["status"], (r["note"] or "").replace("|", "/")))
        L.append("")
    cov = coverage(rows, bom)
    unused = [lid for lid, ids in cov.items() if not ids]
    L += ["## BOM.md lines and the rows that use them", "",
          "Every purchase line is used by at least one row%s." % ("" if not unused else " except: " + ", ".join(unused)), ""]
    with open(os.path.join(out_dir, "BOM_FULL.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    return dict(rows=len(rows), pieces=int(pieces), status=dict(st), needs_action=[r["id"] for r in bad])
