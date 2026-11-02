"""Electrical rule check (ERC) on altaay_lab/wiring/netlist.yaml.

Checks (each finding is ERROR, WARN or INFO):
 1. references: unique component ids and pins; every wire end names an existing COMP.PIN
 2. pin use: "nc" pins have no wire; every other pin has a wire or an internal short/mated link
 3. shorts: union-find over wires plus internal short/mated links; each connected group must carry one net only
 4. domains: wire net domain vs the domains of both end pins; inputs must not see more than their domain maximum
 5. ampacity: wire current (walking mean, worst 100 ms, fall 20 ms) vs the chassis-wiring limit of its gauge
 6. crimps: Molex 08-70-1040 terminals take 22 to 28 AWG only
 7. connector match: a pin in a 5264-type socket group needs a 5264 plug or a 50-37-5033 housing on the wire end
 8. voltage drop per wire at the worst 100 ms current
Writes audit/ERC_REPORT.md and audit/continuity_checklist.csv (the beep list for TEST_PLAN.md section 2).
Usage: python3 audit/erc.py
"""
import os, re, csv, collections
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
NET = os.environ.get("ODM_NETLIST", os.path.join(HERE, "..", "wiring", "netlist.yaml"))
REPORT = os.environ.get("ODM_ERC_REPORT", os.path.join(HERE, "ERC_REPORT.md"))
CHECK = os.environ.get("ODM_ERC_CHECK", os.path.join(HERE, "continuity_checklist.csv"))

# chassis wiring ampacity (single conductor in air), PowerStream wire gauge table, powerstream.com/Wire_Size.htm
AMP = {16: 22.0, 18: 16.0, 20: 11.0, 22: 7.0, 24: 3.5, 26: 2.2, 28: 1.4}
OHM_M = {16: 13.17e-3, 18: 20.95e-3, 20: 33.31e-3, 22: 52.96e-3, 24: 84.22e-3, 26: 133.9e-3, 28: 212.9e-3}
KIT_AWG = 26   # STS3215 kit cable gauge is not published; smallest plausible (same as sim/power_path_sim.py)

d = yaml.safe_load(open(NET))
F = []   # findings: (severity, check, text)
def add(sev, chk, txt): F.append((sev, chk, txt))

comps = {}
for c in d["components"]:
    if c["id"] in comps: add("ERROR", "references", f"duplicate component id {c['id']}")
    comps[c["id"]] = c
pins = {}
for c in comps.values():
    seen = set()
    for p in c.get("pins") or []:
        if p["pin"] in seen: add("ERROR", "references", f"{c['id']}: duplicate pin {p['pin']}")
        seen.add(p["pin"]); pins[f"{c['id']}.{p['pin']}"] = (c, p)
nets, domains = d.get("nets", {}), d.get("domains", {})

def split(ref):
    cid, _, pin = ref.partition(".")
    return cid, pin

wires = d.get("wires", [])
active_cables = {cb["id"] for cb in d.get("cables", []) if cb.get("status", "active") == "active"}
removed_cables = {cb["id"] for cb in d.get("cables", []) if cb.get("status") == "removed"}
used = collections.Counter()
for w in wires:
    if w.get("cable") in removed_cables:
        add("ERROR", "references", f"wire on removed cable {w['cable']}: {w['from']} -> {w['to']}")
    for end in ("from", "to"):
        ref = w[end]
        if ref not in pins: add("ERROR", "references", f"cable {w.get('cable')}: {end} {ref} is not a pin in the netlist")
        else: used[ref] += 1
    if w.get("net") not in nets: add("ERROR", "references", f"cable {w.get('cable')}: net {w.get('net')} is not declared")

# 2. pin use
internal_linked = set()
for c in comps.values():
    for it in c.get("internal") or []:
        if it.get("kind") in ("short", "mated"):
            internal_linked.add(f"{c['id']}.{it['a']}"); internal_linked.add(f"{c['id']}.{it['b']}")
for ref, (c, p) in pins.items():
    if p.get("dir") == "nc":
        if used[ref]: add("ERROR", "pin use", f"{ref} ({p.get('name')}) is marked nc but has {used[ref]} wire(s)")
    elif not used[ref] and ref not in internal_linked:
        add("WARN", "pin use", f"{ref} ({p.get('name')}, {p.get('dir')}) has no wire; mark it nc if that is intended")

