"""Structure twin: walking, turning, side step, backlash and push-recovery loads at every joint (sim pass only).

Cases (the sim agent's cases of sim/added_mass_sim.py, on our 2.65 kg build, policy unchanged):
  walk  : stand_in_place, walk_forward_0.15, turn_1.0, walk_side_0.2, walk_backlash; nominal and seeds 1 to 3
  push  : walk_pushes (15 N for 0.1 s every 3 s, left and right), seeds none and 1 to 3; plus single 0.1 s pushes at
          the largest force our build survived in every gait phase (sim/ADDED_MASS_SIM.md table 8: left 18 N,
          right 15 N, forward 9 N, back 9 N), 8 gait phases each
  push2 : more single pushes with the converged solver (left 9 to 15 N, right 9 and 12 N, forward 12 and 15 N, back 12 N)
  check : solver and time step check on walk_forward_0.15 (iterations 1 against 30, dt 2 ms against 1 ms)
Output: ODM_SCRATCH/loads/<case>.npz (time series, heavy, never in git) and ODM_SCRATCH/loads/summary_<set>.json.
Run: ODM_PLAYGROUND=... ODM_SCRATCH=... nice -n 10 python3 altaay_lab/twin/structure/st_loads.py walk|push|check
"""
import os, sys, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import st_sim as S

OUT = os.path.join(S.SCR_ROOT, "loads"); os.makedirs(OUT, exist_ok=True)
SKIP = 2.0     # the first 2 s (drop onto the floor and settle) are left out, as sim/current_budget.py does
ITER = 30      # Newton iterations per step: the upstream 1 leaves contact forces unconverged (spikes to 2.6 x, check set);
               # 10, 30 and 100 give the same peaks to 0.1 %, so 30 is used for every load case

def rainflow(x):
    """ASTM E1049-85 rainflow counting (three-point method): returns list of (range, mean, count 0.5 or 1)"""
    x = np.asarray(x, float)
    if len(x) < 3: return []
    d = np.diff(x); keep = np.r_[True, (d[1:] * d[:-1]) < 0, True]     # turning points
    tp = x[np.r_[0, np.nonzero(keep[1:-1])[0] + 1, len(x) - 1]] if len(x) > 2 else x
    st = []; out = []
    for v in tp:
        st.append(v)
        while len(st) >= 3:
            X = abs(st[-1] - st[-2]); Y = abs(st[-2] - st[-3])
            if X < Y: break
            if len(st) == 3:
                out.append((Y, 0.5 * (st[-2] + st[-3]), 0.5)); st.pop(0)
            else:
                out.append((Y, 0.5 * (st[-2] + st[-3]), 1.0)); del st[-3:-1]
    for i in range(len(st) - 1):
        out.append((abs(st[i + 1] - st[i]), 0.5 * (st[i + 1] + st[i]), 0.5))
    return out

def channels(R):
    """per joint, in the child link frame at the joint origin (z = joint axis); force of the parent on the child"""
    F, T = R["F"], R["T"]
    return dict(F_radial=np.hypot(F[..., 0], F[..., 1]), F_axial=F[..., 2], F_total=np.linalg.norm(F, axis=-1),
                M_axis=T[..., 2], M_bend=np.hypot(T[..., 0], T[..., 1]))

