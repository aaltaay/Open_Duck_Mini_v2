"""Stock walk with the Pi 5 seat mass, sim pass only.

The shared lab gym overlay is not in this checkout. This script runs the
public playground scene (pin b9be205) that sim/SIM_WALK.md used. Set
ODM_PLAYGROUND to that checkout. The policy is BEST_WALK_ONNX_2.onnx at the
repo root. Nothing here is a hardware pass.

Mass placement, sim pass only: take 10.0 g off head_assembly (the Zero,
cited Adafruit 5291) and put 50 g on the trunk at the seat centre. 50 g is
the shop Weight field for the 4 GB board, SC1111, not an official Raspberry
Pi mass and not the 2 GB board. Seat centre in the print frame is
(7.5, 4.0, -50.45) mm. trunk_top matches the print file after +19.0 mm in x
and -64.9 mm in z, so the trunk-frame position is (-0.0115, 0.004, 0.01445) m.
"""
import os
import sys
import json
import types
os.environ.setdefault("MUJOCO_GL", "egl")

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PG = os.environ.get("ODM_PLAYGROUND", "")
if not PG:
    sys.exit("ODM_PLAYGROUND is not set. The shared lab gym overlay is not in this checkout.")
sys.path.insert(0, PG)

import numpy as np
import mujoco
import imageio
from etils import epath
from PIL import Image, ImageDraw

ROOT = epath.Path(PG) / "playground/open_duck_mini_v2"
# When set, the compiler's copy of the robot MJCF is this text.
SEAT_ROBOT = None


def get_assets():
    assets = {}

    def upd(d, glob="*"):
        for f in epath.Path(d).glob(glob):
            if f.is_file():
                assets[f.name] = f.read_bytes()

    upd(ROOT / "xmls", "*.xml")
    upd(ROOT / "xmls" / "assets")
    if SEAT_ROBOT is not None:
        assets["open_duck_mini_v2.xml"] = SEAT_ROBOT.encode("utf-8")
    return assets


import playground.open_duck_mini_v2 as pkg

base = types.ModuleType("playground.open_duck_mini_v2.base")
base.get_assets = get_assets
sys.modules["playground.open_duck_mini_v2.base"] = base
pkg.base = base
utils = types.ModuleType("playground.common.utils")


class LowPassActionFilter:
    def __init__(self, *a, **k):
        pass


utils.LowPassActionFilter = LowPassActionFilter
sys.modules["playground.common.utils"] = utils

from playground.open_duck_mini_v2 import mujoco_infer as MI

ONNX = os.path.join(REPO, "BEST_WALK_ONNX_2.onnx")
REF = str(ROOT / "data/polynomial_coefficients.pkl")
XML = str(ROOT / "xmls/scene_flat_terrain.xml")
ROBOT = str(ROOT / "xmls/open_duck_mini_v2.xml")
DUR = 26.0
ZERO_KG = 0.010
# Shop weight for the 4 GB board. See the module docstring.
PI5_KG = 0.050
# Trunk frame, metres. See the module docstring.
SEAT_POS = (-0.0115, 0.004, 0.01445)
# Keep-out box 85 by 56 by 15.1 mm, used only for a positive inertia.
BOX = (0.085, 0.056, 0.0151)


def schedule(t):
    if t < 2.0:
        return [0.0, 0, 0.0, 0, 0, 0, 0]
    if t < 14.0:
        return [0.15, 0, 0.0, 0, 0, 0, 0]
    if t < 20.0:
        return [0.0, 0, 1.0, 0, 0, 0, 0]
    return [0.15, 0, 0.0, 0, 0, 0, 0]


def plate_inertia(mass):
    x, y, z = BOX
    ix = mass * (y * y + z * z) / 12.0
    iy = mass * (x * x + z * z) / 12.0
    iz = mass * (x * x + y * y) / 12.0
    return ix, iy, iz


