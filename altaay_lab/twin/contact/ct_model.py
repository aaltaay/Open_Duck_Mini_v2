"""Contact twin for the nest pins, the cloth, and the felt.

Arithmetic only. No MuJoCo, no hardware. Every result carries a label:
cited, calc only, sim pass only, CAD check only, or BLOCKER.

Sources for the numbers that are not cited inside a function:
- QA Technology 100-40 catalog, https://www.qatech.com/downloads/100-40_Catalog.pdf
  opened for this twin. Spring table, tube resistance, tip 40, socket, life.
- Laird Flectron Ni/Cu fabric sheet (Marian copy), 3035-535 PTAF,
  surface resistivity < 0.07 ohm/sq, thickness 0.09 to 0.11 mm.
- Sit pin loads: twin/dock/nest/cad/pins_sit_check.json (sim pass only).
- Sit mass: twin/sit/SIT.md, 2.8078 kg.
- Zone sizes: twin/dock/nest/cad/nestcad_lib.py (the nest CAD; not edited here).
"""

import json
import math
import os

G = 9.81  # m/s^2, MuJoCo default, used only to turn the sit mass into a weight (calc only)
OZ_TO_N = 0.42 / 1.5  # catalog prints 1.5 oz as 0.42 N; keep the table on that scale

# Catalog spring S, force in oz at stroke in mm. Working point 8.05 mm is 5.7 oz / 1.58 N.
SPRING_S_MM = (0.0, 2.54, 5.08, 7.62, 10.16)
SPRING_S_OZ = (1.5, 2.8, 4.1, 5.4, 6.5)
FULL_STROKE_MM = 10.16
RATED_STROKE_MM = 8.05
PRELOAD_N = 0.42
RATED_N = 1.58
PROBE_LIFE = 500000  # cycles at 8.05 mm in the socket, standard spring, not on cloth
PROBE_R_OHM = 0.020  # tube P average resistance, printed as < 20 mOhm
TUBE_P_CURRENT_A = 10.2  # at 120 C; the spring-material note was not opened
TIP40_D_MM = 0.91
TIP40_R_MM = 0.46
TIP_A_MM = TIP40_D_MM / 2.0

# Gold-flashed PdNi on itself, fresh, at 1 N. Not cloth. Fretting paper, normal load 1 N.
# https://centralesupelec.hal.science/hal-03329833/document
METAL_R_AT_1N_OHM = 0.0031
METAL_R_1K_OHM = 0.0102
METAL_R_10K_OHM = 5.050
GOLD_RHO_OHM_M = 22.14e-9  # Wikipedia gold, 20 C

# Laird 3035-535, upper bound, not a typical value.
RS_OHM_SQ = 0.07
CLOTH_T_MM = (0.09, 0.11)

# Felt. US Felt SAE table: psi that gives 10% deflection. Not the nest's unnamed felt.
FELT_10PCT_PSI = {
    "F-1": 21, "F-2": 21, "F-3": 13, "F-5": 6, "F-7": 6,
    "F-10": 4, "F-11": 4, "F-13": 3, "F-15": 3, "F-26": 1,
}
FELT_RECOVERY = 0.99  # Superior Felt, all wool felt type I. Not a pin-crush test.
FELT_T_MM = 2.0  # two 1.0 mm layers, nest CAD

# Zones, nest CAD.
SUN_R = 50.0
GAP = 32.0
RING_R0 = 82.0
RING_R1 = 235.0
TIP_M = 3.0
PAIR_MM = 20.0
PAIR_SPAN_MM = 130.0
PIN_Y = 10.0

