"""STS3215 register addresses, sizes and units used by the bench scripts.

Sources:
  [U] pypot support-feetech-sts3215 branch at f6d305e, pypot/feetech/sts3215_io.py (the table the
      Runtime configure scripts use); rustypot c8b8223 src/device/feetech_sts3215.rs.
  [U] Runtime scripts/check_voltage.py line 31: Present Voltage x 0.1 = volts.
  [I] github.com/commanderfun/STS3215 REGISTER_REFERENCE.md (commit fc359b0): firmware major/minor
      at 0 and 1, current x 6.5 mA, defaults read from two 12 V units at firmware 3.10.
Registers 0, 1 and 86 are not in the pypot table; the scripts read them with pypot's own READ
packet (bus.read_block). Register 86 (acceleration multiplier) is listed by newer rustypot only
(SERVO_DEEP_DIVE.md section 5); on older firmware it may read 0 or fail: that is reported as is.
"""

# name: (address, size in bytes)
REG = {
    "firmware_major": (0, 1),
    "firmware_minor": (1, 1),
    "model": (3, 2),
    "id": (5, 1),
    "baudrate": (6, 1),
    "return_delay": (7, 1),
    "max_temperature_limit": (13, 1),
    "max_voltage_limit": (14, 1),
    "min_voltage_limit": (15, 1),
    "max_torque_limit": (16, 2),
    "p_coefficient": (21, 1),
    "d_coefficient": (22, 1),
    "i_coefficient": (23, 1),
    "protection_current": (28, 2),
    "mode": (33, 1),
    "protective_torque": (34, 1),
    "protection_time": (35, 1),
    "overload_torque": (36, 1),
    "torque_enable": (40, 1),
    "acceleration": (41, 1),
    "goal_position": (42, 2),
    "goal_time": (44, 2),
    "goal_speed": (46, 2),
    "torque_limit": (48, 2),
    "lock": (55, 1),
    "present_position": (56, 2),
    "present_speed": (58, 2),
    "present_load": (60, 2),
    "present_voltage": (62, 1),
    "present_temperature": (63, 1),
    "status": (65, 1),
    "moving": (66, 1),
    "present_current": (69, 2),
    "maximum_velocity": (84, 1),       # pypot name; TEST_PLAN 7.1 "84"
    "maximum_acceleration": (85, 1),   # pypot: "Not in the Memory Table"; G1: must read 0
    "acceleration_multiplier": (86, 1),
}

# Blocks read in one READ each for the factory dump (contiguous, inside the documented table).
DUMP_BLOCKS = [(0, 20), (20, 20), (40, 16), (56, 15), (77, 10)]

VOLT_LSB = 0.1        # V per LSB [U check_voltage.py]
CURRENT_LSB = 0.0065  # A per LSB [I REGISTER_REFERENCE.md]
POS_CENTER = 2048     # rustypot radians_to_dxl_pos(0) = 2048
MODEL_STS3215 = 777   # pypot conversion.py dynamixelModels 777: "FEETECH_STS3215"

STATUS_BITS = {0: "voltage", 1: "sensor", 2: "temperature", 3: "current", 5: "overload"}  # [I] register 65


def le(data, offset, size):
    return int.from_bytes(bytes(data[offset:offset + size]), "little")


def volts(raw):
    return raw * VOLT_LSB


def current_a(raw):
    """Present Current in A. Bit 15 is treated as a direction bit like speed and load
    (UNVERIFIED for current); the magnitude is what the gates use."""
    mag = raw & 0x7FFF
    return -mag * CURRENT_LSB if raw & 0x8000 else mag * CURRENT_LSB


def status_text(raw):
    return ",".join(v for b, v in STATUS_BITS.items() if raw & (1 << b)) or "ok"


def parse_block(start, data):
    """Map a raw block read at `start` into named registers that fall fully inside it."""
    out = {}
    for name, (addr, size) in REG.items():
        if addr >= start and addr + size <= start + len(data):
            out[name] = le(data, addr - start, size)
    return out
