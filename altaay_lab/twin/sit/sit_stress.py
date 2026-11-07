#!/usr/bin/env python3
"""sit_stress.py: hand checks of the stop parts and the joggled shin sheet of the A1b sit (D59). calc only.

  python3 altaay_lab/twin/sit/sit_stress.py [--sim <scratch>/sit_sim_push.json,<scratch>/sit_sim_up.json] [--write]
Writes altaay_lab/twin/sit/sit_stress.json.

Loads per stop (each the larger of the sources named):
  service   the largest stop torque the sim saw (the joint limit force of sit_sim.py push and up runs, torque off on the
            stops, sim pass only) and, for the knee, the 1.57 Nm stand-up peak of SIT_V2.md (the brief's number)
  fall      2 x service (the brief's fall factor)
  abuse     the peaks of the two push cases past the A1b tests (ABUSE: a 12 N shove from 8 sides, the sit sliding on a mat
            at mu 0.4), checked at the fall margin and reported apart (abuse_ok), not part of all_ok
  stall     the servo pressing into its stop at its stall torque: a calibration error the 3 deg software margin does not
            cover. STS3250 knees 2.94 Nm at 7.2 V [F5], STS3215 1.91 Nm at 7.4 V [F1] (KNEE_TWIN.md section 2 table)
Allowables and margins: twin/structure/STRUCTURE_TWIN.md (D26 method): printed PLA in-plane 47.1 MPa (Overture TDS),
across the layers 22 MPa (Ezeh and Susmel 2019); lab margins SF 2.0 for service loads and 1.2 for falls; heat-set insert
sideways low value 618 N. Every stress here uses the 22 MPa interlayer value unless the stress lies in the layers, as
marked. Geometry is measured from the repo STLs and sit_cad.json now.
Methods (calc): contact force F = T / r, r the lever of the pad or lug contact about the joint axis; a beam M / W,
W = I / c from the section polygon; a bearing F / A. Hand checks, not FEA: the coupon test of the joggled sheet is a
BLOCKER (SIT.md).
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitlib as L  # noqa: E402

X_INPLANE, Z_INTER = 47.1, 22.0
SF_SERVICE, SF_FALL = 2.0, 1.2
INSERT_SIDE = 618.0
STALL = {"knee": 2.94, "other": 1.91}
KNEE_PEAK = 1.57                 # SIT_V2.md 3.2, A1b stand-up peak (STS3250 knee)
WEIGHT_N = 27.5                  # SIT_V2.md 3.2 total weight (the repo model's own mass is in sit_sim.json)


def section_props(poly_xy, axis_dir):
    """I about the centroidal axis along axis_dir (2D unit vector in the section plane) and the extreme fibre c"""
    from shapely.geometry import Polygon
    P = Polygon(poly_xy)
    c = np.array(P.centroid.coords[0])
    d = np.array(axis_dir, float)
    d /= np.linalg.norm(d)
    nrm = np.array([-d[1], d[0]])
    # sample the area
    minx, miny, maxx, maxy = P.bounds
    g = np.mgrid[minx:maxx:0.05, miny:maxy:0.05].reshape(2, -1).T
    from shapely import vectorized
    inside = vectorized.contains(P, g[:, 0], g[:, 1])
    q = (g[inside] - c) @ nrm
    A = P.area
    I = float((q ** 2).sum() * 0.05 * 0.05)
    return A, I, float(np.abs(q).max())


SHOVE_N = 12.0                   # a shove on the head (D59 review: a toy gets shoved; 12 N, the largest push of the sim)
GAP_DEG = 3.0                    # the head starts this far off its stop (the software limit) when the shove comes
E_TPU = 26.0                     # MPa, TPU 95A tensile modulus, est (typical data sheet value for 95A grades; not measured)
SF_SHOVE = 1.5                   # the margin asked for the shove (D59 review)
ABUSE = ("8dirs_F12", "mat_mu0.4_F8")   # push cases past the A1b use: a 12 N shove from 8 sides, the sit sliding on a mat


def stop_torques(paths, abuse=False):
    """largest |constraint torque| per joint over the runs (sit_sim.py constraint_torque_max / stop_torque); the ABUSE
    push cases are kept apart (abuse=True gives only them): their peaks are the limit impacts of a shove past the A1b tests"""
    T = {}
    for p in paths:
        if not p:
            continue
        if not os.path.exists(p):
            raise SystemExit("sim result %s not found: the loads would fall back to the floors" % p)
        J = json.load(open(p))
        for r in J["results"]:
            if (r.get("name") in ABUSE) != abuse:
                continue
            for k, v in (r.get("constraint_torque_max") or r.get("stop_torque") or {}).items():
                T[k] = max(T.get(k, 0.0), float(v))
    return T


def lever(axis_p, axis_d, point, force_dir):
    """moment arm of a force along force_dir through point about the axis"""
    r = np.asarray(point, float) - np.asarray(axis_p, float)
    m = np.cross(r, np.asarray(force_dir, float) / np.linalg.norm(force_dir))
    return abs(float(m @ (np.asarray(axis_d, float) / np.linalg.norm(axis_d))))


LUGS = {  # lug key: (host link, host STL, counterpart link, joint, the free side to the stop)
    "roll": ("left_roll_to_pitch_assembly", "left_roll_to_pitch", "hip_roll_assembly", "left_hip_roll", "hip_roll_out"),
    "neck": ("neck_pitch_assembly", "neck_left_sheet", "trunk_assembly", "neck_pitch", "neck_back"),
    "head": ("head_pitch_to_yaw", "head_pitch_to_yaw", "neck_pitch_assembly", "head_pitch", "head_fwd"),
}


def lug_geometry(S):
    """lug = the printed part now minus the part at BASE_REV; contact = its overlap with the counterpart 0.5 deg past
    the stop (centroid); force direction = the counterpart's motion there; root = the lug within 0.5 mm of the old part
    (area = that volume / 0.5); W of a square root of that area; arm = the root centroid to the force line"""
    out = {}
    for key, (hl, stl, cl, jn, stop) in LUGS.items():
        i = L.inst(S, hl, stl)
        Tw = L.inst_world(S, i)
        new = L.to_man(S.world_mesh(i))
        old_m = L.base_mesh("print/%s.stl" % stl)
        old_m.apply_transform(Tw)
        old = L.to_man(old_m)
        lug = new - old
        root = lug ^ (L.dilate(old, 0.5) - old)
        st = L.STOPS[stop]
        past = st["stop"] + (0.5 if st["side"] == "hi" else -0.5)
        T = L.rel_T(S, {jn: np.radians(past)}, cl, hl)
        T2 = L.rel_T(S, {jn: np.radians(past + (0.5 if st["side"] == "hi" else -0.5))}, cl, hl)
        ov = []
        for j in S.inst:
            if j["link"] != cl:
                continue
            X = L.xform(L.to_man(S.world_mesh(j)), T) ^ lug
            if X.volume() > 1e-3:
                m = L.from_man(X)
                ov.append((X.volume(), m.center_mass))
        if not ov or lug.volume() < 1.0:
            out[key] = None
            continue
        v = np.array([o[0] for o in ov])
        cpt = (np.array([o[1] for o in ov]) * v[:, None]).sum(0) / v.sum()
        # motion of the counterpart at the contact point between the two poses: the force on the lug is along it
        p1 = (T2 @ np.linalg.inv(T) @ np.r_[cpt, 1])[:3]
        fdir = p1 - cpt
        fdir = fdir / np.linalg.norm(fdir)
        rc = L.from_man(root).center_mass if root.volume() > 1e-3 else L.from_man(lug).center_mass
        A = max(root.volume() / 0.5, 1e-3)
        arm = float(np.linalg.norm(np.cross(rc - cpt, fdir)))
        out[key] = dict(contact=np.round(cpt, 2).tolist(), force_dir=np.round(fdir, 3).tolist(), root_area=round(A, 1),
                        root_W=round(A ** 1.5 / 6.0, 1), arm=round(arm, 1), lug_mm3=round(lug.volume(), 1), touch_mm3=round(float(v.sum()), 2))
    return out


def check(name, sigma, allow, load, label="calc", what=""):
    sf = allow / sigma if sigma > 1e-9 else float("inf")
    need = SF_FALL if load == "fall" else SF_SERVICE
    return dict(part=name, load=load, stress_MPa=round(sigma, 2), allowable_MPa=allow, SF=round(sf, 2) if sf < 1e6 else None,
                need=need, ok=bool(sf >= need), label=label, what=what)


def axis_inertia(md, dd, jname):
    """inertia about a hinge of everything it carries (the subtree) plus the servo armature, at the pose in dd"""
    import mujoco as m
    j = m.mj_name2id(md, m.mjtObj.mjOBJ_JOINT, jname)
    b0 = md.jnt_bodyid[j]
    a = dd.xaxis[j] / np.linalg.norm(dd.xaxis[j])
    p = dd.xanchor[j]
    I = float(md.dof_armature[md.jnt_dofadr[j]])
    for b in range(md.nbody):
        k = b
        while k != 0 and k != b0:
            k = md.body_parentid[k]
        if k != b0:
            continue
        R = dd.ximat[b].reshape(3, 3)
        d = dd.xipos[b] - p
        r2 = float(d @ d - (d @ a) ** 2)
        I += float(a @ (R @ np.diag(md.body_inertia[b]) @ R.T) @ a) + float(md.body_mass[b]) * r2
    return I, a, p


def head_shove(S, model_dir, lug, pad_dims, pad_r_mm):
    """a SHOVE_N shove on the head with the torque off, the head GAP_DEG off its forward stop: it swings onto the stop
    and the TPU pad takes the impact. Work-energy: omega = sqrt(2 T theta / I); a linear pad k = E A / t at radius r gives
    a peak of omega sqrt(I k_rot) on top of the push (VHB in series is softer still: left out, conservative)"""
    import mujoco as m
    sys.path.insert(0, HERE)
    import sit_model as SM
    md = SM.load(model_dir)
    dd = m.MjData(md)
    dd.qpos[:] = md.key_qpos[0] if md.nkey else dd.qpos
    for jn, v in (("neck_pitch", 22.0), ("head_pitch", -22.0)):
        dd.qpos[md.jnt_qposadr[m.mj_name2id(md, m.mjtObj.mjOBJ_JOINT, jn)]] = np.radians(v)
    m.mj_kinematics(md, dd)
    I, a, p = axis_inertia(md, dd, "head_pitch")
    # lever: the head's farthest point from the head pitch axis, the shove square to it (the largest torque 12 N can give)
    hp, hd = S.joint_world("head_pitch")
    lev = 0.0
    for i in S.inst:
        if i["link"] in ("head_assembly", "neck_yaw_assembly", "head_pitch_to_yaw") and i["key"] in ("head", "head_bot_sheet"):
            V = np.asarray(S.world_mesh(i).vertices)
            dv = V - hp
            lev = max(lev, float(np.sqrt((dv ** 2).sum(1) - (dv @ hd) ** 2).max()))
    T_push = SHOVE_N * lev / 1000.0
    th = np.radians(GAP_DEG)
    w = float(np.sqrt(2 * T_push * th / I))
    A = pad_dims[0] * pad_dims[1]
    k_lin = E_TPU * A / pad_dims[2] * 1000.0                      # N/m (MPa x mm2 / mm = N/mm)
    k_rot = k_lin * (pad_r_mm / 1000.0) ** 2
    T_pk = w * float(np.sqrt(I * k_rot)) + T_push
    F = T_pk * 1000.0 / pad_r_mm
    sig = F / lug["root_area"] + F * lug["arm"] / lug["root_W"]
    return dict(I_axis_kg_m2=round(I, 5), lever_mm=round(lev, 1), push_Nm=round(T_push, 3), gap_deg=GAP_DEG, omega_rad_s=round(w, 3),
                pad_k_N_mm=round(k_lin / 1000, 1), pad_r_mm=round(pad_r_mm, 1), peak_Nm=round(T_pk, 3), F_N=round(F, 1),
                pad_MPa=round(F / A, 2), pad_strain=round(F / (E_TPU * A), 3), lug_MPa=round(sig, 2), SF=round(Z_INTER / sig, 2),
                ok=bool(Z_INTER / sig >= SF_SHOVE))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", default="")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--model", default="", help="the sit model folder (sit_model.py --out <S>/model: <S>/model/sit), for the head shove")
    a = ap.parse_args()
    S = L.scene(fresh=True)
    cad = json.load(open(os.path.join(HERE, "sit_cad.json")))
    if a.write and (not a.sim or not a.model):
        raise SystemExit("--write needs --sim (the push and up results) and --model (the head shove inertia)")
    T = stop_torques(a.sim.split(",") if a.sim else [])
    TA = stop_torques(a.sim.split(",") if a.sim else [], abuse=True)
    rows, loads = [], {}

    def tq(j, floor=0.0, src=None):
        src = T if src is None else src
        return max(floor, src.get("left_" + j, 0.0), src.get("right_" + j, 0.0)) if not j.startswith(("neck", "head")) else max(floor, src.get(j, 0.0))

    def tqa(j):
        return tq(j, 0.0, TA)

    # ---------------- knee stop: pad on the shin spacer, the knee case face, the spacer beam, the inserts, the joggle
    sp = cad["build"]["shin_spacer"]
    n = np.array([sp["case_face_normal_xz"][0], 0.0, sp["case_face_normal_xz"][1]])
    kb = cad["placements"]["knee_bumper"][0]
    Tk = np.array(kb["T_link_mm"])
    pad_c = (S.T0[kb["link"]] @ Tk)[:3, 3]
    kp, kd = S.joint_world("left_knee")
    r_k = lever(kp, kd, pad_c, n)
    t_srv = tq("knee", KNEE_PEAK)
    loads["knee"] = dict(service_Nm=round(t_srv, 3), sim_stop_Nm=round(tq("knee"), 3), lever_mm=round(r_k, 1))
    dims = cad["build"]["shin_spacer"]
    pad_A = 14.0 * 28.0
    poly = np.array(sp["section_xz"])
    t_dir = np.array([-n[2], n[0]])                           # bending axis in the section (x, z) plane
    A, I, c = section_props(poly, t_dir)
    Ls = sp["length"]
    for load, Tn in (("service", t_srv), ("fall", 2 * t_srv), ("stall", STALL["knee"]), ("abuse", tqa("knee"))):
        F = Tn * 1000.0 / r_k                                  # N
        M = F * (Ls / 4 - 28.0 / 8)                            # N mm, simply supported, the load spread over the 28 mm pad
        sig = M / (I / c)
        rows.append(check("shin_spacer (beam between the sheets)", sig, X_INPLANE, "fall" if load in ("fall", "abuse") else "service",
                          what="F %.1f N at r %.1f mm; M %.0f N mm; W %.0f mm3 (layers along the beam: in-plane)" % (F, r_k, M, I / c)))
        rows[-1]["case"] = load
        rows.append(check("knee bumper pad (bearing)", F / pad_A, 10.0, "fall" if load in ("fall", "abuse") else "service",
                          what="TPU 95A on VHB 4950, %.2f MPa over %.0f mm2; 10 MPa used as a TPU compressive working value (est)" % (F / pad_A, pad_A), label="calc, est"))
        rows[-1]["case"] = load
        rows.append(check("spacer inserts (sideways)", F / 4.0, INSERT_SIDE, "fall" if load in ("fall", "abuse") else "service",
                          what="4 inserts per spacer, %.1f N each against %d N" % (F / 4, INSERT_SIDE)))
        rows[-1]["stress_MPa"] = None
        rows[-1]["force_N"] = round(F / 4.0, 1)
        rows[-1]["case"] = load
        # joggle: the knee pin reaction per sheet acts JOG off the plate's mid plane: out-of-plane bending of the 3.9 mm
        # horn zone across its width at r = R_HORN (the chord the sheet spans there)
        R_sheet = (F + WEIGHT_N / 2) / 2
        Mj = R_sheet * L.JOG
        w_band = 25.0
        sig_j = 6 * Mj / (w_band * 3.85 ** 2)
        rows.append(check("shin sheet horn zone at the joggle", sig_j, X_INPLANE, "fall" if load in ("fall", "abuse") else "service",
                          what="R per sheet %.1f N x %.1f mm = %.0f N mm on a %.0f x 3.85 mm section (bending in the layers: the sheet prints flat)" % (
                              R_sheet, L.JOG, Mj, w_band)))
        rows[-1]["case"] = load
    # the knee torque through the horn zone (unchanged geometry): STRUCTURE_TWIN.md 2.4, 5.0 MPa per N m at the sheet neck
    for load, Tn in (("service", t_srv), ("fall", 2 * t_srv)):
        rows.append(check("shin sheet neck, knee torque (FEA scale)", 5.0 * Tn, X_INPLANE, load,
                          what="5.0 MPa per N m (STRUCTURE_TWIN.md, sheetlocal levels 2 and 3) x %.2f N m" % Tn, label="calc (FEA scale)"))
        rows[-1]["case"] = load

    # ---------------- ankle stop: two pads, the clamp block faces
    ap_ = cad["placements"]["ankle_pad"]
    pts = [(S.T0[r["link"]] @ np.array(r["T_link_mm"]))[:3, 3] for r in ap_ if r["link"] == "foot_assembly"]
    nrm_a = np.array(cad["build"]["foot_top"]["pad"]["normal_out"])
    ap_p, ap_d = S.joint_world("left_ankle")
    r_a = float(np.mean([lever(ap_p, ap_d, p, nrm_a) for p in pts]))
    t_a = tq("ankle")
    loads["ankle"] = dict(service_Nm=round(t_a, 3), lever_mm=round(r_a, 1))
    A_pad = 6.0 * 7.5
    for load, Tn in (("service", t_a), ("fall", 2 * t_a), ("stall", STALL["other"]), ("abuse", tqa("ankle"))):
        F = Tn * 1000.0 / max(r_a, 1e-6) / 2
        rows.append(check("ankle pad (bearing, per pad)", F / A_pad, 10.0, "fall" if load in ("fall", "abuse") else "service",
                          what="2 pads, %.1f N each over %.0f mm2" % (F, A_pad), label="calc, est"))
        rows[-1]["case"] = load
        rows.append(check("foot plate pad seat (bearing)", F / A_pad, Z_INTER, "fall" if load in ("fall", "abuse") else "service",
                          what="PLA seat under the pad, across the layers (conservative)"))
        rows[-1]["case"] = load

    # ---------------- lugs: contact force on the lug face; root section measured on the STL
    def lug_rows(name, joint, axis, contact, fdir, root_area, root_W, arm, tn, stall, ta):
        r_ = lever(axis[0], axis[1], contact, fdir)
        loads[name] = dict(service_Nm=round(tn, 3), lever_mm=round(r_, 1), root_area_mm2=round(root_area, 1), root_W_mm3=round(root_W, 1), arm_mm=round(arm, 1))
        for load, Tn in (("service", tn), ("fall", 2 * tn), ("stall", stall), ("abuse", ta)):
            F = Tn * 1000.0 / max(r_, 1e-6)
            sig = F / root_area + F * arm / root_W
            rows.append(check(name, sig, Z_INTER, "fall" if load in ("fall", "abuse") else "service",
                              what="F %.1f N at r %.1f mm; root %.0f mm2, W %.0f mm3, arm %.1f mm (across the layers, conservative)" % (F, r_, root_area, root_W, arm)))
            rows[-1]["case"] = load

    lugs = lug_geometry(S)
    loads["lug_geometry"] = lugs
    for key, joint in (("roll", "hip_roll"), ("neck", "neck_pitch"), ("head", "head_pitch")):
        g = lugs.get(key)
        if not g:
            continue
        jn = "left_" + joint if joint == "hip_roll" else joint
        p_, d_ = S.joint_world(jn)
        tn = tq(joint)
        lug_rows("%s stop lug" % key, jn, (p_, d_), g["contact"], g["force_dir"], g["root_area"], g["root_W"], g["arm"], tn, STALL["other"], tqa(joint))

    # ---------------- a shove on the head: the head lug lands on its TPU pad (sit_cad.py head_pad)
    hpad = cad["build"]["head_pitch_to_yaw"].get("pad")
    if a.model and hpad and lugs.get("head"):
        hp_, hd_ = S.joint_world("head_pitch")
        c_ = np.array(hpad["centre"]) - hp_
        r_pad = float(np.sqrt(c_ @ c_ - (c_ @ hd_) ** 2))
        sh = head_shove(S, a.model, lugs["head"], hpad["dims"], r_pad)
        loads["head shove"] = sh
        rows.append(dict(part="head stop lug, %d N shove on the head (TPU pad)" % SHOVE_N, load="shove", case="shove", stress_MPa=sh["lug_MPa"],
                         allowable_MPa=Z_INTER, SF=sh["SF"], need=SF_SHOVE, ok=sh["ok"], label="calc",
                         what="omega %.2f rad/s after %.0f deg, I %.4f kg m2, pad k %.0f N/mm at r %.1f mm: peak %.2f N m, %.0f N" % (
                             sh["omega_rad_s"], GAP_DEG, sh["I_axis_kg_m2"], sh["pad_k_N_mm"], sh["pad_r_mm"], sh["peak_Nm"], sh["F_N"])))
    # ---------------- a shove backward on the head with the torque off: the neck lug already carries the head (its service
    # torque) and takes the shove on top, statically (it rests on its stop)
    if lugs.get("neck"):
        npnt, nd = S.joint_world("neck_pitch")
        lev = 0.0
        for i in S.inst:
            if i["key"] in ("head", "head_bot_sheet"):
                dv = np.asarray(S.world_mesh(i).vertices) - npnt
                lev = max(lev, float(np.sqrt((dv ** 2).sum(1) - (dv @ nd) ** 2).max()))
        g = lugs["neck"]
        Tn = tq("neck_pitch") + SHOVE_N * lev / 1000.0
        r_ = lever(npnt, nd, g["contact"], g["force_dir"])
        F = Tn * 1000.0 / r_ / 2                                  # two neck sheets, one lug each
        sig = F / g["root_area"] + F * g["arm"] / g["root_W"]
        loads["neck shove"] = dict(lever_mm=round(lev, 1), torque_Nm=round(Tn, 3), F_per_lug_N=round(F, 1))
        rows.append(dict(part="neck stop lug, %d N shove back on the head (static, torque off)" % SHOVE_N, load="shove", case="shove",
                         stress_MPa=round(sig, 2), allowable_MPa=Z_INTER, SF=round(Z_INTER / sig, 2), need=SF_SHOVE,
                         ok=bool(Z_INTER / sig >= SF_SHOVE), label="calc",
                         what="%.2f N m (sim service %.2f + %d N at %.0f mm) over 2 lugs at r %.1f mm" % (Tn, tq("neck_pitch"), SHOVE_N, lev, r_)))
    J = dict(generated_by="altaay_lab/twin/sit/sit_stress.py", label="calc", loads=loads, sim_inputs=[os.path.basename(p) for p in a.sim.split(",") if p], rows=rows,
             all_ok=all(r["ok"] for r in rows if r.get("case") not in ("stall", "abuse")),
             shove_ok=all(r["ok"] for r in rows if r.get("case") == "shove") and any(r.get("case") == "shove" for r in rows),
             abuse_ok=all(r["ok"] for r in rows if r.get("case") == "abuse"), abuse_cases=list(ABUSE),
             abuse_peaks_Nm={k: round(v, 2) for k, v in sorted(TA.items())},
             stall_ok=all(r["ok"] for r in rows if r.get("case") == "stall"))
    for r in rows:
        print("%-44s %-7s %s SF %s (need %.1f) %s" % (r["part"], r.get("case"), r["stress_MPa"] if r["stress_MPa"] is not None else r.get("force_N"),
                                                    r["SF"], r["need"], "ok" if r["ok"] else "LOW"))
    if a.write:
        L.dump(J, os.path.join(HERE, "sit_stress.json"))


if __name__ == "__main__":
    main()
