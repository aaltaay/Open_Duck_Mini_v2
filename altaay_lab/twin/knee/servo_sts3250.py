"""Feetech STS3250 knee servo for the duck twins (D32, SERVO_UPGRADE_OPTIONS.md option A). Sim pass only, calc only.

Every number is from a cited source, or marked ASSUMPTION (a C001 stand-in) or BLOCKER.
[F5] Feetech STS3250 product specification A/0, 2024-01-16 (feetech.cn file 6391772424007467984928587.pdf, sha256 92926b05...
     read 2026-11-02): 12 V typical, 6 to 12 V rated input; no load 0.133 s/60 deg (75 RPM) at 12 V; stall 50 kg.cm and 4.2 A
     at 12 V; idle 24 mA; rated 16 kg.cm and 1.4 A; terminal resistance 1.2 ohm; Kt 11 kg.cm/A; 1/345; 74.5 +/- 1 g;
     45.22 x 24.72 x 35 mm, aluminium case, steel gears, coreless motor, backlash 0.5 deg or less; protections 7-11: overload
     over 80 % of stall for 2 s, over-current over 3.8 A for 2 s (both cleared by a new position command), over 14 V or under
     4 V, over 70 C torque off; operating -20 to 60 C.
[F1] Feetech ST-3215-C001 specification (the twin's C001, twin/thermal/twin_thermal.py PARAMS [F1], servo_sts3215.py
     datasheet_check): 19.5 kg.cm and 2.5 A at 7.4 V, 0.192 s/60 deg at 7.4 V, Kt 8 kg.cm/A, 2.5 ohm, 55 g.
[B1] the twin's C001 is the BAM identification (servo_sts3215.py): torque limit 3.23 Nm at 7.4 V, kt 1.148, loop R 2.630
     ohm (winding 2.5 ohm, the rest 0.130 ohm), MJCF damping 0.56, frictionloss 0.068, armature 0.027.
[R3] Robo9, "Feetech STS3250 smart actuator: evaluation of accuracy, torque and backlash", robonine.com, published
     2025-11-28, modified 2026-02-08 (page sha256 04635622..., read 2026-11-03): section 3.3, 2.0 kg on a 100 mm arm
     (20 kg.cm), continuous oscillation, 12 V, room 25 +/- 2 C, reading 40, 48, 56, 64, 70 C at 0, 2, 4, 6, 8 min.

How the STS3250 enters the twin: the twin's C001 is BAM-identified, and its sheet values differ from BAM (stall 1.91 Nm on
the sheet, 3.23 Nm in BAM). So the STS3250 is the twin's C001 times the ratio of the two Feetech sheets, at the same volts:
  torque limit per volt  x 1.581  (50 kg.cm / 12 V against 19.5 kg.cm / 7.4 V)                       [F5, F1]
  no-load speed per volt x 0.890  (0.133 s/60 deg at 12 V against 0.192 s at 7.4 V)                   [F5, F1]
  current per Nm, copper resistance: the band below (published Kt and R, or the stall line)           [F5, F1]
BAM has one constant for torque per amp and back-EMF; the two STS3250 sheets numbers do not fit one constant, so the model
splits them: torque = (kt / R) u - (kt ke / R) w, motor current (u - ke w) / R, applied volts u up to pmax x V.
The joint damping is then kt ke / R + fv = 1.00 Nm s/rad (set by the published stall and no-load speed; fv is the C001's).

Band (both ends keep the published stall, no-load speed, 70 C cut, 3.8 A / 2 s, 74.5 g):
  low  (cool): Feetech's published Kt 11 kg.cm/A and terminal R 1.2 ohm: copper per Nm^2 0.254 x the C001's;
               heat with the C001 thermal values (ASSUMPTION stand-in for the unpublished STS3250 thermal resistance).
  high (hot):  the stall line (50 kg.cm / 4.2 A, 12 V / 4.2 A): copper per Nm^2 0.414 x the C001's;
               heat x the factor that makes the C001 thermal model reproduce Robo9's measured STS3250 rise [R3].
ASSUMPTION stand-ins (C001 values) in both ends: frictionloss 0.068 Nm, viscous friction 0.059 Nm s/rad, armature 0.027
kg m2, the 0.13 ohm non-winding share of the loop resistance (low end), the servo's heat capacity, case area and sensor
share (twin_thermal.py central corner), firmware error gain 0.166 per P count.
BLOCKER: a bench BAM identification of one STS3250 at 7.2 V (bam/feetech/record.py pendulum, as Rhoban did for the STS3215),
plus a TO1-style heat hold of the same unit. Until then the band is the answer.
"""
import importlib.util, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TWIN = os.path.dirname(HERE)
KGCM = 0.0980665                      # Nm per kg.cm
W60 = math.pi / 3.0                   # rad in 60 deg

