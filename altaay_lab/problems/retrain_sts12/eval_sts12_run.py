#!/usr/bin/env python3
"""60 s em_twin sheet walks of a retrained policy, same setup as problems/sts12_mass.py (PR 71 FIT3).

12 V sheet servo, 3S P45B pack, BEC 12.0 V, backlash scene, 70 g cell in the trunk, both corners.
The 16.0 V pass-through is superseded (outside the cited 4.8 to 12.5 V output).
Adds per-step foot contact (flight phase), action rate, joint accel and jerk, and a speed sequence.
Usage: ODM_ONNX=<policy.onnx> ODM_PLAYGROUND=<pin> python3 eval_sts12_run.py OUT.json [dur] [jobs]
Sim pass only.
"""
import json, os, sys, multiprocessing as mp
LABP = os.environ.get("ODM_LAB_PROBLEMS")
sys.path.insert(0, LABP)
import numpy as np
import sts12_mass as SM   # imports em_twin, sets the 12 V sheet and the 3S cell
ET = SM.ET
import mujoco

CMDS = [0.10, 0.15, 0.20, 0.25, 0.30, 0.40]
SEQ = [(0.0, 0.10), (12.0, 0.20), (24.0, 0.40), (36.0, 0.20), (48.0, 0.10)]   # walk, jog, run, jog, walk

REC = {}
_orig_step = mujoco.mj_step

def _rec_step(model, data, *a, **k):
    _orig_step(model, data, *a, **k)
    r = REC.get("r")
    if r is None:
        return
    if r.get("model") is not model:
        r["model"] = model
        r["lf"] = model.body("foot_assembly").id
        r["rf"] = model.body("foot_assembly_2").id
        r["gb"] = model.geom_bodyid.copy()
    n = data.ncon
    lc = rc = False
    if n:
        g = data.contact.geom[:n]
        b = r["gb"][g]
        lc = bool(np.any(b == r["lf"])); rc = bool(np.any(b == r["rf"]))
    r["c"].append((float(data.time), lc, rc))

mujoco.mj_step = _rec_step
ET.mujoco.mj_step = _rec_step

_MI = ET.MI.MjInfer
class RecInfer(_MI):
    def get_obs(self, data, commands):
        r = REC.get("r")
        if r is not None:
            r["a"].append(np.array(self.last_action, dtype=float))
            r["q"].append(np.array(data.qpos[self.actuator_joint_qpos_addr if hasattr(self, "actuator_joint_qpos_addr") else slice(7, None)], dtype=float).ravel())
            fb = self._floating_base_qpos_addr
            r["p"].append((float(data.time), float(data.qpos[fb]), float(data.qpos[fb + 1]), float(commands[0])))
        return super().get_obs(data, commands)
ET.MI.MjInfer = RecInfer


def stats(r, t0=4.0, fall=None):
    c = np.array([(t, l, rr) for t, l, rr in r["c"]], float)
    tend = fall if fall else 1e9
    sel = (c[:, 0] >= t0) & (c[:, 0] < tend)
    out = {}
    if sel.sum():
        cs = c[sel]; dt = np.median(np.diff(cs[:, 0])) if len(cs) > 1 else 0.002
        fl = (cs[:, 1] == 0) & (cs[:, 2] == 0)
        runs, cur = [], 0
        for f in fl:
            if f: cur += 1
            elif cur: runs.append(cur); cur = 0
        if cur: runs.append(cur)
        out.update(flight_frac=round(float(fl.mean()), 4), flight_events=int(sum(1 for x in runs if x * dt >= 0.010)),
                   flight_longest_ms=round(float(max(runs) * dt * 1000) if runs else 0.0, 1),
                   double_support_frac=round(float(((cs[:, 1] == 1) & (cs[:, 2] == 1)).mean()), 4))
    A = np.array(r["a"]); P = np.array(r["p"])
    if len(A) > 3:
        tt = P[:, 0]; s2 = (tt >= t0) & (tt < tend)
        da = np.diff(A, axis=0)[s2[1:]]
        out["action_rate_mean"] = round(float((da ** 2).sum(1).mean()), 5)  # same sum of squares as cost_action_rate, per 20 ms step
        Q = np.array(r["q"]); h = 0.02
        qd = np.diff(Q, axis=0) / h; qdd = np.diff(qd, axis=0) / h; qddd = np.diff(qdd, axis=0) / h
        m3 = s2[3:]
        if m3.any():
            out["joint_acc_rms_rad_s2"] = round(float(np.sqrt((qdd[1:][m3] ** 2).mean())), 2)
            out["joint_jerk_rms_rad_s3"] = round(float(np.sqrt((qddd[m3] ** 2).mean())), 1)
    return out


