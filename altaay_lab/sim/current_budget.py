"""Current budget for the stock Open Duck Mini v2 walk (sim pass only).

Runs the stock BEST_WALK_ONNX_2 policy in the upstream MuJoCo model with the same control loop as
sim/run_stock_walk.py (upstream MjInfer, unmodified), logs every servo's actuator torque and joint speed
at the physics rate (500 Hz), and converts them to electrical current with the BAM DC motor model that
the MJCF actuators were fitted from.

Motor model (Rhoban BAM, see SERVO_DEEP_DIVE.md E3):
  forcerange = vin * kt / R      (MJCF: 3.23 Nm at vin 7.4 V, so kt / R = 0.43649)
  damping    = kt^2 / R + fv     (MJCF: 0.56)
  applied voltage u = F * R / kt, motor current I = (u - kt * w) / R, electrical power P = u * I
kt is not published for the current MJCF, so three values that keep kt / R fixed are run:
  1.148 (fv = 0.059 from BAM m1.json), 1.21164 (BAM m1.json), 1.28 (top of BAM m1..m6 range).
The highest current of the three is used for sizing.

Paths: set ODM_PLAYGROUND to an Open_Duck_Playground checkout (pin b9be205) and ODM_ONNX to
BEST_WALK_ONNX_2.onnx (Open_Duck_Mini repo root). Output: JSON summary and a PNG plot in ODM_OUT.
"""
import os, sys, types, json
import numpy as np
import mujoco
from etils import epath

PG = os.environ.get("ODM_PLAYGROUND", "/home/user/upstream/Open_Duck_Playground")
ONNX = os.environ.get("ODM_ONNX", os.path.join(os.path.dirname(__file__), "../../BEST_WALK_ONNX_2.onnx"))
OUT = os.environ.get("ODM_OUT", "/tmp/odm_current")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, PG)

# Same two stubs as run_stock_walk.py (training-only modules that need jax).
ROOT = epath.Path(PG) / "playground/open_duck_mini_v2"
def get_assets():
    assets = {}
    def upd(d, glob="*"):
        for f in epath.Path(d).glob(glob):
            if f.is_file():
                assets[f.name] = f.read_bytes()
    upd(ROOT / "xmls", "*.xml"); upd(ROOT / "xmls" / "assets")
    return assets
import playground.open_duck_mini_v2 as pkg
base = types.ModuleType("playground.open_duck_mini_v2.base"); base.get_assets = get_assets
sys.modules["playground.open_duck_mini_v2.base"] = base; pkg.base = base
utils = types.ModuleType("playground.common.utils")
class LowPassActionFilter:
    def __init__(self, *a, **k): pass
utils.LowPassActionFilter = LowPassActionFilter
sys.modules["playground.common.utils"] = utils
from playground.open_duck_mini_v2 import mujoco_infer as MI  # upstream, unmodified

REF = str(ROOT / "data/polynomial_coefficients.pkl")
VIN = 7.4                       # BAM model supply voltage (bam/feetech/actuator.py)
KT_OVER_R = 3.23 / VIN          # from MJCF forcerange
KTS = [1.148, 1.21164, 1.28]
ACC_OFFSET_FIX = os.environ.get("ODM_ACC_OFFSET_FIX", "1") == "1"   # default: match training and the robot (see run())

