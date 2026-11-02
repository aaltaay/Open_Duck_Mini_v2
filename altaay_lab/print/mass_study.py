#!/usr/bin/env python3
"""Mass study: the lightest print settings per part that keep every strength and fit requirement (estimates only).

Three variants of every printed part, sliced with the PrusaSlicer 2.7.2 CLI one part at a time (nothing is printed):
  a  upstream defaults: docs/print_guide.md (PLA 15 %, TPU 40 %) and the slicer's default of 2 walls (every Prusa
     0.20 mm print profile bundled with PrusaSlicer 2.7.2 has perimeters = 2). config_light/ base files, no overrides.
  b  our current settings: config/ plus the parts.csv overrides, exactly as slice.py builds them.
  c  lightest safe: config_light/ base files plus the overrides in config_light/parts_light.csv, plus solid rings
     (PrusaSlicer infill modifiers, config_light/mod_ring.ini) round the insert bores, screw pilots and bearing seats
     that parts_light.csv names.
Everything else (printer, filament, layers, supports, speeds, orientation) is the same in all three, so the grams
differ only by walls, infill and rings.

  python3 mass_study.py holes  --out DIR                    insert bores, pilots and seats of every part (print frame)
  python3 mass_study.py slice  --out DIR --variant a|b|c [--only x.stl,y.stl]
  python3 mass_study.py rings  --out DIR                    G-code check: what fills each ring in variants a, b and c
  python3 mass_study.py coupons --out DIR --coupons CDIR    light copies of the insert coupons (CDIR from make_coupons.py)
  python3 mass_study.py budget --out DIR                    whole-robot mass and centre of mass per variant
  python3 mass_study.py walk   --out DIR [--mode cases|comback] [--seeds N]
                                                            stock policy on the robot with variant c parts (sim pass only)
  python3 mass_study.py tables --out DIR [--md FILE]        markdown tables for MASS_STUDY.md

DIR must be outside the repo (G-code, 3MF and oriented STLs stay out of git). Run slicing with `nice -n 10`.
budget and walk use the sim agent's code unchanged: sim/mass_budget.py (build_budget, robot_com) and
sim/added_mass_sim.py (write_variant, run, gait_stats); only the slice table that build_budget reads is replaced
by this study's numbers. They need ODM_PLAYGROUND (Open_Duck_Playground at b9be205) like those scripts.
"""
import argparse, csv, json, math, os, re, subprocess, sys, time, zipfile
sys.dont_write_bytecode = True          # no __pycache__ in the repo folders we import from
import numpy as np
import trimesh
from xml.sax.saxutils import quoteattr

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SIM = os.path.join(REPO, "altaay_lab", "sim")
CFG_L = os.path.join(HERE, "config_light")
sys.path.insert(0, HERE)
import slice as S                       # orientation, config stack of variant b, G-code parsing (unchanged lab file)

THREADS = "2"                           # shared box: at most 2 slicer threads
RING = {"insert": dict(dmin=3.80, dmax=4.25, min_depth=4.0, wall=2.0),     # mod_ring.ini explains the sizes
        "pilot": dict(dmin=1.85, dmax=2.35, min_depth=3.0, wall=1.5),
        "seat": dict(dmin=31.5, dmax=33.0, min_depth=3.0, wall=2.0)}
# what the rule asks for next to the hole (checked in the G-code by `rings`): insert 1.6 mm solid (CNC Kitchen minimum
# wall, PRINT_CHECK.md flag 1); pilot 1.27 mm (the 3-wall ring of config/pla_print.ini); seat 1.67 mm (the 4-wall ring)
NEED = {"insert": 1.6, "pilot": 1.27, "seat": 1.67}
# variant d: variant c with these parts light (overrides, rings), for the option MASS_STUDY.md reports and does not adopt
D_PARTS = {"head.stl": ("", "insert+pilot+seat")}
RING_END = 0.6                          # mm past each end of the hole
STEP = 0.2                              # mm between section planes in the hole search


# ---------------------------------------------------------------------------------------------------------------
# parts and variants
# ---------------------------------------------------------------------------------------------------------------
def parts():
    return S.read_parts()


def light():
    with open(os.path.join(CFG_L, "parts_light.csv"), newline="") as f:
        return {r["stl"]: r for r in csv.DictReader(f)}


def read_ini(path):
    return S.read_ini(path)


def stack(variant, p):
    """config files, in load order, for one part (variant d: c, with the D_PARTS overrides)"""
    if variant == "b":
        return S.config_stack(p["material"], p["overrides"])
    base = [os.path.join(CFG_L, "printer_generic.ini")]
    base += ([os.path.join(CFG_L, "tpu_print.ini"), os.path.join(CFG_L, "filament_tpu95a.ini")] if p["material"] == "TPU"
             else [os.path.join(CFG_L, "pla_print.ini"), os.path.join(CFG_L, "filament_easy_pla.ini")])
    if variant == "a":
        return base
    ovr = stack_overrides(variant, p)
    return base + [os.path.join(CFG_L, "ovr_%s.ini" % o) for o in ovr.split("+") if o]


