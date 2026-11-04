#!/usr/bin/env python3
"""V1 track 2 (assembly) geometry, CAD check only.

1. Tool path of every driven screw (fasteners/fasteners.json): a bundle of rays from the head along the screw axis,
   radius = tool radius + 0.2 mm, length = the tool reach; plus the screw's own way in (head diameter, length + head).
2. Build order: a topological sort of part placements and screw drives (a screw before any part that blocks its
   tool path; both of its parts before it). Cycles are broken by turning a joint (the blocker moves away), else FAIL.
3. Service from the built duck: lid screws, XT30, microSD, Pi USB (rays from each target; parts that block).
4. D29 eye lamps: bulb, head wall and eye windows along +x through each eye; free depth behind the bulb.
5. D30 button: the body_back control switch cutout, its wall and the free depth behind it.
6. Speaker pocket: is the speaker space closed on all six sides by speaker_stand and speaker_interface?

Reads robot.urdf and the stock STLs through fasteners/fastlib.py (read-only reuse). Writes ASM_OUT/asm_geom.json
(default /home/user/v1_out/asm) and twin/assembly/asm_geom_summary.json.
Tool sizes: TOOLS below, each with its source. Run: python3 altaay_lab/twin/assembly/asm_geom.py
"""
import collections
import heapq
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(LAB, "fasteners"))
import fastlib  # noqa: E402
import trimesh  # noqa: E402

OUT = os.environ.get("ASM_OUT", "/home/user/v1_out/asm")
os.makedirs(OUT, exist_ok=True)
MARGIN = 0.2
TOOLS = {
    "hex2.5": dict(r=2.5 / math.sqrt(3), reach=88.0, short=None,
                   src="BOM T4 Bondhus 12192 set (long arm); 2.5 mm key Bondhus 12154 length 88 mm (MRO Supply, KBC Tools, Zoro listings via search index 2026-11-04); short arm not published in what was read"),
    "hex2.0": dict(r=2.0 / math.sqrt(3), reach=82.6, short=15.9,
                   src="BOM T4; 2 mm long key Bondhus 13952: 3-1/4 in overall, 5/8 in short arm (partssource.com listing via search index 2026-11-04)"),
    "PH0": dict(r=1.5, reach=60.0, short=None,
                src="proposed (needs Ahmed's OK): Wera 2050 PH 0 x 60 mm, blade 60 x 3.0 mm, 157 mm overall (Wera data sheet 05118022001, Rapid 51-1335, via search index)"),
    "PH1": dict(r=2.0, reach=80.0, short=None,
                src="proposed (needs Ahmed's OK): Wera 2050 PH 1 x 80 mm, blade 80 x 4.0 mm (Wera data sheet 05118024001, Rapid 51-1336, via search index)"),
}
HEAD_TOOL = {"M3_din912": "hex2.5", "M2.5_din912": "hex2.0", "M3_iso7380": "hex2.0", "M2_pan_selftap": "PH0",
             "SG90_screw": "PH0", "M3_horn_centre": "PH1", "PA3_idle": "PH1"}
RANK = ["foot_assembly", "foot_assembly_2", "knee_and_ankle_assembly_2", "knee_and_ankle_assembly_4",
        "knee_and_ankle_assembly", "knee_and_ankle_assembly_3", "left_roll_to_pitch_assembly",
        "right_roll_to_pitch_assembly", "hip_roll_assembly", "hip_roll_assembly_2", "trunk_assembly",
        "neck_pitch_assembly", "head_pitch_to_yaw", "neck_yaw_assembly", "head_assembly", "left_antenna_holder",
        "right_antenna_holder"]

S = fastlib.Scene(os.path.join(OUT, "scratch"))
INST = S.inst
nm = lambda k: INST[k]["name"]  # noqa: E731
DROP = set()   # D29 (side lamp dropped) was reverted by Ahmed at about 6:45 PM ET (D33): the side lamp stays in
NOTFIT = {k for k, i in enumerate(INST) if i["name"] == "board" and i["link"] == "head_assembly"}
OBST = [k for k in range(len(INST)) if k not in DROP | NOTFIT]
PL = json.load(open(os.path.join(LAB, "audit", "placements.json")))
OB = [(k, S.mesh(k), INST[k]["link"]) for k in OBST]
for p in PL:
    m = trimesh.creation.box(extents=p["dims_xyz_mm"])
    m.apply_translation(p["center_mm"])
    OB.append(("box:" + p["id"], m, "trunk_assembly"))
OBKEY = [o[0] for o in OB]

# servo cases -> one unit (the middle case index)
MIDS = [k for k in OBST if nm(k) == fastlib.SERVO_MID]
UNIT = {k: k for k in OBKEY}
for k in OBST:
    if nm(k) in (fastlib.SERVO_TOP, fastlib.SERVO_BOT):
        c = S.mesh(k).bounds.mean(0)
        UNIT[k] = min((m for m in MIDS if INST[m]["link"] == INST[k]["link"]),
                      key=lambda m: np.linalg.norm(S.mesh(m).bounds.mean(0) - c))


def uname(u):
    if isinstance(u, str):
        return u
    if u in MIDS:
        return "servo@%s#%d" % (INST[u]["link"], u)
    return "%s#%d" % (nm(u), u)


def ulink(u):
    return "trunk_assembly" if isinstance(u, str) else INST[u]["link"]


def build(cfg=None, keys=None):
    Vs, Fs, own, off = [], [], [], 0
    for j, (key, m, link) in enumerate(OB):
        if keys is not None and key not in keys:
            continue
        V = np.asarray(m.vertices, float)
        if cfg:
            D = S.link_T(link, {**S.zero, **cfg}) @ np.linalg.inv(S.T0[link])
            V = V @ D[:3, :3].T + D[:3, 3]
        Vs.append(V)
        Fs.append(np.asarray(m.faces) + off)
        own.append(np.full(len(m.faces), j))
        off += len(V)
    return trimesh.Trimesh(np.vstack(Vs), np.vstack(Fs), process=False), np.concatenate(own)


def cast(M, own, O, D, maxhits=80):
    tri, ray, loc = M.ray.intersects_id(O, D, multiple_hits=True, max_hits=maxhits, return_locations=True)
    t = np.einsum("ij,ij->i", loc - O[ray], D[ray]) if len(ray) else np.zeros(0)
    return own[tri] if len(tri) else np.zeros(0, int), ray, t


def frame(d):
    d = d / np.linalg.norm(d)
    a = np.cross(d, [1.0, 0, 0])
    if np.linalg.norm(a) < 0.1:
        a = np.cross(d, [0, 1.0, 0])
    a /= np.linalg.norm(a)
    return d, a, np.cross(d, a)


