#!/usr/bin/env python3
"""sit_pose.py: the settled torque-off sit pose from the sim, the sit renders posed by it, and the check that every
record and render of the sit pose agrees with the sim. sim pass only (the pose); CAD check only (the renders).

  python3 altaay_lab/twin/sit/sit_pose.py --out <scratch>/model settle      the sim settle, writes sit_pose.json
  python3 altaay_lab/twin/sit/sit_pose.py --out <scratch>/model check       a fresh settle against sit_pose.json and
                                                                            sit_sim.json (fails past PITCH_TOL)
  python3 altaay_lab/twin/sit/sit_pose.py render --img <folder outside the repo>   sit_side, sit_front, sit_three_quarter

settle: the repo sim model (sit_model.py) stands, sits down the A1b path with torque on (sit_sim.enter), lets the torque
go and rests 20 s on the dock pads with no push (sit_sim.hold). The record is the trunk pose (MuJoCo trunk_assembly
body, which is the robot.urdf base frame: settle fails if any link frame of the sim differs from the URDF's by more than
0.01 mm) and every joint angle at the end; trunk pitch is sit_sim.trunk_state's (nose up positive).
render: robot.urdf with the print/ STLs of the tree, every link placed by the URDF kinematics at the recorded joint
angles and the trunk at the recorded sim pose; no placement of its own. It measures the trunk pitch of the posed meshes
and the floor gap of the seat and soles and refuses to write when the pitch is more than PITCH_TOL off the record.
Why: the first sit renders placed the robot by a separate kinematic step (the commanded angles, 3 deg short of the
stops, rotated until the seat and the soles' lowest points were level) and drew it 14 deg nose up; the sim rests at
+2.7 deg (SIT.md section 5).
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitlib as L  # noqa: E402

POSE = os.path.join(HERE, "sit_pose.json")
PITCH_TOL = 2.0                   # deg: a render or record of the sit pose may differ from the sim by this much
FRAME_TOL_MM = 0.01
SKIP = {"usb_c_charger", "power_switch", "bms", "bno055", "board", "cell", "holder", "raspberrypizerow"}
TPU_KEYS = ("knee_bumper", "ankle_pad", "hip_pad", "roll_pad_left", "roll_pad_right", "sit_seat", "sit_bumper", "foot_bottom_tpu")


def settle(out, T=20.0):
    """the sim's settled torque-off sit: trunk pose, joint angles, pads (sim pass only)"""
    import mujoco as m
    import sit_sim as SS
    SS.OUT[0] = out
    md = SS.model(out)
    dd, SF, pins, _, _ = SS.enter(md)
    r = SS.hold(md, dd, SF, pins, F=0.0, dirs=[], T=T, t_first=T - 5.0)
    ts = SS.trunk_state(md, dd)
    joints = {m.mj_id2name(md, m.mjtObj.mjOBJ_JOINT, j): float(dd.qpos[md.jnt_qposadr[j]]) for j in range(1, md.njnt)}
    tb = m.mj_name2id(md, m.mjtObj.mjOBJ_BODY, "trunk_assembly")
    S = L.scene(fresh=True)
    Tl = S.link_T(joints)
    Tt = body_T(dd, tb)
    worst = 0.0
    for b in range(1, md.nbody):
        n = m.mj_id2name(md, m.mjtObj.mjOBJ_BODY, b)
        if n in Tl:
            worst = max(worst, float(np.linalg.norm((np.linalg.inv(Tt) @ body_T(dd, b))[:3, 3] - Tl[n][:3, 3])))
    if worst > FRAME_TOL_MM:
        raise SystemExit("the sim's link frames differ from robot.urdf by %.3f mm: the pose cannot be carried over" % worst)
    return dict(trunk_T_mm=np.round(Tt, 6).tolist(), trunk_pitch_deg=round(ts["pitch"], 2), trunk_roll_deg=round(ts["roll"], 2),
                trunk_z_mm=round(ts["z"] * 1000, 1), joints_deg={k: round(float(np.degrees(v)), 3) for k, v in joints.items()},
                pads=r["pads_final"], head_elev_deg=round(r["head_elev"], 2), frame_mismatch_mm=round(worst, 5),
                inputs_key=SS.inputs_key(out))


def body_T(dd, b):
    T = np.eye(4)
    T[:3, :3] = dd.xmat[b].reshape(3, 3)
    T[:3, 3] = dd.xpos[b] * 1000.0
    return T


