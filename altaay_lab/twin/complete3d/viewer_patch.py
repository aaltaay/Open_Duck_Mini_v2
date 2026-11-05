"""viewer_patch.py: the phase 2 changes for viewer/make_viewer_data.py, as functions it calls. Not applied in phase 1.

Hooks (make_viewer_data.py main(), base 5bd28f9):
  step 7b  camera:     cad_place["camera"] -> camera_pieces(T_link): PCB slab, lens cylinder, connector zone (part_seats.json)
                       instead of the 25 x 24 x 11.5 box (that box is 3.75 mm off and pokes 4.75 mm out of the face).
  step 10b fasteners:  recs = apply_fastener_patch(recs) before load_fasteners() normalizes them; label_for(rec) when
                       part_inst is null (camera screws now read "head shell into head shell").
  cables:              cables = apply_cable_patch(cables) after load_cables3d(); a cable with shape "flat strip" is drawn
                       with ribbon_mesh() instead of a tube; assert_all_runs(cables3d, manifest_cables) before writing.
  manifest:            manifest["labels"] = labels(); manifest["cables"][i]["hidden_pct"] from inventory.json, and
                       manifest["meta"]["xray"] = True so the page offers "x-ray shells" and "hidden cables on top".
All data files are in this folder. CAD check only.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    p = os.path.join(HERE, name)
    return json.load(open(p)) if os.path.exists(p) else None


def apply_fastener_patch(recs):
    """fasteners.json records -> same list with the fasteners_patch.json updates applied by id (nothing added)"""
    fp = _load("fasteners_patch.json") or {}
    upd = {u["id"]: u for u in fp.get("update", [])}
    out = []
    for r in recs:
        u = upd.get(r.get("id"))
        if u:
            r = dict(r)
            for k in ("part", "seat_world", "axis_world", "length_mm"):
                r[k] = u[k]
            r["seat_link"], r["axis_link"] = u["seat_link"], u["axis_link"]
            r["viewer_label"] = u["viewer_label"]
            r["notes"] = list(r.get("notes") or []) + u["notes"]
        out.append(r)
    return out


def label_for(rec, default):
    """screw label: the record's own text when the joined part is not a CAD instance (part_inst null)"""
    if rec.get("viewer_label"):
        return rec["viewer_label"]
    if rec.get("part_inst") is None and rec.get("part"):
        return "%s: %s into %s" % (rec.get("spec", "screw"), rec["part"], rec.get("into", "?"))
    return default


def apply_cable_patch(cables):
    """load_cables3d() output -> D12 as a flat strip on the designed route, CAM.CSI end moved (cables_patch.json)"""
    cp = _load("cables_patch.json") or {}
    d = cp.get("D12")
    if not d:
        return cables
    for c in cables:
        if c["id"] == "D12":
            c["pts"] = [(d["link"], p, None) for p in d["points_link"]]
            c["shape"] = "flat strip"
            c["width_vecs"] = d["width_link"]
            c["width_mm"], c["thickness_mm"] = d["width_mm"], d["thickness_mm"]
            v = d["verdict"]
            c["note"] = "; ".join([c.get("note") or "", "flat strip route %.1f mm (no twist): 150 mm %s, 200 mm %s" % (
                d["length_mm"], v["150"]["result"], v["200"]["result"])])
    return cables


def ribbon_mesh(points, width_vecs, width, thickness):
    """flat band along points (N x 3) with unit width vectors (N x 3): vertices and triangle faces, both faces closed"""
    P, Wv = np.asarray(points, float), np.asarray(width_vecs, float)
    Wv = Wv / np.linalg.norm(Wv, axis=1)[:, None]
    T = np.gradient(P, axis=0)
    T /= np.maximum(np.linalg.norm(T, axis=1), 1e-9)[:, None]
    N = np.cross(T, Wv)
    N /= np.maximum(np.linalg.norm(N, axis=1), 1e-9)[:, None]
    hw, ht = width / 2.0, thickness / 2.0
    corners = [(-hw, -ht), (hw, -ht), (hw, ht), (-hw, ht)]
    V = np.concatenate([P + Wv * a + N * b for a, b in corners], axis=0)
    n = len(P)
    F = []
    for k in range(4):
        a0, a1 = k * n, ((k + 1) % 4) * n
        for i in range(n - 1):
            F += [(a0 + i, a1 + i, a1 + i + 1), (a0 + i, a1 + i + 1, a0 + i + 1)]
    for i in (0, n - 1):
        q = [k * n + i for k in range(4)]
        F += [(q[0], q[1], q[2]), (q[0], q[2], q[3])] if i == 0 else [(q[0], q[2], q[1]), (q[0], q[3], q[2])]
    return V, np.array(F, int)


def camera_pieces(T_link_world):
    """designed camera seat as boxes and a cylinder, each with a 4x4 pose in the head_assembly link frame"""
    s = (_load("part_seats.json") or {}).get("camera")
    if not s:
        return []
    Tcl = np.array(s["T_cam_link"])
    out = []
    for pc in s["pieces"]:
        T = np.eye(4)
        T[:3, 3] = pc["center_cam"]
        out.append(dict(name=pc["name"], T_link=Tcl @ T, dims=pc.get("dims"), shape=pc.get("shape", "box"),
                        d_mm=pc.get("d_mm"), length_mm=pc.get("length_mm"), source=pc["source"]))
    return out


def assert_all_runs(cables3d_path, manifest_cables):
    """every run of every cable in cables3d.json has a node in the manifest; returns the missing ones (empty = ok)"""
    c3 = json.load(open(cables3d_path))
    want = {"%s:%s" % (c["id"], r.get("name") or k) for c in c3["cables"] for k, r in enumerate(c.get("runs") or [{"name": "main"}])}
    got = {"%s:%s" % (str(c["id"]).split(":")[0], c.get("run") or "main") for c in manifest_cables}
    return sorted(w for w in want if w not in got and w.replace(":main", ":None") not in got)


def labels():
    """labels.json: one fixed label per part and per cable (billboard on the label cylinder, leader to the anchor)"""
    lb = _load("labels.json") or {}
    return dict(rule=lb.get("meta", {}).get("rule"), items=[dict(node=q["node"], text=q["text"], pos=q["pos_world"],
                                                                 anchor=q["anchor_world"], sub=q["sub"]) for q in lb.get("labels", [])])


def hidden_pct():
    """cable id -> percent of sample points enclosed by parts from all 14 ray directions at explode 0 (inventory.json)"""
    inv = _load("inventory.json") or {}
    return {c["id"]: c.get("hidden_pct") for c in inv.get("cables", []) if c.get("hidden_pct") is not None}