def seat_robot_text():
    """Robot MJCF with 10 g off the head and 50 g at the seat."""
    global SEAT_ROBOT
    robot = open(ROBOT, encoding="utf-8").read()
    old = 'mass="0.406607"'
    if robot.count(old) != 1:
        sys.exit("head_assembly mass line was not unique")
    new_m = 0.406607 - ZERO_KG
    ratio = new_m / 0.406607
    robot = robot.replace(old, 'mass="%.6f"' % new_m, 1)
    # Scale that body's inertia with the mass so the head CoM stays put.
    needle = 'fullinertia="0.00244627 0.0016864 0.00108002 -2.02404e-06 9.2382e-05 -1.84944e-05"'
    nums = [float(v) * ratio for v in needle.split('"')[1].split()]
    robot = robot.replace(needle, 'fullinertia="%s"' % " ".join("%.8g" % v for v in nums), 1)
    ix, iy, iz = plate_inertia(PI5_KG)
    block = (
        '\n        <body name="pi5_seat_mass" pos="%.5f %.5f %.5f">\n'
        '          <inertial pos="0 0 0" mass="%.3f" diaginertia="%.8g %.8g %.8g"/>\n'
        "        </body>\n" % (SEAT_POS[0], SEAT_POS[1], SEAT_POS[2], PI5_KG, ix, iy, iz)
    )
    token = '<body name="trunk_assembly"'
    at = robot.find(token)
    end = robot.find(">", at)
    robot = robot[: end + 1] + block + robot[end + 1 :]
    SEAT_ROBOT = robot
    return XML


def stamp(frame):
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)
    draw.rectangle((8, 8, 92, 36), fill=(255, 255, 255))
    draw.text((16, 12), "SIM", fill=(180, 0, 0))
    return np.asarray(img)


def run(xml, video_path):
    infer = MI.MjInfer(xml, REF, ONNX, standing=False)
    model, data = infer.model, infer.data
    w, h = 640, 360
    model.vis.global_.offwidth = max(model.vis.global_.offwidth, w)
    model.vis.global_.offheight = max(model.vis.global_.offheight, h)
    ren = mujoco.Renderer(model, h, w)
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.distance, cam.elevation, cam.azimuth = 1.15, -15, 135
    fb = infer._floating_base_qpos_addr
    writer = None
    if video_path:
        writer = imageio.get_writer(video_path, fps=10, codec="libx264", quality=6, macro_block_size=8)
    log = []
    falls = []
    fallen = False
    counter = 0
    nsteps = int(DUR / infer.sim_dt)
    for _ in range(nsteps):
        mujoco.mj_step(model, data)
        counter += 1
        if counter % infer.decimation != 0:
            continue
        t = counter * infer.sim_dt
        infer.commands = schedule(t)
        infer.imitation_i += 1.0 * infer.phase_frequency_factor
        infer.imitation_i = infer.imitation_i % infer.PRM.nb_steps_in_period
        ph = infer.imitation_i / infer.PRM.nb_steps_in_period * 2 * np.pi
        infer.imitation_phase = np.array([np.cos(ph), np.sin(ph)])
        obs = infer.get_obs(data, infer.commands)
        action = infer.policy.infer(obs)
        infer.last_last_last_action = infer.last_last_action.copy()
        infer.last_last_action = infer.last_action.copy()
        infer.last_action = action.copy()
        infer.motor_targets = infer.default_actuator + action * infer.action_scale
        if MI.USE_MOTOR_SPEED_LIMITS:
            step = infer.max_motor_velocity * (infer.sim_dt * infer.decimation)
            infer.motor_targets = np.clip(
                infer.motor_targets, infer.prev_motor_targets - step, infer.prev_motor_targets + step)
            infer.prev_motor_targets = infer.motor_targets.copy()
        data.ctrl = infer.motor_targets.copy()
        pos = data.qpos[fb:fb + 3].copy()
        quat = data.qpos[fb + 3:fb + 7].copy()
        rot = np.zeros(9)
        mujoco.mju_quat2Mat(rot, quat)
        upz = rot.reshape(3, 3)[2, 2]
        yaw = np.degrees(np.arctan2(rot[3], rot[0]))
        if (pos[2] < 0.10 or upz < 0.5) and not fallen:
            fallen = True
            falls.append(round(t, 2))
        if fallen and pos[2] > 0.13 and upz > 0.8:
            fallen = False
        log.append(dict(t=round(t, 3), x=float(pos[0]), y=float(pos[1]), z=float(pos[2]), upz=float(upz), yaw=float(yaw)))
        if writer and counter % (infer.decimation * 5) == 0:
            cam.lookat[:] = [pos[0], pos[1], 0.17]
            ren.update_scene(data, cam)
            writer.append_data(stamp(ren.render()))
    if writer:
        writer.close()
    summary = summarize(log, falls)
    summary["model_mass_kg"] = round(float(np.sum(model.body_mass)), 4)
    return summary


