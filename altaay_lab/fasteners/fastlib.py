"""Shared scene for the fastener scripts (make_fasteners.py, sweep_fasteners.py, render_fasteners.py).

Same convention as altaay_lab/viewer/make_viewer_data.py:
- robot.urdf (mini_bdx/robots/open_duck_mini_v2, upstream b23317a) posed at zero joint angles with yourdfpy,
  translations x1000 to mm, URDF world frame (x forward, y left, z up).
- every printed URDF mesh is swapped for its print/ STL (same part frame; print/ is the STL set that gets printed).
- head parts that exist only in print/ get the head.stl instance transform; the second bulb is mirrored in y.
- every part instance carries the URDF link it rides on.

Instance order: the URDF visuals in link_map order (identical to altaay_lab/audit/assembly.json, checked on load),
then the 8 head internals. Hole features come from altaay_lab/audit/feat3d.py, run on the STL that is printed.

Heavy caches (features, ray scene) go to the scratch folder given by the caller, never into the repo.
"""
import hashlib
import json
import os
import sys

import numpy as np
import trimesh
import yourdfpy

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
REPO = os.path.dirname(LAB)
URDF_DIR = os.path.join(REPO, "mini_bdx", "robots", "open_duck_mini_v2")
PRINT_DIR = os.path.join(REPO, "print")
AUDIT = os.path.join(LAB, "audit")
sys.path.insert(0, AUDIT)
from feat3d import features  # noqa: E402  (read-only reuse of the audit feature finder)

HEAD_INTERNALS = ["left_eye", "right_eye", "bulb", "bulb", "flash_light_module",
                  "flash_reflector_interface", "speaker_stand", "speaker_interface"]
# link -> viewer subassembly (copied from viewer/make_viewer_data.py LINK_SUB)
LINK_SUB = {
    "trunk_assembly": "trunk",
    "neck_pitch_assembly": "neck", "head_pitch_to_yaw": "neck", "neck_yaw_assembly": "neck",
    "head_assembly": "head", "left_antenna_holder": "head", "right_antenna_holder": "head",
    "hip_roll_assembly": "left_hip", "left_roll_to_pitch_assembly": "left_bracket",
    "knee_and_ankle_assembly": "left_thigh", "knee_and_ankle_assembly_2": "left_shin", "foot_assembly": "left_foot",
    "hip_roll_assembly_2": "right_hip", "right_roll_to_pitch_assembly": "right_bracket",
    "knee_and_ankle_assembly_3": "right_thigh", "knee_and_ankle_assembly_4": "right_shin", "foot_assembly_2": "right_foot",
    # D59 sit parts, each on its own fixed link to the link it is stuck to (twin/sit/sitlib.py SIT_LINKS)
    "left_knee_bumper": "left_shin", "right_knee_bumper": "right_shin", "left_ankle_pads": "left_foot",
    "right_ankle_pads": "right_foot", "left_hip_pad": "left_bracket", "right_hip_pad": "right_bracket",
    "sit_seat": "trunk", "sit_bumper": "trunk",
}
SERVO_TOP, SERVO_MID, SERVO_BOT = ("wj-wk00-0122topcabinetcase_95", "wj-wk00-0123middlecase_56",
                                   "wj-wk00-0124bottomcase_45")


def mm(T):
    T = np.array(T, float).copy()
    T[:3, 3] *= 1000.0
    return T


def sha(path):
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()[:12]