def bundle(p0, d, r, n=8):
    d, a, b = frame(d)
    pts = [p0] + [p0 + r * (math.cos(t) * a + math.sin(t) * b) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]
    return np.array(pts), np.tile(d, (len(pts), 1))


FJ = json.load(open(os.path.join(LAB, "fasteners", "fasteners.json")))["fasteners"]
SCREWS = [f for f in FJ if f["kind"] == "screw" and not f.get("leave_out") and f.get("install") is not False
          and f["source"] != "servo_case"]   # 342 fitted less the 56 factory case screws


def AB(f):
    a = UNIT.get(f.get("part_inst"), None) if f.get("part_inst") is not None else "nomesh:" + f["part"]
    b = UNIT.get(f.get("into_inst"), None) if f.get("into_inst") is not None else "nomesh:" + str(f["into"])
    return a, b


def screw_cast(f, M, own, keymap=None):
    p, a = np.array(f["seat_world"], float), np.array(f["axis_world"], float)
    d = -a / np.linalg.norm(a)
    k_, dk = f["head"]["k"], f["head"]["dk"]
    L = f["length_mm"] if f["length_mm"] is not None else f["draw_length_mm"]
    tool = HEAD_TOOL[f["head"]["type"]]
    T = TOOLS[tool]
    r = TOOLS["hex2.5"]["r"] if f["head"]["type"] == "M3_iso7380" else T["r"]
    O1, D1 = bundle(p + d * (k_ + 0.05), d, r + MARGIN)
    O2, D2 = bundle(p + d * 0.05, d, dk / 2 + 0.1)
    keymap = keymap or OBKEY
    hits, first, toolhits = {}, 1e9, {}
    for O, D, lim, tag in ((O1, D1, T["reach"], "tool"), (O2, D2, L + k_, "screw")):
        o, ray, t = cast(M, own, O, D)
        for oi, ti in zip(o, t):
            if ti < 0 or ti > lim:
                continue
            u = UNIT[keymap[oi]]
            hits[u] = min(hits.get(u, 1e9), float(ti))
            if tag == "tool":
                first = min(first, float(ti))
                if ti > 0.5:
                    toolhits[u] = min(toolhits.get(u, 1e9), float(ti))
    screw_cast.toolhits = toolhits
    return tool, hits, first


res = {"tools": TOOLS, "margin_mm": MARGIN}
M0, own0 = build()
print("scene faces", len(M0.faces), "driven screws", len(SCREWS))
cast0 = {}
for f in SCREWS:
    tool, hits, first = screw_cast(f, M0, own0)
    A, B = AB(f)
    blk = {u: t for u, t in hits.items() if u not in (A, B)}
    selfh = {u: t for u, t in screw_cast.toolhits.items() if u in (A, B)}
    cast0[f["id"]] = dict(tool=tool, A=A, B=B, blk=blk, self=selfh, first=first)
n_clear = sum(1 for c in cast0.values() if not c["blk"] and not c["self"])
print("zero pose, everything present: %d of %d screws have a clear tool path" % (n_clear, len(cast0)))
selfblock = {fid: c for fid, c in cast0.items() if c["self"]}
print("self blocks (own part in the tool path):", len(selfblock))
for fid, c in list(selfblock.items())[:12]:
    print("  ", fid, c["tool"], {uname(u): round(t, 1) for u, t in c["self"].items()})

# ------------------------------------------------------------------ build order (subassemblies merge at each screw)
from scipy.spatial import cKDTree  # noqa: E402
units = sorted(set(UNIT.values()) | {c[x] for c in cast0.values() for x in ("A", "B")}, key=str)
byname = collections.defaultdict(list)
for u in units:
    byname[uname(u).split("#")[0]].append(u)
PRE = {}
LATE = {u: "body_back" for n_ in ("holder", "cell", "box:bms_tenergy", "bms") for u in byname.get(n_, [])}
for u in byname.get("antenna", []):
    LATE[u] = "antenna_holder"
for n_, c_ in (("power_switch", "body_back"), ("box:fuse_holder", "battery_pack_lid"),
               ("box:mosfet_switch", "battery_pack_lid"), ("box:bec_pro", "body_middle_bottom"),
               ("box:usb_slack", "body_middle_bottom"), ("box:power_splice", "trunk_bottom")):
    for u in byname.get(n_, []):
        PRE[u] = byname[c_][0]
screwed = {c[x] for c in cast0.values() for x in ("A", "B")}
umesh = {u: np.vstack([np.asarray(OB[i][1].vertices) for i, k in enumerate(OBKEY) if UNIT[k] == u])
         for u in units if not (isinstance(u, str) and u.startswith("nomesh"))}