def run(scene, schedule, dur, pushes=None, seed=0):
    m = MI.MjInfer(str(ROOT / "xmls" / scene), REF, ONNX, standing=False)
    if ACC_OFFSET_FIX:
        # upstream MjInfer.get_obs adds +1.3 to accelerometer x (mujoco_infer.py line 74); training does not
        # (joystick.py line 502 is a no-op .at[].set) and the robot runtime does not. Undo it here.
        _ga = m.get_accelerometer
        def _ga_fixed(d, _ga=_ga):
            a = np.array(_ga(d), dtype=float); a[0] -= 1.3; return a
        m.get_accelerometer = _ga_fixed
    model, data = m.model, m.data
    fb = m._floating_base_qpos_addr
    qv = m.actuator_qvel_addr
    trunk = model.body("trunk_assembly").id if "trunk_assembly" in [model.body(i).name for i in range(model.nbody)] else 1
    rng = np.random.default_rng(seed)
    nsteps = int(dur / m.sim_dt)
    F = np.zeros((nsteps, model.nu)); W = np.zeros((nsteps, model.nu))
    falls, fallen, counter = [], False, 0
    for k in range(nsteps):
        t = (k + 1) * m.sim_dt
        data.xfrc_applied[:] = 0
        if pushes:
            for (t0, t1, fvec) in pushes:
                if t0 <= t < t1:
                    data.xfrc_applied[trunk, :3] = fvec
        mujoco.mj_step(model, data)
        counter += 1
        if counter % m.decimation == 0:
            m.commands = schedule(t)
            # verbatim MjInfer.run() control logic (same as run_stock_walk.py)
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
                m.motor_targets = np.clip(m.motor_targets,
                    m.prev_motor_targets - m.max_motor_velocity * (m.sim_dt * m.decimation),
                    m.prev_motor_targets + m.max_motor_velocity * (m.sim_dt * m.decimation))
                m.prev_motor_targets = m.motor_targets.copy()
            data.ctrl = m.motor_targets.copy()
            pos = data.qpos[fb:fb+3]; quat = data.qpos[fb+3:fb+7]
            R = np.zeros(9); mujoco.mju_quat2Mat(R, quat); upz = R[8]
            if (pos[2] < 0.10 or upz < 0.5) and not fallen:
                fallen = True; falls.append(round(t, 2))
            if fallen and pos[2] > 0.13 and upz > 0.8:
                fallen = False
        F[k] = data.actuator_force; W[k] = data.qvel[qv]
    return dict(F=F, W=W, names=list(m.actuator_names), dt=m.sim_dt, falls=falls)

def electrical(F, W, kt):
    R = kt / KT_OVER_R
    u = np.clip(F * R / kt, -VIN, VIN)
    I = (u - kt * W) / R
    P = u * I
    return I, P

def movavg(x, n):
    if n <= 1: return x
    c = np.cumsum(np.insert(x, 0, 0.0))
    return (c[n:] - c[:-n]) / n

SKIP_S = 2.0   # stats start after the 2 s settle at the start of every run (drop onto the floor)

def summarize(res, label):
    dt = res["dt"]; out = dict(label=label, falls=res["falls"], skip_s=SKIP_S, per_kt={})
    k0 = int(round(SKIP_S / dt))
    whole = {}
    for kt in KTS:
        I, P = electrical(res["F"], res["W"], kt)
        whole[str(kt)] = round(float((np.clip(P, 0, None).sum(1) / VIN).max()), 3)
        I, P = I[k0:], P[k0:]
        p_nosh = np.clip(P, 0, None).sum(1)        # no regen sharing between servos (conservative)
        p_net = np.clip(P.sum(1), 0, None)         # regen shared on the bus, BEC cannot sink
        i_bus = p_nosh / VIN                        # bus current at 7.4 V
        absI = np.abs(I)
        win = {}
        for name, sec in (("raw_2ms", dt), ("20ms", 0.02), ("100ms", 0.1), ("1s", 1.0), ("10s", 10.0)):
            n = max(1, int(round(sec / dt)))
            if n <= len(i_bus):
                win[name] = round(float(movavg(i_bus, n).max()), 3)
        out["per_kt"][str(kt)] = dict(
            bus_A_mean=round(float(i_bus.mean()), 3),
            bus_A_mean_net_regen=round(float((p_net / VIN).mean()), 3),
            bus_A_p99=round(float(np.percentile(i_bus, 99)), 3),
            bus_A_max_window=win,
            servo_A_max=dict(zip(res["names"], [round(float(v), 3) for v in absI.max(0)])),
            servo_A_rms=dict(zip(res["names"], [round(float(v), 3) for v in np.sqrt((I ** 2).mean(0))])),
            sat_frac=dict(zip(res["names"], [round(float(v), 4) for v in (np.abs(res["F"][k0:]) >= 3.229).mean(0)])),
        )
        if kt == KTS[0]:
            out["_trace_bus_A"] = i_bus
    out["bus_A_max_including_start"] = whole
    return out

