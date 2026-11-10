#!/usr/bin/env python3
"""sit_stress.py: hand checks of the stop parts and the joggled shin sheet of the A1b sit (D59). calc only.

  python3 altaay_lab/twin/sit/sit_stress.py [--sim <scratch>/sit_sim_push.json,<scratch>/sit_sim_up.json] [--write]
Writes altaay_lab/twin/sit/sit_stress.json.

Loads per stop, calc only by the energy method (energy_peaks): the link's kinetic energy at the moment it meets the stop,
0.5 I omega^2 (omega from the sim on the step before the limit engages, which converges with the step unlike the peak
force; I the joint's effective inertia at the sit pose, armature included), absorbed by the stack compliance K of
sitlib.STOP_STACK (TPU face plus lug), gives the peak torque omega sqrt(I K) on top of the rest torque. The compliant
stop sim's own peak is kept as a cross-check (sim_over_energy). Cases:
  service   omega over the push cases (sit_sim.py loads: 3 to 12 N, torque off on the dock pads) past the ABUSE ones
  fall      2 x service (the brief's fall factor)
  abuse     omega over the ABUSE push cases (a 12 N shove from 8 sides, the sit sliding on a mat at mu 0.4), at the fall
            margin and reported apart (abuse_ok), not part of all_ok
  stall     the servo pressing into its stop at its stall torque plus the rest torque: a calibration error the 3 deg
            software margin does not cover. STS3250 knees 2.94 Nm at 7.2 V [F5], STS3215 1.91 Nm at 7.4 V [F1]
  shove     omega at the head and neck stops over the head shove sims (sit_sim.py shove: 12 N on the head, forward and
            back, torque off and on, 0.2 and 1.0 s, the body held), SF 1.5 asked; plus the neck stall at SF 1.5
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
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitlib as L  # noqa: E402
import sit_cad as SC  # noqa: E402  (geometry constants only)

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


def stop_loads(paths, abuse=False, key=None):
    """per joint at its designed stop end, over the runs given (sit_sim.py Stops report, every physics step from the
    torque going off): the largest impact speed omega (rad/s), the largest limit torque the compliant-stop sim saw
    (sim_Nm, a cross-check only: it depends on the step size) and the largest rest torque (the joint held on its stop
    after the motion). The ABUSE push cases are kept apart (abuse=True gives only them). Every result file must carry
    the inputs_key of the model given (a result of another model or sim code is refused)."""
    out = {}
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
            for fld in ("limit_torque_max", "limit_omega_max", "limit_torque_rest", "limit_torque_sustained", "limit_torque_loaded"):
                if fld not in r:
                    raise SystemExit("%s has no %s (per stop end): rerun it" % (os.path.basename(p), fld))
            for fld, nm in (("limit_torque_max", "sim_Nm"), ("limit_omega_max", "omega"), ("limit_torque_rest", "rest_Nm"),
                            ("limit_torque_sustained", "sustained_Nm"), ("limit_torque_loaded", "loaded_Nm")):
                for k, v in r[fld].items():
                    j, end = k.split(":")
                    if DESIGNED_END.get(j) == end:
                        d = out.setdefault(j, dict(omega=0.0, sim_Nm=0.0, rest_Nm=0.0, sustained_Nm=0.0, loaded_Nm=0.0))
                        d[nm] = max(d[nm], float(v))
    return out


def energy_peaks(loads, stops, held=False):
    """calc only: the link's kinetic energy at the moment it meets the stop, 0.5 I omega^2 (I the joint's effective
    inertia at the sit pose, armature included: sit_model.json stops; the held-base value when the body is held),
    absorbed by the stack compliance K (sitlib STOP_STACK, N m/rad), gives the impact peak omega sqrt(I K) on top of
    the rest torque. A stop that is already engaged when the push arrives (the torque-off sit rests on its stops) sees
    the push as a sustained reaction instead: the largest 100 ms mean of the limit torque in the sim (converged, the
    ring-down averaged out). The design load is the larger of the two. The sim's own peak is the cross-check (ratio)."""
    out = {}
    key = "I_eff_held" if held else "I_eff"
    for j, d in loads.items():
        st = stops.get(j)
        if not st:
            continue
        if key not in st:
            raise SystemExit("sit_model.json has no %s: rerun sit_model.py" % key)
        T_dyn = d["omega"] * float(np.sqrt(st[key] * st["K_Nm_rad"]))
        T_e = T_dyn + d["rest_Nm"]
        T = max(T_e, d["sustained_Nm"])
        out[j] = dict(omega_rad_s=round(d["omega"], 3), I_eff=st[key], K_Nm_rad=st["K_Nm_rad"], dyn_Nm=round(T_dyn, 3),
                      rest_Nm=round(d["rest_Nm"], 3), energy_Nm=round(T_e, 3), sustained_Nm=round(d["sustained_Nm"], 3),
                      loaded_raw_Nm=round(d["loaded_Nm"], 3), design_Nm=round(T, 3), sizing="sustained" if d["sustained_Nm"] > T_e else "impact",
                      sim_Nm=round(d["sim_Nm"], 3), sim_over_design=round(d["sim_Nm"] / T, 2) if T > 1e-6 else None)
    return out


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
    # the neck block, the head hook and the roll lug: the pad face centre and normal the builder recorded, checked against the scene
    # the table's r for these three is the builder's pad_r_mm: the radial distance of the pad centre from the joint axis
    # (K = k r^2 with that r, the stiffer and so the conservative case); the lever of the pad's normal about the axis,
    # which turns the stop torque into the pad force (neck_rows, head_rows), is smaller where the face is not tangential
    nb, hh, rl = cad["build"]["neck_stop"], cad["build"]["head_pitch_to_yaw"], cad["build"]["left_roll_to_pitch"]
    levers = {}
    for k, rec, jn in (("neck_back", nb, "neck_pitch"), ("head_fwd", hh, "head_pitch"), ("hip_roll_out", rl, "left_hip_roll")):
        ax_p, ax_d = S.joint_world(jn)
        c = np.array(rec["pad_face_centre"], float)
        meas[k] = float(np.linalg.norm(np.cross(c - np.asarray(ax_p, float), np.asarray(ax_d, float) / np.linalg.norm(ax_d))))
        levers[k] = lever(ax_p, ax_d, c, rec["pad_normal"])
        if abs(meas[k] - rec["pad_r_mm"]) > 0.05:
            raise SystemExit("%s: the builder's pad radius %.2f is not the scene's %.2f" % (k, rec["pad_r_mm"], meas[k]))
    bad = {k: (round(v, 1), L.STOP_STACK[k]["r_mm"]) for k, v in meas.items() if abs(v - L.STOP_STACK[k]["r_mm"]) > tol}
    if bad:
        raise SystemExit("sitlib.STOP_STACK radii differ from the CAD (measured, table): %s" % bad)
    return dict(radius_mm={k: round(v, 2) for k, v in meas.items()}, normal_lever_mm={k: round(v, 2) for k, v in levers.items()})


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


