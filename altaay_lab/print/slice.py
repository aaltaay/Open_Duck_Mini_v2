#!/usr/bin/env python3
"""Slice the Open Duck Mini v2 print package with the PrusaSlicer CLI (estimates only).

Nothing here starts a print. All outputs (oriented STLs, G-code, 3MF, JSON) go to --out, which must
be outside the repo (lab rule: no CAD exports or G-code in git).

  python3 slice.py parts   --out DIR [--set light|heavy] [--only a.stl,b.stl] [--jobs 1]
  python3 slice.py coupons --out DIR --coupons COUPON_DIR      (COUPON_DIR from make_coupons.py)
  python3 slice.py plates  --out DIR --bed 220|256 [--set ..]  (needs a finished `parts` run of the same set in DIR)
  python3 slice.py optional --out DIR                          (optional expression parts, not in totals)
  python3 slice.py summary --out DIR [--before DIR2] [--md FILE]
                           (tables from the runs above; DIR2 holds a `parts --set heavy` run for the "before" columns)

Profiles (DECISIONS.md D22, print/MASS_STUDY.md variant c). Config stack per part in the light set, the default:
config/printer_generic.ini [+ bed_256.ini] + config/pla_print.ini or tpu_print.ini (2 walls) + filament file + the
parts.csv "overrides" in the order given (ovr_insert, ovr_neck, ovr_wall3, ovr_fit), plus solid rings: PrusaSlicer
modifier volumes with config/mod_ring.ini (100 % infill) round the holes of the kinds in parts.csv "rings", found in
the print-oriented STL (find_holes). A part with rings is sliced from a 3MF that carries its modifiers.
--set heavy is the package before D22: config/*_heavy.ini (3 walls), the parts.csv "heavy" overrides, no rings.
S1 gate: the parts with insert rings wait for the light coupons C2aL, C2bL and C3L. `plates` keeps them on plates of
their own and also slices each of those plates with the parts' "heavy" overrides and no rings: the fallback if a
light coupon fails. Every plate is written as a PrusaSlicer 3MF (one object per part, rings as modifiers) next to its
G-code. Upstream STLs are read from <repo>/print/ (upstream commit 730c14b content, unchanged at b23317a).
ODM_SLICER_THREADS sets the slicer threads (default 2, for the shared box).
"""
import argparse, csv, datetime, hashlib, json, math, os, re, subprocess, sys, zipfile
from concurrent.futures import ThreadPoolExecutor
from xml.sax.saxutils import quoteattr

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, "config")
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
PRINT_DIR = os.path.join(REPO, "print")
OLD_SLICE = os.path.join(REPO, "altaay_lab", "audit", "slice_best.json")
SLICER = os.environ.get("PRUSA_SLICER", "prusa-slicer")
THREADS = os.environ.get("ODM_SLICER_THREADS", "2")
FIL_DIA = 1.75
DENSITY = {"PLA": 1.20, "TPU": 1.216}   # Overture TDS values (see filament ini files)
SKIRT = 3.45        # skirt distance 3 mm plus half its line, mm
BED_MARGIN = 4.0    # mm kept free between the outermost part or support and the bed edge, besides the skirt
GAP = 5.0           # mm between the support outlines of two parts on a plate
PLATE_CAP_H = 14.0  # a multi-part plate is kept under this many slicer hours
SETS = ("light", "heavy")

# Solid rings (D22; sizes and reasons in config/mod_ring.ini): kind -> hole diameter range (mm), least hole depth (mm)
# and the solid wall the ring puts round the hole (mm). RING_END: the ring runs this far past each end of the hole.
RING = {"insert": dict(dmin=3.80, dmax=4.25, min_depth=4.0, wall=2.0),
        "pilot": dict(dmin=1.85, dmax=2.35, min_depth=3.0, wall=1.5),
        "seat": dict(dmin=31.5, dmax=33.0, min_depth=3.0, wall=2.0)}
RING_END = 0.6
STEP = 0.2          # mm between section planes in the hole search
GATE = "insert"     # parts with these rings wait for the S1 light coupons (C2aL, C2bL, C3L)

UP = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+y": (0, 1, 0), "-y": (0, -1, 0),
      "+z": (0, 0, 1), "-z": (0, 0, -1)}


# Optional expression parts that are in the URDF but not in print/ or the print guide.
# antenna.stl (meters): a 150 mm rod, 1.8 mm diameter, with a 3.8 x 6 mm end collar. Printed
# flat (rod along the bed). Not in the core totals.
OPTIONAL = [dict(stl="antenna.stl", src=os.path.join(REPO, "mini_bdx", "robots", "open_duck_mini_v2", "antenna.stl"),
                 scale=1000.0, qty=2, materials=[("PLA", ""), ("TPU", "")])]


def read_parts(set_="light"):
    """parts.csv rows. "overrides" and "rings" are the light profile (D22), "heavy" the overrides before D22. With
    set_ "heavy" the "heavy" overrides replace "overrides" and the rings are dropped. "gate": the part waits for the S1
    light coupons (its rings include insert bores)."""
    with open(os.path.join(HERE, "parts.csv"), newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["qty"] = int(r["qty"])
        r["leg1"] = int(r["leg1"] or 0)
        r["spare"] = int(r.get("spare") or 0)
        for k in ("profile", "rings", "heavy"):
            r[k] = r.get(k) or ""
        r["gate"] = GATE in r["rings"].split("+")
    check_profiles(rows)
    if set_ == "heavy":
        for r in rows:
            r.update(overrides=r["heavy"], rings="", gate=False, profile="before D22")
    return rows


def effective(material, overrides, set_):
    """merged settings of one config stack (later files win, as in the slicer), profile names left out"""
    out = {}
    for f in config_stack(material, overrides, set_=set_):
        out.update(read_ini(f))
    out.pop("print_settings_id", None)
    return out


def check_profiles(rows):
    """The parts.csv "profile" column must say what the settings do: heavy = the same settings as before D22 and no
    rings; light = lighter than before, no rings; rings = has rings. Every spare stays heavy (D22)."""
    bad = []
    for r in rows:
        same = effective(r["material"], r["overrides"], "light") == effective(r["material"], r["heavy"], "heavy")
        ok = {"heavy": same and not r["rings"], "light": not same and not r["rings"], "rings": bool(r["rings"])}.get(r["profile"], False)
        if not ok or (r["spare"] and r["profile"] != "heavy"):
            bad.append(r["stl"])
    if bad:
        sys.exit("parts.csv: the profile column does not match the settings for %s" % ", ".join(bad))


def up_vector(up):
    if up.startswith("vec:"):
        v = np.array([float(x) for x in up[4:].split()], float)
        return v / np.linalg.norm(v)
    return np.array(UP[up], float)


def rot_up(up):
    """4x4 rotation that turns the given part direction to +Z (print up)."""
    u = up_vector(up)
    z = np.array([0, 0, 1.0])
    ax = np.cross(u, z)
    if np.linalg.norm(ax) < 1e-9:
        return np.eye(4) if u @ z > 0 else trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
    return trimesh.transformations.rotation_matrix(np.arccos(np.clip(u @ z, -1, 1)), ax)


def oriented(stl, up, out_dir):
    """Write the upstream STL turned to its print orientation, resting on Z=0. Parts given by a
    vector (not along a CAD axis) are also turned about Z to the smallest footprint."""
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, stl)
    if not os.path.exists(dst):
        m = trimesh.load(os.path.join(PRINT_DIR, stl))
        m.apply_transform(rot_up(up))
        if up.startswith("vec:"):
            best = min(range(0, 90), key=lambda d: np.prod(np.ptp(
                (m.vertices[:, :2] @ np.array([[math.cos(math.radians(d)), -math.sin(math.radians(d))],
                                               [math.sin(math.radians(d)), math.cos(math.radians(d))]]).T), axis=0)))
            m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(best), [0, 0, 1]))
        m.apply_translation(-m.bounds[0])
        m.export(dst)
    return dst


