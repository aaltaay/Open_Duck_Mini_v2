# GAPS

## A. Gaps for building it as designed

A1. Servo variant: resolved to STS3215 7.4 V 1:345 (C001), about 85% confidence (SERVO_DEEP_DIVE.md). Not confirmed by apirrone in writing, and his servo firmware version is unknown. Issue #48 (open) still reports poor tracking and feet that barely lift. The likely causes are servo register or firmware state, supply sag or mislabeled 12 V units, not the BOM variant. The C001 reaches about 5.45 rad/s at 7.4 V, matching the 5.24 rad/s in sim. Bench test before the full build.

A2. Over-voltage. A 2S pack charges to 8.4 V, the STS3215 C001 is rated 6 to 7.4 V, and Feetech excludes over-voltage damage from warranty (Feetech after-sales page, REFERENCES.md). Upstream issue 51 asks about 8.4 V on 7.4 V servos; it was closed on 2026-07-19 with no reply. The Waveshare adapter (A) is specced for 9 to 12.6 V input and passes voltage straight to the bus.
Lab change (D3 decided 2026-11-01): Castle CC BEC Pro set to 7.2 V feeds the bus (POWER.md). Open: BEC dropout behavior and setpoint accuracy not published, measure on the bench.

A3. Battery holder current. Upstream issue 51 asks whether the spring holder contacts and thin wires limit current for 14 servos (a question, not a finding). No fuse anywhere in the power path.
Lab change: 15 A ATO fuse (Littelfuse 0287015.PXCN in FHAC0001ZXJ) right after BMS P+, 16 AWG harness. Holder still open: measure drop at 10 A, replace with a spot-welded pack if over about 0.3 V (POWER.md section 5).

