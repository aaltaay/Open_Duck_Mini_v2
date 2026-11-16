#!/usr/bin/env python3
"""Scripted day for the personality engine on the run D policy. Sim pass only.

The picture is the playground flat scene (pin b9be205, scene_flat_terrain.xml),
the same scene the infer script loads, with sts12_runD_policy.onnx. It is not
the pack circuit and it is not a hardware dock.

Standing: the four head actuators are overwritten with the personality targets.
The policy's own head write is commented out in that infer script, and a short
probe (printed into the json next to the video) measures the miss.

Walking: head targets go in the seven command channels the policy already
reads. The head joints are not overwritten while the feet are moving.

Eyes and ears are not joints in this scene. The caption draws them.
Nest vision is still BLOCKER. Sit-from-a-walk is not trained.

Usage, from the repo root:
  ODM_PLAYGROUND=<Open_Duck_Playground at b9be205> python3 altaay_lab/twin/personality_demo.py
"""

from __future__ import annotations

import json
import math
import os
import queue
import sys
import threading
import types

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(LAB, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from altaay_lab.software.personality.engine import Personality, Sensors  # noqa: E402

POLICY_NAME = "sts12_runD_policy.onnx"
VIDEO_NAME = "personality_demo.mp4"
JSON_NAME = "personality_demo.json"
CTRL_DT = 0.02
PERSON_DT = 0.10
FPS = 20
W, H = 1280, 720
# Command inside the run D lin_vel_x range [-0.15, 0.40] (joystick_runD.py, cited).
WALK_VX = 0.15
DOCK_X = 1.20


def _boot_infer(scene_xml):
    """Load MjInfer the same way sim/current_budget.py does. Unmodified class."""
    pg = os.environ.get("ODM_PLAYGROUND")
    if not pg or not os.path.isdir(pg):
        raise SystemExit("Set ODM_PLAYGROUND to the Open Duck Playground checkout at pin b9be205")
    sys.path.insert(0, pg)
    from etils import epath

    root = epath.Path(pg) / "playground/open_duck_mini_v2"

    def get_assets():
        assets = {}

        def upd(folder, pattern):
            for item in epath.Path(folder).glob(pattern):
                if item.is_file():
                    assets[item.name] = item.read_bytes()

        upd(root / "xmls", "*.xml")
        upd(root / "xmls" / "assets", "*")
        return assets

    import playground.open_duck_mini_v2 as pkg

    base = types.ModuleType("playground.open_duck_mini_v2.base")
    base.get_assets = get_assets
    sys.modules["playground.open_duck_mini_v2.base"] = base
    pkg.base = base
    utils = types.ModuleType("playground.common.utils")

    class LowPassActionFilter:
        def __init__(self, *args, **kwargs):
            pass

    utils.LowPassActionFilter = LowPassActionFilter
    sys.modules["playground.common.utils"] = utils
    from playground.open_duck_mini_v2 import mujoco_infer as mi

    onnx = os.environ.get("ODM_ONNX") or os.path.join(
        ROOT, "altaay_lab", "problems", "retrain_sts12", POLICY_NAME
    )
    if os.path.basename(onnx) != POLICY_NAME:
        raise SystemExit("the personality demo must load sts12_runD_policy.onnx")
    infer = mi.MjInfer(
        scene_xml,
        str(root / "data" / "polynomial_coefficients.pkl"),
        onnx,
        standing=False,
    )
    raw = infer.get_accelerometer

    def fixed(data, _raw=raw):
        # Same correction as sim/current_budget.py: the infer script adds 1.3
        # on accelerometer x and the trainer does not.
        acc = np.array(_raw(data), float)
        acc[0] -= 1.3
        return acc

    infer.get_accelerometer = fixed
    return infer, mi


def _scene_xml(pg):
    xmls = os.path.join(pg, "playground", "open_duck_mini_v2", "xmls")
    path = os.path.join(xmls, "scene_personality_demo.xml")
    # Visual marks only. They do not collide. Not the nest CAD.
    text = """<mujoco model="personality_demo">
  <include file="scene_flat_terrain.xml"/>
  <worldbody>
    <body name="home_dock" pos="%.2f 0 0.02">
      <geom name="home_dock" type="box" size="0.22 0.18 0.02" rgba="0.62 0.40 0.18 1" contype="0" conaffinity="0"/>
    </body>
    <body name="person_stub" pos="0.58 0.55 0.40">
      <geom name="person_stub" type="capsule" size="0.09 0.22" rgba="0.22 0.48 0.32 1" contype="0" conaffinity="0"/>
    </body>
  </worldbody>
</mujoco>
""" % DOCK_X
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def _up_and_pos(infer):
    import mujoco

    data = infer.data
    fb = infer._floating_base_qpos_addr
    quat = data.qpos[fb + 3:fb + 7]
    mat = np.zeros(9)
    mujoco.mju_quat2Mat(mat, quat)
    up = float(mat.reshape(3, 3)[2, 2])
    pos = data.qpos[fb:fb + 3]
    return float(pos[0]), float(pos[1]), float(pos[2]), up


def _policy_step(infer, cmd, head_override):
    import mujoco

    model, data = infer.model, infer.data
    for _ in range(infer.decimation):
        mujoco.mj_step(model, data)
    infer.commands = [float(v) for v in cmd]
    infer.imitation_i = (infer.imitation_i + infer.phase_frequency_factor) % infer.PRM.nb_steps_in_period
    phase = infer.imitation_i / infer.PRM.nb_steps_in_period * 2.0 * math.pi
    infer.imitation_phase = np.array([math.cos(phase), math.sin(phase)])
    obs = infer.get_obs(data, infer.commands)
    action = infer.policy.infer(obs)
    infer.last_last_last_action = infer.last_last_action.copy()
    infer.last_last_action = infer.last_action.copy()
    infer.last_action = action.copy()
    motor = infer.default_actuator + action * infer.action_scale
    limit = infer.max_motor_velocity * (infer.sim_dt * infer.decimation)
    motor = np.clip(motor, infer.prev_motor_targets - limit, infer.prev_motor_targets + limit)
    if head_override is not None:
        names = list(infer.actuator_names)
        for joint, value in head_override.items():
            index = names.index(joint)
            lo, hi = model.actuator_ctrlrange[index]
            target = min(float(hi), max(float(lo), float(value)))
            prev = float(infer.prev_motor_targets[index])
            target = min(prev + limit, max(prev - limit, target))
            motor[index] = target
    infer.motor_targets = motor
    infer.prev_motor_targets = motor.copy()
    data.ctrl[:] = motor


def _head_q(infer):
    names = list(infer.actuator_names)
    q = infer.get_actuator_joints_qpos(infer.data.qpos)
    return {name: float(q[names.index(name)]) for name in ("neck_pitch", "head_pitch", "head_yaw", "head_roll")}


def _reset(infer):
    import mujoco

    mujoco.mj_resetDataKeyframe(infer.model, infer.data, 0)
    infer.last_action[:] = 0
    infer.last_last_action[:] = 0
    infer.last_last_last_action[:] = 0
    infer.motor_targets = np.array(infer.default_actuator, float).copy()
    infer.prev_motor_targets = np.array(infer.default_actuator, float).copy()
    infer.data.ctrl[:] = infer.default_actuator
    infer.imitation_i = 0
    infer.commands = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    mujoco.mj_forward(infer.model, infer.data)


def _probe(infer):
    """Two short stands. Not part of the video. Sim pass only."""
    _reset(infer)
    yaw_cmd = 0.40
    channel_err = []
    for k in range(150):
        _policy_step(infer, [0.0, 0.0, 0.0, 0.0, 0.0, yaw_cmd, 0.0], None)
        if k >= 100:
            channel_err.append(abs(_head_q(infer)["head_yaw"] - yaw_cmd))
    channel = float(np.mean(channel_err))
    _reset(infer)
    over_err = []
    for k in range(150):
        _policy_step(
            infer,
            [0.0, 0.0, 0.0, 0.0, 0.0, yaw_cmd, 0.0],
            {"neck_pitch": 0.0, "head_pitch": 0.0, "head_yaw": yaw_cmd, "head_roll": 0.0},
        )
        if k >= 100:
            over_err.append(abs(_head_q(infer)["head_yaw"] - yaw_cmd))
    _reset(infer)
    return {
        "label": "sim pass only",
        "stand_channel_yaw_error_rad": round(channel, 3),
        "stand_override_yaw_error_rad": round(float(np.mean(over_err)), 3),
        "yaw_command_rad": yaw_cmd,
        "note": (
            "The infer script leaves the head-joint write commented out. "
            "Channels are in the observation. Override is used while standing "
            "because the channel error stays large."
        ),
    }


def _beat(t):
    if t < 4.0:
        return "waking up"
    if t < 6.0:
        return "face seen, greeting"
    if t < 17.0:
        return "curious look"
    if t < 18.0:
        return "face lost"
    if t < 24.0:
        return "timer fired"
    if t < 33.0:
        return "pack falling"
    if t < 46.0:
        return "walk home to dock"
    return "at the dock"


class _Day:
    def __init__(self):
        self.fired = set()

    def at(self, t):
        events = []

        def once(name, at):
            if t + 1e-9 >= at and name not in self.fired:
                self.fired.add(name)
                events.append(name)

        pack = 12.4
        if t >= 26.0:
            u = min(1.0, (t - 26.0) / 8.0)
            pack = 12.4 + (10.55 - 12.4) * u
        bearing = None
        attention = "none"
        elevation = None
        if 4.0 <= t < 17.0:
            attention = "face"
            bearing = 0.50 if t < 11.0 else -0.40
            elevation = 0.05
        once("face_seen", 4.0)
        once("face_lost", 17.0)
        once("timer_fired", 18.0)
        sensors = Sensors(
            pack_v=pack,
            idle_s=t,
            posture="walking" if 33.0 <= t < 46.0 else "standing",
            bearing_rad=bearing,
            elevation_rad=elevation,
            attention=attention,
        )
        return sensors, events


def _worker(walk_id, requests, replies):
    duck = Personality(seed=4, mode="kid")
    duck.bind_walk_thread(walk_id)
    duck.arousal = 0.08
    duck.valence = -0.05
    while True:
        item = requests.get()
        if item is None:
            return
        dt, sensors, events = item
        try:
            replies.put(duck.step(dt, sensors, events))
        except Exception as exc:
            replies.put(exc)
            return


def _caption(frame, cmd, beat, t):
    from PIL import Image, ImageDraw, ImageFont

    image = Image.fromarray(frame)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, H - 88, W, H), fill=(18, 16, 14))
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    mood = cmd.mood
    line1 = "sim pass only   %s   t %.0fs" % (beat, t)
    line2 = "mood  valence %+.2f   arousal %.2f   energy %.2f   %s" % (
        mood["valence"], mood["arousal"], cmd.energy, cmd.reason,
    )
    line3 = "%s   intent %s   eyes white %.2f %s   ears %+.2f %+.2f" % (
        cmd.expression, cmd.intent, cmd.eye_brightness, cmd.blink,
        cmd.antenna_left, cmd.antenna_right,
    )
    draw.text((16, H - 80), line1, fill=(255, 244, 220), font=font)
    draw.text((16, H - 52), line2, fill=(255, 244, 220), font=small)
    draw.text((16, H - 28), line3, fill=(255, 244, 220), font=small)
    return np.asarray(image)