class Scene:
    def __init__(self, scratch):
        self.scratch = scratch
        os.makedirs(scratch, exist_ok=True)
        u = yourdfpy.URDF.load(os.path.join(URDF_DIR, "robot.urdf"), load_meshes=False, build_scene_graph=True)
        self.zero = {j: 0.0 for j in u.actuated_joint_names}
        u.update_cfg(self.zero)
        self.u = u
        self.T0 = {ln: mm(u.get_transform(ln)) for ln in u.link_map}
        print_files = {os.path.splitext(f)[0] for f in os.listdir(PRINT_DIR) if f.lower().endswith(".stl")}

        def print_stem(fn):
            s = os.path.splitext(fn)[0]
            if s in print_files:
                return s
            for pre in ("left_", "right_"):
                if s.startswith(pre) and s[len(pre):] in print_files:
                    return s[len(pre):]
            return None
        inst = []
        for ln, link in u.link_map.items():
            Tl = u.get_transform(ln)
            for v in link.visuals:
                fn = os.path.basename(v.geometry.mesh.filename)
                T = mm(Tl @ (v.origin if v.origin is not None else np.eye(4)))
                ps = print_stem(fn)
                src = os.path.join(PRINT_DIR, ps + ".stl") if ps else os.path.join(URDF_DIR, fn)
                inst.append(dict(link=ln, urdf=fn, name=os.path.splitext(fn)[0], key=ps or os.path.splitext(fn)[0],
                                 printed=bool(ps), src=src, to_mm=not ps, T=T, mirror=False, head_internal=False))
        self.n_urdf = len(inst)
        asm = json.load(open(os.path.join(AUDIT, "assembly.json")))["inst"]
        self.assembly_match = len(asm) == len(inst) and all(
            a["mesh"] == i["urdf"] and np.allclose(np.array(a["T"]), i["T"], atol=1e-6) for a, i in zip(asm, inst))
        Th = [i["T"] for i in inst if i["urdf"] == "head.stl"][0]
        self.Th = Th
        seen = {}
        for stem in HEAD_INTERNALS:
            seen[stem] = seen.get(stem, 0) + 1
            mir = seen[stem] == 2
            M = np.diag([1.0, -1.0, 1.0, 1.0]) if mir else np.eye(4)
            inst.append(dict(link="head_assembly", urdf=None, name=stem, key=stem, printed=True,
                             src=os.path.join(PRINT_DIR, stem + ".stl"), to_mm=False, T=Th @ M, mirror=mir,
                             head_internal=True))
        for k, i in enumerate(inst):
            i["idx"] = k
        self.inst = inst
        self.joints = []
        for j in u.robot.joints:
            if j.type != "revolute":
                continue
            Tc = mm(u.get_transform(j.child))
            ax = Tc[:3, :3] @ np.asarray(j.axis, float)
            self.joints.append(dict(name=j.name, parent=j.parent, child=j.child, axis=ax / np.linalg.norm(ax),
                                    origin=Tc[:3, 3].copy(), lo=float(j.limit.lower), hi=float(j.limit.upper)))
        self.joint_by_child = {j["child"]: j for j in self.joints}
        self._local = {}
        self._world = {}

    # ------------------------------------------------------------------ meshes
    def local_mesh(self, src, to_mm):
        if src not in self._local:
            m = trimesh.load(src, force="mesh")
            if to_mm:
                m.apply_scale(1000.0)
            self._local[src] = m
        return self._local[src]

    def mesh(self, k):
        """World mesh of instance k at the zero pose."""
        if k not in self._world:
            i = self.inst[k]
            m = self.local_mesh(i["src"], i["to_mm"]).copy()
            m.apply_transform(i["T"])
            if i["mirror"]:
                m.invert()   # keep normals outward after the mirror
            self._world[k] = m
        return self._world[k]

    def link_T(self, link, cfg):
        self.u.update_cfg(cfg)
        T = mm(self.u.get_transform(link))
        self.u.update_cfg(self.zero)
        return T

    def ancestors(self, link):
        """Links from the root to `link` (inclusive), and the joints in between."""
        chain, joints = [link], []
        while link in self.joint_by_child or link in self._fixed_parent():
            if link in self.joint_by_child:
                j = self.joint_by_child[link]
                joints.append(j["name"])
                link = j["parent"]
            else:
                link = self._fixed_parent()[link]
            chain.append(link)
        return chain[::-1], joints[::-1]

    def _fixed_parent(self):
        if not hasattr(self, "_fp"):
            self._fp = {j.child: j.parent for j in self.u.robot.joints if j.type != "revolute"}
        return self._fp

    def subtree(self, link):
        """All links below `link` (inclusive)."""
        kids = {}
        for j in self.u.robot.joints:
            kids.setdefault(j.parent, []).append(j.child)
        out, st = [], [link]
        while st:
            ln = st.pop()
            out.append(ln)
            st += kids.get(ln, [])
        return set(out)

    # ------------------------------------------------------------------ hole features and sites
    def features(self):
        """feat3d features per unique source STL, cached in scratch by file hash."""
        cache_dir = os.path.join(self.scratch, "feat_cache")
        os.makedirs(cache_dir, exist_ok=True)
        out = {}
        for i in self.inst:
            src = i["src"]
            if src in out:
                continue
            fn = os.path.join(cache_dir, "%s_%s.json" % (os.path.basename(src), sha(src)))
            if os.path.exists(fn):
                out[src] = json.load(open(fn))
            else:
                out[src] = features(self.local_mesh(src, i["to_mm"]))
                json.dump(out[src], open(fn, "w"))
        return out

    def world_features(self):
        F = self.features()
        W = []
        for k, i in enumerate(self.inst):
            T = i["T"]
            for f in F[i["src"]]:
                p0 = (T @ np.r_[f["p0"], 1])[:3]
                p1 = (T @ np.r_[f["p1"], 1])[:3]
                a = p1 - p0
                L = np.linalg.norm(a)
                if L < 1e-6:
                    continue
                W.append(dict(i=k, mesh=i["name"], kind=f["kind"], d=f["d"], p0=p0, p1=p1, ax=a / L, L=L))
        return W

    def sites(self):
        """Coaxial hole stacks, same clustering as altaay_lab/audit/sites.py (0.35 mm, 40 mm), on the printed STLs."""
        W = self.world_features()

        def linedist(p, o, a):
            v = p - o
            return np.linalg.norm(v - np.dot(v, a) * a)
        sites = []
        for w in sorted(W, key=lambda w: -w["L"]):
            for s in sites:
                if abs(abs(np.dot(s["ax"], w["ax"])) - 1) < 1e-3 and linedist(w["p0"], s["o"], s["ax"]) < 0.35 \
                        and linedist(w["p1"], s["o"], s["ax"]) < 0.35:
                    t = [np.dot(w["p0"] - s["o"], s["ax"]), np.dot(w["p1"] - s["o"], s["ax"])]
                    if min(t) < s["tmax"] + 40 and max(t) > s["tmin"] - 40:
                        s["m"].append(w)
                        s["tmin"], s["tmax"] = min(s["tmin"], *t), max(s["tmax"], *t)
                        break
            else:
                sites.append(dict(o=w["p0"], ax=w["ax"], m=[w], tmin=0, tmax=w["L"]))
        out = []
        for s in sites:
            segs = []
            for w in s["m"]:
                t = sorted([np.dot(w["p0"] - s["o"], s["ax"]), np.dot(w["p1"] - s["o"], s["ax"])])
                segs.append(((round(t[0], 2), round(t[1], 2), w["mesh"], w["kind"], w["d"], w["i"]), w))
            segs.sort(key=lambda x: x[0])
            out.append(dict(o=s["o"], ax=s["ax"], segs=[x[0] for x in segs], feat=[x[1] for x in segs]))
        return out, W

    # ------------------------------------------------------------------ rays (static zero-pose scene)
    def ray_scene(self, exclude=()):
        key = tuple(sorted(exclude))
        if not hasattr(self, "_rays"):
            self._rays = {}
        if key not in self._rays:
            parts = [self.mesh(k) for k in range(len(self.inst)) if k not in exclude]
            W = trimesh.util.concatenate(parts)
            try:
                from trimesh.ray.ray_pyembree import RayMeshIntersector
            except Exception:  # fall back to the pure python intersector
                from trimesh.ray.ray_triangle import RayMeshIntersector
            self._rays[key] = (W, RayMeshIntersector(W))
        return self._rays[key]

    def first_hits(self, origins, dirs, tmin=0.1):
        """Distance to the first surface hit beyond tmin for each ray (inf if none)."""
        W, RI = self.ray_scene()
        origins = np.asarray(origins, float)
        dirs = np.asarray(dirs, float)
        out = np.full(len(origins), np.inf)
        locs, ri, _ = RI.intersects_location(origins, dirs, multiple_hits=True)
        if len(locs):
            t = np.einsum("ij,ij->i", locs - origins[ri], dirs[ri])
            for r, tt in zip(ri, t):
                if tt > tmin and tt < out[r]:
                    out[r] = tt
        return out


def frame_from_axis(p, z):
    """4x4 with origin p and local +z along z (x, y any perpendicular pair)."""
    z = np.asarray(z, float) / np.linalg.norm(z)
    t = np.array([1.0, 0, 0]) if abs(z[0]) < 0.9 else np.array([0, 1.0, 0])
    x = np.cross(t, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    M = np.eye(4)
    M[:3, :3] = np.c_[x, y, z]
    M[:3, 3] = p
    return M