# Sit, pins_sit_check.json, chosen pins. (mean, min, max) unless noted.
SIT_MASS_KG = 2.8078
PLANE = dict(
    n=11, all4=11,
    seat_block_N=(0.85, 0.26, 0.91),
    soles_N=(22.85, 22.71, 23.55),
    seat_pin_N=(0.85, 0.82, 0.85),
    bump_pin_N=(1.08, 1.04, 1.11),
    total_pin_N=(3.85, 3.73, 3.93),
    seat_comp_mm=(2.98, 2.76, 3.0),
    bump_comp_mm=(4.55, 4.27, 4.81),
    bumper_gap_mm=(2.95, 2.69, 3.23),
    seat_lift_mm=(0.02, -0.01, 0.24),
)
HEIGHT = dict(
    n=11, all4=11,
    seat_block_N=(2.11, 0.0, 4.83),
    soles_N=(22.14, 19.45, 24.26),
    seat_pin_N=(0.85, 0.82, 0.85),
    bump_pin_N=(0.87, 0.70, 1.05),
    total_pin_N=(3.44, 3.08, 3.73),
    seat_comp_mm=(2.96, 2.76, 3.0),
    bump_comp_mm=(3.14, 1.94, 4.37),
    least_bump_pin_mm=1.85,
    bumper_gap_mm=(4.36, 3.13, 5.57),
)
PROUD = dict(seat=3.0, bump=7.5)

# Currents the studies already use. MCP73213 sheet was not opened.
I_CHARGE = 1.0  # D61 charge current, also TEST_PLAN 20.1
I_TYPICAL = 2.0  # stripe study: charge plus the duck, typical
I_PEAK = 2.8  # stripe study: charge plus the duck, peak
V_PACK = 8.40  # D61 charger setpoint. Datasheet not opened.
V_MAT = 9.5  # D61, calc only, the gated supply
PASCHEN_V = 327.0  # Wikipedia Paschen's law: minimum in air at 1 atm, at 7.5 um
PASCHEN_GAP_UM = 7.5

# Landing scatter, sim pass only, NEST_SIM_V2.md section 3. Not recomputed.
SCATTER = {
    "old_all_y_sigma_mm": 22.3,
    "new_all_y_sigma_mm": 36.1,
    "old_inside_45mm": 0.971,
    "new_inside_45mm": 0.810,
    "old_95th_radial_mm": 37.3,
    "new_95th_radial_mm": 82.8,
    "new_6v_95th_radial_mm": 105.4,
    "steer_first_miss": "8 of 511",
    "steer_why": "5 seat off the sun, 2 on the wrong zone, 1 bumper pin not touching",
    "straight_first_miss": "71",
    "straight_why": "52 a pin on the wrong zone, 19 seat pins off the sun",
}


def spring_n(stroke_mm):
    """Catalog spring S, piecewise linear between the printed ounce points. Calc only.

    Stroke 0 is first touch, where the catalog prints the preload. A gap (negative)
    is no force.
    """
    if stroke_mm < 0:
        return 0.0
    x = min(stroke_mm, SPRING_S_MM[-1])
    for a, b, fa, fb in zip(SPRING_S_MM, SPRING_S_MM[1:], SPRING_S_OZ, SPRING_S_OZ[1:]):
        if x <= b or b == SPRING_S_MM[-1]:
            t = 0.0 if b == a else (x - a) / (b - a)
            return (fa + t * (fb - fa)) * OZ_TO_N
    return SPRING_S_OZ[-1] * OZ_TO_N


def two_point_n(stroke_mm):
    """The nest CAD line: preload to the 8.05 mm point. Calc only, for comparison."""
    if stroke_mm <= 0:
        return 0.0
    return PRELOAD_N + (RATED_N - PRELOAD_N) * stroke_mm / RATED_STROKE_MM


def metal_r_ohm(force_n):
    """Plastic-constriction shape anchored at the cited 3.1 mOhm at 1 N. Calc only.

    R scales as 1/sqrt(F). The anchor is gold-flashed palladium-nickel on itself,
    not gold on cloth. Do not add it on top of the probe's own 20 mOhm.
    """
    if force_n <= 0:
        return None
    return METAL_R_AT_1N_OHM * math.sqrt(1.0 / force_n)


def sheet_r_ohm(distance_mm, a_mm=TIP_A_MM, rs=RS_OHM_SQ):
    """(Rs / 2 pi) ln(d / a). Full-ring return. A tab can be worse. Calc only."""
    if distance_mm <= a_mm:
        return 0.0
    return (rs / (2.0 * math.pi)) * math.log(distance_mm / a_mm)