F5 = dict(V_typ=12.0, s60=0.133, rpm=75, I_noload=0.280, stall_kgcm=50.0, I_stall=4.2, I_idle=0.024, V_rated=(6.0, 12.0),
          rated_kgcm=16.0, I_rated=1.4, R_term=1.2, Kt_kgcm_A=11.0, gear=345, mass_g=74.5, backlash_deg=0.5, T_cut=70.0,
          T_oper_max=60.0, OC_A=3.8, OC_s=2.0, OL_frac=0.80, OL_s=2.0, UV_V=4.0, OV_V=14.0, size_mm=(45.22, 24.72, 35.0))
F1 = dict(V_typ=7.4, s60=0.192, stall_kgcm=19.5, I_stall=2.5, R_term=2.5, Kt_kgcm_A=8.0, mass_g=55.0)
B1 = dict(V=7.4, tau=3.23, kt=1.148, R_w=2.5, damping=0.56, frictionloss=0.068, armature=0.027, P_train=32, P_runtime=30,
          error_gain=0.166)
B1["R"] = B1["kt"] / (B1["tau"] / B1["V"])                       # 2.630 ohm (servo_sts3215.py R_M)
B1["fv"] = B1["damping"] - B1["kt"] * B1["tau"] / B1["V"]          # 0.0589, the live twin's fv
R3 = dict(load_kgcm=20.0, V=12.0, Ta=25.0, T0=40.0, t_s=(0, 120, 240, 360, 480), T_C=(40, 48, 56, 64, 70))

# ratios of the two Feetech sheets at the same volts
R_TAU = (F5["stall_kgcm"] / F5["V_typ"]) / (F1["stall_kgcm"] / F1["V_typ"])                 # 1.5812
R_W0 = (W60 / F5["s60"] / F5["V_typ"]) / (W60 / F1["s60"] / F1["V_typ"])                     # 0.8902
KT_BAND = dict(low=F5["Kt_kgcm_A"] / F1["Kt_kgcm_A"],                                        # 1.375 published
               high=(F5["stall_kgcm"] / F5["I_stall"]) / (F1["stall_kgcm"] / F1["I_stall"]))  # 1.526 stall line
RW_BAND = dict(low=F5["R_term"] / F1["R_term"],                                              # 0.480 published
               high=(F5["V_typ"] / F5["I_stall"]) / (F1["V_typ"] / F1["I_stall"]))            # 0.965 stall line
BANDS = ("low", "high")