# 3. shorts between nets (union-find)
parent = {}
def find(a):
    parent.setdefault(a, a)
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a
def union(a, b): parent[find(a)] = find(b)
for w in wires:
    if w["from"] in pins and w["to"] in pins: union(w["from"], w["to"])
for c in comps.values():
    for it in c.get("internal") or []:
        if it.get("kind") in ("short", "mated"): union(f"{c['id']}.{it['a']}", f"{c['id']}.{it['b']}")
group_nets = collections.defaultdict(set)
for w in wires:
    if w["from"] in pins: group_nets[find(w["from"])].add(w.get("net"))
for g, ns in group_nets.items():
    if len(ns) > 1:
        members = sorted(r for r in parent if find(r) == g)
        add("ERROR", "shorts", f"nets {sorted(ns)} are joined (members: {', '.join(members[:12])}{' ...' if len(members) > 12 else ''})")

# 4. domains
def dom(name): return domains.get(name, {})
for w in wires:
    net = nets.get(w.get("net"), {}); nd = net.get("domain")
    for end in ("from", "to"):
        if w[end] not in pins: continue
        c, p = pins[w[end]]; pd = p.get("domain")
        if pd != nd:
            vmax_p, vmax_n = dom(pd).get("v_max"), dom(nd).get("v_max")
            sev = "INFO"
            if p.get("dir") in ("in", "bidir") and vmax_p is not None and vmax_n is not None and vmax_n > vmax_p + 0.1:
                sev = "ERROR"
            add(sev, "domains", f"cable {w.get('cable')}: {w[end]} pin domain {pd} on net {w.get('net')} (domain {nd})")

# schema keys: anything outside the documented schema is a sign of a YAML parse slip (for example an unquoted comma)
WIRE_KEYS = {"cable", "branch", "from", "to", "net", "gauge", "color", "cut_mm", "i_mean_a", "i_peak_a", "i_fall_a", "ends", "source", "note"}
PIN_KEYS = {"pin", "label", "name", "domain", "group", "dir", "source", "note"}
COMP_KEYS = {"id", "ref", "part", "kind", "region", "ratings", "groups", "pins", "internal", "source", "note"}
for w in wires:
    extra = set(w) - WIRE_KEYS
    if extra: add("WARN", "schema", f"cable {w.get('cable')} {w.get('from')}: unexpected keys {sorted(extra)}")
for c in comps.values():
    extra = set(c) - COMP_KEYS
    if extra: add("WARN", "schema", f"component {c['id']}: unexpected keys {sorted(extra)}")
    for p in c.get("pins") or []:
        extra = set(p) - PIN_KEYS
        if extra: add("WARN", "schema", f"pin {c['id']}.{p.get('pin')}: unexpected keys {sorted(extra)}")

# 5 to 8 per wire
drops = []
def awg_of(g):
    if g is None: return None
    m = re.search(r"(\d+)\s*AWG", str(g))
    if m: return int(m.group(1))
    if "kit" in str(g).lower(): return KIT_AWG
    return None
for w in wires:
    a = awg_of(w.get("gauge")); cab = w.get("cable")
    if a is None:
        if w.get("cut_mm"): add("INFO", "ampacity", f"cable {cab}: gauge '{w.get('gauge')}' not parsed ({w['from']} -> {w['to']})")
        continue
    lim = AMP.get(a)
    for key, sev in (("i_mean_a", "ERROR"), ("i_peak_a", "WARN")):
        i = w.get(key)
        if i is not None and lim is not None and i > lim:
            add(sev, "ampacity", f"cable {cab} {w['from']} -> {w['to']}: {key} {i} A over the {a} AWG chassis limit {lim} A")
    i_fall = w.get("i_fall_a")
    if i_fall is not None and lim is not None and i_fall > 2 * lim:
        add("WARN", "ampacity", f"cable {cab}: fall current {i_fall} A for about 20 ms is over 2 x the {a} AWG limit")
    if "kit" in str(w.get("gauge")).lower() and w.get("i_peak_a"):
        add("INFO", "ampacity", f"cable {cab}: kit cable gauge assumed {KIT_AWG} AWG")
    for e in w.get("ends") or []:
        if "08-70-1040" in str(e) and not (22 <= a <= 28):
            add("ERROR", "crimps", f"cable {cab}: {a} AWG wire on a Molex 08-70-1040 terminal (22 to 28 AWG only), end '{e}'")
    if w.get("cut_mm") and w.get("i_peak_a"):
        r = OHM_M[a] * w["cut_mm"] / 1000.0
        drops.append((round(r * w["i_peak_a"] * 1000, 1), cab, w["from"], w["to"], a, w["cut_mm"], w["i_peak_a"]))
