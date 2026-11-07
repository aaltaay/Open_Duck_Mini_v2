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
SF_SHOVE = 1.5                   # the margin asked for the shove (D59 review)
ABUSE = ("8dirs_F12", "mat_mu0.4_F8")   # push cases past the A1b use: a 12 N shove from 8 sides, the sit sliding on a mat


DESIGNED_END = {"left_knee": "hi", "right_knee": "hi", "left_ankle": "lo", "right_ankle": "lo", "left_hip_roll": "lo",
                "right_hip_roll": "hi", "left_hip_pitch": "lo", "right_hip_pitch": "hi", "neck_pitch": "hi", "head_pitch": "lo"}


def designed_end_ok():
    """DESIGNED_END agrees with sitlib.STOPS (the left joints; the right ones mirror hip roll and hip pitch)"""
    for st in L.STOPS.values():
        if DESIGNED_END.get(st["joint"]) != st["side"]:
            raise SystemExit("DESIGNED_END of %s is not sitlib.STOPS' %s" % (st["joint"], st["side"]))


def stop_torques(paths, abuse=False, key=None, far=False):
    """largest joint limit torque per joint at its designed stop end (sit_sim.py limit_torque_max, every physics step
    from the torque going off, with the compliant stops of sit_model.py); far=True gives the other ends instead (not
    designed stops: reported, not checked). The ABUSE push cases are kept apart (abuse=True gives only them). Every
    result file must carry the inputs_key of the model given (a result of another model or sim code is refused)."""
    T = {}
    for p in paths:
        if not p:
            continue
        if not os.path.exists(p):
            raise SystemExit("sim result %s not found: the loads would fall back to the floors" % p)
        J = json.load(open(p))
        if key is not None and J.get("inputs_key") != key:
            raise SystemExit("%s was run on another model or sim code (inputs_key %s, model %s)" % (os.path.basename(p), J.get("inputs_key"), key))
        for r in J["results"]:
            if (r.get("name") in ABUSE) != abuse:
                continue
            if "limit_torque_max" not in r:
                raise SystemExit("%s has no limit_torque_max (per stop end): rerun it" % os.path.basename(p))
            for k, v in r["limit_torque_max"].items():
                j, end = k.split(":")
                if (DESIGNED_END.get(j) == end) != far:
                    T[j] = max(T.get(j, 0.0), float(v))
    return T


def stack_check(S, cad, tol=1.0):
    """every stop radius of sitlib.STOP_STACK (the compliant stops of the sim) is the CAD's within tol mm"""
    meas = {}
    kb = cad["placements"]["knee_bumper"][0]
    sp = cad["build"]["shin_spacer"]
    n = np.array([sp["case_face_normal_xz"][0], 0.0, sp["case_face_normal_xz"][1]])
    meas["knee_fold"] = lever(*S.joint_world("left_knee"), (S.T0[kb["link"]] @ np.array(kb["T_link_mm"]))[:3, 3], n)
    pts = [(S.T0[r["link"]] @ np.array(r["T_link_mm"]))[:3, 3] for r in cad["placements"]["ankle_pad"] if r["link"] == "foot_assembly"]
    nrm = np.array(cad["build"]["foot_top"]["pad"]["normal_out"])
    meas["ankle_sit"] = float(np.mean([lever(*S.joint_world("left_ankle"), p, nrm) for p in pts]))
    hp = cad["placements"]["hip_pad"][0]
    c = (S.T0[hp["link"]] @ np.array(hp["T_link_mm"]))[:3, 3]
    p_, d_ = S.joint_world("left_hip_pitch")
    v = c - p_
    meas["hip_pitch_back"] = float(np.sqrt(v @ v - (v @ d_) ** 2))
    for k, (key, jn) in (("hip_roll_out", ("roll", "left_hip_roll")), ("neck_back", ("neck", "neck_pitch")), ("head_fwd", ("head", "head_pitch"))):
        g = lug_geometry_cached(S).get(key)
        if g:
            meas[k] = lever(*S.joint_world(jn), g["contact"], g["force_dir"])
    bad = {k: (round(v, 1), L.STOP_STACK[k]["r_mm"]) for k, v in meas.items() if abs(v - L.STOP_STACK[k]["r_mm"]) > tol}
    if bad:
        raise SystemExit("sitlib.STOP_STACK radii differ from the CAD (measured, table): %s" % bad)
    return meas


_LUGS = {}