def stack_overrides(variant, p):
    return D_PARTS[p["stl"]][0] if variant == "d" and p["stl"] in D_PARTS else light()[p["stl"]]["overrides"]


def ring_kinds(variant, p):
    if variant == "d" and p["stl"] in D_PARTS:
        return [k for k in D_PARTS[p["stl"]][1].split("+") if k]
    if variant not in ("c", "d"):
        return []
    return [k for k in light()[p["stl"]]["rings"].split("+") if k]


# ---------------------------------------------------------------------------------------------------------------
# holes in the print-oriented STL
# ---------------------------------------------------------------------------------------------------------------
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


def cmd_holes(a):
    res = {}
    odir = os.path.join(a.out, "oriented")
    for p in parts():
        src = S.oriented(p["stl"], p["up"], odir)
        c = classify(find_holes(trimesh.load(src)))
        res[p["stl"]] = c
        print("%-30s inserts %2d  pilots %2d  seats %d" % (p["stl"], len(c["insert"]), len(c["pilot"]), len(c["seat"])), flush=True)
    json.dump(res, open(os.path.join(a.out, "holes.json"), "w"), indent=1)


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


def write_3mf(path, name, part, mods, settings):
    """PrusaSlicer 3MF: one object, the part as a ModelPart volume and each ring as a ParameterModifier volume that
    carries `settings`. Same file layout as slice.py write_3mf (geometry and per-volume settings only; the print
    config comes from --load)."""
    vols = [(name, part, "ModelPart", {})] + [("%s_ring_%02d" % (k, i), m, "ParameterModifier", settings) for i, (k, m) in enumerate(mods)]
    V, F, ranges, off, nf = [], [], [], 0, 0
    for nm, m, typ, s in vols:
        V.append(np.asarray(m.vertices)); F.append(np.asarray(m.faces) + off)
        ranges.append((nf, nf + len(m.faces) - 1)); off += len(m.vertices); nf += len(m.faces)
    V = np.vstack(V); F = np.vstack(F)
    model = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:slic3rpe="http://schemas.slic3r.org/3mf/2017/06">',
             ' <metadata name="slic3rpe:Version3mf">1</metadata>', ' <resources>', '  <object id="1" type="model"><mesh><vertices>']
    model += ['<vertex x="%.5f" y="%.5f" z="%.5f"/>' % tuple(v) for v in V]
    model.append("</vertices><triangles>")
    model += ['<triangle v1="%d" v2="%d" v3="%d"/>' % tuple(t) for t in F]
    model += ["</triangles></mesh></object>", " </resources>", " <build>",
              '  <item objectid="1" transform="1 0 0 0 1 0 0 0 1 0 0 0" printable="1"/>', " </build>", "</model>"]
    cfg = ['<?xml version="1.0" encoding="UTF-8"?>', "<config>", ' <object id="1" instances_count="1">',
           '  <metadata type="object" key="name" value=%s/>' % quoteattr(name)]
    for (nm, m, typ, s), (f0, f1) in zip(vols, ranges):
        cfg.append('  <volume firstid="%d" lastid="%d">' % (f0, f1))
        cfg.append('   <metadata type="volume" key="name" value=%s/>' % quoteattr(nm))
        cfg.append('   <metadata type="volume" key="volume_type" value="%s"/>' % typ)
        if typ != "ModelPart":
            cfg.append('   <metadata type="volume" key="modifier" value="1"/>')
        for k, v in s.items():
            cfg.append('   <metadata type="volume" key=%s value=%s/>' % (quoteattr(k), quoteattr(v)))
        cfg.append("  </volume>")
    cfg += [" </object>", "</config>"]
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


# ---------------------------------------------------------------------------------------------------------------
# slicing
# ---------------------------------------------------------------------------------------------------------------
def run_slicer(inp, cfgs, gcode):
    cmd = [S.SLICER, "--export-gcode", "--loglevel", "1", "--threads", THREADS]
    for c in cfgs:
        cmd += ["--load", c]
    cmd += ["-o", gcode, inp]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(gcode):
        raise RuntimeError("slicer failed: %s\n%s" % (" ".join(cmd), r.stdout[-2000:] + r.stderr[-2000:]))
    return [l for l in (r.stdout + r.stderr).splitlines() if "error" in l.lower() or "warning" in l.lower()]


