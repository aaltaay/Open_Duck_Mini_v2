#!/usr/bin/env python3
"""sit_records.py: the instance records that follow robot.urdf after the sit job (D59). CAD check only.

  python3 altaay_lab/twin/sit/sit_records.py [--write]          run after sit_cad.py --write and sit_urdf.py --write

Starts from altaay_lab/audit/assembly.json, audit/sites.json and fasteners/fasteners.json at sitlib.BASE_REV (so a
re-run gives the same files) and brings them to the robot.urdf of the working tree:

  assembly.json   the instance list again from robot.urdf (same method as audit/assemble.py: link, mesh, 4x4 in mm at
                  the zero pose). The upstream visuals keep their order (sit_urdf.py writes the sit parts as new links
                  after every upstream link), so instances 0 to 130 are the same; the 6 shin instances now name
                  shin_spacer, shin_right_sheet and shin_left_sheet; the 10 sit parts are 131 to 140. Hole features
                  (audit/feat3d.py) of the new meshes are added; the meshes this job changed elsewhere keep their
                  features after a check that their holes did not change (feat3d on the base and new print STL).
  sites.json      on the 6 shin instances the hole segments come again from the new meshes (sites.py clustering: a
                  feature joins the site it is coaxial with, within 0.35 mm, or opens a new site at the end), so the
                  site numbers the other records use stay. A site whose only holes were the old spacer pattern is
                  left with no segments and a 'd59' note (the shin sheets plug those holes, D39).
                  The foot plates' heel screw stack moved 20 mm in x (sit_cad.py HEEL_DX): their audited features move
                  with it and their sites are redone the same way.
  fasteners.json  the head internals (instances 131 to 138 before) are 141 to 148 now; the shin rows name the shin
                  parts; the 8 spacer screws and 8 inserts of each shin move to the new spacer pattern (sitlib
                  SPACER_HOLES, 9 mm out with the plates); the M2 screws under the clamp blocks keep their seat (the
                  block is counterbored); the heel screws F024, F026 and inserts I34, I46 move HEEL_DX; the shin leg_spacer rows of empty_holes are marked superseded. The sweep
                  fields are then rewritten by fasteners/sweep_fasteners.py on the new ranges (SIT.md commands).
"""
import argparse
import copy
import json
import os
import sys

import numpy as np
import trimesh
import yourdfpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sitlib as L  # noqa: E402
sys.path.insert(0, os.path.join(L.LAB, "audit"))
from feat3d import features  # noqa: E402  (audit/assemble.py method)
import sit_cad as SC  # noqa: E402

AUDIT = os.path.join(L.LAB, "audit")
FJ = os.path.join(L.LAB, "fasteners", "fasteners.json")
SHIN_LINKS = {"knee_and_ankle_assembly_2": 90.65, "knee_and_ankle_assembly_4": 90.65 - 181.2}   # leg centre plane y
RENAME = {"knee_to_ankle_left_sheet": "shin_left_sheet", "knee_to_ankle_right_sheet": "shin_right_sheet", "leg_spacer": "shin_spacer"}
SPACER_ROWS = {   # stock screw/insert rows of the shin spacer -> index of the new hole (SC.SPACER_HOLES) by the stock x
    -27.06: 0, -43.06: 1}
HEEL_ROWS = ("F024", "I34", "F026", "I46")   # the heel screw and its insert, both feet (sit_cad.py HEEL_OLD, HEEL_DX)
CHANGED_ELSEWHERE = ["left_cache", "right_cache", "foot_top", "foot_side", "left_roll_to_pitch", "right_roll_to_pitch",
                     "neck_left_sheet", "neck_right_sheet", "head_pitch_to_yaw", "knee_to_ankle_left_sheet",
                     "knee_to_ankle_right_sheet"]


def git_json(rel):
    return json.loads(L.git_blob(rel).decode())


def urdf_inst():
    u = yourdfpy.URDF.load(L.URDF, load_meshes=False, build_scene_graph=True)
    u.update_cfg({j: 0.0 for j in u.actuated_joint_names})
    out = []
    for ln, link in u.link_map.items():
        Tl = u.get_transform(ln)
        for v in link.visuals:
            fn = v.geometry.mesh.filename.replace("package:///", "").replace("package://", "")
            T = Tl @ (v.origin if v.origin is not None else np.eye(4))
            T = T.copy()
            T[:3, 3] *= 1000
            out.append(dict(link=ln, mesh=fn, T=T.tolist()))
    return u, out


def feats_of_urdf_mesh(fn):
    m = trimesh.load(os.path.join(L.URDF_DIR, fn), force="mesh")
    m.apply_scale(1000)
    return features(m)