def summarize(R, label, t0=SKIP):
    sel = R["t"] >= t0
    ch = channels(R); out = dict(label=label, falls=R["falls"], dur_s=float(R["t"][sel][-1] - R["t"][sel][0]) if sel.any() else 0, joints={})
    for j, nm in enumerate(R["joints"]):
        o = {}
        for c, v in ch.items():
            x = v[sel, j]
            o[c] = dict(peak=float(np.abs(x).max()), p999=float(np.percentile(np.abs(x), 99.9)), rms=float(np.sqrt((x ** 2).mean())),
                        min=float(x.min()), max=float(x.max()))
        # rainflow on the bending moment and the radial force: ranges and counts per second
        for c in ("M_bend", "F_radial", "M_axis", "F_total"):
            cyc = rainflow(ch[c][sel, j]); dur = out["dur_s"] or 1
            rngs = np.array([a for a, _, _ in cyc]); cnt = np.array([n for _, _, n in cyc])
            big = rngs >= 0.5 * (rngs.max() if len(rngs) else 0)
            o[c]["rf_cycles_per_s_over_half_max_range"] = float(cnt[big].sum() / dur) if len(rngs) else 0
            o[c]["rf_max_range"] = float(rngs.max()) if len(rngs) else 0
            # damage-equivalent range at 1 cycle per gait period for an S-N slope m (PLA m about 10 to 15; m = 12 used here)
            m_ = 12.0; n_ref = dur / 0.54
            o[c]["rf_deq_range_m12_per_gait"] = float(((cnt * rngs ** m_).sum() / n_ref) ** (1 / m_)) if len(rngs) else 0
        out["joints"][nm] = o
    grf = R["GRF"][sel]; gz = grf[..., 2]
    out["grf"] = dict(left_peak_z=float(gz[:, 0].max()), right_peak_z=float(gz[:, 1].max()),
                      left_peak_xy=float(np.hypot(grf[:, 0, 0], grf[:, 0, 1]).max()), right_peak_xy=float(np.hypot(grf[:, 1, 0], grf[:, 1, 1]).max()),
                      weight_N=float(2.6528 * 9.81))
    # stance cycles per foot (contact on with more than 2 N)
    on = gz > 2.0; rises = (np.diff(on.astype(int), axis=0) == 1).sum(0)
    out["grf"]["stance_cycles_per_s"] = (rises / max(out["dur_s"], 1e-9)).tolist()
    A = R["A"][sel]; an = R["acc_names"]
    out["acc_peak_g"] = {b: float(np.linalg.norm(A[:, i], axis=-1).max() / 9.81) for i, b in enumerate(an)}
    return out

def save(R, name):
    np.savez_compressed(os.path.join(OUT, name + ".npz"), t=R["t"].astype(np.float32), F=R["F"].astype(np.float32), T=R["T"].astype(np.float32),
                        A=R["A"].astype(np.float32), GRF=R["GRF"].astype(np.float32), base=R["base"].astype(np.float32),
                        q=R["q"].astype(np.float32), joints=np.array(R["joints"]), acc_names=np.array(R["acc_names"]),
                        falls=np.array(R["falls"], float), dt=R["dt"])

WALK = [c for c in S.AM.CASES if c[0] in ("stand_in_place", "walk_forward_0.15", "turn_1.0", "walk_side_0.2", "walk_backlash")]

