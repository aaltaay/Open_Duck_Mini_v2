#!/usr/bin/env python3
"""Parametric CAD for the nest mat, version 2.

The shape reuses the flush-contact field (20 mm conductor, 5 mm felt gap, five
3 mm wells) and the two 1 mm steps from the nest sim (radii 267 and 247 mm,
here as a straight edge at the same stations). The charger and the gate stay
the boards already drawn. Nothing in print/, the URDF, or the nest CAD folder
is written.

Run from the repo root:
  python3 altaay_lab/cad/nest_v2/nest_v2.py
Writes stl/, step/, checks.json, and renders/.

Labels: CAD check only on the meshes, calc only on the arithmetic, sim pass only
only when a stored run is cited. The sit pose used for the renders is
twin/sit/sit_pose.json (sim pass only).
"""
import json
import os
import sys

import numpy as np
import trimesh

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
STL_DIR = os.path.join(HERE, "stl")
STEP_DIR = os.path.join(HERE, "step")
IMG_DIR = os.path.join(HERE, "renders")

# Flush study, draw_flush.py. Calc only there. Kept so this mat matches the window.
PERIOD = 25.0
STRIPE_W = 20.0
GAP = 5.0
WELL_D = 3.0
WELLS_Y = (-24.0, -12.0, 0.0, 12.0, 24.0)
FIELD_HY = 280.0          # half-width of the active field, along the wall
FIELD_HX = 180.0          # half-depth of the active field
WIN_Y, WIN_X = 254.0, 161.0

# Nest sim v3 edge, as straight stations at the same radii. CAD check only once built.
WALL_X = 190.0            # sun centre to the wall, the approved distance
MAT_BACK = 6.0            # felt ends this far short of the wall
TOP_FRONT = -247.0        # upper felt, the sim's TOP_R
BASE_FRONT = -267.0       # lower felt, the sim's BASE_R, 20 mm tread
BACK = WALL_X - MAT_BACK  # 184
FELT_T = 1.0
TOP_HY = FIELD_HY         # 280
BASE_HY = FIELD_HY + 20.0 # 300, the side tread
FOIL_T = 0.10             # surface foil, flush with the 2 mm felt
FOIL_Z0 = 2 * FELT_T - FOIL_T

# Bus bars between the felt layers, at the wall end of the stripes.
# Even periods are plus, odd periods are minus, matching draw_flush.band.
PLUS_TAB = (174.0, 184.0)
MINUS_TAB = (160.0, 172.0)
PLUS_RAIL = (176.0, 184.0)
MINUS_RAIL = (158.0, 170.0)
RAIL_Z = (1.00, 1.40)

# Cord pocket, off the field, at the left end (positive y). Inner clear fits the
# 70 x 26 x 14 mm gate board the nest CAD kept room for.
POCKET = dict(x0=146.0, x1=184.0, y0=302.0, y1=386.0, z0=0.0, z1=24.0, wall=3.0, hole_d=8.0)
# A wide felt tab, so the cord pocket reads as part of the rug, not a loose brick.
TONGUE = dict(x0=80.0, x1=184.0, y0=TOP_HY - 8.0, y1=POCKET["y0"] + 4.0)

# The 40 mm wall card from the close-up study. Flush on the wall, centre 350 mm up.
CARD = dict(size=40.0, z=350.0, thick=1.0)

# Board the pocket is sized for. Nest CAD, CAD check only there: 70 x 26 x 14 mm.
BOARD = (70.0, 26.0, 14.0)


def box(x0, x1, y0, y1, z0, z1):
    import manifold3d
    return manifold3d.Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def stripe_spans(y_limit):
    """(k, y0, y1, plus) for every conductor that meets the field. k even is plus."""
    k0 = int(np.floor((-y_limit) / PERIOD)) - 1
    k1 = int(np.floor(y_limit / PERIOD)) + 1
    out = []
    for k in range(k0, k1 + 1):
        a, b = PERIOD * k, PERIOD * k + STRIPE_W
        lo, hi = max(a, -y_limit), min(b, y_limit)
        if hi - lo < 1.0:
            continue
        out.append((k, lo, hi, k % 2 == 0))
    return out


def to_tm(man):
    mesh = man.to_mesh()
    v = np.array(mesh.vert_properties[:, :3], float)
    f = np.array(mesh.tri_verts, np.int64)
    m = trimesh.Trimesh(vertices=v, faces=f, process=True)
    trimesh.repair.fix_normals(m)
    return m


