"""E1: run the existing electrical rule check (audit/erc.py) without touching its committed outputs, check that the
committed ERC_REPORT.md and continuity_checklist.csv are current, and mutation-test the checker on netlist copies.

Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/e1_erc.py
erc.py is run as is; ODM_NETLIST, ODM_ERC_REPORT and ODM_ERC_CHECK point it at copies in the output folder.
"""
import copy
import os
import re
import subprocess
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

R = V.Result("E1", "Electrical rule check of the netlist (audit/erc.py) plus mutation test",
             "VERIFY_OUT=<out> python3 altaay_lab/verify/e1_erc.py",
             "References, pin use, shorts between nets, voltage domains of 'in', 'bidir' and 'pwr_in' pins, ampacity of wires that "
             "carry a current in the netlist, Molex 08-70-1040 crimp gauge, 5264 connector match; committed report is current; "
             "10 injected faults",
             "Wires with no current in the netlist (see C7); anything not written in netlist.yaml")
OUT = os.path.join(V.out_dir(), "e1_erc")
os.makedirs(OUT, exist_ok=True)
NET = V.lab("wiring", "netlist.yaml")
R.inp(NET, V.lab("audit", "erc.py"), V.lab("audit", "ERC_REPORT.md"), V.lab("audit", "continuity_checklist.csv"))


def run_erc(netlist_path, tag):
    os.makedirs(os.path.join(OUT, tag), exist_ok=True)   # same file names as the committed ones (the report names the csv)
    rep, chk = os.path.join(OUT, tag, "ERC_REPORT.md"), os.path.join(OUT, tag, "continuity_checklist.csv")
    env = dict(os.environ, ODM_NETLIST=netlist_path, ODM_ERC_REPORT=rep, ODM_ERC_CHECK=chk)
    p = subprocess.run([sys.executable, V.lab("audit", "erc.py")], env=env, capture_output=True, text=True, timeout=300)
    txt = open(rep).read() if os.path.exists(rep) else ""
    counts = {}
    for m in re.finditer(r"^## (.+?) \((\d+)\)$", txt, re.M):
        counts[m.group(1)] = int(m.group(2))
    sev = {}
    for chk_name in counts:
        sec = re.search(r"^## %s \(\d+\)\n(.*?)(?=^## |\Z)" % re.escape(chk_name), txt, re.M | re.S)
        lines = sec.group(1) if sec else ""
        sev[chk_name] = {s: len(re.findall(r"^- %s:" % s, lines, re.M)) for s in ("ERROR", "WARN", "INFO")}
    tot = re.search(r"Findings: (\d+) ERROR, (\d+) WARN, (\d+) INFO", txt)
    return p.returncode, (tuple(int(x) for x in tot.groups()) if tot else None), sev, rep, chk, p.stdout + p.stderr


rc, tot, sev, rep, chk, log = run_erc(NET, "real")
if tot is None:
    R.not_run("erc.py did not write a report: " + log[-400:])
    R.write()
    sys.exit(0)
R.ev("erc.py on wiring/netlist.yaml: %d ERROR, %d WARN, %d INFO (exit %d)" % (tot + (rc,)))
head = open(rep).read().splitlines()[2]
R.ev(head)
if tot[0]:
    R.find("FAIL", "erc.py reports %d ERROR on the real netlist" % tot[0], fix="fix the netlist rows named in the ERC report")
if tot[1]:
    R.find("WARN", "erc.py reports %d WARN on the real netlist" % tot[1])
same_rep = open(rep).read() == open(V.lab("audit", "ERC_REPORT.md")).read()
same_chk = open(chk).read() == open(V.lab("audit", "continuity_checklist.csv")).read()
R.ev("committed audit/ERC_REPORT.md current: %s; audit/continuity_checklist.csv current: %s" % (same_rep, same_chk))
if not same_rep or not same_chk:
    R.find("FAIL", "committed ERC outputs are stale against netlist.yaml",
           fix="re-run python3 altaay_lab/audit/erc.py and commit ERC_REPORT.md and continuity_checklist.csv",
           where="altaay_lab/audit/")

# ---------------------------------------------------------------------------------------------- mutations
base = yaml.safe_load(open(NET))


def wire(d, cable, frm=None, to=None):
    for w in d["wires"]:
        if w["cable"] == cable and (frm is None or w["from"] == frm) and (to is None or w["to"] == to):
            return w
    raise KeyError((cable, frm, to))


def m_short(d):      # kit cable S2 V conductor landed on the DATA pin of ID 21
    wire(d, "S2", to="SV21.BUS2.V")["to"] = "SV21.BUS2.D"


def m_crimp(d):      # 16 AWG wire in a Mini-SPOX 22 to 28 AWG terminal
    wire(d, "SP1", to="SV20.BUS2.V")["gauge"] = "16 AWG"


def m_nc(d):         # power wired to the adapter V position that D15 leaves empty
    d["wires"].append({"cable": "SP1", "from": "SPV.S", "to": "U2.H3.V", "net": "SERVO_7V2", "gauge": "22 AWG",
                       "cut_mm": 100, "ends": ["splice", "Molex 50-37-5033 housing + 08-70-1040 crimp"]})


def m_ref(d):        # typo in a pin name
    wire(d, "S3", to="SV22.BUS2.G")["to"] = "SV22.BUS3.G"


def m_amp(d):        # mean current above the 20 AWG chassis limit
    wire(d, "P13", frm="VSW.S")["i_mean_a"] = 12.0


