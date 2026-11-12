# Assembly sequence

The sequence is `twin/assembly/BUILD_ORDER.md`, with the corrections on this page. Do not drive a screw whose `fasteners.json` status says LEAVE OUT or NOT FITTED. The 56 factory case screws stay as they arrived. Heat-set inserts go in before the screw that uses them, the same order that file already assumes.

Tool names are the ones that file already uses. hex2.0 and hex2.5 are BOM T4. PH0 is the cross-head driver already named for the M2 screws. Nothing new is added to the tool list except the jack wrench, and that size is not known (see the nest steps).

## Corrections to the existing steps

These replace the quoted lines. The rest of the file stands.

1. Step 73. The line says four M2x6, including F127. F127 is M2x12 in `fasteners.json` (cad). D59 already puts the neck stop block on that screw.

   Replace with: `4 x M2 self-tapping pan head: trunk_top into the hip-yaw bottom case, PH0 (F057, F058, F125 are M2x6; F127 is M2x12 through the neck stop block, D59). Put the block on before tightening F127.`

2. Step 75. Same for F129.

   Replace with: `4 x M2 self-tapping pan head: trunk_top into the hip-yaw bottom case, PH0 (F059, F060, F131 are M2x6; F129 is M2x12 through the neck stop block, D59). Put the block on before tightening F129.`

3. Before steps 77 and 78, while `body_front` is still in the hand. These two screws are fitted and are not in the order (cad).

   Add: `2 x M2.5x6 DIN 912 A2: cliff board into body_front, hex2.0, from the back of the board (F360, F361, D54). The other two board holes rest on the solid standoffs.`

4. Step 80. The line drives four adapter screws. F120 and F121 are left out.

   Replace with: `2 x M2.5x6 DIN 912 A2: board into trunk_top, hex2.0 (F119, F122).`

5. Step 99. The line drives four Pi screws. F112 and F113 are left out.

   Replace with: `2 x M2.5x6 DIN 912 A2: Pi into head, hex2.0 (F111, F114).`

6. After step 99, before the head bottom sheet (steps 110 and 111). The mic screws are fitted and are not in the order (cad). The bosses are in the head, so they are driven while the head is still open.

   Add: `4 x M2x6 self-tapping pan head: mic boards into the head bosses, PH0 (F356, F357 left; F358, F359 right).`

7. Step 100. The line drives four right-eye screws. F177 and F180 are left out. The washers stay on the screws that are fitted.

   Replace with: `2 x M2.5x8 DIN 912 A2 + 2 x 0.3 mm washers: bulb into right_eye, hex2.0 (F176, F181).`

8. Step 102. The line says four M2x4. The fitted screws are M2x5, and F345 and F346 are left out (cad, D34 and D38).

   Replace with: `2 x M2x5 self-tapping pan head: camera board into head, PH0 (F344, F347).`

9. Step 105. The line drives four speaker-interface screws. F352 and F355 are left out.

   Replace with: `2 x M2.5x5 DIN 912 A2: speaker_interface into speaker_stand, hex2.0 (F353, F354).`

10. Step 106. The line drives four speaker-stand screws. F107 and F110 are left out.

    Replace with: `2 x M2.5x6 DIN 912 A2: speaker_stand into head, hex2.0 (F108, F109).`

Steps 77, 78, 83, and 101 already say which screws are out. Leave those sentences.

The cast in `asm_geom_summary.json` (cited, not re-run) had 0 tool-path violations on the 286 screws it knew. F356 to F361 were not in that cast.

## Nest, after the duck

The nest is not in `BUILD_ORDER.md` and not in `print/`. These steps follow the order already implied by `NEST_CAD.md`: terminals inside the box, then the lid, then the sleeve. No new screw size.

1. Heat-set 6 x M3 inserts (BOM 16) in the four lid posts and the two terminal posts. Bore 4.0 mm, depth 5.8 mm (calc, from `nestcad_lib.py`).
2. Fit the PJ-005A jack in the 8.0 mm hole with the nut and washer that come with the jack (dock line K6b). Do this before the left bolster covers the nut. The wrench size is not in the repo.
3. NT1 and NT2: M3x8 DIN 912, hex 2.5, ring lug under the head, into the terminal posts. Do this before the lid. The lug has no catalog line. Do not buy a lug this page invents.
4. NL1 to NL4: M3x6 button head, hex 2.0, into the lid posts. Do this before the felt sleeve. The sleeve covers the heads (`NEST_CAD.md`).
5. Bolsters and the felt sleeve after the screws.

Duck side: the pin carriers have no screw. They sit in the pockets with the VHB the nest CAD already uses. Do not also cut the five flush wells into those blocks. That study is a different layout.

## Do not assemble yet

- Do not copy a topology STL or a shin-eye STL into the build. Without the recess already in `eye_geom.py`, the existing horn screws do not seat (`CHECKS.md`).
- Do not add a charger-board screw. There is no seat and no hole pattern.
- Do not add a wall-card screw. The closeup study does not name one.
