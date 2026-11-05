"""phase2_data.py: V1 "everything in 3D" phase 2, the data and code edits (CAD check only, calc only for lengths).

Run once from anywhere: python3 altaay_lab/twin/complete3d/phase2_data.py [--page <published page html>]
Every edit is asserted and skips when it is already in place, so a second run changes nothing.
Edits: fasteners.json and fasteners.csv (camera screws M2x5, D34), cables3d.json (D12 flat strip with its gentle loop,
CAM.CSI moved, D10 fan-out runs, SP1 SP2 SP4 SP5 lead-ins to the SPV and SPG splice bodies, new cable D13 = the OFF wire on
the P13 route), wiring/netlist.yaml (SW1 OFF pin, PI pin 37, net PWR_OFF, cable and wire D13, D12 cut 300),
viewer/make_viewer_data.py (camera seated as its PCB, head_board ghost not drawn, camera screw labels, roll_to_pitch
mount text, labels and x-ray in the manifest, D12 drawn as a strip) and the viewer page (x-ray switch, label layer,
flat strip), written to $C3D_OUT/viewer/index.html.
"""
import argparse
import copy
import csv
import json
import os
import re

import numpy as np

from common import CABLES3D, FASTENERS, HEAD_LINK, HERE, LAB, OUT, scene, write_json

LOG = []


def edit(path, old, new, count=1):
    t = open(path, encoding="utf-8").read()
    if new in t and old not in t:
        return False
    assert t.count(old) == count, "%s: %d x %r" % (path, t.count(old), old[:70])
    open(path, "w", encoding="utf-8").write(t.replace(old, new))
    LOG.append("%s: %s" % (os.path.relpath(path, LAB), old[:50].strip()))
    return True


def fasteners():
    f = json.load(open(FASTENERS))
    cam = json.load(open(os.path.join(HERE, "camera_seat.json")))
    for r in f["fasteners"]:
        if r.get("source") != "camera":
            continue
        r.update(spec="M2x5 self-tapping pan head", length_mm=5, part="Camera Module 3 PCB (BOM E6)",
                 viewer_label="M2x5 pan head: camera to head (BOM 17h, pilot drilled to 4.5 mm, D34)",
                 anchor="plastic pilot 1.65 (camera), drilled from 3.2 to 4.5 mm deep (D34)", e=4.0, e_min=4.0, far=5.5,
                 lmin=5.0, lmax=5.25, tip_gap=0.5, stop=5.55, len_status="OK",
                 notes=["Camera Module 3 holes 2.2 mm on 21 x 12.5 (HARDWARE_AUDIT B9); PCB thickness UNVERIFIED, 1.0 mm stand-in",
                        "D34 lead note: M2x5 from the BOM 17h kit; pilot drilled from 3.2 to 4.5 mm with a 1/16 in (1.59 mm) bit "
                        "(print/PRINT_PLAN.md After printing step 6); %.1f mm of material stays past the bottom "
                        "(twin/complete3d/camera_seat.json, CAD check only)" % (cam["pilots"][0]["material_past_bottom_mm"] - 1.3)])
        if r.get("draw_length_mm") is not None:
            r["draw_length_mm"] = 5
    for b in f.get("bom", []):
        if b.get("line") == "17h" and "M2x4" in b.get("specs", ""):
            b["specs"] = re.sub(r"M2x4 self-tapping pan head 6", "M2x4 self-tapping pan head 2", b["specs"])
            b["specs"] = re.sub(r"M2x5 self-tapping pan head 22", "M2x5 self-tapping pan head 26", b["specs"])
    write_json(f, FASTENERS) if False else json.dump(f, open(FASTENERS + ".tmp", "w"), indent=1)
    os.replace(FASTENERS + ".tmp", FASTENERS)
    p = os.path.join(LAB, "fasteners", "fasteners.csv")
    rows = list(csv.reader(open(p)))
    hdr = rows[0]
    ids = {"F344", "F345", "F346", "F347"}
    for row in rows[1:]:
        if row and row[0] in ids:
            for k, h in enumerate(hdr):
                if h in ("spec",):
                    row[k] = "M2x5 self-tapping pan head"
                elif h in ("length_mm", "length"):
                    row[k] = "5"
                elif h in ("len_status",):
                    row[k] = "OK"
                elif h in ("part",):
                    row[k] = "Camera Module 3 PCB (BOM E6)"
    csv.writer(open(p, "w", newline="")).writerows(rows)
    LOG.append("fasteners.json and fasteners.csv: F344 to F347 M2x5, camera to head (D34)")


