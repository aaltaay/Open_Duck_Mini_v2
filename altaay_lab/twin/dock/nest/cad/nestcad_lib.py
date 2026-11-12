"""nestcad_lib.py: shared numbers and helpers of the nest CAD (the charging nest of NATURAL_DOCK_IDEAS.md concept A).

CAD tool and conventions: the same as altaay_lab/twin/dock/dock_parts.py and altaay_lab/twin/sit/sit_cad.py: mesh CAD in
Python with trimesh and manifold3d, units mm, STL as the master file of every part, a JSON record next to the meshes.
The repo is only READ here (robot.urdf, print/*.stl and twin/sit/sitlib.py); nothing is written into it.

Frames (mm):
  trunk frame  the robot.urdf base frame at the zero pose, as sitlib.scene(): x forward, y left, z up.
  nest frame   as sim/nestlib.py: the sun centre on the floor is the origin, x toward the wall (the wall face is the
               plane x = WALL_X), y along the wall (left when you face the wall), z up from the floor.

Every number carries a label where it is used: CAD check only, calc only, sim pass only, index (read from a web search
result, the page itself could not be opened in this session) or est (an estimate with no source in hand).
"""
import json
import os
import sys

import numpy as np
import trimesh
import manifold3d

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("NEST_REPO", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..")))  # the repo root, relative to this file
LAB = os.path.join(REPO, "altaay_lab")
sys.dont_write_bytecode = True                      # the repo is read-only for this job: no __pycache__ in it
sys.path.insert(0, os.path.join(LAB, "twin", "sit"))
import sitlib as L  # noqa: E402

STL_DIR = os.path.join(HERE, "stl")
STEP_DIR = os.path.join(HERE, "step")
IMG_DIR = os.path.join(HERE, "renders")
TR = "trunk_assembly"

# --------------------------------------------------------------------------------------------------------------
# the spring pin (a bought part). QA Technology 100-40 series test probe in a 100-SDN250S solder cup socket.
# Source: the maker's 100-40 catalog, https://www.qatech.com/downloads/100-40_Catalog.pdf (copy at
# https://assets.testequity.com/te1/Documents/pdf/qa-technology/QA-Technology_100-40_Catalog_1123.pdf). Both hosts are
# outside this session's allowed network, so every value marked "index" was read from the search index only.
# --------------------------------------------------------------------------------------------------------------
PIN = dict(
    part="QA Technology 100-40 series probe, standard spring force, in a 100-SDN250S solder cup socket",
    full_stroke=10.16,        # index: "0.100 [2.54] Centers, 0.400 [10.16] Full Stroke"
    rated_stroke=8.05,        # index: forces are given at 0.317 [8.05] stroke
    preload_n=0.42,           # index: standard spring 1.5 oz [43 g / 0.42 N] preload
    rated_n=1.58,             # index: 5.7 oz [162 g / 1.58 N] at 0.317 [8.05]
    life_cycles=500000,       # index: "500,000 cycles"
    tube_d=1.367,             # index: probe diameter 0.0538 [1.367]
    socket_d=1.68,            # est, UNVERIFIED (a 100 mil socket; the catalog drawing was not read)
    mount_hole=1.75,          # est, UNVERIFIED: printed 1.5 and reamed to the catalog's mounting hole with the part in hand
    exposed=12.5,             # est, UNVERIFIED: tip to socket mouth with the plunger free
    socket_len=31.5,          # est, UNVERIFIED: socket mouth to the start of the solder cup
    tail_len=5.0,             # est, UNVERIFIED: solder cup
    press_ring=10.0,          # index: press ring 0.395 [10.03] from the socket mouth (one of three options listed)
    tip_d=2.3,                # est, UNVERIFIED: a spherical radius tip head; the tip style number is a BLOCKER
    probe_g=0.30, socket_g=0.30,   # est, UNVERIFIED: mass per piece
)
PIN_Y = 10.0                  # pins at y = +10 and -10 in each block (20 mm apart, as sim/nestlib.py PIN_Y)
PROUD = dict(seat=3.0, bump=7.5)      # tip proud of the block's lowest point with the plunger free (design choice)
SIT_PITCH = float(np.degrees(np.arctan2(0.04529620636087554, 0.998972088061579)))   # 2.596 deg: sim/calib.json pin_axis (sim pass only)
GAP_RANGE = (2.5, 6.0)        # bumper lowest point above the felt in the torque-off sit, 540-run sim (sim pass only)
GAP_PLANE = (2.47, 3.19)      # the same on the trusted plane contact model (NEST_SIM.md 2.7, sim pass only)
SEAT_LIFT_MAX = 0.87          # seat block lift with pins at twice the assumed force (NEST_SIM.md 2.7, sim pass only)

# the D59 blocks as sit_cad.py builds them (SEAT, BUMPER there)
BLOCK = dict(seat=dict(x=-110.0, z_low=-66.0, r=16.0, half_y=40.0, stl="sit_seat"),
             bump=dict(x=20.0, z_low=-69.0, r=12.0, half_y=30.0, stl="sit_bumper"))
VHB_T = 1.1                   # BOM 29, 3M VHB 4950
CARRIER = dict(col_d=7.0, web_t=3.0, flange_x=8.0, flange_y=29.0, flange_t=2.5, u_bot=-4.5, fit=0.3)
TPU_BORE = 3.6                # the plunger well in the TPU under the carrier (tip head 2.3 est + 0.65 a side)
BODY_HOLE = 3.4               # feedthrough in body_middle_bottom: socket tail and one 22 AWG lead (the M3 clearance drill)
WIRE_OD = 1.7                 # est: 22 AWG silicone lead
PLA_RHO, TPU_RHO = 1.24e-3, 1.21e-3       # g/mm3 (est: typical PLA and TPU 95A filament data)

# --------------------------------------------------------------------------------------------------------------
# the nest (nest frame)
# --------------------------------------------------------------------------------------------------------------
WALL_X = 190.0                # the sun centre is 190 mm from the wall (the brief; sim/nestlib.py WALL_X)
SUN_R = 50.0                  # golden disc, plus (coverage.py concentric pick)
GAP = 32.0                    # plain felt between the sun and the ring
RING_R0, RING_R1 = SUN_R + GAP, 235.0     # pale gold ring, minus
TIP_M = 3.0                   # a pin counts 3 mm inside its zone (coverage.py)
WINDOW = 45.0                 # any-heading landing window of the seat pin pair (coverage.py, calc only)
FELT_T = 1.0                  # each of the two felt layers
TOP_R = 247.0                 # upper felt layer radius (the sim's mat, 494 mm across)
BASE_R = 267.0                # lower felt layer radius: a 20 mm tread, so no step is higher than 1 mm
CLOTH_T = 0.10                # est: nickel copper polyester taffeta (Laird Flectron 3035-535 class, index in the study)
FOIL_T = 0.07                 # est: copper foil tape with conductive adhesive (3M 1181 class, UNVERIFIED)
RIM = dict(depth=50.0, height=30.0, half_len=227.0, r_top=13.0)       # the soft rim: 50 deep (the sim's was 72), 30 high
MAT_BACK = 6.0                # the felt layers end 6 mm from the wall, under the rim
RING_BACK = RIM["depth"] + 6.0            # the ring cloth ends 56 mm from the wall (6 mm in front of the rim face)
BOX = dict(half_len=90.0, x0=2.5, x1=46.0, z0=2.0, z1=27.0, wall=2.0, floor=2.0, lid=2.0, chamfer=9.0)
FEED_W = 12.0                 # plus feed foil between the felt layers
TAB_Y = 40.0                  # the ring tab enters the box at y = +40, the plus feed at y = -40 (a mirror pair, D42)
JACK = dict(hole=8.0, z=15.0, x=24.0)     # Same Sky PJ-005A, 5/16-32 bushing (dock BOM K6b), in the box end wall
M3_CLEAR, INSERT_D, INSERT_DEPTH = 3.4, 4.0, 5.8          # BOM 16 (CNC Kitchen M3 x 5.7, hole 4.0), BOM 17a (M3x8 SHCS)
SIM_WALL_MIN, SIM_RIM_MIN, SIM_RIM_DEPTH = 23.5, 9.5, 72.0   # NEST_SIM.md 2.3 (sim pass only), with the sim's 72 mm rim

COL = dict(felt=(0.71, 0.78, 0.62, 1), felt2=(0.66, 0.74, 0.58, 1), sun=(0.90, 0.70, 0.22, 1), ring=(0.95, 0.87, 0.60, 1),
           rim=(0.62, 0.72, 0.55, 1), box=(0.80, 0.76, 0.66, 1), foil=(0.80, 0.50, 0.25, 1), wall=(0.93, 0.91, 0.87, 1),
           floor=(0.80, 0.74, 0.64, 1), duck=(0.97, 0.83, 0.33, 1), leg=(0.96, 0.72, 0.40, 1), foot=(0.93, 0.56, 0.26, 1),
           tpu=(0.30, 0.33, 0.38, 1), carrier=(0.25, 0.60, 0.75, 1), pin=(0.95, 0.80, 0.20, 1), socket=(0.75, 0.75, 0.78, 1),
           wire_p=(0.80, 0.15, 0.12, 1), wire_m=(0.12, 0.12, 0.12, 1), board=(0.25, 0.50, 0.25, 1), metal=(0.6, 0.6, 0.65, 1))


def pin_force(comp):
    """N at a compression in mm: linear from the preload to the rated point (index values; calc only)"""
    if comp <= 0:
        return 0.0
    return PIN["preload_n"] + (PIN["rated_n"] - PIN["preload_n"]) * comp / PIN["rated_stroke"]


def pin_frame(which):
    """4x4 of a block's pin frame in the trunk frame: origin on the block's bottom cylinder axis at y 0, u (local z) up
    along the pin axis (the floor normal in the sit, SIT_PITCH from trunk z), local y = trunk y"""
    B = BLOCK[which]
    p = np.radians(SIT_PITCH)
    T = np.eye(4)
    T[:3, 0] = [np.cos(p), 0.0, -np.sin(p)]
    T[:3, 1] = [0.0, 1.0, 0.0]
    T[:3, 2] = [np.sin(p), 0.0, np.cos(p)]
    T[:3, 3] = [B["x"], 0.0, B["z_low"] + B["r"]]
    return T


def man(m):
    return L.to_man(m)


def tm(M):
    return L.from_man(M)


def cyl_u(T, y, u0, u1, d, sections=32):
    """cylinder along the local z of frame T at local (0, y), from u0 to u1 (trunk frame mesh)"""
    c = trimesh.creation.cylinder(radius=d / 2.0, height=u1 - u0, sections=sections)
    c.apply_translation((0.0, y, (u0 + u1) / 2.0))
    c.apply_transform(T)
    return c


def box_local(T, lo, hi):
    return L.box(lo, hi, T)


def mcyl(y, u0, u1, d, seg=48):
    """manifold cylinder along local z at local (0, y): exact local coordinates, so faces that should be coplanar are"""
    return manifold3d.Manifold.cylinder(float(u1 - u0), d / 2.0, d / 2.0, int(seg)).translate((0.0, float(y), float(u0)))


def mbox(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    return manifold3d.Manifold.cube(tuple(hi - lo)).translate(tuple(lo))


def clean(M, name):
    """a printable, watertight trimesh of a manifold (one body), checked by an STL round trip"""
    comps = [c for c in M.decompose() if c.volume() > 0.5]
    if len(comps) != 1:
        raise SystemExit("%s: %d bodies" % (name, len(comps)))
    m = tm(comps[0])
    m.merge_vertices()
    ok, vol = L.stl_roundtrip_ok(m)
    if not ok or abs(vol - comps[0].volume()) > 0.05:
        raise SystemExit("%s is not watertight after an STL round trip (volume %.2f against %.2f): pinched edges near %s" % (
            name, vol, comps[0].volume(), np.round(L.pinch_edges(m)[:3], 2).tolist()))
    return m


def write_part(name, mesh, record, step=True, material=None):
    """stl/<name>.stl and step/<name>.step of a part in its part frame; fills record[name]"""
    os.makedirs(STL_DIR, exist_ok=True)
    os.makedirs(STEP_DIR, exist_ok=True)
    p = os.path.join(STL_DIR, name + ".stl")
    mesh.export(p)
    ok, vol = L.stl_roundtrip_ok(mesh)
    rec = dict(stl="stl/%s.stl" % name, faces=int(len(mesh.faces)), watertight=bool(ok), volume_mm3=round(float(mesh.volume), 1),
               bbox_mm=np.round(mesh.bounds, 2).tolist(), bytes=os.path.getsize(p))
    if material:
        rec["material"] = material
    if step:
        import step_export
        s = step_export.mesh_to_step(mesh, os.path.join(STEP_DIR, name + ".step"), name)
        rec.update(step="step/%s.step" % name, step_bytes=s["bytes"], step_faces=s["faces"], step_volume_mm3=s["volume_mm3"])
        if abs(s["volume_mm3"] - mesh.volume) > max(1.0, 1e-3 * abs(mesh.volume)):
            raise SystemExit("%s: STEP volume %.1f differs from the mesh volume %.1f" % (name, s["volume_mm3"], mesh.volume))
    for k in ("bytes", "step_bytes"):
        if rec.get(k, 0) > 5e6:
            raise SystemExit("%s: %s is over 5 MB" % (name, k))
    record[name] = rec
    return rec


def dump(obj, path):
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=1)
        fh.write("\n")


def r(x, n=2):
    return round(float(x), n)


def render(items, az, el, dist, look, out, title, w=1500, h=1050, fovy=30, sub=None, ortho=None):
    """MuJoCo offscreen render of meshes in mm (the method of twin/sit/sit_pose.py _render). items: [(mesh, rgba)]"""
    import tempfile
    os.environ.setdefault("MUJOCO_GL", "egl")
    import mujoco
    from PIL import Image, ImageDraw, ImageFont
    d = tempfile.mkdtemp(prefix="nest_render_")
    assets, geoms = [], []
    for k, (m_, rgba) in enumerate(items):
        p = os.path.join(d, "m%d.stl" % k)
        c = m_.copy()
        c.apply_scale(0.001)
        c.export(p)
        assets.append('<mesh name="m%d" file="%s" inertia="shell"/>' % (k, p))
        geoms.append('<geom type="mesh" mesh="m%d" rgba="%s" contype="0" conaffinity="0"/>' % (k, " ".join(map(str, rgba))))
    gl = ('orthographic="true" fovy="%g"' % ortho) if ortho else ('fovy="%g"' % fovy)        # ortho: view height in m
    xml = ('<mujoco><visual><global offwidth="%d" offheight="%d" %s/><headlight ambient="0.68 0.68 0.68" '
           'diffuse="0.20 0.20 0.20" specular="0 0 0"/><quality offsamples="8"/><map znear="0.002" zfar="60"/></visual>'
           '<asset><texture type="skybox" builtin="flat" rgb1="0.984 0.980 0.965" rgb2="0.984 0.980 0.965" width="32" height="32"/>%s</asset>'
           '<worldbody><light pos="0 0 3" dir="0 0 -1" directional="true" diffuse="0.08 0.08 0.08" specular="0 0 0" castshadow="false"/>'
           '<light pos="-1 -1 2" dir="0.5 0.4 -0.6" directional="true" diffuse="0.06 0.06 0.06" specular="0 0 0" castshadow="false"/>'
           '%s</worldbody></mujoco>' % (w, h, gl, "".join(assets), "".join(geoms)))
    md = mujoco.MjModel.from_xml_string(xml)
    dd = mujoco.MjData(md)
    mujoco.mj_forward(md, dd)
    rr = mujoco.Renderer(md, h, w)
    cam = mujoco.MjvCamera()
    cam.lookat[:] = np.asarray(look, float) / 1000.0
    cam.azimuth, cam.elevation, cam.distance = az, el, dist
    rr.update_scene(dd, cam)
    im = Image.fromarray(rr.render())
    rr.close()
    dr = ImageDraw.Draw(im)
    try:
        f1 = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
        f2 = ImageFont.truetype("DejaVuSans.ttf", 18)
    except OSError:
        f1 = f2 = ImageFont.load_default()
    dr.rectangle([0, 0, w, 44 + (26 * len(sub) if sub else 0) + 8], fill=(251, 250, 246))
    dr.text((16, 8), title, fill=(46, 44, 40), font=f1)
    for k, s in enumerate(sub or []):
        dr.text((16, 44 + 26 * k), s, fill=(90, 86, 78), font=f2)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.save(out)
    return im
