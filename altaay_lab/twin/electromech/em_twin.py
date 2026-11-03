"""Electromechanical twin of the Open Duck Mini v2: the walking robot, its 14 STS3215 servos and its power path as one
closed loop (sim pass only).

Every 2 ms physics step:
  1. each servo's duty (position error x gain, clipped) comes from the robot state and the policy's target, as the
     trained MuJoCo actuator computes it (servo_sts3215.py);
  2. the power network as built (power_net.py: the ngspice circuit of sim/power_fix.py option ab, D15 star plus the D23
     feeds SP4/SP5, netlist lengths) is solved with each servo drawing its supply current for its own volts; the 2S
     Molicel P30B pack (p30b.py) gives the terminal volts for its charge and current; the Castle CC BEC Pro regulates
     7.2 V or passes its input minus the dropout; the 5 V branch draws its constant power;
  3. each servo's gain and torque limit are set from its volts (BAM: both scale with V / 7.4) and MuJoCo steps;
  4. the pack charge counter advances by the pack current (times the time compression factor, 1 = none).
The 50 Hz policy loop is the lab's copy of the upstream MjInfer loop (sim/current_budget.py run(), accelerometer
bias removed). The D16 battery guard (bench/battery_guard.py, unchanged) reads each servo's volts at a random time in
every 0.5 s, quantized down to 0.1 V as register 62, and runs its rules; "shadow" records its events and walks on.

Open loop (for comparison): the trained robot walks with the actuators unchanged, its torques and speeds are logged,
and the same network replays them with the ngspice servo law of sim/power_path_sim.py (commanded volts capped at the
local bus, constant power), as sim/POWER_PATH_SIM.md 'As built' does.

Usage (from altaay_lab/twin/electromech; TWIN_EM_SCRATCH = folder for heavy outputs):
  python3 em_twin.py check | states | session | sweep | png | all   (see the step functions at the end)
"""
import json
import os
import sys
import time

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):   # tiny matrices: one BLAS thread is fastest
    os.environ.setdefault(_v, "1")
import numpy as np                              # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", ".."))
SIM = os.path.join(LAB, "sim")
BENCH = os.path.join(LAB, "bench")
SCR = os.environ.get("TWIN_EM_SCRATCH", "/tmp/twin_em")
os.makedirs(SCR, exist_ok=True)
os.environ.setdefault("ODM_SCRATCH", os.path.join(SCR, "models"))
os.environ.setdefault("ODM_OUT", os.path.join(SCR, "cb_out"))
for p_ in (HERE, SIM, BENCH):
    if p_ not in sys.path:
        sys.path.insert(0, p_)
import mujoco                                   # noqa: E402
import current_budget as CB                     # noqa: E402  lab file: upstream MjInfer with the two training stubs
import added_mass_sim as AM                     # noqa: E402  lab file: model copies at our build's mass, gait statistics
import mass_budget as MB                        # noqa: E402
import battery_guard as BG                      # noqa: E402  bench/battery_guard.py (D16 rules)
import power_net as PN                          # noqa: E402
import servo_sts3215 as SV                      # noqa: E402
import p30b                                     # noqa: E402

MI = CB.MI
OUT_GIT = os.path.join(HERE, "out")
NAMES = PN.NAMES
SID = [PN.SERVO_ID[n] for n in NAMES]
SCENES = {"backlash": "scene_flat_terrain_backlash.xml", "plain": "scene_flat_terrain.xml"}
CMD = {"forward": (0.15, 0.0, 0.0)}
CELL = p30b.P30B()
STATES = {"full": 0.0, "nominal": CELL.q_at_ocv(3.70), "d16": CELL.q_at_ocv(3.57), "low": CELL.q_at_ocv(3.30)}
STATE_TEXT = {"full": "full (q 0 mAh, OCV 4.20 V/cell)", "nominal": "nominal (OCV 3.70 V/cell)",
              "d16": "near the D16 cut (OCV 3.57 V/cell)", "low": "low (OCV 3.30 V/cell, past the guard)"}
LAB_VCELL = {"full": 4.2, "nominal": 3.7, "low": 3.3}            # sim/power_path_sim.py PACK_CELL_V
T_WALK = 2.0                                    # s, the command starts (sim/current_budget.py sched_const)


# ---------------------------------------------------------------------------------------------------------------
def model_folder(mass):
    """trained: the upstream Playground xmls (b9be205) themselves; ours: sim/added_mass_sim.py copy at the
    sim/mass_budget.py inertials (2.6528 kg, the C8 model)"""
    if mass == "trained":
        return AM.SRC_XML
    d = os.path.join(AM.SCR, "models", "ours")
    if not os.path.exists(os.path.join(d, "open_duck_mini_v2_backlash.xml")):
        B = MB.build_budget()
        pl = {p["id"]: p for p in json.load(open(os.path.join(LAB, "audit", "placements.json")))}
        boxes = [("trunk_assembly", np.array(p["center_mm"]) / 1000, np.array(p["dims_xyz_mm"]) / 1000, "0.85 0.1 0.1 1") for p in pl.values()]
        AM.write_variant("ours", B["links"], boxes)
    return d


class Guard:
    """bench/battery_guard.py fed as on the robot: one read of the 14 servos at a random time in each 0.5 s"""

    def __init__(self, rng, t0, mode="shadow"):
        self.g = BG.BatteryGuard(BG.GuardConfig(), state=BG.WALKING)
        self.rng, self.mode = rng, mode
        self.period = self.g.cfg.period_s
        self.k = 0
        self.t0 = t0
        self.next_t = t0 + rng.uniform(0, self.period)
        self.events, self.medians = [], []

    def due(self, t):
        return t >= self.next_t

    def feed(self, t, V):
        volts = {sid: BG.quantize(float(v)) for sid, v in zip(SID, V)}
        ev = self.g.update(t, volts)
        self.medians.append((round(t, 3), self.g.last_median))
        for e in ev:
            self.events.append(e)
            if e["event"] == "walk_stop" and self.mode == "shadow":
                self.g.set_state(BG.WALKING)     # shadow: keep judging as walking (the walk goes on)
                self.g.state = BG.WALKING
                self.g.w_walk.clear()
        self.k += 1
        self.next_t = self.t0 + self.k * self.period + self.rng.uniform(0, self.period)
        return ev


def sampled_frac(v, dt, period=0.02, thr=6.0):
    """fraction of 50 Hz samples under thr for every 2 ms phase of the 20 ms cycle (as sim/power_fix.py)"""
    n = int(round(period / dt))
    return [float((v[ph::n] < thr).mean()) for ph in range(n)]