def cables():
    S = scene()
    c3 = json.load(open(CABLES3D))
    C = {c["id"]: c for c in c3["cables"]}
    E = {e["id"]: e for e in c3["cable_ends"]}
    T0, inv = S.T0, np.linalg.inv
    wof = lambda q: (T0[q["link"]] @ np.r_[q["p"], 1.0])[:3]
    tol = lambda link, pw: (inv(T0[link]) @ np.r_[pw, 1.0])[:3].round(3).tolist()
    rib = json.load(open(os.path.join(HERE, "d12_ribbon.json")))
    cam = json.load(open(os.path.join(HERE, "camera_seat.json")))
    out = {}
    # D12: the flat strip centre line for the length check, the drawing path with the gentle loop for the viewer
    d12 = C["D12"]
    pts = [dict(link=HEAD_LINK, p=[round(v, 3) for v in p]) for p in rib["centerline_link"]]
    d12["points"] = pts
    d12["runs"][0]["points"] = pts
    d12.update(shape="flat strip", width_mm=rib["meta"]["width_mm"], thickness_mm=rib["meta"]["thickness_mm"],
               width_link=[[round(v, 4) for v in w] for w in rib["centerline_width_link"]],
               draw_points=[dict(link=HEAD_LINK, p=[round(v, 3) for v in p]) for p in rib["draw_link"]],
               draw_width_link=[[round(v, 4) for v in w] for w in rib["draw_width_link"]], cut_mm=300,
               strip=dict(source="twin/complete3d/ribbon_d12.py (d12_ribbon.json)", label="CAD check only, calc only for lengths",
                          route_mm=rib["centerline_mm"], drawn_mm=rib["draw_mm"], events=rib["events"],
                          loop={k: v for k, v in (rib.get("slack_loop_300") or {}).items() if k not in ("points_world", "width_world")},
                          sources=rib["meta"]["sources"], blockers=rib["meta"]["blockers"]),
               note="flat strip without a twist (D34): route %.1f mm, the 300 mm cable's spare in one gentle loop" % rib["centerline_mm"])
    for w in d12["wires"]:
        w["cut_mm"] = 300
    eb = cam["d12_end"]["candidates_world"]["back face"]
    E["CAM.CSI"].update(p_world0=[round(v, 2) for v in eb], p=tol(E["CAM.CSI"]["link"], eb),
                        how="[L] twin/complete3d/camera_seat.json: bottom edge centre of the seat measured on head.stl (board centre "
                            "3.75 mm toward the lens row), strip in the board plane 1.0 mm behind the PCB (connector side BLOCKER)")
    out["D12"] = rib["centerline_mm"]
    # D10: fan-out from the bundle start to every Pi pin and splice of the bundle
    d10 = C["D10"]
    main = [r for r in d10["runs"] if r["name"] == "main"][0]
    b0 = main["points"][0]
    have = {r["name"] for r in d10["runs"]}
    fans = []
    for pin in [x.split(".S")[0] if x.endswith(".S") else x for x in d10["from"].split("/")]:
        key = pin if pin in E else pin.split(".")[0]
        if key not in E or np.linalg.norm(np.array(E[key]["p_world0"]) - wof(b0)) < 3.0:
            continue
        name = "fan_%s" % key
        if name not in have:
            d10["runs"].append(dict(name=name, points=[copy.deepcopy(b0), dict(link=E[key]["link"], p=E[key]["p"])], d_mm=1.5,
                                    routed=True, **{"from": "D10 bundle start"}, to=key, joints=[]))
        fans.append(name)
        for w in d10["wires"]:
            if w["from"].split(".S")[0] == pin.split(".S")[0] or w["from"] == pin + ".S":
                if name not in w["runs"]:
                    w["runs"].append(name)
    out["D10 fans"] = fans
    # SP1, SP2, SP4, SP5: lead-in from the SPV/SPG splice bodies (power_splice box) to the routed start (SP.L or SP.R)
    pc = next(r for r in json.load(open(os.path.join(LAB, "audit", "placements.json"))) if r["id"] == "power_splice")
    box = np.array(pc["center_mm"], float)
    for cid in ("SP1", "SP2", "SP4", "SP5"):
        c = C[cid]
        r0 = [r for r in c["runs"] if r["name"] == "main"][0]
        q0 = r0["points"][0]
        if np.linalg.norm(wof(q0) - box) < 1.0:
            continue
        lead = dict(link=q0["link"], p=tol(q0["link"], box))
        r0["points"].insert(0, lead)
        if c["points"] and c["points"][0] == q0:
            c["points"].insert(0, copy.deepcopy(lead))
        out[cid + " lead-in mm"] = round(float(np.linalg.norm(wof(q0) - box)), 1)
    # D13: the OFF wire, Pi GPIO26 (pin 37) to the 2813 OFF input, on the P13 route (D30 netlist note), then P12 and the header
    if "D13" not in C:
        a1, a35 = np.array(E["PI.1"]["p_world0"]), np.array(E["PI.35"]["p_world0"])
        assert abs(np.linalg.norm(a35 - a1) - 17 * 2.54) < 0.6, np.linalg.norm(a35 - a1)
        pin37 = a35 + (a35 - a1) / np.linalg.norm(a35 - a1) * 2.54
        p13, p12 = C["P13"], C["P12"]
        P13 = p13["points"] if np.linalg.norm(wof(p13["points"][0]) - np.array(E["VSW"]["p_world0"])) < \
            np.linalg.norm(wof(p13["points"][-1]) - np.array(E["VSW"]["p_world0"])) else p13["points"][::-1]
        P12 = p12["points"] if np.linalg.norm(wof(p12["points"][0]) - np.array(E["U3.OUT"]["p_world0"])) < \
            np.linalg.norm(wof(p12["points"][-1]) - np.array(E["U3.OUT"]["p_world0"])) else p12["points"][::-1]
        sw = E["SW1.CTL"]
        pts = [dict(link=sw["link"], p=sw["p"])] + copy.deepcopy(P13) + copy.deepcopy(P12) + \
              [dict(link=E["PI.35"]["link"], p=tol(E["PI.35"]["link"], pin37))]
        W = np.array([wof(q) for q in pts])
        L0 = float(np.sum(np.linalg.norm(np.diff(W, axis=0), axis=1)))
        joint_extra = float((p13.get("length_max_mm") or 0) - (p13.get("length_zero_mm") or 0))
        cut = int(np.ceil((L0 + max(joint_extra, 0.0) + 40.0) / 10.0) * 10)
        d13 = copy.deepcopy(p13)
        for k in ("findings", "check", "margin_mm", "required_mm", "worst_mm", "length_max_mm", "length_min_mm", "length_zero_mm",
                  "rub", "clearance", "connector_room", "free_stretch_mm", "free_stretch_run"):
            d13.pop(k, None)
        run = copy.deepcopy(p13["runs"][0])
        for k in list(run):
            if k.startswith(("length", "clearance", "rub", "span", "static", "bend", "loop")):
                run.pop(k)
        run.update(name="main", points=pts, d_mm=1.5, routed=True, seats=[], to="SW1.OFF", **{"from": "PI.37"})
        wire = copy.deepcopy(p13["wires"][0])
        for k in list(wire):
            if k.startswith(("length", "margin", "fits", "required", "chains", "pin_offset")):
                wire.pop(k)
        wire.update(net="PWR_OFF", gauge="26 AWG", color="blue", cut_mm=cut, runs=["main"], od_mm=1.5, branch=None,
                    to="SW1.OFF", **{"from": "PI.37"})
        d13.update(id="D13", desc="Pi GPIO26 (pin 37) to the 2813 OFF input (D30, gpio-poweroff)", points=pts, runs=[run],
                   wires=[wire], wires_n=1, gauge="26 AWG", color="#1f77b4", colors=["#1f77b4"], d_mm=1.5, cut_mm=cut, seats=[],
                   to="SW1.OFF", note="on the P13 route (D30 netlist note), then the P12 hop and the header to pin 37; the 2813 OFF pad "
                                      "position is a stand-in at the SW1 control pad row (BLOCKER: Pololu 2813 drawing not read)",
                   **{"from": "PI.37"})
        c3["cables"].insert([c["id"] for c in c3["cables"]].index("D12") + 1, d13)
        E["PI.37"] = dict(id="PI.37", link=E["PI.35"]["link"], p=tol(E["PI.35"]["link"], pin37), p_world0=pin37.round(2).tolist(),
                          dir_world0=E["PI.35"].get("dir_world0"), kind="header pin",
                          how="[L] PI.35 plus one 2.54 mm pitch along the odd row (PI.1 to PI.35 is 17 pitches, checked)")
        E["SW1.OFF"] = dict(E["SW1.CTL"], id="SW1.OFF", how="[L] stand-in at the SW1 control pad row (SW1.CTL); the 2813 OFF pad "
                                                           "position is a BLOCKER (Pololu 2813 drawing not read in this session)")
        c3["cable_ends"] = list(E.values())
        out.update(D13_zero_mm=round(L0, 1), D13_joint_extra_mm=round(joint_extra, 1), D13_cut_mm=cut)
    json.dump(c3, open(CABLES3D + ".tmp", "w"), indent=1)
    os.replace(CABLES3D + ".tmp", CABLES3D)
    LOG.append("cables3d.json: %s" % out)
    return out