def lug_geometry_cached(S):
    if not _LUGS:
        _LUGS.update(lug_geometry(S))
    return _LUGS


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
    designed_end_ok()
    key = None
    if a.model:
        import sit_sim as SS
        key = SS.inputs_key(os.path.dirname(os.path.normpath(a.model)))
    paths = [p for p in a.sim.split(",") if p]
    load_paths = [p for p in paths if not os.path.basename(p).startswith("sit_sim_shove")]
    shove_paths = [p for p in paths if os.path.basename(p).startswith("sit_sim_shove")]
    if a.write and not shove_paths:
        raise SystemExit("--write needs the head shove results (sit_sim.py shove: sit_sim_shove.json) in --sim")
    T = stop_torques(load_paths, key=key)
    TA = stop_torques(load_paths, abuse=True, key=key)
    TF = stop_torques(load_paths, key=key, far=True)
    rows, loads = [], {}
    stack_check(S, cad)

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

    lugs = lug_geometry_cached(S)
    loads["lug_geometry"] = lugs
    for key, joint in (("roll", "hip_roll"), ("neck", "neck_pitch"), ("head", "head_pitch")):
        g = lugs.get(key)
        if not g:
            continue
        jn = "left_" + joint if joint == "hip_roll" else joint
        p_, d_ = S.joint_world(jn)
        tn = tq(joint)
        lug_rows("%s stop lug" % key, jn, (p_, d_), g["contact"], g["force_dir"], g["root_area"], g["root_W"], g["arm"], tn, STALL["other"], tqa(joint))

    # ---------------- shoves on the head and the neck stall (one lug or face carries it all: no load sharing is counted)
    SH = {}
    for p in shove_paths:
        J_ = json.load(open(p))
        if key is not None and J_.get("inputs_key") != key:
            raise SystemExit("%s was run on another model or sim code" % os.path.basename(p))
        for r in J_["results"]:
            SH[r["name"]] = r
    hd, nk = L.STOP_STACK["head_fwd"], L.STOP_STACK["neck_back"]
    for jn, end, st, g, direction in (("head_pitch", "lo", hd, lugs.get("head"), "forward"), ("neck_pitch", "hi", nk, lugs.get("neck"), "back")):
        for tq_ in ("off", "on"):
            cs = [r for n_, r in SH.items() if r["opt"]["dir"] == direction and r["opt"]["torque"] == tq_]
            if not cs or not g:
                continue
            Tn = max(r["limit_torque_max"].get("%s:%s" % (jn, end), 0.0) for r in cs)
            F = Tn * 1000.0 / st["r_mm"]
            sig = F / g["root_area"] + F * g["arm"] / g["root_W"]
            rows.append(dict(part="%s stop, %d N shove %s on the head, torque %s" % (jn.split("_")[0], SHOVE_N, direction, tq_), load="shove",
                             case="shove", stress_MPa=round(sig, 2), allowable_MPa=Z_INTER, SF=round(Z_INTER / sig, 2), need=SF_SHOVE,
                             ok=bool(Z_INTER / sig >= SF_SHOVE), label="sim pass only (load, compliant stop K %.0f N m/rad) and calc (stress)" % L.stop_K(st),
                             what="%.2f N m at the %s stop (largest of %d sims, 0.2 and 1.0 s) -> %.0f N at r %.1f mm on one lug, root %.0f mm2" % (
                                 Tn, jn, len(cs), F, st["r_mm"], g["root_area"])))
    if lugs.get("neck") and a.model:
        import mujoco as m
        import sit_model as SM
        md = SM.load(a.model)
        dd = m.MjData(md)
        P = json.load(open(os.path.join(HERE, "sit_pose.json")))
        for jn_, v in P["joints_deg"].items():
            dd.qpos[md.jnt_qposadr[m.mj_name2id(md, m.mjtObj.mjOBJ_JOINT, jn_)]] = np.radians(v)
        m.mj_forward(md, dd)
        T_g = abs(float(dd.qfrc_bias[md.jnt_dofadr[m.mj_name2id(md, m.mjtObj.mjOBJ_JOINT, "neck_pitch")]]))
        g = lugs["neck"]
        Tn = STALL["other"] + T_g
        F = Tn * 1000.0 / nk["r_mm"]
        sig = F / g["root_area"] + F * g["arm"] / g["root_W"]
        loads["neck stall"] = dict(stall_Nm=STALL["other"], gravity_Nm=round(T_g, 3), F_N=round(F, 1))
        rows.append(dict(part="neck stop at a servo stall (one lug)", load="stall", case="stall_shove", stress_MPa=round(sig, 2), allowable_MPa=Z_INTER,
                         SF=round(Z_INTER / sig, 2), need=SF_SHOVE, ok=bool(Z_INTER / sig >= SF_SHOVE), label="calc",
                         what="stall %.2f + head weight %.2f N m (sit pose) -> %.0f N at r %.1f mm" % (STALL["other"], T_g, F, nk["r_mm"])))
    loads["far_end_peaks_Nm"] = {k: round(v, 2) for k, v in sorted(TF.items())}
    J = dict(generated_by="altaay_lab/twin/sit/sit_stress.py", label="calc", loads=loads, sim_inputs=[os.path.basename(p) for p in a.sim.split(",") if p], rows=rows,
             all_ok=all(r["ok"] for r in rows if r.get("case") not in ("stall", "abuse")),
             shove_ok=all(r["ok"] for r in rows if r.get("case") in ("shove", "stall_shove")) and any(r.get("case") == "shove" for r in rows),
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
