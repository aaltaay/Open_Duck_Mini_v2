#!/usr/bin/env python3
"""Simulated Feetech STS3215 bus on a pseudo terminal (no hardware).

The real libraries the Runtime uses (rustypot 0.1.0 and pypot support-feetech-sts3215) open
the pty slave as if it were /dev/ttyACM0 and exchange real Feetech packets with it:
  FF FF ID LEN INSTR PARAMS... CHK      CHK = ~(ID + LEN + INSTR + sum(PARAMS)) & 0xFF
  instructions: 0x01 ping, 0x02 read, 0x03 write, 0x04 reg write, 0x05 action, 0x06 reset,
                0x82 sync read (one status packet per listed ID, in order), 0x83 sync write
  status:       FF FF ID LEN ERR DATA... CHK
(protocol per rustypot c8b8223 src/protocol/feetech.rs and pypot v1.py with SYNC_READ = 130).

Model (test model, not a datasheet model):
  - per-servo memory table with STS3215 addresses (odm_bench/sts3215.py); defaults from the
    commanderfun REGISTER_REFERENCE.md factory read, register 85 = 50 as in the third-party build
    log (UPSTREAM_ISSUES.md G1), register 14 = 80 (G4 outside evidence).
  - writing Goal Position turns torque on (assumption: the Runtime HWI.turn_on never writes
    register 40, yet robots stand up, so the real servo must do this or start with torque on).
  - position follows the goal at up to 3400 steps/s (BAM default_max_velocity, SERVO_DEEP_DIVE
    E5); if register 85 is not 0 the speed ramps at reg85 x 40 steps/s^2 (slow, like G1).
  - Present Voltage = floor(10 x V) from a constant or a time profile per servo ID, optionally
    minus a dip that starts at each Goal Position write (goal_dip = (volts, seconds)): a voltage
    locked to the control loop, like the current peak after each 50 Hz command (sim/POWER_FIX.md).
    goal_times keeps the time of every goal write so a test knows the exact time under a level.
  - Present Current from speed and an optional external torque (load rig, D2 thermal test),
    with the servo's own over-current unload (registers 28 and 35, like TEST_PLAN 7.4).
  - temperature: first order, T_ss = ambient + k x I^2.
Optional wire timing emulates 1 Mbaud 8N1 (10 us per byte) plus return delay and USB latency.
Faults per ID: no answer, corrupted checksums, a late status packet (G10 panic path), garbage.

Standalone use (rehearse the bench scripts on a PC):
  python3 fake_sts3215.py --link /tmp/fake_servo_bus --ids 10-14,20-24,30-33
  LD_PRELOAD=<built pty_shim.so> python3 ../power_log.py --port /tmp/fake_servo_bus ...
"""
import argparse
import bisect
import math
import os
import select
import threading
import time
import tty

PING, READ, WRITE, REG_WRITE, ACTION, RESET, SYNC_READ, SYNC_WRITE = 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x82, 0x83
BROADCAST = 0xFE
STEPS_PER_RAD = 4096 / (2 * math.pi)
KT_NM_PER_A = 1.91 / 2.5      # C001 datasheet stall 1.91 Nm at 2.5 A (SERVO_DEEP_DIVE section 2)


def checksum(body):
    return (~sum(body)) & 0xFF


def packet(sid, first, params):
    body = bytes([sid, len(params) + 2, first]) + bytes(params)
    return b"\xff\xff" + body + bytes([checksum(body)])


class VoltageProfile:
    """t (s) -> volts per servo ID, linear interpolation, from a CSV with t_s and v_<id> columns."""

    def __init__(self, path=None, rows=None, speed=1.0, quantize_floor=True):
        self.t, self.v = [], {}
        if path:
            with open(path) as fh:
                lines = [ln for ln in fh if not ln.startswith("#")]
            cols = lines[0].strip().split(",")
            ids = [(k, int(c[2:])) for k, c in enumerate(cols) if c.startswith("v_")]
            for ln in lines[1:]:
                f = ln.strip().split(",")
                self.t.append(float(f[0]))
                for k, sid in ids:
                    self.v.setdefault(sid, []).append(float(f[k]))
        if rows:
            for t, vals in rows:
                self.t.append(t)
                for sid, v in vals.items():
                    self.v.setdefault(sid, []).append(v)
        self.speed = speed
        self.t0 = None

    def start(self, now):
        self.t0 = now

    @property
    def duration(self):
        return self.t[-1] if self.t else 0.0

    def at(self, sid, now):
        if self.t0 is None:
            self.t0 = now
        if now < self.t0:
            return None                  # not started yet: the servo's constant supply applies
        x = (now - self.t0) * self.speed
        col = self.v.get(sid)
        if col is None:
            return None
        if x <= self.t[0]:
            return col[0]
        if x >= self.t[-1]:
            return col[-1]
        k = bisect.bisect_right(self.t, x)
        t0, t1 = self.t[k - 1], self.t[k]
        return col[k - 1] + (col[k] - col[k - 1]) * (x - t0) / (t1 - t0)