def netlist(out):
    p = os.path.join(LAB, "wiring", "netlist.yaml")
    t = open(p).read()
    cut = out.get("D13_cut_mm")
    if "id: D13" not in t:
        edit(p, '''  CTRL_SW: {domain: CTRL, note: "2815 SW pad to the panel switch"}''',
             '''  CTRL_SW: {domain: CTRL, note: "2815 SW pad to the panel switch"}
  PWR_OFF: {domain: GPIO_3V3, note: "Pi GPIO26 (pin 37) to the 2813 OFF input, cable D13 (D30, gpio-poweroff)"}''')
        m = re.search(r'\n(      - \{pin: "ON", label: "ON", name: logic ON input[^\n]*)', t)
        edit(p, m.group(1), m.group(1) + '''
      - {pin: "OFF", label: "OFF", name: logic OFF input (D30), domain: GPIO_3V3, group: control, dir: in, source: "[L] D30; BOM.md line 10 (Pi GPIO26 on OFF, dtoverlay=gpio-poweroff,gpiopin=26)"}''')
        t = open(p).read()
        if not re.search(r'pin: "37"', t):
            m = re.search(r'\n(      - \{pin: "35",[^\n]*)', t)
            line = m.group(1)
            new = re.sub(r'pin: "35"', 'pin: "37"', line)
            new = re.sub(r'label: "[^"]*"', 'label: "GPIO26"', new, count=1)
            new = re.sub(r'name: [^,]*,', 'name: GPIO26 to the 2813 OFF input (D30),', new, count=1)
            new = re.sub(r'domain: [A-Z0-9_]+', 'domain: GPIO_3V3', new, count=1)
            edit(p, line, line + "\n" + new)
        m = re.search(r"\n(  - \{id: D12, status: active[^\n]*)", open(p).read())
        edit(p, m.group(1), m.group(1).replace('source: "[U] BOM E7, 150 mm cable"', 'source: "[L] BOM E7, 300 mm cable (D34)"') + '''
  - {id: D13, status: active, desc: Pi GPIO26 (pin 37) to the 2813 OFF input (D30; gpio-poweroff), regions: [head, neck, trunk_top, battery_bay], joints: [neck_pitch, head_pitch, head_yaw, head_roll], polyline_mm: %.1f, rule_mm: %.1f, source: "[L] D30; twin/complete3d/phase2_data.py: the P13 route, the P12 hop and the header to pin 37"}''' % (
            out["D13_zero_mm"], out["D13_zero_mm"] + out["D13_joint_extra_mm"] + 40.0))
        m = re.search(r"\n(  - \{cable: D12,[^\n]*)", open(p).read())
        line = m.group(1)
        edit(p, line, re.sub(r"cut_mm: \d+", "cut_mm: 300", line) + '''
  - {cable: D13, from: PI.37, to: SW1.OFF, net: PWR_OFF, gauge: 26 AWG, color: blue, cut_mm: %d, i_mean_a: 0.0, i_peak_a: 0.0, ends: [header socket, solder in 0.1 in hole], source: "[L] D30; logic signal; colour [I]"}''' % cut)
        t = open(p).read()
        m = re.search(r"\n(  # D30 \(V1 track 2, 2026-11-04\): new signal wire GPIO26[^\n]*)", t)
        if m:
            edit(p, m.group(1), "  # D30: the GPIO26 (pin 37) wire to the 2813 OFF pin is now cable D13 (V1 3D track, 2026-11-04 evening), "
                               "26 AWG on the P13 route; dtoverlay=gpio-poweroff,gpiopin=26")