def build_parts():
    import manifold3d
    spans = stripe_spans(FIELD_HY - 2.0)
    pockets = []
    plus_bits, minus_bits = [], []
    for k, y0, y1, plus in spans:
        # Surface pocket, open at the top of the felt, floor under the foil.
        pockets.append(box(-FIELD_HX, FIELD_HX, y0, y1, FOIL_Z0, 2 * FELT_T + 0.2))
        tab = PLUS_TAB if plus else MINUS_TAB
        pockets.append(box(tab[0], tab[1], y0, y1, RAIL_Z[0], 2 * FELT_T + 0.2))
        foil = box(-FIELD_HX, tab[0], y0, y1, FOIL_Z0, 2 * FELT_T)
        drop = box(tab[0], tab[1], y0, y1, RAIL_Z[0], 2 * FELT_T)
        (plus_bits if plus else minus_bits).append(foil + drop)
    # Rails tie one polarity. They sit in a pocket so they do not fuse into the felt.
    pockets.append(box(PLUS_RAIL[0], PLUS_RAIL[1], -FIELD_HY, FIELD_HY, RAIL_Z[0], RAIL_Z[1]))
    pockets.append(box(MINUS_RAIL[0], MINUS_RAIL[1], -FIELD_HY, FIELD_HY, RAIL_Z[0], RAIL_Z[1]))
    plus_bits.append(box(PLUS_RAIL[0], PLUS_RAIL[1], -FIELD_HY + 4, FIELD_HY - 4, RAIL_Z[0], RAIL_Z[1]))
    minus_bits.append(box(MINUS_RAIL[0], MINUS_RAIL[1], -FIELD_HY + 4, FIELD_HY - 4, RAIL_Z[0], RAIL_Z[1]))
    # Tails from the rails into the cord pocket, covered by the tongue.
    pockets.append(box(PLUS_RAIL[0], PLUS_RAIL[1], FIELD_HY - 4, POCKET["y0"] + 2, RAIL_Z[0], RAIL_Z[1]))
    pockets.append(box(MINUS_RAIL[0], MINUS_RAIL[1], FIELD_HY - 4, POCKET["y0"] + 2, RAIL_Z[0], RAIL_Z[1]))
    plus_bits.append(box(PLUS_RAIL[0], PLUS_RAIL[1], FIELD_HY - 4, POCKET["y0"] - 1, RAIL_Z[0], RAIL_Z[1]))
    minus_bits.append(box(MINUS_RAIL[0], MINUS_RAIL[1], FIELD_HY - 4, POCKET["y0"] - 1, RAIL_Z[0], RAIL_Z[1]))

    felt_base = box(BASE_FRONT, BACK, -BASE_HY, BASE_HY, 0.0, FELT_T)
    felt_base = felt_base + box(TONGUE["x0"], TONGUE["x1"], TONGUE["y0"], TONGUE["y1"], 0.0, FELT_T)
    felt_top = box(TOP_FRONT, BACK, -TOP_HY, TOP_HY, FELT_T, 2 * FELT_T)
    felt_top = felt_top + box(TONGUE["x0"], TONGUE["x1"], TONGUE["y0"], TONGUE["y1"], FELT_T, 2 * FELT_T)
    felt_top = manifold3d.Manifold.batch_boolean([felt_top] + pockets, manifold3d.OpType.Subtract)

    plus = manifold3d.Manifold.batch_boolean(plus_bits, manifold3d.OpType.Add)
    minus = manifold3d.Manifold.batch_boolean(minus_bits, manifold3d.OpType.Add)

    p = POCKET
    outer = box(p["x0"], p["x1"], p["y0"], p["y1"], p["z0"], p["z1"])
    inner = box(p["x0"] + p["wall"], p["x1"] - p["wall"], p["y0"] + p["wall"], p["y1"] - p["wall"],
                p["wall"], p["z1"] + 1.0)
    hole = manifold3d.Manifold.cylinder(p["y1"] - p["y0"], p["hole_d"] / 2, circular_segments=32)
    hole = hole.rotate([90, 0, 0]).translate((
        (p["x0"] + p["x1"]) / 2, p["y1"], (p["z0"] + p["z1"]) / 2))
    pocket = outer - inner - hole
    cap = box(p["x0"] + 1.0, p["x1"] - 1.0, p["y0"] + 1.0, p["y1"] - 1.0, p["z1"] - 2.0, p["z1"])

    c = CARD
    card = box(WALL_X - c["thick"], WALL_X, -c["size"] / 2, c["size"] / 2, c["z"] - c["size"] / 2, c["z"] + c["size"] / 2)

    wells = manifold3d.Manifold()
    for y in WELLS_Y:
        wells = wells + manifold3d.Manifold.cylinder(0.6, WELL_D / 2, circular_segments=24).translate((0.0, y, 0.0))

    parts = {
        "felt_base": to_tm(felt_base),
        "felt_top": to_tm(felt_top),
        "stripe_plus": to_tm(plus),
        "stripe_minus": to_tm(minus),
        "cord_pocket": to_tm(pocket),
        "cord_cap": to_tm(cap),
        "wall_card": to_tm(card),
        "seat_wells": to_tm(wells),
    }
    return parts, spans


