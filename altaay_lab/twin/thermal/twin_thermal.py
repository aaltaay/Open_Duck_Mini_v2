"""Thermal twin of the Open Duck Mini v2: STS3215 two-node model per servo, coupled to the electronics in the
printed trunk and head (sim pass only).

What it does
  1. Heat per servo from the walk traces of the stock policy (the same traces as sim/runtime_thermal.py; our
     2.65 kg build from the verification run of 2026-11-02 6:36 AM ET, or the twin/electromech session CSVs when
     they exist): winding copper loss with the copper temperature coefficient, the rest of the electrical loop
     (board), the joint friction of the MJCF actuator class and the idle electronics.
  2. Two nodes per servo: winding (C_w) and servo body (C_b: case, gears, PCB, motor can), R_wc between them, and
     the body to the air by natural convection, radiation and the walking air speed on the measured outer case area
     (geometry.json, with the measured share of that area that a printed part covers). The Present Temperature
     sensor reads T_b + w (T_w - T_b); w is not published and is swept.
  3. The trunk and the head as an air node and a wall node each (measured skin areas and wall thickness, PLA
     conduction, natural convection and radiation outside); the cells as their own node; the BEC, the Pololu 2815,
     the fuse, the BMS and the 5 V regulator as steady offsets above the air. The hip yaw and neck pitch servos sit
     in the trunk air, the head roll servo in the head air; their heat goes into that air.
  4. Sessions: continuous walking (plain and backlash model), mixed walking, stand and walk 50/50 and 25/75, at a
     25 C room and a warm 32 C room, full and nominal pack; three parameter corners (low, central, high) and
     one-at-a-time sweeps. Time to the 70 C torque cut, the temperatures at the D16 battery stop, the winding
     temperature, and the timers of the Feetech over-current and overload protections.

Every parameter has a source tag (PARAMS; the tags are listed in THERMAL_TWIN.md, Sources). ASSUMPTION marks a value
with no published source; each one is swept.

Run from the repo root (numpy; matplotlib for the figure):
  TWIN_SCRATCH=<scratch folder> python3 altaay_lab/twin/thermal/twin_thermal.py
  optional: TWIN_TRACES=<folder with trace_<case>.npz> (default TWIN_SCRATCH/traces/ours)
            TWIN_EM_CSV=<twin/electromech/out> (re-run on the closed-loop session CSVs when present)
Outputs: TWIN_SCRATCH/twin_thermal/results.json (full traces), and in this folder results_summary.json,
tables.md and twin_thermal.png (small files).
"""
import json, os, sys, glob
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", ".."))
SCR = os.environ.get("TWIN_SCRATCH", "/tmp/twin_thermal_scratch")
OUT = os.path.join(SCR, "twin_thermal"); os.makedirs(OUT, exist_ok=True)
TRACES = os.environ.get("TWIN_TRACES", os.path.join(SCR, "traces", "ours"))
EM_CSV = os.environ.get("TWIN_EM_CSV", os.path.join(LAB, "twin", "electromech", "out"))
GEOM = json.load(open(os.environ.get("TWIN_GEOM", os.path.join(HERE, "geometry.json"))))

# ----------------------------------------------------------------------------------------------------------------
# Parameters with their source tags (THERMAL_TWIN.md, Sources). Tuples are (low, high) ranges.
PARAMS = dict(
    # [F1] Feetech ST-3215-C001 product specification A/1 2023-06-23
    R_w25=2.5, I_idle=0.021, T_cut=70.0, T_oper_max=60.0, I_rated=0.65, I_stall=2.5, mass_g=55.0,
    # [F2] FTServo wiki STS memory table, [F3] factory register read of STS3215 units (commanderfun/STS3215)
    I_oc=310 * 0.0065, t_oc=2.0, duty_ol=0.80, t_ol=2.0, hold_torque_after_ol=0.20, unload_condition=44,
    # [B1] BAM m1 (kt, R) and the three kt values of sim/current_budget.py; [U1] MJCF class sts3215
    KTS=(1.148, 1.21164, 1.28), KT_OVER_R=3.23 / 7.4, damping=0.56, frictionloss=0.068,
    # [E1] copper resistivity temperature coefficient
    alpha_cu=3.93e-3,
    # measured: geometry.json (outer case area, case plastic volume of the three case meshes)
    V_case_cm3=8.37,
    # [E2] specific heats J/(g K), [E3] densities g/cm3
    cp_nylon=1.60, cp_glass=(0.67, 0.84), cp_metal=(0.375, 0.49), rho_nylon=(1.12, 1.17), rho_glass=(2.4, 2.8),
    # [M1] Faulhaber 1724 SR, 2224 SR, 2232 SR (17 to 22 mm DC motors)
    Rth1_class=(6.9, 10.0), tau_w1_class=(7.2, 12.0), Rth2p_class=(19.0, 27.0), tau_w2p_class=(310.0, 500.0), T_wind_max_class=125.0,
    # [E5] emissivity of plastics
    eps_plastic=(0.90, 0.97),
    # [P1] SD3D PLA data sheet k and cp, [P4] measured 3D printed PLA (AIP 2020) cp 1.2
    k_pla=0.13, cp_pla=(1.2, 1.8),
    # [P2] Ingeo 4043D Tg 55-60 C, HDT 55 C at 0.45 MPa; [P3] Bambu PLA Basic Tg 60 C, HDT 57 C at 0.45 MPa and 54 C at
    # 1.8 MPa; [P5] Overture Easy PLA TDS v5.1 Vicat 66.2 C (the lab's filament)
    Tg_pla=(55.0, 60.0), HDT045_pla=(55.0, 57.0), HDT18_pla=54.0, vicat_easy_pla=66.2,
    # [C1] Molicel P30B data sheet: DC impedance 17 mOhm (50 % SOC), discharge -40 to 60 C, 47 g max; [C2] 18650 cp
    R_cell=0.017, T_cell_max=60.0, m_cell_g=47.0, cp_cell=(0.814, 0.972),
    # [S1] Pololu 2815: 13 mOhm max at 4.5 V gate, 8.6 mOhm max at 10 V; 6 A with the MOSFETs at 55 C, 16 A at
    # 150 C, 12 V, 22 C still air
    R_sw_4v5=0.013, R_sw_10v=0.0086, sw_6A_T=55.0, sw_amb=22.0,
    # [S2] Pololu D30V30F5 efficiency graph, 5 V out: 6 V in about 97 % and 12 V in about 94 % at 0.5 to 1 A
    eta_reg5=(0.94, 0.97),
    # [S3] Raspberry Pi Zero 2 W typical bare-board active current 350 mA; throttles from 80 C, hard limit 85 C
    I_pi=0.35, T_pi_throttle=80.0,
    # [L1] lab power model (sim/POWER_PATH_SIM.md): BMS 25 mOhm max (Tenergy table), fuse 6 mOhm and XT30 1 mOhm
    # (ASSUMPTION), holder 10 to 30 mOhm (ASSUMPTION), pack wires 8.8 mOhm, BEC 0.85 efficiency (ASSUMPTION, Castle
    # publishes none), 5 V branch 3 W typical and 5 W conservative
    R_bms=(0.015, 0.025), R_fuse=0.006, R_xt30=0.002, R_holder=(0.010, 0.030), R_wires=0.0088, eta_bec=(0.80, 0.92),
    P5V=(3.0, 5.0),
    # [S4] CC BEC Pro size 47 x 33 x 22 mm and 40 g (Horizon Hobby page)
    bec_dims_mm=(47.0, 33.0, 22.0), bec_mass_g=40.0,
)
SIGMA = 5.670374e-8
NAMES = ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle", "neck_pitch", "head_pitch", "head_yaw",
         "head_roll", "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]
SERVO_ID = dict(zip(NAMES, [20, 21, 22, 23, 24, 30, 31, 32, 33, 10, 11, 12, 13, 14]))
INSIDE = {"left_hip_yaw": "trunk", "right_hip_yaw": "trunk", "neck_pitch": "trunk", "head_roll": "head"}
LEG = {n for n in NAMES if any(k in n for k in ("hip_roll", "hip_pitch", "knee", "ankle"))}
# share of the walking air speed each servo sees: leg servos all of it, the neck servos outside the shells half of it
# (ASSUMPTION), the servos inside the trunk or head none
VFRAC = np.array([1.0 if n in LEG else (0.0 if n in INSIDE else 0.5) for n in NAMES])

# ----------------------------------------------------------------------------------------------------------------
# [E4] air at 1 bar, linear between 300 and 350 K: k (W/m K), nu (m2/s), Pr
def air(T_k):
    f = (T_k - 300.0) / 50.0
    return 0.02623 + 0.00371 * f, 15.89e-6 + 5.03e-6 * f, 0.707 - 0.007 * f


