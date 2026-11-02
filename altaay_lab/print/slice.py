#!/usr/bin/env python3
"""Slice the Open Duck Mini v2 print package with the PrusaSlicer CLI (estimates only).

Nothing here starts a print. All outputs (oriented STLs, G-code, JSON) go to --out, which must
be outside the repo (lab rule: no CAD exports or G-code in git).

  python3 slice.py parts   --out DIR [--only a.stl,b.stl] [--jobs 2]
  python3 slice.py coupons --out DIR --coupons COUPON_DIR      (COUPON_DIR from make_coupons.py)
  python3 slice.py plates  --out DIR --bed 220|256             (needs a finished `parts` run in DIR)
  python3 slice.py optional --out DIR                          (optional expression parts, not in totals)
  python3 slice.py summary --out DIR [--md FILE]               (tables from the runs above)

Config stack per part: config/printer_generic.ini [+ bed_256.ini] + material print file +
filament file + overrides from parts.csv in the order given (ovr_insert, ovr_neck, ovr_fit).
Upstream STLs are read from <repo>/print/ (upstream commit 730c14b content, unchanged at b23317a).
"""
import argparse, csv, hashlib, json, math, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, "config")
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
PRINT_DIR = os.path.join(REPO, "print")
OLD_SLICE = os.path.join(REPO, "altaay_lab", "audit", "slice_best.json")
SLICER = os.environ.get("PRUSA_SLICER", "prusa-slicer")
FIL_DIA = 1.75
DENSITY = {"PLA": 1.20, "TPU": 1.216}   # Overture TDS values (see filament ini files)
SKIRT = 3.45        # skirt distance 3 mm plus half its line, mm
BED_MARGIN = 4.0    # mm kept free between the outermost part or support and the bed edge, besides the skirt
GAP = 5.0           # mm between the support outlines of two parts on a plate
PLATE_CAP_H = 14.0  # a multi-part plate is kept under this many slicer hours

UP = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+y": (0, 1, 0), "-y": (0, -1, 0),
      "+z": (0, 0, 1), "-z": (0, 0, -1)}


# Optional expression parts that are in the URDF but not in print/ or the print guide.
# antenna.stl (meters): a 150 mm rod, 1.8 mm diameter, with a 3.8 x 6 mm end collar. Printed
# flat (rod along the bed). Not in the core totals.
OPTIONAL = [dict(stl="antenna.stl", src=os.path.join(REPO, "mini_bdx", "robots", "open_duck_mini_v2", "antenna.stl"),
                 scale=1000.0, qty=2, materials=[("PLA", ""), ("TPU", "")])]


