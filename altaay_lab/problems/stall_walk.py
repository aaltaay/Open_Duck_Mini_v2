#!/usr/bin/env python3
"""Why the sheet-stall walk falls, using the electromechanical twin as it is.

Reused, not rewritten:
  twin/electromech/em_twin.py          run()
  twin/electromech/servo_sts3215.py    mode "sheet", the C001 numbers
  twin/electromech/p45b.py             the pack

The sheet does not publish the position gain. Mode "sheet" scales the trained
gain with the stall. One case below turns that scale off and leaves the torque
cap, which is the other reading the servo file already allows. No new actuator.

  python3 altaay_lab/problems/stall_walk.py
Writes stall_walk.json next to this file. sim pass only.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
EM = os.path.join(LAB, "twin", "electromech")
sys.path.insert(0, EM)
os.environ.setdefault("TWIN_EM_SCRATCH", os.path.join(__import__("tempfile").gettempdir(), "twin_em"))

import em_twin as ET  # noqa: E402
import servo_sts3215 as SV  # noqa: E402

_SCALES = SV.ServoBank.scales
_INIT = SV.ServoBank.__init__


def _init(self, model, mode="bam", i_q=SV.I_Q, v_uvp=SV.V_UVP):
    _INIT(self, model, mode=mode, i_q=i_q, v_uvp=v_uvp)
    self._trained_gain = False


def _scales(self, V):
    g, lim, off = _SCALES(self, V)
    if self.mode == "sheet" and self._trained_gain:
        # Torque cap stays the sheet. Gain stays the trained gain times V / 7.4.
        # The sheet says PID and does not give the gain (servo_sts3215.py).
        s = np.clip(np.asarray(V, float), 0.0, None) / SV.V_TRAIN
        g = np.where(off, 0.0, s)
    return g, lim, off


SV.ServoBank.__init__ = _init
SV.ServoBank.scales = _scales


def knee_window(r):
    """Knee volts and how often the torque sits on the cap, up to the fall. sim pass only.

    V_min is the lowest sample in each 100 ms bin (the twin's V_min bins).
    V_mean is the mean of the bin means. The lowest bin mean is not the dip.
    """
    names = list(r["names"])
    ik = [names.index(n) for n in ("left_knee", "right_knee") if n in names]
    bins = r.get("_bins") or {}
    Vmean = bins.get("V_mean")
    Vmin = bins.get("V_min")
    sat = bins.get("sat_frac")
    t_end = (r.get("_binsp") or {}).get("t_end")
    if Vmean is None or Vmin is None or t_end is None or len(t_end) == 0:
        return {}
    fall = r["falls"][0] if r["falls"] else 1e9
    use = np.asarray(t_end) <= fall + 0.05
    if not np.any(use):
        use = np.ones(len(t_end), bool)
    out = {}
    for i, n in zip(ik, ("left_knee", "right_knee")):
        ss = sat[use, i] if sat is not None else None
        out[n] = dict(
            V_min=round(float(Vmin[use, i].min()), 3),
            V_mean=round(float(Vmean[use, i].mean()), 3),
            sat_mean=None if ss is None else round(float(ss.mean()), 3),
        )
    return out


_DUTY = SV.ServoBank.duty_of


def _duty(self, data):
    """Same duty as the servo file, except the trained-gain case.

    Mode sheet scales the gain with the stall, and duty_of uses that same scale.
    When the experiment leaves the gain at the trained value, the torque at 7.4 V
    is kp times the error, still clipped to the sheet cap. The duty has to be that
    torque over the sheet cap, or the bus solve understates the current.
    """
    if not getattr(self, "_trained_gain", False):
        return _DUTY(self, data)
    ctrl = np.where(self.ctrllimited, np.clip(data.ctrl, self.ctrlrange[:, 0], self.ctrlrange[:, 1]), data.ctrl)
    q = data.qpos[self.qadr]
    f74 = self.kp0 * (ctrl - q)
    lo = self.fr0[:, 0] * self.torque_scale
    hi = self.fr0[:, 1] * self.torque_scale
    return np.clip(f74, lo, hi) / hi


SV.ServoBank.duty_of = _duty


def one(name, trained_gain=False, **kw):
    SV.ServoBank._trained_gain_default = trained_gain

    def mark(self, model, mode="bam", i_q=SV.I_Q, v_uvp=SV.V_UVP):
        _init(self, model, mode=mode, i_q=i_q, v_uvp=v_uvp)
        self._trained_gain = trained_gain

    SV.ServoBank.__init__ = mark
    kw.setdefault("dur", 8.0)
    kw.setdefault("stop_on_fall", True)
    kw.setdefault("guard", None)
    kw.setdefault("keep_full", False)
    kw.setdefault("t_stats", 0.0)
    kw.setdefault("cell", "p45b")
    kw.setdefault("q0", 0.0)
    kw.setdefault("servo_mode", "sheet")
    kw.setdefault("mass", "ours")
    print("RUN", name, flush=True)
    r = ET.run(label=name, **kw)
    row = dict(
        name=name,
        label="sim pass only",
        walk=r["walk"],
        supply=r["supply"],
        corner=r["corner"],
        cmd=r["cmd"],
        servo_mode=r["servo_mode"],
        trained_gain=trained_gain,
        falls=r["falls"],
        dur_s=r["dur_s"],
        wall_s=r["wall_s"],
        track_lin=None if r["gait"].get("track_lin") is None else round(r["gait"]["track_lin"], 3),
        vx_m_s=None if r["gait"].get("vx") is None else round(r["gait"]["vx"], 4),
        pitch_mean_deg=None if r["gait"].get("pitch_mean_deg") is None else round(r["gait"]["pitch_mean_deg"], 2),
        pack=r.get("pack"),
        knees=knee_window(r),
        sat_pct=None,
        V_min=None,
    )
    if r.get("servo"):
        names = list(r["names"])
        row["sat_pct"] = {n: r["servo"]["sat_pct"][names.index(n)] for n in ("left_knee", "right_knee") if n in names}
        row["V_min"] = {n: r["servo"]["V_min"][names.index(n)] for n in ("left_knee", "right_knee") if n in names}
        row["tau_limit_mean_Nm"] = {
            n: r["servo"]["tau_limit_mean_Nm"][names.index(n)] for n in ("left_knee", "right_knee") if n in names
        }
    print("  falls", row["falls"], "track", row["track_lin"], "vx", row["vx_m_s"], "knees", row["knees"], "wall", row["wall_s"], flush=True)
    return row


def main():
    sheet = SV.datasheet_check()["sheet"]
    print("datasheet check, sheet mode", json.dumps(sheet), flush=True)
    rows = []
    base = dict(supply="net", corner="typical", walk="backlash")
    rows.append(one("sheet net backlash typical", **base))
    rows.append(one("sheet net backlash high-side", supply="net", corner="high-side", walk="backlash"))
    rows.append(one("sheet net plain typical", supply="net", corner="typical", walk="plain"))
    rows.append(one("sheet fixed 7.4 backlash", supply="fixed", fixed_v=7.4, corner="typical", walk="backlash", dur=20.0))
    # Every speed the report quotes, for 20 s, including the high-side 0.07 m/s case.
    for spd, corner in (
        (0.10, "typical"), (0.09, "typical"), (0.08, "typical"),
        (0.07, "typical"), (0.07, "high-side"),
        (0.06, "typical"), (0.05, "typical"),
    ):
        rows.append(one(
            "sheet net cmd %.2f %s" % (spd, corner),
            supply="net", corner=corner, walk="backlash", cmd=(spd, 0.0, 0.0), dur=20.0,
        ))
    rows.append(one(
        "sheet torque cap, trained gain",
        trained_gain=True, supply="net", corner="typical", walk="backlash", dur=20.0,
    ))
    doc = dict(
        label="sim pass only",
        reused=["twin/electromech/em_twin.py run()", "twin/electromech/servo_sts3215.py mode sheet", "twin/electromech/p45b.py"],
        sheet_vs_datasheet=sheet,
        sheet_note="No-load speed in sheet mode is the BAM speed because the stall scale cancels. Stall torque is the sheet. The gain scale is not on the sheet.",
        tau_sheet_Nm=round(SV.TAU_SHEET, 3),
        tau_train_Nm=SV.TAU_MAX_TRAIN,
        rows=rows,
    )
    path = os.path.join(HERE, "stall_walk.json")
    json.dump(doc, open(path, "w"), indent=1)
    print("wrote", path, flush=True)


if __name__ == "__main__":
    main()
