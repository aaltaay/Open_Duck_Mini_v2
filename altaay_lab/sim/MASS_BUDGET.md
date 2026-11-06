# Mass budget: the robot we will build against the trained model (sim pass only)

Written 2026-11-01 9:40 PM ET by agent M (simulation), for Ahmed's print-readiness pass. Script: sim/mass_budget.py. Regenerate with
`ODM_PLAYGROUND=<Open_Duck_Playground at b9be205> ODM_OUT=<scratch folder> python3 altaay_lab/sim/mass_budget.py`
(tables land in ODM_OUT/mass_budget_tables.md and mass_budget.json; the figure is sim/mass_budget.png). Updated 2026-11-02 12:15 AM ET by agent PP (print package) after DECISIONS.md D22, the light print profile: the script was re-run unchanged on the regenerated print/SLICE_SUMMARY.md and every table below comes from that run; only the printed parts changed mass (1318.6 g to 1190.4 g), and the centre of mass also carries the BEC Pro seat fix (aa7263e, 0.08 mm, print/MASS_STUDY.md). Updated 2026-11-02 about 1:00 AM ET by agent NL2 (final docs pass) after the netlist final pass: the script gained positions for the new inline splices JFI and JFO at the fuse holder seat (audit/placements.json), as VSW and G sit at the switch seat, and was re-run; wires 107.7 to 121.0 g (SP4 and SP5, the P7 lead extensions, the cut lengths from the 3D routes), total 2638.6 to 2651.9 g, nothing else changed. Updated 2026-11-02 about 6:10 AM ET by agent SFX (script run at 5:55 AM ET) after agent CAB's cut changes in wiring/netlist.yaml since that run (the P7 line piece 20 to 30 mm, the SP1 to SP3 ground tails 20 to 30 mm, the SD1 ground stem 30 to 45 mm and data branch 160 to 170 mm, and the D25 twist take-up: SP4 and SP5 V and G +10 mm to 400 and 430 mm, D10 to 220 mm): the script was re-run unchanged and every table below comes from that run; wires 121.0 to 121.8 g, total 2651.9 to 2652.8 g, nothing else changed; sim/mass_budget.png is from the same run. Nothing is weighed yet: every number below is a slicer estimate, a datasheet value or a computation, and the build may differ.

## Answer
- 2026-11-06 ET, V1 freeze (twin/freeze/FREEZE.md section 6, calc only, not yet in the sim model): about +18.6 g on the 2720.1 g build, so about 2738.7 g: the cliff ToF board 1.8 g, two MPR121 boards about 6 g (mass not published: BLOCKER), copper foil about 1.9 g, the new 26 AWG wires D16 to D22 about 6.8 g (2.97 m at about 2.3 g/m), tape about 0.5 g, PLA +3.1 g speaker duct, +0.45 g grille plugs, -1.97 g body_front (the ToF pocket and window take out more than its standoffs add). The trunk takes about 13 g, the head about 6 g. The sim model and C8 still run the 2720.1 g build: re-run sim/mass_budget.py when the boards are weighed.
- 2026-11-05 about 12:50 AM ET, V1 track 9 (D44): the 2S1P Molicel P45B pack replaces the two P30B cells and the 2 x 18650 holder: cells 2 x 70.0 g (Molicel INR21700P45B-01 v0.2) on the grown bay's cell axes, the strip, sleeve and leads 5 g (UNVERIFIED) for the 25 g holder: **+26.0 g**; body_back with the grown bay -1.69 g (sliced 70.18 to 68.49 g without support, print/SLICE_SUMMARY.md). The script (sim/mass_budget.py, run 2026-11-05 ET on this tree) gives 2659.4 g before and 2685.4 g after (without the knee servos' +39.0 g); so the build is about **2.72 kg** (2695.8 + 26.0 - 1.7 = 2720.1 g, not weighed). Whole robot centre of mass at the home pose, trunk frame: [-27.6, 0.4, 49.7] to [-28.7, 0.5, 49.4] mm (1.1 mm back; the walk held 3.6 to 4.4 mm back in sim/ADDED_MASS_SIM.md); trunk principal inertia (kg m2 x 1e-4) [19.70, 34.90, 41.26] to [19.84, 36.98, 43.39]. The tables below are from the run of 2026-11-02 and are not regenerated here (sim/mass_budget.png is). Twin checks at the new mass: twin/battery/BAY.md.
- Our build: **2.72 kg** (2720.1 g since D44: 2695.8 g before, plus 26.0 g for the 2S1P P45B pack and -1.7 g for body_back with the grown bay, line above; the 2695.8 g were: the 2652.8 g of the tables below, plus 39.0 g for the two STS3250 knee servos, 74.5 g against 55 g at each thigh, D32, plus 7.2 g for left and right roll_to_pitch at 3 walls, D38, minus 5.4 g for D39: closed holes -4.2 g of printed parts on the robot (print/SLICE_SUMMARY.md), one M3x8 screw and one insert -1.24 g (0.89 and 0.35 g each, the trunk rows below); plus 2.2 g for D42 (uniform patterns: +0.34 g printed on the robot, print/SLICE_SUMMARY.md; one more M3x8 and insert on head_bot_sheet +1.24 g; one more M2.5x10 on the lid +0.66 g, calc only from its volume); updated 2026-11-04 11:01 PM ET, the tables and the centre of mass are not recomputed; twin/knee/KNEE_TWIN.md). The MuJoCo model the policy was trained on: **2.107 kg** [U] (Open_Duck_Playground b9be205, xmls/open_duck_mini_v2.xml, body masses). Difference **+613 g (+29 %)** [L] (+587 g, +28 % before D44). Before D22 (print profile with 3 to 5 walls) it was 2.77 kg, +660 g (+31 %); D22 alone gave 2.64 kg (2638.6 g), the netlist final pass adds 13.3 g of wire (the D23 ankle feeds SP4 and SP5, the P7 lead extensions, the cut lengths from the 3D routes) and agent CAB's later cut changes (the D25 twist take-up included) 0.9 g more.
- Where: trunk +242 g (+35 %), head +141 g (+35 %), each leg +64 to +65 g (+16 %), neck chain +33 g (+19 %) [L] (table 2).
- Why, in two parts [L] (table 3):
  1. **405 g of parts the trained CAD does not have at all**: screws and inserts 196 g, wires 122 g, the lab-only power parts 59 g (BEC Pro, fuse, Pololu 2815, D30V30F5, splices, XT30, tape), the projector print, foot switches and small electronics.
  2. **140 g more in parts the CAD does have** (267 g before D22). In the legs and neck the trained model's own part masses can be recovered exactly (table 4): the servos agree (53 to 56 g against the 55 g data sheet). Since D22 most leg and body parts print at the upstream 2 walls with solid rings round their insert bores, so in the two legs together the CAD parts are now 1.0 g lighter than the trained model (+76 g before): left_cache is 51.6 g in the trained model and 55.3 g in our slice (75.4 g before), each foot 12.2 g lighter. Parts kept heavy by D22 still weigh more: the neck chain's printed parts are 9 g lighter in all (the fit gives head_yaw_to_roll 36.5 g, about solid PLA for its 29.4 cm3 volume), so its +33 g is all screws and wires. In the trunk (+78 g) and head (+72 g) the split by part is not unique, but the head shell alone is 232 g in our slice (net of support; the head keeps 4 walls) [L] (print/SLICE_SUMMARY.md).
