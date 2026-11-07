#!/usr/bin/env python3
"""sit_model.py: the repo sim model of the A1b sit (D59). Sim model for the sim pass only checks of sit_sim.py.

  python3 altaay_lab/twin/sit/sit_model.py --out <scratch folder outside the repo> [--variant sit|stock]

The model is built from the repo, read on every run:
  body tree, actuators, sensors   the Playground MJCF at b9be205 (ODM_PLAYGROUND, as every repo sim: sim/added_mass_sim.py)
  masses and inertias             sim/mass_budget.py build_budget() (our build, with the sit parts in it), as C8's model
  joint ranges                    robot.urdf limits (the hard stops, sit_urdf.py)
  actuator control ranges         software/servo_limits.json (3 deg inside every hard stop), as the servo angle limit
                                  registers will hold them (servo_limits.py); the stock variant keeps inheritrange
  meshes                          the repo URDF mesh copies of every part sit_cad.py changed or added, in place of the
                                  Playground copies; the shin bodies load shin_left_sheet, shin_right_sheet, shin_spacer;
                                  knee_bumper, ankle_pad, hip_pad, sit_seat and sit_bumper are added at their URDF origins
The model before the sit is C8's 'ours' model of the same repo before this change (sim/added_mass_sim.py), which
sit_sim.py runs through the same tests for the before and after columns.
The check() function asserts that the written model has the URDF ranges and the sit geoms, so a stale model fails.
"""
import argparse
import json
import os
import shutil
import sys
import xml.etree.ElementTree as ET

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitlib as L  # noqa: E402

SIM = os.path.join(L.LAB, "sim")
PG = os.environ.get("ODM_PLAYGROUND", "/home/user/upstream/Open_Duck_Playground")
SRC_XML = os.path.join(PG, "playground", "open_duck_mini_v2", "xmls")
ROBOT_FILES = ("open_duck_mini_v2.xml", "open_duck_mini_v2_backlash.xml")
LIMITS = os.path.join(L.LAB, "software", "servo_limits.json")
SIT_NEW = ("knee_bumper", "ankle_pad", "hip_pad", "sit_seat", "sit_bumper")
SHIN_SWAP = {"left_knee_to_ankle_left_sheet": "shin_left_sheet", "left_knee_to_ankle_right_sheet": "shin_right_sheet",
             "leg_spacer": "shin_spacer"}
SHIN_LINKS = ("knee_and_ankle_assembly_2", "knee_and_ankle_assembly_4")
ACTUATED = ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle", "neck_pitch", "head_pitch", "head_yaw",
            "head_roll", "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]


def urdf_info():
    """joint limits (rad) and the visuals of every link, from robot.urdf"""
    r = ET.parse(L.URDF).getroot()
    lim = {}
    for j in r.findall("joint"):
        l_ = j.find("limit")
        if l_ is not None and j.get("type") == "revolute":
            lim[j.get("name")] = (float(l_.get("lower")), float(l_.get("upper")))
    vis = {}
    for ln in r.findall("link"):
        for v in ln.findall("visual"):
            g = v.find("geometry/mesh")
            if g is None:
                continue
            o = v.find("origin")
            xyz = [float(x) for x in (o.get("xyz") if o is not None else "0 0 0").split()]
            rpy = [float(x) for x in (o.get("rpy") if o is not None else "0 0 0").split()]
            vis.setdefault(ln.get("name"), []).append((os.path.basename(g.get("filename"))[:-4], xyz, rpy))
    return lim, vis


def changed_stems():
    """the URDF mesh copies sit_cad.py wrote (from sit_cad.json)"""
    J = json.load(open(os.path.join(HERE, "sit_cad.json")))
    return sorted(os.path.basename(p["urdf_copy"])[:-4] for p in J["parts"].values())


def quat_rpy(rpy):
    import trimesh.transformations as tf
    q = tf.quaternion_from_euler(*rpy, axes="sxyz")
    return q


def soft_limits():
    J = json.load(open(LIMITS))
    return {j: (np.radians(v["soft_lo_deg"]), np.radians(v["soft_hi_deg"])) for j, v in J["joints"].items()}