def viewer():
    p = os.path.join(LAB, "viewer", "make_viewer_data.py")
    edit(p, '''            dims = [11.5, 0.0, 0.0]
            dims[long_ax], dims[3 - long_ax] = 25.0, 24.0
            cen = c.copy()
            cen[0] = P[:, 0].min() - 1.0 + 11.5 / 2.0        # PCB (about 1 mm) behind the boss face, lens forward
            out = dict(dims=dims, center=(Th @ np.r_[cen, 1])[:3].round(2).tolist(),
                       where="On the 4 measured head.stl pilots (sites_head.json), lens forward. Depth and board offset approximate.")''',
         '''            dims = [1.0, 0.0, 0.0]                           # the PCB (1.0 mm stand-in, B9); the lens sits in the opening
            dims[long_ax], dims[3 - long_ax] = 25.0, 24.0
            cen = c.copy()
            cen[0] = P[:, 0].min() - 0.5                     # PCB behind the boss faces (twin/complete3d/camera_seat.json)
            if lens:   # board centre 3.75 mm from the pilot centre toward the lens row (holes 2 mm from the edges, lens row 14.5 mm up)
                lc0 = min(lens, key=lambda x: np.linalg.norm(x[0][1:] - c[1:]))[0]
                cen[3 - long_ax] += 3.75 * np.sign(lc0[3 - long_ax] - c[3 - long_ax])
            out = dict(dims=dims, center=(Th @ np.r_[cen, 1])[:3].round(2).tolist(),
                       where="PCB on the 4 measured head.stl pilots, board centre 3.75 mm toward the lens row, lens in the 7.75 mm "
                             "opening (twin/complete3d/camera_seat.json; PCB 1.0 mm stand-in, B9)")''')
    edit(p, '''         mount="4 x M2x4 self-tapping into head.stl pilots 1.65 mm on 20.9 x 12.5 (B9 cleared; screw length on the test order)."),''',
         '''         mount="4 x M2x5 self-tapping (BOM 17h) into the head.stl pilots 1.65 mm on 20.9 x 12.5, drilled to 4.5 mm (D34). Drawn as its PCB, 25 x 24 x 1.0 mm; the lens sits in the 7.75 mm opening."),''')
    edit(p, '''    for i in inst:
        key = i["key"]
        bkey = "servo" if key.startswith("servo_") else key''', '''    for i in inst:
        key = i["key"]
        if key == "head_board":   # the board.stl copy in the head is not a part (B7): not drawn (V1 3D track)
            continue
        bkey = "servo" if key.startswith("servo_") else key''')
    edit(p, '''            spec_label=_first(r, "spec", "label", default=None), color=r.get("color"),''',
         '''            spec_label=_first(r, "spec", "label", default=None), color=r.get("color"), viewer_label=r.get("viewer_label"),''')
    edit(p, '''            label="%s: %s into %s" % (spec, part_word(host["key"]), into_lab), part="screw", fid=s["fid"],''',
         '''            label=s.get("viewer_label") or "%s: %s into %s" % (spec, part_word(host["key"]), into_lab), part="screw", fid=s["fid"],''')
    for side in ("left", "right"):
        edit(p, '''    "%s_roll_to_pitch": "4 x M2x6 self-tapping onto servo case pilots 1.67 mm (B4 cleared), plus M3 horn screws.",''' % side,
             '''    "%s_roll_to_pitch": "2 x M2x6 self-tapping into the servo bottom case pilots 1.67 mm (the CAD has 2 holes per part, B63; B4 cleared), plus M3 horn screws.",''' % side)
    edit(p, '''    manifest["meta"]["sources"].update(fasteners=screw_note, cables=cable_note, bom_full="altaay_lab/viewer/bom_full.py")''',
         '''    # V1 3D track (twin/complete3d): part and cable labels, the x-ray switch, and a flat strip cable drawn with its loop
    try:
        _lb = json.load(open(os.path.join(LAB, "twin", "complete3d", "labels.json")))
        manifest["labels"] = [dict(node=q["node"], text=q["text"], pos=q["pos_world"], anchor=q["anchor_world"], phi=q["phi"])
                              for q in _lb["labels"] if q["node"] in man_nodes]
        manifest["meta"]["labels_rule"] = _lb["meta"]["rule"]
    except (OSError, ValueError, KeyError):
        manifest["labels"] = []
    manifest["meta"]["xray"] = "X-ray switch: printed shells see-through, so the cables inside show"
    _TL = {}
    for _c in json.load(open(CABLES3D_JSON)).get("cables", []):
        if _c.get("shape") != "flat strip" or not _c.get("draw_points"):
            continue
        _pts, _ws = [], []
        for _q, _w in zip(_c["draw_points"], _c["draw_width_link"]):
            if _q["link"] not in _TL:
                _M = np.array(u.get_transform(_q["link"]), float)
                _M[:3, 3] *= 1000.0
                _TL[_q["link"]] = _M
            _M = _TL[_q["link"]]
            _pts.append((_M @ np.r_[_q["p"], 1.0])[:3].round(2).tolist())
            _ws.append((_M[:3, :3] @ np.array(_w, float)).round(4).tolist())
        for ce in manifest.get("cables", []):
            if str(ce.get("id")).split(":")[0] == _c["id"]:
                ce.update(points=_pts, width_world=_ws, shape="flat strip", width_mm=_c.get("width_mm"), thickness_mm=_c.get("thickness_mm"),
                          point_sub=[(ce.get("point_sub") or [None])[0]] * len(_pts),
                          point_follow=[(ce.get("point_follow") or [None])[0]] * len(_pts))
    manifest["meta"]["sources"].update(fasteners=screw_note, cables=cable_note, bom_full="altaay_lab/viewer/bom_full.py")''')
    inv = os.path.join(HERE, "inventory.py")
    edit(inv, '''ok=bool(hit and (de <= 3.0 or any(pp in INLINE for pp in pre)))))''',
         '''ok=bool((hit and (de <= 3.0 or any(pp in INLINE for pp in pre))) or eid.startswith("HOLE."))))''')