def h_natural(Ts, Ta, L, frac_vertical=0.69):
    """[H1] Churchill and Chu (laminar form) on the vertical faces, Lloyd and Moran on the horizontal faces"""
    dT = max(abs(Ts - Ta), 0.05); Tf = 0.5 * (Ts + Ta) + 273.15
    k, nu, pr = air(Tf); a = nu / pr; g_b = 9.81 / Tf
    ra = g_b * dT * L ** 3 / (nu * a)
    nu_v = 0.68 + 0.670 * ra ** 0.25 / (1 + (0.492 / pr) ** (9 / 16)) ** (4 / 9)
    Lh = L / 2.0; ra_h = g_b * dT * Lh ** 3 / (nu * a)
    nu_h = 0.405 * ra_h ** 0.25                                   # mean of the hot-up (0.54) and hot-down (0.27) forms
    return frac_vertical * nu_v * k / L + (1 - frac_vertical) * nu_h * k / Lh


def h_forced(v, Tf_c, L):
    """[H1] laminar flat plate, mean Nu = 0.664 Re^0.5 Pr^(1/3)"""
    if v <= 0:
        return 0.0
    k, nu, pr = air(Tf_c + 273.15)
    return 0.664 * (v * L / nu) ** 0.5 * pr ** (1 / 3) * k / L


def h_rad(Ts, Ta, eps):
    T1, T2 = Ts + 273.15, Ta + 273.15
    return eps * SIGMA * (T1 * T1 + T2 * T2) * (T1 + T2)


def h_total(Ts, Ta, v, eps, L=0.035):
    hn, hf = h_natural(Ts, Ta, L), h_forced(v, 0.5 * (Ts + Ta), L)
    return (hn ** 3 + hf ** 3) ** (1 / 3) + h_rad(Ts, Ta, eps)        # mixed convection, n = 3 [H1]

# ----------------------------------------------------------------------------------------------------------------
# Servo heat from the traces (BAM motor model as sim/current_budget.py and sim/runtime_thermal.py)
CASES = ("stand_in_place", "walk_forward_0.15", "walk_backlash", "turn_1.0", "walk_side_0.2")


def _longest(mask, dt):
    out = []
    for j in range(mask.shape[1]):
        m = np.concatenate([[0], mask[:, j].astype(np.int8), [0]]); dm = np.diff(m)
        s, e = np.where(dm == 1)[0], np.where(dm == -1)[0]
        out.append(float((e - s).max() * dt) if len(s) else 0.0)
    return np.array(out)


def servo_heat(case, vcap, kt_pick="worst", skip=2.0):
    """W per servo: winding copper at 25 C (P_cu25), the rest of the loop (P_board), friction, idle; for the kt
    value that gives the highest ('worst') or the lowest ('best') copper loss; plus the protection timers"""
    d = np.load(os.path.join(TRACES, f"trace_{case}.npz"))
    dt = float(d["dt"]); k0 = int(round(skip / dt))
    F = d["F"][k0:].astype(float); W = d["W"][k0:].astype(float)
    assert [str(x) for x in d["names"]] == NAMES
    runs = []
    for kt in PARAMS["KTS"]:
        R = kt / PARAMS["KT_OVER_R"]
        u = np.clip(F * R / kt, -vcap, vcap); I = (u - kt * W) / R
        i2 = (I ** 2).mean(0)
        fv = max(PARAMS["damping"] - kt * PARAMS["KT_OVER_R"], 0.0)
        n2 = int(round(2.0 / dt)); c = np.cumsum(np.vstack([np.zeros((1, 14)), np.abs(I)]), 0)
        runs.append(dict(kt=kt, i2=i2, P_cu25=i2 * PARAMS["R_w25"], P_board=i2 * max(R - PARAMS["R_w25"], 0.0),
                         P_fric=PARAMS["frictionloss"] * np.abs(W).mean(0) + fv * (W ** 2).mean(0),
                         oc_run=_longest(np.abs(I) > PARAMS["I_oc"], dt), ol_run=_longest(np.abs(u) / vcap > PARAMS["duty_ol"], dt),
                         I_2s_max=((c[n2:] - c[:-n2]) / n2).max(0), I_peak=np.abs(I).max(0)))
    tot = np.array([r["P_cu25"] for r in runs])
    pick = tot.argmax(0) if kt_pick == "worst" else tot.argmin(0)
    out = {k: np.array([runs[pick[j]][k][j] for j in range(14)]) for k in ("i2", "P_cu25", "P_board", "P_fric")}
    out["P_idle"] = np.full(14, PARAMS["I_idle"] * vcap)
    for k in ("oc_run", "ol_run", "I_2s_max", "I_peak"):
        out[k] = np.max([r[k] for r in runs], 0)
    out["kt"] = np.array([PARAMS["KTS"][p] for p in pick])
    return out


def scale_heat(h, cf):
    """current factor cf on the electrical losses (copper and board scale with I^2)"""
    g = dict(h); g["P_cu25"] = h["P_cu25"] * cf ** 2; g["P_board"] = h["P_board"] * cf ** 2; g["i2"] = h["i2"] * cf ** 2
    return g


def mix_heat(parts):
    """time-weighted mean of heat dicts: parts = [(weight, heat)]"""
    keys = ("i2", "P_cu25", "P_board", "P_fric", "P_idle")
    return {k: sum(w * h[k] for w, h in parts) for k in keys}

# ----------------------------------------------------------------------------------------------------------------
# Corners. Each entry is a sourced range end or a swept ASSUMPTION (comment block below).
CORNERS = {
    "low": dict(a_mid=0.90, a_contact=0.85, v_walk=0.5, eps=0.97, gf=0.40, cable_g=0.0, cp_metal=0.49, C_w=4.0, R_wc=6.9, w=0.0, cf=1.00,
                kt="best", eta_bec=0.92, R_bms=0.015, R_holder=0.010, sw_hot=1.0, P5V=3.0, cp_pla=1.8, h_in_f=1.3, bec_eps=0.9, Rbms_th=15.0, A_in_f=1.5),
    "central": dict(a_mid=0.70, a_contact=0.75, v_walk=0.2, eps=0.93, gf=0.30, cable_g=2.0, cp_metal=0.43, C_w=2.5, R_wc=10.0, w=0.1, cf=1.00,
                    kt="worst", eta_bec=0.85, R_bms=0.020, R_holder=0.020, sw_hot=1.15, P5V=3.0, cp_pla=1.5, h_in_f=1.0, bec_eps=0.5, Rbms_th=30.0, A_in_f=1.0),
    "high": dict(a_mid=0.50, a_contact=0.55, v_walk=0.0, eps=0.90, gf=0.0, cable_g=4.0, cp_metal=0.375, C_w=1.5, R_wc=15.0, w=0.3, cf=1.25,
                 kt="worst", eta_bec=0.80, R_bms=0.025, R_holder=0.030, sw_hot=1.3, P5V=5.0, cp_pla=1.2, h_in_f=0.7, bec_eps=0.1, Rbms_th=50.0, A_in_f=0.8, wall="mean"),
}
# a_mid, a_contact: share of a free face's heat loss kept where a printed part is 2 to 10 mm away or touching
#   (ASSUMPTION; physics: a 2 to 10 mm air gap conducts 2.6 to 13 W/m2K plus radiation to a warm neighbour; a
#   touching 2 to 4 mm PLA plate adds t/k = 0.015 to 0.03 m2K/W in series with its own outer face, about 75 to 85 %
#   of a free face). geometry.json gives the measured shares of each servo's case area.
# v_walk: relative air speed of a leg servo while walking, ASSUMPTION 0 to 0.5 m/s (walking 0.10 to 0.15 m/s, leg swing).
# gf: glass share of the PA+GF case (ASSUMPTION 0 to 40 %); cable_g: whether the 15 cm lead is in the 55 g (ASSUMPTION).
# cp_metal: the metal parts (motor, gears, shafts) between brass 0.375 and steel 0.49 J/gK [E2].
# C_w: winding plus armature node; coreless windings of the size class have tau_w1 / Rth1 = 0.7 to 1.7 J/K [M1];
#   an iron armature adds mass (ASSUMPTION up to 4 J/K).
# R_wc: winding to the servo body: Rth1 6.9 to 10 K/W of the size class [M1], plus the can to the servo body
#   (ASSUMPTION 0 to 5 K/W).
# w: where the sensor sits between the body (0) and the winding (1). Estimated from the two Robo9 C018 tests
#   (fit_robo9.py): only the stall-line reading of the C018 (4.44 ohm loop) explains both, and it gives w = 0.03 to
#   0.19; swept 0 to 0.3 (Feetech says the protection 'detects the current motor temperature' [F4]).
# cf: current factor on the BAM model, ASSUMPTION 1.0 to 1.25 (the data-sheet stall torque per amp is 0.6 x the BAM
#   kt: load-dependent gear friction that the m1 model lacks [B2]; CURRENT_BUDGET.md asks for up to 2 x).
# eta_bec, R_bms, R_holder, P5V: lab power model ranges [L1]; sw_hot: MOSFET on resistance hot / cold (ASSUMPTION
#   1.0 to 1.3); h_in_f: factor on the inner wall convection (ASSUMPTION); bec_eps: emissivity of the BEC case
#   (ASSUMPTION 0.1 bare metal to 0.9 painted or shrink-wrapped); Rbms_th: BMS to trunk air (ASSUMPTION 15 to 50 K/W,
#   sandwiched between two 2 mm PLA walls: 2 x t/(kA) = 28 K/W per face, plus the four 16 AWG leads).


