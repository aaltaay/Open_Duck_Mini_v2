#!/usr/bin/env python3
"""Build the data for the Open Duck Mini v2 exploded parts-check page.

What it does (re-run it any time the docs, the STLs or placements.json change):
1. Poses the robot from robot.urdf at zero joint angles with yourdfpy (translations x1000 to mm,
   same as audit/assemble.py). Every printed URDF mesh is swapped for its print/ STL (same part
   frame; the script checks the bounds agree within 0.05 mm).
2. Adds the head parts that exist only in print/ (audit/headgroup.py): they are modelled in the
   head.stl frame, so they get the head.stl instance transform; the second bulb is mirrored in y.
3. Draws the M3 heat-set inserts from audit/sites.json (a bore in a printed part, diameter 3.8 to
   4.3 mm, length >= 5.0 mm) as brass cylinders, D 4.6 x 5.7 mm.
4. Adds placeholder boxes for bought parts that are not in the CAD. Positions come from
   audit/placements.json when it exists (re-read on every run, frame urdf_world_mm); the Omron
   foot switches go in the measured foot_top slots; everything else goes in a "Not yet placed" tray.
5. Decimates the meshes for the web (one geometry per unique STL, reused by every instance),
   splits vertices at sharp edges (the page computes normals) and writes:
     <out>/duck.glb       nodes in mm, URDF frame (x forward, y left, z up) under a root node that
                          turns it to glTF y-up and scales to metres
     <out>/duck.glb.txt   the same GLB as base64 text (the artifact host does not serve .glb files)
     <out>/manifest.json  node id -> label, file, subassembly, category, qty, material, print g/h,
                          BOM line, mount note, status; the checklist; the explode vectors.
Docs parsed on every run: PRINT_CHECK.md, print/SLICE_SUMMARY.md (print grams and hours of the D22 profile), BOM.md,
HARDWARE_AUDIT.md (section 6 blockers).

The output folder must be outside the repo (no models in git).
Usage: python3 make_viewer_data.py --out /path/outside/the/repo
"""
import argparse
import json
import os
import re
import struct
import sys
import time
from collections import Counter, OrderedDict, defaultdict

import numpy as np
import trimesh
import yourdfpy

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
REPO = os.path.dirname(LAB)
URDF_DIR = os.path.join(REPO, "mini_bdx", "robots", "open_duck_mini_v2")
PRINT_DIR = os.path.join(REPO, "print")
AUDIT = os.path.join(LAB, "audit")
PLACEMENTS = os.environ.get("ODM_PLACEMENTS", os.path.join(AUDIT, "placements.json"))

INSERT_D, INSERT_L = 4.6, 5.7          # CNC Kitchen M3 x 5.7, D1 4.6 (BOM line 16)
INSERT_BORE = (3.8, 4.3, 5.0)          # bore diameter range and minimum length, mm

# ----------------------------------------------------------------------------------------------
# Catalog of modelled parts that are not printed (URDF mesh file -> part key, label, category, BOM)
BOUGHT = {
    "wj-wk00-0122topcabinetcase_95.stl": ("servo_top", "Servo case, top", "servo", "1"),
    "wj-wk00-0123middlecase_56.stl": ("servo_mid", "Servo case, middle", "servo", "1"),
    "wj-wk00-0124bottomcase_45.stl": ("servo_bottom", "Servo case, bottom", "servo", "1"),
    "drive_palonier.stl": ("horn_drive", "Servo horn, drive side", "horn", "1"),
    "passive_palonier.stl": ("horn_idle", "Servo horn, idle side", "horn", "1"),
    "roll_bearing.stl": ("bearing", "6804ZZ ball bearing 20 x 32 x 7", "bearing", "18"),
    "cell.stl": ("cell", "Molicel INR21700-P45B cell (D44)", "battery", "6"),
    "holder.stl": ("holder", "2S1P pack nickel strip, sleeve and leads (D44)", "battery", "7"),
    "bms.stl": ("bms_cad", "2S BMS, upstream CAD body", "electronics", "8"),
    "usb_c_charger.stl": ("charger", "USB-C 2S charge board", "electronics", "11"),
    "power_switch.stl": ("power_switch", "Control switch, stock panel slide switch (CAD body)", "electronics", "10b"),
    "raspberrypizerow.stl": ("pi", "Raspberry Pi Zero 2 W", "electronics", "3"),
    "bno055.stl": ("imu", "Adafruit BNO055 IMU (2472)", "electronics", "5"),
    "sg90.stl": ("sg90", "SG90 antenna servo", "servo", "14"),
    "antenna.stl": ("antenna", "Antenna rod", "other", None),
    # board.stl is split by link below: trunk = servo adapter, head = Pi footprint copy (B7)
}
BOARD = {"trunk_assembly": ("adapter", "Waveshare Bus Servo Adapter (A)", "electronics", "2"),
         "head_assembly": ("head_board", "board.stl copy in the head (Pi footprint, B7)", "electronics", None)}

HEAD_INTERNALS = ["left_eye", "right_eye", "bulb", "bulb", "flash_light_module",
                  "flash_reflector_interface", "speaker_stand", "speaker_interface"]

# Servo IDs per joint (WIRING.md section 2, from the Runtime and the assembly guide)
SERVO_ID = {"left_hip_yaw": 20, "left_hip_roll": 21, "left_hip_pitch": 22, "left_knee": 23, "left_ankle": 24,
            "right_hip_yaw": 10, "right_hip_roll": 11, "right_hip_pitch": 12, "right_knee": 13, "right_ankle": 14,
            "neck_pitch": 30, "head_pitch": 31, "head_yaw": 32, "head_roll": 33}

# Subassemblies: link -> subassembly; groups are for the isolate menu
LINK_SUB = {
    "trunk_assembly": "trunk",
    "neck_pitch_assembly": "neck", "head_pitch_to_yaw": "neck", "neck_yaw_assembly": "neck",
    "head_assembly": "head", "left_antenna_holder": "head", "right_antenna_holder": "head",
    "hip_roll_assembly": "left_hip", "left_roll_to_pitch_assembly": "left_bracket",
    "knee_and_ankle_assembly": "left_thigh", "knee_and_ankle_assembly_2": "left_shin", "foot_assembly": "left_foot",
    "hip_roll_assembly_2": "right_hip", "right_roll_to_pitch_assembly": "right_bracket",
    "knee_and_ankle_assembly_3": "right_thigh", "knee_and_ankle_assembly_4": "right_shin", "foot_assembly_2": "right_foot",
}
SUBS = [  # id, label, group, level-1 explode vector (mm at full explode)
    ("head", "Head", "head_neck", (0, 0, 300)),
    ("neck", "Neck", "head_neck", (0, 0, 165)),
    ("trunk", "Trunk", "trunk", (0, 0, 0)),
    ("left_hip", "Left hip", "left_leg", (0, 75, -35)),
    ("left_bracket", "Left hip bracket", "left_leg", (0, 120, -60)),
    ("left_thigh", "Left thigh", "left_leg", (0, 165, -105)),
    ("left_shin", "Left shin", "left_leg", (0, 165, -175)),
    ("left_foot", "Left foot", "left_leg", (0, 165, -245)),
    ("right_hip", "Right hip", "right_leg", (0, -75, -35)),
    ("right_bracket", "Right hip bracket", "right_leg", (0, -120, -60)),
    ("right_thigh", "Right thigh", "right_leg", (0, -165, -105)),
    ("right_shin", "Right shin", "right_leg", (0, -165, -175)),
    ("right_foot", "Right foot", "right_leg", (0, -165, -245)),
    ("tray", "Not yet placed", "tray", (0, -190, -245)),
]
GROUPS = [("head_neck", "Head and neck"), ("trunk", "Trunk"), ("left_leg", "Left leg"),
          ("right_leg", "Right leg"), ("tray", "Not yet placed tray")]

# Level-2 explode overrides (mm at full explode): (subassembly, part key) -> vector.
# Everything else moves radially away from its subassembly centre.
V2 = {
    # trunk: front forward, back and battery bay backward in a stack, belly shells up and down
    ("trunk", "body_front"): (80, 0, 0),
    ("trunk", "body_back"): (-125, 0, 0),
    ("trunk", "battery_pack_lid"): (-30, 0, 0),
    ("trunk", "holder"): (-60, 0, 0),
    ("trunk", "cell"): (-88, 0, 0),
    ("trunk", "bms_cad"): (-60, -26, 0),
    ("trunk", "bms_tenergy"): (-60, -26, 0),
    ("trunk", "charger"): (-100, -26, 0),
    ("trunk", "power_switch"): (-100, 0, 30),
    ("trunk", "body_middle_top"): (0, 0, 115),
    ("trunk", "body_middle_bottom"): (0, 0, -85),
    ("trunk", "trunk_top"): (0, 0, 42),
    ("trunk", "trunk_bottom"): (0, 0, -22),
    ("trunk", "adapter"): (0, 0, 78),
    ("trunk", "imu"): (0, 0, -18),
    ("trunk", "bearing"): (0, 0, -48),
    # head: shell lifts off, floor drops, face parts forward, side lamp out to the left
    ("head", "head"): (0, 0, 150),
    ("head", "head_bot_sheet"): (0, 0, -40),
    ("head", "left_eye"): (70, 0, 0),
    ("head", "right_eye"): (70, 0, 0),
    ("head", "bulb"): (42, 0, 0),
    ("head", "flash_light_module"): (10, 60, 0),
    ("head", "flash_reflector_interface"): (22, 100, 0),
    ("head", "speaker_stand"): (0, -30, 0),
    ("head", "speaker_interface"): (0, -62, 0),
    ("head", "pi"): (0, 0, 72),
    ("head", "head_board"): (0, 0, 72),
    ("head", "head_roll_mount"): (0, 0, 92),
    ("head", "bearing"): (-40, 0, 0),
    ("head", "camera"): (60, 0, 20),
    ("neck", "neck_left_sheet"): (0, 30, 0),
    ("neck", "neck_right_sheet"): (0, -30, 0),
    ("neck", "head_pitch_to_yaw"): (0, 0, 22),
    ("neck", "head_yaw_to_roll"): (0, 0, 52),
}
# Servo groups: explode vector of the whole servo inside its subassembly (by joint)
V2_SERVO = {
    "left_hip_yaw": (0, 52, 10), "right_hip_yaw": (0, -52, 10), "neck_pitch": (40, 0, 30),
    "head_pitch": (40, 0, 0), "head_yaw": (55, 0, 52), "head_roll": (30, 0, 25),
}
HORN_PULL, INSERT_PULL = 14.0, 11.0     # extra pull along the horn axis / insert bore, mm
# Ear SG90s (the antenna servos, D47): each hangs from the head side plate on its 2 tab screws and carries its antenna
# holder on the output shaft. They ride with the head shell and part only along their own shaft axis (mm at full
# level-2 explode; + is out of the head), so the explode shows servo, tab screws, plate and holder on one line
# instead of the servo drifting off by itself (twin/companion/ear_mount.py, CAD check only).
EAR_PULL = {"sg90": -20.0, "left_antenna_holder": 30.0, "right_antenna_holder": 30.0, "antenna": 42.0}
# fasteners.json part names that are not a part key: the screw rides with this part
SCREW_PART_ALIAS = {"SG90 tab": "sg90"}
SHORT = {"bec_pro": "BEC Pro", "fuse_holder": "Fuse holder", "mosfet_switch": "Pololu 2813", "led_1": "Eye LED left", "led_2": "Eye LED right", "led_3": "Projector LED", "bms_tenergy": "Tenergy BMS",
         "reg_5v": "5 V reg", "xt30": "XT30U", "xt30_p13": "XT30U P13", "amp": "Amp", "speaker": "Speaker", "camera": "Camera", "led": "LED",
         "foot_switch": "SS-01"}

# Placeholders for bought parts that are not in the CAD. ids match audit/place_parts.py.
PLACEHOLDERS = [
    dict(id="bec_pro", label="Castle CC BEC Pro (servo 7.2 V regulator)", dims=[47, 33, 24], bom="L1",
         blockers=["B11", "B28"], dims_note="47 x 33 x 26 mm envelope covering the 3 published sizes (MOUNTING.md).",
         mount="Belly floor inside body_middle_bottom, foam tape (BOM 29), leads toward the battery bay (MOUNTING.md, D11). "
               "Minimum input voltage is measured on the bench first (TEST_PLAN.md section 4, D16)."),
    dict(id="fuse_holder", label="Littelfuse FHAC0001ZXJ inline ATO fuse holder", dims=[45, 20, 15], bom="L3",
         blockers=["B11", "B28"], dims_note="Envelope 52 x 22 x 18 mm with the cover (Littelfuse drawing, D11).",
         mount="Battery bay front wall, BMS side, foam tape. Inline on lead P7 between the XT30 and the Pololu 2815 (MOUNTING.md)."),
    dict(id="mosfet_switch", label="Pololu 2813 Big Pushbutton Power Switch HP (D30)", dims=[20.3, 25.4, 4.1], bom="10",
         blockers=["B22"], dims_note="20.3 x 25.4 x 4.1 mm.",
         mount="Main power switch (D8): battery bay front wall, foam tape, on-board slide OFF, control pin to the body_back panel switch."),
    dict(id="bms_tenergy", label="Tenergy 32175 2S protection board", dims=[34, 16, 4.5], bom="8",
         blockers=["B12"], dims_note="34 x 16 x 4.5 mm.",
         mount="Replaces the modelled bms.stl (shown solid at the upstream position). Sandwiched between body_back and battery_pack_lid."),
    dict(id="reg_5v", label="5 V regulator, Pololu D30V30F5", dims=[17.8, 20.3, 8], bom="9",
         blockers=["B11", "B28"], dims_note="0.7 x 0.8 in board (17.8 x 20.3 mm, Pololu page); 8 mm height allows the parts.",
         mount="Head floor below the Pi, foam tape (MOUNTING.md, D4). Fed from the switched pack bus up the neck (P13), 5 V to Pi pins 2 and 6."),
    dict(id="xt30", label="XT30U connector pair, mated", dims=[32, 10, 5.2], bom="12",
         blockers=[], dims_note="About 32 x 10 x 5.2 mm mated (approximate).",
         mount="Inline on the pack lead, no screws. Tnkr: left of the cell holder, standing."),
    dict(id="xt30_p13", label="XT30U pair in P13, service plug at the neck base (X3a, D36)", dims=[32, 10, 5.2], bom="12",
         blockers=[], dims_note="About 32 x 10 x 5.2 mm mated (approximate), as the line 12 pair.",
         mount="Inline on P13 on its straight run at the neck base (cables3d.json P13 route), 20 mm or more from the neck_pitch loop end; tied to the P13 bundle. The head comes off by unplugging it (X3a, D36)."),
    dict(id="amp", label="Adafruit MAX98357A I2S amp (3006)", dims=[19, 18, 3], bom="E2",
         blockers=[], dims_note="About 19 x 18 x 3 mm (approximate).",
         mount="Not in CAD, no mount (BOM E2). Tnkr: head floor, right of the speaker stand, foam tape."),
    dict(id="speaker", label="Speaker, Same Sky CMS0361KLX 8 ohm 2 W", dims=[36.1, 36.1, 14.5], bom="E1",
         blockers=["B8"], dims_note="36.1 x 36.1 x 14.5 mm (Same Sky drawing). CAD envelope is 38.5 x 38.7 x 15.",
         mount="Sits in speaker_interface on speaker_stand, held with foam tape (BOM 29). No clip or screw in CAD (B8)."),
    dict(id="camera", label="Raspberry Pi Camera Module 3", dims=[25, 24, 11.5], bom="E6",
         blockers=["B9"], dims_note="25 x 24 x 11.5 mm.",
         mount="4 x M2x5 self-tapping (BOM 17h) into the head.stl pilots 1.65 mm on 20.9 x 12.5, drilled to 4.5 mm (D34). Drawn as its PCB, 25 x 24 x 1.0 mm; the lens sits in the 7.75 mm opening."),
    dict(id="mic_l", label="I2S mic board left (Adafruit 3421, D47)", dims=[16.51, 3.0, 12.7], bom="E8", blockers=[],
         dims_note="16.51 x 12.7 mm board (the 3421 board files); drawn 3.0 mm thick (1.8 mm overall on the product page, 0.4 g).",
         mount="2 x M2x6 (BOM 17h) into 2 printed bosses on the left inner side wall, board back 3.5 mm off the wall, the PCB port on the port tube and the 1.2 mm wall port (twin/companion/mic_seats.json, D47)."),
    dict(id="mic_r", label="I2S mic board right (Adafruit 3421, D47)", dims=[16.51, 3.0, 12.7], bom="E8", blockers=[],
         dims_note="16.51 x 12.7 mm board (the 3421 board files); drawn 3.0 mm thick (1.8 mm overall on the product page, 0.4 g).",
         mount="2 x M2x6 (BOM 17h) into 2 printed bosses on the right inner side wall, the mirror of the left (twin/companion/mic_seats.json, D47)."),
    dict(id="dock_pad", label="Chest contact pad (BOM DK1, D50)", dims=[0.8, 100.0, 76.0], bom="DK1", blockers=[],
         dims_note="100 x 76 x 0.8 mm FR4, four strips.", mount="VHB 4950 on the flat chest face of body_front, trunk z 0 to 76; four leads through one 6.0 mm hole printed in body_front at its centre, with a 45 deg bell mouth inside (MOUNTING.md V1 track 8 phase 3)."),
    dict(id="dock_dk2", label="Charge input ideal diode Pololu 5382 (BOM DK2)", dims=[3.0, 13.0, 8.0], bom="DK2", blockers=[],
         dims_note="0.3 x 0.5 in board, 3 mm with parts.", mount="VHB 4950 on the inner face of body_front below the lead hole (twin/dock/dock_seats.json)."),
    dict(id="dock_f2", label="Charge path fuse holder, 5 A (BOM DK3, DK4)", dims=[18.0, 18.0, 52.0], bom="DK3", blockers=[],
         dims_note="Holder body 50 x 17.2 x 17.2 mm (Littelfuse drawing) as an 18 x 18 x 52 box.", mount="VHB 4950 along the left inner side wall of body_middle_bottom, standing (twin/dock/dock_seats.json)."),
    dict(id="dock_dk6", label="Dock supply ideal diode Pololu 5382 (BOM DK6, D50)", dims=[13.0, 8.0, 3.0], bom="DK6", blockers=[],
         dims_note="0.3 x 0.5 in board, 3 mm with parts.", mount="VHB 4950 under trunk_top beside the 2813 (twin/dock/dock_seats.json)."),
    dict(id="dock_dk7", label="Pack side ideal diode Pololu 5383 (BOM DK7, D50)", dims=[8.0, 13.0, 3.0], bom="DK7", blockers=[],
         dims_note="0.3 x 0.5 in board, 3 mm with parts.", mount="VHB 4950 under trunk_top beside the 2813, VOUT lead to SW1 VIN (twin/dock/dock_seats.json)."),
    dict(id="led_1", label="Eye LED left (1 W bead)", dims=[8, 8, 5], bom="E3", blockers=[],
         dims_note="Size not given: 8 x 8 x 5 mm stand-in.", mount="Behind the left bulb, 100 ohm resistor (B23 cleared)."),
    dict(id="led_2", label="Eye LED right (1 W bead)", dims=[8, 8, 5], bom="E3", blockers=[],
         dims_note="Size not given: 8 x 8 x 5 mm stand-in.", mount="Behind the right bulb, 100 ohm resistor (B23 cleared)."),
    dict(id="led_3", label="Projector LED (1 W bead)", dims=[8, 8, 5], bom="E3", blockers=[],
         dims_note="Size not given: 8 x 8 x 5 mm stand-in.", mount="In the flash reflector interface; retention needs the real reflector (B8)."),
]
FOOT_SWITCH = dict(label="Omron SS-01 foot switch (SS-10 fallback)", dims=[6.4, 19.8, 10.2], bom="13", blockers=[],
                   dims_note="19.8 x 6.4 x 10.2 mm body (Omron SS datasheet), same for SS-01 and SS-10.",
                   mount="Press fit in a foot_top slot 6.4 x 19.8 mm, lever down toward foot_bottom (B11 seat cleared). "
                         "Gold contacts and a 2.2 kOhm pull-up per foot (D17). Height inside the 7.8 mm slot not verified.")