- **Centre of mass** [L], whole robot at the home pose, trunk frame: trained (-25.6, -0.6, 44.0) mm, ours (-27.7, 0.4, 49.5) mm: **x -2.1 mm, y +1.0 mm, z +5.6 mm** (x forward, y left, z up; before D22 x -2.6, y +1.1, z +3.0 mm). It sits behind the trained one because the lab-only parts sit in the battery bay and belly behind the trunk centre of mass: the trunk link's own centre of mass moves 7.5 mm back (x -7.5 mm). D22 moved it 0.5 mm forward and 2.9 mm up: the mass came off the trunk shells behind it and the legs below it (print/MASS_STUDY.md). At the home pose the robot centre of mass is 4.2 mm ahead of the MJCF foot sites in the trained model and 2.1 mm in ours, that is 3.0 mm and 0.9 mm ahead of the ankle servo axes (x = -28.6 mm); the soles span x = -68 to +35 mm [L].
- **Inertia** [L]: trunk principal moments +17 to +20 %, head +22 to +41 % (Centre of mass section).
- **URDF against MJCF** [U]: identical on every link except the head. The URDF head with its antenna holders is 361.0 g, the MJCF head 406.6 g: the URDF (mini_bdx/robots/open_duck_mini_v2/robot.urdf) is an older Onshape export without the eyes, bulbs, eye glass, speaker, camera, speaker stand and speaker interface, and its head.stl is 217 cm3 against 229 cm3 for print/head.stl [L]. Body frames agree to 0.0000 mm in position and 3.0e-13 in rotation [L].
- **How far outside training this is** [U]: training scales every link mass by U(0.9, 1.1) (Open_Duck_Playground common/randomize.py lines 68 to 71). Our links are 0 % (head yaw link) to 98 % (head pitch link) heavier; the trunk 35 %, the head 35 %; only the feet (+4 %) and the head yaw link are inside the +-10 %. The "add mass to torso" and "jitter centre of mass" lines (randomize.py lines 61 to 65 and 73 to 76) act on body id 1 (TORSO_BODY_ID = 1, line 23), which is the massless "base" body, not trunk_assembly; MuJoCo puts a massless body's inertial point at its body position (0, 0, 0.22 m) [L] (checked with a two-body test model), so training added a point mass of -0.1 to +0.1 kg about 22 cm above the trunk origin, near head height. The real trunk centre of mass was never moved in training. What this does to walking is sim/ADDED_MASS_SIM.md.

