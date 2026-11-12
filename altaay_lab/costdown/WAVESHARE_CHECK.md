# Waveshare 7.4 V against the STS3215

Calc only, from datasheets and the product page. No new walk was run. The 3.5 s fall is the one in REDTEAM.md, which cites twin/electromech/ELECTROMECH_TWIN.md. This note does not rerun it.

## What the sheets say

STS3215 C001, Feetech sheet opened this pass (the Seeed copy of 108090023):

- Backlash, item 6-11: at most 0.5 degree. Cited.
- Stall torque, item 5-4: 16.5 kg.cm at 6 V and 19.5 kg.cm at 7.4 V, each plus or minus 10 percent. Cited.
- Stall current, item 5-5: 2 A at 6 V and 2.5 A at 7.4 V. Cited.
- No-load speed, item 5-2: 0.238 s/60 deg at 6 V and 0.192 s/60 deg at 7.4 V. Cited.
- Rated input, item 5-7: 4 V to 7.4 V. Cited.

Waveshare ST3215 7.4 V, product page opened this pass (SKU 33014):

- Stall torque on that column: 19.5 kg.cm at 7.4 V. Cited.
- Locked-rotor current on that column: 2.5 A. Cited, from the same page's selection table read with the price.
- No-load speed on that column: 0.192 s/60 deg at 7.4 V. Cited.
- Operating voltage on that column: 4 V to 7.4 V. Cited.
- Backlash: not on the product page, not on the wiki page, and not in the user-manual extract. BLOCKER.

The user manual PDF was opened (26 pages). The extract did not contain a backlash line, a stall-torque line, or a speed line. The wiki page that links that PDF states 30 kg.cm and 0.222 s/60 deg at 12 V, which is the other column, not the 7.4 V unit.

## Torque

At 7.4 V the two published stall torques are the same number, 19.5 kg.cm. The stall currents and the no-load speeds on the Waveshare 7.4 V column match the C001 sheet. Calc only: 19.5 kg.cm is 1.91 Nm at 0.0980665 N per kgf.cm. REDTEAM.md says the sim knee RMS is 2.19 Nm, above that stall (sim pass only, quoted there from the added-mass table). A servo with this stall still cannot make that torque.

## The 3.5 s fall

REDTEAM.md, from the electromechanical twin, sim pass only: with the sheet stall of 19.5 kg.cm at 7.4 V, the backlash walk falls at 3.52 s (typical) and 3.46 s (high side), and the plain walk at 3.56 s. The same sheet model held at a flat 7.4 V does not fall in 20 s. The fall those runs record is the stall, not a missing backlash number.

The Waveshare 7.4 V column publishes that same stall. Calc only: it does not avoid that fall. A new closed-loop run was not started, and a matching backlash number was not found, so this is not a claim that the two servos are the same part. It is the stall comparison the fall depends on.

Backlash on the C001 sheet is at most 0.5 degree. The Waveshare backlash is BLOCKER until a page states it. That gap does not move the stall result above.
