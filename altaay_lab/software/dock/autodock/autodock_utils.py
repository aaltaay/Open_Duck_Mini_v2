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
# Modified 2026 for the Open Duck Mini v2 (Altaay lab fork): ROS removed (tf.transformations replaced by numpy,
# the ROS message helpers dropped), DockState made a plain IntEnum with the duck's extra states, and avg_2d_poses
# fixed to average yaw on the circle (upstream averaged it arithmetically, which breaks near +/- pi).
# Upstream: https://github.com/osrf/autodock at fd9c2a9aa6d05e4df84883008562e49506f690c0,
# autodock_core/scripts/autodock_core/autodock_utils.py.

import enum
import math
from typing import List, Optional, Tuple

import numpy as np

##############################################################################

Pose2D = Tuple[float, float, float]


class DockState(enum.IntEnum):
    INVALID = 0
    IDLE = 1
    PREDOCK = 2
    PARALLEL_CORRECTION = 3
    STEER_DOCK = 4
    LAST_MILE = 5
    ACTIVATE_CHARGER = 6
    RETRY = 7
    PAUSE = 8
    # duck additions (no upstream equivalent)
    APPROACH = 9
    UNDOCK = 10

    @staticmethod
    def to_string(state) -> str:
        return DockState(state).name

    @staticmethod
    def to_percent(state) -> float:
        _map = {
            DockState.IDLE: 0.0,
            DockState.APPROACH: 0.05,
            DockState.PREDOCK: 0.15,
            DockState.PARALLEL_CORRECTION: 0.35,
            DockState.STEER_DOCK: 0.50,
            DockState.LAST_MILE: 0.8,
            DockState.ACTIVATE_CHARGER: 0.9,
            DockState.RETRY: 0.1,
            DockState.PAUSE: 0.1,
            DockState.UNDOCK: 1.0,
        }
        return _map.get(DockState(state), 0.0)

##############################################################################
# numpy replacements for the tf.transformations calls upstream used


def mat_from_2d(pose_2d: Pose2D) -> np.ndarray:
    """4x4 homogeneous matrix of a planar pose (x, y, yaw)."""
    c, s = math.cos(pose_2d[2]), math.sin(pose_2d[2])
    m = np.eye(4)
    m[0, 0], m[0, 1], m[1, 0], m[1, 1] = c, -s, s, c
    m[0, 3], m[1, 3] = pose_2d[0], pose_2d[1]
    return m


def mat_from_rt(R: np.ndarray, t) -> np.ndarray:
    """4x4 homogeneous matrix from a 3x3 rotation and a translation."""
    m = np.eye(4)
    m[:3, :3] = np.asarray(R, float)
    m[:3, 3] = np.asarray(t, float).ravel()
    return m


def inverse_matrix(m: np.ndarray) -> np.ndarray:
    R, t = m[:3, :3], m[:3, 3]
    out = np.eye(4)
    out[:3, :3] = R.T
    out[:3, 3] = -R.T @ t
    return out


def _yaw_of(m: np.ndarray) -> float:
    # same as tf euler_from_matrix(..., 'sxyz')[2] away from gimbal lock
    return math.atan2(m[1, 0], m[0, 0])


def get_2d_inverse(pose_2d: Pose2D) -> Pose2D:
    """
    Inverse a 2d transformation, mainly to switch the frame of reference
    :return:            2d tf of [x, y, yaw]
    """
    inv = inverse_matrix(mat_from_2d(pose_2d))
    return inv[0, 3], inv[1, 3], _yaw_of(inv)


