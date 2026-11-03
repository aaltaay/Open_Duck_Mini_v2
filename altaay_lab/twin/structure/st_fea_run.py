"""Structure twin: FEA studies of printed parts under the sim loads (FEA pass only, loads sim pass only).

Each study: the printed part(s) of one link, bonded where they are screwed together (st_fea.Part), fixed where they
hold the next servo's case (nodes within 0.3 mm of its case meshes and its case screw holes), and loaded at the
screw holes of the horns (or the bearing boss, or the case screws) through which the joint load enters, with the
two-support split of st_interfaces.split (drive horn: its share of the radial force, the full axial force and the
full axis torque; idle horn or bearing: its share of the radial force). Unit loads are solved once per active load
component; each sim sample is a linear combination of them, so the peak failure index over a whole history and
the stress history at the critical element (fatigue) come from the same solves.
Run: ODM_SCRATCH=... nice -n 10 python3 altaay_lab/twin/structure/st_fea_run.py <study> <level> [level ...]
(mesh levels of st_fea.Part.LEVELS: 1 coarse, 2 medium, 3 fine)
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
    "shin_segment": dict(link="knee_and_ankle_assembly_2", members=["knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet", "leg_spacer"],
                         grow={"leg_spacer": ((0, 0, 1), 0.3)},
                         loads=[("left_knee", "drive", [0, 1, 2, 5]), ("left_knee", "idle", [0, 1])], fix_servo_of="left_ankle"),
    "thigh_segment": dict(link="knee_and_ankle_assembly", members=["knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet", "leg_spacer"],
                          grow={"leg_spacer": ((0, 0, 1), 0.3)},
                          loads=[("left_hip_pitch", "drive", [0, 1, 2, 5]), ("left_hip_pitch", "idle", [0, 1])], fix_servo_of="left_knee"),
    "roll_to_pitch": dict(link="left_roll_to_pitch_assembly", members=["left_roll_to_pitch"],
                          loads=[("left_hip_roll", "drive", [0, 1, 2, 5]), ("left_hip_roll", "idle", [0, 1])], fix_servo_of="left_hip_pitch"),
    "hip_roll_stage": dict(link="hip_roll_assembly", members=["roll_motor_top", "roll_motor_bottom"],
                           loads=[("left_hip_yaw", "drive", [0, 1, 2, 5]), ("left_hip_yaw", "bearing", [0, 1])], fix_servo_of="left_hip_roll"),
    "foot": dict(link="foot_assembly", members=["foot_top", "foot_side", "foot_bottom_pla"],
                 loads=[("left_ankle", "drive", [0, 1, 2, 5]), ("left_ankle", "idle", [0, 1])], fix_face_of="foot_bottom_tpu"),
    "neck_sheets": dict(link="neck_pitch_assembly", members=["neck_left_sheet", "neck_right_sheet"],
                        loads=[("neck_pitch", "drive", [0, 1, 2, 5]), ("neck_pitch", "idle", [0, 1])], fix_servo_of="head_pitch"),
    "head_roll_mount": dict(link="head_assembly", members=["head_roll_mount"],
                            loads=[("head_roll", "drive_via_case", [0, 1, 2, 5])], fix_inserts=True),
}
# proposal studies: the same loads and supports with another print profile on the weak part (STRUCTURE_TWIN.md section 6)
STUDIES["roll_to_pitch_w4i40"] = dict(STUDIES["roll_to_pitch"], prof_over={"left_roll_to_pitch": dict(walls=4, infill=0.40)})
STUDIES["shin_segment_w5i40"] = dict(STUDIES["shin_segment"], prof_over={"knee_to_ankle_left_sheet": dict(walls=5, infill=0.40),
                                                                         "knee_to_ankle_right_sheet": dict(walls=5, infill=0.40)})

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
    P = FE.Part(members, level=int(maxvol), rings=rings, grow=st.get("grow"), prof_over=st.get("prof_over")); P.material(); P.assemble()
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
        o = st["fix_face_of"]; m = trimesh.load(os.path.join(FE.PRINT, o + ".stl"), force="mesh"); m.apply_transform(visual_T(link, o))
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
    return np.stack(sig)

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

TIE_EXCL_MM = 2.0     # elements within 2 mm of a tie spring node are left out of the peak (the bonded joint is judged by its insert loads)

def evaluate(P, S, sig_u, hist, names, k_elem=1500, chunk=2000):
    c = P.X[P.T].mean(1)
    if not hasattr(P, "_tie_nodes"): P._tie_nodes = np.unique(P.ties().ravel()) if len(P.members) > 1 else np.array([], int)
    tie_nodes = P._tie_nodes
    excl = np.concatenate([np.concatenate([g["nodes"] for g in S["groups"]]), S["fixed"]])
    dex = cKDTree(P.X[excl]).query(c)[0]; ok = dex > 1.0       # 1 mm off loaded and fixed nodes (point-like BCs)
    if len(tie_nodes): ok &= cKDTree(P.X[tie_nodes]).query(c)[0] > TIE_EXCL_MM
    mag = np.sqrt((sig_u[:, :, :3] ** 2).sum(-1) + 2 * (sig_u[:, :, 3:] ** 2).sum(-1))
    score = (mag * np.abs(hist).max(0)[:, None]).sum(0); score[~ok] = 0
    cand = np.argsort(score)[-k_elem:]; solid = P.zone[cand] != 3; rho = P.infill[cand]
    su = sig_u[:, cand, :].astype(np.float32)
    best = dict(s=(-1.0, 0, 0), i=(-1.0, 0, 0))
    for a in range(0, len(hist), chunk):
        sx = np.einsum("tk,kei->tei", hist[a:a + chunk].astype(np.float32), su)
        FI, vm, szz, tz, fv, fz = FE.failure_index(sx, solid[None, :], rho[None, :])
        FIs = np.where(solid[None, :], FI, 0); FIi = np.where(~solid[None, :], FI, 0)
        for key, A in (("s", FIs), ("i", FIi)):
            t_, e_ = np.unravel_index(np.argmax(A), A.shape)
            if A[t_, e_] > best[key][0]: best[key] = (float(A[t_, e_]), a + t_, e_)
    fis, ts, es = best["s"]; el = cand[es]
    one = np.einsum("k,ki->i", hist[ts], sig_u[:, el, :])[None, :]
    FI, vm, szz, tz, fv, fz = FE.failure_index(one, np.array([True]), np.array([rho[es]]))
    member = P.members[P.mem[el]]["name"]
    S3 = np.array([[one[0, 0], one[0, 5], one[0, 4]], [one[0, 5], one[0, 1], one[0, 3]], [one[0, 4], one[0, 3], one[0, 2]]])
    res = dict(FI=fis, sample=str(names[ts]), load=hist[ts].round(3).tolist(), mode="interlayer" if fz[0] > fv[0] else "in-plane",
               sig_print=one[0].round(2).tolist(), principal=np.linalg.eigvalsh(S3).round(2).tolist(),
               vm=float(vm[0]), szz=float(szz[0]), tz=float(tz[0]), zone=["wall", "top skin", "bottom skin", "infill", "ring"][int(P.zone[el])],
               member=member, where_link=c[el].round(1).tolist(), FI_infill=best["i"][0], element=int(el))
    sh = hist @ sig_u[:, el, :]
    _, v, z, _, _, _ = FE.failure_index(sh, np.ones(len(sh), bool), np.full(len(sh), rho[es]))
    return res, v.astype(np.float32), z.astype(np.float32)

def run(name, maxvols):
    out = dict(study=name, link=STUDIES[name]["link"], members=STUDIES[name]["members"], meshes=[])
    for mv in maxvols:
        t0 = time.time(); P, S = setup(name, mv); sig_u = solve_units(P, S)
        m = dict(maxvol=mv, nodes=len(P.X), tets=len(P.T), mesh_s=round(P.mesh_s, 1), solver=S["solver"], solve_s=round(S["solve_s"], 1),
                 groups=[dict(joint=g["joint"], kind=g["kind"], n_nodes=int(len(g["nodes"])), screws=g["screws"]) for g in S["groups"]],
                 n_fixed=int(len(S["fixed"])), n_tie_pairs=int(getattr(P, "n_ties", 0)), zone_vol_mm3={k: round(v, 1) for k, v in P.zone_vol.items()},
                 member_vol_mm3={k: round(v, 1) for k, v in P.member_vol.items()}, u_unit_max_mm=S["u_unit_max_mm"], cases={})
        for which in ("walk", "push", "fall"):
            hist, names = history(S, which)
            if not len(hist): continue
            r, hv, hz = evaluate(P, S, sig_u, hist, names)
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
                np.savez_compressed(os.path.join(OUT, f"{name}_{which}_hist.npz"), vm=hv, szz=hz, names=names)
            if which == "fall":
                per = {}
                for nm in sorted(set(names)):
                    sel = names == nm; rr, _, _ = evaluate(P, S, sig_u, hist[sel], names[sel], k_elem=800)
                    per[nm] = dict(FI=rr["FI"], mode=rr["mode"], member=rr["member"], where_link=rr["where_link"], load=rr["load"])
                r["per_run"] = per
            m["cases"][which] = r
            print(f"{name} maxvol {mv} {which}: FI {r['FI']:.3f} (SF {1 / max(r['FI'], 1e-9):.2f}) {r['mode']} {r['zone']} of {r['member']} at {r['where_link']} "
                  f"({r['sample']}); infill FI {r['FI_infill']:.3f}", flush=True)
        m["wall_s"] = round(time.time() - t0, 1); out["meshes"].append(m)
        print(f"{name} maxvol {mv}: {len(P.X)} nodes {len(P.T)} tets, {S['solver']}, {m['wall_s']} s", flush=True)
        json.dump(out, open(os.path.join(OUT, f"{name}.json"), "w"), indent=1, default=float)
    return out

if __name__ == "__main__":
    run(sys.argv[1], tuple(float(x) for x in sys.argv[2:]) or (1.0,))
