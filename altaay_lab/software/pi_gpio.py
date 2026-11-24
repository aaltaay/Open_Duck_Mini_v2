"""GPIO for the day-one eyes on a Pi 5.

The 40-pin header is the standard header (product page). The Pi 5 I/O
controller is RP1, and RPi.GPIO does not drive it. This module uses lgpio
or gpiod. The ear PWM overlay is separate and is not touched here.

A caller can pass a chip with write(gpio, level) for tests. Live mode opens
the gpiochip named by ODM_GPIO_CHIP, default 4, which is the RP1 header on
current Pi 5 images. The chip number is still a check on the first board:
if open fails, the step stays incomplete.
"""

from __future__ import annotations

import os

# Cited, netlist EYE_L GPIO24 and EYE_R GPIO23.
LEFT = 24
RIGHT = 23


def planned_levels():
    """On, then off, left then right. The day-one eyes gate reads this log."""
    return [(LEFT, 1), (RIGHT, 1), (LEFT, 0), (RIGHT, 0)]


class MemoryChip:
    """Records writes. Used by unit tests and by --mock."""

    def __init__(self):
        self.log = []

    def write(self, gpio, level):
        self.log.append((int(gpio), int(level)))


def eye_cycle(chip=None):
    if chip is None:
        chip = open_board_chip()
    for gpio, level in planned_levels():
        chip.write(gpio, level)
    return list(getattr(chip, "log", planned_levels()))


def open_board_chip():
    """Open RP1 GPIO. Raises if neither library nor the chip is present."""
    number = int(os.environ.get("ODM_GPIO_CHIP", "4"))
    try:
        import lgpio
    except ImportError:
        lgpio = None
    if lgpio is not None:
        return _LgpioChip(lgpio, number)
    try:
        import gpiod
    except ImportError as exc:
        raise FileNotFoundError("lgpio and gpiod are not installed") from exc
    return _GpiodChip(gpiod, number)


class _LgpioChip:
    def __init__(self, lgpio, number):
        self._lg = lgpio
        self._h = lgpio.gpiochip_open(number)
        self.log = []

    def write(self, gpio, level):
        self._lg.gpio_claim_output(self._h, int(gpio), int(level))
        self.log.append((int(gpio), int(level)))


class _GpiodChip:
    def __init__(self, gpiod, number):
        self._g = gpiod
        path = "/dev/gpiochip%d" % number
        self._chip = gpiod.Chip(path)
        self._lines = {}
        self.log = []

    def write(self, gpio, level):
        gpio = int(gpio)
        line = self._lines.get(gpio)
        if line is None:
            line = self._chip.get_line(gpio)
            line.request(consumer="odm-day-one", type=self._g.LINE_REQ_DIR_OUT)
            self._lines[gpio] = line
        line.set_value(int(level))
        self.log.append((gpio, int(level)))