def servo_C(c):
    rho = 1.0 / ((1 - c["gf"]) / np.mean(PARAMS["rho_nylon"]) + c["gf"] / np.mean(PARAMS["rho_glass"]))
    m_case = PARAMS["V_case_cm3"] * rho
    cp_case = (1 - c["gf"]) * PARAMS["cp_nylon"] + c["gf"] * np.mean(PARAMS["cp_glass"])
    m_rest = PARAMS["mass_g"] - m_case - c["cable_g"]
    C_total = m_case * cp_case + m_rest * c["cp_metal"]
    return dict(C_total=C_total, C_b=C_total - c["C_w"], m_case=m_case, m_rest=m_rest, cp_case=cp_case)


def servo_area(c):
    """effective outer area per servo, m2, from the measured exposure shares (geometry.json)"""
    A = np.zeros(14)
    for j, n in enumerate(NAMES):
        g = GEOM["servos"][n]
        f_free = g["free_beyond_30mm"] + g["within_10_30mm"]
        A[j] = g["outer_case_area_mm2"] * 1e-6 * (f_free + c["a_mid"] * g["within_2_10mm"] + c["a_contact"] * g["within_2mm"])
    return A

# ----------------------------------------------------------------------------------------------------------------
# Enclosures (trunk and head): air node + wall node; measured areas and wall thickness (geometry.json)
def enclosure_params(name, c):
    e = GEOM[name]
    A_out = e["outer_area_mm2"] * 1e-6
    # inner skin: the measured inner faces include mating faces between parts and ribs, so the convective inner
    # area is taken as the outer skin times A_in_f (ASSUMPTION 0.8 to 1.5), capped at the measured inner area
    A_in = min(e["inner_area_mm2"] * 1e-6, A_out * c.get("A_in_f", 1.0))
    # wall: the thin shells (median 3.0 mm) carry most of the skin; the area-weighted mean (7.0 mm, thick blocks
    # such as trunk_bottom included) is the high corner; infill is treated as solid PLA (ASSUMPTION)
    t = (e["wall_median_mm"] if c.get("wall", "median") == "median" else e["wall_area_weighted_mean_mm"]) * 1e-3
    H = e["bbox_mm"][2] * 1e-3
    m_pla = dict(trunk=406.0, head=289.3)[name]   # print/SLICE_SUMMARY.md D22: g each minus support, trunk 7 parts, head + head_bot_sheet
    C_wall = m_pla * c["cp_pla"]
    C_air = dict(trunk=60.0 * 0.8, head=30.0 * 0.8)[name]   # boards, holder, wires, BEC case near air temperature: ASSUMPTION 60 g / 30 g at 0.8 J/gK
    return dict(A_out=A_out, A_in=A_in, t=t, H=H, C_wall=C_wall, C_air=C_air, R_cond=t / (PARAMS["k_pla"] * 0.5 * (A_in + A_out)))


def sw_R_on(v_gate, c):
    """Pololu 2815 combined on resistance: straight line between the two published maxima [S1], times sw_hot"""
    r = PARAMS["R_sw_4v5"] + (PARAMS["R_sw_10v"] - PARAMS["R_sw_4v5"]) * (np.clip(v_gate, 4.5, 10.0) - 4.5) / 5.5
    return r * c["sw_hot"]


def sw_Rth(c):
    """board to air from Pololu's own point: 6 A heats the MOSFETs to 55 C in 22 C still air at 12 V [S1]; the
    on resistance at 12 V is taken as the 10 V maximum times sw_hot"""
    P = 36.0 * PARAMS["R_sw_10v"] * c["sw_hot"]
    return (PARAMS["sw_6A_T"] - PARAMS["sw_amb"]) / P

# Electrical operating points from the lab's as-built power path (sim/POWER_PATH_SIM.md 'As built', our build,
# backlash walk, typical corner; JSON of the 2026-11-02 6:39 AM ET run): pack mean / RMS, BEC out mean / RMS, bus
# and BEC out volts. Other cases scale with the servo electrical power (BAM, sim/runtime_thermal.py convention).
OP = {"full": dict(pack_mean=5.300, pack_rms=5.607, bec_mean=4.184, bec_rms=4.466, v_bus=7.873, v_bec=7.196, v_servo=7.07),
      "nominal": dict(pack_mean=5.651, pack_rms=5.912, bec_mean=4.257, bec_rms=4.525, v_bus=6.838, v_bec=6.519, v_servo=6.39)}
Q_NGSPICE = 14 * 0.05 * 7.2           # W, the servo quiescent allowance inside those ngspice currents [L1] (data sheet: 21 mA [F1])


def electrical_point(P_servo, P_servo_ref, pack, c, walking):
    """pack and BEC currents for a servo electrical power P_servo (W): the lab's as-built ngspice point (backlash
    walk, our build) scaled by the servo power, with this corner's BEC efficiency; the 5 V branch draws the
    ngspice 5 W through 0.85 on the pack side [L1] (the head heat uses the corner's P5V, below)"""
    o = OP[pack]
    s_servo = (P_servo + Q_NGSPICE) / (P_servo_ref + Q_NGSPICE)
    bec_mean = o["bec_mean"] * s_servo
    bec_rms = bec_mean * (o["bec_rms"] / o["bec_mean"] if walking else 1.0)
    P_bec_out = o["v_bec"] * bec_mean
    P5_pack = 5.0 / 0.85
    P_bus = P_bec_out / c["eta_bec"] + P5_pack
    P_bus_ref = o["v_bec"] * o["bec_mean"] / 0.85 + P5_pack
    pack_mean = o["pack_mean"] * P_bus / P_bus_ref
    pack_rms = pack_mean * (o["pack_rms"] / o["pack_mean"] if walking else 1.0)
    P5 = c["P5V"]; eta5 = np.mean(PARAMS["eta_reg5"])
    return dict(bec_mean=bec_mean, bec_rms=bec_rms, P_bec_out=P_bec_out, P_bec_loss=P_bec_out / c["eta_bec"] - P_bec_out, P5=P5,
                P_reg_loss=P5 / eta5 - P5, pack_mean=pack_mean, pack_rms=pack_rms, v_bus=o["v_bus"])


def trunk_losses(ep, c):
    """W per item from the pack currents (RMS for I^2 R) and the BEC loss"""
    I = ep["pack_rms"]
    return dict(cells=2 * I * I * PARAMS["R_cell"], holder=I * I * c["R_holder"], bms=I * I * c["R_bms"], fuse=I * I * PARAMS["R_fuse"],
                xt30=I * I * PARAMS["R_xt30"], switch=I * I * sw_R_on(ep["v_bus"], c), wires=I * I * PARAMS["R_wires"],
                bec=ep["P_bec_loss"], bec_leads=ep["bec_rms"] ** 2 * 0.004, logic=0.15)
# bec_leads: 2 x 22 AWG x 100 mm in parallel plus P11 16 AWG 100 mm, about 4 mOhm [L1]; logic: Waveshare adapter,
# BNO055 and charger idle, ASSUMPTION 0.15 W.

