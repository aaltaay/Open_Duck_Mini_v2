#!/usr/bin/env python3
"""Camera dock on the gold disc and the pale gold ring. Sim pass only.

The walk, the gold-dome wells, and the stripe score are the camera dock's.
The pose in the loop is the head camera (software/perception/nest_find.py),
except the privileged baseline, which is given the true sun in the trunk
frame. The true pose is the score after the sit.

The cloth sizes are the nest CAD (100 mm disc, ring 82 mm to 235 mm). The
files in cad/nest_v2 are not edited. The cloth geoms do not collide. The
wells still meet the stripes.

Nothing here is a hardware dock.
"""
from __future__ import annotations

import json
import math
import os
import time
import xml.etree.ElementTree as ET

import numpy as np

from altaay_lab.software.autonomy.disc_loop import HEAD_YAW_HI, HEAD_YAW_LO, DiscLoop, fall_outranks_sit
from altaay_lab.software.perception import nest_find as NF
from altaay_lab.twin.dock.camera import camera_dock as CD

# Full field. Height is the cited 66 deg axis, width comes out at 41 deg.
# Calc only. A still is 4608 by 2592 (cited). This is a bin of that field,
# about 8 times on a side, not a centre crop.
IMG_W = 320
IMG_H = 556
# Set point. The brief does not state a shutter time.
EXPOSURE_S = 0.010

# Nest CAD colours, nestcad_lib.COL. CAD check only as a paint choice.
FELT = (0.66, 0.74, 0.58, 1.0)
SUN = (0.90, 0.70, 0.22, 1.0)
RING = (0.95, 0.87, 0.60, 1.0)

ROOMS = {
    "day": {"diffuse": (0.78, 0.76, 0.70), "wall": (0.80, 0.78, 0.74), "floor": (0.86, 0.83, 0.77)},
    "warm": {"diffuse": (0.92, 0.58, 0.32), "wall": (0.70, 0.52, 0.38), "floor": (0.72, 0.56, 0.40)},
    "dim": {"diffuse": (0.26, 0.28, 0.32), "wall": (0.42, 0.44, 0.48), "floor": (0.38, 0.40, 0.44)},
    "cool": {"diffuse": (0.42, 0.55, 0.78), "wall": (0.68, 0.74, 0.80), "floor": (0.60, 0.66, 0.74)},
}

# seed, x, y, yaw deg, room, cover part of the ring, side hazard
CASES = (
    (1, -1.05, 0.00, 0.0, "day", False, False),
    (2, -1.20, 0.22, -20.0, "warm", False, True),
    (3, -0.95, -0.24, 26.0, "dim", True, False),
    (4, -1.35, 0.12, 14.0, "cool", False, False),
    (5, -1.15, 0.04, 150.0, "day", True, True),
    (6, -1.28, -0.28, 10.0, "warm", False, False),
    (7, -1.02, 0.16, 90.0, "dim", False, True),
    (8, -1.40, -0.10, -80.0, "cool", True, False),
)


def _rgba(rgb, a=1.0):
    return "%.3f %.3f %.3f %.2f" % (rgb[0], rgb[1], rgb[2], a)


def _ring_elems(parent):
    r0, r1 = 0.082, 0.235
    n = 72
    cut_x = 0.190 - 0.056
    for i in range(n):
        a0 = 2.0 * math.pi * i / n
        a1 = 2.0 * math.pi * (i + 1) / n
        am = 0.5 * (a0 + a1)
        rm = 0.5 * (r0 + r1)
        x = rm * math.cos(am)
        y = rm * math.sin(am)
        if x > cut_x:
            continue
        tang = rm * (a1 - a0) * 0.92
        radial = 0.5 * (r1 - r0) * 0.96
        g = ET.SubElement(parent, "geom")
        g.set("name", "ring_%d" % i)
        g.set("type", "box")
        g.set("pos", "%.4f %.4f 0.0030" % (x, y))
        g.set("euler", "0 0 %.2f" % math.degrees(am))
        g.set("size", "%.4f %.4f 0.00025" % (radial, tang))
        g.set("rgba", _rgba(RING))
        g.set("contype", "0")
        g.set("conaffinity", "0")
    sun = ET.SubElement(parent, "geom")
    sun.set("name", "sun_disc")
    sun.set("type", "cylinder")
    sun.set("pos", "0 0 0.0036")
    sun.set("size", "0.050 0.00030")
    sun.set("rgba", _rgba(SUN))
    sun.set("contype", "0")
    sun.set("conaffinity", "0")


def _extra(parent, name, pos, size, rgba):
    g = ET.SubElement(parent, "geom")
    g.set("name", name)
    g.set("type", "box")
    g.set("pos", pos)
    g.set("size", size)
    g.set("rgba", rgba)
    g.set("contype", "0")
    g.set("conaffinity", "0")


