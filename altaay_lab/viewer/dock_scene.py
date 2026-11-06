"""Dock and docked scenes for the viewer (called by make_viewer_data.py --scene dock | docked).

dock:   <out>/dock.glb, dock.glb.txt, dock_manifest.json: every component of twin/dock/dock_assembly.py ("dock" state),
        every screw, nut and insert of twin/dock/dock_fasteners.json, every wire of twin/dock/dock_cables3d.json, the parts
        panel from twin/dock/dock_bom.json, in the manifest schema of the duck scene (the page draws them the same way).
docked: <out>/docked.glb, docked.glb.txt, docked_manifest.json: the dock in its "docked" state and the duck of the duck
        scene (<out>/duck.glb and manifest.json, written first by a plain make_viewer_data.py run into the same folder)
        moved onto the seat by the sim pose of twin/dock/docked_pose.json: each duck node keeps its zero-pose mesh and gets
        T_dock(link) x T_zero(link)^-1. The duck's own cables stay in the duck scene.
Frame: the dock frame of twin/dock/dock_parts.py (x toward the mast, z up, mm): the GLB root turns it y-up like the duck.
"""
import base64, json, os, struct, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
REPO = os.path.dirname(LAB)
DOCK = os.path.join(LAB, "twin", "dock")
sys.path.insert(0, DOCK)

WIRE_HEX = {"red": "#d62728", "black": "#2b2b2b", "white": "#e8e8e8", "yellow": "#e6c229", "blue": "#1f5fd6", "green": "#2ca02c"}
CATS = {"pla": ("Printed PLA", "#c5b9a3"), "electronics": ("Electronics / PCB", "#4f9f3a"), "metal": ("Rods, springs, ballast", "#93a1b0"),
        "screw": ("Screw", "#8f9aa5"), "insert": ("M3 insert", "#d3a62c"), "connector": ("Nuts, jack, plug, feet, tags", "#f2f2ee"),
        "cable": ("Cable", "#e07a1f"), "other": ("Other modelled part", "#7c6a58")}
SUBS = {"seat": ("Seat", "dock", [-110, 0, 0]), "spine": ("Spine", "dock", [-55, 0, 0]), "paddle": ("Paddle and pins", "dock", [-95, 0, 25]),
        "spring": ("Paddle springs and rods", "dock", [10, 0, 95]), "mast": ("Mast and base", "dock", [55, 0, 0]),
        "bay": ("Electronics bay", "dock", [120, 0, -10])}


def sub_of(c):
    i = c["id"]
    if i.startswith(("dock_seat", "seat_spring", "switch")) or i in ("foot_1", "foot_2", "foot_3", "foot_4"):
        return "seat"
    if i == "dock_spine":
        return "spine"
    if i.startswith(("dock_paddle", "pin_")):
        return "paddle"
    if i.startswith(("dock_spring", "rod_", "cf_")):
        return "spring"
    if c["group"] == "bay" or i.startswith(("dock_bay", "gate_", "vhb_")):
        return "bay"
    return "mast"


def cat_of(c):
    i = c["id"]
    if c["kind"] == "printed":
        return "pla"
    if i.startswith(("rod_", "cf_", "seat_spring", "ballast_")):
        return "metal"
    if i in ("evm", "swg", "perf", "switch", "fuse_holder") or i.startswith(("gate_", "pin_")):
        return "electronics"
    return "connector"


def v2_of(c):
    i = c["id"]
    return {"dock_seat_top": [0, 0, 55], "dock_bay_lid": [0, 0, 70], "evm": [0, 0, 35], "swg": [0, 0, 35], "fuse_holder": [0, 0, 35],
            "perf": [0, 0, 45]}.get(i, [0, 0, 45] if i.startswith("gate_") else [0, 0, -25] if i.startswith("foot_") else
            [0, 0, 30] if i.startswith("ballast_") else [-12, 0, 0] if i.startswith("pin_") else [0, 0, 0])


def geom_of(m, name):
    return dict(name=name, pos=np.asarray(m.vertices, np.float32), idx=np.asarray(m.faces, np.uint32))


def screw_mesh(d, L, dk, k):
    import trimesh
    a = trimesh.creation.cylinder(radius=d / 2, height=L, sections=14); a.apply_translation((0, 0, L / 2))
    h = trimesh.creation.cylinder(radius=dk / 2, height=k, sections=14); h.apply_translation((0, 0, -k / 2))
    return trimesh.util.concatenate([a, h])