class FakeServo:
    def __init__(self, sid, fw=(3, 10), reg85=50, max_voltage_limit=80, volts=7.4):
        m = bytearray(256)
        m[0], m[1] = fw
        m[3], m[4] = 777 & 0xFF, 777 >> 8          # model 777 = FEETECH_STS3215 in pypot
        m[5] = sid
        m[6] = 0                                   # 1 Mbps
        m[7] = 0                                   # return delay
        m[8] = 1                                   # response level
        m[11], m[12] = 4095 & 0xFF, 4095 >> 8
        m[13] = 70                                 # max temperature limit (REGISTER_REFERENCE.md)
        m[14] = max_voltage_limit
        m[15] = 40
        m[16], m[17] = 1000 & 0xFF, 1000 >> 8
        m[18], m[19], m[20] = 12, 44, 47
        m[21], m[22], m[23] = 32, 32, 0
        m[24] = 16
        m[26] = m[27] = 1
        m[28], m[29] = 310 & 0xFF, 310 >> 8        # protection current 310 x 6.5 mA = 2.0 A
        m[30] = 1
        m[34], m[35], m[36] = 20, 200, 80          # protection time 200 x 10 ms = 2 s
        m[42], m[43] = 2048 & 0xFF, 2048 >> 8
        m[48], m[49] = 1000 & 0xFF, 1000 >> 8
        m[55] = 1
        m[85] = reg85
        self.mem = m
        self.pos = 2048.0
        self.vel = 0.0
        self.temp = 25.0
        self.ambient = 25.0
        self.heat_k = 15.0                         # C per A^2 at steady state (test model)
        self.tau = 60.0
        self.ext_torque_nm = 0.0                   # load rig torque while holding
        self.volts = volts
        self.profile = None
        self.goal_dip = None                       # (volts, seconds): dip after each goal write
        self.goal_times = []                       # monotonic time of each goal write
        self.i_ext = None                          # forced current profile (callable now -> A)
        self.temp_profile = None                   # forced temperature (callable now -> C), tests
        self.over_i_since = None
        self.t_last = None
        self.lock = threading.Lock()

    # register helpers
    def u16(self, a):
        return self.mem[a] | (self.mem[a + 1] << 8)

    def set16(self, a, v):
        v &= 0xFFFF
        self.mem[a], self.mem[a + 1] = v & 0xFF, v >> 8

    def supply(self, now):
        v = None
        if self.profile is not None:
            v = self.profile.at(self.mem[5], now)
        if v is None:
            v = self.volts
        if self.goal_dip and self.goal_times and 0.0 <= now - self.goal_times[-1] < self.goal_dip[1]:
            v -= self.goal_dip[0]
        return v

    def update(self, now):
        with self.lock:
            if self.t_last is None:
                self.t_last = now
            dt = max(0.0, now - self.t_last)
            self.t_last = now
            torque = self.mem[40] == 1
            if torque and dt > 0:
                goal = float(self.u16(42) & 0x7FFF)
                vmax = 3400.0
                gs = self.u16(46)
                if gs:
                    vmax = min(vmax, float(gs))
                err = goal - self.pos
                want = max(-vmax, min(vmax, err / dt))
                acc = self.mem[85] * 40.0
                if acc > 0:
                    dv = want - self.vel
                    dv = max(-acc * dt, min(acc * dt, dv))
                    self.vel += dv
                else:
                    self.vel = want
                self.pos += self.vel * dt
                if (err > 0 and self.pos > goal) or (err < 0 and self.pos < goal):
                    self.pos, self.vel = goal, 0.0
            elif not torque:
                self.vel = 0.0
            # current: idle + speed term + held external torque
            if self.i_ext is not None:
                cur = self.i_ext(now)
            else:
                cur = 0.006 + 0.15 * abs(self.vel) / 3400.0 + (abs(self.ext_torque_nm) / KT_NM_PER_A if torque else 0.0)
            # over-current unload: above protection current for protection time
            lim = self.u16(28) * 0.0065
            if torque and cur > lim:
                if self.over_i_since is None:
                    self.over_i_since = now
                elif now - self.over_i_since > self.mem[35] * 0.01:
                    self.mem[40] = 0
                    self.mem[65] |= 0x20 | 0x08
            else:
                self.over_i_since = None
            if self.temp_profile is not None:
                self.temp = float(self.temp_profile(now))
            elif dt > 0:
                tss = self.ambient + self.heat_k * cur * cur
                self.temp += (tss - self.temp) * min(1.0, dt / self.tau)
            v = self.supply(now)
            self.mem[62] = max(0, min(255, int(math.floor(v * 10.0 + 1e-6))))
            self.mem[63] = max(0, min(255, int(round(self.temp))))
            if v < self.mem[15] * 0.1:
                self.mem[65] |= 0x01
            self.set16(56, int(round(self.pos)) % 4096)
            sp = int(round(abs(self.vel)))
            self.set16(58, sp | (0x8000 if self.vel < 0 else 0))
            load = int(min(1000, abs(self.ext_torque_nm) / 1.91 * 1000)) if torque else 0
            self.set16(60, load)
            ic = int(round(abs(cur) / 0.0065))
            self.set16(69, min(ic, 0x7FFF))
            self.mem[66] = 1 if abs(self.vel) > 1 else 0

    def read(self, addr, n, now):
        self.update(now)
        return bytes(self.mem[addr:addr + n])

    def write(self, addr, data, now):
        self.update(now)
        with self.lock:
            for k, b in enumerate(data):
                self.mem[addr + k] = b
            if addr <= 42 < addr + len(data) or addr <= 43 < addr + len(data):
                self.mem[40] = 1                    # goal write turns torque on (see module doc)
                self.mem[65] &= ~0x28 & 0xFF
                if len(self.goal_times) < 200000:
                    self.goal_times.append(now)
            if addr <= 40 < addr + len(data) and self.mem[40] == 1:
                self.mem[65] &= ~0x28 & 0xFF