def sched_const(v):
    return lambda t: [0.0, 0, 0.0, 0, 0, 0, 0] if t < 2.0 else v

CASES = [
    ("stand_in_place", "scene_flat_terrain.xml", sched_const([0.0, 0, 0.0, 0, 0, 0, 0]), 20.0, None),
    ("walk_forward_0.15", "scene_flat_terrain.xml", sched_const([0.15, 0, 0.0, 0, 0, 0, 0]), 30.0, None),
    ("turn_1.0", "scene_flat_terrain.xml", sched_const([0.0, 0, 1.0, 0, 0, 0, 0]), 20.0, None),
    ("walk_side_0.2", "scene_flat_terrain.xml", sched_const([0.0, 0.2, 0.0, 0, 0, 0, 0]), 20.0, None),
    ("walk_backlash", "scene_flat_terrain_backlash.xml", sched_const([0.15, 0, 0.0, 0, 0, 0, 0]), 30.0, None),
    ("walk_rough_backlash", "scene_rough_terrain_backlash.xml", sched_const([0.15, 0, 0.0, 0, 0, 0, 0]), 30.0, None),
    ("walk_pushes", "scene_flat_terrain.xml", sched_const([0.15, 0, 0.0, 0, 0, 0, 0]), 30.0,
     [(4.0 + 3.0 * i, 4.1 + 3.0 * i, (0.0, (15.0 if i % 2 == 0 else -15.0), 0.0)) for i in range(8)]),
]

if __name__ == "__main__":
    only = sys.argv[1:]
    results = []
    for label, scene, sch, dur, pushes in CASES:
        if only and label not in only: continue
        res = run(scene, sch, dur, pushes)
        if os.environ.get("ODM_SAVE_TRACES"):
            np.savez_compressed(os.path.join(OUT, f"trace_{label}.npz"), F=res["F"], W=res["W"], names=np.array(res["names"]), dt=res["dt"])
        s = summarize(res, label)
        results.append(s)
        k = s["per_kt"][str(KTS[0])]
        print(label, "falls", s["falls"], "mean", k["bus_A_mean"], "p99", k["bus_A_p99"], "win", k["bus_A_max_window"])
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, axs = plt.subplots(len(results), 1, figsize=(9, 1.6 * len(results)), sharex=True)
        axs = np.atleast_1d(axs)
        for ax, s in zip(axs, results):
            tr = s["_trace_bus_A"]; t = np.arange(len(tr)) * 0.002 + SKIP_S
            ax.plot(t, tr, lw=0.4, color="#c0392b"); ax.plot(t[:len(movavg(tr, 50))] + 0.05, movavg(tr, 50), lw=1.0, color="#1f3a93")
            ax.set_ylabel("A"); ax.set_title(s["label"] + " (servo bus current at 7.4 V, kt 1.148; red 2 ms, blue 100 ms avg)", fontsize=8)
            ax.tick_params(labelsize=7); ax.grid(alpha=0.3)
        axs[-1].set_xlabel("time (s)")
        fig.tight_layout(); fig.savefig(os.path.join(OUT, "current_budget.png"), dpi=90)
    except Exception as e:
        print("plot skipped:", e)
    for s in results: s.pop("_trace_bus_A", None)
    json.dump(results, open(os.path.join(OUT, "current_budget.json"), "w"), indent=1)
    print("wrote", OUT)
