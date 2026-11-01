# REFERENCES

## Upstream
- https://github.com/apirrone/Open_Duck_Mini (Apache-2.0, pin b23317a485b3cec7d8417f352478778b3475173c)
- https://github.com/apirrone/Open_Duck_Mini_Runtime (v2, pin 376de65435c93486347cd601a31aa96951799896; release image "V2 Classic" v0.2.3, 2025-08-15)
- https://github.com/apirrone/Open_Duck_Playground (pin b9be205ac64488c23504ca42e5ec790337adeec3)
- https://github.com/apirrone/Open_Duck_reference_motion_generator (pin 3d7bc6fd80e6c35587b2a5279314d946cf63456b)
- Onshape: https://cad.onshape.com/documents/64074dfcfa379b37d8a47762/w/3650ab4221e215a4f65eb7fe/e/0505c262d882183a25049d05
- BOM sheet: https://docs.google.com/spreadsheets/d/1gq4iWWHEJVgAA_eemkTEsshXqrYlFxXAPwO515KpCJc
- Tnkr guide: https://tnkr.ai/explore/docs/open-duck-mini/open-duck-mini-v2#home
- Discord: https://discord.gg/UtJZsgfQGe
- BAM actuator identification: https://github.com/Rhoban/bam

## Key upstream docs (paths at the pin)
- docs/print_guide.md, docs/assembly_guide.md, docs/configure_motors.md
- docs/open_duck_mini_v2_wiring_diagram.png (+ .drawio), docs/wiring.png (+ .drawio)
- print/ (36 STLs), print/mods (community)
- mini_bdx/robots/open_duck_mini_v2/robot.urdf and robot.xml
- BEST_WALK_ONNX.onnx, BEST_WALK_ONNX_2.onnx

## Issues cited
- #1 UBEC placement and future redesign note
- #26 bulb quantity
- #29 Discord phone requirement
- #43 training data
- #48 servo variant and tracking (open)
- #51 2S over-voltage and holder current

## Vendor specs
- Feetech after-sales policy: https://www.feetech.cn/en/after-sales-service-and-policy
- STS3215 C001 at Seeed: https://www.seeedstudio.com/STS3215-19kg-cm-7-4V-Serial-Servo-p-6338.html
- Waveshare Bus Servo Adapter (A): https://www.waveshare.com/bus-servo-adapter-a.htm

## Official photos (box copy, not committed)
/workspace/odm_share/: 01_readme_1.png, 02_readme_2.png, 03_readme_3.png, 05_assembled_1.png, 06_assembled_2.png, 07_legs_assembled.png. Source: upstream README and assembly guide.

## Power and wiring sources (2026-11-01)
- Castle CC BEC Pro: https://castlecreations.com/products/voltage-regulator-cc-bec-pro-20a-010-0004-01 and https://www.castlecreations.com/en/cc-bec-pro-010-0004-01
- CC BEC Pro user guide (P/N 095-0047-00): https://www.freakware.de/technik/CastleCreations/cc_bec_pro_user_guide.pdf
- Castle Link V4: https://castlecreations.com/products/accessories-castle-link-v4-psoc-usb-programming-kit-011-0173-00
- Castle CC BEC 2.0 WP: castlecreations.com, P/N 010-0153-00
- Pololu D42V110F7: https://www.pololu.com/product/5674, D42V110F6: https://www.pololu.com/product/5673, D24V150F7: https://www.pololu.com/product/2883
- Littelfuse 0287015.PXCN (ATO 15 A) and FHAC0001ZXJ (inline ATO holder): littelfuse.com, DigiKey, Newark
- BNTECHGO 16 AWG silicone wire: https://www.amazon.com/dp/B01MCRY7OT
- Waveshare Bus Servo Adapter (A) wiki: https://www.waveshare.com/wiki/Bus_Servo_Adapter_(A)
- Issue #51: https://github.com/apirrone/Open_Duck_Mini/issues/51
- Upstream pins and code: Open_Duck_Mini docs/assembly_guide.md (pin table), Runtime mini_bdx_runtime eyes.py, antennas.py, feet_contacts.py
- BAM STS3215 model (vin 7.4 V): https://github.com/Rhoban/bam bam/feetech/actuator.py
- Sim: Open_Duck_Playground playground/open_duck_mini_v2/mujoco_infer.py and mujoco_infer_base.py
