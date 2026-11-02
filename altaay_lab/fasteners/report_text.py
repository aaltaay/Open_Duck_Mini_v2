"""Text of FASTENERS.md sections 3 to 9, built from fasteners.json data (imported by report_fasteners.py)."""
from collections import Counter, defaultdict


def ids_compact(ids):
    nums = sorted(int(i[1:]) for i in ids)
    out, start, prev = [], None, None
    for n in nums:
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            out.append("F%03d" % start if start == prev else "F%03d-F%03d" % (start, prev))
            start = prev = n
    if start is not None:
        out.append("F%03d" % start if start == prev else "F%03d-F%03d" % (start, prev))
    return ", ".join(out)


def nice(p):
    return p.replace("wj-wk00-0122topcabinetcase_95", "servo top").replace("wj-wk00-0124bottomcase_45", "servo bottom") \
        .replace("wj-wk00-0123middlecase_56", "servo middle")


def sweep_text(r):
    sw = r.get("sweep") or {}
    if not sw:
        return "not swept"
    sf = sw.get("screw_first")
    if sf is not None:
        t = "%s %+.2f vs %s (%s%s)" % (sf.get("cylinder", "head"), sf["clearance_mm"], nice(sf["against"]), sf["where"],
                                       "" if sf["where"].startswith("zero") else " %s" % (sf["at"],))
        if sw.get("status") == "PARTS COLLIDE FIRST":
            t += "; bare parts collide first in some sweeps"
        return t
    parts = []
    for k in ("head", "tip"):
        if k in sw:
            s = sw[k]
            parts.append("%s %.2f vs %s (%s)" % (k, s["clearance_mm"], s["against"].replace("wj-wk00-0122topcabinetcase_95", "servo top")
                                                  .replace("wj-wk00-0124bottomcase_45", "servo bottom")
                                                  .replace("wj-wk00-0123middlecase_56", "servo middle"), s["where"]))
    return "; ".join(parts)


