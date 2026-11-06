"""Write the 3D routes of the dock cables DC1 to DC4 (dock_routes.json, from seats/route2.py) into cables3d/cables3d.json,
the way twin/complete3d/phase2_data.py added D13 (a copy of a routed record, refilled). All points ride on trunk_assembly
(no joint is crossed). Cut = routed length + 2 x 20 mm slack, up to 10 mm (CABLE_MAP length rule). CAD check only.
Run: python3 altaay_lab/twin/dock/dock_cables3d.py [--write]"""
import copy, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
C3P = os.path.join(LAB, "cables3d", "cables3d.json")
R = json.load(open(os.path.join(HERE, "dock_routes.json")))
WIRES = {  # cable: [(run index, from pin, to pin, net, gauge, colour)]
    "DC1": [(0, "DKP.CHG", "DK2.VIN", "CHG_IN", "20 AWG", "red"), (0, "DKP.GND", "DK2.GND", "GND", "26 AWG", "black"),
            (1, "DK2.VOUT", "F2.IN", "CHG_D", "20 AWG", "red"), (2, "F2.OUT", "BMS.P+", "PACK_P", "20 AWG", "red")],
    "DC2": [(0, "DKP.GND", "BMS.P-", "GND", "20 AWG", "black")],
    "DC3": [(0, "DKP.SNS", "RT1.1", "SNS", "26 AWG", "white"), (2, "RT1.2", "BMS.P-", "GND", "26 AWG", "black"),
            (1, "DKP.SNS", "WK1.A", "SNS", "26 AWG", "white"), (3, "WK1.K", "SW1.ON", "SW1_ON", "26 AWG", "white", 0)],
    "DC4": [(0, "DKP.SYS", "DK6.VIN", "SYS_IN", "20 AWG", "orange"), (1, "DK6.VOUT", "SW1.VIN", "PACK_OR", "20 AWG", "orange"),
            (1, "DK6.GND", "SW1.GND", "GND", "26 AWG", "black"), (2, "DK7.VOUT", "SW1.VIN", "PACK_OR", "16 AWG", "red"),
            (2, "DK7.GND", "SW1.GND", "GND", "26 AWG", "black")],
}
DESC = {"DC1": "chest CHG+ to DK2, DK2 to the 5 A fuse F2, F2 to BMS P+ (D43)", "DC2": "chest GND to BMS P- (D43, D50)",
        "DC3": "chest SENSE to the cell NTC and to the wake branch at SW1 ON (D43)", "DC4": "chest SYS to DK6, DK6 and DK7 to SW1 VIN (D50)"}
OD = {"20 AWG": 1.9, "26 AWG": 1.3, "16 AWG": 2.8}
def cut(L): return int(np.ceil((L + 40.0) / 10.0) * 10)
def records():
    C3 = json.load(open(C3P)); tpl = next(c for c in C3["cables"] if c["id"] == "D13")
    out = []
    for cid, ws in WIRES.items():
        runs = list(R["runs"][cid])
        if cid == "DC3":   # the wake branch is inline at the SW1 control pads: WK1.K solders to SW1 ON, no wire run
            p0 = R["terminals"]["SW1.CTL"]
            runs.append(dict(frm="WK1.K", to="SW1.ON", points=[p0, p0], length_mm=0.0))
        rec = copy.deepcopy(tpl)
        for k in ("findings", "check", "margin_mm", "required_mm", "worst_mm", "length_max_mm", "length_min_mm", "length_zero_mm",
                  "rub", "clearance", "connector_room", "free_stretch_mm", "free_stretch_run", "service_loops"):
            rec.pop(k, None)
        rr = []
        for j, r in enumerate(runs):
            run = copy.deepcopy(tpl["runs"][0])
            for k in list(run):
                if k.startswith(("length", "clearance", "rub", "span", "static", "bend", "loop", "service", "ties")): run.pop(k)
            run.update(name="r%d" % j, points=[dict(link="trunk_assembly", p=p) for p in r["points"]], d_mm=1.9, routed=True, seats=[],
                       to=r["to"], **{"from": r["frm"]})
            rr.append(run)
        wl = []
        for wt in ws:
            j, a, b, net, g, col = wt[:6]
            w = copy.deepcopy(tpl["wires"][0])
            for k in list(w):
                if k.startswith(("length", "margin", "fits", "required", "chains", "pin_offset")): w.pop(k)
            Lw = float(runs[j]["length_mm"])
            w.update(length_zero_mm=round(Lw, 1), length_min_mm=round(Lw, 1), length_max_mm=round(Lw, 1))   # no joint crossed
            w.update(net=net, gauge=g, color=col, cut_mm=(wt[6] if len(wt) > 6 else cut(runs[j]["length_mm"])), runs=["r%d" % j], od_mm=OD[g], branch=None,
                     to=b, **{"from": a})
            wl.append(w)
        for run, r in zip(rr, runs):
            run.update(length_zero_mm=round(float(r["length_mm"]), 1), length_min_mm=round(float(r["length_mm"]), 1),
                       length_max_mm=round(float(r["length_mm"]), 1))
        pts = rr[0]["points"]
        Lmax = max(float(r["length_mm"]) for r in runs)
        rec.update(length_zero_mm=round(Lmax, 1), length_min_mm=round(Lmax, 1), length_max_mm=round(Lmax, 1))
        rec.update(id=cid, desc=DESC[cid], points=pts, runs=rr, wires=wl, wires_n=len(wl), gauge=ws[0][4], d_mm=max(OD[w[4]] for w in ws) + 0.6,
                   cut_mm=max(w["cut_mm"] for w in wl), seats=[], joints=[], to=ws[0][2], note="twin/dock/dock_routes.json (seats/route2.py, "
                   "1 mm grid, clear of the printed parts and placed boxes, along the other bundles); trunk only, no joint crossed", **{"from": ws[0][1]})
        out.append(rec)
    return C3, out
if __name__ == "__main__":
    C3, recs = records()
    for r in recs:
        print(r["id"], [(w["from"], w["to"], w["cut_mm"]) for w in r["wires"]])
    if "--write" in sys.argv:
        ids = {r["id"] for r in recs}
        C3["cables"] = [c for c in C3["cables"] if c["id"] not in ids] + recs
        E = {e["id"]: e for e in C3["cable_ends"]}
        for k in [k for k in E if k.startswith("DOCK.")]:
            E.pop(k)
        T = R["terminals"]
        ends = {"DKP": T["DKP.HOLE"], "DK2.VIN": T["DK2.VIN"], "DK2.VOUT": T["DK2.VOUT"], "DK2": T["DK2.VIN"], "F2.IN": T["F2.IN"],
                "F2.OUT": T["F2.OUT"], "RT1.1": T["RT1"], "RT1.2": T["RT1"], "WK1.A": T["SW1.CTL"], "WK1.K": T["SW1.CTL"],
                "DK6.VIN": T["DK6.VIN"], "DK6.VOUT": T["DK6.VOUT"], "DK6": T["DK6.VIN"], "DK7.VIN": T["DK7.VIN"],
                "DK7.VOUT": T["DK7.VOUT"], "DK7": T["DK7.VIN"]}
        for k, p in ends.items():
            E[k] = dict(id=k, link="trunk_assembly", p=p, p_world0=p, kind="dock part pad or lead",
                        how="[L] twin/dock/dock_seats.json and dock_routes.json (D50)")
        C3["cable_ends"] = list(E.values())
        json.dump(C3, open(C3P + ".tmp", "w"), indent=1); os.replace(C3P + ".tmp", C3P)