def _paint(dst, spec):
    room = ROOMS[spec["room"]]
    path = os.path.join(dst, "scene_dock.xml")
    tree = ET.parse(path)
    root = tree.getroot()
    world = root.find("worldbody")
    for geom in list(world.findall("geom")):
        name = geom.get("name")
        if name in ("mark", "mark_gold", "mark2", "mark2_red"):
            world.remove(geom)
        elif not name:
            # Stripe paint. The wells still score on the stripe rule. The
            # camera is looking for the disc and the ring, and the stripes
            # are the same yellow, so they stay in the file and drop out of
            # the picture.
            geom.set("rgba", "0 0 0 0")
        elif name in ("mat_low", "mat_top"):
            geom.set("rgba", _rgba(FELT))
        elif name == "wall":
            geom.set("rgba", _rgba(room["wall"]))
    for light in root.iter("light"):
        if light.get("name") == "room":
            light.set("diffuse", "%.3f %.3f %.3f" % room["diffuse"])
    _ring_elems(world)
    # A felt card on the ring. The disc stays clear. Visual only.
    _extra(world, "occluder", "-0.02 0.16 0.018", "0.040 0.030 0.008", _rgba(FELT))
    _extra(world, "cliff_vis", "-1.70 0.95 0.004", "0.22 0.07 0.002", "0.04 0.04 0.05 1")
    _extra(world, "obstacle_vis", "-0.55 0.72 0.05", "0.04 0.04 0.05", "0.12 0.13 0.14 1")
    tree.write(path)
    terrain = os.path.join(dst, "scene_flat_terrain_backlash.xml")
    st = ET.parse(terrain)
    rgb = "%.3f %.3f %.3f" % room["floor"]
    for tex in st.getroot().iter("texture"):
        if tex.get("name") == "groundplane":
            tex.set("rgb1", rgb)
            tex.set("rgb2", rgb)
            tex.set("markrgb", rgb)
    st.write(terrain)


def _blur(img, du, dv):
    """Short box along the image motion. The length is the 10 ms shutter."""
    length = math.hypot(du, dv)
    if length < 0.8:
        return img
    steps = int(min(6, max(1, round(length))))
    acc = img.astype(np.float32)
    for i in range(1, steps + 1):
        acc += np.roll(img, int(round(du * i / steps)), axis=1)
        acc += np.roll(img, int(round(-du * i / steps)), axis=1)
        acc += np.roll(np.roll(img, int(round(dv * i / steps)), axis=0), int(round(du * i / steps)), axis=1)
    return np.clip(acc / (1 + 3 * steps), 0, 255).astype(np.uint8)


