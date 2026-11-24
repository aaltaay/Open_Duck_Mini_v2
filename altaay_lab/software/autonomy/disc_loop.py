"""Joystick commands from a nest estimate. No simulator and no world pose.

sun_fwd and sun_left are metres in the trunk frame: x forward, y left.
They come from the head camera (software/perception/nest_find.py) or, in the
privileged baseline only, from the true sun. This file does not know which.

The sit distance is a set point. The gold-dome score is applied after the
sit by the caller. Positive yaw rate turns toward +y, the same sign as the
camera dock.
"""

from __future__ import annotations

import math

# Trunk-to-sun distance at which the half turn starts. Set point.
# A walk-in to about 0.40 m, then the side-step yaw, puts the seat on the
# stripes with the heading inside 25 deg (checked in sim). Closer than this
# the yaw dies on the wall.
SIT_FWD_M = 0.40
LAT_OK_M = 0.10
# IMU radians of the half turn. 3.10 rad is 178 deg. The yaw rate is
# 0.45 so the side step has time to put the seat on the foil. Faster
# than that, the sit finishes short of the wells.
TURN_RAD = 3.10
# Look down while the cloth is on the floor. -0.35 rad is -20.1 deg, inside
# the -22 deg software stop (servo_limits.json, cited as the soft stop).
HEAD_DOWN = -0.35
# Head yaw software stops, same file, soft_lo_deg and soft_hi_deg. Cited.
HEAD_YAW_LO = math.radians(-105.0)
HEAD_YAW_HI = math.radians(79.0)
# How long a glimpsed bearing is still worth walking toward. Set point.
MEM_S = 6.0
VX_MAX = 0.18
VY_MAX = 0.12
WZ_MAX = 0.80


def wrap(a):
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def _clip(v, lo, hi):
    return float(max(lo, min(hi, v)))


def _obs_left(head_yaw, image_right):
    """Obstacle bearing in the trunk, left positive.

    image_right is the angle from the camera axis toward image right.
    A positive head yaw looks left, so it adds to that trunk bearing.
    """
    return wrap(float(head_yaw) - float(image_right))


