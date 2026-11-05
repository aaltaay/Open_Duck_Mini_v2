"""inventory.py: every part, every cable and every named screw against what the 3D viewer draws, plus the phase 2
patch data (fasteners, cables, part seats, labels). CAD check only.

Run after camera_seat.py and ribbon_d12.py: python3 altaay_lab/twin/complete3d/inventory.py
Reads the base viewer run in $C3D_VIEWER (manifest.json, duck.glb, run.log) and the published manifest when present.
Writes in altaay_lab/twin/complete3d/: inventory.json, TABLES.md, fasteners_patch.json, cables_patch.json,
part_seats.json, labels.json.
"""
import collections
import importlib
import json
import os
import re
import sys

import numpy as np
import trimesh
import yaml

from common import CABLES3D, FASTENERS, HEAD_LINK, HERE, LAB, OUT, REPO, VIEWER_BASE, glb_meshes, scene, write_json

PUBLISHED = os.path.join(OUT, "published", "manifest.json")
SMALL = ("screw", "insert", "tie", "connector", "cable")
# viewer part -> netlist component ids (wiring/netlist.yaml)
PMAP = {"cell": ["PACK"], "holder": ["PACK"], "bms_tenergy": ["BMS"], "bms_cad": ["BMS"], "charger": ["CHG"], "xt30": ["XT30"],
        "fuse_holder": ["F1"], "mosfet_switch": ["SW1"], "power_switch": ["CTL"], "bec_pro": ["U1"], "adapter": ["U2"],
        "reg_5v": ["U3"], "pi": ["PI"], "imu": ["BNO"], "amp": ["AMP"], "speaker": ["SPK"], "camera": ["CAM"],
        "foot_switch_l1": ["FSL1"], "foot_switch_l2": ["FSL2"], "foot_switch_r1": ["FSR1"], "foot_switch_r2": ["FSR2"],
        "led_1": ["LEDL"], "led_2": ["LEDR"], "led_3": ["LEDP"], "sg90": ["SGL", "SGR"], "power_splice": ["JBP", "JBN", "SPV", "SPG"]}
# head lamps as upstream (lead update 2026-11-04: Ahmed kept one eye LED per eye plus the side projector lamp)
LED_NAME = {"ph-led_1": "Eye LED left", "ph-led_2": "Eye LED right", "ph-led_3": "Projector LED"}
# upstream docs/open_duck_mini_v2_wiring_diagram.drawio parts and links -> lab parts and cables
UPSTREAM_PARTS = [("18650 x2 series", "cell, holder (BOM 6, 7)"), ("BMS", "bms_tenergy (BOM 8)"), ("USB-C charger", "charger (BOM 11)"),
                  ("UBEC", "bec_pro (BOM L1); 5 V from reg_5v (BOM 9)"), ("power switch", "mosfet_switch (BOM 10) + power_switch (10b)"),
                  ("Raspberry pi zero 2W", "pi (BOM 3)"), ("Motor control board", "adapter (BOM 2)"), ("IMU", "imu (BOM 5)"),
                  ("Antenna 1 (x2)", "SG90 servos and antenna rods"), ("switch (x2, feet)", "foot_switch x4 (BOM 13)"),
                  ("flashlight", "led_3 projector (BOM E3) in flash_light_module"), ("Speaker", "speaker (BOM E1) + amp (E2)"),
                  ("Camera", "camera (BOM E6)"), ("Eye LED (x2)", "led_1, led_2 (BOM E3)"), ("Mic", None)]
UPSTREAM_LINKS = [("18650 x2 series -> BMS (3 links: B+, B-, BM)", ["P1", "P2", "P3"]), ("USB-C charger -> BMS (2)", ["P4", "P5"]),
                  ("BMS -> power switch -> UBEC", ["P6", "P8", "P7", "P14", "P9", "P16", "P15", "P10"]),
                  ("UBEC -> 7.4V DC in (2)", ["P11", "SP1", "SP2", "SP3", "SP4", "SP5"]), ("UBEC -> Raspberry pi (5V)", ["P13", "P12", "P17"]),
                  ("usb-c -> micro usb (Pi to motor board)", ["D1"]), ("IMU -> Raspberry pi", ["D2"]),
                  ("switch -> Raspberry pi (feet, 2)", ["D3", "D4"]), ("Raspberry pi -> Antenna 1 (2)", ["D8", "D9"]),
                  ("Raspberry pi -> Speaker", ["D10", "D11"]), ("Raspberry pi -> Eye LED (+ flashlight)", ["D5", "D6", "D7"]),
                  ("Camera -> Raspberry pi", ["D12"]), ("motor board -> Left leg, Right leg, Neck", ["SD1", "SD2", "S2", "S3", "S4", "S5",
                                                                                                   "S7", "S8", "S9", "S10", "S11", "S12", "S13"]),
                  ("Mic -> Raspberry pi (unlabelled purple link)", [])]
