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
GAUGE = {("DKP.CHG", "DK2.VIN"): ("20 AWG", "red"), ("DKP.GND", "DK2.GND"): ("26 AWG", "black"), ("DK2.VOUT", "F2.IN"): ("20 AWG", "red"),
         ("F2.OUT", "BMS.P+"): ("20 AWG", "red"), ("DKP.GND", "BMS.P-"): ("20 AWG", "black"), ("DKP.SNS", "RT1.1"): ("26 AWG", "white"),
         ("RT1.2", "BMS.P-"): ("26 AWG", "black"), ("DKP.SNS", "WK1.A"): ("26 AWG", "white"), ("DKP.SYS", "DK6.VIN"): ("20 AWG", "orange"),
         ("DK6.VOUT", "SW1.VIN"): ("20 AWG", "orange"), ("DK6.GND", "SW1.GND"): ("26 AWG", "black"), ("DK7.VOUT", "SW1.VIN"): ("16 AWG", "red"),
         ("DK7.GND", "SW1.GND"): ("26 AWG", "black"), ("WK1.K", "SW1.ON"): ("26 AWG", "white")}
NET = {"DKP.CHG": "CHG_IN", "DK2.VOUT": "CHG_D", "F2.OUT": "PACK_P", "DKP.SNS": "SNS", "DKP.SYS": "SYS_IN", "DK6.VOUT": "PACK_OR",
       "DK7.VOUT": "PACK_OR", "WK1.K": "SW1_ON"}
DESC = {"DC1": "chest CHG+ to DK2, DK2 to the 5 A fuse F2, F2 to BMS P+ (D43)", "DC2": "chest GND to BMS P- (D43, D50)",
        "DC3": "chest SENSE to the cell NTC and to the wake branch at SW1 ON (D43)", "DC4": "chest SYS to DK6, DK6 and DK7 to SW1 VIN (D50)"}
OD = {"20 AWG": 1.9, "26 AWG": 1.3, "16 AWG": 2.8}
def cut(L): return int(np.ceil((L + 40.0) / 10.0) * 10)
def records():
    """one cables3d run per wire, from that wire's own route in dock_routes.json (route2.py self-check: no shared runs, no point
    inside a body); WK1.K to SW1.ON is an inline joint at the SW1 pads: a zero-length run of its own"""
    C3 = json.load(open(C3P)); tpl = next(c for c in C3["cables"] if c["id"] == "D13")
    out = []
    for cid in ("DC1", "DC2", "DC3", "DC4"):
        routes = list(R["runs"][cid])
        if cid == "DC3":
            p0 = R["terminals"]["SW1.CTL"]
            routes.append(dict(wire_from="WK1.K", wire_to="SW1.ON", frm="SW1.CTL", to="SW1.CTL", points=[p0, p0], length_mm=0.0))
        rec = copy.deepcopy(tpl)
        for k in ("findings", "check", "margin_mm", "required_mm", "worst_mm", "length_max_mm", "length_min_mm", "length_zero_mm",
                  "rub", "clearance", "connector_room", "free_stretch_mm", "free_stretch_run", "service_loops"):
            rec.pop(k, None)
        rr, wl = [], []
        for j, r in enumerate(routes):
            g, col = GAUGE[(r["wire_from"], r["wire_to"])]
            L = float(r["length_mm"])
            run = copy.deepcopy(tpl["runs"][0])
            for k in list(run):
                if k.startswith(("length", "clearance", "rub", "span", "static", "bend", "loop", "service", "ties")): run.pop(k)
            run.update(name="r%d" % j, points=[dict(link="trunk_assembly", p=p) for p in r["points"]], d_mm=OD[g], routed=True, seats=[],
                       to=r["wire_to"], length_zero_mm=round(L, 1), length_min_mm=round(L, 1), length_max_mm=round(L, 1),
                       **{"from": r["wire_from"]})
            rr.append(run)
            w = copy.deepcopy(tpl["wires"][0])
            for k in list(w):
                if k.startswith(("length", "margin", "fits", "required", "chains", "pin_offset")): w.pop(k)
            c = 0 if r["wire_from"] == "WK1.K" else cut(L)
            w.update(net=NET.get(r["wire_from"], "GND"), gauge=g, color=col, cut_mm=c, runs=["r%d" % j], od_mm=OD[g], branch=None,
                     length_zero_mm=round(L, 1), length_min_mm=round(L, 1), length_max_mm=round(L, 1), to=r["wire_to"],
                     **{"from": r["wire_from"]})
            wl.append(w)
        Lmax = max(float(r["length_mm"]) for r in routes)
        rec.update(id=cid, desc=DESC[cid], points=rr[0]["points"], runs=rr, wires=wl, wires_n=len(wl), gauge=wl[0]["gauge"],
                   d_mm=max(w["od_mm"] for w in wl) + 0.6, cut_mm=max(w["cut_mm"] for w in wl), seats=[], joints=[],
                   length_zero_mm=round(Lmax, 1), length_min_mm=round(Lmax, 1), length_max_mm=round(Lmax, 1),
                   to=wl[0]["to"], note="twin/dock/dock_routes.json (seats/route2.py: one route per wire, every placed body an obstacle, "
                   "self-check passed); trunk only, no joint crossed", **{"from": wl[0]["from"]})
        out.append(rec)
    runs_used = [(r["id"], w["runs"][0]) for r in out for w in r["wires"]]
    assert len(runs_used) == len(set(runs_used)), "a wire reuses another wire's run"
    return C3, out


