"""Fake Blinka `busio` for tests: an I2C bus with a byte-level BNO055 at 0x28.

The real adafruit_bno055 5.4.13 driver runs on top of it: chip ID, page and mode registers,
axis remap registers 0x41/0x42 (applied to the physical axes like the chip does), offsets
0x55 to 0x6A, calibration status 0x35, data registers ACC 0x08 (1 m/s^2 = 100 LSB) and
GYR 0x14 (1 dps = 16 LSB). Physical motion is given in the policy frame (x forward, y left,
z up; checked in MuJoCo, software/SOFTWARE.md) and turned into chip axes by a mounting.

Config: ODM_FAKE_IMU (JSON text) or ODM_FAKE_IMU_FILE (JSON file, read again when it changes):
  {"pitch_deg": 0, "roll_deg": 0,        held tilt; pitch + = nose down, roll + = right side down
   "rate": [wx, wy, wz],                 rad/s in the policy frame
   "mount": "runtime",                   runtime | flip_x | rot180z | rot90z
   "noise_acc": 0.01, "noise_gyro": 0.002,
   "glitch_prob": 0.0, "glitch_every": 0, flip bit 7 of the first data byte (UPSTREAM_ISSUES G2)
   "oserror_every": 0, "seed": 1}
"""
import json
import math
import os
import random
import struct

G = 9.81


def _cfg():
    path = os.environ.get("ODM_FAKE_IMU_FILE")
    if path and os.path.exists(path):
        try:
            with open(path) as fh:
                return json.load(fh)
        except (OSError, ValueError):
            pass
    txt = os.environ.get("ODM_FAKE_IMU")
    return json.loads(txt) if txt else {}


def _mount(r, kind):
    """Policy-frame vector -> chip physical axes. 'runtime' is the mounting the Runtime remap
    (Y, X, Z; -, +, +) expects: out = (-p_y, p_x, p_z) = r  =>  p = (r_y, -r_x, r_z)."""
    x, y, z = r
    if kind == "flip_x":            # board upside down, flipped about the robot x axis
        x, y, z = x, -y, -z
    elif kind == "rot180z":         # board turned half a turn in its plane
        x, y, z = -x, -y, z
    elif kind == "rot90z":          # board turned a quarter turn in its plane
        x, y, z = -y, x, z
    return (y, -x, z)


class FakeBNO055:
    def __init__(self):
        self.pages = [bytearray(256), bytearray(256)]
        p0 = self.pages[0]
        p0[0x00] = 0xA0
        p0[0x01] = 0xFB
        p0[0x35] = 0xFF
        p0[0x41] = 0x24
        p0[0x42] = 0x00
        self.reads = 0
        self.data_reads = 0
        self.glitches = 0
        self.rng = random.Random(1)
        self._seeded = None

    @property
    def page(self):
        return self.pages[self.pages[0][0x07] & 1]

    def _physical(self, cfg):
        th = math.radians(cfg.get("pitch_deg", 0.0))
        ph = math.radians(cfg.get("roll_deg", 0.0))
        # specific force of gravity in the policy frame (MuJoCo: level -> (0, 0, +9.81),
        # pitch +20 about +y -> x = -3.36, roll +20 about +x -> y = +3.36)
        f = (-G * math.sin(th) * math.cos(ph), G * math.sin(ph), G * math.cos(th) * math.cos(ph))
        w = tuple(cfg.get("rate", [0.0, 0.0, 0.0]))
        return f, w

    def _remap(self, p):
        cfg_reg, sign_reg = self.pages[0][0x41], self.pages[0][0x42]
        sel = [cfg_reg & 3, (cfg_reg >> 2) & 3, (cfg_reg >> 4) & 3]
        sgn = [(sign_reg >> 2) & 1, (sign_reg >> 1) & 1, sign_reg & 1]
        return tuple((-1 if sgn[k] else 1) * p[sel[k]] for k in range(3))

    def _fill_data(self, cfg):
        seed = cfg.get("seed", 1)
        if seed != self._seeded:
            self.rng = random.Random(seed)
            self._seeded = seed
        f, w = self._physical(cfg)
        kind = cfg.get("mount", "runtime")
        na, ng = cfg.get("noise_acc", 0.01), cfg.get("noise_gyro", 0.002)
        acc = self._remap(_mount(f, kind))
        gyr = self._remap(_mount(w, kind))
        acc = [a + self.rng.gauss(0, na) for a in acc]
        gyr = [g + self.rng.gauss(0, ng) for g in gyr]
        lsb_a = [max(-32768, min(32767, int(round(a * 100)))) for a in acc]
        lsb_g = [max(-32768, min(32767, int(round(math.degrees(g) * 16)))) for g in gyr]
        self.pages[0][0x08:0x0E] = struct.pack("<hhh", *lsb_a)
        self.pages[0][0x14:0x1A] = struct.pack("<hhh", *lsb_g)

    def write(self, reg, data):
        pg = self.page
        for k, b in enumerate(data):
            a = reg + k
            if a == 0x07:                     # page id register exists on both pages
                self.pages[0][0x07] = self.pages[1][0x07] = b & 1
                pg = self.page
                continue
            if a == 0x3F and b & 0x20:
                continue                      # reset trigger: keep state (test model)
            pg[a] = b

    def read(self, reg, n):
        cfg = _cfg()
        self.reads += 1
        every = cfg.get("oserror_every", 0)
        if every and self.reads % every == 0:
            raise OSError(121, "Remote I/O error")
        pg = self.page
        out = bytearray(n)
        if pg is self.pages[0] and reg in (0x08, 0x14) and n >= 6:
            self.data_reads += 1
            self._fill_data(cfg)
            out[:] = pg[reg:reg + n]
            ge, gp = cfg.get("glitch_every", 0), cfg.get("glitch_prob", 0.0)
            if (ge and self.data_reads % ge == 0) or (gp and self.rng.random() < gp):
                out[0] ^= 0x80
                self.glitches += 1
            return out
        out[:] = pg[reg:reg + n]
        return out


class I2C:
    def __init__(self, scl, sda, frequency=100000, timeout=255):
        self.dev = FakeBNO055()
        self._locked = False
        self.frequency = frequency

    def try_lock(self):
        if self._locked:
            return False
        self._locked = True
        return True

    def unlock(self):
        self._locked = False

    def scan(self):
        return [0x28]

    def _check(self, address):
        if address != 0x28:
            raise OSError(19, "No such device")

    def writeto(self, address, buffer, *, start=0, end=None):
        self._check(address)
        b = bytes(buffer[start:end])
        if b:
            self.dev.write(b[0], b[1:])

    def readfrom_into(self, address, buffer, *, start=0, end=None):
        self._check(address)
        end = len(buffer) if end is None else end
        buffer[start:end] = bytes(end - start)

    def writeto_then_readfrom(self, address, buffer_out, buffer_in, *, out_start=0, out_end=None,
                              in_start=0, in_end=None):
        self._check(address)
        out = bytes(buffer_out[out_start:out_end])
        in_end = len(buffer_in) if in_end is None else in_end
        data = self.dev.read(out[0], in_end - in_start)
        buffer_in[in_start:in_end] = data

    def deinit(self):
        pass


class SPI:
    """Type-annotation placeholder (adafruit_bus_device imports busio.SPI)."""


class UART:
    """Type-annotation placeholder."""