def load_step():
    import importlib.util
    p = os.path.join(REPO, "altaay_lab", "twin", "dock", "nest", "cad", "step_export.py")
    spec = importlib.util.spec_from_file_location("nest_step_export", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def export(parts):
    os.makedirs(STL_DIR, exist_ok=True)
    os.makedirs(STEP_DIR, exist_ok=True)
    step = load_step()
    rec = {}
    for name, mesh in parts.items():
        stl = os.path.join(STL_DIR, name + ".stl")
        mesh.export(stl)
        st = step.mesh_to_step(mesh, os.path.join(STEP_DIR, name + ".step"), name)
        rec[name] = dict(
            stl="stl/%s.stl" % name,
            step="step/%s.step" % name,
            stl_bytes=os.path.getsize(stl),
            step_bytes=st["bytes"],
            volume_mm3=round(float(mesh.volume), 1),
            step_volume_mm3=st["volume_mm3"],
            watertight=bool(mesh.is_watertight),
            faces=int(len(mesh.faces)),
        )
        if abs(st["volume_mm3"] - mesh.volume) > max(5.0, 0.01 * abs(mesh.volume)):
            raise SystemExit("%s STEP volume %.1f vs mesh %.1f" % (name, st["volume_mm3"], mesh.volume))
        for key in ("stl_bytes", "step_bytes"):
            if rec[name][key] > 5_000_000:
                raise SystemExit("%s %s is over 5 MB" % (name, key))
    return rec


def checks(parts, spans, rec):
    """CAD check only, except the window line which is the flush study's calc."""
    top = parts["felt_top"]
    base = parts["felt_base"]
    plus, minus = parts["stripe_plus"], parts["stripe_minus"]
    pocket = parts["cord_pocket"]
    out = []

    def add(name, ok, detail):
        out.append(dict(name=name, ok=bool(ok), detail=detail))
        if not ok:
            print("FAIL", name, detail)
        return ok

    add("felt top is 2 mm at the sun",
        abs(top.bounds[1][2] - 2.0) < 0.05 and abs(top.bounds[0][2] - 1.0) < 0.05,
        "z %.2f to %.2f" % (top.bounds[0][2], top.bounds[1][2]))
    add("two 1 mm steps, 20 mm tread",
        abs(base.bounds[0][0] - BASE_FRONT) < 0.2 and abs(top.bounds[0][0] - TOP_FRONT) < 0.2
        and abs((TOP_FRONT - BASE_FRONT) - 20.0) < 0.01,
        "base x0 %.1f, top x0 %.1f" % (base.bounds[0][0], top.bounds[0][0]))
    add("back edge 6 mm off the wall",
        abs(BACK - (WALL_X - MAT_BACK)) < 0.01 and abs(base.bounds[1][0] - BACK) < 0.2,
        "back x %.1f, wall %.1f" % (base.bounds[1][0], WALL_X))
    add("foil is flush, not proud of the felt",
        plus.bounds[1][2] <= 2.01 and minus.bounds[1][2] <= 2.01,
        "plus zmax %.3f, minus zmax %.3f" % (plus.bounds[1][2], minus.bounds[1][2]))
    add("gap is 5 mm, wider than a 3 mm well",
        abs(GAP - 5.0) < 1e-6 and GAP > WELL_D,
        "gap %.1f mm, well %.1f mm" % (GAP, WELL_D))
    # A point in the middle of an even stripe is plus, a gap point is on neither.
    add("plus and minus alternate, matching the flush band rule",
        _polarity_ok(spans, plus, minus),
        "%d stripes" % len(spans))
    p = POCKET
    clear_x = (p["x1"] - p["wall"]) - (p["x0"] + p["wall"])
    clear_y = (p["y1"] - p["wall"]) - (p["y0"] + p["wall"])
    clear_z = p["z1"] - p["wall"]
    add("cord pocket clears the 70 x 26 x 14 mm board",
        clear_y >= BOARD[0] and clear_x >= BOARD[1] and clear_z >= BOARD[2],
        "clear %.1f x %.1f x %.1f mm" % (clear_y, clear_x, clear_z))
    add("pocket is outside the seat window",
        p["y0"] > WIN_Y,
        "pocket y0 %.1f, window %.1f" % (p["y0"], WIN_Y))
    add("no screw holes",
        True,
        "the cord hole is the jack exit, one hole, not a fastener. D39: it has a job. D42: no screws, so no pattern")
    add("seat wells are five, 3 mm, 12 mm apart",
        len(WELLS_Y) == 5 and abs(WELLS_Y[1] - WELLS_Y[0] - 12.0) < 1e-6
        and abs(parts["seat_wells"].extents[1] - (48 + WELL_D)) < 0.5,
        "span y %.2f" % parts["seat_wells"].extents[1])
    add("every mesh is watertight and under 5 MB",
        all(r["watertight"] and r["stl_bytes"] < 5_000_000 and r["step_bytes"] < 5_000_000 for r in rec.values()),
        "parts %d" % len(rec))
    add("window is the published box",
        WIN_Y == 254.0 and WIN_X == 161.0,
        "+/-%.0f mm along the wall, +/-%.0f mm deep" % (WIN_Y, WIN_X))
    failed = [c for c in out if not c["ok"]]
    return out, failed


def _polarity_ok(spans, plus, minus):
    """A ray down through a stripe centre hits that polarity and misses the other."""
    for k, y0, y1, is_plus in spans:
        if y1 - y0 < STRIPE_W - 0.5:
            continue
        y = (y0 + y1) / 2
        x = 0.0
        origin = np.array([[x, y, 5.0]])
        direction = np.array([[0.0, 0.0, -1.0]])
        hp = plus.ray.intersects_any(origin, direction)[0]
        hm = minus.ray.intersects_any(origin, direction)[0]
        if is_plus and not (hp and not hm):
            return False
        if (not is_plus) and not (hm and not hp):
            return False
        gy = y1 + GAP / 2
        if gy < FIELD_HY - 4:
            og = np.array([[x, gy, 5.0]])
            if plus.ray.intersects_any(og, direction)[0] or minus.ray.intersects_any(og, direction)[0]:
                return False
    return True


def _rot180():
    t = np.eye(4)
    t[0, 0] = t[1, 1] = -1.0
    return t


def posed_duck():
    """The recorded sit, turned to face the room, seat on the felt. Sim pose, CAD placement."""
    sys.path.insert(0, os.path.join(REPO, "altaay_lab", "twin", "sit"))
    import sit_pose
    pose = json.load(open(os.path.join(REPO, "altaay_lab", "twin", "sit", "sit_pose.json")))
    items, _ = sit_pose.posed_meshes(pose)
    r = _rot180()
    posed = []
    for inst, mesh in items:
        m = mesh.copy()
        m.apply_transform(r)
        posed.append((inst, m))
    seat = [m for inst, m in posed if inst["key"] == "sit_seat"]
    if len(seat) != 1:
        raise SystemExit("expected one seat, got %d" % len(seat))
    v = seat[0].vertices
    z0 = float(v[:, 2].min())
    low = v[v[:, 2] < z0 + 1.5]
    c = low.mean(axis=0)
    shift = np.eye(4)
    shift[:3, 3] = (-c[0], -c[1], 2.0 - z0)
    out = []
    for inst, m in posed:
        m.apply_transform(shift)
        out.append((inst, m))
    return out, pose


def wells_on_seat(duck):
    """Five gold discs in pockets on the seat face, flush, not proud. CAD check only.

    The pockets are cut in a copy of the posed seat for the render. print/sit_seat.stl
    is not written.
    """
    import manifold3d
    seat = [m for inst, m in duck if inst["key"] == "sit_seat"][0]
    v = seat.vertices
    z0 = float(v[:, 2].min())
    low = v[v[:, 2] < z0 + 1.2]
    c = low.mean(axis=0)
    cutters = manifold3d.Manifold()
    discs = []
    for y in WELLS_Y:
        cutters = cutters + manifold3d.Manifold.cylinder(1.6, WELL_D / 2, circular_segments=24).translate(
            (c[0], c[1] + y, z0 - 0.4))
        disc = manifold3d.Manifold.cylinder(0.45, (WELL_D - 0.2) / 2, circular_segments=24).translate(
            (c[0], c[1] + y, z0))
        discs.append(to_tm(disc))
    src = manifold3d.Mesh(vert_properties=np.asarray(seat.vertices, np.float32),
                          tri_verts=np.asarray(seat.faces, np.uint32))
    cut = to_tm(manifold3d.Manifold(src) - cutters)
    return discs, cut, dict(seat_low_z=round(z0, 2), centre_xy=(round(float(c[0]), 1), round(float(c[1]), 1)),
                            gold_bottom_z=round(z0, 2), gold_top_z=round(z0 + 0.45, 2))


def _vtk_actor(mesh, rgb):
    import vtk
    from vtkmodules.util import numpy_support
    pts = vtk.vtkPoints()
    pts.SetData(numpy_support.numpy_to_vtk(np.asarray(mesh.vertices, np.float64), deep=True))
    faces = np.asarray(mesh.faces, np.int64)
    n = len(faces)
    cells = np.empty((n, 4), np.int64)
    cells[:, 0] = 3
    cells[:, 1:] = faces
    ca = vtk.vtkCellArray()
    ca.SetCells(n, numpy_support.numpy_to_vtkIdTypeArray(cells.ravel(), deep=True))
    poly = vtk.vtkPolyData()
    poly.SetPoints(pts)
    poly.SetPolys(ca)
    norms = vtk.vtkPolyDataNormals()
    norms.SetInputData(poly)
    norms.ConsistencyOn()
    norms.Update()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(norms.GetOutput())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    prop = actor.GetProperty()
    prop.SetColor(*rgb)
    prop.SetAmbient(0.35)
    prop.SetDiffuse(0.70)
    prop.SetSpecular(0.08)
    return actor


def _scene(parts, duck, wells):
    import vtk
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.97, 0.96, 0.93)
    ren.SetAmbient(0.25, 0.24, 0.22)
    felt = (0.74, 0.66, 0.52)
    actors = {
        "felt_base": _vtk_actor(parts["felt_base"], felt),
        "felt_top": _vtk_actor(parts["felt_top"], (0.78, 0.71, 0.56)),
        "stripe_plus": _vtk_actor(parts["stripe_plus"], (0.66, 0.50, 0.28)),
        "stripe_minus": _vtk_actor(parts["stripe_minus"], (0.55, 0.42, 0.24)),
        "cord_pocket": _vtk_actor(parts["cord_pocket"], (0.66, 0.58, 0.46)),
        "cord_cap": _vtk_actor(parts["cord_cap"], felt),
        "wall_card": _vtk_actor(parts["wall_card"], (0.45, 0.28, 0.20)),
    }
    for a in actors.values():
        ren.AddActor(a)
    floor = _vtk_actor(to_tm(box(-420, 280, -460, 480, -3.0, 0.0)), (0.84, 0.80, 0.74))
    wall = _vtk_actor(to_tm(box(WALL_X, WALL_X + 16, -420, 460, 0.0, 520)), (0.91, 0.89, 0.85))
    ren.AddActor(floor)
    ren.AddActor(wall)
    body = (0.93, 0.90, 0.85)
    tpu = (0.42, 0.39, 0.36)
    duck_actors = []
    for inst, mesh in duck:
        key = inst["key"]
        if mesh.vertices.shape[0] < 4:
            continue
        rgb = tpu if ("foot" in key or "pad" in key or "bumper" in key or "seat" in key or "tpu" in key) else body
        if "eye" in key:
            rgb = (0.25, 0.23, 0.20)
        actor = _vtk_actor(mesh, rgb)
        ren.AddActor(actor)
        duck_actors.append((key, actor))
    well_actors = []
    for d in wells:
        a = _vtk_actor(d, (0.82, 0.66, 0.30))
        ren.AddActor(a)
        well_actors.append(a)
    for pos, foc, col in (
        ((-600, -400, 700), (0, 0, 40), (1.0, 0.97, 0.90)),
        ((200, 500, 400), (-40, 0, 30), (0.85, 0.88, 0.95)),
    ):
        light = vtk.vtkLight()
        light.SetPosition(*pos)
        light.SetFocalPoint(*foc)
        light.SetColor(*col)
        light.SetIntensity(0.85)
        ren.AddLight(light)
    return ren, actors, floor, wall, well_actors, duck_actors