def model(band="high", damping=None):
    """the STS3250 in the twin frame at 7.4 V (the twin scales the limit and the gain with V / 7.4, as for the C001).
    damping: a stand-in for the joint damping (for example the C001's 0.56, ASSUMPTION) instead of the published
    torque-speed line; the back-EMF constant follows it and the no-load speed is then not the sheet's"""
    assert band in BANDS
    tau74 = B1["tau"] * R_TAU                                         # 5.107 Nm at 7.4 V, 4.969 Nm at 7.2 V
    w0_c001 = (B1["tau"] - B1["frictionloss"]) / B1["damping"]       # 5.646 rad/s, the twin C001's no load at 7.4 V
    w0 = w0_c001 * R_W0                                               # 5.027 rad/s at 7.4 V
    bemf = (tau74 - B1["frictionloss"]) / w0 - B1["fv"]              # kt ke / R: 0.944 Nm s/rad
    if damping is not None:
        bemf = float(damping) - B1["fv"]; w0 = (tau74 - B1["frictionloss"]) / float(damping)
    kt = B1["kt"] * KT_BAND[band]
    Rw = B1["R_w"] * RW_BAND[band]
    R = Rw + (B1["R"] - B1["R_w"])                                    # winding + the C001's 0.130 ohm (ASSUMPTION)
    pmax = tau74 * R / (kt * B1["V"])
    if pmax > 1.0:                                                    # the stall line itself: full duty, R from the stall
        pmax = 1.0; R = kt * B1["V"] / tau74
    ke = bemf * R / kt
    cu = (Rw / kt ** 2) / (B1["R_w"] / B1["kt"] ** 2)
    return dict(band=band, damping_stand_in=damping, tau74=tau74, kt=kt, ke=ke, R=R, R_w=Rw, pmax=pmax, damping=bemf + B1["fv"], bemf=bemf,
                frictionloss=B1["frictionloss"], armature=B1["armature"], w0_74=w0, copper_per_Nm2_vs_c001=cu,
                oc_A=F5["OC_A"], oc_s=F5["OC_s"], ol_frac=F5["OL_frac"], ol_s=F5["OL_s"], T_cut=F5["T_cut"], uv_V=F5["UV_V"],
                mass_g=F5["mass_g"], dmass_g=F5["mass_g"] - F1["mass_g"], heat_factor=1.0)


def electrical(F, w, V, mdl):
    """applied volts, motor current, supply current (no braking credit) for knee torque F (Nm) and joint speed w"""
    u = np.clip(np.asarray(F, float) * mdl["R"] / mdl["kt"], -mdl["pmax"] * np.asarray(V, float), mdl["pmax"] * np.asarray(V, float))
    im = (u - mdl["ke"] * np.asarray(w, float)) / mdl["R"]
    return u, im, np.maximum(u * im, 0.0) / np.maximum(V, 0.5)


def firmware_P(mdl, p_c001=B1["P_runtime"]):
    """register 21 (position P) that gives the C001's stiffness: kp = V x P x error gain x kt / R (BAM mapping [B1])"""
    return p_c001 * (B1["tau"] / B1["V"]) / (mdl["tau74"] / B1["V"] / mdl["pmax"])


def check_sheet(mdl):
    """the model's stall, no-load speed and stall current at 7.2 and 12 V against the sheet [F5]"""
    out = {}
    for V in (7.2, 12.0):
        s = V / B1["V"]
        w0 = (mdl["tau74"] * s - mdl["frictionloss"]) / mdl["damping"]
        out[f"{V:g} V"] = dict(model_stall_Nm=round(mdl["tau74"] * s, 3), sheet_stall_Nm=round(F5["stall_kgcm"] * KGCM * V / 12, 3),
                               model_no_load_rad_s=round(w0, 3), sheet_no_load_rad_s=round(W60 / F5["s60"] * V / 12, 3),
                               model_stall_A=round(mdl["pmax"] * V / mdl["R"], 3), sheet_stall_A=round(F5["I_stall"] * V / 12, 3))
    return out


def load_thermal():
    p = os.path.join(TWIN, "thermal", "twin_thermal.py")
    os.environ.setdefault("TWIN_SCRATCH", os.path.join(os.path.expanduser("~"), ".cache", "duck_knee_scratch"))
    spec = importlib.util.spec_from_file_location("twin_thermal_knee", p); TT = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(TT); return TT


