# Proposed nest-lid edit

Not applied. `twin/dock/nest/cad/nest_parts.py` is not edited. The check is `lid_check.py` on the profile that file already builds. CAD check only. Nothing is bought.

`BUILD_ORDER.md` was corrected in this branch. The lines that used to live here are in that file now.

## Pattern

Do not use `BX0 + 6`. At that x the lid thickness is 0.0 mm, because the room-side chamfer (8 mm in `box_profile`) meets the lid split at z 23.5 (cad).

Keep the room-side x at `BX0 + 14` (158.0 mm). Lid thickness there is 2.0 mm, and an ISO 7380 M3 head (dk 5.70) has 3.15 mm of flat top inboard of the chamfer (cad).

Set the wall-side x to 174.9 mm, which is the mirror of 158.0 about the tray centre 166.45. Mirror error of the four posts is 0.0 mm (calc).

y is +2 and -2, not +84 and not +62. The jack, the fuse holder, and the gate board are already reserved in `STANDINS`. A post of radius 4 mm at (174.9, 62) enters the fuse holder, and the posts at y -62 enter the gate board (cad, the Codex note on this proposal). The gate board reaches y -8. With a 4 mm radius and a 2 mm gap, the post centres sit at y ±2. Every stand-in gap is then at least 2.0 mm (cad). The tight one is the gate board at (174.9, -2).

Do not copy the 5.5 mm end-wall tie from `rim_parts()` onto these posts. That tie runs toward the end and would close the 2 mm gate gap. The post cylinder already in that function is the boss.

Proposed `LID_POSTS`, for the nest owner to apply and then regenerate with the existing script:

`LID_POSTS = [(BX0 + 14.0, 2.0), (BX0 + 14.0, -2.0), (174.9, 2.0), (174.9, -2.0)]`

174.9 is `2 * ((BX0 + BX1) / 2) - (BX0 + 14)`. Writing it that way keeps it tied to the box constants. Nearest terminal centre is 23.35 mm away (calc). The terminal post radius is 4.5 mm, so the surfaces are about 14.8 mm apart (calc).

## Engagement

The rule already used on the robot is 4.5 mm into a brass insert, and the tip stays 0.3 mm off the floor (`fasteners.json` margin).

| Option | Engaged | Bottoms | Meets 4.5 mm |
|---|---|---|---|
| M3x6, bore 5.8 mm, as drawn | 4.0 mm | no | no |
| M3x6, deeper bore 6.3 mm | 4.0 mm | no | no |
| M3x6, longer insert | 4.0 mm | no | no |
| M3x8, bore 5.8 mm | 5.7 mm | yes | no |
| M3x8, bore 6.3 mm | 5.7 mm | no | yes |

A longer insert does not help. The M3x6 only reaches 4.0 mm past the 2.0 mm lid, and BOM 16 is already a 5.7 mm insert. A deeper bore with the same M3x6 does not help either.

The option that meets the rule with parts already on the bill: change the four lid screws from M3x6 button (BOM 17j) to M3x8 socket head (BOM 17a), and deepen only the four lid-post bores from 5.8 mm to 6.3 mm. The insert stays BOM 16. Engagement 5.7 mm, tip gap 0.3 mm (calc). The post still has solid below that bore: the bore ends at z 17.2 and the post starts at z 2.5 (calc, from `rim_parts`).

The socket head is 3.00 mm tall and the button is 1.65 mm (cited, DIN 912 and ISO 7380, the sizes `FASTENERS.md` already uses). `NEST_CAD.md` says 2.85 mm of felt over the button heads. If the sleeve stays put, the socket head leaves 1.50 mm (calc). That 2.85 mm was not re-measured on the sleeve mesh.

## Still open, not in this edit

Topology STLs that bury screw heads stay out of `print/`. The chest hole in `print/body_front.stl` stays open until its owner fills it. No charger mount. No wall-card fastener. No flush-well cut.