def tip_pressure(force_n):
    """Mean pressure on the tip 40 face. The real spot is smaller. Calc only."""
    area_mm2 = math.pi * TIP_A_MM ** 2
    mpa = force_n / area_mm2  # N/mm2 == MPa
    psi = mpa * 145.0377
    return {"area_mm2": area_mm2, "mpa": mpa, "psi": psi}


def felt_ratios(psi):
    """How many times the SAE 10% pressure this tip pressure is. Cited grades, calc only."""
    out = {}
    for grade, p10 in FELT_10PCT_PSI.items():
        out[grade] = psi / p10
    return out


def loop(n_plus, n_minus, i_a, r_sheet, r_sun=0.0):
    """Series loop. Open if either pole has no pin. Calc only.

    Each live pin contributes the probe maximum (20 mOhm). Sheet resistance is
    the ring term, split across the live minus pins as if the paths were
    independent. They share a tab, so the split is an optimistic bound.
    r_sun is the sun-side extra (0 when the foil is assumed to short the cloth).
    """
    if n_plus < 1 or n_minus < 1:
        return {"closed": False, "r_ohm": None, "v_drop": None, "p_w": None,
                "i_plus_each": None, "i_minus_each": None, "p_hot_pin_w": None}
    r_plus = PROBE_R_OHM / n_plus
    r_minus = PROBE_R_OHM / n_minus
    r_cloth = r_sheet / n_minus
    r = r_plus + r_minus + r_cloth + r_sun
    i_plus = i_a / n_plus
    i_minus = i_a / n_minus
    # hottest single pin: probe resistance only, the sheet heat is in the cloth
    p_pin = max(i_plus, i_minus) ** 2 * PROBE_R_OHM
    return {
        "closed": True,
        "r_ohm": r,
        "v_drop": i_a * r,
        "p_w": (i_a ** 2) * r,
        "i_plus_each": i_plus,
        "i_minus_each": i_minus,
        "p_hot_pin_w": p_pin,
        "p_cloth_w": (i_a ** 2) * (r_cloth + r_sun),
    }


def pins_at(ox, oy, psi):
    """Pin centers in the nest frame. +x toward the wall. psi=0 faces the room.

    Trunk forward is nest -x when psi is 0, so the rear seat stays nearer the wall
    than the bumper. Pair span 130 mm, pins 20 mm apart. Calc only.
    """
    c, s = math.cos(psi), math.sin(psi)
    out = []
    for name, pole, bx, by in (
        ("seat_L", "plus", 0.0, PIN_Y),
        ("seat_R", "plus", 0.0, -PIN_Y),
        ("bump_L", "minus", PAIR_SPAN_MM, PIN_Y),
        ("bump_R", "minus", PAIR_SPAN_MM, -PIN_Y),
    ):
        nx = ox - bx * c + by * s
        ny = oy + bx * s + by * c
        out.append({"name": name, "pole": pole, "x": nx, "y": ny, "r": math.hypot(nx, ny)})
    return out


def zone(pin, margin):
    r = pin["r"]
    if pin["pole"] == "plus":
        return r <= SUN_R - margin
    return (RING_R0 + margin) <= r <= (RING_R1 - margin)


def classify(ox, oy, psi, margin=TIP_M):
    hits = []
    for p in pins_at(ox, oy, psi):
        ok = zone(p, margin)
        hits.append(ok)
    n_hit = sum(hits)
    n_plus = sum(1 for p, ok in zip(pins_at(ox, oy, psi), hits) if ok and p["pole"] == "plus")
    n_minus = n_hit - n_plus
    # A pair shorts the mat only if its two tips can stand on opposite cloths.
    # Center spacing 20 mm, tip diameter 0.91 mm: the metal span is 20 - 0.91 mm.
    span = PAIR_MM - TIP40_D_MM
    pair_can_bridge = span >= GAP
    return {
        "n_hit": n_hit,
        "n_miss": 4 - n_hit,
        "n_plus": n_plus,
        "n_minus": n_minus,
        "charges": n_plus >= 1 and n_minus >= 1,
        "pair_can_bridge_gap": pair_can_bridge,
        "metal_span_mm": span,
    }