class DiscLoop:
    def __init__(self):
        self.phase = "search"
        self.reason = ""
        self.spin = 1.0
        self.t = 0.0
        self.t_phase = 0.0
        self.ever_seen = False
        self.last_fwd = None
        self.last_left = None
        self.creep_left = 0.0
        self.turn0 = None
        self.nudge0 = None
        self.ok_n = 0
        self.spin_t = -10.0
        self.spin_yaw = 0.0
        self.kick_until = -1.0
        self.kicks = 0
        self.mem_b = None
        self.mem_imu = 0.0
        self.mem_t = None
        self.head_cmd = 0.0
        # "sweep" looks around while standing. "spin" turns the body.
        self.scan = "sweep"
        self.turn_clock = None
        self.saw_behind = False
        self.closed = False
        self.kick_age0 = None

    def _sweep(self):
        """Triangle inside the head-yaw software stops. Set point amplitude.

        The stops are -105 deg and +79 deg. Holding both a stop and the
        look-down pitch tips the sim duck, so the sweep is ±0.90 rad,
        which is inside those stops.
        """
        amp = 0.90
        period = 6.0
        phase = (self.t % period) / period
        if phase < 0.5:
            u = phase * 2.0
        else:
            u = (1.0 - phase) * 2.0
        return -amp + u * (2.0 * amp)

    def _note(self, est, imu_yaw):
        if not est or not est.get("seen") or est.get("clipped") or est.get("sun_fwd") is None:
            return
        self.mem_b = math.atan2(float(est["sun_left"]), float(est["sun_fwd"]))
        self.mem_imu = float(imu_yaw)
        self.mem_t = self.t
        self.ever_seen = True
        self.last_fwd = float(est["sun_fwd"])
        self.last_left = float(est["sun_left"])

    def _begin_turn(self, imu_yaw):
        self.phase = "turn"
        self.turn0 = float(imu_yaw)
        self.turn_clock = self.t
        self.t_phase = self.t
        self.kicks = 0
        self.spin_t = self.t
        self.spin_yaw = float(imu_yaw)
        self.closed = False

    def _behind(self, est, imu_yaw):
        """True when the last disc fix, carried by the IMU, is behind the trunk.

        A fresh fix with the sun in front of the nose is not behind. The
        memory is not dropped on the 6 s timer here: the half turn is longer
        than that, and the gate needs the bearing from when the disc was seen.
        """
        if est and est.get("seen") and est.get("sun_fwd") is not None:
            if float(est["sun_fwd"]) < -0.02:
                self.saw_behind = True
            return float(est["sun_fwd"]) < -0.02
        if self.mem_b is None:
            return bool(self.saw_behind)
        rec = wrap(self.mem_b - wrap(float(imu_yaw) - self.mem_imu))
        return abs(rec) > 2.2 or bool(self.saw_behind)

    def _recall(self, imu_yaw):
        """Last nest bearing in the current trunk frame, or None if it is stale."""
        if self.mem_t is None or self.t - self.mem_t > MEM_S or self.mem_b is None:
            return None
        return wrap(self.mem_b - wrap(float(imu_yaw) - self.mem_imu))

    def command(self, est, imu_yaw, dt):
        """Return (vx, vy, wz, head_pitch, head_yaw). est is a dict or None.

        A cliff flag in front stops the forward speed. An obstacle flag near
        the middle of the frame yaws away. Neither one is a world pose.
        Head yaw stays inside the software stops.
        """
        self.t += float(dt)
        imu_yaw = float(imu_yaw)
        seen = bool(est and est.get("seen") and not est.get("clipped") and est.get("sun_fwd") is not None)
        cliff = bool(est and est.get("cliff"))
        obstacle = bool(est and est.get("obstacle"))
        obs_right = float(est.get("obstacle_right") or 0.0) if est else 0.0
        self._note(est, imu_yaw)
        cmd = [0.0, 0.0, 0.0, HEAD_DOWN, 0.0]

        if self.phase == "search":
            if seen and est["sun_fwd"] > 0.15:
                self.phase = "approach"
                self.t_phase = self.t
            else:
                recalled = self._recall(imu_yaw)
                if recalled is not None and abs(recalled) <= 0.35:
                    cmd[0] = 0.14
                    cmd[2] = _clip(1.2 * recalled, -0.45, 0.45)
                    cmd[4] = 0.0
                    self.scan = "spin"
                elif recalled is not None:
                    # Turn the body onto the remembered bearing. The head
                    # stays near the middle so the gait keeps yawing.
                    cmd[2] = _clip(1.1 * recalled, -0.55, 0.55)
                    cmd[4] = 0.0
                    self.scan = "spin"
                elif self.scan == "sweep" and self.t - self.t_phase < 3.2:
                    # Standing look. The sweep stays inside the software
                    # stops. A body yaw at the same time stalls this gait,
                    # so the turn comes after the head is back at center.
                    cmd[2] = 0.0
                    cmd[4] = self._sweep()
                elif self.scan == "sweep":
                    cmd[4] = 0.0
                    if abs(self.head_cmd) < 0.10:
                        self.scan = "spin"
                        self.t_phase = self.t
                        self.spin_t = self.t
                        self.spin_yaw = imu_yaw
                else:
                    # Slow turn in place. Negative yaw is the rate this
                    # policy actually follows with no forward speed.
                    cmd[2] = 0.55 * self.spin
                    cmd[4] = 0.0
                if self.t > 26.0 and not self.ever_seen:
                    self.phase = "fail"
                    self.reason = "no_marker"
        elif self.phase == "approach":
            if seen and est["sun_fwd"] > 0.05:
                self.ever_seen = True
                fwd = float(est["sun_fwd"])
                left = float(est["sun_left"])
                self.last_fwd = fwd
                self.last_left = left
                # Aim a few centimetres to the right of the disc so the
                # left half-turn starts from a heading that lands near 180 deg.
                # A start with the disc still off to the right undershoots.
                aim = left - 0.06
                bearing = math.atan2(aim, fwd)
                dist = math.hypot(fwd, left)
                near = dist <= SIT_FWD_M and abs(left) <= LAT_OK_M
                if cliff and abs(bearing) < 0.50:
                    cmd[0] = 0.0
                    cmd[2] = 0.45 * self.spin
                elif obstacle and abs(obs_right) < 0.30 and abs(wrap(_obs_left(self.head_cmd, obs_right) - math.atan2(left, fwd))) > 0.15:
                    # obstacle_right is image-right positive. The disc bearing
                    # is trunk-left positive. Convert before comparing, and
                    # include the head yaw the camera was looking through.
                    # Positive yaw is a left turn. An obstacle on the image
                    # right is left behind by turning left. A flag on the
                    # disc itself is not a side hazard.
                    cmd[0] = 0.0
                    cmd[2] = 0.50 if obs_right > 0.0 else -0.50
                elif near and -0.20 <= bearing <= 0.22:
                    # Same range as the old half-turn start. A short look
                    # at the disc and the ring squares the heading first.
                    self.phase = "line"
                    self.t_phase = self.t
                    self.line_ok = 0
                elif near and bearing < -0.20:
                    cmd[0] = 0.0
                    cmd[2] = _clip(1.2 * bearing, -0.50, -0.20)
                elif near and bearing > 0.22:
                    cmd[0] = 0.0
                    cmd[2] = _clip(1.0 * bearing, 0.20, 0.45)
                elif abs(bearing) > 0.28 or abs(left) > 0.16:
                    # Square up before closing. Walking a sideways fix into
                    # the wall starts the half turn already off the line.
                    cmd[2] = _clip(1.4 * bearing, -WZ_MAX, WZ_MAX)
                    if abs(bearing) < 0.20:
                        cmd[0] = 0.08
                else:
                    # Well inside the sit distance, the old 0.14 m/s floor
                    # walked the duck into the wall. The turn gate is at
                    # 0.40 m, so the stop is inside that, not in front of it.
                    if dist <= SIT_FWD_M - 0.06:
                        cmd[0] = 0.0
                    else:
                        cmd[0] = _clip(0.90 * (dist - SIT_FWD_M), 0.10, VX_MAX)
                    cmd[1] = _clip(0.55 * aim, -VY_MAX, VY_MAX)
                    cmd[2] = _clip(1.15 * bearing, -0.60, 0.60)
            elif self.last_fwd is not None and self.last_fwd <= 0.85:
                # The disc has left the frame. Turn only if the last bearing
                # was already on the line. Otherwise yaw onto that memory.
                recalled = self._recall(imu_yaw)
                on_line = recalled is None or -0.22 <= recalled <= 0.24
                if recalled is not None and not on_line:
                    cmd[0] = 0.0
                    cmd[2] = _clip(1.2 * recalled, -0.55, 0.55)
                elif self.last_fwd <= 0.60 and on_line:
                    self._begin_turn(imu_yaw)
                else:
                    self.phase = "creep"
                    self.creep_left = min(0.18, max(0.0, self.last_fwd - SIT_FWD_M))
                    self.t_phase = self.t
            elif self.last_fwd is not None and self.last_fwd < 1.40:
                self.phase = "creep"
                self.creep_left = min(0.20, max(0.0, self.last_fwd - SIT_FWD_M))
                self.t_phase = self.t
            else:
                cmd[2] = 0.45 * self.spin
                if self.t - self.t_phase > 8.0:
                    self.phase = "search"
                    self.scan = "sweep"
                    self.t_phase = self.t
            if self.phase == "approach" and self.t - self.t_phase > 26.0:
                self.phase = "fail"
                self.reason = "missed_line"
        elif self.phase == "creep":
            if cliff:
                cmd[0] = 0.0
                cmd[2] = 0.45 * self.spin
            elif seen and est["sun_fwd"] > 0.05:
                self.phase = "approach"
                self.t_phase = self.t
            elif self.creep_left <= 0.03:
                self._begin_turn(imu_yaw)
            else:
                cmd[0] = 0.14
                if self.last_left is not None:
                    cmd[1] = _clip(0.40 * self.last_left, -0.06, 0.06)
                self.creep_left -= 0.14 * float(dt)
            if self.phase == "creep" and self.t - self.t_phase > 7.0:
                self._begin_turn(imu_yaw)
        elif self.phase == "line":
            # Head is already pitched down. Centroid is the lateral offset.
            # Ring major-axis angle is the yaw when it agrees with that.
            # At most 1.5 s, then the same half turn as before.
            cmd[3] = HEAD_DOWN
            fwd = left = None
            if seen and est.get("sun_fwd") is not None:
                fwd = float(est["sun_fwd"])
                left = float(est["sun_left"])
            bear = 0.0 if fwd is None else math.atan2(left, max(fwd, 0.05))
            yaw_e = None if not est else est.get("ring_yaw")
            if yaw_e is None or fwd is None or abs(float(yaw_e)) > 0.35 or abs(wrap(float(yaw_e) - bear)) > 0.25:
                yaw_e = bear
            else:
                yaw_e = 0.5 * float(yaw_e) + 0.5 * bear
            aligned = abs(yaw_e) <= 0.10 and (left is None or abs(left) <= 0.05)
            # Time is the budget. A call count of 8 is 0.16 s at the
            # 0.02 s step, which ended the correction before it moved.
            if aligned or self.t - self.t_phase > 1.5:
                self._begin_turn(imu_yaw)
            elif abs(yaw_e) > 0.10:
                cmd[2] = _clip(1.0 * yaw_e, -0.35, 0.35)
            elif left is not None:
                cmd[1] = _clip(0.6 * left, -0.06, 0.06)
        elif self.phase == "turn":
            cmd[3] = 0.0
            turned = abs(wrap(imu_yaw - (self.turn0 or 0.0)))
            behind = self._behind(est, imu_yaw)
            seen_now = bool(est and est.get("seen") and est.get("sun_fwd") is not None)
            far = seen_now and float(est["sun_fwd"]) < -0.02 and abs(float(est["sun_fwd"])) > 0.38
            # The crouch waits until the IMU has finished the half turn and
            # the disc is behind the nose, and not still half a metre out.
            # A timeout used to sit the duck around a right angle.
            done = turned >= (TURN_RAD - 0.18) and behind and not far
            cap = self.t - (self.turn_clock if self.turn_clock is not None else self.t_phase)
            if done:
                self.phase = "nudge"
                self.t_phase = self.t
                self.nudge0 = imu_yaw
                self.ok_n = 0
            elif cap > 16.0:
                if not self.closed:
                    self.phase = "close"
                    self.t_phase = self.t
                    self.closed = True
                else:
                    self.phase = "fail"
                    self.reason = "short_turn"
            else:
                if self.t - self.spin_t > 1.0:
                    moved = abs(wrap(imu_yaw - self.spin_yaw))
                    # The gait's yaw dies near a right angle if the feet
                    # settle into a stance. A pause then a step restarts it.
                    if moved < 0.08 and self.kicks < 3:
                        self.phase = "rekick"
                        self.kick_age0 = self.t
                        self.kicks += 1
                    self.spin_t = self.t
                    self.spin_yaw = imu_yaw
                # Side step keeps the yaw alive and walks the seat in.
                # Ease it off once the sun is behind, or it walks through the wall.
                cmd[2] = 0.55
                # Keep the side step until the sun is actually behind the
                # nose. Cutting it when the sun is merely abeam leaves the
                # seat short of the foil.
                if seen_now and float(est["sun_fwd"]) < -0.12 and not far:
                    cmd[1] = -0.03
                else:
                    cmd[1] = -0.10
        elif self.phase == "rekick":
            # Pause, then one step with the yaw on. The turn angle is kept.
            cmd[3] = 0.0
            age = self.t - (self.kick_age0 or self.t)
            if age < 0.25:
                pass
            elif age < 0.70:
                cmd[0] = 0.12
                cmd[2] = 0.55
            else:
                self.phase = "turn"
                self.spin_t = self.t
                self.spin_yaw = imu_yaw
        elif self.phase == "close":
            # The turn ran out of time and the disc is still in front, so
            # the seat is short of the foil. One step toward that bearing,
            # then the turn resumes. Not a reverse: this policy has none.
            cmd[3] = 0.0
            age = self.t - self.t_phase
            rec = self._recall(imu_yaw)
            if rec is None and self.mem_b is not None:
                rec = wrap(self.mem_b - wrap(imu_yaw - self.mem_imu))
            if age > 0.55:
                self.phase = "turn"
                self.spin_t = self.t
                self.spin_yaw = imu_yaw
            else:
                cmd[0] = 0.12
                if rec is not None and abs(rec) < 1.3:
                    cmd[2] = _clip(1.0 * rec, -0.40, 0.40)
        elif self.phase == "nudge":
            # Pure yaw only. A side step here, with the duck already facing
            # the room, walks along the wall instead of onto the foil.
            cmd[3] = 0.0
            age = self.t - self.t_phase
            more = abs(wrap(imu_yaw - (self.nudge0 if self.nudge0 is not None else imu_yaw)))
            if more >= 0.10 or age > 1.2:
                self.phase = "trim"
                self.t_phase = self.t
                self.ok_n = 0
            else:
                cmd[2] = 0.40
        elif self.phase == "trim":
            # The sun is behind the duck once the half turn is done. A small
            # yaw puts that bearing on the center line before the sit. The
            # camera path usually has no fix here, and trims for only a moment.
            cmd[3] = 0.0
            err = None
            if seen and est.get("sun_fwd") is not None:
                # Zero when the sun is straight behind. Near pi while it is still ahead.
                # A positive body yaw moves a sun that is already behind further
                # to the left, so the correction is the opposite of this error.
                err = math.atan2(float(est["sun_left"]), -float(est["sun_fwd"]))
            if err is None or abs(err) < 0.10 or self.t - self.t_phase > 8.0:
                self.phase = "settle"
                self.t_phase = self.t
                self.ok_n = 0
            else:
                cmd[2] = _clip(-1.3 * err, -0.40, 0.40)
        elif self.phase == "settle":
            cmd = [0.0, 0.0, 0.0, 0.0, 0.0]
            self.ok_n += 1
            if self.ok_n >= 6:
                self.phase = "sit"
                self.reason = "sat"
        elif self.phase in ("sit", "fail"):
            cmd = [0.0, 0.0, 0.0, 0.0, 0.0]

        if self.phase in ("search", "turn") and abs(cmd[2]) >= 0.40 and cmd[0] < 0.05:
            if self.t - self.spin_t > 1.2:
                moved = abs(wrap(imu_yaw - self.spin_yaw))
                if moved < 0.10 and self.kicks < 4:
                    self.kick_until = self.t + 0.40
                    self.kicks += 1
                    # The second stall means this yaw sign is not the one
                    # the gait is following. Try the other way.
                    if self.phase == "search" and self.kicks >= 2:
                        self.spin = -self.spin
                self.spin_t = self.t
                self.spin_yaw = imu_yaw
            if self.t < self.kick_until and abs(cmd[4]) < 0.7:
                # A short step restarts a stalled yaw. The yaw stays on.
                # Zeroing it left the duck walking away from the nest.
                if self.phase == "turn":
                    cmd[0] = 0.10
                    cmd[2] = 0.55
                else:
                    cmd[0] = 0.08
                    if self.kicks >= 2:
                        cmd[2] = 0.55 * self.spin
        # Slew the head. A step to the software stop tips the walk.
        desired = _clip(cmd[4], HEAD_YAW_LO, HEAD_YAW_HI)
        step = 1.2 * float(dt)
        self.head_cmd += max(-step, min(step, desired - self.head_cmd))
        self.head_cmd = _clip(self.head_cmd, HEAD_YAW_LO, HEAD_YAW_HI)
        cmd[4] = self.head_cmd
        return (float(cmd[0]), float(cmd[1]), float(cmd[2]), float(cmd[3]), float(cmd[4]))