def config_stack(material, overrides, bed=220, set_="light"):
    sfx = "_heavy" if set_ == "heavy" else ""
    files = [os.path.join(CFG, "printer_generic.ini")]
    if int(bed) == 256:
        files.append(os.path.join(CFG, "bed_256.ini"))
    if material == "TPU":
        files += [os.path.join(CFG, "tpu_print%s.ini" % sfx), os.path.join(CFG, "filament_tpu95a.ini")]
    else:
        files += [os.path.join(CFG, "pla_print%s.ini" % sfx), os.path.join(CFG, "filament_easy_pla.ini")]
    for o in [x for x in (overrides or "").split("+") if x]:
        files.append(os.path.join(CFG, "ovr_%s.ini" % o))
    return files


def run_slicer(stls, cfgs, gcode, merge=False, keep_xy=False):
    """merge: several STLs as one plate; keep_xy: keep the XY positions stored in the files
    (always used for plates; without it the CLI re-arranges objects and can overlap them)."""
    cmd = [SLICER, "--export-gcode", "--loglevel", "1", "--threads", THREADS]
    for c in cfgs:
        cmd += ["--load", c]
    if merge:
        cmd += ["--merge", "--dont-arrange"]
    elif keep_xy:
        cmd += ["--dont-arrange"]
    cmd += ["-o", gcode] + list(stls)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(gcode):
        raise RuntimeError("slicer failed: %s\n%s" % (" ".join(cmd), r.stdout[-2000:] + r.stderr[-2000:]))
    return [l for l in (r.stdout + r.stderr).splitlines() if "error" in l.lower() or "warning" in l.lower()]


def hms(s):
    """'1d 2h 3m 4s' -> seconds"""
    return sum(int(v) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[u] for v, u in re.findall(r"(\d+)([dhms])", s))


def parse_gcode(path, density):
    """Totals from the PrusaSlicer footer, filament per feature type (relative E), and the XY
    extent of all moves, of the part only, and of part plus supports."""
    out = {"g": None, "s": None}
    typ, by = "start", {}
    ext = {"all": [], "model": [], "nos": []}
    started = False
    x = y = None
    with open(path) as f:
        for line in f:
            if line.startswith(";TYPE:"):
                typ = line[6:].strip()
            elif line.startswith(";LAYER_CHANGE"):
                started = True
            elif line.startswith("G1 "):
                mx = re.search(r" X(-?[\d.]+)", line)
                my = re.search(r" Y(-?[\d.]+)", line)
                if mx:
                    x = float(mx.group(1))
                if my:
                    y = float(my.group(1))
                me = re.search(r" E(-?[\d.]+)", line)
                if me and (mx or my):
                    e = float(me.group(1))
                    if e > 0:
                        by[typ] = by.get(typ, 0.0) + e
                    if started and x is not None and y is not None:
                        ext["all"].append((x, y))
                        if typ != "Skirt/Brim":
                            ext["nos"].append((x, y))
                            if not typ.startswith("Support material"):
                                ext["model"].append((x, y))
            elif line.startswith("; total filament used [g] ="):
                out["g"] = float(line.split("=")[1])
            elif line.startswith("; estimated printing time (normal mode) ="):
                out["s"] = hms(line.split("=")[1])
    area = math.pi * (FIL_DIA / 2) ** 2
    grams = lambda mm: mm * area * density / 1000.0
    sup = sum(v for k, v in by.items() if k.startswith("Support material"))
    out["g_support"] = round(grams(sup), 2)
    out["g_skirt"] = round(grams(by.get("Skirt/Brim", 0.0)), 2)
    out["g_model"] = round(out["g"] - out["g_support"] - out["g_skirt"], 2)
    for k, v in ext.items():
        if v:
            a = np.array(v)
            out["xy_" + k] = [round(float(a[:, 0].min()), 2), round(float(a[:, 0].max()), 2),
                              round(float(a[:, 1].min()), 2), round(float(a[:, 1].max()), 2)]
    return out


# ---------- solid rings: holes in the print-oriented mesh and the modifier cylinders round them ----------
def find_holes(m, step=STEP):
    """Round holes along the 3 axes of the print frame, from closed inner rings of sections every `step` mm.
    Returns [dict(axis, c (a point on the hole axis, mm; the axis coordinate is 0), d (mean diameter), z0, z1)]."""
    from shapely.geometry import Polygon
    out = []
    for ax in range(3):
        n = np.zeros(3); n[ax] = 1.0
        lo, hi = m.bounds[0][ax], m.bounds[1][ax]
        hs = np.arange(lo + step / 2, hi, step)
        secs = m.section_multiplane(plane_origin=m.bounds[0], plane_normal=n, heights=hs - lo)
        rings = []
        for h, s in zip(hs, secs):
            if s is None:
                continue
            T = s.metadata["to_3D"]
            try:
                polys = s.polygons_full
            except Exception:
                continue
            for poly in polys:
                for r in poly.interiors:
                    q = Polygon(r)
                    if q.area <= 0 or 4 * math.pi * q.area / q.length ** 2 < 0.93:     # round only
                        continue
                    c = np.array(q.centroid.coords[0]); pts = np.array(r.coords)[:-1]
                    rings.append((h, (T @ np.r_[c, 0.0, 1.0])[:3], 2 * float(np.linalg.norm(pts - c, axis=1).mean())))
        rings.sort(key=lambda t: t[0])
        groups = []
        for h, c3, d in rings:
            for g in groups:
                if abs(g["d"] - d) < 0.3 and np.linalg.norm(np.delete(g["c"] - c3, ax)) < 0.3 and h - g["h1"] < step * 1.6:
                    g["h1"] = h; g["ds"].append(d); break
            else:
                groups.append(dict(c=c3, d=d, h0=h, h1=h, ds=[d]))
        for g in groups:
            c = g["c"].copy(); c[ax] = 0.0
            out.append(dict(axis=ax, c=[round(float(x), 3) for x in c], d=round(float(np.median(g["ds"])), 3),
                            z0=round(g["h0"] - step / 2, 2), z1=round(g["h1"] + step / 2, 2)))
    return out


