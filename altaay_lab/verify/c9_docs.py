"""C9: numbers that appear in several docs are the same everywhere (history/ entries are dated and never edited, so
they are left out). Each fact is computed from its source, then every mention found by a pattern is compared.

Facts:
  blockers     total, cleared or decided, test print, open (HARDWARE_AUDIT.md section 6 table) vs every "N BLOCKERS",
               "all N", "X of N cleared", "4 settled by the coupon", "6 assembly or bench checks", "2 waiting"
  blocker words  every "Bnn cleared" in another doc vs the status in HARDWARE_AUDIT.md; BOM.md "BLOCKERS that affect
               this BOM" bullets that only name cleared or decided blockers
  BOM totals   BOM.md Totals table (recomputed by E2) vs totals quoted elsewhere as current
  test order   BOM.md test order total vs other mentions
  part counts  START_HERE "52/52 printed parts, 14/14 servos, 58/58 inserts, 3/3 bearings" vs the fresh viewer run (E4);
               "N STLs" vs print/*.stl
  screws       HARDWARE_AUDIT "189 screws by size" vs BOM.md 17a to 17i Need vs fasteners.json vs MASS_BUDGET.md
  decisions    "D1 to Dn" vs the last decision in DECISIONS.md
  upstream     "137" vs the UPSTREAM_ISSUES.md total line
  currents     WIRING.md section 4 table vs the netlist i_mean, i_peak, i_fall per cable
  print        STATE.md coupon and full print numbers vs print/PRINT_PLAN.md and PRINT_CHECK.md
  mass         2.11 kg (START_HERE, README) vs the trained 2.107 kg and the build 2.77 kg (MASS_BUDGET.md)
Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/c9_docs.py
"""
import glob
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

DOCS = sorted(set(glob.glob(V.lab("*.md")) + glob.glob(V.lab("*", "*.md"))) - set(glob.glob(V.lab("history", "*.md")))
                 - {V.lab("VERIFICATION.md")})


def rel(p):
    return os.path.relpath(p, V.LAB)


def lines_of(p):
    return open(p, encoding="utf-8").read().splitlines()


def mentions(pattern, flags=0):
    out = []
    for p in DOCS:
        for i, ln in enumerate(lines_of(p), 1):
            for m in re.finditer(pattern, ln, flags):
                out.append((rel(p), i, m, ln))
    return out


