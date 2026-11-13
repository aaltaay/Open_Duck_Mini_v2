# Wear coupons: wells, felt, cloth, and the knee loop

Written 2026-11-13. Gate 4 asks for a cycle count written down before the test starts. The counts below are that writing. They are the plan's choice, not a standard and not a result.

A coupon is allowed only after Ahmed says yes. A few wells, a scrap of foil, a scrap of felt, a scrap of cloth. No whole duck. The coupon is not the product.

## Counts, and why these counts

| Coupon | Count written now | Why this count | Stop early if |
|---|---|---|---|
| Gold well on foil | 10,000 sit-downs | 4 docks a day for about 7 years is 10,220 (calc only, 4 times 365 times 7). Rounded to 10,000. | Loop ohms rise more than 20 percent from the first reading, or the gold is cut through |
| Felt under a sole | 10,000 passes | Same home life, one pass per dock | Thickness loss over 20 percent, or mu moves by more than 0.2 from the CHAR-SOLE value |
| Cloth, only if a cloth path is still in a drawer | 10,000 drags | Same count. Nest v2 does not use this cloth. | A hole, a lifted thread, or an open circuit |
| Knee loop wires | 1,000,000 bends | Already written in TEST_PLAN 19.7. Not a new number. | Resistance up more than 10 percent, or a broken strand |

The catalog 500,000 cycles are in a socket, not on foil or cloth (the pin row of TWIN_CHECKLIST.md). Do not quote 500,000 as this life. TEST_PLAN 20.4's 500 cycles stay the first look. 500 is not this life test. Run 500 first. Start the 10,000 only if 500 has no hole and the ohms are still inside 20 percent.

## Wells

Parts. The well and the foil that will be bought. Felt under the foil if that is the stack. A lever or a hand press that lands the well at the force the sit actually uses. Until CHAR-SIT and a contact-force measurement exist, record the force you used and do not invent one. A kitchen scale under the coupon is enough to write the force down.

Cycle. One sit-down is a press to the recorded force, a one-second hold, and a lift. Rate slow enough that the coupon does not heat from the mechanism. Four-wire ohms at 1.0 A every 100 cycles for the first 1,000, then every 1,000. Photograph the gold at the start, at 500, and at the end.

Pass: 10,000 cycles, no cut through the gold, loop still under 0.15 ohm, and the last reading within 20 percent of the first. Then a charge at 1.00 A for 10 minutes on the worn pair: no local hot spot the hand can feel, and a thermocouple on the foil if one is on the bench, under 60 C. The hand check is not a temperature. The thermocouple number is the one that counts. Fail: any stop-early line above.

The thermal twin does not model a worn well. A hot-spot claim from the shell model is BLOCKER.

## Felt

Parts. The felt grade that will be bought. If no grade is named, the coupon waits. Do not wear an unnamed felt and call it the mat.

Load. Sole-shaped TPU coupon, 15 N to start (calc only, about half of a 2.7 kg duck). Write the real normal force. One pass is a 50 mm slide at that load, then back. mu at the start, at 500, at 1,000, and at 10,000, by the CHAR-SOLE pull.

Pass: 10,000 passes, thickness still within 20 percent of the start, mu within 0.2 of the CHAR-SOLE number. The nest sim is re-run with the worn mu and the worn thickness. Fail: a tear, or a mu the sit sim has not been shown.

## Cloth

Nest v2 does not build this coupon. Keep the procedure so a cloth sample is not worn with no rule.

Drag the contact the design would use (a well, not a crown or a spear) across the cloth at the recorded force. 500 drags first (TEST_PLAN 20.2 and 20.4). Life count 10,000 only if 500 does not snag or puncture. Pass: no hole, no lifted thread, and the loop ohms still inside the well rule. Fail: a snag. That fail retires the cloth. It does not retire the wells.

## Knee loop

TEST_PLAN 19.7 already owns this test. Cycle the D3 bundle from 0 to 150 deg on a printed shin and thigh at 2 to 3 Hz to 1,000,000 cycles, with 4-wire resistance. Pass: no rise over 10 percent, no broken strand when the jacket is opened. D61 puts charge contacts under the body, so this loop has no charge wires. Do not add pad wires from an older dock study.

This playbook does not add a second cycle count.

## What the twin does with the result

A wear number replaces a guess only after the CSV row is PASS and the named sim is re-run. Until then gate 4 stays open. `altaay_lab/test/check_bench.py` can score a filled `tp_20_contact.yaml` against the 0.15 ohm ceiling once status is measured. It cannot score a life claim. Life is the cycle count in this file, checked by a person, and written in a new history file.
