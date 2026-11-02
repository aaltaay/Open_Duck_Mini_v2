# SERVO DEEP DIVE: which STS3215 does the Open Duck Mini v2 use, and what is issue #48?

Date: 2026-11-01 (ET). Upstream pin: apirrone/Open_Duck_Mini b23317a485b3cec7d8417f352478778b3475173c, Open_Duck_Playground b9be205ac64488c23504ca42e5ec790337adeec3, Open_Duck_Mini_Runtime 376de65435c93486347cd601a31aa96951799896, Rhoban/bam b9e11118e17fe8ec803d430202f6fcf31d57901e.
Nothing was posted, commented, emailed or bought.

## 1. Conclusion

- Leg servo variant: Feetech STS3215 7.4 V, 1:345 gear, "19 kg.cm" (sold as STS3215-C001). Confidence: high, about 85%.
- Issue #48 is very unlikely to be a "wrong variant in the BOM" problem. The C001 datasheet no-load speed is 52 RPM = 5.45 rad/s at 7.4 V, not 2.7 rad/s. That matches the 5.24 rad/s used in sim, which apirrone says came from system identification of his own servos. The 2.7 rad/s figure in #48 does not appear in any Feetech datasheet we found.
- The #48 symptom (hip roll tracks, hip pitch, knee and ankle reach only 31 to 49% of command, even suspended) is the signature of a joint speed limit on the fast joints, with real speed about half of the modelled speed. The likely causes are servo setup or supply, not gear ratio. In order of likelihood: (1) servo register state or firmware version differs from what BAM identified; (2) supply voltage sag at the servo; (3) a mislabeled or 12 V unit (a 12 V C018 run at 7.4 V gives about 2.9 rad/s, very close to the 2.7 rad/s reported); (4) loop timing and mechanics. Details in section 5.
- What to buy or plan: buy the C001 (7.4 V, 1:345, 19 kg.cm) as the BOM says, 14 pieces plus 1 or 2 spares. Do not buy C044 or C046 for the legs. The shipped policies were trained against a model of the 1:345 servo, and a faster servo would make the policy and the sim not match. Before assembly, bench test one servo (section 6).

## 2. Variant facts (datasheets)

| Variant | Ratio | Rated V | No-load speed | rad/s | Stall torque | Source |
|---|---|---|---|---|---|---|
| C001 | 1:345 | 7.4 V (6 to 7.4) | 0.192 s/60 deg = 52 RPM @7.4V; 42 RPM @6V | 5.45 @7.4V, 4.40 @6V | 19 to 19.5 kg.cm @7.4V (1.91 Nm), 2.5 A | Alibaba Feetech table, Waveshare/Feetech docs |
| C044 | 1:191 | 7.4 V | 0.116 s/60 deg = 86 RPM | 9.0 | listed 27.4 kg.cm (looks suspect), 3.8 A | Alibaba Feetech table |
| C046 | 1:147 | 7.4 V (5 to 8.4) | 0.094 s/60 deg = 106 RPM @7.4V | 11.1 | 14.4 kg.cm @7.4V, Kt 4.36 kg.cm/A | Akizuki C046 spec PDF |
| C018 | 1:345 | 12 V | 0.222 s/60 deg = 45 RPM @12V | 4.7 @12V, about 2.9 @7.4V | 30 kg.cm @12V | Feetech table |
| Waveshare ST3215-HS | lower ratio, 12 V class | 6 to 12.6 V | 106 RPM @12V | 11.1 @12V, about 6.8 @7.4V | 20 kg.cm @12V | Waveshare product page |

## 3. Evidence for the 1:345 7.4 V servo

E1. BOM. bom.csv line 18: "Feetech 7.4v STS 3215", link to the Alibaba "Robot-Servo-STS3215-7-4V-19kg" listing, note "Be sure to buy the 7.4v ones, also called 19kg.cm". The note lives in the Google Sheet BOM; no git commit ever changed the servo spec text (git log -S on all repos).

E2. BAM identification was done on apirrone's own duck servos.
- Rhoban/bam commit b1769a6 (2025-03-17, author apirrone) added params/feetech_sts3215_7_4V/m1.json and bam/feetech/README.md ("Feetech sts3215 7.4V, Authors Antoine Pirrone, Gregoire Passault").
- Gregwar (BAM maintainer) in bam issue #13 (2026-08-10): "The data were provided by @apirrone for the open duck mini".
- m1.json: kt 1.21164, R 2.67617, armature 0.028403, friction_base 0.052393, friction_viscous 0.059085.