def main():
    R = V.Result("C9", "Docs agree: numbers that appear in several docs are the same everywhere",
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/c9_docs.py",
                 "Blocker counts and blocker status words, BOM totals and test order total, part counts, STL count, screw "
                 "counts, decision range, upstream issue count, wire currents (WIRING.md vs netlist), print numbers, robot mass; "
                 "%d docs (history/ left out)" % len(DOCS),
                 "Numbers written in words or in a form the patterns do not catch; history entries; prose claims without numbers")
    R.inp(*DOCS)
    # ------------------------------------------------------------------ blockers
    blk = {}
    for t in V.md_tables(V.lab("HARDWARE_AUDIT.md")):
        if t["header"][:2] == ["#", "Blocker"]:
            for r in t["rows"]:
                blk[r["#"]] = r["Status"]
    n = len(blk)
    tprint = [b for b, s in blk.items() if "TEST PRINT" in s]          # 'DECIDED (D20), TEST PRINT, coupon C4' counts here
    cleared = [b for b, s in blk.items() if s.startswith(("CLEARED", "DECIDED")) and b not in tprint]
    opened = [b for b, s in blk.items() if s.startswith("OPEN")]
    waiting = [b for b in opened if not re.search(r"assembly|bench", blk[b])]
    R.ev("HARDWARE_AUDIT.md section 6: %d blockers; cleared or decided %d; test print %d; open %d (%d assembly or bench, %d waiting on parts: %s)" % (
        n, len(cleared), len(tprint), len(opened), len(opened) - len(waiting), len(waiting), ", ".join(waiting)))
    nb0 = 0
    for f, i, m, ln in mentions(r"\b(\d+) of (\d+) cleared( or decided)?"):
        nb0 += 1
        a, b = int(m.group(1)), int(m.group(2))
        if (a, b) != (len(cleared), n):
            good = m.group(0).replace("%d of %d" % (a, b), "%d of %d" % (len(cleared), n), 1)
            R.find("FAIL", "%s line %d says '%s', HARDWARE_AUDIT.md has %d of %d cleared or decided" % (f, i, m.group(0), len(cleared), n),
                   fix="%s line %d: '%s' -> '%s'" % (f, i, m.group(0), good), where="altaay_lab/" + f)
    checks = [(r"\b(\d+) BLOCKERS\b", n, "total"), (r"\ball (\d+) with the method", n, "total"),
              (r"\b(\d+) settled by the coupon", len(tprint), "test print"),
              (r"\b(\d+) assembly or bench checks", len(opened) - len(waiting), "open, assembly or bench"),
              (r"\b(\d+) waiting on (?:the parts check|part arrival)", len(waiting), "open, waiting on parts")]
    nb = 0
    for pat, want, what in checks:
        for f, i, m, ln in mentions(pat):
            nb += 1
            if int(m.group(1)) != want:
                R.find("FAIL", "%s line %d says %s blockers %s, HARDWARE_AUDIT.md has %d: '%s'" % (f, i, what, m.group(1), want, m.group(0)),
                       fix="%s line %d: '%s' -> '%s'" % (f, i, m.group(0), m.group(0).replace(m.group(1), str(want), 1)), where="altaay_lab/" + f)
    R.ev("blocker count mentions checked: %d" % (nb + nb0))
    # blocker status words in other docs
    nw = 0
    for f, i, m, ln in mentions(r"\b(B\d+)\b(?: is)? cleared( on paper)?"):
        if f == "HARDWARE_AUDIT.md":
            continue
        nw += 1
        b = m.group(1)
        if b in blk and not blk[b].startswith(("CLEARED", "DECIDED")):
            R.find("FAIL", "%s line %d says '%s', HARDWARE_AUDIT.md has %s %s" % (f, i, m.group(0), b, blk[b]),
                   fix="make %s line %d match HARDWARE_AUDIT.md (%s: %s), or clear %s in HARDWARE_AUDIT.md with its evidence" % (
                       f, i, b, blk[b].split(",")[0], b), where="altaay_lab/" + f)
    R.ev("'Bnn cleared' mentions outside HARDWARE_AUDIT.md: %d" % nw)
    sec = V.md_section(V.lab("BOM.md"), r"^BLOCKERS that affect this BOM")
    for ln in sec.splitlines():
        if ln.startswith("- ") and re.search(r"\bB\d+\b", ln):
            bs = re.findall(r"\bB\d+\b", ln)
            closed = lambda st: st.startswith(("CLEARED", "DECIDED")) and not re.search(r"checked on|TEST PRINT|test order", st)  # noqa: E731
            if bs and all(closed(blk.get(b, "")) for b in bs):
                R.find("FAIL", "BOM.md 'BLOCKERS that affect this BOM' still lists '%s', but %s %s in HARDWARE_AUDIT.md" % (
                    ln[2:90], ", ".join(bs), "are" if len(bs) > 1 else "is " + blk[bs[0]].split(" (")[0]),
                    fix="BOM.md: drop the bullet '%s' (or rewrite it to the current status)" % ln[2:60], where="altaay_lab/BOM.md")
    # ------------------------------------------------------------------ BOM totals and test order
    tot = {}
    for t in V.md_tables(V.lab("BOM.md")):
        if t["header"] == ["Scope", "$"]:
            tot = {r["Scope"]: float(r["$"]) for r in t["rows"]}
    to = re.search(r"Test order total: \$([0-9.]+)\.", open(V.lab("BOM.md")).read())
    R.ev("BOM.md: build %.2f, with expression %.2f, with tools %.2f; test order %s" % (
        tot.get("Build total (robot + fasteners + cables + filament)", 0), tot.get("Build + expression pack", 0),
        tot.get("Build + expression + tools", 0), to.group(1) if to else "?"))
    keys = [("build total", "Build total (robot + fasteners + cables + filament)"), ("build + expression pack", "Build + expression pack"),
            ("build + expression + tools", "Build + expression + tools")]
    nq = 0
    for p in DOCS:
        if rel(p) == "BOM.md":
            continue
        for i, ln in enumerate(lines_of(p), 1):
            low = ln.lower()
            for k, key in keys:
                for m in re.finditer(re.escape(k) + r"[^$]{0,40}?\$([0-9,]+\.[0-9]{2})", low):
                    pre, post = low[max(0, m.start() - 40):m.start()], low[m.end():m.end() + 4]
                    if re.search(r"before|previous|was\b", pre + m.group(0)) or re.search(r"^\s*[+=]", post):
                        continue          # an old value, or the first term of a sum ('$919.54 + $31.56 = $951.10')
                    if True:
                        nq += 1
                        v = float(m.group(1).replace(",", ""))
                        if key in tot and abs(v - tot[key]) > 0.005:
                            R.find("FAIL", "%s line %d quotes %s $%s, BOM.md has %.2f" % (rel(p), i, k, m.group(1), tot[key]))
            if "test order" in low and "$" in ln:
                for m in re.finditer(r"test order total[^$]*\$([0-9.]+)", low):
                    nq += 1
                    if to and abs(float(m.group(1).rstrip(".")) - float(to.group(1))) > 0.005:
                        R.find("FAIL", "%s line %d test order total $%s, BOM.md $%s" % (rel(p), i, m.group(1), to.group(1)))
    R.ev("totals quoted as current outside BOM.md: %d checked" % nq)
    # ------------------------------------------------------------------ part counts
    man = os.path.join(V.out_dir(), "e4_viewer", "manifest.json")
    if os.path.exists(man):
        S = json.load(open(man))["checklist"]["summary"]
        fresh = {"printed parts": (S["printed"]["found"], S["printed"]["expected"]), "servos": (S["servos"]["found"], S["servos"]["expected"]),
                 "inserts": (S["inserts"]["found"], S["inserts"]["expected"]), "bearings": (S["bearings"]["found"], S["bearings"]["expected"])}
        for f, i, m, ln in mentions(r"\b(\d+)/(\d+) (printed parts|servos|inserts|bearings)\b"):
            a, b = fresh[m.group(3)]
            if (int(m.group(1)), int(m.group(2))) != (a, b):
                R.find("FAIL", "%s line %d says %s, the viewer run finds %d/%d" % (f, i, m.group(0), a, b))
        R.ev("part counts (viewer run E4): %s" % ", ".join("%s %d/%d" % (k, *v) for k, v in fresh.items()))
    nstl = len(glob.glob(os.path.join(V.REPO, "print", "*.stl")))
    for f, i, m, ln in mentions(r"\b(\d+) STLs\b"):
        if re.search(r"\(%s STLs\)" % m.group(1), ln):      # '(21 STLs)' after a subset of parts
            continue
        if int(m.group(1)) != nstl:
            R.find("FAIL", "%s line %d says %s, print/ has %d STL files" % (f, i, m.group(0), nstl))
    R.ev("print/ STL files: %d" % nstl)
    # ------------------------------------------------------------------ screws
    bom = V.bom_lines()
    sl = [k for k in bom if re.fullmatch(r"17[a-z]", k) and not re.search(r"washer", bom[k]["Item"], re.I)]
    need = sum(V.num(bom[k]["Need"]) for k in sl)
    fj = V.lab("fasteners", "fasteners.json")
    sched = None
    if os.path.exists(fj):
        D = json.load(open(fj))
        fit = [x for x in D["fasteners"] if x["kind"] == "screw" and not any(s in str(x.get("status") or "") for s in ("NOT FITTED", "LEAVE OUT"))]
        bought = [x for x in fit if re.fullmatch(r"17[a-z]", str(x.get("line"))) or x.get("line") is None]
        sched = (len(bought), len(fit))
    mb = open(V.lab("sim", "MASS_BUDGET.md")).read() if os.path.exists(V.lab("sim", "MASS_BUDGET.md")) else ""
    mbs = re.search(r"which gives exactly the audit counts: (.*?) \[L\]", mb)
    mb_n = sum(int(x) for x in re.findall(r"(\d+) (?:insert screws|horn screws|servo-case screws|M2\.5x6|horn centre screws|eye screws|lid|camera|roll_to_pitch)", mbs.group(1))) if mbs else None
    ha = re.search(r"\((\d+) screws by size, (\d+) inserts\)", open(V.lab("HARDWARE_AUDIT.md")).read())
    R.ev("screws: HARDWARE_AUDIT B1 %s; BOM.md screw lines %s Need %g; fasteners.json %s; MASS_BUDGET.md model %s" % (
        ha.group(1) if ha else "?", "17" + "/".join(k[2:] for k in sl), need,
        "%d bought (17x lines and no line) of %d fitted" % sched if sched else "not landed",
        mb_n if mb_n is not None else "?"))
    if ha and int(ha.group(1)) != need:
        R.find("FAIL", "HARDWARE_AUDIT.md B1 says %s screws by size, the BOM.md screw lines (17a to 17%s) need %g" % (ha.group(1), sl[-1][-1], need),
               fix="HARDWARE_AUDIT.md B1: write the count of the final fastener schedule (fasteners/fasteners.json) and the same in BOM.md",
               where="altaay_lab/HARDWARE_AUDIT.md B1")
    if mb_n is not None and sched and mb_n != sched[1]:
        R.find("WARN", "sim/MASS_BUDGET.md models %d screws, fasteners.json fits %d (the screw mass, 175 g, is from the older count)" % (mb_n, sched[1]),
               fix="re-run sim/mass_budget.py on fasteners.json when it is final", where="altaay_lab/sim/MASS_BUDGET.md")
    # ------------------------------------------------------------------ decisions and upstream
    dec = open(V.lab("DECISIONS.md")).read()
    last = max(int(x) for x in re.findall(r"^- D(\d+)\b", dec, re.M))
    for f, i, m, ln in mentions(r"\bD1 to D(\d+)\b"):
        if int(m.group(1)) != last:
            dated = re.search(r"Update 20\d\d-|print-readiness pass, DECISIONS", ln)
            R.find("WARN", "%s line %d says 'D1 to D%s', DECISIONS.md goes to D%d%s" % (
                f, i, m.group(1), last, " (dated section)" if dated else ": the work in that file did not look at D%d to D%d" % (
                    int(m.group(1)) + 1, last)),
                fix=None if dated else "%s: check D%d to D%d against it, then write 'D1 to D%d' (or date the statement)" % (
                    f, int(m.group(1)) + 1, last, last), where="altaay_lab/" + f)
    R.ev("decisions: DECISIONS.md last is D%d" % last)
    up = re.search(r"= (\d+) items, all read", open(V.lab("UPSTREAM_ISSUES.md")).read())
    for f, i, m, ln in mentions(r"\((\d+)\)|(\d+) issues and PRs"):
        val = m.group(1) or m.group(2)
        if "issue" in ln.lower() and up and val and int(val) not in (int(up.group(1)),) and int(val) > 100:
            R.find("FAIL", "%s line %d says %s upstream items, UPSTREAM_ISSUES.md has %s" % (f, i, val, up.group(1)))
    R.ev("upstream items: UPSTREAM_ISSUES.md total %s" % (up.group(1) if up else "?"))
    # ------------------------------------------------------------------ currents: WIRING.md section 4 vs netlist
    net = V.load_netlist()
    cur = {}
    for w in net["wires"]:      # the largest current on any conductor of the cable (P11: the joined 16 AWG pair)
        old = cur.get(w["cable"], (None, None, None))
        cur[w["cable"]] = tuple(max([x for x in (o, w.get(k)) if x is not None], default=None)
                                for o, k in zip(old, ("i_mean_a", "i_peak_a", "i_fall_a")))
    nc = 0
    for t in V.md_tables(V.lab("WIRING.md")):
        if t["header"][:4] != ["Run", "Mean", "Worst 100 ms", "Fall, 20 ms"]:
            continue
        for r in t["rows"]:
            cabs = re.findall(r"\b(P\d+|SP\d|D\d+|SD\d)\b", r["Run"])
            vals = [V.num(r.get(k, "")) if re.search(r"\d", r.get(k, "")) and "mA" not in r.get(k, "") else None for k in ("Mean", "Worst 100 ms", "Fall, 20 ms")]
            for c in cabs:
                if c not in cur or "D2 to" in r["Run"]:
                    continue
                for k, (a, b) in enumerate(zip(vals, cur[c])):
                    if a is not None and b is not None:
                        nc += 1
                        if abs(a - b) > 0.011:
                            R.find("FAIL", "WIRING.md section 4 %s %s: %s A, netlist %s A" % (c, ("mean", "100 ms", "fall")[k], a, b))
    R.ev("WIRING.md section 4 currents vs netlist: %d values compared" % nc)
    # ------------------------------------------------------------------ print numbers
    st = open(V.lab("STATE.md")).read()
    pp = open(V.lab("print", "PRINT_PLAN.md")).read() + open(V.lab("print", "SLICE_SUMMARY.md")).read()
    line = next((ln for ln in st.splitlines() if "Print package" in ln), "")
    nums = re.findall(r"\b(\d+\.\d) (?:h|g)\b", line)
    pool = set(re.findall(r"\b\d+\.\d\b", pp + open(V.lab("PRINT_CHECK.md")).read()))
    miss = [x for x in nums if x not in pool]
    R.ev("STATE.md print numbers (%s) found in print/PRINT_PLAN.md, SLICE_SUMMARY.md or PRINT_CHECK.md: %d of %d" % (
        ", ".join(nums), len(nums) - len(miss), len(nums)))
    for x in miss:
        R.find("FAIL", "STATE.md print number %s is not in print/PRINT_PLAN.md, print/SLICE_SUMMARY.md or PRINT_CHECK.md" % x)
    m27 = re.search(r"need (\d+) g sliced", bom["27"]["Spec"])
    if m27 and abs(int(m27.group(1)) - (1474.5 + 27.8)) > 1:
        R.find("FAIL", "BOM 27 PLA need %s g vs full print 1474.5 g + coupons 27.8 g" % m27.group(1))
    # ------------------------------------------------------------------ mass
    if mb:
        ours = re.search(r"Our build: \*\*([0-9.]+) kg\*\*", mb)
        trained = re.search(r"trained on: \*\*([0-9.]+) kg\*\*", mb)
        for f, i, m, ln in mentions(r"about ([0-9.]+) kg \(sim mass\)|([0-9.]+) kg \(sim mass\)"):
            v = float(m.group(1) or m.group(2))
            if trained and abs(v - float(trained.group(1))) > 0.01:
                R.find("FAIL", "%s line %d sim mass %s kg vs trained %s kg" % (f, i, v, trained.group(1)))
            elif ours and "2.77" not in ln:
                R.find("WARN", "%s line %d gives the robot mass as %s kg (sim mass, trained model); the build is %s kg by sim/MASS_BUDGET.md" % (
                    f, i, v, ours.group(1)),
                    fix="%s line %d: after '%s' add ' (the lab build is about %s kg by the mass budget, sim/MASS_BUDGET.md, not weighed)'"
                        % (f, i, m.group(0), ours.group(1)), where="altaay_lab/" + f)
    cat = [("blocker counts", "cleared or decided'"), ("blocker total", "total blockers"), ("test print count", "settled by the coupon"),
           ("blocker status words", "says 'B"), ("stale BOM blocker bullets", "BLOCKERS that affect"),
           ("screw count", "screws by size"), ("totals", "quotes"), ("part counts", "the viewer run finds"), ("STL count", "STL files"),
           ("currents", "WIRING.md section 4"), ("print numbers", "print number"), ("upstream count", "upstream items")]
    used = []
    for name, needle in cat:
        k = sum(1 for f in R.fails() if needle in f["text"])
        if k:
            used.append("%s %d" % (name, k))
    R.key("%d disagreements (%s); blocker table: %d rows, %d cleared or decided" % (len(R.fails()), ", ".join(used) or "none", n,
                                                                                    len(cleared)))
    R.write()


if __name__ == "__main__":
    main()
