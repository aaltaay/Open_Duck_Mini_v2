"""Fake Blinka `digitalio` for tests.

Inputs on GPIO22 (left foot) and GPIO27 (right foot) follow a scripted contact state, with the
real electrical logic of our build: switch closed = pin pulled LOW (D17 pull-up to 3V3), so
feet_contacts.py returns `not value` = True for contact.

Feet source (first match wins):
  ODM_FAKE_FEET_SCRIPT  CSV "t,left,right" (seconds from the first pin read, 1 = contact);
                        the last row holds until the end
  ODM_FAKE_FEET_FILE    file with "L R" (1 = contact), read again on every access
  ODM_FAKE_FEET         constant "LR", for example "11" both feet on the ground (default "00")
Outputs (eyes, projector) only store their value.
"""
import bisect
import os
import time

LEFT_PIN, RIGHT_PIN = 22, 27


class Direction:
    INPUT, OUTPUT = "input", "output"


class Pull:
    UP, DOWN = "up", "down"


class DriveMode:
    PUSH_PULL, OPEN_DRAIN = "push_pull", "open_drain"


_T0 = None
_SCRIPT = None
READS = {"n": 0}


def _load_script(path):
    t, rows = [], []
    with open(path) as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln or ln.startswith("#") or ln.startswith("t"):
                continue
            a, l, r = ln.split(",")[:3]
            t.append(float(a)); rows.append((int(l), int(r)))
    return t, rows


def contact_state():
    global _T0, _SCRIPT
    now = time.monotonic()
    if _T0 is None:
        _T0 = now
    path = os.environ.get("ODM_FAKE_FEET_SCRIPT")
    if path:
        if _SCRIPT is None:
            _SCRIPT = _load_script(path)
        t, rows = _SCRIPT
        k = max(0, bisect.bisect_right(t, now - _T0) - 1)
        return rows[k]
    path = os.environ.get("ODM_FAKE_FEET_FILE")
    if path and os.path.exists(path):
        try:
            l, r = open(path).read().split()[:2]
            return int(l), int(r)
        except (OSError, ValueError):
            pass
    s = os.environ.get("ODM_FAKE_FEET", "00")
    return int(s[0]), int(s[1])


class DigitalInOut:
    def __init__(self, pin):
        self.pin = pin
        self.direction = Direction.INPUT
        self.pull = None
        self._out = False

    @property
    def value(self):
        if self.direction == Direction.OUTPUT:
            return self._out
        READS["n"] += 1
        l, r = contact_state()
        if self.pin.id == LEFT_PIN:
            return not bool(l)
        if self.pin.id == RIGHT_PIN:
            return not bool(r)
        return self.pull == Pull.UP

    @value.setter
    def value(self, v):
        self._out = bool(v)

    def switch_to_input(self, pull=None):
        self.direction, self.pull = Direction.INPUT, pull

    def switch_to_output(self, value=False, drive_mode=None):
        self.direction, self._out = Direction.OUTPUT, bool(value)

    def deinit(self):
        pass