E3. The sim actuator is that model, exactly. BAM maps to MuJoCo as damping = kt^2/R + friction_viscous, forcerange = vin * kt/R, kp = vin * kp_fw * 0.166 * kt/R (vin 7.4, kp_fw 32). From m1.json: damping 0.608, forcerange 3.35, kp 17.80. The Playground joints_properties.xml at that time had damping 0.60, frictionloss 0.052, armature 0.028, kp 17.8, forcerange 3.35. apirrone confirmed the unit mapping in Open_Duck_Mini issue #20 (2025-04-17): "the 17.8 in mujoco corresponds to 32 in the motors firmware units". Later commits (07c1f5c, d8d15f6, f698836, March 2025) moved to the re-identified values with the firmware velocity limit: damping 0.56, forcerange 3.23, kp 13.37 (current main).

E4. The implied speed matches C001 and rules out the faster ratios. No-load speed of the identified model = (vin * kt/R - friction_base) / (kt^2/R + friction_viscous) = (3.350 - 0.052) / 0.608 = 5.43 rad/s (51.8 RPM). C001 datasheet: 5.45 rad/s at 7.4 V. C044 would be 9.0, C046 11.1, Waveshare HS about 6.8 at 7.4 V. The current BAM st3215 models m1 to m6 (commit 31e5b97, 2026-08-12) give kt 1.17 to 1.28, R 2.45 to 2.75 and fitted max_velocity 5.07 to 5.30 rad/s, again a 50 RPM class servo.

E5. The 5.24 rad/s in sim and runtime comes from that identification. Playground joystick.py max_motor_velocity = 5.24 with target clipping (commit 07c1f5c, "motor velocity limit test", 2025-03-20). BAM commit 5b0486e (2025-03-20, Passault) "adding velocity limit in feetech": default_max_velocity 3400 steps/s = 5.215 rad/s. Runtime issue #7 (2025-04-11), apirrone: "we are using 7.4v so the rpm is higher, but the value you see (5.24) actually comes from system identification!" with a link to the BAM feetech_sts3215_7_4V m1.json.

E6. apirrone separates 7.4 V and 12 V units. Open_Duck_Mini issue #21 (2025-04-19): "12v servos and the 7.4v ones are different ... BEST_WALK_ONNX2.onnx ... was trained for 7.4v servos".

E7. BAM torque scale. The identified stall torque (3.35 Nm) is about 1.75x the C001 datasheet (1.91 Nm) and about 2.4x the C046 datasheet (1.41 Nm). The identified kt (1.21) is about 1.6x the C001 datasheet Kt and about 2.8x the C046 Kt. Both ratios are closer to C001. BAM kt is a fitted output-side constant, so this is supporting evidence only.

## 4. Evidence against, and what is still unknown

- Open_Duck_Mini issue #5 (2025-03-15), MankaranSingh (not a repo collaborator): "make sure to buy the ST3215-HS (106 RPM) version ... @apirrone is far ahead with sim2real on ST3215-HS servos". This is two days before apirrone published the 7.4 V BAM model, and apirrone never confirmed it. The Waveshare ST3215-HS is a 12 V class servo (106 RPM at 12 V, about 6.8 rad/s at 7.4 V), which fits the identified 5.43 rad/s worse than the C001 does. This is the main reason confidence is about 85% and not higher.
- Unknown: a photo of the label or the exact Feetech suffix on apirrone's leg servos; the servo firmware version he identified and trained with (new_record_data.py stores fw_version in file names, so it mattered to him); the supply voltage during identification; whether he mixed variants (for example faster units in some joints).
- Reachy Mini does not help: its current hardware is Dynamixel XL330 and XC330 (Hugging Face hardware datasheet). Older controller code had STS3215 for antennas and base with no variant named.
- Discord is the main support channel and was not readable from here, so any answer apirrone gave there is not included.

## 5. Issue #48 analysis

What #48 shows (redEddie, 2026-06-11, still open, no maintainer reply). Same policy and reference in sim and on hardware. Hip roll tracks about 1.0 on hardware. Hip pitch 0.35 to 0.37, knee 0.31 to 0.44, ankle 0.46 to 0.49. Sim also under-tracks the knee (0.47 to 0.65). It persists when suspended and unloaded. Sim foot clearance is 12 to 15 mm; real feet barely leave the ground. The same "can't lift its feet" symptom is in Open_Duck_Playground issue #5 (apirrone pointed to Discord). In Open_Duck_Mini issue #52 a builder swapped the knees to 12 V 30 kg units and still lacks foot clearance.

Speed demand of the reference motion (our computation from Runtime scripts/polynomial_coefficients.pkl, gait period 0.54 s, 50 fps). Peak joint velocity in the forward walk references:

| Joint | Range (rad) | Peak velocity (rad/s) |
|---|---|---|
| hip roll | about 0.25 | about 1.8 |
| hip pitch | 0.50 to 0.88 | 7.2 to 11.5 |
| knee | 0.69 to 0.97 | 11.0 to 18.9 |
| ankle | 0.41 to 0.89 | 5.7 to 13.5 |

Hip roll needs well under any servo limit, and it is the joint that tracks. Every joint that fails needs a peak speed above 5.24 rad/s, so it is speed limited even in sim. That is why the sim knee also under-tracks. On hardware the ratios are about half of sim. That fits a servo that tops out around 2.5 to 3 rad/s instead of the modelled 5.2, which is what redEddie reports. A faster gear ratio would hide the problem but would also break the match with the policy.

Why a 1:345 7.4 V servo might run at half speed (ranked):

1. Servo state or firmware differs from what was identified. The model assumes P 32 (runtime writes P 30 to legs and 8 to head), D 0, I 0, Acceleration 0 and max acceleration 0 (configure_all_motors.py), Goal Speed 0 and Torque Limit at maximum. BAM's maintainer notes the Feetech firmware internally clamps command variation (BAM PR #12), and newer firmware has extra profile registers (rustypot lists acceleration_multiplier at address 86). Runtime issue #26 shows mixed firmware versions breaking set_kps until all servos were updated with the Feetech Windows tool. Any servo with a different firmware, a non-zero acceleration or goal speed, or a low torque limit would show exactly this.
2. Supply voltage at the servo. Back-EMF limited speed scales with voltage. The BOM uses a 2S 18650 spring holder with thin wires and no fuse (issue #51). Sag under 14 servos can lower speed and torque. Needs logging of Present Voltage during a walk.
3. Mislabeled or 12 V units. A 12 V C018 (also 1:345) at 7.4 V gives about 2.9 rad/s, very close to the 2.7 rad/s claimed. Retail listings mix 7.4 V and 12 V units under "STS3215". Check the label and the max voltage EEPROM register, and measure no-load speed.
4. Loop timing and mechanics. 50 Hz control on a Pi Zero 2 W (the runtime prints "Policy control budget exceeded" when late), backlash or loose screws (a third-party write-up found loosening actuator screws, zhenghaoxu.com/duck writeup.pdf), and calibration offsets.

Not likely: the commented-out velocity clip in v2_rl_walk_mujoco.py. The servo firmware limits speed anyway, and in sim the clip only shapes targets.

## 6. Bench test plan before buying the full set (no purchase made)

1. Buy 1 or 2 C001 first (or use the first units of the order). Read model number, firmware major and minor, P, D, I, Acceleration, Goal Speed, Torque Limit and Max Voltage registers, and log them.
2. Run configure_motor.py settings (P 32, D 0, I 0, acceleration 0). Command a 2 rad step and a 1.5 Hz, 0.4 rad sine with no load at 7.4 V from a bench supply, then at 8.4 V. Log Present Position, Speed and Voltage at 50 Hz or faster.
3. Pass if no-load speed is about 5 rad/s or more at 7.4 V. If it is about 2.7 to 3 rad/s, check the unit is not a 12 V version and update firmware so all units match.
4. Repeat the #48 suspended tracking test on the assembled legs and compare with sim.

Added 2026-11-01 6:44 PM ET (UPSTREAM_ISSUES.md G1 and G3): before the step test, run configure_motor.py on the servo even if its ID was set with the Feetech tool, then read back registers 41, 44, 46 (goal time, goal speed), 84, 85, 86 and the firmware version. Register 85 (max acceleration) must read 0: a third-party build log (github.com/jyxddd/open-duck-mini-notes, not verified by us) found it at its factory value 50, which made its servos about 3 x slower than the sim. All 14 servos must report the same firmware version. If the legs buzz on the ground at P 30, try P 20.

## 7. Draft question for issue #48 (TEXT ONLY, NOT POSTED, needs Ahmed's approval)

Update 2026-11-01: this question was posted on issue #48 by aaltaay at 1:08 PM ET: https://github.com/apirrone/Open_Duck_Mini/issues/48#issuecomment-6561836208 . The heading above is kept as written.

Title: none (comment on #48)

Body:
@apirrone, a short check so builders can buy the right part and debug tracking:
1. Are your leg servos the Feetech STS3215 7.4 V 1:345 (19 kg.cm, sold as C001)? Or were any of them faster units (C044 1:191, C046 1:147 or Waveshare ST3215-HS)? The 7.4 V BAM model (5.43 rad/s implied no-load, 5.24 rad/s max_motor_velocity) matches the C001 datasheet (52 RPM at 7.4 V). A photo of the servo label would settle it.
2. Which servo firmware version (major.minor) did you use for the BAM recordings and for training BEST_WALK_ONNX_2? Did you change any register besides P 32, D 0, I 0, acceleration 0 and maximum acceleration 0 (for example Goal Speed, Torque Limit, Return Delay or acceleration multiplier)?
3. On your robot, what no-load speed do you measure for one leg servo at 7.4 V? What bus voltage do you see during walking?
In #48 the hip roll tracks 1.0 but the hip pitch, knee and ankle track only 0.31 to 0.49. Those joints need peaks of 7 to 19 rad/s in the reference motion, so a servo running at about 2.7 rad/s instead of 5.2 rad/s would explain it.

## Sources

- BOM CSV: a local export of the upstream Google Sheet BOM (there is no bom.csv in the upstream repo at b23317a; noted 2026-11-01)
- sim2real doc: https://github.com/apirrone/Open_Duck_Mini/blob/v2/docs/sim2real.md
- Issue #48: https://github.com/apirrone/Open_Duck_Mini/issues/48
- Issue #5 (HS comment): https://github.com/apirrone/Open_Duck_Mini/issues/5
- Issue #20 (17.8 = 32): https://github.com/apirrone/Open_Duck_Mini/issues/20
- Issue #21 (7.4 V vs 12 V): https://github.com/apirrone/Open_Duck_Mini/issues/21
- Issue #51 (power): https://github.com/apirrone/Open_Duck_Mini/issues/51
- Issue #52 (12 V knees): https://github.com/apirrone/Open_Duck_Mini/issues/52
- Runtime issue #7 (5.24 from sysid): https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/7
- Runtime issue #26 (firmware mismatch): https://github.com/apirrone/Open_Duck_Mini_Runtime/issues/26
- Playground issue #5 (feet not lifting): https://github.com/apirrone/Open_Duck_Playground/issues/5
- BAM commit b1769a6 (m1.json by apirrone): https://github.com/Rhoban/bam/commit/b1769a6707e18e77fd656ea76a63588e0195bcc3
- BAM commit 5b0486e (velocity limit): https://github.com/Rhoban/bam/commit/5b0486e9f6b9508e2c732423e2cd11f8e5a4a2bc
- BAM commit 31e5b97 (m1 to m6): https://github.com/Rhoban/bam/commit/31e5b97b3cabfe2b909850d483c4e84afa9781c4
- BAM params folder: https://github.com/Rhoban/bam/tree/main/params/feetech_sts3215_7_4V
- BAM Feetech actuator: https://github.com/Rhoban/bam/blob/main/bam/feetech/actuator.py
- BAM PR #12 (firmware clamp): https://github.com/Rhoban/bam/pull/12
- BAM issue #13 (data from apirrone): https://github.com/Rhoban/bam/issues/13
- Playground joints_properties.xml: https://github.com/apirrone/Open_Duck_Playground/blob/main/playground/open_duck_mini_v2/xmls/joints_properties.xml
- Playground commits: https://github.com/apirrone/Open_Duck_Playground/commit/07c1f5ce3688a9c167f5ef959eaf0d999f3b8249 and https://github.com/apirrone/Open_Duck_Playground/commit/f6988368da959156d94fcd53b76864724dc52860
- Runtime walk script: https://github.com/apirrone/Open_Duck_Mini_Runtime/blob/main/scripts/v2_rl_walk_mujoco.py
- Runtime configure script: https://github.com/apirrone/Open_Duck_Mini_Runtime/blob/main/scripts/configure_all_motors.py
- Runtime HWI: https://github.com/apirrone/Open_Duck_Mini_Runtime/blob/main/mini_bdx_runtime/mini_bdx_runtime/rustypot_position_hwi.py
- Feetech variant table (Alibaba): https://www.alibaba.com/product-detail/STS3215-1-345-1-191-1_1601438278086.html
- Feetech products: https://www.feetech.cn/en/products-page-6
- C046 spec PDF: https://akizukidenshi.com/goodsaffix/ST-3215-C046%20SEPC.pdf
- Waveshare ST3215 docs: https://docs.waveshare.com/ST3215_Servo
- Waveshare ST3215-HS: https://www.waveshare.com/st3215-hs-servo-motor.htm
- FTServo datasheets: https://ftservo.github.io/ftservo-wiki/products/datasheets/st/
- STS3215 register reference: https://github.com/commanderfun/STS3215/blob/main/REGISTER_REFERENCE.md
- rustypot sts3215 registers: https://docs.rs/rustypot/latest/rustypot/servo/feetech/sts3215/index.html
- Reachy Mini hardware: https://huggingface.co/docs/reachy_mini/main/platforms/reachy_mini/hardware
- Third-party sim2real write-up: https://zhenghaoxu.com/duck%20writeup.pdf