def _draw(img, raw):
    out = img.copy()
    h, w = out.shape[:2]
    box = raw.get("box") if raw else None
    if box is not None:
        x0, y0, x1, y1 = [int(v) for v in box]
        out[max(0, y0):min(h, y0 + 2), max(0, x0):min(w, x1)] = (40, 220, 70)
        out[max(0, y1 - 1):min(h, y1 + 1), max(0, x0):min(w, x1)] = (40, 220, 70)
        out[max(0, y0):min(h, y1), max(0, x0):min(w, x0 + 2)] = (40, 220, 70)
        out[max(0, y0):min(h, y1), max(0, x1 - 1):min(w, x1 + 1)] = (40, 220, 70)
    if raw and raw.get("u") is not None:
        u, v = int(raw["u"]), int(raw["v"])
        out[max(0, v - 2):min(h, v + 3), max(0, u - 8):min(w, u + 9)] = (255, 255, 255)
        out[max(0, v - 8):min(h, v + 9), max(0, u - 2):min(w, u + 3)] = (255, 255, 255)
    if raw and raw.get("cliff"):
        out[h - 8:h, :] = (220, 40, 40)
    if raw and raw.get("obstacle") and raw.get("obstacle_u") is not None:
        u = int(raw["obstacle_u"])
        out[h // 2:h // 2 + 6, max(0, u - 6):min(w, u + 6)] = (255, 140, 20)
    return out


class DiscSim(CD.DockSim):
    def __init__(self, spec, record=False):
        self.spec = spec
        # added_mass_sim sets ODM_ONNX to the stock walk on import. This dock
        # is the run D policy, the same file the marker dock requires.
        run_d = os.path.join(CD.ROOT, CD.POLICY_REL)
        os.environ["ODM_ONNX"] = run_d
        orig = CD._scene_dir

        def patched(folder, _orig=orig, _spec=spec):
            dst = _orig(folder)
            _paint(dst, _spec)
            return dst

        CD._scene_dir = patched
        try:
            super().__init__(seed=int(spec["seed"]), light=1.0, record=record)
        finally:
            CD._scene_dir = orig
        self.ren.close()
        self.model.vis.global_.offwidth = max(int(self.model.vis.global_.offwidth), 960)
        self.model.vis.global_.offheight = max(int(self.model.vis.global_.offheight), IMG_H, 960)
        self.ren = self.mujoco.Renderer(self.model, IMG_H, IMG_W)
        if self.ren3 is not None:
            self.ren3.close()
        self.ren3 = self.mujoco.Renderer(self.model, 360, 640) if record else None
        self.fx, self.fy, self.cx, self.cy, self.hfov = NF.intrinsics(IMG_W, IMG_H)
        self.frame_ms = []
        self.prev = None
        self.base_diffuse = np.array(ROOMS[spec["room"]]["diffuse"], float)
        lid = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_LIGHT, "room")
        self.lid = lid
        self._hide("occluder", spec.get("cover"))
        self._hide("cliff_vis", spec.get("hazard"))
        self._hide("obstacle_vis", spec.get("hazard"))
        self._flicker()

    def _hide(self, name, keep):
        gid = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_GEOM, name)
        if gid < 0:
            return
        if not keep:
            self.model.geom_rgba[gid, 3] = 0.0
            self.model.geom_pos[gid, 2] = -1.0

    def _flicker(self):
        if self.lid < 0:
            return
        wave = 1.0 + 0.08 * math.sin(self.t * 2.1 + 0.3 * int(self.spec["seed"]))
        self.model.light_diffuse[self.lid] = self.base_diffuse * wave

    def _rates(self):
        w = np.array(self.m.get_gyro(self.data), float)
        r = self.data.site_xmat[self.m.imu_site_id].reshape(3, 3)
        wz = float((r @ w)[2])
        jid = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_JOINT, "head_pitch")
        pitch = 0.0
        if jid >= 0:
            pitch = float(self.data.qvel[int(self.model.jnt_dofadr[jid])])
        return wz, pitch

    def privileged_sun(self):
        """Sun in the trunk frame from the simulator state. Baseline only."""
        rot = self.data.xmat[self.trunk].reshape(3, 3)
        origin = self.data.xpos[self.trunk]
        sun = rot.T @ (np.zeros(3) - origin)
        return float(sun[0]), float(sun[1])

    def perceive(self):
        self._flicker()
        self.ren.update_scene(self.data, camera="onboard")
        img = self.ren.render().copy()
        wz, pitch = self._rates()
        du = self.fx * wz * EXPOSURE_S
        dv = self.fy * pitch * EXPOSURE_S
        img = _blur(img, du, dv)
        if self.prev is not None and math.hypot(du, dv) > 2.0:
            img = (0.88 * img.astype(np.float32) + 0.12 * self.prev).astype(np.uint8)
        self.prev = img.copy()
        noisy = CD.degrade(img, self.rng, 1.0, False)
        t0 = time.perf_counter()
        raw = NF.find_nest(noisy, self.fx, self.fy, self.cx, self.cy, roi=getattr(self, "_roi", None))
        self.frame_ms.append((time.perf_counter() - t0) * 1000.0)
        est = {
            "seen": False,
            "clipped": bool(raw.get("clipped")),
            "cliff": bool(raw.get("cliff")),
            "obstacle": bool(raw.get("obstacle")),
            "obstacle_right": 0.0,
            "ring": bool(raw.get("ring")),
            "occluded": bool(raw.get("occluded")),
            "sun_fwd": None,
            "sun_left": None,
            "low": False,
        }
        if raw.get("v") is not None and raw.get("work_h"):
            stride = raw.get("stride") or 1
            est["low"] = (float(raw["v"]) / (float(raw["work_h"]) * stride)) > 0.72
        if raw.get("obstacle_u") is not None:
            est["obstacle_right"] = math.atan((float(raw["obstacle_u"]) - self.cx) / self.fx)
        if raw.get("seen") and raw.get("width_px"):
            rot, pos = self._rel_cam()
            sun = NF.sun_in_trunk(
                raw["u"], raw["v"], raw["width_px"], self.fx, self.fy, self.cx, self.cy, rot, pos,
                raw.get("ring_width_px"),
            )
            if sun is not None and sun["sun_fwd"] > 0.08:
                est["seen"] = True
                est["sun_fwd"] = sun["sun_fwd"]
                est["sun_left"] = sun["sun_left"]
                est["depth_m"] = sun["depth_m"]
                if raw.get("ring_yaw") is not None:
                    est["ring_yaw"] = float(raw["ring_yaw"])
                if raw.get("width_px"):
                    self._roi = (float(raw["u"]), float(raw["v"]), max(110.0, 5.0 * float(raw["width_px"])))
            else:
                self._roi = None
        else:
            self._roi = None
        shown = _draw(noisy, raw)
        return est, shown, raw

    def step_policy(self, cmd, capture=False, blur=False):
        m = self.m
        md, dd = self.model, self.data
        for _ in range(m.decimation):
            self.mujoco.mj_step(md, dd)
        self.t += CD.CTRL_DT
        hp = float(cmd[3]) if len(cmd) > 3 else 0.0
        hy = float(cmd[4]) if len(cmd) > 4 else 0.0
        hy = max(HEAD_YAW_LO, min(HEAD_YAW_HI, hy))
        m.commands = [float(cmd[0]), float(cmd[1]), float(cmd[2]), 0.0, hp, hy, 0.0]
        m.imitation_i = (m.imitation_i + m.phase_frequency_factor) % m.PRM.nb_steps_in_period
        ph = m.imitation_i / m.PRM.nb_steps_in_period * 2 * math.pi
        m.imitation_phase = np.array([math.cos(ph), math.sin(ph)])
        obs = m.get_obs(dd, m.commands)
        act = m.policy.infer(obs)
        m.last_last_last_action = m.last_last_action.copy()
        m.last_last_action = m.last_action.copy()
        m.last_action = act.copy()
        m.motor_targets = m.default_actuator + act * m.action_scale
        lim = m.max_motor_velocity * (m.sim_dt * m.decimation)
        m.motor_targets = np.clip(m.motor_targets, m.prev_motor_targets - lim, m.prev_motor_targets + lim)
        m.prev_motor_targets = m.motor_targets.copy()
        dd.ctrl[:] = m.motor_targets
        # The walk keeps the head level, and the crouch puts the disc on the
        # bottom edge of the frame. While docking, the head pitch target is
        # the look-down command. It stays inside the soft stop.
        aid = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_ACTUATOR, "head_pitch")
        if aid >= 0:
            lo, hi = self.model.actuator_ctrlrange[aid]
            dd.ctrl[aid] = min(hi, max(lo, hp if abs(hp) > 1e-4 else float(dd.ctrl[aid])))
        # Head yaw is a policy command during the walk. The policy does not
        # track it, so a standing search sweep drives the actuator itself.
        # Forcing that actuator while the body is also yawing tips the duck.
        standing = abs(float(cmd[0])) < 0.03 and abs(float(cmd[2])) < 0.08
        if standing and abs(hy) > 0.12:
            yid = self.mujoco.mj_name2id(self.model, self.mujoco.mjtObj.mjOBJ_ACTUATOR, "head_yaw")
            if yid >= 0:
                ylo, yhi = self.model.actuator_ctrlrange[yid]
                dd.ctrl[yid] = min(yhi, max(ylo, hy))
        self._integrate_gyro()
        x, y, yaw, z, up = self.true_pose()
        self._check_fall(z, up)
        return x, y, yaw

    def third(self):
        if self.ren3 is None:
            return None
        cam = self.mujoco.MjvCamera()
        cam.type = self.mujoco.mjtCamera.mjCAMERA_FREE
        p = self.data.xpos[self.trunk]
        cam.lookat[:] = [p[0], p[1], 0.12]
        cam.distance = 1.9
        cam.azimuth = 78
        cam.elevation = -18
        self.ren3.update_scene(self.data, cam)
        return self.ren3.render().copy()