## Method
1. Every link of the trained model was rebuilt from its CAD parts: each URDF mesh instance (mini_bdx/robots/open_duck_mini_v2, the same Onshape document) with a uniform density, which is how Onshape computes the model; head parts that the URDF lacks come from print/*.stl, which share the head.stl frame (audit/headgroup.py) [L].
2. Check of the method: fitting the trained model's per-part masses by non-negative least squares on each link's mass, first moment and full inertia reproduces the leg and neck links to under 0.2 g, 0.25 mm and 1.1 % of inertia (table 4) [L]. The trunk (17 parts) and head (20 parts) have more unknowns than the 10 equations, so their fits are not unique and are not used.
3. Our masses: printed parts from the slicer (support removed), bought parts from datasheets and seller pages, screws from ISO 4762 sizes and the A2 density, wires from the netlist cut lengths and a per-metre mass computed from AWG copper area and the BNTECHGO outside diameters [L] (sources at the end).
4. Our positions: CAD parts on their mesh; lab-only parts as boxes at audit/placements.json (URDF zero-pose frame, the trunk frame); the D30V30F5 below the Pi centre on the head floor (no placements.json entry exists, MOUNTING.md says "head floor below the Pi"); speaker in speaker_interface, camera on its 4 head pilots, amplifier right of the speaker stand; screws and inserts at their measured hole sites (audit/sites.json, audit/sites_head.json, same selection as audit/screws2.py, one screw per anchor), which gives exactly the audit counts: 58 insert screws and 58 inserts, 99 horn screws (BOM 100), 66 servo-case screws, 17 M2.5x6, 14 horn centre screws, 8 eye screws, 4 lid, 4 camera, 4 roll_to_pitch [L]; wires as point masses along a polyline from part to part through the joints they cross [L].
5. Every body's mass, centre of mass and inertia is summed per MJCF body. sim/added_mass_sim.py writes them into a copy of the MJCF.

## Table 1: by category

| Category | Our build g | of which not in the trained CAD g |
|---|---|---|
| servo | 770.0 | 0.0 |
| printed | 1190.4 | 10.3 |
| electronics | 108.3 | 13.9 |
| mechanical | 80.7 | 0.0 |
| battery | 119.0 | 0.0 |
| screw | 175.3 | 175.3 |
| wire | 121.8 | 121.8 |
| lab_added | 61.9 | 58.9 |
| insert | 20.3 | 20.3 |
| misc | 5.0 | 5.0 |
| total | 2652.8 | 405.5 |

## Table 2: per link (MJCF body), trained model, URDF and our build
CoM in the link frame (= the MJCF body frame), mm. Legs are listed both sides.

| Link (MJCF body) | Trained MJCF g | URDF g | Our build g | Delta g | Delta % | Model CoM mm (link frame) | Our CoM mm | CoM shift mm |
|---|---|---|---|---|---|---|---|---|
| trunk | 698.5 | 698.5 | 941.0 | +242.4 | +35 | [-48.3, -0.1, 38.5] | [-55.8, 0.4, 36.8] | [-7.5, 0.5, -1.7] (7.7) |
| L hip roll link | 66.5 | 66.5 | 77.3 | +10.9 | +16 | [0.8, -0.0, -33.1] | [0.8, -0.0, -31.9] | [0.0, 0.0, 1.1] (1.1) |
| L hip pitch link | 75.2 | 75.2 | 86.1 | +10.9 | +14 | [50.8, -0.4, 20.5] | [46.9, -0.4, 19.9] | [-3.9, 0.0, -0.6] (4.0) |
| L thigh (knee servo) | 124.1 | 124.1 | 145.9 | +21.9 | +18 | [2.5, -39.1, 10.3] | [2.3, -35.9, 10.7] | [-0.2, 3.1, 0.4] (3.2) |
| L shin (ankle servo) | 72.6 | 72.6 | 90.3 | +17.7 | +24 | [0.0, -57.7, 18.1] | [-0.0, -50.0, 17.8] | [-0.0, 7.7, -0.3] (7.8) |
| L foot | 75.2 | 75.2 | 78.3 | +3.1 | +4 | [11.1, -24.7, 19.1] | [10.2, -22.1, 18.6] | [-0.9, 2.5, -0.5] (2.7) |
| neck pitch link | 66.2 | 66.2 | 82.8 | +16.6 | +25 | [-0.0, 49.3, 18.2] | [-0.0, 43.7, 16.7] | [0.0, -5.6, -1.5] (5.8) |
| head pitch link | 16.9 | 16.9 | 33.5 | +16.6 | +98 | [-7.7, 26.0, 18.7] | [-3.5, 24.0, 17.1] | [4.2, -2.1, -1.6] (4.9) |
| head yaw link | 91.8 | 91.8 | 92.0 | +0.2 | +0 | [4.1, 0.0, -22.3] | [8.0, 0.0, -20.8] | [3.9, -0.0, 1.5] (4.2) |
| head | 406.6 | 361.0 | 547.2 | +140.6 | +35 | [8.2, -3.9, 22.8] | [10.7, -0.2, 19.9] | [2.5, 3.7, -2.9] (5.3) |
| R hip roll link | 66.5 | 66.5 | 77.4 | +10.9 | +16 | [0.8, -0.0, -33.1] | [0.8, -0.0, -31.9] | [0.0, 0.0, 1.1] (1.1) |
| R hip pitch link | 75.2 | 75.2 | 86.0 | +10.9 | +14 | [-50.8, -0.4, 20.5] | [-46.9, -0.4, 19.9] | [3.9, 0.0, -0.6] (4.0) |
| R thigh (knee servo) | 124.1 | 124.1 | 146.1 | +22.1 | +18 | [2.5, 39.1, 10.8] | [2.3, 36.0, 11.4] | [-0.2, -3.1, 0.6] (3.2) |
| R shin (ankle servo) | 72.6 | 72.6 | 90.4 | +17.8 | +24 | [0.0, -57.7, 18.1] | [-0.0, -50.0, 17.8] | [-0.0, 7.8, -0.3] (7.8) |
| R foot | 75.2 | 75.2 | 78.3 | +3.1 | +4 | [11.1, -24.7, 19.1] | [10.2, -22.1, 18.6] | [-0.9, 2.5, -0.5] (2.7) |
| total | 2107.1 | 2061.5 | 2652.8 | +545.6 | +26 | | | |

## Table 3: where the difference comes from

| Link | Trained g | Ours, parts the trained CAD also has g | Ours, parts the CAD lacks g | of which screws and inserts g | wires g | lab-only parts g |
|---|---|---|---|---|---|---|
| trunk | 698.5 | 776.3 (+77.8) | 164.7 | 41.7 | 63.7 | 54.2 |
| L hip roll link | 66.5 | 69.9 (+3.4) | 7.5 | 5.5 | 1.9 | 0.0 |
| L hip pitch link | 75.2 | 74.9 (-0.2) | 11.1 | 8.3 | 2.8 | 0.0 |
| L thigh (knee servo) | 124.1 | 130.2 (+6.2) | 15.7 | 13.0 | 2.7 | 0.0 |
| L shin (ankle servo) | 72.6 | 75.0 (+2.4) | 15.4 | 13.0 | 2.3 | 0.0 |
| L foot | 75.2 | 63.1 (-12.2) | 15.3 | 11.2 | 0.9 | 0.0 |
| neck pitch link | 66.2 | 68.7 (+2.5) | 14.1 | 7.3 | 6.8 | 0.0 |
| head pitch link | 16.9 | 15.1 (-1.8) | 18.4 | 12.4 | 6.0 | 0.0 |
| head yaw link | 91.8 | 82.2 (-9.6) | 9.8 | 5.0 | 4.8 | 0.0 |
| head | 406.6 | 478.9 (+72.3) | 68.4 | 27.1 | 18.8 | 4.6 |
| R hip roll link | 66.5 | 69.9 (+3.4) | 7.5 | 5.5 | 2.0 | 0.0 |
| R hip pitch link | 75.2 | 74.9 (-0.3) | 11.2 | 8.3 | 2.8 | 0.0 |
| R thigh (knee servo) | 124.1 | 130.2 (+6.1) | 16.0 | 13.0 | 2.9 | 0.0 |
| R shin (ankle servo) | 72.6 | 75.0 (+2.4) | 15.4 | 13.0 | 2.4 | 0.0 |
| R foot | 75.2 | 63.1 (-12.2) | 15.3 | 11.2 | 0.9 | 0.0 |
| total | 2107.1 | 2247.3 (+140.1) | 405.5 | 195.6 | 121.8 | 58.9 |

## Table 4: the trained model's own part masses (fit), legs and neck

| Link | Part | Trained model g (fit) | Our build g | Fit error: mass g, CoM mm, inertia |
|---|---|---|---|---|
| L hip roll link | roll_motor_bottom | 5.5 | 8.2 | -0.04, 0.12, 1.0 % |
|  | roll_motor_top | 7.6 | 6.7 |  |
|  | servo (case + horns) | 53.3 | 55.0 |  |
| L hip pitch link | left_roll_to_pitch | 20.5 | 19.9 | +0.05, 0.13, 0.3 % |
|  | servo (case + horns) | 54.7 | 55.0 |  |
| L thigh (knee servo) | left_cache | 51.6 | 55.3 | +0.03, 0.04, 0.0 % |
|  | leg_spacer | 8.9 | 7.0 |  |
|  | left_knee_to_ankle_right_sheet | 3.3 | 6.2 |  |
|  | left_knee_to_ankle_left_sheet | 4.1 | 6.8 |  |
|  | servo (case + horns) | 56.1 | 55.0 |  |
| L shin (ankle servo) | leg_spacer | 8.7 | 7.0 | +0.01, 0.02, 0.1 % |
|  | left_knee_to_ankle_right_sheet | 3.5 | 6.2 |  |
|  | left_knee_to_ankle_left_sheet | 4.4 | 6.8 |  |
|  | servo (case + horns) | 56.0 | 55.0 |  |
| L foot | foot_side | 13.9 | 13.0 | +0.00, 0.00, 0.0 % |
|  | foot_bottom_tpu | 19.0 | 17.6 |  |
|  | foot_bottom_pla | 19.0 | 9.5 |  |
|  | foot_top | 23.4 | 23.1 |  |
| neck pitch link | neck_left_sheet | 6.0 | 7.3 | -0.05, 0.23, 0.3 % |
|  | neck_right_sheet | 5.1 | 6.4 |  |
|  | servo (case + horns) | 55.0 | 55.0 |  |
| head pitch link | head_pitch_to_yaw | 16.9 | 15.1 | -0.00, 0.00, 0.0 % |
| head yaw link | head_yaw_to_roll | 36.5 | 27.2 | -0.08, 0.02, 1.1 % |
|  | servo (case + horns) | 55.2 | 55.0 |  |

## Centre of mass of the whole robot
- Whole robot CoM at the zero pose, trunk frame: trained [-22.7, -0.7, 39.7] mm (2.107 kg), ours [-24.7, 0.3, 45.9] mm (2.653 kg), shift [-2.1, 1.0, 6.2] mm; feet sites [[-34.6, 89.4, -193.6], [-34.6, -91.8, -193.6]] mm
- Whole robot CoM at the home pose, trunk frame: trained [-25.6, -0.6, 44.0] mm (2.107 kg), ours [-27.7, 0.4, 49.5] mm (2.653 kg), shift [-2.1, 1.0, 5.6] mm; feet sites [[-29.7, 80.9, -160.7], [-30.0, -81.4, -160.8]] mm
- trunk principal inertia about its CoM (kg m2 x 1e-4): trained [16.76, 29.27, 34.45], ours [19.54, 34.89, 41.27]
- head principal inertia about its CoM (kg m2 x 1e-4): trained [10.73, 16.87, 24.53], ours [15.1, 20.58, 32.08]

## UNVERIFIED items (193 g in all)
No published mass was found for these; each has its basis in the source list. The two big ones set the uncertainty of the total:
- 6804ZZ bearings, 3 x 26.9 g: the CAD solid ring at 7.85 g/cm3, an upper bound (a real bearing has balls and a cage). An exploratory fit of the URDF head (not unique, not used in the tables) puts the trained model's head bearing at about 28 g, the same kind of solid-steel value, so the comparison is not affected much [L].
- 2S holder, 25 g: the Amazon listing gives 0.05 kg with "Unit Count 2 Count"; 50 g if that is one holder. +25 g in the battery bay moves the robot centre of mass about 1 mm back.
- Also the STS3215 bag screws (sizes not published, B2), the kit cable conductor size, the BEC Pro output leads, the fuse holder body, the Camera Module 3, the Tenergy board.
- Not counted: threadlocker; the optional antenna rods (2 x 0.56 g net, print/SLICE_SUMMARY.md optional table).
- Assumed, not stated by Feetech: the 55 g servo mass includes its two horns. If the horns ship loose and weigh 2 to 4 g each pair, add 28 to 56 g.
Plus or minus 40 g on the total does not change any conclusion here.

## Findings that matter for the build
1. Note (not print-blocking): our robot is about 26 % heavier than the model the policy was trained on (31 % before D22), far outside the plus or minus 10 % per link of training. sim/ADDED_MASS_SIM.md is the walking check (run on the 2.77 kg build); print/MASS_STUDY.md ran the same cases on the 2.64 kg build of D22, and its (c) column was run again on this 2.65 kg budget (2652.8 g) after agent CAB's later cut changes (sim pass only). The ADDED_MASS_SIM.md walks were not re-run at 2.65 kg.
2. Note: the print profile was the biggest lever we control, and D22 took it (print/MASS_STUDY.md variant c): the large leg and body parts now print at the upstream 2 walls with solid rings round their insert bores, so the legs' CAD parts went from +76 g over the trained model to 1.0 g under, and left_cache slices at 57.3 g with support (77.3 g before D22, 51.6 g in the trained model) [L] (print/SLICE_SUMMARY.md). What is left is mostly parts the CAD does not have (405 g) and the parts D22 keeps heavy for strength (head, neck chain, frame parts). If the S1 coupon gate fails, the 10 insert ring parts keep 4 walls: about +61.7 g.
3. Note: the lab-only parts sit behind the trunk centre of mass and move it 7.5 mm back. sim/ADDED_MASS_SIM.md shows the walk is far more sensitive to the centre of mass moving back than forward, so any later addition (dock electronics, monitor boards) should go forward of x = -56 mm in the trunk frame, not into the battery bay.
4. Proposed hardware check (for TEST_PLAN.md, not owned here): weigh the finished robot and find its centre of mass before the first walk (robot powered at the home pose, toes on one scale and heels on another, or a balance edge under the trunk). Expected: 2.65 kg plus or minus 0.05 kg (2.71 kg if the D22 coupon gate fails) and the centre of mass about 1 mm ahead of the ankle servo axes. sim/ADDED_MASS_SIM.md finds that the stock policy tips over backwards once the whole-robot centre of mass is 4 to 6 mm further back than this estimate, so a measured value more than 4 mm behind the ankle axes means moving rear parts forward before walking.

V1 3D track, 2026-11-04 about 7:40 PM ET (calc only): the D34 camera cable adds 0.64 g (row above) and the new OFF wire D13 (26 AWG, cut 590 mm, rides the P13 route) adds about the 26 AWG grams per metre of this file times 0.59 m; together under 0.1 % of the robot. The tables keep the V1 track 2 totals until the next mass run.

## Every item

| Item | Category | Link | Qty | g each | g total | In CAD | Source key | Note |
|---|---|---|---|---|---|---|---|---|
| 2S cell holder with leads | battery | trunk | 1 | 25.00 | 25.00 | yes | holder |  |
| Molicel P30B cell | battery | trunk | 2 | 47.00 | 94.00 | yes | p30b |  |
| BNO055 breakout (Adafruit 2472) | electronics | trunk | 1 | 3.00 | 3.00 | yes | bno055 |  |
| USB-C 2S charger (Adeept) | electronics | trunk | 1 | 8.53 | 8.53 | yes | charger |  |
| Waveshare Bus Servo Adapter (A) | electronics | trunk | 1 | 16.00 | 16.00 | yes | adapter |  |
| panel control switch | electronics | trunk | 1 | 2.00 | 2.00 | yes | panel_switch |  |
| M3 heat-set inserts x22 in trunk | insert | trunk | 1 | 7.70 | 7.70 | no | insert | sites audit/sites.json, audit/sites_head.json |
| ATO 15 A fuse | lab_added | trunk | 1 | 1.00 | 1.00 | no | ato_fuse | seat: audit/placements.json |
| Amass XT30U pair | lab_added | trunk | 1 | 0.90 | 0.90 | no | xt30_pair | seat: left of the holder (MOUNTING.md, Tnkr placement), 30 mm to +y |
| CC BEC Pro output leads | lab_added | trunk | 1 | 4.60 | 4.60 | no | bec_out_leads | seat: audit/placements.json |
| Castle CC BEC Pro | lab_added | trunk | 1 | 29.00 | 29.00 | no | bec | seat: audit/placements.json |
| Littelfuse FHAC0001ZXJ fuse holder with leads | lab_added | trunk | 1 | 8.00 | 8.00 | no | fuse_holder | seat: audit/placements.json |
| Pololu 2815 MOSFET switch | lab_added | trunk | 1 | 2.60 | 2.60 | no | sw2815 | seat: audit/placements.json |
| Tenergy 32175 BMS | lab_added | trunk | 1 | 3.00 | 3.00 | yes | tenergy_bms | seat: audit/placements.json |
| VHB 4950 tape under bec_pro | lab_added | trunk | 1 | 1.36 | 1.36 | no | vhb_density |  |
| VHB 4950 tape under fuse_holder | lab_added | trunk | 1 | 0.82 | 0.82 | no | vhb_density |  |
| VHB 4950 tape under mosfet_switch | lab_added | trunk | 1 | 0.45 | 0.45 | no | vhb_density |  |
| servo power splices SPV, SPG | lab_added | trunk | 1 | 1.00 | 1.00 | no | splice | seat: audit/placements.json |
| splices JB+, JB- (BEC outputs) | lab_added | trunk | 1 | 1.00 | 1.00 | no | splice |  |
| splices VSW, G (switched bus, ground) | lab_added | trunk | 1 | 1.00 | 1.00 | no | splice |  |
| splices YD3, YG3, JG30, JG20, JG10 (data Y and grounds) | lab_added | trunk | 1 | 2.50 | 2.50 | no | splice |  |
| 6804ZZ bearing | mechanical | trunk | 2 | 26.90 | 53.80 | yes | bearing |  |
| cable ties | misc | trunk | 1 | 1.00 | 1.00 | no | cable_ties |  |
| solder and heat shrink (joints outside splices) | misc | trunk | 1 | 4.00 | 4.00 | no | solder_heatshrink |  |
| battery_pack_lid | printed | trunk | 1 | 13.58 | 13.58 | yes | slice |  |
| body_back | printed | trunk | 1 | 70.35 | 70.35 | yes | slice |  |
| body_front | printed | trunk | 1 | 57.87 | 57.87 | yes | slice |  |
| body_middle_bottom | printed | trunk | 1 | 88.96 | 88.96 | yes | slice |  |
| body_middle_top | printed | trunk | 1 | 66.21 | 66.21 | yes | slice |  |
| trunk_bottom | printed | trunk | 1 | 41.71 | 41.71 | yes | slice |  |
| trunk_top | printed | trunk | 1 | 67.29 | 67.29 | yes | slice |  |
| M2 servo-case screws (servo bag) x20 in trunk | screw | trunk | 1 | 5.47 | 5.47 | no | servo_bag |  |
| M2.5x10 lid screws x4 in trunk | screw | trunk | 1 | 2.36 | 2.36 | no | screw_mass |  |
| M2.5x6 electronics screws x9 in trunk | screw | trunk | 1 | 4.22 | 4.22 | no | screw_mass |  |
| M3 insert screws (M3x8/10/12 mix) x22 in trunk | screw | trunk | 1 | 19.64 | 19.64 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3x6 horn centre screws (servo bag) x3 in trunk | screw | trunk | 1 | 2.34 | 2.34 | no | servo_bag |  |
| STS3215 C001 servo x3 | servo | trunk | 1 | 165.00 | 165.00 | yes | sts3215 |  |
| Mini-SPOX housings and terminals at ID 20, 10, 30 | wire | trunk | 1 | 0.90 | 0.90 | no | terminal | UNVERIFIED: Molex 50-37-5033 or 2.54 mm housing |
| USB cable slack coil (part of Adafruit 3878) | wire | trunk | 1 | 10.95 | 10.95 | no | usb_cable | seat: audit/placements.json |
| wires 16 AWG in trunk | wire | trunk | 1 | 27.51 | 27.51 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires 20 AWG in trunk | wire | trunk | 1 | 5.12 | 5.12 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires 22 AWG in trunk | wire | trunk | 1 | 11.21 | 11.21 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires 26 AWG in trunk | wire | trunk | 1 | 4.57 | 4.57 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires USB 2.0 cable in trunk | wire | trunk | 1 | 2.61 | 2.61 | no | usb_cable |  |
| wires kit cable in trunk | wire | trunk | 1 | 0.84 | 0.84 | no | kit_cable_gpm |  |
| roll_motor_bottom | printed | L hip roll link | 1 | 8.15 | 8.15 | yes | slice |  |
| roll_motor_top | printed | L hip roll link | 1 | 6.73 | 6.73 | yes | slice |  |
| M2 servo-case screws (servo bag) x6 in L hip roll link | screw | L hip roll link | 1 | 1.64 | 1.64 | no | servo_bag |  |
| M3 horn screws (M3x6/M3x5 mix) x4 in L hip roll link | screw | L hip roll link | 1 | 3.09 | 3.09 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3x6 horn centre screws (servo bag) x1 in L hip roll link | screw | L hip roll link | 1 | 0.78 | 0.78 | no | servo_bag |  |
| STS3215 C001 servo x1 | servo | L hip roll link | 1 | 55.00 | 55.00 | yes | sts3215 |  |
| wires 22 AWG in L hip roll link | wire | L hip roll link | 1 | 0.62 | 0.62 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires 26 AWG in L hip roll link | wire | L hip roll link | 1 | 0.46 | 0.46 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires kit cable in L hip roll link | wire | L hip roll link | 1 | 0.86 | 0.86 | no | kit_cable_gpm |  |
| left_roll_to_pitch | printed | L hip pitch link | 1 | 19.94 | 19.94 | yes | slice |  |
| M2 servo-case screws (servo bag) x3 in L hip pitch link | screw | L hip pitch link | 1 | 0.82 | 0.82 | no | servo_bag |  |
| M2x6 roll_to_pitch screws (servo bag, HARDWARE_AUDIT.md B4) x2 in L hip pitch link | screw | L hip pitch link | 1 | 0.55 | 0.55 | no | servo_bag |  |
| M3 horn screws (M3x6/M3x5 mix) x8 in L hip pitch link | screw | L hip pitch link | 1 | 6.19 | 6.19 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3x6 horn centre screws (servo bag) x1 in L hip pitch link | screw | L hip pitch link | 1 | 0.78 | 0.78 | no | servo_bag |  |
| STS3215 C001 servo x1 | servo | L hip pitch link | 1 | 55.00 | 55.00 | yes | sts3215 |  |
| wires 22 AWG in L hip pitch link | wire | L hip pitch link | 1 | 1.01 | 1.01 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires 26 AWG in L hip pitch link | wire | L hip pitch link | 1 | 0.76 | 0.76 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires kit cable in L hip pitch link | wire | L hip pitch link | 1 | 1.01 | 1.01 | no | kit_cable_gpm |  |
| M3 heat-set inserts x4 in L thigh (knee servo) | insert | L thigh (knee servo) | 1 | 1.40 | 1.40 | no | insert | sites audit/sites.json, audit/sites_head.json |
| knee_to_ankle_left_sheet | printed | L thigh (knee servo) | 1 | 6.79 | 6.79 | yes | slice |  |
| knee_to_ankle_right_sheet | printed | L thigh (knee servo) | 1 | 6.15 | 6.15 | yes | slice |  |
| left_cache | printed | L thigh (knee servo) | 1 | 55.27 | 55.27 | yes | slice |  |
| leg_spacer | printed | L thigh (knee servo) | 1 | 7.01 | 7.01 | yes | slice |  |
| M2 servo-case screws (servo bag) x4 in L thigh (knee servo) | screw | L thigh (knee servo) | 1 | 1.09 | 1.09 | no | servo_bag |  |
| M3 horn screws (M3x6/M3x5 mix) x8 in L thigh (knee servo) | screw | L thigh (knee servo) | 1 | 6.19 | 6.19 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3 insert screws (M3x8/10/12 mix) x4 in L thigh (knee servo) | screw | L thigh (knee servo) | 1 | 3.57 | 3.57 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3x6 horn centre screws (servo bag) x1 in L thigh (knee servo) | screw | L thigh (knee servo) | 1 | 0.78 | 0.78 | no | servo_bag |  |
| STS3215 C001 servo x1 | servo | L thigh (knee servo) | 1 | 55.00 | 55.00 | yes | sts3215 |  |
| wires 22 AWG in L thigh (knee servo) | wire | L thigh (knee servo) | 1 | 0.97 | 0.97 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires 26 AWG in L thigh (knee servo) | wire | L thigh (knee servo) | 1 | 0.73 | 0.73 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires kit cable in L thigh (knee servo) | wire | L thigh (knee servo) | 1 | 0.99 | 0.99 | no | kit_cable_gpm |  |
| M3 heat-set inserts x4 in L shin (ankle servo) | insert | L shin (ankle servo) | 1 | 1.40 | 1.40 | no | insert | sites audit/sites.json, audit/sites_head.json |
| knee_to_ankle_left_sheet | printed | L shin (ankle servo) | 1 | 6.79 | 6.79 | yes | slice |  |
| knee_to_ankle_right_sheet | printed | L shin (ankle servo) | 1 | 6.15 | 6.15 | yes | slice |  |
| leg_spacer | printed | L shin (ankle servo) | 1 | 7.01 | 7.01 | yes | slice |  |
| M2 servo-case screws (servo bag) x4 in L shin (ankle servo) | screw | L shin (ankle servo) | 1 | 1.09 | 1.09 | no | servo_bag |  |
| M3 horn screws (M3x6/M3x5 mix) x8 in L shin (ankle servo) | screw | L shin (ankle servo) | 1 | 6.19 | 6.19 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3 insert screws (M3x8/10/12 mix) x4 in L shin (ankle servo) | screw | L shin (ankle servo) | 1 | 3.57 | 3.57 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3x6 horn centre screws (servo bag) x1 in L shin (ankle servo) | screw | L shin (ankle servo) | 1 | 0.78 | 0.78 | no | servo_bag |  |
| STS3215 C001 servo x1 | servo | L shin (ankle servo) | 1 | 55.00 | 55.00 | yes | sts3215 |  |
| wires 22 AWG in L shin (ankle servo) | wire | L shin (ankle servo) | 1 | 0.80 | 0.80 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires 26 AWG in L shin (ankle servo) | wire | L shin (ankle servo) | 1 | 0.73 | 0.73 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires kit cable in L shin (ankle servo) | wire | L shin (ankle servo) | 1 | 0.80 | 0.80 | no | kit_cable_gpm |  |
| Omron SS-01 foot switch x2 | electronics | L foot | 1 | 3.20 | 3.20 | no | omron_ss | seat: 2 slots in foot_top (MOUNTING.md) |
| M3 heat-set inserts x4 in L foot | insert | L foot | 1 | 1.40 | 1.40 | no | insert | sites audit/sites.json, audit/sites_head.json |
| foot_bottom_pla | printed | L foot | 1 | 9.47 | 9.47 | yes | slice |  |
| foot_bottom_tpu | printed | L foot | 1 | 17.57 | 17.57 | yes | slice |  |
| foot_side | printed | L foot | 1 | 12.98 | 12.98 | yes | slice |  |
| foot_top | printed | L foot | 1 | 23.06 | 23.06 | yes | slice |  |
| M3 horn screws (M3x6/M3x5 mix) x8 in L foot | screw | L foot | 1 | 6.19 | 6.19 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3 insert screws (M3x8/10/12 mix) x4 in L foot | screw | L foot | 1 | 3.57 | 3.57 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| wires 26 AWG in L foot | wire | L foot | 1 | 0.89 | 0.89 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| neck_left_sheet | printed | neck pitch link | 1 | 7.32 | 7.32 | yes | slice |  |
| neck_right_sheet | printed | neck pitch link | 1 | 6.37 | 6.37 | yes | slice |  |
| M2 servo-case screws (servo bag) x4 in neck pitch link | screw | neck pitch link | 1 | 1.09 | 1.09 | no | servo_bag |  |
| M3 horn screws (M3x6/M3x5 mix) x7 in neck pitch link | screw | neck pitch link | 1 | 5.41 | 5.41 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3x6 horn centre screws (servo bag) x1 in neck pitch link | screw | neck pitch link | 1 | 0.78 | 0.78 | no | servo_bag |  |
| STS3215 C001 servo x1 | servo | neck pitch link | 1 | 55.00 | 55.00 | yes | sts3215 |  |
| wires 20 AWG in neck pitch link | wire | neck pitch link | 1 | 1.45 | 1.45 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires 26 AWG in neck pitch link | wire | neck pitch link | 1 | 2.58 | 2.58 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires USB 2.0 cable in neck pitch link | wire | neck pitch link | 1 | 1.85 | 1.85 | no | usb_cable |  |
| wires kit cable in neck pitch link | wire | neck pitch link | 1 | 0.93 | 0.93 | no | kit_cable_gpm |  |
| head_pitch_to_yaw | printed | head pitch link | 1 | 15.14 | 15.14 | yes | slice |  |
| M3 horn screws (M3x6/M3x5 mix) x16 in head pitch link | screw | head pitch link | 1 | 12.38 | 12.38 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| wires 20 AWG in head pitch link | wire | head pitch link | 1 | 1.32 | 1.32 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires 26 AWG in head pitch link | wire | head pitch link | 1 | 2.35 | 2.35 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires USB 2.0 cable in head pitch link | wire | head pitch link | 1 | 1.69 | 1.69 | no | usb_cable |  |
| wires kit cable in head pitch link | wire | head pitch link | 1 | 0.65 | 0.65 | no | kit_cable_gpm |  |
| head_yaw_to_roll | printed | head yaw link | 1 | 27.22 | 27.22 | yes | slice |  |
| M2 servo-case screws (servo bag) x4 in head yaw link | screw | head yaw link | 1 | 1.09 | 1.09 | no | servo_bag |  |
| M3 horn screws (M3x6/M3x5 mix) x4 in head yaw link | screw | head yaw link | 1 | 3.09 | 3.09 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3x6 horn centre screws (servo bag) x1 in head yaw link | screw | head yaw link | 1 | 0.78 | 0.78 | no | servo_bag |  |
| STS3215 C001 servo x1 | servo | head yaw link | 1 | 55.00 | 55.00 | yes | sts3215 |  |
| wires 20 AWG in head yaw link | wire | head yaw link | 1 | 0.99 | 0.99 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires 26 AWG in head yaw link | wire | head yaw link | 1 | 1.77 | 1.77 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires USB 2.0 cable in head yaw link | wire | head yaw link | 1 | 1.27 | 1.27 | no | usb_cable |  |
| wires kit cable in head yaw link | wire | head yaw link | 1 | 0.82 | 0.82 | no | kit_cable_gpm |  |
| 1 W LED bead | electronics | head | 3 | 0.30 | 0.90 | no | led |  |
| 100 ohm LED resistor x3 | electronics | head | 1 | 0.75 | 0.75 | no | resistor |  |
| 2.2 kOhm foot pull-up x2 | electronics | head | 1 | 0.50 | 0.50 | no | resistor |  |
| 2x20 header on the Pi | electronics | head | 1 | 2.10 | 2.10 | no | header |  |
| Aurorad S5 reflector | electronics | head | 1 | 1.50 | 1.50 | no | reflector |  |
| Camera Module 3 | electronics | head | 1 | 4.00 | 4.00 | yes | camera3 | seat: 4 pilots in head.stl (audit/sites_head.json) |
| MAX98357A amplifier | electronics | head | 1 | 1.20 | 1.20 | no | max98357 | seat: head floor right of the speaker stand (MOUNTING.md) |
| Raspberry Pi Zero 2 W | electronics | head | 1 | 10.00 | 10.00 | yes | pi |  |
| SG90 antenna servo | electronics | head | 2 | 9.00 | 18.00 | yes | sg90 |  |
| eye glass disc | electronics | head | 2 | 2.08 | 4.16 | yes | eye_glass |  |
| microSD card | electronics | head | 1 | 0.50 | 0.50 | no | microsd |  |
| speaker Same Sky CMS0361KLX | electronics | head | 1 | 28.80 | 28.80 | yes | speaker | seat: speaker_interface (print STL bounds) |
| M3 heat-set inserts x12 in head | insert | head | 1 | 4.20 | 4.20 | no | insert | sites audit/sites.json, audit/sites_head.json |
| Pololu D30V30F5 5 V regulator | lab_added | head | 1 | 3.30 | 3.30 | no | d30v30f5 | seat: head floor below the Pi (MOUNTING.md; no placements.json entry, x and y of the Pi centre) |
| VHB 4950 tape under the regulator | lab_added | head | 1 | 0.32 | 0.32 | no | vhb_density |  |
| splices J5, JG (head 5 V and ground) | lab_added | head | 1 | 1.00 | 1.00 | no | splice |  |
| 6804ZZ bearing | mechanical | head | 1 | 26.90 | 26.90 | yes | bearing |  |
| bulb | printed | head | 2 | 2.04 | 4.08 | yes | slice | seat from print STL in the head.stl frame (audit/headgroup.py) |
| flash_light_module | printed | head | 1 | 8.08 | 8.08 | no | slice | seat from print STL in the head.stl frame (audit/headgroup.py) |
| flash_reflector_interface | printed | head | 1 | 2.27 | 2.27 | no | slice | seat from print STL in the head.stl frame (audit/headgroup.py) |
| head | printed | head | 1 | 232.46 | 232.46 | yes | slice |  |
| head_bot_sheet | printed | head | 1 | 56.79 | 56.79 | yes | slice |  |
| head_roll_mount | printed | head | 1 | 15.34 | 15.34 | yes | slice |  |
| left_antenna_holder | printed | head | 1 | 3.52 | 3.52 | yes | slice |  |
| left_eye | printed | head | 1 | 1.80 | 1.80 | yes | slice | seat from print STL in the head.stl frame (audit/headgroup.py) |
| right_antenna_holder | printed | head | 1 | 3.52 | 3.52 | yes | slice |  |
| right_eye | printed | head | 1 | 4.55 | 4.55 | yes | slice | seat from print STL in the head.stl frame (audit/headgroup.py) |
| speaker_interface | printed | head | 1 | 2.33 | 2.33 | yes | slice | seat from print STL in the head.stl frame (audit/headgroup.py) |
| speaker_stand | printed | head | 1 | 7.64 | 7.64 | yes | slice | seat from print STL in the head.stl frame (audit/headgroup.py) |
| M2 servo-case screws (servo bag) x4 in head | screw | head | 1 | 1.09 | 1.09 | no | servo_bag |  |
| M2.5x6 electronics screws x8 in head | screw | head | 1 | 3.75 | 3.75 | no | screw_mass |  |
| M2.5x8 eye screws (MOUNTING.md) x8 in head | screw | head | 1 | 4.23 | 4.23 | no | screw_mass |  |
| M2x4 camera screws (MOUNTING.md) x4 in head | screw | head | 1 | 0.94 | 0.94 | no | screw_mass |  |
| M3 insert screws (M3x8/10/12 mix) x12 in head | screw | head | 1 | 10.71 | 10.71 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3x6 horn centre screws (servo bag) x1 in head | screw | head | 1 | 0.78 | 0.78 | no | servo_bag |  |
| SG90 bag screws x3 (2 tab, 1 holder) | screw | head | 2 | 0.71 | 1.42 | no | screw_mass | UNVERIFIED: SG90 bag screw sizes not published (B5); taken as M2x4 pan head, |
| STS3215 C001 servo x1 | servo | head | 1 | 55.00 | 55.00 | yes | sts3215 |  |
| 2.54 mm housings and terminals at the Pi header | wire | head | 1 | 2.40 | 2.40 | no | terminal | UNVERIFIED: Molex 50-37-5033 or 2.54 mm housing |
| camera FPC cable 300 mm (D34) | wire | head | 1 | 1.34 | 1.34 | no | fpc | [L] twin/complete3d: 300 x 16 x 0.2 mm at the fpc density of this file (1.4 g/cm3), was 0.70 g for 150 mm |
| wires 20 AWG in head | wire | head | 1 | 4.09 | 4.09 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires 26 AWG in head | wire | head | 1 | 9.66 | 9.66 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires USB 2.0 cable in head | wire | head | 1 | 1.63 | 1.63 | no | usb_cable |  |
| wires kit cable in head | wire | head | 1 | 0.34 | 0.34 | no | kit_cable_gpm |  |
| roll_motor_bottom | printed | R hip roll link | 1 | 8.15 | 8.15 | yes | slice |  |
| roll_motor_top | printed | R hip roll link | 1 | 6.73 | 6.73 | yes | slice |  |
| M2 servo-case screws (servo bag) x6 in R hip roll link | screw | R hip roll link | 1 | 1.64 | 1.64 | no | servo_bag |  |
| M3 horn screws (M3x6/M3x5 mix) x4 in R hip roll link | screw | R hip roll link | 1 | 3.09 | 3.09 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3x6 horn centre screws (servo bag) x1 in R hip roll link | screw | R hip roll link | 1 | 0.78 | 0.78 | no | servo_bag |  |
| STS3215 C001 servo x1 | servo | R hip roll link | 1 | 55.00 | 55.00 | yes | sts3215 |  |
| wires 22 AWG in R hip roll link | wire | R hip roll link | 1 | 0.65 | 0.65 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires 26 AWG in R hip roll link | wire | R hip roll link | 1 | 0.47 | 0.47 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires kit cable in R hip roll link | wire | R hip roll link | 1 | 0.86 | 0.86 | no | kit_cable_gpm |  |
| right_roll_to_pitch | printed | R hip pitch link | 1 | 19.89 | 19.89 | yes | slice |  |
| M2 servo-case screws (servo bag) x3 in R hip pitch link | screw | R hip pitch link | 1 | 0.82 | 0.82 | no | servo_bag |  |
| M2x6 roll_to_pitch screws (servo bag, HARDWARE_AUDIT.md B4) x2 in R hip pitch link | screw | R hip pitch link | 1 | 0.55 | 0.55 | no | servo_bag |  |
| M3 horn screws (M3x6/M3x5 mix) x8 in R hip pitch link | screw | R hip pitch link | 1 | 6.19 | 6.19 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3x6 horn centre screws (servo bag) x1 in R hip pitch link | screw | R hip pitch link | 1 | 0.78 | 0.78 | no | servo_bag |  |
| STS3215 C001 servo x1 | servo | R hip pitch link | 1 | 55.00 | 55.00 | yes | sts3215 |  |
| wires 22 AWG in R hip pitch link | wire | R hip pitch link | 1 | 1.06 | 1.06 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires 26 AWG in R hip pitch link | wire | R hip pitch link | 1 | 0.77 | 0.77 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires kit cable in R hip pitch link | wire | R hip pitch link | 1 | 0.99 | 0.99 | no | kit_cable_gpm |  |
| M3 heat-set inserts x4 in R thigh (knee servo) | insert | R thigh (knee servo) | 1 | 1.40 | 1.40 | no | insert | sites audit/sites.json, audit/sites_head.json |
| knee_to_ankle_left_sheet | printed | R thigh (knee servo) | 1 | 6.79 | 6.79 | yes | slice |  |
| knee_to_ankle_right_sheet | printed | R thigh (knee servo) | 1 | 6.15 | 6.15 | yes | slice |  |
| leg_spacer | printed | R thigh (knee servo) | 1 | 7.01 | 7.01 | yes | slice |  |
| right_cache | printed | R thigh (knee servo) | 1 | 55.22 | 55.22 | yes | slice |  |
| M2 servo-case screws (servo bag) x4 in R thigh (knee servo) | screw | R thigh (knee servo) | 1 | 1.09 | 1.09 | no | servo_bag |  |
| M3 horn screws (M3x6/M3x5 mix) x8 in R thigh (knee servo) | screw | R thigh (knee servo) | 1 | 6.19 | 6.19 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3 insert screws (M3x8/10/12 mix) x4 in R thigh (knee servo) | screw | R thigh (knee servo) | 1 | 3.57 | 3.57 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3x6 horn centre screws (servo bag) x1 in R thigh (knee servo) | screw | R thigh (knee servo) | 1 | 0.78 | 0.78 | no | servo_bag |  |
| STS3215 C001 servo x1 | servo | R thigh (knee servo) | 1 | 55.00 | 55.00 | yes | sts3215 |  |
| wires 22 AWG in R thigh (knee servo) | wire | R thigh (knee servo) | 1 | 1.13 | 1.13 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires 26 AWG in R thigh (knee servo) | wire | R thigh (knee servo) | 1 | 0.81 | 0.81 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires kit cable in R thigh (knee servo) | wire | R thigh (knee servo) | 1 | 1.01 | 1.01 | no | kit_cable_gpm |  |
| M3 heat-set inserts x4 in R shin (ankle servo) | insert | R shin (ankle servo) | 1 | 1.40 | 1.40 | no | insert | sites audit/sites.json, audit/sites_head.json |
| knee_to_ankle_left_sheet | printed | R shin (ankle servo) | 1 | 6.79 | 6.79 | yes | slice |  |
| knee_to_ankle_right_sheet | printed | R shin (ankle servo) | 1 | 6.15 | 6.15 | yes | slice |  |
| leg_spacer | printed | R shin (ankle servo) | 1 | 7.01 | 7.01 | yes | slice |  |
| M2 servo-case screws (servo bag) x4 in R shin (ankle servo) | screw | R shin (ankle servo) | 1 | 1.09 | 1.09 | no | servo_bag |  |
| M3 horn screws (M3x6/M3x5 mix) x8 in R shin (ankle servo) | screw | R shin (ankle servo) | 1 | 6.19 | 6.19 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3 insert screws (M3x8/10/12 mix) x4 in R shin (ankle servo) | screw | R shin (ankle servo) | 1 | 3.57 | 3.57 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3x6 horn centre screws (servo bag) x1 in R shin (ankle servo) | screw | R shin (ankle servo) | 1 | 0.78 | 0.78 | no | servo_bag |  |
| STS3215 C001 servo x1 | servo | R shin (ankle servo) | 1 | 55.00 | 55.00 | yes | sts3215 |  |
| wires 22 AWG in R shin (ankle servo) | wire | R shin (ankle servo) | 1 | 0.84 | 0.84 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires 26 AWG in R shin (ankle servo) | wire | R shin (ankle servo) | 1 | 0.74 | 0.74 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |
| wires kit cable in R shin (ankle servo) | wire | R shin (ankle servo) | 1 | 0.80 | 0.80 | no | kit_cable_gpm |  |
| Omron SS-01 foot switch x2 | electronics | R foot | 1 | 3.20 | 3.20 | no | omron_ss | seat: 2 slots in foot_top (MOUNTING.md) |
| M3 heat-set inserts x4 in R foot | insert | R foot | 1 | 1.40 | 1.40 | no | insert | sites audit/sites.json, audit/sites_head.json |
| foot_bottom_pla | printed | R foot | 1 | 9.47 | 9.47 | yes | slice |  |
| foot_bottom_tpu | printed | R foot | 1 | 17.57 | 17.57 | yes | slice |  |
| foot_side | printed | R foot | 1 | 12.98 | 12.98 | yes | slice |  |
| foot_top | printed | R foot | 1 | 23.06 | 23.06 | yes | slice |  |
| M3 horn screws (M3x6/M3x5 mix) x8 in R foot | screw | R foot | 1 | 6.19 | 6.19 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| M3 insert screws (M3x8/10/12 mix) x4 in R foot | screw | R foot | 1 | 3.57 | 3.57 | no | screw_mass | sites audit/sites.json, audit/sites_head.json |
| wires 26 AWG in R foot | wire | R foot | 1 | 0.89 | 0.89 | no | wire_gpm | [L] wiring/netlist.yaml cut_mm, routed along the joints crossed |


Source keys:

- a2_density: [I] AZoM 304 stainless density 7.85 to 8.06 g/cm3, middle 7.95 used (https://www.azom.com/properties.aspx?ArticleID=965)
- adapter: [I] Waveshare Bus Servo Adapter (A) page, 'Weight: 0.016 kg' (https://www.waveshare.com/bus-servo-adapter-a.htm); may include packaging
- ato_fuse: UNVERIFIED: Littelfuse 0287015.PXCN ATO blade, no weight found
- awg: [I] Wikipedia American wire gauge, d = 0.127 mm x 92^((36 - n) / 39) (https://en.wikipedia.org/wiki/American_wire_gauge)
- bearing: UNVERIFIED: 6804ZZ mass not found (SKF, NSK, vendor pages refused or 404); CAD roll_bearing.stl solid ring x 7.85 g/cm3 = 26.9 g, an upper bound (real bearings have balls and a cage)
- bec: [I] Castle CC BEC Pro user guide 095-0047-00, 'Weight (w/o wires) 1 oz (29 grams)' (https://www.freakware.de/technik/CastleCreations/cc_bec_pro_user_guide.pdf)
- bec_out_leads: UNVERIFIED: CC BEC Pro output leads, length and gauge not published (netlist U1); 2 leads x 3 wires x 150 mm x 5.1 g/m (22 AWG silicone)
- bno055: [I] Adafruit 2472, 'Weight: 3g' (https://www.adafruit.com/product/2472)
- cable_ties: UNVERIFIED: a few small cable ties (USB slack coil, harness)
- camera3: UNVERIFIED: Raspberry Pi Camera Module 3 weight not found (raspberrypi.com refused curl, product brief and Adafruit 5657 give none); 25 x 24 x 11.5 mm module
- charger: [I] Amazon B0BJTW4QBR Adeept 2S USB-C charger, 'Item Weight 8.53 g' (https://www.amazon.com/dp/B0BJTW4QBR)
- cu_density: [I] Wikipedia Copper, density 8.935 g/cm3 at 20 C (https://en.wikipedia.org/wiki/Copper)
- d30v30f5: [I] Pololu 4892 D30V30F5 specs, 'Weight: 3.3 g' without headers (https://www.pololu.com/product/4892/specs)
- eye_glass: [I] Amazon B0C4H17QSH 60 discs, 'Item Weight 4.4 ounces' = 2.08 g per disc with packaging (upper bound) (https://www.amazon.com/dp/B0C4H17QSH)
- fpc: UNVERIFIED: Adafruit 3157 camera cable 150 x 16 x 0.2 mm (product page), about 1.4 g/cm3 laminate
- fuse_holder: UNVERIFIED: Littelfuse FHAC0001ZXJ body 50 x 17.2 x 17.2 mm with 2 x 90 mm 16 AWG leads (BOM L3); leads alone 2 x 0.09 m x 18.1 g/m = 3.3 g, body and cover about 4.7 g
- header: [I] Adafruit 2822 2x20 male header for the Pi Zero, 'Weight: 2.1g' (https://www.adafruit.com/product/2822)
- holder: UNVERIFIED: Amazon B09WCT8672 lists 'Item Weight 0.05 kg' with 'Unit Count 2 Count' (https://www.amazon.com/dp/B09WCT8672); 25 g assumes the 0.05 kg is for 2 holders; 50 g if it is one
- housing: UNVERIFIED: Molex 50-37-5033 or 2.54 mm housing
- insert: [I] CNC Kitchen US store product data for 'Heat Set Insert M3 x 5.7 - 100 pieces': variant weight 35 g per 100 (store shipping weight, bag included) (https://cnckitchenus.store/products/heat-set-insert-m3-x-5-7-100-pieces.js)
- iso4762: [I] ISO 4762 / DIN 912 dimensions dk, k, s, t (https://www.fasteners.eu/standards/DIN/912/)
- kit_cable_gpm: UNVERIFIED: STS3215 kit cable conductor not published (power_path_sim.py assumes 26 AWG); 26 AWG copper 1.15 g/m plus PVC 1.1 mm OD at 1.4 g/cm3 = 2.2 g/m per conductor
- led: UNVERIFIED: uxcell 1 W COB bead B07DHB13J4, listing gives no weight
- max98357: [I] Adafruit 3006, 'Product Weight: 1.2g' (https://www.adafruit.com/product/3006)
- microsd: UNVERIFIED: microSD card, no weight on the SanDisk listing read
- omron_ss: [I] Omron SS datasheet en-ss.pdf, 'Weight Approx. 1.6g (pin plunger models)' (https://omronfs.omron.com/en_US/ecb/products/pdf/en-ss.pdf)
- p30b: [I] Molicel INR-18650-P30B product data sheet v1.0, 'Weight 47 g (Max)' (https://cdn.shopify.com/s/files/1/0481/9678/0183/files/Product-Data-Sheet-of-INR-18650-P30B-80111-2.pdf); 44.7 to 45.0 g measured in a UN38.3 report (https://www.18650batterystore.com/products/molicel-p30b-18650-3000mah-36a-battery)
- panel_switch: UNVERIFIED: stock panel slide switch, no datasheet part yet (BOM 10b); CAD power_switch.stl 0.96 cm3 x about 2 g/cm3 (metal and plastic)
- pi: [I] Adafruit 5291 Raspberry Pi Zero 2 W, 'Product Weight: 10.0g' (https://www.adafruit.com/product/5291)
- reflector: UNVERIFIED: Aurorad S5 20 x 15 mm aluminium reflector, Amazon page returned an error
- resistor: UNVERIFIED: 1/4 W through-hole resistor, no weight on the Adafruit 2782 or SparkFun PRT-14493 pages
- screw_mass: [L] computed in sim/mass_budget.py from ISO 4762 sizes and the A2 density: M3x5 0.73 g, M3x6 0.78 g, M3x8 0.87 g, M3x10 0.96 g, M3x12 1.05 g, M2.5x6 0.47 g, M2.5x8 0.53 g, M2.5x10 0.59 g, M2x6pan 0.27 g, M2x5pan 0.25 g, M2x4pan 0.24 g
- servo_bag: UNVERIFIED: STS3215 bag screws (B2, sizes not published); taken as M2x6 pan head, D18 gives the M2 pan head as 4.0 x 1.6 mm; the horn centre screw is M3x6 (Feetech spec item 6-13) taken as an M3x6 SHCS
- sg90: [I] Amazon B072V529YD Miuzei SG90, 'Item Weight 9 g' (https://www.amazon.com/dp/B072V529YD), lead included
- silicone_density: [I] Wikipedia Silicone rubber, density 0.95 to over 1.20 g/cm3, high end used (https://en.wikipedia.org/wiki/Silicone_rubber)
- slice: [L] print/SLICE_SUMMARY.md per-part table: 'g each' minus 'support g each' (support is removed after printing; skirt is 1 loop, 1 layer, under 0.1 g)
- solder_heatshrink: UNVERIFIED: solder and heat shrink on about 60 joints outside the splices, about 0.07 g each
- speaker: [I] Same Sky CMS0361KLX datasheet, 'weight 28.8 g' (https://www.sameskydevices.com/product/resource/cms0361klx.pdf)
- splice: UNVERIFIED: one solder splice with adhesive heat shrink
- steel_density: [I] AZoM 304 stainless density 7.85 to 8.06 g/cm3 (https://www.azom.com/properties.aspx?ArticleID=965); 7.85 used for bearing steel
- sts3215: [I] Feetech STS3215 C001 product specification 2023-06-23, item 6-8 'Weight 55 +/- 1 g' (copy at https://download.kamami.pl/p1198708-STS3215-C001-20230624.pdf)
- sw2815: [I] Pololu 2815 specs, 'Weight: 2.6 g' without the optional connectors (https://www.pololu.com/product/2815/specs)
- tenergy_bms: UNVERIFIED: Tenergy 32175 page gives no weight; 34 x 16 x 4.5 mm box x 1.2 g/cm3 (median bounding-box density of the 5 small boards above with a published weight: Pi 0.97, MAX98357A 1.16, D30V30F5 1.03, 2815 1.37, BNO055 about 1.9 g/cm3)
- terminal: UNVERIFIED: Molex 08-70-1040 or 2.54 mm crimp terminal
- usb_cable: [I] Adafruit 3878 USB C to Micro B 0.9 m, 'Product Weight: 20.0g' (https://www.adafruit.com/product/3878)
- vhb_density: UNVERIFIED: 3M VHB 4950 foam density about 0.8 g/cm3 (3M data sheet not read); 1.1 mm thick, 19 mm wide (BOM 29)
- wire_gpm: [L] computed: 16 AWG 18.1 g/m, 20 AWG 6.9 g/m, 22 AWG 5.1 g/m, 26 AWG 3.1 g/m; check: the BNTECHGO 16 AWG listing gives 'Item Weight 11.2 ounces' for 50 ft = 20.8 g/m with packaging
- wire_od: [I] BNTECHGO listings, outside diameter +/- 0.1 mm: 16 AWG 3.0 (https://www.amazon.com/dp/B01MCRY7OT), 20 AWG 1.8 (https://www.amazon.com/dp/B01F8PO5XE), 22 AWG 1.7 (https://www.amazon.com/dp/B09X4KY56S), 26 AWG 1.5 mm (https://www.amazon.com/dp/B08F9CF85N)
- xt30_pair: [I] Amazon B08P5HVMYT Amass XT30U 10 pairs, 'Item Weight 0.317 ounces' = 9.0 g for 10 pairs (https://www.amazon.com/dp/B08P5HVMYT)

Hardware counts placed at hole sites: M2 servo-case screws (servo bag) 66, M2.5x10 lid screws 4, M2.5x6 electronics screws 17, M2.5x8 eye screws (MOUNTING.md) 8, M2x4 camera screws (MOUNTING.md) 4, M2x6 roll_to_pitch screws (servo bag, HARDWARE_AUDIT.md B4) 4, M3 heat-set inserts 58, M3 horn screws (M3x6/M3x5 mix) 99, M3 insert screws (M3x8/10/12 mix) 58, M3x6 horn centre screws (servo bag) 14

## V1 track 2 recount (2026-11-04, calc only; twin/assembly/asm_calc.py, asm_calc.json)
Scope: the pieces the model did not count or counted by an older list. The model itself (sim/mass_budget.py) is not changed; the lead decides the gym model update.

| Item | Change g | Source |
|---|---|---|
| 286 driven screws (342 fitted less the 56 factory case screws inside the servos): 174.3 g against 175.3 g for the 274 modelled | -1.0 | fasteners.json; the ISO 4762 and pan head formulas and the A2 density of sim/mass_budget.py |
| 16 eye washers, ISO 7092 2.7 x 5.0 x 0.3 mm | +0.5 | BOM 17l, A2 density |
| D30: Pololu 2813 2.7 g for the 2815 2.6 g | +0.1 | Pololu specs |
| D30: OFF wire GPIO26 to the 2813, 26 AWG, 531.7 mm (the P13 route) | +1.6 | wiring/netlist.yaml P13 rule length, the 26 AWG g/m of sim/mass_budget.py |
| D30: printed button plate, 535 mm3 | +0.6 | CAD volume times the sliced bulb ratio (print/SLICE_SUMMARY.md) |
| D38 screw cut (V1 screws job): -25 screws (10 x M3x8, 6 x M2.5x6, 4 x M2.5x8, 2 x M2.5x5, 1 x M2.5x10, 2 x M2x5), -10 inserts (0.35 g each, the INSERT_G source), -8 washers; +5.6 cm3 PLA in the tongue, lips and ribs | -13.8 | calc only: screws 14.23 g from the screw_mass sizes (no size for M2.5x5, M2x5: BLOCKER); washers not counted (no washer mass in this budget: BLOCKER); the 3 changed parts at their re-sliced grams less support (slice.py, D22): +3.9 g on the robot. Not yet in 'Our build': the sim owner re-runs sim/mass_budget.py |
| Cable ties (D25): 78 fitted at most against the 1.0 g modelled | 0 to +31.5 | upper bound 0.417 g per tie, the gross weight of a 142 mm Panduit PLT1.5M-C (TME); trimmed tails weigh less |
| 55 adhesive tie mounts (BOM 34, 34b) | not counted | BLOCKER: no published mass; weigh 10 of each on arrival |

New total: 2654.7 g counted for sure (+1.9 g), up to 2686.2 g with the tie upper bound (+33.4 g, +1.26 %), plus the tie mounts. Over 1 % only at the tie bound; if the weighing confirms it, every result run at 2652.8 g moves: the stock policy at our mass (sim/ADDED_MASS_SIM.md), the structure twin loads, the track 1 and 1b shove currents (B47), the thermal twin, and the RunPod training mass (STATE.md open question 1). D29 (two LEDs per eye) was reverted (D33), so the LEDs, the side lamp prints and E5 stay as modelled.