def _run_story(infer):
    import mujoco

    _reset(infer)
    model = infer.model
    model.vis.global_.offwidth = max(model.vis.global_.offwidth, W)
    model.vis.global_.offheight = max(model.vis.global_.offheight, H)
    renderer = mujoco.Renderer(model, H, W)
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.distance = 1.55
    cam.elevation = -18
    cam.azimuth = 135

    requests = queue.Queue()
    replies = queue.Queue()
    worker = threading.Thread(target=_worker, args=(threading.get_ident(), requests, replies), daemon=True)
    worker.start()
    day = _Day()
    requests.put((PERSON_DT, *day.at(0.0)))
    first = replies.get()
    if isinstance(first, Exception):
        raise first
    cmd = first

    frames = []
    walk_err = []
    fallen = False
    fall_t = None
    t = 0.0
    next_person = PERSON_DT
    next_frame = 0.0
    x0, y0, _, _ = _up_and_pos(infer)
    arrived = False
    arrival_t = None
    while t < 58.0:
        x, y, z, up = _up_and_pos(infer)
        if (not arrived) and cmd.intent == "go_home" and t >= 30.0 and x < DOCK_X - 0.28:
            vx = WALK_VX
        else:
            vx = 0.0
            if cmd.intent == "go_home" and x >= DOCK_X - 0.28:
                arrived = True
                if arrival_t is None:
                    arrival_t = t
        head = {
            "neck_pitch": cmd.neck_pitch,
            "head_pitch": cmd.head_pitch,
            "head_yaw": cmd.head_yaw,
            "head_roll": cmd.head_roll,
        }
        channels = [vx, 0.0, 0.0, head["neck_pitch"], head["head_pitch"], head["head_yaw"], head["head_roll"]]
        override = None if vx > 0.0 else head
        _policy_step(infer, channels, override)
        t += CTRL_DT
        q = _head_q(infer)
        if vx > 0.0:
            walk_err.append(abs(q["head_yaw"] - head["head_yaw"]))
        x, y, z, up = _up_and_pos(infer)
        if z < 0.08 or up < 0.4:
            fallen = True
            fall_t = round(t, 2)
        if t + 1e-9 >= next_person:
            requests.put((PERSON_DT, *day.at(t)))
            got = replies.get()
            if isinstance(got, Exception):
                raise got
            cmd = got
            next_person += PERSON_DT
        if t + 1e-9 >= next_frame:
            cam.lookat[:] = [x, y, 0.16]
            renderer.update_scene(infer.data, cam)
            beat = "at the dock" if arrived else _beat(t)
            frames.append(_caption(renderer.render().copy(), cmd, beat, t))
            next_frame += 1.0 / FPS
        if fallen and fall_t is not None and t > fall_t + 2.0:
            break
        if arrived and arrival_t is not None and t >= arrival_t + 4.0 and t >= 36.0:
            break
    requests.put(None)
    worker.join(timeout=2.0)
    x, y, z, up = _up_and_pos(infer)
    return {
        "frames": frames,
        "fallen": fallen,
        "fall_t": fall_t,
        "duration_s": round(t, 2),
        "end_x_m": round(x, 3),
        "end_y_m": round(y, 3),
        "end_z_m": round(z, 3),
        "start_x_m": round(x0, 3),
        "start_y_m": round(y0, 3),
        "walk_channel_yaw_error_rad": None if not walk_err else round(float(np.mean(walk_err)), 3),
        "arrived": arrived,
    }


