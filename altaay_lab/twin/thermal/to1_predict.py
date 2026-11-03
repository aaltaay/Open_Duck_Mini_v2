"""Predicted bench curves, so the bench logs can be laid over the twin (sim pass only): the TO1 thermal hold
(TEST_PLAN.md 7.3) for one C001, and the heat checks of TEST_PLAN 4.1 (CC BEC Pro) and 4.2 (Pololu 2815).

Stalled horn, Present Current held at I, 7.2 V, still air at 25 C, the whole outer case free (no printed parts).
Heat: I^2 x the BAM loop resistance (kt / 0.43649 = 2.63 to 2.93 ohm; the winding share is the data-sheet 2.5 ohm,
with the copper temperature coefficient), plus the 21 mA idle current; no friction at a stall. Output for each corner
of twin_thermal.py: the reading at 5, 10, 20 and 30 minutes, the time to the 70 C cut, the steady values, and the
apparent thermal resistance and time constant that a log of the reading would give.

Run: python3 altaay_lab/twin/thermal/to1_predict.py   (writes to1_predict.json next to this file)
"""
import json, os
import numpy as np
import twin_thermal as TT

HERE = os.path.dirname(os.path.abspath(__file__))


def hold(I, c, Ta=25.0, t_end=3600.0, dt=0.5, V=7.2):
    kt = TT.PARAMS["KTS"][0] if c["kt"] == "worst" else TT.PARAMS["KTS"][-1]
    R_loop = kt / TT.PARAMS["KT_OVER_R"]
    P_w25 = I * I * TT.PARAMS["R_w25"]; P_b = I * I * (R_loop - TT.PARAMS["R_w25"]) + TT.PARAMS["I_idle"] * V
    sc = TT.servo_C(c); A = TT.GEOM["servos"]["right_knee"]["outer_case_area_mm2"] * 1e-6
    Tw = Tb = Ta; rows = []; t_cut = None
    for s in range(int(t_end / dt)):
        if s % 20 == 0:
            h = TT.h_total(Tb, Ta, 0.0, c["eps"])
        pw = P_w25 * (1 + TT.PARAMS["alpha_cu"] * (Tw - 25.0))
        q = (Tw - Tb) / c["R_wc"]
        Tw += dt * (pw - q) / c["C_w"]; Tb += dt * (P_b + q - h * A * (Tb - Ta)) / sc["C_b"]
        Ts = Tb + c["w"] * (Tw - Tb)
        if t_cut is None and Ts >= TT.PARAMS["T_cut"]:
            t_cut = s * dt
        rows.append((s * dt, Ts, Tw, Tb))
    r = np.array(rows)
    at = {f"{m}_min": round(float(np.interp(m * 60, r[:, 0], r[:, 1])), 1) for m in (5, 10, 20, 30)}
    Ts_end = r[-1, 1]; P_tot = P_w25 * (1 + TT.PARAMS["alpha_cu"] * (r[-1, 2] - 25)) + P_b
    i63 = np.searchsorted(r[:, 1] - Ta, 0.632 * (Ts_end - Ta))
    return dict(I_A=I, P_start_W=round(P_w25 + P_b, 2), reading=at, t_cut_min=None if t_cut is None else round(t_cut / 60, 1),
                reading_60min=round(float(Ts_end), 1), winding_60min=round(float(r[-1, 2]), 1), body_60min=round(float(r[-1, 3]), 1),
                apparent_Rth_K_per_W=round(float((Ts_end - Ta) / P_tot), 1), apparent_tau_min=round(float(r[min(i63, len(r) - 1), 0] / 60), 1))




def bench_power_parts():
    """TEST_PLAN 4.1 (CC BEC Pro, 10 min at 5 A out, no airflow, case under 60 C) and 4.2 (Pololu 2815, 10 min at
    6.0 A on its seat with the foam tape, board under 50 C), in a 22 C room (Pololu's own still-air point).
    BEC: loss 36 W x (1/eta - 1), the case from its size [S4] with one 47 x 33 face on the bench, its heat capacity
    40 g x 0.6 to 0.9 J/gK (ASSUMPTION: material not published). 2815: loss 36 A2 x R_on at a 7.4 V gate, board to air
    from Pololu's 6 A / 55 C point (twin_thermal.sw_Rth), heat capacity 3 to 5 J/K (ASSUMPTION: 2.7 g board plus the
    leads)."""
    out = {}
    a, b, h = TT.PARAMS["bec_dims_mm"]; A = (2 * (a * b + a * h + b * h) - a * b) * 1e-6
    for cn, c in TT.CORNERS.items():
        P = 36.0 * (1 / c["eta_bec"] - 1)
        T = 22.0; Cb = 40.0 * (0.9 if cn == "low" else 0.75 if cn == "central" else 0.6)
        for s in range(int(600 / 0.5)):
            hb = TT.h_natural(T, 22.0, L=0.033) + TT.h_rad(T, 22.0, c["bec_eps"])
            T += 0.5 * (P - hb * A * (T - 22.0)) / Cb
        Tss = 22.0 + 20.0
        for _ in range(50):
            hb = TT.h_natural(Tss, 22.0, L=0.033) + TT.h_rad(Tss, 22.0, c["bec_eps"]); Tss = 22.0 + P / (hb * A)
        Ps = 36.0 * TT.sw_R_on(7.4, c); Rs = TT.sw_Rth(c); Cs = 5.0 if cn == "low" else 4.0 if cn == "central" else 3.0
        Ts10 = 22.0 + Ps * Rs * (1 - np.exp(-600.0 / (Cs * Rs)))
        out[cn] = dict(bec_eta=c["eta_bec"], bec_loss_W=round(P, 2), bec_case_10min_C=round(T, 1), bec_case_steady_C=round(Tss, 1),
                       sw_loss_W=round(Ps, 3), sw_Rth_K_per_W=round(Rs, 1), sw_board_10min_C=round(Ts10, 1), sw_board_steady_C=round(22.0 + Ps * Rs, 1))
    return out


def main():
    r = dict(to1={cn: [hold(I, c) for I in (0.9, 1.2, 1.5)] for cn, c in TT.CORNERS.items()}, bench_power_parts=bench_power_parts())
    json.dump(r, open(os.path.join(HERE, "to1_predict.json"), "w"), indent=1)
    for cn, rows in r["to1"].items():
        for x in rows:
            print(cn, x)
    print(json.dumps(r["bench_power_parts"], indent=1))


if __name__ == "__main__":
    main()