# ----------------------------------------------------------------------------------------------------------------
def simulate(sched, heats, eps_of, c, Ta, t_end=90 * 60.0, dt=0.5, guard=None, A_scale=None, trunk_fan=1.0, record=10.0):
    """coupled transient: 14 servos (2 nodes each), trunk air and wall, cells, head air and wall.
    sched(t) -> state key; heats[key] = dict(servo=heat dict, trunk=dict of W, head=W).
    guard: dict(stop=C, resume=C, rest='stand') stands the robot when the hottest sensor reaches stop."""
    sc = servo_C(c); A = servo_area(c) * (A_scale if A_scale is not None else 1.0)
    et, eh = enclosure_params("trunk", c), enclosure_params("head", c)
    C_cells = 2 * PARAMS["m_cell_g"] * np.mean(PARAMS["cp_cell"])
    A_cells = 2 * (np.pi * 18.6 * 65.2) * 1e-6 * 0.5          # half of the two cell cans faces bay air (ASSUMPTION; the holder covers the rest)
    ins_t = np.array([INSIDE.get(n) == "trunk" for n in NAMES]); ins_h = np.array([INSIDE.get(n) == "head" for n in NAMES])
    Tw = np.full(14, Ta); Tb = np.full(14, Ta)
    T_ta, T_tw, T_c, T_ha, T_hw = Ta, Ta, Ta, Ta, Ta
    t_cut = np.full(14, np.nan); Tw_cut = np.full(14, np.nan)
    rec = dict(t=[], Ts=[], Tw=[], Tb=[], trunk_air=[], trunk_wall=[], cells=[], head_air=[], state=[])
    state_g, walk_t, n = "walk", 0.0, int(round(t_end / dt))
    max_Ts, max_Tw, max_Tb = np.full(14, -1e9), np.full(14, -1e9), np.full(14, -1e9)
    for s in range(n):
        t = s * dt
        key = sched(t)
        if guard is not None and key not in ("stand", "off"):
            hot = np.max(Tb + c["w"] * (Tw - Tb))
            if state_g == "walk" and hot >= guard["stop"]:
                state_g = "rest"
            elif state_g == "rest" and hot <= guard["resume"]:
                state_g = "walk"
            if state_g == "rest":
                key = guard.get("rest", "stand")
        walking = key not in ("stand", "off")
        if walking:
            walk_t += dt
        H = heats[key]; hs = H["servo"]
        Tamb = np.where(ins_t, T_ta, np.where(ins_h, T_ha, Ta))
        if s % 20 == 0:
            v = c["v_walk"] if walking else 0.0
            hh = np.array([h_total(Tb[j], Tamb[j], v * VFRAC[j], c["eps"]) for j in range(14)])
            # enclosure coefficients
            hto = h_total(T_tw, Ta, 0.13 if walking else 0.0, np.mean(PARAMS["eps_plastic"]), L=et["H"])
            hti = h_natural(T_ta, T_tw, L=0.5 * et["H"]) * c["h_in_f"] * trunk_fan
            hho = h_total(T_hw, Ta, 0.13 if walking else 0.0, np.mean(PARAMS["eps_plastic"]), L=eh["H"])
            hhi = h_natural(T_ha, T_hw, L=0.5 * eh["H"]) * c["h_in_f"]
            hc = h_natural(T_c, T_ta, L=0.0186) * c["h_in_f"] * trunk_fan
        on = np.isnan(t_cut)                                     # after its 70 C cut a servo carries no torque: idle only
        P_w = np.where(on, hs["P_cu25"] * (1 + PARAMS["alpha_cu"] * (Tw - 25.0)), 0.0)
        P_b = np.where(on, hs["P_board"] + hs["P_fric"], 0.0) + hs["P_idle"]
        q_wb = (Tw - Tb) / c["R_wc"]; q_ba = hh * A * (Tb - Tamb)
        Tw = Tw + dt * (P_w - q_wb) / c["C_w"]
        Tb = Tb + dt * (P_b + q_wb - q_ba) / sc["C_b"]
        # trunk: the heat of the electronics (not the cells) and of the servos inside leaves their surfaces partly by
        # convection into the air and partly by radiation straight to the walls: share AIR_SHARE to the air
        # (ASSUMPTION 0.6: convection and radiation coefficients are of the same size for eps 0.5 to 0.9 surfaces).
        # The cells (their own node) exchange with the air by convection and with the walls by radiation.
        Lt = H["trunk"]
        q_cells_conv = hc * A_cells * (T_c - T_ta)
        q_cells_rad = h_rad(T_c, T_tw, 0.9) * A_cells * (T_c - T_tw)
        q_comp = sum(v for k, v in Lt.items() if k not in ("cells", "holder")) + q_ba[ins_t].sum()
        q_tw = hti * et["A_in"] * (T_ta - T_tw)
        q_to = (T_tw - Ta) / (0.5 * et["R_cond"] + 1.0 / (hto * et["A_out"]))
        q_vent = c.get("G_vent", 0.0) * (T_ta - Ta)              # forced air exchange through vents (mitigation runs only)
        T_ta += dt * (c.get("air_share", 0.6) * q_comp + q_cells_conv - q_tw - q_vent) / et["C_air"]
        T_tw += dt * ((1 - c.get("air_share", 0.6)) * q_comp + q_cells_rad + q_tw - q_to) / et["C_wall"]
        T_c += dt * (Lt["cells"] + Lt["holder"] - q_cells_conv - q_cells_rad) / C_cells
        q_head = H["head"] + q_ba[ins_h].sum()
        q_hw = hhi * eh["A_in"] * (T_ha - T_hw)
        q_ho = (T_hw - Ta) / (0.5 * eh["R_cond"] + 1.0 / (hho * eh["A_out"]))
        T_ha += dt * (c.get("air_share", 0.6) * q_head - q_hw) / eh["C_air"]
        T_hw += dt * ((1 - c.get("air_share", 0.6)) * q_head + q_hw - q_ho) / eh["C_wall"]
        Ts = Tb + c["w"] * (Tw - Tb)
        new = np.isnan(t_cut) & (Ts >= PARAMS["T_cut"]); t_cut[new] = t; Tw_cut[new] = Tw[new]
        max_Ts = np.maximum(max_Ts, Ts); max_Tw = np.maximum(max_Tw, Tw); max_Tb = np.maximum(max_Tb, Tb)
        if s % int(round(record / dt)) == 0:
            for k_, v_ in (("t", t), ("Ts", Ts.copy()), ("Tw", Tw.copy()), ("Tb", Tb.copy()), ("trunk_air", T_ta), ("trunk_wall", T_tw),
                           ("cells", T_c), ("head_air", T_ha), ("state", key)):
                rec[k_].append(v_)
    out = {k: (np.array(v) if k != "state" else v) for k, v in rec.items()}
    out.update(t_cut=t_cut, Tw_at_cut=Tw_cut, walk_share=walk_t / t_end, max_Ts=max_Ts, max_Tw=max_Tw, max_Tb=max_Tb)
    return out


# ----------------------------------------------------------------------------------------------------------------
# Steady hot spots above the local air (W x K/W), and the BEC case from its size
def hot_spots(L, T_air, c, ep):
    out = {}
    # BEC Pro: free faces of its 47 x 33 x 22 mm box (the 47 x 33 face sits on 1.1 mm foam tape; no heat through it)
    a, b, h = PARAMS["bec_dims_mm"]
    A_bec = (2 * (a * b + a * h + b * h) - a * b) * 1e-6
    T = T_air + 20.0
    for _ in range(30):                      # h depends on the case temperature
        hb = h_natural(T, T_air, L=0.033) + h_rad(T, T_air, c["bec_eps"])
        T = T_air + L["bec"] / (hb * A_bec)
    out["bec_case"] = T
    # Pololu 2815
    out["switch_mosfets"] = T_air + L["switch"] * sw_Rth(c)
    # fuse holder body 50 x 17.2 x 17.2 mm, one long face on tape
    A_f = (2 * 17.2 * 17.2 + 3 * 50 * 17.2) * 1e-6
    T = T_air + 5.0
    for _ in range(30):
        hf = h_natural(T, T_air, L=0.0172) + h_rad(T, T_air, 0.9)
        T = T_air + L["fuse"] / (hf * A_f)
    out["fuse_holder"] = T
    out["bms"] = T_air + L["bms"] * c["Rbms_th"]
    return out


def regulator_hot(P_loss, T_air):
    """Pololu D30V30F5, 0.7 x 0.8 in board on foam tape: one face and the edges to the air"""
    A = (17.8 * 20.3 + 2 * (17.8 + 20.3) * 3.0) * 1e-6
    T = T_air + 5.0
    for _ in range(30):
        hr = h_natural(T, T_air, L=0.0178) + h_rad(T, T_air, 0.9)
        T = T_air + P_loss / (hr * A)
    return T