# Blockers per part key (HARDWARE_AUDIT.md section 6). Status is read from the doc on every run.
BLOCKERS = {
    "servo": ["B2", "B6", "B10", "B17", "B21"], "horn_drive": ["B6"], "horn_idle": ["B6"],
    "battery_pack_lid": ["B3"], "left_roll_to_pitch": ["B4"], "right_roll_to_pitch": ["B4"],
    "left_antenna_holder": ["B5"], "right_antenna_holder": ["B5"], "sg90": ["B5", "B28"],
    "adapter": ["B7"], "speaker_interface": ["B8"], "speaker_stand": ["B8"],
    "flash_light_module": ["B8"], "flash_reflector_interface": ["B8"], "head": ["B9"],
    "bms_cad": ["B12"], "imu": ["B13", "B20"], "left_eye": ["B14"], "right_eye": ["B14"],
    "foot_top": ["B16"], "power_switch": ["B22"], "pi": ["B24"], "foot_bottom_tpu": ["B26"],
    "holder": ["B27", "B28"], "insert": ["B15"],
}
MOUNT = {
    "servo": "Case: M2 self-tapping screws from the servo bag into printed parts (bag split by size is B2). "
             "Horns: M3x6 SHCS (88) or M3x5 (12 short sites) into the horns; horn centre screw from the bag.",
    "horn_drive": "Ships with the servo. Printed part screws to it with M3x6 SHCS (M3x5 at short sites).",
    "horn_idle": "Ships with the servo (idle side). Printed part screws to it with M3x6 SHCS.",
    "bearing": "Press into a 32.19 mm seat (2 in trunk_bottom, 1 in head): 0.19 mm slip fit on a 32.00 bearing (PRINT_CHECK flag 7).",
    "cell": "Molicel P45B cell in the 2S1P pack (D44): spot-welded nickel strip, never soldered; captive in the grown body_back bay with the pack (0.25 mm clear per side, 0.5 mm to the lid pad, a 1 mm foam pad on the pad; twin/battery/BAY.md). Charge both cells to the same voltage first.",
    "holder": "2S1P Molicel P45B pack (D44): no holder; the spot-welded nickel strips and the 2S sleeve hold the 2 cells. Captive in the grown body_back bay, closed by battery_pack_lid: sits on the bay floor ledges, a 1 mm foam pad (BOM 7) on the lid's centre pad, 0.5 mm from the pad at x -121.5 mm, 0.25 mm per side in the cut, 0 overlap with every part (CAD check, twin/battery/BAY.md).",
    "bms_cad": "Sandwiched between body_back and battery_pack_lid, no screws. Free envelope here 17.75 x 47.2 x 5.33 mm (B12).",
    "charger": "body_back: 1 x M2.5x6 into a 2.0 pilot (the 2nd hole has no pilot), USB-C out of the body_back opening.",
    "power_switch": "Held by the body_back cutout (23.4 x 7.4 x 16.8 mm CAD body).",
    "pi": "head.stl: 4 x M2.5x6 DIN 912 into 2.0 pilots, components side up.",
    "adapter": "trunk_top: 4 x M2.5x6 on 4 printed bosses 5 mm high, USB-C toward the neck opening.",
    "imu": "trunk_top: 4 x M2.5x6 (M2.5x8 would bottom out with a 1.6 mm PCB). x forward, chip up. Hole spacing B13, axis signs B20.",
    "sg90": "Hangs from the 7.25 mm head side plate: 2 SG90 bag screws per servo up through the tabs into blind 1.5 mm "
            "pilots 27.5 mm apart, coaxial with the tab holes; the body ends sit in the plate pocket, which stops it turning; "
            "output shaft out through the plate to the ear holder (B5 cleared; twin/companion/ear_mount.json, CAD check only).",
    "antenna": "Optional PLA rod on the antenna holder: in the CAD but not in print/, export it from the URDF mesh (print/PRINT_PLAN.md).",
    "battery_pack_lid": "4 x M2.5x10 DIN 912 into body_back pilots, head sits proud on the lid face (B3 cleared).",
    "left_eye": "4 x M2.5x8 through the bulb and the head wall into the eye (left pilot 2.2 mm, B14).",
    "right_eye": "4 x M2.5x8 through the bulb and the head wall into the eye (pilot 2.05 mm).",
    "bulb": "Clamped between the eye and the head wall by the 4 eye screws. 2 needed (print guide says 1).",
    "speaker_stand": "4 x M2.5x6 into head.stl 2.0 pilots.",
    "speaker_interface": "Holds the speaker on the stand. No clip or screw in CAD (B8).",
    "flash_light_module": "No screw found in CAD. Holds the reflector interface (B8).",
    "flash_reflector_interface": "Reflector seat tapers to 20.0 mm, about 10 mm deep, narrow end 8.07 mm (B8).",
    "left_roll_to_pitch": "2 x M2x6 self-tapping into the servo bottom case pilots 1.67 mm (the CAD has 2 holes per part, B63; B4 cleared), plus M3 horn screws.",
    "right_roll_to_pitch": "2 x M2x6 self-tapping into the servo bottom case pilots 1.67 mm (the CAD has 2 holes per part, B63; B4 cleared), plus M3 horn screws.",
    "left_antenna_holder": "SG90 bag screw onto the SG90 horn (clearance 2.7 in a 5.05 recess, B5 cleared).",
    "right_antenna_holder": "SG90 bag screw onto the SG90 horn (clearance 2.7 in a 5.05 recess, B5 cleared).",
    "foot_top": "2 M3 inserts with a 1.5 mm wall (B16: print 4 perimeters). 2 slots for the Omron SS-10 switches.",
    "insert": "Heat-set with a Pinecil insert tip into a 4.0 mm bore. Depth 5.8 vs 6.7 mm check (B15).",
}
MOUNTING_MATCH = [
    (r"^Raspberry Pi Zero", ["pi"]), (r"^Waveshare", ["adapter"]),
    (r"^BNO055", ["imu"]), (r"^USB-C 2S charger", ["charger"]), (r"^(Control|Power) switch", ["power_switch"]),
    (r"^2S BMS", ["bms_tenergy", "bms_cad"]), (r"^2S1P Molicel P45B pack", ["holder", "cell"]), (r"^battery_pack_lid", ["battery_pack_lid"]),
    (r"^Speaker", ["speaker", "speaker_stand", "speaker_interface"]), (r"^Eyes", ["left_eye", "right_eye", "bulb", "led"]),
    (r"^Projector LED", ["flash_light_module", "flash_reflector_interface"]),
    (r"^Antenna servos", ["sg90", "left_antenna_holder", "right_antenna_holder"]), (r"^Castle CC BEC Pro", ["bec_pro"]),
    (r"^(5 V regulator|HENGE)", ["reg_5v"]), (r"^Fuse holder", ["fuse_holder"]), (r"^Pololu 2815", ["mosfet_switch"]),
    (r"^XT30", ["xt30"]), (r"MAX98357A", ["amp"]), (r"^Foot switch", ["foot_switch"]), (r"^Camera Module", ["camera"]), (r"^I2S microphones", ["mic_l", "mic_r"]),
    (r"^Touch boards", ["tch_h", "tch_b"]), (r"^Cliff sensor", ["tof_cliff"]),
]
# placed boxes follow this part in the explode when it is within 6 mm (the lab's stated mounting surface)
FOLLOW_HINT = {"mosfet_switch": "battery_pack_lid", "fuse_holder": "battery_pack_lid", "bec_pro": "body_middle_bottom",
               "reg_5v": "head_bot_sheet", "camera": "head", "bms_tenergy": "bms_cad"}
LABEL = {"head": "Head shell", "foot_bottom_tpu": "Foot sole (TPU)", "foot_bottom_pla": "Foot bottom plate",
         "left_cache": "Left leg cover", "right_cache": "Right leg cover", "bulb": "Eye bulb",
         "trunk_top": "Trunk top frame", "trunk_bottom": "Trunk bottom frame"}

# How each BOM line shows in the model (line id -> kind, part keys, note)
BOM_VIEW = {
    "1": ("cad", ["servo"], ["horn_drive", "horn_idle"], "12 STS3215 servos (the knees are line 1b), each 3 case parts plus 2 horns"),
    "1b": ("cad", ["servo"], ["horn_drive", "horn_idle"], "the 2 STS3250 knee servos (D32): the same outline, so the same case meshes"),
    "2": ("cad", ["adapter"], [], "board.stl on trunk_top. A copy of board.stl also sits in the head as the Pi footprint (B7)"),
    "3": ("cad", ["pi"], [], ""), "4": ("none", [], [], "Inside the Pi, not modelled"),
    "5": ("cad", ["imu"], [], ""), "6": ("cad", ["cell"], [], ""), "7": ("cad", ["holder"], [], ""),
    "8": ("placeholder", ["bms_tenergy"], ["bms_cad"], "Placeholder in the upstream bms.stl slot; the CAD body is kept and marked replaced"),
    "9": ("placeholder", ["reg_5v"], [], "Pololu step-down size, about 18 x 18 x 8"),
    "10": ("placeholder", ["mosfet_switch"], [], ""),
    "5b": ("placeholder", ["tof_cliff"], [], "In the chest of body_front, 52 deg down (D54)"),
    "10r": ("none", [], [], "Replaced by line 10 (D30), quantity 0"), "10b-old": ("none", [], [], "Replaced by line 10b (D30), quantity 0"),
    "E7r": ("none", [], [], "Replaced by line E7 (D34), quantity 0"),
    "10b": ("cad", ["power_switch"], [], "The CAD power_switch body in the body_back cutout"),
    "11": ("cad", ["charger"], [], ""), "12": ("placeholder", ["xt30", "xt30_p13"], [], "2 mated pairs used of the 10 bought: the battery disconnect and the P13 service plug (X3a, D36)"),
    "13": ("placeholder", ["foot_switch"], [], "In the foot_top slots"), "14": ("cad", ["sg90"], [], ""),
    "13b": ("none", [], [], "Resistor, leads soldered at the Pi header (D17)"),
    "L1": ("placeholder", ["bec_pro"], [], ""), "L3": ("placeholder", ["fuse_holder"], [], "Dims not verified"),
    "L4": ("none", [], [], "Sits in the L3 holder"), "16": ("cad", ["insert"], [], "Drawn from the measured bores"),
    "18": ("cad", ["bearing"], [], ""), "19": ("none", [], [], "Consumable"),
    "17a": ("none", [], [], "Screw"), "17b": ("none", [], [], "Screw"), "17c": ("none", [], [], "Screw"),
    "17d": ("none", [], [], "Screw"), "17e": ("none", [], [], "Screw"), "17f": ("none", [], [], "Screw"),
    "17g": ("none", [], [], "Screw"), "17i": ("none", [], [], "Screw"), "17h": ("none", [], [], "Screw kit"),
    "17j": ("none", [], [], "Screw"), "17k": ("none", [], [], "Screw"), "17l": ("none", [], [], "Washer"),
    "20": ("none", [], [], "Cable"), "21": ("none", [], [], "Connector"), "22": ("none", [], [], "Crimp terminal"),
    "L5": ("none", [], [], "Wire"), "23": ("none", [], [], "Wire"), "24": ("none", [], [], "Wire"), "25": ("none", [], [], "Wire"),
    "26": ("none", [], [], "Heat shrink"), "29": ("none", [], [], "Foam tape"),
    "15": ("none", [], [], "Off-robot accessory, not modelled"),
    "27": ("filament", ["pla"], [], "Printed parts"), "28": ("filament", ["tpu"], [], "Printed parts"),
    "E1": ("placeholder", ["speaker"], [], ""), "E2": ("placeholder", ["amp"], [], ""),
    "E3": ("placeholder", ["led"], [], "3 beads: 2 eyes, 1 projector"), "E3b": ("none", [], [], "Resistor"),
    "E4": ("none", [], [], "Glass disc, not modelled"), "E5": ("none", [], [], "Reflector, not modelled"),
    "E6": ("placeholder", ["camera"], [], ""), "E8": ("placeholder", ["mic_l", "mic_r"], [], "2 boards, one per side wall"), "E9": ("placeholder", ["tch_h", "tch_b"], [], "2 boards: head roof and body side wall (D51)"), "E10": ("none", [], [], "Copper foil pads on the inner shells (twin/freeze/touch_pads.json), not modelled"), "DK1": ("placeholder", ["dock_pad"], [], ""), "DK2": ("placeholder", ["dock_dk2"], [], ""), "DK3": ("placeholder", ["dock_f2"], [], ""), "DK4": ("none", [], [], "Fuse in the DK3 holder"), "DK5": ("none", [], [], "Small parts on the leads"), "DK6": ("placeholder", ["dock_dk6"], [], ""), "DK7": ("placeholder", ["dock_dk7"], [], ""), "E7": ("none", [], [], "Cable"),
    "T1": ("none", [], [], "Tool"), "T2": ("none", [], [], "Tool"), "T3": ("none", [], [], "Tool"),
    "T4": ("none", [], [], "Tool"), "T5": ("none", [], [], "Tool"), "L2": ("none", [], [], "Tool"),
}


# ---------------------------------------------------------------------------------------------- docs
def md_tables(path):
    """Every pipe table in a markdown file: list of dict(section, header, rows)."""
    out, section = [], ""
    lines = open(path, encoding="utf-8").read().splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("#"):
            section = ln.lstrip("#").strip()
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|\s*:?-{2,}", lines[i + 1]):
            header = [c.strip() for c in ln.strip().strip("|").split("|")]
            rows = []
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(dict(zip(header, cells)))
                i += 1
            out.append(dict(section=section, header=header, rows=rows))
            continue
        i += 1
    return out


def num(s):
    m = re.match(r"\s*([0-9]+(?:\.[0-9]+)?)", s or "")
    return float(m.group(1)) if m else None


def load_docs():
    pc = [t for t in md_tables(os.path.join(LAB, "PRINT_CHECK.md")) if t["header"][:2] == ["STL", "Qty"] and "g each" in t["header"]]
    if not pc:
        sys.exit("PRINT_CHECK.md: per-STL table not found")
    printed = {}
    for r in pc[0]["rows"]:
        stem = r["STL"].replace(".stl", "")
        mat = r.get("Material/infill", "")
        printed[stem] = dict(qty=int(num(r["Qty"])), material=mat, cat="tpu" if "TPU" in mat else "pla",
                             g_each=num(r.get("g each")), h_each=num(r.get("h each")),
                             g_total=num(r.get("g total")), h_total=num(r.get("h total")),
                             flags=r.get("Flags", ""), inserts=r.get("Inserts", ""), orient=r.get("Orientation", ""),
                             footprint=r.get("Footprint mm", ""), height=r.get("Height mm", ""), bed=r.get("Bed fit", ""))
    # print grams and hours of the D22 light profile (DECISIONS.md D22) from print/SLICE_SUMMARY.md, used when that table is
    # clean: the same STLs and quantities as PRINT_CHECK.md and its parts add up to its Total row. PRINT_CHECK.md (7:24 PM ET
    # run, before D22) stays the source of the geometry columns (orientation, bed fit, flags) and the fallback for the grams.
    global PRINT_SOURCE
    ss = [t for t in md_tables(SLICE_SUMMARY) if t["header"][:2] == ["STL", "Qty"] and "g each" in t["header"]] \
        if os.path.exists(SLICE_SUMMARY) else []
    tot = [r for t in (md_tables(SLICE_SUMMARY) if ss else []) if t["header"][:4] == ["Material", "Parts", "Grams", "Hours"]
           for r in t["rows"] if r["Material"].strip().lower() == "total"]
    why = "print/SLICE_SUMMARY.md has no per-part table" if not ss else ""
    if ss:
        d22 = {r["STL"].replace(".stl", ""): r for r in ss[0]["rows"]}
        if {k: int(num(v["Qty"])) for k, v in d22.items()} != {k: v["qty"] for k, v in printed.items()}:
            why = "print/SLICE_SUMMARY.md per-part STLs or quantities differ from PRINT_CHECK.md"
        elif not tot:
            why = "print/SLICE_SUMMARY.md has no Total row"
        else:
            g_sum = sum(num(v["g each"]) * int(num(v["Qty"])) for v in d22.values())
            if abs(g_sum - num(tot[0]["Grams"])) > 0.5:
                why = "print/SLICE_SUMMARY.md parts add up to %.1f g, its Total row says %s g" % (g_sum, tot[0]["Grams"])
    if why:
        PRINT_SOURCE = dict(doc="PRINT_CHECK.md", note=why + ": print grams from PRINT_CHECK.md (before D22)")
        print("print grams: " + PRINT_SOURCE["note"])
    else:
        for stem, v in d22.items():
            printed[stem].update(material="%s, %s" % (v["Material"], v["Profile"]), g_each=num(v["g each"]),
                                 h_each=num(v["h each"]), g_total=num(v["g total"]), h_total=num(v["h total"]))
        PRINT_SOURCE = dict(doc="print/SLICE_SUMMARY.md", total=dict(parts=num(tot[0]["Parts"]), grams=num(tot[0]["Grams"]),
                                                                    hours=num(tot[0]["Hours"])),
                            note="D22 light profile, PrusaSlicer 2.7.2 estimates (print/SLICE_SUMMARY.md per part table)")
    bom = []
    for t in md_tables(os.path.join(LAB, "BOM.md")):
        if t["header"][:2] != ["#", "Item"] or "Need" not in t["header"]:
            continue
        for r in t["rows"]:
            bom.append(dict(line=r["#"], section=t["section"], item=r["Item"], spec=r.get("Spec", ""),
                            need=r.get("Need", ""), buy=r.get("Buy", ""), supplier=r.get("Supplier", ""),
                            verified=r.get("Verified", "")))
    blockers = {}
    for t in md_tables(os.path.join(LAB, "HARDWARE_AUDIT.md")):
        if t["header"][:3] == ["#", "Blocker", "Status"]:
            for r in t["rows"]:
                if re.match(r"^B\d+$", r["#"]):
                    st = r["Status"]
                    closed = st.upper().startswith(("CLEARED", "DECIDED"))
                    blockers[r["#"]] = dict(title=r["Blocker"], status=st, open=not closed,
                                            how=r.get("How verified, or what is still needed", ""))
    if not blockers:
        sys.exit("HARDWARE_AUDIT.md: section 6 blocker table not found")
    mounting = {}
    for t in md_tables(os.path.join(LAB, "MOUNTING.md")):
        if t["header"][:1] == ["Component"]:
            for r in t["rows"]:
                for pat, keys in MOUNTING_MATCH:
                    if re.search(pat, r["Component"], re.I):
                        for k in keys:
                            mounting.setdefault(k, dict(component=r["Component"], mounts_to=r.get("Printed part it mounts to", ""),
                                                        screw=r.get("Screw", ""), orientation=r.get("Orientation", ""),
                                                        status=r.get("Status", "")))
                        break
    return printed, bom, blockers, mounting


