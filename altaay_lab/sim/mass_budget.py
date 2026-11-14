"""Mass budget of the Open Duck Mini v2 as the lab will build it, against the trained model (sim pass only).

What it does
1. Lists every part of our build with its mass and a source tag ([U] upstream file, [L] lab file or script,
   [I] internet page, UNVERIFIED when no source was found; the basis of every UNVERIFIED number is printed).
2. Places every part in a link of the robot: CAD parts on their URDF mesh instance (uniform density over the
   mesh, the same way Onshape computes the trained model), lab-only parts as boxes at audit/placements.json,
   screws and inserts at their measured hole sites (audit/sites.json, audit/sites_head.json), wires along a
   route polyline through the joints they cross (wiring/netlist.yaml), small parts at their CAD seat.
3. Sums mass, centre of mass and inertia per link and for the whole robot and compares them with the
   MuJoCo model the policy was trained on (Open_Duck_Playground MJCF) and with the URDF inertials.
4. Fits the trained model's own per-part masses (non-negative least squares on each link's mass, first moment
   and inertia) so the difference can be explained part by part where the fit is well posed.

Frames: every link frame is the URDF link frame (identical to the MJCF body frame, checked in check_frames()).
Lengths in metres inside the code, mm in the printed tables.

Usage (paths relative to the repo; nothing outside the repo is needed except the Playground clone):
  ODM_PLAYGROUND=<Open_Duck_Playground at b9be205> ODM_OUT=<scratch folder> python3 altaay_lab/sim/mass_budget.py
Outputs in ODM_OUT: mass_budget.json (every part and link) and mass_budget_tables.md (the tables in MASS_BUDGET.md).
Other scripts import build_budget() (sim/added_mass_sim.py).
"""
import os, sys, json, math, collections
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../.."))
LAB = os.path.join(REPO, "altaay_lab")
URDF_DIR = os.path.join(REPO, "mini_bdx/robots/open_duck_mini_v2")
PRINT_DIR = os.path.join(REPO, "print")
PG = os.environ.get("ODM_PLAYGROUND", "/home/user/upstream/Open_Duck_Playground")
OUT = os.environ.get("ODM_OUT", "/tmp/odm_mass")

# ---------------------------------------------------------------------------------------------------------------
# Unit masses and material data, each with its source
# ---------------------------------------------------------------------------------------------------------------
S = {}   # key -> (value, tag)
def src(key, value, tag):
    S[key] = (value, tag); return value

STS3215_G = src("sts3215", 55.0, "[I] Feetech STS3215 C001 product specification 2023-06-23, item 6-8 'Weight 55 +/- 1 g' (copy at https://download.kamami.pl/p1198708-STS3215-C001-20230624.pdf)")
P30B_G = src("p30b", 47.0, "[I] Molicel INR-18650-P30B product data sheet v1.0, 'Weight 47 g (Max)' (https://cdn.shopify.com/s/files/1/0481/9678/0183/files/Product-Data-Sheet-of-INR-18650-P30B-80111-2.pdf); 44.7 to 45.0 g measured in a UN38.3 report (https://www.18650batterystore.com/products/molicel-p30b-18650-3000mah-36a-battery)")
PI_G = src("pi", 10.0, "[I] Adafruit 5291 Raspberry Pi Zero 2 W, 'Product Weight: 10.0g' (https://www.adafruit.com/product/5291)")
HEADER_G = src("header", 2.1, "[I] Adafruit 2822 2x20 male header for the Pi Zero, 'Weight: 2.1g' (https://www.adafruit.com/product/2822)")
BNO_G = src("bno055", 3.0, "[I] Adafruit 2472, 'Weight: 3g' (https://www.adafruit.com/product/2472)")
ADAPTER_G = src("adapter", 16.0, "[I] Waveshare Bus Servo Adapter (A) page, 'Weight: 0.016 kg' (https://www.waveshare.com/bus-servo-adapter-a.htm); may include packaging")
CHARGER_G = src("charger", 8.53, "[I] Amazon B0BJTW4QBR Adeept 2S USB-C charger, 'Item Weight 8.53 g' (https://www.amazon.com/dp/B0BJTW4QBR)")
P45B_G = src("p45b", 70.0, "[I] Molicel INR21700P45B-01 cell specification v0.2, 2.4.2 'Weight (g) 70.0 (Max)', 21.40 +/- 0.15 x 70.00 +/- 0.15 mm (https://www.kronium.cz/uploads/p45b-datasheet.pdf); D44")
PACKWRAP_G = src("packwrap", 5.0, "UNVERIFIED: 2S1P P45B pack wrap: 2 nickel strips 0.15 x 8 x 30 mm (0.3 g, 8.9 g/cm3), a 2S PVC sleeve and fish-paper rings (about 3 g), 16 AWG leads 2 x 0.08 m (about 1.5 g); not weighed (track 9)")
# D44 (track 9): the 2S1P P45B pack replaces the 2 x P30B cells and the 2 x 18650 holder. Cells as solid cylinders' boxes on
# their axes in the grown bay (trunk frame, mm): x -133.1, y -9.35 and +12.2, z -4.0 to 67.0 (twin/battery/BAY.md)
P45B_SEATS = [(-133.1, -9.35, 31.5), (-133.1, 12.2, 31.5)]
HOLDER_G = src("holder", 25.0, "UNVERIFIED: Amazon B09WCT8672 lists 'Item Weight 0.05 kg' with 'Unit Count 2 Count' (https://www.amazon.com/dp/B09WCT8672); 25 g assumes the 0.05 kg is for 2 holders; 50 g if it is one")
SG90_G = src("sg90", 9.0, "[I] Amazon B072V529YD Miuzei SG90, 'Item Weight 9 g' (https://www.amazon.com/dp/B072V529YD), lead included")
BEC_G = src("bec", 29.0, "[I] Castle CC BEC Pro user guide 095-0047-00, 'Weight (w/o wires) 1 oz (29 grams)' (https://www.freakware.de/technik/CastleCreations/cc_bec_pro_user_guide.pdf)")
SW2815_G = src("sw2815", 2.6, "[I] Pololu 2815 specs, 'Weight: 2.6 g' without the optional connectors (https://www.pololu.com/product/2815/specs)")
REG_G = src("d30v30f5", 3.3, "[I] Pololu 4892 D30V30F5 specs, 'Weight: 3.3 g' without headers (https://www.pololu.com/product/4892/specs)")
AMP_G = src("max98357", 1.2, "[I] Adafruit 3006, 'Product Weight: 1.2g' (https://www.adafruit.com/product/3006)")
SPK_G = src("speaker", 28.8, "[I] Same Sky CMS0361KLX datasheet, 'weight 28.8 g' (https://www.sameskydevices.com/product/resource/cms0361klx.pdf)")
USB_G = src("usb_cable", 20.0, "[I] Adafruit 3878 USB C to Micro B 0.9 m, 'Product Weight: 20.0g' (https://www.adafruit.com/product/3878)")
XT30_G = src("xt30_pair", 0.9, "[I] Amazon B08P5HVMYT Amass XT30U 10 pairs, 'Item Weight 0.317 ounces' = 9.0 g for 10 pairs (https://www.amazon.com/dp/B08P5HVMYT)")
SS_G = src("omron_ss", 1.6, "[I] Omron SS datasheet en-ss.pdf, 'Weight Approx. 1.6g (pin plunger models)' (https://omronfs.omron.com/en_US/ecb/products/pdf/en-ss.pdf)")
GLASS_G = src("eye_glass", 2.08, "[I] Amazon B0C4H17QSH 60 discs, 'Item Weight 4.4 ounces' = 2.08 g per disc with packaging (upper bound) (https://www.amazon.com/dp/B0C4H17QSH)")
INSERT_G = src("insert", 0.35, "[I] CNC Kitchen US store product data for 'Heat Set Insert M3 x 5.7 - 100 pieces': variant weight 35 g per 100 (store shipping weight, bag included) (https://cnckitchenus.store/products/heat-set-insert-m3-x-5-7-100-pieces.js)")
# UNVERIFIED small items (no published mass found); basis given
TENERGY_G = src("tenergy_bms", 3.0, "UNVERIFIED: Tenergy 32175 page gives no weight; 34 x 16 x 4.5 mm box x 1.2 g/cm3 (median bounding-box density of the 5 small boards above with a published weight: Pi 0.97, MAX98357A 1.16, D30V30F5 1.03, 2815 1.37, BNO055 about 1.9 g/cm3)")
SWITCH_G = src("panel_switch", 2.0, "UNVERIFIED: stock panel slide switch, no datasheet part yet (BOM 10b); CAD power_switch.stl 0.96 cm3 x about 2 g/cm3 (metal and plastic)")
CAM_G = src("camera3", 4.0, "UNVERIFIED: Raspberry Pi Camera Module 3 weight not found (raspberrypi.com refused curl, product brief and Adafruit 5657 give none); 25 x 24 x 11.5 mm module")
FPC_G = src("fpc", 0.7, "UNVERIFIED: Adafruit 3157 camera cable 150 x 16 x 0.2 mm (product page), about 1.4 g/cm3 laminate")
SD_G = src("microsd", 0.5, "UNVERIFIED: microSD card, no weight on the SanDisk listing read")
LED_G = src("led", 0.3, "UNVERIFIED: uxcell 1 W COB bead B07DHB13J4, listing gives no weight")
RES_G = src("resistor", 0.25, "UNVERIFIED: 1/4 W through-hole resistor, no weight on the Adafruit 2782 or SparkFun PRT-14493 pages")
REFL_G = src("reflector", 1.5, "UNVERIFIED: Aurorad S5 20 x 15 mm aluminium reflector, Amazon page returned an error")
FUSEHOLDER_G = src("fuse_holder", 8.0, "UNVERIFIED: Littelfuse FHAC0001ZXJ body 50 x 17.2 x 17.2 mm with 2 x 90 mm 16 AWG leads (BOM L3); leads alone 2 x 0.09 m x 18.1 g/m = 3.3 g, body and cover about 4.7 g")
FUSE_G = src("ato_fuse", 1.0, "UNVERIFIED: Littelfuse 0287015.PXCN ATO blade, no weight found")
SPLICE_G = src("splice", 0.5, "UNVERIFIED: one solder splice with adhesive heat shrink")
TAPE_DENS = src("vhb_density", 0.8, "UNVERIFIED: 3M VHB 4950 foam density about 0.8 g/cm3 (3M data sheet not read); 1.1 mm thick, 19 mm wide (BOM 29)")
HOUSING_G = src("housing", 0.15, "UNVERIFIED: Molex 50-37-5033 or 2.54 mm housing")
TERMINAL_G = src("terminal", 0.05, "UNVERIFIED: Molex 08-70-1040 or 2.54 mm crimp terminal")
BEC_LEADS_G = src("bec_out_leads", 4.6, "UNVERIFIED: CC BEC Pro output leads, length and gauge not published (netlist U1); 2 leads x 3 wires x 150 mm x 5.1 g/m (22 AWG silicone)")
DOCKPAD_G = src("dock_pad", 15.6, "calc: BOM DK1 chest pad 100 x 76 x 0.8 mm FR4 at 1.85 g/cm3 (11.2 g) plus four 100 x 17.5 mm strips of 2 oz copper (70 um, 8.94 g/cm3: 4.4 g); not weighed")
IDEAL_DIODE_G = src("ideal_diode", 0.2, "[L] BOM.md DK7: Pololu 5383 7.6 x 12.7 mm, 0.2 g (Pololu page); the 5382 (DK2, DK6) is taken the same (UNVERIFIED)")
NTC_G = src("ntc", 0.5, "UNVERIFIED: Adafruit 372 10 k NTC with its leads, no weight on the page")
MIC_G = src("mic_3421", 0.4, "[L] twin/companion/COMPANION.md: Adafruit 3421, 16.7 x 12.7 x 1.8 mm, 0.4 g each (product page)")
MPR121_G = src("mpr121", 3.0, "BLOCKER: Adafruit 1982 MPR121 mass not published; twin/freeze/FREEZE.md section 6 takes about 6 g for the two")
TOF_G = src("tof", 1.8, "[L] twin/freeze/FREEZE.md section 6: Adafruit 5396 VL53L4CD board 1.8 g")
FOIL_G = src("copper_foil", 1.9, "[L] twin/freeze/FREEZE.md section 6: Adafruit 1127 copper foil pads PH1, PH2, PB1 with guard rings, about 1.9 g")
SOLDER_HS_G = src("solder_heatshrink", 4.0, "UNVERIFIED: solder and heat shrink on about 60 joints outside the splices, about 0.07 g each")
TIE_G = src("cable_ties", 1.0, "UNVERIFIED: a few small cable ties (USB slack coil, harness)")
BEARING_STEEL = src("steel_density", 7.85, "[I] AZoM 304 stainless density 7.85 to 8.06 g/cm3 (https://www.azom.com/properties.aspx?ArticleID=965); 7.85 used for bearing steel")
BEARING_NOTE = src("bearing", None, "UNVERIFIED: 6804ZZ mass not found (SKF, NSK, vendor pages refused or 404); CAD roll_bearing.stl solid ring x 7.85 g/cm3 = 26.9 g, an upper bound (real bearings have balls and a cage)")