def build(D, screws, inserts, fitted, hits, d18, bom_rows, short_part, fmt, GROUPS, SRC):
    L = []
    w = L.append
    byid = {r["id"]: r for r in screws}
    # ------------------------------------------------------------------ 3. findings
    w("## 3. Findings that change the build")
    w("")
    w("Severity: print-blocking (fix before the part is printed), build-blocking (fix or decide before assembly), note.")
    w("")
    F = []
    # sweep hits other than D18 and tessellation-level contacts
    real = [h for h in hits if h["worst_mm"] < -0.1 and not any(h["id"] == r["id"] and h["kind"] == "head" for r, _ in d18)]
    contact = [h for h in hits if -0.1 <= h["worst_mm"] < 0]
    if d18:
        F.append(("note (known, D18)", "Sweep finds the D18 hit again: the outer servo-bag M2 screw in roll_motor_bottom (%s) "
                  "overlaps the roll_to_pitch arm by up to %.2f mm over the whole hip roll range, both legs, with the 4.0 x 1.6 mm pan "
                  "head stand-in (D18 found 1.3 mm with the head on the site axis; here the screw sits on the pilot centre line). "
                  "Left out as D18 decided; marked LEAVE OUT in fasteners.json." % (
                      ", ".join(r["id"] for r, _ in d18), -min(h["worst_mm"] for _, h in d18))))
    for code, txt in D.get("_findings", []):
        F.append((code, txt))
    for n, (sev, txt) in enumerate(F, 1):
        w("%d. **%s**: %s" % (n, sev, txt))
    w("")
    # ------------------------------------------------------------------ 4. schedule
    w("## 4. Schedule by subassembly")
    w("")
    w("One row per joint type. e = thread engaged (mm), rule = minimum from section 8. Length status: OK meets the rule; "
      "BELOW RULE = the longest stock length that does not bottom is still short of the rule; NEW LENGTH = not on BOM.md. "
      "Window = where the anchor starts and ends below the head seat, stop = first solid surface on the screw core. "
      "Sweep = worst clearance of head or tip over the static check and the joint sweeps where the screw is touched before "
      "the bare parts touch (negative = overlap; values within 0.1 mm of zero are sampling level). Per-instance positions, "
      "links and notes: fasteners.json and fasteners.csv.")
    for g, title in GROUPS:
        rows = defaultdict(list)
        for r in screws:
            if r["group"] != g:
                continue
            key = (r.get("part"), r.get("into"), r.get("anchor"), r["spec"], r.get("status") or "", r.get("len_status") or "")
            rows[key].append(r)
        ins = [x for x in inserts if x["group"] == g]
        w("")
        w("### %s" % title)
        w("")
        w("| Qty | Spec | Joins (head side -> anchor) | Anchor | Window near-far, stop | e / rule | Length | Clearance hole, head recess | Sweep worst | Supply | IDs |")
        w("|---|---|---|---|---|---|---|---|---|---|---|")
        for key, rs in sorted(rows.items(), key=lambda kv: (kv[0][2] or "", kv[0][0] or "", kv[0][3])):
            r = rs[0]
            cl = r.get("clearance") or {}
            rc = r.get("recess_check") or {}
            clr = ("%s %s (%+.2f)" % (fmt(cl.get("hole"), 2), cl.get("status"), cl.get("margin"))) if cl else ""
            if rc:
                clr += "; recess %s vs head %s %s" % (fmt(rc["recess"], 2), fmt(rc["head"], 2), rc["status"])
            if r.get("head_proud_of_recess"):
                clr += "; head sits on the face (recess too small)"
            worst = min(rs, key=lambda x: ((x.get("sweep") or {}).get("screw_first") or {}).get("clearance_mm", 99))
            st = r.get("status") or ""
            lens = (r.get("len_status") or "") + ((" / " + st) if st and st not in ("OK",) else "")
            w("| %d | %s | %s -> %s | %s | %s-%s, %s | %s / %s | %s | %s | %s | %s | %s |" % (
                len(rs), r["spec"], short_part(r.get("part")), short_part(r.get("into")), r.get("anchor"),
                fmt(r.get("near")), fmt(r.get("far")), fmt(r.get("stop")), fmt(r.get("e")), fmt(r.get("e_min")),
                lens, clr, sweep_text(worst), (r.get("supply") or "").split(" [")[0], ids_compact([x["id"] for x in rs])))
        if ins:
            w("| %d | M3 heat-set insert | in %s | bore %s | | | | | | BOM 16 | %s |" % (
                len(ins), ", ".join(sorted({x["into"] for x in ins})), ", ".join(sorted({"%.2f x %.1f" % (x.get("bore_d", 0), x.get("bore_len", 0)) for x in ins})),
                ", ".join(x["id"] for x in ins)))
    w("")
    # ------------------------------------------------------------------ 5. checks
    w("## 5. Checks")
    w("")
    sw = D.get("sweep", {})
    w("(a) Heads and tips against every part, over every joint range: %d heads and %d protruding tips; static check at the "
      "zero pose against every part, single sweeps of all %d revolute joints over their URDF limits (%d steps each), and "
      "%d consecutive joint pairs on a %dx%d grid (%s). Part surfaces sampled at %.0f points per mm2. Method as "
      "print/check_hip_roll_screw.py. %d hit rows (one row per screw, cylinder, part and sweep), classed below; %d of them "
      "are within 0.1 mm (sample spacing and tessellation level)." % (
          sum(1 for r in screws if (r.get("head") or {}).get("dk")), sum(1 for r in screws if "tip" in (r.get("sweep") or {})),
          len(sw.get("joints", [])), sw.get("steps", 0), len(sw.get("pairs", [])), sw.get("grid", 0), sw.get("grid", 0),
          ", ".join(sw.get("pairs", [])), sw.get("density", 0),
          len(hits), sum(1 for h in hits if -0.1 <= h["worst_mm"] < 0)))
    w("")
    cls = Counter(h.get("cls") for h in hits)
    w("Hit classes: " + ", ".join("%s %d" % kv for kv in cls.most_common()) + ". 'parts collide first' = at the smallest angle "
      "where the screw is touched, the touching part already cuts into a part on the screw's side, so the joint cannot get "
      "there (a joint range question for the sim and the controller, not a screw question). 'static contact' = within 0.1 mm "
      "at the zero pose (sampling level). Rows that matter (screw first, or static overlap deeper than 0.1 mm):")
    w("")
    w("| ID | Spec | Cylinder | Against | Where | Worst (mm) | At | Class | With ISO 7380 head |")
    w("|---|---|---|---|---|---|---|---|---|")
    fac = [h for h in hits if h.get("cls") == "static overlap" and byid[h["id"]]["source"] == "servo_case"]
    for h in sorted([h for h in hits if h.get("cls") in ("screw", "static overlap") and h not in fac],
                    key=lambda h: (h["id"], h["worst_mm"])):
        low = (byid[h["id"]].get("sweep") or {}).get("with_iso7380_head")
        lowt = ("%+.2f" % low["clearance_mm"]) if low and low.get("against") == h["against"] else ("%+.2f vs %s" % (
            low["clearance_mm"], low["against"]) if low else "")
        w("| %s | %s | %s | %s | %s | %.2f | %s | %s | %s |" % (h["id"], h["spec"], h["kind"], short_part(h["against"]), h["where"],
                                                           h["worst_mm"], h["at"], h.get("cls"), lowt))
    if fac:
        w("| %d factory case screws | PA2.0 (factory) | head | the bracket above each servo | zero pose (static) | %.2f | 0.0 | "
          "static overlap | model limit: stand-in head 1.6 mm, relief 1.38 mm (section 3) |" % (
              len({h["id"] for h in fac}), min(h["worst_mm"] for h in fac)))
    pc = Counter()
    for h in hits:
        if h.get("cls") == "parts collide first":
            pc[h["where"]] += 1
    w("")
    w("Joint sweeps where bare parts collide inside the URDF limits (seen from the screws; rows per joint): " +
      ", ".join("%s %d" % kv for kv in pc.most_common()) + ".")
    w("")
    ls = Counter(r.get("len_status") for r in fitted if r.get("len_status"))
    w("(b) Engagement against the cited rules (section 8): " + ", ".join("%s %d" % kv for kv in ls.most_common()) +
      ". Every BELOW RULE row is set by the CAD pilot or bore depth: no stock length meets the rule without bottoming. "
      "Rows: section 4; shortfalls are listed as findings. No new BLOCKER: the 4 camera rows (BOTTOMS with an assumed 1.0 mm "
      "PCB) wait on B9.")
    w("")
    cs = Counter((r.get("clearance") or {}).get("status") for r in fitted if r.get("clearance"))
    rs_ = Counter((r.get("recess_check") or {}).get("status") for r in fitted if r.get("recess_check"))
    w("(c) Clearance holes (hole minus screw major diameter; printed holes under 0.15 mm margin = TIGHT): " +
      ", ".join("%s %d" % kv for kv in cs.most_common()) + ". Head recesses (recess minus head dk, DIN 912 knurled max): " +
      ", ".join("%s %d" % kv for kv in rs_.most_common()) + ".")
    w("")
    w("(d) Counts per spec against BOM.md: section 2. Mismatches and fixes: section 9.")
    w("")
    # ------------------------------------------------------------------ 6. servo hardware
    w("## 6. Servo and SG90 hardware (what comes in the bags)")
    w("")
    for t in D.get("_servo_text", []):
        w("- " + t)
    w("")
    # ------------------------------------------------------------------ 7. ledger
    led = D.get("empty_holes", [])
    w("## 7. Every hole accounted for")
    w("")
    w("Hole stacks found on the printed STLs: %d. Used by a fastener or insert: %d. Empty, with the reason:" % (
        D["meta"]["scene"]["sites"], D["meta"]["scene"]["sites"] - len(led)))
    w("")
    w("| Reason | Stacks |")
    w("|---|---|")
    for k, v in Counter(x["why"].split(" (")[0].split(":")[0] if not x["why"].startswith("UNUSED") else x["why"] for x in led).most_common():
        w("| %s | %d |" % (k, v))
    w("")
    # ------------------------------------------------------------------ 8. rules
    w("## 8. Rules and sources")
    w("")
    for t in D.get("_rules_text", []):
        w("- " + t)
    w("")
    # ------------------------------------------------------------------ 9. edits and blockers
    w("## 9. Proposed edits for files this folder does not own, and open BLOCKERs")
    w("")
    for t in D.get("_edits_text", []):
        w("- " + t)
    w("")
    return L
