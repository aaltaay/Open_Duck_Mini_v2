# START HERE: Open Duck Mini v2 (Altaay lab fork)

Read this file first. It is written so a new agent on a different account can pick up the duck build with no other context.
Last written: 2026-11-01 2:18 PM ET by Legged Robots, Grok Bot agent of Ahmed Altaay.

## What this is
This repo is a public fork of [apirrone/Open_Duck_Mini](https://github.com/apirrone/Open_Duck_Mini). Upstream branch `v2` is left untouched at b23317a. All Altaay lab work lives ONLY on branch `altaay-lab`, ONLY in this `altaay_lab/` folder.

The robot: Open Duck Mini v2, an open source bipedal robot by Antoine Pirrone, inspired by Disney's BDX droid. About 42 cm tall, about 2.11 kg (sim mass), 14 Feetech STS3215 serial bus servos (5 per leg, 4 in the neck and head), Raspberry Pi Zero 2 W, BNO055 IMU, 2S 18650 pack. It walks with an RL policy trained in MuJoCo Playground and exported to ONNX.

Owner bot: **Legged Robots, Grok Bot agent of Ahmed Altaay**. The duck is one of four Altaay legged robots (with Minto, Tom and a humanoid, all in private lab repos).

Naming: "Mento" and "Minto" in older files and commits refer to the same owner bot, now named Legged Robots (Grok Bot agent of Ahmed Altaay).

## Current status (plain words)
- Research and hardware audit done. Nothing bought, nothing printed.
- Plan: build stock first, exactly as designed upstream. Next lab step: freeze the design, then make an assembly map.
- Sim: the stock BEST_WALK_ONNX_2 policy walks in MuJoCo with no falls, about 0.097 m/s for a 0.15 m/s command (sim/SIM_WALK.md). Sim pass only.
- Hardware audit (from upstream STL commit 730c14b): 58 heat-set inserts, 193 screws, 3 x 6804 bearings, every hole and cable measured. 29 BLOCKERS listed (HARDWARE_AUDIT.md).
- BOM before shipping and tax: build $715.27, with expression pack $761.22, with tools $899.89 (BOM.md, bom.json).
- Servo: evidence points to STS3215 7.4 V 1:345 "19 kg.cm" (C001), about 85 % confidence (SERVO_DEEP_DIVE.md).
- Power: Castle Creations CC BEC Pro set to 7.2 V plus a 15 A ATO fuse (decided by Ahmed 2026-11-01 1:09 PM ET; POWER.md, WIRING.md).
- Issue #48 question: posted upstream by aaltaay on 2026-11-01 1:08 PM ET: https://github.com/apirrone/Open_Duck_Mini/issues/48#issuecomment-6561836208 . DECISIONS.md D1 records this too.

## Hard requirements (lab-wide, set by Ahmed)
1. Self-charging dock: the robot finds a dock by itself (AprilTag), charges through pogo pins, and goes back to the dock at about 20 % battery.
2. Get up after falls, by itself.
3. Stairs: climb AND descend a 15-step US stair (197 mm rise, 254 mm tread, 25 mm nosing) at 10 s per step or faster, aiming for 4 s per step.
4. All of this must work in sim before anything is printed.

Open Duck Mini v2 exceptions (Ahmed, 2026-11-01):
- EXEMPT from the stair rule (item 3). The legs are too short for a 197 mm rise (altaay_lab/GAPS.md B7).
- Build stock first, exactly as designed upstream. Dock and get-up (items 1 and 2) are NOT exempt; they come later as a separate lab step.

## Lab rules
- Buy nothing without Ahmed's explicit OK. Send no messages, emails, posts or issue comments without his OK.
- BOMs list item prices without shipping costs, but every item must ship to the USA and carry longevity info (how long it will stay available, single source or not).
- No guesses: every number and part is measured or sourced (link or datasheet). If it cannot be, it is a BLOCKER, written down as one.
- Bus servos only (serial bus or CAN bus actuators, no PWM hobby servos for joints).
- Chinese parts only with a full continuous spec (rated, not just peak), a warranty and a sim model. Flag every Chinese and single-source part.
- Heavy data (videos, renders, sim outputs) goes on Ahmed's PC at F:\GrokBox_Archive, never in git. This is a public fork without the lab size hook, so check file sizes by hand (keep every file well under 5 MB).
- No em dashes in any file. Plain, short language. Say "sim pass only" for sim results.
- Full lab rules: altaay-lab-shared/AGENTS.md (private repo).

Duck note on "bus servos only": the 14 joint servos are serial bus. The optional antenna servos in the upstream design are SG90 PWM servos, which conflict with this rule. BOM.md line 14 lists them; GAPS.md B10a records this as a lab-rule gap; the stock build keeps them because Ahmed chose stock first, and a bus-servo swap belongs to the later lab step.

## Repo map (altaay_lab/ only)
| Path | What it is |
|---|---|
| START_HERE.md | This file. |
| README.md | Intro, official links, licenses, upstream commit pins. |
| STATE.md | Current state and next steps. |
| DECISIONS.md | Open questions D1, D2, D4, D6, D7 and the decided items. |
| BOM.md, bom.json | US BOM with item prices (no shipping), longevity and lab change lines. |
| GAPS.md | Gap list vs lab rules (B7 is the stair exemption reason). |
| REFERENCES.md | Sources. |
| SERVO_DEEP_DIVE.md | STS3215 variant analysis and the issue #48 question draft (section 7). |
| POWER.md, WIRING.md, wiring/ | Power design (BEC, fuse), wiring schematic (make_wiring.py, odm_v2_wiring.svg and .png). |
| sim/SIM_WALK.md, sim/run_stock_walk.py, sim/*.png | Stock walk check in MuJoCo and two stills. |
| HARDWARE_AUDIT.md | Full audit and the 29 BLOCKERS. |
| PRINT_CHECK.md | Print checks per part. |
| CABLE_MAP.md | Every cable, length and route. |
| MOUNTING.md | Inserts, screws, bearings per part. |
| audit/ | Measurement scripts (measure.py, screws.py, pocket.py, sites.py, cables.py, mkbom.py and others) and their json data. |
| history/ | One dated file per milestone. |

## Upstream pins
| Repo | Commit |
|---|---|
| Open_Duck_Mini (v2) | b23317a |
| Open_Duck_Mini_Runtime (v2) | 376de65 |
| Open_Duck_Playground (main) | b9be205 |
| Open_Duck_reference_motion_generator (main) | 3d7bc6f |
| STL set used by the audit | 730c14b |

CAD, STL and sim assets are not copied here. Use the upstream commits. Onshape CAD and the upstream BOM sheet are linked in README.md.

## Where things live
| What | Where |
|---|---|
| Lab docs, audit, BOM | This folder, branch altaay-lab |
| CAD | Upstream Onshape document and upstream STL files at the pinned commits (README.md). No lab CAD export yet. |
| Sim model and policy | Upstream repos at the pinned commits (MJCF, BEST_WALK_ONNX_2). Nothing trained by the lab. |
| Heavy files (stock walk video odm_v2_stock_walk.mp4 5.8 MB, upstream README and assembly photos, wiring and sim stills) | Only on the Grok Bot box at /workspace/odm_share/ (about 13 MB). NOT yet on F:\GrokBox_Archive. The archive copy should go under F:\GrokBox_Archive\workspace\odm_share\ when the box is next archived. |
| Lab-wide shared files (costs, CAD export standard, handoffs) | Private repo altaay-lab-shared and F:\GrokBox_Archive\lab_shared\ on Ahmed's PC (need Ahmed's access grant) |
| Google Drive | Ahmed's lab Drive folder "Altaay Robotics Lab" (private). It has no Duck folder yet. |

## Open decisions
Full text: [DECISIONS.md](DECISIONS.md).
- D1 Servo variant: buy C001 as written and bench test 1 or 2 first (recommended). The upstream question is now posted (see status).
- D2 Accept Feetech under the lab rule (no thermal duty curve), or require a duty test first?
- D4 Swap the generic UBEC for a Pololu D36V28F5 (US, spec'd)? That changes the as-is build.
- D6 Runtime and Playground have no license. Ask upstream to add one? (needs Ahmed's OK)
- D7 Pi Zero 2 W out of stock at US resellers: wait, pay eBay prices, or test another board?
- Decided 2026-11-01: stair exempt (12:51 PM ET), build stock first, dock and get-up later (12:53 PM ET), BEC Pro 7.2 V plus 15 A fuse (1:09 PM ET).

## Next steps
1. Ahmed answers D1, D2, D4, D6, D7. Watch issue #48 for a reply.
2. Freeze the design (BOM, print list, wiring), then make an assembly map.
3. With Ahmed's OK only: order one STS3215 of the chosen variant and bench test at 7.2 V and at low pack voltage.
4. Print one leg in PLA, check the 6804ZZ bearing seat (measured 32.19 mm) and insert size.
5. Bench test the CC BEC Pro (setpoint, dropout at 7.0 and 6.5 V input, temperature at 8 A).
6. Copy /workspace/odm_share to F:.
7. Later lab step: self-docking and get-up after falls, in sim first.

## How to contribute without conflicts
- One owner per file. The owner bot of this repo is Legged Robots, Grok Bot agent of Ahmed Altaay. Do not edit another agent's files; copy them and ask the owner (through Ahmed) for changes.
- History is one new file per entry: `altaay_lab/history/YYYY-MM-DD_HHMM_<topic>.md` (time in America/New_York). Never edit an old entry; write a new one that supersedes it.
- Never use a shared running log that several agents append to.
- If a second agent works in parallel, use a branch and a small PR per change. Always `git pull` right before you commit and push.
- Commit as: `git -c user.name=aaltaay -c user.email=aaltaay@users.noreply.github.com commit ...`
- In this fork: only branch `altaay-lab`, only folder `altaay_lab/`. Never push to upstream `v2` and never open a PR to apirrone without Ahmed's OK.
- Pull right before every push: `git pull origin altaay-lab`, then `git push origin altaay-lab`.
- This repo is PUBLIC: no prices beyond the BOM, no personal data, no private Drive ids or PC paths beyond the archive names above.
