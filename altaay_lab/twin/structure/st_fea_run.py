"""Structure twin: FEA studies of printed parts under the sim loads (FEA pass only, loads sim pass only).

Each study: the printed part(s) of one link, bonded where they are screwed together (st_fea.Part), fixed where they
hold the next servo's case (nodes within 0.3 mm of its case meshes and its case screw holes), and loaded at the
screw holes of the horns (or the bearing boss, or the case screws) through which the joint load enters, with the
two-support split of st_interfaces.split (drive horn: its share of the radial force, the full axial force and the
full axis torque; idle horn or bearing: its share of the radial force). Unit loads are solved once per active load
component; each sim sample is a linear combination of them, so the peak failure index over a whole history and
the stress history at the critical element (fatigue) come from the same solves.
Run: ODM_SCRATCH=... nice -n 10 python3 altaay_lab/twin/structure/st_fea_run.py <study> <level> [level ...]
(mesh levels of st_fea.Part.LEVELS: 1 coarse, 2 medium, 3 fine); checks: st_fea_run.py conv <study> 1 2 3 (mesh
convergence, into fea_conv/), st_fea_run.py avgcheck <study> (stress averaging radius), st_fea_run.py sheetlocal
(knee sheet eye alone under a unit knee torque, levels 1 to 3)
"""
import os, sys, json, glob, time
import numpy as np
import trimesh, yourdfpy
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import st_fea as FE
import st_interfaces as SI

SCR = os.environ.get("ODM_SCRATCH", "/tmp/odm_twin_structure")
OUT = os.path.join(SCR, "fea"); os.makedirs(OUT, exist_ok=True)
URDF_DIR = os.path.join(FE.REPO, "mini_bdx/robots/open_duck_mini_v2")
SERVO = ("wj-wk00-0123middlecase_56.stl", "wj-wk00-0124bottomcase_45.stl", "wj-wk00-0122topcabinetcase_95.stl")
PRINT_NAME = {"left_knee_to_ankle_left_sheet": "knee_to_ankle_left_sheet", "left_knee_to_ankle_right_sheet": "knee_to_ankle_right_sheet"}
_U = [None]
def urdf():
    if _U[0] is None: _U[0] = yourdfpy.URDF.load(os.path.join(URDF_DIR, "robot.urdf"), load_meshes=False, build_scene_graph=True)
    return _U[0]

def visual_T(link, part):
    for v in urdf().link_map[link].visuals:
        fn = os.path.basename(v.geometry.mesh.filename)[:-4]
        if PRINT_NAME.get(fn, fn) == part:
            T = np.array(v.origin, float).copy(); T[:3, 3] *= 1000.0; return T
    raise KeyError((link, part))

def joint_in_link(link, joint):
    """4x4 (mm) of the joint (child) frame at q = 0 in 'link'"""
    jt = urdf().joint_map[joint]
    if link == jt.child: return np.eye(4)
    T = np.array(jt.origin, float).copy(); T[:3, 3] *= 1000.0; return T

def servo_meshes(link, near_mm):
    out = []
    for v in urdf().link_map[link].visuals:
        fn = os.path.basename(v.geometry.mesh.filename)
        if fn in SERVO:
            m = trimesh.load(os.path.join(URDF_DIR, fn), force="mesh"); m.apply_scale(1000.0)
            T = np.array(v.origin, float).copy(); T[:3, 3] *= 1000.0; m.apply_transform(T)
            if np.linalg.norm(m.centroid - near_mm) < 80: out.append(m)
    return out

def near_surface(meshes, pts, spacing=0.08):
    S = [trimesh.sample.sample_surface(m, int(min(4e6, max(2e4, m.area / spacing ** 2))))[0] for m in meshes]
    return cKDTree(np.vstack(S)).query(pts)[0]

