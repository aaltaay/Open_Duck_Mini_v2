"""Walk time per charge and servo copper loss for the Open Duck Mini v2 (sim pass only).

Inputs: the per-servo torque and speed traces that sim/added_mass_sim.py saves for the trained model ("stock") and our
build ("ours"), the BAM motor model of sim/current_budget.py, and the Molicel P30B data-sheet discharge curves.

1. Pack power per case: servo electrical power (BAM model, sum of positive servo power, no credit for braking),
   divided by the BEC efficiency, plus the servo electronics idle current, plus the 5 V branch through its regulator,
   plus I^2 R in the pack path (holder, BMS, wires, XT30, fuse, switch).
2. Discharge: constant power from full charge on 2 x P30B in series; the cell voltage under load comes from the
   data-sheet curves (voltage against capacity at 0.6, 1.5, 3, 10 and 20 A, interpolated in current). Time to the
   D16 stop (3.5 V per cell under load, 7.0 V at the cells) and to other stop voltages.
3. Copper loss per joint: RMS motor current squared times the winding resistance, for the three BAM kt values used
   by current_budget.py and for the Feetech data-sheet terminal resistance.

Usage (from the repo root, after added_mass_sim.py has written its traces):
  ODM_SCRATCH=<scratch folder> python3 altaay_lab/sim/runtime_thermal.py
Outputs: ODM_SCRATCH/runtime_thermal/runtime_thermal.json and tables.md, and altaay_lab/sim/runtime_thermal.png.
"""
import os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.environ.get("ODM_SCRATCH", "/tmp/odm_added_mass")
TR = os.path.join(SCR, "added_mass", "traces")
OUT = os.path.join(SCR, "runtime_thermal"); os.makedirs(OUT, exist_ok=True)

# BAM model as in sim/current_budget.py (not imported: that module starts the MuJoCo stubs)
VIN = 7.4; KT_OVER_R = 3.23 / VIN; KTS = [1.148, 1.21164, 1.28]
def electrical(F, W, kt):
    R = kt / KT_OVER_R; u = np.clip(F * R / kt, -VIN, VIN); I = (u - kt * W) / R
    return I, u * I, R

# Molicel INR-18650-P30B, cell voltage under constant-current discharge at 23 C, digitized from the data sheet
# 'Discharge Rate Characteristics' by https://www.18650batterystore.com/products/molicel-p30b-18650-3000mah-36a-battery
# (figures 3.1 and 3.2 there; data sheet: https://cdn.shopify.com/s/files/1/0481/9678/0183/files/Product-Data-Sheet-of-INR-18650-P30B-80111-2.pdf)
P30B_Q = [0, 500, 1000, 1500, 2000, 2500]                    # mAh delivered
P30B = {0.6: ([4.19, 4.01, 3.83, 3.67, 3.48, 3.18], 2924), 1.5: ([4.18, 3.99, 3.81, 3.64, 3.46, 3.16], 2871),
        3.0: ([4.15, 3.95, 3.78, 3.60, 3.43, 3.13], 2846), 10.0: ([4.09, 3.83, 3.67, 3.51, 3.34, 3.07], 2854),
        20.0: ([3.99, 3.70, 3.57, 3.42, 3.26, 3.00], 2890)}  # (volts at P30B_Q, end mAh at 2.50 V)
def v_cell(q_mah, i_a):
    cur = sorted(P30B)
    def at(c):
        v, qe = P30B[c]; return np.interp(q_mah, P30B_Q + [qe], v + [2.50], right=2.0)
    if i_a <= cur[0]: return at(cur[0])
    if i_a >= cur[-1]: return at(cur[-1])
    for a, b in zip(cur[:-1], cur[1:]):
        if a <= i_a <= b: return at(a) + (at(b) - at(a)) * (i_a - a) / (b - a)