# ----------------------------------------------------------------------------------------------------------------
# Battery time to the D16 stop for our 2.65 kg build (sim/runtime_thermal.py discharge model, unchanged)
def d16_minutes():
    os.environ["ODM_SCRATCH"] = os.path.join(SCR, "rt_scratch")
    tr = os.path.join(SCR, "rt_scratch", "added_mass", "traces")
    os.makedirs(tr, exist_ok=True)
    for vn in ("ours", "stock"):
        p = os.path.join(tr, vn)
        if not os.path.exists(p):
            os.symlink(os.path.join(os.path.dirname(TRACES), vn), p)
    sys.path.insert(0, os.path.join(LAB, "sim"))
    import runtime_thermal as RT
    S = {c: RT.case_stats("ours", c) for c in ("stand_in_place", "walk_forward_0.15", "walk_backlash", "turn_1.0", "walk_side_0.2")}
    duty = {"continuous walk, plain model": {"walk_forward_0.15": 1.0}, "continuous walk, backlash model": {"walk_backlash": 1.0},
            "mixed walking (1/2 forward, 1/4 turn, 1/4 side)": {"walk_forward_0.15": 0.5, "turn_1.0": 0.25, "walk_side_0.2": 0.25},
            "stand and walk 50/50": {"stand_in_place": 0.5, "walk_forward_0.15": 0.5},
            "stand 75 %, walk 25 %": {"stand_in_place": 0.75, "walk_forward_0.15": 0.25},
            "stand and walk 50/50, backlash": {"stand_in_place": 0.5, "walk_backlash": 0.5},
            "stand 75 %, walk 25 %, backlash": {"stand_in_place": 0.75, "walk_backlash": 0.25}}
    out = {}
    for dn, mix in duty.items():
        cc = RT.CORNERS["typical"]
        Ps = sum(f * S[case]["per_kt"][str(cc["kt"])]["P_servo_W"] for case, f in mix.items())
        r = RT.discharge(RT.pack_power(Ps, cc), cc["R_path"], ("cell", 3.5))
        out[dn] = dict(minutes=round(r["minutes"], 1), P_servo_W=round(Ps, 2))
    Pservo = {c: S[c]["per_kt"]["1.148"]["P_servo_W"] for c in S}
    return out, Pservo

# ----------------------------------------------------------------------------------------------------------------
SESSIONS = {
    # name: (list of (state, seconds) repeated, walk model)
    "continuous walk, plain model": ([("walk", 60.0)], "plain"),
    "continuous walk, backlash model": ([("walk", 60.0)], "backlash"),
    "mixed walking (1/2 forward, 1/4 turn, 1/4 side)": ([("walk", 60.0)], "mixed"),
    "stand and walk 50/50": ([("walk", 60.0), ("stand", 60.0)], "plain"),
    "stand 75 %, walk 25 %": ([("walk", 30.0), ("stand", 90.0)], "plain"),
    "stand and walk 50/50, backlash": ([("walk", 60.0), ("stand", 60.0)], "backlash"),
    "stand 75 %, walk 25 %, backlash": ([("walk", 30.0), ("stand", 90.0)], "backlash"),
}


def make_sched(pattern):
    per = sum(d for _, d in pattern)
    def f(t):
        x = t % per
        for st, d in pattern:
            if x < d:
                return st
            x -= d
        return pattern[-1][0]
    return f


def em_ratio(walk_model, pack):
    """closed-loop winding RMS current at this pack state over the full-pack value, per servo, from the
    twin/electromech pack-state runs (out/states_<walk>.json, typical corner, seed none); None if absent"""
    f = os.path.join(EM_CSV, f"states_{'plain' if walk_model == 'mixed' else walk_model}.json")
    if pack == "full" or not os.path.exists(f):
        return None
    d = json.load(open(f))
    sel = {e["state"]: e["closed"]["Im_rms"] for e in d if e.get("kind") == "pack state" and e.get("seed") is None and e.get("corner") == "typical"}
    if "full" not in sel or pack not in sel:
        return None
    return np.array([sel[pack][n] / sel["full"][n] if sel["full"][n] > 0 else 1.0 for n in NAMES])


def build_heats(pack, c, Pservo, walk_model):
    """heat inputs for the 'walk' and 'stand' states. Full pack: the open-loop traces with the servo volts capped
    at the full-pack mean. Nominal pack: the full-pack heat times the closed-loop current ratio of twin/electromech
    when that file exists (the robot walks slower and draws less), else the traces capped at the nominal volts."""
    vcap = OP[pack]["v_servo"]
    ratio = em_ratio(walk_model, pack)
    if ratio is not None:
        vcap = OP["full"]["v_servo"]
    hs = {case: scale_heat(servo_heat(case, vcap, c["kt"]), c["cf"]) for case in CASES}
    if ratio is not None:
        for case in CASES:
            if case != "stand_in_place":
                hs[case] = dict(hs[case]); r2 = ratio ** 2
                for k in ("i2", "P_cu25", "P_board"):
                    hs[case][k] = hs[case][k] * r2
    if walk_model == "plain":
        hw, Pw = hs["walk_forward_0.15"], Pservo["walk_forward_0.15"]
    elif walk_model == "backlash":
        hw, Pw = hs["walk_backlash"], Pservo["walk_backlash"]
    else:
        hw = mix_heat([(0.5, hs["walk_forward_0.15"]), (0.25, hs["turn_1.0"]), (0.25, hs["walk_side_0.2"])])
        Pw = 0.5 * Pservo["walk_forward_0.15"] + 0.25 * Pservo["turn_1.0"] + 0.25 * Pservo["walk_side_0.2"]
    hst, Pst = hs["stand_in_place"], Pservo["stand_in_place"]
    out = {}
    for key, h, P, walking in (("walk", hw, Pw, True), ("stand", hst, Pst, False)):
        ep = electrical_point(P * c["cf"] ** 2, Pservo["walk_backlash"], pack, c, walking)
        L = trunk_losses(ep, c)
        head = ep["P5"] + ep["P_reg_loss"]
        out[key] = dict(servo=h, trunk=L, head=head, ep=ep)
    return out, hs


def run_all():
    d16, Pservo = d16_minutes()
    res = dict(d16=d16, Pservo=Pservo, runs={}, heat={}, protections={})
    # heat table and protection timers (central corner, full pack, cf 1)
    c0 = CORNERS["central"]
    for pack in ("full", "nominal"):
        for case in CASES:
            h = servo_heat(case, OP[pack]["v_servo"], "worst")
            res["heat"][f"{pack}|{case}"] = {n: dict(I_rms=float(np.sqrt(h["i2"][j])), P_cu25=float(h["P_cu25"][j]), P_board=float(h["P_board"][j]),
                                                     P_fric=float(h["P_fric"][j]), P_idle=float(h["P_idle"][j]), oc_run_s=float(h["oc_run"][j]),
                                                     ol_run_s=float(h["ol_run"][j]), I_2s_max=float(h["I_2s_max"][j]), I_peak=float(h["I_peak"][j]))
                                             for j, n in enumerate(NAMES)}
    # main grid: sessions x ambient x pack x corner
    for sname, (pattern, wm) in SESSIONS.items():
        for pack in ("full", "nominal"):
            for cn, c in CORNERS.items():
                heats, _ = build_heats(pack, c, Pservo, wm)
                for Ta in (25.0, 32.0):
                    r = simulate(make_sched(pattern), heats, None, c, Ta)
                    key = f"{sname}|{pack}|{cn}|{Ta:.0f}"
                    res["runs"][key] = summarize(r, d16.get(sname, d16.get(sname.replace(", backlash", ""), {})).get("minutes"), heats, c, Ta)
                    if cn == "central" and pack == "full":
                        res["runs"][key]["trace"] = dict(t=r["t"][::3].tolist(), Ts=r["Ts"][::3].round(2).tolist(), Tw=r["Tw"][::3].round(2).tolist(),
                                                         Tb=r["Tb"][::3].round(2).tolist(), trunk_air=r["trunk_air"][::3].round(2).tolist(),
                                                         cells=r["cells"][::3].round(2).tolist(), head_air=r["head_air"][::3].round(2).tolist())
        print("done", sname, flush=True)
    return res


def summarize(r, t_d16_min, heats, c, Ta):
    j_k = [NAMES.index("left_knee"), NAMES.index("right_knee")]
    t_cut = r["t_cut"] / 60.0
    out = dict(t_cut_min={n: (None if np.isnan(t_cut[j]) else round(float(t_cut[j]), 1)) for j, n in enumerate(NAMES)},
               Tw_at_cut={n: (None if np.isnan(r["Tw_at_cut"][j]) else round(float(r["Tw_at_cut"][j]), 1)) for j, n in enumerate(NAMES)},
               max_Ts={n: round(float(r["max_Ts"][j]), 1) for j, n in enumerate(NAMES)},
               max_Tw={n: round(float(r["max_Tw"][j]), 1) for j, n in enumerate(NAMES)},
               max_Tb={n: round(float(r["max_Tb"][j]), 1) for j, n in enumerate(NAMES)},
               t_d16_min=t_d16_min, walk_share=round(r["walk_share"], 3))
    if t_d16_min:
        i = int(np.clip(np.searchsorted(r["t"], t_d16_min * 60.0), 0, len(r["t"]) - 1))
        out["at_d16"] = dict(Ts={n: round(float(r["Ts"][i, j]), 1) for j, n in enumerate(NAMES)},
                             Tw={n: round(float(r["Tw"][i, j]), 1) for j, n in enumerate(NAMES)},
                             Tb={n: round(float(r["Tb"][i, j]), 1) for j, n in enumerate(NAMES)},
                             trunk_air=round(float(r["trunk_air"][i]), 1), trunk_wall=round(float(r["trunk_wall"][i]), 1),
                             cells=round(float(r["cells"][i]), 1), head_air=round(float(r["head_air"][i]), 1))
        hs = hot_spots(heats["walk"]["trunk"], float(r["trunk_air"][i]), c, heats["walk"]["ep"])
        out["at_d16"]["hot_spots"] = {k: round(float(v), 1) for k, v in hs.items()}
        out["at_d16"]["regulator"] = round(float(regulator_hot(heats["walk"]["ep"]["P_reg_loss"], float(r["head_air"][i]))), 1)
    out["end"] = dict(trunk_air=round(float(r["trunk_air"][-1]), 1), cells=round(float(r["cells"][-1]), 1), head_air=round(float(r["head_air"][-1]), 1))
    out["losses_walk"] = {k: round(float(v), 3) for k, v in heats["walk"]["trunk"].items()}
    out["losses_stand"] = {k: round(float(v), 3) for k, v in heats["stand"]["trunk"].items()}
    out["head_walk_W"] = round(float(heats["walk"]["head"]), 3)
    return out




