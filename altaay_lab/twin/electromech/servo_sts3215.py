"""Feetech STS3215 (C001, 7.4 V, 1:345) servo model with its supply voltage, for the electromechanical twin (sim pass only).

What the trained robot has (Open_Duck_Playground b9be205, playground/open_duck_mini_v2/xmls, MuJoCo position actuators):
  torque = clip(kp * (target - q), -3.23, +3.23) Nm, then joint damping 0.56 Nm s/rad, frictionloss 0.068 Nm,
  armature 0.027 kg m2; kp 13.37 (open_duck_mini_v2.xml) or 17.11 (open_duck_mini_v2_backlash.xml); targets
  rate-limited to 5.24 rad/s in the 50 Hz policy loop (joystick.py max_motor_velocity, mujoco_infer.py). Nothing in
  the training env depends on a supply voltage: the limits are those of BAM's STS3215 at vin = 7.4 V.
How BAM models the servo (Rhoban/bam b9e1111, bam/feetech/actuator.py and bam/actuator.py; identification data by
A. Pirrone, params/feetech_sts3215_7_4V): firmware P controller duty = clip(kp_fw * error_gain * (q* - q), +-max_pwm),
applied volts = vin * duty, torque = kt/R * volts - kt^2/R * dq (- friction). Its MuJoCo mapping: kp = vin kp_fw
error_gain kt/R, forcerange = vin kt/R (x max_pwm), damping = kt^2/R + friction_viscous. So the stiffness and the torque
limit are both proportional to the volts the H-bridge gets, and the back-EMF term (in the damping) is not.
This model (mode "bam", the default): the servo's own supply volts V replace vin:
  kp(V) = kp_train * V / 7.4, forcerange(V) = 3.23 * V / 7.4, damping, friction and armature unchanged.
  At V = 7.4 V it is the trained actuator exactly (checked by twin.py check_stock). The no-load speed then falls with
  V by back-EMF: w0 = (3.23 V / 7.4 - 0.068) / 0.56, 5.65 rad/s at 7.4 V and 4.56 rad/s at 6.0 V (ratio 0.807; the
  C001 data sheet: 52 and 42 RPM, ratio 0.808).
Other modes (sensitivity): "comp" = firmware that compensates the bus volts (kp unchanged, only the limit scales);
"fixed" = no voltage effect (the trained actuator whatever V is; for the open-loop comparison).
Current (as sim/current_budget.py and sim/power_path_sim.py): kt = 1.148 (highest-current value of the three the lab
runs, fv = 0.059 from BAM m1.json), R = kt / (3.23 / 7.4) = 2.630 ohm; applied volts u = F R / kt; motor current
Im = (u - kt w) / R; supply current Is = max(u Im, 0) / V + I_q (no credit for braking, as the ngspice model).
Protections (Feetech STS3215 C001 product specification 2023-06-23, item 7-11): under 4 V or over 8 V input the servo
enters protection (torque off here while V < 4.0 V; timing not published, ASSUMPTION instant); over 2 A for 2 s
(over-current) and over 80 % of stall for 2 s (overload) are counted, not acted on (a new position command clears
both flags, and the walk sends one every 20 ms).
"""
import numpy as np

V_TRAIN = 7.4            # V: BAM STS3215Actuator vin, the supply volts behind the MJCF kp and forcerange
TAU_MAX_TRAIN = 3.23     # Nm at 7.4 V, MJCF forcerange. Not the data sheet. The sheet stall is TAU_SHEET.
KT = 1.148               # Nm/A, sim/current_budget.py KTS[0]. Not the data sheet Kt.
KT_OVER_R = TAU_MAX_TRAIN / V_TRAIN
R_M = KT / KT_OVER_R     # ohm, the BAM fit
I_Q = 0.05               # A per servo electronics, as sim/power_path_sim.py (ASSUMPTION there; data sheet idle is 21 mA)
V_UVP = 4.0              # V, C001 spec 7-11 input under-voltage protection
OC_A, OC_S = 2.0, 2.0    # C001 spec 7-11 over-current: more than 2 A for 2 s
OL_FRAC, OL_S = 0.8, 2.0  # C001 spec 7-11 overload: more than 80 % of stall for 2 s

