"""Shared helpers for the altaay_lab/verify checks (read only: no check writes inside the repo except
run_all.sh, which writes altaay_lab/VERIFICATION.md through report.py).

Every check is a small script that:
  1. reads the lab files (never edits them; scripts it must run are copied to the output folder first),
  2. records evidence lines (numbers) and findings (FAIL, WARN, INFO, each with a proposed fix),
  3. writes <out>/<check id>.json, which report.py turns into the matrix in VERIFICATION.md.

Status rules (the same for every check):
  FAIL    at least one FAIL finding
  PASS    no FAIL finding (WARN findings are listed but do not fail the check)
  NOT RUN the check could not run (missing input, missing tool, skipped); the reason is the evidence
Paths: ODM_RUNTIME (Open_Duck_Mini_Runtime at 376de65) and ODM_PLAYGROUND (Open_Duck_Playground at b9be205)
default to /home/user/upstream/... as in the lab sims.
"""
import ast
import hashlib
import json
import os
import re
import sys
import time
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
REPO = os.path.dirname(LAB)
RUNTIME = os.environ.get("ODM_RUNTIME", "/home/user/upstream/Open_Duck_Mini_Runtime")
PLAYGROUND = os.environ.get("ODM_PLAYGROUND", "/home/user/upstream/Open_Duck_Playground")


def lab(*p):
    return os.path.join(LAB, *p)


def out_dir():
    """Output folder for results (outside the repo). Set by run_all.sh through VERIFY_OUT."""
    d = os.environ.get("VERIFY_OUT") or os.path.join(os.environ.get("TMPDIR", "/tmp"), "odm_verify")
    d = os.path.abspath(d)
    if os.path.commonpath([d, REPO]) == REPO:
        sys.exit("VERIFY_OUT must be outside the repo: " + d)
    os.makedirs(d, exist_ok=True)
    return d


def sha(path, n=10):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()[:n]
    except OSError:
        return None


def mtime_utc(path):
    try:
        return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(os.path.getmtime(path)))
    except OSError:
        return None


class Result:
    """One row of the matrix."""

    def __init__(self, cid, title, command, covers, not_covers):
        self.d = OrderedDict(id=cid, title=title, command=command, status=None, reason="", evidence=[],
                             findings=[], covers=covers, not_covers=not_covers, inputs={}, started=time.time())

    def ev(self, text):
        self.d["evidence"].append(str(text))

    def key(self, text):
        """the short line of numbers the matrix shows"""
        self.d["key"] = str(text)

    def find(self, sev, text, fix=None, where=None):
        assert sev in ("FAIL", "WARN", "INFO")
        self.d["findings"].append(dict(sev=sev, text=str(text), fix=fix, where=where))

    def inp(self, *paths):
        for p in paths:
            rel = os.path.relpath(p, REPO) if os.path.isabs(p) else p
            self.d["inputs"][rel] = dict(sha=sha(p), mtime=mtime_utc(p))

    def not_run(self, reason):
        self.d["status"] = "NOT RUN"
        self.d["reason"] = reason

    def fails(self):
        return [f for f in self.d["findings"] if f["sev"] == "FAIL"]

    def write(self):
        if self.d["status"] is None:
            self.d["status"] = "FAIL" if self.fails() else "PASS"
        self.d["seconds"] = round(time.time() - self.d.pop("started"), 1)
        self.d["finished_utc"] = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
        path = os.path.join(out_dir(), self.d["id"] + ".json")
        json.dump(self.d, open(path, "w"), indent=1)
        n = {s: sum(1 for f in self.d["findings"] if f["sev"] == s) for s in ("FAIL", "WARN", "INFO")}
        print("%s %s: %s (%d FAIL, %d WARN, %d INFO)%s" % (self.d["id"], self.d["title"], self.d["status"], n["FAIL"],
                                                          n["WARN"], n["INFO"],
                                                          (" reason: " + self.d["reason"]) if self.d["reason"] else ""))
        for e in self.d["evidence"]:
            print("   ev:", e)
        for f in self.d["findings"]:
            if f["sev"] != "INFO":
                print("   %s: %s" % (f["sev"], f["text"]))
        return self.d["status"]