def hole_nodes(P, screws, r_hole):
    out = []
    for x in screws:
        c = np.array(x["seat_link"], float); a = np.array(x["axis_link"], float); a /= np.linalg.norm(a)
        out.append(P.nodes_near_hole(c + a * x["near"] / 2.0, a, r_hole, x["near"] / 2.0 + 0.3, face_r=r_hole + 1.4))
    return np.unique(np.concatenate(out)) if out else np.array([], int)

# active components per group: index into (Fx, Fy, Fz, Mx, My, Mz) of the group's load in the joint frame
STUDIES = {
    # D59 moved the shin plates to shin_left_sheet / shin_right_sheet / shin_spacer. The knee sheet eye is on shin_left_sheet.
    "shin_segment": dict(link="knee_and_ankle_assembly_2", members=["shin_left_sheet", "shin_right_sheet", "shin_spacer"],
                         grow={"shin_spacer": ((0, 0, 1), 0.3)},
                         loads=[("left_knee", "drive", [0, 1, 2, 5]), ("left_knee", "idle", [0, 1])], fix_servo_of="left_ankle"),
    "thigh_segment": dict(link="knee_and_ankle_assembly", members=["knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet", "leg_spacer"],
                          grow={"leg_spacer": ((0, 0, 1), 0.3)},
                          loads=[("left_hip_pitch", "drive", [0, 1, 2, 5]), ("left_hip_pitch", "idle", [0, 1])], fix_servo_of="left_knee"),
    "roll_to_pitch": dict(link="left_roll_to_pitch_assembly", members=["left_roll_to_pitch"],
                          loads=[("left_hip_roll", "drive", [0, 1, 2, 5]), ("left_hip_roll", "idle", [0, 1])], fix_servo_of="left_hip_pitch"),
    "hip_roll_stage": dict(link="hip_roll_assembly", members=["roll_motor_top", "roll_motor_bottom"],
                           loads=[("left_hip_yaw", "drive", [0, 1, 2, 5]), ("left_hip_yaw", "bearing", [0, 1])], fix_servo_of="left_hip_roll"),
    "foot": dict(link="foot_assembly", members=["foot_top"],
                 loads=[("left_ankle", "drive", [0, 1, 2, 5])], fix_face_of=["foot_bottom_pla", "foot_side"],
                 simplify={"foot_top": 0.01}),     # the STL has a 0.003 mm edge and 310 needle triangles: unsimplified, 70 % of the tets are under 1e-4 mm3 and CG stalls
    "neck_sheets": dict(link="neck_pitch_assembly", members=["neck_left_sheet", "neck_right_sheet"],
                        loads=[("neck_pitch", "drive", [0, 1, 2, 5]), ("neck_pitch", "idle", [0, 1])], fix_servo_of="head_pitch"),
    "head_roll_mount": dict(link="head_assembly", members=["head_roll_mount"],
                            loads=[("head_roll", "drive_via_case", [0, 1, 2, 5])], fix_inserts=True),
}
# proposal studies: the same loads and supports with another print profile on the weak part (STRUCTURE_TWIN.md section 6)
STUDIES["roll_to_pitch_w4i40"] = dict(STUDIES["roll_to_pitch"], prof_over={"left_roll_to_pitch": dict(walls=4, infill=0.40)})
STUDIES["roll_to_pitch_w3"] = dict(STUDIES["roll_to_pitch"], prof_over={"left_roll_to_pitch": dict(walls=3)})                # its profile before D22
STUDIES["roll_to_pitch_w6i40"] = dict(STUDIES["roll_to_pitch"], prof_over={"left_roll_to_pitch": dict(walls=6, infill=0.40)})  # the 5 mm walls print solid
STUDIES["roll_to_pitch_upx"] = dict(STUDIES["roll_to_pitch"], prof_over={"left_roll_to_pitch": dict(up="+x")})   # hip roll axis vertical
STUDIES["roll_to_pitch_upy"] = dict(STUDIES["roll_to_pitch"], prof_over={"left_roll_to_pitch": dict(up="+y")})   # link x vertical: the wall between the ears lies flat
STUDIES["shin_segment_w5i40"] = dict(STUDIES["shin_segment"], prof_over={"shin_left_sheet": dict(walls=5, infill=0.40),
                                                                         "shin_right_sheet": dict(walls=5, infill=0.40)})