# Path and loads (sources in RUNTIME_THERMAL.md)
CORNERS = {
    "typical": dict(kt=1.21164, P5V=3.0, R_path=0.064, eta_bec=0.85, eta_reg=0.85, servo_scale=1.0),
    "conservative": dict(kt=1.148, P5V=5.0, R_path=0.084, eta_bec=0.85, eta_reg=0.85, servo_scale=1.0),
    "real servos 1.5 x sim power": dict(kt=1.148, P5V=5.0, R_path=0.084, eta_bec=0.85, eta_reg=0.85, servo_scale=1.5),
}
I_IDLE = 0.021        # A per servo, Feetech C001 spec item 5-6 'Idle Current (at stopped) 21 mA'
V_SERVO = 7.2         # BEC set point (D3)
R_DATASHEET = 2.5     # ohm, Feetech C001 spec item 5-10 'Terminal resistance 2.5 ohm'
I_RATED = 0.65        # A, Feetech C001 spec item 5-9 'Rated Current 650 mA' at rated torque 5 kg.cm (item 5-8), 7.4 V
T_CUT = 70.0          # C, Feetech C001 spec item 7-11 'Over Hot: more than 70 C, torque output off'
T_OPER_MAX = 60.0     # C, Feetech C001 spec item 1-2 operating temperature -20 to 60 C
SKIP = 2.0            # s, as current_budget.py

def load_case(vn, label):
    d = np.load(os.path.join(TR, vn, f"trace_{label}.npz"))
    k0 = int(round(SKIP / float(d["dt"])))
    return d["F"][k0:].astype(float), d["W"][k0:].astype(float), [str(x) for x in d["names"]], float(d["dt"])

def case_stats(vn, label):
    F, W, names, dt = load_case(vn, label)
    out = dict(per_kt={})
    for kt in KTS:
        I, P, R = electrical(F, W, kt)
        irms = np.sqrt((I ** 2).mean(0))
        out["per_kt"][str(kt)] = dict(P_servo_W=float(np.clip(P, 0, None).sum(1).mean()), P_servo_net_W=float(np.clip(P.sum(1), 0, None).mean()),
                                      I_rms=dict(zip(names, irms.round(4).tolist())), R=R,
                                      P_cu=dict(zip(names, (irms ** 2 * R).round(4).tolist())),
                                      P_cu_datasheet_R=dict(zip(names, (irms ** 2 * R_DATASHEET).round(4).tolist())))
    return out

def pack_power(P_servo, c):
    """power drawn from the switched pack bus (W) for a servo electrical power P_servo (W)"""
    return (c["servo_scale"] * P_servo + 14 * I_IDLE * V_SERVO) / c["eta_bec"] + c["P5V"] / c["eta_reg"]

def discharge(P_bus, R_path, stop, dq=2.0, q_max=2950.0):
    """constant power P_bus at the switched bus. stop: (kind, volts): 'cell' per-cell terminal volts, 'bus' switched-bus volts.
    returns minutes to the stop, mAh delivered, mean pack current, and the voltage trace"""
    q = 0.0; t = 0.0; I = P_bus / 8.0; trace = []
    while q < q_max:
        for _ in range(30):                      # solve P_bus = (2 V_cell(q, I) - I R_path) I
            vb = 2 * v_cell(q, I) - I * R_path
            if vb <= 0.5: return None
            I_new = P_bus / vb
            if abs(I_new - I) < 1e-5: break
            I = 0.5 * (I + I_new)
        vc = v_cell(q, I); vb = 2 * vc - I * R_path
        trace.append((t / 60, q, 2 * vc, vb, I))
        if (stop[0] == "cell" and vc <= stop[1]) or (stop[0] == "bus" and vb <= stop[1]):
            return dict(minutes=t / 60, mAh=q, I_mean=q / 1000 / (t / 3600) if t else I, trace=trace)
        t += dq / 1000 / I * 3600; q += dq
    return dict(minutes=t / 60, mAh=q, I_mean=q / 1000 / (t / 3600), trace=trace, note="ran out of table")

