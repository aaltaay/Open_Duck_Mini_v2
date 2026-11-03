"""Check the servo thermal model against the only published STS3215 temperature curves (sim pass only).

Data (Robo9 bench tests, STS3215 C018 12 V, 1:345, the same PA+GF case and 55 g as our C001 [R1]):
  - static hold, 1 kg on a 15 cm lever (15 kg.cm), chart 'Static Load Overheat Test': 25, 30, 35, 40, 45, 48 C at
    0, 2, 4, 6, 8, 10 min, then 48 C at 20, 40, 60 min;
  - +-90 deg oscillation, chart 'Oscillation in a +-90-Degree Range': 48, 52, 56, 58, 60, 60 C at 0 to 50 min
    (then the speed was lowered and it went on to 71 C);
  - two-minute hold at 50 % load (22 kg.cm, 0.75 A, 12 V): internal sensor 31 to 41 C, thermal camera 30 to 33.5 C.
Read from the charts' plotted points (round values; the charts look hand-entered at 2 and 10 min steps).

What can be fitted: the time constant and the steady rise of each curve (no heat input is published, so the thermal
resistance itself cannot be fitted). What is checked: (1) the physics time constant of the servo body in still air
(heat capacity from the masses, natural convection and radiation on the measured case area) against the fitted
one; (2) the heat input the model needs for the 23 K static rise against the C018 data sheet (15 kg.cm / 11 kg.cm
per A = 1.36 A through 1.0 ohm, plus idle); (3) the two-minute test: the share w of the winding rise that the
sensor sees, given the measured 0.75 A.

Run: python3 altaay_lab/twin/thermal/fit_robo9.py   (writes fit_robo9.json next to this file)
"""
import json, os
import numpy as np
import twin_thermal as TT

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC_T = np.array([0, 2, 4, 6, 8, 10, 20, 40, 60.0]) * 60
STATIC_C = np.array([25, 30, 35, 40, 45, 48, 48, 48, 48.0])
OSC_T = np.array([0, 10, 20, 30, 40, 50.0]) * 60
OSC_C = np.array([48, 52, 56, 58, 60, 60.0])
C018 = dict(R_term=1.0, Kt_kgcm_per_A=11.0, V=12.0)     # C018 spec [F5]: 1.0 ohm, 11 kg.cm/A (SERVO_UPGRADE_OPTIONS.md table)


def fit_first_order(t, T):
    best = None
    for tau in np.linspace(30, 3600, 3000):
        x = 1 - np.exp(-t / tau)
        A = np.vstack([np.ones_like(x), x]).T
        coef, *_ = np.linalg.lstsq(A, T, rcond=None)
        rms = float(np.sqrt(np.mean((A @ coef - T) ** 2)))
        if best is None or rms < best[0]:
            best = (rms, tau, coef)
    rms, tau, (T0, dT) = best
    # tau range whose RMS stays within 0.5 K of the best (the charts read to about 1 C)
    ok = []
    for tau2 in np.linspace(30, 3600, 3000):
        x = 1 - np.exp(-t / tau2); A = np.vstack([np.ones_like(x), x]).T
        coef, *_ = np.linalg.lstsq(A, T, rcond=None)
        if np.sqrt(np.mean((A @ coef - T) ** 2)) <= rms + 0.5:
            ok.append(tau2)
    return dict(tau_s=round(tau, 0), tau_range_s=[round(min(ok), 0), round(max(ok), 0)], T0=round(T0, 2), dT=round(dT, 2), rms_K=round(rms, 2))


def bench(P_w, P_b, c, Ta=25.0, t_end=3600.0, dt=0.5, v=0.0):
    """one servo in still air on a bench: the corner's C and R values, the whole outer case area free"""
    sc = TT.servo_C(c); A = TT.GEOM["servos"]["left_knee"]["outer_case_area_mm2"] * 1e-6
    Tw = Tb = Ta; out = []
    for s in range(int(t_end / dt)):
        if s % 20 == 0:
            h = TT.h_total(Tb, Ta, v, c["eps"])
        pw = P_w * (1 + TT.PARAMS["alpha_cu"] * (Tw - 25.0))
        q = (Tw - Tb) / c["R_wc"]
        Tw += dt * (pw - q) / c["C_w"]; Tb += dt * (P_b + q - h * A * (Tb - Ta)) / sc["C_b"]
        out.append((s * dt, Tw, Tb))
    return np.array(out)