def pitch_of(R):
    """sit_sim.trunk_state's pitch of a trunk rotation (nose up positive)"""
    return float(np.degrees(np.arcsin(np.clip(R[2, 0], -1, 1))))


def posed_meshes(P):
    """every URDF mesh at the recorded pose (mm, the sim world: floor at z 0)"""
    S = L.scene(fresh=True)
    Tl = S.link_T({k: np.radians(v) for k, v in P["joints_deg"].items()})
    Tt = np.array(P["trunk_T_mm"])
    out = []
    for i in S.inst:
        if i["key"] in SKIP:
            continue
        mm_ = S.world_mesh(i).copy()
        mm_.apply_transform(Tt @ Tl[i["link"]] @ np.linalg.inv(S.T0[i["link"]]))
        out.append((i, mm_))
    return out, Tt @ Tl["trunk_assembly"]


def render_check(P):
    """the trunk pitch and the seat and sole floor gaps of the posed meshes (what the render draws)"""
    items, Ttr = posed_meshes(P)
    pitch = pitch_of(Ttr[:3, :3])
    low = {}
    for i, mm_ in items:
        if i["key"] in ("sit_seat", "sit_bumper", "foot_bottom_tpu"):
            k = i["key"] if i["key"] != "foot_bottom_tpu" else "sole_" + i["link"]
            low[k] = round(float(mm_.bounds[0][2]), 2)
    return items, dict(pitch_deg=round(pitch, 2), lowest_z_mm=low)


def check_rest(rc, tol=2.0):
    """the posed seat and both soles rest on the floor (z 0 of the sim world) within tol mm: the pose is the resting one"""
    bad = {k: v for k, v in rc["lowest_z_mm"].items() if k != "sit_bumper" and abs(v) > tol}
    if bad:
        raise SystemExit("the posed seat or soles are off the floor by more than %.1f mm: %s" % (tol, bad))


def check_pose(P, pitch_sim, what):
    d = abs(P - pitch_sim)
    if d > PITCH_TOL:
        raise SystemExit("%s trunk pitch %.2f deg differs from the sim's settled %.2f deg by %.2f (more than %.1f)" % (
            what, P, pitch_sim, d, PITCH_TOL))
    return round(d, 2)


def render(img):
    import trimesh
    os.environ.setdefault("MUJOCO_GL", "egl")
    P = json.load(open(POSE))
    items, rc = render_check(P)
    check_pose(rc["pitch_deg"], P["trunk_pitch_deg"], "the render's")
    check_rest(rc)
    sit_keys = {"shin_left_sheet", "shin_right_sheet", "shin_spacer", "neck_left_sheet", "neck_right_sheet", "head_pitch_to_yaw",
                "left_roll_to_pitch", "right_roll_to_pitch", "left_cache", "right_cache", "foot_top", "foot_side",
                "knee_to_ankle_left_sheet", "knee_to_ankle_right_sheet"}
    draw = []
    for i, mm_ in items:
        col = (0.25, 0.25, 0.25, 1) if i["key"] in TPU_KEYS else ((1.0, 0.6, 0.3, 1) if i["key"] in sit_keys else (0.8, 0.8, 0.8, 1))
        draw.append((mm_, col))
    lo = np.min([m_.bounds[0] for m_, _ in draw], 0)
    hi = np.max([m_.bounds[1] for m_, _ in draw], 0)
    floor = trimesh.creation.box((400, 300, 1))
    floor.apply_translation([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, -0.5])
    draw.append((floor, (0.9, 0.95, 0.9, 1)))
    J = P["joints_deg"]
    cap = ("A1b sit, torque off, sim settled pose (sit_pose.json from sit_sim.py, sim pass only): trunk pitch %+.1f deg nose up, "
           "trunk z %.0f mm; hip %.1f, knee %.1f, ankle %.1f, roll %.1f, neck %.1f, head %.1f; robot.urdf + print/ STLs" % (
               P["trunk_pitch_deg"], P["trunk_z_mm"], J["left_hip_pitch"], J["left_knee"], J["left_ankle"], J["left_hip_roll"],
               J["neck_pitch"], J["head_pitch"]))
    look = (lo + hi) / 2000.0
    for name, az, el in (("side", 90, -5), ("front", 0, -5), ("three_quarter", 45, -20)):
        _render(draw, az, el, 0.95, look, os.path.join(img, "sit_%s.png" % name), cap)
    print("rendered: trunk pitch %.2f deg (record %.2f), lowest z %s" % (rc["pitch_deg"], P["trunk_pitch_deg"], rc["lowest_z_mm"]))


