"""The simulated bus speaks the Feetech protocol the Runtime libraries use."""
import json
import subprocess
import os

from conftest import IDS, PY, TESTS, needs_libs

import fake_sts3215 as fk


def test_checksum_matches_rustypot_unit_vectors():
    # rustypot c8b8223 src/protocol/feetech.rs tests: ping id 1 and read id 1 addr 0x2B len 1
    assert fk.packet(1, fk.PING, b"") == bytes([0xFF, 0xFF, 0x01, 0x02, 0x01, 0xFB])
    assert fk.packet(1, fk.READ, bytes([0x2B, 0x01])) == bytes([0xFF, 0xFF, 0x01, 0x04, 0x02, 0x2B, 0x01, 0xCC])
    # sync read of ids 11, 12 at 30 length 2 (same file, create_sync_read_packet)
    p = fk.packet(0xFE, fk.SYNC_READ, bytes([0x1E, 0x02, 0x0B, 0x0C]))
    assert p == bytes([0xFF, 0xFF, 0xFE, 0x06, 0x82, 0x1E, 0x02, 0x0B, 0x0C, 0x42])


CLIENT = r'''
import json, sys, time
import rustypot
from pypot.feetech import FeetechSTS3215IO
port = sys.argv[1]
ids = [20,21,22,23,24,30,31,32,33,10,11,12,13,14]
out = {}
p = FeetechSTS3215IO(port, baudrate=1000000, use_sync_read=True)   # check_voltage.py call, opened first
out["pypot_voltage"] = list(p.get_present_voltage(ids))
out["pypot_model"] = list(p.get_model([20]))
io = rustypot.feetech(port, 1000000)                                  # rustypot_position_hwi.py line 77
out["pos0"] = io.read_present_position(ids)
io.write_goal_position(ids, [0.3] * 14)
time.sleep(0.5)
out["pos1"] = io.read_present_position(ids)
out["vel"] = io.read_present_velocity(ids)
io.set_kps(ids, [30.0] * 14)
time.sleep(0.01)   # raw pypot flushes OUTPUT before sending: give rustypot's write time to leave
out["P"] = list(p.get_P_coefficient([20, 14]))
io.disable_torque(ids)
time.sleep(0.01)
out["torque"] = list(p.is_torque_enabled([20, 14]))
print(json.dumps(out))
'''


@needs_libs
def test_real_libraries_against_fake_bus(make_bus, shim):
    bus = make_bus(reg85=0, volts=7.2)
    env = dict(os.environ, LD_PRELOAD=shim, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([PY, "-c", CLIENT, bus.path], capture_output=True, text=True, env=env, timeout=60)
    assert r.returncode == 0, r.stderr[-2000:]
    out = json.loads(r.stdout.strip().splitlines()[-1])
    assert out["pypot_voltage"] == [72] * 14
    assert out["pypot_model"] == ["FEETECH_STS3215"]
    assert all(abs(x) < 1e-3 for x in out["pos0"])
    assert all(abs(x - 0.3) < 0.01 for x in out["pos1"])       # goal reached (reg 85 = 0)
    assert out["P"] == [30, 30]
    assert out["torque"] == [False, False]
    # packets actually seen on the wire, sizes as in software/SOFTWARE.md section 6
    rx = [pkt for _, d, pkt in bus.log if d == "rx"]
    sync_reads = [p for p in rx if p[4] == fk.SYNC_READ and p[5] == 56]
    sync_writes = [p for p in rx if p[4] == fk.SYNC_WRITE and p[5] == 42]
    assert sync_reads and len(sync_reads[0]) == 22                 # position sync read request, 14 IDs
    assert sync_writes and len(sync_writes[0]) == 50               # goal sync write, 14 IDs x 2 bytes
    tx56 = [pkt for _, d, pkt in bus.log if d == "tx" and len(pkt) == 8]
    assert tx56                                                    # 8-byte status packets for 2-byte reads


RACE = r"""
import json, sys
sys.path.insert(0, sys.argv[2])
import rustypot
from pypot.feetech import FeetechSTS3215IO
from odm_bench import bus
port = sys.argv[1]
ids = [20, 21]
res = {}
for mode in ("raw", "safe"):
    p = FeetechSTS3215IO(port, baudrate=1000000, use_sync_read=True)
    if mode == "safe":
        bus.make_flush_safe(p)
    io = rustypot.feetech(port, 1000000) if mode == "raw" else res["_io"]
    res["_io"] = io
    lost = 0
    for k in range(150):
        kp = 10 + (k % 40)
        io.set_kps(ids, [float(kp)] * 2)          # sync write, no reply
        got = p.get_P_coefficient(ids)            # pypot right after: flush, then read
        lost += tuple(got) != (kp, kp)
    res[mode] = lost
    p.close()
res.pop("_io")
print(json.dumps(res))
"""


@needs_libs
def test_pypot_output_flush_race_and_the_safe_flush(make_bus, shim):
    """Raw pypot can discard a rustypot sync write still in the tty output queue (TCOFLUSH);
    odm_bench.bus.make_flush_safe (tcdrain + input flush only) never loses one."""
    bus = make_bus(ids=[20, 21], reg85=0)
    env = dict(os.environ, LD_PRELOAD=shim, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([PY, "-c", RACE, bus.path, str(TESTS.parent)], capture_output=True, text=True, env=env,
                       timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
    res = json.loads(r.stdout.strip().splitlines()[-1])
    print("lost writes out of 150:", res)
    assert res["safe"] == 0