for u in units:
    if u in screwed or u in PRE or u in LATE or u not in umesh:
        continue
    cand = [v for v in screwed if v in umesh and ulink(v) == ulink(u)]
    if cand:
        smp = umesh[u][:: max(1, len(umesh[u]) // 300)]
        PRE[u] = min(cand, key=lambda v: cKDTree(umesh[v]).query(smp)[0].min())
import random  # noqa: E402


def run_greedy(seed):
    global par, members
    rnd = random.Random(seed)
    jitter = {fid: (rnd.random() if seed else 0.0) for fid in cast0}
    par = {u: u for u in units}
    members = {u: {u} for u in units}
    for u, c_ in PRE.items():
        union(c_, u)
    return greedy_body(jitter)


par = {u: u for u in units}


def find(x):
    while par[x] != x:
        par[x] = par[par[x]]
        x = par[x]
    return x


members = {u: {u} for u in units}


def union(a_, b_):
    ra, rb = find(a_), find(b_)
    if ra == rb:
        return
    par[rb] = ra
    members[ra] |= members.pop(rb)


for u, c_ in PRE.items():
    union(c_, u)
res["pre_joined"] = {uname(u): uname(c_) for u, c_ in PRE.items()}
FBYID = {f["id"]: f for f in SCREWS}
JN = {j["name"]: j for j in S.joints}


def path_joints(l1, l2):
    _, j1 = S.ancestors(l1)
    _, j2 = S.ancestors(l2)
    return [j for j in j1 + j2 if (j in j1) != (j in j2)]


def joint_fix(f, u):
    """Turn one joint between the screw's link and blocker u until u leaves the tool path."""
    ls, lb = f["link"], ulink(u)
    keys = [k for k in OBKEY if UNIT[k] == u]
    for jn in path_joints(ls, lb):
        j = JN[jn]
        for th in sorted(np.linspace(j["lo"], j["hi"], 25), key=abs):
            if abs(th) < 1e-3:
                continue
            cfg = {jn: float(th)}
            Ds = S.link_T(ls, {**S.zero, **cfg}) @ np.linalg.inv(S.T0[ls])
            Db = S.link_T(lb, {**S.zero, **cfg}) @ np.linalg.inv(S.T0[lb])
            Drel = np.linalg.inv(Ds) @ Db
            Vs, Fs, own, off = [], [], [], 0
            for kk in keys:
                m = OB[OBKEY.index(kk)][1]
                Vs.append(np.asarray(m.vertices) @ Drel[:3, :3].T + Drel[:3, 3])
                Fs.append(np.asarray(m.faces) + off)
                own.append(np.full(len(m.faces), OBKEY.index(kk)))
                off += len(m.vertices)
            Mb = trimesh.Trimesh(np.vstack(Vs), np.vstack(Fs), process=False)
            _, hits, _ = screw_cast(f, Mb, np.concatenate(own))
            if u not in hits:
                return dict(joint=jn, angle_deg=round(math.degrees(th), 1))
    return None


def rank(fid, jitter=None):
    lk = FBYID[fid]["link"]
    return (RANK.index(lk) if lk in RANK else 99, (jitter or {}).get(fid, 0.0), fid)


def present_blk(fid):
    c = cast0[fid]
    m_ = members[find(c["A"])] | members[find(c["B"])]
    return [u for u in c["blk"] if u in m_]


FORCED = ["F073", "F074", "F049", "F050", "F138", "F139", "F126", "F128", "F130", "F132"]


def greedy_body(jitter):
    pending, seq, fixes, fails = set(cast0), [], {}, {}
    DRIVE_SET = {}
    while pending:
        drv = [fid for fid in pending if not present_blk(fid)]
        turn = {}
        if not drv:
            for fid in sorted(pending, key=lambda x: rank(x, jitter)):
                fx = [joint_fix(FBYID[fid], u) for u in present_blk(fid)]
                if all(fx):
                    turn[fid] = fx
                    break
            if turn:
                drv = list(turn)
            else:
                fid = min(pending, key=lambda x: (len(present_blk(x)), rank(x, jitter)))
                fails[fid] = {uname(u): round(cast0[fid]["blk"][u], 1) for u in present_blk(fid)}
                drv = [fid]
        forced_now = [fid for fid in FORCED if fid in drv]
        if forced_now:
            drv = forced_now[:1]
        inner = [fid for fid in drv if find(cast0[fid]["A"]) == find(cast0[fid]["B"])]
        if inner:
            pick = min(inner, key=lambda x: rank(x, jitter))
        else:
            def penalty(fid):
                c = cast0[fid]
                new = members[find(c["A"])] | members[find(c["B"])]
                if FBYID[fid]["part"] == "battery_pack_lid":
                    new = new | {u for u, c_ in LATE.items() if c_ == "body_back"}
                n = 0
                for g in pending:
                    if g == fid:
                        continue
                    cg = cast0[g]
                    if (cg["A"] in new or cg["B"] in new) and not present_blk(g) and any(u in new for u in cg["blk"]):
                        n += 1000 if g in FORCED else 1
                return (n, 0 if FBYID[fid]["source"] in ("horn_centre", "idle_boss") else 1, rank(fid, jitter))
            pick = min(drv, key=penalty)
        c = cast0[pick]
        joined = find(c["A"]) != find(c["B"])
        if pick in turn:
            fixes[pick] = turn[pick]
        seq.append(dict(id=pick, spec=FBYID[pick]["spec"], part=FBYID[pick]["part"], into=FBYID[pick]["into"],
                        tool=c["tool"], link=FBYID[pick]["link"], group=FBYID[pick]["group"], joins=joined,
                        joint_turn=turn.get(pick), fail=fails.get(pick),
                        blocked_later=sorted(uname(u) for u in c["blk"])))
        if FBYID[pick]["part"] == "battery_pack_lid":
            for u, c_ in LATE.items():
                if c_ == "body_back":
                    union(byname["body_back"][0], u)
        union(c["A"], c["B"])
        if FBYID[pick]["part"].endswith("antenna_holder"):
            hk = c["A"]
            ant = min((u for u, c_ in LATE.items() if c_ == "antenna_holder"),
                      key=lambda u: np.linalg.norm(umesh[u].mean(0) - umesh[hk].mean(0)))
            union(hk, ant)
        seq[-1]["members_after"] = len(members[find(c["A"])])
        seq[-1]["present_at_drive"] = None
        DRIVE_SET[pick] = set(members[find(c["A"])])
        pending.discard(pick)
    return seq, fixes, fails, DRIVE_SET


best = None
for seed in range(0, int(os.environ.get("ASM_SEEDS", "1"))):
    r_ = run_greedy(seed)
    if best is None or len(r_[2]) < len(best[2]):
        best = r_ + (seed,)
    if not r_[2]:
        break
seq, fixes, fails, DRIVE_SET, best_seed = best
par = {u: u for u in units}
members = {u: {u} for u in units}
res["greedy_seed"] = best_seed
# final order and its check. Fixes found by the cast: the PH0 x 25 mm bit (BIT: blockers past 25 mm do not count),
# the 2.5 mm key's short arm (SHORT: own part at 64.9 mm, swing 210 to 250 deg free), the neck turn for F083/F084.
BIT = {"F126": 25.0, "F128": 25.0, "F130": 25.0, "F132": 25.0, "F348": 25.0, "F350": 25.0}
SHORT = {"F158", "F159", "F160", "F161"}
EAGER = ["F126", "F128", "F130", "F132"]


def eff_blk(fid):
    c = cast0[fid]
    b = {u: t for u, t in c["blk"].items() if t <= BIT.get(fid, 1e9)}
    if fid in fixes:
        b = {}
    return b


def simulate(order_ids, eager):
    global par, members
    par = {u: u for u in units}
    members = {u: {u} for u in units}
    for u, c_ in PRE.items():
        union(c_, u)
    out, viol, todo, lid_done = [], [], [i for i in order_ids if i not in eager], False
    pend_e = list(eager)

    def blocked(fid):
        c = cast0[fid]
        m_ = members[find(c["A"])] | members[find(c["B"])]
        if FBYID[fid]["part"] == "battery_pack_lid" and not lid_done:
            m_ = m_ | {u for u, c_ in LATE.items() if c_ == "body_back"}
        return [uname(u) for u in eff_blk(fid) if u in m_]

    def drive(fid):
        nonlocal lid_done
        c = cast0[fid]
        bl = blocked(fid)
        if bl:
            viol.append(dict(id=fid, blocked_by=bl))
        if FBYID[fid]["part"] == "battery_pack_lid" and not lid_done:
            for u, c_ in LATE.items():
                if c_ == "body_back":
                    union(byname["body_back"][0], u)
            lid_done = True
        joined = find(c["A"]) != find(c["B"])
        union(c["A"], c["B"])
        if FBYID[fid]["part"].endswith("antenna_holder"):
            ant = min((u for u, c_ in LATE.items() if c_ == "antenna_holder"),
                      key=lambda u: np.linalg.norm(umesh[u].mean(0) - umesh[c["A"]].mean(0)))
            union(c["A"], ant)
        f = FBYID[fid]
        out.append(dict(id=fid, spec=f["spec"], part=f["part"], into=f["into"], tool=c["tool"], link=f["link"],
                        group=f["group"], joins=joined, A=uname(c["A"]), B=uname(c["B"]),
                        note=("PH0 x 25 mm bit" if fid in BIT else "2.5 mm key short arm" if fid in SHORT else
                              ("turn %s to %.1f deg" % (fixes[fid][0]["joint"], fixes[fid][0]["angle_deg"]) if fid in fixes else "")),
                        blocked_later=sorted(uname(u) for u in c["blk"])))
    for fid in todo:
        for e in list(pend_e):
            c = cast0[e]
            if find(c["A"]) == find(c["B"]) or True:
                if not blocked(e) and (find(c["A"]) == find(c["B"]) or len(members[find(c["B"])]) > 1 or True):
                    if any(uname(cast0[e]["B"]) == uname(cast0[x]["B"]) for x in [o["id"] for o in out]):
                        drive(e)
                        pend_e.remove(e)
        drive(fid)
    for e in pend_e:
        drive(e)
    return out, viol


final, viol = simulate([st["id"] for st in seq], EAGER)
res["build_order_final"] = final
res["verify"] = dict(violations=viol, n=len(final))
print("final order", len(final), "violations", viol)

print("build order: %d screws; joint turns %d; still blocked %d; subassemblies left %d" % (
    len(seq), len(fixes), len(fails), len(members)))
for fid, fx in fixes.items():
    f = FBYID[fid]
    print("  turn", fid, f["spec"], f["part"], "->", f["into"], fx)
for fid, bl in fails.items():
    f = FBYID[fid]
    print("  FAIL", fid, f["spec"], f["part"], "->", f["into"], "tool", cast0[fid]["tool"], "blocked by", bl,
          "first", round(cast0[fid]["first"], 1))
def sector(f, units_present, hs=(15.0, 20.0, 25.0, 30.0)):
    keys = {k for k in OBKEY if UNIT[k] in units_present}
    if not keys:
        return None
    Mx, ox = build(keys=keys)
    p, a = np.array(f["seat_world"], float), np.array(f["axis_world"], float)
    d, e1, e2 = frame(-a)
    T = TOOLS[cast0[f["id"]]["tool"]]
    out = {}
    for h in hs:
        c = p + d * (f["head"]["k"] + h)
        angs = np.linspace(0, 2 * math.pi, 36, endpoint=False)
        Dd = np.array([math.cos(t) * e1 + math.sin(t) * e2 for t in angs])
        o, ray, t = cast(Mx, ox, np.tile(c, (36, 1)), Dd)
        free = np.ones(36, bool)
        for oi, ri, ti in zip(o, ray, t):
            if 0 < ti < T["reach"]:
                free[ri] = False
        best, run = 0, 0
        for v in np.r_[free, free]:
            run = run + 1 if v else 0
            best = max(best, min(run, 36))
        out[h] = best * 10
    return out


res["sectors"] = {}
for fid in list(fails) + list(selfblock):
    f = FBYID[fid]
    if cast0[fid]["tool"].startswith("hex"):
        sec = sector(f, DRIVE_SET.get(fid, set()))
        res["sectors"][fid] = sec
    bl = {}
    for u in list(cast0[fid]["blk"]) + list(cast0[fid]["self"]):
        ks = [k for k in OBKEY if UNIT[k] == u]
        b0 = np.min([OB[OBKEY.index(k)][1].bounds[0] for k in ks], axis=0)
        b1 = np.max([OB[OBKEY.index(k)][1].bounds[1] for k in ks], axis=0)
        bl[uname(u)] = [b0.round(1).tolist(), b1.round(1).tolist()]
    print("  detail", fid, f["spec"], f["part"], "->", f["into"], "seat", np.round(f["seat_world"], 1).tolist(),
          "axis", np.round(f["axis_world"], 2).tolist(), "first", round(cast0[fid]["first"], 1),
          "free swing arc deg by height", res["sectors"].get(fid), "blockers", bl, "sweep", f.get("sweep", {}).get("worst_text"))
res["build_order"] = seq
res["fixes"] = {k: v for k, v in fixes.items()}
res["fails"] = fails
res["self_blocks"] = {fid: {uname(u): round(t, 1) for u, t in c["self"].items()} for fid, c in selfblock.items()}
res["cast_zero"] = {fid: dict(tool=c["tool"], first=c["first"], blk={uname(u): t for u, t in c["blk"].items()})
                    for fid, c in cast0.items()}
for fid, c in list(selfblock.items())[:20]:
    f = FBYID[fid]
    print("  self", fid, f["spec"], f["part"], "->", f["into"], c["tool"], {uname(u): round(t, 1) for u, t in c["self"].items()})

# ------------------------------------------------------------------ service from the built duck
ico = trimesh.creation.icosphere(subdivisions=3).vertices  # 642 directions


def access(p, dirs=ico, removed=()):
    O = np.tile(p, (len(dirs), 1))
    o, ray, t = cast(M0, own0, O, np.asarray(dirs, float))
    hit = collections.defaultdict(set)
    for oi, ri, ti in zip(o, ray, t):
        if ti > 0.3:
            hit[ri].add(UNIT[OBKEY[oi]])
    return [hit.get(i, set()) for i in range(len(dirs))]


def greedy(hl, steps_=4, exclude=()):
    R, outl = set(exclude), []
    for _ in range(steps_):
        open_now = sum(1 for h in hl if h <= R)
        cand = collections.Counter(u for h in hl if not h <= R for u in h - R if (h - R) == {u})
        if not cand:
            cand = collections.Counter(u for h in hl for u in h - R)
        if not cand:
            break
        u, _ = max(cand.items(), key=lambda x: (sum(1 for h in hl if h <= R | {x[0]}), x[1]))
        R.add(u)
        outl.append(dict(remove=uname(u), open_fraction=round(sum(1 for h in hl if h <= R) / len(hl), 3),
                         before=round(open_now / len(hl), 3)))
    return outl


serv = {}
lid = byname["battery_pack_lid"][0]
lid_screws = [f for f in SCREWS if f["part"] == "battery_pack_lid"]
serv["lid_screws_built"] = {f["id"]: {uname(u): round(t, 1) for u, t in cast0[f["id"]]["blk"].items()}
                            for f in lid_screws}
bb = byname["body_back"][0]
bb_screws = [f for f in SCREWS if f["part"] == "body_back" or f["into"] == "body_back"]
serv["body_back_screws_built"] = {f["id"]: dict(spec=f["spec"], into=f["into"], part=f["part"],
                                                blk={uname(u): round(t, 1) for u, t in cast0[f["id"]]["blk"].items()})
                                  for f in bb_screws}
xt = np.array([-123.0, 31.0, 30.0])
hl = access(xt)
serv["xt30"] = dict(point=xt.tolist(), open_built=round(sum(1 for h in hl if not h) / len(hl), 3),
                    greedy=greedy(hl), blockers=collections.Counter(uname(u) for h in hl for u in h).most_common(8))
MODN = ("body_back", "battery_pack_lid", "holder", "cell", "bms", "box:bms_tenergy", "power_switch", "usb_c_charger",
        "box:fuse_holder", "box:mosfet_switch")
modkeys = {k for k in OBKEY if uname(UNIT[k]).split("#")[0] in MODN}
for lid_on in (False,):
    pass
nolid = {k for k in modkeys if uname(UNIT[k]).split("#")[0] not in ("battery_pack_lid", "box:fuse_holder", "box:mosfet_switch")}
Mnl, ownnl = build(keys=nolid)
O = np.tile(xt, (len(ico), 1))
o, ray, t = cast(Mnl, ownnl, O, np.asarray(ico, float))
hn = collections.defaultdict(set)
for oi, ri, ti in zip(o, ray, t):
    if ti > 0.3:
        hn[ri].add(UNIT[OBKEY[oi]])
serv["xt30_module_lid_off"] = dict(open=round(sum(1 for i in range(len(ico)) if not hn.get(i)) / len(ico), 3),
                                   open_forward=round(sum(1 for i, v in enumerate(ico) if not hn.get(i) and v[0] > 0.5) /
                                                      max(1, sum(1 for v in ico if v[0] > 0.5)), 3))
# lid screws with the module pulled back along -x
for pull in (0.0, 20.0):
    Vs, Fs, own, off = [], [], [], 0
    for j, (key, m, link) in enumerate(OB):
        V = np.asarray(m.vertices, float) + (np.array([-pull, 0, 0]) if key in modkeys else 0.0)
        Vs.append(V); Fs.append(np.asarray(m.faces) + off); own.append(np.full(len(m.faces), j)); off += len(V)
    Mp = trimesh.Trimesh(np.vstack(Vs), np.vstack(Fs), process=False)
    ownp = np.concatenate(own)
    outp = {}
    for f in lid_screws:
        g = dict(f)
        g["seat_world"] = (np.array(f["seat_world"]) + [-pull, 0, 0]).tolist()
        tool, hits, first = screw_cast(g, Mp, ownp)
        A_, B_ = AB(f)
        blk = {uname(u): round(t, 1) for u, t in hits.items() if u not in (A_, B_)}
        pa, aa = np.array(g["seat_world"]), np.array(f["axis_world"])
        d, e1, e2 = frame(-aa)
        c = pa + d * (f["head"]["k"] + 15.9)
        Dd = np.array([math.cos(t) * e1 + math.sin(t) * e2 for t in np.linspace(0, 2 * math.pi, 36, endpoint=False)])
        o, ray, t = cast(Mp, ownp, np.tile(c, (36, 1)), Dd)
        free = np.ones(36, bool)
        for oi, ri, ti in zip(o, ray, t):
            if 0 < ti < 80.3:
                free[ri] = False
        best, run = 0, 0
        for v in np.r_[free, free]:
            run = run + 1 if v else 0
            best = max(best, min(run, 36))
        outp[f["id"]] = dict(first=round(first, 1), blk=blk, short_arm_swing_deg=best * 10)
    serv["lid_screws_pull_%d" % pull] = outp
    del Mp, ownp, Vs, Fs, own
    print("pull", pull, json.dumps(outp))
Mmod, ownmod = build(keys=modkeys)
O = np.tile(xt, (len(ico), 1))
o, ray, t = cast(Mmod, ownmod, O, np.asarray(ico, float))
hm = collections.defaultdict(set)
for oi, ri, ti in zip(o, ray, t):
    if ti > 0.3:
        hm[ri].add(UNIT[OBKEY[oi]])
hlm = [hm.get(i, set()) for i in range(len(ico))]
serv["xt30_module_only"] = dict(module=sorted(uname(UNIT[k]) for k in modkeys),
                                open=round(sum(1 for h in hlm if not h) / len(hlm), 3),
                                open_forward=round(sum(1 for h, v in zip(hlm, ico) if not h and v[0] > 0.5) /
                                                   max(1, sum(1 for v in ico if v[0] > 0.5)), 3),
                                greedy=greedy(hlm, 3))
cell_c = np.array(S.mesh(byname["cell"][0]).bounds.mean(0))
hl = access(cell_c)
serv["cell"] = dict(point=cell_c.round(1).tolist(), open_built=round(sum(1 for h in hl if not h) / len(hl), 3),
                    greedy=greedy(hl, 5))

# Pi bodies
pi_k = [k for k in OBST if nm(k) == "raspberrypizerow"][0]
pim = S.mesh(pi_k)
pb = pim.bounds
bodies = []
for b in pim.split(only_watertight=False):
    e = b.bounds[1] - b.bounds[0]
    if e.max() > 3.0:
        bodies.append(dict(lo=b.bounds[0].round(2).tolist(), hi=b.bounds[1].round(2).tolist(), ext=e.round(2).tolist()))
bodies.sort(key=lambda x: -np.prod(x["ext"]))
serv["pi_bounds"] = pb.round(2).tolist()
serv["pi_bodies"] = bodies[:25]
ax = int(np.argmax(pb[1] - pb[0]))       # long axis
ay = [i for i in range(3) if i != ax and (pb[1] - pb[0])[i] > 10][0]
az = [i for i in range(3) if i not in (ax, ay)][0]


def near_end(b, axis, side):
    return abs((b["lo"] if side < 0 else b["hi"])[axis] - (pb[0] if side < 0 else pb[1])[axis]) < 3.0


sd = [b for b in bodies if 10 <= sorted(b["ext"])[2] <= 16 and 10 <= sorted(b["ext"])[1] <= 15
      and sorted(b["ext"])[0] <= 2.5 and (near_end(b, ax, -1) or near_end(b, ax, 1))]
usb = [b for b in bodies if 6.5 <= sorted(b["ext"])[2] <= 9 and 4.5 <= sorted(b["ext"])[1] <= 6.5
       and 2.0 <= sorted(b["ext"])[0] <= 3.5 and (near_end(b, ay, -1) or near_end(b, ay, 1))]
serv["pi_axes"] = dict(long=ax, short=ay, thick=az)
serv["sd_candidates"], serv["usb_candidates"] = sd, usb


def target(b, axis):
    side = -1 if near_end(b, axis, -1) else 1
    p = (np.array(b["lo"]) + np.array(b["hi"])) / 2
    p[axis] = (b["lo"] if side < 0 else b["hi"])[axis] + side * 0.6
    d = np.zeros(3)
    d[axis] = side
    return p, d


for tag, cands, axis, need in (("microsd", sd, ax, 15.0), ("usb", usb, ay, 20.0)):
    outl = []
    for b in cands:
        p, d = target(b, axis)
        O, D = bundle(p, d, 1.5)
        o, ray, t = cast(M0, own0, O, D)
        first = collections.defaultdict(lambda: 1e9)
        for oi, ti in zip(o, t):
            if ti > 0.05:
                u = UNIT[OBKEY[oi]]
                first[u] = min(first[u], float(ti))
        cone = [v for v in ico if np.dot(v, d) > math.cos(math.radians(60))]
        hl = access(p, cone)
        outl.append(dict(point=p.round(2).tolist(), dir=d.tolist(),
                         along_axis={uname(u): round(t, 1) for u, t in sorted(first.items(), key=lambda x: x[1])[:6]},
                         cone60_open_built=round(sum(1 for h in hl if not h) / len(hl), 3),
                         greedy=greedy(hl, 4)))
    serv[tag] = outl
sl = {}
for x in (3.5, 6, 9, 13, 20, 33, 45, 55, 60, 64, 67.5):
    sec = pim.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0])
    if sec is not None:
        sb = sec.bounds
        sl[x] = dict(y=[round(sb[0][1], 1), round(sb[1][1], 1)], z=[round(sb[0][2], 1), round(sb[1][2], 1)])