LUGS = {  # lug key: (host link, host STL, counterpart link, joint, the free side to the stop); the neck and head stops are
          # TPU faces on parts of ours now (neck_rows, head_rows), not lugs
    "roll": ("left_roll_to_pitch_assembly", "left_roll_to_pitch", "hip_roll_assembly", "left_hip_roll", "hip_roll_out"),
}
TPU_BEARING = 10.0               # MPa, TPU 95A compressive working value (est), as the knee bumper row
SCREW_PULLOUT_N = 500.0          # est: an M2 thread-forming screw 3.2 mm into the STS3215 case (PA+GF), tau 50 MPa x pi d e x 0.5
                                 # thread form; no pull-out datasheet or test: BLOCKER (TEST_PLAN 19.8) until measured
VHB_SHEAR = 0.6                  # MPa, VHB 4950 static shear working value (est; the pads sit in pockets, so the pocket wall takes the slide)
INTER_SHEAR = Z_INTER / np.sqrt(3.0)   # MPa, shear across the layers taken as the interlayer tensile value over root 3 (est)


def _edge_motion(ax_p, ax_d, point):
    """unit direction of a point's motion under a rotation about the axis (the tangent at the contact)"""
    v = np.cross(np.asarray(ax_d, float), np.asarray(point, float) - np.asarray(ax_p, float))
    return v / np.linalg.norm(v)


def _section_at_z(mesh_world, z, y_sel):
    """the polygon of a world mesh cut at z (the loop whose y passes y_sel), as (x, y) points"""
    sec = mesh_world.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        raise SystemExit("no section at z %.1f" % z)
    loops = [np.asarray(l) for l in sec.discrete if y_sel(np.asarray(l)[:, 1])]
    if len(loops) != 1:
        raise SystemExit("section at z %.1f: %d loops (one expected)" % (z, len(loops)))
    return loops[0][:, :2]


