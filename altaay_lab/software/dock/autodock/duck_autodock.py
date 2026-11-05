#!/usr/bin/env python3

# Copyright 2021 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Modified 2026 for the Open Duck Mini v2 (Altaay lab fork), from simple_autodock.py (class AutoDockStateMachine):
# ROS removed (argparse main, rospy sleeps, services and BatteryState replaced by the DockIO calls); exit(0) replaced
# by a zero command and return False; the states adapted to a walking robot that cannot creep (no stepping under a
# 0.10 forward command, turning only from 0.25 rad/s, sidestep only at 0.20 m/s; the shared lab gym probes): every
# motion is a timed pulse followed by stop-and-look, PARALLEL_CORRECTION is a sidestep instead of turn-drive-turn,
# STEER_DOCK walks short straight segments with a look between them, LAST_MILE ends on the chest bumper, and
# ACTIVATE_CHARGER sits the duck on the seat and waits for the pins. Added: APPROACH to a staging point (rule after
# Nav2 nav2_docking, Apache-2.0), a three-frame tag confirmation with a jump check (rule after
# Quchaosheng/ros2-apriltag-docking-demo, Apache-2.0), an ENTER gate (lateral and yaw limits of the contact pads),
# and the retry that stands up before it backs out.
# Upstream: https://github.com/osrf/autodock at fd9c2a9aa6d05e4df84883008562e49506f690c0,
# autodock_core/scripts/simple_autodock.py.

import logging
import math
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from .autodock_utils import DockState
from . import autodock_utils as utils
from .autodock_base import AutoDockBase, AutoDockConfig, DockIO

log = logging.getLogger("autodock")


