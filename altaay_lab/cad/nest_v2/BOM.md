# Nest v2 cost notes

Prices live in this file only. Nothing was bought. A page that was not opened is BLOCKER, not a guess.

## Opened

Mill-Max 0906-0-15-20-76-14-11-0, spring pin. DigiKey product page, opened 2026-11-12:

https://www.digikey.com/en/products/detail/mill-max-manufacturing-corp/0906-0-15-20-76-14-11-0/1147049

The page's bulk table, USD:

| Quantity | Unit price |
|---|---|
| 1 | 0.86 |
| 10 | 0.733 |
| 25 | 0.6868 |
| 50 | 0.654 |
| 100 | 0.6227 |
| 250 | 0.58364 |
| 500 | 0.55574 |

This pin is not in the picked mat. It is the part a spring field (option e) would use. A point-tip grid fine enough for a 3 mm well, over a 560 mm by 360 mm field, is about 45,000 pins (calc only, NEST_V2.md). At the quantity-1 price that is about 38,700 USD (calc only, 45000 times 0.86). At the 500-piece price it is about 25,000 USD (calc only, 45000 times 0.55574). The page's 1,000-piece break was not copied here. Either way it is not a rug.

The picked mat uses no Mill-Max pins.

## Duck-side wells, tried after the flush face read 0 N

The mat in this file is unchanged. D61 was not edited. The approved line is still a flush well and nothing standing out of the duck (DECISION.md).

A placed sit with the seat face and the bumper in the model leaves the flush wells 0.36 mm above the mat, because the bumper and the seat edges take the load (twin/dock/camera/SEAT_WELLS.md). Three duck-side options were simulated. The one put into the dock model is a 1.5 mm gold dome standing 0.9 mm proud of the seat face. That is the smallest height in the 0.3 to 1.5 mm sweep whose low print tolerance, 0.6 mm, still presses every well. It does not match the flush line. It adds no bought part: the gold is the well already drawn, formed proud. A solid cap 0.9 mm tall on a 1.5 mm radius is about 0.06 g, and five of them are about 0.29 g (calc only, spherical cap, 19.3 g/cm3). The foil price is still BLOCKER.

The Mill-Max 0906 above, spring 76, is the spring option that was not picked. The sheet gives 25 g at first touch and 60 g at mid stroke, 0.495 mm, with a 0.991 mm stroke (Mill-Max data sheet, the Farnell copy of 0906-0-15-20-76-14-11-0, and the element14 listing). Five pins at the quantity-1 price are 4.30 USD (calc only, 5 times 0.86). Springs on the duck are the thing DECISION.md dropped. The low print tolerance, a pin only 0.69 mm proud, put 0.18 N on each well, under the 0.294 N floor. The full comparison is twin/dock/camera/SEAT_CONTACTS.md.

## Not opened, so no dollar figure

- Felt sheet. BLOCKER.
- Copper foil tape for the stripes. BLOCKER.
- The five gold well discs. BLOCKER. They can be punched from the same foil if a later pass says so. That is not a price.
- EDAC magnetic housings. BLOCKER.
- Qi2 coil and receiver module. BLOCKER. The ST brief and the WPC page that were opened do not print a price.
- The 40 mm wall card. It is a felt or printed square. No electronics. Not on the order list, so no price.

## Camera mark, added for the head camera

The dock sim uses an 80 mm black square at the same station as the 40 mm card (centre 350 mm up, on the centre line). 40 mm is about 11 px wide at 1.5 m on a 320-wide frame of the standard module (calc only, camera brief 41 deg across the short axis). The black sheet is Grainear 9 by 12 inch black craft felt, 6 sheets, listed at 6.99 USD (Amazon B0FXKGNV95, the page price shown 2026-11-15, cited). One sheet is 1.17 USD (calc only, 6.99 divided by 6). The gold patch is cut from the stripe foil. Foil dollars stay BLOCKER. The mat felt grade stays BLOCKER. Nothing was bought. The STL in this folder was not rebuilt. It still shows the 40 mm card.

A second mark stands on the room side of the sun, at x = -2.20 m, centre 280 mm up, on the centre line, facing the duck. It is a 120 mm black square from the same Grainear sheet. One 9 by 12 inch sheet is 229 by 305 mm, and 80 mm plus 120 mm is 200 mm, so both squares fit on one sheet (calc only). The patch on this one is red so the camera can tell it from the wall card after the duck turns. The red sheet is a 9 by 12 inch craft felt, listed at 0.65 USD each (OnlineFabricStore, 9 inch by 12 inch red felt sheet, the page price shown 2026-11-15, cited). The patch is about 32 mm, so one sheet covers it (calc only). Nothing was bought. The stripe pitch is unchanged: 20 mm foil and a 5 mm felt gap. A narrower gap can be bridged by a coin (NEST_V2.md, blocker 2). The extra stripe margin in the camera dock comes from closing the heading, not from a wider foil.

## What the picked mat adds, without a price

| Part | Count | Note |
|---|---|---|
| Felt, 1 mm sheet | 2 | base and top, cut |
| Foil stripe, 20 mm | 23 | 11 plus, 12 minus, on 2 buses |
| Gold well, 3 mm | 5 | in the seat, flush |
| Cord pocket, printed | 1 | no screws |
| Felt cap | 1 | sits in the pocket opening, 0.4 mm clear a side |
| Wall card, 40 mm | 1 | optional, Ahmed has not approved it |
| Charger board | 0 new | already drawn, in the duck |

The gate board that turns the field on is not designed. Its pocket is sized. It is not a line on this list.
