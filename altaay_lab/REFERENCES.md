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

## Hardware audit sources (2026-11-01)
- Upstream STLs: apirrone/Open_Duck_Mini_v2 print/ at commit 730c14bc50e4e60c4a983f57fd739e015510cc76
- https://boltdepot.com/Product-Details?product=6370
- https://boltdepot.com/Product-Details?product=6371
- https://boltdepot.com/Product-Details?product=6372
- https://boltdepot.com/Product-Details?product=6377
- https://boltdepot.com/Product-Details?product=6378
- https://boltdepot.com/Product-Details?product=6379
- https://boltdepot.com/Product-Details?product=6380
- https://boltdepot.com/Product-Details?product=6381
- https://cnckitchenus.store/products/heat-set-insert-m3-x-5-7-100-pieces
- https://crawfordtool.com/products/bondhus-12192-metric-hex-key-set-l-wrenches-7-pieces-1-5mm-to-6mm
- https://download.kamami.pl/p1198708-STS3215-C001-20230624.pdf
- https://files.waveshare.com/wiki/Bus-Servo-Adapter-(A
- https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/2194/PA-09_PA-20_Compatibility_Chart_5-4-17.pdf
- https://pine64.com/product/pinecil-smart-mini-portable-soldering-iron/
- https://pine64.com/product/pinecil-threaded-insert-tips-set-and-adapter/
- https://www.18650batterystore.com/products/molicel-p30b-18650-3000mah-36a-battery
- https://www.adafruit.com/product/2472
- https://www.adafruit.com/product/3006
- https://www.adafruit.com/product/5291
- https://www.amazon.com/AITRIP-Lithium-Battery-Charger-Balance/dp/B08NSTF8CT
- https://www.amazon.com/Adeept-18650-Charge-Charging-Board/dp/B0BJTW4QBR
- https://www.amazon.com/BNTECHGO-Gauge-Silicone-Wire-Temperature/dp/B01F8PO5XE
- https://www.amazon.com/BNTECHGO-Silicone-Spool-Color-100ft/dp/B09X4KY56S
- https://www.amazon.com/Engineer-PA-09-Micro-Connector-Crimpers/dp/B002AVVO7K
- https://www.amazon.com/Malockos-HENGE-Aeroplane-Helicopter-Mulitcopter/dp/B0DBPXNN7N
- https://www.amazon.com/Wirefy-180-Heat-Shrink-Tubing/dp/B084GDLSCK
- https://www.amazon.com/dp/B004L439FE
- https://www.amazon.com/dp/B072V529YD
- https://www.amazon.com/dp/B08F9CF85N
- https://www.amazon.com/dp/B08P5HVMYT
- https://www.amazon.com/dp/B09LCK7QJ2
- https://www.amazon.com/dp/B09WCT8672
- https://www.amazon.com/dp/B0B67NKCSW
- https://www.amazon.com/dp/B0BGMP1MZ7
- https://www.amazon.com/dp/B0D99THG1M
- https://www.digikey.com/en/products/result?keywords=0287015.PXCN
- https://www.digikey.com/en/products/result?keywords=omron%20SS-10
- https://www.homedepot.com/p/Klein-Tools-Klein-Kurve-Wire-Stripper-and-Cutter-20-30-AWG-Solid-22-32-AWG-Stranded-11057/100352112
- https://www.imscrews.com/products/imscrews-100-pcs-m2-x-5mm-black-self-tapping-screws-304-stainless-steel-phillips-pan-washer-head-natural-black-no-peeling-type-a-point-for-metal-wood-plastic
- https://www.mantech.co.za/Datasheets/Products/STS3215-200620A.pdf
- https://www.mouser.com/c/?q=08-70-1040
- https://www.mouser.com/c/?q=50-37-5033
- https://www.newark.com/search?st=FHAC0001ZXJ