FASTENERS_JSON = os.path.join(LAB, "fasteners", "fasteners.json")
CABLES3D_JSON = os.path.join(LAB, "cables3d", "cables3d.json")
SLICE_SUMMARY = os.path.join(LAB, "print", "SLICE_SUMMARY.md")      # D22 print grams (load_docs)
PRINT_SOURCE = {}
SCREW_PULL = 9.0                       # stage-3 pull of a screw out of its hole, mm
SCREW_COLOR = {"M3": "#8f9aa5", "M2.5": "#b4bcc4", "M2": "#d2d7db"}
HEAD_DEFAULT = {  # DIN 912 socket head (dk, k) and pan head sizes, mm (ISO 4762 / ISO 7045 nominal)
    ("SHCS", 3.0): (5.5, 3.0), ("SHCS", 2.5): (4.5, 2.5), ("SHCS", 2.0): (3.8, 2.0),
    ("pan", 2.0): (4.0, 1.6), ("pan", 2.6): (5.0, 2.1), ("pan", 3.0): (5.6, 2.4),
}


def _first(rec, *keys, default=None):
    for k in keys:
        if isinstance(rec, dict) and rec.get(k) is not None:
            return rec[k]
    return default


def load_fasteners(path=FASTENERS_JSON):
    """altaay_lab/fasteners/fasteners.json -> normalized screws in URDF world mm (zero pose). [] if absent."""
    if not os.path.exists(path):
        return [], "fasteners.json not found: no screws drawn"
    raw = json.load(open(path))
    recs = raw.get("fasteners", raw.get("instances", raw)) if isinstance(raw, dict) else raw
    out, skipped = [], Counter()
    for r in recs:
        kind = str(_first(r, "kind", "type", default="screw")).lower()
        if "insert" in kind or "bearing" in kind:
            skipped[kind] += 1          # inserts and bearings are drawn from the CAD already
            continue
        if str(r.get("status") or "").startswith(("LEAVE OUT", "NOT FITTED")):
            skipped["left out or not fitted"] += 1     # D18, D38 and the idle horn screws: not drawn, not counted
            continue
        pose = r.get("pose") if isinstance(r.get("pose"), dict) else {}
        world = pose.get("world") if isinstance(pose.get("world"), dict) else pose
        p = _first(world, "head", "p", "head_mm", "pos") if world else None
        p = p if p is not None else _first(r, "seat_world", "head_world_mm", "head_world", "p_world", "head_point", "pos", "p")
        ax = _first(world, "axis", "ax") if world else None
        ax = ax if ax is not None else _first(r, "axis_world", "ax_world", "axis", "ax")
        size = str(_first(r, "size", default="M3"))
        L = _first(r, "length_mm", "length", "len", "L")
        from_drawing = L is None and r.get("draw_length_mm") is not None
        if from_drawing:                # no stock length chosen (factory case screws, SG90 bag): draw the drawing's length
            L = r["draw_length_mm"]
        if p is None or ax is None or L is None:
            skipped["no pose or length"] += 1
            continue
        d = float(_first(r, "d", default=None) or re.sub(r"[^0-9.]", "", size) or 3.0)
        hrec = r.get("head") if isinstance(r.get("head"), dict) else {}
        head = str(hrec.get("type") if hrec else _first(r, "head", "head_type", default="SHCS"))
        head_key = "pan" if re.search(r"pan|self|7045|7981|tapping", head, re.I) else "SHCS"
        hd, hh = HEAD_DEFAULT.get((head_key, d), (d * 1.85, d))
        if hrec.get("dk"):
            hd, hh = float(hrec["dk"]), float(hrec.get("k") or hh)
        sweep = r.get("sweep") if isinstance(r.get("sweep"), dict) else {}
        flags = [x for x in (r.get("len_status"), sweep.get("status")) if x and str(x).upper() not in ("OK", "PASS")]
        ax = np.array(ax, float)
        ax /= np.linalg.norm(ax)
        # a screw with washers under its head (the eye screws, DECISIONS.md D21 note): the seat is the part face, so the
        # screw is drawn washer.t further out, its head on the washer stack (fasteners/VIEWER_NOTE.md "What to draw")
        wrec = r.get("washer") if isinstance(r.get("washer"), dict) else None
        washer = None
        if wrec:
            wl = re.search(r"\bBOM (?:line )?(\d+[a-z]?)\b", str(wrec.get("spec", "")))
            washer = dict(t=float(wrec.get("t", 0.0)), n=int(wrec.get("n", 1)), t_each=float(wrec.get("t_each", wrec.get("t", 0.0))),
                          spec=str(wrec.get("spec", "")), line=wl.group(1) if wl else "")
            p = np.array(p, float) - ax * washer["t"]
        joins = r.get("joins") if isinstance(r.get("joins"), list) else None
        note = "; ".join([str(x) for x in (r.get("notes") or [])] + ([sweep["worst_text"]] if sweep.get("worst_text") else [])) or str(_first(r, "note", default=""))
        if from_drawing:
            note = "; ".join(x for x in (note, "length from the drawing, not yet chosen") if x)
        out.append(dict(
            fid=str(_first(r, "id", "fid", default="F%03d" % (len(out) + 1))), size=size, d=d, L=float(L), head=head,
            head_d=float(_first(r, "head_d", default=hd)), head_h=float(_first(r, "head_h", default=hh)),
            p=np.array(p, float), ax=ax, part=_first(r, "part", "head_part", default=(joins or [None])[0]),
            into=_first(r, "into", "anchor_part", default=(joins or [None, None])[1]),
            anchor=_first(r, "anchor", "anchor_type", default=""), link=_first(r, "link"),
            line=str(_first(r, "line", "bom", "bom_line", default="") or ""),
            supplied=_first(r, "supplied", "supply", default="bought"),
            engagement=_first(r, "engagement_mm", "e", "engagement"),
            status=("; ".join(str(f) for f in flags) if flags else _first(r, "status", default="OK")),
            note=note,
            spec_label=_first(r, "spec", "label", default=None), color=r.get("color"), viewer_label=r.get("viewer_label"),
            flags=flags, from_drawing=from_drawing, washer=washer, fit=not (r.get("leave_out") or r.get("install") is False),
            fit_note=("left out (%s)" % (r.get("status") or "D18")) if r.get("leave_out") else
                     ("stays in the bag, not fitted" if r.get("install") is False else "")))
    n_draw = sum(1 for s in out if s["from_drawing"])
    return out, "%d screws from altaay_lab/fasteners/fasteners.json%s%s" % (
        len(out), (", %d with the length from the drawing, not yet chosen" % n_draw) if n_draw else "",
        (" (not drawn: %d screws left out or not fitted; inserts are drawn from the CAD bores, %d insert rows in fasteners.json of which %d left out)" % (
            skipped.get("left out or not fitted", 0), skipped.get("insert", 0), sum(1 for r in recs if "insert" in str(r.get("kind", "")).lower() and r.get("leave_out")))) if skipped else "")


def _wire_line(w):
    """one cables3d wire record as a short line: '16 AWG red 120 mm PACK.B+ to BMS.B+'"""
    cut = w.get("cut_mm")
    cut = ("%g mm" % cut) if isinstance(cut, (int, float)) else (("%s mm" % cut) if cut else "")
    return " ".join(str(x) for x in (w.get("gauge"), w.get("color"), cut, "%s to %s" % (w.get("from", "?"), w.get("to", "?"))) if x)


def load_cables3d(path=CABLES3D_JSON):
    """altaay_lab/cables3d/cables3d.json -> list of cables with points as (link, xyz in that link's frame, mm). [] if absent."""
    if not os.path.exists(path):
        return [], "cables3d.json not found: no cables drawn"
    raw = json.load(open(path))
    recs = raw.get("cables", raw) if isinstance(raw, dict) else raw
    out = []
    expanded = []
    for c in recs:   # a cable with branches has several runs: draw each run as its own tube
        runs = c.get("runs") or []
        if len(runs) > 1:
            for k, rn in enumerate(runs):
                e = dict(c)
                e["points"] = rn.get("points") or []
                e["run"] = rn.get("name") or "run %d" % (k + 1)
                e["run_k"] = k
                e["d_mm"] = rn.get("d_mm", c.get("d_mm"))
                if rn.get("length_max_mm") is not None:
                    e["length_max_mm"] = rn["length_max_mm"]
                    e["length_zero_mm"] = rn.get("length_zero_mm")
                expanded.append(e)
        else:
            expanded.append(c)
    for c in expanded:
        pts = []
        for q in c.get("points", []):
            if isinstance(q, dict):
                pts.append((q.get("link"), _first(q, "p", "xyz", "local", "p_link"), _first(q, "world", "p_world")))
            elif isinstance(q, (list, tuple)) and len(q) >= 4:
                pts.append((q[3], q[:3], None))
        if c.get("points_world") is not None:
            links = c.get("links") or [None] * len(c["points_world"])
            pts = [(l, None, w) for l, w in zip(links, c["points_world"])]
        # check is "pass", "test fit", "fail" or "": cables3d also writes "pass with notes"; the full text and the notes go
        # in the note. "test fit": the cable reaches but has less than the 2 x 20 mm slack (cables3d/check_cables.py; the
        # TEST_PLAN 1.4 test fit decides); "fail" only when it cannot reach
        chk_raw = str(_first(c, "check", "result", "status", default="")).strip()
        chk = "pass" if chk_raw.lower().startswith("pass") else ("test fit" if chk_raw.lower().startswith("test fit") else
                                                                 ("fail" if chk_raw.lower().startswith("fail") else ""))
        fnd = c.get("findings")
        notes = (["check: " + chk_raw] if chk_raw.lower() != chk else []) + [c.get("note")] + (fnd if isinstance(fnd, list) else [fnd])
        # wires may be a list of wire records: the page gets a count and one short line per wire
        wl = c.get("wires")
        detail = [_wire_line(x) for x in wl if isinstance(x, dict)] if isinstance(wl, list) else []
        out.append(dict(id=c["id"], run=c.get("run"), run_k=c.get("run_k", 0), seats=c.get("seats") or [],
                        desc=c.get("desc", ""), pts=pts, color=_first(c, "color", "colour", default="#e07a1f"),
                        d=float(_first(c, "d_mm", "outer_d_mm", "diameter_mm", "od_mm", default=3.0)),
                        frm=_first(c, "from", default=""), to=_first(c, "to", default=""), gauge=_first(c, "gauge", default=""),
                        wires=len(wl) if isinstance(wl, list) else _first(c, "wires", "n_wires", "wires_n", default=None),
                        wires_detail=detail, cut_mm=_first(c, "cut_mm", default=None),
                        routed_mm=_first(c, "length_zero_mm", "routed_mm", "length_mm", default=None),
                        worst_mm=_first(c, "length_max_mm", "worst_mm", "max_mm", default=None),
                        check=chk, note="; ".join(OrderedDict.fromkeys(str(x) for x in notes if x))))
    return out, "%d cables from altaay_lab/cables3d/cables3d.json" % len(out)


def load_cables3d_extras(path=CABLES3D_JSON):
    """terminals (seats for the parts the CAD lacks) and retention items (ties, mounts, guides) from cables3d.json."""
    if not os.path.exists(path):
        return [], []
    raw = json.load(open(path))
    if not isinstance(raw, dict):
        return [], []
    return raw.get("terminals") or [], raw.get("retention") or []


# heat shrink sleeves of scene_extras.json that blueprint/make_scene_extras.py set at a fixed distance from a cables3d.json
# seat (cable_ends id, distance in mm, from its code): step 10e warns when the seat has moved away from them
SLEEVE_OFFSET = {"splice-JBP": ("JB", 4.5), "splice-JBN": ("JB", 4.5), "splice-YD3": ("Y.SD1", 2.5), "splice-YG3": ("Y.SD1", 2.5),
                 "hs-R1-LED": ("LEDL", 1.0), "hs-R2-LED": ("LEDR", 1.0), "hs-R3-LED": ("LEDP", 1.0),
                 "hs-P10-BEC-INp": ("U1.IN", 6.5), "hs-P10-BEC-INn": ("U1.IN", 6.5),
                 "hs-U1-OUT1S": ("JB", 14.15), "hs-U1-OUT2S": ("JB", 14.15),
                 "hs-XT30-Fp": ("XT30.F", 2.69), "hs-XT30-Fn": ("XT30.F", 2.69), "hs-XT30-Mp": ("XT30.M", 2.69),
                 "hs-XT30-Mn": ("XT30.M", 2.69)}
LEAD_GAUGES = ("resistor lead", "BEC lead", "SG90 lead")


def _unit(v):
    v = np.asarray(v, float)
    n = float(np.linalg.norm(v))
    return v / n if n else v


def _side(t):
    """a unit vector square to t (horizontal when t is not vertical)"""
    t = _unit(t)
    return _unit(np.cross(t, [0, 0, 1.0])) if abs(t[2]) < 0.9 else _unit(np.cross(t, [1.0, 0, 0]))


def bundle_od(ods):
    """outside diameter of a bundle of wires (blueprint/make_scene_extras.py: 1.155 d sqrt(n) packing)"""
    n, d = len(ods), max(ods)
    return d if n == 1 else (2.0 * d if n == 2 else 1.155 * d * np.sqrt(n))


def _walk(points, start, dist):
    """point and direction dist mm along a polyline from its end nearest start; also the gap from start to that end"""
    P = np.array(points, float)
    if np.linalg.norm(P[-1] - start) < np.linalg.norm(P[0] - start):
        P = P[::-1]
    gap = float(np.linalg.norm(P[0] - start))
    seg = np.diff(P, axis=0)
    sl = np.linalg.norm(seg, axis=1)
    acc = 0.0
    for k in range(len(seg)):
        if sl[k] < 1e-9:
            continue
        if acc + sl[k] >= dist:
            return P[k] + seg[k] * (dist - acc) / sl[k], seg[k] / sl[k], gap, float(sl.sum())
        acc += sl[k]
    k = int(np.nonzero(sl > 1e-9)[0][-1])
    return P[-1], seg[k] / sl[k], gap, float(sl.sum())


def _anchor_id(pin, comps, E3):
    """the cables3d.json cable_ends id for a netlist pin: the pin, the pin without its sign, COMP.GROUP, or COMP"""
    comp, p = (pin.split(".", 1) + [""])[:2]
    grp = next((x.get("group") for x in (comps.get(comp) or {}).get("pins") or [] if x.get("pin") == p), "")
    for k in (pin, pin.rstrip("+-"), "%s.%s" % (comp, str(grp or "").upper()), comp):
        if k in E3:
            return k
    return None


