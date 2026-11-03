"""Structure twin: loads at every printed-part interface, from the joint loads of st_loads.py and st_falls.py (sim pass only).

For every actuated joint the sim gives the 6D load of the parent link on the child link at the joint origin, in the
child link frame (z = joint axis). It passes, in series, through:
  child side : the drive horn screw group (4 x M3 into the aluminium drive horn, on the output spline) and the idle
               horn screw group (4 x M3 into the idle horn, on the idle boss) into the child's printed parts;
  parent side: the servo case screw group (M2 self-tapping into the PA+GF case pilots) and the pocket into the
               parent's printed parts.
Split used (statics, ASSUMPTION): the force perpendicular to the axis and the bending moment are shared by the two
horn groups as a beam on two supports at their axial positions (fasteners.json screw seats); the axis torque goes
through the drive horn only (the idle horn turns freely on the idle boss); the axial force is taken in full by
either group (worst case for its screws). Bolt group: per screw shear = group force / 4 + torque / (4 r); per screw
tension = axial / 4 + group moment / (2 r) when the group is also given half the bending moment (the second model,
the worse of the two is kept). Case screws: RBE3 split of the same 6D load over the case screws of that servo in
the parent frame (pocket contact ignored, so an upper bound).
Output: ODM_SCRATCH/interfaces.json and the tables used by STRUCTURE.md.
"""
import os, sys, json, glob
import numpy as np
import yourdfpy

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "../.."))
REPO = os.path.abspath(os.path.join(LAB, ".."))
SCR = os.environ.get("ODM_SCRATCH", "/tmp/odm_twin_structure")
JOINTS = ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle", "neck_pitch", "head_pitch", "head_yaw",
          "head_roll", "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]

def fasteners():
    return json.load(open(os.path.join(LAB, "fasteners/fasteners.json")))["fasteners"]

BEARINGS = {   # 6804 bearings on a joint axis (URDF roll_bearing.stl instances), axial position in the child frame (mm)
    "left_hip_yaw": dict(z=-62.8, part="trunk_bottom", what="6804 seat in trunk_bottom (roll_motor_bottom turns in it)"),
    "right_hip_yaw": dict(z=-62.8, part="trunk_bottom", what="6804 seat in trunk_bottom (roll_motor_bottom turns in it)"),
    "head_roll": dict(z=85.5, part="head", what="6804 seat in the head (head_yaw_to_roll turns in it)")}

def groups():
    """per joint: drive and idle horn groups and the case screw group, positions in the child frame at q = 0 (mm)"""
    F = fasteners(); u = yourdfpy.URDF.load(os.path.join(REPO, "mini_bdx/robots/open_duck_mini_v2/robot.urdf"), load_meshes=False, build_scene_graph=True)
    out = {}
    for j in JOINTS:
        jt = u.joint_map[j]; child, parent = jt.child, jt.parent
        To = np.array(jt.origin); Toi = np.linalg.inv(To)
        def to_child(p, link):
            p = np.asarray(p, float)
            return p if link == child else (Toi[:3, :3] @ (p / 1000.0) + Toi[:3, 3]) * 1000.0
        def dir_child(a, link):
            a = np.asarray(a, float); return a if link == child else Toi[:3, :3] @ a
        g = dict(child=child, parent=parent, origin=To, drive=None, idle=None, case=[])
        for kind, anc in (("drive", "horn(drive)"), ("idle", "horn(passive)")):
            xs = [x for x in F if x["anchor"] == anc and x.get("servo") == j]
            if xs:
                P = np.array([to_child(x["seat_link"], x["link"]) for x in xs]); A = np.array([dir_child(x["axis_link"], x["link"]) for x in xs])
                face = np.mean(P + A * np.array([x["near"] for x in xs])[:, None], axis=0)
                g[kind] = dict(n=len(xs), part=xs[0]["part"], link=xs[0]["link"], side="child" if xs[0]["link"] == child else "parent",
                               r=float(np.hypot(P[:, 0], P[:, 1]).mean()), z=float(face[2]), spec=xs[0]["spec"], ids=[x["id"] for x in xs], e=xs[0].get("e"))
        if g["idle"] is None and j in BEARINGS:
            b = BEARINGS[j]; g["idle"] = dict(n=0, part=b["part"], link=None, side="bearing", r=0.0, z=b["z"], spec="6804 bearing", ids=[], e=None, what=b["what"])
        cs = [x for x in F if x["anchor"] == "servo pilot" and x.get("servo") == j and x.get("len_status", "").find("LEAVE OUT") < 0]
        g["case"] = [dict(id=x["id"], part=x["part"], link=x["link"], side="child" if x["link"] == child else "parent",
                          p=to_child(x["seat_link"], x["link"]), a=dir_child(x["axis_link"], x["link"]), spec=x["spec"], e=x.get("e")) for x in cs]
        out[j] = g
    return out

