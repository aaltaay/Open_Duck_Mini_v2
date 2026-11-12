# Assembly sequence

Follow `twin/assembly/BUILD_ORDER.md`. The 2026-11-12 lines in that file are the fastener-file lengths (F127 and F129 are M2x12, F344 and F347 are M2x5), the fitted screws only, and the mic screws F356 to F359 and the cliff screws F360 and F361. Do not drive a screw whose status says LEAVE OUT or NOT FITTED. The 56 factory case screws stay as they arrived.

The 2026-11-04 tool cast (0 violations on 286 screws) was not re-run. F356 to F361 were not in it. Their tools are the PH0 and hex 2.0 that file already uses.

## Nest, after the duck

The nest is not in `BUILD_ORDER.md` and not in `print/`. These steps follow the order already implied by `NEST_CAD.md`: terminals inside the box, then the lid, then the sleeve. No new screw size. The lid proposal in `PROPOSED_EDITS.md` is not applied, so these steps still use the drawn M3x6 and the 5.8 mm bore.

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