def _spec_of(row):
    seed, x, y, yaw, room, cover, hazard = row
    return {
        "seed": seed, "x": x, "y": y, "yaw": yaw, "room": room,
        "cover": cover, "hazard": hazard,
    }


def due_estimate(queue, now, fresh, horizon=0.45):
    """The pose the controller may use.

    A disc fix is visible only after its queued time. A frame that has just
    been captured still contributes cliff and obstacle flags.
    """
    due = [e for (t, e) in queue if e is not None and t <= now and now - t < horizon]
    if due:
        use = dict(due[-1])
        if fresh is not None:
            use["cliff"] = fresh["cliff"]
            use["obstacle"] = fresh["obstacle"]
            use["obstacle_right"] = fresh["obstacle_right"]
        return use
    if fresh is None:
        return None
    held = _blank_est()
    held["cliff"] = fresh["cliff"]
    held["obstacle"] = fresh["obstacle"]
    held["obstacle_right"] = fresh["obstacle_right"]
    return held


def _blank_est():
    return {
        "seen": False, "clipped": False, "cliff": False, "obstacle": False,
        "obstacle_right": 0.0, "ring": False, "occluded": False,
        "sun_fwd": None, "sun_left": None,
    }


def _sit_once(sim):
    """Crouch, score, leave the gains saved so a miss can stand again.

    Returns (charging, sat, reason). The pose is the sit. Sim pass only.
    """
    target = CD._sit_targets(sim.model, sim.m)
    sim._gain = sim.model.actuator_gainprm.copy()
    sim._bias = sim.model.actuator_biasprm.copy()
    sim.go_pose(target, 3.0, sitting=True)
    sim.torque_off(1.2)
    if sim.fallen:
        return False, False, "fell"
    x, y, yaw, _, _ = sim.true_pose()
    scored = CD.score_wells(x, y, yaw)
    heading = abs(math.degrees(CD.wrap(yaw - math.pi)))
    geom = bool(scored["contacts_meet"] and heading < 25.0)
    elec = CD.score_charge(sim, x, y, yaw, geom)
    if geom and elec.get("charging"):
        return True, True, "docked"
    why = "sat_off" if not scored["contacts_meet"] else "heading"
    return False, True, why