def steady_servo(heat, c, Ta_vec, walking=True):
    """steady winding, body and sensor temperatures per servo (no time limit, no cut), for a constant heat dict"""
    A = servo_area(c)
    Tb = np.array(Ta_vec, float) + 10.0; Tw = Tb + 10.0
    v = c["v_walk"] if walking else 0.0
    for _ in range(200):
        P_w = heat["P_cu25"] * (1 + PARAMS["alpha_cu"] * (Tw - 25.0))
        P_b = heat["P_board"] + heat["P_fric"] + heat["P_idle"]
        h = np.array([h_total(Tb[j], Ta_vec[j], v * VFRAC[j], c["eps"]) for j in range(14)])
        Tb_new = Ta_vec + (P_w + P_b) / (h * A)
        Tw_new = Tb_new + P_w * c["R_wc"]
        if np.max(np.abs(Tb_new - Tb)) < 1e-4 and np.max(np.abs(Tw_new - Tw)) < 1e-4:
            break
        Tb, Tw = 0.5 * (Tb + Tb_new), 0.5 * (Tw + Tw_new)
    return dict(Tb=Tb, Tw=Tw, Ts=Tb + c["w"] * (Tw - Tb), R_ba=1.0 / (h * A))


# ----------------------------------------------------------------------------------------------------------------
# Sensitivity, mitigations, the electromech re-run, tables
def one_at_a_time(Pservo, d16):
    """vary one parameter from the central corner to its low and high value; right knee, full pack, 25 C"""
    base = CORNERS["central"]
    keys = ["a_mid", "v_walk", "eps", "gf", "cp_metal", "C_w", "R_wc", "w", "cf", "kt"]
    out = {}
    for k in keys:
        out[k] = {}
        for side in ("low", "high"):
            c = dict(base); c[k] = CORNERS[side][k]
            if k == "a_mid":
                c["a_contact"] = CORNERS[side]["a_contact"]
            row = {}
            for sname in ("continuous walk, plain model", "continuous walk, backlash model", "stand and walk 50/50"):
                pattern, wm = SESSIONS[sname]
                heats, _ = build_heats("full", c, Pservo, wm)
                r = simulate(make_sched(pattern), heats, None, c, 25.0, t_end=60 * 60.0)
                j = NAMES.index("right_knee")
                row[sname] = dict(value=c[k], t_cut_min=None if np.isnan(r["t_cut"][j]) else round(float(r["t_cut"][j] / 60), 1),
                                  max_Ts=round(float(r["max_Ts"][j]), 1))
            out[k][side] = row
    return out


def mitigations(Pservo, d16):
    base = CORNERS["central"]; out = {}
    plans = {
        "none": dict(c={}, guard=None, A_scale=None),
        "thermal guard: stand at 55 C, walk again at 45 C (Present Temperature)": dict(c={}, guard=dict(stop=55.0, resume=45.0, rest="stand"), A_scale=None),
        "thermal guard: stand at 55 C, walk again at 50 C": dict(c={}, guard=dict(stop=55.0, resume=50.0, rest="stand"), A_scale=None),
        "thermal guard with torque-off rests (robot on a stand): stop 55 C, resume 45 C": dict(c={}, guard=dict(stop=55.0, resume=45.0, rest="off"), A_scale=None),
        "clip-on aluminium heat sinks on the knee cases (+30 % effective area, ASSUMPTION)": dict(c={}, guard=None, A_scale="knees1.3"),
        "trunk fan and vents (forced exchange 0.3 W/K, 3 x inner convection, ASSUMPTION)": dict(c=dict(G_vent=0.3), guard=None, A_scale=None, fan=3.0),
    }
    for pname, p in plans.items():
        out[pname] = {}
        for sname in ("continuous walk, plain model", "continuous walk, backlash model", "stand and walk 50/50"):
            for Ta in (25.0, 32.0):
                c = dict(base); c.update(p["c"])
                pattern, wm = SESSIONS[sname]
                heats, _ = build_heats("full", c, Pservo, wm)
                # torque-off rest: servo heat is the idle current only; electronics as standing
                off = dict(servo={k: (np.zeros(14) if k != "P_idle" else heats["stand"]["servo"]["P_idle"]) for k in ("i2", "P_cu25", "P_board", "P_fric", "P_idle")},
                           trunk=heats["stand"]["trunk"], head=heats["stand"]["head"], ep=heats["stand"]["ep"])
                heats["off"] = off
                A_scale = None
                if p["A_scale"] == "knees1.3":
                    A_scale = np.array([1.3 if "knee" in n else 1.0 for n in NAMES])
                r = simulate(make_sched(pattern), heats, None, c, Ta, guard=p["guard"], A_scale=A_scale, trunk_fan=p.get("fan", 1.0))
                j = NAMES.index("right_knee")
                t16 = d16.get(sname, {}).get("minutes")
                i16 = int(np.clip(np.searchsorted(r["t"], (t16 or 90) * 60.0), 0, len(r["t"]) - 1))
                out[pname][f"{sname}|{Ta:.0f}"] = dict(t_cut_min=None if np.isnan(r["t_cut"][j]) else round(float(r["t_cut"][j] / 60), 1),
                                                       max_Ts_knee=round(float(r["max_Ts"][j]), 1), max_Tw_knee=round(float(r["max_Tw"][j]), 1),
                                                       walk_share=round(r["walk_share"], 3), trunk_air_at_d16=round(float(r["trunk_air"][i16]), 1),
                                                       cells_at_d16=round(float(r["cells"][i16]), 1),
                                                       walking_minutes_in_90=round(r["walk_share"] * 90, 1))
    return out


def steady_table(Pservo):
    out = {}
    for cn in ("low", "central", "high"):
        c = CORNERS[cn]
        for wm, case in (("plain", "walk_forward_0.15"), ("backlash", "walk_backlash")):
            h = scale_heat(servo_heat(case, OP["full"]["v_servo"], c["kt"]), c["cf"])
            for Ta in (25.0, 32.0):
                st = steady_servo(h, c, np.full(14, Ta))
                out[f"{cn}|{wm}|{Ta:.0f}"] = {n: dict(Tb=round(float(st["Tb"][j]), 1), Tw=round(float(st["Tw"][j]), 1), Ts=round(float(st["Ts"][j]), 1),
                                                      R_ba=round(float(st["R_ba"][j]), 2), P_total=round(float(h["P_cu25"][j] + h["P_board"][j] + h["P_fric"][j] + h["P_idle"][j]), 2))
                                              for j, n in enumerate(NAMES)}
    return out


def em_sessions():
    """the twin/electromech closed-loop session CSVs (5 s bins), when present: per-servo motor RMS current per bin"""
    files = sorted(glob.glob(os.path.join(EM_CSV, "session_*.csv")))
    out = {}
    for f in files:
        lines = [l for l in open(f).read().splitlines() if l and not l.startswith("#")]
        hdr = lines[0].split(","); rows = [[float(x) if x else np.nan for x in l.split(",")] for l in lines[1:]]
        A = np.array(rows)
        col = {h: i for i, h in enumerate(hdr)}
        if not all(f"im_rms_{SERVO_ID[n]}" in col for n in NAMES):
            continue
        out[os.path.basename(f)] = dict(t=A[:, col["t_s"]], im_rms=np.array([A[:, col[f"im_rms_{SERVO_ID[n]}"]] for n in NAMES]).T,
                                        i_pack=A[:, col["i_pack"]] if "i_pack" in col else None, v_bus=A[:, col["v_bus"]] if "v_bus" in col else None,
                                        i_bec=A[:, col["i_bec_out"]] if "i_bec_out" in col else None, fallen=A[:, col["fallen"]] if "fallen" in col else None)
    return out


