"""Headless replica of Open_Duck_Playground/playground/open_duck_mini_v2/mujoco_infer.py (MjInfer.run).
Only change: no interactive viewer; commands follow a fixed schedule; frames go to an offscreen renderer.
Upstream classes are imported unmodified. Two jax-only modules are stubbed (base.get_assets, common.utils)."""
import os, sys, types, json
os.environ.setdefault("MUJOCO_GL", "egl")
PG = "/workspace/tmp_odm/Open_Duck_Playground"
sys.path.insert(0, PG)
import numpy as np, mujoco, imageio
from etils import epath

# stub: playground.open_duck_mini_v2.base (real one imports jax/mjx/mujoco_playground only for training)
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
class LowPassActionFilter:  # unused by upstream run() (filter lines are commented out upstream)
    def __init__(self, *a, **k): pass
utils.LowPassActionFilter = LowPassActionFilter
sys.modules["playground.common.utils"] = utils

from playground.open_duck_mini_v2 import mujoco_infer as MI  # upstream, unmodified

ONNX = "/workspace/tmp_odm/Open_Duck_Mini/BEST_WALK_ONNX_2.onnx"
REF = str(ROOT / "data/polynomial_coefficients.pkl")
XML = str(ROOT / "xmls/scene_flat_terrain.xml")
OUT = sys.argv[1] if len(sys.argv) > 1 else "/workspace/tmp_odm/simrun/walk.mp4"
DUR = 26.0
def schedule(t):  # [vx, vy, wz, neck, head_pitch, head_yaw, head_roll]
    if t < 2.0:  return [0.0, 0, 0.0, 0, 0, 0, 0]      # stand / step in place
    if t < 14.0: return [0.15, 0, 0.0, 0, 0, 0, 0]     # forward at max command (COMMANDS_RANGE_X[1])
    if t < 20.0: return [0.0, 0, 1.0, 0, 0, 0, 0]      # turn left in place (COMMANDS_RANGE_THETA[1])
    return [0.15, 0, 0.0, 0, 0, 0, 0]                   # forward again

m = MI.MjInfer(XML, REF, ONNX, standing=False)
model, data = m.model, m.data
W, H = 960, 540
model.vis.global_.offwidth = max(model.vis.global_.offwidth, W)
model.vis.global_.offheight = max(model.vis.global_.offheight, H)
ren = mujoco.Renderer(model, H, W)
cam = mujoco.MjvCamera(); cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.distance, cam.elevation, cam.azimuth = 1.15, -15, 135
fb = m._floating_base_qpos_addr
writer = imageio.get_writer(OUT, fps=50, codec="libx264", quality=8, macro_block_size=8)
log, stills, falls, fallen = [], {}, [], False
counter, step = 0, 0
nsteps = int(DUR / m.sim_dt)
for _ in range(nsteps):
    mujoco.mj_step(model, data)
    counter += 1
    if counter % m.decimation == 0:
        t = counter * m.sim_dt
        m.commands = schedule(t)
        # ---- verbatim logic of MjInfer.run() ----
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
        # ---- end verbatim ----
        pos = data.qpos[fb:fb+3].copy(); quat = data.qpos[fb+3:fb+7].copy()
        R = np.zeros(9); mujoco.mju_quat2Mat(R, quat); upz = R.reshape(3,3)[2,2]
        yaw = np.degrees(np.arctan2(R[3], R[0]))
        if (pos[2] < 0.10 or upz < 0.5) and not fallen:
            fallen = True; falls.append(round(t, 2))
        if fallen and pos[2] > 0.13 and upz > 0.8: fallen = False
        log.append(dict(t=round(t,3), x=pos[0], y=pos[1], z=pos[2], upz=upz, yaw=yaw, cmd=m.commands[:3]))
        cam.lookat[:] = [pos[0], pos[1], 0.17]
        ren.update_scene(data, cam); frame = ren.render()
        writer.append_data(frame)
        for ts in (8.0, 17.0):
            if abs(t - ts) < 1e-6: stills[ts] = frame.copy()
writer.close()
od = os.path.dirname(OUT)
for ts, fr in stills.items():
    imageio.imwrite(os.path.join(od, f"still_{int(ts)}s.png"), fr)
json.dump(dict(log=log, falls=falls), open(os.path.join(od, "walk_log.json"), "w"), default=float)
L = {round(r["t"],2): r for r in log}
def seg(a, b):
    ra, rb = L[a], L[b]; d = np.hypot(rb["x"]-ra["x"], rb["y"]-ra["y"])
    return dict(dist=round(d,3), speed=round(d/(b-a),3), dyaw=round(((rb["yaw"]-ra["yaw"]+180)%360)-180,1))
print("falls:", falls)
print("min z:", round(min(r["z"] for r in log),3), "min upz:", round(min(r["upz"] for r in log),3))
print("forward 4-14s:", seg(4.0, 14.0)); print("turn 14-20s:", seg(14.0, 20.0)); print("forward2 21-26s:", seg(21.0, 26.0))
print("start z:", round(log[0]["z"],3))