def _farthest(sign_x, sign_y, margin, step, psi_max_deg):
    """How far the seat center can move on one ray and still charge. Calc only."""
    psi_max = math.radians(psi_max_deg)
    n_psi = 1 if psi_max_deg == 0 else int(round(2 * psi_max_deg)) + 1
    last = 0.0
    r = 0.0
    while r <= 90.0:
        ox, oy = sign_x * r, sign_y * r
        good = True
        for k in range(n_psi):
            psi = -psi_max if n_psi == 1 else (-psi_max + (2 * psi_max) * k / (n_psi - 1))
            if not classify(ox, oy, psi, margin)["charges"]:
                good = False
                break
        if not good:
            break
        last = r
        r += step
    return last


def window(margin=TIP_M, step=1.0, psi_max_deg=0.0):
    """Seat-center travel that still puts at least one pin on each cloth.

    Full annulus, no wall cut and no notch. Calc only. The nest CAD's 45 mm
    window includes that cut; this number is the plain annulus.
    """
    return {
        "lateral_mm": _farthest(0.0, 1.0, margin, step, psi_max_deg),
        "toward_wall_mm": _farthest(1.0, 0.0, margin, step, psi_max_deg),
        "away_from_wall_mm": _farthest(-1.0, 0.0, margin, step, psi_max_deg),
        "psi_max_deg": psi_max_deg,
        "margin_mm": margin,
    }


def one_axis_miss_table():
    """Lateral offset of the seat center, heading 0, counted margin. Calc only."""
    rows = []
    for oy in range(0, 81, 5):
        c = classify(0.0, float(oy), 0.0, TIP_M)
        rows.append({"oy_mm": oy, "n_miss": c["n_miss"], "n_plus": c["n_plus"],
                     "n_minus": c["n_minus"], "charges": c["charges"]})
    return rows


def force_block():
    strokes = {
        "seat_design_proud": PROUD["seat"],
        "seat_plane_mean": PLANE["seat_comp_mm"][0],
        "bump_plane_mean": PLANE["bump_comp_mm"][0],
        "bump_plane_min": PLANE["bump_comp_mm"][1],
        "bump_height_mean": HEIGHT["bump_comp_mm"][0],
        "bump_height_least_pin": HEIGHT["least_bump_pin_mm"],
        "bump_flush": PROUD["bump"],
    }
    out = {}
    for name, mm in strokes.items():
        out[name] = {
            "stroke_mm": mm,
            "catalog_table_N": round(spring_n(mm), 4),
            "two_point_line_N": round(two_point_n(mm), 4),
            "metal_floor_mOhm": None if spring_n(mm) == 0 else round(metal_r_ohm(spring_n(mm)) * 1e3, 3),
            "stroke_left_mm": round(FULL_STROKE_MM - mm, 3),
        }
    weight = SIT_MASS_KG * G
    plane_sum = PLANE["soles_N"][0] + PLANE["seat_block_N"][0] + PLANE["total_pin_N"][0]
    return {
        "label_force": "calc only, from the catalog ounce table",
        "label_sit": "sim pass only, pins_sit_check.json, 11 sits",
        "strokes": out,
        "weight_N": round(weight, 3),
        "plane_support_sum_N": round(plane_sum, 3),
        "plane_support_minus_weight_N": round(plane_sum - weight, 3),
        "two_seat_pins_at_3mm_N": round(2 * spring_n(PROUD["seat"]), 3),
        "plane_seat_block_still_N": PLANE["seat_block_N"][0],
        "pins_share_of_weight": round(PLANE["total_pin_N"][0] / weight, 4),
        "soles_share_of_weight": round(PLANE["soles_N"][0] / weight, 4),
    }