def _composite_at_z(mesh_world, z, y_sel):
    """the section of a world mesh at z over the loops y_sel picks: the largest loop less the holes inside it (the screw
    hole through the flange lobe), bending about y: area, I about the composite centroid, the extreme fibre, the x extent"""
    from shapely.geometry import Polygon
    sec = mesh_world.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        raise SystemExit("no section at z %.1f" % z)
    polys = [Polygon(np.asarray(l)[:, :2]) for l in sec.discrete if y_sel(np.asarray(l)[:, 1])]
    if not polys:
        raise SystemExit("section at z %.1f: no loop" % z)
    outer = max(polys, key=lambda q: q.area)
    holes = [q for q in polys if q is not outer and outer.contains(q)]
    A = outer.area - sum(q.area for q in holes)
    cx = (outer.centroid.x * outer.area - sum(q.centroid.x * q.area for q in holes)) / A

    def Ix(q):
        Ai, Ii, ci = section_props(np.asarray(q.exterior.coords), (0.0, 1.0))
        return Ii + Ai * (q.centroid.x - cx) ** 2
    I = Ix(outer) - sum(Ix(q) for q in holes)
    x_min, x_max = outer.bounds[0], outer.bounds[2]
    return float(A), float(I), float(max(abs(x_max - cx), abs(x_min - cx))), float(x_min), float(x_max)


def neck_geometry(S, cad):
    """the neck block as built: the pad (centre, normal, radius, the edge's slide fraction), the left pillar's base section
    (bending about y, across the layers: the block prints standing), the screw lever (pivot at the pillar's back edge)"""
    nb = cad["build"]["neck_stop"]
    ax_p, ax_d = S.joint_world("neck_pitch")
    c, n = np.array(nb["pad_face_centre"]), np.array(nb["pad_normal"])
    v = _edge_motion(ax_p, ax_d, c)
    slide = float(np.sqrt(max(0.0, 1.0 - float(v @ n) ** 2)))             # tangential fraction of the pad force
    pl = cad["placements"]["neck_stop"][0]
    m = trimesh.load(os.path.join(L.PRINT, "neck_stop.stl"), force="mesh")
    m.apply_transform(S.T0[pl["link"]] @ np.array(pl["T_link_mm"]))
    # the pillar's base: the lowest level where the right half's section is the pillar's footprint (100 mm2 or more), not
    # the flange lobe's spigot in the trunk_top screw recess below it; the section there is the pillar with its screw
    # lobe, less the screw hole
    z_base = None
    for z in np.arange(float(m.bounds[0][2]) + 0.5, float(m.bounds[0][2]) + 12.0, 0.5):
        try:
            A, I, cc, x_min, x_max = _composite_at_z(m, float(z), lambda y: y.min() > 0)
        except SystemExit:
            continue
        if A >= 100.0:
            z_base = float(z) - 0.5
            break
    if z_base is None:
        raise SystemExit("neck block: no pillar footprint of 100 mm2 within 12 mm of the bottom")
    # the pillar just above the flange (the foot behind it and the screw lobes end there): the pillar alone in bending
    z_fl = z_base + SC.FLANGE_T
    A2, I2, cc2, xmin2, xmax2 = _composite_at_z(m, z_fl + 0.5, lambda y: y.min() > 0)
    pad = L.STOP_STACK["neck_back"]["pads"][0]
    return dict(centre=c, normal=n, r=lever(ax_p, ax_d, c, n), r_centre=float(nb["pad_r_mm"]), slide=slide, pad_area=pad[0] * pad[1], pad_len=pad[0], pad_w=pad[1],
                edge_w=nb["sheet_back_edge_y"][1] - nb["sheet_back_edge_y"][0], base=dict(A=A, W=I / cc, x_min=x_min, x_max=x_max, z=z_base),
                pillar=dict(A=A2, W=I2 / cc2, x_min=xmin2, x_max=xmax2, z=z_fl),
                screw_x=SC.NECK_SCREWS[0][0], pocket=SC.POCKET, volume=nb["volume_mm3"])


