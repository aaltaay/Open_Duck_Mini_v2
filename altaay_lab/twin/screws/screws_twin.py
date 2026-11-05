"""Screw twin: classify every fastener, find the safe minimum per joint, pick the screws that stay,
and time the build before and after (calc only, CAD check only).

Read only: fasteners/fasteners.json, twin/structure/STRUCTURE_TWIN.md (tables 5 and 3.2), sim/MASS_BUDGET.md,
data/geom_joints.json (geom_joints.py), data/lips.json (mesh_designs.py, optional).
Writes data/classification.csv, data/joints.json, data/joints.csv, data/assembly_steps.csv, data/summary.json,
data/phase2_fasteners.json. Light (under 300 MB).

Rules (lab margin, STRUCTURE_TWIN.md section 3): walking and push SF >= 2.0; falls SF >= 1.2.
- Joints in the servo chain (horn screws, servo case mounts) use STRUCTURE_TWIN.md table 5 as it stands. A group
  that is at or under a margin today (walk, push, fall soft or fall mid) needs more, not fewer: it keeps all.
- Other structural joints (table 3.2 rows, the leg segment stack, the sole, the trunk frame) keep all: either a
  margin is already short, or the joint is not modelled (BLOCKER for any cut).
- Joints that hold a cover, a shell or a board: F1 (no separation in a fall) with the most conservative split, one
  screw takes the whole inertial pull of the part and what rides on it at the worst fall acceleration; capacity is
  the smaller of head pull-through (plug shear pi dk t tau) and insert pull-out or thread strip. Then the count is
  set by geometry: a stiff board or bracket on 4 seats keeps the 2 diagonal screws (it rests on the other 2 seats,
  so it cannot rock); a thin plate, lid or shell keeps 3 (a plane needs 3 points) chosen as the largest triangle
  round its centre of mass. F2 (bearing, crack but no separation) is reported for the shells with the upper bound
  that the whole trunk contact force goes through one shell joint in shear.
"""
import csv, itertools, json, math, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(HERE, "data")
G = 9.81

SRC = {
    "ST": "[L] twin/structure/STRUCTURE_TWIN.md",
    "MB": "[L] sim/MASS_BUDGET.md",
    "FJ": "[L] fasteners/fasteners.json",
    "GJ": "[L] twin/screws/data/geom_joints.json (CAD check only)",
    "dfma": "[I] https://dfma.com/resources/assembly-cost-estimating.asp (search text: threaded screw 8 to 12 s "
            "'align, drive, verify'; snap-fit 2 to 4 s; press-fit 2 to 4 s)",
}
# cited inputs ------------------------------------------------------------------------------------------
ACC_G = {"trunk": {"walk": 3.0, "soft": 45.0, "mid": 128.0}, "head": {"walk": 3.0, "soft": 71.0, "mid": 196.0}}
ACC_SRC = SRC["ST"] + " section 3.2: walking 1 to 3 g; worst of 10 falls: soft 71 g head, 45 g trunk; mid 196 g head, 128 g trunk"
SHELL_HIT_N = {"soft": 900.0, "mid": 2800.0}
SHELL_HIT_SRC = SRC["ST"] + " answer: a printed wall hit in its middle (soft) sees 400 to 900 N, an edge on a hard floor (mid) 1300 to 2800 N"
PLA_X, TAU_LO, TAU_HI = 47.1, 12.7, 27.2
PLA_SRC = SRC["ST"] + " section 2.2 and 3: X 47.1 MPa (Overture PLA TDS v5.1); shear 12.7 to 27.2 MPa (0.577 x 22 or 47.1)"
INSERT_PULL, INSERT_SIDE = 1354.0, 618.0
INSERT_SRC = SRC["ST"] + " section 3: pull-out 1354 to 1552 N (Eng. Proc. 157(1):40, 2026), sideways 618 to 1235 N (ASSUMPTION range there)"
DK = {"M3": 5.5, "M2.5": 4.5}
DK_SRC = "[I] DIN 912 table via fasteners.json meta sources din912 (dk M2.5 4.50, M3 5.50)"
T_SCREW, T_SNAP = (8.0, 10.0, 12.0), (2.0, 3.0, 4.0)


def pull_through(size, t):
    return math.pi * DK[size] * t * TAU_LO