def rz(q):
    c, s = np.cos(q), np.sin(q); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])

def split(F, T, g):
    """per sample: drive and idle group loads (force perpendicular vector, axial, axis torque) in the child frame"""
    d, i = g["drive"], g["idle"]
    Fr = F[:, :2]; Mp = T[:, :2]; Fa = F[:, 2]; Mz = T[:, 2]
    if d and i:
        zd, zi = d["z"] / 1000.0, i["z"] / 1000.0
        # z_d R_d + z_i R_i = M_perp x e_z ; R_d + R_i = F_r   (moments about the joint origin, m)
        mxe = np.stack([Mp[:, 1], -Mp[:, 0]], axis=1)     # (Mx, My, 0) x (0, 0, 1) = (My, -Mx, 0)
        Rd = (mxe - zi * Fr) / (zd - zi); Ri = Fr - Rd
    else:
        Rd = Fr; Ri = np.zeros_like(Fr)
    return Rd, Ri, Fa, Mz, Mp

def screw_loads(F, T, g):
    """per sample: per-screw worst shear and tension (N) for the drive and idle groups, and the bearing radial load.
    tension_A: axial force in full on this group (two-support beam, no group moment); tension_B: plus half the
    bending moment taken by the group as a moment (stiff-plate bound)"""
    Rd, Ri, Fa, Mz, Mp = split(F, T, g); out = {}
    for kind, R in (("drive", Rd), ("idle", Ri)):
        G = g[kind]
        if not G: continue
        rad = np.linalg.norm(R, axis=1)
        if G["n"] == 0:
            out[kind] = dict(shear=rad, tension_A=np.abs(Fa), tension_B=np.abs(Fa), group_force=rad, axial=np.abs(Fa), torque=np.zeros_like(Mz))
            continue
        n, r = G["n"], G["r"] / 1000.0
        shear = rad / n + (np.abs(Mz) / (n * r) if kind == "drive" else 0)
        out[kind] = dict(shear=shear, tension_A=np.abs(Fa) / n, tension_B=np.abs(Fa) / n + np.linalg.norm(Mp, axis=1) / 2 / (2 * r),
                         group_force=rad, axial=np.abs(Fa), torque=np.abs(Mz) if kind == "drive" else np.zeros_like(Mz))
    return out

def case_loads(F, T, q, g):
    """RBE3 split of the 6D joint load over the case screws (pocket contact ignored, so an upper bound); positions are
    in the child frame at q = 0; screws on the parent side turn with -q relative to the child frame. Per screw |shear|
    and the pull along the screw axis, N"""
    cs = g["case"]
    if not cs: return None
    P = np.array([c["p"] for c in cs]) / 1000.0; A = np.array([c["a"] for c in cs]); side = cs[0]["side"]
    shear = np.zeros((len(F), len(cs))); pull = np.zeros((len(F), len(cs)))
    for k in range(len(F)):
        if side == "parent":
            Rq = rz(-q[k]); Pk = P @ Rq.T; Ak = A @ Rq.T          # parent-fixed screws seen from the child frame
        else:
            Pk, Ak = P, A
        cc = Pk.mean(0); r = Pk - cc
        J = sum((ri @ ri) * np.eye(3) - np.outer(ri, ri) for ri in r)
        Mc = T[k] + np.cross(-cc, F[k])                              # moment about the screw group centroid
        a = np.linalg.pinv(J) @ Mc
        f = F[k][None, :] / len(cs) + np.cross(a[None, :], r)
        ax = np.einsum("ij,ij->i", f, Ak)
        pull[k] = np.abs(ax); shear[k] = np.linalg.norm(f - ax[:, None] * Ak, axis=1)
    return dict(shear=shear, pull=pull, ids=[c["id"] for c in cs], parts=[c["part"] for c in cs], specs=[c["spec"] for c in cs])

