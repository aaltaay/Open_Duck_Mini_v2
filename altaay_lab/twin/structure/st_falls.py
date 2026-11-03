"""Structure twin: fall impact loads with a contact stiffness sweep (sim pass only).

The upstream MJCF lets only the two TPU soles touch the floor, so a fallen robot sinks through it. st_sim.build_model
(collide=True) gives every printed part a convex-hull contact with the floor (not with the robot). Each fall runs
first at the lab settings (2 ms step, contact time constant 0.02 s, the MuJoCo default) until the first hit of a
printed part; it is then replayed from 0.1 s before that hit with a 0.1 ms step and a stiffer contact on the printed
parts (time constant 0.02, 0.005, 0.002, 0.001, 0.0005 s, damping ratio 1), so every stiffness starts from the same
state. The impact window is 1.2 s (the first hit, the head swing and the second hit).

Cases (sim pass only):
  stand_push_<dir> : standing (zero command), one 0.1 s push on the trunk at t = 3 s, 60 N, back, forward, left, right
                     (40 N does not topple it: the policy steps and recovers)
  stand_torque_off : standing, every servo loses torque at t = 3 s (kp 0, the joint damping and friction stay)
  rough_seed<k>    : walk_rough_backlash_raised_start of print/MASS_STUDY.md (rough terrain, start raised 23 mm), seeds 1 to 6
Output: ODM_SCRATCH/falls/<case>_tc<..>.npz and ODM_SCRATCH/falls/summary_falls.json
Run: ODM_PLAYGROUND=... ODM_SCRATCH=... nice -n 10 python3 altaay_lab/twin/structure/st_falls.py [cases]
"""
import os, sys, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import st_sim as S
import mujoco

OUT = os.path.join(S.SCR_ROOT, "falls"); os.makedirs(OUT, exist_ok=True)
# (time constant s, damping ratio): dr 1 is the MuJoCo default shape (no bounce); dr 0.2 bounces (restitution about 0.5)
# and gives a contact natural frequency w = 1 / (tc dr), so stiffness per kg of effective mass k/m = w^2:
# 1e5, 1e6, 3e6 and 1e7 N/m per kg for the four dr 0.2 entries
TCS = ((0.02, 1.0), (0.005, 1.0), (0.002, 1.0), (0.001, 1.0), (0.0005, 1.0),
       (0.0158, 0.2), (0.005, 0.2), (0.00289, 0.2), (0.00158, 0.2))
DT_IMPACT = 0.0001
WIN = 1.2
ITER = 30

def cases():
    out = []
    for dirn, vec in (("back", (-1, 0, 0)), ("forward", (1, 0, 0)), ("left", (0, 1, 0)), ("right", (0, -1, 0))):
        out.append((f"stand_push_{dirn}", "scene_flat_terrain.xml", S.CB.sched_const([0, 0, 0, 0, 0, 0, 0]), 8.0,
                    [(3.0, 3.1, tuple(60.0 * np.array(vec, float)))], 0.0, None, 0.0, None))
    out.append(("stand_torque_off", "scene_flat_terrain.xml", S.CB.sched_const([0, 0, 0, 0, 0, 0, 0]), 8.0, None, 0.0, None, 0.0, 3.0))
    rb = [c for c in S.AM.CASES if c[0] == "walk_rough_backlash_raised_start"][0]
    for sd in range(1, 7):
        out.append((f"rough_seed{sd}", rb[1], rb[2], rb[3], None, rb[5], sd, 2.0, None))
    return out

def first_hit(folder, case):
    """lab-setting run until the first printed-part contact; returns (snapshots, t_hit, sim)"""
    name, scene, sch, dur, pushes, dz, seed, xyr, t_off = case
    sim = S.Sim(folder, scene, dz, seed, xyr, dt=0.002, iterations=ITER)
    snaps = []; t_hit = None
    n = int(round(dur / 0.002))
    kp0 = sim.model.actuator_gainprm[:, 0].copy(); bias0 = sim.model.actuator_biasprm[:, :3].copy()
    for k in range(n):
        if t_off is not None and abs(sim.t - t_off) < 1e-9:
            sim.model.actuator_gainprm[:, 0] = 0; sim.model.actuator_biasprm[:, 1] = 0
        if k % 10 == 0:
            snaps.append(sim.snapshot()); snaps = snaps[-30:]
        sim.step(sch, pushes)
        hit = any(b not in (sim.model.body("foot_assembly").id, sim.model.body("foot_assembly_2").id) and np.linalg.norm(f) > 0.5
                  for b, (f, pen, nc) in sim.contacts().items())
        if hit:
            t_hit = sim.t; break
    sim.model.actuator_gainprm[:, 0] = kp0; sim.model.actuator_biasprm[:, :3] = bias0
    return snaps, t_hit, sim

def body_vel(sim):
    """world linear velocity of every body centre of mass (m/s)"""
    md, d = sim.model, sim.data; out = np.zeros((md.nbody, 3)); r = np.zeros(6)
    for b in range(md.nbody):
        mujoco.mj_objectVelocity(md, d, mujoco.mjtObj.mjOBJ_BODY, b, r, 0)
        out[b] = r[3:] + np.cross(r[:3], d.xipos[b] - d.xpos[b])
    return out

