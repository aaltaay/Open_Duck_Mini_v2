# Shin drive eye: walk 2 and soft fall 1.2

Written 2026-11-12 9:06 AM ET. This builds on twin/structure/TOPOLOGY.md and twin/structure/STRUCTURE_TWIN.md. It does not replace those numbers, and it does not copy anything into print/.

Labels: FEA pass only is the linear tetrahedron solver in st_fea.py. CAD check only is a mesh clearance or a hole ray. Calc only is a scale applied to an FEA number. Sim pass only is a MuJoCo load. Cited is a datasheet or a catalog page opened for this file. BLOCKER means the number is not on that page.

## The limit

The servo-facing face of the drive eye is 2.02 mm from the knee servo case (CAD check only), at [5.28, 9.65, 0.0] mm in the shin link. Thickening toward the servo is not available. The topology collar already grew the other way, the head side, by about 6.6 mm inside a 32 mm radius.

## Which number is the stock eye

Three published walking safety factors sit on this part. They are not three answers for one mesh.

| Number | What it is | Mesh | Loads and supports |
|---|---|---|---|
| 1.56 to 1.63 | 2026-11-03 structure twin, level 1 and level 2 | TetGen tetrahedra on knee_to_ankle_left_sheet, the shin plate before D59 | Build 2.653 kg. Ten soft falls. Supports and the failure index are the ones in st_fea.py |
| 0.79, then 1.30 | Topology pass, stock print STL, then the collar | Voxel grid, pitch in the band 0.75 to 0.8 mm. TetGen does not recover these STLs | Same shin_segment study: drive sheet, idle sheet, spacer, ankle case fixed, knee horn screws loaded. Build 2.808 kg. Eleven soft falls |
| 0.58, then 0.97 | This file's first pass, stock, then the collar | Same voxel code, pitch fixed at 0.8 mm | Same study, same scripts. Walk knee peaks match a re-run under MuJoCo 3.17.0 (the version in the structure twin) and under 4.0.1. Nine soft falls: two rough seeds did not hit a printed part |

The solver, the 1 mm average, the failure index, and the shin supports were not edited between the topology pass and this one. The only later edit in st_fea.py is the STL path helper, and the stock shin is read from print/ either way.

Re-run of the stock eye and of the topology collar, same scripts, voxel pitch 0.75 mm (FEA pass only): stock walk 0.80, soft worst 0.47, 7 of 9 under 1.2. Collar walk 1.30, soft worst 0.70, 3 of 9 under 1.2. The stock walk 0.80 and the collar walk 1.30 are the topology numbers (0.79 and 1.30). The stock soft worst 0.47 is their 0.46. The collar soft worst did not come back (0.70 here, 0.87 in that file): this session has 9 soft-fall files, not 11.

The 0.58 is the same part at 0.8 mm. The peak moves, from in-plane at the eye to an interlayer wall element, and the safety factor drops. It is a real result of the coarser pitch. It is the wrong number to set beside 0.79. The number that matches the topology pass is the 0.75 mm re-run: stock walk 0.80, collar walk 1.30.

The 2026-11-03 value is not 0.79. That study is TetGen, on the older shin plate, on a lighter build. Voxel and TetGen are not the same mesh, and those two safety factors are not a disagreement about one model.

Soft falls are time constant 0.0158 s and damping ratio 0.2, the same level as the topology pass. Walk and push are the cases in st_loads.py.

The horn screws stay the four that are already there (F203, F205, F207, F250 on the left shin). No screw is added, so the D42 pattern is unchanged. A ray along each screw axis is open (CAD check only, 0 of 12 samples solid). D39 is unchanged.

## Materials (cited)

Room-temperature tensile strength is X-Y and Z, MPa. Heat deflection is ISO 75. S in the failure index is set equal to Z, the same assumption as the structure twin, not a datasheet shear.

