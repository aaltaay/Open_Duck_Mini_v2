#!/usr/bin/env python3
"""The dock's design numbers (calc only): paddle and pin force across the docking window, the seat springs and the
switch, the charge times at the MCP73213 EV board's 1.0 A, the tipping of the dock. Writes dock_design.json.

Run: python3 altaay_lab/twin/dock/dock_design.py
Sources are in each entry ([I] web page or data sheet read 2026-11-06, [L] this repo).
"""
import json, os
import numpy as np
import dock_parts as DP

HERE = os.path.dirname(os.path.abspath(__file__))
G = 9.80665


def paddle():
    pin = DP.PIN
    f_mid = pin["force_mid_gf"] / 1000 * G                       # N per pin at mid stroke
    n = len(DP.PADDLE_PINS)
    need = n * f_mid
    f_cf = DP.CF["load_n"]
    out = dict(source_pin="[I] Mill-Max 0933-0-15-20-72-14-11-0 data sheet (mm.digikey.com/Volume0/opasdata/d220001/medias/docus/7171/0933-0-15-20-72-14-11-0.pdf, updated 8/8/25): 45 gf at mid stroke, stroke 1.397 mm, 6 A (4.80 A derated), 40 mOhm max, press-fit into an insulator, hole 1.600 mm max",
               source_spring="[I] Century Spring CF37CS (https://www.centuryspring.com/shop/cf37cs, read 2026-11-06): constant force 0.37 lb = 1.65 N, drum 6.4 mm, 4.75 x 0.08 mm strip 304.8 mm, hole 3.25 mm, $2.82; the page gives no load tolerance: +/- 10 % assumed (BLOCKER, BT1 measures it)",
               pins=n, f_pin_mid_n=round(f_mid, 3), f_needed_n=round(need, 2))
    rows = []
    for tol in (-0.10, 0.0, 0.10):
        F = 2 * f_cf * (1 + tol)
        # pin force model: linear through zero (s_mid = 0.699 mm at 0.441 N) or with a 50 % preload; the face stops at PIN_PROUD
        s_lin = min(DP.PIN_PROUD, pin["stroke"] / 2 * (F / n) / f_mid)
        k_pre = f_mid / 2 / (pin["stroke"] / 2)
        s_pre = min(DP.PIN_PROUD, max(0.0, (F / n - f_mid / 2) / k_pre))
        rows.append(dict(spring_tol=tol, paddle_force_n=round(F, 2), per_pin_n=round(F / n, 3), margin_over_mid=round(F / need - 1, 3),
                         compression_linear_mm=round(s_lin, 3), compression_preload_mm=round(s_pre, 3),
                         all_pins_past_mid=bool(min(s_lin, s_pre) >= pin["stroke"] / 2 - 1e-9)))
    out["rows"] = rows
    out["window"] = "constant force over the whole 0 to 40 mm push (the sim's docked pushes were 2.6 to 30.3 mm, acc10), any yaw the swivel takes (+/- 10 deg), any lateral and vertical error inside the strips: each pin carries F/6"
    out["old"] = dict(design="2 x 37.5 N/m compression springs, no preload, 6 x 0932 at 0.59 N", force_at_push_mm={str(x): round(0.075 * x, 2) for x in (7, 17, 30, 40)},
                      needed_n=round(6 * 0.060 * G, 2), note="0.5 to 2.3 N over the sim's 7 to 30 mm pushes against 3.53 N needed: short pushes left the pins at 0.08 to 0.4 N")
    # the face only meets the chest if a pin needs more than F/6 to reach PIN_PROUD
    out["face_contact"] = "the tips stand %.2f mm proud; at the nominal %.2f N each pin is pressed %.2f to %.2f mm (mid stroke is %.3f mm), so the face stays %.2f mm or more off the chest; the face is only an over-travel stop at %.0f %% of the stroke" % (
        DP.PIN_PROUD, rows[1]["paddle_force_n"], rows[1]["compression_linear_mm"], rows[1]["compression_preload_mm"], pin["stroke"] / 2,
        DP.PIN_PROUD - max(rows[1]["compression_linear_mm"], rows[1]["compression_preload_mm"]), 100 * DP.PIN_PROUD / pin["stroke"])
    # what the duck feels
    fmax = rows[2]["paddle_force_n"]
    out["duck"] = dict(push_max_n=fmax, old_max_n=3.0, belly_force_n=[7.0, 22.0],
                       friction_needed=round(fmax / 7.0, 2), friction_needed_old=round(2.3 / 7.0, 2),
                       note="the paddle pushes the chest back with at most %.2f N (the old paddle 3.0 N at full travel, 1.3 N at the 17 mm mean push); the belly on the seat (7 to 22 N, sim) must hold it: friction %.2f or more at the lightest sit (BLOCKER 10 and BT9; the sim uses 1.0)" % (fmax, fmax / 7.0))
    # constant-force spring set-up
    cf = DP.CF
    ext0 = 104.0 - DP.COIL_C[0]
    out["cf_setup"] = dict(coil_od_mm=cf["coil_od"], strip_extension_rest_mm=ext0, strip_extension_full_mm=ext0 + DP.TRAVEL,
                           rule_min_extension_mm=round(1.25 * cf["drum"], 1),
                           note="[I] a constant-force spring reaches its load after about 1.25 drum diameters of extension (Century Spring constant force spring design guide, general rule; BT1 checks it); %.0f mm at rest" % ext0)
    out["travel"] = dict(rod_mm=DP.ROD["x1"] - DP.ROD["x0"], carriage_end_full_mm=108.0 + DP.TRAVEL, channel_end_mm=149.0,
                         clear_mm=149.0 - (108.0 + DP.TRAVEL))
    return out