def read_parts():
    with open(os.path.join(HERE, "parts.csv"), newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["qty"] = int(r["qty"])
        r["leg1"] = int(r["leg1"] or 0)
        r["spare"] = int(r.get("spare") or 0)
    return rows


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


def config_stack(material, overrides, bed=220):
    files = [os.path.join(CFG, "printer_generic.ini")]
    if int(bed) == 256:
        files.append(os.path.join(CFG, "bed_256.ini"))
    if material == "TPU":
        files += [os.path.join(CFG, "tpu_print.ini"), os.path.join(CFG, "filament_tpu95a.ini")]
    else:
        files += [os.path.join(CFG, "pla_print.ini"), os.path.join(CFG, "filament_easy_pla.ini")]
    for o in [x for x in (overrides or "").split("+") if x]:
        files.append(os.path.join(CFG, "ovr_%s.ini" % o))
    return files


def run_slicer(stls, cfgs, gcode, merge=False, keep_xy=False):
    """merge: several STLs as one plate; keep_xy: keep the XY positions stored in the files
    (always used for plates; without it the CLI re-arranges objects and can overlap them)."""
    cmd = [SLICER, "--export-gcode", "--loglevel", "1"]
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


def slice_one(stl_path, material, overrides, gcode, bed=220):
    warn = run_slicer([stl_path], config_stack(material, overrides, bed), gcode)
    r = parse_gcode(gcode, DENSITY[material])
    m = trimesh.load(stl_path)
    r["footprint"] = [round(float(m.extents[0]), 1), round(float(m.extents[1]), 1)]
    r["height"] = round(float(m.extents[2]), 1)
    # how far supports reach past the part outline, per side: [-x, +x, -y, +y]
    mo, ns = r.get("xy_model"), r.get("xy_nos")
    r["support_reach"] = [round(max(0.0, mo[0] - ns[0]), 2), round(max(0.0, ns[1] - mo[1]), 2),
                          round(max(0.0, mo[2] - ns[2]), 2), round(max(0.0, ns[3] - mo[3]), 2)] if mo and ns else [0, 0, 0, 0]
    r["slicer_messages"] = warn
    return r


def cmd_parts(a):
    parts = read_parts()
    if a.only:
        keep = set(a.only.split(","))
        parts = [p for p in parts if p["stl"] in keep]
    odir = os.path.join(a.out, "oriented")
    gdir = os.path.join(a.out, "gcode_parts")
    os.makedirs(gdir, exist_ok=True)
    res_path = os.path.join(a.out, "parts.json")
    res = json.load(open(res_path)) if os.path.exists(res_path) else {}

    def job(p):
        src = oriented(p["stl"], p["up"], odir)
        g = os.path.join(gdir, p["stl"].replace(".stl", ".gcode"))
        r = slice_one(src, p["material"], p["overrides"], g)
        r.update(qty=p["qty"], material=p["material"], overrides=p["overrides"], up=p["up"],
                 sha256=hashlib.sha256(open(os.path.join(PRINT_DIR, p["stl"]), "rb").read()).hexdigest())
        print("%-32s %7.2f g %6.2f h  support %6.2f g  reach %s" % (
            p["stl"], r["g"], r["s"] / 3600, r["g_support"], r["support_reach"]), flush=True)
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


def place_and_slice(name, copies, src_of, reach_of, material, overrides, bed, out_dir):
    """copies: [(key, w, h)] support outlines; src_of[key] = oriented STL; reach_of[key] = support
    reach [-x, +x, -y, +y]. Writes the placed STLs and slices the plate as one job."""
    pl = pack(copies, bed)
    if pl is None:
        raise RuntimeError("plate %s does not fit a %d bed" % (name, bed))
    pdir = os.path.join(out_dir, name)
    os.makedirs(pdir, exist_ok=True)
    files = []
    m0 = SKIRT + BED_MARGIN
    for key, (x, y, rot) in pl.items():
        rx0, rx1, ry0, ry1 = reach_of[key]
        m = trimesh.load(src_of[key])
        if rot:   # +90 deg about Z: old -y reach becomes +x, old +y becomes -x, old -x becomes -y
            m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))
            rx0, rx1, ry0, ry1 = ry1, ry0, rx0, rx1
        m.apply_translation([m0 + x + rx0 - m.bounds[0][0], m0 + y + ry0 - m.bounds[0][1], -m.bounds[0][2]])
        f = os.path.join(pdir, "%s.stl" % key)
        m.export(f)
        files.append(f)
    g = os.path.join(out_dir, name + ".gcode")
    warn = run_slicer(files, config_stack(material, overrides, bed), g, merge=True)
    r = parse_gcode(g, DENSITY[material])
    e = r.get("xy_all")
    r["fits_bed"] = bool(e and e[0] >= 0 and e[2] >= 0 and e[1] <= bed and e[3] <= bed)
    r["slicer_messages"] = warn
    r["conflicts"] = [w for w in warn if "conflict" in w.lower()]
    r["items"] = sorted(pl.keys())
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
    """One print profile per plate, packed by support outline, multi-part plates under cap_h hours."""
    groups = {}
    for p, sp in items:
        groups.setdefault((p["material"], p["overrides"]), []).append((p, sp))
    plates = []
    for (mat, ovr), its in sorted(groups.items()):
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
                open_pl.append({"material": mat, "overrides": ovr, "items": [(p["stl"], sp)], "s": r["s"],
                                "copies": [("c0", w, h)]})
        plates += open_pl
    return plates