| Material | X-Y | Z | Modulus X-Y | HDT 1.8 MPa | HDT 0.45 MPa | Density | Source |
|---|---|---|---|---|---|---|---|
| PLA, the lab value | 47.1 | 22 design | 2641 | 49 to 57 (the thermal twin) | | 1.20 | structure twin, Overture PLA |
| PETG HF | 34 ± 4 | 23 ± 4 | 1810 ± 190 | 62 C | 69 C | 1.28 | Bambu PETG HF TDS V1.0, Tg 66 C. Bars were annealed. The sheet says not to anneal real prints. |
| PLA-CF | 38 ± 4 | 26 ± 2 | not in the table read here | 54 C | 55 C | 1.22 | Bambu PLA-CF table, Tg 63 C, Vicat 69 C |
| ASA | 37 ± 3 | 31 ± 4 | 2450 ± 270 | 92 C | 100 C | 1.05 | Bambu ASA TDS V3.0. Bars were annealed. |
| PA6-CF | 102 ± 7 | 48 ± 6 | 4430 ± 310 | 164 C | 186 C | 1.09 | Bambu PA6-CF TDS V3.0. Tg 68 C, Vicat 212 C. Bars were annealed and dried at 80 C for 12 h. Saturated water absorption 2.35 %. |

The knee case is in the 55 to 63 C band. The heat study's torque-off leaves the case near 63 C (calc only), and the knee twin's range is 47 to 63 C (sim pass only). The sheets touch the case.

Hot PLA tensile at that band is BLOCKER. Grasso and others (2018) did not report a tensile strength at 50 C or 60 C, because those bars did not separate. The 0.62 factor at 50 C in the structure twin is a compression result (Slavkovic and others, 2024), not a 60 C tensile. PLA-CF heat deflection, 54 C and 55 C, sits at the bottom of the knee band. PETG heat deflection at 1.8 MPa is 62 C, inside the band, and its room-temperature strength is lower than this PLA. ASA holds its heat deflection above the band, and its room-temperature strength is also lower than this PLA.

PA6-CF heat deflection is far above the band, at a test stress of 0.45 MPa and 1.8 MPa. The eye stress on the recommended shape is about 36 MPa (102 / 2.81, calc only from the FEA safety factor). Heat deflection does not prove the 102 MPa at 63 C. Tensile strength of PA6-CF at 55 to 63 C is BLOCKER. The sheet's humid bending strength drops from 151 MPa dry to 95 MPa (cited, Bambu comparison, flexural, not tensile). Wet tensile is BLOCKER. A sensitivity that scales the 0.75 mm safety factor by 95 / 151 is calc only and is not a result: walking 2.85 becomes 1.79, and the soft worst 1.61 becomes 1.01. Both would miss. That sensitivity is why a dry annealed coupon at about 60 C is still required.

## Printer

The PA6-CF sheet (cited) says: dry the spool at 80 C for 8 to 12 h in a blast oven, or on the printer bed at 90 to 100 C for 12 h; keep it under 20 percent relative humidity; nozzle 260 to 290 C; nozzle size 0.4 mm, 0.6 mm recommended, or 0.8 mm; chamber 45 to 60 C. The sheet does not name the nozzle metal. Carbon fiber wears a brass nozzle, so a hardened nozzle is part of printing this filament. The lab printer file is a generic 0.4 mm profile for estimates, and it says the real printer is not known (print/PRINT_PLAN.md, print/config/printer_generic.ini). Whether that printer has a hardened nozzle and a chamber that holds 45 to 60 C is BLOCKER.

## What was run

Same segment as st_fea_run.py shin_segment: drive sheet, idle sheet, spacer. Proposed shapes are under twin/structure/shin_eye/stl/. The servo-facing face is not moved. This table is the 0.8 mm pass. The 0.75 mm re-run that matches the topology stock and collar walks is in the section above, and the recommendation uses that pitch.

