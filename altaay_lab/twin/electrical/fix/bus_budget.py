"""Target guard for the duck's 50 Hz walk loop (robot side: runs on the Pi, numpy only). Fix for HARDWARE_AUDIT B47.

TargetGuard = two steps on the 14 targets, in this order:
1. The training's own target speed clip: each target moves at most 5.24 rad/s x 0.02 s = 0.105 rad from the last sent
   target (Open_Duck_Playground joystick.py line 59 and lines 411 to 416). The stock runtime has it commented out
   (Open_Duck_Mini_Runtime 376de65 scripts/v2_rl_walk_mujoco.py lines 292 to 298), so the robot runs a policy without the
   clip it was trained with.
2. BusBudget: it predicts each servo's supply current from the target, the present angle
and the present speed with the twin's servo model, and if the sum is over the budget it lowers one common torque cap c
(Nm) until the predicted sum fits: target' = q + clip(target - q, -c / kp, +c / kp). Servos asking for less than c are
untouched, so the small balance corrections stay; only the joints that would sit at their torque limit together are
trimmed. When the sum is under the budget (all of walking, all of the get-up programs in the twin) nothing changes.
Twin result (sim pass only): ../ELECTRICAL_TWIN.md, "Track 1b fixes".

Servo model (the duck repo's twin/electromech/servo_sts3215.py, mode "bam"): torque = clip(kp (target - q), +-tau),
kp = 13.37 Nm/rad x (P / 32) x (V / 7.4), tau = 3.23 Nm x (V / 7.4) x (register 48 / 1000); applied volts u = F R / kt;
supply current = max(u (u - kt w), 0) / (R V) + 0.05 A, kt = 1.148 Nm/A, R = 2.630 ohm. P 32 is the firmware gain behind
the trained kp (Rhoban/bam b9e1111 bam/feetech/actuator.py lines 36 to 40 and 148 to 152: duty = P x 0.166 x error, so kp
scales with P). The stock runtime writes P 30 to the legs and P 8 to the four head servos (Open_Duck_Mini_Runtime 376de65
scripts/v2_rl_walk_mujoco.py lines 175 to 179), which is RUNTIME_P below.

Where it goes (track 3 runs it in the real code; the upstream files stay unmodified, D6): in the duck repo's
bench/odm_bench/walkhooks.py HookedRLWalk, inside the existing hwi.set_position_all wrapper, before write(...):
    t = np.array([joints_positions[n] for n in names]); t2, info = self.guard(t, q, w)
    joints_positions = dict(zip(names, t2)); self.motor_targets[:] = t2     # the next obs sees the sent targets
with names = list(self.hwi.joints.keys()) and q, w the present angles (rad) and speeds (rad/s) that get_obs() read this
cycle (v2_rl_walk_mujoco.py lines 127 to 140: hwi.get_present_positions / get_present_velocities; wrap them to keep the
last values). Build once: self.guard = TargetGuard(init_targets=self.init_pos). Cost: about 0.3 ms per step in numpy on
this box (test_speed below); check it on the Pi with bench/timing_budget.py.
Servo registers: none change. P 30 / 8 stay as the runtime writes them (register 21, Position loop P coefficient),
48 Torque Limit stays at its power-on value from 16 (1000), and 28 Protection Current / 38 Overcurrent protection time keep
their factory values (FTServo wiki STS memory table; factory read 310 and 200 on firmware 3.10 units). Lowering 48 was
tried in the twin and costs walking (see ELECTRICAL_TWIN.md); 28 and 38 act per servo after 10 ms or more and unload the
joint, so they cannot hold a summed current.
"""
import numpy as np

V_TRAIN, TAU_TRAIN, KP_TRAIN, P_TRAIN = 7.4, 3.23, 13.37, 32
KT, I_Q = 1.148, 0.05                         # servo_sts3215.py KT, I_Q
R_M = KT / (TAU_TRAIN / V_TRAIN)              # servo_sts3215.py R_M, 2.630 ohm
MAX_MOTOR_VEL, CTRL_DT = 5.24, 0.02          # joystick.py line 59 (max_motor_velocity), 50 Hz control
RUNTIME_P = np.array([30, 30, 30, 30, 30, 8, 8, 8, 8, 30, 30, 30, 30, 30], float)   # hwi.joints order: 5 left leg, 4 head, 5 right leg
BUDGET_A = 10.0                               # predicted servo bus sum at 7.2 V; chosen in the twin (ELECTRICAL_TWIN.md, Track 1b fixes)