def place_sleeve(j, netlist, E3, runs_of, od_of):
    """Where to draw one heat shrink sleeve of bom_full.sleeve_joints, from cables3d.json cable_ends (E3) and the routed
    runs of this build (runs_of: cable id -> cables_out entries, world mm). Returns (candidates, (length, diameter), info):
    candidates in order of preference, each (centre, axis, text); step 10f draws the first that lies in no CAD part.
    None when no seat or route places it."""
    comps = {c["id"]: c for c in netlist["components"]}
    act = {c["id"] for c in netlist["cables"] if c.get("status", "active") == "active"}
    ods = [od_of[g] for g in j["gauges"] if od_of.get(g)]
    P = lambda k: np.array(E3[k]["p_world0"], float)        # noqa: E731
    Dn = lambda k: _unit(E3[k].get("dir_world0") or [1, 0, 0])   # noqa: E731

    def near_run(cables, a):
        runs = [r for c_ in cables for r in runs_of.get(c_, []) if len(r["points"]) >= 2]
        if not runs:
            return None
        return min(runs, key=lambda r: min(np.linalg.norm(np.array(r["points"][0]) - a), np.linalg.norm(np.array(r["points"][-1]) - a)))

    if j["kind"] == "splice":
        L, D = 20.0, (bundle_od(ods) if ods else 3.0) + 1.0
        info = dict(size="sleeve %g x %.1f mm, the blueprint splice stand-in (bundle of the wire outside diameters + 1.0 mm "
                         "shrink wall), UNVERIFIED" % (L, D))
        if j["name"] in E3:
            info["anchor"] = j["name"]
            return [(P(j["name"]), Dn(j["name"]), "its cables3d.json seat %s" % j["name"])], (L, D), info
        # an inline splice on a routed run (P7 JFI and JFO): the made piece (not a part's own lead) sets how far along the
        # run it sits from that piece's fixed end, the rule cables3d uses for its splices ('N mm along the route', netlist
        # length); if that spot is inside a part, 2 mm steps either way along the run
        at = [w for w in netlist["wires"] if w["cable"] in act and j["name"] in (w["from"].split(".")[0], w["to"].split(".")[0])]
        made = [w for w in at if w.get("color") != "holder lead" and w.get("gauge") not in LEAD_GAUGES
                and isinstance(w.get("cut_mm"), (int, float))]
        for w in sorted(made, key=lambda w: w["cut_mm"]):
            far = w["to"] if w["from"].split(".")[0] == j["name"] else w["from"]
            aid = _anchor_id(far, comps, E3)
            best = near_run([w["cable"]], P(aid)) if aid else None
            if best is None:
                continue
            info["anchor"] = aid
            cands = []
            for dd in [0.0] + [s * k for k in (2.0, 4.0, 6.0, 8.0, 10.0) for s in (1, -1)]:
                q, tq, gap, total = _walk(best["points"], P(aid), max(0.0, float(w["cut_mm"]) + dd))
                cands.append((q, tq, "%g mm along the routed %s %s run (%.1f mm) from %s: the netlist cut of %s to %s, as "
                                     "cables3d places its splices on a run%s" % (
                                         w["cut_mm"] + dd, w["cable"], best.get("run") or "main", total, aid, w["from"], w["to"],
                                         (" (moved %+g mm along the run to clear the CAD parts)" % dd) if dd else "")))
            return cands, (L, D), info
        return None
    if j["kind"] not in ("wire to lead", "lead to lead"):
        return None                                       # XT30 cups and lead caps: scene_extras.json draws them
    comp = j["part"]
    ck = (comps.get(comp) or {}).get("kind")
    L, D = (12.0, 4.5) if ods and max(ods) >= 2.5 else (6.0, 3.0)
    info = dict(size="sleeve %g x %.1f mm, UNVERIFIED stand-in as the blueprint sleeves on the BEC input (12 x 4.5) and LED "
                     "(6 x 3) lead joints" % (L, D))
    if ck == "resistor":
        # inline at its LED (netlist: its other lead is soldered to the LED lead): this joint is past the resistor body,
        # which blueprint draws 2.0 to 8.3 mm out of the LED lead exit
        led = next((w[s] for w in netlist["wires"] if w["cable"] in act and w.get("gauge") == "resistor lead"
                    for s, o in (("to", "from"), ("from", "to")) if w[o].split(".")[0] == comp), None)
        aid = _anchor_id(led, comps, E3) if led else None
        if not aid:
            return None
        info["anchor"] = aid
        return [(P(aid) + Dn(aid) * x, Dn(aid), "%.1f mm out of the %s lead exit along its cables3d.json direction: past the "
                 "inline resistor body, which blueprint draws 2.0 to 8.3 mm out" % (x, aid)) for x in (11.3, 13.3, 15.3)], (L, D), info
    aid = _anchor_id(j["name"], comps, E3)
    if not aid:
        return None
    a, d = P(aid), Dn(aid)
    info["anchor"] = aid
    if ck == "led":
        # beside the anode joint sleeve (blueprint hs-R*-LED, 1.0 mm out), on any side; where no side is free (the projector
        # LED's 4 mm lead channel) staggered along the leads behind the resistor-side joint
        s1, s2 = _side(d), _unit(np.cross(d, _side(d)))
        cands = [(a + d * 1.0 + v * 3.0, d, "1.0 mm out of the %s lead exit, 3.0 mm beside the anode joint sleeve (blueprint "
                  "hs-R*-LED)" % aid) for v in (s1, -s1, s2, -s2)]
        cands += [(a + d * x, d, "%.1f mm out of the %s lead exit on the lead axis: no room beside the anode joint, so the "
                   "cathode joint is staggered behind the resistor and its far joint" % (x, aid)) for x in (17.3, 19.3, 21.3)]
        return cands, (L, D), info
    # a part's own lead of unpublished length (holder, BEC): 6 mm along the route from the lead exit, as blueprint draws the
    # BEC input joints, + and - joints 2.5 mm to either side; further along in 2 mm steps if that spot is inside a part
    sign = 1.0 if j["name"].endswith("+") else (-1.0 if j["name"].endswith("-") else 0.0)
    best = near_run(j["cables"], a)
    cands = []
    if best is not None:
        for x in np.arange(6.0, 31.0, 2.0):
            q, tq, gap, total = _walk(best["points"], a, float(x))
            if gap >= 5.0:
                continue
            for off in OrderedDict.fromkeys((2.5 * sign, 0.0, -2.5 * sign)):
                cands.append((q + _side(tq) * off, tq, "%g mm along the routed %s run from the %s lead exit, %+.1f mm to the "
                              "side: the lead length is not published, so the real joint sits further along, as blueprint draws "
                              "the BEC input joints" % (x, best["cable"], aid, off)))
    cands.append((a + d * 6.0 + _side(d) * 2.5 * sign, d, "6 mm out of the %s lead exit along its cables3d.json direction, "
                  "%+.1f mm to the side" % (aid, 2.5 * sign)))
    return cands, (L, D), info


# ---------------------------------------------------------------------------------------------- geometry
def load_mesh(path, to_mm):
    m = trimesh.load(path, force="mesh")
    if to_mm:
        m.apply_scale(1000.0)
    return m


def web_geometry(m, target, angle_deg=32.0):
    """Decimate to about `target` faces and split vertices at sharp edges (the page computes normals)."""
    v, f = np.asarray(m.vertices, np.float64), np.asarray(m.faces, np.int64)
    if len(f) > target * 1.05:
        import fast_simplification
        v, f = fast_simplification.simplify(v, f, target_reduction=1.0 - target / len(f))
    mm = trimesh.Trimesh(v, f, process=True)
    sm = trimesh.graph.smooth_shade(mm, angle=np.radians(angle_deg), facet_minarea=None)
    return np.asarray(sm.vertices, np.float32), np.asarray(sm.faces, np.uint32)


def face_target(n, key):
    caps = {"servo_bottom": 5000, "servo_top": 3600, "servo_mid": 1000, "horn_drive": 900, "horn_idle": 900,
            "pi": 7000, "adapter": 3000, "cell": 1200}
    if key in caps:
        return min(n, caps[key])
    return n if n <= 5000 else int(min(16000, 5000 + 0.4 * (n - 5000)))


def cylinder(d, length, seg=20):
    r, h = d / 2.0, length / 2.0
    a = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    ring = np.c_[r * np.cos(a), r * np.sin(a)]
    side = np.vstack([np.c_[ring, np.full(seg, -h)], np.c_[ring, np.full(seg, h)]])
    top = np.vstack([[0, 0, h], np.c_[ring, np.full(seg, h)]])
    bot = np.vstack([[0, 0, -h], np.c_[ring, np.full(seg, -h)]])
    V = np.vstack([side, top, bot]).astype(np.float32)
    F = []
    for i in range(seg):
        j = (i + 1) % seg
        F += [[i, j, seg + j], [i, seg + j, seg + i]]
    o = 2 * seg
    F += [[o, o + 1 + i, o + 1 + (i + 1) % seg] for i in range(seg)]
    o2 = o + seg + 1
    F += [[o2, o2 + 1 + (i + 1) % seg, o2 + 1 + i] for i in range(seg)]
    return V, np.array(F, np.uint32)


def unit_box():
    V, F = [], []
    for axis in range(3):
        for s in (-0.5, 0.5):
            u, w = [(axis + 1) % 3, (axis + 2) % 3]
            quad = []
            for a, b in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)):
                p = [0, 0, 0]
                p[axis], p[u], p[w] = s, a, b
                quad.append(p)
            base = len(V)
            V += quad
            F += [[base, base + 1, base + 2], [base, base + 2, base + 3]] if s > 0 else [[base, base + 2, base + 1], [base, base + 3, base + 2]]
    return np.array(V, np.float32), np.array(F, np.uint32)


def screw_mesh(d, length, head_d, head_h, seg=14):
    """Screw in its own frame: head on +z from 0 to head_h, shank on -z from 0 to -length (mm)."""
    sv, sf = cylinder(d, length, seg)
    sv = sv + np.array([0, 0, -length / 2.0], np.float32)
    hv, hf = cylinder(head_d, head_h, seg)
    hv = hv + np.array([0, 0, head_h / 2.0], np.float32)
    return np.vstack([sv, hv]).astype(np.float32), np.vstack([sf, hf + len(sv)]).astype(np.uint32)


def rot_z_to(ax):
    z = np.array(ax, float) / np.linalg.norm(ax)
    t = np.array([1.0, 0, 0]) if abs(z[0]) < 0.9 else np.array([0, 1.0, 0])
    x = np.cross(t, z); x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.c_[x, y, z]


def write_glb(path, geoms, nodes):
    blob, views, accs, meshes = bytearray(), [], [], []

    def view(data, target):
        while len(blob) % 4:
            blob.append(0)
        views.append(dict(buffer=0, byteOffset=len(blob), byteLength=len(data), target=target))
        blob.extend(data)
        return len(views) - 1

    for g in geoms:
        p = np.ascontiguousarray(g["pos"], np.float32)
        ap = len(accs)
        accs.append(dict(bufferView=view(p.tobytes(), 34962), componentType=5126, count=int(len(p)), type="VEC3",
                         min=[round(float(x), 4) for x in p.min(0)], max=[round(float(x), 4) for x in p.max(0)]))
        idx = np.ascontiguousarray(g["idx"]).ravel()
        small = len(p) < 65536
        ai = len(accs)
        accs.append(dict(bufferView=view(idx.astype(np.uint16 if small else np.uint32).tobytes(), 34963),
                         componentType=5123 if small else 5125, count=int(idx.size), type="SCALAR"))
        meshes.append(dict(name=g["name"], primitives=[dict(attributes=dict(POSITION=ap), indices=ai, mode=4)]))
    gn = [dict(name="duck", rotation=[-0.70710678, 0, 0, 0.70710678], scale=[0.001, 0.001, 0.001],
               children=list(range(1, len(nodes) + 1)),
               extras=dict(units="mm", frame="URDF zero pose: x forward, y left, z up"))]
    for n in nodes:
        M = np.asarray(n["matrix"], float)
        gn.append(dict(name=n["name"], mesh=n["mesh"], matrix=[round(float(x), 6) for x in M.T.ravel()],
                       extras=dict(id=n["name"])))
    gltf = dict(asset=dict(version="2.0", generator="altaay_lab/viewer/make_viewer_data.py"), scene=0,
                scenes=[dict(nodes=[0])], nodes=gn, meshes=meshes, accessors=accs, bufferViews=views,
                buffers=[dict(byteLength=len(blob))])
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    while len(blob) % 4:
        blob.append(0)
    with open(path, "wb") as fh:
        fh.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob)))
        fh.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        fh.write(struct.pack("<II", len(blob), 0x004E4942) + bytes(blob))


def camera_from_pilots(Th):
    """Camera Module 3 box on the 4 blind pilots in head.stl (HARDWARE_AUDIT B9), from audit/sites_head.json
    (head frame). Board 25 x 24, holes 21 x 12.5; the PCB sits on the boss faces, lens toward the front wall."""
    path = os.path.join(AUDIT, "sites_head.json")
    if not os.path.exists(path):
        return None
    pil, lens = [], []
    for s in json.load(open(path)):
        o, ax = np.array(s["o"], float), np.array(s["ax"], float)
        if abs(ax[0]) < 0.9:
            continue
        for t0, t1, part, kind, d, _ in s["segs"]:
            if part != "head":
                continue
            ends = sorted([o + ax * t0, o + ax * t1], key=lambda p: p[0])
            if 1.55 <= d <= 1.75 and 2.5 <= t1 - t0 <= 4.0:
                pil.append(ends[0])            # boss face = the end toward the inside (smaller x)
            elif 7.0 <= d <= 9.5:
                lens.append((ends[0], d))
    import itertools
    for quad in itertools.combinations(range(len(pil)), 4):
        P = np.array([pil[k] for k in quad])
        dd = sorted(np.linalg.norm(P[a] - P[b]) for a, b in itertools.combinations(range(4), 2))
        if np.allclose(dd, [12.5, 12.5, 21.0, 21.0, 24.43, 24.43], atol=0.5):
            c = P.mean(0)
            span = P.max(0) - P.min(0)
            long_ax = int(np.argmax(span[1:])) + 1          # the 21 mm direction carries the 25 mm board side
            dims = [1.0, 0.0, 0.0]                           # the PCB (1.0 mm stand-in, B9); the lens sits in the opening
            dims[long_ax], dims[3 - long_ax] = 25.0, 24.0
            cen = c.copy()
            cen[0] = P[:, 0].min() - 0.5                     # PCB behind the boss faces (twin/complete3d/camera_seat.json)
            if lens:   # board centre 3.75 mm from the pilot centre toward the lens row (holes 2 mm from the edges, lens row 14.5 mm up)
                lc0 = min(lens, key=lambda x: np.linalg.norm(x[0][1:] - c[1:]))[0]
                cen[3 - long_ax] += 3.75 * np.sign(lc0[3 - long_ax] - c[3 - long_ax])
            out = dict(dims=dims, center=(Th @ np.r_[cen, 1])[:3].round(2).tolist(),
                       where="PCB on the 4 measured head.stl pilots, board centre 3.75 mm toward the lens row, lens in the 7.75 mm "
                             "opening (twin/complete3d/camera_seat.json; PCB 1.0 mm stand-in, B9)")
            if lens:
                lc, ld = min(lens, key=lambda x: np.linalg.norm(x[0][1:] - c[1:]))
                off = lc - c
                out["lens_hole"] = dict(center_world=(Th @ np.r_[lc, 1])[:3].round(2).tolist(), d_mm=ld,
                                        offset_from_pilot_centre_mm=off[1:].round(2).tolist())
            return out
    return None


def head_floor_spot(u, inst, src, Th, dims, clearance=1.5, gap=1.1, step=1.0):
    """Free flat spot on the head floor (head_bot_sheet top) under the Pi for a box of dims (x, y, height).
    Obstacles: every head part at zero pose, plus the neck links that move inside the head, swept over the
    head roll, yaw and pitch ranges (relative to the head). Returns the spot closest to the Pi centre.
    gap: the box sits on the 1.1 mm VHB 4950 foam tape (BOM 29). It was 0.5 mm until the 2026-11-01 seat-fit
    check (viewer/MISSING_3D.md) found the box 0.59 mm into the tape, so the box is now 0.6 mm higher."""
    pi = [i for i in inst if i["key"] == "pi"]
    fl = [i for i in inst if i["key"] == "head_bot_sheet"]
    if not pi or not fl:
        return None
    pi, fl = pi[0], fl[0]
    floor = src["head_bot_sheet"].copy().apply_transform(fl["T"])
    z_top = float(floor.bounds[1][2])
    lo = pi["bmin"][:2] - 25.0
    hi = pi["bmax"][:2] + 25.0
    nx, ny = int(np.ceil((hi[0] - lo[0]) / step)), int(np.ceil((hi[1] - lo[1]) / step))
    gx, gy = lo[0] + (np.arange(nx) + 0.5) * step, lo[1] + (np.arange(ny) + 0.5) * step
    X, Y = np.meshgrid(gx, gy, indexing="ij")
    org = np.c_[X.ravel(), Y.ravel(), np.full(X.size, z_top + 5.0)]
    locs, ri, _ = floor.ray.intersects_location(org, np.tile([0, 0, -1.0], (len(org), 1)), multiple_hits=False)
    support = np.zeros(X.size, bool)
    support[ri[np.abs(locs[:, 2] - z_top) < 0.3]] = True
    support = support.reshape(nx, ny)
    z0, z1 = z_top + 0.05, z_top + gap + dims[2] + clearance
    blocked = np.zeros((nx, ny), bool)

    def mark(P):
        m = (P[:, 2] > z0) & (P[:, 2] < z1) & (P[:, 0] >= lo[0]) & (P[:, 0] < lo[0] + nx * step) \
            & (P[:, 1] >= lo[1]) & (P[:, 1] < lo[1] + ny * step)
        P = P[m]
        blocked[((P[:, 0] - lo[0]) / step).astype(int), ((P[:, 1] - lo[1]) / step).astype(int)] = True

    def dense(mesh, per_mm2=4.0):
        return trimesh.sample.sample_surface(mesh, max(1000, int(mesh.area * per_mm2)), seed=1)[0]
    moving = ("neck_yaw_assembly", "head_pitch_to_yaw", "neck_pitch_assembly")
    for i in inst:
        if i["link"] in moving or i["key"] == "head_bot_sheet":
            continue
        if np.any(i["bmax"][:2] < lo) or np.any(i["bmin"][:2] > hi) or i["bmax"][2] < z0 or i["bmin"][2] > z1:
            continue
        mark(dense(src[i["key"]].copy().apply_transform(i["T"])))

    def mm(T):
        T = np.array(T, float)
        T[:3, 3] *= 1000.0
        return T
    lim = {j.name: (j.limit.lower, j.limit.upper) for j in u.robot.joints if j.type == "revolute"}
    zero = {n: 0.0 for n in u.actuated_joint_names}
    u.update_cfg(zero)
    H0 = mm(u.get_transform("head_assembly"))
    L0 = {ln: np.linalg.inv(mm(u.get_transform(ln))) for ln in moving}
    local = [(i["link"], np.linalg.inv(i["T"]), i["T"], dense(src[i["key"]], 3.0)) for i in inst if i["link"] in moving]
    local = [(ln, Ti, T, (T[:3, :3] @ P.T).T + T[:3, 3]) for ln, Ti, T, P in local]   # zero-pose world points
    for r in np.linspace(*lim["head_roll"], 7):
        for yv in np.linspace(*lim["head_yaw"], 13):
            for pv in np.linspace(*lim["head_pitch"], 5):
                cfg = dict(zero, head_roll=r, head_yaw=yv, head_pitch=pv)
                u.update_cfg(cfg)
                Hq = H0 @ np.linalg.inv(mm(u.get_transform("head_assembly")))
                for ln in moving:
                    M = Hq @ mm(u.get_transform(ln)) @ L0[ln]
                    for ln2, Ti, T, Pw in local:
                        if ln2 == ln:
                            mark((M[:3, :3] @ Pw.T).T + M[:3, 3])
    u.update_cfg(zero)
    # box footprint must be fully supported, the footprint grown by the clearance fully free
    fx, fy = int(np.ceil(dims[0] / step)), int(np.ceil(dims[1] / step))
    cl = int(np.ceil(clearance / step))

    def psum(a):
        s = np.zeros((a.shape[0] + 1, a.shape[1] + 1), np.int32)
        s[1:, 1:] = np.cumsum(np.cumsum(a.astype(np.int32), 0), 1)
        return s
    S, B = psum(support), psum(blocked)
    best = None
    for ix in range(cl, nx - fx - cl + 1):
        for iy in range(cl, ny - fy - cl + 1):
            if S[ix + fx, iy + fy] - S[ix, iy + fy] - S[ix + fx, iy] + S[ix, iy] != fx * fy:
                continue
            a, b, c2, d2 = ix - cl, iy - cl, ix + fx + cl, iy + fy + cl
            if B[c2, d2] - B[a, d2] - B[c2, b] + B[a, b]:
                continue
            cx, cy = lo[0] + (ix + fx / 2.0) * step, lo[1] + (iy + fy / 2.0) * step
            if not (pi["bmin"][0] <= cx <= pi["bmax"][0] and pi["bmin"][1] <= cy <= pi["bmax"][1]):
                continue
            dist = np.hypot(cx - pi["c"][0], cy - pi["c"][1])
            if best is None or dist < best[0]:
                best = (dist, cx, cy)
    if best is None:
        return None
    return dict(dims=[float(d) for d in dims], center=[round(best[1], 1), round(best[2], 1), round(z_top + gap + dims[2] / 2.0, 2)],
                where="Head floor under the Pi, on %.1f mm foam tape: free flat spot found by make_viewer_data.py (clear of head "
                      "parts and of the neck parts over the head roll, yaw and pitch ranges, %.1f mm clearance)" % (gap, clearance),
                floor_top_z=round(z_top, 2), dist_to_pi_centre_mm=round(float(best[0]), 1),
                free_below_pi_mm=round(float(pi["bmin"][2] - z_top), 1))


def radial(c, centre, base=12.0, k=0.45):
    d = np.asarray(c, float) - np.asarray(centre, float)
    n = np.linalg.norm(d)
    return np.zeros(3) if n < 1e-6 else d / n * (base + k * n)


def label_of(stem):
    return LABEL.get(stem, stem.replace("_", " ").capitalize())