# screws: ISO 4762 (DIN 912) head and socket sizes, pitch diameter shank, A2 density
ISO4762 = {"M2": dict(d=2.0, P=0.4, dk=3.8, k=2.0, s=1.5, t=1.0), "M2.5": dict(d=2.5, P=0.45, dk=4.5, k=2.5, s=2.0, t=1.1),
           "M3": dict(d=3.0, P=0.5, dk=5.5, k=3.0, s=2.5, t=1.3)}
src("iso4762", None, "[I] ISO 4762 / DIN 912 dimensions dk, k, s, t (https://www.fasteners.eu/standards/DIN/912/)")
A2_DENS = src("a2_density", 7.95, "[I] AZoM 304 stainless density 7.85 to 8.06 g/cm3, middle 7.95 used (https://www.azom.com/properties.aspx?ArticleID=965)")
def shcs_g(size, L):
    p = ISO4762[size]
    head = math.pi / 4 * p["dk"] ** 2 * p["k"] - (math.sqrt(3) / 2) * p["s"] ** 2 * p["t"]
    d2 = p["d"] - 0.6495 * p["P"]                      # pitch diameter (ISO 724)
    shank = math.pi / 4 * d2 ** 2 * L
    return (head + shank) * A2_DENS / 1000.0
def panhead_g(d, P, dk, k, L):                          # pan head self-tapping, head as a cylinder
    head = math.pi / 4 * dk ** 2 * k
    d2 = d - 0.6495 * P
    return (head + math.pi / 4 * d2 ** 2 * L) * A2_DENS / 1000.0
SCREW_G = {"M3x5": shcs_g("M3", 5), "M3x6": shcs_g("M3", 6), "M3x8": shcs_g("M3", 8), "M3x10": shcs_g("M3", 10), "M3x12": shcs_g("M3", 12),
           "M2.5x6": shcs_g("M2.5", 6), "M2.5x8": shcs_g("M2.5", 8), "M2.5x10": shcs_g("M2.5", 10),
           "M2x6pan": panhead_g(2.0, 0.4, 4.0, 1.6, 6), "M2x5pan": panhead_g(2.0, 0.4, 4.0, 1.6, 5), "M2x4pan": panhead_g(2.0, 0.4, 4.0, 1.6, 4)}
src("screw_mass", None, "[L] computed in sim/mass_budget.py from ISO 4762 sizes and the A2 density: " + ", ".join(f"{k} {v:.2f} g" for k, v in SCREW_G.items()))
src("servo_bag", None, "UNVERIFIED: STS3215 bag screws (B2, sizes not published); taken as M2x6 pan head, D18 gives the M2 pan head as 4.0 x 1.6 mm; the horn centre screw is M3x6 (Feetech spec item 6-13) taken as an M3x6 SHCS")

# wire mass per metre: tinned copper (AWG area, copper 8.935 g/cm3) plus silicone (0.95 to 1.20 g/cm3, 1.20 used)
CU_DENS = src("cu_density", 8.935, "[I] Wikipedia Copper, density 8.935 g/cm3 at 20 C (https://en.wikipedia.org/wiki/Copper)")
SIL_DENS = src("silicone_density", 1.20, "[I] Wikipedia Silicone rubber, density 0.95 to over 1.20 g/cm3, high end used (https://en.wikipedia.org/wiki/Silicone_rubber)")
OD_MM = {16: 3.0, 20: 1.8, 22: 1.7, 26: 1.5}
src("wire_od", None, "[I] BNTECHGO listings, outside diameter +/- 0.1 mm: 16 AWG 3.0 (https://www.amazon.com/dp/B01MCRY7OT), 20 AWG 1.8 (https://www.amazon.com/dp/B01F8PO5XE), 22 AWG 1.7 (https://www.amazon.com/dp/B09X4KY56S), 26 AWG 1.5 mm (https://www.amazon.com/dp/B08F9CF85N)")
src("awg", None, "[I] Wikipedia American wire gauge, d = 0.127 mm x 92^((36 - n) / 39) (https://en.wikipedia.org/wiki/American_wire_gauge)")
def awg_area(n):
    d = 0.127 * 92 ** ((36 - n) / 39.0); return math.pi / 4 * d * d, d
def wire_g_per_m(n, od=None):
    a, d = awg_area(n); od = od or OD_MM[n]
    ins = math.pi / 4 * od * od - math.pi / 4 * (1.15 * d) ** 2      # stranded bundle about 1.15 x the solid diameter
    return a * CU_DENS + ins * SIL_DENS                               # mm2 x g/cm3 = g/m
WIRE_GPM = {n: wire_g_per_m(n) for n in OD_MM}
src("wire_gpm", None, "[L] computed: " + ", ".join(f"{n} AWG {v:.1f} g/m" for n, v in WIRE_GPM.items()) + "; check: the BNTECHGO 16 AWG listing gives 'Item Weight 11.2 ounces' for 50 ft = 20.8 g/m with packaging")
KIT_GPM = src("kit_cable_gpm", 2.2, "UNVERIFIED: STS3215 kit cable conductor not published (power_path_sim.py assumes 26 AWG); 26 AWG copper 1.15 g/m plus PVC 1.1 mm OD at 1.4 g/cm3 = 2.2 g/m per conductor")

# printed parts: sliced grams minus support grams (print/SLICE_SUMMARY.md, robot set, PrusaSlicer 2.7.2, final settings)
src("slice", None, "[L] print/SLICE_SUMMARY.md per-part table: 'g each' minus 'support g each' (support is removed after printing; skirt is 1 loop, 1 layer, under 0.1 g)")
PRINT_SRC = S["slice"][1]
def load_slice_summary():
    path = os.path.join(LAB, "print/SLICE_SUMMARY.md"); rows = {}; on = False
    for line in open(path):
        if line.startswith("## "): on = line.startswith("## Per part")      # only the robot-set table (not the optional antennas)
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if on and len(c) == 11 and c[0].endswith(".stl") and c[1].isdigit():
            rows[c[0][:-4]] = dict(qty=int(c[1]), material=c[2], g_each=float(c[4]), support_each=float(c[6]))
    assert len(rows) == 49, len(rows)      # 36 robot STLs, 44 with the D59 sit parts, 47 with the neck stop block, its pads and the head pad, 49 with the two
                                           # conformal roll pads (twin/sit/sit_print.py)
    return rows

# ---------------------------------------------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------------------------------------------
class Mass:
    """mass m (kg), com c (m, link frame), inertia I about the com (kg m2, link axes)"""
    def __init__(self, m=0.0, c=(0, 0, 0), I=None):
        self.m = float(m); self.c = np.array(c, float); self.I = np.zeros((3, 3)) if I is None else np.array(I, float)
    def __add__(self, o):
        m = self.m + o.m
        if m <= 0: return Mass()
        c = (self.m * self.c + o.m * o.c) / m
        def sh(x):
            r = x.c - c; return x.I + x.m * (np.dot(r, r) * np.eye(3) - np.outer(r, r))
        return Mass(m, c, sh(self) + sh(o))
def box_mass(m, c, dims):
    a, b, h = dims
    return Mass(m, c, np.diag([m * (b * b + h * h), m * (a * a + h * h), m * (a * a + b * b)]) / 12.0)
def point_mass(m, c): return Mass(m, c)

_mesh_cache = {}
def mesh_props(path):
    """unit-density volume (m3), centroid (m) and inertia about the centroid per unit density, of an STL (m or mm)"""
    if path not in _mesh_cache:
        import trimesh
        mesh = trimesh.load(path, force="mesh")
        if mesh.extents.max() > 5: mesh.apply_scale(0.001)          # print STLs are in mm
        mesh.density = 1.0
        _mesh_cache[path] = (float(mesh.volume), mesh.center_mass.copy(), mesh.moment_inertia.copy(), mesh)
    return _mesh_cache[path]
def mesh_mass(path, T, m):
    V, c, J, _ = mesh_props(path); R = T[:3, :3]; t = T[:3, 3]
    return Mass(m, R @ c + t, R @ (J * (m / V)) @ R.T)   # also right for a mirror (det -1)

# ---------------------------------------------------------------------------------------------------------------
# Trained model inertials
# ---------------------------------------------------------------------------------------------------------------
BODIES = ["trunk_assembly", "hip_roll_assembly", "left_roll_to_pitch_assembly", "knee_and_ankle_assembly", "knee_and_ankle_assembly_2",
          "foot_assembly", "neck_pitch_assembly", "head_pitch_to_yaw", "neck_yaw_assembly", "head_assembly", "hip_roll_assembly_2",
          "right_roll_to_pitch_assembly", "knee_and_ankle_assembly_3", "knee_and_ankle_assembly_4", "foot_assembly_2"]