| Option | Walk | Push | Soft worst | Soft under 1.2 | What it is |
|---|---|---|---|---|---|
| Stock, PLA | 0.58 | 0.53 | 0.54 | 5 of 9 | print/ shin_left_sheet |
| Stock, PETG | 0.56 | 0.51 | 0.39 | 7 of 9 | cited allowables, PLA stress field |
| Stock, PLA-CF | 0.63 | 0.57 | 0.43 | 6 of 9 | cited allowables, PLA stress field |
| Stock, ASA | 0.61 | 0.56 | 0.42 | 5 of 9 | cited allowables, PLA stress field |
| Stock, PA6-CF | 1.26 | 1.14 | 0.92 | 2 of 9 | cited allowables, PLA stress field. Mode is interlayer, so Z = 48 MPa sets it |
| Collar, PLA | 0.97 | 0.77 | 0.61 | 3 of 9 | the topology STL |
| Collar, PA6-CF | 2.11 | 1.69 | 1.33 | 0 of 9 | cited allowables. A re-solve with the drive sheet at 4430 MPa gives the same 2.11 and 1.33 |
| Collar plus head recess, PLA | 0.98 | 0.78 | 0.63 | 3 of 9 | recess diameter 5.8 mm, back to the original head seat |
| Collar plus head recess, PA6-CF | 2.12 | 1.71 | 1.37 | 0 of 9 | push stays under 2 |
| Taper, PLA | 1.10 | 0.81 | 0.60 | 3 of 9 | collar stepped out to 48 mm |
| Taper, 5 walls 40 % | 1.70 | 1.50 | 0.79 | 2 of 9 | peak moves to the idle sheet |
| Taper, solid drive sheet | 1.70 | 1.50 | 0.80 | 1 of 9 | same idle-sheet peak. Gyroid at 100 % is not a slicer setting. The FEA treats the infill zone as solid |
| Taper, layers along +x | 1.31 | 1.08 | 0.81 | 2 of 9 | one other print orientation. Not enough |
| Web, PLA | 1.28 | 0.96 | 0.74 | 3 of 9 | taper plus a 6.6 mm web on the thin run |
| Web plus head recess, PLA | 1.29 | 0.96 | 0.74 | 3 of 9 | the shape that can still use the M3x6 |
| Web plus head recess, PA6-CF | 2.80 | 2.09 | 1.63 | 0 of 9 | cited allowables on the PLA modulus solve |
| Same, drive sheet modulus 4430 MPa | 2.81 | 2.10 | 1.61 | 0 of 9 | FEA pass only. The stiffer drive sheet does not drop the margin |

All of those rows are FEA pass only. PETG, PLA-CF, ASA, and PA6-CF rows that say "cited allowables" use the PLA stress field. For an in-plane peak that is exact when the modulus is uniform. The two modulus re-solves are the rows that say 4430 MPa.

On the recommended shape, member by member (FEA pass only):

| Member | PLA walk / soft | PA6-CF walk / soft |
|---|---|---|
| Drive sheet (the web) | 1.29 / 0.74, 3 of 9 under 1.2 | 2.79 / 1.62, 0 of 9 |
| Idle sheet (stock geometry) | 1.70 / 0.80, 1 of 9 under 1.2 | 3.69 / 1.73, 0 of 9 |
| Spacer | does not govern | does not govern |

The idle sheet in PLA misses both margins. Both shin sheets have to be PA6-CF. The spacer can stay PLA.

## Parts that were checked and not used

Bunting FFM003006010, SAE 841 oil-filled bronze flanged bearing (cited, catalog page): nominal bore 3 mm (3.002 to 3.012 mm), outside 6 mm (6.019 to 6.031 mm), length 10 mm, flange outside 9 mm, flange thickness 1.5 mm, catalog temperature 10 F to 220 F. The horn screws sit on a 7 mm radius. The hub bore is 7.2 mm. A 6 mm sleeve leaves about 0.4 mm of plastic between the sleeve and the hub (calc only). The 9 mm flange overlaps the hub (CAD check only). The part does not fit this eye. It was not meshed.

CNC Kitchen M3 x 5.7 (BOM line 16, outside 4.6 mm, hole 4.0 mm) is a thread in the plastic. The horn screw threads into the aluminum horn and passes through the plastic. The insert bore is an M3 thread, so a 3 mm shank does not pass. It is not a bushing for this joint. No FEA.

Bolt Depot 6382 is an M3x16 DIN 912 A2 socket head (cited, the product page: length 16 mm, head 5.32 to 5.68 mm, height 2.86 to 3.00 mm). A 16 mm screw through a 9 mm eye would stick out of the horn toward the servo. It is not used. The head recess puts the existing M3x6 (BOM line 17d, Bolt Depot 6378) back on the original seat. No new screw, no new part.

## Print mass and time

