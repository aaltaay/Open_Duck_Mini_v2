"""Fake Blinka `pwmio` for tests (antennas.py imports it at module load)."""


class PWMOut:
    def __init__(self, pin, frequency=500, duty_cycle=0, variable_frequency=False):
        self.pin, self.frequency, self.duty_cycle = pin, frequency, duty_cycle

    def deinit(self):
        pass
