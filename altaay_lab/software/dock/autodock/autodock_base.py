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
# Modified 2026 for the Open Duck Mini v2 (Altaay lab fork): ROS removed (no rospy, tf2, actionlib, publishers or
# services). Every robot interface goes through a DockIO object (below), so the same code runs on the duck, in the
# shared lab gym and in the unit tests. Bug fixes: publish_cmd clamped linear.x against the angular range and never
# clamped angular.z (now each axis against its own range); a lateral command (linear_y) is added for the duck's
# sidestep; every loop that used exit(0) now sends a zero command and returns False.
# Upstream: https://github.com/osrf/autodock at fd9c2a9aa6d05e4df84883008562e49506f690c0,
# autodock_core/scripts/autodock_core/autodock_server.py (class AutoDockServer).

import logging
from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np

from .autodock_utils import DockState, Pose2D
from . import autodock_utils as utils

log = logging.getLogger("autodock")

##############################################################################


class DockIO:
    """What the state machine needs from the robot. The duck runtime, the gym sim and the tests implement it.
    Frames: 'base' is the duck's trunk origin with roll and pitch removed (x forward, y left, z up); marker
    poses use the aruco convention (x right on the tag, y up, z out of the tag toward the camera)."""

    def now(self) -> float:                                  # seconds, monotonic
        raise NotImplementedError

    def sleep(self, dt: float) -> None:                      # the sim advances its physics here
        raise NotImplementedError

    def send_cmd(self, vx: float, vy: float, wz: float) -> None:   # the gamepad command interface
        raise NotImplementedError

    def get_marker(self, marker: str) -> Optional[Tuple[np.ndarray, float]]:
        """(4x4 pose of the marker in base, timestamp) of the last guarded detection, or None."""
        raise NotImplementedError

    def get_odom(self) -> Optional[np.ndarray]:
        """4x4 pose of base in a fixed odom frame: IMU yaw plus dead-reckoned x, y (the duck has no wheels)."""
        raise NotImplementedError

    def set_detections(self, on: bool) -> bool:
        return True

    def bumper_contact(self) -> bool:                        # chest on the dock bumper
        return False

    def sit(self) -> bool:                                   # scripted crouch onto the seat, torque low
        return True

    def stand(self) -> bool:                                 # scripted rise to the home pose, policy back on
        return True

    def charge_state(self) -> str:
        """'CHARGING', 'CONTACT' (pins closed, charge not started: cells too warm), or 'NONE'."""
        return "NONE"

    def cancelled(self) -> bool:
        return False

    def paused(self) -> bool:
        return False


@dataclass
class AutoDockConfig:
    """Default AutoDockConfig (upstream field names kept; duck values live in duck_autodock.yaml)."""
    # General configs
    tf_expiry: float = 0.5
    dock_timeout: float = 180.0
    controller_rate: float = 10.0
    # frames and topics
    base_link: str = "base"
    left_marker: str = "tag_1"
    right_marker: str = "tag_2"
    centre_marker: str = "tag_0"
    # vel profile
    linear_vel_range: Tuple[float, float] = (-0.15, 0.15)
    linear_y_range: Tuple[float, float] = (-0.20, 0.20)        # new: the duck's sidestep
    angular_vel_range: Tuple[float, float] = (-0.5, 0.5)
    max_linear_vel: float = 0.15
    min_linear_vel: float = 0.15
    max_angular_vel: float = 0.5
    min_angular_vel: float = 0.25
    # stop thresh
    stop_yaw_diff: float = 0.087
    stop_trans_diff: float = 0.02
    # debug state
    debug_mode: bool = False
    extra: dict = field(default_factory=dict)


##############################################################################


