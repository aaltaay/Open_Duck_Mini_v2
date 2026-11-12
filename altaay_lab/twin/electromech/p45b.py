"""Molicel INR-21700-P45B cell model for the 2S pack (D44). A reading of the data sheet, not a cell measurement.

Data: data/p45b_datasheet.json, digitized from the version 1.2 figure 'Discharge Rate Characteristics'
at 23 C (0.2C, 1.0C, 10 A, 20 A, 30 A, 45 A) by p45b_digitize.py. One pixel on that figure is about 7 mV,
and the stroke is about 2 pixels, so a point is good to about 15 mV.

Nameplate, version 1.2, not from the figure:
  typical capacity 4500 mAh, minimum 4300 mAh, nominal 3.6 V
  charge 4.2 V, discharge cut-off 2.5 V
  standard charge 4.5 A, maximum charge 13.5 A with a 70 C cut-off
  continuous discharge 45 A with an 80 C cut-off
  charge temperature 0 C to 60 C, discharge temperature -40 C to 60 C
  AC impedance 7 mOhm at 30 percent SOC, DC impedance 15 mOhm at 50 percent SOC
  21.55 mm by 70.15 mm maximum, 70 g maximum

The 0.2C and 1.0C currents are 0.9 A and 4.5 A, from the typical 4500 mAh. The figure does not start
exactly on the 0 mAh axis line, so the model extends the first tracked segment back to 0 mAh and does
not let that extension go above the 4.2 V charge voltage. That extension is marked in summary().

Model (one cell; the pack is 2 in series, so both cells carry the pack current):
  q        charge delivered since a full charge (mAh)
  V(q, I)  terminal volts at a steady current I, linear between the measured currents,
           extended below 0.9 A with the 0.9 to 4.5 A slope and above 45 A with the 30 to 45 A slope
  OCV(q)   V(q, 0), the zero-current end of that line (an extrapolation)
  R(q, I)  -dV/dI, the slope of the surface. The data sheet's 15 mOhm is a DC pulse at 50 percent
           SOC, not this constant-current slope. summary() prints both.
State of charge uses the 1C curve read down to 2.5 V, not the 4500 mAh nameplate.
Not modelled: temperature (the curves are at 23 C), ageing, cell-to-cell imbalance, the BMS 2.40 V cut.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "p45b_datasheet.json")
V_CHARGE = 4.2
V_CUT = 2.5


def _load(path):
    d = json.load(open(path))
    q = np.array(d["mAh"], float)
    names = list(d["curves"])
    I = np.array([d["curves"][n]["current_A"] for n in names], float)
    order = np.argsort(I)
    I = I[order]
    names = [names[i] for i in order]
    V = np.array([[np.nan if x is None else x for x in d["curves"][n]["volts"]] for n in names], float)
    # extend each curve back to 0 mAh from its first two tracked points, and not above the charge voltage
    for k in range(len(I)):
        known = np.where(~np.isnan(V[k]))[0]
        if len(known) < 2:
            raise RuntimeError("curve %s is too short" % names[k])
        i0, i1 = int(known[0]), int(known[1])
        slope = (V[k, i1] - V[k, i0]) / (q[i1] - q[i0])
        for j in range(i0):
            V[k, j] = min(V_CHARGE, V[k, i0] + slope * (q[j] - q[i0]))
        # one-sample holes inside the tracked span
        for j in range(i0, int(known[-1]) + 1):
            if np.isnan(V[k, j]):
                L = j - 1
                while np.isnan(V[k, L]):
                    L -= 1
                R = j + 1
                while np.isnan(V[k, R]):
                    R += 1
                f = (q[j] - q[L]) / (q[R] - q[L])
                V[k, j] = V[k, L] * (1 - f) + V[k, R] * f
    ends = []
    for k, n in enumerate(names):
        known = np.where(~np.isnan(V[k]))[0]
        ends.append(float(q[known[-1]]))
    q_end = min(ends)
    # 1C capacity is read on that curve alone, down to 2.5 V or to its own last point
    k1 = int(np.where(np.isclose(I, 4.5))[0][0])
    known = np.where(~np.isnan(V[k1]))[0]
    qq, vv = q[known], V[k1, known]
    below = np.where(vv <= V_CUT)[0]
    if len(below):
        j = int(below[0])
        if j == 0:
            q_cap = float(qq[0])
        else:
            f = (V_CUT - vv[j - 1]) / (vv[j] - vv[j - 1])
            q_cap = float(qq[j - 1] + f * (qq[j] - qq[j - 1]))
    else:
        q_cap = float(qq[-1])
    ok = q <= q_end + 1e-6
    return d, I, q[ok], V[:, ok], q_end, q_cap


class P45B:
    def __init__(self, path=DATA, mode="steady", r_ac=None, tau_s=10.0):
        d, I, q, V, q_end, q_cap = _load(path)
        self.src = d["source"]
        self.nameplate = d
        self.r_ac = (d["datasheet_impedance"]["AC_30pct_SOC_mOhm"] / 1000.0) if r_ac is None else r_ac
        self.I = I
        self.q = q
        self.V = V
        self.q_end = q_end
        self.q_cap = q_cap
        self.mode = mode
        self.tau_s = tau_s
        self.i_slow = None
        self._cq = None

    def _col(self, qm):
        qm = min(max(qm, float(self.q[0])), float(self.q[-1]))
        if self._cq is not None and abs(self._cq[0] - qm) < 0.01:
            return self._cq[1]
        j = int(np.clip(np.searchsorted(self.q, qm) - 1, 0, len(self.q) - 2))
        f = (qm - self.q[j]) / (self.q[j + 1] - self.q[j])
        col = self.V[:, j] * (1 - f) + self.V[:, j + 1] * f
        self._cq = (qm, col)
        return col

    def v_steady(self, qm, i):
        v = self._col(qm)
        I = self.I
        if i <= I[0]:
            return float(v[0] + (v[0] - v[1]) / (I[1] - I[0]) * (I[0] - i))
        if i >= I[-1]:
            return float(v[-1] - (v[-2] - v[-1]) / (I[-1] - I[-2]) * (i - I[-1]))
        return float(np.interp(i, I, v))

    def slope(self, qm, i):
        """-dV/dI at (qm, i), ohm, from the constant-current figure"""
        v = self._col(qm)
        I = self.I
        k = int(np.clip(np.searchsorted(I, i) - 1, 0, len(I) - 2))
        return float((v[k] - v[k + 1]) / (I[k + 1] - I[k]))

    def ocv(self, qm):
        return self.v_steady(qm, 0.0)

    def q_at_ocv(self, v_ocv):
        qs = np.linspace(self.q[0], self.q[-1], 4000)
        o = np.array([self.ocv(x) for x in qs])
        if v_ocv >= o[0]:
            return float(qs[0])
        if v_ocv <= o[-1]:
            return float(qs[-1])
        return float(np.interp(-v_ocv, -o, qs))

    def soc(self, qm):
        return 1.0 - qm / self.q_cap

    def reset(self, i0=None):
        self.i_slow = i0

    def v_cell(self, qm, i, dt=None):
        if self.mode == "steady":
            return self.v_steady(qm, i)
        if self.i_slow is None:
            self.i_slow = i
        return self.v_steady(qm, self.i_slow) - self.r_ac * (i - self.i_slow)

    def advance(self, i, dt):
        if self.mode == "ac":
            if self.i_slow is None:
                self.i_slow = i
            self.i_slow += (i - self.i_slow) * min(1.0, dt / self.tau_s)


def hours_at_current(i_pack, cell=None, v_stop_ocv=3.30):
    """calc only: hold one pack current and walk down the figure until cell OCV is v_stop_ocv,
    and until the loaded cell is 2.5 V. The pack is 2S, so the cell current is the pack current."""
    c = cell or P45B()
    # 1 second steps is enough for a constant current
    q = 0.0
    t_ocv = None
    t_cut = None
    v_full = c.v_steady(0.0, i_pack)
    t = 0.0
    dt = 1.0
    while q < c.q_end - 1.0 and t < 8 * 3600:
        v = c.v_steady(q, i_pack)
        if t_ocv is None and c.ocv(q) <= v_stop_ocv:
            t_ocv = t
        if t_cut is None and v <= V_CUT:
            t_cut = t
            break
        q += i_pack * dt / 3.6
        t += dt
    return dict(i_pack_A=i_pack, v_cell_full_V=round(v_full, 3), v_pack_full_V=round(2 * v_full, 3),
                minutes_to_ocv=None if t_ocv is None else round(t_ocv / 60.0, 1),
                ocv_stop_V=v_stop_ocv, minutes_to_2p5V=None if t_cut is None else round(t_cut / 60.0, 1),
                q_end_mAh=round(q if t_cut else c.q_end, 1))


def summary(cell=None):
    c = cell or P45B()
    out = dict(q_end_mAh=round(c.q_end, 1), q_cap_1C_to_2p5V_mAh=round(c.q_cap, 1),
               nameplate_typical_mAh=c.nameplate["datasheet_capacity_mAh"]["typical"],
               ocv_full=round(c.ocv(0.0), 3), note="0 mAh row is the first tracked segment extended back to the axis, capped at 4.2 V")
    for v in (3.70, 3.57, 3.50, 3.30):
        qm = c.q_at_ocv(v)
        out["ocv_%.2f" % v] = dict(q_mAh=round(qm, 1), soc=round(c.soc(qm), 3),
                                   v_at_4p5A=round(c.v_steady(qm, 4.5), 3), v_at_5p5A=round(c.v_steady(qm, 5.5), 3),
                                   slope_4p5_10A_mOhm=round(1000 * c.slope(qm, 6.0), 1))
    qm = c.q_at_ocv(3.70)
    out["datasheet_DC_50pct_mOhm"] = c.nameplate["datasheet_impedance"]["DC_50pct_SOC_mOhm"]
    out["figure_slope_at_OCV_3p70_mOhm"] = out["ocv_3.70"]["slope_4p5_10A_mOhm"]
    out["constant_current"] = {("I%.0f" % I): hours_at_current(I, c) for I in (4.0, 5.0, 6.0)}
    return out


if __name__ == "__main__":
    print(json.dumps(summary(), indent=1))