@dataclass
class DuckAutoDockConfig(AutoDockConfig):
    """Starting values from the phase 1 probes (sim pass only); duck_autodock.yaml overrides them."""
    cam_offset: float = 0.121          # m, base origin to the marker plane when the chest is on the bumper
    front_dock: bool = True
    max_parallel_offset: float = 0.012  # m, sidestep if the lateral error is larger
    predock_tf_samples: int = 3        # looks averaged before the lateral decision
    offset_to_angular_vel: float = 1.1  # kept for the record; the duck steers with pulses
    to_last_mile_dis: float = 0.25     # m, blind ENTER length (marker distance minus cam_offset)
    to_last_mile_tol: float = 0.05
    stop_distance: float = 0.0
    max_last_mile_odom: float = 0.32   # m, longest blind walk before giving up
    enable_charger: bool = True
    check_battery_status: bool = True
    check_battery_timeout: float = 10.0  # s, the pins must report within this after the sit
    retry_count: int = 3
    retry_retreat_dis: float = 0.35    # m, walk out after turning about, so the side tags are in view again
    # duck additions
    staging_dis: float = 0.60          # m, marker distance of the staging point (Nav2 staging pose)
    approach_timeout: float = 120.0
    settle_s: float = 0.4              # stop-and-look: wait after a stop before a look
    look_frames: int = 3               # three-frame confirmation
    look_dt: float = 0.1
    look_jump_m: float = 0.03          # reject a look whose frames disagree by more
    look_jump_rad: float = 0.12
    fwd_speed_real: float = 0.096      # m/s the policy walks at the 0.15 command (gym probe)
    back_speed_real: float = 0.044     # m/s at -0.15
    side_speed_real: float = 0.092     # m/s at vy 0.20
    side_cmd: float = 0.20
    turn_slow_cmd: float = 0.25
    turn_slow_real: float = 0.12       # rad/s
    turn_fast_cmd: float = 0.5
    turn_fast_real: float = 0.38
    fast_turn_above: float = 0.0       # rad: always the 0.5 turn (wz 0.25 is one-sided: +6.7 deg against -0.4 deg in 1.5 s)
    max_pulse_s: float = 2.0
    # measured pulse response from standing (gym probe, our build, sim pass only): [pulse s, result] incl. coasting
    turn_slow_table: tuple = ((0.0, 0.0), (1.0, 0.0286), (2.0, 0.169), (3.0, 0.279))      # wz 0.25: rad
    turn_fast_table: tuple = ((0.0, 0.0), (0.2, 0.013), (0.3, 0.068), (0.4, 0.112), (0.5, 0.174), (1.0, 0.294), (2.0, 0.715))  # wz +0.5 (left): rad
    turn_right_table: tuple = ((0.0, 0.0), (0.3, 0.063), (0.5, 0.090), (1.0, 0.218), (2.0, 0.50))   # wz -0.5 (right): rad, weaker (probe)
    side_table: tuple = ((0.0, 0.0), (0.3, 0.0004), (0.5, 0.0096), (0.7, 0.017), (1.0, 0.0398), (2.0, 0.112))  # vy +0.2 (left) only: m
    right_shift_turn: float = 0.35     # rad: a step to the right is turn right, walk, turn left (vy -0.2 gives no motion)
    right_ok: float = 0.014            # m: a left-of-axis error up to this is accepted (no right move)
    staging_lateral: float = -0.025    # m: approach to the right of the axis, so corrections are left sidesteps
    axis_save_within: float = 0.75     # m: save the axis heading from side-tag looks closer than this
    fwd_table: tuple = ((0.0, 0.0), (0.3, 0.0013), (0.6, 0.0243), (1.0, 0.0735), (2.0, 0.157), (4.0, 0.360))  # vx 0.15: m
    steer_segment: float = 0.12        # m per straight segment in STEER_DOCK
    heading_hold_rad: float = 0.06     # yaw drift that triggers a turn command while walking (a turn slows the walk)
    hold_turn_cmd: float = 0.5
    hold_min_dist: float = 0.15        # m: no heading hold on shorter walks (wz 0.5 while walking overshoots)
    enter_max_lateral: float = 0.015   # m, ENTER gate (the pads take +/- 25 mm, keep margin for the blind walk)
    enter_max_yaw: float = 0.052       # rad (3 deg; the pads take 10 deg, a 3 deg walk drifts 15 mm in 0.29 m)
    max_predock_loops: int = 8
    back_pulse_s: float = 1.5          # s per backward pulse in back_off
    max_sidesteps: int = 6             # sidestep corrections per state before it moves on or fails
    sit_gap: float = 0.0425            # m, chest to bumper at the stop; the sit travels about 45 to 50 mm forward
    sit_gap_tol: float = 0.004         # m, stop accepted up to this far beyond the target
    stop_lead: float = 0.004           # m, stop this early for the step that finishes after the zero command
    last_mile_timeout: float = 12.0
    check_ahead: float = 0.10          # m before the stop point: the last look, about 0.16 m from the camera
    last_lateral_tol: float = 0.008    # m, sidestep at the check point if the lateral error is larger
    last_yaw_tol: float = 0.035        # rad (2 deg): a yawed chest meets the bumper on one corner and falls short
    last_right_ok: float = 0.012       # m: at the last-mile check a left error over this is moved too (the soles clear
                                       # the 40 mm seat by about 22 mm a side, dock sim foot_axis_min)
    last_checks: int = 5               # looks and corrections at the last-mile check point
    recover_face_tol: float = 0.20     # rad: when the tags are lost, turn to face the remembered mast first
    recover_min_range: float = 0.55    # m: then step back until the mast is this far (the tags above the view closer in)
    recover_tries: int = 6
    last_jump_m: float = 0.03          # m: last-mile jump guard on single centre-tag frames
    max_diag_walk: float = 0.12        # m: longest diagonal walk of a right move
    last_diag_walk: float = 0.07       # m: the same at the last-mile check point (0.16 m before the stop)
    walk_in_max_lateral: float = 0.020  # m: hard limit at the check point, the soles clear the 40 mm seat by about 22 mm
    walk_in_max_yaw: float = 0.07      # rad (4 deg): hard limit at the check point
    undock_timeout: float = 90.0       # s: the undock's own budget (16 back pulses with their looks take about 60 s)
    top_ups: int = 3                   # still looks and top-up steps after the last-mile stop