def _back_out(sim):
    """Stand and walk away from the wall, then the loop searches again.

    After the half turn the duck faces the room, so forward is away from
    the nest. This policy has no reverse speed. About 2 s is the set point.
    """
    if getattr(sim, "_gain", None) is not None:
        sim.model.actuator_gainprm[:] = sim._gain
        sim.model.actuator_biasprm[:] = sim._bias
    # The crouch is below the walking fall check. Rise under the sit check,
    # then walk. Forward faces the room after the half turn.
    sim.sitting = True
    sim.go_pose(sim.m.default_actuator, 1.4, sitting=True)
    sim.sitting = False
    if sim.fallen:
        return
    t0 = sim.t
    while sim.t < t0 + 2.0 and not sim.fallen:
        err = CD.wrap(math.pi - sim.true_pose()[2])
        if abs(err) > 0.45:
            cmd = (0.0, 0.0, float(max(-0.50, min(0.50, 1.2 * err))), 0.0, 0.0)
        else:
            cmd = (0.12, 0.0, float(max(-0.30, min(0.30, 0.8 * err))), -0.35, 0.0)
        sim.step_policy(cmd)


def run_case(spec, privileged=False, record=False, limit_s=48.0):
    sim = DiscSim(spec, record=record)
    loop = DiscLoop()
    frames = []
    errs = []
    saw = 0
    rings = 0
    cliffs = 0
    obstacles = 0
    occluded = 0
    tries = 0
    try:
        CD._place(sim, spec["x"], spec["y"], math.radians(spec["yaw"]))
        k = 0
        sits = 0
        handled = False
        while sim.t < limit_s and not sim.fallen and sits < 3:
            if loop.phase in ("sit", "fail"):
                if loop.phase != "sit":
                    break
                sits += 1
                charged, sat_now, why = _sit_once(sim)
                handled = True
                sat = sat_now
                if charged:
                    reason = "docked"
                elif sat_now:
                    reason = why
                elif sim.fallen:
                    reason = "fell"
                if charged or sim.fallen or sits >= 3 or sim.t >= limit_s - 8.0:
                    sat = sat_now
                    if charged:
                        reason = "docked"
                    elif sat_now:
                        reason = why
                    break
                # A miss stands and walks away from the wall, then searches again.
                _back_out(sim)
                if sim.fallen:
                    # The crouch already happened. The fall is what ended it.
                    reason = "fell"
                    sat = False
                    break
                loop = DiscLoop()
                sim.est_q = []
                sim._last_fwd = None
                sim._last_left = None
                sim._roi = None
                continue
            fresh = None
            shown = None
            if privileged:
                fwd, left = sim.privileged_sun()
                use = _blank_est()
                use.update(seen=True, sun_fwd=fwd, sun_left=left, ring=True)
            else:
                if k % 2 == 0:
                    fresh, shown, raw = sim.perceive()
                    tries += 1
                    if fresh["seen"]:
                        # One frame cannot jump half a metre. That jump is a
                        # speck, not the disc. The last good fix stays in the queue.
                        last = getattr(sim, "_last_fwd", None)
                        last_l = getattr(sim, "_last_left", None)
                        jump = last is not None and abs(fresh["sun_fwd"] - last) > 0.45
                        slide = last_l is not None and abs(fresh["sun_left"] - last_l) > 0.40
                        if jump or slide:
                            fresh["seen"] = False
                        else:
                            sim._last_fwd = fresh["sun_fwd"]
                            sim._last_left = fresh["sun_left"]
                    if fresh["seen"]:
                        saw += 1
                        pf, pl = sim.privileged_sun()
                        errs.append((fresh["sun_fwd"] - pf, fresh["sun_left"] - pl))
                    if fresh.get("ring"):
                        rings += 1
                    if fresh.get("cliff"):
                        cliffs += 1
                    if fresh.get("obstacle"):
                        obstacles += 1
                    if fresh.get("occluded") and fresh.get("seen"):
                        occluded += 1
                    if record and shown is not None and k % 6 == 0:
                        wide = sim.third()
                        frames.append((wide, shown, loop.phase, fresh))
                    # 0.10 s delay, same window as the marker dock. A miss does
                    # not delete a fix that is still inside the window.
                    sim.est_q.append((sim.t + CD.LAT_S, fresh if fresh["seen"] else None))
                use = due_estimate(sim.est_q, sim.t, fresh)
            cmd = loop.command(use, sim.imu_yaw, CD.CTRL_DT)
            if os.environ.get("DISC_DEBUG") and k % 25 == 0:
                tp = sim.true_pose()
                print(
                    "t=%.1f %s cmd %s true %.2f %.2f %.0f est %s"
                    % (
                        sim.t, loop.phase, tuple(round(c, 2) for c in cmd),
                        tp[0], tp[1], math.degrees(tp[2]),
                        None if not (use and use.get("seen")) else (round(use["sun_fwd"], 2), round(use["sun_left"], 2)),
                    ),
                    flush=True,
                )
            sim.step_policy(cmd)
            k += 1
        if not handled:
            sat = False
            reason = loop.reason or "timeout"
            if sim.fallen:
                reason = "fell"
        # A fall while standing, backing out, or searching again is not the
        # earlier missed sit. sat_off and heading are only for a duck that
        # is still up.
        sat, reason = fall_outranks_sit(sat, reason, bool(sim.fallen))
        x, y, yaw, z, up = sim.true_pose()
        scored = CD.score_wells(x, y, yaw)
        heading = abs(math.degrees(CD.wrap(yaw - math.pi)))
        ok = bool(sat and scored["contacts_meet"] and not sim.fallen and heading < 25.0)
        elec = CD.score_charge(sim, x, y, yaw, ok)
        if ok and elec.get("charging"):
            reason = "docked"
        elif sat and not ok:
            reason = "sat_off" if not scored["contacts_meet"] else "heading"
        err_fwd = None
        err_left = None
        if errs:
            err_fwd = float(np.median([e[0] for e in errs]))
            err_left = float(np.median([e[1] for e in errs]))
        ms = None
        if sim.frame_ms:
            ms = float(np.median(sim.frame_ms))
        row = dict(
            seed=int(spec["seed"]),
            privileged=bool(privileged),
            source="privileged" if privileged else "camera",
            room=spec["room"],
            cover=bool(spec["cover"]),
            hazard=bool(spec["hazard"]),
            start=[round(spec["x"], 3), round(spec["y"], 3), round(spec["yaw"], 1)],
            ok=bool(ok and elec.get("charging")),
            charging=bool(elec.get("charging")),
            reason=reason,
            t_s=round(sim.t, 2),
            sits=int(sits),
            fell=bool(sim.fallen),
            sat=bool(sat),
            saw_frac=round(saw / tries, 3) if tries else None,
            ring_frac=round(rings / tries, 3) if tries else None,
            cliff_frames=cliffs,
            obstacle_frames=obstacles,
            occluded_frames=occluded,
            err_fwd_m=None if err_fwd is None else round(err_fwd, 3),
            err_left_m=None if err_left is None else round(err_left, 3),
            frame_ms=None if ms is None else round(ms, 2),
            true=[round(x, 3), round(y, 3), round(math.degrees(yaw), 1)],
            label="sim pass only",
            **{k: scored[k] for k in ("contacts_meet", "align_mm", "yaw_err_deg", "stripe_margin_mm")},
        )
        return row, frames
    finally:
        sim.close()