def cmd_slice(a):
    v = a.variant
    odir = os.path.join(a.out, "oriented")
    gdir = os.path.join(a.out, "gcode_%s" % v); os.makedirs(gdir, exist_ok=True)
    rpath = os.path.join(a.out, "results_%s.json" % v)
    res = json.load(open(rpath)) if os.path.exists(rpath) else {}
    holes = json.load(open(os.path.join(a.out, "holes.json"))) if v in ("c", "d") else None
    ring_set = read_ini(os.path.join(CFG_L, "mod_ring.ini"))
    keep = set(a.only.split(",")) if a.only else None
    for p in parts():
        if (keep and p["stl"] not in keep) or (v == "d" and p["stl"] not in D_PARTS):
            continue
        src = S.oriented(p["stl"], p["up"], odir)
        cfgs = stack(v, p)
        kinds = ring_kinds(v, p)
        g = os.path.join(gdir, p["stl"].replace(".stl", ".gcode"))
        t = time.time()
        if kinds:
            mods = ring_meshes(holes[p["stl"]], kinds)
            inp = os.path.join(gdir, p["stl"].replace(".stl", ".3mf"))
            write_3mf(inp, p["stl"][:-4], trimesh.load(src), mods, ring_set)
        else:
            mods, inp = [], src
        warn = run_slicer(inp, cfgs, g)
        r = S.parse_gcode(g, S.DENSITY[p["material"]])
        r.update(qty=p["qty"], material=p["material"], variant=v, settings=[os.path.relpath(c, REPO) for c in cfgs],
                 rings={k: sum(1 for kk, _ in mods if kk == k) for k in kinds}, slicer_messages=warn,
                 overrides=(p["overrides"] if v == "b" else ("" if v == "a" else stack_overrides(v, p))))
        for k in ("xy_all", "xy_model", "xy_nos"):
            r.pop(k, None)
        res[p["stl"]] = r
        print("%s %-30s %7.2f g  net %7.2f g  %6.2f h  rings %s  (%.0f s)" % (
            v, p["stl"], r["g"], r["g"] - r["g_support"], r["s"] / 3600, r["rings"] or "-", time.time() - t), flush=True)
        json.dump(res, open(rpath, "w"), indent=1, sort_keys=True)


def gcode_moves(path):
    """extrusion segments of the model (no skirt, no support): [(type, x0, y0, x1, y1, z_mid, e)] and the model XY extent"""
    segs, typ, z, hgt, x, y = [], None, 0.0, 0.2, None, None
    num = lambda line, k: (lambda m: float(m.group(1)) if m else None)(re.search(r" %s(-?[\d.]+)" % k, line))
    with open(path) as f:
        for line in f:
            if line.startswith(";TYPE:"):
                typ = line[6:].strip()
            elif line.startswith(";Z:"):
                z = float(line[3:])
            elif line.startswith(";HEIGHT:"):
                hgt = float(line[8:])
            elif line.startswith("G1 "):
                nx, ny, e = num(line, "X"), num(line, "Y"), num(line, "E")
                if e and e > 0 and (nx is not None or ny is not None) and x is not None and typ and \
                        typ != "Skirt/Brim" and not typ.startswith("Support material"):
                    segs.append((typ, x, y, nx if nx is not None else x, ny if ny is not None else y, z - hgt / 2, e))
                x = nx if nx is not None else x
                y = ny if ny is not None else y
    a = np.array([(s[1], s[2]) for s in segs] + [(s[3], s[4]) for s in segs])
    return segs, (a[:, 0].min(), a[:, 0].max(), a[:, 1].min(), a[:, 1].max())


def band_material(m, h, need, n=3000, seed=1):
    """volume (mm3) of part material in the band round a hole: 0.15 mm off the hole wall out to `need`, along the hole"""
    rng = np.random.default_rng(seed)
    r0, r1 = h["d"] / 2 + 0.15, h["d"] / 2 + need
    r = np.sqrt(rng.uniform(r0 ** 2, r1 ** 2, n)); t = rng.uniform(0, 2 * np.pi, n); s = rng.uniform(h["z0"], h["z1"], n)
    ax = h["axis"]; o = [i for i in range(3) if i != ax]
    P = np.zeros((n, 3)); P[:, ax] = s; P[:, o[0]] = h["c"][o[0]] + r * np.cos(t); P[:, o[1]] = h["c"][o[1]] + r * np.sin(t)
    return float(np.pi * (r1 ** 2 - r0 ** 2) * (h["z1"] - h["z0"]) * m.contains(P).mean())