def run_set(which, folder):
    res = []
    if which == "walk":
        for label, scene, sch, dur, pushes, dz in WALK:
            for sd in (None, 1, 2, 3):
                t = time.time(); R = S.run_logged(folder, scene, sch, dur, pushes, dz, seed=sd, iterations=ITER)
                nm = f"{label}_s{sd or 0}"; save(R, nm); s = summarize(R, nm); res.append(s)
                print(f"{nm:28s} falls {R['falls']} knee M_axis peak {s['joints']['left_knee']['M_axis']['peak']:.2f} "
                      f"ankle F peak {s['joints']['left_ankle']['F_total']['peak']:.1f} GRF {s['grf']['left_peak_z']:.1f} ({time.time() - t:.0f} s)", flush=True)
    elif which == "push":
        lab = [c for c in S.AM.CASES if c[0] == "walk_pushes"][0]
        for sd in (None, 1, 2, 3):
            R = S.run_logged(folder, lab[1], lab[2], lab[3], lab[4], lab[5], seed=sd, iterations=ITER)
            nm = f"walk_pushes_s{sd or 0}"; save(R, nm); s = summarize(R, nm); res.append(s)
            print(f"{nm:28s} falls {R['falls']} GRF {s['grf']['left_peak_z']:.1f} {s['grf']['right_peak_z']:.1f}", flush=True)
        for dirn, vec, f in (("left", (0, 1, 0), 18), ("right", (0, -1, 0), 15), ("forward", (1, 0, 0), 9), ("back", (-1, 0, 0), 9)):
            for ph in range(8):
                t0 = 6.0 + ph * 0.54 / 8
                R = S.run_logged(folder, "scene_flat_terrain.xml", S.CB.sched_const([0.15, 0, 0, 0, 0, 0, 0]), 10.0,
                                 [(t0, t0 + 0.1, tuple(f * np.array(vec, float)))], iterations=ITER)
                nm = f"push1_{dirn}_{f}N_ph{ph}"; save(R, nm); s = summarize(R, nm, t0=t0 - 0.5); s["push_t0"] = t0; res.append(s)
                print(f"{nm:28s} falls {R['falls']} GRF {s['grf']['left_peak_z']:.1f} {s['grf']['right_peak_z']:.1f}", flush=True)
    elif which == "push2":
        # converged solver: single 0.1 s pushes at 8 gait phases, rising force; keeps every run (fell or not)
        for dirn, vec, forces in (("left", (0, 1, 0), (9, 12, 15)), ("right", (0, -1, 0), (9, 12)), ("forward", (1, 0, 0), (12, 15)),
                                  ("back", (-1, 0, 0), (12,))):
            for f in forces:
                for ph in range(8):
                    t0 = 6.0 + ph * 0.54 / 8
                    R = S.run_logged(folder, "scene_flat_terrain.xml", S.CB.sched_const([0.15, 0, 0, 0, 0, 0, 0]), 10.0,
                                     [(t0, t0 + 0.1, tuple(f * np.array(vec, float)))], iterations=ITER)
                    nm = f"push1_{dirn}_{f}N_ph{ph}"; save(R, nm); s = summarize(R, nm, t0=t0 - 0.5); s["push_t0"] = t0; res.append(s)
                    print(f"{nm:28s} falls {R['falls']}", flush=True)
    elif which == "check":
        lab = [c for c in S.AM.CASES if c[0] == "walk_forward_0.15"][0]
        for it, dt in ((1, 0.002), (30, 0.002), (1, 0.001), (30, 0.001)):
            R = S.run_logged(folder, lab[1], lab[2], 12.0, None, 0.0, dt=dt, iterations=it if it > 1 else None, log_every=int(round(0.002 / dt)))
            nm = f"check_it{it}_dt{dt * 1000:g}ms"; s = summarize(R, nm); res.append(s)
            j = s["joints"]
            print(f"{nm:28s} falls {R['falls']} knee Mz {j['left_knee']['M_axis']['peak']:.2f} knee Mb {j['left_knee']['M_bend']['peak']:.2f} "
                  f"ankle F {j['left_ankle']['F_total']['peak']:.1f} hip pitch Mb {j['left_hip_pitch']['M_bend']['peak']:.2f} GRF {s['grf']['left_peak_z']:.1f}", flush=True)
    json.dump(res, open(os.path.join(OUT, f"summary_{which}.json"), "w"), indent=1)
    return res

def trained_vs_ours(folder):
    """the walking runs (all walk cases, nominal and seeds 1 to 3, ITER iterations) with the trained inertials
    (MB.model_inertials(), the stock build) and with ours: peak per joint and component, and the peak sole force.
    Writes loads/trained_vs_ours.json."""
    dS, _ = S.build_model("st_stock", links=S.MB.model_inertials())
    res = {}
    for nm, d in (("trained", dS), ("ours", folder)):
        agg = {}
        for label, scene, sch, dur, pushes, dz in WALK:
            if label == "stand_in_place": continue
            for sd in (None, 1, 2, 3):
                R = S.run_logged(d, scene, sch, dur, pushes, dz, seed=sd, iterations=ITER, contacts=True)
                s = summarize(R, label)
                for j, v in s["joints"].items():
                    for c in ("F_radial", "F_axial", "M_axis", "M_bend"):
                        agg.setdefault(j, {}).setdefault(c, 0.0); agg[j][c] = max(agg[j][c], v[c]["peak"])
                agg["grf"] = max(agg.get("grf", 0.0), s["grf"]["left_peak_z"], s["grf"]["right_peak_z"])
                if R["falls"]: print(nm, label, sd, "FELL", R["falls"], flush=True)
        res[nm] = agg
    json.dump(res, open(os.path.join(OUT, "trained_vs_ours.json"), "w"), indent=1)
    print("GRF peak trained", round(res["trained"]["grf"], 1), "ours", round(res["ours"]["grf"], 1))
    return res

if __name__ == "__main__":
    which = sys.argv[1]
    folder, B = S.build_model("st_ours")
    if which == "trained": trained_vs_ours(folder)
    else: run_set(which, folder)
    print("wrote", OUT)