def classify(holes):
    out = {}
    for k, sp in RING.items():
        out[k] = [h for h in holes if sp["dmin"] <= h["d"] <= sp["dmax"] and h["z1"] - h["z0"] >= sp["min_depth"] - 1e-6]
    return out


def ring_meshes(holes, kinds):
    """modifier cylinders (trimesh, print frame) for the hole kinds asked for"""
    out = []
    for k in kinds:
        sp = RING[k]
        for h in holes[k]:
            cyl = trimesh.creation.cylinder(radius=h["d"] / 2 + sp["wall"], height=h["z1"] - h["z0"] + 2 * RING_END, sections=64)
            if h["axis"] == 0:
                cyl.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
            elif h["axis"] == 1:
                cyl.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
            c = np.array(h["c"], float); c[h["axis"]] = (h["z0"] + h["z1"]) / 2
            cyl.apply_translation(c)
            out.append((k, cyl))
    return out


def holes_for(parts, odir, out):
    """insert bores, pilots and seats of every part that gets rings (print frame), cached in OUT/holes.json"""
    path = os.path.join(out, "holes.json")
    H = json.load(open(path)) if os.path.exists(path) else {}
    todo = [p for p in parts if p["rings"] and p["stl"] not in H]
    for p in todo:
        H[p["stl"]] = classify(find_holes(trimesh.load(oriented(p["stl"], p["up"], odir))))
    if todo:
        json.dump(H, open(path, "w"), indent=1)
    return H


def ring_mods(holes, rings):
    """[(name, cylinder, settings)]: the modifier volumes for the ring kinds in `rings` (config/mod_ring.ini)"""
    kinds = [k for k in (rings or "").split("+") if k]
    if not kinds:
        return []
    sets = read_ini(os.path.join(CFG, "mod_ring.ini"))
    return [("%s_ring_%02d" % (k, i), m, sets) for i, (k, m) in enumerate(ring_meshes(holes, kinds))]


def ring_count(mods):
    out = {}
    for name, _, _ in mods:
        k = name.split("_ring_")[0]
        out[k] = out.get(k, 0) + 1
    return out


def slice_one(inp, material, overrides, gcode, bed=220, set_="light", mesh=None):
    """inp: an STL, or a 3MF that carries the part's ring modifiers; mesh: the part's STL when inp is a 3MF"""
    warn = run_slicer([inp], config_stack(material, overrides, bed, set_), gcode)
    r = parse_gcode(gcode, DENSITY[material])
    m = trimesh.load(mesh or inp)
    r["footprint"] = [round(float(m.extents[0]), 1), round(float(m.extents[1]), 1)]
    r["height"] = round(float(m.extents[2]), 1)
    # how far supports reach past the part outline, per side: [-x, +x, -y, +y]
    mo, ns = r.get("xy_model"), r.get("xy_nos")
    r["support_reach"] = [round(max(0.0, mo[0] - ns[0]), 2), round(max(0.0, ns[1] - mo[1]), 2),
                          round(max(0.0, mo[2] - ns[2]), 2), round(max(0.0, ns[3] - mo[3]), 2)] if mo and ns else [0, 0, 0, 0]
    r["slicer_messages"] = warn
    return r


def cmd_parts(a):
    parts = read_parts(a.set)
    if a.only:
        keep = set(a.only.split(","))
        parts = [p for p in parts if p["stl"] in keep]
    odir = os.path.join(a.out, "oriented")
    gdir = os.path.join(a.out, "gcode_parts")
    os.makedirs(gdir, exist_ok=True)
    res_path = os.path.join(a.out, "parts.json")
    res = json.load(open(res_path)) if os.path.exists(res_path) else {}
    holes = holes_for(parts, odir, a.out)

    def job(p):
        src = oriented(p["stl"], p["up"], odir)
        g = os.path.join(gdir, p["stl"].replace(".stl", ".gcode"))
        mods = ring_mods(holes.get(p["stl"]), p["rings"])
        inp = src
        if mods:
            inp = g.replace(".gcode", ".3mf")
            write_3mf(inp, [(p["stl"][:-4], trimesh.load(src), {}, mods)])
        r = slice_one(inp, p["material"], p["overrides"], g, set_=a.set, mesh=src)
        r.update(qty=p["qty"], material=p["material"], overrides=p["overrides"], rings=ring_count(mods), set=a.set,
                 profile=p["profile"], up=p["up"],
                 sha256=hashlib.sha256(open(os.path.join(PRINT_DIR, p["stl"]), "rb").read()).hexdigest())
        print("%-32s %7.2f g %6.2f h  support %6.2f g  rings %s  reach %s" % (
            p["stl"], r["g"], r["s"] / 3600, r["g_support"], r["rings"] or "-", r["support_reach"]), flush=True)
        return p["stl"], r

    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for k, r in ex.map(job, parts):
            res[k] = r
    json.dump(res, open(res_path, "w"), indent=1, sort_keys=True)


# ---------- plate packing (MaxRects, best short side fit, 90 degree turns allowed) ----------
def maxrects(items, W, H):
    """items: [(key, w, h)] already including the gap. Returns {key: (x, y, rotated)} or None."""
    free = [(0.0, 0.0, W, H)]
    place = {}
    for key, w, h in sorted(items, key=lambda t: -t[1] * t[2]):
        best = None
        for fx, fy, fw, fh in free:
            for rot, (iw, ih) in ((False, (w, h)), (True, (h, w))):
                if iw <= fw + 1e-9 and ih <= fh + 1e-9:
                    score = (min(fw - iw, fh - ih), max(fw - iw, fh - ih))
                    if best is None or score < best[0]:
                        best = (score, fx, fy, iw, ih, rot)
        if best is None:
            return None
        _, x, y, iw, ih, rot = best
        place[key] = (x, y, rot)
        nf = []
        for fx, fy, fw, fh in free:
            if x >= fx + fw or x + iw <= fx or y >= fy + fh or y + ih <= fy:
                nf.append((fx, fy, fw, fh))
                continue
            if x > fx:
                nf.append((fx, fy, x - fx, fh))
            if x + iw < fx + fw:
                nf.append((x + iw, fy, fx + fw - x - iw, fh))
            if y > fy:
                nf.append((fx, fy, fw, y - fy))
            if y + ih < fy + fh:
                nf.append((fx, y + ih, fw, fy + fh - y - ih))
        free = [r for r in nf if not any(r != o and r[0] >= o[0] and r[1] >= o[1] and
                                         r[0] + r[2] <= o[0] + o[2] and r[1] + r[3] <= o[1] + o[3] for o in nf)]
    return place