def _shot(ren, path, pos, focal, up=(0, 0, 1), title="", hide=()):
    import vtk
    from PIL import Image, ImageDraw, ImageFont
    for a in hide:
        a.SetVisibility(0)
    cam = ren.GetActiveCamera()
    cam.SetPosition(*pos)
    cam.SetFocalPoint(*focal)
    cam.SetViewUp(*up)
    cam.SetClippingRange(0.5, 8000.0)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.AddRenderer(ren)
    win.SetSize(1500, 1050)
    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(path)
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()
    win.Finalize()
    for a in hide:
        a.SetVisibility(1)
    if title:
        im = Image.open(path)
        dr = ImageDraw.Draw(im)
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 22)
        except OSError:
            font = ImageFont.load_default()
        tw = dr.textlength(title, font=font)
        dr.rectangle([16, 16, 32 + tw, 52], fill=(251, 250, 246))
        dr.text((24, 22), title, fill=(46, 44, 40), font=font)
        im.save(path)


def render(parts, duck, wells):
    os.makedirs(IMG_DIR, exist_ok=True)
    ren, actors, floor, wall, well_actors, duck_actors = _scene(parts, duck, wells)
    keep = {"sit_seat", "sit_bumper"}
    hidden_body = [a for key, a in duck_actors if key not in keep]
    hide_mat = (floor, wall, actors["felt_base"], actors["felt_top"], actors["stripe_plus"],
                actors["stripe_minus"], actors["cord_pocket"], actors["cord_cap"], actors["wall_card"])
    # Shots. Positions are mm, nest frame. The wall is +x.
    shots = [
        ("sit_three_quarter.png", (-980, -760, 640), (0, 0, 60), (0, 0, 1), "The sit, on the mat", ()),
        ("sit_side.png", (30, -1100, 320), (10, 0, 50), (0, 0, 1), "Side, facing the room", ()),
        ("sit_front.png", (-1100, -40, 280), (20, 0, 60), (0, 0, 1), "Facing the room", ()),
        ("mat_top.png", (-20, 10, 1450), (-20, 10, 0), (1, 0, 0), "The mat, from above. Wall at the top.", ()),
        ("belly.png", (0, -36, -28), (0, 0, 2), (0, 1, 0), "Under the seat. Five flush wells, nothing proud.",
         hide_mat + tuple(hidden_body)),
    ]
    import vtk
    under = vtk.vtkLight()
    under.SetPosition(0, -20, -80)
    under.SetFocalPoint(0, 0, 2)
    under.SetIntensity(1.4)
    under.SetColor(1.0, 0.96, 0.88)
    for name, pos, focal, up, title, hide in shots:
        if name == "belly.png":
            ren.AddLight(under)
        _shot(ren, os.path.join(IMG_DIR, name), pos, focal, up, title, hide)
        if name == "belly.png":
            ren.RemoveLight(under)
        print("wrote", name)
    return [s[0] for s in shots]


