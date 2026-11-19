"""Mock servo bus and the day-one sensors. No serial port and no Pi.

The bus keeps the register names in odm_bench/sts3215.py. Present voltage
uses the cited 0.1 V step (SOFTWARE.md section 3). A healthy mock sits at
the 12.0 V rail (netlist SERVO_12V0) with the software angle limits from
software/servo_limits.json and the horn at raw 2048 (center).

Sensors the day-one script asks for:
  camera   a non-empty stand-in frame (the real frame rate is BLOCKER)
  imu      still, level, +z up (SOFTWARE.md section 4)
  eyes     GPIO24 left and GPIO23 right (netlist)
  speaker  48 kHz S32_LE, shutdown line high only while samples are written
  mic      two slots, 48 kHz S32_LE (SOFTWARE.md section 11)
  charge   four body pins, open when not on the cloth (TEST_PLAN section 2)
  meters   12.00 V servo rail and 5.00 V logic rail

This is the mock hardware used in CI. It is not a measurement.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(LAB, "software"))

from odm_bench.joints import IDS, JOINTS  # noqa: E402
from odm_bench.sts3215 import POS_CENTER, VOLT_LSB  # noqa: E402

# Cited, netlist SERVO_12V0 and domain 5V. The mock meter reads the set points.
BEC_V = 12.0
RAIL_5V = 5.0
# Cited, Present Voltage 0.1 V per LSB. 120 * 0.1 = 12.0 V.
VOLT_RAW_12V = 120

# Cited, netlist eye and charge pins.
EYE_LEFT = 24
EYE_RIGHT = 23
CHARGE_STAT_GPIO = 5    # header pin 29
CHARGE_EN_GPIO = 6      # header pin 31

# Cited, TEST_PLAN section 2: different nets on one connector read over 1 Mohm.
OPEN_OHM = 1.0e9

# Cited, SOFTWARE.md section 11 and TEST_PLAN 17: 48 kHz, S32_LE, two channels.
SAMPLE_RATE = 48000
# Lab choice for a short tone: one tenth of full scale, under the 99 percent
# clip line in TEST_PLAN 17.4 (cited). Not an SPL.
TONE_FRACTION = 0.1

CHARGE_PAIRS = (
    ("seat_plus", "seat_minus"),
    ("belly_plus", "belly_minus"),
    ("seat_plus", "belly_minus"),
    ("belly_plus", "seat_minus"),
)


def _limits_by_id():
    import set_angle_limits as lim
    rows = {}
    for joint, spec in lim.load_limits().items():
        rows[spec["id"]] = (spec["raw_soft"][0], spec["raw_soft"][1], joint)
    return rows


class MockBus:
    """In-memory Feetech-style register file, one servo per joint id."""

    def __init__(self, ids=None, voltage_raw=VOLT_RAW_12V, position=POS_CENTER, limits=None):
        self.ids = list(IDS if ids is None else ids)
        table = _limits_by_id()
        self.servos = {}
        for sid in self.ids:
            if limits and sid in limits:
                lo, hi = limits[sid]
            elif sid in table:
                lo, hi = table[sid][0], table[sid][1]
            else:
                lo, hi = 0, 4095
            self.servos[sid] = {
                "min_angle_limit": int(lo),
                "max_angle_limit": int(hi),
                "present_position": int(position),
                "present_voltage": int(voltage_raw),
            }

    def scan(self):
        return list(self.ids)

    def read(self, sid, name):
        if sid not in self.servos:
            raise KeyError(sid)
        return self.servos[sid][name]


class MockHardware:
    """name is the label printed on a mock run: 'mock hardware'."""

    name = "mock hardware"

    def __init__(self, bus=None, bec_v=BEC_V, rail_5v=RAIL_5V, camera=b"mock-frame",
                 imu_n_glitch=None, eyes=None, charge_ohm=None, speaker_fraction=TONE_FRACTION,
                 mic_silent=False):
        self.bus = bus if bus is not None else MockBus()
        self.bec_v = bec_v
        self.rail_5v = rail_5v
        self.camera = camera
        self.imu_n_glitch = imu_n_glitch
        self.eyes = eyes if eyes is not None else (EYE_LEFT, EYE_RIGHT)
        self.charge_ohm = OPEN_OHM if charge_ohm is None else charge_ohm
        self.speaker_fraction = speaker_fraction
        self.mic_silent = mic_silent
        self.eye_log = []
        self.speaker_log = []
        self.amp_sd = 0

    def servo_ids(self):
        return self.bus.scan()

    def read_reg(self, sid, name):
        return self.bus.read(sid, name)

    def meters(self):
        return {"bec_v": self.bec_v, "rail_5v": self.rail_5v}

    def camera_frame(self):
        return self.camera

    def imu_samples(self, n):
        """Level and still: accel (0, 0, +9.81), gyro 0. SOFTWARE.md section 4."""
        out = []
        for i in range(n):
            accel = (0.0, 0.0, 9.81)
            gyro = (0.0, 0.0, 0.0)
            if self.imu_n_glitch is not None and i == self.imu_n_glitch:
                accel = (0.0, 0.0, 9.81 + 1.28)  # the G2 top-bit step imu_check.py names
            out.append((gyro, accel))
        return out

    def eye_cycle(self):
        for level in (1, 0):
            for gpio in self.eyes:
                self.eye_log.append((gpio, level))
        return list(self.eye_log)

    def speaker_tone(self):
        """A few samples and the amp shutdown line. SD is high only while playing (D48)."""
        full = (1 << 31) - 1
        amp = int(self.speaker_fraction * full)
        self.amp_sd = 1
        samples = [amp, -amp, amp, -amp]
        self.speaker_log = samples
        self.amp_sd = 0
        return {"rate": SAMPLE_RATE, "channels": 2, "samples": samples, "sd_after": self.amp_sd}

    def mic_capture(self):
        full = (1 << 31) - 1
        if self.mic_silent:
            left = [0, 0, 0, 0]
            right = [0, 0, 0, 0]
        else:
            # A clap on the left slot first, then the right. Not a measured delay.
            amp = int(TONE_FRACTION * full)
            left = [0, amp, 0, 0]
            right = [0, 0, amp, 0]
        return {"rate": SAMPLE_RATE, "left": left, "right": right}

    def charge_pairs(self):
        return {pair: self.charge_ohm for pair in CHARGE_PAIRS}

    def volts(self, raw):
        return raw * VOLT_LSB
