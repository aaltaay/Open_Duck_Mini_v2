"""step_export.py: write a watertight triangle mesh (mm) as a STEP solid (AP214). CAD check only.

The project's CAD is mesh CAD (trimesh + manifold3d, as altaay_lab/twin/dock/dock_parts.py and twin/sit/sit_cad.py), so
the STL is the master file of every part. The STEP written here is the same solid as a faceted B-rep: one planar face
per group of coplanar triangles (ShapeUpgrade_UnifySameDomain merges them), curved surfaces stay as flat facets.
It needs OCP (pip package cadquery-ocp), which is NOT a repo dependency: point NEST_OCP at a folder that holds it
(pip install --target <folder> cadquery-ocp), outside the repo.
"""
import os
import sys

import numpy as np

_OCP = os.environ.get("NEST_OCP")
if _OCP and _OCP not in sys.path:
    sys.path.insert(0, _OCP)


def _st(cls, name):
    """a static method by either OCP naming (OCP 7: name_s, OCP 8: name)"""
    return getattr(cls, name + "_s", None) or getattr(cls, name)


def mesh_to_step(mesh, path, name="part", unify=True):
    """mesh: trimesh.Trimesh, watertight, mm. Returns dict(faces, volume_mm3, is_solid, bytes)."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
    from OCP.gp import gp_Pnt
    from OCP.TopoDS import TopoDS
    from OCP.TopAbs import TopAbs_SHELL, TopAbs_FACE
    from OCP.TopExp import TopExp_Explorer
    from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
    from OCP.ShapeFix import ShapeFix_Solid
    from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
    from OCP.Interface import Interface_Static
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    from OCP.TCollection import TCollection_HAsciiString
    V = np.asarray(mesh.vertices, float)
    sew = BRepBuilderAPI_Sewing(1e-4)
    P = [gp_Pnt(*map(float, v)) for v in V]
    for a, b, c in np.asarray(mesh.faces):
        poly = BRepBuilderAPI_MakePolygon(P[a], P[b], P[c], True)
        f = BRepBuilderAPI_MakeFace(poly.Wire(), True)
        if f.IsDone():
            sew.Add(f.Face())
    sew.Perform()
    sh = sew.SewedShape()
    ex = TopExp_Explorer(sh, TopAbs_SHELL)
    mk = BRepBuilderAPI_MakeSolid()
    n_shell = 0
    while ex.More():
        mk.Add(_st(TopoDS, 'Shell')(ex.Current()))
        n_shell += 1
        ex.Next()
    solid = mk.Solid()
    fx = ShapeFix_Solid(solid)
    fx.Perform()
    shape = fx.Solid()
    if unify:
        u = ShapeUpgrade_UnifySameDomain(shape, True, True, False)
        u.SetLinearTolerance(1e-4)
        u.SetAngularTolerance(1e-5)
        u.Build()
        shape = u.Shape()
    g = GProp_GProps()
    _st(BRepGProp, 'VolumeProperties')(shape, g)
    vol = g.Mass()
    if vol < 0:
        shape.Reverse()
        vol = -vol
    nf = 0
    ex = TopExp_Explorer(shape, TopAbs_FACE)
    while ex.More():
        nf += 1
        ex.Next()
    _st(Interface_Static, "SetCVal")("write.step.schema", "AP214")
    _st(Interface_Static, "SetCVal")("write.step.unit", "MM")
    _st(Interface_Static, "SetCVal")("write.step.product.name", name)
    w = STEPControl_Writer()
    w.Transfer(shape, STEPControl_AsIs)
    w.Write(path)
    return dict(faces=nf, volume_mm3=round(vol, 1), shells=n_shell, bytes=os.path.getsize(path))


if __name__ == "__main__":
    import trimesh
    for f in sys.argv[1:]:
        m = trimesh.load(f, force="mesh")
        print(f, mesh_to_step(m, os.path.splitext(f)[0] + ".step", os.path.basename(f)[:-4]), "mesh volume", round(m.volume, 1))