def get_centre_tf(tf1: np.ndarray, tf2: np.ndarray, offset=0.0) -> Pose2D:
    """
    Get centre point of both tf1 and tf2, Note that this output new frame
    has a different orientation as the marker, which it's frame is x axis
    (pointing out of the marker) is directed towards the robot's camera.
    :param tf1, tf2:    4x4 homogenous matrix from tf1 and tf2
    :param offset:      (optional) offset target point to the normal
    :return:            2d tf of the centre [x, y, yaw]
    """
    x1, y1, _ = get_2d_pose(tf1)
    x2, y2, _ = get_2d_pose(tf2)
    _x = (x1 + x2) / 2
    _y = (y1 + y2) / 2
    _yaw = -math.atan2((x2 - x1), (y2 - y1))
    _x += math.cos(_yaw) * offset
    _y += math.sin(_yaw) * offset
    return _x, _y, _yaw


def get_2d_pose(_tf: np.ndarray) -> Pose2D:
    """
    :param:   input homogenous matrix
    :return : 2dPose in x, y, yaw format
    """
    return _tf[0, 3], _tf[1, 3], _yaw_of(_tf)


def apply_2d_transform(mat: np.ndarray, transform: Pose2D) -> np.ndarray:
    """
    Apply a 2d transform to a homogenous matrix
    :param mat:         the input 4x4 homogenous matrix
    :param transform :  2d transform which to apply to the mat
    :return :           transformed homogenous transformation matrix
    """
    return np.matmul(mat, mat_from_2d(transform))


def compute_tf_diff(current_tf: np.ndarray, ref_tf: np.ndarray) -> Pose2D:
    """
    Find the diff of two transformation matrix
    :return :  the 2d planer trans fo the 2 inputs; [x, y, yaw]
    """
    tf_diff = np.matmul(inverse_matrix(current_tf), ref_tf)
    return tf_diff[0, 3], tf_diff[1, 3], _yaw_of(tf_diff)


def avg_2d_poses(poses: List[Pose2D]) -> Optional[Pose2D]:
    """
    Provide the average of a list of 2D poses. Yaw is averaged on the circle (fix: upstream summed the angles).
    :param poses    : a list of 2d poses
    :return         : output avg Pose2D
    """
    _l = len(poses)
    if _l == 0:
        return None
    _x = sum(p[0] for p in poses) / _l
    _y = sum(p[1] for p in poses) / _l
    _yaw = math.atan2(sum(math.sin(p[2]) for p in poses), sum(math.cos(p[2]) for p in poses))
    return _x, _y, _yaw


def sat_proportional_filter(
        input: float, abs_min=0.0, abs_max=10.0, factor=1) -> float:
    """
    Simple saturated proportional filter
    :param input                : input value
    :param abs_min and abs_max  : upper and lower bound, abs value
    :param factor               : multiplier factor for the input value
    :return                     : output filtered value, within boundary
    """
    output = 0.0
    input *= factor
    if abs(input) < abs_min:
        if (input < 0):
            output = -abs_min
        else:
            output = abs_min
    elif abs(input) > abs_max:
        if (input > 0):
            output = abs_max
        else:
            output = -abs_max
    else:
        output = input
    return output


def bin_filter(input: float, abs_boundary: float) -> float:
    """
    Simple binary filter, will provide abs_ceiling as a binary output,
    according to the 'negativity' of the input value
    """
    output = abs(abs_boundary)
    if input < 0:
        output = -abs(abs_boundary)
    return output


def flip_yaw(yaw: float) -> float:
    """
    Flip yaw angle by 180 degree, input yaw range should be within
    [-pi, pi] radian. Output will also be within the same range.
    """
    if yaw >= 0:
        return yaw - math.pi
    else:
        return yaw + math.pi


def set_angle(angle: float) -> float:
    """
    Ensure the angle is within the range of [-pi, pi] radian convention
    """
    return math.atan2(math.sin(angle), math.cos(angle))


def flip_base_frame(input: Pose2D):
    """
    Flip the current reference frame by 180 degree. As such, the negativity
    of translation is flipped, and the yaw angle is located at the opposite
    quadrant. Currently is used to flip from 'back dock' to 'front dock'
    """
    return -input[0], -input[1], flip_yaw(input[2])