for yv in (32.5, 34, 36, 60, 62.5):
    sec = pim.section(plane_origin=[0, yv, 0], plane_normal=[0, 1, 0])
    if sec is not None:
        sb = sec.bounds
        sl["y%.1f" % yv] = dict(x=[round(sb[0][0], 1), round(sb[1][0], 1)], z=[round(sb[0][2], 1), round(sb[1][2], 1)])
serv["pi_slices"] = sl
for tag, p, d in (("microsd", np.array([2.0, 48.1, 223.8]), np.array([-1.0, 0, 0])),
                  ("usb_edge", np.array([20.6, 31.25, 223.1]), np.array([0, -1.0, 0]))):
    O, D = bundle(p, d, 1.5)
    o, ray, t = cast(M0, own0, O, D)
    first = collections.defaultdict(lambda: 1e9)
    for oi, ti in zip(o, t):
        if ti > 0.05:
            u = UNIT[OBKEY[oi]]
            first[u] = min(first[u], float(ti))
    cone = [v for v in ico if np.dot(v, d) > math.cos(math.radians(60))]
    hl = access(p, cone)
    serv[tag] = dict(point=p.tolist(), dir=d.tolist(),
                     along_axis={uname(u): round(t, 1) for u, t in sorted(first.items(), key=lambda x: x[1])[:6]},
                     cone60_open_built=round(sum(1 for h in hl if not h) / len(hl), 3), greedy=greedy(hl, 4))
    hb = byname["head_bot_sheet"][0]
    cone_all = [v for v in ico]
    hl2 = access(p, cone_all)
    serv[tag]["open_any_dir_bot_sheet_off"] = round(sum(1 for h in hl2 if h <= {hb}) / len(hl2), 3)
    serv[tag]["open_any_dir_built"] = round(sum(1 for h in hl2 if not h) / len(hl2), 3)
    print(tag, json.dumps(serv[tag]))