def robo9_rise(mdl, k=1.0, TT=None, corner="central", t_end=900.0, dt=0.5):
    """[R3] section 3.3 in the twin's two-node servo model with the C001 thermal values (ASSUMPTION stand-in): one servo
    on a bench (whole case free, still air), 20 kg.cm held (ASSUMPTION: the load torque all through the swing; the swing
    and its accelerations are not given), start 40 C in both nodes, room 25 C. Heat x k. Returns (times, readings)."""
    TT = TT or load_thermal()
    c = TT.CORNERS[corner]; P = TT.PARAMS
    sc = TT.servo_C(c)
    A = TT.GEOM["servos"]["left_knee"]["outer_case_area_mm2"] * 1e-6
    tau = R3["load_kgcm"] * KGCM
    im = tau / mdl["kt"]
    Tw = Tb = R3["T0"]; ts, Ts = [], []
    for s in range(int(t_end / dt) + 1):
        ts.append(s * dt); Ts.append(Tb + c["w"] * (Tw - Tb))
        Pw = k * im * im * mdl["R_w"] * (1 + P["alpha_cu"] * (Tw - 25.0))
        Pb = k * im * im * (mdl["R"] - mdl["R_w"]) + F5["I_idle"] * R3["V"]
        q_wb = (Tw - Tb) / c["R_wc"]; q_ba = TT.h_total(Tb, R3["Ta"], 0.0, c["eps"]) * A * (Tb - R3["Ta"])
        Tw += dt * (Pw - q_wb) / c["C_w"]; Tb += dt * (Pb + q_wb - q_ba) / sc["C_b"]
    return np.array(ts), np.array(Ts)


def t_reach(ts, Ts, T):
    i = np.where(Ts >= T)[0]
    return float(ts[i[0]]) if len(i) else None


def robo9_factor(mdl, TT=None):
    """the heat factor k that makes the reading reach 70 C at 8 min, as Robo9 measured (bisection; 1 if the model is
    already as fast)"""
    TT = TT or load_thermal()
    t1 = t_reach(*robo9_rise(mdl, 1.0, TT), 70.0)
    if t1 is not None and t1 <= 480.0:
        return 1.0, t1
    lo, hi = 1.0, 20.0
    for _ in range(40):
        k = 0.5 * (lo + hi); t = t_reach(*robo9_rise(mdl, k, TT), 70.0)
        if t is not None and t <= 480.0:
            hi = k
        else:
            lo = k
    return hi, t1


def band_model(band, TT=None, damping=None):
    """the model of one band end with its heat factor (low: 1, the C001 stand-in; high: the Robo9 factor)"""
    m = model(band, damping)
    if band == "high":
        m["heat_factor"], m["robo9_t70_at_k1_s"] = robo9_factor(m, TT)
    return m


def knee_arrays(names, band, TT=None):
    """per-servo arrays (names order) for the live twin: C001 everywhere, the STS3250 on the two knees"""
    m = band_model(band, TT); n = len(names)
    kn = np.array(["knee" in s for s in names])
    f = lambda a, b: np.where(kn, b, a).astype(float)
    return dict(model=m, knee=kn, ktau=f(np.full(n, B1["kt"]), m["kt"]), ke=f(np.full(n, B1["kt"]), m["ke"]),
                R0=f(np.full(n, B1["R"]), m["R"]), Rw25=f(np.full(n, B1["R_w"]), m["R_w"]), pmax=f(np.ones(n), m["pmax"]),
                tau0=f(np.full(n, B1["tau"]), m["tau74"]), heat=f(np.ones(n), m["heat_factor"]))


# ------------------------------------------------------------------------------------------------ MuJoCo helpers
def add_point_mass(m, body, pos, dm):
    """add a point mass dm (kg) at pos (body frame) to a compiled MuJoCo model's body (mass, centre, inertia, subtree)"""
    import mujoco
    M0 = float(m.body_mass[body]); c0 = m.body_ipos[body].copy()
    Rq = np.zeros(9); mujoco.mju_quat2Mat(Rq, m.body_iquat[body]); Rq = Rq.reshape(3, 3)
    I0 = Rq @ np.diag(m.body_inertia[body]) @ Rq.T
    M1 = M0 + dm; c1 = (M0 * c0 + dm * np.asarray(pos, float)) / M1
    pa = lambda mm, d: mm * (d @ d * np.eye(3) - np.outer(d, d))
    I1 = I0 + pa(M0, c0 - c1) + pa(dm, np.asarray(pos, float) - c1)
    ev, V = np.linalg.eigh(I1)
    if np.linalg.det(V) < 0:
        V[:, 0] = -V[:, 0]
    q = np.zeros(4); mujoco.mju_mat2Quat(q, V.reshape(-1))
    m.body_mass[body] = M1; m.body_ipos[body] = c1; m.body_inertia[body] = ev; m.body_iquat[body] = q
    b = body
    while True:
        m.body_subtreemass[b] += dm
        if b == 0:
            break
        b = int(m.body_parentid[b])
    return dict(body=int(body), mass_before_kg=M0, mass_after_kg=M1)