def holes_changed(stem):
    """hole features of the base and the new print STL of a part this job changed elsewhere (sitlib.holes_changed)"""
    return L.holes_changed(L.base_mesh("print/%s.stl" % stem), trimesh.load(os.path.join(L.REPO, "print", stem + ".stl"), force="mesh"))


def linedist(p, o, a):
    v = p - o
    return float(np.linalg.norm(v - np.dot(v, a) * a))


def world_feats(A_inst, feats, ks):
    W = []
    for k in ks:
        i = A_inst[k]
        T = np.array(i["T"])
        for f in feats[i["mesh"]]:
            p0 = (T @ np.r_[f["p0"], 1])[:3]
            p1 = (T @ np.r_[f["p1"], 1])[:3]
            a = p1 - p0
            Ln = np.linalg.norm(a)
            if Ln < 1e-6:
                continue
            W.append(dict(i=k, mesh=i["mesh"].split(":")[-1].replace(".stl", ""), kind=f["kind"], d=f["d"], p0=p0, p1=p1, ax=a / Ln, L=Ln))
    return W


def update_sites(sites, A_inst, feats, ks, log):
    """drop the segments of instances ks and add them again from the new features (audit/sites.py clustering)"""
    ks = set(ks)
    out = copy.deepcopy(sites)
    # every site keeps its axis and its axial extent from before, so a hole that did not move joins its own site again
    work = []
    for si, s in enumerate(out):
        ts = [t for g in s["segs"] for t in g[:2]] or [0.0]
        work.append(dict(o=np.array(s["o"], float), ax=np.array(s["ax"], float), idx=si, new=[], tmin=min(ts), tmax=max(ts)))
    emptied = []
    for si, s in enumerate(out):
        before = len(s["segs"])
        s["segs"] = [g for g in s["segs"] if g[5] not in ks]
        if before and not s["segs"]:
            emptied.append(si)
    W = world_feats(A_inst, feats, sorted(ks))
    added = 0
    for w in sorted(W, key=lambda w: -w["L"]):
        hit = None
        for s in work:
            if abs(abs(np.dot(s["ax"], w["ax"])) - 1) < 1e-3 and linedist(w["p0"], s["o"], s["ax"]) < 0.35 and linedist(w["p1"], s["o"], s["ax"]) < 0.35:
                t = [np.dot(w["p0"] - s["o"], s["ax"]), np.dot(w["p1"] - s["o"], s["ax"])]
                if min(t) < s["tmax"] + 40 and max(t) > s["tmin"] - 40:
                    hit = s
                    break
        if hit is None:
            hit = dict(o=w["p0"].copy(), ax=w["ax"].copy(), idx=None, new=[], tmin=0.0, tmax=w["L"])
            work.append(hit)
            added += 1
        t = sorted([np.dot(w["p0"] - hit["o"], hit["ax"]), np.dot(w["p1"] - hit["o"], hit["ax"])])
        hit["tmin"], hit["tmax"] = min(hit["tmin"], *t), max(hit["tmax"], *t)
        hit["new"].append([round(float(t[0]), 1), round(float(t[1]), 1), w["mesh"], w["kind"], w["d"], int(w["i"])])
    for s in work:
        if not s["new"]:
            continue
        if s["idx"] is None:
            out.append(dict(o=np.round(s["o"], 1).tolist(), ax=np.round(s["ax"], 3).tolist(), segs=sorted(s["new"]),
                            d59="new hole of the D59 shin parts (twin/sit/sit_records.py)"))
        else:
            out[s["idx"]]["segs"] = sorted(out[s["idx"]]["segs"] + s["new"])
    for si in emptied:
        if not out[si]["segs"]:
            out[si]["d59"] = "the shin spacer moved to the sheet back edge (D59): these holes are plugged in the shin sheets (D39)"
    log["sites"] = dict(features=len(W), new_sites=added, emptied=[si for si in emptied if not out[si]["segs"]],
                        total=len(out))
    return out


def link_pose(T0, link, seat, axis_world, R_old_link):
    Tli = np.linalg.inv(T0[link])
    p = (Tli @ np.r_[seat, 1])[:3]
    a = Tli[:3, :3] @ np.asarray(axis_world, float)
    P = np.eye(4)
    P[:3, :3] = np.asarray(R_old_link, float)
    P[:3, 3] = p
    return p, a, P