def short(ovr):
    return (ovr or "base").replace("+", "_")


def cmd_plates(a):
    parts = read_parts()
    res = json.load(open(os.path.join(a.out, "parts.json")))
    odir = os.path.join(a.out, "oriented")
    bed = int(a.bed)
    out_dir = os.path.join(a.out, "plates_%d" % bed)
    os.makedirs(out_dir, exist_ok=True)
    leg, rest = build_queue(parts)
    plan = [("L1-%d" % (i + 1), pl) for i, pl in enumerate(group_plates(leg, res, bed, 99))]
    plan += [("P%d-%02d" % (bed, i + 1), pl) for i, pl in enumerate(group_plates(rest, res, bed, PLATE_CAP_H))]
    out = []
    for name, pl in plan:
        name = "%s_%s_%s" % (name, pl["material"], short(pl["overrides"]))
        copies, src, reach = [], {}, {}
        for i, (s, sp) in enumerate(pl["items"]):
            k = "%02d_%s%s" % (i, s.replace(".stl", ""), "_SPARE" if sp else "")
            o = outline(res[s])
            copies.append((k, o[0], o[1]))
            src[k] = os.path.join(odir, s)
            reach[k] = [o[2], o[4], o[3], o[5]]   # [-x, +x, -y, +y]
        r = place_and_slice(name, copies, src, reach, pl["material"], pl["overrides"], bed, out_dir)
        r.update(name=name, material=pl["material"], overrides=pl["overrides"], bed=bed,
                 stls=[s for s, sp in pl["items"]], spares=[s for s, sp in pl["items"] if sp])
        print("%-32s %7.1f g %6.2f h fits=%s conflicts=%d  %s" % (
            name, r["g"], r["s"] / 3600, r["fits_bed"], len(r["conflicts"]),
            ", ".join(s + (" (spare)" if sp else "") for s, sp in pl["items"])), flush=True)
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
    """objs: [(name, trimesh in bed coordinates, {setting: value})]. Writes a PrusaSlicer 3MF whose
    objects carry their own settings (per-object overrides). The print config itself is passed to
    the slicer with --load, so the file holds geometry and per-object settings only."""
    import zipfile
    from xml.sax.saxutils import quoteattr
    model = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:slic3rpe="http://schemas.slic3r.org/3mf/2017/06">',
             ' <metadata name="slic3rpe:Version3mf">1</metadata>', ' <resources>']
    cfg = ['<?xml version="1.0" encoding="UTF-8"?>', '<config>']
    build = []
    for k, (name, m, sets) in enumerate(objs, start=1):
        model.append('  <object id="%d" type="model"><mesh><vertices>' % k)
        model += ['<vertex x="%.5f" y="%.5f" z="%.5f"/>' % tuple(v) for v in m.vertices]
        model.append("</vertices><triangles>")
        model += ['<triangle v1="%d" v2="%d" v3="%d"/>' % tuple(t) for t in m.faces]
        model.append("</triangles></mesh></object>")
        build.append('  <item objectid="%d" transform="1 0 0 0 1 0 0 0 1 0 0 0" printable="1"/>' % k)
        cfg.append(' <object id="%d" instances_count="1">' % k)
        cfg.append('  <metadata type="object" key="name" value=%s/>' % quoteattr(name))
        for kk, vv in sets.items():
            cfg.append('  <metadata type="object" key=%s value=%s/>' % (quoteattr(kk), quoteattr(vv)))
        cfg.append('  <volume firstid="0" lastid="%d">' % (len(m.faces) - 1))
        cfg.append('   <metadata type="volume" key="name" value=%s/>' % quoteattr(name))
        cfg.append('   <metadata type="volume" key="volume_type" value="ModelPart"/>')
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
    res = {}
    for c in man["coupons"]:
        src = os.path.join(a.coupons, c["file"])
        g = os.path.join(gdir, c["file"].replace(".stl", ".gcode"))
        r = slice_one(src, c["material"], c["overrides"], g)
        r.update({k: c[k] for k in ("id", "material", "overrides", "source")})
        res[c["file"]] = r
        print("%-46s %6.2f g %6.1f min  support %5.2f g" % (c["file"], r["g"], r["s"] / 60, r["g_support"]), flush=True)
    # Coupon session: ONE plate per material. Each coupon keeps its part's profile through
    # per-object settings (from its ovr_*.ini files) in a 3MF; the base profile comes from --load.
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
            if rot:
                m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))
                rx0, rx1, ry0, ry1 = ry1, ry0, rx0, rx1
            m.apply_translation([m0 + x + rx0 - m.bounds[0][0], m0 + y + ry0 - m.bounds[0][1], -m.bounds[0][2]])
            sets = {}
            for o in [x for x in (c["overrides"] or "").split("+") if x]:
                sets.update(read_ini(os.path.join(CFG, "ovr_%s.ini" % o)))
            objs.append((k, m, sets))
        f3 = os.path.join(sdir, name + ".3mf")
        write_3mf(f3, objs)
        g = os.path.join(sdir, name + ".gcode")
        warn = run_slicer([f3], config_stack(mat, "", 220), g, keep_xy=True)
        r = parse_gcode(g, DENSITY[mat])
        e = r.get("xy_all")
        r["fits_bed"] = bool(e and e[0] >= 0 and e[2] >= 0 and e[1] <= 220 and e[3] <= 220)
        r["per_object_g"] = per_object_grams(g, DENSITY[mat])
        r.update(name=name, material=mat, overrides="per object", files=[c["file"] for c in cs],
                 slicer_messages=warn, settings={k: s for k, _, s in objs})
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