# Feetech STS3215 product specification A/1, 2023-06-23, the file PARTS_AUDIT.md cites
# (https://files.seeedstudio.com/products/Feetech/108090023_STS3215-C001_Datasheet.pdf).
# kgf.cm to Nm is 0.0980665. Item 5-11 Kt 7.8 kg.cm/A times item 5-5 stall current 2.5 A
# equals item 5-4 stall torque 19.5 kg.cm, so those three lines agree.
KGFCM = 0.0980665
TAU_SHEET = 19.5 * KGFCM          # Nm at 7.4 V, item 5-4. At 6.0 V the sheet says 16.5 kg.cm.
TAU_SHEET_6V = 16.5 * KGFCM
KT_SHEET = 7.8 * KGFCM            # Nm/A, item 5-11
I_STALL_SHEET = 2.5               # A at 7.4 V, item 5-5. At 6.0 V the sheet says 2.0 A.
R_WIND_SHEET = 2.5                # ohm, item 5-10 terminal resistance
# The stall line is 7.4 V / 2.5 A = 2.96 ohm, 0.46 ohm above the 2.5 ohm terminal resistance.
# The current model uses the stall line so the stall current matches the sheet. Copper heat uses 2.5 ohm.
R_SHEET = V_TRAIN / I_STALL_SHEET
I_Q_SHEET = 0.021                 # A, item 5-6 idle current. No-load running current is 150 mA at 7.4 V (item 5-3),
                                  # which is not the same number: it includes the motor current while spinning.
SHEET_SCALE = TAU_SHEET / TAU_MAX_TRAIN
# No-load speed, item 5-2: 0.192 s/60 deg at 7.4 V (the sheet also prints 52 RPM), 0.238 s/60 deg at 6.0 V (42 RPM).
W0_SHEET = (np.pi / 3.0) / 0.192
W0_SHEET_6V = (np.pi / 3.0) / 0.238
# Operating range item 1-2 is -20 C to 60 C. Item 7-11 overheat turns torque off above 70 C.
# Both lines are on the sheet. The operating limit used for the gate is 60 C.
T_OPER_MIN, T_OPER_MAX = -20.0, 60.0
T_TORQUE_OFF = 70.0
# Not on the sheet, so they stay guesses when mode is "sheet":
#   joint damping and frictionloss: the MJCF values, scaled by SHEET_SCALE so the no-load speed stays
#     near the sheet (the scale keeps the speed; the MJCF numbers themselves are not on the sheet)
#   armature 0.027 kg m2: the MJCF, never measured here
#   position gain: the trained kp times SHEET_SCALE. The sheet says the control law is PID and customizable.
#     It does not give the gain. Scaling with kt/R is the BAM mapping, applied to the sheet stall.
#   whether the firmware holds stiffness as the bus falls: not published (TEST_PLAN 7.5)