def neck_rows(rows, G, Tn, case, need, label="calc"):
    """one face carries the whole stop torque (no sharing between the two pillars)"""
    F = Tn * 1000.0 / G["r"]
    load = "fall" if case in ("fall", "abuse") else "service"

    def add(name, sigma, allow, what, lab=label):
        r = check(name, sigma, allow, load, label=lab, what=what)
        r["need"], r["ok"], r["case"] = need, bool((allow / sigma if sigma > 1e-9 else 1e9) >= need), case
        rows.append(r)
    add("neck pad (TPU bearing)", F / G["pad_area"], TPU_BEARING, "F %.1f N on the %.1f mm lever of the pad's normal (pad centre r %.1f) over %.0f mm2 (one face)" % (F, G["r"], G["r_centre"], G["pad_area"]), "calc, est")
    add("neck sheet back edge (in-plane bearing)", F / (G["edge_w"] * G["pad_len"]), X_INPLANE,
        "the stock sheet's %.1f mm back edge over the %.0f mm pad, the load in the sheet's plane" % (G["edge_w"], G["pad_len"]))
    add("neck pad pocket wall (the slide, across the layers)", F * G["slide"] / (G["pad_w"] * G["pocket"]), Z_INTER,
        "%.2f of F along the face = %.1f N on the %.1f x %.1f mm pocket wall" % (G["slide"], F * G["slide"], G["pad_w"], G["pocket"]))
    # the pillar base: the pad force (along -n) at the pad centre, moment about the base section centroid (bending about y)
    c, n, b = G["centre"], G["normal"], G["base"]
    Fv = -n * F
    xc = 0.5 * (b["x_min"] + b["x_max"])
    M = abs(Fv[0] * (c[2] - b["z"]) - Fv[2] * (c[0] - xc))
    add("neck pillar base (bending, across the layers)", M / b["W"] + abs(Fv[2]) / b["A"], Z_INTER,
        "M %.0f N mm on W %.0f mm3 plus %.1f N on %.0f mm2 (the block prints standing: the base is a layer plane)" % (M, b["W"], abs(Fv[2]), b["A"]))
    b2 = G["pillar"]
    xc2 = 0.5 * (b2["x_min"] + b2["x_max"])
    M2 = abs(Fv[0] * (c[2] - b2["z"]) - Fv[2] * (c[0] - xc2))
    add("neck pillar above the flange (bending, across the layers)", M2 / b2["W"] + abs(Fv[2]) / b2["A"], Z_INTER,
        "M %.0f N mm on W %.0f mm3 plus %.1f N on %.0f mm2 at z %.1f (the pillar alone, over the foot and the lobes)" % (M2, b2["W"], abs(Fv[2]), b2["A"], b2["z"]))
    # the screw: the block tips about its back bottom edge; the screw at x_screw holds it
    Mp = abs(Fv[0]) * (c[2] - b["z"]) - abs(Fv[2]) * (c[0] - b["x_min"])   # the backward push lifts the front, the downward part holds it
    Ts = max(0.0, Mp) / (G["screw_x"] - b["x_min"])
    r = dict(part="neck block screw F127 or F129 (pull-out, one screw)", load=load, case=case, stress_MPa=None, force_N=round(Ts, 1),
             allowable_MPa=None, SF=round(SCREW_PULLOUT_N / Ts, 2) if Ts > 1e-6 else None, need=need, ok=bool(Ts < 1e-6 or SCREW_PULLOUT_N / Ts >= need),
             label="calc, est; BLOCKER: pull-out not measured",
             what="tip moment %.0f N mm about the pillar's back edge (x %.1f), screw lever %.1f mm: %.1f N against %.0f N est" % (
                 max(0.0, Mp), b["x_min"], G["screw_x"] - b["x_min"], Ts, SCREW_PULLOUT_N))
    rows.append(r)