def _write_video(frames, path):
    import subprocess

    proc = subprocess.Popen(
        [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "32", "-preset", "veryfast", "-movflags", "+faststart",
            path,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    for frame in frames:
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    err = proc.stderr.read().decode("utf-8", "replace")
    code = proc.wait()
    if code != 0:
        raise SystemExit(err[-2000:])


def main():
    pg = os.environ.get("ODM_PLAYGROUND")
    scene = _scene_xml(pg)
    infer, _mi = _boot_infer(scene)
    probe = _probe(infer)
    story = _run_story(infer)
    out_dir = os.path.join(HERE, "out")
    vid_dir = os.path.join(out_dir, "videos")
    os.makedirs(vid_dir, exist_ok=True)
    video = os.path.join(vid_dir, VIDEO_NAME)
    _write_video(story["frames"], video)
    size = os.path.getsize(video)
    if size > 5 * 1024 * 1024:
        raise SystemExit("video is over 5 MB")
    doc = {
        "label": "sim pass only",
        "policy": POLICY_NAME,
        "scene": "playground scene_flat_terrain.xml at pin b9be205, plus two visual marks",
        "standing_head": "override the four head actuators",
        "walking_head": "command channels only, joints not overwritten",
        "probe": probe,
        "duration_s": story["duration_s"],
        "frames": len(story["frames"]),
        "fps": FPS,
        "width": W,
        "height": H,
        "video_bytes": size,
        "fallen": story["fallen"],
        "fall_t_s": story["fall_t"],
        "arrived_near_mark": story["arrived"],
        "start_x_m": story["start_x_m"],
        "end_x_m": story["end_x_m"],
        "end_y_m": story["end_y_m"],
        "walk_channel_yaw_error_rad": story["walk_channel_yaw_error_rad"],
        "walk_command_m_s": WALK_VX,
        "not_in_this_clip": [
            "nest camera",
            "charge current",
            "sit from a walk",
            "ear servos and eye beads (caption only)",
            "a real face finder or a real sound direction",
        ],
    }
    with open(os.path.join(out_dir, JSON_NAME), "w", encoding="utf-8") as handle:
        json.dump(doc, handle, indent=1)
        handle.write("\n")
    print(json.dumps(doc, indent=1))


if __name__ == "__main__":
    main()