SHORT = {"trunk_assembly": "trunk", "hip_roll_assembly": "L hip roll link", "left_roll_to_pitch_assembly": "L hip pitch link",
         "knee_and_ankle_assembly": "L thigh (knee servo)", "knee_and_ankle_assembly_2": "L shin (ankle servo)", "foot_assembly": "L foot",
         "neck_pitch_assembly": "neck pitch link", "head_pitch_to_yaw": "head pitch link", "neck_yaw_assembly": "head yaw link",
         "head_assembly": "head", "hip_roll_assembly_2": "R hip roll link", "right_roll_to_pitch_assembly": "R hip pitch link",
         "knee_and_ankle_assembly_3": "R thigh (knee servo)", "knee_and_ankle_assembly_4": "R shin (ankle servo)", "foot_assembly_2": "R foot"}
def mjcf_assets():
    xd = os.path.join(PG, "playground/open_duck_mini_v2/xmls"); a = {}
    for f in os.listdir(xd):
        if f.endswith(".xml"): a[f] = open(os.path.join(xd, f), "rb").read()
    for f in os.listdir(os.path.join(xd, "assets")): a[f] = open(os.path.join(xd, "assets", f), "rb").read()
    return xd, a
def model_inertials():
    import mujoco
    xd, a = mjcf_assets()
    m = mujoco.MjModel.from_xml_string(open(os.path.join(xd, "open_duck_mini_v2.xml")).read(), assets=a)
    out = {}
    for b in BODIES:
        i = m.body(b).id; q = m.body_iquat[i]; R = np.zeros(9); mujoco.mju_quat2Mat(R, q); R = R.reshape(3, 3)
        out[b] = Mass(m.body_mass[i], m.body_ipos[i], R @ np.diag(m.body_inertia[i]) @ R.T)
    return out
def urdf():
    import yourdfpy
    return yourdfpy.URDF.load(os.path.join(URDF_DIR, "robot.urdf"), load_meshes=False, build_scene_graph=True)
def urdf_inertials(u):
    out = {}
    for ln, link in u.link_map.items():
        if link.inertial is None or link.inertial.mass < 1e-6: continue
        Ro = link.inertial.origin[:3, :3]
        out[ln] = Mass(link.inertial.mass, link.inertial.origin[:3, 3], Ro @ link.inertial.inertia @ Ro.T)
    # the MJCF head carries the antenna holders (separate links in the URDF): merge them at zero angle
    h = out["head_assembly"]
    for al in ("left_antenna_holder", "right_antenna_holder"):
        T = u.get_transform(al, "head_assembly"); x = out.pop(al)
        h = h + Mass(x.m, T[:3, :3] @ x.c + T[:3, 3], T[:3, :3] @ x.I @ T[:3, :3].T)
    out["head_urdf_with_antenna_holders"] = h
    return out
def check_frames(u):
    """max difference between MJCF body frames and URDF link frames at the zero pose (mm, rotation entries)"""
    import mujoco
    xd, a = mjcf_assets()
    m = mujoco.MjModel.from_xml_string(open(os.path.join(xd, "open_duck_mini_v2.xml")).read(), assets=a)
    d = mujoco.MjData(m); d.qpos[:] = 0; d.qpos[3] = 1; mujoco.mj_kinematics(m, d)
    tb = m.body("trunk_assembly").id
    Tt = np.eye(4); Tt[:3, :3] = d.xmat[tb].reshape(3, 3); Tt[:3, 3] = d.xpos[tb]
    dp = dr = 0.0
    for b in BODIES:
        i = m.body(b).id; Tm = np.eye(4); Tm[:3, :3] = d.xmat[i].reshape(3, 3); Tm[:3, 3] = d.xpos[i]
        Tm = np.linalg.inv(Tt) @ Tm; Tu = u.get_transform(b, "trunk_assembly")
        dp = max(dp, np.abs(Tm[:3, 3] - Tu[:3, 3]).max() * 1000); dr = max(dr, np.abs(Tm[:3, :3] - Tu[:3, :3]).max())
    return dp, dr

# ---------------------------------------------------------------------------------------------------------------
# Our build
# ---------------------------------------------------------------------------------------------------------------
SERVO_CASE = ("wj-wk00-0123middlecase_56.stl", "wj-wk00-0124bottomcase_45.stl", "wj-wk00-0122topcabinetcase_95.stl")
HORNS = ("drive_palonier.stl", "passive_palonier.stl")
PRINT_NAME = {"left_knee_to_ankle_left_sheet": "knee_to_ankle_left_sheet", "left_knee_to_ankle_right_sheet": "knee_to_ankle_right_sheet"}
JOINT_OF_ID = {20: "left_hip_yaw", 21: "left_hip_roll", 22: "left_hip_pitch", 23: "left_knee", 24: "left_ankle",
               10: "right_hip_yaw", 11: "right_hip_roll", 12: "right_hip_pitch", 13: "right_knee", 14: "right_ankle",
               30: "neck_pitch", 31: "head_pitch", 32: "head_yaw", 33: "head_roll"}   # [U] Runtime ids, netlist SVxx
LINK_ALIAS = {"left_antenna_holder": "head_assembly", "right_antenna_holder": "head_assembly", "trunk": "trunk_assembly",
              "head": "head_assembly", "left_foot": "foot_assembly", "right_foot": "foot_assembly_2",
              # D59 sit parts on their own fixed links (twin/sit/sitlib.py SIT_LINKS): the MJCF body they ride on
              "left_knee_bumper": "knee_and_ankle_assembly_2", "right_knee_bumper": "knee_and_ankle_assembly_4",
              "left_ankle_pads": "foot_assembly", "right_ankle_pads": "foot_assembly_2", "left_hip_pad": "left_roll_to_pitch_assembly",
              "right_hip_pad": "right_roll_to_pitch_assembly", "sit_seat": "trunk_assembly", "sit_bumper": "trunk_assembly",
              "neck_stop": "trunk_assembly", "neck_pads": "trunk_assembly", "head_pad": "head_pitch_to_yaw",
              "left_roll_pad": "left_roll_to_pitch_assembly", "right_roll_pad": "right_roll_to_pitch_assembly"}

class Item:
    def __init__(self, name, cat, mass_g, source, link, mass_obj, in_model, note=""):
        self.name, self.cat, self.mass_g, self.source, self.link, self.M, self.in_model, self.note = name, cat, mass_g, source, link, mass_obj, in_model, note

