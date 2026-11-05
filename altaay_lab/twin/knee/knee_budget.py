"""The track 1b target guard (twin/electrical/fix/bus_budget.py) with STS3250 knees (D32). Sim pass only, calc only.

bus_budget.py is loaded by path and not edited. load() returns a fresh copy of it whose gains() and currents_from_torque()
know the two knees: torque limit x 1.581 and the STS3250 current law of servo_sts3250.py (the other 12 stay C001). The
guard itself (TargetGuard: the training's 5.24 rad/s clip, then the 10.0 A bus budget) is unchanged.
Why it matters: with the C001 law the guard would over-predict each knee's current by 1 / 0.25 to 1 / 0.41 per Nm^2 and
cut the knees' torque in pushes for nothing; with the C001 limit it would cap them at 3.14 Nm.
Units: RUNTIME_P stays in C001-equivalent counts (30 legs, 8 head). The knees' own register 21 value is
servo_sts3250.firmware_P(model, 30): 11 (published Kt and R) to 19 (stall line), BLOCKER until the bench BAM fit.
"""
import importlib.util, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HWI = ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle", "neck_pitch", "head_pitch", "head_yaw",
       "head_roll", "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]   # bus_budget RUNTIME_P order


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod); return mod


def load(band="high", names=HWI, damping=None):
    BB = _load("bus_budget_knee_" + band, os.path.join(os.path.dirname(HERE), "electrical", "fix", "bus_budget.py"))
    S = _load("servo_sts3250_kb", os.path.join(HERE, "servo_sts3250.py"))
    m = S.model(band, damping)
    kn = np.array(["knee" in n for n in names])
    kt = np.where(kn, m["kt"], BB.KT); ke = np.where(kn, m["ke"], BB.KT); R = np.where(kn, m["R"], BB.R_M)
    pm = np.where(kn, m["pmax"], 1.0); tf = np.where(kn, S.R_TAU, 1.0)

    def gains(volts=7.2, p_fw=BB.RUNTIME_P, torque_limit=1000):
        s = float(volts) / BB.V_TRAIN
        return BB.KP_TRAIN * np.asarray(p_fw, float) / BB.P_TRAIN * s, BB.TAU_TRAIN * tf * s * np.asarray(torque_limit, float) / 1000.0

    def currents_from_torque(F, w, volts=7.2):
        u = np.clip(np.asarray(F, float) * R / kt, -pm * volts, pm * volts)
        return np.maximum(u * (u - ke * np.asarray(w, float)), 0.0) / (R * max(volts, 0.5)) + BB.I_Q

    BB.gains, BB.currents_from_torque = gains, currents_from_torque
    BB.KNEE = dict(band=band, mask=kn, register21_for_P30=round(S.firmware_P(m, 30), 2), torque_limit_7V2_Nm=round(m["tau74"] * 7.2 / 7.4, 3))
    return BB


if __name__ == "__main__":
    for b in ("low", "high"):
        BB = load(b); g = BB.TargetGuard(init_targets=np.zeros(14))
        F = np.zeros(14); F[[3, 12]] = 3.0
        print(b, BB.KNEE["register21_for_P30"], BB.KNEE["torque_limit_7V2_Nm"], "knee 3 Nm held: A per knee", BB.currents_from_torque(F, np.zeros(14))[[3, 12]].round(3),
              "C001 law", _load("bb0", os.path.join(os.path.dirname(HERE), "electrical", "fix", "bus_budget.py")).currents_from_torque(F, np.zeros(14))[[3, 12]].round(3))