INLINE = {"VSW", "G", "YD3", "YG3", "JG20", "JG10", "JG30", "J5", "JG", "JBP", "JBN", "SPV", "SPG", "JFI", "JFO"}
SPEC_RE = re.compile(r"(?:(\d+)\s*x\s*)?\b(M2\.5|M2|M3)\s*x\s*(\d+(?:\.\d+)?)", re.I)


def md_rows(path):
    for i, line in enumerate(open(path), 1):
        if line.startswith("|") and not re.match(r"^\|\s*-", line):
            yield i, [c.strip() for c in line.strip().strip("|").split("|")]


def main():
    S = scene()
    M = json.load(open(os.path.join(VIEWER_BASE, "manifest.json")))
    PUB = json.load(open(PUBLISHED)) if os.path.exists(PUBLISHED) else None
    nodes = M["nodes"]
    c3 = json.load(open(CABLES3D))
    FJ = json.load(open(FASTENERS))
    NL = yaml.safe_load(open(os.path.join(LAB, "wiring", "netlist.yaml")))
    cam = json.load(open(os.path.join(HERE, "camera_seat.json")))
    rib = json.load(open(os.path.join(HERE, "d12_ribbon.json")))
    glb = glb_meshes()
    how = {}
    for line in open(os.path.join(VIEWER_BASE, "run.log")):
        m = re.match(r"\s+placeholder (\S+)\s+sub \S+\s+follow (\S+)\s+dist ([\d.]+)\s+(.*)", line)
        if m:
            how[m.group(1)] = dict(follow=m.group(2), dist=float(m.group(3)), how=m.group(4).strip())
    try:
        sys.path.insert(0, os.path.join(LAB, "viewer"))
        BOM_VIEW = importlib.import_module("make_viewer_data").BOM_VIEW
    except Exception as e:  # noqa: BLE001
        BOM_VIEW = {}
        print("BOM_VIEW not read:", e)
    screws = [f for f in FJ["fasteners"] if f["kind"] == "screw"]

    def fast_for(names):
        keys = [n.lower().replace("_", " ") for n in names if n]
        hit = [f for f in FJ["fasteners"] if any(k and (k in str(f.get("part", "")).lower().replace("_", " ") or
                                                        k in str(f.get("into", "")).lower().replace("_", " ")) for k in keys)]
        return dict(n=len(hit), by_spec=dict(collections.Counter(f["spec"] for f in hit)))

    wires = NL["wires"]
    comp_cables = collections.defaultdict(set)
    for w in wires:
        for end in (w["from"], w["to"]):
            comp_cables[str(end).split(".")[0]].add(w["cable"])
    seat_cables = collections.defaultdict(set)
    for c in c3["cables"]:
        for s in (c.get("seats") or []):
            if s.get("part"):
                seat_cables[s["part"]].add(c["id"])
    # ---------------------------------------------------------------- parts
    parts = []
    guide = {}
    for line in open(os.path.join(REPO, "docs", "print_guide.md")):
        m = re.match(r"- (\S+)\.stl x(\d+)", line)
        if m:
            guide[m.group(1)] = int(m.group(2))
    by_part = collections.defaultdict(list)
    for k, v in nodes.items():
        by_part[v.get("part")].append((k, v))
    for stem, qty in guide.items():
        inst = [(k, v) for k, v in by_part.get(stem, []) if v.get("category") in ("pla", "tpu")]
        parts.append(dict(group="printed", part=stem, qty_upstream=qty, in_viewer=len(inst),
                          seated="yes (robot.urdf or head.stl frame)" if len(inst) >= qty else "NO: %d of %d drawn" % (len(inst), qty),
                          note=("print guide lists 1, CAD and PRINT_CHECK use 2 (upstream issue 26)" if stem == "bulb" else ""),
                          mount=(inst[0][1].get("mount") if inst else ""), fasteners=fast_for([stem]),
                          cables=sorted(seat_cables.get(stem, []))))
    groups = collections.OrderedDict()
    for k, v in nodes.items():
        cat = v.get("category")
        if cat in SMALL or cat in ("pla", "tpu"):
            continue
        g = v.get("group") if str(v.get("group", "")).startswith("servo-") else (k if cat == "placeholder" else v.get("part"))
        groups.setdefault((cat, g), []).append((k, v))
    for (cat, g), lst in groups.items():
        k0, v0 = lst[0]
        pid = k0[3:] if k0.startswith("ph-") else v0.get("part")
        h = how.get(pid, {})
        if pid == "camera" and k0 in glb and np.linalg.norm(glb[k0].bounds.mean(0) - np.array(cam["board"]["pcb_slab_center_world"])) < 0.5:
            seated = "yes: PCB on the measured head.stl pilots (camera_seat.json), within %.2f mm" % float(
                np.linalg.norm(glb[k0].bounds.mean(0) - np.array(cam["board"]["pcb_slab_center_world"])))
        elif pid == "camera":
            seated = ("NO: box centred on the 4 pilots, %.2f mm off the drawing's board centre, and its 11.5 mm depth drawn forward "
                      "through the front wall (%d of 400 samples inside head.stl); designed seat in part_seats.json"
                      % (abs(cam["viewer_box_today"]["offset_along_Y_mm"]), cam["viewer_box_today"]["inside_shell_points"]))
        elif cat == "placeholder" and "Cable terminal seat" in h.get("how", ""):
            seated = "approximate: seat from the cables3d terminal, size stand-in (%s)" % h.get("how", "")[:60]
        elif cat == "placeholder":
            seated = "yes: %s" % h.get("how", "measured")[:70]
        else:
            seated = "yes (robot.urdf CAD body)"
        ids = PMAP.get(pid, [])
        if str(g).startswith("servo-"):
            sid = re.findall(r"\d+", str(v0.get("label", "")) + " " + str(v0.get("servo", "")))
            ids = ["SV%s" % s for s in sid[:1]]
        cab = sorted(set().union(*[comp_cables.get(i, set()) for i in ids])) if ids else []
        parts.append(dict(group="bought" if cat != "other" else "printed rod", part=g, category=cat, bom=v0.get("bom"),
                          label=LED_NAME.get(k0, v0.get("label")), in_viewer=len(lst), seated=seated, status=v0.get("status"),
                          mount=v0.get("mount", ""), fasteners=fast_for([pid, v0.get("label", "")[:20]] + ids),
                          cables=cab, netlist_ids=ids))
    bom = []
    for i, c in md_rows(os.path.join(LAB, "BOM.md")):
        if len(c) > 4 and re.match(r"^(\d+[a-z]?|[A-Z]\d+[a-z]?)$", c[0]) and not c[0].startswith("TO"):
            bom.append(dict(line=c[0], item=c[1], spec=c[2], qty=c[3], md_line=i))
    seen_bom = {str(v.get("bom")) for v in nodes.values()}
    for b in bom:
        if b["line"] in seen_bom:
            continue
        bv = BOM_VIEW.get(b["line"])
        kind = bv[0] if bv else "?"
        parts.append(dict(group="bought, no own node", part=b["item"], bom=b["line"], in_viewer=0,
                          seated={"none": "no body by design (%s)" % (bv[3] if bv and len(bv) > 3 else ""),
                                  "placeholder": "placeholder", "cad": "CAD"}.get(kind, "drawn as %s" % kind) if bv else
                          "not in the robot: tool, supply or spare line (no viewer entry in BOM_VIEW)",
                          spec=b["spec"][:90], qty=b["qty"], fasteners=dict(n=sum(1 for f in screws if str(f.get("line")) == b["line"]))))
    upstream = [dict(upstream_part=u, lab=l, gap=l is None) for u, l in UPSTREAM_PARTS]
    # ---------------------------------------------------------------- cables
    ends = {e["id"]: e for e in c3["cable_ends"]}
    pool = [(k, glb[k]) for k, v in nodes.items() if k in glb and v.get("category") not in ("cable", "screw", "tie", "insert")]
    boxes = np.array([m.bounds for _, m in pool])
    big = trimesh.util.concatenate([m for _, m in pool])
    pqs = {}

    def near_nodes(p, rad):
        dbox = np.linalg.norm(np.maximum(0, np.maximum(boxes[:, 0] - p, p - boxes[:, 1])), axis=1)
        out = []
        for j in np.where(dbox <= rad)[0]:
            k, m = pool[j]
            if k not in pqs:
                pqs[k] = trimesh.proximity.ProximityQuery(m)
            out.append((float(pqs[k].on_surface(np.atleast_2d(p))[1][0]), k))
        return sorted(out)

    def match(k, pre):
        v = nodes.get(k, {})
        ids = PMAP.get(k[3:] if k.startswith("ph-") else v.get("part"), [])
        if any(pp in ids for pp in pre):
            return True
        if any(pp.startswith("SV") for pp in pre) and v.get("category") in ("servo", "horn"):
            return True
        return any(re.search(r"(^|[-_])%s($|[-_])" % re.escape(pp.lower()), k.lower()) for pp in pre)

    DIRS = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]] +
                    [[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], float)
    DIRS /= np.linalg.norm(DIRS, axis=1)[:, None]

    def w_of(pt):
        return (S.T0[pt["link"]] @ np.r_[pt["p"], 1.0])[:3]

    drawn = collections.Counter(str(c["id"]).split(":")[0] for c in M["cables"])
    drawn_pub = collections.Counter(str(c["id"]).split(":")[0] for c in PUB["cables"]) if PUB else {}
    cmap_ids, wiring_ids = set(), set()
    for i, c in md_rows(os.path.join(LAB, "CABLE_MAP.md")):
        if c and re.match(r"^(P|D|S|SD|SP)\d+$", c[0]):
            cmap_ids.add(c[0])
    for i, c in md_rows(os.path.join(LAB, "WIRING.md")):
        if c and re.match(r"^\d+$", c[0]):
            wiring_ids.update(re.findall(r"\b(?:SP|SD|P|D|S)\d+\b", " ".join(c[1:])))
    up_ids = {x for _, l in UPSTREAM_LINKS for x in l}
    nl = {c["id"]: c for c in NL["cables"]}
    cables = []
    for cid in sorted(set(nl) | {c["id"] for c in c3["cables"]} | cmap_ids | wiring_ids,
                      key=lambda s: (re.sub(r"\d", "", s), int(re.sub(r"\D", "", s) or 0))):
        c = next((x for x in c3["cables"] if x["id"] == cid), None)
        runs = (c.get("runs") or [dict(name="main", points=c["points"], d_mm=c["d_mm"])]) if c else []
        endchk, hidden = [], []
        for rn in runs:
            pts = rn["points"]
            for side, pt, pins in (("start", pts[0], c["from"]), ("end", pts[-1], c["to"])):
                p = w_of(pt)
                eid = min(ends, key=lambda e: np.linalg.norm(np.array(ends[e]["p_world0"]) - p))
                de = float(np.linalg.norm(np.array(ends[eid]["p_world0"]) - p))
                pre = sorted({x.split(".")[0] for x in (str(c["from"]) + "/" + str(c["to"])).split("/")})
                cand = near_nodes(p, 6.0)
                hit = next(((d, k) for d, k in cand if match(k, pre)), None)
                endchk.append(dict(run=rn.get("name"), side=side, cable_end=eid, end_gap_mm=de,
                                   nearest_part=cand[0][1] if cand else None, part_gap_mm=cand[0][0] if cand else 99.0,
                                   matched=hit[1] if hit else None, expected=pre,
                                   ok=bool((hit and (de <= 3.0 or any(pp in INLINE for pp in pre))) or eid.startswith("HOLE.") or (side == "start" and any(str(x.get("name", "")).startswith("fan_") for x in runs)))))
            P = np.array([w_of(q) for q in pts])
            S_ = np.concatenate([np.linspace(P[i], P[i + 1], 4, endpoint=False) for i in range(len(P) - 1)] + [P[-1:]])
            S_ = S_[np.linspace(0, len(S_) - 1, min(10, len(S_))).astype(int)]
            O = np.repeat(S_, len(DIRS), 0)
            hid = big.ray.intersects_any(O, np.tile(DIRS, (len(S_), 1))).reshape(len(S_), len(DIRS)).all(1)
            hidden.append(float(hid.mean()))
        shape = ("flat strip: width and thickness BLOCKER (stand-in 16 mm at the 15-pin end, 11.5 mm at the 22-pin end, 0.3 mm)"
                 if cid == "D12" else ("round bundle d %.2f mm ([L] hexagonal packing estimate of %s wires, cables3d.json d_mm)"
                                       % (c["d_mm"], c.get("wires_n")) if c else ""))
        cables.append(dict(id=cid, desc=(c or {}).get("desc") or nl.get(cid, {}).get("desc"), netlist_status=nl.get(cid, {}).get("status"),
                           in_cables3d=c is not None, in_cable_map=cid in cmap_ids, in_wiring=cid in wiring_ids, in_upstream=cid in up_ids,
                           runs=len(runs), runs_drawn_base=drawn.get(cid, 0), runs_drawn_published=drawn_pub.get(cid, 0),
                           ends_ok="%d of %d" % (sum(e["ok"] for e in endchk), len(endchk)),
                           ends_bad=[e for e in endchk if not e["ok"]], shape=shape,
                           hidden_pct=round(100 * float(np.mean(hidden)), 0) if hidden else None, check=(c or {}).get("check")))
    scene_extras = json.load(open(os.path.join(LAB, "viewer", "scene_extras.json")))["items"]
    plug_cables = sorted({it["cable"] for it in scene_extras if it.get("kind") == "connector" and it.get("cable")})
    lead_check = dict(
        cables_in_cables3d=len(c3["cables"]), runs_in_cables3d=sum(len(c.get("runs") or [1]) for c in c3["cables"]),
        runs_drawn_base=len(M["cables"]), runs_drawn_published=len(PUB["cables"]) if PUB else None,
        cables_with_a_scene_extras_plug=len(plug_cables), plug_cables=plug_cables,
        netlist_only_ids=sorted(set(nl) - {c["id"] for c in c3["cables"]}),
        note="FSL1, FSL2, FSR1, FSR2 are netlist components (foot switches); J5, JG10, JG20, JG30 are inline splices (check_cables INLINE): not cables")
    # ---------------------------------------------------------------- screws named in the docs vs fasteners.json
    named = []
    for path in ("MOUNTING.md", "BOM.md"):
        for i, line in enumerate(open(os.path.join(LAB, path)), 1):
            for m in SPEC_RE.finditer(line):
                named.append(dict(src="%s:%d" % (path, i), n=int(m.group(1)) if m.group(1) else None,
                                  spec=("%sx%s" % (m.group(2), m.group(3))).lower(), ctx=line.strip()[:110]))
    for k, v in nodes.items():
        if v.get("category") in SMALL:
            continue
        for m in SPEC_RE.finditer(str(v.get("mount", ""))):
            named.append(dict(src="viewer mount %s" % k, n=int(m.group(1)) if m.group(1) else None,
                              spec=("%sx%s" % (m.group(2), m.group(3))).lower(), ctx=str(v.get("mount"))[:110], part=v.get("part")))
    have = collections.Counter(re.match(r"(M[\d.]+x[\d.]+)", f["spec"]).group(1).lower() for f in screws if re.match(r"M[\d.]+x", f["spec"]))
    for nmd in named:
        nmd["in_fasteners_json_total"] = have.get(nmd["spec"], 0)
        if nmd.get("part"):
            pf = fast_for([nmd["part"]])
            nmd["in_fasteners_json_for_part"] = sum(n for s, n in pf["by_spec"].items() if s.lower().startswith(nmd["spec"]))
            nmd["missing"] = max(0, (nmd["n"] or 0) - nmd["in_fasteners_json_for_part"])
        else:
            nmd["missing"] = max(0, (nmd["n"] or 0) - nmd["in_fasteners_json_total"])
    bom_screw = []
    for b in bom:
        m = re.match(r"^(M[\d.]+)x([\d.]+)", b["item"]) or re.match(r"^(M[\d.]+)x([\d.]+)", b["spec"])
        if m and b["qty"].isdigit():
            sp = ("%sx%s" % (m.group(1), m.group(2))).lower()
            bom_screw.append(dict(line=b["line"], spec=sp, bom_qty=int(b["qty"]), in_fasteners_json=have.get(sp, 0)))
    # ---------------------------------------------------------------- phase 2 patch data
    T0h = S.T0[HEAD_LINK]
    invh = np.linalg.inv(T0h)
    fpatch = dict(meta=dict(label="CAD check only", how="update these records in fasteners.json by id; nothing is added",
                            source="camera_seat.json"), update=[])
    for s in cam["screws"]:
        fpatch["update"].append(dict(id=s["id"], part="Camera Module 3 PCB (BOM E6)", seat_world=s["seat_world"],
                                     axis_world=s["axis_world"], seat_link=(invh @ np.r_[s["seat_world"], 1.0])[:3],
                                     axis_link=invh[:3, :3] @ np.array(s["axis_world"]), length_mm=s["length_mm"],
                                     len_status_by_pcb_t=s["by_pcb_t"], viewer_label="M2x4 pan head: camera PCB into head pilot",
                                     notes=["seat on the PCB back face at the 1.0 mm stand-in (BLOCKER: PCB thickness)",
                                            "option, CAD check only: drill the 4 pilots from 3.2 to 4.5 mm (material past the bottom "
                                            "%.1f mm, measured) and use M2x5 from the same kit: 4.0 mm engaged at t = 1.0 (2 x d rule met), "
                                            "0.5 mm to the bottom" % s["material_past_bottom_mm"]]))
    end_back = cam["d12_end"]["candidates_world"]["back face"]
    cpatch = dict(meta=dict(label="CAD check only (clearance), calc only (length)", source="d12_ribbon.json, camera_seat.json"),
                  D12=dict(shape="flat strip", width_mm=rib["meta"]["width_mm"], width_used=rib["meta"].get("width_used"),
                           thickness_mm=rib["meta"]["thickness_mm"], link=HEAD_LINK, points_link=rib["points_link"],
                           width_link=rib["width_link"], length_mm=rib["length_mm"], verdict=rib["verdict"],
                           events=rib["events"], blockers=rib["meta"]["blockers"]),
                  cable_ends={"CAM.CSI": dict(p_world0=end_back, p=(invh @ np.r_[end_back, 1.0])[:3], dir_world0=cam["d12_end"]["exit_dir_world"],
                                              kind="15-pin FPC", how="[L] camera_seat.json: bottom edge centre of the designed seat, "
                                                                         "back face option (connector side BLOCKER)")},
                  draw_every_run=True)
    pc = cam["board"]
    Tcl = np.array(cam["frame"]["T_cam_link"])
    seats = dict(meta=dict(label="CAD check only", frame="head_assembly link frame (T_cam_link) and URDF world"),
                 camera=dict(replaces="ph-camera box", T_cam_link=Tcl, T_cam_world=cam["frame"]["T_cam_world"],
                             pieces=[dict(name="PCB", center_cam=[0, (pc["y_bottom"] + pc["y_top"]) / 2 - (pc["y_bottom"] + pc["y_top"]) / 2,
                                                                -pc["dims_mm"][2] / 2], dims=pc["dims_mm"], source="[I] HARDWARE_AUDIT B9"),
                                     dict(name="lens through the opening", shape="cylinder", d_mm=5.75,
                                          center_cam=[0, 6.25 - 3.75, cam["lens"]["pcb_front_to_wall_mm"] / 2 + 1.25],
                                          length_mm=cam["lens"]["pcb_front_to_wall_mm"] + (cam["lens"]["wall_t_mm"] or 0),
                                          source="[I] viewer lens note (RP-008153-DS-1)"),
                                     dict(name="15-pin connector zone (stand-in)", center_cam=[0, pc["y_bottom"] + 2.5 - (pc["y_bottom"] + pc["y_top"]) / 2,
                                                                                               -pc["dims_mm"][2] - 1.0],
                                          dims=[16.0, 5.0, 2.0], source="BLOCKER: connector size and side")],
                             note="origin = board centre on the PCB front face; the pilot pattern centre is 3.75 mm toward -Y"))
    # labels: fixed labels for parts and cables, hover only for screws, inserts, ties, connectors, horns
    tgt = []
    for k, v in nodes.items():
        if k not in glb or v.get("category") in SMALL + ("horn",):
            continue
        if str(v.get("group", "")).startswith("servo-") and any(t[2] == v["group"] for t in tgt):
            continue
        tgt.append((k, LED_NAME.get(k) or v.get("label") or v.get("part") or k, v.get("group") if str(v.get("group", "")).startswith("servo-") else k,
                    glb[k].bounds.mean(0), v.get("sub")))
    for c in c3["cables"]:
        P = np.array([w_of(p) for p in c["points"]])
        tgt.append(("cable-" + c["id"], c["id"], "cable-" + c["id"], P[len(P) // 2], None))
    allb = np.array([m.bounds for m in glb.values()])
    lo, hi = allb[:, 0].min(0), allb[:, 1].max(0)
    ctr = (lo + hi) / 2
    Rr = float(np.max(np.linalg.norm(np.array([t[3][:2] for t in tgt]) - ctr[:2], axis=1))) + 35.0
    H = 4.5
    placed = []
    VD = np.array([[1.0, 0], [-1.0, 0], [0, 1.0], [0, -1.0]])
    PA = dict(phi=[], z=[], w=[])

    def free(ph, z, wl):
        if not PA["phi"]:
            return True
        qp, qz, qw = np.array(PA["phi"]), np.array(PA["z"]), np.array(PA["w"])
        for vd in VD:
            if np.cos(ph) * vd[0] + np.sin(ph) * vd[1] <= 0.25:
                continue
            sel = np.cos(qp) * vd[0] + np.sin(qp) * vd[1] > 0.25
            ax = np.array([-vd[1], vd[0]])
            du = np.abs(Rr * ((np.cos(ph) - np.cos(qp)) * ax[0] + (np.sin(ph) - np.sin(qp)) * ax[1]))
            if np.any(sel & (du < (wl + qw) / 2 + 1) & (np.abs(z - qz) < H + 1)):
                return False
        return True

    for k, text, _, a, sub in sorted(tgt, key=lambda t: -t[3][2]):
        wl = 1.9 * len(str(text)[:28]) + 2
        phi0 = np.arctan2(a[1] - ctr[1], a[0] - ctr[0])
        best = None
        for dz in sorted(np.arange(-120, 121, 5.0), key=abs):
            for dp in sorted(np.arange(-1.0, 1.01, 0.05), key=abs):
                if free(phi0 + dp, a[2] + dz, wl):
                    best = (phi0 + dp, a[2] + dz)
                    break
            if best:
                break
        ph, z = best or (phi0, a[2])
        PA["phi"].append(ph)
        PA["z"].append(z)
        PA["w"].append(wl)
        placed.append(dict(node=k, text=str(text)[:28], anchor_world=a, phi=ph, z=z, w=wl, h=H, sub=sub,
                           pos_world=[ctr[0] + Rr * np.cos(ph), ctr[1] + Rr * np.sin(ph), z], free=best is not None))
    overl = {}
    for vname, vd in (("front", np.array([1.0, 0, 0])), ("back", np.array([-1.0, 0, 0])), ("left", np.array([0, 1.0, 0])),
                      ("right", np.array([0, -1.0, 0]))):
        vis = [q for q in placed if np.cos(q["phi"]) * vd[0] + np.sin(q["phi"]) * vd[1] > 0.25]
        ax = np.array([-vd[1], vd[0], 0])
        n = 0
        for i in range(len(vis)):
            for j in range(i + 1, len(vis)):
                pi_, pj = np.array(vis[i]["pos_world"]), np.array(vis[j]["pos_world"])
                if abs((pi_ - pj) @ ax) < (vis[i]["w"] + vis[j]["w"]) / 2 + 0.99 and abs(pi_[2] - pj[2]) < H + 0.99:
                    n += 1
        overl[vname] = dict(visible=len(vis), overlaps=n)
    labels = dict(meta=dict(label="CAD check only", rule="billboard labels on a cylinder R %.0f mm round the robot axis, leader line "
                                                         "to the anchor; a label shows only when it faces the camera (outward normal "
                                                         "within 75 degrees of the view); screws, inserts, ties, connectors and horns "
                                                         "get hover labels only" % Rr, radius_mm=Rr, centre=ctr, size_mm=[1.9, H],
                            overlaps_by_view=overl, not_placed=sum(not q["free"] for q in placed)), labels=placed)
    inv_out = dict(meta=dict(script="altaay_lab/twin/complete3d/inventory.py", label="CAD check only", viewer_run=M["meta"].get("generated"),
                             published_run=PUB["meta"].get("generated") if PUB else None),
                   lead_findings_check=lead_check, parts=parts, upstream_parts=upstream, upstream_links=UPSTREAM_LINKS,
                   cables=cables, screws_named=named, bom_screw_lines=bom_screw,
                   counts=dict(parts_rows=len(parts), parts_seated=sum(str(p["seated"]).startswith("yes") for p in parts),
                               cables=len(cables), cables_all_runs_drawn=sum(c["runs"] and c["runs_drawn_base"] == c["runs"] for c in cables),
                               cables_ends_ok=sum(c["ends_ok"].split(" of ")[0] == c["ends_ok"].split(" of ")[1] and c["runs"] > 0 for c in cables),
                               screws_in_fasteners_json=len(screws), named_missing=sum(n["missing"] for n in named)))
    for name, obj in (("inventory.json", inv_out), ("fasteners_patch.json", fpatch), ("cables_patch.json", cpatch),
                      ("part_seats.json", seats), ("labels.json", labels)):
        write_json(obj, os.path.join(HERE, name))
    # TABLES.md
    L = ["# TABLES: every part, cable and named screw against the 3D viewer (CAD check only)", "",
         "Generated by altaay_lab/twin/complete3d/inventory.py from the viewer run of %s (base 5bd28f9) and the published run of %s."
         % (M["meta"].get("generated"), PUB["meta"].get("generated") if PUB else "n/a"), "", "## Parts", "",
         "| Group | Part | BOM | In viewer | Seated at its real position | Mount | Fasteners (fasteners.json) | Cables |", "|---|---|---|---|---|---|---|---|"]
    for p in parts:
        fs = p.get("fasteners") or {}
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            p["group"], p.get("label") or p["part"], p.get("bom") or "", p["in_viewer"], p["seated"], str(p.get("mount") or "")[:80].replace("|", "/"),
            ("%d: " % fs.get("n", 0)) + ", ".join("%s %d" % kv for kv in (fs.get("by_spec") or {}).items()), ", ".join(p.get("cables") or [])))
    L += ["", "Upstream design parts (docs/open_duck_mini_v2_wiring_diagram.drawio) against the lab parts:", "",
          "| Upstream part | Lab part |", "|---|---|"] + ["| %s | %s |" % (u["upstream_part"], u["lab"] or "GAP: no lab part, no seat") for u in upstream]
    L += ["", "## Cables", "", "| Cable | What | In cables3d / CABLE_MAP / WIRING / upstream | Runs | Drawn (base, published) | Both ends at the right part | Shape | Check |",
          "|---|---|---|---|---|---|---|---|"]
    for c in cables:
        L.append("| %s | %s | %s | %d | %d, %d | %s%s | %s | %s |" % (
            c["id"], (c["desc"] or "")[:40], "/".join("yes" if x else "no" for x in (c["in_cables3d"], c["in_cable_map"], c["in_wiring"], c["in_upstream"])),
            c["runs"], c["runs_drawn_base"], c["runs_drawn_published"], c["ends_ok"],
            ("; off: " + "; ".join("%s %s at %s %.1f mm" % (e["run"], e["side"], e["nearest_part"], e["part_gap_mm"]) for e in c["ends_bad"][:3])) if c["ends_bad"] else "",
            c["shape"][:70], c["check"] or c.get("netlist_status") or ""))
    L += ["", "Upstream links -> lab cables:", ""] + ["- %s: %s" % (u, ", ".join(l) or "GAP: no lab cable") for u, l in UPSTREAM_LINKS]
    L += ["", "## Screws named in MOUNTING.md, BOM.md and the viewer mount texts", "",
          "| Source | Named | Spec | In fasteners.json (part / total) | Missing | Text |", "|---|---|---|---|---|---|"]
    for n in named:
        L.append("| %s | %s | %s | %s / %d | %d | %s |" % (n["src"], n["n"] or "", n["spec"], n.get("in_fasteners_json_for_part", ""),
                                                           n["in_fasteners_json_total"], n["missing"], n["ctx"].replace("|", "/")[:90]))
    L += ["", "| BOM line | Spec | BOM qty | In fasteners.json |", "|---|---|---|---|"] + [
        "| %s | %s | %d | %d |" % (b["line"], b["spec"], b["bom_qty"], b["in_fasteners_json"]) for b in bom_screw]
    open(os.path.join(HERE, "TABLES.md"), "w").write("\n".join(L) + "\n")
    print(json.dumps(inv_out["counts"]), json.dumps(lead_check)[:700])
    print("labels", overl, "not placed", labels["meta"]["not_placed"], "R", round(Rr))
    print("hidden", [(c["id"], c["hidden_pct"]) for c in cables if c["hidden_pct"] is not None])
    print("bad ends", [(c["id"], c["ends_ok"], [(e["run"], e["side"], e["nearest_part"], round(e["part_gap_mm"], 1), round(e["end_gap_mm"], 1), e["expected"])
                                               for e in c["ends_bad"][:2]]) for c in cables if c["ends_bad"]][:30])
    print("missing named", [(n["src"], n["n"], n["spec"], n.get("in_fasteners_json_for_part"), n["in_fasteners_json_total"]) for n in named if n["missing"]])
    print("bom screws", [(b["line"], b["spec"], b["bom_qty"], b["in_fasteners_json"]) for b in bom_screw])
    print("not seated", [(p["part"], p["seated"][:50]) for p in parts if not str(p["seated"]).startswith(("yes", "no body"))])


if __name__ == "__main__":
    main()
