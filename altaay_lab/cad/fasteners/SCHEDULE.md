# Fastener schedule

Every robot screw is one object in `schedule.json` under `robot` (361 screws: 324 fitted, 37 left out). The nest joints are under `nest`. They are not in `fasteners.json`. This page is the reading guide. The numbers below are the ones `audit.py` wrote.

## Fields on each robot row

| Field | Meaning | Label |
|---|---|---|
| `id`, `spec`, `size`, `length_mm`, `head`, `material` | The screw already in `fasteners.json`. Material is A2 when the spec says A2. | cad |
| `fitted`, `status` | Left out when the status says LEAVE OUT or NOT FITTED. | cad |
| `joint`, `anchor`, `insert` | Head side, the part it screws into, and the insert when the anchor is an insert. | cad |
| `nut` | None on the robot. `fasteners.json` records no hex pocket. | cad |
| `washer` | `two 0.3 mm M2.5` on the 4 fitted eye screws (8 washers, BOM 17l, D21). Null on the rest. | cad |
| `hole_mm`, `hole_status` | Clearance hole already measured in that file. | cad |
| `e_mm`, `e_rule_mm`, `tip_gap_mm` | Thread engaged, the rule that file already uses, and the gap to the first solid. | cad |
| `recess_mm`, `recess_status` | Head recess against the DIN 912 knurl that file already uses. | cad |
| `wall_clearance_mm`, `wall_against` | Worst head clearance already stored from the joint sweep. | cad |
| `wire_gap_mm`, `wire_id` | Zero-pose gap from the screw centreline to that cable, after the wire radius and the head radius. Not a sweep. | cad |
| `torque_chart_nm`, `torque_chart_applies` | The cited table, and whether its own depth line is met. | cited, then cad |
| `threadlocker` | `yes` only for metal into the motor metal. | cited |
| `bom_line`, `supply` | The existing BOM line. | cad |

## Robot rollup (cad)

From `fasteners.json`, counted again here.

| | Count |
|---|---|
| Screws in the file | 361 |
| Fitted | 324 |
| Left out on purpose | 37 |
| Length status OK | 154 |
| Length status BELOW RULE | 89 |
| Length status BELOW RULE, NEW LENGTH | 2 |
| Fitted with no length-status word (factory case screws, bag screws the file marks unverified or FIT) | 79 |
| Head recess INTERFERENCE | 24 |
| Head recess TIGHT | 22 |
| Threadlocker yes (metal into the horn or the output shaft) | 116 of the 324 fitted |
| Threadlocker no | 208 of the 324 fitted |
| Chart torque applies | 0 of 324 |

The 24 recess clashes and the 89 short engagements are the ones `FASTENERS.md` already lists. This audit does not pick a new length for them. The pilot or the bore is too shallow for a longer stock screw, which is that file's own finding.

`seat_world` matches the URDF link transform of `seat_link` within 0.001 mm (cad). The wire gaps use that same transform.

## Torque (cited, then not used)

RLS installation guide TTD01_03, issue 03, 6 Dec 2023, dry A2/A4 property class 70:

| Head | M2 | M2.5 | M3 |
|---|---|---|---|
| DIN 912 / ISO 4762 | 0.35 Nm | 0.7 Nm | 1.2 Nm |
| ISO 7380 | 0.19 Nm | 0.37 Nm | 0.6 Nm |

The same page says the depth of the screw in the threaded hole is at least 1 x D nominal for steel or 2 x D nominal for aluminum. Horn thread on this duck is about 2.2 to 2.4 mm in aluminum (cad, `fasteners.json`), and 2 x 3 mm is 6 mm. Inserts are brass in plastic, which that sentence does not cover. Self-tappers are in plastic. So `torque_chart_applies` is false on every fitted screw. The upstream guide does not give a torque either. This audit does not invent one.

## Threadlocker (cited)

`docs/assembly_guide.md`: a little Loctite 243 when the screw is metal against metal in the motors. BOM 19 is that bottle. `threadlocker` is yes on those rows (horn screws and the output-shaft screws). It is no on screws into plastic and on screws into inserts. Factory case screws are already in the servo. Do not add locker to them at assembly.

The same RLS page suggests a medium-strength threadlocker (Loctite 243) where the joint sees vibration or temperature change. That is the same bottle. It does not add a new part, and it does not override the guide's "metal into the motor" line.

## Nest joints (calc, from `nest_parts.py`)

Not installed. No new screw size. The duck side of the nest adds no screw (the carriers sit in the pockets, as `NEST_CAD.md` already says).

| Id | Qty | Spec | Head | Material | Nut or insert | Washer | Hole | Engaged | Tool |
|---|---|---|---|---|---|---|---|---|---|
| NL1 to NL4 | 4 | M3x6 ISO 7380 | button, hex 2.0 | A2 | M3 heat-set insert, BOM 16, bore 4.0 mm, depth 5.8 mm | none | 3.4 mm | 4.0 mm | hex 2.0, already on BOM T4. Same key `BUILD_ORDER.md` uses for M3 button heads |
| NT1, NT2 | 2 | M3x8 DIN 912 | socket, hex 2.5 | A2 | M3 heat-set insert, BOM 16 | none. An M3 ring lug is named under the head. The lug has no catalog line in the BOM. | 3.4 mm | not known. The lug thickness is not in the CAD. | hex 2.5, already on BOM T4 |
| Jack | 1 | Same Sky PJ-005A, dock line K6b | the jack's own nut and washer | the jack's | the nut that comes with the jack | the washer that comes with the jack | 8.0 mm | the jack's own thread | wrench size is not in the repo |

Lid engagement is 6.0 mm minus the 2.0 mm lid, so 4.0 mm (calc). The robot rule for a brass insert is 4.5 mm (cited via `FASTENERS.md` section 8). An M3x8 would enter 6.0 mm into a 5.8 mm bore and bottom (calc). No stock length meets the rule. The nest file already chose M3x6 from BOM 17j. This audit does not add a length.

Lid screws are a rectangle. About their own centre the mirror error is 0.0 mm (calc). About the tray centre the mirror error is 8.0 mm, and that centre sits 4.0 mm toward the wall of the part centre (calc). D42 asks for the part's own centre. See `PROPOSED_EDITS.md`. The terminal pair mirrors about the part centre (error 0.0 mm, calc).

Chart torque does not apply to the lid screws: 4.0 mm in a brass insert is not the steel or aluminum depth on TTD01_03. Threadlocker: these threads are not metal into a motor, so the assembly guide does not call for it.

Wire clearance for the nest screws was not measured. The nest is not in the robot cable file.
