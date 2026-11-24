"""Nest and nested scenes. The wall and paddle dock stays in dock_scene.py.

nest: the nest v2 meshes in print/nest (millimetres, nest frame).
nested: that mat plus the duck at the recorded sit, turned to face the room,
seat on the felt. The pose is sim pass only (twin/sit/sit_pose.json). The
placement on the felt is the same shift cad/nest_v2/nest_v2.py uses.
"""
import datetime
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
REPO = os.path.dirname(LAB)
NEST = os.path.join(REPO, "print", "nest")

COLORS = {
    "felt_base": "felt",
    "felt_top": "felt",
    "stripe_plus": "foil",
    "stripe_minus": "foil",
    "cord_pocket": "pla",
    "cord_cap": "pla",
    "wall_card": "card",
    "gold_domes": "gold",
}
CATS = {
    "felt": ("Felt", "#cbb892"),
    "foil": ("Foil", "#c4a15a"),
    "pla": ("Printed PLA", "#c5b9a3"),
    "card": ("Wall card", "#8a5a3b"),
    "gold": ("Gold domes", "#e6c35c"),
    "duck": ("Duck", "#d9d3c7"),
    "cable": ("Cable", "#e07a1f"),
}


def _geom_mesh(mesh, name):
    if len(mesh.faces) > 600:
        step = int(np.ceil(len(mesh.faces) / 600.0))
        mesh = trimesh.Trimesh(vertices=np.asarray(mesh.vertices), faces=np.asarray(mesh.faces)[::step], process=False)
        mesh.remove_unreferenced_vertices()
    return dict(name=name, pos=np.asarray(mesh.vertices, np.float64), idx=np.asarray(mesh.faces, np.int64))


def _geom(path, name):
    return _geom_mesh(trimesh.load(path), name)


def _duck_on_mat():
    """Recorded sit, facing the room, seat on the felt. Sim pose, CAD shift."""
    sys.path.insert(0, os.path.join(REPO, "altaay_lab", "cad", "nest_v2"))
    import nest_v2
    posed, _pose = nest_v2.posed_duck()
    geoms, nodes = [], []
    for i, (inst, mesh) in enumerate(posed):
        name = "duck-%s-%d" % (inst["key"], i)
        geoms.append(_geom_mesh(mesh, name))
        cat = "gold" if inst["key"] == "gold_domes" else "duck"
        nodes.append(_node(name, i, np.eye(4), category=cat, sub="duck"))
    return geoms, nodes


def _node(name, mesh, matrix, category=None, sub="mat"):
    return dict(
        name=name, mesh=mesh, matrix=matrix,
        label=name.replace("_", " "), part=name,
        category=category or COLORS.get(name, "pla"),
        sub=sub, status="SIM",
        v1=[0, 0, 0], v2=[0, 0, 0], v3=[0, 0, 0],
    )


def build(out, scene, write_glb):
    names = [n[:-4] for n in sorted(os.listdir(NEST)) if n.endswith(".stl")]
    geoms = [_geom(os.path.join(NEST, n + ".stl"), n) for n in names]
    eye = np.eye(4)
    nodes = [_node(n, i, eye.copy()) for i, n in enumerate(names)]
    if scene == "nested":
        duck_geoms, duck_nodes = _duck_on_mat()
        off = len(geoms)
        for n in duck_nodes:
            n["mesh"] += off
        geoms.extend(duck_geoms)
        nodes.extend(duck_nodes)
    prefix = "nest" if scene == "nest" else "nested"
    nodes_man = {}
    for n in nodes:
        nodes_man[n["name"]] = dict(n)
        nodes_man[n["name"]]["matrix"] = [round(float(x), 6) for x in np.asarray(n["matrix"]).T.ravel()]
    cats = {k: dict(label=v[0], color=v[1], count=0) for k, v in CATS.items()}
    for v in nodes_man.values():
        cats[v["category"]]["count"] += 1
    printed = [dict(stl=n + ".stl", label=n.replace("_", " "), found=1, expected=1, ok=True, nodes=[n]) for n in names]
    if scene == "nested":
        for n in nodes:
            if n["name"].startswith("duck-"):
                printed.append(dict(stl=n["name"], label=n["label"], found=1, expected=1, ok=True, nodes=[n["name"]]))
    man = dict(
        meta=dict(
            generated=datetime.date.today().isoformat(),
            script="altaay_lab/viewer/make_viewer_data.py --scene %s" % scene,
            units="mm",
            scene=scene,
            explode=dict(stage1=[0.0, 0.6], stage2=[0.2, 0.9], stage3=[0.5, 1.0], horn_pull=14.0, insert_pull=11.0),
            note="SIM. Nest v2. Not the wall and paddle dock.",
        ),
        categories=cats,
        groups=[dict(id="mat", label="Nest", subs=["mat"])] + (
            [dict(id="duck", label="Duck", subs=["duck"])] if scene == "nested" else []),
        subassemblies={
            "mat": dict(label="Mat", group="mat", v1=[0, 0, 0], centre=[0, 0, 0]),
            "duck": dict(label="Duck", group="duck", v1=[0, 0, 0], centre=[0, 0, 0]),
        },
        tray=None,
        nodes=nodes_man,
        servos=[],
        blockers={},
        cables=[],
        bom_full=[],
        purchase=[],
        retention=[],
        labels=[],
        checklist=dict(
            summary=dict(
                printed=dict(found=len(printed), expected=len(printed), stl_files=len(printed),
                             stl_found=len(printed), grams=0, hours=0, doc_total_parts=len(printed),
                             grams_source="not sliced", pla=len(printed), tpu=0),
                servos=dict(found=0, expected=0),
                inserts=dict(found=0, expected=0, by_part={}),
                bearings=dict(found=0, expected=0),
                placeholders=dict(total=0, placed=0, tray=0, replaced={}),
                bom=dict(lines=0, cad=0, both=0, placeholder=0, filament=0, not_modelled=0, mismatches=[]),
                printed_mismatches=[],
                blockers_open=[],
                blockers_total=0,
                screws=dict(found=0, by_spec={}, expected=0),
                cables={"found": 0, "pass": 0, "test_fit": 0, "fail": 0},
            ),
            printed=printed,
            bom=[],
            extra=[],
            notes=[dict(kind="doc", text="SIM. 38 of 40 charging docks is sim pass only. The charge path is two nets.", nodes=[])],
        ),
    )
    path = os.path.join(out, prefix + ".glb")
    write_glb(path, geoms, nodes)
    # The page loads name.glb.txt (base64). dock_scene does that in write().
    import base64
    raw = open(path, "rb").read()
    open(path + ".txt", "w").write(base64.b64encode(raw).decode("ascii"))
    import json
    json.dump(man, open(os.path.join(out, prefix + "_manifest.json"), "w"), indent=1)
    print(prefix, "nodes", len(nodes), "bytes", len(raw))