def build_budget(holder_g=None, include_antennas=False):
    """returns dict(items=[Item], links={body: Mass}, model={body: Mass}, urdf=..., fit=..., notes=[...])"""
    u = urdf()
    sl = load_slice_summary()
    items = []; notes = []
    def T_of(link):   # transform of a URDF link into its MJCF body frame (antenna links -> head)
        tgt = LINK_ALIAS.get(link, link)
        return tgt, (np.eye(4) if tgt == link else u.get_transform(link, tgt))
    # ---- CAD instances from the URDF ----
    inst = []      # (link_target, mesh_file, T_in_target)
    for ln, link in u.link_map.items():
        tgt, Tl = T_of(ln)
        for v in link.visuals:
            fn = os.path.basename(v.geometry.mesh.filename)
            inst.append((tgt, fn, Tl @ (v.origin if v.origin is not None else np.eye(4)), ln))
    # servo groups: one per servo case set (topcabinetcase instance); 55 g split case/horns as the trained model (fit below)
    case_frac = 0.874   # [L] fit_model(): the trained model's case parts carry 87 % of the servo group mass (leg and neck links)
    servo_groups = collections.defaultdict(list)
    for k, (tgt, fn, T, ln) in enumerate(inst):
        if fn in SERVO_CASE + HORNS:
            servo_groups[(tgt, ln)].append((fn, T))
    n_servo = 0; servo_pos = {}
    for (tgt, ln), lst in servo_groups.items():
        cases = [x for x in lst if x[0] in SERVO_CASE]; horns = [x for x in lst if x[0] in HORNS]
        nset = len([x for x in cases if x[0] == SERVO_CASE[2]])
        Vc = sum(mesh_props(os.path.join(URDF_DIR, f))[0] for f, _ in cases); Vh = sum(mesh_props(os.path.join(URDF_DIR, f))[0] for f, _ in horns)
        M = Mass()
        for f, T in cases: M = M + mesh_mass(os.path.join(URDF_DIR, f), T, nset * STS3215_G / 1000 * case_frac * mesh_props(os.path.join(URDF_DIR, f))[0] / Vc)
        for f, T in horns: M = M + mesh_mass(os.path.join(URDF_DIR, f), T, nset * STS3215_G / 1000 * (1 - case_frac) * mesh_props(os.path.join(URDF_DIR, f))[0] / Vh)
        items.append(Item(f"STS3215 C001 servo x{nset}", "servo", nset * STS3215_G, S["sts3215"][1], tgt, M, True))
        n_servo += nset
        for f, T in cases:
            if f == SERVO_CASE[2]:
                servo_pos.setdefault(tgt, []).append(T)
    assert n_servo == 14, n_servo
    # printed parts and CAD electronics
    head_stl_T = None
    for tgt, fn, T, ln in inst:
        base = fn[:-4]
        if fn in SERVO_CASE + HORNS: continue
        pname = PRINT_NAME.get(base, base)
        if pname in sl:
            r = sl[pname]; g = r["g_each"] - r["support_each"]
            pp = os.path.join(PRINT_DIR, pname + ".stl")
            geom = pp if os.path.exists(pp) else os.path.join(URDF_DIR, fn)
            items.append(Item(pname, "printed", g, PRINT_SRC, tgt, mesh_mass(geom, T, g / 1000), True,
                              "TPU" if r["material"] == "TPU" else ""))
            if pname == "head": head_stl_T = T
            continue
        if base == "antenna":
            g = 0.89 - 0.33
            if include_antennas:
                items.append(Item("antenna rod (optional)", "printed", g, "[L] print/SLICE_SUMMARY.md optional table, 0.89 g less 0.33 g support", tgt, mesh_mass(os.path.join(URDF_DIR, fn), T, g / 1000), True))
            continue
        P = os.path.join(URDF_DIR, fn)
        if base == "cell":       # D44: one P45B per URDF cell instance, on the grown bay's cell axes
            k_cell = sum(1 for it in items if it.name == "Molicel P45B cell")
            c_mm = np.array(P45B_SEATS[k_cell]) / 1000.0
            items.append(Item("Molicel P45B cell", "battery", P45B_G, S["p45b"][1] + "; seat: grown bay (D44, track 9)", tgt,
                              box_mass(P45B_G / 1000, c_mm, (0.0214, 0.0214, 0.070)), True))
        elif base == "holder":   # D44: the 2 x 18650 holder is gone; the spot-welded pack's strip, sleeve and leads instead
            g = holder_g if holder_g is not None else PACKWRAP_G
            items.append(Item("2S1P P45B pack strip, sleeve and leads", "battery", g, S["packwrap"][1], tgt,
                              box_mass(g / 1000, np.array((-133.1, 1.4, 31.5)) / 1000.0, (0.0222, 0.0437, 0.071)), True))
        elif base == "bms":
            pass   # replaced by the Tenergy board at its placement (below)
        elif base == "board" and ln == "trunk_assembly":
            items.append(Item("Waveshare Bus Servo Adapter (A)", "electronics", ADAPTER_G, S["adapter"][1], tgt, mesh_mass(P, T, ADAPTER_G / 1000), True))
        elif base == "board":
            notes.append("head board.stl is the Pi footprint (MOUNTING.md, B7): no mass of its own")
        elif base == "raspberrypizerow":
            items.append(Item("Raspberry Pi Zero 2 W", "electronics", PI_G, S["pi"][1], tgt, mesh_mass(P, T, PI_G / 1000), True))
            items.append(Item("2x20 header on the Pi", "electronics", HEADER_G, S["header"][1], tgt, mesh_mass(P, T, HEADER_G / 1000), False))
            items.append(Item("microSD card", "electronics", SD_G, S["microsd"][1], tgt, mesh_mass(P, T, SD_G / 1000), False))
            pi_T = (tgt, T)
        elif base == "bno055":
            items.append(Item("BNO055 breakout (Adafruit 2472)", "electronics", BNO_G, S["bno055"][1], tgt, mesh_mass(P, T, BNO_G / 1000), True))
        elif base == "usb_c_charger":
            items.append(Item("USB-C 2S charger (Adeept)", "electronics", CHARGER_G, S["charger"][1], tgt, mesh_mass(P, T, CHARGER_G / 1000), True))
        elif base == "power_switch":
            items.append(Item("panel control switch", "electronics", SWITCH_G, S["panel_switch"][1], tgt, mesh_mass(P, T, SWITCH_G / 1000), True))
        elif base == "sg90":
            items.append(Item("SG90 antenna servo", "electronics", SG90_G, S["sg90"][1], tgt, mesh_mass(P, T, SG90_G / 1000), True))
            g3 = 3 * SCREW_G["M2x4pan"]
            items.append(Item("SG90 bag screws x3 (2 tab, 1 holder)", "screw", g3, "UNVERIFIED: SG90 bag screw sizes not published (B5); taken as M2x4 pan head, " + S["screw_mass"][1],
                              tgt, mesh_mass(P, T, g3 / 1000), False))
        elif base == "roll_bearing":
            V = mesh_props(P)[0]; g = V * 1e6 * BEARING_STEEL
            items.append(Item("6804ZZ bearing", "mechanical", g, S["bearing"][1], tgt, mesh_mass(P, T, g / 1000), True))
        else:
            raise RuntimeError("unhandled CAD part " + fn)
    # ---- head-region print parts that the URDF does not have (same frame as print/head.stl) ----
    assert head_stl_T is not None
    for pname in ("left_eye", "right_eye", "bulb", "flash_light_module", "flash_reflector_interface", "speaker_stand", "speaker_interface"):
        r = sl[pname]; g = r["g_each"] - r["support_each"]
        Ts = [head_stl_T] + ([head_stl_T @ np.diag([1, -1, 1, 1.0])] if pname == "bulb" else [])   # second bulb is the mirror (audit/headgroup.py)
        for T in Ts:
            items.append(Item(pname, "printed", g, PRINT_SRC + "; seat from print STL in the head.stl frame (audit/headgroup.py)",
                              "head_assembly", mesh_mass(os.path.join(PRINT_DIR, pname + ".stl"), T, g / 1000), pname not in ("flash_light_module", "flash_reflector_interface")))
    def head_pt(p_mm):   # point in the print head.stl frame (mm) -> head link (m)
        return (head_stl_T @ np.r_[np.array(p_mm, float) / 1000.0, 1.0])[:3]
    def head_bounds(pname):
        _, _, _, mesh = mesh_props(os.path.join(PRINT_DIR, pname + ".stl")); return mesh.bounds * 1000
    # bought parts in the head with a CAD seat
    sb = head_bounds("speaker_interface")
    spk_c = head_pt([(sb[0, 0] + sb[1, 0]) / 2, sb[0, 1] + 14.5 / 2 + 2, (sb[0, 2] + sb[1, 2]) / 2])
    items.append(Item("speaker Same Sky CMS0361KLX", "electronics", SPK_G, S["speaker"][1] + "; seat: speaker_interface (print STL bounds)", "head_assembly",
                      box_mass(SPK_G / 1000, spk_c, (0.036, 0.0145, 0.036)), True))
    cam_c = head_pt([113.8 - 6.0, -6.25, 153.1])     # 4 camera pilots at x 113.8, y 0 / -12.5, z 142.6 / 163.6 (audit/sites_head.json)
    items.append(Item("Camera Module 3", "electronics", CAM_G, S["camera3"][1] + "; seat: 4 pilots in head.stl (audit/sites_head.json)", "head_assembly",
                      box_mass(CAM_G / 1000, cam_c, (0.0115, 0.025, 0.024)), True))
    items.append(Item("camera FPC cable 150 mm", "wire", FPC_G, S["fpc"][1], "head_assembly", point_mass(FPC_G / 1000, (cam_c + pi_T[1][:3, 3]) / 2), False))
    for pname in ("left_eye", "right_eye"):
        b = head_bounds(pname); c = head_pt(b.mean(0))
        items.append(Item("eye glass disc", "electronics", GLASS_G, S["eye_glass"][1], "head_assembly", point_mass(GLASS_G / 1000, c), True))
    for pname, mir in (("bulb", False), ("bulb", True), ("flash_light_module", False)):
        b = head_bounds(pname); c = b.mean(0); c = c * np.array([1, -1, 1]) if mir else c
        items.append(Item("1 W LED bead", "electronics", LED_G, S["led"][1], "head_assembly", point_mass(LED_G / 1000, head_pt(c)), False))
    rb = head_bounds("flash_reflector_interface")
    items.append(Item("Aurorad S5 reflector", "electronics", REFL_G, S["reflector"][1], "head_assembly", point_mass(REFL_G / 1000, head_pt(rb.mean(0))), False))
    # Pi, regulator and amp on the head floor: floor top z = head_bot_sheet top (print STL bounds)
    floor_z = head_bounds("head_bot_sheet")[1, 2]
    Tpi = pi_T[1]; pi_c_link = Tpi[:3, 3]
    pi_c_head = (np.linalg.inv(head_stl_T) @ np.r_[mesh_props(os.path.join(URDF_DIR, "raspberrypizerow.stl"))[1] @ Tpi[:3, :3].T + Tpi[:3, 3], 1])[:3] * 1000
    reg_c = head_pt([pi_c_head[0], pi_c_head[1], floor_z + 1.1 + 9.0 / 2])   # D30V30F5 17.8 x 20.3 x 9 mm on foam tape below the Pi
    items.append(Item("Pololu D30V30F5 5 V regulator", "lab_added", REG_G, S["d30v30f5"][1] + "; seat: head floor below the Pi (MOUNTING.md; no placements.json entry, x and y of the Pi centre)", "head_assembly",
                      box_mass(REG_G / 1000, reg_c, (0.0178, 0.0203, 0.009)), False))
    stb = head_bounds("speaker_stand")
    amp_c = head_pt([(stb[0, 0] + stb[1, 0]) / 2, stb[0, 1] - 2 - 17.8 / 2, floor_z + 1.5])   # 'head floor, flat, right of the speaker stand' (MOUNTING.md, Tnkr)
    items.append(Item("MAX98357A amplifier", "electronics", AMP_G, S["max98357"][1] + "; seat: head floor right of the speaker stand (MOUNTING.md)", "head_assembly",
                      box_mass(AMP_G / 1000, amp_c, (0.0194, 0.0178, 0.003)), False))
    for nm, n in (("100 ohm LED resistor", 3), ("2.2 kOhm foot pull-up", 2)):
        items.append(Item(nm + f" x{n}", "electronics", n * RES_G, S["resistor"][1], "head_assembly", point_mass(n * RES_G / 1000, pi_c_link), False))
    # ---- lab-only parts at audit/placements.json (URDF zero-pose world = trunk frame, mm) ----
    pl = {p["id"]: p for p in json.load(open(os.path.join(LAB, "audit/placements.json")))}
    def pl_box(pid, g):
        p = pl[pid]; return box_mass(g / 1000, np.array(p["center_mm"]) / 1000, np.array(p["dims_xyz_mm"]) / 1000)
    PLSRC = "; seat: audit/placements.json"
    items.append(Item("Castle CC BEC Pro", "lab_added", BEC_G, S["bec"][1] + PLSRC, "trunk_assembly", pl_box("bec_pro", BEC_G), False))
    items.append(Item("CC BEC Pro output leads", "lab_added", BEC_LEADS_G, S["bec_out_leads"][1] + PLSRC, "trunk_assembly", pl_box("bec_pro", BEC_LEADS_G), False))
    items.append(Item("Littelfuse FHAC0001ZXJ fuse holder with leads", "lab_added", FUSEHOLDER_G, S["fuse_holder"][1] + PLSRC, "trunk_assembly", pl_box("fuse_holder", FUSEHOLDER_G), False))
    items.append(Item("ATO 15 A fuse", "lab_added", FUSE_G, S["ato_fuse"][1] + PLSRC, "trunk_assembly", pl_box("fuse_holder", FUSE_G), False))
    items.append(Item("Pololu 2815 MOSFET switch", "lab_added", SW2815_G, S["sw2815"][1] + PLSRC, "trunk_assembly", pl_box("mosfet_switch", SW2815_G), False))
    items.append(Item("servo power splices SPV, SPG", "lab_added", 2 * SPLICE_G, S["splice"][1] + PLSRC, "trunk_assembly", pl_box("power_splice", 2 * SPLICE_G), False))
    items.append(Item("Tenergy 32175 BMS", "lab_added", TENERGY_G, S["tenergy_bms"][1] + PLSRC, "trunk_assembly", pl_box("bms_tenergy", TENERGY_G), True,
                      "replaces the CAD bms part"))
    # parts from the netlist without a CAD body: XT30 pair, the other solder splices, foot switches
    def inst_centroid(fn, link):
        for tgt, f, T, ln in inst:
            if f == fn and tgt == link:
                return T[:3, :3] @ mesh_props(os.path.join(URDF_DIR, f))[1] + T[:3, 3]
    xt30_c = inst_centroid("holder.stl", "trunk_assembly") + np.array([0, 0.03, 0])      # 'body_back, left of the holder' (MOUNTING.md, Tnkr)
    items.append(Item("Amass XT30U pair", "lab_added", XT30_G, S["xt30_pair"][1] + "; seat: left of the holder (MOUNTING.md, Tnkr placement), 30 mm to +y", "trunk_assembly",
                      point_mass(XT30_G / 1000, xt30_c), False))
    adapter_c = inst_centroid("board.stl", "trunk_assembly")
    for nm, c, lk, n in (("splices VSW, G (switched bus, ground)", np.array(pl["mosfet_switch"]["center_mm"]) / 1000, "trunk_assembly", 2),
                         ("splices JB+, JB- (BEC outputs)", np.array(pl["bec_pro"]["center_mm"]) / 1000, "trunk_assembly", 2),
                         ("splices YD3, YG3, JG30, JG20, JG10 (data Y and grounds)", adapter_c, "trunk_assembly", 5),
                         ("splices J5, JG (head 5 V and ground)", pi_c_link, "head_assembly", 2)):
        items.append(Item(nm, "lab_added", n * SPLICE_G, S["splice"][1], lk, point_mass(n * SPLICE_G / 1000, c), False))
    for foot in ("foot_assembly", "foot_assembly_2"):
        items.append(Item("Omron SS-01 foot switch x2", "electronics", 2 * SS_G, S["omron_ss"][1] + "; seat: 2 slots in foot_top (MOUNTING.md)", foot,
                          point_mass(2 * SS_G / 1000, inst_centroid("foot_top.stl", foot)), False))
    # foam tape under the 4 taped parts, by footprint
    tape = {"bec_pro": 0.047 * 0.033, "fuse_holder": 0.052 * 0.018, "mosfet_switch": 0.0254 * 0.0203}
    for pid, a in tape.items():
        g = a * 1.1e-3 * TAPE_DENS * 1e6
        items.append(Item(f"VHB 4950 tape under {pid}", "lab_added", g, S["vhb_density"][1], "trunk_assembly", pl_box(pid, g), False))
    g = 0.0178 * 0.0203 * 1.1e-3 * TAPE_DENS * 1e6
    items.append(Item("VHB 4950 tape under the regulator", "lab_added", g, S["vhb_density"][1], "head_assembly", point_mass(g / 1000, reg_c), False))
    # ---- duck-side dock parts (D43, D50) and the companion and freeze boards (D47, D51, D54) ----
    # seats: audit/placements.json boxes, the touch pad centres of twin/freeze/touch_pads.json; zero-pose world = trunk frame
    T_head_inv = np.linalg.inv(u.get_transform("head_assembly", "trunk_assembly"))
    def at(link, p_world_mm):
        p = np.array(p_world_mm, float) / 1000.0
        return p if link == "trunk_assembly" else (T_head_inv @ np.r_[p, 1.0])[:3]
    tp = json.load(open(os.path.join(LAB, "twin", "freeze", "touch_pads.json")))["pads"]
    for nm, pid, g, key, lk in (("chest contact pad (BOM DK1)", "dock_pad", DOCKPAD_G, "dock_pad", "trunk_assembly"),
                                ("Pololu 5382 ideal diode, charge input (BOM DK2)", "dock_dk2", IDEAL_DIODE_G, "ideal_diode", "trunk_assembly"),
                                ("Pololu 5382 ideal diode, dock supply (BOM DK6)", "dock_dk6", IDEAL_DIODE_G, "ideal_diode", "trunk_assembly"),
                                ("Pololu 5383 ideal diode, pack side (BOM DK7)", "dock_dk7", IDEAL_DIODE_G, "ideal_diode", "trunk_assembly"),
                                ("Littelfuse FHAC0001ZXJ charge fuse holder (BOM DK3)", "dock_f2", FUSEHOLDER_G, "fuse_holder", "trunk_assembly"),
                                ("ATO 5 A charge fuse (BOM DK4)", "dock_f2", FUSE_G, "ato_fuse", "trunk_assembly"),
                                ("I2S mic board, left (Adafruit 3421, D47)", "mic_l", MIC_G, "mic_3421", "head_assembly"),
                                ("I2S mic board, right (Adafruit 3421, D47)", "mic_r", MIC_G, "mic_3421", "head_assembly"),
                                ("MPR121 touch board, head (D51)", "tch_h", MPR121_G, "mpr121", "head_assembly"),
                                ("MPR121 touch board, body (D51)", "tch_b", MPR121_G, "mpr121", "trunk_assembly"),
                                ("cliff ToF board (Adafruit 5396, D54)", "tof_cliff", TOF_G, "tof", "trunk_assembly")):
        items.append(Item(nm, "lab_added", g, S[key][1] + PLSRC, lk, point_mass(g / 1000, at(lk, pl[pid]["center_mm"])), False))
    rt1 = (-129.6, 0.0, 66.0)        # the NTC in the cell seat (twin/dock/dock_routes.json RT1)
    items.append(Item("cell NTC 10 k on its lead (BOM DK5)", "lab_added", NTC_G, S["ntc"][1], "trunk_assembly", point_mass(NTC_G / 1000, at("trunk_assembly", rt1)), False))
    items.append(Item("wake branch: zener, diode, 10 k; and the 100 k across DK2 (BOM DK5)", "lab_added", 4 * RES_G, S["resistor"][1], "trunk_assembly",
                      point_mass(4 * RES_G / 1000, at("trunk_assembly", (-107.8, 24.0, 44.0))), False))
    items.append(Item("dock splices JGD, JSN (GND and SENSE branches)", "lab_added", 2 * SPLICE_G, S["splice"][1], "trunk_assembly",
                      point_mass(2 * SPLICE_G / 1000, at("trunk_assembly", (27.0, 0.0, 31.0))), False))
    foil = [(k, v) for k, v in tp.items()]
    for k, v in foil:
        g = FOIL_G * v["pad_area_mm2"] / sum(w["pad_area_mm2"] for _, w in foil)
        items.append(Item(f"copper foil touch pad {k} with its guard ring (D51)", "lab_added", g, S["copper_foil"][1], v["link"],
                          point_mass(g / 1000, at(v["link"], v["centre_world"])), False))
    # ---- wires along their routes ----
    wire_items, usb_route_frac = wires(u, inst, servo_pos, pl, head_pt, pi_c_link, reg_c, amp_c, spk_c, cam_c)
    items += wire_items
    # USB cable: route part with the wires, slack coil at placements usb_slack
    items.append(Item("USB cable slack coil (part of Adafruit 3878)", "wire", USB_G * (1 - usb_route_frac), S["usb_cable"][1] + PLSRC, "trunk_assembly",
                      pl_box("usb_slack", USB_G * (1 - usb_route_frac)), False))
    # ---- screws and inserts at their hole sites ----
    items += hardware(u, head_stl_T)
    items.append(Item("solder and heat shrink (joints outside splices)", "misc", SOLDER_HS_G, S["solder_heatshrink"][1], "trunk_assembly",
                      point_mass(SOLDER_HS_G / 1000, np.array(pl["power_splice"]["center_mm"]) / 1000), False))
    items.append(Item("cable ties", "misc", TIE_G, S["cable_ties"][1], "trunk_assembly", point_mass(TIE_G / 1000, np.array(pl["usb_slack"]["center_mm"]) / 1000), False))
    # ---- sums ----
    links = {b: Mass() for b in BODIES}
    for it in items:
        if it.mass_g <= 0: continue
        links[it.link] = links[it.link] + it.M
    return dict(items=items, links=links, notes=notes, urdf=u)

