# GAPS

## A. Gaps for building it as designed

A1. Servo variant: resolved to STS3215 7.4 V 1:345 (C001), about 85% confidence (SERVO_DEEP_DIVE.md). Not confirmed by apirrone in writing, and his servo firmware version is unknown. Issue #48 (open) still reports poor tracking and feet that barely lift. The likely causes are servo register or firmware state, supply sag or mislabeled 12 V units, not the BOM variant. The C001 reaches about 5.45 rad/s at 7.4 V, matching the 5.24 rad/s in sim. Bench test before the full build.

A2. Over-voltage. A 2S pack charges to 8.4 V, the STS3215 C001 is rated 6 to 7.4 V, and Feetech excludes over-voltage damage from warranty (issue #51). The Waveshare adapter (A) is specced for 9 to 12.6 V input and passes voltage straight to the bus.

A3. Battery holder current. Spring holder contacts limit current for 14 servos (issue #51). No fuse anywhere in the power path.

A4. No real schematic. Wiring is a block diagram (docs/open_duck_mini_v2_wiring_diagram.png), a pictorial of the head (wiring.png) and a Pi pin table. No wire gauges, connector part numbers or fuse. The UBEC is "stuffed in the back" (issue #1).

A5. Fasteners not counted. assembly_guide.md says "X m3 screws (TODO : add the exact number)". M3x6 and M3x10 are named, plus plastic screws from the servo kits. M3 insert length and diameter not stated.

A6. Bearings not named. BOM says 3 bearings. The CAD bearing model is 32x32x7 mm, so 6804ZZ (20x32x7) is inferred, not confirmed.

A7. Assembly guide is incomplete: servo driver board mount "TODO take a photo", expression features "TODO add instructions". Runtime docs have TODOs for the udev rule and for flashing offsets, and prepare_robot.md is outdated.

A8. Print guide error: the bulb part is listed x1 but 2 are needed (issue #26). TPU hardness not stated.

A9. BOM is in EUR with amazon.fr, alibaba and aliexpress links. Several lines name no exact model (switch, charger, holder, wire, SD card). Chinese-language BOM and guide are on feishu.

A10. Pi Zero 2 W is out of stock at Adafruit and PiShop.us on 2026-11-01.

A11. Support is mainly on Discord (issue #29 reports a phone number requirement). Tnkr hosts the step-by-step guide.

A12. Camera and microphone are in the expression BOM but not integrated in the runtime.

A13. Policy training data and exact training config for the shipped ONNX are not fully published (issue #43, not re-verified).

## B. Gaps against lab rules

B1. Wiring access. Ahmed requires full wiring, cabling and schematic access. Only diagrams exist (A4). We must draw our own schematic from the CAD and pin table.

B2. Servo durability. No continuous duty or thermal spec for STS3215. Warranty on motor and gears is 6 months. Expect wear in knees and hips. No published lifetime data.

B3. Battery and BMS. Generic 2S BMS with no comms and no fuel gauge. Charging is a manual USB-C plug. check_voltage.py reads bus voltage only.

B4. IMU and compute. BNO055 (Adafruit, US) is fine. Pi Zero 2 W (512 MB) has no spare headroom for vision and is in short supply.

B5. Self docking: missing. No AprilTag code, no camera in the build, no pogo pins, no dock, no return at about 20% battery. Needs a camera, a charge contact design in the feet or back, a dock and a battery estimate.

B6. Get up after falls: missing. Training only terminates the episode on a fall. No get-up policy or motion.

B7. Stairs: not possible. EXEMPT by Ahmed on 2026-11-01, no action needed. Lab stair rise is 197 mm (254 mm tread, 15 steps). Thigh is about 79 mm and shin about 79 mm. Hip pitch axis is about 220 mm above ground with straight legs and about 150 mm in the walking crouch. The rise is about 90% of the fully straight leg and about 130% of walking hip height. The 104 mm foot fits the tread, but the robot cannot lift a foot onto the step. Even a scaled design would need roughly 2x leg length.

B8. Sim model: present. MJCF in Open_Duck_Playground (playground/open_duck_mini_v2/xmls/open_duck_mini_v2.xml, plus a backlash variant) and URDF plus MJCF in Open_Duck_Mini/mini_bdx/robots/open_duck_mini_v2. Actuator model from BAM (kp 13.37, forcerange 3.23 Nm).

B9. Trained policy: present for walking (BEST_WALK_ONNX.onnx, BEST_WALK_ONNX_2.onnx). Not tested on hardware by us. Trained against the BAM model of apirrone's 7.4 V 1:345 servos (A1), so faster variants would not match it.

B10. Chinese parts rule. STS3215 is borderline (partial spec, short warranty, sim yes). Waveshare adapter, BMS, UBEC, charger, holder and SG90s fail (no spec or warranty).

B11. Non-US sellers. Upstream BOM links are EU and China only. US equivalents found for every line (BOM.md). Nothing is sold only through Discord.

B12. Licensing. Runtime, Playground and reference motion generator have no license file.