def load_runs(pattern):
    runs = []
    for f in sorted(glob.glob(pattern)):
        d = np.load(f, allow_pickle=True); runs.append((os.path.basename(f)[:-4], d))
    return runs

def window(d, name):
    """time window for the statistics: after the 2 s settle; runs that fell end 1 s before the fall (a fallen robot
    in the floor-less upstream model is not a load case)"""
    t = d["t"]; sel = t >= 2.0
    if name.startswith("push1_"):
        t0 = float(name.split("_ph")[1]) * 0.54 / 8 + 6.0; sel = t >= t0 - 0.5
    fl = d["falls"] if "falls" in d.files else np.array([])
    if len(fl): sel &= t < float(fl[0]) - 1.0
    return sel

if __name__ == "__main__":
    G = groups()
    json.dump({j: dict(child=g["child"], parent=g["parent"], drive=g["drive"], idle=g["idle"],
                       case=[dict(id=c["id"], part=c["part"], spec=c["spec"], e=c["e"]) for c in g["case"]]) for j, g in G.items()},
              open(os.path.join(SCR, "interface_groups.json"), "w"), indent=1, default=float)
    sets = dict(walk=os.path.join(SCR, "loads/walk_*.npz") + "|" + os.path.join(SCR, "loads/turn_*.npz") + "|" + os.path.join(SCR, "loads/stand_*.npz"),
                push=os.path.join(SCR, "loads/push1_*.npz") + "|" + os.path.join(SCR, "loads/walk_pushes_*.npz"),
                fall_default=os.path.join(SCR, "falls/*_tc0.02_dr1.npz"),           # MuJoCo default contact
                fall_soft=os.path.join(SCR, "falls/*_tc0.0158_dr0.2.npz"),          # K eff about 0.3 MN/m (st_report.falls_table)
                fall_mid=os.path.join(SCR, "falls/*_tc0.005_dr0.2.npz"),            # about 3 MN/m
                fall_hard=os.path.join(SCR, "falls/*_tc0.00289_dr0.2.npz"))         # about 9 MN/m
    res = {}
    for sname, pats in sets.items():
        runs = []
        for p in pats.split("|"): runs += load_runs(p)
        if sname == "walk": runs = [(n, d) for n, d in runs if not n.startswith("walk_pushes")]
        agg = {}
        for name, d in runs:
            sel = np.ones(len(d["t"]), bool) if sname.startswith("fall") else window(d, name)
            if sel.sum() < 10: continue
            for ji, j in enumerate(JOINTS):
                F = d["F"][sel, ji].astype(float); T = d["T"][sel, ji].astype(float); q = d["q"][sel, ji].astype(float)
                st = 5 if not sname.startswith("fall") else 2
                sl = screw_loads(F, T, G[j]); cl = case_loads(F[::st], T[::st], q[::st], G[j])
                a = agg.setdefault(j, {})
                for kind, v in sl.items():
                    for c in ("shear", "tension_A", "tension_B", "group_force", "axial", "torque"):
                        key = f"{kind}_{c}"; a[key] = max(a.get(key, 0.0), float(v[c].max()))
                if cl:
                    a["case_shear"] = max(a.get("case_shear", 0.0), float(cl["shear"].max()))
                    a["case_pull"] = max(a.get("case_pull", 0.0), float(cl["pull"].max()))
                    a["case_ids"] = cl["ids"]; a["case_specs"] = sorted(set(cl["specs"]))
        res[sname] = agg
        print("==", sname, len(runs), "runs")
        for j in JOINTS:
            a = agg[j]
            print(f"{j:16s} drive: shear {a.get('drive_shear', 0):6.1f} tA {a.get('drive_tension_A', 0):6.1f} tB {a.get('drive_tension_B', 0):6.1f} | idle/brg: shear {a.get('idle_shear', 0):6.1f} "
                  f"tA {a.get('idle_tension_A', 0):6.1f} | group F d {a.get('drive_group_force', 0):6.1f} i {a.get('idle_group_force', 0):6.1f} | case: shear {a.get('case_shear', 0):6.1f} pull {a.get('case_pull', 0):6.1f}")
    json.dump(res, open(os.path.join(SCR, "interfaces.json"), "w"), indent=1, default=float)
    print("wrote", os.path.join(SCR, "interfaces.json"))
