#!/usr/bin/env python3
"""Write the servo angle limit registers to the software limits of D59 (3 deg inside every hard stop).

The limits come from software/servo_limits.json (twin/sit/servo_limits.py: the URDF ranges, the designed sit stops and
the CAD contacts); the zero offsets from the duck config the Runtime reads (joints_offsets, radians, added to every goal
by rustypot_position_hwi.py lines 111 and 120 at 376de65). Registers [U] rustypot c8b8223 src/device/feetech_sts3215.rs
and pypot f6d305e sts3215_io.py: min angle limit 9 and max angle limit 11 (u16, raw steps), lock 55 (EEPROM write lock).
Factory values 0 and 4095 (no limit). Raw = 2048 + (q + offset) x 4096 / 2 pi (rustypot's conversion; STS3250 knees the
same, KNEE_TWIN.md section 2). A range that would cross the 0/4095 wrap is refused: no register offset is written (the
lab keeps register 31 at 0 and the Runtime offsets in the config).

  python3 set_angle_limits.py [--config duck_config.json] [--ids 23,13]            print the table (no bus)
  python3 set_angle_limits.py --port /dev/ttyACM0 --write [--ids ...] [--zero-offsets]
      torque off, unlock, write 9 and 11, lock, read back; exit 0 when every servo reads back its values.
--zero-offsets writes the limits for a zero offset (bring-up of one servo before its horn goes on, TEST_PLAN 7.1);
run it again with the calibrated config after TEST_PLAN 19 (software/CALIBRATION.md).
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
LIMITS = os.path.join(LAB, "software", "servo_limits.json")
CONFIG = os.path.join(LAB, "software", "duck_config.altaay.json")
STEPS = 4096 / (2 * math.pi)


def load_limits(path=LIMITS):
    J = json.load(open(path))
    return J["joints"]


def load_offsets(path=CONFIG):
    J = json.load(open(path))
    return {k: float(v) for k, v in J.get("joints_offsets", {}).items()}


def registers(soft_lo_deg, soft_hi_deg, offset_rad=0.0):
    """(min raw, max raw) for a joint's software limits and its zero offset; ValueError if the range wraps"""
    lo = 2048 + (math.radians(soft_lo_deg) + offset_rad) * STEPS
    hi = 2048 + (math.radians(soft_hi_deg) + offset_rad) * STEPS
    lo, hi = int(math.ceil(lo)), int(math.floor(hi))        # round inward: never past the software limit
    if not (0 < lo < hi < 4095):
        raise ValueError("range %d..%d crosses the 0/4095 encoder wrap (offset %.3f rad)" % (lo, hi, offset_rad))
    return lo, hi


def table(limits, offsets, ids=None, zero_offsets=False):
    rows = []
    for jn, v in limits.items():
        if ids and v["id"] not in ids:
            continue
        off = 0.0 if zero_offsets else offsets.get(jn, 0.0)
        lo, hi = registers(v["soft_lo_deg"], v["soft_hi_deg"], off)
        rows.append(dict(joint=jn, id=v["id"], soft_deg=[v["soft_lo_deg"], v["soft_hi_deg"]], offset_rad=off, min_raw=lo, max_raw=hi,
                         margin_to_wrap=min(lo, 4095 - hi)))
    return rows


def write_bus(port, rows):
    sys.path.insert(0, HERE)
    from odm_bench import bus
    return write_rows(bus.open_pypot(port, sync_read=False), rows)


def write_rows(io, rows):
    """write and read back the limit registers of `rows` (table()) on an open bus (bench/first_servo_check.py uses it at
    bring-up, after 7.1); True when every servo reads back its values"""
    sys.path.insert(0, HERE)
    from odm_bench import bus, sts3215
    ok = True
    for r in rows:
        sid = r["id"]
        if not bus.ping(io, sid):
            print("servo %d (%s): no answer" % (sid, r["joint"]))
            ok = False
            continue
        io.disable_torque([sid])
        bus.write_block(io, sid, sts3215.REG["lock"][0], bytes([0]))
        bus.write_block(io, sid, sts3215.REG["min_angle_limit"][0], int(r["min_raw"]).to_bytes(2, "little"))
        bus.write_block(io, sid, sts3215.REG["max_angle_limit"][0], int(r["max_raw"]).to_bytes(2, "little"))
        bus.write_block(io, sid, sts3215.REG["lock"][0], bytes([1]))
        got = (bus.read_reg(io, sid, "min_angle_limit"), bus.read_reg(io, sid, "max_angle_limit"))
        r["read_back"] = list(got)
        good = got == (r["min_raw"], r["max_raw"])
        ok &= good
        print("servo %d %-16s min %4d max %4d read back %s %s" % (sid, r["joint"], r["min_raw"], r["max_raw"], got, "OK" if good else "MISMATCH"))
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--config", default=CONFIG)
    ap.add_argument("--limits", default=LIMITS)
    ap.add_argument("--ids", type=lambda s: [int(x) for x in s.split(",")])
    ap.add_argument("--zero-offsets", action="store_true")
    a = ap.parse_args(argv)
    rows = table(load_limits(a.limits), load_offsets(a.config), a.ids, a.zero_offsets)
    for r in rows:
        print("%-16s id %2d soft %7.2f .. %7.2f deg  offset %+.4f rad  registers 9 = %4d, 11 = %4d  (wrap margin %d)" % (
            r["joint"], r["id"], r["soft_deg"][0], r["soft_deg"][1], r["offset_rad"], r["min_raw"], r["max_raw"], r["margin_to_wrap"]))
    if a.write:
        if not a.port:
            ap.error("--write needs --port")
        return 0 if write_bus(a.port, rows) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