class CameraOutcomes:
    """The object the autonomy supervisor calls for one live dock.

    dock() is the closed loop. Pass privileged=True only for the baseline
    that is allowed to read the true sun.
    """

    def __init__(self, spec, privileged=False):
        self.spec = spec
        self.privileged = privileged
        self.row = None

    def dock(self):
        self.row, _frames = run_case(self.spec, privileged=self.privileged, record=False)
        return {
            "seed": self.row["seed"],
            "t_s": self.row["t_s"],
            "charging": self.row["charging"],
            "reason": self.row["reason"],
            "fell": self.row["fell"],
            "source": self.row["source"],
        }

    def getup(self):
        return True


def _label(draw, text, xy, fill):
    draw.text(xy, text, fill=fill)


def compose(wide, cam, phase, est):
    from PIL import Image, ImageDraw, ImageFont
    canvas = Image.new("RGB", (980, 420), (24, 26, 28))
    if wide is not None:
        canvas.paste(Image.fromarray(wide), (16, 36))
    ch, cw = cam.shape[:2]
    scale = 360 / float(ch)
    cam_w = int(cw * scale)
    cam_i = Image.fromarray(cam).resize((cam_w, 360))
    canvas.paste(cam_i, (980 - cam_w - 16, 36))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except OSError:
        font = ImageFont.load_default()
        small = font
    _label(draw, "SIM", (16, 8), (255, 220, 80))
    _label(draw, "sim pass only", (70, 10), (220, 220, 220))
    _label(draw, "third person", (16, 400), (200, 200, 200))
    seen = "disc" if est and est.get("seen") else "no disc"
    if est and est.get("ring"):
        seen += " + ring"
    if est and est.get("cliff"):
        seen += " CLIFF"
    if est and est.get("obstacle"):
        seen += " OBS"
    _label(draw, "head camera  " + phase + "  " + seen, (980 - cam_w - 16, 400), (200, 200, 200))
    del small
    return np.asarray(canvas)