def cmd_rings(a):
    """Solidity next to each ringed hole of variant c, in the G-code of variants a, b and c of the same part: filament
    laid in the band from 0.15 mm off the hole wall out to the distance the rule asks for (NEED), divided by the part
    material in that band (mesh sampled). About 1 means solid; 15 % infill in the band shows as well under 1.
    Extrusion type labels are also kept, but PrusaSlicer labels a large region at 100 % infill "Internal infill",
    so the labels alone cannot tell sparse from solid."""
    holes = json.load(open(os.path.join(a.out, "holes.json")))
    area = math.pi * (S.FIL_DIA / 2) ** 2
    out = {}
    for p in parts():
        rv = "d" if p["stl"] in D_PARTS else "c"          # the variant whose G-code has this part's rings
        kinds = ring_kinds(rv, p)
        if not kinds or (a.only and p["stl"] not in a.only.split(",")):
            continue
        m = trimesh.load(os.path.join(a.out, "oriented", p["stl"]))
        rings = [(k, h) for k in kinds for h in holes[p["stl"]][k]]
        vol = {}
        for k, h in rings:
            vol[k] = vol.get(k, 0.0) + band_material(m, h, NEED[k])
        out[p["stl"]] = {"band_material_mm3": vol}
        for v in ("a", "b", rv):
            segs, ext = gcode_moves(os.path.join(a.out, "gcode_%s" % v, p["stl"].replace(".stl", ".gcode")))
            off = np.array([(ext[0] + ext[1]) / 2 - (m.bounds[0][0] + m.bounds[1][0]) / 2,
                            (ext[2] + ext[3]) / 2 - (m.bounds[0][1] + m.bounds[1][1]) / 2, 0.0])
            # sample every extrusion every 0.5 mm (filament shared out evenly), so long lines crossing a band count too
            A = np.array([(s[1], s[2], s[3], s[4], s[5], s[6]) for s in segs])
            n = np.maximum(1, np.ceil(np.hypot(A[:, 2] - A[:, 0], A[:, 3] - A[:, 1]) / 0.5)).astype(int)
            idx = np.repeat(np.arange(len(A)), n)
            frac = (np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n) + 0.5) / np.repeat(n, n)
            S_ = np.c_[A[idx, 0] + frac * (A[idx, 2] - A[idx, 0]), A[idx, 1] + frac * (A[idx, 3] - A[idx, 1]), A[idx, 4]] - off
            E = A[idx, 5] / np.repeat(n, n)
            T = np.array([s[0] for s in segs])[idx]
            by = {}
            for k, h in rings:
                ax = h["axis"]; c = np.array(h["c"], float)
                d = S_ - c; d[:, ax] = 0.0
                r = np.linalg.norm(d, axis=1)
                inside = (S_[:, ax] >= h["z0"]) & (S_[:, ax] <= h["z1"]) & (r > h["d"] / 2 + 0.15) & (r < h["d"] / 2 + NEED[k])
                d_ = by.setdefault(k, {"filament_mm3": 0.0})
                d_["filament_mm3"] += float(E[inside].sum()) * area
                for t in set(T[inside]):
                    grp = "walls" if "perimeter" in t.lower() else ("labelled internal infill" if t == "Internal infill" else "labelled solid infill or gap fill")
                    d_[grp] = d_.get(grp, 0.0) + float(E[inside & (T == t)].sum()) * area
            for k in by:
                by[k]["solidity"] = by[k]["filament_mm3"] / vol[k] if vol[k] > 0 else None
            out[p["stl"]][v] = by
            print("%-24s %s %s" % (p["stl"], v, "  ".join("%s solidity %.2f (filament %.0f of %.0f mm3)" % (
                k, d_["solidity"], d_["filament_mm3"], vol[k]) for k, d_ in by.items())), flush=True)
    json.dump(out, open(os.path.join(a.out, "rings_check.json"), "w"), indent=1)


def cmd_coupons(a):
    """Light copies of the coupons whose source part gets rings in variant c (COUPON_DIR from make_coupons.py):
    config_light base, the source part's parts_light.csv overrides, rings found in the coupon itself."""
    man = json.load(open(os.path.join(a.coupons, "manifest.json")))
    L = light()
    ring_set = read_ini(os.path.join(CFG_L, "mod_ring.ini"))
    gdir = os.path.join(a.out, "gcode_coupons_light"); os.makedirs(gdir, exist_ok=True)
    out = {}
    for c in man["coupons"]:
        lr = L.get(c["source"])
        if not lr or not lr["rings"]:
            continue
        src = os.path.join(a.coupons, c["file"])
        m = trimesh.load(src)
        kinds = [k for k in lr["rings"].split("+") if k]
        hl = classify(find_holes(m))
        mods = ring_meshes(hl, kinds)
        p = dict(stl=c["source"], material=c["material"])
        cfgs = stack("c", p)
        f3 = os.path.join(gdir, c["file"].replace(".stl", "_light.3mf"))
        write_3mf(f3, c["id"] + "_light", m, mods, ring_set)
        g = f3.replace(".3mf", ".gcode")
        run_slicer(f3, cfgs, g)
        r = S.parse_gcode(g, S.DENSITY[c["material"]])
        out[c["id"]] = dict(file=c["file"], source=c["source"], g=r["g"], min=r["s"] / 60, g_support=r["g_support"],
                            rings={k: sum(1 for kk, _ in mods if kk == k) for k in kinds}, settings=[os.path.relpath(x, REPO) for x in cfgs])
        print("%-4s light: %.2f g  %.0f min  rings %s" % (c["id"], r["g"], r["s"] / 60, out[c["id"]]["rings"]), flush=True)
    json.dump(out, open(os.path.join(a.out, "coupons_light.json"), "w"), indent=1)


# ---------------------------------------------------------------------------------------------------------------
# whole robot: the sim agent's method (sim/mass_budget.py), only the slice table swapped
# ---------------------------------------------------------------------------------------------------------------
def slice_rows(out, v):
    """rows in the form sim/mass_budget.py load_slice_summary() returns: {part: dict(qty, material, g_each, support_each)}"""
    R = json.load(open(os.path.join(out, "results_%s.json" % ("c" if v == "d" else v))))
    if v == "d":
        R.update(json.load(open(os.path.join(out, "results_d.json"))))
    return {stl[:-4]: dict(qty=r["qty"], material=r["material"], g_each=r["g"], support_each=r["g_support"]) for stl, r in R.items()}


def c0_rows(out):
    """variant c without modifier rings: the ring parts keep their variant b settings (whole-part walls)"""
    rb, rc = slice_rows(out, "b"), slice_rows(out, "c")
    L = light()
    return {k: (rb[k] if L[k + ".stl"]["rings"] else rc[k]) for k in rc}


