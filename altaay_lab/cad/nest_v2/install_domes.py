#!/usr/bin/env python3
"""Gold domes on the seat, and a copy of the nest v2 meshes into print/nest.

The domes are the 0.9 mm proud caps from twin/dock/camera/SEAT_CONTACTS.md.
print/sit_seat.stl is not replaced. The new mesh sits in the seat part frame.

Run from the repo root:
  python3 altaay_lab/cad/nest_v2/install_domes.py
"""
import os
import shutil

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SEAT = os.path.join(REPO, "print", "sit_seat.stl")
PRINT_NEST = os.path.join(REPO, "print", "nest")
URDF_DIR = os.path.join(REPO, "mini_bdx", "robots", "open_duck_mini_v2")
WELL_Y = (-24.0, -12.0, 0.0, 12.0, 24.0)
R_MM = 1.5
PROUD_MM = 0.9


def cap(face):
    """Spherical cap, 1.5 mm radius, 0.9 mm proud, outward toward -z.

    The sphere centre sits inside the seat. Vertices below the face are the cap.
    """
    sphere = trimesh.creation.icosphere(subdivisions=3, radius=R_MM)
    centre = face + np.array([0.0, 0.0, R_MM - PROUD_MM])
    sphere.apply_translation(centre)
    keep = sphere.vertices[:, 2] <= face[2] + 1e-6
    faces = keep[sphere.faces].all(axis=1)
    out = sphere.submesh([np.flatnonzero(faces)], append=True)
    return out


def main():
    seat = trimesh.load(SEAT)
    zmin = float(seat.vertices[:, 2].min())
    low = seat.vertices[seat.vertices[:, 2] < zmin + 2.0]
    c = low.mean(axis=0)
    parts = []
    for y in WELL_Y:
        parts.append(cap(np.array([c[0], c[1] + y, zmin])))
    domes = trimesh.util.concatenate(parts)
    mm_path = os.path.join(REPO, "print", "gold_domes.stl")
    domes.export(mm_path)
    meters = domes.copy()
    meters.apply_scale(0.001)
    meters.export(os.path.join(URDF_DIR, "gold_domes.stl"))
    os.makedirs(PRINT_NEST, exist_ok=True)
    src = os.path.join(HERE, "stl")
    for name in sorted(os.listdir(src)):
        if name.endswith(".stl"):
            shutil.copyfile(os.path.join(src, name), os.path.join(PRINT_NEST, name))
    nest_urdf = os.path.join(URDF_DIR, "nest")
    os.makedirs(nest_urdf, exist_ok=True)
    for name in sorted(os.listdir(src)):
        if not name.endswith(".stl"):
            continue
        m = trimesh.load(os.path.join(src, name))
        m.apply_scale(0.001)
        m.export(os.path.join(nest_urdf, name))
    print("domes", domes.extents.tolist(), "faces", len(domes.faces))
    print("centre", [round(float(x), 2) for x in c], "zmin", round(zmin, 2))
    print("print nest", len(os.listdir(PRINT_NEST)), "files")


if __name__ == "__main__":
    main()