def hole_cylinders(link, names):
    """Screw holes and horn hubs kept open in a voxel mesh (D39: a hole that has a screw stays open). Link frame, mm."""
    F = SI.fasteners(); holes = []; horns = {}
    for x in F:
        if x.get("link") != link or x.get("part") not in names: continue
        anc = x.get("anchor") or ""
        if anc not in ("horn(drive)", "horn(passive)", "servo pilot", "M3 insert"): continue
        a = np.array(x["axis_link"], float); n = np.linalg.norm(a)
        if n < 1e-9: continue
        a = a / n; c = np.array(x["seat_link"], float)
        r = 1.7 if anc != "servo pilot" else 1.25
        holes.append((c + a * float(x.get("near") or 2.0) / 2.0, a, r, float(x.get("near") or 2.0) / 2.0 + 1.2))
        if anc.startswith("horn"):
            horns.setdefault((x.get("servo"), anc), []).append((c, a))
    for pts in horns.values():
        if len(pts) < 3: continue
        C = np.mean([p[0] for p in pts], 0); A = np.mean([p[1] for p in pts], 0); A = A / np.linalg.norm(A)
        holes.append((C, A, 3.6, 6.0))          # the 7 mm horn hub
    return holes

def setup(name, maxvol):
    st = STUDIES[name]; link = st["link"]; G = SI.groups(); F = SI.fasteners()
    members = [(p, visual_T(link, p)) for p in st["members"]]
    rings = []
    for p, T in members:
        if FE.profile_of(p)["rings"] == "insert":
            for x in F:
                if x["kind"] == "insert" and x["into"] == p and x["link"] == link:
                    a = np.array(x["axis_link"], float); c = np.array(x["seat_link"], float) + a * x["bore_len"] / 2
                    rings.append((c, a / np.linalg.norm(a), x["bore_d"] / 2 + 2.0, x["bore_len"] / 2 + 0.6))
    voxel = os.environ.get("ST_VOXEL_MM")
    voxel_mm = float(voxel) if voxel else None
    holes = hole_cylinders(link, st["members"]) if voxel_mm else ()
    P = FE.Part(members, level=int(maxvol), rings=rings, grow=st.get("grow"), prof_over=st.get("prof_over"), simplify=st.get("simplify"),
                voxel_mm=voxel_mm, holes=holes); P.material(); P.assemble()
    groups = []
    for (j, kind, comps) in st["loads"]:
        g = G[j]; JT = joint_in_link(link, j); R = JT[:3, :3]; o = JT[:3, 3]
        if kind == "bearing":
            z = g["idle"]["z"]; c = R @ np.array([0, 0, z]) + o; a = R @ np.array([0, 0, 1.0])
            nodes = P.nodes_near_hole(c, a, 10.0, 3.6)         # the boss in the 6804 inner race (bore 20 mm, width 7 mm)
            ref = c; scr = ["6804 boss"]
        elif kind == "drive_via_case":
            xs = [x for x in F if x["anchor"] == "servo pilot" and x.get("servo") == j and x["link"] == link]
            nodes = hole_nodes(P, xs, 1.25); ref = R @ np.array([0, 0, g["drive"]["z"]]) + o; scr = [x["id"] for x in xs]
        else:
            anc = "horn(drive)" if kind == "drive" else "horn(passive)"
            xs = [x for x in F if x["anchor"] == anc and x.get("servo") == j and x["link"] == link]
            nodes = hole_nodes(P, xs, 1.6); scr = [x["id"] for x in xs]
            ref = np.mean([np.array(x["seat_link"]) + np.array(x["axis_link"]) * x["near"] for x in xs], axis=0)
        groups.append(dict(joint=j, kind=kind, comps=comps, nodes=nodes, ref=ref, R=R, screws=scr))
    fix = []
    if st.get("fix_servo_of"):
        js = st["fix_servo_of"]; near = joint_in_link(link, js)[:3, 3]
        sn = np.nonzero(P.surface_nodes())[0]
        fix.append(sn[near_surface(servo_meshes(link, near), P.X[sn]) < 0.3])
        cs = [x for x in F if x["anchor"] == "servo pilot" and x.get("servo") == js and x["link"] == link]
        if cs: fix.append(hole_nodes(P, cs, 1.25))
    if st.get("fix_face_of"):
        for o in (st["fix_face_of"] if isinstance(st["fix_face_of"], (list, tuple)) else [st["fix_face_of"]]):
            m = trimesh.load(os.path.join(FE.PRINT, o + ".stl"), force="mesh"); m.apply_transform(visual_T(link, o))
            sn = np.nonzero(P.surface_nodes())[0]; fix.append(sn[near_surface([m], P.X[sn]) < 0.3])
    if st.get("fix_inserts"):
        xs = [x for x in F if x["anchor"] == "M3 insert" and x["link"] == link and x["part"] in st["members"]]
        fix.append(hole_nodes(P, xs, 1.8))
    fixed = np.unique(np.concatenate(fix))
    return P, dict(groups=groups, fixed=fixed, study=st)

