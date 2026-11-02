"""Robot scene for the 3D completeness data (altaay_lab/blueprint): the robot posed at zero, in mm.

Same conventions as altaay_lab/viewer/make_viewer_data.py and altaay_lab/cables3d/c3d_lib.py:
URDF world at the zero pose, x forward, y left, z up, millimetres. Link transforms from yourdfpy (x1000).
Every printed URDF mesh is swapped for its print/ STL (same part frame). The head parts that exist only in
print/ are modelled in the head.stl frame and get the head.stl instance transform; the second bulb is mirrored in y.
Read-only inputs: mini_bdx/robots/open_duck_mini_v2/robot.urdf and meshes (Open_Duck_Mini b23317a), print/*.stl.
"""
import os
import sys

import numpy as np
import trimesh
import yourdfpy

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
REPO = os.path.dirname(LAB)
URDF_DIR = os.path.join(REPO, "mini_bdx", "robots", "open_duck_mini_v2")
PRINT_DIR = os.path.join(REPO, "print")
HEAD_INTERNALS = ["left_eye", "right_eye", "bulb", "bulb", "flash_light_module",
                  "flash_reflector_interface", "speaker_stand", "speaker_interface"]
CASE = {"wj-wk00-0122topcabinetcase_95.stl": "servo_top", "wj-wk00-0123middlecase_56.stl": "servo_mid",
        "wj-wk00-0124bottomcase_45.stl": "servo_bottom"}
SERVO_ID = {"left_hip_yaw": 20, "left_hip_roll": 21, "left_hip_pitch": 22, "left_knee": 23, "left_ankle": 24,
            "right_hip_yaw": 10, "right_hip_roll": 11, "right_hip_pitch": 12, "right_knee": 13, "right_ankle": 14,
            "neck_pitch": 30, "head_pitch": 31, "head_yaw": 32, "head_roll": 33}


def mm(T):
    T = np.array(T, float).copy()
    T[:3, 3] *= 1000.0
    return T


class Scene:
    def __init__(self):
        self.u = yourdfpy.URDF.load(os.path.join(URDF_DIR, "robot.urdf"), load_meshes=False, build_scene_graph=True)
        self.joints = {}
        for j in self.u.robot.joints:
            if j.type == "revolute":
                self.joints[j.name] = dict(parent=j.parent, child=j.child, axis=np.asarray(j.axis, float),
                                           lo=float(j.limit.lower), hi=float(j.limit.upper))
        self.u.update_cfg({n: 0.0 for n in self.u.actuated_joint_names})
        self.T0 = {ln: mm(self.u.get_transform(ln)) for ln in self.u.link_map}
        prints = {os.path.splitext(f)[0] for f in os.listdir(PRINT_DIR) if f.endswith(".stl")}
        self.inst, self._mesh = [], {}
        for ln, link in self.u.link_map.items():
            for v in link.visuals:
                fn = os.path.basename(v.geometry.mesh.filename)
                stem = os.path.splitext(fn)[0]
                key, path, scale = stem, os.path.join(URDF_DIR, fn), 1000.0
                for s in (stem, stem.replace("left_", "", 1), stem.replace("right_", "", 1)):
                    if s in prints:
                        key, path, scale = s, os.path.join(PRINT_DIR, s + ".stl"), 1.0
                        break
                key = CASE.get(fn, key)
                self.inst.append(dict(link=ln, key=key, urdf=fn, path=path, scale=scale,
                                      T=mm(v.origin if v.origin is not None else np.eye(4))))
        th = [i for i in self.inst if i["key"] == "head"][0]
        seen = {}
        for stem in HEAD_INTERNALS:
            seen[stem] = seen.get(stem, 0) + 1
            M = np.diag([1.0, -1.0, 1.0, 1.0]) if seen[stem] == 2 else np.eye(4)
            self.inst.append(dict(link=th["link"], key=stem, urdf=None, path=os.path.join(PRINT_DIR, stem + ".stl"),
                                  scale=1.0, T=th["T"] @ M, mirrored=seen[stem] == 2))
        for k, i in enumerate(self.inst):
            i["idx"] = k
            i["W"] = self.T0[i["link"]] @ i["T"]          # part frame -> world (mm)

    def find(self, key, link=None):
        return [i for i in self.inst if i["key"] == key and (link is None or i["link"] == link)]

    def mesh(self, i):
        p = i["path"]
        if p not in self._mesh:
            m = trimesh.load(p, force="mesh")
            if i["scale"] != 1.0:
                m.apply_scale(i["scale"])
            self._mesh[p] = m
        return self._mesh[p]

    def world_mesh(self, i):
        m = self.mesh(i).copy()
        if i.get("mirrored"):
            m.invert()
        m.apply_transform(i["W"])
        return m

    def servos(self):
        """one record per STS3215: joint, servo id, link, case frame -> world (the bottom case STL frame).
        Case frame (measured on the case meshes): horn axis along local y at x -25.5, z 0."""
        out = []
        for c in self.find("servo_bottom"):
            Tw = c["W"]
            hc = (Tw @ np.array([-25.5, 7.0, 0.0, 1.0]))[:3]
            ax = Tw[:3, :3] @ np.array([0, 1.0, 0])
            best = None
            for jn, j in self.joints.items():
                if "antenna" in jn or c["link"] not in (j["parent"], j["child"]):
                    continue
                Tc = self.T0[j["child"]]
                p, a = Tc[:3, 3], Tc[:3, :3] @ j["axis"]
                d = hc - p
                off = np.linalg.norm(d - np.dot(d, a) * a)
                if abs(np.dot(a, ax)) > 0.99:
                    score = (round(off, 1), np.linalg.norm(d))
                    if best is None or score < best[0]:
                        best = (score, jn)
            jn = best[1] if best else None
            out.append(dict(joint=jn, id=SERVO_ID.get(jn), link=c["link"], W=Tw))
        return out


def tf(M, p):
    return (M @ np.r_[np.asarray(p, float), 1.0])[:3]


def rot(M, d):
    v = M[:3, :3] @ np.asarray(d, float)
    return v / np.linalg.norm(v)