class ServoBank:
    """the 14 actuators of a MuJoCo model; sets their gain and torque limit from each servo's volts"""

    def __init__(self, model, mode="bam", i_q=I_Q, v_uvp=V_UVP):
        self.m = model
        self.mode = mode
        self.i_q = i_q
        self.v_uvp = v_uvp
        self.kp0 = model.actuator_gainprm[:, 0].copy()
        self.b1 = model.actuator_biasprm[:, 1].copy()
        self.fr0 = model.actuator_forcerange.copy()
        assert np.allclose(self.b1, -self.kp0), "position actuators expected (biasprm[1] = -kp)"
        assert np.allclose(model.actuator_biasprm[:, 2], 0.0), "kv = 0 expected"
        self.ctrlrange = model.actuator_ctrlrange.copy()
        self.ctrllimited = model.actuator_ctrllimited.astype(bool).copy()
        self.trn = model.actuator_trnid[:, 0].copy()
        self.qadr = model.jnt_qposadr[self.trn]
        self.dadr = model.jnt_dofadr[self.trn]
        assert np.allclose(model.actuator_gear[:, 0], 1.0)
        self.n = model.nu
        self.duty = np.zeros(self.n)
        self.off = np.zeros(self.n, bool)
        # sheet: scale the joint damping and the friction with the stall, so the no-load speed stays
        # near the data sheet while the torque limit falls to the sheet. The MJCF numbers are not on the sheet.
        self.torque_scale = SHEET_SCALE if mode == "sheet" else 1.0
        if mode == "sheet":
            self.m.dof_damping[self.dadr] *= SHEET_SCALE
            self.m.dof_frictionloss[self.dadr] *= SHEET_SCALE

    def restore(self):
        self.m.actuator_gainprm[:, 0] = self.kp0
        self.m.actuator_biasprm[:, 1] = self.b1
        self.m.actuator_forcerange[:] = self.fr0

    def scales(self, V):
        """(gain scale, limit scale) per servo for supply volts V"""
        s = self.torque_scale * np.clip(V, 0.0, None) / V_TRAIN
        off = V < self.v_uvp
        if self.mode == "fixed":
            g = np.ones(self.n); lim = np.ones(self.n)
        elif self.mode == "comp":
            g = np.ones(self.n); lim = s
        else:
            g = s; lim = s
        g = np.where(off, 0.0, g); lim = np.where(off, 0.0, lim)
        return g, lim, off

    def force(self, data, V):
        """the actuator force MuJoCo will compute in the next mj_step for supply volts V (same formula, same state)"""
        g, lim, off = self.scales(V)
        ctrl = np.where(self.ctrllimited, np.clip(data.ctrl, self.ctrlrange[:, 0], self.ctrlrange[:, 1]), data.ctrl)
        q = data.qpos[self.qadr]
        F = self.kp0 * g * (ctrl - q)
        return np.clip(F, self.fr0[:, 0] * lim, self.fr0[:, 1] * lim), off

    def duty_of(self, data):
        """F / F_limit at 7.4 V for the current state, the V-independent part of the BAM duty (mode bam)"""
        ctrl = np.where(self.ctrllimited, np.clip(data.ctrl, self.ctrlrange[:, 0], self.ctrlrange[:, 1]), data.ctrl)
        q = data.qpos[self.qadr]
        lo = self.fr0[:, 0] * self.torque_scale
        hi = self.fr0[:, 1] * self.torque_scale
        return np.clip(self.kp0 * self.torque_scale * (ctrl - q), lo, hi) / hi

    def apply(self, V):
        """write the gain and limit for supply volts V into the model (used by the next mj_step)"""
        g, lim, off = self.scales(V)
        self.m.actuator_gainprm[:, 0] = self.kp0 * g
        self.m.actuator_biasprm[:, 1] = self.b1 * g
        lo = self.fr0[:, 0] * lim; hi = self.fr0[:, 1] * lim
        hi = np.where(off, 1e-12, hi); lo = np.where(off, -1e-12, lo)
        self.m.actuator_forcerange[:, 0] = lo
        self.m.actuator_forcerange[:, 1] = hi
        self.off = off

    @staticmethod
    def electrical(F, w, V, i_q=None, mode="bam"):
        """applied volts, motor current and supply current for actuator force F, joint speed w and supply volts V"""
        kt, rm, iq0 = _motor(mode)
        if i_q is None:
            i_q = iq0
        u = F * rm / kt
        im = (u - kt * w) / rm
        isup = np.maximum(u * im, 0.0) / np.maximum(V, 0.5) + i_q
        return u, im, isup


def _motor(mode):
    """(kt Nm/A, R ohm, idle A) for the supply-current law"""
    if mode == "sheet":
        return KT_SHEET, R_SHEET, I_Q_SHEET
    return KT, R_M, I_Q