def insert_groups(P, S):
    """tie pairs grouped by the nearest M3 insert axis (within 6 mm) of the members (fasteners.json, link frame)"""
    F = SI.fasteners(); link = S["study"]["link"]; names = [M["name"] for M in P.members]
    ins = [x for x in F if x["kind"] == "insert" and x["link"] == link and x["into"] in names]
    pairs = P.ties() if len(P.members) > 1 else np.zeros((0, 2), int)
    if not len(ins) or not len(pairs): return [], pairs, np.array([], int)
    mid = 0.5 * (P.X[pairs[:, 0]] + P.X[pairs[:, 1]]); grp = np.full(len(pairs), -1)
    best = np.full(len(pairs), 6.0)
    for k, x in enumerate(ins):
        c = np.array(x["seat_link"], float); a = np.array(x["axis_link"], float); a /= np.linalg.norm(a)
        d = mid - c; rad = np.linalg.norm(d - np.outer(d @ a, a), axis=1)
        take = rad < best; best[take] = rad[take]; grp[take] = k
    return ins, pairs, grp

def solve_units(P, S):
    sig = []; S["solve_s"] = 0.0; S["u_unit_max_mm"] = []; S["tie_unit"] = []
    ins, pairs, grp = insert_groups(P, S); S["inserts"] = [dict(id=x["id"], into=x["into"], screw=x.get("screw"), axis=x["axis_link"]) for x in ins]
    for gr in S["groups"]:
        for k in gr["comps"]:
            e = np.zeros(6); e[k] = 1.0
            Fl = gr["R"] @ e[:3]; Ml = gr["R"] @ (e[3:] * 1000.0)   # unit: 1 N, or 1 N m given in N mm
            P.solve([(gr["nodes"], Fl, Ml, gr["ref"])], S["fixed"]); sig.append(P.stress_print())
            if len(ins):
                fpair = P.k_tie * (P.u[pairs[:, 0]] - P.u[pairs[:, 1]])     # force of member b on member a per pair, N
                S["tie_unit"].append(np.array([fpair[grp == k].sum(0) for k in range(len(ins))]))
            S["solve_s"] += P.solve_s; S["solver"] = P.solver; S["u_unit_max_mm"].append(float(np.abs(P.u).max()))
    sig = np.stack(sig)
    S["sig_raw"] = sig
    if AVG_MM > 0:
        W = FE.averaging_matrix(P, AVG_MM); sig = np.stack([W @ x for x in sig])
    return sig

