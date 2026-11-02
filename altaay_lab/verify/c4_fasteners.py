"""C4a and C4b: every screw in altaay_lab/fasteners/fasteners.json (fasteners agent) against the BOM and the joint ranges.

C4a  every fitted screw has a BOM line that exists in BOM.md (or the servo / SG90 bag it ships in), its size and length
     are what that line buys, and the count per line is covered by Buy and equals Need; for a kit line, the count per
     size the line states ("50 each of M2x4, M2x5, ...", "50 pcs of each size") covers the schedule size by size (WARN
     when the line states no count per size)
C4b  no head or tip collision over the joint ranges (the sweep in fasteners.json, sweep_fasteners.py) except known,
     decided ones (D18: the outer hip roll screw is left out)
Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/c4_fasteners.py
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

FJ = V.lab("fasteners", "fasteners.json")
SKIP = ("NOT FITTED", "LEAVE OUT")      # statuses of screws that are not put in


def fitted(f):
    return f["kind"] == "screw" and not any(s in str(f.get("status") or "") for s in SKIP)


def size_len(spec):
    m = re.search(r"\b(M\d(?:\.\d)?)x(\d+(?:\.\d)?)", spec or "")
    return (m.group(1), float(m.group(2))) if m else (None, None)


def size_key(size, L):
    return "%sx%g" % (size, L)


def expand_sizes(txt):
    """'M2x4, M2x5, M2x6, M2x8 and M2.6x6, x8, x10, x12' -> ['M2x4', ..., 'M2.6x6', 'M2.6x8', 'M2.6x10', 'M2.6x12']
    (a bare 'x8' takes the diameter of the size before it)."""
    out, d = [], None
    for tok in re.findall(r"\b(M\d(?:\.\d)?)?x(\d+(?:\.\d)?)\b", txt or ""):
        d = tok[0] or d
        if d:
            out.append(size_key(d, float(tok[1])))
    return out


def kit_counts(b):
    """How many of each size one kit holds, read from the BOM line text: '50 each of M2x4, M2x5, ...' (sizes named) and
    '50 pcs of each size' (applies to the sizes named in the kit description, before 'Used'). Returns
    ({size: count}, [quotes], [problems]); an empty dict when the line states no count per size."""
    text = " | ".join(b.get(k, "") for k in ("Item", "Spec", "Verified"))     # '|' ends a size list at a column edge
    desc = re.split(r"\bUsed\b", b.get("Item", "") + " " + b.get("Spec", ""))[0]
    counts, quotes, probs = {}, [], []
    for m in re.finditer(r"\b(\d+)\s+each\s+of\s+(.+?)(?=;|:|\||\.\s|\.$|$)", text):
        sizes = expand_sizes(m.group(2))
        quotes.append(m.group(0).strip())
        for s in sizes:
            if s in counts and counts[s] != int(m.group(1)):
                probs.append("%s: %d and %s in the line" % (s, counts[s], m.group(1)))
            counts[s] = int(m.group(1))
    for m in re.finditer(r"\b(\d+)\s+(?:pcs|pieces)\s+(?:of\s+)?each\s+size\b", text):
        quotes.append(m.group(0).strip())
        for s in (list(counts) or expand_sizes(desc)):
            if s in counts and counts[s] != int(m.group(1)):
                probs.append("%s: %d and %s in the line" % (s, counts[s], m.group(1)))
            counts.setdefault(s, int(m.group(1)))
    return counts, quotes, probs


def c4a(D, bom):
    R = V.Result("C4a", "Every fitted screw has a BOM line, a length that line buys, and a count it covers (fasteners.json vs BOM.md)",
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/c4_fasteners.py",
                 "Every fitted screw in fasteners.json (servo case screws included): BOM line exists, size and length match the "
                 "line's Item and Spec, count per line vs Need and Buy, per size for a kit (the count per size its line "
                 "states, e.g. '50 each of'), screws with no line; washers and other new items",
                 "Servo and SG90 bag contents by size (B2, test order TO1 and TO6), thread engagement (fasteners agent), stock "
                 "at order time")
    R.inp(FJ, V.lab("BOM.md"))
    F = D["fasteners"]
    fit = [f for f in F if fitted(f)]
    skipped = Counter(f.get("status") for f in F if f["kind"] == "screw" and not fitted(f))
    R.ev("fasteners.json: %d records, %d screws, %d fitted (left out: %s), %d inserts" % (
        len(F), sum(1 for f in F if f["kind"] == "screw"), len(fit), dict(skipped) or "none", sum(1 for f in F if f["kind"] == "insert")))
    by_line = defaultdict(list)
    for f in fit:
        by_line[f.get("line")].append(f)
    no_line = by_line.pop(None, [])
    def bom_for(spec):
        size, L = size_len(spec)
        head = "button" if re.search(r"7380|button", spec, re.I) else ("SHCS|912" if re.search(r"912", spec) else "")
        for lid, b in bom.items():
            t = b["Item"] + " " + b["Spec"]
            if size and re.search(r"\b%sx%g\b" % (re.escape(size), L), t) and (not head or re.search(head, t, re.I)):
                return lid
        return None
    unmatched = []
    for spec, fs in sorted(Counter(f["spec"] for f in no_line).items()):
        lid = bom_for(spec)
        if lid:
            R.find("WARN", "%d x %s: fasteners.json names no BOM line, BOM.md line %s buys it (Need %s, Buy %s)" % (
                fs, spec, lid, bom[lid]["Need"], bom[lid]["Buy"]), fix="fasteners.json: set line '%s' on these screws" % lid,
                where="altaay_lab/fasteners")
            if V.num(bom[lid]["Need"]) != fs:
                R.find("FAIL", "line %s %s: schedule %d, BOM Need %s" % (lid, bom[lid]["Item"], fs, bom[lid]["Need"]))
        else:
            unmatched.append((spec, fs))
    if unmatched:
        R.find("FAIL", "%d fitted screws have no BOM line: %s" % (sum(n for _, n in unmatched), "; ".join("%d x %s" % (n, s) for s, n in unmatched)),
               fix="add a BOM.md line for each, or change the screw to a length the BOM buys", where="altaay_lab/BOM.md")
    bag_lines = {"1": "STS3215 servo bag (18 screws per servo, B2)", "14": "SG90 bag"}
    kit_note = []
    for line, fs in sorted(by_line.items(), key=lambda kv: kv[0]):
        if line not in bom:
            R.find("FAIL", "%d screws name BOM line %s, which is not in BOM.md" % (len(fs), line))
            continue
        b = bom[line]
        text = (b["Item"] + " " + b["Spec"])
        specs = Counter(f["spec"] for f in fs)
        if line in bag_lines:
            R.ev("line %s (%s): %d screws, %s" % (line, bag_lines[line], len(fs), dict(specs)))
            if line == "1":
                per_servo = len(fs) / 14.0
                if per_servo > 18:
                    R.find("FAIL", "the schedule takes %.1f screws per servo from the bag, more than the 18 it ships with" % per_servo)
            continue
        bad_len = []
        for s in specs:
            size, L = size_len(s)
            if size is None or not re.search(r"%sx%g\b" % (re.escape(size), L), text):
                bad_len.append(s)
        need, buy = V.num(b["Need"]), V.num(b["Buy"])
        pack = (b["Pack"] or "").lower()
        cap = None if pack == "kit" else (buy * V.num(pack) if V.num(pack) and buy < V.num(pack) else buy)
        R.ev("line %s %s: schedule %d (%s); BOM Need %s, Buy %s %s" % (line, b["Item"], len(fs), ", ".join("%d %s" % (n, s) for s, n in specs.items()),
                                                                     b["Need"], b["Buy"], b["Pack"]))
        if bad_len:
            R.find("FAIL", "line %s (%s) does not buy %s" % (line, b["Item"], bad_len),
                   fix="buy that length on its own line or change the screw", where="altaay_lab/BOM.md line %s" % line)
        if cap is not None and len(fs) > cap:
            R.find("FAIL", "line %s %s: the schedule fits %d, the BOM buys %g" % (line, b["Item"], len(fs), cap),
                   fix="BOM.md line %s: Need %d, Buy at least %d (10 to 20%% spares rule)" % (line, len(fs), int(len(fs) * 1.15 + 0.999)),
                   where="altaay_lab/BOM.md line %s" % line)
        elif need is not None and len(fs) != need:
            R.find("FAIL" if pack != "kit" else "WARN", "line %s %s: schedule %d, BOM Need %g" % (line, b["Item"], len(fs), need),
                   fix="BOM.md line %s: Need %d (fasteners.json count)%s" % (line, len(fs), "; and state how many of each size the kit holds" if pack == "kit" else ""),
                   where="altaay_lab/BOM.md line %s" % line)
        if pack == "kit":
            per, quotes, probs = kit_counts(b)
            nkit = buy or 1
            if not per:
                R.find("WARN", "line %s is a kit: how many of each size it holds is not in BOM.md, so %d screws (%s) cannot be checked against it"
                       % (line, len(fs), dict(specs)), fix="write the kit's count per size into BOM.md line %s" % line)
                kit_note.append("kit %s holds an unstated count per size" % line)
                continue
            for p_ in probs:
                R.find("FAIL", "line %s states two counts for one size: %s" % (line, p_), where="altaay_lab/BOM.md line %s" % line)
            used, short_, missing = [], [], []
            for s, n in sorted(specs.items(), key=lambda kv: -kv[1]):
                size, L = size_len(s)
                k = size_key(size, L) if size else s
                if k not in per:
                    missing.append("%d x %s" % (n, s))
                    continue
                used.append("%s %d of %d" % (k, n, per[k] * nkit))
                if n > per[k] * nkit:
                    short_.append("%s: the schedule fits %d, %g kit(s) hold %d" % (k, n, nkit, per[k] * nkit))
            R.ev("line %s kit, count per size from the line text (%s): %s" % (line, "; ".join("'%s'" % q for q in quotes), ", ".join(used) or "none"))
            for x in short_:
                R.find("FAIL", "line %s kit is short: %s" % (line, x), fix="BOM.md line %s: buy more kits or a second line for that size" % line,
                       where="altaay_lab/BOM.md line %s" % line)
            if missing:
                R.find("FAIL", "line %s kit does not hold %s (sizes in the kit: %s)" % (line, ", ".join(missing), ", ".join(sorted(per))),
                       fix="BOM.md: a line that buys that size", where="altaay_lab/BOM.md line %s" % line)
            # Need per size, when the line writes it ('30 (M2x5 22, M2x4 6, M2x8 2)'), against the schedule
            need_sz = {size_key(m.group(1), float(m.group(2))): int(m.group(3))
                       for m in re.finditer(r"\b(M\d(?:\.\d)?)x(\d+(?:\.\d)?)\s+(\d+)\b", b["Need"] or "")}
            sched_sz = Counter()
            for s, n in specs.items():
                size, L = size_len(s)
                sched_sz[size_key(size, L) if size else s] += n
            if need_sz and need_sz != dict(sched_sz):
                R.find("WARN", "line %s Need by size %s, the schedule fits %s" % (line, need_sz, dict(sched_sz)),
                       fix="BOM.md line %s Need: %s" % (line, ", ".join("%s %d" % kv for kv in sched_sz.items())),
                       where="altaay_lab/BOM.md line %s" % line)
            kit_note.append("kit %s holds %s per size by its line text, enough for %s" % (
                line, "/".join(str(v) for v in sorted(set(per.values()))), ", ".join(used)) if not (short_ or missing)
                else "kit %s is short or lacks a size (see FAIL)" % line)
    others = [b for b in D.get("bom", []) if b.get("line") == "new"]
    screw_specs = {f["spec"] for f in no_line}
    for b in others:
        sp = b["specs"] if isinstance(b["specs"], str) else ", ".join(b["specs"])
        rest = [x.strip() for x in re.split(r",\s*(?=[A-Z])", sp) if not any(x.strip().startswith(t) for t in screw_specs)]
        rest = [x for x in rest if not (re.search(r"washer", x, re.I) and any(re.search(r"washer", b["Item"], re.I) and
                                                                               re.search(r"M2\.5", b["Item"]) for b in bom.values()))]
        if rest:
            R.find("FAIL", "fasteners.json also needs, with no BOM line: %s" % ", ".join(rest),
                   fix="add a BOM.md line (FASTENERS.md section 2 'new' row)", where="altaay_lab/BOM.md")
    nl = sum(len(v) for v in by_line.values())
    off = sorted({re.search(r"line (\w+)", f["text"]).group(1) for f in R.d["findings"] if f["sev"] == "FAIL" and re.search(r"^line \w+", f["text"])})
    R.key("%d fitted screws and %d inserts; %d screws name no BOM line in fasteners.json (BOM.md buys %d of them); Need differs "
          "from the schedule on lines: %s; %s" % (
              len(fit), sum(1 for f in F if f["kind"] == "insert"), len(no_line), len(no_line) - sum(n for _, n in unmatched),
              ", ".join(off) or "none", "; ".join(kit_note) or "no kit line"))
    ins = [f for f in F if f["kind"] == "insert"]
    R.ev("inserts: %d in fasteners.json, BOM 16 Need %s" % (len(ins), bom["16"]["Need"]))
    if len(ins) != V.num(bom["16"]["Need"]):
        R.find("FAIL", "inserts: fasteners.json %d vs BOM 16 Need %s" % (len(ins), bom["16"]["Need"]))
    return R


def c4b(D):
    R = V.Result("C4b", "No screw head or tip collision over the joint ranges, except known, decided ones (fasteners sweep vs D18 and D19)",
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/c4_fasteners.py",
                 "Every fitted screw's head and protruding tip vs every part over each joint's URDF range and 13 joint pairs "
                 "(sweep_fasteners.py results in fasteners.json); hits split into screw-limited, parts-first and static contact",
                 "Real head sizes of the bag screws (stand-in models), print tolerance, real joint stops tighter than the URDF")
    R.inp(FJ, V.lab("DECISIONS.md"))
    sw = D.get("sweep")
    if not sw:
        R.not_run("fasteners.json has no sweep yet (sweep_fasteners.py not run)")
        return R
    F = {f["id"]: f for f in D["fasteners"]}
    hits = sw.get("hits", [])
    st = Counter((f.get("sweep") or {}).get("status") for f in F.values() if fitted(f))
    R.ev("sweep: %d steps per joint, %d joint pairs, %d hit rows; fitted screws by status %s" % (sw.get("steps"), len(sw.get("pairs", [])),
                                                                                             len(hits), dict(st)))
    decided = {fid for fid, f in F.items() if "D18" in str(f.get("status")) or "D18" in " ".join(map(str, f.get("notes") or []))}
    dec_txt = {}
    for ln in open(V.lab("DECISIONS.md")).read().splitlines():
        m = re.match(r"^- (D\d+)\b.*DECIDED", ln)
        if m:
            for fid in re.findall(r"\bF\d{3}\b", ln):
                dec_txt.setdefault(fid, m.group(1))
    R.ev("screws named in a DECIDED entry of DECISIONS.md: %s" % (", ".join("%s (%s)" % kv for kv in sorted(dec_txt.items())) or "none"))
    by = defaultdict(list)
    for h in hits:
        if h["id"] in F and fitted(F[h["id"]]):
            by[h["cls"]].append(h)
    R.ev("hit rows on fitted screws by class: %s" % {k: len(v) for k, v in by.items()})
    scr = [h for h in by.get("screw", []) + by.get("static overlap", [])]
    groups = {"button head fixes it": set(), "button head, under 0.3 mm": set(), "button head still hits": set(),
              "stand-in head (size not published)": set(), "against a CAD body the build replaces": set(), "no decision": set()}
    for h in scr:
        f = F[h["id"]]
        if h["id"] in decided:
            continue
        iso = (f.get("sweep") or {}).get("with_iso7380_head")
        stand_in = f.get("source") == "servo_case" or "SG90" in f["spec"] or str(f.get("status")) in ("FACTORY", "UNVERIFIED")
        if "ISO 7380" in f["spec"] and iso is not None:
            k = "button head fixes it" if iso["clearance_mm"] >= 0.3 else ("button head, under 0.3 mm" if iso["clearance_mm"] >= 0 else "button head still hits")
        elif stand_in:
            k = "stand-in head (size not published)"
        elif h["against"] in ("bms", "board", "power_switch", "usb_c_charger"):
            k = "against a CAD body the build replaces"
        else:
            k = "no decision"
        groups[k].add(h["id"])
    R.ev("screw-limited and static-overlap hits by screw: %s" % "; ".join("%s %d" % (k, len(v)) for k, v in groups.items() if v))
    R.ev("parts collide before the screw: %d rows; static contact under 0.1 mm at the zero pose: %d rows" % (
        len(by.get("parts collide first", [])), len(by.get("static contact", []))))
    def worst_of(ids):
        hs = sorted([h for h in scr if h["id"] in ids], key=lambda h: h["worst_mm"])
        out, seen = [], set()
        for h in hs:
            if h["id"] in seen:
                continue
            seen.add(h["id"])
            iso = (F[h["id"]].get("sweep") or {}).get("with_iso7380_head")
            out.append("%s %s vs %s at %s %s, %.2f mm%s" % (h["id"], F[h["id"]]["spec"], h["against"], h["where"], h["at"], h["worst_mm"],
                                                            (", %.2f mm with the button head" % iso["clearance_mm"]) if iso and "ISO 7380" in F[h["id"]]["spec"] else ""))
        return "; ".join(out[:6])
    envp = os.path.join(V.out_dir(), "e9_envelope.json")
    env_txt = ""
    if os.path.exists(envp):
        E0 = json.load(open(envp))
        Es = [E0[m] for m in ("stock", "ours") if m in E0] or [E0]
        def span(j):
            lo = [E[k]["lo_deg"][j] for E in Es for k in E if k != "stand_in_place" and E[k]["lo_deg"].get(j) is not None]
            hi = [E[k]["hi_deg"][j] for E in Es for k in E if k != "stand_in_place" and E[k]["hi_deg"].get(j) is not None]
            return (min(lo), max(hi)) if lo and hi else None
        onset = {}
        for h in scr:
            if h["id"] in groups["button head still hits"] and h.get("angles") and "+" not in h["where"]:
                a = min(h["angles"], key=abs)
                onset[h["id"]] = (h["where"], a, span(h["where"]))
        env_txt = "; ".join("%s: hits from %s %+.1f deg, the sim walk uses %+.1f to %+.1f deg (E9)" % (k, w, a, sp[0], sp[1])
                            for k, (w, a, sp) in sorted(onset.items()) if sp)
        if env_txt:
            R.ev("collision onset vs the sim walk envelope: " + env_txt)
    still = groups["button head still hits"]
    known = {i for i in still if i in dec_txt}
    if still - known:
        R.find("FAIL", "%d screws still hit with the ISO 7380 button head fasteners.json now gives them, and no decision covers it: %s%s" % (
            len(still - known), worst_of(still - known),
            (" (outside the walk: %s; the URDF range, falls and manual moves still reach it)" % env_txt) if env_txt else ""),
            fix="a decision in DECISIONS.md: limit hip yaw to about 21.7 deg in the controller and the sim (FASTENERS.md findings 3 "
                "and 4) or a relief in body_middle_bottom; until then this is an open collision", where="altaay_lab/DECISIONS.md")
    if known:
        R.find("WARN", "%d screws still hit with the button head, known and left as a joint range point in %s (not fixed): %s%s" % (
            len(known), ", ".join(sorted({dec_txt[i] for i in known})), worst_of(known),
            (" (outside the walk: %s, see C11)" % env_txt) if env_txt else ""),
            fix="see C11: nothing in the Runtime limits hip yaw; decide the limit before the first powered joint sweep (TEST_PLAN.md 8.3)")
    if groups["no decision"]:
        R.find("FAIL", "%d fitted screws hit a part with no decision: %s" % (len(groups["no decision"]), worst_of(groups["no decision"])),
               fix="shorter or low-head screw, leave it out (like D18), or a decision in DECISIONS.md", where="altaay_lab/fasteners")
    if groups["button head fixes it"] or groups["button head, under 0.3 mm"]:
        bh = groups["button head fixes it"] | groups["button head, under 0.3 mm"]
        line_bh = next((lid for lid, b in V.bom_lines().items() if re.search(r"button head", b["Item"], re.I)), None)
        R.find("WARN", "%d screws clear only because of the M3x6 ISO 7380 button head (decision: %s; BOM line: %s); %d of them by less "
               "than 0.3 mm: %s" % (len(bh), ", ".join(sorted({dec_txt[i] for i in bh if i in dec_txt})) or "none",
                                     line_bh or "none", len(groups["button head, under 0.3 mm"]), worst_of(groups["button head, under 0.3 mm"])),
               fix="record the button-head change as a decision (DECISIONS.md D19) with the BOM line, and add the rub check to the "
                   "first-leg check (print/PRINT_PLAN.md)")
    if groups["stand-in head (size not published)"]:
        R.find("WARN", "%d servo case or bag screws overlap a part with the stand-in head model (real head size not published): %s" % (
            len(groups["stand-in head (size not published)"]), worst_of(groups["stand-in head (size not published)"])),
            fix="measure the factory and bag screw heads on the first servo and the SG90 pack (test orders TO1 and TO6, B2)")
    if groups["against a CAD body the build replaces"]:
        R.find("WARN", "%d screws touch a CAD body the build replaces (keep the real part clear when placing it): %s" % (
            len(groups["against a CAD body the build replaces"]), worst_of(groups["against a CAD body the build replaces"])))
    sc = by.get("static contact", [])
    if sc:
        w = min(sc, key=lambda h: h["worst_mm"])
        R.find("WARN", "%d screws touch a part at the zero pose by up to %.2f mm (static contact: head seated against a face; "
               "under the 0.1 mm modelling resolution)" % (len({h['id'] for h in sc}), -w["worst_mm"]))
    R.key("screw hits by kind: %s; D18 screws left out: %d" % ("; ".join("%s %d" % (k, len(v)) for k, v in groups.items() if v),
                                                              sum(1 for f in F.values() if "D18" in str(f.get("status")))))
    d18 = [f for f in F.values() if "D18" in str(f.get("status"))]
    R.ev("D18 screws marked in fasteners.json: %d (%s)" % (len(d18), ", ".join(f["id"] for f in d18) or "none"))
    if not d18:
        R.find("WARN", "no screw in fasteners.json carries the D18 decision (the outer hip roll screw left out on both legs)",
               fix="mark the 2 outer roll_motor_bottom screws status 'LEAVE OUT (D18)' in make_fasteners.py", where="altaay_lab/fasteners")
    return R


def main():
    if not os.path.exists(FJ):
        for cid, t in (("C4a", "Every fitted screw has a BOM line"), ("C4b", "No screw collision over the joint ranges")):
            r = V.Result(cid, t, "VERIFY_OUT=<out> python3 altaay_lab/verify/c4_fasteners.py", "", "")
            r.not_run("altaay_lab/fasteners/fasteners.json not found")
            r.write()
        return
    D = json.load(open(FJ))
    bom = V.bom_lines()
    c4a(D, bom).write()
    c4b(D).write()


if __name__ == "__main__":
    main()