DUTY = {   # name: {case: time fraction}
    "continuous walk forward 0.15 m/s": {"walk_forward_0.15": 1.0},
    "continuous walk forward, backlash model": {"walk_backlash": 1.0},
    "continuous mixed walking (1/2 forward, 1/4 turn, 1/4 side)": {"walk_forward_0.15": 0.5, "turn_1.0": 0.25, "walk_side_0.2": 0.25},
    "stand and walk 50/50": {"stand_in_place": 0.5, "walk_forward_0.15": 0.5},
    "stand 75 %, walk 25 %": {"stand_in_place": 0.75, "walk_forward_0.15": 0.25},
}
STOPS = [("D16 stop: 3.5 V per cell under load (7.0 V at the cells)", ("cell", 3.5)),
         ("7.0 V on the switched bus (after holder, BMS, fuse, switch)", ("bus", 7.0)),
         ("3.3 V per cell under load (6.6 V)", ("cell", 3.3)),
         ("to empty: 2.5 V per cell (data-sheet end, not a stop to use)", ("cell", 2.55))]

def main():
    cases = sorted({c for d in DUTY.values() for c in d} | {"walk_pushes"})
    S = {vn: {c: case_stats(vn, c) for c in cases} for vn in ("stock", "ours")}
    res = dict(cases=S, runtime={}, thermal={})
    L = []; P = L.append
    # ---- pack power and runtime ----
    P("| Model | Duty cycle | Corner | Servo electrical W | Pack bus W | Mean pack A | Minutes to D16 stop | mAh to D16 stop | Minutes to 7.0 V bus | Minutes to 3.3 V/cell | Minutes to empty |")
    P("|---|---|---|---|---|---|---|---|---|---|---|")
    for vn in ("stock", "ours"):
        res["runtime"][vn] = {}
        for dn, mix in DUTY.items():
            res["runtime"][vn][dn] = {}
            for cn, c in CORNERS.items():
                Ps = sum(f * S[vn][case]["per_kt"][str(c["kt"])]["P_servo_W"] for case, f in mix.items())
                Pb = pack_power(Ps, c)
                r = {nm: discharge(Pb, c["R_path"], st) for nm, st in STOPS}
                d16 = r[STOPS[0][0]]
                res["runtime"][vn][dn][cn] = dict(P_servo_W=Ps, P_bus_W=Pb, **{nm: dict(minutes=x["minutes"], mAh=x["mAh"], I_mean=x["I_mean"]) for nm, x in r.items()})
                P(f"| {vn} | {dn} | {cn} | {Ps:.1f} | {Pb:.1f} | {d16['I_mean']:.2f} | {d16['minutes']:.0f} | {d16['mAh']:.0f} | "
                  f"{r[STOPS[1][0]]['minutes']:.0f} | {r[STOPS[2][0]]['minutes']:.0f} | {r[STOPS[3][0]]['minutes']:.0f} |")
                if vn == "ours" and cn == "typical": res["runtime"][vn][dn][cn]["trace"] = r[STOPS[3][0]]["trace"][::10]
    # ---- copper loss per joint ----
    P("\nCopper loss per joint, W (RMS motor current squared x winding resistance), walking cases, highest of the three BAM kt values; data-sheet R in brackets:\n")
    joints = list(S["ours"]["walk_forward_0.15"]["per_kt"]["1.148"]["I_rms"])
    order = [j for j in joints if j.startswith("left")] + [j for j in joints if j.startswith("right")] + [j for j in joints if not j.startswith(("left", "right"))]
    for vn in ("stock", "ours"):
        P(f"\n{vn}:\n"); P("| Joint | " + " | ".join(["stand", "forward", "turn", "side", "backlash forward"]) + " | I rms, backlash forward (A) |")
        P("|---|---|---|---|---|---|---|")
        res["thermal"][vn] = {}
        for j in order:
            cells = []
            for case in ("stand_in_place", "walk_forward_0.15", "turn_1.0", "walk_side_0.2", "walk_backlash"):
                pk = max(S[vn][case]["per_kt"][str(kt)]["P_cu"][j] for kt in KTS)
                pd = max(S[vn][case]["per_kt"][str(kt)]["P_cu_datasheet_R"][j] for kt in KTS)
                cells.append(f"{pk:.2f} ({pd:.2f})")
                res["thermal"][vn].setdefault(j, {})[case] = dict(P_cu_W=pk, P_cu_datasheet_R_W=pd,
                                                                  I_rms=max(S[vn][case]["per_kt"][str(kt)]["I_rms"][j] for kt in KTS))
            irms = res["thermal"][vn][j]["walk_backlash"]["I_rms"]
            P(f"| {j} | " + " | ".join(cells) + f" | {irms:.2f} |")
    P(f"\nRated copper loss for comparison: {I_RATED} A rated current squared x {R_DATASHEET} ohm = {I_RATED ** 2 * R_DATASHEET:.2f} W (Feetech C001 spec items 5-9, 5-10).")
    # critical thermal resistance to reach the 70 C cut from 25 C and from 35 C, hottest joint
    for vn in ("stock", "ours"):
        for case in ("walk_forward_0.15", "walk_backlash"):
            j = max(order, key=lambda x: res["thermal"][vn][x][case]["P_cu_W"]); p = res["thermal"][vn][j][case]["P_cu_W"]
            P(f"{vn}, {case}: hottest joint {j}, {p:.2f} W; a winding-to-room thermal resistance above {(T_CUT - 25) / p:.1f} K/W (25 C room) "
              f"or {(T_CUT - 35) / p:.1f} K/W (35 C inside the body) reaches the 70 C cut in steady state")
            res["thermal"][vn][f"critical_Rth_{case}"] = dict(joint=j, P_cu_W=p, Rth_25C=(T_CUT - 25) / p, Rth_35C=(T_CUT - 35) / p)
    open(os.path.join(OUT, "tables.md"), "w").write("\n".join(L))
    json.dump(res, open(os.path.join(OUT, "runtime_thermal.json"), "w"), indent=1, default=float)
    print("\n".join(L))
    # ---- plot ----
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.8))
        cols = ["#4a6fa5", "#c0392b", "#7d3c98", "#1e8449", "#b9770e"]
        for (dn, col) in zip(DUTY, cols):
            tr = np.array(res["runtime"]["ours"][dn]["typical"]["trace"])
            axs[0].plot(tr[:, 0], tr[:, 2], color=col, lw=1.1, label=dn)
        axs[0].axhline(7.0, color="k", ls="--", lw=0.8); axs[0].text(1, 7.03, "D16 stop, 7.0 V at the cells", fontsize=7)
        axs[0].set_xlabel("minutes from full charge"); axs[0].set_ylabel("pack voltage at the cells under load (V)")
        axs[0].set_ylim(5.0, 8.6); axs[0].legend(fontsize=6, loc="lower left"); axs[0].grid(alpha=0.3)
        axs[0].set_title("Our build, typical corner (sim pass only)", fontsize=8)
        x = np.arange(len(order)); w = 0.38
        for k, (vn, col) in enumerate((("stock", "#4a6fa5"), ("ours", "#c0392b"))):
            axs[1].bar(x + (k - 0.5) * w, [res["thermal"][vn][j]["walk_backlash"]["P_cu_W"] for j in order], w, color=col, label=vn)
        axs[1].axhline(I_RATED ** 2 * R_DATASHEET, color="k", ls="--", lw=0.8); axs[1].text(-0.4, I_RATED ** 2 * R_DATASHEET + 0.1, "rated current loss", fontsize=7)
        axs[1].set_xticks(x); axs[1].set_xticklabels([j.replace("left_", "L ").replace("right_", "R ") for j in order], rotation=60, fontsize=7)
        axs[1].set_ylabel("copper loss (W), backlash walk"); axs[1].legend(fontsize=7); axs[1].grid(alpha=0.3, axis="y")
        axs[1].set_title("Copper loss per joint, walking forward, backlash model", fontsize=8)
        fig.tight_layout(); fig.savefig(os.path.join(HERE, "runtime_thermal.png"), dpi=80); plt.close(fig)
    except Exception as e:
        print("plot skipped:", e)

if __name__ == "__main__":
    main()