# ------------------------------------------------------------------------------------------ markdown
def md_tables(path):
    """Every pipe table in a markdown file: [{section, header, rows: [dict]}]. section = last heading."""
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
                body = lines[i].strip()
                body = body[1:] if body.startswith("|") else body
                body = body[:-1] if body.endswith("|") else body
                cells = [c.strip() for c in body.split("|")]
                if len(cells) != len(header):          # a cell holds a '|': fall back to the ' | ' split
                    cells = [c.strip() for c in lines[i].strip().strip("|").split(" | ")]
                rows.append(dict(zip(header, cells)))
                i += 1
            out.append(dict(section=section, header=header, rows=rows))
            continue
        i += 1
    return out


def md_section(path, heading_re):
    """Text of the first section whose heading matches heading_re, up to the next heading of the same or higher level."""
    lines = open(path, encoding="utf-8").read().splitlines()
    start, level = None, None
    for i, ln in enumerate(lines):
        m = re.match(r"^(#+)\s+(.*)", ln)
        if m and start is None and re.search(heading_re, m.group(2)):
            start, level = i, len(m.group(1))
            continue
        if m and start is not None and len(m.group(1)) <= level:
            return "\n".join(lines[start:i])
    return "\n".join(lines[start:]) if start is not None else ""


def bom_lines(path=None):
    """BOM.md purchase lines by line id (column '#'), every column plus 'section'."""
    path = path or lab("BOM.md")
    out = OrderedDict()
    for t in md_tables(path):
        if t["header"][:2] != ["#", "Item"] or "Need" not in t["header"]:
            continue
        for r in t["rows"]:
            r = dict(r)
            r["section"] = t["section"]
            out[r["#"]] = r
    return out


def num(s):
    m = re.search(r"-?[0-9]+(?:\.[0-9]+)?", str(s if s is not None else ""))
    return float(m.group(0)) if m else None


def load_netlist(path=None):
    import yaml
    return yaml.safe_load(open(path or lab("wiring", "netlist.yaml"), encoding="utf-8"))


def erc_tables():
    """AMP (A per AWG), OHM_M and KIT_AWG read from audit/erc.py by parsing it (erc.py runs on import)."""
    src = open(lab("audit", "erc.py"), encoding="utf-8").read()
    vals = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in ("AMP", "OHM_M", "KIT_AWG"):
                vals[node.targets[0].id] = ast.literal_eval(node.value)
    return vals


def awg_of(g, kit_awg=26):
    """Same rule as audit/erc.py awg_of: '22 AWG' -> 22, 'kit cable' -> kit_awg, else None."""
    if g is None:
        return None
    m = re.search(r"(\d+)\s*AWG", str(g))
    if m:
        return int(m.group(1))
    if "kit" in str(g).lower():
        return kit_awg
    return None


def py_assign(path, name):
    """Literal value assigned to a module-level or attribute name (self.<name> or <name>) in a Python file."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if (isinstance(t, ast.Name) and t.id == name) or (isinstance(t, ast.Attribute) and t.attr == name):
                try:
                    return ast.literal_eval(node.value)
                except ValueError:
                    pass
    raise KeyError("%s not found in %s" % (name, path))


def py_assign_attr(path, name):
    """Value of NAME = board.Dxx in a Runtime file -> 'Dxx' (or 'SCL'/'SDA')."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id == name and isinstance(node.value, ast.Attribute):
                return node.value.attr
    raise KeyError("%s not found in %s" % (name, path))


# Raspberry Pi 40-pin header: BCM GPIO -> physical pin (pinout.xyz; the same on every 40-pin Pi, Zero 2 W included)
BCM_TO_PIN = {2: 3, 3: 5, 4: 7, 17: 11, 27: 13, 22: 15, 10: 19, 9: 21, 11: 23, 0: 27, 5: 29, 6: 31, 13: 33, 19: 35,
              26: 37, 14: 8, 15: 10, 18: 12, 23: 16, 24: 18, 25: 22, 8: 24, 7: 26, 1: 28, 12: 32, 16: 36, 20: 38, 21: 40}
PWR_PINS = {"3V3": {1, 17}, "5V": {2, 4}, "GND": {6, 9, 14, 20, 25, 30, 34, 39}}