PATTERNS = dict(walk=["loads/walk_forward*", "loads/turn_*", "loads/walk_side*", "loads/walk_backlash*", "loads/stand_*"],
                push=["loads/push1_*", "loads/walk_pushes_*"],
                fall=["falls/*_tc0.02_dr1", "falls/*_tc0.0158_dr0.2", "falls/*_tc0.005_dr0.2", "falls/*_tc0.00289_dr0.2"])

def history(S, which):
    """columns = the active components of every group, joint frame (N, N m)"""
    G = SI.groups(); names = []; rows = []
    for p in PATTERNS[which]:
        for f in sorted(glob.glob(os.path.join(SCR, p + ".npz"))):
            d = np.load(f, allow_pickle=True); nm = os.path.basename(f)[:-4]
            sel = np.ones(len(d["t"]), bool) if which == "fall" else SI.window(d, nm)
            if which != "fall": sel[1::2] = False
            if sel.sum() == 0: continue
            block = []
            for gr in S["groups"]:
                ji = SI.JOINTS.index(gr["joint"]); g = G[gr["joint"]]
                Fj = d["F"][sel, ji].astype(float); Tj = d["T"][sel, ji].astype(float)
                Rd, Ri, Fa, Mz, Mp = SI.split(Fj, Tj, g)
                L = np.zeros((len(Fj), 6))
                if gr["kind"] in ("drive", "drive_via_case"): L[:, :2] = Rd; L[:, 2] = Fa; L[:, 5] = Mz
                else: L[:, :2] = Ri
                block.append(L[:, gr["comps"]])
            rows.append(np.concatenate(block, axis=1)); names += [nm] * int(sel.sum())
    return (np.concatenate(rows) if rows else np.zeros((0, 1))), np.array(names)

ALT_STRENGTHS = {"makerZ": (47.1, 39.4, 39.4), "PETG": (34.0, 23.0, 23.0)}   # MPa: X, Z, S (sources in STRUCTURE_TWIN.md 2.2 and 5)
TIE_EXCL_MM = 2.0     # elements within 2 mm of a tie spring node are left out of the peak (the bonded joint is judged by its insert loads)
AVG_MM = float(os.environ.get("ST_AVG_MM", "1.0"))   # stress averaging radius for the failure index (st_fea.averaging_matrix); 0 = raw element peak