def load_mb():
    sys.path.insert(0, SIM)
    import mass_budget as MB
    return MB


def cmd_budget(a):
    MB = load_mb()
    orig = MB.load_slice_summary
    model = MB.model_inertials()
    sets = [("SLICE_SUMMARY (check)", orig())] + [(v, slice_rows(a.out, v)) for v in ("a", "b", "c", "d")] + [("c0", c0_rows(a.out))]
    out = {"model": {}, "variants": {}}
    for pose in ("zero", "home"):
        cm, Mm, feet = MB.robot_com(model, "home" if pose == "home" else None)
        out["model"][pose] = dict(com_mm=(cm * 1000).tolist(), kg=Mm, feet_mm=(np.array(feet) * 1000).tolist())
    out["model"]["links"] = {b: dict(g=model[b].m * 1000, com_mm=(model[b].c * 1000).tolist()) for b in MB.BODIES}
    for name, rows in sets:
        MB.load_slice_summary = lambda rows=rows: rows
        B = MB.build_budget()
        L = B["links"]
        rec = dict(total_g=sum(x.m for x in L.values()) * 1000,
                   printed_g=sum(i.mass_g for i in B["items"] if i.cat == "printed"),
                   links={b: dict(g=L[b].m * 1000, com_mm=(L[b].c * 1000).tolist(),
                                  printed_g=sum(i.mass_g for i in B["items"] if i.link == b and i.cat == "printed")) for b in MB.BODIES})
        for pose in ("zero", "home"):
            c, M, feet = MB.robot_com(L, "home" if pose == "home" else None)
            rec[pose] = dict(com_mm=(c * 1000).tolist(), kg=M, feet_mm=(np.array(feet) * 1000).tolist())
        ev = lambda I: np.linalg.eigvalsh(I).tolist()
        rec["inertia_1e-4"] = {b: [x * 1e4 for x in ev(L[b].I)] for b in ("trunk_assembly", "head_assembly")}
        out["variants"][name] = rec
        print("%-22s total %7.1f g  printed %7.1f g  home CoM %s mm" % (name, rec["total_g"], rec["printed_g"],
                                                                         np.round(rec["home"]["com_mm"], 2).tolist()), flush=True)
    MB.load_slice_summary = orig
    out["model"]["inertia_1e-4"] = {b: [x * 1e4 for x in np.linalg.eigvalsh(model[b].I)] for b in ("trunk_assembly", "head_assembly")}
    json.dump(out, open(os.path.join(a.out, "budget.json"), "w"), indent=1)


# ---------------------------------------------------------------------------------------------------------------
# walk: the sim agent's cases on the robot with variant c parts (sim pass only)
# ---------------------------------------------------------------------------------------------------------------
def MODEL_ROWS(out):
    """slice tables of the robots the walk check runs: (b), (c), (d) = (c) with the light head, (a)"""
    return {"ours_b": slice_rows(out, "b"), "light_c": slice_rows(out, "c"), "light_d": slice_rows(out, "d"), "upstream_a": slice_rows(out, "a")}


def cmd_walk(a):
    os.environ.setdefault("ODM_SCRATCH", os.path.join(a.out, "sim"))
    sys.path.insert(0, SIM)
    import added_mass_sim as AMS                          # unchanged; writes only to ODM_SCRATCH
    MB = AMS.MB
    orig = MB.load_slice_summary
    V = {"stock": AMS.write_variant("stock", MB.model_inertials())}
    for name, rows in MODEL_ROWS(a.out).items():
        MB.load_slice_summary = lambda rows=rows: rows
        V[name] = AMS.write_variant(name, MB.build_budget()["links"])
    wpath = os.path.join(a.out, "walk.json")
    W = json.load(open(wpath)) if os.path.exists(wpath) else {}
    if a.mode == "comback":
        # sim/added_mass_sim.py run_com_back on our robot with variant b or c parts: trunk centre of mass moved back by
        # dx, stand 10 s and walk forward 12 s from the upstream start, seeds none and 1 to 3 (same cases, same fall rule)
        import copy
        for vn in a.models.split(","):
            MB.load_slice_summary = lambda vn=vn: MODEL_ROWS(a.out)[vn]
            base = MB.build_budget()["links"]
            MB.load_slice_summary = orig
            for dx in [float(x) for x in a.dx.split(",")]:
                Lk = {k: copy.deepcopy(v) for k, v in base.items()}
                Lk["trunk_assembly"].c = Lk["trunk_assembly"].c + np.array([dx / 1000, 0, 0])
                folder = AMS.write_variant("%s_trunkcom%+g" % (vn, dx), Lk)
                for (label, cmd, dur), dz in [(c, z) for z in a.start_dz for c in (("stand", [0, 0, 0], 10.0), ("walk_forward", [0.15, 0, 0], 12.0))]:
                    key = "comback|%s|%+g|%s" % (vn, dx, label) + ("" if dz == 0 else "|raised%g" % (dz * 1000))
                    if key in W:
                        continue
                    fl = []
                    for sd in (None, 1, 2, 3):
                        res = AMS.run(folder, "scene_flat_terrain.xml", AMS.CB.sched_const(cmd + [0, 0, 0, 0]), dur, None, dz, seed=sd)
                        fl.append(res["falls"][0] if res["falls"] else None)
                    W[key] = dict(falls=fl, trunk_g=base["trunk_assembly"].m * 1000, robot_g=sum(x.m for x in base.values()) * 1000)
                    print("com back %-8s %+5.1f mm %-12s start +%.0f mm falls at %s" % (vn, dx, label, dz * 1000, fl), flush=True)
                    json.dump(W, open(wpath, "w"), indent=1)
        return
    MB.load_slice_summary = orig
    names = a.models.split(",")
    cases = [c for c in AMS.CASES if c[0] in a.cases.split(",")]
    seeds = [None] + list(range(1, a.seeds + 1))
    for vn in names:
        for label, scene, sch, dur, pushes, dz in cases:
            for sd in seeds:
                key = "%s|%s|%s" % (vn, label, sd)
                if key in W:
                    continue
                t = time.time()
                res = AMS.run(V[vn], scene, sch, dur, pushes, dz, seed=sd, xy_range=2.0 if (sd and "rough" in label) else 0.0)
                g = AMS.gait_stats(res, AMS.CMD[label])
                W[key] = dict(falls=res["falls"], track_lin=g.get("track_lin"), track_yaw=g.get("track_yaw"), vx=g.get("vx"),
                              vy=g.get("vy"), wz=g.get("wz"), pitch_mean_deg=g.get("pitch_mean_deg"), roll_rms_deg=g.get("roll_rms_deg"))
                print("%-8s %-34s seed %-4s falls %s track %s pitch %.1f (%.0f s)" % (
                    vn, label, sd, res["falls"], W[key]["track_lin"] if W[key]["track_lin"] is not None else W[key]["track_yaw"],
                    W[key]["pitch_mean_deg"] or 0, time.time() - t), flush=True)
                json.dump(W, open(wpath, "w"), indent=1)