serv["head_bot_sheet_screws_built"] = {f["id"]: dict(spec=f["spec"], into=f["into"], tool=cast0[f["id"]]["tool"],
                                                     blk={uname(u): round(t, 1) for u, t in cast0[f["id"]]["blk"].items()})
                                       for f in SCREWS if "head_bot_sheet" in (f["part"], f["into"])}
serv["head_roll_mount_screws_built"] = {f["id"]: dict(spec=f["spec"], into=f["into"], tool=cast0[f["id"]]["tool"],
                                                      blk={uname(u): round(t, 1) for u, t in cast0[f["id"]]["blk"].items()})
                                        for f in SCREWS if f["part"] == "head_roll_mount" and f["into"] == "head"}
print("hbs", json.dumps(serv["head_bot_sheet_screws_built"])[:1500])
print("hrm", json.dumps(serv["head_roll_mount_screws_built"])[:800])
print("xt30_module_only", json.dumps(serv["xt30_module_only"]))
serv["n_pi_bodies"] = len(bodies)
print("pi bodies", len(bodies), json.dumps(bodies[:14]))
print("pi slices", json.dumps(sl))
res["service"] = serv
print(json.dumps({k: v for k, v in serv.items() if k not in ("pi_bodies",)}, indent=None, default=str)[:6000])