def head_geometry(S, cad):
    """the head hook as built: the pad; the hook's root on the stock yoke (the doubler glued to the left arm's outer face:
    its face area and polar modulus, for the in-plane moment the face carries in shear); the composite section (arm plus
    doubler) cut level with the root centroid, which carries that moment across the layers; the foot plate's section"""
    hh = cad["build"]["head_pitch_to_yaw"]
    ax_p, ax_d = S.joint_world("head_pitch")
    c, n = np.array(hh["pad_face_centre"]), np.array(hh["pad_normal"])
    v = _edge_motion(ax_p, ax_d, c)
    slide = float(np.sqrt(max(0.0, 1.0 - float(v @ n) ** 2)))
    i = L.inst(S, "head_pitch_to_yaw", "head_pitch_to_yaw")
    Tw = L.inst_world(S, i)
    new_m = S.world_mesh(i)
    new = L.to_man(new_m)
    old_m = L.base_mesh("print/head_pitch_to_yaw.stl")
    old_m.apply_transform(Tw)
    old = L.to_man(old_m)
    hook = new - old
    root = hook ^ (L.dilate(old, 0.5) - old)
    if hook.volume() < 1.0 or root.volume() < 0.5:
        raise SystemExit("head hook: no hook on head_pitch_to_yaw (%.1f mm3, root %.1f)" % (hook.volume(), root.volume()))
    A = root.volume() / 0.5
    rm = L.from_man(root)
    rc = rm.center_mass
    # the root face lies in the x z plane (the arm's outer face): its polar modulus about the centroid for a moment about y
    P = np.asarray(rm.vertices)[:, [0, 2]]
    Jp = float(((P - P.mean(0)) ** 2).sum(1).mean()) * A
    r_max = float(np.sqrt(((P - P.mean(0)) ** 2).sum(1)).max())
    fdir = -n                                                           # the force on the hook, from the sheet
    arm = float(np.linalg.norm(np.cross(rc - c, fdir)))                # lever of the force line about the root centroid
    # the composite section (arm plus doubler) level with the root centroid, left arm (y > 12): bending about y
    from shapely.geometry import Polygon
    sec = new_m.section(plane_origin=[0, 0, float(rc[2])], plane_normal=[0, 0, 1])
    loops = [np.asarray(l)[:, :2] for l in sec.discrete if np.asarray(l)[:, 1].min() > 12.0]
    if not loops:
        raise SystemExit("head hook: no left arm section at z %.1f" % rc[2])
    polys = [Polygon(l) for l in loops]
    outer = max(polys, key=lambda q: q.area)
    holes = [q for q in polys if q is not outer and outer.contains(q)]
    Aa = outer.area - sum(q.area for q in holes)
    cx = (outer.centroid.x * outer.area - sum(q.centroid.x * q.area for q in holes)) / Aa
    def Ix(q):
        Ai, Ii, ci = section_props(np.asarray(q.exterior.coords), (0.0, 1.0))
        return Ii + Ai * (q.centroid.x - cx) ** 2
    Ia = Ix(outer) - sum(Ix(q) for q in holes)
    cmax = max(abs(outer.bounds[2] - cx), abs(outer.bounds[0] - cx))
    comp = dict(A=Aa, W=Ia / cmax, z=float(rc[2]), lever=float(np.linalg.norm(np.cross(np.array([cx, rc[1], rc[2]]) - c, fdir))))
    # the foot plate: a vertical cut at x 13 (between the drop and the foot), y > 12
    sec = new_m.section(plane_origin=[13.0, 0, 0], plane_normal=[1, 0, 0])
    loops = [np.asarray(l) for l in sec.discrete if np.asarray(l)[:, 1].min() > 12.0 and np.asarray(l)[:, 2].max() < 150.0]
    if not loops:
        raise SystemExit("head hook: no foot section at x 13")
    fp = max(loops, key=lambda l: Polygon(l[:, [1, 2]]).area)
    Af, If, cf = section_props(fp[:, [1, 2]], (1.0, 0.0))                # bending about y: the extreme fibre along z
    fc = np.array([13.0, Polygon(fp[:, [1, 2]]).centroid.x, Polygon(fp[:, [1, 2]]).centroid.y])
    foot = dict(A=Af, W=If / cf, lever=float(np.linalg.norm(np.cross(fc - c, fdir))))
    pad = L.STOP_STACK["head_fwd"]["pads"][0]
    return dict(centre=c, normal=n, r=lever(ax_p, ax_d, c, n), r_centre=float(hh["pad_r_mm"]), slide=slide, pad_area=pad[0] * pad[1], pad_len=pad[0], pad_w=pad[1],
                edge_w=hh["sheet_front_edge_y"][1] - hh["sheet_front_edge_y"][0], root=dict(A=A, Jp=Jp, r_max=r_max, arm=arm, centre=rc),
                composite=comp, foot=foot, pocket=SC.POCKET, hook_mm3=hh["hook_mm3"], axis=(ax_p, ax_d))