# 7. connector match
for w in wires:
    for end, e in zip(("from", "to"), w.get("ends") or []):
        ref = w[end]
        if ref not in pins: continue
        c, p = pins[ref]; grp = (c.get("groups") or {}).get(p.get("group"), {})
        conn = str(grp.get("connector", ""))
        if "5264" in conn and not any(k in str(e) for k in ("5264", "50-37-5033", "servo", "kit")):
            add("WARN", "connector match", f"cable {w.get('cable')}: {ref} sits in a {conn} but the wire end is '{e}'")
        if ("2.54" in conn or "0.1 in" in conn) and "5264" in str(e):
            add("ERROR", "connector match", f"cable {w.get('cable')}: 2.5 mm 5264 plug on a 2.54 mm pin group at {ref}")

# continuity checklist
with open(CHECK, "w", newline="") as fh:
    cw = csv.writer(fh)
    cw.writerow(["cable", "from", "to", "net", "gauge", "cut_mm", "expect", "check_no_short_to"])
    for w in wires:
        if w["from"] not in pins or w["to"] not in pins: continue
        c, p = pins[w["from"]]
        sibl = [f"{c['id']}.{q['pin']}" for q in (c.get("pins") or []) if q.get("group") == p.get("group") and q["pin"] != p["pin"]]
        cw.writerow([w.get("cable"), w["from"], w["to"], w.get("net"), w.get("gauge"), w.get("cut_mm"), "under 1 ohm, read in ohms (TEST_PLAN.md section 2)", " ".join(sibl[:6])])

sev_n = collections.Counter(s for s, _, _ in F)
by_chk = collections.defaultdict(list)
for s, chk, t in F: by_chk[chk].append((s, t))
lines = ["# ERC report (generated by audit/erc.py from wiring/netlist.yaml)", "",
         f"Components {len(comps)}, pins {len(pins)}, cables {len(d.get('cables', []))} ({len(removed_cables)} removed), wires {len(wires)}.",
         f"Findings: {sev_n.get('ERROR', 0)} ERROR, {sev_n.get('WARN', 0)} WARN, {sev_n.get('INFO', 0)} INFO.", "",
         "Ampacity limits: chassis wiring, PowerStream wire gauge table (powerstream.com/Wire_Size.htm). Kit servo cables assumed 26 AWG (gauge not published).", ""]
for chk in ("references", "schema", "pin use", "shorts", "domains", "ampacity", "crimps", "connector match"):
    rows = by_chk.get(chk, [])
    lines.append(f"## {chk} ({len(rows)})")
    if not rows: lines.append("No findings.")
    for s, t in sorted(rows, key=lambda x: {"ERROR": 0, "WARN": 1, "INFO": 2}[x[0]]):
        lines.append(f"- {s}: {t}")
    lines.append("")
lines += ["## Largest voltage drops at the worst 100 ms current", "", "| mV | cable | from | to | AWG | cut mm | A |", "|---|---|---|---|---|---|---|"]
for row in sorted(drops, reverse=True)[:15]:
    lines.append("| " + " | ".join(str(x) for x in row) + " |")
lines += ["", f"Continuity checklist for TEST_PLAN.md section 2: audit/{os.path.basename(CHECK)} ({len(wires)} rows)."]
open(REPORT, "w").write("\n".join(lines) + "\n")
print("\n".join(lines[:6]))
for s, chk, t in F:
    if s != "INFO": print(f"{s} [{chk}] {t}")