# ------------------------------------------------------------------ D29 eyes
Th = S.Th
eyes = {}
for k in [k for k in OBST if nm(k) == "bulb"]:
    bmesh = S.mesh(k)
    lo, hi = bmesh.bounds
    side = "left" if lo[1] > 0 else "right"
    yc, zc = (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2
    ys = np.arange(-19, 19.01, 0.5)
    G = np.array([[60.0, yc + a, zc + b] for a in ys for b in ys])
    D = np.tile([1.0, 0, 0], (len(G), 1))
    o, ray, t = cast(M0, own0, G, D, maxhits=40)
    per = collections.defaultdict(list)
    for oi, ri, ti in zip(o, ray, t):
        per[ri].append((60.0 + ti, uname(UNIT[OBKEY[oi]])))
    grid = []
    for i, (a, b) in enumerate([(a, b) for a in ys for b in ys]):
        hs = sorted(per.get(i, []))
        names = [h[1].split("#")[0] for h in hs]
        behind = [x for x, n_ in hs if x < lo[0] - 0.05 and not n_.startswith("bulb")]
        grid.append(dict(dy=float(a), dz=float(b), r=float(math.hypot(a, b)), bulb="bulb" in names,
                         head=any(n_ == "head" and lo[0] - 1 < x < hi[0] + 6 for x, n_ in [(x, n.split("#")[0]) for x, n in hs]),
                         eye=any(n_.endswith("_eye") for n_ in names),
                         behind_free=float(lo[0] - max(behind)) if behind else 36.0,
                         names=names[:6]))

    def open_radius(key):
        bad = [g["r"] for g in grid if g[key]]
        return min(bad) if bad else 19.0
    bulb_open = [g for g in grid if not g["bulb"] and g["r"] < 17.5]
    bulb_hole_r = min(g["r"] for g in grid if g["bulb"])
    eyes[side] = dict(bulb_bounds=[lo.round(2).tolist(), hi.round(2).tolist()], centre=[round(yc, 2), round(zc, 2)], bulb_centre_hole_r=bulb_hole_r, bulb_k=k,
                      bulb_open_points=len(bulb_open), bulb_open_r_max=max([g["r"] for g in bulb_open], default=0),
                      head_window_r=open_radius("head"), eye_window_r=open_radius("eye"),
                      behind_free_min_r10=min(g["behind_free"] for g in grid if g["r"] <= 10),
                      behind_free_min_r14=min(g["behind_free"] for g in grid if g["r"] <= 14),
                      sample_centre=[g for g in grid if g["r"] == 0][0])
res["eyes"] = eyes
print("eyes", json.dumps(eyes))

# ------------------------------------------------------------------ D30 button: body_back cutout
sw_k = [k for k in OBST if nm(k) == "power_switch"][0]
swm = S.mesh(sw_k)
V = np.asarray(swm.vertices)
c0 = V.mean(0)
_, sv, Vt = np.linalg.svd(V - c0, full_matrices=False)
ext = [(V - c0) @ Vt[i] for i in range(3)]
spans = [e.max() - e.min() for e in ext]
order_ = np.argsort(spans)          # smallest .. largest
iw, idp, il = order_[0], order_[1], order_[2]   # width 7.4, depth 16.8, length 23.4
n_ = Vt[idp].copy()
e_ = ext[idp]
lo_end = np.abs(((V - c0) @ Vt[il])[e_ < e_.min() + 1.0]).max()
hi_end = np.abs(((V - c0) @ Vt[il])[e_ > e_.max() - 1.0]).max()
if lo_end < hi_end:                  # flange (long) end must be at the low end of n_
    n_ = -n_
    e_ = -e_
pf = c0 + n_ * e_.min()              # flange end plane point
u_, v_ = Vt[il], Vt[iw]
bbm = S.mesh(byname["body_back"][0])
G, us_, vs_ = [], np.arange(-15, 15.01, 0.25), np.arange(-7, 7.01, 0.25)
for a in us_:
    for b in vs_:
        G.append(pf - n_ * 10 + a * u_ + b * v_)
G = np.array(G)
tri, ray, loc = bbm.ray.intersects_id(G, np.tile(n_, (len(G), 1)), multiple_hits=True, max_hits=10, return_locations=True)
tt = collections.defaultdict(list)
for ri, L_ in zip(ray, loc):
    tt[ri].append(float(np.dot(L_ - G[ri], n_)) - 10)
cells = []
for i, (a, b) in enumerate([(a, b) for a in us_ for b in vs_]):
    h = sorted(tt.get(i, []))
    near = [x for x in h if -6 < x < 12]
    cells.append(dict(u=float(a), v=float(b), open=not near, wall=(near[1] - near[0]) if len(near) >= 2 else None,
                      face=near[0] if near else None))
opn = [c for c in cells if c["open"]]
cu = [c["u"] for c in opn if abs(c["v"]) < 0.3]
cv = [c["v"] for c in opn if abs(c["u"]) < 0.3]
rim = [c["wall"] for c in cells if c["wall"] and not c["open"] and abs(c["v"]) < 5 and abs(c["u"]) < 13]
# free depth behind the cutout, every part but the switch itself
Gi = np.array([pf + a * u_ + b * v_ for a in np.arange(-7, 7.01, 1.0) for b in np.arange(-3, 3.01, 1.0)])
o, ray, t = cast(M0, own0, Gi, np.tile(n_, (len(Gi), 1)))
depth = collections.defaultdict(lambda: 99.0)
who = {}
for oi, ri, ti in zip(o, ray, t):
    if OBKEY[oi] == sw_k or ti < 1.0:
        continue
    if ti < depth[ri]:
        depth[ri], who[ri] = float(ti), uname(UNIT[OBKEY[oi]])
dmin = min(depth[i] for i in range(len(Gi)))
res["button"] = dict(switch_spans=[round(float(s), 2) for s in spans], axis_in=n_.round(3).tolist(),
                     flange_point=pf.round(2).tolist(), cutout_u=[min(cu), max(cu)] if cu else None,
                     cutout_v=[min(cv), max(cv)] if cv else None, open_cells=len(opn),
                     rim_wall_mm=[round(float(np.min(rim)), 2), round(float(np.median(rim)), 2)] if rim else None,
                     free_depth_min=round(dmin, 1), free_depth_by=collections.Counter(who.values()).most_common(4),
                     free_depth_median=round(float(np.median([depth[i] for i in range(len(Gi))])), 1))
faces_ = [c["face"] for c in cells if not c["open"] and c["face"] is not None and abs(c["u"]) <= 12.5 and abs(c["v"]) <= 6.0]
t_face = float(np.median(faces_))
fl = [c["face"] for c in cells if not c["open"] and c["face"] is not None and abs(c["u"]) <= 11.7 and abs(c["v"]) <= 5.5]
best_r = (0, 0)
for uh in np.arange(5.0, 12.01, 0.25):
    for vh in np.arange(2.0, 5.01, 0.25):
        cs = [c for c in cells if abs(c["u"]) <= uh and abs(c["v"]) <= vh]
        if all(c["open"] for c in cs) and uh * vh > best_r[0] * best_r[1]:
            best_r = (float(uh), float(vh))
res["button"]["open_rect_half_uv"] = best_r
PU, PV = 2 * best_r[0] - 0.5, 2 * best_r[1] - 0.5            # 0.25 mm clearance per side
plug_cells = [c for c in cells if abs(c["u"]) <= PU / 2 and abs(c["v"]) <= PV / 2]
res["button"]["outer_face_t"] = round(t_face, 2)
res["button"]["flange_23p4x11_face_spread"] = [round(float(np.min(fl)) - t_face, 2), round(float(np.max(fl)) - t_face, 2)]
res["button"]["plug_19x6p6_cells_open"] = [sum(1 for c in plug_cells if c["open"]), len(plug_cells)]
try:
    Rm = np.eye(4)
    Rm[:3, 0], Rm[:3, 1], Rm[:3, 2] = u_, v_, n_
    plug = trimesh.creation.box(extents=[PU, PV, 3.0])
    res["button"]["plug_uv_mm"] = [round(PU, 2), round(PV, 2)]
    plug.apply_translation([0, 0, t_face + 1.5])
    flange = trimesh.creation.box(extents=[23.4, 11.0, 1.5])
    flange.apply_translation([0, 0, t_face - 0.75])
    hole = trimesh.creation.cylinder(radius=3.2, height=20.0)
    plate = trimesh.boolean.difference([trimesh.boolean.union([plug, flange], engine="manifold"), hole], engine="manifold")
    Rm[:3, 3] = pf
    plate.apply_transform(Rm)
    pfn = os.path.join(HERE, "button_plate_d30.stl")
    plate.export(pfn)
    Mbb, obb = build(keys={k for k in OBKEY if k != sw_k})
    inter = trimesh.proximity.signed_distance(Mbb, plate.vertices[:: max(1, len(plate.vertices) // 400)]) if False else None
    # interference: plate vertices inside other parts (ray parity along +n)
    P = plate.vertices
    tri, ray, loc = Mbb.ray.intersects_id(P - n_ * 0.0, np.tile(n_, (len(P), 1)), multiple_hits=True, max_hits=40,
                                          return_locations=True)
    res["button"]["plate_file"] = pfn
    res["button"]["plate_volume_mm3"] = round(float(plate.volume), 1)
    res["button"]["plate_watertight"] = bool(plate.is_watertight)
except Exception as ex:   # noqa: BLE001
    res["button"]["plate_error"] = repr(ex)
print("button", json.dumps(res["button"]))

# ------------------------------------------------------------------ speaker pocket
st = [k for k in OBST if nm(k) in ("speaker_stand", "speaker_interface")]
lo = np.min([S.mesh(k).bounds[0] for k in st], axis=0)
hi = np.max([S.mesh(k).bounds[1] for k in st], axis=0)
Mspk, owns = build(keys=set(st))
pts = np.array([[x, y, z] for x in np.arange(lo[0] + 1, hi[0], 2.0) for y in np.arange(lo[1] + 1, hi[1], 2.0)
                for z in np.arange(lo[2] + 1, hi[2], 2.0)])
dirs6 = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]], float)
enc = []
for d in dirs6:
    tri, ray, loc = Mspk.ray.intersects_id(pts, np.tile(d, (len(pts), 1)), multiple_hits=False, return_locations=True)
    h = np.full(len(pts), np.inf)
    h[ray] = np.einsum("ij,ij->i", loc - pts[ray], np.tile(d, (len(ray), 1)))
    enc.append(h)
enc = np.array(enc)              # 6 x n
closed = np.all(enc < 30, axis=0)
# exclude points inside material: odd parity along +x
tri, ray, loc = Mspk.ray.intersects_id(pts, np.tile([1.0, 0, 0], (len(pts), 1)), multiple_hits=True, max_hits=20,
                                       return_locations=True)
par = np.bincount(ray, minlength=len(pts)) % 2
cav = closed & (par == 0)
pc = pts[cav]
res["speaker_pocket"] = dict(n_points=int(cav.sum()), lo=pc.min(0).round(1).tolist() if len(pc) else None,
                             hi=pc.max(0).round(1).tolist() if len(pc) else None,
                             open_sides_at_centre=None)
if len(pc):
    c = pc.mean(0)
    hs = []
    for d in dirs6:
        tri, ray, loc = Mspk.ray.intersects_id(c[None], d[None], multiple_hits=False, return_locations=True)
        hs.append(round(float(np.dot(loc[0] - c, d)), 1) if len(loc) else None)
    res["speaker_pocket"]["centre"] = c.round(1).tolist()
    res["speaker_pocket"]["wall_dist_xyz_pm"] = hs
if len(pc):
    c = (pc.min(0) + pc.max(0)) / 2
    ext = pc.max(0) - pc.min(0) + 2.0
    thin = int(np.argmin(ext))
    box = np.array([36.0, 36.0, 36.0])
    box[thin] = 14.5                        # BOM E1 Same Sky CMS0361KLX 36 x 36 x 14.5 mm
    Mall = M0
    faces = {}
    for ax_ in range(3):
        for sg in (-1, 1):
            n = np.zeros(3)
            n[ax_] = sg
            o_ = [i for i in range(3) if i != ax_]
            P = []
            for a_ in np.linspace(-0.45, 0.45, 7):
                for b_ in np.linspace(-0.45, 0.45, 7):
                    q = c.copy()
                    q[ax_] += sg * box[ax_] / 2
                    q[o_[0]] += a_ * box[o_[0]]
                    q[o_[1]] += b_ * box[o_[1]]
                    P.append(q)
            P = np.array(P)
            o, ray, t = cast(Mall, own0, P, np.tile(n, (len(P), 1)))
            gap = {}
            for oi, ri, ti in zip(o, ray, t):
                if ti > -0.01:
                    gap[ri] = min(gap.get(ri, 99), ti)
                    gap[(ri, "who")] = uname(UNIT[OBKEY[oi]]) if gap[ri] == ti else gap.get((ri, "who"))
            g_ = [gap.get(i, 99) for i in range(len(P))]
            who_ = collections.Counter(gap.get((i, "who")) for i in range(len(P)) if gap.get(i, 99) < 3)
            faces["%s%s" % ("+" if sg > 0 else "-", "xyz"[ax_])] = dict(covered_within_3mm=round(sum(1 for x in g_ if x < 3) / len(g_), 2),
                                                                         median_gap=round(float(np.median(g_)), 2), by=who_.most_common(3))
    res["speaker_pocket"]["box_centre"] = c.round(1).tolist()
    res["speaker_pocket"]["faces"] = faces
print("speaker", json.dumps(res["speaker_pocket"]))
try:
    import manifold3d  # noqa: F401
    have_manifold = True
except Exception:
    have_manifold = False
res["manifold3d"] = have_manifold
# side projector lamp (stock, D33): contact of flash_light_module with the head shell, the only support it has
fk = [k for k in OBST if nm(k) == "flash_light_module"][0]
rk = [k for k in OBST if nm(k) == "flash_reflector_interface"][0]
hk_ = [k for k in OBST if nm(k) == "head"][0]
fm, hm_, rm_ = S.mesh(fk), S.mesh(hk_), S.mesh(rk)
cen = fm.triangles_center
_, dist, _ = trimesh.proximity.closest_point(hm_, cen)
area = fm.area_faces
res["side_lamp"] = dict(contact_area_mm2_within_0p3=round(float(area[dist < 0.3].sum()), 1),
                        contact_area_mm2_within_1p0=round(float(area[dist < 1.0].sum()), 1),
                        min_gap_mm=round(float(dist.min()), 3), module_bounds=fm.bounds.round(1).tolist())
_, d2, _ = trimesh.proximity.closest_point(fm, rm_.triangles_center)
res["side_lamp"]["reflector_interface_contact_mm2_within_0p3"] = round(float(rm_.area_faces[d2 < 0.3].sum()), 1)
print("side_lamp", res["side_lamp"])

json.dump(res, open(os.path.join(OUT, "asm_geom.json"), "w"), default=str)
summ = dict(verify=res["verify"], driven=len(SCREWS), clear_all_present=n_clear, self_blocks=res["self_blocks"], fixes=res["fixes"],
            fails=res["fails"], side_lamp=res.get("side_lamp"), pre_joined=res["pre_joined"], eyes=eyes, button=res["button"], speaker_pocket=res["speaker_pocket"],
            service={k: v for k, v in serv.items() if k not in ("pi_bodies",)}, tools=TOOLS)
json.dump(summ, open(os.path.join(HERE, "asm_geom_summary.json"), "w"), indent=1, default=str)
print("wrote", os.path.join(OUT, "asm_geom.json"))