def cmd_summary(a):
    parts = read_parts()
    res = json.load(open(os.path.join(a.out, "parts.json")))
    old = json.load(open(OLD_SLICE))
    L = ["| STL | Qty | Material | Override | g each | h each | support g each | g total | h total | old g each | old h each |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    tot, otot, spare = {}, {}, {}
    for p in parts:
        r, o, q = res[p["stl"]], old[p["stl"]], p["qty"]
        t = tot.setdefault(p["material"], [0, 0.0, 0.0, 0.0])
        t[0] += q; t[1] += q * r["g"]; t[2] += q * r["s"]; t[3] += q * r["g_support"]
        ot = otot.setdefault(p["material"], [0, 0.0, 0.0])
        ot[0] += q; ot[1] += q * o["g"]; ot[2] += q * o["t"]
        if p["spare"]:
            sp = spare.setdefault(p["material"], [0, 0.0, 0.0])
            sp[0] += p["spare"]; sp[1] += p["spare"] * r["g"]; sp[2] += p["spare"] * r["s"]
        L.append("| %s | %d | %s | %s | %.2f | %s | %.2f | %.1f | %s | %.2f | %s |" % (
            p["stl"], q, p["material"], p["overrides"] or "-", r["g"], h(r["s"]), r["g_support"],
            q * r["g"], h(q * r["s"]), o["g"], h(o["t"])))
    L += ["", "| Material | Parts | Grams | Hours | of which support g | Old grams | Old hours |", "|---|---|---|---|---|---|---|"]
    for m in sorted(tot):
        t, ot = tot[m], otot[m]
        L.append("| %s | %d | %.1f | %.1f | %.1f | %.1f | %.1f |" % (m, t[0], t[1], t[2] / 3600, t[3], ot[1], ot[2] / 3600))
    at = [sum(tot[m][i] for m in tot) for i in range(4)]
    ao = [sum(otot[m][i] for m in otot) for i in range(3)]
    L.append("| Total | %d | %.1f | %.1f | %.1f | %.1f | %.1f |" % (at[0], at[1], at[2] / 3600, at[3], ao[1], ao[2] / 3600))
    if spare:
        L += ["", "Spares (G5, G6): " + "; ".join("%s %d parts, %.1f g, %.1f h" % (m, v[0], v[1], v[2] / 3600) for m, v in sorted(spare.items()))]
    txt = "\n".join(L) + "\n"
    for bed in (220, 256):
        pj = os.path.join(a.out, "plates_%d.json" % bed)
        if os.path.exists(pj):
            P = json.load(open(pj))
            txt += "\nPlates, %d bed:\n\n| Plate | Parts | g | h | fits |\n|---|---|---|---|---|\n" % bed
            for r in P:
                names = []
                for s in sorted(set(r["stls"])):
                    n, ns = r["stls"].count(s), r["spares"].count(s)
                    names.append("%s x%d%s" % (s.replace(".stl", ""), n, (" (%d spare)" % ns) if ns else ""))
                txt += "| %s | %s | %.1f | %s | %s |\n" % (r["name"], ", ".join(names), r["g"], h(r["s"]),
                                                        "yes" if r["fits_bed"] and not r["conflicts"] else "CHECK")
            txt += "| Total | | %.1f | %.1f | |\n" % (sum(r["g"] for r in P), sum(r["s"] for r in P) / 3600)
    cj = os.path.join(a.out, "coupons.json")
    if os.path.exists(cj):
        C = json.load(open(cj))
        txt += "\nCoupons:\n\n| File | Material | Override | g | min | support g |\n|---|---|---|---|---|---|\n"
        for f, r in sorted(C["coupons"].items()):
            txt += "| %s | %s | %s | %.2f | %.0f | %.2f |\n" % (f, r["material"], r["overrides"] or "-", r["g"], r["s"] / 60, r["g_support"])
        for r in C["session"]:
            txt += "| job %s | %s | %s | %.2f | %.0f | %.2f |\n" % (r["name"], r["material"], r["overrides"] or "-", r["g"], r["s"] / 60, r["g_support"])
    oj = os.path.join(a.out, "optional.json")
    if os.path.exists(oj):
        O = json.load(open(oj))
        txt += "\nOptional expression parts (not in the totals above):\n\n| Part | Qty | Material | g each | min each | support g each | g for qty | h for qty |\n|---|---|---|---|---|---|---|---|\n"
        for k, r in sorted(O.items()):
            txt += "| %s | %d | %s | %.2f | %.0f | %.2f | %.2f | %s |\n" % (k.split()[0], r["qty"], r["material"], r["g"], r["s"] / 60,
                                                                     r["g_support"], r["qty"] * r["g"], h(r["qty"] * r["s"]))
    if a.md:
        open(a.md, "w").write(txt)
    print(txt)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    for n in ("parts", "coupons", "plates", "optional", "summary"):
        s = sp.add_parser(n)
        s.add_argument("--out", required=True, help="output folder outside the repo")
        if n == "parts":
            s.add_argument("--only", default="")
            s.add_argument("--jobs", type=int, default=2)
        if n == "coupons":
            s.add_argument("--coupons", required=True, help="folder written by make_coupons.py")
        if n == "plates":
            s.add_argument("--bed", default="220", choices=["220", "256"])
        if n == "summary":
            s.add_argument("--md", default="")
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    if out == REPO or out.startswith(REPO + os.sep):
        sys.exit("--out must be outside the repo (no G-code or CAD exports in git)")
    os.makedirs(out, exist_ok=True)
    a.out = out
    {"parts": cmd_parts, "coupons": cmd_coupons, "plates": cmd_plates, "optional": cmd_optional,
     "summary": cmd_summary}[a.cmd](a)


if __name__ == "__main__":
    main()