class Fault:
    def __init__(self):
        self.drop = False
        self.corrupt_next = 0
        self.late_s = 0.0          # deliver this servo's next status packet late
        self.late_count = 0


class FakeBus:
    def __init__(self, servos, wire_time=False, usb_latency_s=0.0, link=None):
        self.servos = {s.mem[5]: s for s in servos}
        self.wire_time = wire_time
        self.usb_latency_s = usb_latency_s
        self.master, self.slave = os.openpty()
        tty.setraw(self.slave)
        self.path = os.ttyname(self.slave)
        self.link = link
        if link:
            if os.path.lexists(link):
                os.unlink(link)
            os.symlink(self.path, link)
        self.faults = {}
        self.log = []                  # (t, "rx"/"tx", bytes)
        self.log_on = True
        self.counts = {}
        self._stop = False
        self._buf = b""
        self._wlock = threading.Lock()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def fault(self, sid):
        return self.faults.setdefault(sid, Fault())

    def set_profile(self, profile, delay_s=0.0):
        """Servo voltages follow `profile`; its time 0 is `delay_s` from now (first row before)."""
        now = time.monotonic()
        profile.start(now + delay_s)
        for s in self.servos.values():
            s.profile = profile

    def stop(self):
        self._stop = True
        self._thread.join(timeout=1)
        for fd in (self.master, self.slave):
            try:
                os.close(fd)
            except OSError:
                pass
        if self.link and os.path.islink(self.link):
            os.unlink(self.link)

    # wire timing
    def _wait_bytes(self, n, t_from):
        if not self.wire_time:
            return time.monotonic()
        t_end = t_from + n * 10e-6
        while True:
            now = time.monotonic()
            if now >= t_end:
                return now
            if t_end - now > 0.0005:
                time.sleep(t_end - now - 0.0003)

    def _send(self, data):
        with self._wlock:
            os.write(self.master, data)
        if self.log_on:
            self.log.append((time.monotonic(), "tx", data))

    def _loop(self):
        while not self._stop:
            r, _, _ = select.select([self.master], [], [], 0.05)
            if not r:
                continue
            try:
                d = os.read(self.master, 4096)
            except OSError:
                time.sleep(0.01)
                continue
            self._buf += d
            self._parse()

    def _parse(self):
        while True:
            i = self._buf.find(b"\xff\xff")
            if i < 0:
                self._buf = self._buf[-1:] if self._buf.endswith(b"\xff") else b""
                return
            self._buf = self._buf[i:]
            if len(self._buf) < 4:
                return
            n = self._buf[3]
            if len(self._buf) < 4 + n:
                return
            pkt, self._buf = self._buf[:4 + n], self._buf[4 + n:]
            t_rx = time.monotonic()
            if self.log_on:
                self.log.append((t_rx, "rx", pkt))
            if checksum(pkt[2:-1]) != pkt[-1]:
                self.counts["bad_rx"] = self.counts.get("bad_rx", 0) + 1
                continue
            self._handle(pkt, t_rx)

    def _status(self, sid, params, err=0):
        f = self.faults.get(sid)
        p = packet(sid, err, params)
        if f and f.corrupt_next > 0:
            f.corrupt_next -= 1
            p = p[:-1] + bytes([p[-1] ^ 0x5A])
        return p

    def _reply(self, sid, params, t_ready, err=0):
        f = self.faults.get(sid)
        if f and f.drop:
            return t_ready
        p = self._status(sid, params, err)
        t = self._wait_bytes(len(p), t_ready)
        if f and f.late_count > 0:
            f.late_count -= 1
            threading.Timer(f.late_s, self._send, args=(p,)).start()
            return t
        self._send(p)
        return t

    def _handle(self, pkt, t_rx):
        sid, inst, params = pkt[2], pkt[4], pkt[5:-1]
        self.counts[inst] = self.counts.get(inst, 0) + 1
        t = self._wait_bytes(len(pkt), t_rx) + self.usb_latency_s
        if self.usb_latency_s:
            while time.monotonic() < t:
                time.sleep(0.0001)
        now = time.monotonic()        # with wire timing: when the packet's last byte has arrived
        if inst == SYNC_READ:
            addr, ln, ids = params[0], params[1], params[2:]
            for i in ids:
                s = self.servos.get(i)
                if s is None:
                    continue
                t = self._reply(i, s.read(addr, ln, time.monotonic()), t + s.mem[7] * 2e-6)
            return
        if inst == SYNC_WRITE:
            addr, ln = params[0], params[1]
            body = params[2:]
            pairs = [(body[k], body[k + 1:k + 1 + ln]) for k in range(0, len(body) - ln, ln + 1)]
            for i, data in pairs:
                s = self.servos.get(i)
                if s is not None:
                    s.write(addr, data, now)
                    if addr == 5:
                        self.servos[data[0]] = self.servos.pop(i)
            return
        targets = list(self.servos.values()) if sid == BROADCAST else [self.servos[sid]] if sid in self.servos else []
        for s in targets:
            sid_now = s.mem[5]
            if inst == PING:
                if sid != BROADCAST:
                    self._reply(sid_now, b"", t)
            elif inst == READ:
                addr, ln = params[0], params[1]
                if sid != BROADCAST:
                    self._reply(sid_now, s.read(addr, ln, now), t)
            elif inst in (WRITE, REG_WRITE):
                addr, data = params[0], params[1:]
                if inst == WRITE:
                    s.write(addr, data, now)
                    if addr == 5:
                        self.servos[data[0]] = self.servos.pop(sid_now)
                else:
                    s._pending = (addr, bytes(data))
                if sid != BROADCAST and s.mem[8] >= 1:
                    self._reply(s.mem[5], b"", t)
            elif inst == ACTION:
                pend = getattr(s, "_pending", None)
                if pend:
                    s.write(pend[0], pend[1], now)
                    s._pending = None
            elif inst == RESET:
                pass

    def inject_garbage(self, data=b"\x13\x37\x00"):
        self._send(data)

    def babble(self, seconds):
        """Stray single bytes back to back for `seconds` (a device talking out of turn): the input
        buffer keeps filling while a library flushes it (rustypot's flush-then-assert, G10)."""
        def run():
            t_end = time.monotonic() + seconds
            while time.monotonic() < t_end and not self._stop:
                with self._wlock:
                    os.write(self.master, b"\x00")
        threading.Thread(target=run, daemon=True).start()


def parse_ids(text):
    out = []
    for part in text.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--link", default="/tmp/fake_servo_bus", help="symlink to the pty slave")
    ap.add_argument("--ids", default="10-14,20-24,30-33", help="servo IDs on the bus (factory servo: 1)")
    ap.add_argument("--volts", type=float, default=7.2)
    ap.add_argument("--profile", help="CSV voltage profile (t_s, v_<id> columns), e.g. tests/data/*.csv")
    ap.add_argument("--speed", type=float, default=1.0, help="profile time scale")
    ap.add_argument("--reg85", type=int, default=50)
    ap.add_argument("--wire-time", action="store_true", help="emulate 1 Mbaud wire time")
    a = ap.parse_args()
    bus = FakeBus([FakeServo(i, reg85=a.reg85, volts=a.volts) for i in parse_ids(a.ids)], wire_time=a.wire_time, link=a.link)
    bus.log_on = False
    if a.profile:
        bus.set_profile(VoltageProfile(a.profile, speed=a.speed))
    print(f"fake STS3215 bus on {bus.path} (link {a.link}), IDs {sorted(bus.servos)}; Ctrl-C to stop", flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        bus.stop()


if __name__ == "__main__":
    main()