def outline(r):
    """Part plus support outline (w, h) and the part offset inside it, from a single-part slice."""
    rx0, rx1, ry0, ry1 = r.get("support_reach", [0, 0, 0, 0])
    w, h = r["footprint"]
    return (w + rx0 + rx1, h + ry0 + ry1, rx0, ry0, rx1, ry1)


def pack(copies, bed):
    """copies: [(key, w, h)] support outlines. Usable square = bed - 2*(skirt + margin)."""
    W = bed - 2 * (SKIRT + BED_MARGIN) + GAP
    return maxrects([(k, w + GAP, h + GAP) for k, w, h in copies], W, W)


def place_and_slice(name, copies, src_of, reach_of, material, overrides, bed, out_dir, mods_of=None, set_="light"):
    """copies: [(key, w, h)] support outlines; src_of[key] = oriented STL; reach_of[key] = support reach [-x, +x, -y, +y];
    mods_of[key] = ring modifiers in the oriented part frame. Places every copy, writes the plate as a 3MF (one object
    per copy, its rings as modifiers) and slices it as one job with the plate's profile."""
    pl = pack(copies, bed)
    if pl is None:
        raise RuntimeError("plate %s does not fit a %d bed" % (name, bed))
    objs = []
    m0 = SKIRT + BED_MARGIN
    for key, (x, y, rot) in pl.items():
        rx0, rx1, ry0, ry1 = reach_of[key]
        m = trimesh.load(src_of[key])
        T = np.eye(4)
        if rot:   # +90 deg about Z: old -y reach becomes +x, old +y becomes -x, old -x becomes -y
            T = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1])
            m.apply_transform(T)
            rx0, rx1, ry0, ry1 = ry1, ry0, rx0, rx1
        t = [m0 + x + rx0 - m.bounds[0][0], m0 + y + ry0 - m.bounds[0][1], -m.bounds[0][2]]
        m.apply_translation(t)
        T = trimesh.transformations.translation_matrix(t) @ T
        mods = []
        for n, c, s in (mods_of or {}).get(key, []):
            c = c.copy()
            c.apply_transform(T)
            mods.append((n, c, s))
        objs.append((key, m, {}, mods))
    f3 = os.path.join(out_dir, name + ".3mf")
    write_3mf(f3, objs)
    g = os.path.join(out_dir, name + ".gcode")
    warn = run_slicer([f3], config_stack(material, overrides, bed, set_), g, keep_xy=True)
    r = parse_gcode(g, DENSITY[material])
    e = r.get("xy_all")
    r["fits_bed"] = bool(e and e[0] >= 0 and e[2] >= 0 and e[1] <= bed and e[3] <= bed)
    r["slicer_messages"] = warn
    r["conflicts"] = [w for w in warn if "conflict" in w.lower()]
    r["items"] = sorted(pl.keys())
    r["per_object_g"] = per_object_grams(g, DENSITY[material])
    return r


def build_queue(parts):
    """What is printed after the coupon session: leg 1 first, then the rest plus spares."""
    leg, rest = [], []
    for p in parts:
        n_leg = p["leg1"]
        n_rest = p["qty"] - p["leg1"]
        if p["stl"] == "left_eye.stl":            # whole-part test print T1 in the coupon session
            n_rest -= 1
        if p["stl"] == "foot_bottom_tpu.stl":     # T2 in the coupon session is the leg 1 sole
            n_leg -= 1
        leg += [(p, False)] * max(0, n_leg)
        rest += [(p, False)] * max(0, n_rest) + [(p, True)] * p["spare"]
    return leg, rest


def group_plates(items, res, bed, cap_h):
    """One print profile per plate, packed by support outline, multi-part plates under cap_h hours. Rings ride with
    their part as modifiers, but the parts that wait for the S1 gate get plates of their own, so a failed gate
    changes whole plates and not parts inside a plate."""
    groups = {}
    for p, sp in items:
        groups.setdefault((p["material"], p["overrides"], p["gate"]), []).append((p, sp))
    plates = []
    for (mat, ovr, gate), its in sorted(groups.items()):
        its.sort(key=lambda t: -outline(res[t[0]["stl"]])[0] * outline(res[t[0]["stl"]])[1])
        open_pl = []
        for p, sp in its:
            r = res[p["stl"]]
            w, h = outline(r)[:2]
            for pl in open_pl:
                if (pl["s"] + r["s"]) / 3600 > cap_h:
                    continue
                trial = pl["copies"] + [("c%d" % len(pl["copies"]), w, h)]
                if pack(trial, bed) is not None:
                    pl["copies"] = trial
                    pl["items"].append((p["stl"], sp))
                    pl["s"] += r["s"]
                    break
            else:
                if pack([("c0", w, h)], bed) is None:
                    raise RuntimeError("%s with its supports does not fit a %d bed" % (p["stl"], bed))
                open_pl.append({"material": mat, "overrides": ovr, "gate": gate, "items": [(p["stl"], sp)], "s": r["s"],
                                "copies": [("c0", w, h)]})
        plates += open_pl
    return plates


def short(ovr, gate=False):
    return (ovr or "base").replace("+", "_") + ("_rings" if gate else "")


