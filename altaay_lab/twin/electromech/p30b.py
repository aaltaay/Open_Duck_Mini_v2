"""Molicel INR-18650-P30B cell model for the electromechanical twin (sim pass only).

Data: data/p30b_datasheet.json, the data sheet 'Discharge Rate Characteristics' at 23 C (0.6, 1.5, 3, 10 and 20 A,
constant current, terminal volts against mAh delivered), digitized by p30b_digitize.py and checked against the
independent digitization in sim/runtime_thermal.py (largest difference 13 mV).

Model (one cell; the pack is 2 in series, so both cells carry the pack current):
  q        charge delivered since a full charge (mAh); state of charge SOC = 1 - q / 2846 mAh (1C capacity to 2.5 V)
  V(q, I)  terminal volts at a steady current I: the data sheet surface, linear between the measured currents,
           extended below 0.6 A with the 0.6 to 1.5 A slope (to I = 0) and above 20 A with the 10 to 20 A slope
  OCV(q)   = V(q, 0), the zero-current end of that line (an extrapolation, 9 to 20 mV above the 0.6 A curve)
  R(q, I)  = -dV/dI, the slope of the surface: 10 to 30 mOhm, highest at low current
Two dynamic readings of the same surface bracket the cell's fast response, which the data sheet does not give:
  'steady' (default, conservative): V = V(q, I(t)) at every step: every current pulse sees the full steady-state slope.
  'ac'     (optimistic): V = V(q, I_slow) - R_ac (I - I_slow), R_ac = 8 mOhm (data sheet AC impedance, 30 % SOC) and
           I_slow = I filtered with tau_s (ASSUMPTION 10 s, not published): pulses see only the AC impedance.
Not modelled: temperature (the curves are at 23 C), ageing (the data sheet cycle curve: about 93 % capacity after
300 cycles at 1C), cell-to-cell imbalance, the BMS 2.40 V cut.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "p30b_datasheet.json")
Q_CAP_1C = 2846.0   # mAh to 2.5 V at 3 A (1C), the data sheet curve as read in sim/runtime_thermal.py; SOC = 1 - q / Q_CAP_1C


class P30B:
    def __init__(self, path=DATA, mode="steady", r_ac=None, tau_s=10.0):
        d = json.load(open(path))
        self.src = d["source"]
        self.r_ac = (d["datasheet_impedance"]["AC_30pct_SOC_mOhm"] / 1000.0) if r_ac is None else r_ac
        cur = sorted((c["current_A"], name) for name, c in d["curves"].items())
        self.I = np.array([c for c, _ in cur])
        q = np.array(d["mAh"], float)
        V = np.array([[np.nan if x is None else x for x in d["curves"][name]["volts"]] for _, name in cur])   # (nI, nq)
        self.q_end = float(min(d["curves"][name]["end_mAh"] for _, name in cur))   # all curves defined up to here
        self.q_cap = Q_CAP_1C
        ok = q <= self.q_end
        self.q = q[ok]
        self.V = V[:, ok]
        # interior holes (none expected) are filled along q
        for k in range(len(self.I)):
            bad = np.isnan(self.V[k])
            if bad.any():
                self.V[k, bad] = np.interp(self.q[bad], self.q[~bad], self.V[k, ~bad])
        self.mode = mode
        self.tau_s = tau_s
        self.i_slow = None
        self._cq = None                          # cached column (charge, volts at the measured currents)

    # ---------------------------------------------------------------- the steady surface
    def _col(self, qm):
        """volts at the measured currents for charge delivered qm (mAh), linear in q (cached: q moves slowly)"""
        qm = min(max(qm, self.q[0]), self.q[-1])
        if self._cq is not None and abs(self._cq[0] - qm) < 0.01:
            return self._cq[1]
        j = int(np.clip(np.searchsorted(self.q, qm) - 1, 0, len(self.q) - 2))
        f = (qm - self.q[j]) / (self.q[j + 1] - self.q[j])
        col = self.V[:, j] * (1 - f) + self.V[:, j + 1] * f
        self._cq = (qm, col)
        return col

    def v_steady(self, qm, i):
        v = self._col(qm); I = self.I
        if i <= I[0]:
            return float(v[0] + (v[0] - v[1]) / (I[1] - I[0]) * (I[0] - i))
        if i >= I[-1]:
            return float(v[-1] - (v[-2] - v[-1]) / (I[-1] - I[-2]) * (i - I[-1]))
        return float(np.interp(i, I, v))

    def slope(self, qm, i):
        """-dV/dI at (qm, i), ohm"""
        v = self._col(qm); I = self.I
        k = int(np.clip(np.searchsorted(I, i) - 1, 0, len(I) - 2))
        return float((v[k] - v[k + 1]) / (I[k + 1] - I[k]))

    def ocv(self, qm):
        return self.v_steady(qm, 0.0)

    def q_at_ocv(self, v_ocv):
        """charge delivered (mAh) at which OCV = v_ocv"""
        qs = np.linspace(self.q[0], self.q[-1], 2000)
        o = np.array([self.ocv(x) for x in qs])
        if v_ocv >= o[0]:
            return float(qs[0])
        if v_ocv <= o[-1]:
            return float(qs[-1])
        return float(np.interp(-v_ocv, -o, qs))

    def soc(self, qm):
        return 1.0 - qm / self.q_cap

    # ---------------------------------------------------------------- dynamic reading
    def reset(self, i0=None):
        self.i_slow = i0

    def v_cell(self, qm, i, dt=None):
        """terminal volts of one cell at charge delivered qm (mAh) and current i (A, discharge positive)"""
        if self.mode == "steady":
            return self.v_steady(qm, i)
        if self.i_slow is None:
            self.i_slow = i
        return self.v_steady(qm, self.i_slow) - self.r_ac * (i - self.i_slow)

    def advance(self, i, dt):
        """after a step of length dt at current i: update the slow current ('ac' mode)"""
        if self.mode == "ac":
            if self.i_slow is None:
                self.i_slow = i
            self.i_slow += (i - self.i_slow) * min(1.0, dt / self.tau_s)


def summary(cell=None):
    """the numbers the twin docs quote: OCV and the slope at the pack states"""
    c = cell or P30B()
    out = dict(q_end_mAh=round(c.q_end, 1), q_cap_1C_mAh=c.q_cap, ocv_full=round(c.ocv(0.0), 3))
    for v in (3.70, 3.57, 3.50, 3.30):
        qm = c.q_at_ocv(v)
        out["ocv_%.2f" % v] = dict(q_mAh=round(qm, 1), soc=round(c.soc(qm), 3), v_at_3A=round(c.v_steady(qm, 3.0), 3),
                                   v_at_5p5A=round(c.v_steady(qm, 5.5), 3), slope_3_10A_mOhm=round(1000 * c.slope(qm, 5.0), 1),
                                   slope_10_20A_mOhm=round(1000 * c.slope(qm, 12.0), 1))
    return out


if __name__ == "__main__":
    print(json.dumps(summary(), indent=1))