class AutoDockBase:
    """Port of AutoDockServer: the ROS-free base class of the dock state machine."""

    def __init__(self, config: AutoDockConfig, io: DockIO):
        self.cfg = config
        self.io = io
        assert len(self.cfg.linear_vel_range) == 2 and len(self.cfg.angular_vel_range) == 2 \
            and len(self.cfg.linear_y_range) == 2, "velocity ranges should have size of 2"
        assert self.cfg.linear_vel_range[0] < self.cfg.linear_vel_range[1], "linear vel min should be less than max"
        assert self.cfg.linear_y_range[0] < self.cfg.linear_y_range[1], "lateral vel min should be less than max"
        assert self.cfg.angular_vel_range[0] < self.cfg.angular_vel_range[1], "angular vel min should be less than max"
        self.dock_state = DockState.INVALID
        self.start_time = self.io.now()
        self.sleep_period = 1.0 / self.cfg.controller_rate
        self.history = []                       # (time, state, note) for logs and the sim score
        self.set_aruco_detections(detection_state=False)

    def start(self) -> bool:
        log.warning("Server implementation has not been specified. Do overload the start() function")
        return False

    def set_state(self, state: DockState, printout=""):
        self.dock_state = state
        self.history.append((round(self.io.now(), 3), DockState.to_string(state), printout))
        log.info(f" State: [{DockState.to_string(state)}] | {printout}")

    def check_cancel(self) -> bool:
        if self.io.cancelled():
            log.warning("Cancel requested")
            return True
        if (self.io.now() - self.start_time) > self.cfg.dock_timeout:
            self.set_state(self.dock_state, "Reach Timeout")
            return True
        return False

    @staticmethod
    def _clamp(v: float, rng) -> float:
        return min(max(v, rng[0]), rng[1])

    def publish_cmd(self, linear_vel=0.0, angular_vel=0.0, linear_y=0.0):
        """Command the robot to move, default param is STOP! (fixed: each axis against its own range)"""
        vx = self._clamp(linear_vel, self.cfg.linear_vel_range)
        vy = self._clamp(linear_y, self.cfg.linear_y_range)
        wz = self._clamp(angular_vel, self.cfg.angular_vel_range)
        self.io.send_cmd(vx, vy, wz)
        return vx, vy, wz

    def stop(self) -> bool:
        """zero command; used on every failure exit instead of upstream's exit(0)"""
        self.publish_cmd()
        return False

    def get_odom(self) -> Optional[np.ndarray]:
        return self.io.get_odom()

    def get_tf(self, target_link: str) -> Optional[np.ndarray]:
        """pose of the marker in base, None if missing or older than tf_expiry"""
        got = self.io.get_marker(target_link)
        if got is None:
            return None
        mat, stamp = got
        if self.io.now() - stamp > self.cfg.tf_expiry:
            return None
        return mat

    def get_centre_of_side_markers(self, offset=0.0) -> Optional[Pose2D]:
        left_tf = self.get_tf(self.cfg.left_marker)
        right_tf = self.get_tf(self.cfg.right_marker)
        if left_tf is None or right_tf is None:
            return None
        return utils.get_centre_tf(left_tf, right_tf, offset)

    def do_pause(self) -> bool:
        prev_state = self.dock_state
        self.set_state(DockState.PAUSE, f"pause action from {prev_state}")
        self.publish_cmd()
        while True:
            if self.check_cancel():
                return False
            if not self.io.paused():
                self.set_state(prev_state, "resume action from pause")
                return True
            self.io.sleep(self.sleep_period)

    def _guard(self) -> bool:
        """common loop guard: cancel, timeout, pause"""
        if self.check_cancel():
            return False
        if self.io.paused() and not self.do_pause():
            return False
        return True

    def move_with_odom(self, forward: float, stop_on_bumper=False) -> bool:
        """Move robot in linear motion with odom (duck: IMU yaw plus dead reckoning). Blocking."""
        self.set_state(self.dock_state, f"move robot: {forward:.3f} m")
        _initial_tf = self.get_odom()
        if _initial_tf is None:
            return self.stop()
        _goal_tf = utils.apply_2d_transform(_initial_tf, (forward, 0, 0))
        while True:
            if not self._guard():
                return self.stop()
            if stop_on_bumper and forward > 0 and self.io.bumper_contact():
                self.publish_cmd()
                return True
            _curr_tf = self.get_odom()
            if _curr_tf is None:
                return self.stop()
            dx, dy, dyaw = utils.compute_tf_diff(_curr_tf, _goal_tf)
            if abs(dx) < self.cfg.stop_trans_diff or (dx < 0 < forward) or (dx > 0 > forward):
                self.publish_cmd()
                return True
            ang_vel = utils.sat_proportional_filter(dyaw, abs_max=self.cfg.min_angular_vel, factor=0.2)
            if abs(ang_vel) < self.cfg.min_angular_vel:      # duck: no turn command under its turn dead band
                ang_vel = 0.0
            l_vel = utils.bin_filter(dx, self.cfg.min_linear_vel)
            if forward < 0:
                l_vel = self.cfg.linear_vel_range[0]          # the policy only backs up at its -0.15 limit
            self.publish_cmd(linear_vel=l_vel, angular_vel=ang_vel)
            self.io.sleep(self.sleep_period)

    def rotate_with_odom(self, rotate: float) -> bool:
        """Spot rotate with odom (duck: IMU yaw). Blocking."""
        self.set_state(self.dock_state, f"Turn robot: {rotate:.3f} rad")
        _initial_tf = self.get_odom()
        if _initial_tf is None:
            return self.stop()
        _goal_tf = utils.apply_2d_transform(_initial_tf, (0, 0, rotate))
        while True:
            if not self._guard():
                return self.stop()
            _curr_tf = self.get_odom()
            if _curr_tf is None:
                return self.stop()
            dx, dy, dyaw = utils.compute_tf_diff(_curr_tf, _goal_tf)
            if abs(dyaw) < self.cfg.stop_yaw_diff:
                self.publish_cmd()
                return True
            ang_vel = utils.sat_proportional_filter(dyaw, abs_min=self.cfg.min_angular_vel, abs_max=self.cfg.max_angular_vel)
            self.publish_cmd(angular_vel=ang_vel)
            self.io.sleep(self.sleep_period)

    def set_aruco_detections(self, detection_state) -> bool:
        return self.io.set_detections(bool(detection_state))