def write(out, variant="sit"):
    sys.path.insert(0, SIM)
    import mass_budget as MB
    d = os.path.join(out, variant)
    os.makedirs(d, exist_ok=True)
    B = MB.build_budget()
    links = B["links"]
    lim, vis = urdf_info()
    soft = soft_limits()
    stems = changed_stems()
    for f in os.listdir(SRC_XML):
        if f.endswith(".xml") and f not in ROBOT_FILES:
            shutil.copy(os.path.join(SRC_XML, f), d)
    for rf in ROBOT_FILES:
        tree = ET.parse(os.path.join(SRC_XML, rf))
        root = tree.getroot()
        for body in root.iter("body"):
            nm = body.get("name")
            if nm in links:
                x = links[nm]
                inert = body.find("inertial")
                for k in list(inert.attrib):
                    del inert.attrib[k]
                I = x.I
                inert.set("pos", " ".join("%.9g" % v for v in x.c))
                inert.set("mass", "%.9g" % x.m)
                inert.set("fullinertia", " ".join("%.9g" % v for v in (I[0, 0], I[1, 1], I[2, 2], I[0, 1], I[0, 2], I[1, 2])))
            if variant != "sit":
                continue
            if nm in SHIN_LINKS:
                for g in body.findall("geom"):
                    if g.get("mesh") in SHIN_SWAP:
                        g.set("mesh", SHIN_SWAP[g.get("mesh")])
            for stem, xyz, rpy in vis.get(nm, []):
                if stem in SIT_NEW:
                    q = quat_rpy(rpy)
                    g = ET.SubElement(body, "geom")
                    g.set("type", "mesh")
                    g.set("class", "visual")
                    g.set("name", "%s_%s" % (stem, nm))
                    g.set("mesh", stem)
                    g.set("pos", " ".join("%.9g" % v for v in xyz))
                    g.set("quat", " ".join("%.9g" % v for v in q))
                    g.set("rgba", "0.95 0.75 0.2 1")
        if variant == "sit":
            asset = root.find("asset")
            have = {m.get("name") for m in asset.findall("mesh")}
            for s in sorted(set(SHIN_SWAP.values()) | set(SIT_NEW)):
                if s not in have:
                    m = ET.SubElement(asset, "mesh")
                    m.set("name", s)
                    m.set("file", s + ".stl")
            for j in root.iter("joint"):
                n = j.get("name")
                if n in lim:
                    j.set("range", "%.9g %.9g" % lim[n])
            for a in root.iter("position"):
                n = a.get("joint")
                if n in soft:
                    if "inheritrange" in a.attrib:
                        del a.attrib["inheritrange"]
                    a.set("ctrlrange", "%.9g %.9g" % soft[n])
        tree.write(os.path.join(d, rf))
    # the meshes: Playground assets, with the repo URDF copies of every changed and new part over them
    J = dict(variant=variant, playground=SRC_XML, mass_kg=round(sum(v.m for v in links.values()), 4),
             repo_meshes=stems if variant == "sit" else [], urdf_limits_deg={k: [round(np.degrees(a), 3) for a in v] for k, v in lim.items()},
             soft_limits_deg={k: [round(np.degrees(a), 3) for a in v] for k, v in soft.items()} if variant == "sit" else {})
    L.dump(J, os.path.join(d, "sit_model.json"))
    return d


def assets(d):
    """mesh and xml assets of a model folder: Playground meshes, the repo copies of the changed parts on top"""
    J = json.load(open(os.path.join(d, "sit_model.json")))
    a = {}
    for f in os.listdir(os.path.join(SRC_XML, "assets")):
        a[f] = open(os.path.join(SRC_XML, "assets", f), "rb").read()
    for s in J["repo_meshes"]:
        a[s + ".stl"] = open(os.path.join(L.URDF_DIR, s + ".stl"), "rb").read()
    for f in os.listdir(d):
        if f.endswith(".xml"):
            a[f] = open(os.path.join(d, f), "rb").read()
    return a


def load(d, scene="scene_flat_terrain.xml"):
    import mujoco
    return mujoco.MjModel.from_xml_string(open(os.path.join(d, scene)).read(), assets=assets(d))


def check(d):
    """the written model matches the repo now: URDF ranges, the sit geoms, the repo meshes (fails loudly if stale)"""
    import mujoco
    md = load(d)
    J = json.load(open(os.path.join(d, "sit_model.json")))
    lim, vis = urdf_info()
    bad = []
    if J["variant"] == "sit":
        for jn in ACTUATED:
            jid = mujoco.mj_name2id(md, mujoco.mjtObj.mjOBJ_JOINT, jn)
            if not np.allclose(md.jnt_range[jid], lim[jn], atol=1e-6):
                bad.append("%s range %s, URDF %s" % (jn, md.jnt_range[jid], lim[jn]))
        names = {mujoco.mj_id2name(md, mujoco.mjtObj.mjOBJ_GEOM, g) or "" for g in range(md.ngeom)}
        for ln, vv in vis.items():
            for stem, _, _ in vv:
                if stem in SIT_NEW and "%s_%s" % (stem, ln) not in names:
                    bad.append("geom %s_%s missing" % (stem, ln))
        if set(J["repo_meshes"]) != set(changed_stems()):
            bad.append("model meshes differ from sit_cad.json")
    if bad:
        raise SystemExit("sit model is stale: " + "; ".join(bad))
    return md


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--variant", default="sit", choices=("sit",))
    a = ap.parse_args()
    d = write(a.out, a.variant)
    md = check(d)
    print(d, "bodies", md.nbody, "geoms", md.ngeom, "mass %.4f kg" % sum(md.body_mass))
