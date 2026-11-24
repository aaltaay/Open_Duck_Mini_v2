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
                elif obstacle and abs(obs_right) < 0.30 and abs(obs_right - bearing) > 0.22:
                    # Positive yaw is a left turn. An obstacle on the image
                    # right (positive) is left behind by turning left.
                    # A flag on the disc itself is not a side hazard.
                    cmd[2] = 0.50 if obs_right > 0.0 else -0.50
                elif near and -0.20 <= bearing <= 0.22:
                    self.phase = "turn"
                    self.turn0 = imu_yaw
                    self.t_phase = self.t
                    self.kicks = 0
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
                    cmd[0] = _clip(0.90 * (dist - SIT_FWD_M), 0.14, VX_MAX)
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
                    self.phase = "turn"
                    self.turn0 = imu_yaw
                    self.t_phase = self.t
                    self.kicks = 0
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
                self.phase = "turn"
                self.turn0 = imu_yaw
                self.t_phase = self.t
                self.kicks = 0
            else:
                cmd[0] = 0.14
                if self.last_left is not None:
                    cmd[1] = _clip(0.40 * self.last_left, -0.06, 0.06)
                self.creep_left -= 0.14 * float(dt)
            if self.phase == "creep" and self.t - self.t_phase > 7.0:
                self.phase = "turn"
                self.turn0 = imu_yaw
                self.t_phase = self.t
                self.kicks = 0
        elif self.phase == "turn":
            cmd[3] = 0.0
            turned = abs(wrap(imu_yaw - (self.turn0 or 0.0)))
            if turned > TURN_RAD or self.t - self.t_phase > 22.0:
                self.phase = "nudge"
                self.t_phase = self.t
                self.nudge0 = imu_yaw
                self.ok_n = 0
            else:
                # A pure yaw dies near a right angle on this policy. A small
                # side command keeps the gait turning. It is eased off once
                # the turn is past that point, or it walks into the wall.
                # The side step is what walks the seat onto the foil while the
                # yaw is still changing. Too small and the sit is short of
                # the wells. Too large and the duck walks into the wall.
                cmd[1] = -0.09 if turned < 2.0 else -0.02
                cmd[2] = 0.45
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
                err = math.atan2(float(est["sun_left"]), -float(est["sun_fwd"]))
            if err is None or abs(err) < 0.10 or self.t - self.t_phase > 8.0:
                self.phase = "settle"
                self.t_phase = self.t
                self.ok_n = 0
            else:
                cmd[2] = _clip(1.3 * err, -0.40, 0.40)
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