def cmd_plates(a):
    parts = read_parts(a.set)
    P = {p["stl"]: p for p in parts}
    res = json.load(open(os.path.join(a.out, "parts.json")))
    odir = os.path.join(a.out, "oriented")
    bed = int(a.bed)
    out_dir = os.path.join(a.out, "plates_%d" % bed)
    os.makedirs(out_dir, exist_ok=True)
    holes = holes_for(parts, odir, a.out)
    leg, rest = build_queue(parts)
    plan = [("L1-%d" % (i + 1), pl) for i, pl in enumerate(group_plates(leg, res, bed, 99))]
    plan += [("P%d-%02d" % (bed, i + 1), pl) for i, pl in enumerate(group_plates(rest, res, bed, PLATE_CAP_H))]
    out = []
    for name, pl in plan:
        name = "%s_%s_%s" % (name, pl["material"], short(pl["overrides"], pl["gate"]))
        copies, src, reach, mods = [], {}, {}, {}
        for i, (s, sp) in enumerate(pl["items"]):
            k = "%02d_%s%s" % (i, s.replace(".stl", ""), "_SPARE" if sp else "")
            o = outline(res[s])
            copies.append((k, o[0], o[1]))
            src[k] = os.path.join(odir, s)
            reach[k] = [o[2], o[4], o[3], o[5]]   # [-x, +x, -y, +y]
            mods[k] = ring_mods(holes.get(s), P[s]["rings"])
        r = place_and_slice(name, copies, src, reach, pl["material"], pl["overrides"], bed, out_dir, mods, a.set)
        r.update(name=name, material=pl["material"], overrides=pl["overrides"], gate=pl["gate"], bed=bed,
                 stls=[s for s, sp in pl["items"]], spares=[s for s, sp in pl["items"] if sp],
                 ringed=sorted({s for s, sp in pl["items"] if P[s]["rings"]}))
        fb = ""
        if pl["gate"]:
            # the S1 gate fallback: the same plate with the parts' settings before D22 (4 walls) and no rings
            fbs = {P[s]["heavy"] for s, sp in pl["items"]}
            if len(fbs) != 1:
                raise RuntimeError("plate %s: its gated parts have different heavy overrides %s" % (name, sorted(fbs)))
            fo = fbs.pop()
            f = place_and_slice(name + "_fallback", copies, src, reach, pl["material"], fo, bed, out_dir, None, a.set)
            r["fallback"] = dict(overrides=fo, g=f["g"], s=f["s"], g_support=f["g_support"], fits_bed=f["fits_bed"],
                                 conflicts=f["conflicts"])
            fb = "  fallback (%s, no rings) %.1f g %.2f h fits=%s" % (fo, f["g"], f["s"] / 3600, f["fits_bed"])
        print("%-34s %7.1f g %6.2f h fits=%s conflicts=%d  %s%s" % (
            name, r["g"], r["s"] / 3600, r["fits_bed"], len(r["conflicts"]),
            ", ".join(s + (" (spare)" if sp else "") for s, sp in pl["items"]), fb), flush=True)
        out.append(r)
    json.dump(out, open(os.path.join(a.out, "plates_%d.json" % bed), "w"), indent=1)


def read_ini(path):
    """key = value lines of a PrusaSlicer ini (comments skipped)."""
    out = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def write_3mf(path, objs):
    """objs: [(name, trimesh in bed coordinates, {setting: value}[, [(modifier name, trimesh, {setting: value})]])].
    Writes a PrusaSlicer 3MF: one object per entry with its own settings (per-object overrides), the part as a
    ModelPart volume and each modifier (a solid ring) as a ParameterModifier volume that carries its settings. The
    print config itself is passed to the slicer with --load, so the file holds geometry and per-object and per-volume
    settings only."""
    model = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:slic3rpe="http://schemas.slic3r.org/3mf/2017/06">',
             ' <metadata name="slic3rpe:Version3mf">1</metadata>', ' <resources>']
    cfg = ['<?xml version="1.0" encoding="UTF-8"?>', '<config>']
    build = []
    for k, o in enumerate(objs, start=1):
        name, m, sets = o[0], o[1], o[2]
        vols = [(name, m, "ModelPart", {})] + [(n, mm, "ParameterModifier", s) for n, mm, s in (o[3] if len(o) > 3 else [])]
        V, F, ranges, off, nf = [], [], [], 0, 0
        for _, mm, _, _ in vols:
            V.append(np.asarray(mm.vertices))
            F.append(np.asarray(mm.faces) + off)
            ranges.append((nf, nf + len(mm.faces) - 1))
            off += len(mm.vertices)
            nf += len(mm.faces)
        model.append('  <object id="%d" type="model"><mesh><vertices>' % k)
        model += ['<vertex x="%.5f" y="%.5f" z="%.5f"/>' % tuple(v) for v in np.vstack(V)]
        model.append("</vertices><triangles>")
        model += ['<triangle v1="%d" v2="%d" v3="%d"/>' % tuple(t) for t in np.vstack(F)]
        model.append("</triangles></mesh></object>")
        build.append('  <item objectid="%d" transform="1 0 0 0 1 0 0 0 1 0 0 0" printable="1"/>' % k)
        cfg.append(' <object id="%d" instances_count="1">' % k)
        cfg.append('  <metadata type="object" key="name" value=%s/>' % quoteattr(name))
        for kk, vv in sets.items():
            cfg.append('  <metadata type="object" key=%s value=%s/>' % (quoteattr(kk), quoteattr(vv)))
        for (vn, _, typ, s), (f0, f1) in zip(vols, ranges):
            cfg.append('  <volume firstid="%d" lastid="%d">' % (f0, f1))
            cfg.append('   <metadata type="volume" key="name" value=%s/>' % quoteattr(vn))
            cfg.append('   <metadata type="volume" key="volume_type" value="%s"/>' % typ)
            if typ != "ModelPart":
                cfg.append('   <metadata type="volume" key="modifier" value="1"/>')
            for kk, vv in s.items():
                cfg.append('   <metadata type="volume" key=%s value=%s/>' % (quoteattr(kk), quoteattr(vv)))
            cfg.append("  </volume>")
        cfg.append(" </object>")
    model += [" </resources>", " <build>"] + build + [" </build>", "</model>"]
    cfg.append("</config>")
    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", "\n".join(model))
        z.writestr("Metadata/Slic3r_PE_model.config", "\n".join(cfg))


def per_object_grams(gcode, density):
    """Filament per labelled object in a plate G-code (support counted with its object)."""
    cur, by = None, {}
    area = math.pi * (FIL_DIA / 2) ** 2
    for line in open(gcode):
        if line.startswith("; printing object "):
            cur = line[len("; printing object "):].split(" id:")[0].strip()
        elif line.startswith("; stop printing object"):
            cur = None
        elif cur and line.startswith("G1 ") and " E" in line and (" X" in line or " Y" in line):
            e = float(re.search(r" E(-?[\d.]+)", line).group(1))
            if e > 0:
                by[cur] = by.get(cur, 0.0) + e
    return {k: round(v * area * density / 1000.0, 2) for k, v in by.items()}