PrusaSlicer 2.7.2 through print/slice.py, the parts.csv stack for these sheets (3 walls, fit). Model grams, not weighed. Quantity is 2. The stock drive sheet is 10.38 g and 1.09 h, which matches the topology file. Support grams are extra and are listed in slice.json.

| Shape | g per part | h per part | Robot delta g, PLA | Robot delta h |
|---|---|---|---|---|
| Stock drive sheet | 10.38 | 1.09 | 0 | 0 |
| Collar | 14.12 | 1.60 | +7.48 | +1.02 |
| Collar, head recess | 13.82 | 1.63 | +6.88 | +1.08 |
| Web, head recess | 15.43 | 1.74 | +10.10 | +1.30 |
| Web, 5 walls 40 % | 21.62 | 2.38 | +22.48 | +2.58 |
| Web, rectilinear 100 % | 29.22 | 2.51 | +37.68 | +2.84 |

There is no PA6-CF profile in print/config/. The time above is the PLA profile. PA6-CF grams scale the toolpath by 1.09 / 1.20 (cited densities): the recessed web is 14.02 g per part, 28.03 g for the pair, which is +7.27 g against the PLA stock pair. The idle sheet, stock STL, is 9.89 g and 1.07 h in PLA (slicer). In PA6-CF that is 8.98 g per part, 17.96 g for the pair, which is 1.82 g under the PLA pair. Net for the four sheets, PA6-CF against today's PLA: +5.45 g (calc only on the two idle sheets, slicer on the drive sheets). Idle-sheet time does not change.

## Recommendation

Print the drive sheet from twin/structure/shin_eye/stl/shin_left_sheet_web_cbore.stl, in Bambu PA6-CF, dried and annealed the way the tensile bars were. Print the idle sheet, shin_right_sheet, in the same PA6-CF, stock geometry. Leave the spacer in PLA. Keep the M3x6 horn screws.

On the 0.75 mm mesh, the one that reproduces the topology stock and collar walks, with the drive sheet at the PA6-CF modulus, the segment safety factors are 2.85 walking, 2.48 push, and 1.61 soft worst, 0 of 9 under 1.2 (FEA pass only). The same shape at 0.8 mm was 2.81, 2.10, and 1.61. The idle sheet on its own, with the cited PA6-CF allowables, is 3.69 walking and 1.73 soft (FEA pass only, the 0.8 mm field).

Nothing else that was run meets both 2 and 1.2. PLA, PETG, PLA-CF, and ASA miss on every shape. PA6-CF on the stock eye misses (1.26 and 0.92). The collar in PA6-CF meets walking and the soft fall (2.12 and 1.37) and misses push (1.71).

Do not copy the STL into print/. Hot tensile and wet tensile of PA6-CF are BLOCKER. A coupon of this sheet, dry and at about 60 C, has to replace those two before the structure row can pass. The nest mass is still not in this model.

## Sources

- Bambu PA6-CF TDS V3.0: https://wiki.bambulab.com/filament-acc/petcf-ppacf/c750bddfb8e44af6ae9f7dd9625fa458.pdf
- Bambu PETG HF TDS V1.0: https://botland.com.pl/img/art/inne/25540_karta_produktu.pdf
- Bambu PLA-CF table (tensile, heat deflection, density, Tg): https://www.crea3d.com/en/?controller=attachment&id_attachment=1006
- Bambu ASA TDS V3.0: https://wiki.bambulab.com/filament-acc/abs-asa-pc/6eaf4c432d1d4014a1975e55a55ed00b.pdf
- Bambu filament comparison, PA6-CF humid flexural drop 151 MPa to 95 MPa: https://wiki.bambulab.com/en/filament/petcf_ppacf
- Grasso, Azzouz, Ruiz-Hincapie, Zarrelli, Ren (2018), Rapid Prototyping Journal 24(8): 1337-1346. The 50 C and 60 C bars did not separate, so they were not given a tensile strength: https://www.emerald.com/rpj/article/24/8/1337/367278/Effect-of-temperature-on-the-mechanical-properties
- Bunting FFM003006010: https://catalog.buntingbearings.com/item/sae841-metric-powdered-metal-sleeve-bearings/bronze-metric-flanged-bearings-sae-841/ffm003006010
- Bolt Depot 6382, M3x16, not used: https://boltdepot.com/Product-Details?product=6382