# ---------------------------------------------------------------------------------------------------------------
# tables
# ---------------------------------------------------------------------------------------------------------------
def trained_part_masses():
    """MASS_BUDGET.md table 4: the trained model's own part masses (fit), legs and neck. {print stl: [g, ...]}"""
    name = {"left_knee_to_ankle_right_sheet": "knee_to_ankle_right_sheet", "left_knee_to_ankle_left_sheet": "knee_to_ankle_left_sheet"}
    out, on = {}, False
    for line in open(os.path.join(SIM, "MASS_BUDGET.md")):
        if line.startswith("## "):
            on = line.startswith("## Table 4")
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if on and len(c) == 5 and c[1] and not c[1].startswith("servo") and c[1] != "Part" and not set(c[1]) <= set("-"):
            out.setdefault(name.get(c[1], c[1]) + ".stl", []).append(float(c[2]))
    for l, r in (("left_cache", "right_cache"), ("left_roll_to_pitch", "right_roll_to_pitch")):
        out[r + ".stl"] = out[l + ".stl"]                 # the trained right leg links are mirror copies (table 2)
    return out


def cmd_tables(a):
    P = parts()
    R = {v: json.load(open(os.path.join(a.out, "results_%s.json" % v))) for v in ("a", "b", "c")}
    TM = trained_part_masses()
    L = light()
    lines = []
    w = lines.append
    w("| STL | Qty | Trained model g [L] | (a) g | (a) on robot g | (a) h | (b) g | (b) on robot g | (b) h | (c) g | (c) on robot g | (c) h | (c) settings |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    tot = {v: {} for v in R}
    for p in P:
        s = p["stl"]
        cells = []
        for v in ("a", "b", "c"):
            r = R[v][s]
            cells += ["%.2f" % r["g"], "%.2f" % (r["g"] - r["g_support"]), "%.2f" % (r["s"] / 3600)]
            t = tot[v].setdefault(p["material"], [0, 0.0, 0.0, 0.0])
            t[0] += p["qty"]; t[1] += p["qty"] * r["g"]; t[2] += p["qty"] * (r["g"] - r["g_support"]); t[3] += p["qty"] * r["s"]
        rc = R["c"][s]
        sett = "+".join(x for x in [L[s]["overrides"]] if x) or "base"
        if rc.get("rings"):
            sett += ", rings " + ", ".join("%d %s" % (n, k) for k, n in rc["rings"].items())
        tm = " / ".join("%.1f" % x for x in TM.get(s, [])) or "-"
        w("| %s | %d | %s | %s | %s |" % (s, p["qty"], tm, " | ".join(cells), sett))
    w("")
    w("| Material | Parts | (a) g | (a) on robot g | (a) h | (b) g | (b) on robot g | (b) h | (c) g | (c) on robot g | (c) h |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for m in ("PLA", "TPU", "all"):
        cells = []
        for v in ("a", "b", "c"):
            ts = list(tot[v].values()) if m == "all" else [tot[v][m]]
            cells += ["%.1f" % sum(t[1] for t in ts), "%.1f" % sum(t[2] for t in ts), "%.1f" % (sum(t[3] for t in ts) / 3600)]
        n = sum(t[0] for t in (tot["a"].values() if m == "all" else [tot["a"][m]]))
        w("| %s | %d | %s |" % (m, n, " | ".join(cells)))
    # c0: rings dropped, ring parts at their variant b settings
    c0 = sum(p["qty"] * ((R["b"] if L[p["stl"]]["rings"] else R["c"])[p["stl"]]["g"]) for p in P)
    c0n = sum(p["qty"] * ((lambda r: r["g"] - r["g_support"])((R["b"] if L[p["stl"]]["rings"] else R["c"])[p["stl"]])) for p in P)
    c0h = sum(p["qty"] * ((R["b"] if L[p["stl"]]["rings"] else R["c"])[p["stl"]]["s"]) for p in P) / 3600
    w("")
    w("c0 (variant c with no rings; the ring parts keep their variant b settings): %.1f g, on robot %.1f g, %.1f h" % (c0, c0n, c0h))
    # check of variant b against SLICE_SUMMARY.md
    MBrows = None
    try:
        MB = load_mb(); MBrows = MB.load_slice_summary()
    except Exception as e:
        w("SLICE_SUMMARY check skipped: %s" % e)
    if MBrows:
        dg = max(abs(R["b"][k + ".stl"]["g"] - r["g_each"]) for k, r in MBrows.items())
        ds = max(abs(R["b"][k + ".stl"]["g_support"] - r["support_each"]) for k, r in MBrows.items())
        w("Variant b against print/SLICE_SUMMARY.md: largest difference %.2f g per part (support %.2f g)." % (dg, ds))
    bj = os.path.join(a.out, "budget.json")
    if os.path.exists(bj):
        B = json.load(open(bj))
        mo = B["model"]
        w("")
        SHORT = getattr(MB, "SHORT", {}) if MBrows else {}
        w("| Link (MJCF body) | Trained g [U] | (b) g | (c) g | (c) - (b) g | (c) - trained g | (b) printed g | (c) printed g |")
        w("|---|---|---|---|---|---|---|---|")
        vb, vc = B["variants"]["b"], B["variants"]["c"]
        for b, lm in mo["links"].items():
            w("| %s | %.1f | %.1f | %.1f | %+.1f | %+.1f | %.1f | %.1f |" % (SHORT.get(b, b), lm["g"], vb["links"][b]["g"], vc["links"][b]["g"],
                                                                     vc["links"][b]["g"] - vb["links"][b]["g"], vc["links"][b]["g"] - lm["g"],
                                                                     vb["links"][b]["printed_g"], vc["links"][b]["printed_g"]))
        tm = sum(x["g"] for x in mo["links"].values())
        pr = lambda v: sum(t[2] for t in tot[v].values())          # same sum as the per-part totals above
        w("| total | %.1f | %.1f | %.1f | %+.1f | %+.1f | %.1f | %.1f |" % (tm, vb["total_g"], vc["total_g"], vc["total_g"] - vb["total_g"],
                                                                     vc["total_g"] - tm, pr("b"), pr("c")))
        w("")
        w("| Variant | Robot g | vs trained | Home pose CoM mm (trunk frame) | CoM - trained mm | CoM - (b) mm | Zero pose CoM mm |")
        w("|---|---|---|---|---|---|---|")
        cmh = np.array(mo["home"]["com_mm"]); cbh = np.array(B["variants"]["b"]["home"]["com_mm"])
        w("| trained | %.1f | - | %s | - | - | %s |" % (mo["home"]["kg"] * 1000, np.round(cmh, 1).tolist(), np.round(mo["zero"]["com_mm"], 1).tolist()))
        for name, rec in B["variants"].items():
            ch = np.array(rec["home"]["com_mm"])
            w("| %s | %.1f | %+.1f %% | %s | %s | %s | %s |" % (name, rec["total_g"], (rec["total_g"] / (mo["home"]["kg"] * 1000) - 1) * 100,
                                                          np.round(ch, 1).tolist(), np.round(ch - cmh, 1).tolist(), np.round(ch - cbh, 1).tolist(),
                                                          np.round(rec["zero"]["com_mm"], 1).tolist()))
        w("")
        w("Foot sites at the home pose (trained model, trunk frame, mm): %s" % np.round(mo["home"]["feet_mm"], 1).tolist())
        for name in ("b", "c"):
            r = B["variants"][name]
            w("Variant %s: trunk inertia %s, head inertia %s (principal, kg m2 x 1e-4); trained trunk %s, head %s" % (
                name, np.round(r["inertia_1e-4"]["trunk_assembly"], 2).tolist(), np.round(r["inertia_1e-4"]["head_assembly"], 2).tolist(),
                np.round(mo["inertia_1e-4"]["trunk_assembly"], 2).tolist(), np.round(mo["inertia_1e-4"]["head_assembly"], 2).tolist()))
    wj = os.path.join(a.out, "walk.json")
    if os.path.exists(wj):
        W = json.load(open(wj))
        models = [m for m in ("stock", "ours_b", "light_c", "light_d", "upstream_a") if any(k.startswith(m + "|") for k in W)]
        cases = []
        for k in W:
            if not k.startswith("comback|") and k.split("|")[1] not in cases:
                cases.append(k.split("|")[1])
        tr = lambda r: r["track_lin"] if r.get("track_lin") is not None else r.get("track_yaw")
        w("")
        w("| Case (nominal run) | " + " | ".join(models) + " |")
        w("|---|" + "---|" * len(models))
        for c in cases:
            cells = []
            for m in models:
                r = W.get("%s|%s|None" % (m, c))
                cells.append("-" if r is None else ("fell at %s s" % r["falls"][0] if r["falls"] else
                             "%.2f, pitch %+.1f deg" % (tr(r), r["pitch_mean_deg"])))
            w("| %s | %s |" % (c, " | ".join(cells)))
        w("")
        w("| Case (seeds 1 to 6) | Model | Runs that fell | First fall (s) | Tracking mean (min to max), runs that did not fall |")
        w("|---|---|---|---|---|")
        for c in cases:
            for m in models:
                rs = [W[k] for k in W if k.startswith("%s|%s|" % (m, c)) and not k.endswith("|None")]
                if not rs:
                    continue
                fl = [[f for f in r["falls"] if f > 1.0] for r in rs]      # added_mass_sim.run_seeds counts falls after 1 s
                ok = [tr(r) for r, f in zip(rs, fl) if not f]
                w("| %s | %s | %d of %d | %s | %s |" % (c, m, sum(1 for f in fl if f), len(rs), ", ".join("%.1f" % f[0] for f in fl if f) or "-",
                                                   ("%.2f (%.2f to %.2f)" % (np.mean(ok), min(ok), max(ok))) if ok else "-"))
        cb = {k: v for k, v in W.items() if k.startswith("comback|")}
        if cb and os.path.exists(bj):
            B = json.load(open(bj))
            feet = lambda v: sum(f[0] for f in B["variants"][v]["home"]["feet_mm"]) / 2
            w("")
            w("| Model | Trunk CoM moved mm | Robot CoM moved mm | Robot CoM ahead of the foot sites mm | Stand, upstream start: falls (s), runs none, 1, 2, 3 | Walk, upstream start | Stand, start raised 12 mm | Walk, start raised 12 mm |")
            w("|---|---|---|---|---|---|---|---|")
            f = lambda r: "-" if r is None else ", ".join("none" if x is None else "%.2f" % x for x in r["falls"])
            for m, v in (("ours_b", "b"), ("light_c", "c"), ("light_d", "d"), ("upstream_a", "a")):
                if v not in B["variants"]:
                    continue
                dxs = sorted({float(k.split("|")[2]) for k in cb if k.split("|")[1] == m}, reverse=True)
                for dx in dxs:
                    g = lambda lab, sfx="": cb.get("comback|%s|%+g|%s%s" % (m, dx, lab, sfx))
                    any_ = next(r for r in (g("stand"), g("stand", "|raised12")) if r)
                    ratio = any_["trunk_g"] / any_["robot_g"]
                    ahead = B["variants"][v]["home"]["com_mm"][0] + dx * ratio - feet(v)
                    w("| %s | %+.1f | %+.1f | %.1f | %s | %s | %s | %s |" % (m, dx, dx * ratio, ahead, f(g("stand")), f(g("walk_forward")),
                                                                     f(g("stand", "|raised12")), f(g("walk_forward", "|raised12"))))
    txt = "\n".join(lines) + "\n"
    open(os.path.join(a.out, "mass_study_tables.md"), "w").write(txt)
    if a.md:
        open(a.md, "w").write(txt)
    print(txt)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    for n in ("holes", "slice", "rings", "coupons", "budget", "walk", "tables"):
        s = sp.add_parser(n)
        s.add_argument("--out", required=True, help="output folder outside the repo")
        if n == "slice":
            s.add_argument("--variant", required=True, choices=["a", "b", "c", "d"])
        if n in ("slice", "rings"):
            s.add_argument("--only", default="")
        if n == "coupons":
            s.add_argument("--coupons", required=True, help="folder written by make_coupons.py")
        if n == "walk":
            s.add_argument("--mode", default="cases", choices=["cases", "comback"])
            s.add_argument("--models", default="ours_b,light_c")
            s.add_argument("--cases", default="walk_forward_0.15,turn_1.0,walk_side_0.2,walk_backlash")
            s.add_argument("--seeds", type=int, default=0)
            s.add_argument("--dx", default="-10,-12.5,-15,-17.5", help="comback: trunk CoM shifts, mm")
            s.add_argument("--start_dz", default="0", help="comback: start raised by these, m (sim agent: 0 and 0.012)")
        if n == "tables":
            s.add_argument("--md", default="")
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    if out == REPO or out.startswith(REPO + os.sep):
        sys.exit("--out must be outside the repo (no G-code, 3MF or CAD exports in git)")
    os.makedirs(out, exist_ok=True)
    a.out = out
    if hasattr(a, "start_dz"):
        a.start_dz = [float(x) for x in a.start_dz.split(",")]
    dict(holes=cmd_holes, slice=cmd_slice, rings=cmd_rings, coupons=cmd_coupons, budget=cmd_budget, walk=cmd_walk,
         tables=cmd_tables)[a.cmd](a)


if __name__ == "__main__":
    main()
