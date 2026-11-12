# 2026-11-11 8:28 PM ET: review fixes, coupon exception and the cell bay

The automatic review on the bench and audit pull request found two problems. Both are fixed in the docs.
Nothing was bought. The bill was not changed. No decision record was edited.

- Gate 0 still forbids printing the duck, welding the pack, and placing the full order. A characterization
  coupon is allowed after Ahmed says yes. For the pins that is TEST_PLAN.md 20.1 to 20.4: a few pins, a
  scrap of cloth, a scrap of felt, no whole duck. The coupon is how the pin-contact row stops being a
  guess. It is not the product and it is not the one-click bill. DEFINITION_OF_DONE.md and
  TWIN_CHECKLIST.md say so.
- The opened P45B sheet maximum is 21.55 mm by 70.15 mm. That is the top of the 21.40 plus or minus 0.15 mm
  by 70.00 plus or minus 0.15 mm band the bay already used. The sleeved pack is 22.2 by 43.7 by 71.0 mm
  (CAD check only, twin/battery/bay_edit.py). The cell maximum fits. The bay is not resized. The viewer
  cylinders at 21.4 by 70 mm are the nominal picture, not the cavity. The battery row stays FAIL because
  the weld has no part number and the electromechanical twin still runs a P30B pack.