def impact(folder, case, snaps, t_hit, tc, dr=1.0):
    name, scene, sch, dur, pushes, dz, seed, xyr, t_off = case
    sim = S.Sim(folder, scene, dz, seed, xyr, dt=0.002, iterations=ITER)
    s0 = [s for s in snaps if s["t"] <= t_hit - 0.1 + 1e-9]
    s0 = s0[-1] if s0 else snaps[0]
    sim.restore(s0)
    if t_off is not None and s0["t"] >= t_off - 1e-9:
        sim.model.actuator_gainprm[:, 0] = 0; sim.model.actuator_biasprm[:, 1] = 0
    sim.set_dt(DT_IMPACT); sim.counter = int(round((s0["counter"] % 10) * 0.002 / DT_IMPACT))
    sim.set_body_solref(tc, dr)
    n = int(round(WIN / DT_IMPACT)); every = 2
    J = len(S.JOINTS); nb = sim.model.nbody
    tt, FF, TT, BC, PEN, AA, VV, QQ = [], [], [], [], [], [], [], []
    qa = np.array(sim.m.actuator_joint_qpos_addr).ravel()
    for k in range(n):
        if t_off is not None and abs(sim.t - t_off) < DT_IMPACT / 2:
            sim.model.actuator_gainprm[:, 0] = 0; sim.model.actuator_biasprm[:, 1] = 0
        sim.step(sch, pushes)
        if k % every: continue
        F, T, A = sim.record()
        bc = np.zeros((nb, 3)); pen = np.zeros(nb)
        for b, (f, p, nc) in sim.contacts().items(): bc[b] = f; pen[b] = p
        tt.append(sim.t); FF.append(F); TT.append(T); BC.append(bc); PEN.append(pen); AA.append([A[b] for b in sim.sA]); VV.append(body_vel(sim)); QQ.append(sim.data.qpos[qa].copy())
    R = dict(t=np.array(tt), F=np.array(FF), T=np.array(TT), BC=np.array(BC), PEN=np.array(PEN), A=np.array(AA), V=np.array(VV), q=np.array(QQ),
             acc_names=list(sim.sA.keys()), body_names=sim.body_names, joints=S.JOINTS)
    np.savez_compressed(os.path.join(OUT, f"{name}_tc{tc:g}_dr{dr:g}.npz"), **{k: (np.array(v) if not isinstance(v, np.ndarray) else v.astype(np.float32) if v.dtype.kind == "f" else v) for k, v in R.items()})
    return R

def summarize(R, name, tc, t_hit, dr=1.0):
    bn = R["body_names"]; out = dict(case=name, tc=tc, dr=dr, w_rad_s=1.0 / (tc * dr), t_hit=t_hit, bodies={}, joints={}, acc_peak_g={})
    BCn = np.linalg.norm(R["BC"], axis=-1)
    for b in range(BCn.shape[1]):
        if BCn[:, b].max() < 1.0: continue
        i = int(np.argmax(BCn[:, b])); pen = float(-R["PEN"][i, b])
        on = np.nonzero(BCn[:, b] > 1.0)[0]; i0 = int(on[0]); dtl = R["t"][1] - R["t"][0]
        w30 = (R["t"] >= R["t"][i0]) & (R["t"] < R["t"][i0] + 0.03)
        vpre = R["V"][max(i0 - 1, 0), b]
        out["bodies"][bn[b]] = dict(peak_N=float(BCn[i, b]), t=float(R["t"][i]), t_onset=float(R["t"][i0]), pen_mm_at_peak=pen * 1000,
                                    impulse_Ns=float(BCn[:, b].sum() * dtl), impulse_first30ms_Ns=float(BCn[w30, b].sum() * dtl),
                                    v_pre_mps=[float(x) for x in vpre], v_pre_down_mps=float(-vpre[2]))
    F, T = R["F"], R["T"]
    for j, nm in enumerate(R["joints"]):
        fr = np.hypot(F[:, j, 0], F[:, j, 1]); fa = F[:, j, 2]; mb = np.hypot(T[:, j, 0], T[:, j, 1]); mz = T[:, j, 2]
        out["joints"][nm] = dict(F_radial=float(fr.max()), F_axial=float(np.abs(fa).max()), F_total=float(np.linalg.norm(F[:, j], axis=-1).max()),
                                 M_bend=float(mb.max()), M_axis=float(np.abs(mz).max()))
    for i, b in enumerate(R["acc_names"]):
        out["acc_peak_g"][b] = float(np.linalg.norm(R["A"][:, i], axis=-1).max() / 9.81)
    return out

if __name__ == "__main__":
    only = sys.argv[1:]
    folder, B = S.build_model("st_fall", collide=True)
    res = []
    path = os.path.join(OUT, "summary_falls.json")
    if os.path.exists(path): res = [r for r in json.load(open(path)) if not only or r["case"] not in only]
    for case in cases():
        if only and case[0] not in only: continue
        t0 = time.time(); snaps, t_hit, _ = first_hit(folder, case)
        if t_hit is None:
            print(f"{case[0]:20s} no printed-part hit in {case[3]} s", flush=True); res.append(dict(case=case[0], t_hit=None)); continue
        for tc, dr in TCS:
            R = impact(folder, case, snaps, t_hit, tc, dr); s = summarize(R, case[0], tc, t_hit, dr); res.append(s)
            top = sorted(s["bodies"].items(), key=lambda kv: -kv[1]["peak_N"])[:3]
            print(f"{case[0]:20s} hit {t_hit:.3f} s tc {tc:<7g} dr {dr:<4g} " + ", ".join(f"{b} {v['peak_N']:.0f} N pen {v['pen_mm_at_peak']:.2f} mm" for b, v in top) +
                  f" | head_roll F {s['joints']['head_roll']['F_total']:.0f} N, neck_pitch Mb {s['joints']['neck_pitch']['M_bend']:.1f} Nm, head acc {s['acc_peak_g'].get('head_assembly', 0):.0f} g ({time.time() - t0:.0f} s)", flush=True)
        json.dump(res, open(path, "w"), indent=1)
    print("wrote", OUT)