def run_em(Pservo):
    """re-run the knee and all servos on the closed-loop currents: copper and board from each bin's motor RMS current,
    friction and idle from the open-loop trace of the same walk (not in the CSV)"""
    ses = em_sessions(); out = {}
    for name, S in ses.items():
        walk = "backlash" if "backlash" in name else "plain"
        for cn in ("central", "high", "low"):
            c = CORNERS[cn]
            base, _ = build_heats("full", c, Pservo, walk)
            fr = base["walk"]["servo"]
            R_loop = PARAMS["KTS"][0] / PARAMS["KT_OVER_R"]
            t = S["t"]
            def sched(tt, t=t):
                return int(np.clip(np.searchsorted(t, tt), 0, len(t) - 1))
            heats = {}
            for i in range(len(t)):
                i2 = np.nan_to_num(S["im_rms"][i]) ** 2 * c["cf"] ** 2
                heats[i] = dict(servo=dict(i2=i2, P_cu25=i2 * PARAMS["R_w25"], P_board=i2 * (R_loop - PARAMS["R_w25"]), P_fric=fr["P_fric"], P_idle=fr["P_idle"]),
                                trunk=base["walk"]["trunk"], head=base["walk"]["head"])
            for Ta in (25.0, 32.0):
                r = simulate(sched, heats, None, c, Ta, t_end=float(t[-1]))
                out[f"{name}|{cn}|{Ta:.0f}"] = dict(t_cut_min={n: (None if np.isnan(r["t_cut"][j]) else round(float(r["t_cut"][j] / 60), 1)) for j, n in enumerate(NAMES)},
                                                    max_Ts={n: round(float(r["max_Ts"][j]), 1) for j, n in enumerate(NAMES)},
                                                    session_min=round(float(t[-1]) / 60, 1),
                                                    knee_im_rms_mean={n: round(float(np.nanmean(S["im_rms"][:, NAMES.index(n)])), 3) for n in ("left_knee", "right_knee")})
    return out


def main():
    res = run_all()
    print("one at a time", flush=True)
    res["oat"] = one_at_a_time(res["Pservo"], res["d16"])
    print("mitigations", flush=True)
    res["mitigations"] = mitigations(res["Pservo"], res["d16"])
    res["steady"] = steady_table(res["Pservo"])
    res["corners"] = {cn: dict(c, **{k: round(float(v), 2) for k, v in servo_C(c).items()}) for cn, c in CORNERS.items()}
    res["enclosure"] = {cn: {k: {kk: round(float(vv), 5) for kk, vv in enclosure_params(k, CORNERS[cn]).items()} for k in ("trunk", "head")} for cn in CORNERS}
    res["switch_Rth_K_per_W"] = {cn: round(sw_Rth(CORNERS[cn]), 1) for cn in CORNERS}
    try:
        res["em"] = run_em(res["Pservo"])
    except Exception as e:  # noqa: BLE001
        res["em"] = dict(error=repr(e))
    json.dump(res, open(os.path.join(OUT, "results.json"), "w"), indent=1, default=float)
    small = {k: v for k, v in res.items() if k != "runs"}
    small["runs"] = {k: {kk: vv for kk, vv in v.items() if kk != "trace"} for k, v in res["runs"].items()}
    json.dump(small, open(os.path.join(HERE, "results_summary.json"), "w"), indent=0, default=float)
    write_tables(res)
    try:
        plot(res)
    except Exception as e:  # noqa: BLE001
        print("plot skipped:", e)
    print("wrote", os.path.join(OUT, "results.json"), "and", os.path.join(HERE, "results_summary.json"))


def _fmt_cut(t, mx):
    return f"**{t:.0f} min**" if t is not None else f"no cut (peak {mx:.0f} C)"


