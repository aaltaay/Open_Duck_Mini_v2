"""Accelerated home plant for the autonomy soak.

Pack voltage uses the digitized P45B figure (twin/electromech/p45b.py), three
cells in series, which is the netlist pack. Walk current is the only published
mean, 5.144 A (sim pass only, problems/FIT3.md, 0.15 m/s typical). That walk
used a 16 V regulator set point that is superseded. A mean pack current on the
held 12.0 V rail is BLOCKER. The 10 s held-rail peak is 9.261 A (sim pass only,
problems/HOLD12_WALK.md), under the 45 A cell line and under the 30 A board.

Charge current is 1.006 A (calc only, the BQ24133 ISET divider, netlist and
circuitry/BQ24133_BOARD.md). It is inside the cited 0.6 A to 2.5 A chip window
and under the cited 13.5 A cell charge maximum.

Knee temperature is a first-order fit (calc only) to two sim pass only points
in twin/life/LIFE.md: 22 C room, 60 C at 3.7 minutes, unguarded end 99.3 C.
Cooling uses that same time constant toward the torque-off end of 24.6 C.
The cool-down constant is not published. BLOCKER. It is an assumption.
"""

from __future__ import annotations

import math

from altaay_lab.software.personality.limits import PACK_LOW_V
from altaay_lab.twin.electromech.p45b import P45B

# sim pass only, FIT3.md. See the module note. Not a new set point.
WALK_PACK_A = 5.144

# Cited, STS3215 idle, twin/thermal/BQ24133_HEAT.md.
SERVO_IDLE_A = 0.021
SERVO_COUNT = 14

# Cited set point of the held rail. Not scanned as BEC_V.
RAIL_V = 12.0

# Cited minimum, verify/part_limits.yaml servo_reg eff_min.
I7C_EFF_MIN = 0.94

# Cited typical Pi draw, part_limits pi_zero_2w, times the 5 V rail.
# The 5 V regulator efficiency was not copied. BLOCKER. This term adds the
# watts with no extra loss, so the pack current is a lower bound on the Pi.
PI_W = 0.350 * 5.0

# Calc only, netlist CHG ratings i_charge_a.
CHARGE_A = 1.006

# sim pass only, LIFE.md, 22 C room, right knee reading.
T_ROOM_C = 22.0
T_HOT_C = 99.3
T_60_C = 60.0
T_60_S = 3.7 * 60.0
T_OFF_C = 24.6


def heat_tau_s():
    """Seconds. Calc only from the two LIFE.md points above."""
    ratio = (T_60_C - T_HOT_C) / (T_ROOM_C - T_HOT_C)
    return T_60_S / -math.log(ratio)


def idle_pack_a(pack_v):
    """Pack current while torque is off. Calc only from the cited pieces above."""
    v = max(float(pack_v), PACK_LOW_V)
    p_servo = SERVO_COUNT * SERVO_IDLE_A * RAIL_V
    return p_servo / (I7C_EFF_MIN * v) + PI_W / v


class HomePlant:
    """Voltage, knee temperature, and posture. No room geometry.

    A floor plan and a live camera are BLOCKER. Dock success is sampled by
    the supervisor from the measured 40, not from a new physics run.
    """

    def __init__(self, cell=None):
        self.cell = cell if cell is not None else P45B()
        self.q_mAh = 0.0
        self.knee_c = T_ROOM_C
        self.t = 0.0
        self.posture = "standing"
        self.idle_s = 0.0
        self.fallen = False
        self.attention = "none"
        self.face_close = False
        self.bearing = None
        self.tau_s = heat_tau_s()
        self.v_pack = self._terminal(idle_pack_a(3.0 * self.cell.ocv(0.0)))
        self.min_pack_v = self.v_pack
        self.at_floor = False
        self.motion = "sit"

    def ocv_pack(self):
        return 3.0 * float(self.cell.ocv(self.q_mAh))

    def _terminal(self, amps):
        return 3.0 * float(self.cell.v_steady(self.q_mAh, max(0.0, amps)))

    def current_a(self, motion):
        if motion == "charge":
            return -CHARGE_A
        if motion in ("walk", "stand", "getup"):
            return WALK_PACK_A
        v = self.ocv_pack()
        return idle_pack_a(v)

    def advance(self, motion, dt):
        """Move energy and heat forward by dt seconds. Does not cross 9.0 V."""
        dt = float(dt)
        if dt < 0.0:
            raise ValueError("dt must be >= 0")
        left = dt
        while left > 1e-9:
            step = min(left, 0.25)
            self._step(motion, step)
            left -= step
        self.t += dt
        self.motion = motion

    def _step(self, motion, step):
        heat_on = motion in ("walk", "stand", "getup")
        target = T_HOT_C if heat_on else T_OFF_C
        self.knee_c = target + (self.knee_c - target) * math.exp(-step / self.tau_s)
        if self.knee_c < 0.0:
            self.knee_c = 0.0
        if self.knee_c > 120.0:
            self.knee_c = 120.0

        if motion in ("walk", "getup"):
            self.posture = "walking"
            self.idle_s = 0.0
        elif motion == "stand":
            self.posture = "standing"
            self.idle_s = 0.0
        else:
            self.posture = "sitting"
            self.idle_s += step

        if motion == "charge":
            self.q_mAh = max(0.0, self.q_mAh - CHARGE_A * step / 3.6)
            self.v_pack = self.ocv_pack()
            self.at_floor = False
        else:
            amps = WALK_PACK_A if motion in ("walk", "stand", "getup") else idle_pack_a(self.ocv_pack())
            nxt = self.q_mAh + amps * step / 3.6
            nxt = min(nxt, float(self.cell.q_end))
            saved = self.q_mAh
            self.q_mAh = nxt
            v = self._terminal(amps)
            if v < PACK_LOW_V:
                self.q_mAh = saved
                self.at_floor = True
                self.v_pack = max(self._terminal(amps), PACK_LOW_V)
            else:
                self.at_floor = False
                self.v_pack = v
        if self.v_pack < self.min_pack_v:
            self.min_pack_v = self.v_pack

    def snapshot(self):
        return {
            "q_mAh": self.q_mAh,
            "knee_c": self.knee_c,
            "t": self.t,
            "posture": self.posture,
            "idle_s": self.idle_s,
            "fallen": self.fallen,
            "v_pack": self.v_pack,
            "min_pack_v": self.min_pack_v,
            "at_floor": self.at_floor,
            "attention": self.attention,
            "face_close": self.face_close,
            "bearing": self.bearing,
        }

    def restore(self, saved):
        for name in (
            "q_mAh", "knee_c", "t", "posture", "idle_s", "fallen",
            "v_pack", "min_pack_v", "at_floor", "attention", "face_close", "bearing",
        ):
            setattr(self, name, saved[name])