def resistance_block():
    distances = (50.0, 100.0, 200.0)
    sheets = {str(int(d)): round(sheet_r_ohm(d), 4) for d in distances}
    # Working sheet term: 100 mm full-ring return. Not a guaranteed upper bound.
    r_sheet = sheet_r_ohm(100.0)
    currents = {"charge_1A": I_CHARGE, "typical_2A": I_TYPICAL, "peak_2_8A": I_PEAK}
    patterns = {
        "four_pins": (2, 2),
        "one_plus_misses": (1, 2),
        "one_minus_misses": (2, 1),
        "one_of_each_misses": (1, 1),
        "both_plus_miss": (0, 2),
        "both_minus_miss": (2, 0),
        "three_miss_one_plus_left": (1, 0),
        "three_miss_one_minus_left": (0, 1),
    }
    table = {}
    for name, (np, nm) in patterns.items():
        table[name] = {}
        for ck, i in currents.items():
            row = loop(np, nm, i, r_sheet, r_sun=0.0)
            clean = {}
            for k, v in row.items():
                if isinstance(v, float):
                    clean[k] = round(v, 5)
                else:
                    clean[k] = v
            table[name][ck] = clean
    no_foil = sheet_r_ohm(SUN_R)
    return {
        "rs_ohm_sq": RS_OHM_SQ,
        "rs_note": "Laird 3035-535 prints < 0.07 ohm/sq. Used as 0.07, an upper bound on resistivity, not on path resistance.",
        "probe_ohm": PROBE_R_OHM,
        "sheet_ohm_at_mm": sheets,
        "sheet_used_mm": 100.0,
        "sheet_used_ohm": round(r_sheet, 4),
        "sun_no_foil_to_rim_ohm": round(no_foil, 4),
        "sun_foil_through_ohm": None,
        "sun_foil_note": "BLOCKER. The Laird sheet gives surface resistivity, not through-thickness. Foil adhesive was not opened.",
        "patterns": table,
        "metal_vs_force_mOhm": {
            "0.70N": round(metal_r_ohm(0.70) * 1e3, 3),
            "0.85N": round(metal_r_ohm(spring_n(3.0)) * 1e3, 3),
            "1.00N": round(metal_r_ohm(1.0) * 1e3, 3),
            "1.07N": round(metal_r_ohm(spring_n(PLANE["bump_comp_mm"][0])) * 1e3, 3),
            "1.50N": round(metal_r_ohm(1.50) * 1e3, 3),
        },
        "holm": (
            "BLOCKER. Pure gold resistivity is cited (%.2f nOhm m at 20 C). "
            "Plating hardness was not opened, so a Holm spot resistance is not computed."
            % (GOLD_RHO_OHM_M * 1e9)
        ),
    }


def felt_block():
    f = spring_n(PROUD["seat"])
    p = tip_pressure(f)
    ratios = felt_ratios(p["psi"])
    # more than 10% is known; the depth is not
    return {
        "tip": "40 round, 0.91 mm, catalog",
        "force_N": round(f, 4),
        "pressure_psi": round(p["psi"], 2),
        "pressure_mpa": round(p["mpa"], 3),
        "area_mm2": round(p["area_mm2"], 4),
        "times_10pct_pressure": {k: round(v, 2) for k, v in ratios.items()},
        "defl_if_only_10pct_mm": round(0.10 * FELT_T_MM, 3),
        "thickness_cap_mm": FELT_T_MM,
        "recovery_cited": FELT_RECOVERY,
        "set_if_crushed_full_thickness_mm": round((1.0 - FELT_RECOVERY) * FELT_T_MM, 4),
        "set_if_only_10pct_mm": round((1.0 - FELT_RECOVERY) * 0.10 * FELT_T_MM, 4),
        "extra_stroke_cap_mm": FELT_T_MM,
        "flush_plus_cap_mm": round(PROUD["bump"] + FELT_T_MM, 3),
        "still_under_full_stroke": PROUD["bump"] + FELT_T_MM < FULL_STROKE_MM,
    }


