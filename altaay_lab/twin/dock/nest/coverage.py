#!/usr/bin/env python3
"""coverage.py: calc only. (1) how forgiving each contact layout is for the real sit contact points,
(2) coil coupling against sideways offset for the wireless options, (3) the wireless power and heat budget.
Inputs: sit_contacts.json (sim pass only), stripes/twozone.json numbers quoted from STRIPE_MAT_STUDY 1.5.
  python3 coverage.py
Writes coverage.json.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SC = json.load(open(os.path.join(HERE, "sit_contacts.json")))
G = SC["flat_floor"]["geometry"]
SEAT_X = float(np.mean(G["seat"]["within_1mm_of_lowest_x"]))        # trunk frame, mm
BUMP_X = float(np.mean(G["bumper"]["within_1mm_of_lowest_x"]))
D_SB = BUMP_X - SEAT_X                                               # seat button to bumper button
PIN_Y = 10.0                                                         # two pins per net at y +/-10 mm
TIP_M = 3.0                                                          # a pin counts only when 3 mm inside its zone
SOLE = [(c["centre_of_pressure_trunk_frame_mm"]) for k, c in SC["flat_floor"]["contacts"].items() if "foot" in k]
rng = np.random.default_rng(7)


def pins(x, y, psi):
    """world positions of the 2 seat pins and the 2 bumper pins; (x, y) is the seat button centre, psi the heading"""
    c, s = np.cos(psi), np.sin(psi)
    out = {}
    for nm, dx in (("seat", 0.0), ("bump", D_SB)):
        for sg in (-1, 1):
            out[(nm, sg)] = (x + dx * c - sg * PIN_Y * s, y + dx * s + sg * PIN_Y * c)
    return out


def ok_concentric(x, y, psi, Rc, gap, Rout):
    """centre disc radius Rc = one pole, ring Rc+gap to Rout = the other. Powered: at least one seat pin on the disc and
    one bumper pin on the ring, and no pin on the wrong zone (that would short through the two pins of a net)"""
    P = pins(x, y, psi)
    r = {k: np.hypot(*v) for k, v in P.items()}
    seat_on = [(r[("seat", s)] < Rc - TIP_M) for s in (-1, 1)]
    seat_bad = [(r[("seat", s)] > Rc + gap - TIP_M) & (r[("seat", s)] < Rout + TIP_M) for s in (-1, 1)]
    bump_on = [(r[("bump", s)] > Rc + gap + TIP_M) & (r[("bump", s)] < Rout - TIP_M) for s in (-1, 1)]
    bump_bad = [(r[("bump", s)] < Rc + TIP_M) for s in (-1, 1)]
    return (seat_on[0] | seat_on[1]) & (bump_on[0] | bump_on[1]) & ~(seat_bad[0] | seat_bad[1]) & ~(bump_bad[0] | bump_bad[1])


def ok_bands(x, y, psi, A0, A1, gap, B1, half_w):
    """two bands parallel to the wall: band A from A0 to A1 (distance from the wall), band B from A1+gap to B1; x is the
    distance from the wall of the seat button, y along the wall. Either polarity accepted (ideal bridge)."""
    P = pins(x, y, psi)
    def zone(p):
        px, py = p
        inside = abs(py) < half_w - TIP_M
        a = (px > A0 + TIP_M) & (px < A1 - TIP_M) & inside
        b = (px > A1 + gap + TIP_M) & (px < B1 - TIP_M) & inside
        return a, b
    sa0, sb0 = zone(P[("seat", -1)]); sa1, sb1 = zone(P[("seat", 1)])
    ba0, bb0 = zone(P[("bump", -1)]); ba1, bb1 = zone(P[("bump", 1)])
    seatA, seatB, bumpA, bumpB = sa0 | sa1, sb0 | sb1, ba0 | ba1, bb0 | bb1
    return (seatA & bumpB & ~seatB & ~bumpA) | (seatB & bumpA & ~seatA & ~bumpB)


def ok_leaves(x, y, psi, gap=40.0, half_w=300.0, depth=(90.0, 490.0)):
    """yesterday's two-zone mat (one leaf per foot), the sole inner-edge strip as a 76 mm line; (x, y) is the trunk origin,
    x the distance from the wall. Left leaf y > gap/2, right leaf y < -gap/2. Wrong way round does not charge."""
    c, s = np.cos(psi), np.sin(psi)
    ok = np.ones_like(x, dtype=bool)
    for (sx, sy), want in zip(SOLE, (1, -1)) if SOLE[0][1] > 0 else zip(SOLE[::-1], (1, -1)):
        ey = sy - np.sign(sy) * 7.9                                   # inner edge of the flat face
        for a in (-38.0, 38.0):
            px = x + (sx + a) * c - ey * s
            py = y + (sx + a) * s + ey * c
            ok &= (want * py > gap / 2 + TIP_M) & (abs(py) < half_w - TIP_M) & (px > depth[0]) & (px < depth[1])
    return ok


def window_concentric(Rc, gap, Rout):
    """largest seat-button offset from the centre that charges at every heading (grid), and at heading within +/-180"""
    best = 0.0
    psi = np.radians(np.arange(0, 360, 2.0))
    th = np.radians(np.arange(0, 360, 5.0))
    for e in np.arange(2, 80, 1.0):
        X = e * np.cos(th)[:, None] + 0 * psi[None, :]
        Y = e * np.sin(th)[:, None] + 0 * psi[None, :]
        if ok_concentric(X, Y, psi[None, :] + 0 * X, Rc, gap, Rout).all():
            best = e
        else:
            break
    return best


def mc(fn, n, sx, sy, syaw, centre):
    x = centre[0] + rng.normal(0, sx, n)
    y = centre[1] + rng.normal(0, sy, n)
    psi = np.radians(rng.normal(0, syaw, n))
    return float(fn(x, y, psi).mean())


# ---------------------------------------------------------------- coils
MU0 = 4e-7 * np.pi


def ring_M(r1, r2, dz, dx, n=180):
    """mutual inductance of two filament rings (radii r1, r2 m), axial gap dz, sideways offset dx: Neumann integral"""
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    a = np.c_[r1 * np.cos(t), r1 * np.sin(t)]
    b = np.c_[dx + r2 * np.cos(t), r2 * np.sin(t)]
    da = np.c_[-r1 * np.sin(t), r1 * np.cos(t)] * (2 * np.pi / n)
    db = np.c_[-r2 * np.sin(t), r2 * np.cos(t)] * (2 * np.pi / n)
    R = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(-1) + dz * dz)
    return MU0 / (4 * np.pi) * ((da[:, None, :] * db[None, :, :]).sum(-1) / R).sum()


def coil_radii(od, idm, turns):
    return np.linspace(idm / 2, od / 2, turns) / 1000.0


def coil_L(od, idm, turns, wire_r=0.0004):
    r = coil_radii(od, idm, turns)
    L = 0.0
    for i, ri in enumerate(r):
        L += MU0 * ri * (np.log(8 * ri / wire_r) - 2.0)
        for j, rj in enumerate(r):
            if i != j:
                L += ring_M(ri, rj, 0.0, 0.0, n=120)
    return L


def pair_M(tx, rx, gap, dx):
    return sum(ring_M(a, b, gap / 1000.0, dx / 1000.0) for a in coil_radii(*tx) for b in coil_radii(*rx))


def eta_max(k, Q1, Q2):
    f = k * k * Q1 * Q2
    return f / (1 + np.sqrt(1 + f)) ** 2


def coil_cases():
    cases = {
        "A: phone-size pair, Tx 50/20 mm, Rx 45/20 mm (coil outer/inner diameter), gap 4 mm": ((50, 20, 10), (45, 20, 12), 4),
        "B: 82/30 mm hobby pair (the size of DFRobot FIT0703), gap 6 mm": ((82, 30, 12), (82, 30, 12), 6),
        "C: seat-block Rx 30/12 mm on a 50/20 mm Tx, gap 4 mm": ((50, 20, 10), (30, 12, 10), 4),
        "D: wide Tx 160/60 mm under the nest, Rx 50/20 mm in the keel, gap 6 mm": ((160, 60, 14), (50, 20, 12), 6),
        "E: wide Tx 160/60 mm, Rx 82/30 mm, gap 6 mm": ((160, 60, 14), (82, 30, 12), 6),
    }
    out = {}
    for nm, (tx, rx, gap) in cases.items():
        L1, L2 = coil_L(*tx), coil_L(*rx)
        rows = []
        for dx in (0, 5, 10, 15, 20, 30, 40, 50, 60):
            M = pair_M(tx, rx, gap, dx)
            k = M / np.sqrt(L1 * L2)
            rows.append(dict(offset_mm=dx, k=round(float(k), 3), rel_M=None, link_eff_bound_Q60=round(float(eta_max(abs(k), 60, 60)), 3)))
        for r in rows:
            r["rel_M"] = round(r["k"] / rows[0]["k"], 2)
        tol70 = max([r["offset_mm"] for r in rows if r["rel_M"] >= 0.7] or [0])
        tol50 = max([r["offset_mm"] for r in rows if r["rel_M"] >= 0.5] or [0])
        out[nm] = dict(rows=rows, offset_where_coupling_keeps_70pct_mm=tol70, offset_where_coupling_keeps_50pct_mm=tol50,
                       note="air-core filament model, no ferrite: ferrite raises k but the shape against offset is similar; "
                            "link bound is the textbook k^2 Q1 Q2 formula with Q 60 on both coils (assumption)")
    return out


if __name__ == "__main__":
    R = dict(label="calc only", inputs=dict(seat_button_x=round(SEAT_X, 1), bumper_button_x=round(BUMP_X, 1), spacing_mm=round(D_SB, 1),
                                           pin_pair_half_spacing_mm=PIN_Y, pin_margin_mm=TIP_M, sole_cop=SOLE))
    # 1. concentric design search
    best = None
    rows = []
    for gap in (25, 32, 40):
        for Rc in range(36, 62, 2):
            e = window_concentric(Rc, gap, 235.0)
            rows.append(dict(gap=gap, Rc=Rc, any_heading_radius_mm=e))
            if gap == 32 and (best is None or e > best[1]):
                best = (Rc, e)
    R["concentric_search"] = rows
    Rc, e = best
    R["concentric_pick"] = dict(centre_disc_radius_mm=Rc, gap_mm=32, ring_outer_radius_mm=235, any_heading_window_radius_mm=e)
    print("concentric pick Rc", Rc, "window +/-", e)
    # 2. bands: A 110..(110+A_w), gap 32, B to 480
    A0, gap, B1 = 140.0, 32.0, 520.0
    bands = []
    for Aw in (80, 95, 110, 125):
        A1 = A0 + Aw
        for yaw in (0, 20, 30, 45, 60):
            xs = np.arange(A0, A1, 0.5)
            okx = ok_bands(xs, 0 * xs, np.radians(yaw) + 0 * xs, A0, A1, gap, B1, 280.0)
            okx2 = ok_bands(xs, 0 * xs, np.radians(-yaw) + 0 * xs, A0, A1, gap, B1, 280.0)
            both = okx & okx2
            span = float(xs[both].max() - xs[both].min()) if both.any() else 0.0
            bands.append(dict(band_A_depth=Aw, yaw=yaw, fore_aft_window_mm=round(span, 1), centre_from_wall=round(float(xs[both].mean()), 1) if both.any() else None))
    R["bands_search"] = bands
    bp = [b for b in bands if b["band_A_depth"] == 110]
    R["bands_pick"] = dict(band_A=[140, 250], gap=32, band_B=[282, 520], half_width_mm=280, windows=bp,
                           along_wall_window_mm="+/-%d" % (280 - 3 - 10 - 20))
    print("bands", [(b["yaw"], b["fore_aft_window_mm"]) for b in bp])
    # 3. Monte Carlo: first-sit success for assumed landing scatter (1 sigma), three layouts
    scat = [("straight walk-in, as DEEP_ANALYSIS 2.2 (p95 about 2 sigma)", 15, 17, 4),
            ("walk-in then the turn on the spot: walk-in scatter plus the turn scatter of turn_probe.json (sim), heading held by the IMU", 18, 18, 6),
            ("after a turn on the spot, mild guess", 25, 25, 10),
            ("after a turn on the spot, sloppy guess", 40, 40, 20),
            ("very sloppy", 60, 60, 30)]
    cx_b = [b for b in bp if b["yaw"] == 20][0]["centre_from_wall"]
    mcr = []
    for nm, sx, sy, syaw in scat:
        n = 400000
        p_c = mc(lambda x, y, p: ok_concentric(x, y, p, Rc, 32.0, 235.0), n, sx, sy, syaw, (0, 0))
        p_b = mc(lambda x, y, p: ok_bands(x, y, p, 140.0, 250.0, 32.0, 520.0, 280.0), n, sx, sy, syaw, (cx_b, 0))
        p_l = mc(lambda x, y, p: ok_leaves(x, y, p), n, sx, sy, syaw, (297.0, 0))
        row = dict(case=nm, sigma_mm=[sx, sy], sigma_yaw_deg=syaw)
        for key, p in (("nest_sun_concentric", p_c), ("pond_two_bands", p_b), ("lily_two_leaves_feet", p_l)):
            row[key] = dict(first_sit=round(p, 3), within_3_sits=round(1 - (1 - p) ** 3, 3))
        mcr.append(row)
        print(nm, {k: v for k, v in row.items() if isinstance(v, dict)})
    R["monte_carlo_first_sit"] = dict(note="assumed normal landing scatter, not a walk sim; 'within 3 sits' assumes each re-sit is a fresh independent draw", rows=mcr)
    # 4. coils
    R["coils"] = coil_cases()
    for k, v in R["coils"].items():
        print(k, [(r["offset_mm"], r["k"], r["rel_M"]) for r in v["rows"]], v["offset_where_coupling_keeps_70pct_mm"])
    # 5. power and heat budget (calc only)
    chg = 8.4 * 1.0
    load_twin, sys_typ, sys_pk = 0.62 * 8.4, 9.0 * 1.0, 9.0 * 1.8
    P = dict(charge_W=chg, docked_load_twin_W=round(load_twin, 1), sys_typ_W=sys_typ, sys_peak_W=sys_pk,
             total_typ_twin_W=round(chg + load_twin, 1), total_typ_interface_W=round(chg + sys_typ, 1), total_peak_W=round(chg + sys_pk, 1))
    heat = []
    for nm, rx_out, eff_rx, eff_link, eff_chg in (("Qi 15 W class (receiver output 15 W max)", 15.0, 0.88, 0.75, 0.93),
                                                  ("hobby 36 W pair (12 V 3 A class), run at 17.4 W", 17.4, 0.88, 0.75, 0.93),
                                                  ("hobby 36 W pair at the 24.6 W peak", 24.6, 0.88, 0.75, 0.93)):
        rx_loss = rx_out * (1 / eff_rx - 1)
        wall = rx_out / eff_link
        tx_loss = wall - rx_out - rx_loss
        chg_loss = min(rx_out, chg / eff_chg) * (1 - eff_chg)
        heat.append(dict(case=nm, receiver_output_W=rx_out, loss_in_receiver_coil_and_rectifier_W=round(rx_loss, 1),
                         loss_in_dock_W=round(tx_loss, 1), from_the_wall_W=round(wall, 1), loss_in_switching_charger_in_trunk_W=round(chg_loss, 2),
                         assumptions="receiver 88 % (inside the 85 to 93 % of DOCK_RESEARCH 3.4), end to end 75 % (est), switching charger 93 % (TI BQ25883 figure at 1 A)"))
    R["wireless_budget"] = dict(needs=P, heat=heat)
    # capacitive check
    eps0 = 8.854e-12
    A = 0.080 * 0.032
    C = eps0 * 3.0 * A / 0.001
    R["capacitive"] = dict(plate="the seat block face 80 x 32 mm through 1 mm of TPU (relative permittivity 3, est)", C_pF=round(C * 1e12, 1),
                           two_plates_in_series_pF=round(C * 1e12 / 2, 1),
                           volts_rms_across_gap_for_2A_at_1MHz=round(2.0 / (2 * np.pi * 1e6 * C / 2), 0),
                           note="about 2 A at 9 V needs kilovolts across the plates at 1 MHz: not a home product")
    # cloth zone spreading resistance
    Rs = 0.07
    R["cloth_zone"] = dict(sheet_ohm_sq=Rs, spreading_resistance_ohm_1mm_tip_to_50mm=round(Rs / (2 * np.pi) * np.log(50 / 1.0), 3),
                           loss_at_2A_W=round(4 * Rs / (2 * np.pi) * np.log(50 / 1.0), 2),
                           note="one pin tip of 1 mm contact radius feeding a cloth zone collected at 50 mm; two pins per net halve it")
    json.dump(R, open(os.path.join(HERE, "coverage.json"), "w"), indent=1)