def summarize(log, falls):
    by_t = {round(r["t"], 2): r for r in log}

    def yaw_change(a, b):
        rows = [r for r in log if a - 1e-9 <= r["t"] <= b + 1e-9]
        total = 0.0
        prev = rows[0]["yaw"]
        for row in rows[1:]:
            step = ((row["yaw"] - prev + 180.0) % 360.0) - 180.0
            total += step
            prev = row["yaw"]
        return total

    def seg(a, b):
        ra, rb = by_t[a], by_t[b]
        dist = float(np.hypot(rb["x"] - ra["x"], rb["y"] - ra["y"]))
        return {
            "dist_m": round(dist, 3),
            "speed_m_s": round(dist / (b - a), 3),
            "dyaw_deg": round(yaw_change(a, b), 1),
        }

    path = 0.0
    for a, b in zip(log, log[1:]):
        path += float(np.hypot(b["x"] - a["x"], b["y"] - a["y"]))
    net = float(np.hypot(log[-1]["x"] - log[0]["x"], log[-1]["y"] - log[0]["y"]))
    return {
        "label": "sim pass only",
        "falls": falls,
        "min_z_m": round(min(r["z"] for r in log), 3),
        "min_upz": round(min(r["upz"] for r in log), 3),
        "path_m": round(path, 2),
        "net_m": round(net, 2),
        "forward_4_to_14_s": seg(4.0, 14.0),
        "turn_14_to_20_s": seg(14.0, 20.0),
        "forward_22_to_26_s": seg(22.0, 26.0),
    }


def main():
    out = os.path.join(os.path.dirname(__file__), "pi5_seat_walk_sim.mp4")
    baseline = run(XML, None)
    seated = run(seat_robot_text(), out)
    report = {
        "label": "sim pass only",
        "scene": "public playground scene_flat_terrain.xml at pin b9be205. The shared lab gym overlay is not in this checkout.",
        "policy": "BEST_WALK_ONNX_2.onnx",
        "schedule": "0 to 2 s stand, 2 to 14 s vx 0.15, 14 to 20 s wz 1.0, 20 to 26 s vx 0.15",
        "previous_published": {
            "source": "sim/SIM_WALK.md",
            "path_m": 2.7,
            "net_m": 1.32,
            "heading_drift_deg": "about 4 over 10 s",
            "falls": "none",
            "forward_speed_m_s": 0.097,
        },
        "baseline_this_script": baseline,
        "seat_mass": seated,
        "mass": {
            "removed_kg": ZERO_KG,
            "removed_label": "cited, Adafruit 5291, the Zero",
            "added_kg": PI5_KG,
            "added_label": "cited, raspberrypi.dk Weight 50 g for Raspberry Pi 5 4 GB, SC1111. Not the 2 GB board. Official drawing prints no mass.",
            "seat_pos_m": list(SEAT_POS),
            "video": "altaay_lab/sim/pi5_seat_walk_sim.mp4",
        },
    }
    path = os.path.join(os.path.dirname(__file__), "pi5_seat_walk.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1)
        handle.write("\n")
    print(json.dumps({"baseline": baseline, "seat": seated}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