def safety_block():
    return {
        "paschen_V": PASCHEN_V,
        "paschen_gap_um": PASCHEN_GAP_UM,
        "pack_over_paschen": round(V_PACK / PASCHEN_V, 4),
        "mat_over_paschen": round(V_MAT / PASCHEN_V, 4),
        "air_arc_sustained": False,
        "why": "Both voltages are a few percent of the 327 V minimum. No gap in air at 1 atm breaks down below that minimum.",
        "inrush_J": None,
        "inrush_note": "BLOCKER. Input capacitance of the unseated charger was not opened, so 0.5 C V^2 is not computed.",
        "walk_clearance_mm": 77.4,
        "walk_clearance_label": "CAD check only, NEST_CAD.md check D",
    }


def miss_census(step=5.0, psi_step_deg=15.0):
    """Count seat-center cells by how many pins miss. Full annulus. Calc only."""
    bins = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    charge = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    examples = {}
    n = 0
    ox = -80.0
    while ox <= 80.0:
        oy = -80.0
        while oy <= 80.0:
            psi = -math.pi
            while psi < math.pi - 1e-9:
                c = classify(ox, oy, psi, TIP_M)
                bins[c["n_miss"]] += 1
                if c["charges"]:
                    charge[c["n_miss"]] += 1
                key = c["n_miss"]
                if key not in examples:
                    examples[key] = {"ox": ox, "oy": oy, "psi_deg": round(math.degrees(psi), 1),
                                     "n_plus": c["n_plus"], "n_minus": c["n_minus"],
                                     "charges": c["charges"]}
                n += 1
                psi += math.radians(psi_step_deg)
            oy += step
        ox += step
    return {"cells": n, "by_miss": bins, "charging_by_miss": charge, "example": examples}


def geometry_block():
    head0 = window(TIP_M, 1.0, 0.0)
    # spot checks
    center = classify(0.0, 0.0, 0.0, TIP_M)
    lat40 = classify(0.0, 40.0, 0.0, TIP_M)
    lat60 = classify(0.0, 60.0, 0.0, TIP_M)
    return {
        "metal_span_mm": round(PAIR_MM - TIP40_D_MM, 3),
        "gap_mm": GAP,
        "pair_cannot_bridge": (PAIR_MM - TIP40_D_MM) < GAP,
        "window_heading0": head0,
        "at_center": center,
        "lateral_40mm": lat40,
        "lateral_60mm": lat60,
        "lateral_table": one_axis_miss_table(),
        "census": miss_census(),
        "full_annulus_note": "No wall cut and no notch. The nest CAD coverage, which has both, reported wrong-pole share 0. This script does not replace that.",
    }


def build():
    return {
        "labels": "cited numbers are named in CONTACT_TWIN.md; forces and ohms below are calc only unless the key says sim",
        "force": force_block(),
        "resistance": resistance_block(),
        "felt": felt_block(),
        "safety": safety_block(),
        "geometry": geometry_block(),
        "scatter_sim_pass_only": SCATTER,
    }


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "results.json")
    data = build()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
        f.write("\n")
    fce = data["force"]
    print("seat 3.0 mm", fce["strokes"]["seat_design_proud"]["catalog_table_N"], "N")
    print("bump plane mean", fce["strokes"]["bump_plane_mean"]["catalog_table_N"], "N")
    print("weight", fce["weight_N"], "support", fce["plane_support_sum_N"])
    print("sheet 100 mm", data["resistance"]["sheet_used_ohm"])
    print("four at 1 A", data["resistance"]["patterns"]["four_pins"]["charge_1A"])
    print("one each at 2.8 A", data["resistance"]["patterns"]["one_of_each_misses"]["peak_2_8A"])
    print("window", data["geometry"]["window_heading0"])
    print("census", data["geometry"]["census"]["by_miss"], data["geometry"]["census"]["charging_by_miss"])
    print("examples", data["geometry"]["census"]["example"])
    print("bridge", data["geometry"]["pair_cannot_bridge"], data["geometry"]["metal_span_mm"])
    print("felt psi", data["felt"]["pressure_psi"], "x F-1", data["felt"]["times_10pct_pressure"]["F-1"])
    print("wrote", os.path.basename(path))


if __name__ == "__main__":
    main()
