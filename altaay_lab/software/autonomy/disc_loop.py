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
# Closer than this the gait stalls on the wall and the yaw dies. A turn
# from here, with a small side command, finishes facing the room and the
# seat lands on the stripes (calc only, camera_dock.SEAT_X, checked in sim).
SIT_FWD_M = 0.42
LAT_OK_M = 0.09
# IMU radians of that half turn. 2.80 rad is 160 deg.
TURN_RAD = 2.80
# Look down while the cloth is on the floor. -0.35 rad is -20.1 deg, inside
# the -22 deg software stop (servo_limits.json, cited as the soft stop).
HEAD_DOWN = -0.35
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
        self.ok_n = 0
        self.spin_t = -10.0
        self.spin_yaw = 0.0
        self.kick_until = -1.0
        self.kicks = 0

    def command(self, est, imu_yaw, dt):
        """Return (vx, vy, wz, head_pitch). est is a dict or None.

        A cliff flag in front stops the forward speed. An obstacle flag near
        the middle of the frame yaws away. Neither one is a world pose.
        """
        self.t += float(dt)
        imu_yaw = float(imu_yaw)
        seen = bool(est and est.get("seen") and not est.get("clipped") and est.get("sun_fwd") is not None)
        cliff = bool(est and est.get("cliff"))
        obstacle = bool(est and est.get("obstacle"))
        obs_right = float(est.get("obstacle_right") or 0.0) if est else 0.0
        cmd = [0.0, 0.0, 0.0, HEAD_DOWN]

        if self.phase == "search":
            if seen and est["sun_fwd"] > 0.15:
                self.ever_seen = True
                self.last_fwd = float(est["sun_fwd"])
                self.last_left = float(est["sun_left"])
                self.phase = "approach"
                self.t_phase = self.t
            else:
                cmd[2] = 0.50 * self.spin
                if self.t - self.t_phase > 7.0:
                    self.spin = -self.spin
                    self.t_phase = self.t
                if self.t > 22.0 and not self.ever_seen:
                    self.phase = "fail"
                    self.reason = "no_marker"
        elif self.phase == "approach":
            if seen and est["sun_fwd"] > 0.05:
                self.ever_seen = True
                fwd = float(est["sun_fwd"])
                left = float(est["sun_left"])
                self.last_fwd = fwd
                self.last_left = left
                bearing = math.atan2(left, fwd)
                dist = math.hypot(fwd, left)
                if cliff and abs(bearing) < 0.50:
                    cmd[0] = 0.0
                    cmd[2] = 0.45 * self.spin
                elif obstacle and abs(obs_right) < 0.30:
                    cmd[2] = -0.50 if obs_right > 0.0 else 0.50
                elif dist <= SIT_FWD_M and abs(left) <= LAT_OK_M and abs(bearing) < 0.50:
                    self.phase = "turn"
                    self.turn0 = imu_yaw
                    self.t_phase = self.t
                    self.kicks = 0
                elif abs(bearing) > 0.42:
                    cmd[2] = _clip(1.4 * bearing, -WZ_MAX, WZ_MAX)
                else:
                    cmd[0] = _clip(0.90 * (dist - SIT_FWD_M), 0.14, VX_MAX)
                    cmd[1] = _clip(0.55 * left, -VY_MAX, VY_MAX)
                    cmd[2] = _clip(1.15 * bearing, -0.60, 0.60)
            elif self.last_fwd is not None and self.last_fwd <= 0.75:
                # The disc has dropped out of the bottom of the frame. Turning
                # here is safer than walking the last range estimate into the wall.
                self.phase = "turn"
                self.turn0 = imu_yaw
                self.t_phase = self.t
                self.kicks = 0
            elif self.last_fwd is not None and self.last_fwd < 1.40:
                self.phase = "creep"
                self.creep_left = min(0.20, max(0.0, self.last_fwd - SIT_FWD_M))
                self.t_phase = self.t
            else:
                cmd[2] = 0.45 * self.spin
                if self.t - self.t_phase > 8.0:
                    self.phase = "search"
                    self.t_phase = self.t
            if self.phase == "approach" and self.t - self.t_phase > 26.0:
                self.phase = "fail"
                self.reason = "missed_line"
        elif self.phase == "creep":
            if seen and est["sun_fwd"] > 0.05:
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
            if turned > TURN_RAD or self.t - self.t_phase > 9.0:
                self.phase = "settle"
                self.t_phase = self.t
                self.ok_n = 0
            else:
                # A pure yaw dies near a right angle on this policy. A small
                # side command keeps the gait turning, the same shape as the
                # marker dock's turn.
                cmd[1] = -0.08
                cmd[2] = 0.55
        elif self.phase == "settle":
            cmd = [0.0, 0.0, 0.0, 0.0]
            self.ok_n += 1
            if self.ok_n >= 6:
                self.phase = "sit"
                self.reason = "sat"
        elif self.phase in ("sit", "fail"):
            cmd = [0.0, 0.0, 0.0, 0.0]

        if self.phase in ("search", "turn") and abs(cmd[2]) >= 0.40 and cmd[0] < 0.05:
            if self.t - self.spin_t > 1.2:
                moved = abs(wrap(imu_yaw - self.spin_yaw))
                if moved < 0.10 and self.kicks < 4:
                    self.kick_until = self.t + 0.40
                    self.kicks += 1
                self.spin_t = self.t
                self.spin_yaw = imu_yaw
            if self.t < self.kick_until:
                # A short step restarts a stalled yaw. During the turn the yaw
                # stays on, or the duck walks off the line it just closed.
                if self.phase == "turn":
                    cmd[0] = 0.10
                    cmd[2] = 0.55
                else:
                    cmd[0] = 0.12
                    cmd[2] = 0.0
        return (float(cmd[0]), float(cmd[1]), float(cmd[2]), float(cmd[3]))
