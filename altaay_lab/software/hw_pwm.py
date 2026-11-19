"""Hardware PWM for the ear servos. The Runtime file is not edited (D6).

antennas.py at Runtime 376de65 drives GPIO12 and GPIO13 with Blinka software
PWM. The boot overlay pwm-2chan already gives those pins to the PWM block
(PI_SETUP.md 4c, netlist ANT_R and ANT_L). This module writes that block.

The pulse map is the one in antennas.py value_to_duty_cycle: 1.5 ms plus
0.5 ms times the command, then clamped. The netlist PWM_3V3 note calls that
50 Hz and 1 to 2 ms. The clamp constants 3277 and 6553 are from that file.

Question for Ahmed: STATE.md item 10. D6 keeps antennas.py unmodified.
software/ANTENNAS_PWM.md states the question. install_pi.sh can point the
walk at this overlay. It does not change the Runtime.
"""

import os
from pathlib import Path

# Cited, antennas.py at 376de65: frequency 50 and MIN_UPDATE_INTERVAL 1/50.
# Cited, netlist domain PWM_3V3: 50 Hz, 1 to 2 ms.
PERIOD_NS = 20_000_000
FREQUENCY_HZ = 50

# Cited, antennas.py value_to_duty_cycle clamp. 16-bit full scale is 65535.
DUTY_FULL = 65535
DUTY_MIN = 3277
DUTY_MAX = 6553

# Cited, netlist: GPIO12 right antenna PWM0, GPIO13 left antenna PWM1.
RIGHT_GPIO = 12
LEFT_GPIO = 13
CHANNEL = {RIGHT_GPIO: 0, LEFT_GPIO: 1}

# Cited, antennas.py: left sign +1, right sign -1. Command is -1 to 1
# (software/personality/limits.py, COMPANION.md).
LEFT_SIGN = 1
RIGHT_SIGN = -1


def value_to_duty_cycle(v):
    """Same arithmetic as antennas.py value_to_duty_cycle. v is unitless, -1 to 1."""
    pulse_width_ms = 1.5 + (v * 0.5)
    duty_cycle = int((pulse_width_ms / 20) * DUTY_FULL)
    return min(max(duty_cycle, DUTY_MIN), DUTY_MAX)


def command_to_duty(value, sign):
    """antennas.py set_position: reject outside -1 to 1, then apply the sign."""
    if value < -1 or value > 1:
        raise ValueError("antenna command must be from -1 to 1")
    return value_to_duty_cycle(value * sign)


def duty_to_ns(duty):
    """Nanoseconds on a 20 ms period. Calc only from the cited 16-bit duty."""
    duty = int(duty)
    if duty < DUTY_MIN or duty > DUTY_MAX:
        raise ValueError("duty %s is outside the antennas.py 1 ms to 2 ms clamp" % duty)
    return (duty * PERIOD_NS) // DUTY_FULL


def _under_sys(path):
    """True when path is the kernel PWM tree, not a mock directory."""
    try:
        return Path(path).resolve().is_relative_to("/sys")
    except (OSError, ValueError):
        return str(path).startswith("/sys/")


class Chip:
    """sysfs pwmchip. A normal directory with an export file is the fake chip."""

    def __init__(self, root=None):
        if root is None:
            root = os.environ.get("ODM_PWM_CHIP", "/sys/class/pwm/pwmchip0")
        self.root = Path(root)

    def export(self, index):
        channel = self.root / ("pwm%d" % index)
        if channel.exists():
            return channel
        export = self.root / "export"
        # A path under /sys is the real PWM device. Never create that tree.
        # A missing chip is a failure, not a folder of ordinary files.
        if _under_sys(self.root):
            if not export.exists():
                raise FileNotFoundError("PWM chip is not present at %s" % self.root)
            export.write_text("%d\n" % index)
            if not channel.exists():
                raise OSError("export did not create %s" % channel)
            return channel
        # File-backed stand-in. Used by --mock and by unit tests only.
        export.parent.mkdir(parents=True, exist_ok=True)
        if not export.exists():
            export.write_text("")
        export.write_text("%d\n" % index)
        if not channel.exists():
            channel.mkdir()
            for name in ("period", "duty_cycle", "enable"):
                (channel / name).write_text("0\n")
        return channel

    def write(self, index, name, value):
        path = self.export(index) / name
        path.write_text("%s\n" % value)

    def read(self, index, name):
        return (self.export(index) / name).read_text().strip()


class PWMOut:
    """Drop-in for Blinka pwmio.PWMOut on the two ear pins only.

    duty_cycle uses the antennas.py 16-bit scale. deinit stops the pulses
    (PI_SETUP.md 4c: the SG90 should idle with the line quiet).
    """

    def __init__(self, pin, frequency=500, duty_cycle=0, variable_frequency=False, chip_root=None):
        gpio = pin.id if hasattr(pin, "id") else int(pin)
        if gpio not in CHANNEL:
            raise ValueError("hardware PWM overlay covers GPIO12 and GPIO13 only, got %s" % gpio)
        if frequency != FREQUENCY_HZ:
            raise ValueError("ear PWM is 50 Hz (cited), got %s" % frequency)
        self.pin = pin
        self.gpio = gpio
        self.frequency = frequency
        self._index = CHANNEL[gpio]
        self._chip = Chip(chip_root)
        self._duty = None
        self.duty_cycle = duty_cycle

    @property
    def duty_cycle(self):
        return self._duty

    @duty_cycle.setter
    def duty_cycle(self, duty):
        duty = int(duty)
        ns = duty_to_ns(duty)
        # Enable is dropped first so a shorter period cannot reject the old duty.
        self._chip.write(self._index, "enable", 0)
        self._chip.write(self._index, "duty_cycle", 0)
        self._chip.write(self._index, "period", PERIOD_NS)
        self._chip.write(self._index, "duty_cycle", ns)
        self._chip.write(self._index, "enable", 1)
        self._duty = duty

    def deinit(self):
        self._chip.write(self._index, "enable", 0)


def patch(pwmio_module, chip_root=None):
    """Replace pwmio.PWMOut. Other pins are refused. The Runtime file stays as it is."""

    class _EarPWM(PWMOut):
        def __init__(self, pin, frequency=500, duty_cycle=0, variable_frequency=False):
            super().__init__(pin, frequency=frequency, duty_cycle=duty_cycle,
                             variable_frequency=variable_frequency, chip_root=chip_root)

    pwmio_module.PWMOut = _EarPWM
    return pwmio_module


def install_import_hook(chip_root=None):
    """Wrap a later `import pwmio` so the ear pins use this overlay."""
    import importlib.util
    import sys

    class _Hook:
        def find_spec(self, fullname, path, target=None):
            if fullname != "pwmio" or getattr(self, "_busy", False):
                return None
            self._busy = True
            try:
                sys.meta_path.remove(self)
                spec = importlib.util.find_spec("pwmio")
            finally:
                sys.meta_path.insert(0, self)
                self._busy = False
            if spec is None or spec.loader is None:
                return None
            orig = spec.loader.exec_module

            def exec_module(module):
                orig(module)
                patch(module, chip_root=chip_root)

            spec.loader.exec_module = exec_module
            return spec

    sys.meta_path.insert(0, _Hook())