class DuckAutoDock(AutoDockBase):
    """The dock state machine for the walking duck (port of AutoDockStateMachine)."""

    def __init__(self, config: DuckAutoDockConfig, io: DockIO):
        super().__init__(config, io)
        self.dock_state = DockState.IDLE
        self.sat = False
        self.attempts = 0
        self.axis_yaw_odom = None          # dock axis heading in the odom (IMU) frame, saved from the side tags
        self.mast_odom = None              # (x, y) of the mast face centre in the odom frame, from the last good look

    # ------------------------------------------------------------------ geometry
    @staticmethod
    def _xy(m: np.ndarray) -> np.ndarray:
        return np.array([m[0, 3], m[1, 3]])

    def dock_relative(self, use_centre=True) -> Optional[Tuple[float, float, float, str]]:
        """(along, lateral, yaw_err, source) of the duck relative to the dock axis, from the latest markers.
        along: distance of base from the marker plane; lateral: + = duck left of the axis; yaw_err: the turn
        (rad, + = left) that faces the duck square to the mast."""
        L, R = self.get_tf(self.cfg.left_marker), self.get_tf(self.cfg.right_marker)
        if L is not None and R is not None:
            pL, pR = self._xy(L), self._xy(R)
            u = pR - pL
            n = np.array([u[1], -u[0]]) / max(np.linalg.norm(u), 1e-9)      # normal toward the duck
            M = 0.5 * (pL + pR)
            src = "sides"
            o = self.get_odom()
            if o is not None and float(-M @ n) < self.cfg.axis_save_within:
                d0 = -n
                self.axis_yaw_odom = utils.set_angle(utils.get_2d_pose(o)[2] + math.atan2(d0[1], d0[0]))
        elif use_centre:
            C = self.get_tf(self.cfg.centre_marker)
            if C is None:
                return None
            M = self._xy(C)
            o = self.get_odom() if self.axis_yaw_odom is not None else None
            if o is not None:
                # the dock axis heading saved from the side tags, carried on the IMU yaw
                th = utils.set_angle(self.axis_yaw_odom - utils.get_2d_pose(o)[2])
                n = -np.array([math.cos(th), math.sin(th)])
                src = "centre+imu"
            else:
                z = C[:3, 2]                                                # tag z points out of the tag
                n = np.array([z[0], z[1]]) / max(np.linalg.norm(z[:2]), 1e-9)
                src = "centre"
        else:
            return None
        self._remember_mast(M)
        d = -n
        p = -M
        lft = np.array([-d[1], d[0]])
        return float(p @ n), float(p @ lft), math.atan2(d[1], d[0]), src

    def _remember_mast(self, M: np.ndarray) -> None:
        """keep the mast face centre (base frame M) in the odom frame, for the lost-tag recovery"""
        o = self.get_odom()
        if o is None:
            return
        x, y, th = utils.get_2d_pose(o)
        c, s = math.cos(th), math.sin(th)
        self.mast_odom = (x + c * M[0] - s * M[1], y + s * M[0] + c * M[1])

    def mast_bearing(self) -> Optional[Tuple[float, float]]:
        """(bearing rad, + = left; range m) from the base to the remembered mast, on odometry"""
        o = self.get_odom()
        if o is None or self.mast_odom is None:
            return None
        x, y, th = utils.get_2d_pose(o)
        dx, dy = self.mast_odom[0] - x, self.mast_odom[1] - y
        return utils.set_angle(math.atan2(dy, dx) - th), math.hypot(dx, dy)

    def look(self, use_centre=True):
        """stop-and-look: stop, settle, then confirm over look_frames frames: all present and no jump (the
        jump limit grows with range, since the side-tag baseline gives a noisier normal far away); a set with a
        jump is retaken up to 3 times. One frame of the set may miss the markers (a sway on the low-friction floor
        dropped single frames at the last-mile check point in the dock sim); a set missing more is retaken once, then
        the look returns None."""
        self.publish_cmd()
        self.io.sleep(self.cfg.settle_s)
        misses, best = 0, None
        for _ in range(3):
            got = []
            for _ in range(self.cfg.look_frames):
                r = self.dock_relative(use_centre)
                if r is not None:
                    got.append(r)
                self.io.sleep(self.cfg.look_dt)
            if len(got) < max(1, self.cfg.look_frames - 1):
                misses += 1
                if misses >= 2:
                    return None
                continue
            a = np.array([g[:3] for g in got])
            lim = self.cfg.look_jump_m * max(1.0, float(np.median(a[:, 0])) / 0.4)
            yaw = utils.avg_2d_poses([(0, 0, g[2]) for g in got])[2]
            best = (float(np.median(a[:, 0])), float(np.median(a[:, 1])), yaw, got[-1][3])
            if np.ptp(a[:, 0]) <= lim and np.ptp(a[:, 1]) <= lim and \
                    max(abs(utils.set_angle(g[2] - yaw)) for g in got) <= self.cfg.look_jump_rad * max(1.0, lim / self.cfg.look_jump_m):
                return best
        if best is None:
            return None
        return best[:3] + (best[3] + "-noisy",)

    # ------------------------------------------------------------------ motion pulses
    @staticmethod
    def _pulse_time(table, want: float) -> float:
        """inverse of a measured (pulse s, result) table: the pulse length for a wanted result"""
        ts = [t for t, _ in table]
        vs = [v for _, v in table]
        return float(np.interp(abs(want), vs, ts))

    def turn_pulse(self, angle: float) -> bool:
        """wz 0.5 pulse; left and right have their own measured tables (the policy turns right about half as well)"""
        table = self.cfg.turn_fast_table if angle > 0 else self.cfg.turn_right_table
        t = min(self._pulse_time(table, angle), self.cfg.max_pulse_s)
        self.publish_cmd(angular_vel=math.copysign(self.cfg.turn_fast_cmd, angle))
        self.io.sleep(t)
        self.publish_cmd()
        return self._guard()

    def side_pulse(self, lateral: float, right_ok: Optional[float] = None, max_walk: Optional[float] = None) -> bool:
        """move toward the axis: lateral > 0 means the duck is left of it. The stock policy steps left (vy +0.2)
        but does not step right at all (vy -0.2 gives 0 mm in 2 s, gym probe): a right move is turn right, a short
        diagonal walk, and a turn back left (the upstream PARALLEL_CORRECTION idea, shortened)"""
        if lateral > 0 and lateral <= (self.cfg.right_ok if right_ok is None else right_ok):
            return self._guard()                        # small left-of-axis errors are left alone (pads take +/- 21 mm)
        if lateral < 0:
            t = min(self._pulse_time(self.cfg.side_table, lateral), self.cfg.max_pulse_s)
            self.publish_cmd(linear_y=self.cfg.side_cmd)
            self.io.sleep(t)
            self.publish_cmd()
            return self._guard()
        a = self.cfg.right_shift_turn
        o0 = self.get_odom()
        yaw0 = utils.get_2d_pose(o0)[2] if o0 is not None else None
        if not self.turn_pulse(-a):
            return False
        o1 = self.get_odom()
        turned = abs(utils.set_angle(utils.get_2d_pose(o1)[2] - yaw0)) if (o1 is not None and yaw0 is not None) else a
        if turned < 0.6 * a:
            # a weak right turn (the soft floor turned 0.11 of 0.35 rad): turn the rest first, or the diagonal walk
            # becomes a long forward walk (it walked 0.22 m into the dock from the last-mile check point)
            if not self.turn_pulse(-(a - turned)):
                return False
            o1 = self.get_odom()
            turned = abs(utils.set_angle(utils.get_2d_pose(o1)[2] - yaw0)) if (o1 is not None and yaw0 is not None) else a
        cap = self.cfg.max_diag_walk if max_walk is None else max_walk
        self.walk_segment(min(cap, max(0.025, lateral / max(math.sin(turned), 0.15))))
        o2 = self.get_odom()
        back = utils.set_angle(yaw0 - utils.get_2d_pose(o2)[2]) if (o2 is not None and yaw0 is not None) else a
        return self.turn_pulse(back)

    def walk_segment(self, dist: float, stop_on_bumper=False, yaw_offset=0.0) -> bool:
        """walk straight dist metres at the 0.15 command, holding the start heading plus yaw_offset (the dock
        axis heading from the last look) on the IMU yaw"""
        o0 = self.get_odom()
        if o0 is None:
            return self.stop()
        yaw0 = utils.get_2d_pose(o0)[2] + yaw_offset
        t_end = self.io.now() + self._pulse_time(self.cfg.fwd_table, dist)
        while self.io.now() < t_end:
            if not self._guard():
                return self.stop()
            if stop_on_bumper and self.io.bumper_contact():
                break
            o = self.get_odom()
            dyaw = utils.set_angle(yaw0 - utils.get_2d_pose(o)[2]) if o is not None else 0.0
            hold = dist >= self.cfg.hold_min_dist and abs(dyaw) > self.cfg.heading_hold_rad
            wz = math.copysign(self.cfg.hold_turn_cmd, dyaw) if hold else 0.0      # short walks: straight, the look fixes yaw
            self.publish_cmd(linear_vel=self.cfg.max_linear_vel, angular_vel=wz)
            self.io.sleep(self.sleep_period)
        self.publish_cmd()
        return True

    # ------------------------------------------------------------------ states
    def start(self) -> bool:
        """Start Docking Sequence (upstream loop with the duck's APPROACH first)"""
        self.start_time, self.timeout_s = self.io.now(), self.cfg.dock_timeout
        self.set_aruco_detections(detection_state=True)
        ok = self.do_approach()
        current_retry_count = 0
        while ok:
            self.attempts += 1
            if (self.do_predock() and self.do_steer_dock() and self.do_last_mile() and self.do_activate_charger()):
                self.publish_cmd()
                self.set_state(DockState.IDLE, "All Success!")
                self.set_aruco_detections(detection_state=False)
                return True
            self.publish_cmd()
            if current_retry_count >= self.cfg.retry_count or self.check_cancel():
                break
            current_retry_count += 1
            log.warning(f"Attempting retry: {current_retry_count}/{self.cfg.retry_count}")
            if not self.do_retry():
                break
        self.set_aruco_detections(detection_state=False)
        self.publish_cmd()
        self.set_state(DockState.IDLE, "Failed")
        return False

    def do_approach(self) -> bool:
        """duck addition: find the mast and walk to the staging point on the dock axis"""
        self.set_state(DockState.APPROACH, "walk to the staging point")
        t0 = self.io.now()
        searched, recover = 0.0, 0
        while self.io.now() - t0 < self.cfg.approach_timeout:
            if not self._guard():
                return self.stop()
            r = self.look()
            if r is None:
                # lost the tags: turn to face the mast remembered on odometry, then step back until it is far enough
                # for the tags to be in the view (fix for the turn-aways of the dock sim: facing the axis heading
                # left the mast out of the view from 0.2 m off the axis, and a blind search then turned away)
                mb = self.mast_bearing()
                if mb is not None and recover < self.cfg.recover_tries:
                    recover += 1
                    brg, rng = mb
                    if abs(brg) > self.cfg.recover_face_tol:
                        self.turn_by(brg, tol=self.cfg.recover_face_tol)
                        continue
                    if rng < self.cfg.recover_min_range:
                        self.publish_cmd(linear_vel=self.cfg.linear_vel_range[0])
                        self.io.sleep(self.cfg.back_pulse_s)
                        self.publish_cmd()
                        continue
                if searched > 2 * math.pi:
                    return self.stop()
                self.turn_pulse(0.5)                      # SEARCH: turn in place
                searched += 0.5
                continue
            along, lat, yaw, src = r
            if not src.startswith("sides"):
                C = self.get_tf(self.cfg.centre_marker)
                if C is not None:
                    brg = math.atan2(C[1, 3], C[0, 3])
                    if abs(brg) > 0.10:
                        self.turn_pulse(brg)
                        continue
            # close enough along the axis: square up and hand over to PREDOCK (it nulls the lateral offset)
            if along - self.cfg.staging_dis <= 0.08:
                if abs(yaw) > self.cfg.stop_yaw_diff:
                    self.turn_pulse(yaw)
                    continue
                return True
            # head for the staging point S on the axis, but never more than 0.30 rad off the axis heading, so the
            # three tags stay in view (the duck's heading in axis coordinates is -yaw)
            want = max(-0.30, min(0.30, math.atan2(-(lat - self.cfg.staging_lateral), along - self.cfg.staging_dis)))
            turn = utils.set_angle(want + yaw)
            if abs(turn) > 0.12:
                self.turn_pulse(turn)
                continue
            self.walk_segment(min(0.25, along - self.cfg.staging_dis), yaw_offset=turn)
        return self.stop()

    def do_predock(self) -> bool:
        """square up to the side markers, then null the lateral offset (sidestep in place of the upstream
        PARALLEL_CORRECTION turn-drive-turn)"""
        self.set_state(DockState.PREDOCK, "start docking")
        samples, n_side = [], 0
        for _ in range(self.cfg.max_predock_loops * 3):
            if not self._guard():
                return self.stop()
            r = self.look(use_centre=False)
            if r is None:
                r = self.look(use_centre=True)
                if r is None:
                    log.error("Not detecting the markers, exit state")
                    return self.stop()
            along, lat, yaw, src = r
            if abs(yaw) > self.cfg.stop_yaw_diff:
                samples = []
                self.turn_pulse(yaw)
                continue
            samples.append(lat)
            if len(samples) < self.cfg.predock_tf_samples:
                continue
            y_offset = float(np.mean(samples))
            samples = []
            if abs(y_offset) > self.cfg.max_parallel_offset and n_side < self.cfg.max_sidesteps:
                n_side += 1
                self.set_state(DockState.PARALLEL_CORRECTION, f"sidestep {y_offset:.3f} m")
                if not self.side_pulse(y_offset):
                    return self.stop()
                self.set_state(DockState.PREDOCK, "try predock again")
                continue
            if abs(y_offset) > 3 * self.cfg.max_parallel_offset:
                log.error(f"lateral offset {y_offset:.3f} m left after {n_side} sidesteps")
                return self.stop()
            return True
        return self.stop()

    def do_steer_dock(self) -> bool:
        """walk in short straight segments to the last-mile start, correcting between them"""
        self.set_state(DockState.STEER_DOCK)
        target = self.cfg.cam_offset + self.cfg.to_last_mile_dis
        n_gate = 0
        for _ in range(12):
            if not self._guard():
                return self.stop()
            r = self.look()
            if r is None:
                log.error("Not able to locate the markers, exit")
                return self.stop()
            along, lat, yaw, src = r
            if along - target <= self.cfg.to_last_mile_tol:
                # ENTER gate: square and centred enough for the pads
                if abs(lat) > self.cfg.enter_max_lateral:
                    if n_gate >= self.cfg.max_sidesteps:
                        # out of corrections: fail the state (retry), never waive the gate (PR 20 review)
                        log.error(f"ENTER gate: lateral {lat:.3f} m left after {n_gate} sidesteps")
                        return self.stop()
                    n_gate += 1
                    self.set_state(DockState.PARALLEL_CORRECTION, f"gate sidestep {lat:.3f} m")
                    self.side_pulse(lat)
                    continue
                if abs(yaw) > self.cfg.enter_max_yaw:
                    self.turn_pulse(yaw)
                    continue
                return True
            if abs(yaw) > 2 * self.cfg.stop_yaw_diff:
                self.turn_pulse(yaw)
                continue
            if abs(lat) > 2 * self.cfg.max_parallel_offset:
                self.side_pulse(lat)
                continue
            self.walk_segment(min(self.cfg.steer_segment, along - target), yaw_offset=yaw)
        return self.stop()

    def do_last_mile(self) -> bool:
        """walk in on the centre tag (40 mm, readable down to about 6 cm from the camera) and stop the chest
        sit_gap short of the bumper; the sit's forward travel then puts the chest on the bumper (the shared lab gym
        sit probe, sim pass only). Blind only if the tag is lost, for at most max_last_mile_odom."""
        self.set_state(DockState.LAST_MILE)
        stop_along = self.cfg.cam_offset + self.cfg.sit_gap
        # stage 1: walk to a check point where the 40 mm tag still reads well, then null the lateral offset there
        settled, lat = False, None
        for _ in range(self.cfg.last_checks):
            r = self.look()
            if r is None:
                log.error("no markers at the last-mile check point")
                return self.stop()
            if r[0] > stop_along + self.cfg.check_ahead + 0.02:
                self.walk_segment(r[0] - stop_along - self.cfg.check_ahead, yaw_offset=r[2])
                continue
            C = self.get_tf(self.cfg.centre_marker)
            lat = -float(C[1, 3]) if C is not None else r[1]       # duck squared: the tag's y in base is -lateral
            if abs(lat) > self.cfg.last_lateral_tol:
                self.side_pulse(lat, right_ok=self.cfg.last_right_ok, max_walk=self.cfg.last_diag_walk)
                continue
            if abs(r[2]) > self.cfg.last_yaw_tol:
                self.turn_pulse(r[2])
                continue
            settled = True
            break
        if not settled and not (lat is not None and abs(lat) <= self.cfg.walk_in_max_lateral
                                and abs(r[2]) <= self.cfg.walk_in_max_yaw):
            # out of checks: walk in only inside the soles' clearance of the seat, else fail the state (retry)
            log.error(f"last-mile check point: not centred and square after {self.cfg.last_checks} checks")
            return self.stop()
        if self.get_odom() is None:
            log.error("no odometry in the last mile")
            return self.stop()
        t0, lost_since, walked_blind = self.io.now(), None, 0.0
        last_along = r[0] if r is not None else None   # the check-point look, in case the first moving read misses
        t_seen = t0
        while self.io.now() - t0 < self.cfg.last_mile_timeout:
            if not self._guard():
                return self.stop()
            C = self.get_tf(self.cfg.centre_marker)
            if C is not None and last_along is not None:
                # one-frame jump guard: a reading closer than the walk can have come since the last one is dropped
                # (the walk is never faster than fwd_speed_real, so a true reading is not below this bound)
                if float(C[0, 3]) < last_along - (self.io.now() - t_seen) * self.cfg.fwd_speed_real - self.cfg.last_jump_m:
                    C = None
            if C is not None:
                lost_since, last_along = None, float(C[0, 3])   # duck squared by PREDOCK: the tag x in base is the range
                t_seen = self.io.now()
                along = last_along
            else:
                # the 40 mm tag leaves the view about 7 cm from the camera: dead-reckon from the last reading
                if last_along is None:
                    log.error("no centre-tag range in the last mile")
                    return self.stop()
                lost_since = self.io.now() if lost_since is None else lost_since
                walked_blind = (self.io.now() - lost_since) * self.cfg.fwd_speed_real
                along = last_along - walked_blind
                if walked_blind > self.cfg.max_last_mile_odom:
                    log.error("centre tag lost too long in the last mile")
                    return self.stop()
            if along <= stop_along + self.cfg.stop_lead:
                break
            # straight, no heading hold: the walk in is under 0.15 m (hold_min_dist), and a wz 0.5 hold here
            # overshot to 8 to 17 deg and put a sole on the seat end in the dock sim (falls, acc5 and acc6)
            self.publish_cmd(linear_vel=self.cfg.max_linear_vel)
            self.io.sleep(self.sleep_period)
        self.publish_cmd()
        # check the stop on a still look (median of three centre-tag frames); a short top-up step if it stopped far
        for _ in range(self.cfg.top_ups):
            self.io.sleep(self.cfg.settle_s)
            got = []
            for _ in range(self.cfg.look_frames):
                C = self.get_tf(self.cfg.centre_marker)
                if C is not None:
                    got.append(float(C[0, 3]))
                self.io.sleep(self.cfg.look_dt)
            if not got:
                break
            err = float(np.median(got)) - stop_along
            if err <= self.cfg.sit_gap_tol:
                break
            self.walk_segment(err)
        if self.io.bumper_contact():
            log.warning("chest already on the bumper before the sit")
        return True

    def do_activate_charger(self) -> bool:
        self.set_state(DockState.ACTIVATE_CHARGER, "Docked, sit and wait for the pins")
        self.io.sleep(0.5)
        if not self.io.sit():
            return self.stop()
        self.sat = True
        if not self.cfg.check_battery_status:
            return True
        t0 = self.io.now()
        while self.io.now() - t0 < self.cfg.check_battery_timeout:
            st = self.io.charge_state()
            if st in ("CHARGING", "CONTACT"):
                self.set_state(DockState.ACTIVATE_CHARGER, f"pins report {st}")
                return True
            self.io.sleep(0.5)
        log.error("time out for the pins")
        return False

    def turn_by(self, angle: float, tol: float = 0.15) -> bool:
        """turn in place by angle (one direction, the turn unwrapped on the IMU yaw: no sign flip near +/- pi)"""
        o = self.get_odom()
        if o is None:
            return self.stop()
        last, done = utils.get_2d_pose(o)[2], 0.0
        for _ in range(16):
            rest = abs(angle) - abs(done)
            if rest < tol:
                return True
            if not self.turn_pulse(math.copysign(min(0.7, rest), angle)):
                return False
            self.io.sleep(0.3)
            o = self.get_odom()
            y = utils.get_2d_pose(o)[2]
            done += utils.set_angle(y - last)
            last = y
        return False

    def back_off(self) -> bool:
        """leave the dock along its axis: short backward pulses (vx -0.15; the only backward command that moves),
        each followed by a look and a left sidestep for the rightward drift of backing (39 mm in 3 s in the probe),
        so the feet stay clear of the 40 mm spine. Turning in place on the dock put a foot on the spine in the sim."""
        for _ in range(16):
            r = self.look()
            if r is not None and r[0] >= self.cfg.cam_offset + self.cfg.retry_retreat_dis:
                return True
            if r is not None and r[1] < -self.cfg.last_lateral_tol:
                self.side_pulse(r[1])
            self.publish_cmd(linear_vel=self.cfg.linear_vel_range[0])
            self.io.sleep(self.cfg.back_pulse_s)
            self.publish_cmd()
            if not self._guard():
                return self.stop()
        return self.stop()

    def do_retry(self) -> bool:
        """stand up if seated, leave the dock, find the staging point again, then try PREDOCK"""
        if self.check_cancel():
            return False
        if self.sat:
            self.io.stand()
            self.sat = False
        if self.dock_state in (DockState.ACTIVATE_CHARGER, DockState.LAST_MILE):
            self.set_state(DockState.RETRY, "back off along the axis")
            if not self.back_off():
                return False
            return self.do_approach()
        if self.dock_state in (DockState.STEER_DOCK, DockState.PREDOCK, DockState.PARALLEL_CORRECTION):
            self.set_state(DockState.RETRY, "skip retreat, find the staging point and try predock")
            return self.do_approach()
        log.info("State is not retry-able")
        return False

    def do_undock(self) -> bool:
        """after the wake: stand, then leave clear of the spine (the dock opens the pins first, Nav2 rule). Undocking has
        its own timeout budget from now (a charge lasts longer than dock_timeout, so the docking start time would fail
        the first guard), and it turns the tag detections on for the retreat (start() turned them off after docking;
        back_off() reads its distance and lateral drift from looks) and off again at the end."""
        self.start_time, self.timeout_s = self.io.now(), self.cfg.undock_timeout
        self.set_aruco_detections(detection_state=True)
        try:
            self.set_state(DockState.UNDOCK, "stand and leave")
            if self.sat:
                self.io.stand()
                self.sat = False
            ok = self.back_off()
        finally:
            self.publish_cmd()
            self.set_aruco_detections(detection_state=False)
        self.set_state(DockState.IDLE, "undocked" if ok else "undock failed")
        return ok


def load_config(path: Optional[str] = None) -> DuckAutoDockConfig:
    """DuckAutoDockConfig with the values of duck_autodock.yaml (if given)."""
    cfg = DuckAutoDockConfig()
    if path:
        import yaml
        with open(path) as f:
            vals = yaml.safe_load(f) or {}
        for k, v in vals.items():
            if not hasattr(cfg, k):
                raise KeyError(f"unknown autodock key {k}")
            if isinstance(getattr(cfg, k), tuple):
                v = tuple(v)
            setattr(cfg, k, v)
    return cfg
