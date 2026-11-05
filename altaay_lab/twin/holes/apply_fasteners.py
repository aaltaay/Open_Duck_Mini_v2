"""Apply D39 (track 2e) to a fasteners.json: the one more pass, the left eye diagonal, and the closed holes.
Usage: python3 apply_fasteners.py <repo root>   (phase 1: the scratch worktree only)
- F076 and its insert: LEAVE OUT (D39 screw cut), with the ear seats on body_middle_bottom_lip (twin/holes).
- left eye: F178 and F183 out, F179 and F182 back (with their 2 washers each): one bulb STL serves both eyes,
  mirrored, so both bulbs must leave the same 2 STL holes empty.
- every row whose hole is now closed gets the note; empty_holes rows that were closed get "closed": true.
Ids, order and every other field stay, so joints.json and the reports keep their references.
"""
import json, os, sys
root = sys.argv[1]
fn = os.path.join(root, "altaay_lab", "fasteners", "fasteners.json")
FJ = json.load(open(fn))
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
rep = json.load(open(os.path.join(DATA, "close_report.json")))
CUT = {"F076", "F178", "F183"}
BACK = {"F179", "F182"}
ins_of = {f["screw"]: f["id"] for f in FJ["fasteners"] if f["kind"] == "insert"}
CUT |= {ins_of[s] for s in list(CUT) if s in ins_of}
NOTE = "D39: hole closed in the printed part (twin/holes, close_holes.py); the screw comes back only with a reprint"
# per fastener: its printed holes and whether each closed (close_report.json, every instance of every STL)
holes_of = {}
for h in rep["holes"]:
    if h["stl"].endswith(("_groove", "_lip")):
        continue
    for u in h["users"]:
        holes_of.setdefault(u, []).append(h)
def hole_note(fid):
    hs = holes_of.get(fid, [])
    shut = sorted({h["stl"] for h in hs if h["decision"] == "close"})
    kept = sorted({"%s (%s)" % (h["stl"], h["why"][:70]) for h in hs if h["decision"] != "close"})
    if shut and not kept:
        return NOTE + ": " + ", ".join(shut)
    if shut:
        return "D39: hole closed in " + ", ".join(shut) + "; kept in " + "; ".join(kept)
    if kept:
        return "D39: hole kept in " + "; ".join(kept)
    return "D39: no printed hole (bought parts only)"
n = dict(cut=0, back=0, noted=0, empty_closed=0)
for f in FJ["fasteners"]:
    if f["id"] in CUT:
        f["status"] = "LEAVE OUT (D39 screw cut)"; f["leave_out"] = True
        f["notes"] = [x for x in f.get("notes", []) if not x.startswith("D38")] + ["D39: left out by the V1 holes job (twin/holes)", hole_note(f["id"])]
        n["cut"] += 1
    elif f["id"] in BACK:
        f.pop("leave_out", None); f["status"] = None
        f["notes"] = [x for x in f.get("notes", []) if not x.startswith("D38")] + ["D39: fitted again (left eye keeps this diagonal so both bulbs, one STL, leave the same 2 holes empty)"]
        n["back"] += 1
    elif str(f.get("status") or "").startswith(("LEAVE OUT", "NOT FITTED")):
        f["notes"] = [x.replace("; hole kept", "") for x in f.get("notes", [])] + [hole_note(f["id"])]
        n["noted"] += 1
# empty_holes: match each entry to the current site by origin and axis (as inventory.py does), closed when every printed row closed
raw = json.load(open(os.path.join(DATA, "sites_raw.json")))
dec = {}
for h in rep["holes"]:
    if not h["stl"].endswith(("_groove", "_lip")):
        dec.setdefault(h["site"], set()).add(h["decision"])
for e in FJ["empty_holes"]:
    m = [r["site"] for r in raw if abs(sum(a * b for a, b in zip(r["ax"], e["axis"]))) > 0.995 and sum((a - b) ** 2 for a, b in zip(r["o"], e["at"])) ** 0.5 < 0.2]
    if m and dec.get(m[0]) == {"close"}:
        e["closed"] = True; e["why"] = "CLOSED (D39): " + e["why"]; n["empty_closed"] += 1
json.dump(FJ, open(fn, "w"), separators=(",", ":"))
F = FJ["fasteners"]
fit = lambda x: x.get("status") not in ("NOT FITTED", "LEAVE OUT (D18)") and not x.get("leave_out")
print(n, "screws fitted", sum(1 for x in F if x["kind"] == "screw" and fit(x)), "inserts fitted", sum(1 for x in F if x["kind"] == "insert" and fit(x)),
      "washers", sum(2 for x in F if x["kind"] == "screw" and "washers" in x["spec"] and fit(x)))