def knee_servo_site(m, knee_joint):
    """(body, position in that body) of the knee servo case: the knee joint's parent body holds the servo (BOM_FULL F07:
    the knee servo screws into the thigh); its centre is the mean of that body's servo case mesh geoms (names wj-wk00, the
    Feetech case meshes of the URDF, SERVO_UPGRADE_OPTIONS.md section 1), else the knee axis point."""
    import mujoco
    child = int(m.jnt_bodyid[knee_joint]); parent = int(m.body_parentid[child])
    pts = []
    for g in range(m.ngeom):
        if m.geom_bodyid[g] == parent and m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH:
            nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_MESH, int(m.geom_dataid[g])) or ""
            if "wj-wk00" in nm.lower():
                pts.append(m.geom_pos[g].copy())
    if pts:
        return parent, np.mean(pts, 0), f"{len(pts)} case meshes"
    Rq = np.zeros(9); mujoco.mju_quat2Mat(Rq, m.body_quat[child])
    return parent, m.body_pos[child] + Rq.reshape(3, 3) @ m.jnt_pos[knee_joint], "knee axis point (no case mesh found)"


def apply_knees(m, act_ids, dof_ids, joint_ids, mdl, kp_factor=1.0, mass=True):
    """the two knee actuators of a compiled model become STS3250s: torque limit x 1.581, joint damping, kp x kp_factor
    (1 = the trained stiffness, i.e. register 21 set by firmware_P), and +19.5 g each at the servo case"""
    out = []
    for a, dof, j in zip(act_ids, dof_ids, joint_ids):
        m.actuator_forcerange[a] = m.actuator_forcerange[a] * R_TAU
        m.actuator_gainprm[a, 0] *= kp_factor; m.actuator_biasprm[a, 1] *= kp_factor
        m.dof_damping[dof] = mdl["damping"]; m.dof_armature[dof] = mdl["armature"]; m.dof_frictionloss[dof] = mdl["frictionloss"]
        if mass:
            b, p, how = knee_servo_site(m, j)
            r = add_point_mass(m, b, p, mdl["dmass_g"] / 1000.0); r["where"] = how; out.append(r)
    return out


def summary():
    TT = load_thermal()
    res = dict(ratios=dict(torque_per_volt=round(R_TAU, 4), no_load_speed_per_volt=round(R_W0, 4),
                           kt=dict((k, round(v, 4)) for k, v in KT_BAND.items()), R_w=dict((k, round(v, 4)) for k, v in RW_BAND.items())))
    for b in BANDS:
        m = band_model(b, TT)
        m["sheet_check"] = check_sheet(m)
        m["firmware_P_for_runtime_P30"] = round(firmware_P(m, 30), 2); m["firmware_P_for_trained_P32"] = round(firmware_P(m, 32), 2)
        ts, Ts = robo9_rise(m, m["heat_factor"], TT)
        m["robo9_model_C_at_0_2_4_6_8_min"] = [round(float(Ts[int(t / 0.5)]), 1) for t in R3["t_s"]]
        tsk1, Tsk1 = robo9_rise(m, 1.0, TT)
        m["robo9_model_C_at_k1"] = [round(float(Tsk1[int(t / 0.5)]), 1) for t in R3["t_s"]]
        res[b] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()}
    c = dict(B1); c["no_load_74"] = (B1["tau"] - B1["frictionloss"]) / B1["damping"]
    res["c001_twin"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in c.items()}
    return res


if __name__ == "__main__":
    r = summary()
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    json.dump(r, open(os.path.join(HERE, "out", "model.json"), "w"), indent=1)
    print(json.dumps(r, indent=1))