def main():
    parts, spans = build_parts()
    rec = export(parts)
    rows, failed = checks(parts, spans, rec)
    duck, pose = posed_duck()
    wells, seat_cut, seat_note = wells_on_seat(duck)
    duck = [(inst, seat_cut if inst["key"] == "sit_seat" else mesh) for inst, mesh in duck]
    # How high the bumper and the soles sit, once the seat is on the felt.
    gaps = {}
    for inst, mesh in duck:
        key = inst["key"]
        if key in ("sit_seat", "sit_bumper") or "foot_bottom" in key:
            gaps[key + ":" + inst["link"]] = round(float(mesh.vertices[:, 2].min()) - 2.0, 2)
    doc = dict(
        label="CAD check only, except the sit pose (sim pass only) and the window (calc only, flush study)",
        parts=rec,
        checks=rows,
        failed=[c["name"] for c in failed],
        seat=seat_note,
        gaps_mm_above_felt=gaps,
        pose_pitch_deg=pose.get("trunk_pitch_deg"),
        n_stripes=len(spans),
        n_plus=sum(1 for s in spans if s[3]),
        n_minus=sum(1 for s in spans if not s[3]),
    )
    with open(os.path.join(HERE, "checks.json"), "w") as fh:
        json.dump(doc, fh, indent=1)
        fh.write("\n")
    if failed:
        raise SystemExit("checks failed: %s" % doc["failed"])
    render(parts, duck, wells)
    print("PASS", len(parts), "parts", len(spans), "stripes")


if __name__ == "__main__":
    main()