if __name__ == "__main__":
    C3, recs = records()
    for r in recs:
        print(r["id"], [(w["from"], w["to"], w["cut_mm"]) for w in r["wires"]])
    if "--write" in sys.argv:
        ids = {r["id"] for r in recs}
        C3["cables"] = [c for c in C3["cables"] if c["id"] not in ids] + recs
        # D50: P7's load run (F1.OUT to the fuse lead extension at JFO, then to DK7 VIN) re-routed to DK7 VIN
        p7 = next(c for c in C3["cables"] if c["id"] == "P7")
        r7 = R["runs"]["P7"][0]; L7 = float(r7["length_mm"])
        run = next(r for r in p7["runs"] if r["name"] == "load")
        for k in [k for k in run if k.startswith(("clearance", "rub", "static"))]:
            run.pop(k)
        run.update(points=[dict(link="trunk_assembly", p=p) for p in r7["points"]], to="DK7.VIN", length_zero_mm=round(L7, 1),
                   length_min_mm=round(L7, 1), length_max_mm=round(L7, 1), clearance_min_mm=round(float(r7["min_clear_centre_mm"]) - 1.4, 2))
        for w in p7["wires"]:
            if "load" in (w.get("runs") or []):
                w.update(to="DK7.VIN", length_zero_mm=round(L7, 1), length_min_mm=round(L7, 1), length_max_mm=round(L7, 1))
        p7.update(length_zero_mm=max(L7, 51.7), length_min_mm=max(L7, 51.7), length_max_mm=max(L7, 51.7))
        E = {e["id"]: e for e in C3["cable_ends"]}
        for k in [k for k in E if k.startswith("DOCK.")]:
            E.pop(k)
        T = R["terminals"]
        ends = {"DKP": T["DKP.CHG"], "DKP.CHG": T["DKP.CHG"], "DKP.SNS": T["DKP.SNS"], "DKP.GND": T["DKP.GND"], "DKP.SYS": T["DKP.SYS"],
                "DK2.GND": T["DK2.GND"], "DK6.GND": T["DK6.GND"], "DK7.GND": T["DK7.GND"], "DK2.VIN": T["DK2.VIN"], "DK2.VOUT": T["DK2.VOUT"], "DK2": T["DK2.VIN"], "F2.IN": T["F2.IN"],
                "F2.OUT": T["F2.OUT"], "RT1.1": T["RT1"], "RT1.2": T["RT1"], "WK1.A": T["SW1.CTL"], "WK1.K": T["SW1.CTL"],
                "DK6.VIN": T["DK6.VIN"], "DK6.VOUT": T["DK6.VOUT"], "DK6": T["DK6.VIN"], "DK7.VIN": T["DK7.VIN"],
                "DK7.VOUT": T["DK7.VOUT"], "DK7": T["DK7.VIN"]}
        for k, p in ends.items():
            E[k] = dict(id=k, link="trunk_assembly", p=p, p_world0=p, kind="dock part pad or lead",
                        how="[L] twin/dock/dock_seats.json and dock_routes.json (D50)")
        C3["cable_ends"] = list(E.values())
        json.dump(C3, open(C3P + ".tmp", "w"), indent=1); os.replace(C3P + ".tmp", C3P)