def cmd_coupons(a):
    man = json.load(open(os.path.join(a.coupons, "manifest.json")))
    gdir = os.path.join(a.out, "gcode_coupons")
    os.makedirs(gdir, exist_ok=True)
    res, mods_of = {}, {}
    for c in man["coupons"]:
        src = os.path.join(a.coupons, c["file"])
        g = os.path.join(gdir, c["file"].replace(".stl", ".gcode"))
        # a light coupon (rings) gets its rings round the holes found in the coupon itself, as its part does
        mods = ring_mods(classify(find_holes(trimesh.load(src))), c.get("rings")) if c.get("rings") else []
        mods_of[c["file"]] = mods
        inp = src
        if mods:
            inp = g.replace(".gcode", ".3mf")
            write_3mf(inp, [(c["file"][:-4], trimesh.load(src), {}, mods)])
        r = slice_one(inp, c["material"], c["overrides"], g, mesh=src)
        r.update({k: c[k] for k in ("id", "material", "overrides", "source")})
        r["rings"] = ring_count(mods)
        res[c["file"]] = r
        print("%-50s %6.2f g %6.1f min  support %5.2f g  rings %s" % (c["file"], r["g"], r["s"] / 60, r["g_support"],
                                                                      r["rings"] or "-"), flush=True)
    # Coupon session: ONE plate per material. Each coupon keeps its part's profile through per-object settings (from
    # its ovr_*.ini files) and its rings as modifiers in a 3MF; the base profile comes from --load.
    plates = []
    sdir = os.path.join(a.out, "session")
    os.makedirs(sdir, exist_ok=True)
    for mat in sorted({c["material"] for c in man["coupons"]}):
        cs = [c for c in man["coupons"] if c["material"] == mat]
        name = "S%d_%s_coupons" % (len(plates) + 1, mat)
        copies, reach = [], {}
        for c in cs:
            k = c["file"].replace(".stl", "")
            o = outline(res[c["file"]])
            copies.append((k, o[0], o[1]))
            reach[k] = [o[2], o[4], o[3], o[5]]
        pl = pack(copies, 220)
        if pl is None:
            raise RuntimeError("coupon plate %s does not fit a 220 bed" % name)
        objs = []
        m0 = SKIRT + BED_MARGIN
        for c in cs:
            k = c["file"].replace(".stl", "")
            x, y, rot = pl[k]
            rx0, rx1, ry0, ry1 = reach[k]
            m = trimesh.load(os.path.join(a.coupons, c["file"]))
            T = np.eye(4)
            if rot:
                T = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1])
                m.apply_transform(T)
                rx0, rx1, ry0, ry1 = ry1, ry0, rx0, rx1
            t = [m0 + x + rx0 - m.bounds[0][0], m0 + y + ry0 - m.bounds[0][1], -m.bounds[0][2]]
            m.apply_translation(t)
            T = trimesh.transformations.translation_matrix(t) @ T
            mods = []
            for n, cyl, s in mods_of[c["file"]]:
                cyl = cyl.copy()
                cyl.apply_transform(T)
                mods.append((n, cyl, s))
            sets = {}
            for o in [x for x in (c["overrides"] or "").split("+") if x]:
                sets.update(read_ini(os.path.join(CFG, "ovr_%s.ini" % o)))
            objs.append((k, m, sets, mods))
        f3 = os.path.join(sdir, name + ".3mf")
        write_3mf(f3, objs)
        g = os.path.join(sdir, name + ".gcode")
        warn = run_slicer([f3], config_stack(mat, "", 220), g, keep_xy=True)
        r = parse_gcode(g, DENSITY[mat])
        e = r.get("xy_all")
        r["fits_bed"] = bool(e and e[0] >= 0 and e[2] >= 0 and e[1] <= 220 and e[3] <= 220)
        r["per_object_g"] = per_object_grams(g, DENSITY[mat])
        r.update(name=name, material=mat, overrides="per object", files=[c["file"] for c in cs],
                 slicer_messages=warn, settings={k: s for k, _, s, _ in objs},
                 rings={k: ring_count(mm) for k, _, _, mm in objs if mm})
        plates.append(r)
        print("session job %-20s %6.2f g %6.1f min fits=%s  %s" % (name, r["g"], r["s"] / 60, r["fits_bed"], r["per_object_g"]), flush=True)
    json.dump({"coupons": res, "session": plates}, open(os.path.join(a.out, "coupons.json"), "w"), indent=1)


def cmd_optional(a):
    """Slice the optional parts flat, in each listed material."""
    odir = os.path.join(a.out, "oriented")
    gdir = os.path.join(a.out, "gcode_optional")
    os.makedirs(odir, exist_ok=True)
    os.makedirs(gdir, exist_ok=True)
    res = {}
    for o in OPTIONAL:
        m = trimesh.load(o["src"])
        m.apply_scale(o["scale"])
        c = m.center_mass
        P = m.principal_inertia_vectors
        axis = P[np.argmax(np.ptp((m.vertices - c) @ P.T, axis=0))]       # long axis
        up = np.cross(axis, [0, 0, 1.0]) if abs(axis[2]) < 0.9 else np.cross(axis, [1.0, 0, 0])
        up /= np.linalg.norm(up)
        m.apply_transform(rot_up("vec:%f %f %f" % tuple(up)))
        m.apply_transform(trimesh.transformations.rotation_matrix(
            -math.atan2(*(m.principal_inertia_vectors[np.argmax(np.ptp(m.vertices @ m.principal_inertia_vectors.T, axis=0))][[1, 0]])), [0, 0, 1]))
        m.apply_translation(-m.bounds[0])
        src = os.path.join(odir, "optional_" + o["stl"])
        m.export(src)
        for mat, ovr in o["materials"]:
            g = os.path.join(gdir, "%s_%s.gcode" % (o["stl"][:-4], mat))
            r = slice_one(src, mat, ovr, g)
            r.update(qty=o["qty"], material=mat, volume_cm3=round(m.volume / 1000, 3))
            res["%s %s" % (o["stl"], mat)] = r
            print("%-18s %-4s %6.2f g %6.1f min  support %5.2f g  footprint %s h %s" % (
                o["stl"], mat, r["g"], r["s"] / 60, r["g_support"], r["footprint"], r["height"]), flush=True)
    json.dump(res, open(os.path.join(a.out, "optional.json"), "w"), indent=1)


# ---------- summary ----------
def h(s):
    return "%.2f" % (s / 3600.0)


def profile_cell(p, r):
    """e.g. 'light (fit)', 'rings (base + 8 insert rings)', 'heavy (wall3+fit)'"""
    rings = " + ".join("%d %s rings" % (n, k) for k, n in sorted((r.get("rings") or {}).items()))
    return "%s (%s)" % (p["profile"] or "-", " + ".join(x for x in (p["overrides"] or "base", rings) if x))


def names_cell(r, ringed=()):
    out = []
    for s in sorted(set(r["stls"])):
        n, ns = r["stls"].count(s), r["spares"].count(s)
        out.append("%s x%d%s%s" % (s.replace(".stl", ""), n, (" (%d spare)" % ns) if ns else "",
                                   " (rings)" if s in ringed else ""))
    return ", ".join(out)