def write_video(frames, path):
    if not frames:
        return None
    os.makedirs(os.path.dirname(path), exist_ok=True)
    shots = [compose(*fr) for fr in frames]
    h, w = shots[0].shape[:2]
    cmd = [
        "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", "%dx%d" % (w, h), "-r", "8", "-i", "-",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "32",
        "-preset", "veryfast", "-movflags", "+faststart", path,
    ]
    import subprocess
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for fr in shots:
        proc.stdin.write(np.ascontiguousarray(fr).tobytes())
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0 or not os.path.isfile(path):
        raise SystemExit("video encode failed")
    if os.path.getsize(path) > 5_000_000:
        raise SystemExit("video over 5 MB")
    return path


def write_result(rows, still, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cam = [r for r in rows if r["source"] == "camera"]
    priv = [r for r in rows if r["source"] == "privileged"]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.4))
    if still is not None:
        axes[0].imshow(still)
    axes[0].set_title("SIM  sim pass only  head camera")
    axes[0].axis("off")
    labels = ["camera", "privileged"]
    vals = [
        sum(1 for r in cam if r["charging"]),
        sum(1 for r in priv if r["charging"]),
    ]
    ns = [len(cam), len(priv)]
    axes[1].bar(labels, vals, color=("#c48a2a", "#3d6b8c"))
    for i, (v, n) in enumerate(zip(vals, ns)):
        axes[1].text(i, v + 0.05, "%d / %d" % (v, n), ha="center")
    axes[1].set_ylim(0, max(ns + [1]) + 0.8)
    axes[1].set_ylabel("charging docks")
    axes[1].set_title("sim pass only")
    fig.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def summarize(rows):
    def pack(group):
        n = len(group)
        hit = sum(1 for r in group if r["charging"])
        reasons = {}
        for r in group:
            if not r["charging"]:
                reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
        ms = [r["frame_ms"] for r in group if r.get("frame_ms")]
        return {
            "n": n,
            "charging": hit,
            "rate": None if not n else round(hit / n, 3),
            "failures": reasons,
            "frame_ms_median": None if not ms else round(float(np.median(ms)), 2),
            "label": "sim pass only",
        }
    cam = [r for r in rows if r["source"] == "camera"]
    priv = [r for r in rows if r["source"] == "privileged"]
    return {"camera": pack(cam), "privileged": pack(priv)}


def probe(spec=None):
    spec = spec or _spec_of(CASES[0])
    sim = DiscSim(spec, record=False)
    try:
        CD._place(sim, spec["x"], spec["y"], math.radians(spec["yaw"]))
        # A short look-down so the frame is the head the loop uses, not only the keyframe.
        for _ in range(15):
            sim.step_policy((0.0, 0.0, 0.0, -0.35))
        est, shown, raw = sim.perceive()
        fwd, left = sim.privileged_sun()
        print("hfov", round(sim.hfov, 2), "est", est, "true_fwd", round(fwd, 3), "true_left", round(left, 3))
        print("raw seen", raw.get("seen"), "width", raw.get("width_px"), "ring", raw.get("ring"), "ms", sim.frame_ms)
        out = os.environ.get("DISC_PROBE_PNG")
        if out:
            from PIL import Image
            Image.fromarray(shown).save(out)
            print("wrote", os.path.basename(out))
    finally:
        sim.close()


def forty_specs():
    """The card dock's 40 starts, with a room, a cover, and a side hazard.

    The poses are STARTS and STARTS_NEW in camera_dock.py. The lamp, the
    felt card, and the side box are this file's. Two retries, same rule as
    the card batch (retries < 2).
    """
    rooms = ("day", "warm", "dim", "cool")
    specs = []
    for seed, x, y, yaw, _light in list(CD.STARTS) + list(CD.STARTS_NEW):
        specs.append({
            "seed": int(seed),
            "x": float(x),
            "y": float(y),
            "yaw": float(yaw),
            "room": rooms[(int(seed) - 1) % 4],
            "cover": int(seed) % 3 == 0,
            "hazard": int(seed) % 2 == 0,
        })
    return specs