def dock_parts(state):
    """(geoms, nodes, man_nodes) for every dock component and fastener"""
    import trimesh
    import dock_assembly as DA
    comps = DA.components(state)
    geoms, nodes, man = [], [], {}
    for c in comps:
        nid = "dock-" + c["id"]
        geoms.append(geom_of(c["mesh"], nid)); nodes.append(dict(name=nid, mesh=len(geoms) - 1, matrix=np.eye(4)))
        sub = sub_of(c)
        man[nid] = dict(label=c["label"], part=c["id"], file="twin/dock/stl/%s.stl" % c["id"].rsplit("_", 1)[0] if c["kind"] == "printed" and c["id"][-2:] in ("_l", "_r") and "spring" in c["id"] else
                        ("twin/dock/stl/%s.stl" % c["id"] if c["kind"] == "printed" else "(drawn) " + c["label"]),
                        link="dock", sub=sub, category=cat_of(c), status="OK", blockers=[], mount=c["mount"], v2=v2_of(c), qty=1,
                        material="PLA, light profile" if c["kind"] == "printed" else "", bom=c["bom"], source=c["src"])
    F = json.load(open(os.path.join(DOCK, "dock_fasteners.json")))["fasteners"]
    for f in F:
        T = np.array(f["pose_dock"], float)
        nid = "dock-" + f["id"]
        if f["kind"] == "screw":
            m = screw_mesh(f["d"], f["length_mm"], f["head"]["dk"], f["head"]["k"]); cat = "screw"
            lab = "%s: %s into %s" % (f["spec"], f["part"], f["into"])
        elif f["kind"] == "insert":
            m = trimesh.creation.cylinder(radius=2.3, height=5.7, sections=12); m.apply_translation((0, 0, 2.85)); cat = "insert"
            lab = "M3 heat-set insert in %s (for %s)" % (f["part"], f["screw"])
        else:
            m = trimesh.creation.cylinder(radius=f["s"] / 2 / np.cos(np.pi / 6), height=f["h"], sections=6); m.apply_translation((0, 0, f["h"] / 2)); cat = "connector"
            lab = "%s (%s)" % (f["spec"], f.get("screw") or "jack")
        geoms.append(geom_of(m, nid)); nodes.append(dict(name=nid, mesh=len(geoms) - 1, matrix=T))
        ax = np.array(f["axis_world"], float)
        sub = "paddle" if f.get("group") == "paddle pivot" else "spring" if f.get("group", "").startswith(("drum", "spring")) else \
            "seat" if f.get("group", "").startswith("seat") else "spine" if f.get("group") == "spine to base" else \
            "bay" if f.get("group", "").startswith(("bay", "gate", "DC")) else "mast"
        man[nid] = dict(label=lab, part=cat, fid=f["id"], file="(drawn) %s" % f["spec"], link="dock", sub=sub, category=cat, qty=1,
                        material="A2 stainless" if cat != "insert" else "brass", bom=f["line"], status=f.get("len_status", "OK"), blockers=[],
                        mount="%s; engaged %s mm (rule %s)" % (f.get("anchor", ""), f.get("e", ""), f.get("e_min", "")) if cat == "screw" else "",
                        color=f.get("color"), v2=[0, 0, 0], v3=(-ax * (14.0 if cat == "screw" else 9.0)).round(2).tolist(),
                        spec=dict(size=f.get("size"), length=f.get("length_mm"), head=(f.get("head") or {}).get("type")),
                        joins=[f.get("part"), f.get("into")], supplied="DOCK " + f["line"], note="; ".join(f.get("notes", [])))
    return geoms, nodes, man