def wires(u, inst, servo_pos, pl, head_pt, pi_c, reg_c, amp_c, spk_c, cam_c):
    """every wire in wiring/netlist.yaml as point masses along a route polyline: from-part, the joints crossed, to-part"""
    import yaml
    nl = yaml.safe_load(open(os.path.join(LAB, "wiring/netlist.yaml")))
    cab = {c["id"]: c for c in nl["cables"]}
    # joint positions in the zero-pose trunk frame, link tree
    J = {}
    for j in u.robot.joints:
        if j.type == "revolute":
            J[j.name] = dict(p=u.get_transform(j.child, "trunk_assembly")[:3, 3], parent=LINK_ALIAS.get(j.parent, j.parent), child=LINK_ALIAS.get(j.child, j.child))
    par = {}
    for j in u.robot.joints:
        if j.type == "revolute" and "antenna" not in j.name: par[j.child] = (j.parent, j.name)
    def chain(l):
        out = []
        while l in par: out.append(l); l = par[l][0]
        return out + [l]
    def to_trunk(link, p): return (u.get_transform(link, "trunk_assembly") @ np.r_[p, 1])[:3]
    def to_link(link, p): return (np.linalg.inv(u.get_transform(link, "trunk_assembly")) @ np.r_[p, 1])[:3]
    def inst_c(fn, link):
        for tgt, f, T, ln in inst:
            if f == fn and tgt == link:
                return to_trunk(link, T[:3, :3] @ mesh_props(os.path.join(URDF_DIR, f))[1] + T[:3, 3])
        raise KeyError(fn)
    # servo case centres per joint: the servo case nearest to the joint axis (15.5 mm for every joint; the head yaw and
    # head roll servos sit in the child link of their joint, all others in the parent link)
    servo_c = {}
    for jn in JOINT_OF_ID.values():
        best = None
        for sl_link, Ts in servo_pos.items():
            for T in Ts:
                c = to_trunk(sl_link, T[:3, :3] @ mesh_props(os.path.join(URDF_DIR, SERVO_CASE[2]))[1] + T[:3, 3])
                dd = np.linalg.norm(c - J[jn]["p"])
                if best is None or dd < best[0]: best = (dd, c, sl_link)
        servo_c[jn] = (best[1], best[2])
    P = lambda pid: np.array(pl[pid]["center_mm"]) / 1000
    ADAPTER = inst_c("board.stl", "trunk_assembly"); NECK = J["neck_pitch"]["p"]
    holder = inst_c("holder.stl", "trunk_assembly"); charger = inst_c("usb_c_charger.stl", "trunk_assembly"); ctl = inst_c("power_switch.stl", "trunk_assembly")
    bno = inst_c("bno055.stl", "trunk_assembly")
    pos = {"PACK": (holder, "trunk_assembly"), "BMS": (P("bms_tenergy"), "trunk_assembly"), "CHG": (charger, "trunk_assembly"),
           "XT30": (holder + np.array([0, 0.03, 0]), "trunk_assembly"),          # 'body_back, left of the holder' (MOUNTING.md, Tnkr), about 30 mm to +y
           "F1": (P("fuse_holder"), "trunk_assembly"), "SW1": (P("mosfet_switch"), "trunk_assembly"), "CTL": (ctl, "trunk_assembly"),
           # JFI, JFO: the inline splices that extend the two fuse holder leads with 16 AWG (netlist P7, 2026-11-02), placed at the
           # fuse holder seat (audit/placements.json fuse_holder), as VSW and G sit at the mosfet_switch seat
           "JFI": (P("fuse_holder"), "trunk_assembly"), "JFO": (P("fuse_holder"), "trunk_assembly"),
           "VSW": (P("mosfet_switch"), "trunk_assembly"), "G": (P("mosfet_switch"), "trunk_assembly"),
           "U1": (P("bec_pro"), "trunk_assembly"), "JBP": (P("bec_pro"), "trunk_assembly"), "JBN": (P("bec_pro"), "trunk_assembly"),
           "U2": (ADAPTER, "trunk_assembly"), "SPV": (P("power_splice"), "trunk_assembly"), "SPG": (P("power_splice"), "trunk_assembly"),
           # D65 limb breakers have no 3D route yet. Seat them on the servo splice until a route exists.
           "EFL": (P("power_splice"), "trunk_assembly"), "EFR": (P("power_splice"), "trunk_assembly"),
           "EFN": (P("power_splice"), "trunk_assembly"),
           "YD3": (ADAPTER, "trunk_assembly"), "YG3": (ADAPTER, "trunk_assembly"), "JG30": (servo_c["neck_pitch"][0], "trunk_assembly"),
           "JG20": (servo_c["left_hip_yaw"][0], "trunk_assembly"), "JG10": (servo_c["right_hip_yaw"][0], "trunk_assembly"),
           "BNO": (bno, "trunk_assembly")}
    hd = "head_assembly"
    # JPI is the charger header on the Pi pins (netlist cable CE). It has no cables3d end, and its cut length is null.
    for k, c in (("U3", reg_c), ("J5", pi_c), ("JG", pi_c), ("PI", pi_c), ("JPI", pi_c), ("RL", pi_c), ("RR", pi_c), ("RP", pi_c), ("RFL", pi_c), ("RFR", pi_c),
                 ("AMP", amp_c), ("SPK", spk_c), ("CAM", cam_c)):
        pos[k] = (to_trunk(hd, c), hd)
    for k, pname, mir in (("LEDL", "bulb", False), ("LEDR", "bulb", True), ("LEDP", "flash_light_module", False)):
        _, _, _, mesh = mesh_props(os.path.join(PRINT_DIR, pname + ".stl")); c = mesh.bounds.mean(0) * 1000
        c = c * np.array([1, -1, 1]) if mir else c
        pos[k] = (to_trunk(hd, head_pt(c)), hd)
    for k, fn in (("SGL", 0), ("SGR", 1)):
        sg = [T for tgt, f, T, ln in inst if f == "sg90.stl"]
        T = sg[fn]; pos[k] = (to_trunk(hd, T[:3, :3] @ mesh_props(os.path.join(URDF_DIR, "sg90.stl"))[1] + T[:3, 3]), hd)
    for k, foot in (("FSL1", "foot_assembly"), ("FSL2", "foot_assembly"), ("FSR1", "foot_assembly_2"), ("FSR2", "foot_assembly_2")):
        pos[k] = (inst_c("foot_top.stl", foot), foot)
    for i, jn in JOINT_OF_ID.items():
        pos[f"SV{i}"] = (servo_c[jn][0], servo_c[jn][1])
    # components added after this table (dock D43/D50, companion D47, freeze D51/D54): the centre of their cable ends in
    # cables3d/cables3d.json (zero-pose world = trunk frame), so every wire of the netlist has both ends placed
    ends = collections.defaultdict(list)
    for e in json.load(open(os.path.join(LAB, "cables3d", "cables3d.json")))["cable_ends"]:
        ends[e["id"].split(".")[0]].append(e)
    for cid, es in ends.items():
        if cid not in pos:
            lk = es[0]["link"]; c = np.mean([x["p_world0"] for x in es], axis=0) / 1000.0
            pos[cid] = (c, lk)
    out = []; usb_frac = None
    per_link = collections.defaultdict(lambda: [0.0, np.zeros(3)])   # aggregate per (link, gauge) for a short table
    for w in nl["wires"]:
        c = cab[w["cable"]]
        if c["status"] != "active": continue
        g = w["gauge"]; L = (w.get("cut_mm") or 0) / 1000.0
        if g in ("resistor lead", "BEC lead", "SG90 lead", "board", "bead lead"): continue  # on a part already weighed: resistor, BEC lead, SG90, charger board, NTC bead
        a = w["from"].split(".")[0]; b = w["to"].split(".")[0]
        pa, la = pos[a]; pb, lb = pos[b]
        ca, cb = chain(la), chain(lb); common = next(l for l in ca if l in cb)
        js = [par[l][1] for l in ca[:ca.index(common)]] + [par[l][1] for l in reversed(cb[:cb.index(common)])]
        pts = [pa] + [J[j]["p"] for j in js] + [pb]
        segl = [ca[k] for k in range(ca.index(common))] + [common] + list(reversed(cb[:cb.index(common)]))
        # segment k from pts[k] to pts[k+1] lies in link segl[k]
        lens = np.array([np.linalg.norm(pts[k + 1] - pts[k]) for k in range(len(pts) - 1)])
        if g == "USB 2.0 cable":
            route = lens.sum(); usb_frac = min(1.0, (route + 0.0452 + 0.04) / 0.9)   # CABLE_MAP rule ends; the rest is slack in the coil
            mass = USB_G * usb_frac; srcs = S["usb_cable"][1] + "; route part by the CABLE_MAP length rule, rest in the slack coil"
        elif g == "FPC ribbon": continue                                        # camera cable item above
        elif g == "kit cable":
            mass = KIT_GPM * L; srcs = S["kit_cable_gpm"][1]
        elif g == "SG90 lead + 26 AWG":
            mass = WIRE_GPM[26] * 0.020; srcs = "[L] 20 mm 26 AWG extension (netlist note) at " + f"{WIRE_GPM[26]:.1f} g/m"
        elif g.endswith("AWG"):
            n = int(g.split()[0]); mass = WIRE_GPM[n] * L; srcs = f"[L] wiring/netlist.yaml cut_mm x {WIRE_GPM[n]:.1f} g/m ({n} AWG, computed above)"
        else:
            raise RuntimeError("gauge " + g)
        if lens.sum() < 1e-6: lens = np.array([1.0]); pts = [pa, pa]; segl = [la]
        for k in range(len(lens)):
            mk = mass * lens[k] / lens.sum(); lk = segl[k]; mid = (pts[k] + pts[k + 1]) / 2
            per_link[(lk, g)][0] += mk; per_link[(lk, g)][1] += mk * mid
    # also the made-lead housings and terminals at servo ends (SP1/SD1 at ID 20, SP3/SD1 at ID 30, SP2/SD2 at ID 10) and Pi 2.54 mm housings
    hw = [("Mini-SPOX housings and terminals at ID 20, 10, 30", "trunk_assembly", 3 * HOUSING_G + 9 * TERMINAL_G, (pos["SV20"][0] + pos["SV10"][0] + pos["SV30"][0]) / 3),
          ("2.54 mm housings and terminals at the Pi header", hd, 8 * HOUSING_G + 24 * TERMINAL_G, pos["PI"][0])]
    for (lk, g), (m, mp) in sorted(per_link.items()):
        if m <= 0: continue
        c = to_link(lk, mp / m)
        tag = S["usb_cable"][1] if g == "USB 2.0 cable" else (S["kit_cable_gpm"][1] if g == "kit cable" else "[L] wiring/netlist.yaml cut_mm, routed along the joints crossed; " + S["wire_gpm"][1])
        out.append(Item(f"wires {g} in {SHORT.get(lk, lk)}", "wire", m * 1.0, tag, lk, point_mass(m / 1000, c), False))
    for nm, lk, m, p in hw:
        out.append(Item(nm, "wire", m, S["housing"][1] + "; " + S["terminal"][1], lk, point_mass(m / 1000, to_link(lk, p)), False))
    return out, usb_frac