def m_dom_pwr(d):    # pack voltage on the BNO055 VIN (3.3 V part, dir pwr_in)
    w = wire(d, "D2", to="BNO.VIN")
    w["from"], w["net"] = "VSW.S", "VSW"


def m_dom_in(d):     # pack voltage on a GPIO input (GPIO22, dir in)
    w = wire(d, "D3", frm="PI.15", to="FSL1.NO")
    w["from"], w["net"] = "VSW.S", "VSW"
    wire(d, "D3", frm="RFL.2")["net"] = "VSW"
    wire(d, "D3", frm="FSL1.NO")["net"] = "VSW"


def m_conn(d):       # 2.5 mm 5264 plug on the 2.54 mm Pi header
    wire(d, "D10", to="AMP.LRC")["ends"] = ["5264 plug", "solder"]


def m_schema(d):     # misspelt key (a YAML slip)
    wire(d, "P12", frm="U3.VOUT")["guage"] = "20 AWG"


def m_removed(d):    # a wire left on the removed cable S14
    d["wires"].append({"cable": "S14", "from": "SV24.BUS1.D", "to": "SV30.BUS2.D", "net": "BUS_DATA", "gauge": "22 AWG",
                       "cut_mm": 490, "ends": ["Molex 50-37-5033 housing + 08-70-1040 crimp", "Molex 50-37-5033 housing + 08-70-1040 crimp"]})


MUT = [  # id, what, function, (check section, severity expected)
    ("M1", "S2 V conductor moved to the ID 21 DATA pin (short SERVO_7V2 to BUS_DATA)", m_short, ("shorts", "ERROR")),
    ("M2", "SP1 V wire made 16 AWG on an 08-70-1040 terminal", m_crimp, ("crimps", "ERROR")),
    ("M3", "wire added to the empty adapter H3 V position (nc pin, D15)", m_nc, ("pin use", "ERROR")),
    ("M4", "pin name typo SV22.BUS3.G", m_ref, ("references", "ERROR")),
    ("M5", "P13 mean current 12 A on 20 AWG (limit 11 A)", m_amp, ("ampacity", "ERROR")),
    ("M6", "switched pack (8.4 V) on BNO055 VIN (3.3 V, dir pwr_in)", m_dom_pwr, ("domains", "ERROR")),
    ("M7", "switched pack (8.4 V) on GPIO22 (dir in)", m_dom_in, ("domains", "ERROR")),
    ("M8", "5264 plug on a 2.54 mm header pin group", m_conn, ("connector match", "ERROR")),
    ("M9", "misspelt wire key 'guage'", m_schema, ("schema", "WARN")),
    ("M10", "wire left on removed cable S14", m_removed, ("references", "ERROR")),
]
caught = 0
missed = []
for mid, what, fn, (sec, want) in MUT:
    d = copy.deepcopy(base)
    fn(d)
    p = os.path.join(OUT, "netlist_%s.yaml" % mid)
    yaml.safe_dump(d, open(p, "w"), sort_keys=False)
    _, t2, s2, _, _, lg = run_erc(p, mid)
    got = (s2.get(sec) or {}).get(want, 0)
    base_n = (sev.get(sec) or {}).get(want, 0)
    ok = t2 is not None and got > base_n
    caught += ok
    if not ok:
        missed.append(what)
    R.find("INFO" if ok else "WARN", "%s %s: %s (expected %s in '%s'; got %s)" % (
        mid, "caught" if ok else "NOT caught", what, want, sec, s2.get(sec)),
        fix=None if ok else ("audit/erc.py check 4: treat pwr_in like in and bidir, i.e. "
                             "`if p.get(\"dir\") in (\"in\", \"bidir\", \"pwr_in\") and ...`" if mid == "M6" else
                             "extend audit/erc.py so it reports this fault"),
        where="altaay_lab/audit/erc.py" if not ok else None)
R.ev("mutation test: %d of %d injected faults caught" % (caught, len(MUT)))
R.key("%d ERROR, %d WARN on %d components and %d wires; committed report and beep list current: %s; injected faults caught: "
      "%d of %d%s" % (tot[0], tot[1], len(base.get("components") or []), len(base.get("wires") or []), same_rep and same_chk, caught,
                      len(MUT), " (missed: %s)" % "; ".join(missed) if missed else ""))

# extended domain rule on the real netlist (erc.py checks pwr_in pins since 2026-11-02; kept as an independent check)
nets, domains = base["nets"], base["domains"]
pins = {"%s.%s" % (c["id"], p["pin"]): p for c in base["components"] for p in (c.get("pins") or [])}
bad = []
for w in base["wires"]:
    nd = (nets.get(w.get("net")) or {}).get("domain")
    for end in ("from", "to"):
        p = pins.get(w[end])
        if not p or p.get("dir") != "pwr_in":
            continue
        vp, vn = (domains.get(p.get("domain")) or {}).get("v_max"), (domains.get(nd) or {}).get("v_max")
        if vp is not None and vn is not None and vn > vp + 0.1:
            bad.append("%s (%s, max %s V) on net %s (max %s V)" % (w[end], p.get("domain"), vp, w.get("net"), vn))
n_pwr_in = sum(1 for w in base["wires"] for e in ("from", "to") if (pins.get(w[e]) or {}).get("dir") == "pwr_in")
R.ev("extended domain rule (pwr_in pins, independent of erc.py): %d wire ends on pwr_in pins, %d over their domain" % (n_pwr_in, len(bad)))
for b in bad:
    R.find("FAIL", "power input above its domain: " + b, fix="check the part rating; fix the net or the pin domain")
R.write()