def evaluate(P, S, sig_u, hist, names, k_elem=1500, chunk=2000, strengths=(47.1, 22.0, 22.0)):
    """strengths: in-plane X, interlayer Z and interlayer shear S, MPa (default: PLA with the 22 MPa design value)"""
    c = P.X[P.T].mean(1)
    if not hasattr(P, "_ok_mask"):
        tie_nodes = np.unique(P.ties().ravel()) if len(P.members) > 1 else np.array([], int)
        excl = np.concatenate([np.concatenate([g["nodes"] for g in S["groups"]]), S["fixed"]])
        ok = cKDTree(P.X[excl]).query(c)[0] > 1.0                 # 1 mm off loaded and fixed nodes (point-like BCs)
        if len(tie_nodes): ok &= cKDTree(P.X[tie_nodes]).query(c)[0] > TIE_EXCL_MM
        P._ok_mask = ok
    ok = P._ok_mask
    key = id(sig_u)
    if getattr(P, "_mag_key", None) != key:
        P._mag = np.sqrt((sig_u[:, :, :3] ** 2).sum(-1) + 2 * (sig_u[:, :, 3:] ** 2).sum(-1)); P._mag_key = key
    mag = P._mag
    score = (mag * np.abs(hist).max(0)[:, None]).sum(0); score[~ok] = 0
    cand = np.argsort(score)[-k_elem:]; solid = P.zone[cand] != 3; rho = P.infill[cand]
    su = sig_u[:, cand, :].astype(np.float32)
    best = dict(s=(-1.0, 0, 0), i=(-1.0, 0, 0))
    for a in range(0, len(hist), chunk):
        sx = np.einsum("tk,kei->tei", hist[a:a + chunk].astype(np.float32), su)
        FI, vm, szz, tz, fv, fz = FE.failure_index(sx, solid[None, :], rho[None, :], *strengths)
        FIs = np.where(solid[None, :], FI, 0); FIi = np.where(~solid[None, :], FI, 0)
        for key, A in (("s", FIs), ("i", FIi)):
            t_, e_ = np.unravel_index(np.argmax(A), A.shape)
            if A[t_, e_] > best[key][0]: best[key] = (float(A[t_, e_]), a + t_, e_)
    fis, ts, es = best["s"]; el = cand[es]
    one = np.einsum("k,ki->i", hist[ts], sig_u[:, el, :])[None, :]
    FI, vm, szz, tz, fv, fz = FE.failure_index(one, np.array([True]), np.array([rho[es]]), *strengths)
    member = P.members[P.mem[el]]["name"]
    S3 = np.array([[one[0, 0], one[0, 5], one[0, 4]], [one[0, 5], one[0, 1], one[0, 3]], [one[0, 4], one[0, 3], one[0, 2]]])
    res = dict(FI=fis, sample=str(names[ts]), load=hist[ts].round(3).tolist(), mode="interlayer" if fz[0] > fv[0] else "in-plane",
               sig_print=one[0].round(2).tolist(), principal=np.linalg.eigvalsh(S3).round(2).tolist(),
               vm=float(vm[0]), szz=float(szz[0]), tz=float(tz[0]), zone=["wall", "top skin", "bottom skin", "infill", "ring"][int(P.zone[el])],
               member=member, where_link=c[el].round(1).tolist(), FI_infill=best["i"][0], element=int(el))
    sh = hist @ sig_u[:, el, :]
    _, v, z, t, _, _ = FE.failure_index(sh, np.ones(len(sh), bool), np.full(len(sh), rho[es]))
    return res, v.astype(np.float32), z.astype(np.float32), t.astype(np.float32)   # von Mises, interlayer tension and interlayer shear histories

def run(name, maxvols):
    out = dict(study=name, link=STUDIES[name]["link"], members=STUDIES[name]["members"], meshes=[])
    for mv in maxvols:
        t0 = time.time(); P, S = setup(name, mv); sig_u = solve_units(P, S)
        m = dict(maxvol=mv, avg_mm=AVG_MM, nodes=len(P.X), tets=len(P.T), mesh_s=round(P.mesh_s, 1), solver=S["solver"], solve_s=round(S["solve_s"], 1),
                 groups=[dict(joint=g["joint"], kind=g["kind"], n_nodes=int(len(g["nodes"])), screws=g["screws"]) for g in S["groups"]],
                 n_fixed=int(len(S["fixed"])), n_tie_pairs=int(getattr(P, "n_ties", 0)), zone_vol_mm3={k: round(v, 1) for k, v in P.zone_vol.items()},
                 member_vol_mm3={k: round(v, 1) for k, v in P.member_vol.items()}, u_unit_max_mm=S["u_unit_max_mm"], cases={})
        for which in ("walk", "push", "fall"):
            hist, names = history(S, which)
            if not len(hist): continue
            r, hv, hz, ht = evaluate(P, S, sig_u, hist, names)
            if which != "fall":                     # the same field with the maker interlayer value and with PETG strengths (whole part, not only the weak spot)
                r["alt"] = {}
                for lab, stg in ALT_STRENGTHS.items():
                    ra = evaluate(P, S, sig_u, hist, names, strengths=stg)[0]
                    r["alt"][lab] = dict(FI=ra["FI"], mode=ra["mode"], zone=ra["zone"], member=ra["member"], where_link=ra["where_link"], sample=ra["sample"])
            if AVG_MM > 0 and which != "fall":
                rr = evaluate(P, S, S["sig_raw"], hist, names, k_elem=800)[0]
                r["raw_element_peak"] = dict(FI=rr["FI"], mode=rr["mode"], zone=rr["zone"], member=rr["member"], where_link=rr["where_link"])
            if S.get("tie_unit"):
                TU = np.stack(S["tie_unit"])                               # (ncomp, nins, 3)
                Fi = np.einsum("tk,kij->tij", hist, TU)                    # (nt, nins, 3)
                il = {}
                for k, x in enumerate(S["inserts"]):
                    a = np.array(x["axis"], float); a /= np.linalg.norm(a); ax = Fi[:, k] @ a
                    sh = np.linalg.norm(Fi[:, k] - np.outer(ax, a), axis=1)
                    il[x["id"]] = dict(into=x["into"], pull_max=float(np.abs(ax).max()), shear_max=float(sh.max()))
                r["insert_loads"] = il
            if which != "fall" and mv == maxvols[-1]:
                np.savez_compressed(os.path.join(OUT, f"{name}_{which}_hist.npz"), vm=hv, szz=hz, tz=ht, names=names)
            if which == "fall":
                per = {}
                for nm in sorted(set(names)):
                    sel = names == nm; rr = evaluate(P, S, sig_u, hist[sel], names[sel], k_elem=800)[0]
                    per[nm] = dict(FI=rr["FI"], mode=rr["mode"], member=rr["member"], where_link=rr["where_link"], load=rr["load"])
                r["per_run"] = per
            m["cases"][which] = r
            print(f"{name} maxvol {mv} {which}: FI {r['FI']:.3f} (SF {1 / max(r['FI'], 1e-9):.2f}) {r['mode']} {r['zone']} of {r['member']} at {r['where_link']} "
                  f"({r['sample']}); infill FI {r['FI_infill']:.3f}", flush=True)
        m["wall_s"] = round(time.time() - t0, 1); out["meshes"].append(m)
        print(f"{name} maxvol {mv}: {len(P.X)} nodes {len(P.T)} tets, {S['solver']}, {m['wall_s']} s", flush=True)
        json.dump(out, open(os.path.join(OUT, f"{name}.json"), "w"), indent=1, default=float)
    return out