def main():
    res = dict(static=fit_first_order(STATIC_T, STATIC_C), oscillation=fit_first_order(OSC_T, OSC_C - 48.0))
    res["oscillation"]["note"] = "fitted on the rise above the 48 C start, 0 to 50 min (before the speed change)"
    rows = {}
    for cn, c in TT.CORNERS.items():
        sc = TT.servo_C(c); A = TT.GEOM["servos"]["left_knee"]["outer_case_area_mm2"] * 1e-6
        h23 = TT.h_total(48.0, 25.0, 0.0, c["eps"])
        R_ba = 1.0 / (h23 * A)
        tau_phys = sc["C_total"] * R_ba
        row = dict(C_total_J_per_K=round(sc["C_total"], 1), R_ba_bench_K_per_W=round(R_ba, 2), h_bench_W_m2K=round(h23, 2), tau_physics_s=round(tau_phys, 0))
        # two readings of the C018 data: (a) data-sheet Kt and 1.0 ohm terminal resistance; (b) the stall line
        # (12 V / 2.7 A = 4.44 ohm loop) with the measured 0.75 A of the two-minute test
        for tag, R_loop in (("a_datasheet_1ohm", C018["R_term"]), ("b_stall_line_4p44ohm", 12.0 / 2.7)):
            idle = TT.PARAMS["I_idle"] * C018["V"]
            # two-minute test: heat from the measured 0.75 A; w from the internal +10 K
            P2w = 0.85 * 0.75 ** 2 * R_loop; P2b = 0.15 * 0.75 ** 2 * R_loop + idle   # winding share of the loop 0.85 (ASSUMPTION; C001: 2.5 of 2.63 to 2.93 ohm)
            tr2 = bench(P2w, P2b, c, Ta=31.0, t_end=120.0)
            dTb2, dTw2 = tr2[-1, 2] - 31.0, tr2[-1, 1] - 31.0
            w2 = (10.0 - dTb2) / (dTw2 - dTb2) if dTw2 > dTb2 else float("nan")
            # static test: the hold current that gives the 23 K steady sensor rise with this corner's w
            lo, hi = 0.05, 3.0
            for _ in range(60):
                I = 0.5 * (lo + hi)
                tr = bench(0.85 * I * I * R_loop, 0.15 * I * I * R_loop + idle, c, t_end=3600.0, dt=1.0)
                Ts = tr[-1, 2] + c["w"] * (tr[-1, 1] - tr[-1, 2])
                lo, hi = (I, hi) if Ts < 48.0 else (lo, I)
            I_static = 0.5 * (lo + hi)
            tr = bench(0.85 * I_static ** 2 * R_loop, 0.15 * I_static ** 2 * R_loop + idle, c, t_end=3600.0, dt=1.0)
            Ts = tr[:, 2] + c["w"] * (tr[:, 1] - tr[:, 2])
            pred = np.interp(STATIC_T, tr[:, 0], Ts)
            row[tag] = dict(two_min_body_rise_K=round(float(dTb2), 2), two_min_winding_rise_K=round(float(dTw2), 2), w_for_10K=round(float(w2), 2),
                            static_hold_current_for_48C_A=round(I_static, 3), static_hold_current_datasheet_Kt_A=round(15.0 / C018["Kt_kgcm_per_A"], 3),
                            static_pred_C=[round(float(x), 1) for x in pred], static_pred_rms_K=round(float(np.sqrt(np.mean((pred - STATIC_C) ** 2))), 2))
        rows[cn] = row
    res["model_vs_robo9"] = rows
    json.dump(res, open(os.path.join(HERE, "fit_robo9.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
