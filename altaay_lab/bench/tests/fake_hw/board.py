"""Fake Blinka `board` for tests: BCM pin objects only (no hardware)."""


class Pin:
    def __init__(self, n):
        self.id = n

    def __repr__(self):
        return f"board.D{self.id}"

    def __eq__(self, other):
        return isinstance(other, Pin) and other.id == self.id

    def __hash__(self):
        return hash(self.id)


for _n in range(28):
    globals()[f"D{_n}"] = Pin(_n)
SDA = globals()["D2"]
SCL = globals()["D3"]
