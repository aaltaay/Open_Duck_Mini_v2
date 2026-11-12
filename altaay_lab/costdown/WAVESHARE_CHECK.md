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

At 7.4 V the two published stall torques are the same number, 19.5 kg.cm. The stall currents and the no-load speeds on the Waveshare 7.4 V column match the C001 sheet at that one voltage. Calc only: 19.5 kg.cm is 1.91 Nm at 0.0980665 N per kgf.cm. The C001 sheet also prints 16.5 kg.cm at 6 V. The Waveshare page does not print a 6 V stall. That point is BLOCKER for the Waveshare unit.

The trained-actuator knee RMS of 2.19 Nm (sim pass only, the added-mass table, quoted in REDTEAM.md) is above 1.91 Nm. That torque is the trained actuator, not the sheet-stall walk.

## The 3.5 s fall

The electromechanical twin, sim pass only, quoted by REDTEAM.md: with the sheet stall on the as-built bus, the backlash walk falls at 3.52 s (typical) and 3.46 s (high side), and the plain walk falls at 3.56 s. The same file's next sentence is the condition: the same sheet model held at a flat 7.4 V does not fall in 20 s and walks at 0.64 of the command. The fall is the sag on the first steps, not the stall alone.

Matching the 7.4 V stall does not by itself say the Waveshare unit falls or that it stays up. The published fall uses the sheet's stall line as voltage changes, on the as-built power path. The Waveshare unit was not put in that model, and it was not measured. Whether it avoids the fall is BLOCKER.

What can be said, calc only: if a later run gives the Waveshare the same voltage-dependent stall as the C001 sheet, and the same power path, then those published sheet-stall runs are the comparison. The page opened here does not give the 6 V stall that line needs, so that "if" is not met.

Backlash on the C001 sheet is at most 0.5 degree. The Waveshare backlash is BLOCKER until a page states it.