def seat():
    sp = DP.SEAT_SPRING
    k = sp["rate"]
    Lr = DP.SPRING_REST_L
    rows = []
    sw_of = 0.78
    k_f = 3 * 3500.0 * (4 * 1.2 ** 3 / 12) / 12.0 ** 3          # PLA beam 12 x 4 x 1.2 mm, E 3.5 GPa (assumed)
    for travel in (0.0, 1.0, 3.0, 5.0, 6.0):
        L = Lr - travel
        Fs = 2 * k * (sp["free"] - L)
        Fsw = sw_of if travel >= 5.0 else 0.0
        Fflex = k_f * max(0.0, travel - 5.0 - 0.55) if travel > 5.55 else 0.0
        rows.append(dict(travel_mm=travel, spring_length_mm=round(L, 2), springs_n=round(Fs, 2), switch_n=round(Fsw + Fflex, 2), total_n=round(Fs + Fsw + Fflex, 2)))
    top_g = 46.85 * 1.24 * 0.45   # volume x PLA density x the light profile's fill fraction (about 0.45 for a 12 mm plate, calc)
    return dict(spring="[I] Century Spring CC-28CS (https://www.centuryspring.com/shop/cc-28cs, read 2026-11-06): music wire, OD 7.14 mm, ID 6.12 mm, free 23.88 mm, 0.25 N/mm, solid 6.1 mm, max deflection 17.78 mm, max load 4.45 N, $2.81",
                switch="[I] Omron D2F-01L (https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf): hinge lever OF max 0.78 N, OT min 0.55 mm, FP max 10 mm, OP 6.8 +/- 1.5 mm",
                post_top_mm=round(DP.POST_TOP, 2), rest_length_mm=Lr, loaded_length_mm=round(Lr - DP.SEAT_TRAVEL, 2),
                deflection_loaded_mm=round(sp["free"] - Lr + DP.SEAT_TRAVEL, 2), max_deflection_mm=sp["max_defl"],
                solid_mm=sp["solid"], top_weight_n=round(top_g / 1000 * G, 2), preload_n=round(2 * k * (sp["free"] - Lr), 2),
                finger_rate_n_per_mm=round(k_f, 2), rows=rows,
                closes="the switch closes at 5.0 of the 6.0 mm of travel at the nominal OP (the slots give +/- 2 mm to set it at BT5); the seat bottoms on its walls at %.1f N in all; a seated duck puts 7 to 22 N on it (sim), so it is always fully down and at 112 mm" % rows[-1]["total_n"],
                old="the old text asked for 8 to 12 N to close: above the sim's lightest sit (7 N), and the old seat top floated at 112 mm with no spring named and no actuator for the switch")