def _render(items, az, el, dist, look, out, title, w=1000, h=900):
    """MuJoCo offscreen render of meshes in mm (sit_cad.py figures use the same light and camera)"""
    import tempfile
    import mujoco
    from PIL import Image, ImageDraw
    d = tempfile.mkdtemp(prefix="sit_render_")
    assets, geoms = [], []
    for k, (m_, rgba) in enumerate(items):
        p = os.path.join(d, "m%d.stl" % k)
        c = m_.copy()
        c.apply_scale(0.001)
        c.export(p)
        assets.append('<mesh name="m%d" file="%s"/>' % (k, p))
        geoms.append('<geom type="mesh" mesh="m%d" rgba="%s" contype="0" conaffinity="0"/>' % (k, " ".join(map(str, rgba))))
    xml = ('<mujoco><visual><global offwidth="%d" offheight="%d" fovy="30"/><headlight ambient="0.35 0.35 0.35" '
           'diffuse="0.6 0.6 0.6"/><quality offsamples="8"/></visual><asset>%s</asset><worldbody><light pos="0.5 -0.5 1" '
           'dir="-0.4 0.4 -0.8" diffuse="0.4 0.4 0.4"/>%s</worldbody></mujoco>' % (w, h, "".join(assets), "".join(geoms)))
    md = mujoco.MjModel.from_xml_string(xml)
    dd = mujoco.MjData(md)
    mujoco.mj_forward(md, dd)
    r = mujoco.Renderer(md, h, w)
    cam = mujoco.MjvCamera()
    cam.lookat[:] = look
    cam.azimuth, cam.elevation, cam.distance = az, el, dist
    r.update_scene(dd, cam)
    im = Image.fromarray(r.render())
    r.close()
    dr = ImageDraw.Draw(im)
    words, line, y = title.split(" "), "", 8
    for wd in words:                      # wrap the caption to the image width
        if len(line) + len(wd) > 150:
            dr.text((10, y), line, fill=(255, 255, 255))
            line, y = "", y + 14
        line += wd + " "
    dr.text((10, y), line, fill=(255, 255, 255))
    im.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=("settle", "check", "render"))
    ap.add_argument("--out", help="the sit_sim.py --out folder (the model in <out>/sit)")
    ap.add_argument("--img", help="render: the image folder (outside the repo)")
    a = ap.parse_args()
    if a.what == "render":
        render(a.img)
        return
    P = settle(a.out)
    _, rc = render_check(P)
    P["render_pitch_deg"] = rc["pitch_deg"]
    P["render_lowest_z_mm"] = rc["lowest_z_mm"]
    check_pose(rc["pitch_deg"], P["trunk_pitch_deg"], "the posed meshes'")
    check_rest(rc)
    if a.what == "settle":
        L.dump(dict(generated_by="altaay_lab/twin/sit/sit_pose.py settle", label="sim pass only", pitch_tol_deg=PITCH_TOL, **P), POSE)
        print("wrote altaay_lab/twin/sit/sit_pose.json: trunk pitch %.2f deg, z %.1f mm" % (P["trunk_pitch_deg"], P["trunk_z_mm"]))
        return
    R = json.load(open(POSE))
    if R.get("inputs_key") != P["inputs_key"]:
        raise SystemExit("sit_pose.json was settled on another model or sim code: run settle again")
    check_pose(R["trunk_pitch_deg"], P["trunk_pitch_deg"], "sit_pose.json's")
    check_pose(R["render_pitch_deg"], P["trunk_pitch_deg"], "the render record's")
    SJ = json.load(open(os.path.join(HERE, "sit_sim.json")))
    lo_, hi_ = SJ["push"]["pitch_deg"]
    if not (lo_ - PITCH_TOL <= P["trunk_pitch_deg"] <= hi_ + PITCH_TOL):
        raise SystemExit("the settled pitch %.2f is outside sit_sim.json's push pitch range %s by more than %.1f deg" % (
            P["trunk_pitch_deg"], [lo_, hi_], PITCH_TOL))
    print("sit pose check: PASS (sim %.2f, record %.2f, render %.2f, push range %s, tol %.1f deg)" % (
        P["trunk_pitch_deg"], R["trunk_pitch_deg"], R["render_pitch_deg"], [lo_, hi_], PITCH_TOL))


if __name__ == "__main__":
    main()