def avgcheck(name, radii=(0.5, 1.0, 1.5)):
    """averaging radius check at mesh level 1: SF walk, push and the soft and mid falls with the failure index on the
    element stress averaged over each radius (0 = the raw element peak). Writes ODM_SCRATCH/fea_conv/avgcheck_<study>.json.
    Run: st_fea_run.py avgcheck <study>"""
    global AVG_MM
    keep = AVG_MM; AVG_MM = 0.0
    P, S = setup(name, 1.0); sig_raw = solve_units(P, S); AVG_MM = keep
    c = P.X[P.T].mean(1); solid = P.zone != 3; tree = cKDTree(c)
    H = {w: history(S, w) for w in ("walk", "push", "fall")}
    out = dict(study=name, level=1, nodes=len(P.X), tets=len(P.T), rows=[])
    for r in (0.0,) + tuple(radii):
        k = 32 if r <= 1.0 else 96
        sig = sig_raw if r == 0 else np.stack([FE.averaging_matrix(P, r, k=k) @ x for x in sig_raw])
        row = dict(radius_mm=r, k_nearest=k if r else None)
        for which in ("walk", "push"):
            P._mag_key = None
            res = evaluate(P, S, sig, *H[which])[0]
            el = res["element"]
            nb = [j for j in tree.query_ball_point(c[el], r) if P.mem[j] == P.mem[el] and solid[j] == solid[el]] if r else [el]
            row[which] = dict(SF=1 / res["FI"], mode=res["mode"], zone=res["zone"], member=res["member"], where_link=res["where_link"],
                              sample=res["sample"], n_elements_in_radius=len(nb))
        hist, names = H["fall"]
        for lv, tag in (("soft", "_tc0.0158_dr0.2"), ("mid", "_tc0.005_dr0.2")):
            sfs = []
            for nm in sorted(set(n for n in names if n.endswith(tag))):
                sel = names == nm; P._mag_key = None
                rr = evaluate(P, S, sig, hist[sel], names[sel], k_elem=800)[0]; sfs.append(1 / rr["FI"])
            row["fall_" + lv] = dict(worst_SF=min(sfs), n_under_1_2=int(sum(s < 1.2 for s in sfs)), n=len(sfs))
        out["rows"].append(row)
        print(f"{name} avg {r} mm: walk SF {row['walk']['SF']:.2f} at {row['walk']['where_link']} ({row['walk']['n_elements_in_radius']} elements), "
              f"push SF {row['push']['SF']:.2f}, fall soft {row['fall_soft']['worst_SF']:.2f} ({row['fall_soft']['n_under_1_2']} of {row['fall_soft']['n']} under 1.2), "
              f"fall mid {row['fall_mid']['worst_SF']:.2f} ({row['fall_mid']['n_under_1_2']} of {row['fall_mid']['n']})", flush=True)
    os.makedirs(os.path.join(SCR, "fea_conv"), exist_ok=True)
    json.dump(out, open(os.path.join(SCR, "fea_conv", f"avgcheck_{name}.json"), "w"), indent=1, default=float)
    return out

