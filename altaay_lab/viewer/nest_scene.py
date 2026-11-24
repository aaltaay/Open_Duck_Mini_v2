#!/usr/bin/env python3
"""Nest v2 mat and the five gold domes for the viewer.

The wall and paddle dock stays in dock_scene.py. This scene replaces it on the
page. Frames are millimetres, nest frame: sun at the origin, x toward the wall.
"""
import json
import os
import struct

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(LAB, ".."))
NEST = os.path.join(LAB, "print", "nest_v2")
DOME = os.path.join(ROOT, "mini_bdx", "robots", "open_duck_mini_v2", "gold_dome_install.json")

# Felt and foil colours. Not a material measurement.
COLORS = {
    "felt": "#c4a574",
    "foil_plus": "#c9a227",
    "foil_minus": "#e6d59a",
    "gold": "#d4af37",
    "pla": "#eceff1",
}


def load_stl(path):
    raw = open(path, "rb").read()
    if raw[:5].lower() == b"solid" and b"facet" in raw[:1000]:
        text = raw.decode("utf-8", "ignore").splitlines()
        verts, faces = [], []
        tri = []
        for line in text:
            bits = line.split()
            if len(bits) >= 4 and bits[0] == "vertex":
                tri.append([float(bits[1]), float(bits[2]), float(bits[3])])
                if len(tri) == 3:
                    base = len(verts)
                    verts.extend(tri)
                    faces.append([base, base + 1, base + 2])
                    tri = []
        return np.array(verts, np.float32), np.array(faces, np.uint32)
    n = struct.unpack("<I", raw[80:84])[0]
    verts, faces = [], []
    off = 84
    for i in range(n):
        rec = raw[off:off + 50]
        nums = struct.unpack("<12fH", rec)
        base = len(verts)
        verts.extend([nums[3:6], nums[6:9], nums[9:12]])
        faces.append([base, base + 1, base + 2])
        off += 50
    return np.array(verts, np.float32), np.array(faces, np.uint32)


def sphere(radius, n=8):
    verts, faces = [], []
    for i in range(n + 1):
        th = np.pi * i / n
        for j in range(n * 2):
            ph = 2 * np.pi * j / (n * 2)
            verts.append([radius * np.sin(th) * np.cos(ph), radius * np.sin(th) * np.sin(ph), radius * np.cos(th)])
    verts = np.array(verts, np.float32)
    for i in range(n):
        for j in range(n * 2):
            a = i * (n * 2) + j
            b = a + n * 2
            c = i * (n * 2) + (j + 1) % (n * 2)
            d = c + n * 2
            faces.append([a, c, b])
            faces.append([c, d, b])
    return verts, np.array(faces, np.uint32)


def eye():
    return np.eye(4)


def translate(x, y, z):
    m = np.eye(4)
    m[0, 3], m[1, 3], m[2, 3] = x, y, z
    return m


def build(out, scene, write_glb):
    inst = json.load(open(DOME))
    parts = [
        ("felt_base", "felt", "Felt base"),
        ("felt_top", "felt", "Felt top"),
        ("stripe_plus", "foil_plus", "Plus stripes"),
        ("stripe_minus", "foil_minus", "Minus stripes"),
        ("cord_pocket", "pla", "Cord pocket"),
        ("cord_cap", "pla", "Cord cap"),
        ("wall_card", "pla", "Wall card, study mark"),
    ]
    geoms, nodes, man_nodes = [], [], {}
    for name, cat, label in parts:
        path = os.path.join(NEST, name + ".stl")
        if not os.path.isfile(path):
            raise SystemExit("missing " + path)
        v, f = load_stl(path)
        geoms.append(dict(name=name, pos=v, idx=f))
        nodes.append(dict(name=name, mesh=len(geoms) - 1, matrix=eye()))
        man_nodes[name] = dict(label=label, category=cat, part=name, color=COLORS[cat], joins=[], host=None)
    v, f = sphere(inst["radius_mm"])
    geoms.append(dict(name="gold_dome", pos=v, idx=f))
    mesh_i = len(geoms) - 1
    # Seat on the felt. Tip is 0.9 mm into the 2 mm stack, so the centre is 0.6 mm above the felt top.
    zc = 2.0 + inst["radius_mm"] - inst["proud_mm"]
    for i, y in enumerate(inst["y_mm"]):
        nm = "gold_dome_%d" % (i + 1)
        nodes.append(dict(name=nm, mesh=mesh_i, matrix=translate(0.0, y, zc)))
        man_nodes[nm] = dict(label="Gold dome %d" % (i + 1), category="gold", part="gold_dome",
                             color=COLORS["gold"], joins=[], host=None)
    cats = {
        "felt": dict(label="Felt", color=COLORS["felt"], count=2),
        "foil_plus": dict(label="Plus foil", color=COLORS["foil_plus"], count=1),
        "foil_minus": dict(label="Minus foil", color=COLORS["foil_minus"], count=1),
        "pla": dict(label="Printed pocket", color=COLORS["pla"], count=3),
        "gold": dict(label="Gold dome", color=COLORS["gold"], count=5),
        "cable": dict(label="Cable", color="#607d8b", count=0),
    }
    title = "Nest" if scene == "nest" else "Nested"
    man = dict(
        meta=dict(generated="nest_v2", script="altaay_lab/viewer/nest_scene.py", units="mm",
                  frame="nest frame, sun at the origin, x toward the wall",
                  sources=dict(parts="altaay_lab/print/nest_v2", domes="gold_dome_install.json"),
                  scene=scene, explode=dict(stage1=[0.0, 0.6], stage2=[0.2, 0.9], stage3=[0.5, 1.0], horn_pull=14.0, insert_pull=11.0),
                  totals={}, placements="nest_v2 meshes plus five gold domes"),
        categories=cats,
        groups=[dict(id="nest", label="Nest mat", subs=["mat"])],
        subassemblies={"mat": dict(label=title, group="nest", v1=False, centre=[0, 0, 1])},
        tray=None, nodes=man_nodes, servos=[], blockers={},
        checklist=dict(summary=dict(printed=dict(found=2, expected=2, stl_files=2, stl_found=2, grams=0, hours=0,
                                                 doc_total_parts=2, grams_source="not sliced", pla=2, tpu=0),
                                    servos=dict(found=0, expected=0), inserts=dict(found=0, expected=0, by_part={}),
                                    bearings=dict(found=0, expected=0), placeholders=dict(total=0, placed=0, tray=0, replaced={}),
                                    bom=dict(lines=0, cad=0, both=0, placeholder=0, filament=0, not_modelled=0, mismatches=[]),
                                    printed_mismatches=[], blockers_open=[], blockers_total=0,
                                    screws=dict(found=0, by_spec={}, expected=0),
                                    cables={"found": 0, "pass": 0, "test_fit": 0, "fail": 0}),
                       printed=[], bom=[], extra=[],
                       notes=[dict(kind="doc", text="Nest v2 mat and five 0.9 mm gold domes. The wall and paddle dock is archived. Sim pass only for the 38 of 40 docks.", nodes=[])]),
        cables=[], bom_full=[], purchase={}, retention=[], labels=[])
    from dock_scene import write
    prefix = "nest" if scene == "nest" else "nested"
    write(out, prefix, geoms, nodes, man, write_glb)
    return prefix