def gains(volts=7.2, p_fw=RUNTIME_P, torque_limit=1000):
    """(kp Nm/rad, torque limit Nm) per servo at bus volts V, firmware P and register 48 (0 to 1000)"""
    s = float(volts) / V_TRAIN
    return KP_TRAIN * np.asarray(p_fw, float) / P_TRAIN * s, TAU_TRAIN * s * np.asarray(torque_limit, float) / 1000.0


def currents_from_torque(F, w, volts=7.2):
    """supply current per servo (A) for torque F (Nm) and joint speed w (rad/s); no credit for braking"""
    u = np.clip(np.asarray(F, float) * R_M / KT, -volts, volts)
    return np.maximum(u * (u - KT * np.asarray(w, float)), 0.0) / (R_M * max(volts, 0.5)) + I_Q


def servo_currents(targets, q, w, volts=7.2, p_fw=RUNTIME_P, torque_limit=1000, cap=None):
    kp, tau = gains(volts, p_fw, torque_limit)
    lim = tau if cap is None else np.minimum(tau, cap)
    return currents_from_torque(np.clip(kp * (np.asarray(targets, float) - q), -lim, lim), w, volts)


class BusBudget:
    def __init__(self, budget_a=BUDGET_A, volts=7.2, p_fw=RUNTIME_P, torque_limit=1000, iters=14):
        self.budget, self.volts, self.p_fw, self.tl, self.iters = float(budget_a), float(volts), p_fw, torque_limit, iters
        self.kp, self.tau = gains(volts, p_fw, torque_limit)
        self.n_steps = 0; self.n_cut = 0

    def predict(self, targets, q, w, cap=None):
        return float(servo_currents(targets, q, w, self.volts, self.p_fw, self.tl, cap).sum())

    def limit(self, targets, q, w):
        """(new targets, info). info: predicted A before and after, the cap in Nm (None if untouched)"""
        t = np.asarray(targets, float); q = np.asarray(q, float); w = np.asarray(w, float)
        self.n_steps += 1
        i0 = self.predict(t, q, w)
        if i0 <= self.budget:
            return t, dict(i_pred_A=i0, i_after_A=i0, cap_Nm=None)
        lo, hi = 0.0, float(self.tau.max())            # predicted sum is non-decreasing in the cap
        for _ in range(self.iters):
            c = 0.5 * (lo + hi)
            if self.predict(t, q, w, c) <= self.budget:
                lo = c
            else:
                hi = c
        e = np.clip(t - q, -lo / self.kp, lo / self.kp)
        self.n_cut += 1
        return q + e, dict(i_pred_A=i0, i_after_A=self.predict(q + e, q, w), cap_Nm=lo)


class TargetGuard:
    """the training's target speed clip, then the bus budget; call once per 50 Hz cycle with the policy's targets"""

    def __init__(self, budget_a=BUDGET_A, volts=7.2, p_fw=RUNTIME_P, torque_limit=1000, init_targets=None, clip=True):
        self.budget = BusBudget(budget_a, volts, p_fw, torque_limit)
        self.clip = clip
        self.prev = None if init_targets is None else np.asarray(init_targets, float).copy()

    def __call__(self, targets, q, w):
        t = np.asarray(targets, float)
        if self.clip:
            prev = np.asarray(q, float) if self.prev is None else self.prev
            d = MAX_MOTOR_VEL * CTRL_DT
            t = np.clip(t, prev - d, prev + d)
        t, info = self.budget.limit(t, q, w)
        self.prev = t.copy()
        return t, info


class FallHold:
    """Optional third step (the 15 A aim in the twin): once the torso tilts past 45 deg, send the joint angles of that
    moment and stop following the policy, as the get-up library's fall stop (shared lab gym, overlay gym/overlays/duck,
    getup/falls.py FallStop; the gym fall rule is 45 deg). tilt_deg from the BNO055 fused orientation (NDOF mode, the
    runtime's raw_imu.py line 27): acos of the body z axis against vertical. reset() when the operator unpauses."""

    def __init__(self, tilt_deg=45.0):
        self.tilt = float(tilt_deg); self.hold = None

    def __call__(self, targets, q, tilt_deg):
        if self.hold is None and tilt_deg > self.tilt:
            self.hold = np.asarray(q, float).copy()
        return np.asarray(targets, float) if self.hold is None else self.hold.copy()

    def reset(self):
        self.hold = None