def update_fasteners(D, T0, log):
    D = copy.deepcopy(D)
    n_head = 0
    for f in D["fasteners"]:
        for k in ("part_inst", "into_inst"):
            if f.get(k) is not None and f[k] >= L.N_URDF_BASE:
                f[k] += 10
                n_head += 1
        sw = f.get("sweep") or {}
        for v in sw.values():
            if isinstance(v, dict) and v.get("part_inst") is not None and v["part_inst"] >= L.N_URDF_BASE:
                v["part_inst"] += 10
    for h in (D.get("sweep") or {}).get("hits", []):
        for k in ("against_inst", "part_inst"):
            if h.get(k) is not None and h[k] >= L.N_URDF_BASE:
                h[k] += 10
    log["head_internal_refs_moved"] = n_head
    moved, renamed = [], []
    for f in D["fasteners"]:
        if f.get("link") not in SHIN_LINKS:
            continue
        for k in ("part", "into"):
            if f.get(k) in RENAME:
                f[k] = RENAME[f[k]]
                renamed.append(f["id"])
        is_spacer = f.get("into") == "shin_spacer" and f["kind"] in ("screw", "insert")
        if is_spacer:
            x_old = round(f["seat_world"][0], 2)
            hole = SC.SPACER_HOLES[SPACER_ROWS[x_old]]
            yc = SHIN_LINKS[f["link"]]
            n = 1.0 if f["seat_world"][1] > yc else -1.0          # the plate it sits on moved JOG away from the centre plane
            seat = np.array([hole[0], f["seat_world"][1] + n * L.JOG, hole[1]])
            p, a, P = link_pose(T0, f["link"], seat, f["axis_world"], np.array(f["pose_link"])[:3, :3])
            f["seat_world"] = [round(float(v), 3) for v in seat]
            f["seat_link"] = [round(float(v), 3) for v in p]
            f["pose_link"] = [[round(float(v), 4) for v in row] for row in P]
            f["site"] = None
            f["notes"] = list(f.get("notes") or []) + [
                "D59: on the new shin_spacer pattern (twin/sit/sit_cad.py SPACER_HOLES, both ends one pattern, D42), "
                "the plate %.0f mm out with the joggle; same stack as the stock spacer joint (sheet 1.85 mm under the "
                "recess, 0.10 mm gap, 5.7 mm insert), so the same screw; make_fasteners site: none (moved by "
                "twin/sit/sit_records.py)" % L.JOG]
            moved.append(f["id"])
        elif f["kind"] == "screw" and f.get("into", "").startswith("wj-wk00") and f.get("part") in ("shin_left_sheet", "shin_right_sheet") \
                and f["seat_world"][2] < SC.Z_CLAMP:
            rc = f.get("recess_check") or {}
            if "proud" in rc:
                rc["proud"] = round(rc["proud"] - L.JOG, 2)
            f["seat_type"] = (f.get("seat_type") or "") + ", %.0f mm block over it (D59 clamp block, counterbored)" % L.JOG
            f["notes"] = list(f.get("notes") or []) + [
                "D59: the clamp block stands %.0f mm out over this head; the head seat is the stock one, reached "
                "through the block's counterbore (twin/sit/sit_cad.py M2_HEAD_CB)" % L.JOG]
    for f in D["fasteners"]:
        if f["id"] in HEEL_ROWS:
            if abs(f["seat_world"][0] - SC.HEEL_OLD[0]) > 0.05 or abs(f["seat_world"][2] - SC.HEEL_OLD[1]) > 0.05:
                raise SystemExit("%s is not at the stock heel screw place: %s" % (f["id"], f["seat_world"]))
            seat = np.array(f["seat_world"], float) + [SC.HEEL_DX, 0.0, 0.0]
            p, a, P = link_pose(T0, f["link"], seat, f["axis_world"], np.array(f["pose_link"])[:3, :3])
            f["seat_world"] = [round(float(v), 3) for v in seat]
            f["seat_link"] = [round(float(v), 3) for v in p]
            f["pose_link"] = [[round(float(v), 4) for v in row] for row in P]
            f["site"] = None
            f["notes"] = list(f.get("notes") or []) + [
                "D59: the heel screw stack moved %.0f mm toward the toe, out of the foot notch the shin's ankle clamp "
                "corner needs past -88 deg (twin/sit/sit_cad.py HEEL_DX); same stack, same screw; the old holes are "
                "plugged (D39)" % SC.HEEL_DX]
            moved.append(f["id"])
    log["fasteners_moved"] = moved
    log["fasteners_renamed"] = sorted(set(renamed))
    sup = []
    for e in D.get("empty_holes", []):
        at = e.get("at") or [0, 0, 0]
        if at[2] < -60 and any(h.get("part") == "leg_spacer" for h in e.get("holes", [])):
            e["superseded"] = "D59: the shin spacer is shin_spacer now (no such hole); the thigh leg_spacer keeps it"
            sup.append(e["site"])
    log["empty_holes_superseded"] = sup
    sc = D["meta"]["scene"]
    sc["urdf_instances"] = sc["urdf_instances"] + 10
    sc["instances"] = sc["instances"] + 10
    sc["d59"] = ("robot.urdf carries the 10 sit parts as instances 131 to 140 (new fixed links); head internals are 141 "
                 "to 148; shin rows moved by twin/sit/sit_records.py")
    return D


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    log = {}
    A0 = git_json("altaay_lab/audit/assembly.json")
    S0 = git_json("altaay_lab/audit/sites.json")
    F0 = git_json("altaay_lab/fasteners/fasteners.json")
    u, inst = urdf_inst()
    if len(inst) != L.N_URDF_BASE + 10:
        raise SystemExit("robot.urdf has %d visuals, expected %d (run sit_urdf.py --write)" % (len(inst), L.N_URDF_BASE + 10))
    changed_inst = []
    for k, (a0, a1) in enumerate(zip(A0["inst"], inst)):
        if a0["link"] != a1["link"] or not np.allclose(np.array(a0["T"]), np.array(a1["T"]), atol=1e-6):
            raise SystemExit("instance %d moved: %s %s -> %s %s" % (k, a0["link"], a0["mesh"], a1["link"], a1["mesh"]))
        if a0["mesh"] != a1["mesh"]:
            changed_inst.append(k)
    if sorted(a1["mesh"] for k, a1 in enumerate(inst) if k in changed_inst) != sorted(["shin_spacer.stl", "shin_right_sheet.stl", "shin_left_sheet.stl"] * 2):
        raise SystemExit("unexpected mesh changes at %s" % changed_inst)
    feats = dict(A0["feats"])
    new_meshes = sorted({i["mesh"] for i in inst} - set(feats))
    for fn in new_meshes:
        feats[fn] = feats_of_urdf_mesh(fn)
    # the foot plates: their heel screw stack moved (sit_cad.py move_heel_screw); the other features stay as audited
    heel_old_part = np.array([SC.HEEL_OLD[0], SC.HEEL_OLD[1]])
    foot_inst = []
    for fn in ("foot_side.stl", "foot_top.stl"):
        ks = [k for k, i in enumerate(inst) if i["mesh"] == fn]
        Tw = np.array(inst[ks[0]]["T"])
        n = 0
        out_f = []
        for f in feats[fn]:
            p0w = (Tw @ np.r_[f["p0"], 1])[:3]
            if abs(p0w[0] - heel_old_part[0]) < 1.0 and abs(p0w[2] - heel_old_part[1]) < 1.0:
                dxp = np.linalg.inv(Tw)[:3, :3] @ np.array([SC.HEEL_DX, 0.0, 0.0])
                f = dict(f, p0=(np.asarray(f["p0"]) + dxp).tolist(), p1=(np.asarray(f["p1"]) + dxp).tolist())
                n += 1
            out_f.append(f)
        if n == 0:
            raise SystemExit("%s: no heel screw feature in the audited features" % fn)
        feats[fn] = out_f
        foot_inst += ks
    log["assembly"] = dict(instances=len(inst), swapped=changed_inst, new_meshes={fn: len(feats[fn]) for fn in new_meshes},
                           heel_screw_features_moved=dict(instances=foot_inst, dx_mm=SC.HEEL_DX))
    hc = {s: holes_changed(s) for s in CHANGED_ELSEWHERE}
    log["holes_of_parts_changed_elsewhere"] = {s: ("same %d holes" % v["base"]) if not v["gone"] and not v["added"] else v for s, v in hc.items()}
    # the foot plates' heel screw move is checked feature by feature in sit_cad.py write() (HEEL_DX); nothing else may change
    bad = {s: v for s, v in hc.items() if (v["gone"] or v["added"]) and s not in ("foot_top", "foot_side")}
    A1 = dict(inst=inst, feats=feats)
    S1 = update_sites(S0, inst, feats, changed_inst + foot_inst + list(range(L.N_URDF_BASE, L.N_URDF_BASE + 10)), log)
    T0 = {ln: L.c3d_lib.mm(u.get_transform(ln)) for ln in u.link_map}
    F1 = update_fasteners(F0, T0, log)
    print(json.dumps(log, indent=1, default=str))
    if bad:
        raise SystemExit("holes changed on parts outside the shin: %s (sit_cad.py must keep them)" % sorted(bad))
    if a.write:
        json.dump(A1, open(os.path.join(AUDIT, "assembly.json"), "w"))
        json.dump(S1, open(os.path.join(AUDIT, "sites.json"), "w"), default=str)
        with open(FJ, "w") as fh:
            json.dump(F1, fh)
        L.dump(log, os.path.join(HERE, "sit_records.json"))
        print("written: audit/assembly.json, audit/sites.json, fasteners/fasteners.json, twin/sit/sit_records.json")


if __name__ == "__main__":
    main()