A4. No real schematic. Wiring is a block diagram (docs/open_duck_mini_v2_wiring_diagram.png), a pictorial of the head (wiring.png) and a Pi pin table. No wire gauges, connector part numbers or fuse. The UBEC is "stuffed in the back" (issue #1).
Lab answer: WIRING.md plus wiring/odm_v2_wiring.svg and .png, with gauges, connectors, part numbers, and upstream vs inferred marked. Upstream pin table and Runtime code disagree on eyes and antennas (left and right swapped).

A5. Fasteners not counted. assembly_guide.md says "X m3 screws (TODO : add the exact number)". M3x6 and M3x10 are named, plus plastic screws from the servo kits. M3 insert length and diameter not stated. RESOLVED 2026-11-01 by measurement: 58 M3 inserts (bore 3.9 to 4.2, CNC Kitchen M3x5.7), 193 screws to buy by size, 80 from the servo bags, 0 nuts, 0 washers. See HARDWARE_AUDIT.md. Still open: servo bag split by size (B2), 6 holes with no anchor (B4, B5).

A6. Bearings. RESOLVED 2026-11-01 by measurement: the CAD bearing model is 19.99 ID x 32.19 OD x 7.0 mm (the earlier 32x32x7 note was wrong), seats measure 32.19 mm in trunk_bottom (2) and head (1). That is 6804ZZ (20x32x7), confirmed against the ISO 15 dimension table. See PRINT_CHECK.md.

A7. Assembly guide is incomplete: servo driver board mount "TODO take a photo", expression features "TODO add instructions". Runtime docs have TODOs for the udev rule and for flashing offsets, and prepare_robot.md is outdated.

A8. Print guide error: the bulb part is listed x1 but 2 are needed (issue #26). TPU hardness not stated. Confirmed by geometry: the assembly uses 2 bulb copies (sites_head.json, one per eye). TPU hardness still open (B26).

A9. BOM is in EUR with amazon.fr, alibaba and aliexpress links. Several lines name no exact model (switch, charger, holder, wire, SD card). Chinese-language BOM and guide are on feishu.

A10. Pi Zero 2 W is out of stock at Adafruit and PiShop.us on 2026-11-01.

A11. Support is mainly on Discord (issue #29 reports a phone number requirement). Tnkr hosts the step-by-step guide.

A12. Camera and microphone are in the expression BOM but not integrated in the runtime.

A13. Policy training data and exact training config for the shipped ONNX are not fully published (issue #43, not re-verified).

## B. Gaps against lab rules

B1. Wiring access. Ahmed requires full wiring, cabling and schematic access. Only diagrams exist (A4). We must draw our own schematic from the CAD and pin table.
Done 2026-11-01 as a block-level schematic (WIRING.md). Head chain branch point and the Pi 5 V feed point are inferred.

B2. Servo durability. No continuous duty or thermal spec for STS3215. Warranty on motor and gears is 6 months. Expect wear in knees and hips. No published lifetime data.

B3. Battery and BMS. Generic 2S BMS with no comms and no fuel gauge. Charging is a manual USB-C plug. check_voltage.py reads bus voltage only.

B4. IMU and compute. BNO055 (Adafruit, US) is fine. Pi Zero 2 W (512 MB) has no spare headroom for vision and is in short supply.

B5. Self docking: missing. No AprilTag code, no camera in the build, no pogo pins, no dock, no return at about 20% battery. Needs a camera, a charge contact design in the feet or back, a dock and a battery estimate.

B6. Get up after falls: missing. Training only terminates the episode on a fall. No get-up policy or motion.

B7. Stairs: not possible. EXEMPT by Ahmed on 2026-11-01, no action needed. Lab stair rise is 197 mm (254 mm tread, 15 steps). Thigh is about 79 mm and shin about 79 mm. Hip pitch axis is about 220 mm above ground with straight legs and about 150 mm in the walking crouch. The rise is about 90% of the fully straight leg and about 130% of walking hip height. The 104 mm foot fits the tread, but the robot cannot lift a foot onto the step. Even a scaled design would need roughly 2x leg length.

B8. Sim model: present. MJCF in Open_Duck_Playground (playground/open_duck_mini_v2/xmls/open_duck_mini_v2.xml, plus a backlash variant) and URDF plus MJCF in Open_Duck_Mini/mini_bdx/robots/open_duck_mini_v2. Actuator model from BAM (kp 13.37, forcerange 3.23 Nm).

B9. Trained policy: present for walking (BEST_WALK_ONNX.onnx, BEST_WALK_ONNX_2.onnx). Not tested on hardware by us. Trained against the BAM model of apirrone's 7.4 V 1:345 servos (A1), so faster variants would not match it.

B10. Chinese parts rule. STS3215 is borderline (partial spec, short warranty, sim yes). Waveshare adapter, BMS, UBEC, charger, holder and SG90s fail (no spec or warranty).

B10a. Bus servos only rule (added 2026-11-01). The 2 SG90-class antenna servos (BOM.md row 14) are PWM hobby servos, not bus servos, so they break the lab "bus servos only" rule. This is a lab-rule gap, not a defect of the upstream design: the stock build keeps them because Ahmed chose to build v2 stock first (2026-11-01 12:53 PM ET, DECISIONS.md). A bus-servo swap (for example 2 more Feetech STS-series bus servos on the neck chain) belongs to the later lab step, together with docking and get-up.

B11. Non-US sellers. Upstream BOM links are EU and China only. US equivalents found for every line (BOM.md). Nothing is sold only through Discord.

B12. Licensing. Runtime, Playground and reference motion generator have no license file.


A12. Adapter (Waveshare bus servo adapter, board.stl on trunk_top) has only 2 servo sockets (H3, H5, wired in parallel), but 3 chains leave it (left leg, right leg, neck). No Y-lead is needed: the neck chain hangs off the left ankle's free bus port through one made lead S14 (Tnkr wiring of the upstream assembly, no splitter; CABLE_MAP.md). B19 cleared 2026-11-01.
## C. Update 2026-11-01 about 6:25 PM ET (print-readiness pass, DECISIONS.md D1 to D12)
- A1 servo variant: decided C001, bench test 1 servo first (D1, D2). Issue #48 stays on watch.
- A2 over-voltage: unchanged, Castle CC BEC Pro at 7.2 V (D3).
- A3 battery holder current: sim walking mean at the pack is about 4.2 A (sim/CURRENT_BUDGET.md, sim pass only), so the 10 A holder drop test keeps 2 x margin. Fuse 15 A stays; BMS now Tenergy 32175 with a published 22 +/- 5 A over-current trip (D10).
- A4 schematic: being redrawn as a real schematic plus a harness drawing (wiring/, WIRING.md, CABLE_MAP.md).
- A10 Pi Zero 2 W stock: decided (D7). In-stock fallback CanaKit kit with pre-soldered header; the header fits in the head (44.3 mm free below the Pi).
- B3 battery and BMS: BMS has a spec table now (Tenergy). Still no fuel gauge or comms; battery level for docking comes later (lab step with docking).
- B10 Chinese parts rule: generic UBEC replaced by a Pololu regulator (US), generic BMS replaced by the Tenergy board (US seller, full spec table), main switch is a Pololu 2815 (US). Still flagged: Feetech STS3215 (accepted for the stock build with a bench thermal test, D2), Waveshare adapter, USB-C charger, cell holder, SG90 antenna servos (B10a).
- B12 licensing: no message sent (D6). Runtime and Playground used unmodified at pinned commits and not republished.
- New, from the free-space search (D11): every part not in the CAD has a measured seat. No STL edit is needed for the stock build plus the lab power changes.
- Upstream issues: every issue and PR in the 4 upstream repos is triaged in UPSTREAM_ISSUES.md, with the gaps that affect this build listed first.
- New 2026-11-01 6:56 PM ET (exploded-view check): the 2 antennas (antenna.stl: a 150 mm rod, 1.8 mm across, with a 3.8 mm tip bead, measured by the print package check) are in the URDF but not in print/, the print guide or the BOM. Plan: print them in PLA from the URDF mesh as an optional expression part, with spares, since a TPU rod this thin would sag (print/PRINT_PLAN.md).
- New 2026-11-01 6:56 PM ET (parts check): the Waveshare adapter marks "MAX:6A" at its servo header and is specced for 9 to 12.6 V input. Answer D15: servo power bypasses the adapter (BEC -> belly splices -> one power lead per chain), the adapter carries USB data only.
- New 2026-11-01 6:56 PM ET (parts check): the Tenergy BMS over-discharge cut (2.40 V per cell) is below the Molicel P30B minimum (2.5 V), and Castle does not publish the CC BEC Pro minimum input voltage. Answer: software cut-off at servo Present Voltage 6.0 V (TEST_PLAN.md section 11) and a BEC input sweep on the bench before assembly (TEST_PLAN.md section 4).