def charge_model(i_cc, i_term_frac=0.10, cap_ah=4.5, r_ohm=0.080, v_cv=8.40, soc0=0.0, dt=10.0):
    """Generic 2S NCA/NMC: OCV per cell from a smooth table (ASSUMPTION, the same kind of model as DOCK_TWIN 11.3); CC then
    CV at v_cv until the current is under i_term_frac x i_cc. Returns (hours, soc at the end)."""
    soc_t = np.array([0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0])
    ocv_t = np.array([3.0, 3.35, 3.46, 3.57, 3.64, 3.70, 3.76, 3.83, 3.91, 3.99, 4.08, 4.14, 4.20])
    soc, t = soc0, 0.0
    while t < 12 * 3600:
        ocv = 2 * np.interp(soc, soc_t, ocv_t)
        i = min(i_cc, (v_cv - ocv) / r_ohm)
        if i < i_term_frac * i_cc:
            break
        soc = min(1.0, soc + i * dt / 3600 / cap_ah); t += dt
    return t / 3600, soc


def charge():
    rows = []
    for i in (1.1, 1.0):
        for soc0, lab in ((0.0, "from empty"), (0.48, "from the 48 % go-home point")):
            h, s = charge_model(i, soc0=soc0)
            rows.append(dict(i_cc_a=i, start=lab, hours=round(h, 2), soc_end=round(s, 3)))
    e = {(r["i_cc_a"], r["start"]): r for r in rows}
    ratio = e[(1.0, "from empty")]["hours"] / e[(1.1, "from empty")]["hours"]
    return dict(source="[I] MCP73213 EV board user's guide DS51849A (ww1.microchip.com/downloads/en/DeviceDoc/51849A.pdf): preset 500 mA, 1000 mA with the PROG via to ground; 10 % termination; U1 MCP73213-A6S/MF (BOM table B-1); 1100 mA needs R_PROG 1.00 k (table 2-1)",
                pick="1.0 A: the PROG via tied to ground on the shipped board (no resistor change)", rows=rows,
                scale_vs_11=round(ratio, 3),
                doc_scaled=dict(from_empty_h=round(4.3 * ratio, 1), go_home_h=round(2.4 * ratio, 1),
                                note="DOCK_TWIN 11.3's charge_awake runs (4.3 h and 2.4 h at 1.1 A, with SYS carrying the load) scaled by this model's ratio"),
                timer_h=6.0, night_h=6.0)