def hardware(u, head_stl_T):
    """screws and inserts at the measured hole sites (same selection as audit/screws2.py, without its ray cast)"""
    A = json.load(open(os.path.join(LAB, "audit/assembly.json")))
    inst_link = [LINK_ALIAS.get(i["link"], i["link"]) for i in A["inst"]]
    sites = json.load(open(os.path.join(LAB, "audit/sites.json")))
    sites_head = json.load(open(os.path.join(LAB, "audit/sites_head.json")))
    def anchor_type(m, d, L):
        if m == "drive_palonier" and abs(d - 2.5) < 0.2: return "horn(drive)"
        if m == "passive_palonier" and abs(d - 2.5) < 0.2: return "horn(passive)"
        if abs(d - 4.0) < 0.15 and L >= 5.0: return "M3 insert"
        if m.startswith("wj-") and d < 2.1: return "servo pilot"
        if abs(d - 2.0) < 0.1 and L >= 4.5 and not m.startswith("wj-"): return "plastic pilot 2.0"
        return None
    def rows_of(S_, frame):
        rows = []; seen = set()
        for si, s in enumerate(S_):
            o = np.array(s["o"], float); ax = np.array(s["ax"], float)
            segs = [dict(t0=a, t1=b, m=m, k=k, d=d, i=i) for a, b, m, k, d, i in s["segs"]]
            for sg in segs:
                m = sg["m"]
                if m.startswith("wj-") or "palonier" in m: continue
                if not (2.4 <= sg["d"] <= 3.7): continue
                if anchor_type(m, sg["d"], sg["t1"] - sg["t0"]): continue
                heads = [h for h in segs if h["i"] == sg["i"] and 3.9 <= h["d"] <= 7.1 and (abs(h["t1"] - sg["t0"]) < 0.45 or abs(h["t0"] - sg["t1"]) < 0.45)
                         and not (abs(h["d"] - 4.0) < 0.15 and h["t1"] - h["t0"] >= 5.0)]
                if heads:
                    h = heads[0]; direction = 1 if abs(h["t1"] - sg["t0"]) < 0.45 else -1; hf = h["t1"] if direction == 1 else h["t0"]
                else:
                    hf = None
                    for direction, face in ((1, sg["t0"]), (-1, sg["t1"])):
                        c = [x for x in segs if x["i"] != sg["i"] and anchor_type(x["m"], x["d"], x["t1"] - x["t0"]) and (x["t0"] - face) * direction > 0]
                        if c: hf = face; break
                    if hf is None: continue
                cand = [x for x in segs if x["i"] != sg["i"] and anchor_type(x["m"], x["d"], x["t1"] - x["t0"]) and max((x["t0"] - hf) * direction, (x["t1"] - hf) * direction) > 0.3]
                if not cand:
                    continue
                cand.sort(key=lambda x: min((x["t0"] - hf) * direction, (x["t1"] - hf) * direction)); a = cand[0]
                at = anchor_type(a["m"], a["d"], a["t1"] - a["t0"])
                p_screw = o + ax * (hf + direction * 3.0)                  # about the middle of a short screw
                p_anchor = o + ax * ((a["t0"] + a["t1"]) / 2)
                key = (si, a["i"], a["t0"])          # one physical screw per anchor: a screw through two clamped parts gives two clearance rows
                if key in seen: continue
                seen.add(key)
                rows.append(dict(part=m, inst=sg["i"], anchor=at, into=a["m"], into_inst=a["i"], p=p_screw, pa=p_anchor, frame=frame))
        return rows
    rows = rows_of(sites, "trunk") + rows_of(sites_head, "head")
    def place(r, p):
        if r["frame"] == "trunk":
            lk = inst_link[r["inst"]]; Tl = u.get_transform(lk, "trunk_assembly")
            return lk, (np.linalg.inv(Tl) @ np.r_[p / 1000.0, 1])[:3]
        return "head_assembly", (head_stl_T @ np.r_[p / 1000.0, 1])[:3]
    # only head rows from sites_head (the trunk sites file holds no head parts: the URDF head is the old one)
    rows = [r for r in rows if r["frame"] == "head" or inst_link[r["inst"]] != "head_assembly"]
    out = []; cnt = collections.Counter()
    M3_INSERT_MIX = (44 * SCREW_G["M3x8"] + 12 * SCREW_G["M3x10"] + 2 * SCREW_G["M3x12"]) / 58     # BOM 17a/17b/17c mix
    HORN_MIX = (88 * SCREW_G["M3x6"] + 12 * SCREW_G["M3x5"]) / 100                                  # BOM 17d/17e mix
    agg = collections.defaultdict(lambda: [0.0, np.zeros(3), 0])
    for r in rows:
        at = r["anchor"]
        if at == "M3 insert":
            g = M3_INSERT_MIX; kind = "M3 insert screws (M3x8/10/12 mix)"
        elif at.startswith("horn"):
            g = HORN_MIX; kind = "M3 horn screws (M3x6/M3x5 mix)"
        elif at == "servo pilot":
            g = SCREW_G["M2x6pan"]; kind = "M2 servo-case screws (servo bag)"
        elif at == "plastic pilot 2.0":
            if r["part"] == "battery_pack_lid": g = SCREW_G["M2.5x10"]; kind = "M2.5x10 lid screws"
            elif r["part"] in ("left_eye", "right_eye", "bulb"): g = SCREW_G["M2.5x8"]; kind = "M2.5x8 eye screws"
            else: g = SCREW_G["M2.5x6"]; kind = "M2.5x6 electronics screws"
        else:
            continue
        lk, c = place(r, r["p"]); cnt[kind] += 1
        a = agg[(lk, kind)]; a[0] += g; a[1] += g * c; a[2] += 1
        if at == "M3 insert":
            lk2, c2 = place(dict(r, inst=r["into_inst"]), r["pa"]) if r["frame"] == "trunk" else place(r, r["pa"])
            a = agg[(lk2, "M3 heat-set inserts")]; a[0] += INSERT_G; a[1] += INSERT_G * c2; a[2] += 1; cnt["M3 heat-set inserts"] += 1
    # horn centre screws: one per servo at its drive horn
    for i in [k for k, x in enumerate(A["inst"]) if x["mesh"] == "drive_palonier.stl"]:
        lk = inst_link[i]; T = np.array(A["inst"][i]["T"]); c_world = T[:3, 3] / 1000.0
        c = (np.linalg.inv(u.get_transform(lk, "trunk_assembly")) @ np.r_[c_world, 1])[:3]
        g = SCREW_G["M3x6"]; a = agg[(lk, "M3x6 horn centre screws (servo bag)")]; a[0] += g; a[1] += g * c; a[2] += 1; cnt["M3x6 horn centre screws (servo bag)"] += 1
    # screws the hole search does not anchor (audit/screws2.json 'NONE' rows and pilots under 4.5 mm), placed at their part
    def part_c(mesh_name, link):
        for k, x in enumerate(A["inst"]):
            if x["mesh"] == mesh_name and inst_link[k] == link:
                T = np.array(x["T"]); T[:3, 3] /= 1000.0; V, cc, _, _ = mesh_props(os.path.join(URDF_DIR, mesh_name))
                return (np.linalg.inv(u.get_transform(link, "trunk_assembly")) @ np.r_[T[:3, :3] @ cc + T[:3, 3], 1])[:3]
    extra = [("M2x6 roll_to_pitch screws (servo bag, HARDWARE_AUDIT.md B4)", "left_roll_to_pitch_assembly", part_c("left_roll_to_pitch.stl", "left_roll_to_pitch_assembly"), 2, SCREW_G["M2x6pan"]),
             ("M2x6 roll_to_pitch screws (servo bag, HARDWARE_AUDIT.md B4)", "right_roll_to_pitch_assembly", part_c("right_roll_to_pitch.stl", "right_roll_to_pitch_assembly"), 2, SCREW_G["M2x6pan"])]
    for pname, n in (("left_eye", 4), ("right_eye", 4)):
        _, _, _, mesh = mesh_props(os.path.join(PRINT_DIR, pname + ".stl"))
        extra.append(("M2.5x8 eye screws (MOUNTING.md)", "head_assembly", (head_stl_T @ np.r_[mesh.bounds.mean(0), 1])[:3], n, SCREW_G["M2.5x8"]))
    extra.append(("M2x4 camera screws (MOUNTING.md)", "head_assembly", (head_stl_T @ np.r_[np.array([113.8, -6.25, 153.1]) / 1000, 1])[:3], 4, SCREW_G["M2x4pan"]))
    for nm, lk, c, n, g in extra:
        a = agg[(lk, nm)]; a[0] += n * g; a[1] += n * g * c; a[2] += n; cnt[nm] += n
    tags = {"M3 insert screws (M3x8/10/12 mix)": S["screw_mass"][1] + "; sites audit/sites.json, audit/sites_head.json",
            "M3 horn screws (M3x6/M3x5 mix)": S["screw_mass"][1] + "; sites audit/sites.json, audit/sites_head.json",
            "M2 servo-case screws (servo bag)": S["servo_bag"][1], "M3x6 horn centre screws (servo bag)": S["servo_bag"][1],
            "M2.5x10 lid screws": S["screw_mass"][1], "M2.5x8 eye screws": S["screw_mass"][1], "M2.5x6 electronics screws": S["screw_mass"][1],
            "M3 heat-set inserts": S["insert"][1] + "; sites audit/sites.json, audit/sites_head.json",
            "M2x6 roll_to_pitch screws (servo bag, HARDWARE_AUDIT.md B4)": S["servo_bag"][1], "M2.5x8 eye screws (MOUNTING.md)": S["screw_mass"][1],
            "M2x4 camera screws (MOUNTING.md)": S["screw_mass"][1]}
    for (lk, kind), (g, gc, n) in sorted(agg.items()):
        out.append(Item(f"{kind} x{n} in {SHORT.get(lk, lk)}", "insert" if kind == "M3 heat-set inserts" else "screw", g, tags[kind], lk, point_mass(g / 1000, gc / g), False))
    hardware.counts = dict(cnt)
    return out