def write_tables(res):
    L = []; P = L.append
    P("# Thermal twin tables (generated by twin_thermal.py; sim pass only)\n")
    P("## D16 battery stop, our 2.65 kg build (sim/runtime_thermal.py discharge model, typical corner)\n")
    P("| Session | Minutes to the D16 stop | Servo electrical W |"); P("|---|---|---|")
    for k, v in res["d16"].items():
        P(f"| {k} | {v['minutes']:.1f} | {v['P_servo_W']:.1f} |")
    P("\n## Heat per servo, full pack (BAM model, worst kt; W)\n")
    for case in ("walk_forward_0.15", "walk_backlash", "stand_in_place"):
        P(f"\n{case}:\n"); P("| Servo | I rms (A) | winding copper at 25 C | board | friction | idle | total | longest run over 2.0 A (s) | longest run over 80 % duty (s) | highest 2 s mean current (A) |")
        P("|---|---|---|---|---|---|---|---|---|---|")
        for n in NAMES:
            h = res["heat"][f"full|{case}"][n]
            tot = h["P_cu25"] + h["P_board"] + h["P_fric"] + h["P_idle"]
            P(f"| {n} | {h['I_rms']:.2f} | {h['P_cu25']:.2f} | {h['P_board']:.2f} | {h['P_fric']:.2f} | {h['P_idle']:.2f} | {tot:.2f} | {h['oc_run_s']:.3f} | {h['ol_run_s']:.3f} | {h['I_2s_max']:.2f} |")
    P("\n## Knee (worse of the two): time to the 70 C cut or the peak reading within 90 min\n")
    P("| Session | Pack | Room | low corner | central corner | high corner | central: knee reading / winding at the D16 stop |")
    P("|---|---|---|---|---|---|---|")
    for sname in SESSIONS:
        for pack in ("full", "nominal"):
            for Ta in ("25", "32"):
                cells = []
                for cn in ("low", "central", "high"):
                    r = res["runs"][f"{sname}|{pack}|{cn}|{Ta}"]
                    ts = [r["t_cut_min"][k] for k in ("left_knee", "right_knee") if r["t_cut_min"][k] is not None]
                    mx = max(r["max_Ts"]["left_knee"], r["max_Ts"]["right_knee"])
                    cells.append(_fmt_cut(min(ts) if ts else None, mx))
                rc = res["runs"][f"{sname}|{pack}|central|{Ta}"]
                kc = [rc["t_cut_min"][k] for k in ("left_knee", "right_knee") if rc["t_cut_min"][k] is not None]
                if kc and rc.get("t_d16_min") and min(kc) <= rc["t_d16_min"]:
                    kk = min(("left_knee", "right_knee"), key=lambda k: rc["t_cut_min"][k] if rc["t_cut_min"][k] is not None else 1e9)
                    tail = f"cut at {min(kc):.0f} min, winding {rc['Tw_at_cut'][kk]:.0f} C then"
                elif rc.get("at_d16"):
                    a = rc["at_d16"]; kk = max(("left_knee", "right_knee"), key=lambda k: a["Ts"][k])
                    tail = f"{a['Ts'][kk]:.0f} C / {a['Tw'][kk]:.0f} C at {rc['t_d16_min']:.0f} min"
                else:
                    tail = "-"
                P(f"| {sname} | {pack} | {Ta} C | " + " | ".join(cells) + f" | {tail} |")
    P("\n## Every servo, central corner, full pack: time to the cut (min) or peak reading (C)\n")
    snames = list(SESSIONS)
    P("| Servo | " + " | ".join(f"{s} {Ta} C" for s in snames[:5] for Ta in ("25", "32")) + " |")
    P("|---|" + "---|" * 10)
    for n in NAMES:
        cells = []
        for s in snames[:5]:
            for Ta in ("25", "32"):
                r = res["runs"][f"{s}|full|central|{Ta}"]
                t = r["t_cut_min"][n]
                cells.append(f"**{t:.0f}**" if t is not None else f"{r['max_Ts'][n]:.0f} C")
        P(f"| {n} | " + " | ".join(cells) + " |")
    P("\n## Steady temperatures if walking never stopped (no cut applied), full pack\n")
    P("| Corner, walk, room | right knee: body / winding / reading | left knee | worst ankle | worst hip pitch | head pitch |"); P("|---|---|---|---|---|---|")
    for k, v in res["steady"].items():
        def f(n): return f"{v[n]['Tb']:.0f} / {v[n]['Tw']:.0f} / {v[n]['Ts']:.0f}"
        an = max(("left_ankle", "right_ankle"), key=lambda n: v[n]["Ts"]); hp = max(("left_hip_pitch", "right_hip_pitch"), key=lambda n: v[n]["Ts"])
        P(f"| {k.replace('|', ', ')} C | {f('right_knee')} | {f('left_knee')} | {an}: {f(an)} | {hp}: {f(hp)} | {f('head_pitch')} |")
    P("\n## One parameter at a time from the central corner (right knee, full pack, 25 C)\n")
    P("| Parameter | low value: plain / backlash / 50-50 | high value: plain / backlash / 50-50 |"); P("|---|---|---|")
    for k, v in res["oat"].items():
        def g(side):
            row = v[side]; val = list(row.values())[0]["value"]
            return f"{val}: " + " / ".join((f"{x['t_cut_min']:.0f} min" if x["t_cut_min"] is not None else f"{x['max_Ts']:.0f} C") for x in row.values())
        P(f"| {k} | {g('low')} | {g('high')} |")
    P("\n## Electronics in the trunk and the head (central corner, full pack, at the D16 stop)\n")
    P("| Session, room | trunk air | trunk wall | cells | head air | BEC case | Pololu 2815 MOSFETs | fuse holder | BMS | 5 V regulator |"); P("|---|---|---|---|---|---|---|---|---|---|")
    for sname in SESSIONS:
        for Ta in ("25", "32"):
            for cn in ("central", "high"):
                r = res["runs"][f"{sname}|full|{cn}|{Ta}"]
                a = r.get("at_d16")
                if not a:
                    continue
                hs = a["hot_spots"]
                P(f"| {sname}, {Ta} C, {cn} | {a['trunk_air']:.0f} | {a['trunk_wall']:.0f} | {a['cells']:.0f} | {a['head_air']:.0f} | {hs['bec_case']:.0f} | {hs['switch_mosfets']:.0f} | {hs['fuse_holder']:.0f} | {hs['bms']:.0f} | {a['regulator']:.0f} |")
    P("\n## Trunk losses while walking (W), central and high corner, full pack\n")
    for sname in ("continuous walk, plain model", "continuous walk, backlash model"):
        for cn in ("central", "high"):
            r = res["runs"][f"{sname}|full|{cn}|25"]
            P(f"- {sname}, {cn}: " + ", ".join(f"{k} {v:.2f}" for k, v in r["losses_walk"].items()) + f"; total {sum(r['losses_walk'].values()):.2f} W; head 5 V branch and regulator {r['head_walk_W']:.2f} W")
    P("\n## Printed parts against the servo cases (geometry.json) and the servo body temperature they see\n")
    P("Body node = the servo case and its contents (the PLA at a touching face sees about this). PLA: HDT 49 to 57 C, Tg 55 to 60 C, Vicat 66.2 C (Overture Easy PLA).\n")
    P("| Servo | printed parts touching the case (under 0.3 mm), mm2 | horn faces on printed parts, mm2 | body peak: plain walk 25 / 32 C | backlash walk 25 / 32 C | 50/50 25 / 32 C | 25/75 25 / 32 C |")
    P("|---|---|---|---|---|---|---|")
    PRN = {"left_knee_to_ankle_left_sheet": "knee_to_ankle_left_sheet", "left_knee_to_ankle_right_sheet": "knee_to_ankle_right_sheet"}
    for n in NAMES:
        g = GEOM["servos"][n]
        parts = ", ".join(f"{PRN.get(x['part'], x['part'])} {x['area_under_0p3mm_mm2']:.0f}" for x in g["contacts"] if x["area_under_0p3mm_mm2"] > 0)
        horns = ", ".join(f"{h['horn'].replace('_palonier', '')} on {PRN.get(h['part'], h['part'])} {h['area_under_0p3mm_mm2']:.0f}" for h in g["horn_contacts"])
        cells = []
        for s_ in ("continuous walk, plain model", "continuous walk, backlash model", "stand and walk 50/50", "stand 75 %, walk 25 %"):
            cells.append(" / ".join(f"{res['runs'][f'{s_}|full|central|{Ta}']['max_Tb'][n]:.0f}" for Ta in ("25", "32")))
        P(f"| {n} | {parts or '-'} | {horns or '-'} | " + " | ".join(cells) + " |")
    P("\n## Mitigations (central corner, full pack; right knee)\n")
    P("| Plan | Session, room | knee: time to cut or peak | knee winding peak | walking minutes in 90 | trunk air / cells at the D16 stop |"); P("|---|---|---|---|---|---|")
    for pname, v in res["mitigations"].items():
        for key, x in v.items():
            s, Ta = key.split("|")
            cut = f"**{x['t_cut_min']:.0f} min**" if x["t_cut_min"] is not None else f"no cut, peak {x['max_Ts_knee']:.0f} C"
            P(f"| {pname} | {s}, {Ta} C | {cut} | {x['max_Tw_knee']:.0f} C | {x['walking_minutes_in_90']:.0f} | {x['trunk_air_at_d16']:.0f} / {x['cells_at_d16']:.0f} C |")
    if isinstance(res.get("em"), dict) and res["em"] and "error" not in res["em"]:
        P("\n## Re-run on the twin/electromech closed-loop sessions\n")
        P("| Session file, corner, room | session minutes | knee time to cut or peak | knee mean motor RMS current |"); P("|---|---|---|---|")
        for k, v in res["em"].items():
            ts = [v["t_cut_min"][n] for n in ("left_knee", "right_knee") if v["t_cut_min"][n] is not None]
            mx = max(v["max_Ts"]["left_knee"], v["max_Ts"]["right_knee"])
            P(f"| {k.replace('|', ', ')} C | {v['session_min']} | {_fmt_cut(min(ts) if ts else None, mx)} | {v['knee_im_rms_mean']} |")
    open(os.path.join(HERE, "tables.md"), "w").write("\n".join(L) + "\n")


def plot(res):
    """right knee reading and winding until the D16 stop (a cross marks the 70 C cut: the robot falls there);
    trunk air, cells and head air until the D16 stop"""
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 3, figsize=(13.5, 4.2))
    cols = {"continuous walk, plain model": "#4a6fa5", "continuous walk, backlash model": "#c0392b", "stand and walk 50/50": "#1e8449", "stand 75 %, walk 25 %": "#b9770e"}
    j = NAMES.index("right_knee")
    for ax, Ta in zip(axs[:2], ("25", "32")):
        for s, col in cols.items():
            run = res["runs"][f"{s}|full|central|{Ta}"]; tr = run.get("trace")
            if not tr:
                continue
            t = np.array(tr["t"]) / 60; Ts = np.array(tr["Ts"])[:, j]; Tw = np.array(tr["Tw"])[:, j]
            t16 = res["d16"].get(s, {}).get("minutes") or t[-1]
            tc = run["t_cut_min"]["right_knee"]
            end = min(t16, tc) if tc is not None else t16
            m = t <= end
            ax.plot(t[m], Ts[m], color=col, lw=1.4, label=f"{s}: reading")
            ax.plot(t[m], Tw[m], color=col, lw=0.8, ls=":", label=f"{s}: winding")
            if tc is not None and tc <= t16:
                ax.plot([tc], [70.0], marker="x", color=col, ms=8, mew=2)
            else:
                ax.plot([t16], [Ts[m][-1]], marker="|", color=col, ms=10, mew=2)
        ax.axhline(70, color="k", lw=0.9); ax.text(0.5, 71.5, "70 C torque cut (x: cut, the robot falls; |: D16 battery stop)", fontsize=6.5)
        ax.set_xlabel("minutes from a cold start"); ax.set_ylabel("right knee (C)"); ax.set_ylim(20, 140); ax.set_xlim(0, 70); ax.grid(alpha=0.3)
        ax.set_title(f"Right knee, central corner, full pack, room {Ta} C (sim pass only)", fontsize=8)
    axs[0].legend(fontsize=5.5, loc="upper right", ncol=1)
    for s, col in (("continuous walk, backlash model", "#c0392b"), ("continuous walk, plain model", "#4a6fa5"), ("stand and walk 50/50", "#1e8449")):
        tr = res["runs"][f"{s}|full|central|25"]["trace"]
        t = np.array(tr["t"]) / 60; m = t <= res["d16"][s]["minutes"]
        axs[2].plot(t[m], np.array(tr["trunk_air"])[m], color=col, lw=1.3, label=f"trunk air, {s}")
        axs[2].plot(t[m], np.array(tr["cells"])[m], color=col, lw=1.0, ls="--", label=f"cells, {s}")
        axs[2].plot(t[m], np.array(tr["head_air"])[m], color=col, lw=0.9, ls=":", label=f"head air, {s}")
    axs[2].axhline(60, color="k", lw=0.8); axs[2].text(0.5, 60.6, "P30B discharge limit 60 C", fontsize=7)
    axs[2].set_xlabel("minutes, to the D16 battery stop"); axs[2].set_ylabel("C"); axs[2].set_ylim(20, 65); axs[2].grid(alpha=0.3)
    axs[2].legend(fontsize=5.5, loc="lower right")
    axs[2].set_title("Trunk air, cells, head air, central corner, 25 C room", fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "twin_thermal.png"), dpi=80); plt.close(fig)


if __name__ == "__main__":
    main()