def sheetlocal(levels=(1, 2, 3)):
    """local mesh check at the knee sheet eye neck: knee_to_ankle_left_sheet alone (fixed at the ankle servo contact and
    its case screw holes), a unit knee torque (1 N m) at the knee drive horn screws; von Mises per N m outside 1 mm of
    the boundary nodes, raw element values and 1 mm averages, at mesh levels 1 to 3. Writes fea_conv/sheet_local.json.
    Run: st_fea_run.py sheetlocal"""
    global AVG_MM
    STUDIES["sheet_local"] = dict(link="knee_and_ankle_assembly_2", members=["knee_to_ankle_left_sheet"],
                                  loads=[("left_knee", "drive", [5])], fix_servo_of="left_ankle")
    keep = AVG_MM; AVG_MM = 0.0; out = []
    for lv in levels:
        P, S = setup("sheet_local", float(lv)); raw = solve_units(P, S)[0]; avg = FE.averaging_matrix(P, 1.0) @ raw
        c = P.X[P.T].mean(1); excl = np.concatenate([S["groups"][0]["nodes"], S["fixed"]]); ok = cKDTree(P.X[excl]).query(c)[0] > 1.0
        near = np.linalg.norm(c[:, :2] - np.array([-11.8, -9.7]), axis=1) < 3.0          # the neck between the horn eye and the plate
        r = dict(level=lv, nodes=len(P.X), tets=len(P.T), u_max_mm_per_Nm=float(np.abs(P.u).max()), solver=S["solver"])
        for lab, sg in (("raw", raw), ("avg1mm", avg)):
            vm = FE.failure_index(sg, np.ones(len(sg), bool), np.ones(len(sg)))[1]
            i = np.argmax(np.where(ok, vm, 0)); j = np.argmax(np.where(ok & near, vm, 0))
            r[lab] = dict(vm_peak_per_Nm=float(vm[i]), at=c[i].round(2).tolist(), vm_neck_per_Nm=float(vm[j]), neck_at=c[j].round(2).tolist())
        out.append(r); print(r, flush=True)
    AVG_MM = keep
    os.makedirs(os.path.join(SCR, "fea_conv"), exist_ok=True)
    json.dump(out, open(os.path.join(SCR, "fea_conv", "sheet_local.json"), "w"), indent=1, default=float)
    return out

if __name__ == "__main__":
    if sys.argv[1] == "avgcheck": avgcheck(sys.argv[2])
    elif sys.argv[1] == "sheetlocal": sheetlocal()
    elif sys.argv[1] == "conv":                       # mesh convergence: st_fea_run.py conv <study> 1 2 3 (writes ODM_SCRATCH/fea_conv/)
        OUT = os.path.join(SCR, "fea_conv"); os.makedirs(OUT, exist_ok=True); run(sys.argv[2], tuple(float(x) for x in sys.argv[3:]))
    else: run(sys.argv[1], tuple(float(x) for x in sys.argv[2:]) or (1.0,))