def supply_current_bam(duty, w, V, mode="bam", d_comp=None, i_q=None, v_uvp=V_UVP, slope=False):
    """supply current as a function of the servo's volts V for the next step (vector over the 14 servos).
    mode bam: F = duty * 3.23 * V / 7.4 -> u = duty * V, Is = max(duty (duty V - kt w), 0) / R + I_q (affine in V).
    mode comp: F = clip(kp0 e, +-3.23 V / 7.4) -> u = clip(d_comp * 7.4, +-V) where d_comp = kp0 e / (3.23) (unclipped).
    mode fixed: F = duty * 3.23 -> u = duty * 7.4 (not capped by V; the trained actuator)."""
    kt, rm, iq0 = _motor(mode)
    if i_q is None:
        i_q = iq0
    Vc = np.maximum(V, 0.5)
    if mode in ("bam", "sheet"):
        u = duty * Vc
    elif mode == "comp":
        u = np.minimum(np.maximum(d_comp * V_TRAIN, -Vc), Vc)
    else:
        u = duty * V_TRAIN
    im = (u - kt * w) / rm
    p = u * im
    on = (p > 0.0) & (V >= v_uvp)
    isup = np.where(on, p / Vc, 0.0) + i_q
    if not slope:
        return isup
    if mode in ("bam", "sheet"):                 # Is = d (d V - kt w) / R + I_q: slope d^2 / R where it draws
        ds = np.where(on, duty * duty / rm, 0.0)
    else:                                        # numeric for the other modes
        ds = (supply_current_bam(duty, w, V + 1e-4, mode, d_comp, i_q, v_uvp) - isup) / 1e-4
    return isup, ds


def datasheet_check():
    """model stall torque, stall current and no-load speed at 6.0 and 7.4 V against the C001 data sheet"""
    fc, b = 0.068, 0.56                       # MJCF frictionloss and damping
    out = {}
    for V, ds in ((6.0, dict(rpm=42, s60=0.238, stall_kgcm=16.5, stall_A=2.0)), (7.4, dict(rpm=52, s60=0.192, stall_kgcm=19.5, stall_A=2.5))):
        w0 = (KT_OVER_R * V - fc) / b
        out["%.1f V" % V] = dict(model_no_load_rad_s=round(w0, 3), datasheet_no_load_rad_s=round(np.pi / 3 / ds["s60"], 3),
                                 model_stall_Nm=round(KT_OVER_R * V, 3), datasheet_stall_Nm=round(ds["stall_kgcm"] * 0.0980665, 3),
                                 model_stall_A=round(V / R_M, 3), datasheet_stall_A=ds["stall_A"])
    a, b_ = out["6.0 V"], out["7.4 V"]
    out["ratio 6.0 / 7.4"] = dict(model_speed=round(a["model_no_load_rad_s"] / b_["model_no_load_rad_s"], 3),
                                  datasheet_speed=round(a["datasheet_no_load_rad_s"] / b_["datasheet_no_load_rad_s"], 3),
                                  model_stall=round(a["model_stall_Nm"] / b_["model_stall_Nm"], 3),
                                  datasheet_stall=round(a["datasheet_stall_Nm"] / b_["datasheet_stall_Nm"], 3),
                                  model_stall_A=round(a["model_stall_A"] / b_["model_stall_A"], 3),
                                  datasheet_stall_A=round(a["datasheet_stall_A"] / b_["datasheet_stall_A"], 3))
    # sheet mode: torque, damping and friction all scale by SHEET_SCALE, so the no-load speed is the BAM
    # speed (the scale cancels) and the stall torque is the sheet. Speed tolerance on the sheet is +/-10 percent.
    fc, b = 0.068, 0.56
    out["sheet"] = {}
    for V, w_ds, tau_ds, i_ds in ((6.0, W0_SHEET_6V, TAU_SHEET_6V, 2.0), (7.4, W0_SHEET, TAU_SHEET, I_STALL_SHEET)):
        w0 = (TAU_MAX_TRAIN * V / V_TRAIN - fc) / b
        out["sheet"]["%.1f V" % V] = dict(model_no_load_rad_s=round(w0, 3), datasheet_no_load_rad_s=round(w_ds, 3),
                                          model_stall_Nm=round(TAU_SHEET * V / V_TRAIN, 3), datasheet_stall_Nm=round(tau_ds, 3),
                                          model_stall_A=round(V / R_SHEET, 3), datasheet_stall_A=i_ds)
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(datasheet_check(), indent=1))