# ---------------------------------------------------------------------------------------------------------------
# Fit of the trained model's per-part masses (explains the difference part by part)
# ---------------------------------------------------------------------------------------------------------------
def fit_model(u, model):
    from scipy.optimize import nnls
    res = {}
    for ln in BODIES:
        if ln in ("trunk_assembly", "head_assembly"): continue        # 15 to 20 parts for 10 equations: not well posed
        link = u.link_map[ln]; Mm = model[ln]
        groups = collections.OrderedDict()
        for v in link.visuals:
            fn = os.path.basename(v.geometry.mesh.filename); T = v.origin if v.origin is not None else np.eye(4)
            g = "servo (case + horns)" if fn in SERVO_CASE + HORNS else fn[:-4]
            V, c, Jc, _ = mesh_props(os.path.join(URDF_DIR, fn)); R = T[:3, :3]; cw = R @ c + T[:3, 3]
            Iw = R @ Jc @ R.T + V * (np.dot(cw, cw) * np.eye(3) - np.outer(cw, cw))
            a = np.r_[V, V * cw, Iw[0, 0], Iw[1, 1], Iw[2, 2], Iw[0, 1], Iw[0, 2], Iw[1, 2]]
            groups[g] = groups.get(g, 0) + a
        names = list(groups); A_ = np.array([groups[n] for n in names]).T
        IO = Mm.I + Mm.m * (np.dot(Mm.c, Mm.c) * np.eye(3) - np.outer(Mm.c, Mm.c))
        b = np.r_[Mm.m, Mm.m * Mm.c, IO[0, 0], IO[1, 1], IO[2, 2], IO[0, 1], IO[0, 2], IO[1, 2]]
        L = 0.05; w = np.r_[1, [1 / L] * 3, [1 / L ** 2] * 6]
        rho, rn = nnls(A_ * w[:, None], b * w)
        fit = A_ @ rho
        res[ln] = dict(parts={n: float(rho[i] * A_[0, i] * 1000) for i, n in enumerate(names)},
                       com_err_mm=float(np.linalg.norm(fit[1:4] / fit[0] - Mm.c) * 1000), mass_err_g=float((fit[0] - Mm.m) * 1000),
                       inertia_rel_err=float(np.abs(fit[4:7] - b[4:7]).max() / np.abs(b[4:7]).max()))
    return res

# ---------------------------------------------------------------------------------------------------------------
# Whole-robot centre of mass at a pose
# ---------------------------------------------------------------------------------------------------------------
def robot_com(links, qpos_joints=None):
    """links: {body: Mass}. Puts them into the MJCF (zero or keyframe 'home' joint angles), returns com in the trunk frame (m), total kg"""
    import mujoco
    xd, a = mjcf_assets()
    m = mujoco.MjModel.from_xml_string(open(os.path.join(xd, "scene_flat_terrain.xml")).read(), assets=a)
    d = mujoco.MjData(m)
    d.qpos[:] = m.keyframe("home").qpos if qpos_joints == "home" else 0
    d.qpos[0:3] = 0; d.qpos[3:7] = [1, 0, 0, 0]
    mujoco.mj_kinematics(m, d)
    tb = m.body("trunk_assembly").id; Rt = d.xmat[tb].reshape(3, 3); pt = d.xpos[tb]
    M = 0.0; mc = np.zeros(3)
    for bname, x in links.items():
        i = m.body(bname).id; R = d.xmat[i].reshape(3, 3); p = d.xpos[i]
        cw = R @ x.c + p; M += x.m; mc += x.m * cw
    c = mc / M
    feet = [d.site_xpos[m.site(s).id] for s in ("left_foot", "right_foot")]
    return Rt.T @ (c - pt), M, [Rt.T @ (f - pt) for f in feet]