def parse_table5():
    rows = {}
    for line in open(os.path.join(LAB, "twin", "structure", "STRUCTURE_TWIN.md")):
        m = re.match(r"^\| ((?:left|right|neck|head)_\w+ (?:drive horn|idle horn|servo case screws)) \| (\d+) \|"
                     r"[^|]*\| ([\d.]+) \| (\d+) \| [\d.]+ / ([\d.]+) \| [\d.]+ / ([\d.]+) \| [\d.]+ / ([\d.]+) \| [\d.]+ / ([\d.]+) \|", line)
        if m:
            rows[m.group(1)] = dict(n=int(m.group(2)), t=float(m.group(3)), cap=float(m.group(4)),
                                    walk=float(m.group(5)), push=float(m.group(6)), soft=float(m.group(7)), mid=float(m.group(8)))
    return rows


def parse_masses():
    mass = {}
    for line in open(os.path.join(LAB, "sim", "MASS_BUDGET.md")):
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) >= 6 and re.match(r"^[\d.]+$", c[4] or "x") and c[1] in ("printed", "electronics", "lab_added", "mechanical"):
            mass.setdefault(c[0], float(c[4]))
    return mass


def area_of(x):
    p, i, g = x["part"], x["into"], x["group"]
    if p == "body_front":
        return "body front"
    if p in ("body_back", "battery_pack_lid", "usb_c_charger"):
        return "back"
    if g == "head" or i == "head" or x["source"] == "camera":
        return "head"
    if g == "neck":
        return "neck"
    if g in ("left_leg", "right_leg"):
        return g.replace("_", " ")
    return "trunk inside"


def proj(p, o, u, v):
    d = [p[k] - o[k] for k in range(3)]
    return (sum(d[k] * u[k] for k in range(3)), sum(d[k] * v[k] for k in range(3)))


def tri_area(a, b, c):
    return abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2


def inside(p, a, b, c):
    s = [(b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]),
         (c[0] - b[0]) * (p[1] - b[1]) - (c[1] - b[1]) * (p[0] - b[0]),
         (a[0] - c[0]) * (p[1] - c[1]) - (a[1] - c[1]) * (p[0] - c[0])]
    return all(x >= 0 for x in s) or all(x <= 0 for x in s)


def pick_diagonal(rows):
    best = max(itertools.combinations(rows, 2), key=lambda pr: math.dist(pr[0]["seat_world"], pr[1]["seat_world"]))
    return [r["id"] for r in best]


def pick_triangle(rows, com, u, v, need=None):
    o = rows[0]["seat_world"]
    P = {r["id"]: proj(r["seat_world"], o, u, v) for r in rows}
    c = proj(com, o, u, v)
    best, key = None, None
    for t in itertools.combinations(rows, 3):
        if need and not need(t):
            continue
        a, b, d = (P[r["id"]] for r in t)
        k = (inside(c, a, b, d), tri_area(a, b, d))
        if key is None or k > key:
            best, key = t, k
    return [r["id"] for r in best], key[0], round(key[1], 0)


