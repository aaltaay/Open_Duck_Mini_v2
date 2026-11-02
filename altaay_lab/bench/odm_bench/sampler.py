"""Staggered guard reads: Present Voltage (62) and Present Temperature (63) in one SYNC READ.

Registers 62 and 63 are adjacent, so the temperature costs 1 byte per servo on the read the
battery guard already makes. The 14 servos are split into `groups` interleaved groups (default 2
of 7, each group spans all three chains); each call reads the next group only, so one guard tick
costs a 15 byte request and 7 x 8 byte replies = 71 bytes = 0.71 ms of wire time at 1 Mbaud
(10 bits per byte), instead of 134 bytes for all 14 (SOFTWARE.md section 6).
With the default tick of 0.25 s every servo is refreshed every 0.5 s.
"""
import time

from . import bus, joints


class GuardSampler:
    def __init__(self, io, ids=None, groups=2, errors=None, max_age_s=2.0):
        self.io, self.errors = io, errors
        self.ids = list(ids or joints.IDS)
        groups = max(1, min(groups, len(self.ids)))
        self.groups = [self.ids[k::groups] for k in range(groups)]
        self.k = 0
        self.max_age_s = max_age_s
        self.v, self.temp, self.stamp = {}, {}, {}
        self.reads = self.failures = 0
        self.last_duration_s = None

    def _read(self, ids):
        got, failed = bus.sync_read_block(self.io, ids, 62, 2, self.errors)
        now = time.monotonic()
        for i, d in got.items():
            self.v[i], self.temp[i], self.stamp[i] = d[0] * 0.1, d[1], now
        return got, failed

    def read_all(self):
        """All servos at once (start checks, before torque-on). Returns (volts, temps)."""
        got, _ = self._read(self.ids)
        return {i: self.v[i] for i in got}, {i: self.temp[i] for i in got}

    def read(self):
        """One staggered tick. Returns (volts of every fresh servo or None, temps read this tick)."""
        ids = self.groups[self.k]
        self.k = (self.k + 1) % len(self.groups)
        self.reads += 1
        t0 = time.perf_counter()
        try:
            got, _ = self._read(ids)
        except Exception as e:  # noqa: BLE001 - any bus error is a failed tick
            got = {}
            if self.errors is not None:
                self.errors.add("pypot", "guard_read_exception", None, repr(e))
        self.last_duration_s = time.perf_counter() - t0
        if not got:
            self.failures += 1
        now = time.monotonic()
        fresh = {i: v for i, v in self.v.items() if now - self.stamp[i] <= self.max_age_s}
        return (fresh or None), {i: self.temp[i] for i in got}