def run_retries(spec, privileged, tries=1, limit_s=70.0):
    """One episode. A failed sit stands, backs away, and tries again inside it.

    Repeating the same start from scratch was deterministic, so those retries
    never changed the result. tries is kept so older callers still run.
    """
    last = None
    for attempt in range(max(1, int(tries))):
        row, _frames = run_case(spec, privileged=privileged, record=False, limit_s=limit_s)
        row = dict(row)
        row["attempt"] = int(row.get("sits") or attempt + 1)
        last = row
        if row.get("charging"):
            break
    return last


def _forty_job(job):
    spec, privileged, limit_s = job
    os.environ.setdefault("MUJOCO_GL", "osmesa")
    row = run_retries(spec, privileged, limit_s=limit_s)
    print(
        "%s seed %d %s try %s %s yaw %s"
        % (row["source"], row["seed"], row["room"], row["attempt"], row["reason"], row.get("yaw_err_deg")),
        flush=True,
    )
    return row


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--probe", action="store_true")
    p.add_argument("--batch", action="store_true")
    p.add_argument("--forty", action="store_true")
    p.add_argument("--video", action="store_true")
    p.add_argument("--n", type=int, default=8)
    p.add_argument("--jobs", type=int, default=3)
    p.add_argument("--limit", type=float, default=48.0)
    p.add_argument("--out", default=os.path.join(os.path.dirname(__file__)))
    args = p.parse_args()
    if args.probe:
        probe()
        return
    if args.forty:
        import multiprocessing as mp
        jobs = []
        for spec in forty_specs():
            jobs.append((spec, False, args.limit))
            jobs.append((spec, True, args.limit))
        ctx = mp.get_context("spawn")
        rows = []
        with ctx.Pool(max(1, args.jobs)) as pool:
            for row in pool.imap_unordered(_forty_job, jobs):
                rows.append(row)
        rows.sort(key=lambda r: (r["source"], r["seed"]))
        summary = summarize(rows)
        payload = {"summary": summary, "rows": rows, "label": "sim pass only", "retries": 2}
        with open(os.path.join(args.out, "disc_batch.json"), "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1, sort_keys=True)
            handle.write("\n")
        # A search that starts facing away, camera view, if one charged.
        behind = [
            r for r in rows
            if r["source"] == "camera" and r["charging"] and abs(r["start"][2]) >= 70.0
        ]
        pick = behind[0] if behind else next((r for r in rows if r["source"] == "camera" and r["charging"]), None)
        still = None
        if pick is not None:
            spec = next(s for s in forty_specs() if s["seed"] == pick["seed"])
            _row, frames = run_case(spec, privileged=False, record=True, limit_s=args.limit)
            for wide, cam, phase, est in frames:
                if est and est.get("seen"):
                    still = compose(wide, cam, phase, est)
                    break
            if still is None and frames:
                still = compose(*frames[0])
            if frames:
                write_video(frames, os.path.join(args.out, "disc_dock_sim.mp4"))
        if still is not None:
            write_result(rows, still, os.path.join(args.out, "disc_dock_result.png"))
        print(json.dumps(summary, sort_keys=True))
        return
    if not args.batch and not args.video:
        p.error("pass --probe, --batch, or --video")
    rows = []
    still = None
    video_frames = None
    cases = [_spec_of(row) for row in CASES[: args.n]]
    if args.batch:
        for spec in cases:
            for privileged in (False, True):
                row, frames = run_case(spec, privileged=privileged, record=False, limit_s=args.limit)
                rows.append(row)
                print(
                    "%s seed %d %s t=%.1f %s" % (row["source"], row["seed"], row["room"], row["t_s"], row["reason"]),
                    flush=True,
                )
        # One recorded camera pass for the picture. Prefer a charge, else seed 1.
        pick = next((r for r in rows if r["source"] == "camera" and r["charging"]), None)
        if pick is None:
            pick = next(r for r in rows if r["source"] == "camera")
        spec = next(s for s in cases if s["seed"] == pick["seed"])
        row, frames = run_case(spec, privileged=False, record=True, limit_s=args.limit)
        video_frames = frames
        still = None
        for wide, cam, phase, est in frames:
            if est and est.get("seen"):
                still = compose(wide, cam, phase, est)
                break
        if still is None and frames:
            still = compose(*frames[0])
        summary = summarize(rows)
        payload = {"summary": summary, "rows": rows, "label": "sim pass only"}
        with open(os.path.join(args.out, "disc_batch.json"), "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1, sort_keys=True)
            handle.write("\n")
        if still is not None:
            write_result(rows, still, os.path.join(args.out, "disc_dock_result.png"))
        if video_frames:
            write_video(video_frames, os.path.join(args.out, "disc_dock_sim.mp4"))
        print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