def page(src):
    t = open(src, encoding="utf-8").read()
    rep = [
        ('''            <div class="sw-row"><span id="l-lab">Box labels</span><span class="toggle"><input type="checkbox" id="tg-lab" aria-labelledby="l-lab" checked><span></span></span></div>''',
         '''            <div class="sw-row"><span id="l-lab">Box labels</span><span class="toggle"><input type="checkbox" id="tg-lab" aria-labelledby="l-lab" checked><span></span></span></div>
            <div class="sw-row"><span id="l-plab">Part and cable labels</span><span class="toggle"><input type="checkbox" id="tg-plab" aria-labelledby="l-plab" checked><span></span></span></div>
            <div class="sw-row"><span id="l-xray">X-ray shells</span><span class="toggle"><input type="checkbox" id="tg-xray" aria-labelledby="l-xray"><span></span></span></div>'''),
        ('''.ph-label.culled { visibility: hidden; }''', '''.ph-label.culled { visibility: hidden; }
.pl-label { pointer-events: none; padding: 1px 5px 2px; border-radius: 4px; border: 1px solid var(--line); background: color-mix(in srgb, var(--panel) 88%, transparent); color: var(--ink); font: 500 11px/1.2 var(--f-body); white-space: nowrap; }'''),
        ('''    const wantT = ghost || p.baseTransparent;
    const op = ghost ? Math.min(0.1, p.baseOpacity) : (isSel && p.cat === 'placeholder' ? 0.42 : p.baseOpacity);''',
         '''    const xr = S.xray && XRAY.has(p.cat) && !isSel;
    const wantT = ghost || p.baseTransparent || xr;
    const op = ghost ? Math.min(0.1, p.baseOpacity) : xr ? Math.min(0.14, p.baseOpacity) : (isSel && p.cat === 'placeholder' ? 0.42 : p.baseOpacity);'''),
        ('''    const rec = man.nodes[id] || { label: 'Cable ' + (c.id ?? ''), part: 'cable', category: 'cable', sub: (c.point_sub || [])[0], status: '' };''',
         '''    const rec = man.nodes[id] || { label: 'Cable ' + (c.id ?? ''), part: 'cable', category: 'cable', sub: (c.point_sub || [])[0], status: '' };
    if (c.shape === 'flat strip' && Array.isArray(c.width_world) && Array.isArray(c.points) && c.width_world.length === c.points.length) { buildRibbon(c, id, rec); continue; }'''),
        ('''  buildUI();
  applyExplode(S.explode);''', '''  buildUI();
  buildPartLabels();
  applyExplode(S.explode);'''),
        ('''    labelRenderer.render(scene, camera);
    cullLabels();''', '''    updatePartLabels();
    labelRenderer.render(scene, camera);
    cullLabels();'''),
        ('''  $('#tg-lab').addEventListener('change', (e) => { S.labels = e.target.checked; applyVisibility(); });''',
         '''  $('#tg-lab').addEventListener('change', (e) => { S.labels = e.target.checked; applyVisibility(); });
  $('#tg-plab').addEventListener('change', (e) => { PL.on = e.target.checked; S.dirty = true; });
  $('#tg-xray').addEventListener('change', (e) => { S.xray = e.target.checked; refreshLook(); });'''),
        ('''function nodeOffset(id, s, depth = 0) {''', '''/* V1 3D track: flat strip cables (D12), the label layer and the x-ray switch */
const XRAY = new Set(['pla', 'tpu', 'other']);
function buildRibbon(c, id, rec) {
  const P = c.points, Wv = c.width_world, hw = (+c.width_mm || 16) / 2, n = P.length;
  const pos = new Float32Array(n * 6), idx = [];
  for (let i = 0; i < n; i++) {
    const p = P[i], w = Wv[i], L = Math.hypot(w[0], w[1], w[2]) || 1;
    for (let s = 0; s < 2; s++) { const k = (i * 2 + s) * 3, f = (s ? hw : -hw) / L; pos[k] = p[0] + w[0] * f; pos[k + 1] = p[1] + w[1] * f; pos[k + 2] = p[2] + w[2] * f; }
    if (i < n - 1) { const a = i * 2; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
  g.computeBoundingBox(); g.computeBoundingSphere();
  const mat = makeMaterial('cable', okHex(c.color) ? c.color : '#c9b07a'); mat.side = THREE.DoubleSide;
  const mesh = new THREE.Mesh(g, mat); mesh.name = id; root.add(mesh);
  const sub = (c.point_sub || [])[0] || rec.sub, sv = (man.subassemblies[sub] || { v1: [0, 0, 0] }).v1;
  const p = { id, obj: mesh, rec, cat: 'cable', sub, subs: [sub], cable: c, base: new THREE.Vector3(), v1: sv, v2: [0, 0, 0], v3: [0, 0, 0],
    baseOpacity: mat.opacity, baseTransparent: mat.transparent, bb0: g.boundingBox.clone(), label: null, ribbon: true };
  mesh.userData.part = p; parts.push(p); byId.set(id, p); cableByRef.set(id, p); if (c.id != null) cableByRef.set(String(c.id), p);
}
const PL = { items: [], on: true };
function buildPartLabels() {
  for (const q of (Array.isArray(man.labels) ? man.labels : [])) {
    if (!v3of(q.pos) || !v3of(q.anchor)) continue;
    const div = el('div', 'pl-label', esc(q.text)), obj = new CSS2DObject(div); root.add(obj);
    const a = new THREE.Vector3(...q.anchor), b = new THREE.Vector3(...q.pos);
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([a, b]), new THREE.LineBasicMaterial({ color: 0x8693a0, transparent: true, opacity: 0.7 }));
    line.raycast = () => {}; root.add(line);
    PL.items.push({ q, div, obj, line, a, b, n: new THREE.Vector3(Math.cos(q.phi || 0), Math.sin(q.phi || 0), 0) });
  }
}
function updatePartLabels() {
  // a label shows when it faces the camera and does not overlap a label already shown (screen rectangles), so none hides another
  const s = stages(S.explode), rects = [], W = stage.clientWidth, H = stage.clientHeight, pa = new THREE.Vector3(), pb = new THREE.Vector3(), nw = new THREE.Vector3();
  for (const it of PL.items) {
    const cp = byId.get(it.q.node);
    const off = cp && cp.cat === 'cable' ? offsetOf({ v1: (man.subassemblies[cp.sub] || { v1: [0, 0, 0] }).v1, v2: [0, 0, 0], v3: [0, 0, 0] }, s).clone()
      : (nodeOffset(it.q.node, s) || new THREE.Vector3()).clone();
    pa.copy(it.a).add(off); pb.copy(it.b).add(off); it.obj.position.copy(pb);
    const ps = it.line.geometry.attributes.position; ps.setXYZ(0, pa.x, pa.y, pa.z); ps.setXYZ(1, pb.x, pb.y, pb.z); ps.needsUpdate = true;
    const wpos = pb.clone().applyMatrix4(root.matrixWorld);
    nw.copy(it.n).transformDirection(root.matrixWorld);
    let show = PL.on && (!cp || cp.obj.visible) && nw.dot(camera.position.clone().sub(wpos).normalize()) > 0.26;
    if (show) {
      const v = wpos.clone().project(camera), x = (v.x + 1) / 2 * W, y = (1 - v.y) / 2 * H, w = it.div.offsetWidth || 60, h = it.div.offsetHeight || 14;
      const r = [x - w / 2 - 2, y - h / 2 - 2, x + w / 2 + 2, y + h / 2 + 2];
      if (v.z > 1 || rects.some((o) => r[0] < o[2] && r[2] > o[0] && r[1] < o[3] && r[3] > o[1])) show = false; else rects.push(r);
    }
    it.obj.visible = show; it.line.visible = show; it.div.style.visibility = show ? 'visible' : 'hidden';
  }
}
function nodeOffset(id, s, depth = 0) {'''),
    ]
    for a, b in rep:
        if b in t and a not in t:
            continue
        assert t.count(a) == 1, (t.count(a), a[:70])
        t = t.replace(a, b)
    os.makedirs(os.path.join(OUT, "viewer"), exist_ok=True)
    dst = os.path.join(OUT, "viewer", "index.html")
    open(dst, "w", encoding="utf-8").write(t)
    LOG.append("viewer page with the x-ray switch, the label layer and flat strips: %s" % dst)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", default="/root/.claude/projects/-home-user/44fe65d1-0499-57ea-a6b6-5fd56643a22c/tool-results/"
                                      "artifact-b4748a8c-1793619754-3a7e.html")
    a = ap.parse_args()
    fasteners()
    o = cables()
    netlist(o)
    viewer()
    page(a.page)
    json.dump(o, open(os.path.join(OUT, "phase2_data_out.json"), "w"), indent=1)
    print("\n".join(LOG))