def head_rows(rows, G, Tn, case, need, label="calc"):
    F = Tn * 1000.0 / G["r"]
    load = "fall" if case in ("fall", "abuse") else "service"

    def add(name, sigma, allow, what, lab=label):
        r = check(name, sigma, allow, load, label=lab, what=what)
        r["need"], r["ok"], r["case"] = need, bool((allow / sigma if sigma > 1e-9 else 1e9) >= need), case
        rows.append(r)
    add("head pad (TPU bearing)", F / G["pad_area"], TPU_BEARING, "F %.1f N at r %.1f mm over %.0f mm2" % (F, G["r"], G["pad_area"]), "calc, est")
    add("neck sheet front edge (in-plane bearing)", F / (G["edge_w"] * G["pad_len"]), X_INPLANE,
        "the stock left sheet's %.1f mm front edge over the %.0f mm pad, the load in the sheet's plane" % (G["edge_w"], G["pad_len"]))
    add("head pad pocket wall (the slide, across the layers)", F * G["slide"] / (G["pad_w"] * G["pocket"]), Z_INTER,
        "%.2f of F along the face = %.1f N on the %.1f x %.1f mm pocket wall" % (G["slide"], F * G["slide"], G["pad_w"], G["pocket"]))
    rt, cp, ft = G["root"], G["composite"], G["foot"]
    M = F * rt["arm"]
    add("head hook root face on the arm (shear across the layers, est)", M * rt["r_max"] / rt["Jp"] + F / rt["A"], INTER_SHEAR,
        "the doubler's face on the arm, %.0f mm2, carries M %.0f N mm (lever %.1f mm) in shear: Jp %.0f mm4, r %.1f mm" % (rt["A"], M, rt["arm"], rt["Jp"], rt["r_max"]), "calc, est")
    Mc = F * cp["lever"]
    add("yoke left arm with the doubler, level with the root (bending across the layers)", Mc / cp["W"] + F / cp["A"], Z_INTER,
        "the composite section at z %.1f: net %.0f mm2, W %.0f mm3, M %.0f N mm (lever %.1f mm)" % (cp["z"], cp["A"], cp["W"], Mc, cp["lever"]))
    Mf = F * ft["lever"]
    add("head hook foot plate at x 13 (bending, in the plate)", Mf / ft["W"] + F / ft["A"], X_INPLANE,
        "the 4 mm plate outboard of the sheet: %.0f mm2, W %.0f mm3, M %.0f N mm (lever %.1f mm); the plate prints flat" % (ft["A"], ft["W"], Mf, ft["lever"]))


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
        if lug.volume() < 1.0:
            out[key] = None
            continue
        rec = json.load(open(os.path.join(HERE, "sit_cad.json")))["build"].get("left_roll_to_pitch", {}) if key == "roll" else {}
        if rec.get("pad_face_centre"):
            # the lug carries a TPU face (sit_cad.py roll_pad): the contact is the pad face, the force along its normal
            cpt, fdir, vsum = np.array(rec["pad_face_centre"], float), -np.array(rec["pad_normal"], float), float(rec.get("touch_mm3", 0.0))
        else:
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
            if not ov:
                out[key] = None
                continue
            v = np.array([o[0] for o in ov])
            cpt = (np.array([o[1] for o in ov]) * v[:, None]).sum(0) / v.sum()
            # motion of the counterpart at the contact point between the two poses: the force on the lug is along it
            p1 = (T2 @ np.linalg.inv(T) @ np.r_[cpt, 1])[:3]
            fdir = p1 - cpt
            fdir = fdir / np.linalg.norm(fdir)
            vsum = float(v.sum())
        rc = L.from_man(root).center_mass if root.volume() > 1e-3 else L.from_man(lug).center_mass
        A = max(root.volume() / 0.5, 1e-3)
        arm = float(np.linalg.norm(np.cross(rc - cpt, fdir)))
        out[key] = dict(contact=np.round(cpt, 2).tolist(), force_dir=np.round(fdir, 3).tolist(), root_area=round(A, 1),
                        root_W=round(A ** 1.5 / 6.0, 1), arm=round(arm, 1), lug_mm3=round(lug.volume(), 1), touch_mm3=round(vsum, 2),
                        pad_bearing_mm2=rec.get("bearing_mm2"), pad_r_mm=rec.get("pad_r_mm"))
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
    if not a.sim or not a.model:
        raise SystemExit("needs --sim (the loads and shove results) and --model (the sit model folder)")
    designed_end_ok()
    inkey = None
    if a.model:
        import sit_sim as SS
        inkey = SS.inputs_key(os.path.dirname(os.path.normpath(a.model)))
    paths = [p for p in a.sim.split(",") if p]
    load_paths = [p for p in paths if not os.path.basename(p).startswith("sit_sim_shove")]
    shove_paths = [p for p in paths if os.path.basename(p).startswith("sit_sim_shove")]
    if a.write and not shove_paths:
        raise SystemExit("--write needs the head shove results (sit_sim.py shove: sit_sim_shove.json) in --sim")
    stops_md = json.load(open(os.path.join(a.model, "sit_model.json")))["stops"] if a.model else {}
    EP = energy_peaks(stop_loads(load_paths, key=inkey), stops_md)
    EA = energy_peaks(stop_loads(load_paths, abuse=True, key=inkey), stops_md)
    T = {j: v["design_Nm"] for j, v in EP.items()}
    TA = {j: v["design_Nm"] for j, v in EA.items()}
    REST = {j: v["rest_Nm"] for j, v in EP.items()}
    rows, loads = [], {}
    loads["energy_method"] = dict(label="calc only", service=EP, abuse=EA,
                                  note="design = max(omega sqrt(I K) + rest, sustained 100 ms mean); sim_over_design is the compliant-stop sim's own peak over it (0.5 ms step)")
    radii = stack_check(S, cad)

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
    for load, Tn in (("service", t_srv), ("fall", 2 * t_srv), ("stall", STALL["knee"] + REST.get("left_knee", 0.0)), ("abuse", tqa("knee"))):
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
    for load, Tn in (("service", t_a), ("fall", 2 * t_a), ("stall", STALL["other"] + REST.get("left_ankle", 0.0)), ("abuse", tqa("ankle"))):
        F = Tn * 1000.0 / max(r_a, 1e-6) / 2
        rows.append(check("ankle pad (bearing, per pad)", F / A_pad, 10.0, "fall" if load in ("fall", "abuse") else "service",
                          what="2 pads, %.1f N each over %.0f mm2" % (F, A_pad), label="calc, est"))
        rows[-1]["case"] = load
        rows.append(check("foot plate pad seat (bearing)", F / A_pad, Z_INTER, "fall" if load in ("fall", "abuse") else "service",
                          what="PLA seat under the pad, across the layers (conservative)"))
        rows[-1]["case"] = load

    # ---------------- lugs: contact force on the lug face; root section measured on the STL
    def lug_rows(name, joint, axis, contact, fdir, root_area, root_W, arm, tn, stall, ta, bearing=None, pad_r=None):
        r_ = lever(axis[0], axis[1], contact, fdir)
        loads[name] = dict(service_Nm=round(tn, 3), lever_mm=round(r_, 1), pad_centre_r_mm=pad_r, pad_bearing_mm2=bearing,
                           root_area_mm2=round(root_area, 1), root_W_mm3=round(root_W, 1), arm_mm=round(arm, 1))
        for load, Tn in (("service", tn), ("fall", 2 * tn), ("stall", stall), ("abuse", ta)):
            F = Tn * 1000.0 / max(r_, 1e-6)
            ld = "fall" if load in ("fall", "abuse") else "service"
            if bearing:
                rows.append(check(name.replace("lug root (bending, across the layers)", "pad (TPU bearing)"), F / bearing, TPU_BEARING, ld, label="calc, est",
                                  what="F %.1f N on the %.1f mm lever of the pad's normal (pad centre r %.1f) over the case's %.0f mm2 on the face" % (F, r_, pad_r or 0.0, bearing)))
                rows[-1]["case"] = load
            sig = F / root_area + F * arm / root_W
            rows.append(check(name, sig, Z_INTER, ld,
                              what="F %.1f N at r %.1f mm; root %.0f mm2, W %.0f mm3, arm %.1f mm (across the layers, conservative)" % (F, r_, root_area, root_W, arm)))
            rows[-1]["case"] = load

    lugs = lug_geometry_cached(S)
    loads["lug_geometry"] = lugs
    loads["stop_radii_mm"] = radii
    g = lugs.get("roll")
    if not g:
        raise SystemExit("no hip roll lug on left_roll_to_pitch")
    p_, d_ = S.joint_world("left_hip_roll")
    lug_rows("roll stop lug root (bending, across the layers)", "left_hip_roll", (p_, d_), g["contact"], g["force_dir"], g["root_area"], g["root_W"], g["arm"],
             tq("hip_roll"), STALL["other"] + REST.get("left_hip_roll", 0.0), tqa("hip_roll"), bearing=g.get("pad_bearing_mm2"), pad_r=g.get("pad_r_mm"))
    # ---------------- the neck block and the head hook (TPU faces in pockets on parts of ours)
    GN, GH = neck_geometry(S, cad), head_geometry(S, cad)
    loads["neck_stop"] = dict(service_Nm=round(tq("neck_pitch"), 3), lever_mm=round(GN["r"], 1), pad_centre_r_mm=round(GN["r_centre"], 1), slide_fraction=round(GN["slide"], 3),
                              pillar_A_mm2=round(GN["pillar"]["A"], 1), pillar_W_mm3=round(GN["pillar"]["W"], 1), pillar_z=round(GN["pillar"]["z"], 1),
                              base_A_mm2=round(GN["base"]["A"], 1), base_W_mm3=round(GN["base"]["W"], 1), base_x=[round(GN["base"]["x_min"], 1), round(GN["base"]["x_max"], 1)])
    loads["head_hook"] = dict(service_Nm=round(tq("head_pitch"), 3), lever_mm=round(GH["r"], 1), pad_centre_r_mm=round(GH["r_centre"], 1),
                              slide_fraction=round(GH["slide"], 3), hook_mm3=GH["hook_mm3"],
                              root_area_mm2=round(GH["root"]["A"], 1), root_Jp_mm4=round(GH["root"]["Jp"], 0), root_arm_mm=round(GH["root"]["arm"], 1),
                              composite_A_mm2=round(GH["composite"]["A"], 1), composite_W_mm3=round(GH["composite"]["W"], 1),
                              foot_A_mm2=round(GH["foot"]["A"], 1), foot_W_mm3=round(GH["foot"]["W"], 1))
    for case, Tn, need in (("service", tq("neck_pitch"), SF_SERVICE), ("fall", 2 * tq("neck_pitch"), SF_FALL),
                           ("stall", STALL["other"] + REST.get("neck_pitch", 0.0), SF_SERVICE), ("abuse", tqa("neck_pitch"), SF_FALL)):
        neck_rows(rows, GN, Tn, case, need)
    for case, Tn, need in (("service", tq("head_pitch"), SF_SERVICE), ("fall", 2 * tq("head_pitch"), SF_FALL),
                           ("stall", STALL["other"] + REST.get("head_pitch", 0.0), SF_SERVICE), ("abuse", tqa("head_pitch"), SF_FALL)):
        head_rows(rows, GH, Tn, case, need)

    # ---------------- shoves on the head (12 N, body held) and the neck stall: one face carries it all
    SH = {}
    for p in shove_paths:
        J_ = json.load(open(p))
        if inkey is not None and J_.get("inputs_key") != inkey:
            raise SystemExit("%s was run on another model or sim code" % os.path.basename(p))
        for r in J_["results"]:
            SH[r["name"]] = r
    import mujoco as m
    import sit_model as SM
    md = SM.load(a.model)
    dd = m.MjData(md)
    P = json.load(open(os.path.join(HERE, "sit_pose.json")))
    for jn_, v in P["joints_deg"].items():
        dd.qpos[md.jnt_qposadr[m.mj_name2id(md, m.mjtObj.mjOBJ_JOINT, jn_)]] = np.radians(v)
    m.mj_forward(md, dd)
    hd_b = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, "head_assembly")

    def axis_static(jn):
        """gravity torque at the joint in the sit pose, and the arm of a horizontal shove at the head's CoM about it"""
        j = m.mj_name2id(md, m.mjtObj.mjOBJ_JOINT, jn)
        T_g = abs(float(dd.qfrc_bias[md.jnt_dofadr[j]]))
        arm = abs(float(dd.xipos[hd_b][2] - dd.xanchor[j][2]))            # a horizontal force: the arm is the height difference (m)
        return T_g, arm
    for jn, end, G, rowfn, direction, name in (("head_pitch", "lo", GH, head_rows, "forward", "head"), ("neck_pitch", "hi", GN, neck_rows, "back", "neck")):
        T_g, arm = axis_static(jn)
        for tq_ in ("off", "on"):
            cs = [r for n_, r in SH.items() if r["opt"]["dir"] == direction and r["opt"]["torque"] == tq_ and r["opt"].get("held")]
            if not cs:
                continue
            k_ = "%s:%s" % (jn, end)
            for r in cs:
                for fld in ("limit_omega_max", "limit_torque_rest", "limit_torque_max", "limit_torque_sustained", "limit_torque_loaded"):
                    if fld not in r:
                        raise SystemExit("%s has no %s: rerun sit_sim.py shove" % (r["name"], fld))
            w_ = max(r["limit_omega_max"].get(k_, 0.0) for r in cs)
            if jn == "head_pitch":
                # the neck's own slams (its far end -20 under a forward shove, its +25 stop) carry the head, which rests on
                # its stop, with them: the head stop takes the head's share of that energy too (conservative)
                w_ = max([w_] + [r["limit_omega_max"].get("neck_pitch:%s" % e_, 0.0) for r in cs for e_ in ("lo", "hi")])
            rest_ = max(r["limit_torque_rest"].get(k_, 0.0) for r in cs)
            sus_ = max(r["limit_torque_sustained"].get(k_, 0.0) for r in cs)
            raw_ = max(r["limit_torque_loaded"].get(k_, 0.0) for r in cs)
            sim_ = max(r["limit_torque_max"].get(k_, 0.0) for r in cs)
            T_e = w_ * float(np.sqrt(stops_md[jn]["I_eff_held"] * stops_md[jn]["K_Nm_rad"])) + rest_
            T_calc = SHOVE_N * arm + T_g                                    # the sustained shove, by hand (arm in m: MuJoCo)
            Tn = max(T_e, sus_, T_calc)
            loads["shove %s %s torque %s" % (jn, direction, tq_)] = dict(
                omega_rad_s=round(w_, 3), energy_Nm=round(T_e, 3), sustained_sim_Nm=round(sus_, 3), loaded_raw_Nm=round(raw_, 3),
                sustained_calc_Nm=round(T_calc, 3), calc=dict(shove_N=SHOVE_N, arm_mm=round(arm * 1000.0, 1), gravity_Nm=round(T_g, 3)),
                design_Nm=round(Tn, 3), sizing="impact" if Tn == T_e else ("sustained (sim)" if Tn == sus_ else "sustained (calc)"),
                sim_Nm=round(sim_, 3), sim_over_design=round(sim_ / Tn, 2) if Tn > 1e-6 else None, cases=[r["name"] for r in cs])
            rowfn(rows, G, Tn, "shove", SF_SHOVE, label="calc only (energy and sustained, omega and the 100 ms mean from the sim; stop K %.0f N m/rad)" % stops_md[jn]["K_Nm_rad"])
            for r_ in rows[-5:]:
                r_["part"] = "%s stop, %d N shove %s on the head, torque %s: %s" % (name, SHOVE_N, direction, tq_, r_["part"])
    T_g, _ = axis_static("neck_pitch")
    Tn = STALL["other"] + T_g
    loads["neck stall"] = dict(stall_Nm=STALL["other"], gravity_Nm=round(T_g, 3), F_N=round(Tn * 1000.0 / GN["r"], 1))
    n0 = len(rows)
    neck_rows(rows, GN, Tn, "stall_shove", SF_SHOVE)
    for r_ in rows[n0:]:
        r_["part"] = "neck stop at a servo stall (one face): " + r_["part"]
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