def dock_cables():
    J = json.load(open(os.path.join(DOCK, "dock_cables3d.json")))
    NL = __import__("yaml").safe_load(open(os.path.join(DOCK, "dock_netlist.yaml")))
    desc = {c["id"]: c["desc"] for c in NL["cables"]}
    out = []
    for c in J["cables"]:
        for r in c["runs"]:
            if not r.get("points"):
                continue
            P = np.array(r["points"])
            subs = ["paddle" if (p[0] < 22 and p[2] > 125) else "seat" if p[0] < -15 else "spine" if p[0] < 30 else "bay" if p[0] >= 103 else "mast" for p in P]
            out.append(dict(id="%s:%s" % (c["id"], r["wire"]), cable=c["id"], run=r["wire"], seats=[], desc=desc.get(c["id"], ""),
                            node="dock-cable-%s-%s" % (c["id"], r["wire"].replace(".", "_")), color=WIRE_HEX.get(r["color"], "#e07a1f"),
                            d_mm=r["od_mm"], points=P.round(2).tolist(), point_sub=subs, point_follow=[None] * len(P), sub=subs[len(P) // 2],
                            **{"from": r["frm"]}, to=r["to"], gauge=r["gauge"], wires=1, wires_detail=["%s %s %s" % (r["net"], r["gauge"], r["color"])],
                            cut_mm=r["cut_mm"], routed_mm=r["length_mm"], worst_mm=r["length_mm"],
                            check="pass" if J["self_check"] == "PASS" else "fail",
                            note="clearance %s mm to every body (wire radius %s mm); cut %s mm by the rule (dock_routes.py)" % (r.get("clearance_mm"), r.get("radius_mm"), r["cut_mm"])))
    return out


def dock_cables_docked():
    """the dock wires in the docked state: the paddle points move with the paddle push and turn of docked_pose.json"""
    import dock_assembly as DA
    out = dock_cables()
    c, sn = np.cos(DA.YAW_DOCKED), np.sin(DA.YAW_DOCKED)
    for cb in out:
        P = np.array(cb["points"])
        for i, sub in enumerate(cb["point_sub"]):
            if sub == "paddle":
                x, y = P[i, 0] - 18.0, P[i, 1]
                P[i, 0], P[i, 1] = 18.0 + c * x - sn * y + DA.PUSH_DOCKED, sn * x + c * y
        cb["points"] = P.round(2).tolist()
        cb["note"] += "; the paddle end follows the docked push and turn, the loop to the mast face takes up the travel"
    return out


def dock_manifest(nodes_man, cables, generated):
    B = json.load(open(os.path.join(DOCK, "dock_bom.json")))
    S = json.load(open(os.path.join(DOCK, "stl", "slice.json")))
    F = json.load(open(os.path.join(DOCK, "dock_fasteners.json")))
    printed = []
    for name, r in S["parts"].items():
        ids = [k for k, v in nodes_man.items() if v["category"] == "pla" and v["part"] in (name, name + "_l", name + "_r")]
        printed.append(dict(stl=name + ".stl", label=name.replace("dock_", "").replace("_", " "), expected=r["qty"], found=len(ids), material="PLA (light profile)",
                            g_each=r["grams"], h_each=r["hours"], g_total=round(r["grams"] * r["qty"], 1), h_total=round(r["hours"] * r["qty"], 2),
                            flags="ok", file_in_print=False, ok=len(ids) == r["qty"], note="twin/dock/stl/", nodes=ids))
    purchase, bomrows, full = {}, [], []
    for l in B["lines"]:
        ids = [k for k, v in nodes_man.items() if v.get("bom") == l["line"]]
        cost = None if l["unit"] is None else round(l["unit"] * l["buy"], 2)
        purchase[l["line"]] = dict(item=l["part"], spec=l["pn"], supplier=l["seller"], link=l["url"], buy=str(l["buy"]), pack="1", line_cost=cost,
                                   need=str(l["need"]), verified=l["read"], ships="Yes", section="Dock station")
        cnt = len(ids)
        bomrows.append(dict(line=l["line"], section="Dock station: " + l["group"], item=l["part"], spec=l["pn"], need=str(l["need"]), buy=str(l["buy"]),
                            supplier=l["seller"], verified=l["read"], kind="cad" if cnt else "not_modelled",
                            show=("In the model (%d)" % cnt) if cnt else "Not drawn (bulk or surplus)", count=cnt or None, expected=None, ok=True,
                            note=l["read"], blockers=["K5 price"] if l["unit"] is None else [], nodes=ids))
        full.append(dict(id=l["line"], section="Dock station", item=l["part"], spec=l["pn"], qty=l["need"], unit="pcs", spare=max(0, l["buy"] - l["need"]),
                         where=", ".join(sorted({nodes_man[i]["sub"] for i in ids})) or "dock", nodes=ids, line=l["line"],
                         status="BLOCKER" if l["unit"] is None else "bought" if l["buy"] else "surplus", note=l["read"], source=l["read"],
                         supplier=l["seller"], link=l["url"], buy=str(l["buy"]), pack="1", line_cost=cost))
    scr = [f for f in F["fasteners"] if f["kind"] == "screw"]
    by_spec = {}
    for f in scr:
        k = "%s x %g" % (f["size"], f["length_mm"]); by_spec[k] = by_spec.get(k, 0) + 1
    ins = [f for f in F["fasteners"] if f["kind"] == "insert"]
    by_part = {}
    for f in ins:
        by_part[f["part"]] = by_part.get(f["part"], 0) + 1
    T = B["totals"]
    blockers = {"DK-K5": dict(title="Spring pin price (Mill-Max 0933-0-15-20-72-14-11-0)", status="OPEN", open=True, how="digikey.com is outside this session's network; the 0932's $1.23 is the stand-in"),
                "DK-SPRING-TOL": dict(title="CF37CS load tolerance", status="OPEN", open=True, how="not on the Century page: +/- 10 % assumed, BT1 measures it"),
                "DK-EVM-OUTLINE": dict(title="Charger board outline", status="OPEN", open=True, how="26.0 x 22.6 mm scaled from the user's guide layout; measure the board"),
                "DK-PERF-HOLE": dict(title="Perma-Proto mounting hole diameter", status="OPEN", open=True, how="3.2 mm assumed for M3; measure"),
                "DK-HOLD": dict(title="Friction of the belly on the seat", status="OPEN", open=True, how="0.52 needed at the lightest sit (7 N) against the 3.62 N push; BT9")}
    summ = dict(printed=dict(found=sum(p["found"] for p in printed), expected=sum(p["expected"] for p in printed), stl_files=len(printed),
                             stl_found=sum(1 for p in printed if p["found"]), grams=S["total_g"], hours=S["total_h"], doc_total_parts=sum(p["expected"] for p in printed),
                             grams_source="twin/dock/stl/slice.json", pla=sum(p["expected"] for p in printed), tpu=0),
                servos=dict(found=0, expected=0), inserts=dict(found=len(ins), expected=len(ins), by_part=by_part), bearings=dict(found=0, expected=0),
                placeholders=dict(total=0, placed=0, tray=0, replaced={}),
                bom=dict(lines=len(B["lines"]), cad=sum(1 for b in bomrows if b["count"]), both=0, placeholder=0, filament=1, not_modelled=sum(1 for b in bomrows if not b["count"]), mismatches=[]),
                printed_mismatches=[p["stl"] for p in printed if not p["ok"]], blockers_open=list(blockers), blockers_total=len(blockers),
                screws=dict(found=len(scr), by_spec=by_spec, expected=len(scr)),
                cables=dict(found=len(cables), pass_=0, test_fit=0, fail=0))
    summ["cables"] = dict(found=len(cables), test_fit=0, fail=sum(1 for c in cables if c["check"] == "fail"))
    summ["cables"]["pass"] = len(cables) - summ["cables"]["fail"]
    cats = {k: dict(label=v[0], color=v[1], count=0) for k, v in CATS.items()}
    for v in nodes_man.values():
        cats.setdefault(v["category"], dict(label=v["category"], color="#8a8f98", count=0))["count"] += 1
    cats["cable"]["count"] = len(cables)
    subs = {k: dict(label=v[0], group=v[1], v1=v[2], centre=[0, 0, 0]) for k, v in SUBS.items()}
    return dict(meta=dict(generated=generated, script="altaay_lab/viewer/make_viewer_data.py --scene dock (viewer/dock_scene.py)", units="mm",
                          frame="dock frame: x toward the mast (the paddle face at rest x 0), y left, z up from the floor (glTF root turns it y-up, scale 0.001)",
                          sources=dict(parts="altaay_lab/twin/dock/dock_assembly.py", fasteners="altaay_lab/twin/dock/dock_fasteners.json",
                                       cables="altaay_lab/twin/dock/dock_cables3d.json", bom="altaay_lab/twin/dock/dock_bom.json"),
                          explode=dict(stage1=[0.0, 0.6], stage2=[0.2, 0.9], stage3=[0.5, 1.0], horn_pull=14.0, insert_pull=11.0),
                          totals=T, scene="dock"),
                categories=cats, groups=[dict(id="dock", label="Dock station", subs=list(SUBS))], subassemblies=subs, tray=None, nodes=nodes_man,
                servos=[], blockers=blockers, checklist=dict(summary=summ, printed=printed, bom=bomrows, extra=[],
                notes=[dict(kind="check", text=b["title"] + ": " + b["how"], nodes=[]) for b in blockers.values()] +
                      [dict(kind="doc", text="Sim pass only: the paddle at 3.29 N constant, PLA face friction 0.4 (DOCK_TWIN section 12.1); CAD check only for every fit and route.", nodes=[])]), cables=cables, bom_full=full,
                purchase=purchase, retention=[], labels=[])


def read_glb(path):
    raw = open(path, "rb").read()
    jl = struct.unpack("<I", raw[12:16])[0]
    J = json.loads(raw[20:20 + jl])
    bl = struct.unpack("<I", raw[20 + jl:24 + jl])[0]
    blob = raw[28 + jl:28 + jl + bl]
    geoms = []
    for m in J["meshes"]:
        pr = m["primitives"][0]
        ap, ai = J["accessors"][pr["attributes"]["POSITION"]], J["accessors"][pr["indices"]]
        vp, vi = J["bufferViews"][ap["bufferView"]], J["bufferViews"][ai["bufferView"]]
        pos = np.frombuffer(blob[vp["byteOffset"]:vp["byteOffset"] + vp["byteLength"]], np.float32).reshape(-1, 3)
        idx = np.frombuffer(blob[vi["byteOffset"]:vi["byteOffset"] + vi["byteLength"]], np.uint16 if ai["componentType"] == 5123 else np.uint32)
        geoms.append(dict(name=m["name"], pos=pos.copy(), idx=idx.astype(np.uint32)))
    nodes = []
    for n in J["nodes"][1:]:
        M = np.array(n["matrix"], float).reshape(4, 4).T
        nodes.append(dict(name=n["name"], mesh=n["mesh"], matrix=M))
    return geoms, nodes


def write(out, prefix, geoms, nodes, man, write_glb):
    path = os.path.join(out, prefix + ".glb")
    write_glb(path, geoms, nodes)
    M = man["meta"]
    M["sources"].setdefault("urdf", "mini_bdx/robots/open_duck_mini_v2/robot.urdf (the duck of the Docked scene; the dock is its own frame)")
    M["sources"].setdefault("inserts", "altaay_lab/twin/dock/dock_fasteners.json")
    M["sources"].setdefault("docs", "altaay_lab/twin/dock/DOCK_TWIN.md, dock_bom.json, dock_netlist.yaml")
    M.setdefault("placements", "every dock part placed by twin/dock/dock_assembly.py (no boxes)")
    M["glb"] = dict(nodes=len(nodes), triangles_drawn=int(sum(len(g["idx"]) // 3 for g in geoms)), bytes=os.path.getsize(path))
    M.setdefault("unmapped", [])
    with open(path, "rb") as fh, open(os.path.join(out, prefix + ".glb.txt"), "w") as fo:
        fo.write(base64.b64encode(fh.read()).decode("ascii"))
    json.dump(man, open(os.path.join(out, prefix + "_manifest.json"), "w"), separators=(",", ":"))
    sizes = {f: os.path.getsize(os.path.join(out, f)) for f in (prefix + ".glb.txt", prefix + "_manifest.json")}
    print("wrote", sizes)
    big = [f for f, s in sizes.items() if s > 16e6]
    if big:
        raise SystemExit("over 16 MB: %s" % big)
    return sizes


def build(out, scene, write_glb):
    generated = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    if scene == "dock":
        geoms, nodes, nm = dock_parts("dock")
        cab = dock_cables()
        man = dock_manifest(nm, cab, generated)
        return write(out, "dock", geoms, nodes, man, write_glb)
    # docked: the dock in the docked state plus the duck of <out>/duck.glb posed by the sim
    import yourdfpy
    import dock_assembly as DA
    dg, dn, dm = dock_parts("docked")
    dman = dock_manifest(dm, dock_cables_docked(), generated)
    duck_glb, duck_man = os.path.join(out, "duck.glb"), os.path.join(out, "manifest.json")
    if not (os.path.exists(duck_glb) and os.path.exists(duck_man)):
        raise SystemExit("run make_viewer_data.py --out %s first (the duck scene), then --scene docked" % out)
    g2, n2 = read_glb(duck_glb)
    M2 = json.load(open(duck_man))
    u = yourdfpy.URDF.load(os.path.join(REPO, "mini_bdx", "robots", "open_duck_mini_v2", "robot.urdf"), load_meshes=False, build_scene_graph=True)
    u.update_cfg(np.zeros(len(u.actuated_joint_names)))
    T0 = {l: u.get_transform(l) for l in u.link_map}
    TD = DA.docked_duck_links()
    off = len(dg)
    moved = 0
    for n in n2:
        rec = M2["nodes"].get(n["name"], {})
        link = rec.get("link")
        if link not in TD:
            link = "trunk_assembly"     # placeholders and tray parts are in the zero-pose world, the trunk frame
        if link in TD and link in T0:
            A = T0[link].copy(); A[:3, 3] *= 1000.0
            n["matrix"] = TD[link] @ np.linalg.inv(A) @ n["matrix"]; moved += 1
        elif link not in (None,):
            pass
        n["mesh"] += off
    geoms = dg + g2
    nodes = dn + [n for n in n2 if M2["nodes"].get(n["name"], {}).get("category") not in ("cable", "tie")]
    man = dman
    duck_nodes = {k: dict(v, sub="duck_" + (v.get("sub") or "trunk"), v1=None) for k, v in M2["nodes"].items() if v.get("category") not in ("cable", "tie")}
    man["nodes"].update(duck_nodes)
    for k, c in M2["categories"].items():
        if k not in man["categories"]:
            man["categories"][k] = dict(c)
        else:
            man["categories"][k]["count"] += c.get("count", 0)
    for k, s in M2["subassemblies"].items():
        man["subassemblies"]["duck_" + k] = dict(label="Duck: " + s["label"], group="duck", v1=[0, 0, 0], centre=s.get("centre", [0, 0, 0]))
    man["groups"].append(dict(id="duck", label="Duck (docked, sim pose)", subs=["duck_" + k for k in M2["subassemblies"]]))
    man["bom_full"] = man["bom_full"] + [dict(r, section="Duck: " + r.get("section", "")) for r in M2["bom_full"]]
    man["purchase"].update({("duck " + k): v for k, v in M2["purchase"].items()})
    sm, ds = man["checklist"]["summary"], M2["checklist"]["summary"]
    for k in ("printed", "inserts", "servos", "bearings"):
        sm[k]["found"] += ds[k]["found"]; sm[k]["expected"] += ds[k]["expected"]
    sm["printed"]["grams"] = round(sm["printed"]["grams"] + ds["printed"]["grams"], 1); sm["printed"]["hours"] = round(sm["printed"]["hours"] + ds["printed"]["hours"], 1)
    sm["printed"]["stl_files"] += ds["printed"]["stl_files"]; sm["printed"]["stl_found"] += ds["printed"]["stl_found"]
    sm["screws"]["found"] += ds["screws"]["found"]; sm["screws"]["expected"] = None
    for k, v in ds["screws"]["by_spec"].items():
        sm["screws"]["by_spec"][k] = sm["screws"]["by_spec"].get(k, 0) + v
    man["checklist"]["printed"] += M2["checklist"]["printed"]
    man["checklist"]["notes"] += M2["checklist"].get("notes", []); man["checklist"]["extra"] += M2["checklist"].get("extra", [])
    man["checklist"]["bom"] += [dict(b, section="Duck: " + b["section"]) for b in M2["checklist"]["bom"]]
    sm["bom"]["lines"] += ds["bom"]["lines"]
    man["servos"] = M2.get("servos", [])
    man["blockers"].update(M2["blockers"]); sm["blockers_open"] += ds["blockers_open"]; sm["blockers_total"] += ds["blockers_total"]
    man["meta"]["scene"] = "docked"
    man["meta"]["docked"] = dict(source=DA.POSE["source"], push_mm=DA.PUSH_DOCKED, yaw_deg=round(float(np.degrees(DA.YAW_DOCKED)), 2), duck_nodes_moved=moved,
                                 note="the duck's cables and ties are drawn in the Duck scene only")
    return write(out, "docked", geoms, nodes, man, write_glb)