def seg_speeds(r, fall=None):
    P = np.array(r["p"]); out = []
    bounds = [s[0] for s in SEQ] + [60.0]
    for i, (t0, v) in enumerate(SEQ):
        a, b = t0 + 2.0, bounds[i + 1]      # skip the first 2 s after each change
        if fall and fall < b: b = fall
        sel = (P[:, 0] >= a) & (P[:, 0] < b)
        if sel.sum() < 10:
            out.append(dict(cmd=v, from_s=t0, speed_m_s=None)); continue
        x, y = P[sel, 1], P[sel, 2]
        out.append(dict(cmd=v, from_s=t0, speed_m_s=round(float(np.hypot(x[-1] - x[0], y[-1] - y[0]) / (P[sel, 0][-1] - P[sel, 0][0])), 4)))
    return out


def one(job):
    corner, cmd, dur = job
    REC["r"] = dict(c=[], a=[], q=[], p=[])
    if cmd == "seq":
        def sched(t):
            v = SEQ[0][1]
            for t0, vv in SEQ:
                if t >= t0: v = vv
            return [v, 0.0, 0.0, 0, 0, 0, 0]
        ET.CB.sched_const = lambda c: sched
        row = SM.walk(corner, SEQ[0][1], dur)
        row["cmd_m_s"] = "seq " + "/".join(str(v) for _, v in SEQ)
    else:
        row = SM.walk(corner, cmd, dur)
    fall = row["fall_s"][0] if isinstance(row["fall_s"], list) and row["fall_s"] else None
    row["smooth"] = stats(REC["r"], fall=fall)
    if cmd == "seq":
        row["segments"] = seg_speeds(REC["r"], fall)
    # the gait pitch and roll RMS from em_twin (after 4 s)
    return row


def init():
    dst, moved = SM.heavier_model()
    ET.model_folder = lambda mass: dst
    return moved


if __name__ == "__main__":
    out = sys.argv[1]; dur = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    jobs_n = int(sys.argv[3]) if len(sys.argv) > 3 else 14
    which = os.environ.get("EVAL_CMDS")
    cmds = [float(x) if x != "seq" else "seq" for x in which.split(",")] if which else CMDS + ["seq"]
    moved = init()
    jobs = [(c, v, dur) for v in cmds for c in ("typical", "high-side")]
    # also expose gait pitch and roll rms
    _orig_walk = SM.walk
    def walk2(corner, cmd, d):
        r = ET.run(mass="ours", walk="backlash", cmd=(cmd, 0.0, 0.0), dur=d, supply="net", corner=corner, extra=dict(BEC_V=12.0),
                   cell="p45b3", q0=0.0, servo_mode="sheet", guard=None, keep_full=False, stop_on_fall=True, t_stats=0.0, label="sts12r")
        g = r["gait"]
        return dict(label="sim pass only", corner=corner, cmd_m_s=cmd, dur_s=r["dur_s"], fall_s=r["falls"] or "none",
                    vx_m_s=None if g.get("vx") is None else round(g["vx"], 4),
                    track_lin=None if g.get("track_lin") is None else round(g["track_lin"], 3),
                    pitch_rms_deg=None if g.get("pitch_rms_deg") is None else round(g["pitch_rms_deg"], 3),
                    roll_rms_deg=None if g.get("roll_rms_deg") is None else round(g["roll_rms_deg"], 3),
                    knees=SM.knees_of(r), pack=r.get("pack"))
    SM.walk = walk2
    with mp.get_context("fork").Pool(min(jobs_n, len(jobs))) as pool:
        rows = pool.map(one, jobs)
    doc = dict(label="sim pass only", onnx=os.path.basename(os.environ.get("ODM_ONNX", "")), trunk=moved, dur_s=dur, rows=rows)
    json.dump(doc, open(out, "w"), indent=1)
    for r in rows:
        print(r["corner"], r["cmd_m_s"], r["fall_s"], r["vx_m_s"], r.get("pitch_rms_deg"), r.get("roll_rms_deg"), r["knees"], r["smooth"], r.get("segments", ""), flush=True)