def tipping():
    """Tipping of the dock (calc only). The CG is measured on the model: each printed part at its sliced grams (stl/slice.json)
    at its own mesh centroid, the ballast bars at 7.87 g/cm3, bought parts at 2.0 g/cm3 of their drawn volume (a rough
    stand-in; the adapter off the dock is left out). The support polygon is the convex hull of the rubber feet (4 mm
    radius). For each load the check picks the support edge itself: the hull's farthest point in the load's horizontal
    direction is the pivot, so the lever of the weight is (pivot - CG) along that direction and the overturning moment is
    the load x its height. Target margin 3x: a one-off check of a light printed stand with unmeasured friction, feet and
    floor, and the loads themselves are estimates (calc); 3x covers a CG 1/3 of the way toward the edge or a load twice
    the estimate."""
    import dock_assembly as DA
    from scipy.spatial import ConvexHull
    S = json.load(open(os.path.join(HERE, "stl", "slice.json")))["parts"]
    m, mc = 0.0, np.zeros(3)
    for c in DA.components("dock"):
        if c["id"].startswith(("adapter", "plug")):
            continue
        base = c["id"] if c["id"] in S else c["id"][:-2]
        g = S[base]["grams"] if c["kind"] == "printed" else c["mesh"].volume / 1000 * (7.87 if c["id"].startswith("ballast") else 2.0)
        m += g; mc += g * c["mesh"].center_mass
    cg = mc / m; W = m / 1000 * G
    feet = [c["mesh"].bounds.mean(0)[:2] for c in DA.components("dock") if c["id"].startswith("foot_")]
    ring = np.array([f + 4.0 * np.array([np.cos(a), np.sin(a)]) for f in feet for a in np.linspace(0, 2 * np.pi, 24, endpoint=False)])
    H = ring[ConvexHull(ring).vertices]
    def case(name, F, d, z, extra=None, target=3.0):
        d = np.array(d, float) / np.linalg.norm(d)
        piv = H[np.argmax(H @ d)]; reach = float(piv @ d)
        lever = reach - cg[:2] @ d; resist = W * lever / 1000
        ws = [(W, cg)]
        if extra:                                  # a vertical load (a duck's weight) at a point: its own lever about the same edge
            Wd, pd = extra
            resist += Wd * (reach - np.array(pd[:2]) @ d) / 1000
        over = F * z / 1000
        return dict(case=name, force_n=round(F, 2), height_mm=z, direction=np.round(d, 3).tolist(), pivot_xy=np.round(piv, 1).tolist(),
                    weight_lever_mm=round(float(lever), 1), resist_nm=round(float(resist), 3), overturn_nm=round(over, 3),
                    margin=round(float(resist / over), 2) if over else None, target=target,
                    tips_at_n=round(float(resist / (z / 1000)), 1), ok=bool(over == 0 or resist / over >= target))
    Fp = 2 * DP.CF["load_n"] * 1.1
    duck_w = 2.749 * G
    R = [case("walk-in push on the paddle, +x", Fp, (1, 0), 185.0),
         case("seated duck at the seat's back corner, its weight off-centre, with the paddle push", Fp, (1, 0), 185.0, extra=(duck_w, (-110.0, 20.0))),
         case("seated duck, its CG at the sim's worst lateral error (x -63, y 21)", Fp, (1, 0), 185.0, extra=(duck_w, (-63.0, 21.0)))]
    # the duck's weight inside the hull cannot tip it; its lever about the nearest edge (positive = inside)
    pt = np.array((-110.0, 20.0)); inside = min(float(H[np.argmax(H @ dd)] @ dd - pt @ dd) for dd in
                                            [np.array((np.cos(a), np.sin(a))) for a in np.linspace(0, 2 * np.pi, 72, endpoint=False)])
    dd = pt - H.mean(0); dd /= np.linalg.norm(dd); piv = H[np.argmax(H @ dd)]; reach = float(piv @ dd)
    out_mm = float(pt @ dd - reach)
    corner = dict(case="seated duck's whole weight at the seat's outer back corner (an extreme: its CG cannot sit there)", direction=np.round(dd, 3).tolist(),
                  pivot_xy=np.round(piv, 1).tolist(), outside_mm=round(out_mm, 1), duck_overturn_nm=round(max(out_mm, 0) * duck_w / 1000, 3),
                  dock_resist_nm=round(W * (reach - cg[:2] @ dd) / 1000, 3))
    corner["margin"] = round(corner["dock_resist_nm"] / corner["duck_overturn_nm"], 1) if corner["duck_overturn_nm"] else None
    corner["ok"] = bool(corner["margin"] is None or corner["margin"] >= 3.0)
    kid = [case("a child's bump or pull at the mast top, %s" % nm, 5.0, dd, 460.0) for nm, dd in
           (("+x (toward the back)", (1, 0)), ("-x (toward the seat)", (-1, 0)), ("+y", (0, 1)), ("-y", (0, -1)))]
    return dict(mass_kg=round(m / 1000, 3), cg_mm=np.round(cg, 1).tolist(), support="feet hull (12 feet, 4 mm radius)", hull_xy=np.round(H, 1).tolist(),
                duck_corner_inside_hull_mm=round(inside, 1), cases=R, corner=corner, kid=kid, target=3.0,
                note="the pivot is picked per load from the hull (the farthest support point along the load); the seated duck's weight acts inside the hull (%.0f mm in from the nearest edge), so it only steadies the dock. A 5 N push at the mast top (460 mm) is a stand-in for a child's bump: the tip force per direction is listed; it is under 3x, see 12.6" % inside)


if __name__ == "__main__":
    D = dict(paddle=paddle(), seat=seat(), charge=charge(), tipping=tipping(),
             label="calc only; pin, spring and switch values read from the pages named in each entry")
    json.dump(D, open(os.path.join(HERE, "dock_design.json"), "w"), indent=1)
    print(json.dumps(D, indent=1))