# ---------------------------------------------------------------------------------------------------------------
def main():
    os.makedirs(OUT, exist_ok=True)
    B = build_budget()
    u = B["urdf"]; ours = B["links"]; model = model_inertials(); ui = urdf_inertials(u)
    dp, dr = check_frames(u)
    fit = fit_model(u, model)
    lines = []; P = lines.append
    tot_ours = sum(x.m for x in ours.values()); tot_model = sum(x.m for x in model.values())
    tot_urdf = sum(x.m for k, x in ui.items() if k in BODIES and k != "head_assembly") + ui["head_urdf_with_antenna_holders"].m
    P(f"Frames: MJCF body frames equal the URDF link frames at the zero pose to {dp:.4f} mm and {dr:.1e} in rotation.\n")
    # per category
    cats = collections.OrderedDict()
    for it in B["items"]: cats.setdefault(it.cat, [0.0, 0.0]); cats[it.cat][0] += it.mass_g; cats[it.cat][1] += 0 if it.in_model else it.mass_g
    unv = sum(it.mass_g for it in B["items"] if it.source.startswith("UNVERIFIED"))
    P("| Category | Our build g | of which not in the trained CAD g |"); P("|---|---|---|")
    for k, (g, gn) in cats.items(): P(f"| {k} | {g:.1f} | {gn:.1f} |")
    P(f"| total | {tot_ours*1000:.1f} | {sum(v[1] for v in cats.values()):.1f} |")
    P(f"\nUNVERIFIED items: {unv:.1f} g in all.\n")
    # per link
    P("| Link (MJCF body) | Trained MJCF g | URDF g | Our build g | Delta g | Delta % | Model CoM mm (link frame) | Our CoM mm | CoM shift mm |")
    P("|---|---|---|---|---|---|---|---|---|")
    rows = []
    for b in BODIES:
        mo = model[b]; ou = ours[b]; ur = ui["head_urdf_with_antenna_holders"] if b == "head_assembly" else ui[b]
        sh = (ou.c - mo.c) * 1000
        P(f"| {SHORT[b]} | {mo.m*1000:.1f} | {ur.m*1000:.1f} | {ou.m*1000:.1f} | {(ou.m-mo.m)*1000:+.1f} | {(ou.m/mo.m-1)*100:+.0f} | "
          f"{np.round(mo.c*1000,1).tolist()} | {np.round(ou.c*1000,1).tolist()} | {np.round(sh,1).tolist()} ({np.linalg.norm(sh):.1f}) |")
        rows.append(dict(body=b, model_g=mo.m * 1000, urdf_g=ur.m * 1000, ours_g=ou.m * 1000, model_com_mm=(mo.c * 1000).tolist(), ours_com_mm=(ou.c * 1000).tolist(),
                         model_I=mo.I.tolist(), ours_I=ou.I.tolist()))
    P(f"| total | {tot_model*1000:.1f} | {tot_urdf*1000:.1f} | {tot_ours*1000:.1f} | {(tot_ours-tot_model)*1000:+.1f} | {(tot_ours/tot_model-1)*100:+.0f} | | | |")
    # decomposition per link: parts the trained CAD also has, parts it lacks
    P("\n| Link | Trained g | Ours, parts the trained CAD also has g | Ours, parts the CAD lacks g | of which screws and inserts g | wires g | lab-only parts g |")
    P("|---|---|---|---|---|---|---|")
    dec = {}
    for b in BODIES + ["total"]:
        its = [i for i in B["items"] if b == "total" or i.link == b]
        a = sum(i.mass_g for i in its if i.in_model); n = sum(i.mass_g for i in its if not i.in_model)
        sc = sum(i.mass_g for i in its if not i.in_model and i.cat in ("screw", "insert")); wi = sum(i.mass_g for i in its if not i.in_model and i.cat == "wire")
        la = sum(i.mass_g for i in its if not i.in_model and i.cat == "lab_added")
        mo = (tot_model if b == "total" else model[b].m) * 1000
        dec[b] = dict(model_g=mo, in_cad_g=a, not_in_cad_g=n, screws_inserts_g=sc, wires_g=wi, lab_g=la)
        P(f"| {SHORT.get(b, b)} | {mo:.1f} | {a:.1f} ({a - mo:+.1f}) | {n:.1f} | {sc:.1f} | {wi:.1f} | {la:.1f} |")
    # whole robot com
    P("")
    for pose in ("zero", "home"):
        cm, Mm, feet = robot_com(model, pose if pose == "home" else None); co, Mo, _ = robot_com(ours, pose if pose == "home" else None)
        P(f"Whole robot CoM at the {pose} pose, trunk frame: trained {np.round(cm*1000,1).tolist()} mm ({Mm:.3f} kg), ours {np.round(co*1000,1).tolist()} mm ({Mo:.3f} kg), shift {np.round((co-cm)*1000,1).tolist()} mm; feet sites {np.round(np.array(feet)*1000,1).tolist()} mm")
    # inertia of trunk and head
    P("")
    for b in ("trunk_assembly", "head_assembly"):
        ev_m = np.linalg.eigvalsh(model[b].I); ev_o = np.linalg.eigvalsh(ours[b].I)
        P(f"{SHORT[b]} principal inertia about its CoM (kg m2 x 1e-4): trained {np.round(ev_m*1e4,2).tolist()}, ours {np.round(ev_o*1e4,2).tolist()}")
    # fit table
    P("\nTrained model per-part masses from the fit (NNLS on mass, first moment and inertia of each link; trunk and head not well posed):\n")
    P("| Link | Part | Trained model g (fit) | Our build g | Fit error: mass g, CoM mm, inertia |"); P("|---|---|---|---|---|")
    ours_by = collections.defaultdict(float)
    for it in B["items"]:
        if it.cat in ("printed",): ours_by[(it.link, it.name)] += it.mass_g
    for ln, r in fit.items():
        if ln.endswith("_2") and ln.startswith("hip"): continue
        if ln in ("right_roll_to_pitch_assembly", "knee_and_ankle_assembly_3", "knee_and_ankle_assembly_4", "foot_assembly_2"): continue
        first = True
        for n, g in r["parts"].items():
            our = STS3215_G if n.startswith("servo") else ours_by.get((ln, PRINT_NAME.get(n, n)), float("nan"))
            P(f"| {SHORT[ln] if first else ''} | {n} | {g:.1f} | {our:.1f} | {(f'{r['mass_err_g']:+.2f}, {r['com_err_mm']:.2f}, {r['inertia_rel_err']*100:.1f} %') if first else ''} |")
            first = False
    # items table (long): identical items merged, source given as a key into the source list below
    keys = sorted(S, key=lambda k: -len(S[k][1]))
    def skey(text):
        for k in keys:
            if S[k][1] in text: return k, text.replace(S[k][1], "").strip("; ")
        if text.startswith("UNVERIFIED"): return "UNVERIFIED", text[len("UNVERIFIED: "):]
        return None, text
    merged = collections.OrderedDict()
    for it in sorted(B["items"], key=lambda x: (BODIES.index(x.link), x.cat, x.name)):
        k = (it.name, it.cat, it.link, round(it.mass_g, 2), it.in_model, it.source)
        merged[k] = merged.get(k, 0) + 1
    P("\nEvery item (legs: both sides listed; 'in CAD' = the trained model has this part):\n")
    P("| Item | Category | Link | Qty | g each | g total | In CAD | Source key | Note |"); P("|---|---|---|---|---|---|---|---|---|")
    for (name, cat, link, g, inm, srctext), n in merged.items():
        k, rest = skey(srctext)
        P(f"| {name} | {cat} | {SHORT[link]} | {n} | {g:.2f} | {n * g:.2f} | {'yes' if inm else 'no'} | {k or '-'} | {rest} |")
    P("\nSource keys:\n")
    for k in sorted(S):
        P(f"- {k}: {S[k][1]}")
    P("\nHardware counts placed at hole sites: " + ", ".join(f"{k} {v}" for k, v in sorted(hardware.counts.items())))
    open(os.path.join(OUT, "mass_budget_tables.md"), "w").write("\n".join(lines))
    plot(B, model, dec)
    json.dump(dict(links=rows, items=[dict(name=i.name, cat=i.cat, link=i.link, g=i.mass_g, in_model=i.in_model, source=i.source, com_m=i.M.c.tolist()) for i in B["items"]],
                   fit=fit, sources={k: v[1] for k, v in S.items()}, hardware_counts=hardware.counts, total_ours_kg=tot_ours, total_model_kg=tot_model,
                   total_urdf_kg=tot_urdf), open(os.path.join(OUT, "mass_budget.json"), "w"), indent=1)
    print("\n".join(lines[:60]))
    print("wrote", OUT)

def plot(B, model, dec):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    order = ["trunk_assembly", "head_assembly", "neck_pitch_assembly", "head_pitch_to_yaw", "neck_yaw_assembly", "hip_roll_assembly",
             "left_roll_to_pitch_assembly", "knee_and_ankle_assembly", "knee_and_ankle_assembly_2", "foot_assembly"]
    cats = ["servo", "printed", "battery", "electronics", "mechanical", "lab_added", "screw", "insert", "wire", "misc"]
    cols = ["#4a6fa5", "#bfc9d9", "#7d3c98", "#1e8449", "#7f8c8d", "#c0392b", "#b9770e", "#e5c07b", "#2e86c1", "#555555"]
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.0), gridspec_kw=dict(width_ratios=[2.3, 1]))
    x = np.arange(len(order)); w = 0.38
    axs[0].bar(x - w / 2, [model[b].m * 1000 for b in order], w, color="#cccccc", edgecolor="#555555", label="trained model")
    bottom = np.zeros(len(order))
    for c, col in zip(cats, cols):
        v = np.array([sum(i.mass_g for i in B["items"] if i.link == b and i.cat == c) for b in order])
        axs[0].bar(x + w / 2, v, w, bottom=bottom, color=col, label=c); bottom += v
    axs[0].set_xticks(x); axs[0].set_xticklabels([SHORT[b].replace(" (knee servo)", "").replace(" (ankle servo)", "").replace("L ", "") for b in order], rotation=35, fontsize=7, ha="right")
    axs[0].set_ylabel("mass per link (g); legs: one side"); axs[0].legend(fontsize=6, ncol=2); axs[0].grid(alpha=0.3, axis="y")
    axs[0].set_title(f"Trained model {sum(x.m for x in model.values())*1000:.0f} g, our build {sum(i.mass_g for i in B['items']):.0f} g", fontsize=9)
    cm, _, feet = robot_com(model, "home"); co, _, _ = robot_com(B["links"], "home")
    for c, mk, lab in ((cm, "o", "trained"), (co, "s", "ours")):
        axs[1].plot(c[0] * 1000, c[2] * 1000, mk, ms=7, label=f"robot CoM, {lab}")
    for b, mk in (("trunk_assembly", "^"),):
        axs[1].plot(model[b].c[0] * 1000, model[b].c[2] * 1000, mk, color="#4a6fa5", ms=6, label="trunk CoM, trained")
        axs[1].plot(B["links"][b].c[0] * 1000, B["links"][b].c[2] * 1000, mk, color="#c0392b", ms=6, label="trunk CoM, ours")
    axs[1].set_xlabel("x in the trunk frame (mm, + forward)"); axs[1].set_ylabel("z in the trunk frame (mm)")
    axs[1].set_title("Centre of mass, home pose, side view", fontsize=9); axs[1].grid(alpha=0.3); axs[1].legend(fontsize=6)
    axs[1].set_aspect("equal", adjustable="datalim")
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "mass_budget.png"), dpi=80); plt.close(fig)

if __name__ == "__main__":
    main()
