# Open Duck Mini v2 (Altaay lab notes)

Open Duck Mini v2 is an open source, roughly 42 cm tall, 2.1 kg (sim mass) (the lab build is about 2.65 kg by the mass budget, sim/MASS_BUDGET.md, not weighed) bipedal robot by Antoine Pirrone, inspired by Disney's BDX droid. It has 14 Feetech STS3215 serial bus servos (5 per leg, 4 in the neck and head), a Raspberry Pi Zero 2 W, a BNO055 IMU and a 2S 18650 pack. It walks with an RL policy trained in MuJoCo Playground and exported to ONNX.

Goal of this folder: build the robot exactly as designed upstream, and record every gap before buying anything.

## Official links
- Main repo: https://github.com/apirrone/Open_Duck_Mini (default branch v2)
- Runtime: https://github.com/apirrone/Open_Duck_Mini_Runtime (branch v2)
- Training: https://github.com/apirrone/Open_Duck_Playground
- Reference motion: https://github.com/apirrone/Open_Duck_reference_motion_generator
- Onshape CAD: https://cad.onshape.com/documents/64074dfcfa379b37d8a47762/w/3650ab4221e215a4f65eb7fe/e/0505c262d882183a25049d05
- Upstream BOM: https://docs.google.com/spreadsheets/d/1gq4iWWHEJVgAA_eemkTEsshXqrYlFxXAPwO515KpCJc
- Build guide (Tnkr): https://tnkr.ai/explore/docs/open-duck-mini/open-duck-mini-v2#home
- Discord: https://discord.gg/UtJZsgfQGe

## License
- Open_Duck_Mini: Apache-2.0 (LICENSE file in repo).
- Runtime, Playground, reference motion generator: no LICENSE file found at the commits below. Default copyright applies until upstream adds one (see DECISIONS D6).
- Onshape CAD: public document, license not stated separately (not verified).

## Upstream pin
| Repo | Branch | Commit | Date |
|---|---|---|---|
| Open_Duck_Mini | v2 | b23317a485b3cec7d8417f352478778b3475173c | 2026-01-31 |
| Open_Duck_Mini_Runtime | v2 | 376de65435c93486347cd601a31aa96951799896 | 2026-09-07 |
| Open_Duck_Playground | main | b9be205ac64488c23504ca42e5ec790337adeec3 | 2025-08-05 |
| Open_Duck_reference_motion_generator | main | 3d7bc6fd80e6c35587b2a5279314d946cf63456b | 2025-04-03 |

CAD, STL and sim assets are not copied here. Use the upstream commits above.

## Files
STATE.md, DECISIONS.md, BOM.md, GAPS.md, REFERENCES.md, SERVO_DEEP_DIVE.md, POWER.md, WIRING.md (+ wiring/), sim/SIM_WALK.md (+ sim/run_stock_walk.py), HARDWARE_AUDIT.md, PRINT_CHECK.md, CABLE_MAP.md, MOUNTING.md, audit/ (measurement scripts and data)