def cmd_summary(a):
    parts = read_parts(a.set)
    res = json.load(open(os.path.join(a.out, "parts.json")))
    if a.before:
        B = json.load(open(os.path.join(a.before, "parts.json")))
        old = {k: dict(g=v["g"], t=v["s"], sup=v["g_support"]) for k, v in B.items()}
        on = "before"
    else:
        old = {k: dict(g=v["g"], t=v["t"], sup=None) for k, v in json.load(open(OLD_SLICE)).items()}
        on = "old"
    T = ["| STL | Qty | Material | Profile | g each | h each | support g each | g total | h total | %s g each | %s h each |" % (on, on),
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    tot, otot, spare = {}, {}, {}
    net = onet = 0.0
    for p in parts:
        r, o, q = res[p["stl"]], old[p["stl"]], p["qty"]
        t = tot.setdefault(p["material"], [0, 0.0, 0.0, 0.0])
        t[0] += q; t[1] += q * r["g"]; t[2] += q * r["s"]; t[3] += q * r["g_support"]
        ot = otot.setdefault(p["material"], [0, 0.0, 0.0])
        ot[0] += q; ot[1] += q * o["g"]; ot[2] += q * o["t"]
        net += q * (r["g"] - r["g_support"])
        onet += q * (o["g"] - (o["sup"] or 0.0))
        if p["spare"]:
            sp = spare.setdefault(p["material"], [0, 0.0, 0.0])
            sp[0] += p["spare"]; sp[1] += p["spare"] * r["g"]; sp[2] += p["spare"] * r["s"]
        T.append("| %s | %d | %s | %s | %.2f | %s | %.2f | %.1f | %s | %.2f | %s |" % (
            p["stl"], q, p["material"], profile_cell(p, r), r["g"], h(r["s"]), r["g_support"],
            q * r["g"], h(q * r["s"]), o["g"], h(o["t"])))
    on_c = on.capitalize()
    T += ["", "| Material | Parts | Grams | Hours | of which support g | %s grams | %s hours |" % (on_c, on_c), "|---|---|---|---|---|---|---|"]
    for m in sorted(tot):
        t, ot = tot[m], otot[m]
        T.append("| %s | %d | %.1f | %.1f | %.1f | %.1f | %.1f |" % (m, t[0], t[1], t[2] / 3600, t[3], ot[1], ot[2] / 3600))
    at = [sum(tot[m][i] for m in tot) for i in range(4)]
    ao = [sum(otot[m][i] for m in otot) for i in range(3)]
    T.append("| Total | %d | %.1f | %.1f | %.1f | %.1f | %.1f |" % (at[0], at[1], at[2] / 3600, at[3], ao[1], ao[2] / 3600))
    T.append("")
    T.append("On the robot (grams less support, the way sim/mass_budget.py counts a printed part): %.1f g%s." % (
        net, (", %.1f g before (%+.1f g)" % (onet, net - onet)) if a.before else ""))
    gated = [p for p in parts if p["gate"]]
    fb = None
    if gated and a.before:
        dg = sum(p["qty"] * (old[p["stl"]]["g"] - res[p["stl"]]["g"]) for p in gated)
        dn = sum(p["qty"] * ((old[p["stl"]]["g"] - old[p["stl"]]["sup"]) - (res[p["stl"]]["g"] - res[p["stl"]]["g_support"])) for p in gated)
        ds = sum(p["qty"] * (old[p["stl"]]["t"] - res[p["stl"]]["s"]) for p in gated)
        fb = (sum(p["qty"] for p in gated), dg, dn, ds)
        T.append("")
        T.append("S1 gate fallback: if a light coupon (C2aL, C2bL, C3L) fails, the %d parts with insert rings (%s) print with "
                 "their heavy overrides (insert, 4 walls) and no rings: %+.1f g filament, %+.1f g on the robot, %+.2f h "
                 "(the 'before' columns of these parts)." % (fb[0], ", ".join("%s x%d" % (p["stl"][:-4], p["qty"]) for p in gated),
                                                                dg, dn, ds / 3600))
    if spare:
        T += ["", "Spares (G5, G6, one set, printed in the plates below): " + "; ".join(
            "%s %d parts, %.1f g, %.1f h" % (m, v[0], v[1], v[2] / 3600) for m, v in sorted(spare.items()))]
    body = "\n".join(T) + "\n"
    plate_tot = {}
    for bed in (220, 256):
        pj = os.path.join(a.out, "plates_%d.json" % bed)
        if not os.path.exists(pj):
            continue
        P = json.load(open(pj))
        body += "\n## Plates, %d bed\n\n| Plate | Parts | g | h | fits |\n|---|---|---|---|---|\n" % bed
        for r in P:
            body += "| %s | %s | %.1f | %s | %s |\n" % (r["name"], names_cell(r, r.get("ringed", ())), r["g"], h(r["s"]),
                                                     "yes" if r["fits_bed"] and not r["conflicts"] else "CHECK")
        gs, ss = sum(r["g"] for r in P), sum(r["s"] for r in P)
        body += "| Total | %d jobs | %.1f | %.1f | |\n" % (len(P), gs, ss / 3600)
        plate_tot[bed] = (len(P), gs, ss)
        F = [r for r in P if r.get("fallback")]
        if F:
            body += ("\nS1 gate fallback, %d bed: if a light coupon fails, print these plates (same parts, same places) with "
                     "the profile below and no rings:\n\n| Plate | Profile | g | h | fits | change g | change h |\n"
                     "|---|---|---|---|---|---|---|\n" % bed)
            for r in F:
                f = r["fallback"]
                body += "| %s | %s | %.1f | %s | %s | %+.1f | %+.2f |\n" % (r["name"], f["overrides"], f["g"], h(f["s"]),
                                                                       "yes" if f["fits_bed"] and not f["conflicts"] else "CHECK",
                                                                       f["g"] - r["g"], (f["s"] - r["s"]) / 3600)
            dg, ds = sum(r["fallback"]["g"] - r["g"] for r in F), sum(r["fallback"]["s"] - r["s"] for r in F)
            body += "| Total | | | | | %+.1f | %+.2f |\n" % (dg, ds / 3600)
            body += "\nWith the fallback the full print is %d jobs, %.1f g and %.1f h.\n" % (len(P), gs + dg, (ss + ds) / 3600)
    cj = os.path.join(a.out, "coupons.json")
    S = None
    if os.path.exists(cj):
        C = json.load(open(cj))
        body += "\n## Coupons\n\n| File | Material | Profile | g | min | support g |\n|---|---|---|---|---|---|\n"
        for f, r in sorted(C["coupons"].items()):
            rings = " + ".join("%d %s ring%s" % (n, k, "" if n == 1 else "s") for k, n in sorted((r.get("rings") or {}).items()))
            prof = " + ".join(x for x in (r["overrides"] or "base", rings) if x)
            body += "| %s | %s | %s | %.2f | %.0f | %.2f |\n" % (f, r["material"], prof, r["g"], r["s"] / 60, r["g_support"])
        for r in C["session"]:
            body += "| job %s | %s | %s | %.2f | %.0f | %.2f |\n" % (r["name"], r["material"], r["overrides"] or "-", r["g"], r["s"] / 60, r["g_support"])
        S = C["session"]
    oj = os.path.join(a.out, "optional.json")
    if os.path.exists(oj):
        O = json.load(open(oj))
        body += "\n## Optional expression parts (not in the totals above)\n\n| Part | Qty | Material | g each | min each | support g each | g for qty | h for qty |\n|---|---|---|---|---|---|---|---|\n"
        for k, r in sorted(O.items()):
            body += "| %s | %d | %s | %.2f | %.0f | %.2f | %.2f | %s |\n" % (k.split()[0], r["qty"], r["material"], r["g"], r["s"] / 60,
                                                                     r["g_support"], r["qty"] * r["g"], h(r["qty"] * r["s"]))
    # header and what changed, from the same numbers
    now = datetime.datetime.now(datetime.timezone.utc).astimezone(__import__("zoneinfo").ZoneInfo("America/New_York"))
    hd = ["# SLICE_SUMMARY", "",
          "Last updated: %s ET. Generated by `python3 slice.py summary --out <dir>%s --md SLICE_SUMMARY.md` after the "
          "`parts`%s, `coupons`, `plates` (220 and 256) and `optional` runs (see PRINT_PLAN.md). Nothing has been printed." % (
              now.strftime("%Y-%m-%d %-I:%M %p"), " --before <dir_heavy>" if a.before else "",
              " (light, and `--set heavy` into <dir_heavy>)" if a.before else ""), "",
          "All grams and hours are PrusaSlicer 2.7.2 estimates made on the box with the generic printer in "
          "config/printer_generic.ini (0.4 mm nozzle, moderate speeds, 1500 mm/s2). They are not printed results. A faster "
          "printer will take fewer hours; grams change little between printers. Grams include supports and the skirt.", ""]
    if a.set == "light":
        hd.append("Settings: the light profile of DECISIONS.md D22 (print/MASS_STUDY.md variant c). Base config/pla_print.ini "
                  "and config/tpu_print.ini: 2 walls, gyroid infill PLA 15 %% and TPU 40 %%. Per-part overrides from parts.csv: "
                  "insert 4 walls; neck 5 walls and 40 %%; wall3 3 walls; fit outer wall first at 25 mm/s. Solid rings: "
                  "100 %% infill cylinders (config/mod_ring.ini) round the insert bores (2.0 mm solid) and screw pilots "
                  "(1.5 mm) of the parts with a rings entry in parts.csv; those parts are sliced from a 3MF that carries "
                  "the modifiers.%s Densities from the Overture data sheets: Easy PLA 1.20, TPU 95A 1.216 g/cm3. Upstream "
                  "STLs: print/ at 730c14b (unchanged at b23317a)." % (
                      " 'Before' columns: the same parts with the settings before D22 (`slice.py parts --set heavy`: "
                      "config/*_heavy.ini with 3 walls, the parts.csv heavy overrides, no rings)." if a.before else ""))
    else:
        hd.append("Settings: the heavy set, the package before DECISIONS.md D22 (config/*_heavy.ini with 3 walls and the "
                  "parts.csv heavy overrides, no rings).")
    if a.before:
        hd += ["", "## What changed with D22", ""]
        hd.append("- Robot set (36 STLs, 52 parts): %.1f g and %.1f h, against %.1f g and %.1f h before (%+.1f g, %+.1f h). "
                  "On the robot: %.1f g against %.1f g (%+.1f g)." % (at[1], at[2] / 3600, ao[1], ao[2] / 3600, at[1] - ao[1],
                                                                       (at[2] - ao[2]) / 3600, net, onet, net - onet))
        # two slicer runs of the same settings can differ by 0.01 g and 1 s (seen on head_yaw_to_roll)
        same = [p["stl"][:-4] for p in parts if abs(res[p["stl"]]["g"] - old[p["stl"]]["g"]) < 0.015 and
                abs(res[p["stl"]]["s"] - old[p["stl"]]["t"]) <= 1]
        hd.append("- Lighter: %d STLs. Unchanged (within 0.01 g and 1 s, the run to run noise): %d STLs (%s)." % (
            len(parts) - len(same), len(same), ", ".join(same)))
        if fb:
            hd.append("- S1 gate fallback (light coupon fails): %+.1f g filament, %+.1f g on the robot, %+.2f h on the %d insert ring parts." % (
                fb[1], fb[2], fb[3] / 3600, fb[0]))
        for bed, (n, gs, ss) in sorted(plate_tot.items()):
            bp = os.path.join(a.before, "plates_%d.json" % bed)
            if os.path.exists(bp):
                BP = json.load(open(bp))
                hd.append("- Plates, %d bed: %d jobs, %.1f g, %.1f h; before %d jobs, %.1f g, %.1f h." % (
                    bed, n, gs, ss / 3600, len(BP), sum(r["g"] for r in BP), sum(r["s"] for r in BP) / 3600))
        if S:
            hd.append("- Coupon session: %s." % "; ".join("%s %.1f g, %.2f h" % (r["name"], r["g"], r["s"] / 3600) for r in S))
        oldt = json.load(open(OLD_SLICE))
        hd.append("- The old PRINT_CHECK run (audit/slice_best.json, parts.csv quantities): %.1f g, %.1f h." % (
            sum(p["qty"] * oldt[p["stl"]]["g"] for p in parts), sum(p["qty"] * oldt[p["stl"]]["t"] for p in parts) / 3600))
    txt = "\n".join(hd) + "\n\n## Per part (robot set: 36 STLs, 52 parts)\n\n" + body
    if a.md:
        open(a.md, "w").write(txt)
    print(txt)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    for n in ("parts", "coupons", "plates", "optional", "summary"):
        s = sp.add_parser(n)
        s.add_argument("--out", required=True, help="output folder outside the repo")
        if n in ("parts", "plates", "summary"):
            s.add_argument("--set", default="light", choices=SETS, help="light: the profile of D22 (default); heavy: before D22")
        if n == "parts":
            s.add_argument("--only", default="")
            s.add_argument("--jobs", type=int, default=1)
        if n == "coupons":
            s.add_argument("--coupons", required=True, help="folder written by make_coupons.py")
        if n == "plates":
            s.add_argument("--bed", default="220", choices=["220", "256"])
        if n == "summary":
            s.add_argument("--md", default="")
            s.add_argument("--before", default="", help="folder of a `parts --set heavy` run (and its plates, if any)")
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    if out == REPO or out.startswith(REPO + os.sep):
        sys.exit("--out must be outside the repo (no G-code or CAD exports in git)")
    os.makedirs(out, exist_ok=True)
    a.out = out
    if getattr(a, "before", ""):
        a.before = os.path.abspath(a.before)
    {"parts": cmd_parts, "coupons": cmd_coupons, "plates": cmd_plates, "optional": cmd_optional,
     "summary": cmd_summary}[a.cmd](a)


if __name__ == "__main__":
    main()