def main():
    FJ = json.load(open(os.path.join(LAB, "fasteners", "fasteners.json")))
    F = FJ["fasteners"]
    T5, M = parse_table5(), parse_masses()
    GJ = {(g["part"], g["into"], g["part_inst"]): g for g in json.load(open(os.path.join(DATA, "geom_joints.json")))}
    lips = json.load(open(os.path.join(DATA, "lips.json"))) if os.path.exists(os.path.join(DATA, "lips.json")) else {}
    screws = [x for x in F if x["kind"] == "screw"]
    inserts = {x["screw"]: x for x in F if x["kind"] == "insert"}

    def fitted(x):
        return x.get("status") not in ("NOT FITTED", "LEAVE OUT (D18)") and not x.get("leave_out")

    def klass(x):
        if x["source"] in ("servo_case", "horn_centre", "idle_boss") or x["anchor"].startswith("SG90 output shaft"):
            return "a"
        if x["source"] in ("camera", "sg90_tab"):
            return "c"
        return "b"

    # ---- joints ---------------------------------------------------------------------------------------
    joints = collections.OrderedDict()
    for x in screws:
        if klass(x) == "a":
            continue
        if x["anchor"].startswith("horn("):
            key = "%s %s horn" % (x["servo"], "drive" if "drive" in x["anchor"] else "idle")
        elif x["anchor"] == "servo pilot":
            key = "%s servo case screws" % x["servo"]
        elif x["part"] in ("body_front", "body_back"):
            key = "%s shell" % x["part"]
        else:
            key = "%s -> %s (%s)" % (x["part"], x["into"], x["link"])
        joints.setdefault(key, []).append(x)

    out, keep = [], {}
    for key, rows in joints.items():
        fit = [r for r in rows if fitted(r)]
        n = len(fit)
        p, i = rows[0]["part"], rows[0]["into"]
        J = dict(joint=key, cls="".join(sorted(set(klass(r) for r in rows))), n_listed=len(rows), n_before=n,
                 spec=sorted(set(r["spec"] for r in rows)), area=area_of(rows[0]), ids=[r["id"] for r in fit])
        kept, why, sf = [r["id"] for r in fit], "", {}
        if key in T5 or key.replace(" idle horn", " idle horn") in T5:
            t = T5[key]
            sf = {k: t[k] for k in ("walk", "push", "soft", "mid")}
            short = [k for k in ("walk", "push") if t[k] < 2.0] + [k for k in ("soft", "mid") if t[k] < 1.2]
            if short:
                why = "servo chain, table 5: under the margin today in %s, so it needs more, not fewer (keep all)" % ", ".join(short)
            else:
                nmin = math.ceil(n * max(2 / t["walk"], 2 / t["push"], 1.2 / t["soft"], 1.2 / t["mid"]))
                why = "servo chain, table 5: n_min %d by load; kept all (moment and fatigue of the pattern not modelled)" % nmin
            J["role"], J["src"] = "structural, servo chain", SRC["ST"] + " table 5"
        elif "servo case screws" in key or "horn" in key:
            J["role"] = "structural, servo chain"
            why = "servo chain, no table 5 row: keep all (BLOCKER for any cut: not modelled)"
        else:
            rule = None
            if p in ("body_front", "body_back"):
                rule = "shell"
            elif p in ("battery_pack_lid", "head_bot_sheet"):
                rule = "plate"
            elif p in ("raspberrypizerow", "board", "speaker_stand", "speaker_interface", "bulb") or rows[0]["source"] == "camera":
                rule = "diagonal"
            J["role"] = {"shell": "cover (shell)", "plate": "cover or lid", "diagonal": "board or bracket"}.get(rule, "structural or kept")
            if rule is None:
                reasons = {
                    "head_roll_mount": "carries the head on the neck; table 3.2 side SF at mid 0.76 (under 1.2): keep all",
                    "trunk_top": "frame: both hip yaw bearing loads, table 3.2 SF at mid 0.6: keep all",
                    "body_middle_bottom": "frame: carries the shells, the battery and the shell-hit forces to trunk_bottom; no lateral key (0 mm2 lateral contact, GJ); not modelled: keep all (BLOCKER for any cut)",
                    "foot_side": "ankle idle horn share, table 3.2 SF 17 / 15 / 7.4 / 2.4: one screw would carry it but lets the part turn: keep 2",
                    "foot_bottom_tpu": "sole: walking friction loads, not modelled: keep all",
                    "bno055": "IMU: kept at 4 so the board cannot chatter (the policy reads its gyro and accelerometer, WIRING.md; the fall rule reads its NDOF orientation)",
                    "usb_c_charger": "one screw plus the USB-C cutout today; the plug forces need the screw: keep 1",
                    "left_cache": "leg segment stack (the M3x10 passes the cache and the knee sheet into leg_spacer; the FEA ties it): keep all",
                    "right_cache": "leg segment stack (the M3x10 passes the cache and the knee sheet into leg_spacer; the FEA ties it): keep all",
                    "knee_to_ankle_left_sheet": "leg_spacer ties of the shin and thigh segments (FEA tied; knee sheet SF 1.63 walking, under 2): keep all",
                    "knee_to_ankle_right_sheet": "leg_spacer ties of the shin and thigh segments (FEA tied; knee sheet SF 1.63 walking, under 2): keep all",
                }
                why = reasons.get(p, "SG90 tab: antenna torque and the head swing hit (G6) not modelled: keep all (BLOCKER for any cut)"
                                  if rows[0]["source"] == "sg90_tab" else "kept (not a cover or board)")
            else:
                # F1: inertial pull, one screw takes it all
                head = area_of(rows[0]) == "head"
                acc = ACC_G["head" if head else "trunk"]
                ride = {
                    "body_front": (["body_front"], 0.0),
                    "body_back": (["body_back", "battery_pack_lid"], 122.0 + 8.5),
                    "battery_pack_lid": (["battery_pack_lid"], 122.0),
                    "head_bot_sheet": (["head_bot_sheet"], 3.3 + 1.2),
                    "speaker_stand": ([], 38.8), "speaker_interface": ([], 31.1), "bulb": ([], 9.0),
                    "raspberrypizerow": ([], 12.6), "board": ([], 16.0), "camera PCB (not in CAD)": ([], 4.0),
                }[p]
                m_g = sum(M.get(k, 0.0) for k in ride[0]) + ride[1]
                size = rows[0]["size"]
                if rows[0]["anchor"] == "M3 insert":
                    t = min(r.get("near") or 9 for r in fit)
                    cap = min(pull_through(size, t), INSERT_PULL)
                    cap_src = "min(head pull-through pi x %.1f x %.1f x %.1f, insert pull-out %d)" % (DK[size], t, TAU_LO, INSERT_PULL)
                else:
                    strip = {"battery_pack_lid": 305, "speaker_stand": 180, "speaker_interface": 168, "bulb": 144,
                             "raspberrypizerow": 275, "board": 263, "camera PCB (not in CAD)": 144}[p]
                    cap, cap_src = float(strip), "thread strip, low end, %s table 3.2" % SRC["ST"]
                F1 = {k: m_g / 1000 * acc[k] * G for k in ("walk", "soft", "mid")}
                sf = {"walk": round(cap / F1["walk"], 1), "soft": round(cap / F1["soft"], 1), "mid": round(cap / F1["mid"], 1)}
                J.update(mass_g=round(m_g, 1), mass_src=SRC["MB"] + " and " + SRC["ST"] + " table 3.2",
                         F1_pull_N={k: round(v, 1) for k, v in F1.items()}, cap_per_screw_N=round(cap, 0), cap_src=cap_src,
                         SF_F1_one_screw=sf, F1_pass=sf["walk"] >= 2 and sf["soft"] >= 1.2 and sf["mid"] >= 1.2)
                g = GJ.get((p, i, rows[0]["part_inst"])) or next((v for k, v in GJ.items() if k[0] == p), None)
                if rule == "diagonal":
                    kept = pick_diagonal(fit)
                    why = "stiff board or bracket on 4 seats: the 2 diagonal screws hold it, it rests on the other 2 seats and cannot rock; F1 SF %.1f at mid with one screw" % sf["mid"]
                elif rule == "plate":
                    kept, ok, ar = pick_triangle(fit, g["part_com_world"], g["u"], g["v"])
                    lat = g["contact_mm2"]["lateral_by_side"]
                    why = ("thin plate: 3 screws (a plane needs 3 points), largest triangle %s its centre of mass (%.0f mm2 of the screw plane); edges captured %s; F1 SF %.1f at mid with one screw"
                           % ("round" if ok else "NOT round", ar, lat, sf["mid"]))
                else:  # shell: 2 into body_middle_top (it hangs between the shells) + 1 into body_middle_bottom
                    com = g["part_com_world"]
                    if p == "body_front":   # 4: the side shear at mid needs the 4th screw (lip legs 1732 N, data/lips.json)
                        top = [r for r in fit if r["into"] == "body_middle_top"]
                        bot = [r for r in fit if r["into"] == "body_middle_bottom"]
                        kept = pick_diagonal(top) + pick_diagonal(bot)
                        ok, ar = True, 0
                    else:
                        kept, ok, ar = pick_triangle(fit, com, g["u"], g["v"],
                                                     need=lambda t: 1 <= sum(r["into"] == "body_middle_top" for r in t) <= 2)
                    nb = sum(1 for r in fit if r["id"] in kept)
                    bearing = 3.0 * min(r.get("near") or 9 for r in fit) * PLA_X
                    lipcap = lips.get(p, {}).get("capacity_N", {})
                    F2 = {}
                    for lv in ("soft", "mid"):
                        F2[lv] = dict(before=round(n * bearing / SHELL_HIT_N[lv], 2), after_screws=round(nb * bearing / SHELL_HIT_N[lv], 2))
                        for dn in ("y", "z_up", "z_down"):
                            F2[lv]["after_with_lip_" + dn] = round((nb * bearing + lipcap.get(dn, 0)) / SHELL_HIT_N[lv], 2)
                    J.update(F2_bearing_per_screw_N=round(bearing, 0), F2_src=SHELL_HIT_SRC, F2_SF=F2)
                    why = ("shell: %d screws (at least 1 into body_middle_top, which hangs between the two shells, and 1 into body_middle_bottom), largest triangle %s its centre of mass (%.0f mm2); F1 SF %.1f at mid with one screw. F2 (bearing, crack but no separation): see F2_SF; the printed lip (mesh_designs.py) carries the side and vertical shear where it can be printed"
                           % (len(kept), "round" if ok else "NOT round", ar, sf["mid"]))
                    if p == "body_back":
                        J["needs_ahmed_ok"] = "downward shear on the back shell (only in an upside-down landing) at the mid fall level: SF %.2f after, %.2f today; no lip can print there (body_middle_top's back face is its print bed)" % (F2["mid"]["after_with_lip_z_down"], F2["mid"]["before"])
        J.update(n_after=len(kept), kept=kept, cut=[r for r in J["ids"] if r not in kept], why=why, SF=sf)
        for r in fit:
            keep[r["id"]] = r["id"] in kept
        out.append(J)

    # ---- per fastener classification ------------------------------------------------------------------
    rows_csv, cnt = [], collections.Counter()
    for x in screws:
        c, f = klass(x), fitted(x)
        k = keep.get(x["id"], True) if f else False
        cnt[(c, "listed")] += 1
        cnt[(c, "fitted")] += f
        cnt[(c, "after")] += (f and k)
        cnt[(area_of(x), c, "before")] += f
        cnt[(area_of(x), c, "after")] += (f and k)
        rows_csv.append([x["id"], "screw", c, x["spec"], x["part"], x["into"], x["anchor"], area_of(x), int(f), int(f and k),
                         x.get("supply", ""), "" if not f else ("keep" if k else "cut")])
    ins_after = 0
    for sid, ins in inserts.items():
        k = keep.get(sid, True)
        ins_after += k
        rows_csv.append([ins["id"], "insert", "b", ins["spec"], ins["into"], "", "for " + sid, area_of(next(s for s in screws if s["id"] == sid)), 1, int(k), "BOM 16", "keep" if k else "cut"])
    washers_before = sum(2 for x in screws if "washers" in x["spec"] and fitted(x))
    washers_after = sum(2 for x in screws if "washers" in x["spec"] and fitted(x) and keep.get(x["id"], True))
    with open(os.path.join(DATA, "classification.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "kind", "class", "spec", "part", "into", "anchor", "area", "fitted_before", "fitted_after", "supply", "verdict"])
        w.writerows(rows_csv)

    # ---- assembly steps (fastening operations; cited per operation times) -------------------------------
    def step_of(x):
        p, sub = x["part"], x["viewer_sub"]
        if x["source"] in ("horn_centre", "idle_boss"):
            return "02 servo prep: horn centre and idle screws"
        if p in ("body_front", "body_back"):
            return "19 shells front and back"
        if p in ("battery_pack_lid", "usb_c_charger"):
            return "15 battery bay, charger, lid"
        if p in ("board", "bno055"):
            return "14 trunk electronics"
        if sub in ("head",) and p in ("head_bot_sheet", "head_roll_mount"):
            return "18 head closing"
        if sub == "head" or x["group"] == "head" or x["source"] == "camera":
            return "17 head internals"
        order = {"left_foot": "03", "left_shin": "04", "left_thigh": "05", "left_bracket": "06", "left_hip": "07",
                 "right_foot": "08", "right_shin": "09", "right_thigh": "10", "right_bracket": "11", "right_hip": "12",
                 "trunk": "13", "neck": "16"}
        return "%s %s" % (order.get(sub, "13"), sub.replace("_", " "))
    steps = collections.OrderedDict()
    ins_n = collections.Counter()
    for x in screws:
        if not fitted(x) or x["source"] == "servo_case":
            continue
        s = step_of(x)
        st = steps.setdefault(s, collections.Counter())
        st["screws_before"] += 1
        st["screws_after"] += keep.get(x["id"], True)
        if "washers" in x["spec"]:
            st["washers_before"] += 2
            st["washers_after"] += 2 * keep.get(x["id"], True)
        if x["id"] in inserts:
            ins_n["before"] += 1
            ins_n["after"] += keep.get(x["id"], True)
    steps["19 shells front and back"]["lips_after"] = 2  # shell pressed over its lip (press-fit class)
    rows_st, tot = [], collections.Counter()
    for s in sorted(steps):
        c = steps[s]
        for when in ("before", "after"):
            for j, lv in enumerate(("lo", "mid", "hi")):
                tot[(when, lv)] += c["screws_" + when] * T_SCREW[j] + c["washers_" + when] * T_SNAP[j] + c.get("lips_" + when, 0) * T_SNAP[j]
        rows_st.append([s, c["screws_before"], c["screws_after"], c["washers_before"], c["washers_after"], c.get("lips_after", 0),
                        round((c["screws_before"] * T_SCREW[1] + c["washers_before"] * T_SNAP[1]) / 60, 1),
                        round((c["screws_after"] * T_SCREW[1] + c["washers_after"] * T_SNAP[1] + c.get("lips_after", 0) * T_SNAP[1]) / 60, 1)])
    rows_st.insert(0, ["01 heat-set inserts (part prep)", "", "", "", "", "", "BLOCKER x %d" % ins_n["before"], "BLOCKER x %d" % ins_n["after"]])
    with open(os.path.join(DATA, "assembly_steps.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["step", "screws_before", "screws_after", "washers_before", "washers_after", "lip_press_after", "min_before", "min_after"])
        w.writerows(rows_st)
        w.writerow([])
        w.writerow(["# times: screw 8/10/12 s, washer and press or snap 2/3/4 s: " + SRC["dfma"] + "; washer and lip press use the press-fit class (lab mapping); servo case screws are factory fitted (0 s); heat-set insert time: BLOCKER (no published per-insert time found; check: time 10 inserts on the S1 coupons)"])

    # ---- summary and phase 2 data -----------------------------------------------------------------------
    bc_b = cnt[("b", "fitted")] + cnt[("c", "fitted")]
    bc_a = cnt[("b", "after")] + cnt[("c", "after")]
    tot_b = sum(cnt[(c, "fitted")] for c in "abc")
    tot_a = sum(cnt[(c, "after")] for c in "abc")
    areas = sorted({k[0] for k in cnt if len(k) == 3})
    summary = dict(
        counts={c: dict(listed=cnt[(c, "listed")], fitted=cnt[(c, "fitted")], after=cnt[(c, "after")]) for c in "abc"},
        fitted_before=tot_b, fitted_after=tot_a, cut=tot_b - tot_a,
        share_cut_of_bc=round((bc_b - bc_a) / bc_b, 3), share_cut_of_total=round((tot_b - tot_a) / tot_b, 3),
        target_90pct_of_total_needs_cut=math.ceil(0.9 * tot_b),
        inserts_before=len(inserts), inserts_after=ins_after, washers_before=washers_before, washers_after=washers_after,
        by_area={a: {c: [cnt[(a, c, "before")], cnt[(a, c, "after")]] for c in "abc" if cnt[(a, c, "before")]} for a in areas},
        fastening_hours={w: [round(tot[(w, lv)] / 3600, 2) for lv in ("lo", "mid", "hi")] for w in ("before", "after")},
        kept_by_role=collections.Counter(), sources=dict(SRC, acc=ACC_SRC, pla=PLA_SRC, insert=INSERT_SRC, dk=DK_SRC))
    for J in out:
        summary["kept_by_role"][J["role"]] += J["n_after"]
    json.dump(out, open(os.path.join(DATA, "joints.json"), "w"), indent=1)
    with open(os.path.join(DATA, "joints.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["joint", "class", "area", "role", "n_before", "n_after", "cut_ids", "SF", "why"])
        for J in out:
            w.writerow([J["joint"], J["cls"], J["area"], J["role"], J["n_before"], J["n_after"], " ".join(J["cut"]), json.dumps(J["SF"]), J["why"]])
    json.dump(summary, open(os.path.join(DATA, "summary.json"), "w"), indent=1)
    cut_ids = [J for J in out if J["cut"]]
    json.dump(dict(note="phase 2 input for fasteners.json and BOM.md: screws to drop, their inserts, the washers that go with them; holes stay in the STLs (reversible)",
                   screws_cut=[i for J in cut_ids for i in J["cut"]],
                   inserts_cut=[inserts[i]["id"] for J in cut_ids for i in J["cut"] if i in inserts],
                   washers_cut=sum(2 for J in cut_ids for i in J["cut"] if "washers" in next(s for s in screws if s["id"] == i)["spec"]),
                   by_joint={J["joint"]: J["cut"] for J in cut_ids}),
              open(os.path.join(DATA, "phase2_fasteners.json"), "w"), indent=1)
    print(json.dumps({k: summary[k] for k in summary if k not in ("sources", "by_area")}))
    print(json.dumps(summary["by_area"]))
    for J in out:
        if J["cut"] or J["role"].startswith("cover") or J["role"].startswith("board"):
            print(J["joint"], J["n_before"], "->", J["n_after"], J.get("SF"), J.get("F2_SF", ""), J["why"][:160])


if __name__ == "__main__":
    main()