# ---------------------------------------------------------------------------------------------- build
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, help="output folder, must be outside the repo")
    ap.add_argument("--write-bom", action="store_true",
                    help="also write altaay_lab/BOM_FULL.md and altaay_lab/bom_full.csv (text, every part)")
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    if os.path.commonpath([out, REPO]) == REPO:
        sys.exit("refusing to write inside the repo: " + out)
    os.makedirs(out, exist_ok=True)
    t_start = time.time()
    warnings = []

    printed_doc, bom, blk, mounting = load_docs()
    print_files = {os.path.splitext(f)[0] for f in os.listdir(PRINT_DIR) if f.lower().endswith(".stl")}

    def print_stem(urdf_fn):
        s = os.path.splitext(urdf_fn)[0]
        if s in print_files:
            return s
        for pre in ("left_", "right_"):
            if s.startswith(pre) and s[len(pre):] in print_files:
                return s[len(pre):]
        return None

    # 1. URDF at zero joint angles
    u = yourdfpy.URDF.load(os.path.join(URDF_DIR, "robot.urdf"), load_meshes=False, build_scene_graph=True)
    u.update_cfg(np.zeros(len(u.actuated_joint_names)))
    inst = []
    for ln, link in u.link_map.items():
        Tl = u.get_transform(ln)
        for v in link.visuals:
            fn = os.path.basename(v.geometry.mesh.filename)
            T = Tl @ (v.origin if v.origin is not None else np.eye(4))
            T = T.copy()
            T[:3, 3] *= 1000.0
            inst.append(dict(link=ln, urdf=fn, T=T, src="urdf"))
    n_urdf = len(inst)
    # cross-check with the audit's assembly (sites.json instance indices refer to it)
    asm_path = os.path.join(AUDIT, "assembly.json")
    asm_ok = False
    if os.path.exists(asm_path):
        A = json.load(open(asm_path))["inst"]
        asm_ok = len(A) == n_urdf and all(a["mesh"] == i["urdf"] and np.allclose(np.array(a["T"]), i["T"], atol=1e-6) for a, i in zip(A, inst))
    if not asm_ok:
        warnings.append("URDF instances do not match audit/assembly.json; insert hosts are matched by nearest part")

    # 2. map to parts
    unmapped = []
    mesh_src = {}   # part key -> (path, to_mm)
    for i in inst:
        stem = print_stem(i["urdf"])
        if stem:
            i.update(key=stem, label=label_of(stem), cat=printed_doc.get(stem, {}).get("cat", "pla"), bom=None,
                     file="print/" + stem + ".stl", printed=True)
            mesh_src[stem] = (os.path.join(PRINT_DIR, stem + ".stl"), False)
            i["urdf_check"] = i["urdf"]
        elif i["urdf"] == "board.stl":
            key, lab, cat, bl = BOARD.get(i["link"], ("board", "board.stl", "electronics", None))
            i.update(key=key, label=lab, cat=cat, bom=bl, file="urdf/board.stl", printed=False)
            mesh_src[key] = (os.path.join(URDF_DIR, "board.stl"), True)
        elif i["urdf"] in BOUGHT:
            key, lab, cat, bl = BOUGHT[i["urdf"]]
            i.update(key=key, label=lab, cat=cat, bom=bl, file="urdf/" + i["urdf"], printed=False)
            mesh_src[key] = (os.path.join(URDF_DIR, i["urdf"]), True)
        else:
            unmapped.append(i["urdf"])
            i.update(key=os.path.splitext(i["urdf"])[0], label=i["urdf"], cat="other", bom=None,
                     file="urdf/" + i["urdf"], printed=False)
            mesh_src[i["key"]] = (os.path.join(URDF_DIR, i["urdf"]), True)

    # frame check: print STL vs URDF mesh (x1000), same part frame
    # The frame is the same when, on every axis, at least one of the two bounding faces agrees within 0.05 mm: a frame
    # shift or turn moves both faces of an axis, a printed feature the lab added (D38 tongue and lips, D47 mic seats,
    # D54 cliff seat) moves one face only. The faces that moved are listed with their size (frame_grown).
    frame_check, frame_grown = {}, {}
    for i in inst:
        if i.get("printed") and i["key"] not in frame_check:
            a = load_mesh(os.path.join(URDF_DIR, i["urdf"]), True).bounds
            b = load_mesh(os.path.join(PRINT_DIR, i["key"] + ".stl"), False).bounds
            d = b - a                                    # print minus URDF, rows min and max
            per_axis = [float(min(abs(d[0][k]), abs(d[1][k]))) for k in range(3)]
            frame_check[i["key"]] = round(max(per_axis), 3)
            grown = {"%s%s" % ("-+"[row], "xyz"[k]): round(float(d[row][k]) * (1 if row else -1), 3)
                     for row in (0, 1) for k in range(3) if abs(d[row][k]) > 0.05}
            if grown:
                frame_grown[i["key"]] = grown
    bad = {k: v for k, v in frame_check.items() if v > 0.05}
    if bad:
        warnings.append("print STL and URDF mesh frames differ (both faces of an axis moved) by more than 0.05 mm: %s" % bad)

    # 3. head internals in the head.stl frame
    Th = [i["T"] for i in inst if i["key"] == "head"][0]
    seen = Counter()
    for stem in HEAD_INTERNALS:
        seen[stem] += 1
        M = np.diag([1.0, -1.0, 1.0, 1.0]) if seen[stem] == 2 else np.eye(4)
        inst.append(dict(link="head_assembly", urdf=None, T=Th @ M, src="print", key=stem, label=label_of(stem),
                         cat=printed_doc.get(stem, {}).get("cat", "pla"), bom=None, file="print/" + stem + ".stl",
                         printed=True, mirrored=bool(seen[stem] == 2)))
        mesh_src[stem] = (os.path.join(PRINT_DIR, stem + ".stl"), False)

    # load source meshes once
    src = {k: load_mesh(p, mm) for k, (p, mm) in mesh_src.items()}
    # D44 (V1 track 9): the 2S1P Molicel P45B pack in the grown bay replaces the URDF's 18650 cells and holder:
    # 21.4 x 70.0 mm cells on their axes (trunk frame x -133.1, y -9.35 and +12.2, z 31.5) and the pack's two nickel strips
    if "cell" in src:
        src["cell"] = trimesh.creation.cylinder(radius=10.7, height=70.0, sections=48)
        for i, yc in zip([i for i in inst if i["key"] == "cell"], (-9.35, 12.2)):
            i["T"] = trimesh.transformations.translation_matrix((-133.1, yc, 31.5))
    if "holder" in src:
        src["holder"] = trimesh.util.concatenate([trimesh.creation.box((8.0, 30.0, 0.3), trimesh.transformations.translation_matrix((0, 0, z)))
                                                  for z in (35.65, -35.65)])
        for i in [i for i in inst if i["key"] == "holder"]:
            i["T"] = trimesh.transformations.translation_matrix((-133.1, 1.4, 31.5))
    for i in inst:
        m = src[i["key"]]
        corners = trimesh.bounds.corners(m.bounds)
        w = (i["T"][:3, :3] @ corners.T).T + i["T"][:3, 3]
        i["bmin"], i["bmax"] = w.min(0), w.max(0)
        i["c"] = (i["bmin"] + i["bmax"]) / 2.0
        i["sub"] = LINK_SUB.get(i["link"], "trunk")

    # 4. servos: group 3 case parts + 2 horns, name by the joint the drive horn sits on
    joints = []
    for j in u.robot.joints:
        if j.type != "revolute":
            continue
        Tc = u.get_transform(j.child)
        joints.append((j.name, Tc[:3, 3] * 1000.0, Tc[:3, :3] @ np.asarray(j.axis, float), j.child, j.parent))
    servo_groups = []
    by_link = defaultdict(list)
    for k, i in enumerate(inst):
        if i["key"] in ("servo_top", "servo_mid", "servo_bottom", "horn_drive", "horn_idle"):
            by_link[i["link"]].append(k)
    for ln, ks in by_link.items():
        mids = [k for k in ks if inst[k]["key"] == "servo_mid"]
        free = set(ks) - set(mids)
        for km in mids:
            g = dict(mid=km)
            for part in ("servo_top", "servo_bottom", "horn_drive", "horn_idle"):
                cand = [k for k in free if inst[k]["key"] == part]
                kb = min(cand, key=lambda k: np.linalg.norm(inst[k]["c"] - inst[km]["c"]))
                free.discard(kb)
                g[part] = kb
            hc = inst[g["horn_drive"]]["c"]

            def axis_dist(jt):
                d = hc - jt[1]
                a = jt[2] / np.linalg.norm(jt[2])
                return np.linalg.norm(d - np.dot(d, a) * a)
            # the servo body sits in the parent or the child link of the joint it drives; collinear
            # axes (left and right hip pitch) are told apart by that and by the distance to the joint origin
            cand = [jt for jt in joints if not jt[0].endswith("antenna") and ln in (jt[3], jt[4])]
            jt = min(cand, key=lambda jt: (round(axis_dist(jt), 1), np.linalg.norm(hc - jt[1])))
            g.update(joint=jt[0], axis_err=round(float(axis_dist(jt)), 2), link=ln)
            servo_groups.append(g)
    jn = Counter(g["joint"] for g in servo_groups)
    if len(servo_groups) != 14 or max(jn.values()) > 1:
        warnings.append("servo grouping is not one servo per joint: %s" % dict(jn))
    for g in servo_groups:
        members = [g[p] for p in ("servo_top", "mid", "servo_bottom")]
        cen = np.mean([inst[k]["c"] for k in members], axis=0)
        for p in ("servo_top", "mid", "servo_bottom", "horn_drive", "horn_idle"):
            i = inst[g[p]]
            i["servo"] = g["joint"]
            i["servo_centre"] = cen
            if g["joint"] in ("left_knee", "right_knee"):
                i["bom"] = "1b"                                   # D32: the STS3250 knee servo is BOM line 1b
            if p.startswith("horn"):
                ext = i["bmax"] - i["bmin"]
                ax = int(np.argmin(ext))
                d = np.zeros(3)
                d[ax] = np.sign((i["c"] - cen)[ax]) or 1.0
                i["v3"] = d * HORN_PULL

    # 5. node ids
    used = Counter()
    for i in inst:
        if "servo" in i:
            part = {"servo_top": "top", "servo_mid": "mid", "servo_bottom": "bottom", "horn_drive": "horn_drive",
                    "horn_idle": "horn_idle"}[i["key"]]
            i["id"] = "servo-%s-%s" % (i["servo"], part)
        else:
            used[(i["link"], i["key"])] += 1
            i["id"] = "%s-%s-%d" % (i["link"], i["key"], used[(i["link"], i["key"])])
    dup = [k for k, n in Counter(i["id"] for i in inst).items() if n > 1]
    if dup:
        sys.exit("duplicate node ids: %s; servo joints %s" % (dup, [(g["joint"], g["axis_err"], g["link"]) for g in servo_groups]))

    # 6. inserts
    sites = json.load(open(os.path.join(AUDIT, "sites.json")))
    inserts = []
    printed_keys = set(printed_doc)
    for si, s in enumerate(sites):
        o, ax = np.array(s["o"], float), np.array(s["ax"], float)
        ax /= np.linalg.norm(ax)
        segs = s["segs"]
        for seg in segs:
            t0, t1, part, kind, dia, hi = seg
            stem = print_stem(part + ".stl") or part
            if stem not in printed_keys or not (INSERT_BORE[0] <= dia <= INSERT_BORE[1]) or (t1 - t0) < INSERT_BORE[2]:
                continue
            c = o + ax * (t0 + t1) / 2.0
            if asm_ok:
                host = inst[hi]
            else:
                host = min((i for i in inst if i["key"] == stem), key=lambda i: np.linalg.norm(i["c"] - c))

            def touches(at_end, same):
                for q in segs:
                    if q is seg:
                        continue
                    if (q[5] == hi) != same:
                        continue
                    if (at_end and abs(q[0] - t1) < 0.5) or (not at_end and abs(q[1] - t0) < 0.5):
                        return True
                return False
            o0, o1 = touches(False, False), touches(True, False)
            if o1 and not o0:
                sgn = 1.0
            elif o0 and not o1:
                sgn = -1.0
            else:
                s0, s1 = touches(False, True), touches(True, True)
                sgn = 1.0 if (s0 and not s1) else (-1.0 if (s1 and not s0) else 0.0)
            inserts.append(dict(site=si, host=host["id"], host_key=host["key"], c=c, ax=ax, bore_d=dia,
                                bore_len=round(t1 - t0, 2), open_dir=sgn))
    # D38: inserts whose screw is left out (fasteners.json leave_out) are not fitted: the bore stays empty
    _fj = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fasteners", "fasteners.json")
    _lo = [y for y in json.load(open(_fj))["fasteners"] if y["kind"] == "insert" and y.get("leave_out")]
    inserts = [x for x in inserts if not any(x["host_key"] == y["into"] and
                                             float(np.linalg.norm(np.asarray(x["c"], float) - np.asarray(y["seat_world"], float))) < 6.0
                                             for y in _lo)]
    n_ins = Counter(x["host_key"] for x in inserts)

    # 7. foot switch slots: 6.4 x 19.8 pockets in foot_top (PRINT_CHECK, HARDWARE_AUDIT B11)
    from shapely.geometry import Polygon
    ft = src["foot_top"]
    slot_local = []
    for z in np.arange(ft.bounds[0][2] + 0.5, ft.bounds[1][2], 0.5):
        sec = ft.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if sec is None:
            continue
        p2, T2 = sec.to_2D()
        for poly in p2.polygons_full:
            for r in poly.interiors:
                q = Polygon(r.coords)
                rr = q.minimum_rotated_rectangle
                xs, ys = rr.exterior.coords.xy
                e = sorted([np.hypot(xs[1] - xs[0], ys[1] - ys[0]), np.hypot(xs[2] - xs[1], ys[2] - ys[1])])
                if abs(e[0] - 6.4) < 0.3 and abs(e[1] - 19.8) < 0.4:
                    cc = (T2 @ np.r_[np.array(q.centroid.coords[0]), 0, 1])[:3]
                    slot_local.append(np.r_[cc[:2], z])
    slots = []
    for p in slot_local:
        for s_ in slots:
            if np.linalg.norm(s_["xy"] - p[:2]) < 1.0:
                s_["z0"], s_["z1"] = min(s_["z0"], p[2]), max(s_["z1"], p[2])
                break
        else:
            slots.append(dict(xy=p[:2], z0=p[2], z1=p[2]))
    feet = [i for i in inst if i["key"] == "foot_top"]
    switches = []
    for f in sorted(feet, key=lambda i: -i["c"][1]):
        side = "l" if f["c"][1] > 0 else "r"
        for n_, s_ in enumerate(sorted(slots, key=lambda s: s["xy"][0])):
            # slot from z0-0.25 to z1+0.25 (0.5 mm section step); open end faces foot_bottom (lowest world z)
            ends = [(f["T"] @ np.r_[s_["xy"], z, 1])[:3] for z in (s_["z0"] - 0.25, s_["z1"] + 0.25)]
            lo = min(ends, key=lambda p: p[2])
            cen = lo + np.array([0, 0, FOOT_SWITCH["dims"][2] / 2.0])
            switches.append(dict(FOOT_SWITCH, id="foot_switch_%s%d" % (side, n_ + 1),
                                 label="%s (%s foot, slot %d)" % (FOOT_SWITCH["label"], "left" if side == "l" else "right", n_ + 1),
                                 center=cen.tolist(), frame="urdf_world_mm", where="foot_top slot (measured)",
                                 slot_depth=round(float(s_["z1"] - s_["z0"] + 0.5), 1), sub=f["sub"], follow=f["id"]))

    # 7b. parts placed from the CAD: camera on its 4 head pilots, 5 V regulator on the head floor under the Pi
    cad_place = {}
    cam = camera_from_pilots(Th)
    if cam:
        cad_place["camera"] = cam
    else:
        warnings.append("camera pilots not found in audit/sites_head.json: camera goes in the tray")
    reg = head_floor_spot(u, inst, src, Th, [p for p in PLACEHOLDERS if p["id"] == "reg_5v"][0]["dims"])
    if reg:
        cad_place["reg_5v"] = reg
    else:
        warnings.append("no free flat spot for the 5 V regulator under the Pi: it goes in the tray")

    terminals, retention_in = load_cables3d_extras()
    for tm in terminals:
        tid = str(tm.get("id", ""))
        if tid in {p["id"] for p in PLACEHOLDERS} and tm.get("center_mm") is not None and tid not in cad_place:
            cad_place[tid] = dict(center=[float(x) for x in tm["center_mm"]],
                                  dims=[float(x) for x in (tm.get("dims_xyz_mm") or [p for p in PLACEHOLDERS if p["id"] == tid][0]["dims"])],
                                  where="Cable terminal seat from altaay_lab/cables3d (%s)" % str(tm.get("how", ""))[:160],
                                  link=tm.get("link"))

    # 8. placeholders: placements.json (lead) > measured slots > tray
    placements, pl_note = {}, "audit/placements.json not found: unplaced parts are in the tray"
    if os.path.exists(PLACEMENTS):
        try:
            raw = json.load(open(PLACEMENTS))
            raw = raw if isinstance(raw, list) else raw.get("placements", [])
            for r in raw:
                if r.get("center_mm") is None:
                    continue
                if r.get("frame", "urdf_world_mm") != "urdf_world_mm":
                    warnings.append("placements.json %s: frame %s not supported, ignored" % (r.get("id"), r.get("frame")))
                    continue
                placements[r["id"]] = r
            pl_note = "audit/placements.json read %s: %d placed (%s)" % (
                time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(PLACEMENTS))), len(placements),
                ", ".join(sorted(placements)))
        except Exception as e:  # keep building with the tray
            warnings.append("placements.json unreadable: %s" % e)
    ph_all = [dict(p) for p in PLACEHOLDERS] + switches
    known = {p["id"] for p in ph_all}
    for pid, r in placements.items():
        if pid not in known:   # a part the lead placed that this script does not know: still draw it
            ph_all.append(dict(id=pid, label=r.get("label", pid), dims=r["dims_xyz_mm"], bom=None, blockers=[],
                               dims_note="From placements.json.", mount=r.get("source", "")))
    for p in ph_all:
        r = placements.get(p["id"])
        if r:
            p["dims"] = [float(x) for x in r["dims_xyz_mm"]]
            p["center"] = [float(x) for x in r["center_mm"]]
            p["where"] = "Lab placement, audit/placements.json" + (" (%s)" % r["source"] if r.get("source") else "")
            p["placement"] = {k: v for k, v in r.items() if k not in ("id", "label")}
        elif p["id"] in cad_place:
            c = cad_place[p["id"]]
            p["dims"], p["center"], p["where"] = c["dims"], c["center"], c["where"]
            p["placement"] = {k: v for k, v in c.items() if k not in ("dims", "center", "where")}
    # placed boxes move with the modelled part they touch (smallest surface distance from the box)
    world_mesh = {}

    def touching_part(center, dims):
        c, h = np.array(center, float), np.array(dims, float) / 2.0
        g = np.array(np.meshgrid(*[[-1, 0, 1]] * 3)).reshape(3, -1).T
        pts = c + g * h
        best, bd = None, 1e9
        for i in inst:
            if np.any(i["bmin"] - 30 > c + h) or np.any(i["bmax"] + 30 < c - h):
                continue
            if i["id"] not in world_mesh:
                world_mesh[i["id"]] = src[i["key"]].copy().apply_transform(i["T"])
            _, d, _ = trimesh.proximity.closest_point(world_mesh[i["id"]], pts)
            if d.min() < bd:
                best, bd = i, float(d.min())
        return best, bd
    tray_items = [p for p in ph_all if "center" not in p]
    by_id = {i["id"]: i for i in inst}
    for p in ph_all:
        if "center" not in p:
            continue
        if p.get("follow"):
            near, dist = by_id[p["follow"]], 0.0
        else:
            near, dist = touching_part(p["center"], p["dims"])
            hint = FOLLOW_HINT.get(p["id"])
            if hint and near is not None and near["key"] != hint:
                cands = [i for i in inst if i["key"] == hint]
                if cands:
                    h = min(cands, key=lambda i: np.linalg.norm(i["c"] - np.array(p["center"])))
                    if h["id"] not in world_mesh:
                        world_mesh[h["id"]] = src[h["key"]].copy().apply_transform(h["T"])
                    c, hh = np.array(p["center"], float), np.array(p["dims"], float) / 2.0
                    g = np.array(np.meshgrid(*[[-1, 0, 1]] * 3)).reshape(3, -1).T
                    dh = float(trimesh.proximity.closest_point(world_mesh[h["id"]], c + g * hh)[1].min())
                    if dh <= 6.0:
                        near, dist = h, dh
        if near is None:
            tray_items.append(p)
            del p["center"]
            continue
        p["sub"], p["follow"], p["follow_dist"] = near["sub"], near["id"], round(dist, 1)
    # tray layout: rows along x on a plate right of the robot (-y), at floor level
    ys = [i["bmin"][1] for i in inst]
    floor = min(i["bmin"][2] for i in inst)
    gap, width = 14.0, 230.0
    x, yrow, rowdepth = 0.0, 0.0, 0.0
    tray_items.sort(key=lambda p: -p["dims"][0] * p["dims"][1])
    for p in tray_items:
        dx, dy, dz = p["dims"]
        if x > 0 and x + dx > width:
            x, yrow, rowdepth = 0.0, yrow + rowdepth + gap, 0.0
        p["tray_xy"] = (x + dx / 2.0, yrow + dy / 2.0)
        x += dx + gap
        rowdepth = max(rowdepth, dy)
    tray_d = yrow + rowdepth
    tray_used_w = max([p["tray_xy"][0] + p["dims"][0] / 2.0 for p in tray_items], default=0.0)
    tray = None
    if tray_items:
        tx0 = -40.0 - tray_used_w / 2.0
        ty1 = min(ys) - 60.0
        tz = floor
        for p in tray_items:
            p["center"] = [tx0 + p["tray_xy"][0], ty1 - p["tray_xy"][1], tz + 3.0 + p["dims"][2] / 2.0]
            p["sub"] = "tray"
            p["where"] = "Not yet placed tray"
        tray = dict(min=[tx0 - 12, ty1 - tray_d - 12, tz], max=[tx0 + tray_used_w + 12, ty1 + 12, tz + 3.0],
                    label="Not yet placed")

    # 9. subassembly centres and explode vectors
    sub_c = {}
    for sid, *_ in SUBS:
        bs = [(i["bmin"], i["bmax"]) for i in inst if i["sub"] == sid]
        if bs:
            sub_c[sid] = (np.min([b[0] for b in bs], 0) + np.max([b[1] for b in bs], 0)) / 2.0
    if tray:
        sub_c["tray"] = (np.array(tray["min"]) + np.array(tray["max"])) / 2.0
    for i in inst:
        if "servo" in i:
            v = V2_SERVO.get(i["servo"])
            i["v2"] = np.array(v, float) if v is not None else radial(i["servo_centre"], sub_c[i["sub"]])
        else:
            v = V2.get((i["sub"], i["key"]))
            i["v2"] = np.array(v, float) if v is not None else radial(i["c"], sub_c[i["sub"]])
    shell = next((i for i in inst if i["key"] == "head"), None)
    ears = [i for i in inst if i["key"] == "sg90"]
    if shell is not None and ears:
        for i in inst:
            if i["key"] not in EAR_PULL:
                continue
            sv = min(ears, key=lambda e: float(np.linalg.norm(np.asarray(e["c"]) - np.asarray(i["c"]))))   # its own ear servo
            ax = sv["T"][:3, :3] @ np.array([0.0, 0.0, 1.0])                                   # output shaft, out of the head
            i["v2"] = shell["v2"] + ax / np.linalg.norm(ax) * EAR_PULL[i["key"]]
    for p in ph_all:
        if p["sub"] == "tray":
            p["v2"] = np.zeros(3)
            continue
        v = V2.get((p["sub"], p["id"]))
        p["v2"] = np.array(v, float) if v is not None else by_id[p["follow"]]["v2"].copy()

    placed_ids = {p["id"] for p in ph_all if p["sub"] != "tray"}

    # 10. geometry for the GLB (one per unique source mesh)
    geoms, gidx = [], {}
    for key in sorted(k for k in src if k != "head_board"):   # head_board: board.stl copy in the head, not a part (B7)
        m = src[key]
        pos, idx = web_geometry(m, face_target(len(m.faces), key))
        gidx[key] = len(geoms)
        geoms.append(dict(name=key, pos=pos, idx=idx, src_faces=int(len(m.faces))))
    cpos, cidx = cylinder(INSERT_D, INSERT_L)
    gidx["_insert"] = len(geoms)
    geoms.append(dict(name="insert_m3", pos=cpos, idx=cidx, src_faces=int(len(cidx))))
    bpos, bidx = unit_box()
    gidx["_box"] = len(geoms)
    geoms.append(dict(name="placeholder_box", pos=bpos, idx=bidx, src_faces=12))

    nodes, man_nodes = [], {}
    servo_model = lambda j: "STS3250" if j in ("left_knee", "right_knee") else "STS3215"     # D32: STS3250 knees, STS3215 C001 elsewhere
    servo_label = lambda j: "%s servo ID %d, %s" % (servo_model(j), SERVO_ID.get(j, 0), j.replace("_", " "))

    def status_of(keys, cleared_ok=()):
        ids = []
        for k in keys:
            for b in BLOCKERS.get(k, []):
                if b not in ids:
                    ids.append(b)
        rows = [dict(id=b, status=blk[b]["status"] if b in blk else "not in HARDWARE_AUDIT", title=blk.get(b, {}).get("title", ""),
                     open=bool(blk.get(b, {}).get("open", True)) and b not in cleared_ok) for b in ids]
        op = [r["id"] for r in rows if r["open"]]
        return ("OK" if not op else ", ".join(op)), rows

    pd_ = printed_doc
    for i in inst:
        key = i["key"]
        if key == "head_board":   # B7: the board.stl copy in the head marks the Pi footprint, it is not a part: no node, mesh or label
            continue
        bkey = "servo" if key.startswith("servo_") else key
        st, rows = status_of([bkey])
        rec = dict(label=servo_label(i["servo"]) + " (" + i["label"].split(", ")[-1] + ")" if "servo" in i and key.startswith("servo_")
                   else (i["label"] + (" of servo ID %d" % SERVO_ID.get(i["servo"], 0) if "servo" in i else "")),
                   part=key, file=i["file"], link=i["link"], sub=i["sub"], category=i["cat"],
                   status=st, blockers=rows, mount=MOUNT.get(bkey, ""), v2=np.round(i["v2"], 2).tolist())
        if "servo" in i and key.startswith("servo_"):            # D32: STS3250 on the two knees, STS3215 C001 on the other 12
            knee = servo_model(i["servo"]) == "STS3250"
            rec.update(model=servo_model(i["servo"]), mass_g=74.5 if knee else 55.0, mass_note="whole servo (Feetech sheets)",
                       bom="1b" if knee else "1")
            if knee:
                rec["mount"] = rec["mount"] + " Knees (STS3250, D32): aluminium case tapped 4-M2.0, so 2 M2x6 machine screws into the thigh (BOM_FULL F07b; thread depth not published)."
        if i.get("printed"):
            d = pd_.get(key, {})
            rec.update(qty=d.get("qty"), material=d.get("material"), grams=d.get("g_each"), hours=d.get("h_each"),
                       print_flags=d.get("flags"), orientation=d.get("orient"), bed=d.get("bed"),
                       inserts=int(n_ins.get(key, 0)), bom="27" if d.get("cat") != "tpu" else "28")
            if n_ins.get(key) and not rec["mount"]:
                rec["mount"] = "%d M3 heat-set inserts in this part (each instance)." % (n_ins[key] // max(1, d.get("qty", 1)))
            elif n_ins.get(key):
                rec["mount"] += " %d M3 inserts per part." % (n_ins[key] // max(1, d.get("qty", 1)))
        else:
            rec.update(bom=i["bom"], qty=None)
        if "servo" in i:
            rec.update(servo=i["servo"], servo_id=SERVO_ID.get(i["servo"]), group="servo-" + i["servo"])
        if "v3" in i:
            rec["v3"] = np.round(i["v3"], 2).tolist()
        if i.get("mirrored"):
            rec["mirrored"] = True
        if mounting.get(bkey):
            rec["mounting"] = mounting[bkey]
        if key == "bms_cad" and "bms_tenergy" in placed_ids:
            rec.update(replaced="Replaced by the Tenergy 32175 (ph-bms_tenergy). Kept to show the upstream position.",
                       label=rec["label"] + " (replaced)")
        man_nodes[i["id"]] = rec
        nodes.append(dict(name=i["id"], mesh=gidx[key], matrix=i["T"]))
    # qty for bought parts = how many of that part key are in the model
    kc = Counter(i["key"] for i in inst)
    for nid, rec in man_nodes.items():
        if rec["qty"] is None:
            rec["qty"] = 14 if rec["part"].startswith("servo_") or rec["part"].startswith("horn_") else kc[rec["part"]]
    for n_, x in enumerate(inserts):
        nid = "insert-%02d" % (n_ + 1)
        R = rot_z_to(x["ax"])
        M = np.eye(4)
        M[:3, :3], M[:3, 3] = R, x["c"]
        host = by_id[x["host"]]
        st, rows = status_of(["insert"] + (["foot_top"] if x["host_key"] == "foot_top" else []))
        man_nodes[nid] = dict(label="M3 heat-set insert in %s" % label_of(x["host_key"]).lower(), part="insert",
                              file="(drawn) D %.1f x %.1f mm" % (INSERT_D, INSERT_L), link=host["link"], sub=host["sub"],
                              category="insert", qty=len(inserts), material="Brass", bom="16", status=st, blockers=rows,
                              mount=MOUNT["insert"] + " Bore %.1f mm x %.1f mm deep (sites.json site %d)." % (x["bore_d"], x["bore_len"], x["site"]),
                              host=x["host"], v2=np.round(host["v2"], 2).tolist(),
                              v3=np.round(x["ax"] * x["open_dir"] * INSERT_PULL + (host.get("v3") if isinstance(host.get("v3"), np.ndarray) else 0), 2).tolist())
        nodes.append(dict(name=nid, mesh=gidx["_insert"], matrix=M))
    for p in ph_all:
        nid = "ph-" + p["id"]
        M = np.diag([p["dims"][0], p["dims"][1], p["dims"][2], 1.0])
        M[:3, 3] = p["center"]
        pkey = "foot_switch" if p["id"].startswith("foot_switch") else ("led" if p["id"].startswith("led_") else p["id"])
        st, rows = status_of([pkey])
        for b in p.get("blockers", []):
            if b not in [r["id"] for r in rows]:
                rows.append(dict(id=b, status=blk.get(b, {}).get("status", "?"), title=blk.get(b, {}).get("title", ""), open=bool(blk.get(b, {}).get("open", True))))
        op = [r["id"] for r in rows if r["open"]]
        mrow = mounting.get(pkey)
        man_nodes[nid] = dict(label=p["label"], part=pkey, file="(placeholder, not in CAD)", link=None, sub=p["sub"], mounting=mrow,
                              category="placeholder", qty=sum(1 for q in ph_all if q["id"].split("_")[0] == p["id"].split("_")[0]) if pkey in ("led", "foot_switch") else 1,
                              material=None, bom=p.get("bom"), status="OK" if not op else ", ".join(op), blockers=rows,
                              mount=p.get("mount", ""), dims=[round(float(d), 2) for d in p["dims"]], dims_note=p.get("dims_note", ""),
                              where=p.get("where", ""), placement=p.get("placement"), v2=np.round(p["v2"], 2).tolist(),
                              short=SHORT.get(p["id"], SHORT.get(pkey, p["label"].split(" (")[0])), follow=p.get("follow"),
                              follow_dist_mm=p.get("follow_dist"))
        nodes.append(dict(name=nid, mesh=gidx["_box"], matrix=M))

    import bom_full
    # 10b. every screw (altaay_lab/fasteners/fasteners.json): one GLB node each, riding with the part under its head
    def host_of(part, p, link=None):
        stem = SCREW_PART_ALIAS.get(part) or (print_stem(part + ".stl") if part else None) or part
        cand = [i for i in inst if i["key"] == stem] or [i for i in inst if part and i.get("urdf") and os.path.splitext(i["urdf"])[0] == part]
        if link:
            cand = [i for i in cand if i["link"] == link] or cand
        if not cand:
            cand = [i for i in inst if (link is None or i["link"] == link)] or inst
        def dist(i):
            q = np.clip(p, i["bmin"], i["bmax"])
            return float(np.linalg.norm(q - p))
        return min(cand, key=dist)

    def part_word(name):
        n = str(name or "?")
        if n.startswith("wj-wk00") or n.startswith("servo_"):
            return "servo case"
        if "palonier" in n or n.startswith("horn_"):
            return "servo horn (%s)" % ("drive" if "drive" in n else "idle")
        if n == "sg90":
            return "SG90 ear servo tab"
        stem = print_stem(n + ".stl") or n
        return label_of(stem).lower()

    screws, screw_note = load_fasteners()
    screw_geo, screw_rows = {}, []
    spec_count = Counter("%s x %g" % (s["size"], s["L"]) for s in screws)
    for n_, s in enumerate(screws, 1):
        gk = (s["d"], s["L"], s["head_d"], s["head_h"])
        if gk not in screw_geo:
            sv, sf = screw_mesh(*gk)
            screw_geo[gk] = len(geoms)
            geoms.append(dict(name="screw_%gx%g" % (s["d"], s["L"]), pos=sv, idx=sf, src_faces=int(len(sf))))
        host = host_of(s["part"], s["p"], s["link"])
        nid = "screw-%03d" % n_
        M = np.eye(4)
        M[:3, :3], M[:3, 3] = rot_z_to(-s["ax"]), s["p"]
        spec = s["spec_label"] or "%sx%g %s" % (s["size"], s["L"], s["head"])
        into_lab = part_word(s["into"])
        bl = re.findall(r"\bB\d+\b", " ".join(str(x) for x in (s["status"], s["note"])))
        st, rows_ = status_of([]) if not bl else (", ".join(bl), [dict(id=b, status=blk.get(b, {}).get("status", "?"),
                                                                        title=blk.get(b, {}).get("title", ""), open=bool(blk.get(b, {}).get("open", True))) for b in bl])
        hv3 = np.array(host["v3"], float) if host.get("v3") is not None else np.zeros(3)
        man_nodes[nid] = dict(
            label=s.get("viewer_label") or "%s: %s into %s" % (spec, part_word(host["key"]), into_lab), part="screw", fid=s["fid"],
            file="(drawn) %s x %g mm, %s head %.1f x %.1f" % (s["size"], s["L"], s["head"], s["head_d"], s["head_h"]),
            link=host["link"], sub=host["sub"], category="screw", qty=spec_count["%s x %g" % (s["size"], s["L"])],
            material="Steel (A2 stainless or as supplied)", bom=s["line"] or None, status=st if s["status"] in (None, "", "OK", "ok") else str(s["status"]),
            fid_flags=s.get("flags") or [],
            blockers=rows_, mount="%s into %s (%s). %s" % (spec, into_lab, s["anchor"] or "anchor not given",
                                                          ("Engagement %.1f mm." % float(s["engagement"])) if isinstance(s["engagement"], (int, float)) else ""),
            spec=dict(size=s["size"], length=s["L"], head=s["head"], head_d=s["head_d"], head_h=s["head_h"]),
            joins=[host["key"], s["into"]], anchor=s["anchor"], engagement_mm=s["engagement"], note=s["note"] or "",
            supplied=s["supplied"], color=s.get("color") or SCREW_COLOR.get(s["size"], "#9aa4ae"),
            v2=np.round(host["v2"], 2).tolist(), v3=np.round(hv3 - s["ax"] * SCREW_PULL, 2).tolist(), host=host["id"])
        nodes.append(dict(name=nid, mesh=screw_geo[gk], matrix=M))
        if not s.get("fit", True):          # drawn so the hole is visible, but not counted as a part to fit
            man_nodes[nid]["label"] += " (%s)" % s["fit_note"]
            man_nodes[nid]["fitted"] = False
            continue
        screw_rows.append(dict(spec=spec, line=s["line"], link=host["link"], sub=host["sub"], node=nid,
                               supplied=("in kit" if re.search(r"servo|kit|bag|comes", str(s["supplied"]), re.I) else "bought"),
                               desc="%s, %s head" % (s["anchor"] or "", s["head"]), note=s["note"] or "", washer=s.get("washer")))
    print(screw_note)

    # 10c. every cable (altaay_lab/cables3d/cables3d.json): points bound to links; the page builds the tubes
    cables_in, cable_note = load_cables3d()
    link_T = {ln: u.get_transform(ln) for ln in u.link_map}
    cables_out, cable_rows = [], []
    for c in cables_in:
        P, subs, follow = [], [], []
        for link, loc, world in c["pts"]:
            if world is not None:
                w = np.array(world, float)
            elif link in link_T and loc is not None:
                T = link_T[link]
                w = T[:3, :3] @ np.array(loc, float) + T[:3, 3] * 1000.0
            else:
                continue
            P.append(w)
            sub = LINK_SUB.get(link, "trunk")
            subs.append(sub)
            cand = [i for i in inst if i["link"] == link] or inst
            hi = min(cand, key=lambda i: float(np.linalg.norm(np.clip(w, i["bmin"], i["bmax"]) - w)))
            follow.append(hi["id"])
        if len(P) < 2:
            warnings.append("cable %s has fewer than 2 usable points" % c["id"])
            continue
        nid = "cable-%s" % c["id"] + ("-%d" % c["run_k"] if c.get("run") and c.get("run_k") else "")
        usubs = list(OrderedDict.fromkeys(subs))
        seats = []
        for st_ in c.get("seats") or []:     # seat centres in URDF world mm (or link frame + link)
            ctr = st_.get("center_mm") or st_.get("center")
            if ctr is not None and st_.get("frame") == "link" and st_.get("link") in link_T:
                T = link_T[st_["link"]]
                ctr = (T[:3, :3] @ np.array(ctr, float) + T[:3, 3] * 1000.0).tolist()
            seats.append(dict(kind=st_.get("kind"), part=st_.get("part"), center=[round(float(x), 2) for x in ctr] if ctr is not None else None,
                              size_mm=st_.get("size_mm"), note=st_.get("note") or st_.get("how") or ""))
        chk = c["check"].lower()
        man_nodes[nid] = dict(label="Cable %s%s: %s" % (c["id"], (" (" + c["run"] + ")") if c.get("run") else "", c.get("desc") or "%s to %s" % (c["frm"], c["to"])),
                              part="cable", file="(drawn) tube", cable=c["id"],
                              link=None, sub=usubs[0], subs=usubs, category="cable", qty=1, material=c["gauge"], bom=None,
                              status="OK" if chk in ("pass", "ok", "") else c["check"], blockers=[], mount=str(c["note"] or ""),
                              v2=[0, 0, 0], color=c["color"])
        cables_out.append(dict(id=c["id"] + ((":" + c["run"]) if c.get("run") and c.get("run_k") else ""), cable=c["id"], run=c.get("run"),
                               seats=seats, desc=c.get("desc", ""), node=nid, color=c["color"], d_mm=c["d"], points=np.round(P, 2).tolist(),
                               point_sub=subs, point_follow=follow, **{"from": c["frm"]}, to=c["to"], gauge=c["gauge"],
                               wires=c["wires"], wires_detail=c["wires_detail"], cut_mm=c["cut_mm"], routed_mm=c["routed_mm"],
                               worst_mm=c["worst_mm"], check=c["check"], note=c["note"]))
        cable_rows.append(dict(id=c["id"], node=nid, check=("%s: worst %s mm vs cut %s mm" % (c["check"], c["worst_mm"], c["cut_mm"]))
                               if c["check"] else ""))
    # a cable with several runs: one BOM_FULL row lists every run node
    _runs = defaultdict(list)
    for r_ in cable_rows:
        _runs[r_["id"]].append(r_["node"])
    cable_rows = [dict(id=k, node=v[0], nodes=v, check=next((r_["check"] for r_ in cable_rows if r_["id"] == k and r_["check"]), "")) for k, v in _runs.items()]
    print(cable_note)

    # 10d. cable ties, adhesive mounts and guides (cables3d.json "retention"): the page draws them, BOM_FULL counts them
    retention_out, tie_rows = [], []
    tie_line = next((lid for lid, b in bom_full.bom_lines().items() if re.search(r"cable tie|zip tie", b["Item"], re.I)), "")
    for n_, r in enumerate(retention_in, 1):
        c = r.get("center_mm") or r.get("center")
        if c is None:
            continue
        w = np.array(c, float)
        link = r.get("link")
        cand = [i for i in inst if i["link"] == link] or inst
        hi = min(cand, key=lambda i: float(np.linalg.norm(np.clip(w, i["bmin"], i["bmax"]) - w)))
        kind = str(r.get("kind", "cable tie"))
        gap, note = bool(r.get("gap")), str(r.get("note") or "")
        if kind.lower().startswith("gap"):   # "gap: no printed surface within 15 mm" names a gap, not a kind of retention
            gap = True
            note = "; ".join(x for x in (kind.split(":", 1)[1].strip() if ":" in kind else "", note) if x)
            kind = next((str(v) for k, v in r.items() if k != "kind" and "kind" in k and v), "cable tie")
        nid = "tie-%03d" % n_
        mtype = (r.get("mount_fit") or {}).get("type")
        if "mount" in kind:
            line = {"MB3A": "34", "ABM1M": "34b"}.get(mtype, "")    # D25: one BOM row per mount type; no fit, no part
        elif "printed" in kind:
            line = ""                                                # stock hole or drilled tie-hole pair: the tie only
        else:
            line = tie_line
        cabs = r.get("cables") or []
        man_nodes[nid] = dict(label="%s%s holding %s" % (kind[0].upper() + kind[1:], " (gap: no CAD feature)" if gap else "", ", ".join(cabs) or "cables"),
                              part="tie", file="(drawn)", link=hi["link"], sub=hi["sub"], category="tie", qty=1, material=None,
                              bom=line or None, status="GAP" if gap else "OK", blockers=[], mount=note,
                              v2=np.round(hi["v2"], 2).tolist(), host=hi["id"], gap=gap, kind=kind, cables=cabs)
        retention_out.append(dict(id=str(r.get("id", nid)), node=nid, kind=kind, cables=cabs, center=np.round(w, 2).tolist(),
                                  axis=[float(x) for x in (r.get("axis") or [1, 0, 0])], follow=hi["id"], gap=gap,
                                  part=r.get("part"), note=note))
        tie_rows.append(dict(kind=kind, line=line, node=nid, gap=gap, mount=mtype))
    if retention_out:
        print("%d retention items (ties, mounts, guides) from cables3d.json" % len(retention_out))

    # 10e. connectors, splices, resistors, foam pads, discs (altaay_lab/viewer/scene_extras.json): solid small parts
    extras_path = os.path.join(HERE, "scene_extras.json")
    n_extra = 0
    replaced = OrderedDict()            # placeholder node id -> the small parts that replace its dashed box
    c3_raw = json.load(open(CABLES3D_JSON)) if os.path.exists(CABLES3D_JSON) else {}
    E3 = {e["id"]: e for e in (c3_raw.get("cable_ends") or []) if isinstance(e, dict) and e.get("p_world0") is not None}
    followed = []                       # scene_extras splices moved to their cables3d.json seat of this run
    bpos, bidx = unit_box()
    gidx["_solidbox"] = len(geoms)
    geoms.append(dict(name="small_part_box", pos=bpos, idx=bidx, src_faces=12))
    if os.path.exists(extras_path):
        raw = json.load(open(extras_path))
        items = raw.get("items", raw) if isinstance(raw, dict) else raw
        for it in items:
            c = it.get("center_mm")
            d = it.get("dims_mm")
            if c is None or d is None:
                continue
            w = np.array(c, float)
            sid = str(it.get("id", ""))
            moved = None
            # a splice that sits on its own cables3d.json seat (blueprint: centre = cable_ends[name]) follows that seat when
            # the routes move it (cables agent), so the sleeve stays on the cable without a blueprint re-run
            anc = E3.get(sid[len("splice-"):]) if it.get("kind") == "splice" and sid.startswith("splice-") else None
            if anc and "splice" in str(anc.get("kind", "")):
                a = np.array(anc["p_world0"], float)
                if float(np.linalg.norm(a - w)) > 0.05:
                    moved = round(float(np.linalg.norm(a - w)), 2)
                    followed.append("%s %.2f mm" % (sid, moved))
                    w = a
            link = it.get("link")
            cand = [i for i in inst if i["link"] == link] or inst
            hi = min(cand, key=lambda i: float(np.linalg.norm(np.clip(w, i["bmin"], i["bmax"]) - w)))
            M = np.eye(4)
            R3, dl = it.get("rotation_3x3"), it.get("dims_local_mm")
            if R3 is not None and dl is not None:   # exact box: columns are the world directions of width, height, length
                M[:3, :3] = np.array(R3, float) @ np.diag([float(dl[1]), float(dl[2]), float(dl[0])])
                d = dl
            else:
                ax = np.array(it.get("axis") or [1, 0, 0], float)
                ax = ax / (np.linalg.norm(ax) or 1.0)
                R = rot_z_to(ax)                     # box z along the item's long axis
                M[:3, :3] = R @ np.diag([float(d[1]), float(d[2]), float(d[0])])
            M[:3, 3] = w
            round_ = str(it.get("shape") or "").lower() in ("cylinder", "cone")   # a cone is drawn as its cylinder envelope
            if round_ and "_solidcyl" not in gidx:
                ypos, yidx = cylinder(1.0, 1.0, 24)
                gidx["_solidcyl"] = len(geoms)
                geoms.append(dict(name="small_part_cylinder", pos=ypos, idx=yidx, src_faces=int(len(yidx))))
            n_extra += 1
            nid = "x-%s" % re.sub(r"[^A-Za-z0-9_-]", "_", str(it.get("id", n_extra)))
            man_nodes[nid] = dict(label=str(it.get("label", it.get("id", ""))), part=str(it.get("kind", "other")), file="(drawn) small part",
                                  link=hi["link"], sub=hi["sub"], category="connector", qty=1, material=None,
                                  bom=it.get("bom_line"), bom_full_row=it.get("bom_full_row"), bom_full_item=it.get("bom_full_item"),
                                  status="OK", blockers=[],
                                  mount=str(it.get("source", "")), kind=it.get("kind"), color=it.get("color"),
                                  dims=[float(x) for x in d], v2=np.round(hi["v2"], 2).tolist(), host=hi["id"])
            if it.get("bom_full_rows_also"):
                man_nodes[nid]["bom_full_rows_also"] = list(it["bom_full_rows_also"])
            if it.get("render"):                     # "translucent": a wrap or skin (kapton on the BMS)
                man_nodes[nid]["render"] = str(it["render"])
            if it.get("kind") in ("splice", "heat_shrink"):   # a heat shrink sleeve: BOM_FULL counts it against its joint
                man_nodes[nid]["sleeve"] = sid
                if moved:
                    man_nodes[nid]["mount"] += "; centre moved %.2f mm to its cables3d.json seat of this run" % moved
            ph = "ph-%s" % it["replaces_placeholder"] if it.get("replaces_placeholder") else None
            if ph in man_nodes:
                replaced.setdefault(ph, []).append(nid)
            nodes.append(dict(name=nid, mesh=gidx["_solidcyl" if round_ else "_solidbox"], matrix=M))
        nodes[:] = [n for n in nodes if n["name"] not in replaced]   # the real items replace the dashed placeholder boxes
        print("%d small parts from viewer/scene_extras.json%s" % (n_extra, ("; placeholder boxes replaced: " + ", ".join(
            "%s by %s" % (ph, ", ".join(v)) for ph, v in replaced.items())) if replaced else ""))
        if followed:
            print("splices moved to their cables3d.json seats: " + ", ".join(followed))
        # sleeves blueprint/make_scene_extras.py placed at a fixed offset from a cables3d seat it does not follow here:
        # warn when the seat moved away (re-run the blueprint script, or let step 10f place them)
        for it in items:
            exp = SLEEVE_OFFSET.get(str(it.get("id", "")))
            anc = E3.get(exp[0]) if exp else None
            if anc and it.get("center_mm") is not None:
                dist = float(np.linalg.norm(np.array(anc["p_world0"], float) - np.array(it["center_mm"], float)))
                if abs(dist - exp[1]) > 1.0:
                    warnings.append("scene_extras.json %s is %.1f mm from its cables3d.json seat %s (placed %.1f mm off it): "
                                    "re-run blueprint/make_scene_extras.py" % (it["id"], dist, exp[0], exp[1]))

    # 10f. heat shrink sleeves the netlist calls for (viewer/bom_full.py sleeve_joints, the rule BOM_FULL counts) that
    # scene_extras.json does not draw: placed now from cables3d.json (cable ends and routed runs), so they follow the routes
    import bom_full
    import yaml
    netlist = yaml.safe_load(open(os.path.join(LAB, "wiring", "netlist.yaml"), encoding="utf-8"))
    od_of = {}
    for c3c in c3_raw.get("cables") or []:
        for wr in c3c.get("wires") or []:
            if isinstance(wr, dict) and wr.get("od_mm"):
                od_of.setdefault(wr.get("gauge"), float(wr["od_mm"]))
    have = {r.get("sleeve") for r in man_nodes.values() if r.get("sleeve")}
    runs_of = defaultdict(list)
    for co in cables_out:
        runs_of[co["cable"]].append(co)
    sl_new, sl_skip, placed = [], [], []
    if "_solidcyl" not in gidx:
        ypos, yidx = cylinder(1.0, 1.0, 24)
        gidx["_solidcyl"] = len(geoms)
        geoms.append(dict(name="small_part_cylinder", pos=ypos, idx=yidx, src_faces=int(len(yidx))))
    joints = bom_full.sleeve_joints(netlist)
    jmap = {j["id"]: j for j in joints}
    for rec in man_nodes.values():           # every drawn sleeve names the netlist pin(s) of its joint (verify C1 checks them)
        if rec.get("sleeve") in jmap:
            rec["sleeve_pins"] = list(jmap[rec["sleeve"]]["pins"])
    g27 = np.array(np.meshgrid([-0.45, 0, 0.45], [-0.45, 0, 0.45], [-0.45, 0, 0.45])).reshape(3, -1).T

    def inside_parts(w, ax, L, D):
        """CAD parts that hold any of 27 sample points of a sleeve (blueprint/check_scene_extras.py method)"""
        pts = w + (g27 * np.array([D, D, L])) @ rot_z_to(ax).T
        lo_, hi_ = pts.min(0), pts.max(0)
        hit = {}
        for i in inst:
            if np.any(i["bmax"] < lo_) or np.any(i["bmin"] > hi_):
                continue
            if i["id"] not in world_mesh:
                world_mesh[i["id"]] = src[i["key"]].copy().apply_transform(i["T"])
            m_ = world_mesh[i["id"]]
            if m_.is_watertight:
                n_in = int(m_.contains(pts).sum())
                if n_in:
                    hit[i["key"]] = n_in
        return hit

    for j in joints:
        if j["id"] in have:
            continue
        pl = place_sleeve(j, netlist, E3, runs_of, od_of)
        if pl is None:
            sl_skip.append(j["id"])
            warnings.append("heat shrink sleeve %s (%s %s) has no cables3d.json seat or route to place it on: not drawn" % (
                j["id"], j["kind"], j["name"]))
            continue
        cands, (L, D), how = pl

        def clash(c_):
            """CAD parts holding the sleeve, plus 'sleeve' when it overlaps a sleeve placed before it in this step"""
            h_ = inside_parts(c_[0], c_[1], L, D)
            a_ = c_[0] + np.outer(np.linspace(-0.5, 0.5, 5) * L, _unit(c_[1]))
            for w2, ax2, L2, D2 in placed:
                b_ = w2 + np.outer(np.linspace(-0.5, 0.5, 5) * L2, _unit(ax2))
                if float(np.min(np.linalg.norm(a_[:, None, :] - b_[None, :, :], axis=2))) < (D + D2) / 2.0:
                    h_["sleeve"] = h_.get("sleeve", 0) + 27
            return h_
        tried = [(cands[0], clash(cands[0]))]
        k_ = 1
        while tried[-1][1] and k_ < len(cands):       # the first candidate that lies in no CAD part and no other sleeve
            tried.append((cands[k_], clash(cands[k_])))
            k_ += 1
        (w, ax, txt), hit = min(tried, key=lambda x: sum(x[1].values())) if all(h for _, h in tried) else tried[-1]
        how = dict(how, text=txt + ("; still dips into %s (%s of 27 sample points)" % (", ".join(hit), sum(hit.values())) if hit else ""))
        if hit:
            warnings.append("heat shrink sleeve %s lies partly inside %s at every spot tried" % (j["id"], ", ".join(hit)))
        placed.append((w, ax, L, D))
        cand = [i for i in inst if i["link"] == E3.get(how["anchor"], {}).get("link")] or inst
        hi = min(cand, key=lambda i: float(np.linalg.norm(np.clip(w, i["bmin"], i["bmax"]) - w)))
        M = np.eye(4)
        M[:3, :3] = rot_z_to(ax) @ np.diag([D, D, L])
        M[:3, 3] = w
        nid = "x-%s" % re.sub(r"[^A-Za-z0-9_-]", "_", j["id"])
        kind = "splice" if j["kind"] == "splice" else "heat_shrink"
        label = ("Splice %s (%s), solder in adhesive heat shrink" % (j["name"], ", ".join(j["cables"])) if kind == "splice" else
                 "Heat shrink over the %s joint at %s (%s, %s)" % (j["kind"], j["name"], ", ".join(j["cables"]), j.get("other", "")))
        man_nodes[nid] = dict(label=label, part=kind, file="(drawn) small part", link=hi["link"], sub=hi["sub"],
                              category="connector", qty=1, material=None, bom="26",
                              bom_full_item="Heat shrink pieces (splices and solder joints)", status="OK", blockers=[],
                              mount="Placed by make_viewer_data.py step 10f from cables3d.json: %s. %s; %s" % (
                                  how["text"], j["note"], how["size"]), kind=kind, color="#202020" if kind == "splice" else "#2b2b2b",
                              dims=[L, D, D], v2=np.round(hi["v2"], 2).tolist(), host=hi["id"], sleeve=j["id"],
                              sleeve_pins=list(j["pins"]))
        nodes.append(dict(name=nid, mesh=gidx["_solidcyl"], matrix=M))
        sl_new.append(j["id"])
    print("heat shrink sleeves placed from cables3d.json (not in scene_extras.json): %d%s%s" % (
        len(sl_new), (" (" + ", ".join(sl_new) + ")") if sl_new else "", ("; not placed: " + ", ".join(sl_skip)) if sl_skip else ""))

    glb_path = os.path.join(out, "duck.glb")
    write_glb(glb_path, geoms, nodes)
    # base64 text copy for the artifact page: the artifact host serves text and images, not .glb
    import base64
    with open(glb_path, "rb") as fh, open(os.path.join(out, "duck.glb.txt"), "w") as fo:
        fo.write(base64.b64encode(fh.read()).decode("ascii"))

    # 11. checklist
    found = Counter(r["part"] for r in man_nodes.values() if r["category"] in ("pla", "tpu"))
    printed_rows = []
    for stem in sorted(set(pd_) | {k for k in found}):
        d = pd_.get(stem, {})
        exp, got = d.get("qty"), found.get(stem, 0)
        note = ""
        if "guide x1" in d.get("flags", ""):
            note = "Print guide lists 1, the CAD and PRINT_CHECK use 2 (issue #26)"
        printed_rows.append(dict(stl=stem + ".stl", label=label_of(stem), expected=exp, found=got,
                                 material=d.get("material"), g_each=d.get("g_each"), h_each=d.get("h_each"),
                                 g_total=d.get("g_total"), h_total=d.get("h_total"), flags=d.get("flags"),
                                 file_in_print=stem in print_files, ok=(exp == got and stem in print_files), note=note,
                                 nodes=[k for k, r in man_nodes.items() if r["part"] == stem and r["category"] in ("pla", "tpu")]))
    servo_n = len({r["group"] for r in man_nodes.values() if r.get("group")})
    bom_rows = []
    ph_by_part = defaultdict(list)
    for k, r in man_nodes.items():
        ph_by_part[r["part"]].append(k)
    servo_nodes = [k for k, r in man_nodes.items() if r.get("group")]
    for b in bom:
        default = ("none", [], [], "Tool" if b["section"].startswith("Tools") else "Test equipment"
                   if b["section"].startswith("Test equipment") else "Consumable or wire, counted in BOM_FULL.md")
        kind, parts, related, note = BOM_VIEW.get(b["line"], default)
        if b["line"] not in BOM_VIEW and not (b["section"].startswith(("Tools", "Test equipment", "Cables"))):
            warnings.append("BOM line %s (%s) has no view mapping" % (b["line"], b["item"]))
        exp = num(b["need"]) if re.match(r"^\s*\d+\s*$", b["need"] or "") else None
        if kind == "filament":
            ids = [k for k, r in man_nodes.items() if r["category"] == parts[0]]
            cnt = len(ids)
            exp = sum(d["qty"] for d in pd_.values() if d["cat"] == parts[0])
        elif parts == ["servo"]:                       # D32: line 1 counts the STS3215 C001 servos, line 1b the STS3250 knees
            want = "STS3250" if b["line"] == "1b" else "STS3215"
            ids = [k for k in servo_nodes if not man_nodes[k]["part"].startswith("horn") and man_nodes[k].get("model") == want]
            cnt = len({man_nodes[k].get("group") for k in ids})
        else:
            ids = []
            for pk in parts:
                ids += ph_by_part.get(pk, [])
            cnt = len(ids)
        rel = [k for pk in related for k in ph_by_part.get(pk, [])]
        show = {"cad": "In CAD", "placeholder": "Placeholder", "filament": "As %d printed parts" % cnt}.get(kind, "Not modelled")
        if kind == "placeholder" and any(not k.startswith("ph-") for k in rel):
            show += " + CAD body (replaced)" if any(man_nodes[k].get("replaced") for k in rel) else " + CAD body"
        if kind == "cad" and parts == ["servo"]:
            show += " (%d servos)" % cnt
        ok = None if kind == "none" else (exp is None or cnt == exp)
        bl = re.findall(r"\bB\d+\b", b["verified"])
        bom_rows.append(dict(line=b["line"], section=b["section"], item=b["item"], spec=b["spec"], need=b["need"],
                             buy=b["buy"], supplier=b["supplier"], verified=b["verified"], kind=kind, show=show,
                             count=cnt if kind != "none" else None, expected=exp, ok=ok, note=note,
                             blockers=sorted(set(bl), key=lambda s: int(s[1:])), nodes=ids + rel))
    extra_rows = []
    for key, why in (("antenna", "Antenna rod: optional PLA part, in the CAD but not in print/ (print/PRINT_PLAN.md); filament line 27"),
                     ("horn_drive", "Servo horns: ship with the servo (BOM line 1), 2 per servo")):
        ids = [k for k, r in man_nodes.items() if r["part"] == key or (key == "horn_drive" and r["part"] == "horn_idle")]
        if ids:
            extra_rows.append(dict(item=why, count=len(ids), nodes=ids))

    notes = []
    pc_txt = open(os.path.join(LAB, "PRINT_CHECK.md"), encoding="utf-8").read()
    for n_stl in sorted(set(re.findall(r"(\d+) STLs", pc_txt))):
        if int(n_stl) != len(pd_):
            notes.append(dict(kind="doc", text="PRINT_CHECK.md says %s STLs in one place; its per-STL table has %d rows and print/ has %d STL files." % (n_stl, len(pd_), len(print_files))))
    if any("guide x1" in (d.get("flags") or "") for d in pd_.values()):
        notes.append(dict(kind="doc", text="Bulb: the upstream print guide lists 1, the CAD and PRINT_CHECK use 2 (issue #26).",
                          nodes=[k for k, r in man_nodes.items() if r["part"] == "bulb"]))
    b9 = [b for b in bom if b["line"] == "9"]
    if b9 and "HENGE" in b9[0]["spec"]:
        notes.append(dict(kind="bom", text="BOM.md line 9 still names the HENGE 4 A UBEC; the 5 V placeholder uses the Pololu step-down size (about 18 x 18 x 8).",
                          nodes=[k for k, r in man_nodes.items() if r["part"] == "reg_5v"]))
    b8 = [b for b in bom if b["line"] == "8"]
    if b8 and "Tenergy" not in b8[0]["spec"] and "bms_tenergy" in placed_ids:
        notes.append(dict(kind="bom", text="BOM.md line 8 still names the JZK 2S BMS; the lab placement uses the Tenergy 32175 in the bms.stl slot.",
                          nodes=[k for k, r in man_nodes.items() if r["part"] in ("bms_cad", "bms_tenergy")]))
    lh = (cad_place.get("camera") or {}).get("lens_hole")
    if lh:
        off = max(abs(v) for v in lh["offset_from_pilot_centre_mm"])
        if off > 5.5:
            # Checked 2026-11-01 against the Raspberry Pi Camera Module 3 mechanical drawing (RP-008153-DS-1):
            # the lens (dia 5.75) sits on the upper hole row, 14.5 mm from the bottom edge, so it is 6.25 mm off the
            # 4-hole centre. The head.stl opening matches the real camera.
            notes.append(dict(kind="info", text="Camera: the lens opening in head.stl (D %.2f mm) is %.2f mm off the centre of the 4 pilots, on the upper pilot row. "
                              "This matches the Camera Module 3 drawing (RP-008153-DS-1: lens on the upper hole row, 14.5 mm from the bottom edge). Checked 2026-11-01, no change needed." % (lh["d_mm"], off),
                              nodes=[k for k, r in man_nodes.items() if r["part"] in ("camera", "head")]))
    doc_total = PRINT_SOURCE.get("total")      # D22 grams from print/SLICE_SUMMARY.md when load_docs() found it clean
    if doc_total is None:
        for t in md_tables(os.path.join(LAB, "PRINT_CHECK.md")):
            if t["header"][:4] == ["Material", "Parts", "Grams", "Hours"]:
                for r in t["rows"]:
                    if r["Material"].strip().lower() == "total":
                        doc_total = dict(parts=num(r["Parts"]), grams=num(r["Grams"]), hours=num(r["Hours"]))
    n_printed_found = sum(found.values())
    n_printed_exp = sum(d["qty"] for d in pd_.values())
    bom_kinds = Counter(r["kind"] for r in bom_rows)
    summary = dict(
        printed=dict(found=n_printed_found, expected=n_printed_exp, stl_files=len(pd_), stl_found=len([s for s in found if found[s]]),
                     grams=doc_total["grams"] if doc_total else round(sum(d["g_total"] or 0 for d in pd_.values()), 1),
                     hours=doc_total["hours"] if doc_total else round(sum(d["h_total"] or 0 for d in pd_.values()), 1),
                     doc_total_parts=doc_total["parts"] if doc_total else None,
                     grams_source=PRINT_SOURCE.get("doc", "PRINT_CHECK.md"), grams_note=PRINT_SOURCE.get("note", ""),
                     pla=sum(d["qty"] for d in pd_.values() if d["cat"] == "pla"), tpu=sum(d["qty"] for d in pd_.values() if d["cat"] == "tpu")),
        servos=dict(found=servo_n, expected=int(sum(num(b["need"]) for b in bom if b["line"] in ("1", "1b")))),
        inserts=dict(found=len(inserts), expected=int(num([b["need"] for b in bom if b["line"] == "16"][0])), by_part=dict(n_ins)),
        bearings=dict(found=kc["bearing"], expected=int(num([b["need"] for b in bom if b["line"] == "18"][0]))),
        placeholders=dict(total=len(ph_all), placed=sum(1 for p in ph_all if p["sub"] != "tray"), tray=len(tray_items)),
        bom=dict(lines=len(bom_rows), cad=bom_kinds["cad"], both=bom_kinds["both"], placeholder=bom_kinds["placeholder"],
                 filament=bom_kinds["filament"], not_modelled=bom_kinds["none"],
                 mismatches=[r["line"] for r in bom_rows if r["ok"] is False]),
        printed_mismatches=[r["stl"] for r in printed_rows if not r["ok"]],
        blockers_open=sorted([b for b, v in blk.items() if v["open"]], key=lambda s: int(s[1:])),
        blockers_total=len(blk),
        screws=dict(found=len(screws), by_spec=dict(sorted(spec_count.items()))),
        cables=dict(found=len(cables_out), passed=sum(1 for c in cables_out if str(c["check"]).lower() in ("pass", "ok")),
                    test_fit=sum(1 for c in cables_out if str(c["check"]).lower() == "test fit"),
                    failed=sum(1 for c in cables_out if str(c["check"]).lower() in ("fail", "failed"))))
    summary["cables"]["pass"], summary["cables"]["fail"] = summary["cables"]["passed"], summary["cables"]["failed"]

    # 11b. every-part BOM (viewer/bom_full.py): one row per distinct item, linked to the nodes that show it
    import bom_full
    import yaml
    netlist = yaml.safe_load(open(os.path.join(LAB, "wiring", "netlist.yaml"), encoding="utf-8"))
    bom_lines = bom_full.bom_lines()
    import csv as _csv
    parts_csv = list(_csv.DictReader(open(os.path.join(LAB, "print", "parts.csv"), encoding="utf-8")))
    sub_labels = {sid: l for sid, l, g, v in SUBS}
    bom_full_rows = bom_full.build(man_nodes, sub_labels, netlist, bom_lines, parts_csv,
                                   fasteners=screw_rows or None, cables3d=cable_rows or None, link_sub=LINK_SUB,
                                   ties=tie_rows or None)
    row_by_id = {r["id"]: r for r in bom_full_rows}
    row_by_item = {}
    for r in bom_full_rows:
        row_by_item.setdefault(r["item"], r)
    for nid, rec in man_nodes.items():  # small parts name their BOM_FULL row: link them so the row highlights them
        # by item name first (row ids shift when BOM_FULL is rebuilt), else by the row id they were written with
        row = row_by_item.get(rec.get("bom_full_item")) or row_by_id.get(rec.get("bom_full_row"))
        if row is not None:
            rec["bom_full_row"] = row["id"]           # the page opens the row by this id
        for r in [row] + [row_by_id.get(x) for x in rec.get("bom_full_rows_also") or []]:
            if r is not None and nid not in r["nodes"]:
                r["nodes"].append(nid)
    for ph, new in replaced.items():   # a replaced placeholder box: rows and notes point at the small parts instead
        for r in bom_full_rows + bom_rows + extra_rows + notes:
            if ph in (r.get("nodes") or []):
                r["nodes"] = list(OrderedDict.fromkeys(x for n in r["nodes"] for x in (new if n == ph else [n])))
        del man_nodes[ph]
    summary["placeholders"]["replaced"] = {ph: new for ph, new in replaced.items()}
    for r in bom_full_rows:            # cables carry the first purchase line of their row (wire, kit cable, USB, FPC)
        for nid in r["nodes"]:
            if nid in man_nodes and man_nodes[nid].get("category") == "cable" and r["line"]:
                man_nodes[nid]["bom"] = re.split(r",\s*", r["line"])[0]
                man_nodes[nid]["bom_lines"] = r["line"]
    def money(x):
        try:
            return round(float(str(x).replace("$", "").replace(",", "")), 2)
        except ValueError:
            return 0.0
    for r in bom_full_rows:
        r["line_cost"] = money(r.get("line_cost", ""))
    purchase = {lid: dict(item=b.get("Item", ""), spec=b.get("Spec", ""), supplier=b.get("Supplier", ""), link=b.get("Link", ""),
                          buy=b.get("Buy", ""), pack=b.get("Pack", ""), line_cost=money(b.get("Line $", "")), need=b.get("Need", ""),
                          verified=b.get("Verified", ""), ships=b.get("Ships to USA", ""), section=b.get("section", ""))
                for lid, b in bom_lines.items()}
    summary["bom_full"] = dict(rows=len(bom_full_rows), status=dict(Counter(r["status"] for r in bom_full_rows)),
                               needs_action=[r["id"] for r in bom_full_rows if r["status"] in ("MISSING", "SHORT", "CHECK")])

    cats = {
        "pla": dict(label="Printed PLA", color="#c5b9a3"), "tpu": dict(label="Printed TPU", color="#2a9d8f"),
        "servo": dict(label="Servo", color="#3d4656"), "horn": dict(label="Servo horn", color="#ee8434"),
        "electronics": dict(label="Electronics / PCB", color="#4f9f3a"), "battery": dict(label="Battery", color="#d1495b"),
        "bearing": dict(label="Bearing", color="#93a1b0"), "insert": dict(label="M3 insert", color="#d3a62c"),
        "placeholder": dict(label="Placeholder (not in CAD)", color="#a855c8"), "other": dict(label="Other modelled part", color="#7c6a58"),
        "screw": dict(label="Screw", color="#8f9aa5"), "cable": dict(label="Cable", color="#e07a1f"),
        "tie": dict(label="Cable tie, mount or guide", color="#5b6b7a"),
        "connector": dict(label="Connectors and small parts", color="#f2f2ee"),
    }
    cat_count = Counter(r["category"] for r in man_nodes.values())
    for k in cats:
        cats[k]["count"] = cat_count.get(k, 0)
    manifest = dict(
        meta=dict(generated=time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), script="altaay_lab/viewer/make_viewer_data.py",
                  units="mm", frame="URDF zero pose: x forward, y left, z up (glTF root turns it y-up, scale 0.001)",
                  sources=dict(urdf="mini_bdx/robots/open_duck_mini_v2/robot.urdf (Open_Duck_Mini b23317a)",
                               stl="print/ (STL commit 730c14b per PRINT_CHECK.md)", inserts="altaay_lab/audit/sites.json",
                               docs="altaay_lab/PRINT_CHECK.md, print/SLICE_SUMMARY.md (D22 print grams), BOM.md, HARDWARE_AUDIT.md section 6, MOUNTING.md"),
                  placements=pl_note, assembly_json_match=asm_ok, frame_check_mm=frame_check, frame_grown_mm=frame_grown,
                  unmapped=sorted(set(unmapped)), warnings=warnings,
                  glb=dict(bytes=os.path.getsize(glb_path), geometries=len(geoms), nodes=len(nodes),
                           triangles_unique=int(sum(len(g["idx"]) for g in geoms)),
                           triangles_drawn=int(sum(len(geoms[n["mesh"]]["idx"]) for n in nodes)),
                           source_triangles={g["name"]: g["src_faces"] for g in geoms}),
                  explode=dict(stage1=[0.0, 0.6], stage2=[0.2, 0.9], stage3=[0.5, 1.0], horn_pull=HORN_PULL, insert_pull=INSERT_PULL)),
        categories=cats,
        groups=[dict(id=g, label=l, subs=[s[0] for s in SUBS if s[2] == g and (s[0] in sub_c)]) for g, l in GROUPS],
        subassemblies={sid: dict(label=l, group=g, v1=list(v), centre=np.round(sub_c[sid], 1).tolist())
                       for sid, l, g, v in SUBS if sid in sub_c},
        tray=tray, nodes=man_nodes,
        servos=[dict(joint=g["joint"], id=SERVO_ID.get(g["joint"]), link=g["link"], axis_err_mm=g["axis_err"]) for g in servo_groups],
        blockers=blk,
        checklist=dict(summary=summary, printed=printed_rows, bom=bom_rows, extra=extra_rows, notes=notes),
        cables=cables_out,
        bom_full=bom_full_rows,
        purchase=purchase,
        retention=retention_out,
    )
    # V1 3D track (twin/complete3d): part and cable labels, the x-ray switch, and a flat strip cable drawn with its loop
    try:
        _lb = json.load(open(os.path.join(LAB, "twin", "complete3d", "labels.json")))
        manifest["labels"] = [dict(node=q["node"], text=q["text"], pos=q["pos_world"], anchor=q["anchor_world"], phi=q["phi"])
                              for q in _lb["labels"] if q["node"] in man_nodes]
        manifest["meta"]["labels_rule"] = _lb["meta"]["rule"]
    except (OSError, ValueError, KeyError):
        manifest["labels"] = []
    manifest["meta"]["xray"] = "X-ray switch: printed shells see-through, so the cables inside show"
    _TL = {}
    for _c in json.load(open(CABLES3D_JSON)).get("cables", []):
        if _c.get("shape") != "flat strip" or not _c.get("draw_points"):
            continue
        _pts, _ws = [], []
        for _q, _w in zip(_c["draw_points"], _c["draw_width_link"]):
            if _q["link"] not in _TL:
                _M = np.array(u.get_transform(_q["link"]), float)
                _M[:3, 3] *= 1000.0
                _TL[_q["link"]] = _M
            _M = _TL[_q["link"]]
            _pts.append((_M @ np.r_[_q["p"], 1.0])[:3].round(2).tolist())
            _ws.append((_M[:3, :3] @ np.array(_w, float)).round(4).tolist())
        for ce in manifest.get("cables", []):
            if str(ce.get("id")).split(":")[0] == _c["id"]:
                ce.update(points=_pts, width_world=_ws, shape="flat strip", width_mm=_c.get("width_mm"), thickness_mm=_c.get("thickness_mm"),
                          point_sub=[(ce.get("point_sub") or [None])[0]] * len(_pts),
                          point_follow=[(ce.get("point_follow") or [None])[0]] * len(_pts))
    manifest["meta"]["sources"].update(fasteners=screw_note, cables=cable_note, bom_full="altaay_lab/viewer/bom_full.py")
    with open(os.path.join(out, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, separators=(",", ":"))
    if args.write_bom:
        res = bom_full.write_docs(bom_full_rows, bom_lines, time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()))
        print("BOM_FULL.md and bom_full.csv:", res)

    # 12. report
    print("URDF instances %d, head internals %d, inserts %d, placeholders %d (tray %d)" % (
        n_urdf, len(inst) - n_urdf, len(inserts), len(ph_all), len(tray_items)))
    print("printed parts found %d / expected %d over %d STLs; servos %d / %d; inserts %d / %d %s" % (
        n_printed_found, n_printed_exp, len(pd_), servo_n, summary["servos"]["expected"], len(inserts),
        summary["inserts"]["expected"], dict(n_ins)))
    print("printed mismatches:", summary["printed_mismatches"] or "none")
    print("BOM lines %d: %s; mismatches %s" % (len(bom_rows), dict(bom_kinds), summary["bom"]["mismatches"] or "none"))
    print("unmapped meshes:", sorted(set(unmapped)) or "none")
    print("insert open ends unknown:", sum(1 for x in inserts if x["open_dir"] == 0))
    print(pl_note)
    for p in ph_all:
        print("  placeholder %-16s sub %-10s follow %-40s dist %s  %s" % (p["id"], p["sub"], p.get("follow"), p.get("follow_dist"), p.get("where", "")[:70]))
    for n in notes:
        print("NOTE:", n["text"])
    print("GLB %s: %.2f MB, %d geometries, %d nodes, %d unique / %d drawn triangles" % (
        glb_path, os.path.getsize(glb_path) / 1e6, len(geoms), len(nodes), manifest["meta"]["glb"]["triangles_unique"],
        manifest["meta"]["glb"]["triangles_drawn"]))
    for w in warnings:
        print("WARNING:", w)
    print("done in %.1f s" % (time.time() - t_start))


if __name__ == "__main__":
    main()
