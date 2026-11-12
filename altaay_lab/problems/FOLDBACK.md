# Fold-back charge and the 6 hour timer

Calc only. Nothing bought, nothing redesigned. The board stays the one in circuitry/CHARGER_BOARD.md. The cell model stays twin/electromech/p45b.py, the digitized discharge figure of the P45B sheet, version 1.2.

Run: `python3 altaay_lab/problems/foldback.py`

The script checks itself against the charger note: at 32 C on the sheet's 62 C/W board, a pack held at 6.0 V allows 0.359 A, and 4.5 Ah at that current plus the note's 0.50 h tail is 13.02 h. That is the "about 13 h" line. It matches.

## What that 13 h line is

It holds the pack at 6.0 V for the whole 4.5 Ah, at the current the die would allow at that one voltage. A charge cannot do that. As soon as charge goes in, the voltage rises, and the allowed current rises with it. Below the precondition line the chip is not in that fast-charge current at all.

Precondition, from the same note (Table 2 of DS20002190C): current 10 percent, timer 32 minutes, threshold 71.5 percent of 8.40 V. That threshold is 6.006 V (calc, already in the charger note). The chip decides this from the terminal at the small current. The fast-charge current is not flowing yet, so it does not lift the pin over the line.

## The integral

Voltage is the discharge figure's zero-current end, plus the current times the sheet's 15 mOhm DC pulse. This is not a charge curve. The sheet's standard charge is 4.5 A. A real charge sits above this voltage, so the current the die allows is higher and the time is shorter than the hours below. These hours are a long estimate.

The figure's zero-current end at 0 mAh is 4.175 V per cell, so the pack in this model ends at 8.38 V, short of the 8.40 V regulation. There is no taper after that in the figure. The 0.50 h in the charger note is the standard-charge difference at 4.5 A, not a measurement of this taper.

Room 32 C, program current 1.00 A, 62 C/W, the sheet's board. Calc only.

| Start | Where it comes from | Charge put back | Hours | Against the timer |
|---|---|---|---|---|
| 3.30 V per cell | electromechanical row, open circuit at the end of the trained walk (sim pass only there) | 3861 mAh on the figure | 5.88 h | past 5.4 h, inside 6.6 h |
| 3.60 V per cell | nominal | 2859 mAh on the figure | 3.85 h | inside 5.4 h and inside 6.6 h |
| 3.00 V per cell | the charger note's 6.0 V pack | 4358 mAh on the figure | 7.13 h on a 5 mAh step, 7.15 h on a 2 mAh step | past 6.6 h on this long estimate |
| figure low end, 2.80 V per cell | the bottom of the digitized grid | 4450 mAh | 8.07 h, of which 0.94 h is precondition | the 32 minute precondition timer trips |

Adding the note's 0.50 h on top of the 5.88 h, as a long decoration and not as a 1 A measurement, gives 6.38 h. That is still inside 6.6 h.

At 25 C, same board, 1.00 A, the walk-stop case is 5.43 h. That is 0.03 h past 5.4 h. The 0.90 A corner is 5.54 h and the 1.10 A corner is 5.39 h. The 25 C case sits on the minimum timer. It is not a clear miss once the model is admitted to be long.

## What this closes, and what it does not

The 13 h figure is not the charge time. On the cited 62 C/W board, a duck that stopped at 3.30 V per cell has a long estimate of 5.88 h, which fits inside the 6.6 h maximum, and a real charge is not longer than that estimate on the fold-back stretch. The 5.4 h minimum is not cleared: the long estimate is past it at 32 C, and a shorter real charge might still land inside it. That minimum stays not shown.

A start at the bottom of the figure trips the 32 minute precondition timer (0.94 h at 0.10 A before the pack reaches 6.006 V). The walk stop at 6.60 V does not enter precondition.

In-trunk thermal resistance is still BLOCKER. The 62 C/W number is the sheet's board, not the closed trunk. On this same long estimate, 5.4 h is crossed at 56.5 C/W and 6.6 h is crossed at 69.6 C/W (calc only, 32 C room, 1.00 A, walk-stop start). A trunk warmer than 69.6 C/W makes even the long estimate miss the maximum timer. No heatsink and no new current were drawn. The board is unchanged.
