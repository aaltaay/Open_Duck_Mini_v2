"""Cited Pi 5 outline used by the seat and by the fit notes.

Drawing RP-008347-DS-1. The drawing says the figures are approximate and
are not production data. Hole y inset is calc only from 56 mm and 49 mm.
"""

BOARD_X_MM = 85.0
BOARD_Y_MM = 56.0
HOLE_D_MM = 2.7
HOLE_PITCH_X_MM = 58.0
HOLE_INSET_X_MM = 3.5
HOLE_PITCH_Y_MM = 49.0
HOLE_INSET_Y_MM = (BOARD_Y_MM - HOLE_PITCH_Y_MM) / 2.0

# Active Cooler drawing. Height is the side view.
COOLER_H_MM = 12.70

# Cited product page: 5 V / 5 A via USB-C.
SUPPLY_V = 5.0
SUPPLY_A = 5.0

# Cited, Raspberry Pi whitepaper RP-010139-WP table 1, the high end of the
# minimum band already used in BOARDS.md. Not a measured idle watt.
MIN_W_HIGH = 5.0


def hole_centers():
    xs = (HOLE_INSET_X_MM, HOLE_INSET_X_MM + HOLE_PITCH_X_MM)
    ys = (HOLE_INSET_Y_MM, HOLE_INSET_Y_MM + HOLE_PITCH_Y_MM)
    return [(x, y) for x in xs for y in ys]