# ---------------------------------------------------------------------------------------------------------------
def run(mass="ours", walk="backlash", cmd=CMD["forward"], dur=30.0, supply="net", corner="typical", extra=None,
        cell="p30b", q0=0.0, vcell=3.7, compress=1.0, servo_mode="bam", seed=None, guard="shadow", t_stats=4.0,
        keep_full=True, bin_s=0.1, stop_q=None, stop_on_fall=False, fixed_v=7.4, cell_mode="steady", label="",
        full_windows=None, progress=0.0, pushes=None):
    """one walk. supply: "stock" (trained actuators, no supply effect), "fixed" (every servo at fixed_v volts),
    "net" (the power network). cell: "p30b" (charge q0 mAh, advanced by the pack current x compress) or "lab"
    (OCV vcell per cell with the corner's Rc, as sim/power_path_sim.py). Returns a result dict; full traces in it."""
    folder = model_folder(mass)
    AM._ASSET_DIR[0] = folder
    m = MI.MjInfer(os.path.join(folder, SCENES[walk]), CB.REF, CB.ONNX, standing=False)
    if seed is not None:                         # joint start jitter U(-0.03, 0.03) rad, as sim/added_mass_sim.py seeds
        rng0 = np.random.default_rng(seed)
        qa = np.array(m.actuator_joint_qpos_addr).ravel()
        m.data.qpos[qa] += rng0.uniform(-0.03, 0.03, len(qa))
    mujoco.mj_forward(m.model, m.data)
    _ga = m.get_accelerometer

    def _ga_fixed(d, _ga=_ga):
        a = np.array(_ga(d), dtype=float); a[0] -= 1.3; return a
    m.get_accelerometer = _ga_fixed              # as sim/current_budget.py (bias not in training or on the robot)
    model, data = m.model, m.data
    trunk = model.body("trunk_assembly").id
    names = list(m.actuator_names)
    perm = np.array([names.index(n) for n in NAMES])       # model actuator index of each NAMES entry
    bank = SV.ServoBank(model, mode=servo_mode)
    fb = m._floating_base_qpos_addr
    qv = m.actuator_qvel_addr
    dt = m.sim_dt
    nsteps = int(round(dur / dt))
    cellm = p30b.P30B(mode=cell_mode) if cell == "p30b" else None
    net = PN.Net(corner, extra, cell_model=cellm) if supply == "net" else None
    q = float(q0)
    sched = CB.sched_const(list(cmd) + [0, 0, 0, 0])
    rng = np.random.default_rng(1000 + (seed or 0))
    gd = Guard(rng, T_WALK, guard) if (guard and supply == "net") else None
    nb = max(1, int(round(bin_s / dt)))
    nbins = nsteps // nb
    k0 = int(round(t_stats / dt))
    # accumulators (NAMES order)
    acc = dict(n=0, lt6=np.zeros(14), lt45=np.zeros(14), lt40=np.zeros(14), vmin=np.full(14, 99.0), vsum=np.zeros(14),
               sat=np.zeros(14), im2=np.zeros(14), isup=np.zeros(14), pin=np.zeros(14), err2=np.zeros(14), limsum=np.zeros(14),
               pk_i=[], pk_v=[], bus=[], vout=[], vbin=[])
    BIN = {k: np.zeros((nbins, 14), np.float32) for k in ("V_mean", "V_min", "Isup_mean", "Im_rms", "Pcu_mean", "Pel_mean", "absF_mean", "sat_frac", "w_rms")}
    BINP = {k: np.zeros(nbins, np.float32) for k in ("t_end", "q_mAh", "v_pack_mean", "v_pack_min", "i_pack_mean", "i_pack_max", "v_bus_mean",
                                                    "v_bec_out_mean", "v_bec_out_min", "i_bec_out_mean", "x", "y", "z", "yaw", "fallen")}
    if keep_full:
        FULL = {k: np.zeros((nsteps, 14), np.float32) for k in ("V", "Isup", "Im", "F", "w")}
        FULLP = {k: np.zeros(nsteps, np.float32) for k in ("v_pack", "i_pack", "v_bus", "v_bin", "v_out", "i_bout", "q")}
    win = []                                     # optional full-rate windows for long runs: list of (t0, t1)
    WIN = {}
    if full_windows:
        for (a, b) in full_windows:
            WIN[(a, b)] = dict(t=[], V=[], Isup=[], Im=[], F=[], w=[], pack=[])
    blk = {k: [] for k in ("V", "Vmin", "Isup", "Im2", "Pel", "absF", "sat", "w2", "vp", "ip", "vb", "vo", "io")}
    log, falls, fallen, counter = [], [], False, 0
    # stock replay pairs (as sim/current_budget.py: F after the step, W after the step)
    Ftr = np.zeros((nsteps, 14), np.float32) if supply == "stock" else None
    Wtr = np.zeros((nsteps, 14), np.float32) if supply == "stock" else None
    V = np.full(14, 7.4)
    y = None
    t_start = time.time()
    stopped = None
    for k in range(nsteps):
        t = (k + 1) * dt
        w_m = data.qvel[bank.dadr].copy()
        err_n = (np.clip(data.ctrl, bank.ctrlrange[:, 0], bank.ctrlrange[:, 1]) - data.qpos[bank.qadr])[perm]
        if supply == "stock":
            V = np.full(14, SV.V_TRAIN)
        elif supply == "fixed":
            V = np.full(14, float(fixed_v))
            bank.apply(np.full(model.nu, float(fixed_v)))
        else:
            duty = bank.duty_of(data)[perm]
            wn = w_m[perm]
            if servo_mode == "comp":
                ctrl = np.where(bank.ctrllimited, np.clip(data.ctrl, bank.ctrlrange[:, 0], bank.ctrlrange[:, 1]), data.ctrl)
                dc = (bank.kp0 * (ctrl - data.qpos[bank.qadr]) / bank.fr0[:, 1])[perm]
            else:
                dc = None

            def isup_fn(vn, duty=duty, wn=wn, dc=dc):
                return SV.supply_current_bam(duty, wn, vn, servo_mode, d_comp=dc)
            isup_fn.slope = lambda vn, duty=duty, wn=wn, dc=dc: SV.supply_current_bam(duty, wn, vn, servo_mode, d_comp=dc, slope=True)
            y = net.solve(isup_fn, vcell=vcell, qm=q)
            V = net.servo_volts(y)
            Vm = np.empty(model.nu); Vm[perm] = V
            bank.apply(Vm)
        if pushes:                                   # as sim/current_budget.py: force on the trunk
            data.xfrc_applied[:] = 0
            for (pa, pb, fvec) in pushes:
                if pa <= t < pb:
                    data.xfrc_applied[trunk, :3] = fvec
        mujoco.mj_step(model, data)
        counter += 1
        F_m = data.actuator_force.copy()
        Fn = F_m[perm]; wn = w_m[perm]
        u, im, isup = SV.ServoBank.electrical(Fn, wn, V)
        if supply == "stock":
            Ftr[k] = F_m; Wtr[k] = data.qvel[qv]
        if y is not None:
            ipk = float(y[net.o["i_pack"]])
            if cellm is not None:
                q += ipk * dt / 3.6 * compress
                cellm.advance(ipk, dt)
            vp, vb, vo, io, vbin = (float(y[net.o[x]]) for x in ("v_pack", "v_bus", "v_out", "i_bout", "v_bin"))
        else:
            ipk = vp = vb = vo = io = vbin = np.nan
        lim = np.abs(model.actuator_forcerange[perm, 1])          # the limit this step ran with
        sat = np.abs(Fn) >= 0.999 * lim - 1e-9
        if keep_full:
            FULL["V"][k] = V; FULL["Isup"][k] = isup; FULL["Im"][k] = im; FULL["F"][k] = Fn; FULL["w"][k] = wn
            for kk, val in (("v_pack", vp), ("i_pack", ipk), ("v_bus", vb), ("v_bin", vbin), ("v_out", vo), ("i_bout", io), ("q", q)):
                FULLP[kk][k] = val
        for (a, b), Wd in WIN.items():
            if a <= t < b:
                Wd["t"].append(t); Wd["V"].append(V.astype(np.float32)); Wd["Isup"].append(isup.astype(np.float32)); Wd["Im"].append(im.astype(np.float32))
                Wd["F"].append(Fn.astype(np.float32)); Wd["w"].append(wn.astype(np.float32)); Wd["pack"].append((vp, ipk, vb, vo, io, q))
        # bins
        blk["V"].append(V); blk["Isup"].append(isup); blk["Im2"].append(im * im); blk["Pel"].append(u * im); blk["absF"].append(np.abs(Fn))
        blk["sat"].append(sat); blk["w2"].append(wn * wn); blk["vp"].append(vp); blk["ip"].append(ipk); blk["vb"].append(vb); blk["vo"].append(vo); blk["io"].append(io)
        if (k + 1) % nb == 0 and (k + 1) // nb - 1 < nbins:
            j = (k + 1) // nb - 1
            Vb = np.array(blk["V"])
            BIN["V_mean"][j] = Vb.mean(0); BIN["V_min"][j] = Vb.min(0); BIN["Isup_mean"][j] = np.mean(blk["Isup"], 0)
            BIN["Im_rms"][j] = np.sqrt(np.mean(blk["Im2"], 0)); BIN["Pcu_mean"][j] = np.mean(blk["Im2"], 0) * SV.R_M
            BIN["Pel_mean"][j] = np.mean(blk["Pel"], 0); BIN["absF_mean"][j] = np.mean(blk["absF"], 0); BIN["sat_frac"][j] = np.mean(blk["sat"], 0)
            BIN["w_rms"][j] = np.sqrt(np.mean(blk["w2"], 0))
            BINP["t_end"][j] = t; BINP["q_mAh"][j] = q; BINP["v_pack_mean"][j] = np.mean(blk["vp"]); BINP["v_pack_min"][j] = np.min(blk["vp"])
            BINP["i_pack_mean"][j] = np.mean(blk["ip"]); BINP["i_pack_max"][j] = np.max(blk["ip"]); BINP["v_bus_mean"][j] = np.mean(blk["vb"])
            BINP["v_bec_out_mean"][j] = np.mean(blk["vo"]); BINP["v_bec_out_min"][j] = np.min(blk["vo"]); BINP["i_bec_out_mean"][j] = np.mean(blk["io"])
            pos = data.qpos[fb:fb + 3]; quat = data.qpos[fb + 3:fb + 7]
            Rm = np.zeros(9); mujoco.mju_quat2Mat(Rm, quat)
            BINP["x"][j], BINP["y"][j], BINP["z"][j] = pos
            BINP["yaw"][j] = np.arctan2(Rm[3], Rm[0]); BINP["fallen"][j] = float(fallen)
            for kk in blk:
                blk[kk].clear()
        if k >= k0:
            acc["n"] += 1; acc["lt6"] += V < 6.0; acc["lt45"] += V < 4.5; acc["lt40"] += V < 4.0
            acc["vmin"] = np.minimum(acc["vmin"], V); acc["vsum"] += V; acc["sat"] += sat; acc["im2"] += im * im
            acc["isup"] += isup; acc["pin"] += u * im; acc["err2"] += err_n * err_n; acc["limsum"] += lim
            if y is not None:
                acc["pk_i"].append(ipk); acc["bus"].append(vb); acc["vout"].append(vo); acc["vbin"].append(vbin); acc["pk_v"].append(vp)
        if gd is not None and gd.due(t):
            gd.feed(t, V)
            if guard == "act" and gd.g.state == BG.HARD_STOPPED and stopped is None:
                stopped = ("guard hard stop", round(t, 2))
        if counter % m.decimation == 0:
            m.commands = sched(t)
            if guard == "act" and gd is not None and gd.g.state in (BG.STOPPING, BG.STANDING):
                m.commands = [0.0] * 7
            m.imitation_i += 1.0 * m.phase_frequency_factor
            m.imitation_i = m.imitation_i % m.PRM.nb_steps_in_period
            ph = m.imitation_i / m.PRM.nb_steps_in_period * 2 * np.pi
            m.imitation_phase = np.array([np.cos(ph), np.sin(ph)])
            obs = m.get_obs(data, m.commands)
            action = m.policy.infer(obs)
            m.last_last_last_action = m.last_last_action.copy()
            m.last_last_action = m.last_action.copy()
            m.last_action = action.copy()
            m.motor_targets = m.default_actuator + action * m.action_scale
            if MI.USE_MOTOR_SPEED_LIMITS:
                m.motor_targets = np.clip(m.motor_targets, m.prev_motor_targets - m.max_motor_velocity * (m.sim_dt * m.decimation),
                                          m.prev_motor_targets + m.max_motor_velocity * (m.sim_dt * m.decimation))
                m.prev_motor_targets = m.motor_targets.copy()
            data.ctrl = m.motor_targets.copy()
            pos = data.qpos[fb:fb + 3].copy(); quat = data.qpos[fb + 3:fb + 7].copy()
            Rm = np.zeros(9); mujoco.mju_quat2Mat(Rm, quat); Rm = Rm.reshape(3, 3); upz = Rm[2, 2]
            if (pos[2] < 0.10 or upz < 0.5) and not fallen:
                fallen = True; falls.append(round(t, 2))
            if fallen and pos[2] > 0.13 and upz > 0.8:
                fallen = False
            yaw = np.arctan2(Rm[1, 0], Rm[0, 0]); pitch = np.arcsin(-np.clip(Rm[2, 0], -1, 1)); roll = np.arctan2(Rm[2, 1], Rm[2, 2])
            log.append((t, pos[0], pos[1], pos[2], yaw, pitch, roll, 0, 0, 0, float(fallen)))
            if progress and (k + 1) % int(round(progress / dt)) == 0:
                print("  %s t %.0f s q %.0f mAh pack %.2f V bus %.2f V falls %s (%.0f s wall)" % (label, t, q, vp, vb, falls, time.time() - t_start), flush=True)
        if stop_on_fall and falls:
            stopped = stopped or ("fall", falls[0])
        if stop_q is not None and q >= stop_q:
            stopped = stopped or ("charge limit", round(t, 2))
        if stopped:
            nsteps = k + 1
            break
    bank.restore()
    wall = time.time() - t_start
    L = np.array(log)
    res = dict(label=label, mass=mass, walk=walk, cmd=list(cmd), dur_s=round(nsteps * dt, 3), supply=supply, corner=corner, extra=extra or {},
               cell=cell, cell_mode=cell_mode, q0_mAh=round(q0, 1), q_end_mAh=round(q, 1), vcell=vcell, compress=compress, servo_mode=servo_mode,
               seed=seed, falls=[f for f in falls if f > 1.0], stopped=stopped, wall_s=round(wall, 1), dt=dt, names=NAMES, servo_ids=SID)
    if net is not None:
        it = np.array(net.iters)
        res["solver_iterations"] = dict(mean=round(float(it.mean()), 2), max=int(it.max()), p99=float(np.percentile(it, 99)))
    g = AM.gait_stats(dict(log=L, F=np.zeros((max(nsteps, 1), model.nu)), dt=dt, names=names), list(cmd)) if len(L) else {}
    res["gait"] = {k_: g.get(k_) for k_ in ("vx", "vy", "wz", "track_lin", "track_yaw", "pitch_mean_deg", "pitch_rms_deg", "roll_rms_deg", "z_mean")}
    n = max(acc["n"], 1)
    pct = lambda a: [round(100.0 * float(x) / n, 2) for x in a]          # noqa: E731
    res["servo"] = dict(V_min=[round(float(x), 3) for x in acc["vmin"]], V_mean=[round(float(x) / n, 3) for x in acc["vsum"]],
                        pct_below_6V=pct(acc["lt6"]), pct_below_4V5=pct(acc["lt45"]), ms_below_4V5=[round(float(x) * dt * 1000, 1) for x in acc["lt45"]],
                        ms_below_4V0=[round(float(x) * dt * 1000, 1) for x in acc["lt40"]], sat_pct=pct(acc["sat"]),
                        Im_rms=[round(float(np.sqrt(x / n)), 4) for x in acc["im2"]], Isup_mean=[round(float(x) / n, 4) for x in acc["isup"]],
                        Pcu_W=[round(float(x / n) * SV.R_M, 4) for x in acc["im2"]], Pel_W=[round(float(x) / n, 4) for x in acc["pin"]],
                        err_rms_deg=[round(float(np.degrees(np.sqrt(x / n))), 3) for x in acc["err2"]],
                        tau_limit_mean_Nm=[round(float(x) / n, 4) for x in acc["limsum"]])
    if acc["pk_i"]:
        pk = np.array(acc["pk_i"])
        c100 = np.convolve(pk, np.ones(50) / 50, "valid") if len(pk) > 50 else pk
        res["pack"] = dict(i_mean=round(float(pk.mean()), 3), i_rms=round(float(np.sqrt((pk ** 2).mean())), 3), i_max=round(float(pk.max()), 3),
                           i_max_100ms=round(float(c100.max()), 3), v_term_mean=round(float(np.mean(acc["pk_v"])), 3), v_term_min=round(float(np.min(acc["pk_v"])), 3),
                           bus_mean=round(float(np.mean(acc["bus"])), 3), bus_min=round(float(np.min(acc["bus"])), 3),
                           bec_out_mean=round(float(np.mean(acc["vout"])), 3), bec_out_min=round(float(np.min(acc["vout"])), 3),
                           bec_in_min=round(float(np.min(acc["vbin"])), 3), bec_out_pct_below_6V=round(100 * float((np.array(acc["vout"]) < 6.0).mean()), 2))
    if gd is not None:
        res["guard"] = dict(mode=guard, events=gd.events, n_reads=gd.k)
        res["_guard_medians"] = gd.medians
    if keep_full:
        res["_full"] = {k_: v[:nsteps] for k_, v in FULL.items()}
        res["_fullp"] = {k_: v[:nsteps] for k_, v in FULLP.items()}
        Vf = res["_full"]["V"][k0:]
        if len(Vf):
            res["servo"]["pct_below_6V_50Hz_best_worst"] = [[round(100 * min(sampled_frac(Vf[:, i], dt)), 1), round(100 * max(sampled_frac(Vf[:, i], dt)), 1)] for i in range(14)]
    nbu = min(nbins, nsteps // nb)
    res["_bins"] = {k_: v[:nbu] for k_, v in BIN.items()}
    res["_binsp"] = {k_: v[:nbu] for k_, v in BINP.items()}
    res["_log"] = L
    if WIN:
        res["_windows"] = {"%g-%g" % kk: {k_: np.array(v, np.float32) for k_, v in Wd.items()} for kk, Wd in WIN.items()}
    if supply == "stock":
        res["_trace"] = dict(F=Ftr[:nsteps], W=Wtr[:nsteps], names=np.array(names), dt=dt)
    return res


# ---------------------------------------------------------------------------------------------------------------
def replay(trace, t0=10.0, t1=16.0, corner="typical", extra=None, cell="lab", vcell=3.7, q0=0.0, cell_mode="steady"):
    """open loop: a stock walk's torques and speeds (sim/current_budget.py trace format) through the as-built network,
    with the servo law of sim/power_path_sim.py (commanded volts capped at the local volts, constant power)"""
    F, W, dt = np.asarray(trace["F"], float), np.asarray(trace["W"], float), float(trace["dt"])
    names = [str(x) for x in trace["names"]]
    perm = np.array([names.index(n) for n in NAMES])
    Rm = SV.R_M
    u_cmd = np.clip(F * Rm / SV.KT, -SV.V_TRAIN, SV.V_TRAIN)[:, perm]
    Wn = W[:, perm]
    k0, k1 = int(t0 / dt), int(t1 / dt)
    cellm = p30b.P30B(mode=cell_mode) if cell == "p30b" else None
    net = PN.Net(corner, extra, cell_model=cellm)
    iq = net.iq
    n = k1 - k0
    Vs = np.zeros((n, 14)); P = np.zeros((n, 6))
    for j, k in enumerate(range(k0, k1)):
        uc, ww = u_cmd[k], Wn[k]

        def law(v, uc=uc, ww=ww):
            vl = np.maximum(v, 0.5); ue = np.clip(uc, -vl, vl)
            return np.maximum(ue * (ue - SV.KT * ww) / Rm, 0.0) / vl + iq
        y = net.solve(law, vcell=vcell, qm=q0)
        if cellm is not None:
            cellm.advance(float(y[net.o["i_pack"]]), dt)
        Vs[j] = net.servo_volts(y)
        P[j] = [y[net.o["v_pack"]], y[net.o["i_pack"]], y[net.o["v_bus"]], y[net.o["v_out"]], y[net.o["i_bout"]], y[net.o["v_bin"]]]
    return dict(t=np.arange(k0, k1) * dt, V=Vs, pack=P, names=NAMES, dt=dt, iters=np.array(net.iters))


def replay_summary(r):
    V, P, dt = r["V"], r["pack"], r["dt"]
    i = P[:, 1]
    out = dict(bus_mean=round(float(P[:, 2].mean()), 3), bec_out_mean=round(float(P[:, 3].mean()), 3), pack_i_mean=round(float(i.mean()), 3),
               pack_i_max=round(float(i.max()), 3), pack_i_rms=round(float(np.sqrt((i ** 2).mean())), 3),
               V_min=[round(float(x), 3) for x in V.min(0)], V_mean=[round(float(x), 3) for x in V.mean(0)],
               pct_below_6V=[round(100 * float(x), 2) for x in (V < 6.0).mean(0)], ms_below_4V5=[round(float(x) * dt * 1000, 1) for x in (V < 4.5).sum(0)],
               pct_below_6V_50Hz_best_worst=[[round(100 * min(sampled_frac(V[:, k], dt)), 1), round(100 * max(sampled_frac(V[:, k], dt)), 1)] for k in range(14)])
    w = int(np.argmin(V.min(0)))
    out["worst"] = NAMES[w]
    return out


def save_npz(path, res):
    """heavy outputs (scratch): full traces, bins, the base log"""
    d = {}
    for key in ("_full", "_fullp", "_bins", "_binsp"):
        for k, v in (res.get(key) or {}).items():
            d["%s_%s" % (key.strip("_"), k)] = v
    if "_log" in res:
        d["log"] = np.asarray(res["_log"], np.float32)
    for wk, W in (res.get("_windows") or {}).items():
        for k, v in W.items():
            d["win_%s_%s" % (wk, k)] = v
    if "_guard_medians" in res:
        d["guard_medians"] = np.array([(a, np.nan if b is None else b) for a, b in res["_guard_medians"]], np.float32)
    d["names"] = np.array(NAMES); d["servo_ids"] = np.array(SID)
    np.savez_compressed(path, **d)


def public(res):
    return {k: v for k, v in res.items() if not k.startswith("_")}


# ---------------------------------------------------------------------------------------------------------------
# steps
# ---------------------------------------------------------------------------------------------------------------
def _write(name, obj, git=True):
    os.makedirs(os.path.join(SCR, "json"), exist_ok=True)
    json.dump(obj, open(os.path.join(SCR, "json", name), "w"), indent=1, default=float)
    if git:
        os.makedirs(OUT_GIT, exist_ok=True)
        json.dump(obj, open(os.path.join(OUT_GIT, name), "w"), indent=1, default=float)


def stock_trace(mass, walk, dur=30.0, seed=None):
    """the trained-actuator walk (open-loop input), saved in the sim/current_budget.py trace format"""
    path = os.path.join(SCR, "traces", "trace_%s_%s_s%s_%gs.npz" % (mass, walk, seed, dur))
    if os.path.exists(path):
        d = dict(np.load(path, allow_pickle=True))
        return d, path, json.loads(str(d["meta"]))
    r = run(mass, walk, dur=dur, supply="stock", seed=seed, keep_full=False, guard=None)
    tr = r["_trace"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    meta = dict(gait=r["gait"], falls=r["falls"], servo=r["servo"])
    np.savez_compressed(path, F=tr["F"], W=tr["W"], names=tr["names"], dt=tr["dt"], meta=json.dumps(meta))
    return dict(np.load(path, allow_pickle=True)), path, meta


def _short(r):
    """the numbers the tables use, NAMES order -> dict by joint"""
    s = r["servo"]
    d = dict(falls=r["falls"], gait={k: (None if v is None else round(v, 4)) for k, v in r["gait"].items()}, pack=r.get("pack"),
             guard=[(e["t"], e["event"], e["value"]) for e in (r.get("guard") or {}).get("events", [])],
             wall_s=r["wall_s"], solver=r.get("solver_iterations"))
    for key in ("V_min", "V_mean", "pct_below_6V", "ms_below_4V5", "ms_below_4V0", "sat_pct", "Im_rms", "Pcu_W", "err_rms_deg", "tau_limit_mean_Nm",
                "pct_below_6V_50Hz_best_worst"):
        if key in s:
            d[key] = dict(zip(NAMES, s[key]))
    return d


def check():
    """validation: servo model against the data sheet and the trained actuator, network against ngspice"""
    out = dict(servo_datasheet=SV.datasheet_check())
    dd = json.load(open(p30b.DATA))
    out["p30b"] = dict(check_vs_runtime_thermal_max_abs_mV=dd["check_vs_runtime_thermal_max_abs_mV"], cell=p30b.summary(CELL))
    # 1. the twin at 7.4 V is the trained robot; the stock run is the lab loop
    ident = {}
    for mass in ("trained", "ours"):
        a = run(mass, "backlash", dur=16.0, supply="stock", keep_full=True, guard=None)
        b = run(mass, "backlash", dur=16.0, supply="fixed", fixed_v=7.4, keep_full=True, guard=None)
        folder = model_folder(mass)
        lab = AM.run(folder, SCENES["backlash"], CB.sched_const([0.15, 0, 0, 0, 0, 0, 0]), 16.0)
        names = list(lab["names"]); perm = [names.index(n) for n in NAMES]
        ident[mass] = dict(fixed_7V4_vs_stock_max_abs_dF_Nm=float(np.abs(a["_full"]["F"] - b["_full"]["F"]).max()),
                           fixed_7V4_vs_stock_max_abs_dlog=float(np.abs(a["_log"] - b["_log"]).max()),
                           stock_vs_lab_loop_max_abs_dF_Nm=float(np.abs(a["_trace"]["F"] - lab["F"].astype(np.float32)).max()),
                           stock_vs_lab_loop_max_abs_dW=float(np.abs(a["_trace"]["W"] - lab["W"].astype(np.float32)).max()),
                           stock_gait=a["gait"])
        print("identity", mass, ident[mass], flush=True)
    out["identity"] = ident
    # 2. open-loop replay through the Python network against the lab's ngspice as-built run on the same traces
    rep = []
    _mk(os.path.join(SCR, "ngspice"))
    for mass in ("trained", "ours"):
        tr, path, meta = stock_trace(mass, "backlash", dur=16.0)
        for pk in ("full", "nominal", "low"):
            for corner in ("typical", "high-side"):
                ex = dict(PN.CORNERS[corner])
                tag = "ng_%s_%s_%s" % (mass, pk, corner)
                ng = PN.PF.run("check " + tag, path, 10.0, 16.0, LAB_VCELL[pk], PN.PF.OPTIONS["ab"], "high-side", extra=ex, save=tag,
                               save_dir=os.path.join(SCR, "ngspice"))
                nv = np.load(os.path.join(SCR, "ngspice", tag + ".npz"))
                py = replay(tr, 10.0, 16.0, corner=corner, cell="lab", vcell=LAB_VCELL[pk])
                ps = replay_summary(py)
                nn = [str(x) for x in nv["names"]]
                dv = max(float(np.abs(np.interp(py["t"], nv["t"] + 10.0, nv["V"][nn.index(n)]) - py["V"][:, i]).max()) for i, n in enumerate(NAMES))
                row = dict(mass=mass, pack=pk, corner=corner, max_abs_dV_2ms_points=round(dv, 5),
                           ngspice=dict(bus_mean=ng["bus_V_mean"], bec_out_mean=ng["bec_out_V_mean"], pack_mean=ng["pack_A_mean"], pack_max=ng["pack_A_max"],
                                        pack_rms=ng["pack_A_rms"], worst=ng["worst_servo"], worst_min=ng["worst_servo_V_min"],
                                        knees_pct6=[ng["servo_pct_below_6V"]["left_knee"], ng["servo_pct_below_6V"]["right_knee"]],
                                        ankle_pct6=ng["ankle_pct_below_6V"], head_roll_pct6=ng["servo_pct_below_6V"]["head_roll"]),
                           python=dict(bus_mean=ps["bus_mean"], bec_out_mean=ps["bec_out_mean"], pack_mean=ps["pack_i_mean"], pack_max=ps["pack_i_max"],
                                       pack_rms=ps["pack_i_rms"], worst=ps["worst"], worst_min=min(ps["V_min"]),
                                       knees_pct6=[ps["pct_below_6V"][NAMES.index("left_knee")], ps["pct_below_6V"][NAMES.index("right_knee")]],
                                       ankle_pct6=max(ps["pct_below_6V"][NAMES.index("left_ankle")], ps["pct_below_6V"][NAMES.index("right_ankle")]),
                                       head_roll_pct6=ps["pct_below_6V"][NAMES.index("head_roll")]))
                rep.append(row)
                print("replay", mass, pk, corner, "max dV %.4f V" % dv, row["ngspice"]["worst"], row["ngspice"]["worst_min"], row["python"]["worst_min"],
                      "knees", row["ngspice"]["knees_pct6"], row["python"]["knees_pct6"], flush=True)
    out["replay_vs_ngspice"] = rep
    # 3. the closed loop's own currents through ngspice (lab cells, nominal, both corners)
    same = []
    for corner in ("typical", "high-side"):
        r = run("ours", "backlash", dur=16.0, supply="net", corner=corner, cell="lab", vcell=3.7, keep_full=True, guard=None)
        dt = r["dt"]; k0, k1 = int(10.0 / dt), int(16.0 / dt)
        I = r["_full"]["Isup"][k0:k1].astype(float); t = np.arange(k0, k1) * dt
        tt, Vng, vout, vbus = PN.ngspice_same_currents(t, I, corner=corner, vcell=3.7)
        Vpy = r["_full"]["V"][k0:k1].astype(float)
        dv = max(float(np.abs(np.interp(t - t[0], tt, Vng[i]) - Vpy[:, i]).max()) for i in range(14))
        dvo = float(np.abs(np.interp(t - t[0], tt, vout) - r["_fullp"]["v_out"][k0:k1]).max())
        same.append(dict(corner=corner, max_abs_dV_servo=round(dv, 5), max_abs_dV_bec_out=round(dvo, 5), n_points=int(len(t))))
        print("same currents", corner, same[-1], flush=True)
    out["same_currents_vs_ngspice"] = same
    _write("check.json", out)
    return out


def states(walks=("backlash", "plain"), seeds=(None, 1), corners=("typical", "high-side"), sts=("full", "nominal", "d16", "low"), mass="ours", dur=30.0):
    """the walk at fixed pack states (charge frozen): closed loop against open loop, both corners"""
    rows = []
    for walk in walks:
        for seed in seeds:
            tr, path, meta = stock_trace(mass, walk, dur=dur, seed=seed)
            fx = run(mass, walk, dur=dur, supply="fixed", fixed_v=7.2, seed=seed, keep_full=False, guard=None)
            rows.append(dict(kind="reference", walk=walk, seed=seed, case="stock (trained actuators)", **{"gait": meta["gait"], "falls": meta["falls"]}))
            rows.append(dict(kind="reference", walk=walk, seed=seed, case="every servo at 7.2 V", **_short(fx)))
            print("ref", walk, seed, "stock", round(meta["gait"]["track_lin"], 3), "7.2 V", round(fx["gait"]["track_lin"], 3), flush=True)
            for st in sts:
                for corner in corners:
                    r = run(mass, walk, dur=dur, supply="net", corner=corner, cell="p30b", q0=STATES[st], compress=0.0, seed=seed, keep_full=True,
                            guard="shadow", label="%s %s %s" % (walk, st, corner))
                    save_npz(os.path.join(SCR, "states", "closed_%s_%s_%s_s%s.npz" % (walk, st, corner, seed)), r) if _mk(os.path.join(SCR, "states")) else None
                    op = replay(tr, 4.0, dur, corner=corner, cell="p30b", q0=STATES[st])
                    os_ = replay_summary(op)
                    row = dict(kind="pack state", walk=walk, seed=seed, state=st, corner=corner, q_mAh=round(STATES[st], 1), soc=round(CELL.soc(STATES[st]), 3),
                               ocv_cell=round(CELL.ocv(STATES[st]), 3), closed=_short(r),
                               open=dict(V_min=dict(zip(NAMES, os_["V_min"])), V_mean=dict(zip(NAMES, os_["V_mean"])), pct_below_6V=dict(zip(NAMES, os_["pct_below_6V"])),
                                         ms_below_4V5=dict(zip(NAMES, os_["ms_below_4V5"])), bus_mean=os_["bus_mean"], bec_out_mean=os_["bec_out_mean"],
                                         pack_i_mean=os_["pack_i_mean"], pack_i_max=os_["pack_i_max"], pack_i_rms=os_["pack_i_rms"], worst=os_["worst"],
                                         pct_below_6V_50Hz_best_worst=dict(zip(NAMES, os_["pct_below_6V_50Hz_best_worst"]))))
                    rows.append(row)
                    c = row["closed"]
                    print("%-8s s%-4s %-7s %-9s closed: falls %s track %.3f knees min %.2f/%.2f <6V %.1f/%.1f %% | open: knees min %.2f/%.2f <6V %.1f/%.1f %% (%.0f s)" % (
                        walk, seed, st, corner, c["falls"], c["gait"]["track_lin"] or 0, c["V_min"]["left_knee"], c["V_min"]["right_knee"],
                        c["pct_below_6V"]["left_knee"], c["pct_below_6V"]["right_knee"], row["open"]["V_min"]["left_knee"], row["open"]["V_min"]["right_knee"],
                        row["open"]["pct_below_6V"]["left_knee"], row["open"]["pct_below_6V"]["right_knee"], r["wall_s"]), flush=True)
    _write("states_%s.json" % "_".join(walks), rows)
    return rows


def _mk(d):
    os.makedirs(d, exist_ok=True)
    return True


def session(walk="backlash", corner="typical", extra=None, tag=None, dur=3000.0, cell_mode="steady", servo_mode="bam"):
    """a session that runs the pack down from a full charge, no time compression; the D16 guard in shadow mode.
    Stops at a fall or when the cells reach OCV 3.30 V (past the guard's hard stop)."""
    tag = tag or "%s_%s" % (walk, corner)
    wins = [(60.0, 80.0)] + [(float(a), float(a) + 20.0) for a in range(300, int(dur), 300)]
    r = run("ours", walk, dur=dur, supply="net", corner=corner, extra=extra, cell="p30b", q0=0.0, compress=1.0, guard="shadow", keep_full=False,
            bin_s=0.1, stop_q=STATES["low"], stop_on_fall=True, label="session " + tag, full_windows=wins, progress=60.0, cell_mode=cell_mode,
            servo_mode=servo_mode)
    _mk(os.path.join(SCR, "session"))
    save_npz(os.path.join(SCR, "session", "session_%s.npz" % tag), r)
    summ = session_summary(r, tag)
    _write("session_%s.json" % tag, summ)
    session_csv(r, tag)
    return summ


def _moving_speed(B, win_s=20.0):
    """forward speed (heading frame) over a moving window, from the 0.1 s bins: distance along the mean heading / time"""
    t, x, y, yaw = B["t_end"].astype(float), B["x"].astype(float), B["y"].astype(float), np.unwrap(B["yaw"].astype(float))
    n = max(1, int(round(win_s / float(t[1] - t[0]))))
    v = np.full(len(t), np.nan)
    for i in range(n, len(t)):
        dx, dy = x[i] - x[i - n], y[i] - y[i - n]
        h = 0.5 * (yaw[i] + yaw[i - n])
        v[i] = (np.cos(h) * dx + np.sin(h) * dy) / (t[i] - t[i - n])
    return t, v


def session_summary(r, tag):
    B, BP = r["_bins"], r["_binsp"]
    t, v20 = _moving_speed(BP, 20.0)
    ref_sel = (t >= 30.0) & (t <= 70.0)                     # 20 s windows ending 30 to 70 s: walking 10 to 70 s, full pack
    v_ref = float(np.nanmean(v20[ref_sel])) if ref_sel.any() else float("nan")
    cmd = 0.15
    below = np.where((t > 70.0) & (v20 < 0.85 * v_ref))[0]
    # first time the 20 s speed stays under 85 % of the full-charge speed for 60 s
    first_bad = None
    for i in below:
        j = np.where((t >= t[i]) & (t <= t[i] + 60.0))[0]
        if len(j) and np.all(v20[j] < 0.85 * v_ref):
            first_bad = float(t[i]); break
    ev = (r.get("guard") or {}).get("events", [])
    def first(name):
        x = [e for e in ev if e["event"] == name]
        return (x[0]["t"], x[0]["value"]) if x else (None, None)
    ws, hs = first("walk_stop"), first("hard_stop")
    def at(tq):
        if tq is None: return None
        i = int(np.clip(np.searchsorted(t, tq), 0, len(t) - 1))
        return dict(t_s=round(float(t[i]), 1), minute=round(float(t[i]) / 60, 2), q_mAh=round(float(BP["q_mAh"][i]), 1), soc=round(CELL.soc(float(BP["q_mAh"][i])), 3),
                    ocv_cell=round(CELL.ocv(float(BP["q_mAh"][i])), 3), v_pack=round(float(BP["v_pack_mean"][i]), 3),
                    speed_20s=None if np.isnan(v20[i]) else round(float(v20[i]), 4), speed_rel_full=None if np.isnan(v20[i]) else round(float(v20[i] / v_ref), 3))
    # minute table: per minute mean speed, pack, bus, the lowest servo per joint group
    rows = []
    for mnt in range(int(t[-1] // 60) + 1):
        sel = (t > mnt * 60) & (t <= (mnt + 1) * 60)
        if sel.sum() < 10: continue
        Vm, Vn = B["V_mean"][sel], B["V_min"][sel]
        rows.append(dict(minute=mnt + 1, q_mAh=round(float(BP["q_mAh"][sel][-1]), 1), soc=round(CELL.soc(float(BP["q_mAh"][sel][-1])), 3),
                         speed=None if np.all(np.isnan(v20[sel])) else round(float(np.nanmean(v20[sel])), 4),
                         v_pack=round(float(BP["v_pack_mean"][sel].mean()), 3), i_pack=round(float(BP["i_pack_mean"][sel].mean()), 3),
                         v_bus=round(float(BP["v_bus_mean"][sel].mean()), 3), v_bec_out=round(float(BP["v_bec_out_mean"][sel].mean()), 3),
                         median_servo_v=round(float(np.median(Vm.mean(0))), 3),
                         knee_min=round(float(Vn[:, [NAMES.index("left_knee"), NAMES.index("right_knee")]].min()), 3),
                         ankle_min=round(float(Vn[:, [NAMES.index("left_ankle"), NAMES.index("right_ankle")]].min()), 3),
                         head_roll_min=round(float(Vn[:, NAMES.index("head_roll")].min()), 3),
                         knee_sat_pct=round(100 * float(B["sat_frac"][sel][:, [NAMES.index("left_knee"), NAMES.index("right_knee")]].mean()), 1),
                         fallen=bool(BP["fallen"][sel].max() > 0)))
    return dict(tag=tag, walk=r["walk"], corner=r["corner"], extra=r["extra"], cell_mode=r["cell_mode"], servo_mode=r["servo_mode"], compress=r["compress"],
                dur_s=r["dur_s"], wall_s=r["wall_s"], stopped=r["stopped"], falls=r["falls"], q_end_mAh=r["q_end_mAh"],
                full_charge_speed=round(v_ref, 4), full_charge_track=round(v_ref / cmd, 3),
                walk_degraded=at(first_bad), guard_walk_stop=at(ws[0]), guard_walk_stop_value=ws[1], guard_hard_stop=at(hs[0]), guard_hard_stop_value=hs[1],
                guard_events=ev, solver=r.get("solver_iterations"), minutes=rows)


def session_csv(r, tag, bin_out_s=5.0):
    """5 s bins for the twin/thermal job and the plots (format: ELECTROMECH_TWIN.md 'Trace format')"""
    B, BP = r["_bins"], r["_binsp"]
    t = BP["t_end"].astype(float)
    nb = int(round(bin_out_s / float(t[1] - t[0])))
    nbin = len(t) // nb
    _, v20 = _moving_speed(BP, 20.0)
    cols = ["t_s", "q_mAh", "soc", "v_pack", "i_pack", "v_bus", "v_bec_out", "i_bec_out", "speed_20s", "fallen"]
    per = [("V_mean", "v"), ("V_min", "vmin"), ("Isup_mean", "isup"), ("Im_rms", "im_rms"), ("Pcu_mean", "pcu"), ("sat_frac", "sat")]
    hdr = cols + ["%s_%d" % (p, sid) for _, p in per for sid in SID]
    lines = ["# twin/electromech/em_twin.py session %s (sim pass only); 5 s bins; columns in ELECTROMECH_TWIN.md 'Trace format'; servo columns end in the servo ID" % tag,
             ",".join(hdr)]
    for j in range(nbin):
        s = slice(j * nb, (j + 1) * nb)
        row = [t[s][-1], BP["q_mAh"][s][-1], CELL.soc(float(BP["q_mAh"][s][-1])), BP["v_pack_mean"][s].mean(), BP["i_pack_mean"][s].mean(), BP["v_bus_mean"][s].mean(),
               BP["v_bec_out_mean"][s].mean(), BP["i_bec_out_mean"][s].mean(), np.nanmean(v20[s]) if not np.all(np.isnan(v20[s])) else np.nan, BP["fallen"][s].max()]
        for key, _ in per:
            X = B[key][s]
            if key == "V_min":
                v = X.min(0)
            elif key == "Im_rms":
                v = np.sqrt((X.astype(float) ** 2).mean(0))
            else:
                v = X.mean(0)
            row += list(v)
        lines.append(",".join("%.4g" % x if np.isfinite(x) else "" for x in row))
    open(os.path.join(OUT_GIT, "session_%s.csv" % tag), "w").write("\n".join(lines) + "\n")


def sweep(walk="backlash", seeds=(None,), dur=30.0):
    """hop resistance at the TEST_PLAN 5 bands and the BEC dropout; plus the two model brackets (servo firmware, cell pulses)"""
    cases = [("baseline (typical corner, hop 27.6 mOhm, dropout 0.30 V)", "typical", {}, {}),
             ("hop 28 mOhm per conductor (TEST_PLAN 5 pass limit)", "typical", PN.hop_extra(28.0), {}),
             ("hop 40 mOhm per conductor (TEST_PLAN 5 warn limit)", "typical", PN.hop_extra(40.0), {}),
             ("BEC dropout 0.10 V", "typical", dict(BEC_DROP=0.10), {}),
             ("BEC dropout 0.60 V", "typical", dict(BEC_DROP=0.60), {}),
             ("high-side corner, dropout 0.10 V", "high-side", dict(BEC_DROP=0.10), {}),
             ("high-side corner, dropout 0.30 V", "high-side", {}, {}),
             ("high-side corner, dropout 0.60 V", "high-side", dict(BEC_DROP=0.60), {}),
             ("servo firmware compensates the bus volts (mode comp)", "typical", {}, dict(servo_mode="comp")),
             ("cell pulses see only the 8 mOhm AC impedance (cell mode ac)", "typical", {}, dict(cell_mode="ac"))]
    rows = []
    for st in ("nominal", "d16"):
        for seed in seeds:
            tr, path, meta = stock_trace("ours", walk, dur=dur, seed=seed)
            for name, corner, ex, kw in cases:
                r = run("ours", walk, dur=dur, supply="net", corner=corner, extra=ex, cell="p30b", q0=STATES[st], compress=0.0, seed=seed, keep_full=True,
                        guard="shadow", label=name, **kw)
                op = replay_summary(replay(tr, 4.0, dur, corner=corner, extra=ex, cell="p30b", q0=STATES[st], cell_mode=kw.get("cell_mode", "steady")))
                row = dict(case=name, state=st, walk=walk, seed=seed, corner=corner, extra=ex, kw=kw, closed=_short(r),
                           open=dict(V_min=dict(zip(NAMES, op["V_min"])), pct_below_6V=dict(zip(NAMES, op["pct_below_6V"])), bus_mean=op["bus_mean"],
                                     bec_out_mean=op["bec_out_mean"], worst=op["worst"]))
                rows.append(row)
                c = row["closed"]
                print("%-60s %-7s closed falls %s track %.3f knees <6V %.1f/%.1f %% ankles %.1f/%.1f head roll %.1f | open knees %.1f/%.1f ankles %.1f/%.1f" % (
                    name, st, c["falls"], c["gait"]["track_lin"] or 0, c["pct_below_6V"]["left_knee"], c["pct_below_6V"]["right_knee"], c["pct_below_6V"]["left_ankle"],
                    c["pct_below_6V"]["right_ankle"], c["pct_below_6V"]["head_roll"], row["open"]["pct_below_6V"]["left_knee"], row["open"]["pct_below_6V"]["right_knee"],
                    row["open"]["pct_below_6V"]["left_ankle"], row["open"]["pct_below_6V"]["right_ankle"]), flush=True)
    _write("sweep_%s.json" % walk, rows)
    return rows


# the rows of sim/POWER_PATH_SIM.md 'As built' (ngspice replay, 10 to 16 s, lab cells): worst servo min, knees, head roll, ankle
ASBUILT_DOC = {
    ("trained", "full", "high-side"): dict(bus=7.72, bec=7.17, worst=("left_knee", 5.91), ankle=0.0, knees=(0.2, 0.0), head_roll=0.0),
    ("trained", "full", "typical"): dict(bus=7.89, bec=7.20, worst=("left_knee", 6.52), ankle=0.0, knees=(0.0, 0.0), head_roll=0.0),
    ("trained", "nominal", "high-side"): dict(bus=6.69, bec=6.37, worst=("head_roll", 4.88), ankle=19.3, knees=(27.8, 27.9), head_roll=32.6),
    ("trained", "nominal", "typical"): dict(bus=6.86, bec=6.54, worst=("left_knee", 5.58), ankle=4.8, knees=(5.6, 7.9), head_roll=5.1),
    ("trained", "low", "high-side"): dict(bus=5.87, bec=5.55, worst=("head_roll", 4.19), ankle=100.0, knees=(100.0, 100.0), head_roll=100.0),
    ("trained", "low", "typical"): dict(bus=6.04, bec=5.72, worst=("right_knee", 4.82), ankle=100.0, knees=(100.0, 99.9), head_roll=100.0),
    ("ours", "full", "high-side"): dict(bus=7.70, bec=7.16, worst=("left_knee", 5.95), ankle=0.0, knees=(0.2, 0.0), head_roll=0.1),
    ("ours", "full", "typical"): dict(bus=7.87, bec=7.20, worst=("left_knee", 6.55), ankle=0.0, knees=(0.0, 0.0), head_roll=0.0),
    ("ours", "nominal", "high-side"): dict(bus=6.67, bec=6.35, worst=("head_roll", 4.91), ankle=21.4, knees=(31.1, 30.6), head_roll=33.5),
    ("ours", "nominal", "typical"): dict(bus=6.84, bec=6.52, worst=("left_knee", 5.61), ankle=6.4, knees=(6.4, 9.8), head_roll=6.8),
    ("ours", "low", "high-side"): dict(bus=5.85, bec=5.53, worst=("head_roll", 4.07), ankle=100.0, knees=(100.0, 100.0), head_roll=100.0),
    ("ours", "low", "typical"): dict(bus=6.02, bec=5.70, worst=("head_roll", 4.87), ankle=100.0, knees=(100.0, 100.0), head_roll=100.0),
}


def asbuilt_table():
    """the POWER_PATH_SIM.md 'As built' cases with the loop closed: same network, same lab cells (OCV 4.2 / 3.7 / 3.3 V
    per cell with the corner's Rc), same 10 to 16 s window of the backlash walk, same masses"""
    rows = []
    for mass in ("trained", "ours"):
        for pk in ("full", "nominal", "low"):
            for corner in ("typical", "high-side"):
                r = run(mass, "backlash", dur=16.0, supply="net", corner=corner, cell="lab", vcell=LAB_VCELL[pk], t_stats=10.0, keep_full=True, guard=None)
                s = _short(r)
                doc = ASBUILT_DOC[(mass, pk, corner)]
                w = min(NAMES, key=lambda n: s["V_min"][n])
                row = dict(mass=mass, pack=pk, corner=corner, doc=doc,
                           closed=dict(bus=r["pack"]["bus_mean"], bec=r["pack"]["bec_out_mean"], worst=(w, s["V_min"][w]),
                                       ankle=max(s["pct_below_6V"]["left_ankle"], s["pct_below_6V"]["right_ankle"]),
                                       knees=(s["pct_below_6V"]["left_knee"], s["pct_below_6V"]["right_knee"]), head_roll=s["pct_below_6V"]["head_roll"],
                                       any_ms_below_4V5=max(s["ms_below_4V5"].values()), pack=r["pack"], falls=r["falls"], gait=s["gait"],
                                       V_min=s["V_min"], pct_below_6V=s["pct_below_6V"], sat_pct=s["sat_pct"]))
                rows.append(row)
                print("as built %-7s %-7s %-9s doc: %s %.2f V, knees %s, ankle %.1f, head roll %.1f | closed: %s %.2f V, knees (%.1f, %.1f), ankle %.1f, head roll %.1f, bus %.2f (doc %.2f), falls %s" % (
                    mass, pk, corner, doc["worst"][0], doc["worst"][1], doc["knees"], doc["ankle"], doc["head_roll"], w, s["V_min"][w],
                    row["closed"]["knees"][0], row["closed"]["knees"][1], row["closed"]["ankle"], row["closed"]["head_roll"], row["closed"]["bus"], doc["bus"], r["falls"]), flush=True)
    _write("asbuilt_closed_loop.json", rows)
    return rows


def _f(x, fmt="%.2f"):
    return "-" if x is None else fmt % x


def tables(detail_walks=("backlash",)):
    """markdown tables for ELECTROMECH_TWIN.md from the JSON outputs (printed; nothing is typed by hand)"""
    J = os.path.join(SCR, "json")
    out = []
    P = out.append
    ck = json.load(open(os.path.join(J, "check.json")))
    P("### Validation\n")
    P("| Check | Result |\n|---|---|")
    r = ck["servo_datasheet"]["ratio 6.0 / 7.4"]
    P("| Servo model against the C001 data sheet, 6.0 V over 7.4 V | no-load speed %.3f (data sheet %.3f), stall current %.3f (%.3f), stall torque %.3f (%.3f, +/-10 %% tolerance) |" % (
        r["model_speed"], r["datasheet_speed"], r["model_stall_A"], r["datasheet_stall_A"], r["model_stall"], r["datasheet_stall"]))
    for mass, d in ck["identity"].items():
        P("| Twin with every servo at 7.4 V against the trained actuators, %s, 16 s backlash walk | largest torque difference %.1f Nm, largest pose difference %.1f |" % (
            "trained mass" if mass == "trained" else "our build", d["fixed_7V4_vs_stock_max_abs_dF_Nm"], d["fixed_7V4_vs_stock_max_abs_dlog"]))
        P("| Stock twin run against the lab loop (sim/added_mass_sim.py run(), the E5 / C8 traces), %s | largest torque difference %.1f Nm, speed %.1f rad/s |" % (
            "trained mass" if mass == "trained" else "our build", d["stock_vs_lab_loop_max_abs_dF_Nm"], d["stock_vs_lab_loop_max_abs_dW"]))
    dv = [x["max_abs_dV_2ms_points"] for x in ck["replay_vs_ngspice"]]
    P("| Python network against ngspice (sim/power_fix.py option ab), the same open-loop replay, 12 cases (2 masses x full/nominal/low x 2 corners), 3000 points each | largest servo volts difference %.1f mV (median of the cases %.1f mV); lowest servo identical in all 12 cases |" % (
        1000 * max(dv), 1000 * float(np.median(dv))))
    for x in ck["same_currents_vs_ngspice"]:
        P("| The closed loop's own 14 servo currents fed to ngspice as current sources, our build, nominal (lab cells), %s corner, 3000 points | largest servo volts difference %.2f mV, BEC output %.2f mV |" % (
            x["corner"], 1000 * x["max_abs_dV_servo"], 1000 * x["max_abs_dV_bec_out"]))
    P("| P30B data sheet digitization against sim/runtime_thermal.py, 25 points | largest difference %.0f mV |" % ck["p30b"]["check_vs_runtime_thermal_max_abs_mV"])
    P("")
    P("Replay against ngspice, per case (time under 6.0 V counted on the 2 ms grid here, by ngspice time steps there):\n")
    P("| Trace, pack, corner | ngspice: lowest servo; knees L / R; ankle; head roll | Python: same | largest difference |\n|---|---|---|---|")
    for x in ck["replay_vs_ngspice"]:
        n, p = x["ngspice"], x["python"]
        P("| %s, %s, %s | %s %.3f V; %.1f / %.1f %%; %.1f %%; %.1f %% | %s %.3f V; %.1f / %.1f %%; %.1f %%; %.1f %% | %.1f mV |" % (
            "trained mass" if x["mass"] == "trained" else "our build", x["pack"], x["corner"], n["worst"].replace("_", " "), n["worst_min"], n["knees_pct6"][0], n["knees_pct6"][1],
            n["ankle_pct6"], n["head_roll_pct6"], p["worst"].replace("_", " "), p["worst_min"], p["knees_pct6"][0], p["knees_pct6"][1], p["ankle_pct6"], p["head_roll_pct6"],
            1000 * x["max_abs_dV_2ms_points"]))
    # as built, closed loop
    f = os.path.join(J, "asbuilt_closed_loop.json")
    if os.path.exists(f):
        P("\n### The POWER_PATH_SIM.md 'As built' cases with the loop closed (lab cells, backlash walk 10 to 16 s)\n")
        P("| Trace, pack, corner | Open loop (POWER_PATH_SIM.md): lowest servo; knees L / R; ankles; head roll under 6.0 V | Closed loop (twin): same | Closed loop: forward speed / command (stock walk) | Torso pitch | Falls |\n|---|---|---|---|---|---|")
        stock = {m: ck["identity"][m]["stock_gait"]["track_lin"] for m in ck["identity"]}
        for x in json.load(open(f)):
            d, c = x["doc"], x["closed"]
            P("| %s, %s (%.1f V), %s | %s %.2f V; %.1f / %.1f %%; %.1f %%; %.1f %% | %s %.2f V; %.1f / %.1f %%; %.1f %%; %.1f %% | %.2f (%.2f) | %+.1f deg | %s |" % (
                "trained mass" if x["mass"] == "trained" else "our build", x["pack"], 2 * LAB_VCELL[x["pack"]], x["corner"], d["worst"][0].replace("_", " "), d["worst"][1],
                d["knees"][0], d["knees"][1], d["ankle"], d["head_roll"], c["worst"][0].replace("_", " "), c["worst"][1], c["knees"][0], c["knees"][1], c["ankle"],
                c["head_roll"], c["gait"]["track_lin"], stock[x["mass"]], c["gait"]["pitch_mean_deg"], "none" if not c["falls"] else c["falls"]))
    # pack states with the P30B
    for walk in ("backlash", "plain"):
        f = os.path.join(J, "states_%s.json" % walk)
        if not os.path.exists(f):
            continue
        rows = json.load(open(f))
        refs = [r for r in rows if r["kind"] == "reference"]
        st_rows = [r for r in rows if r["kind"] == "pack state"]
        stock_tr = np.mean([r["gait"]["track_lin"] for r in refs if r["case"].startswith("stock")])
        v72_tr = np.mean([r["gait"]["track_lin"] for r in refs if r["case"].startswith("every servo")])
        seeds = sorted({str(r["seed"]) for r in st_rows})
        P("\n### Pack states, %s walk, our build, 2S P30B (charge held), mean of %d start seeds, 4 to 30 s\n" % ("backlash-model" if walk == "backlash" else "plain-model", len(seeds)))
        P("Reference: trained actuators (no supply effect) %.3f of the command; every servo at a steady 7.2 V %.3f.\n" % (stock_tr, v72_tr))
        P("| State | Corner | Pack: terminal mean; BEC out mean | Closed loop: speed / command (share of stock); pitch; falls | Lowest servo, closed / open | Knees L / R under 6 V, closed / open | Ankles (worse) under 6 V, closed / open | Head roll under 6 V, closed / open |\n|---|---|---|---|---|---|---|---|")
        for st in ("full", "nominal", "d16", "low"):
            for corner in ("typical", "high-side"):
                rs = [r for r in st_rows if r["state"] == st and r["corner"] == corner]
                if not rs:
                    continue
                m = lambda fn: float(np.mean([fn(r) for r in rs]))       # noqa: E731
                tr = m(lambda r: r["closed"]["gait"]["track_lin"] or 0.0)
                falls = sum(1 for r in rs if r["closed"]["falls"])
                lc = m(lambda r: min(r["closed"]["V_min"].values())); lo = m(lambda r: min(r["open"]["V_min"].values()))
                k = lambda loop, j: m(lambda r: r[loop]["pct_below_6V"][j])  # noqa: E731
                a = lambda loop: m(lambda r: max(r[loop]["pct_below_6V"]["left_ankle"], r[loop]["pct_below_6V"]["right_ankle"]))  # noqa: E731
                P("| %s | %s | %.2f V; %.2f V | %.3f (%.0f %%); %+.1f deg; %d of %d | %.2f / %.2f V | %.1f / %.1f %%, %.1f / %.1f %% | %.1f %%, %.1f %% | %.1f %%, %.1f %% |" % (
                    STATE_TEXT[st], corner, m(lambda r: r["closed"]["pack"]["v_term_mean"]), m(lambda r: r["closed"]["pack"]["bec_out_mean"]), tr, 100 * tr / stock_tr,
                    m(lambda r: r["closed"]["gait"]["pitch_mean_deg"]), falls, len(rs), lc, lo, k("closed", "left_knee"), k("closed", "right_knee"),
                    k("open", "left_knee"), k("open", "right_knee"), a("closed"), a("open"), k("closed", "head_roll"), k("open", "head_roll")))
        if walk not in detail_walks:
            continue
        for corner in ("typical", "high-side"):
            P("\nEvery servo, %s walk, %s corner, mean of the seeds: lowest volts and time under 6.0 V, closed loop / open loop\n" % (walk, corner))
            P("| Servo (ID) | " + " | ".join(STATE_TEXT[s].split(" (")[0] for s in ("full", "nominal", "d16", "low")) + " |\n|---|---|---|---|---|")
            for j in NAMES:
                cells = []
                for st in ("full", "nominal", "d16", "low"):
                    rs = [r for r in st_rows if r["state"] == st and r["corner"] == corner]
                    if not rs:
                        cells.append("-"); continue
                    m = lambda loop, key: float(np.mean([r[loop][key][j] for r in rs]))   # noqa: E731
                    cells.append("%.2f / %.2f V; %.1f / %.1f %%" % (m("closed", "V_min"), m("open", "V_min"), m("closed", "pct_below_6V"), m("open", "pct_below_6V")))
                P("| %s (%d) | %s |" % (j.replace("_", " "), PN.SERVO_ID[j], " | ".join(cells)))
        P("\nKnees and ankles in the closed loop (mean of the seeds):\n")
        P("| State | Corner | Joint | Volts mean / min | Torque limit mean (Nm; 3.23 at 7.4 V) | Time at the limit | Tracking error RMS | Motor current RMS | Copper loss |\n|---|---|---|---|---|---|---|---|---|")
        for st in ("full", "nominal", "d16", "low"):
            for corner in ("typical", "high-side"):
                rs = [r for r in st_rows if r["state"] == st and r["corner"] == corner]
                if not rs:
                    continue
                for j in ("left_knee", "right_knee", "left_ankle", "right_ankle"):
                    m = lambda key: float(np.mean([r["closed"][key][j] for r in rs]))   # noqa: E731
                    P("| %s | %s | %s | %.2f / %.2f V | %.2f | %.1f %% | %.1f deg | %.2f A | %.2f W |" % (
                        st, corner, j.replace("_", " "), m("V_mean"), m("V_min"), m("tau_limit_mean_Nm"), m("sat_pct"), m("err_rms_deg"), m("Im_rms"), m("Pcu_W")))
    # sessions
    for tag in ("backlash_typical", "backlash_high-side", "plain_typical", "plain_high-side"):
        f = os.path.join(J, "session_%s.json" % tag)
        if not os.path.exists(f):
            continue
        s = json.load(open(f))
        P("\n### Session %s\n" % tag.replace("_", ", "))
        P("Full-charge speed %.4f m/s (%.3f of the command). Ran %.1f min of walking, stopped by: %s. Falls: %s." % (
            s["full_charge_speed"], s["full_charge_track"], s["dur_s"] / 60, s["stopped"], s["falls"] or "none"))
        for key, txt in (("walk_degraded", "walk under 85 % of the full-charge speed (20 s windows, held 60 s)"), ("guard_walk_stop", "D16 guard walk stop"),
                         ("guard_hard_stop", "D16 guard hard stop (walking floor 5.4 V)")):
            a = s.get(key)
            if a:
                P("- %s: minute %.1f, %.0f mAh, SOC %.0f %%, cell OCV %.3f V, pack %.2f V under load, speed %s of full" % (
                    txt, a["minute"], a["q_mAh"], 100 * a["soc"], a["ocv_cell"], a["v_pack"], _f(a["speed_rel_full"], "%.2f")))
            else:
                P("- %s: not reached" % txt)
        P("\n| Minute | Charge used (mAh) | SOC | Speed (m/s) | Pack V | Pack A | BEC out V | Servo median V | Knee min V | Ankle min V | Head roll min V | Knee at limit |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
        for row in s["minutes"]:
            if row["minute"] % 2 and row["minute"] != len(s["minutes"]):
                continue
            P("| %d | %.0f | %.0f %% | %s | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.0f %% |" % (
                row["minute"], row["q_mAh"], 100 * row["soc"], _f(row["speed"], "%.3f"), row["v_pack"], row["i_pack"], row["v_bec_out"], row["median_servo_v"],
                row["knee_min"], row["ankle_min"], row["head_roll_min"], row["knee_sat_pct"]))
    # pushes (the C8 push case with the loop closed)
    f = os.path.join(J, "pushes_plain.json")
    if os.path.exists(f):
        rows = json.load(open(f))
        ref = [r for r in rows if r["kind"] == "reference"]
        P("\n### 15 N pushes every 3 s (the C8 push case, plain walk), our build, P30B, closed loop, %d seeds\n" % len(ref))
        P("Trained actuators: falls in %d of %d runs, speed / command %.3f.\n" % (sum(1 for r in ref if r["falls"]), len(ref), np.mean([r["gait"]["track_lin"] for r in ref])))
        P("| State | Corner | Runs that fell | Speed / command (mean) | Lowest servo (mean of the runs) |\n|---|---|---|---|---|")
        for st in ("full", "nominal", "d16"):
            for corner in ("typical", "high-side"):
                rs = [r for r in rows if r["kind"] == "pack state" and r["state"] == st and r["corner"] == corner]
                if rs:
                    P("| %s | %s | %d of %d | %.3f | %.2f V |" % (STATE_TEXT[st], corner, sum(1 for r in rs if r["falls"]), len(rs),
                                                            np.mean([r["gait"]["track_lin"] for r in rs]), np.mean([min(r["V_min"].values()) for r in rs])))
    # sweep
    for walk in ("backlash", "plain"):
        f = os.path.join(J, "sweep_%s.json" % walk)
        if not os.path.exists(f):
            continue
        rows = json.load(open(f))
        P("\n### Sweep, %s walk, our build, P30B, closed loop (open loop in brackets)\n" % walk)
        P("| Case | State | Speed / command | Falls | Lowest servo | Knees L / R under 6 V | Ankles (worse) | Head roll | Bus mean |\n|---|---|---|---|---|---|---|---|---|")
        for x in rows:
            c, o = x["closed"], x["open"]
            P("| %s | %s | %.3f | %s | %.2f (%.2f) V | %.1f / %.1f (%.1f / %.1f) %% | %.1f (%.1f) %% | %.1f (%.1f) %% | %.2f V |" % (
                x["case"], x["state"], c["gait"]["track_lin"] or 0, "none" if not c["falls"] else c["falls"], min(c["V_min"].values()), min(o["V_min"].values()),
                c["pct_below_6V"]["left_knee"], c["pct_below_6V"]["right_knee"], o["pct_below_6V"]["left_knee"], o["pct_below_6V"]["right_knee"],
                max(c["pct_below_6V"]["left_ankle"], c["pct_below_6V"]["right_ankle"]), max(o["pct_below_6V"]["left_ankle"], o["pct_below_6V"]["right_ankle"]),
                c["pct_below_6V"]["head_roll"], o["pct_below_6V"]["head_roll"], c["pack"]["bus_mean"]))
    txt = "\n".join(out)
    open(os.path.join(SCR, "tables.md"), "w").write(txt + "\n")
    print(txt)


PUSHES_C8 = [(4.0 + 3.0 * i, 4.1 + 3.0 * i, (0.0, (15.0 if i % 2 == 0 else -15.0), 0.0)) for i in range(8)]   # sim/current_budget.py walk_pushes


def push_test(seeds=(None, 1, 2), sts=("full", "nominal", "d16"), corners=("typical", "high-side"), dur=30.0):
    """the C8 push case (plain model, 15 N for 0.1 s every 3 s, left and right in turn) with the loop closed"""
    rows = []
    for seed in seeds:
        st0 = run("ours", "plain", dur=dur, supply="stock", seed=seed, keep_full=False, guard=None, pushes=PUSHES_C8)
        rows.append(dict(kind="reference", case="stock (trained actuators)", seed=seed, falls=st0["falls"], gait=st0["gait"]))
        print("push stock seed %s falls %s track %.3f" % (seed, st0["falls"], st0["gait"]["track_lin"] or 0), flush=True)
        for st in sts:
            for corner in corners:
                r = run("ours", "plain", dur=dur, supply="net", corner=corner, cell="p30b", q0=STATES[st], compress=0.0, seed=seed, keep_full=False,
                        guard=None, pushes=PUSHES_C8)
                rows.append(dict(kind="pack state", state=st, corner=corner, seed=seed, **_short(r)))
                print("push %-8s %-9s seed %s falls %s track %.3f lowest %.2f V" % (st, corner, seed, r["falls"], r["gait"]["track_lin"] or 0,
                                                                                 min(r["servo"]["V_min"])), flush=True)
    _write("pushes_plain.json", rows)
    return rows


def png():
    """figures for ELECTROMECH_TWIN.md (each under 500 kB, written next to this file)"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    J = os.path.join(SCR, "json")
    # 1. sessions
    tags = [t for t in ("backlash_typical", "backlash_high-side", "plain_typical", "plain_high-side") if os.path.exists(os.path.join(SCR, "session", "session_%s.npz" % t))]
    if tags:
        fig, axs = plt.subplots(3, 1, figsize=(10, 8.2), sharex=True)
        cols = {"backlash_typical": "#1f5fa6", "backlash_high-side": "#c0392b", "plain_typical": "#5b9bd5", "plain_high-side": "#e59a8f"}
        for tg in tags:
            d = np.load(os.path.join(SCR, "session", "session_%s.npz" % tg))
            sj = json.load(open(os.path.join(J, "session_%s.json" % tg)))
            BP = {k[len("binsp_"):]: d[k] for k in d.files if k.startswith("binsp_")}
            t, v20 = _moving_speed(BP, 20.0)
            c = cols[tg]
            axs[0].plot(t / 60, v20 / sj["full_charge_speed"], color=c, lw=1.0, label=tg.replace("_", ", "))
            k2 = np.ones(20) / 20.0                  # 2 s mean of the 0.1 s bins
            axs[1].plot(t[19:] / 60, np.convolve(BP["v_pack_mean"], k2, "valid"), color=c, lw=0.9, ls="--")
            axs[1].plot(t[19:] / 60, np.convolve(BP["v_bec_out_mean"], k2, "valid"), color=c, lw=1.1)
            gm = d["guard_medians"]
            g5 = np.convolve(np.nan_to_num(gm[:, 1], nan=np.nanmean(gm[:, 1])), np.ones(10) / 10.0, "valid")   # the guard's 5 s mean
            axs[2].plot(gm[9:, 0] / 60, g5, color=c, lw=1.0)
            for key, ls in (("guard_walk_stop", "-"), ("guard_hard_stop", ":")):
                if sj.get(key):
                    for a in axs:
                        a.axvline(sj[key]["minute"], color=c, lw=0.9, ls=ls)
            if sj.get("walk_degraded"):
                axs[0].plot(sj["walk_degraded"]["minute"], sj["walk_degraded"]["speed_rel_full"], "v", color=c, ms=7)
            for f in sj["falls"]:
                axs[0].plot(f / 60, 0.1, "x", color=c, ms=9)
        axs[0].axhline(0.85, color="k", lw=0.7, ls="--"); axs[0].text(0.2, 0.86, "85 % of the full-charge speed (TEST_PLAN 9 speed rule)", fontsize=7)
        axs[0].set_ylabel("forward speed, 20 s window\n(share of the full-charge speed)", fontsize=8); axs[0].set_ylim(0, 1.25); axs[0].legend(fontsize=7, loc="lower left")
        axs[1].set_ylabel("pack terminal (dashed) and\nBEC output (solid), 2 s mean, V", fontsize=8)
        axs[2].axhline(6.0, color="k", lw=0.7, ls="--"); axs[2].axhline(5.4, color="k", lw=0.6, ls=":")
        axs[2].set_ylabel("guard: 5 s mean of the\n14-servo median (V)", fontsize=8); axs[2].set_xlabel("session time (min), no time compression", fontsize=8)
        for a in axs:
            a.grid(alpha=0.3); a.tick_params(labelsize=7)
        fig.suptitle("Session from a full charge, our 2.65 kg build, D15 + D23 as built, 2S P30B (vertical lines: D16 guard walk stop solid, hard stop dotted; sim pass only)", fontsize=8.5)
        fig.tight_layout(); fig.savefig(os.path.join(HERE, "em_twin_session.png"), dpi=80); plt.close(fig)
    # 2. pack states: closed against open loop
    f = os.path.join(J, "states_backlash.json")
    if os.path.exists(f):
        rows = [r for r in json.load(open(f)) if r["kind"] == "pack state"]
        sts = [s for s in ("full", "nominal", "d16", "low") if any(r["state"] == s for r in rows)]
        joints = ("left_knee", "right_knee", "left_ankle", "right_ankle", "head_roll")
        fig, axs = plt.subplots(1, 3, figsize=(14, 4.0), gridspec_kw=dict(width_ratios=[1, 1, 0.8]))
        for ai, corner in enumerate(("typical", "high-side")):
            ax = axs[ai]; x = np.arange(len(sts)); wd = 0.08
            for ji, jn in enumerate(joints):
                for li, (loop, hatch) in enumerate((("closed", ""), ("open", "//"))):
                    y = [np.mean([r[loop]["pct_below_6V"][jn] for r in rows if r["state"] == s and r["corner"] == corner]) for s in sts]
                    ax.bar(x + (ji * 2 + li - 4.5) * wd, y, wd, color=plt.cm.tab10(ji), hatch=hatch, edgecolor="k", lw=0.3,
                           label=("%s, %s loop" % (jn.replace("_", " "), loop)) if ai == 0 else None)
            ax.axhline(10, color="k", lw=0.8, ls="--")
            ax.set_xticks(x); ax.set_xticklabels([STATE_TEXT[s].split(" (")[0] for s in sts], fontsize=7)
            ax.set_ylabel("time under 6.0 V (% of the walk, counted in time)", fontsize=7.5); ax.set_title("%s corner" % corner, fontsize=8)
            ax.grid(alpha=0.3, axis="y"); ax.tick_params(labelsize=7); ax.set_ylim(0, 105)
        axs[0].legend(fontsize=5.5, ncol=2, loc="upper left")
        ax = axs[2]
        for walk, mk in (("backlash", "o"), ("plain", "s")):
            fw = os.path.join(J, "states_%s.json" % walk)
            if not os.path.exists(fw):
                continue
            rw = json.load(open(fw))
            stock = np.mean([r["gait"]["track_lin"] for r in rw if r["kind"] == "reference" and r["case"].startswith("stock")])
            sr = [r for r in rw if r["kind"] == "pack state"]
            for corner, ls in (("typical", "-"), ("high-side", "--")):
                y = [100 * np.mean([r["closed"]["gait"]["track_lin"] for r in sr if r["state"] == s and r["corner"] == corner]) / stock for s in sts]
                ax.plot(np.arange(len(sts)), y, ls, marker=mk, ms=4, lw=1, label="%s walk, %s" % (walk, corner))
        ax.axhline(100, color="k", lw=0.6); ax.set_ylim(0, 110)
        ax.set_xticks(np.arange(len(sts))); ax.set_xticklabels([STATE_TEXT[s].split(" (")[0] for s in sts], fontsize=7)
        ax.set_ylabel("walk speed, closed loop (% of the trained actuators)", fontsize=7.5); ax.set_title("walk speed", fontsize=8)
        ax.grid(alpha=0.3); ax.tick_params(labelsize=7); ax.legend(fontsize=6, loc="lower left")
        fig.suptitle("Our build, 2S P30B, as built: time under 6.0 V, closed loop (twin) against open loop (stock walk replayed), backlash walk; and the walk speed (sim pass only)", fontsize=8.5)
        fig.tight_layout(); fig.savefig(os.path.join(HERE, "em_twin_states.png"), dpi=80); plt.close(fig)


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "check"
    if step == "check":
        check()
    elif step == "states":
        states(walks=tuple(sys.argv[2].split(",")) if len(sys.argv) > 2 else ("backlash", "plain"))
    elif step == "session":
        walk = sys.argv[2] if len(sys.argv) > 2 else "backlash"
        corner = sys.argv[3] if len(sys.argv) > 3 else "typical"
        session(walk, corner)
    elif step == "sweep":
        sweep(sys.argv[2] if len(sys.argv) > 2 else "backlash")
    elif step == "png":
        png()
    elif step == "asbuilt":
        asbuilt_table()
    elif step == "tables":
        tables()
    elif step == "pushes":
        push_test()
    else:
        raise SystemExit("unknown step %s" % step)
