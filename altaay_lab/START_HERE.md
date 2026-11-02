# START HERE: Open Duck Mini v2 (Altaay lab fork)

Read this file first. It is written so a new agent on a different account can pick up the duck build with no other context.
Last written: 2026-11-01 2:18 PM ET by Legged Robots, Grok Bot agent of Ahmed Altaay. Updated 2026-11-01 about 7:00 PM ET by the Claude Code agent (print-readiness pass under Ahmed's delegation, DECISIONS.md D1 to D18; branch claude/print-ready, pull request into altaay-lab).

## What this is
This repo is a public fork of [apirrone/Open_Duck_Mini](https://github.com/apirrone/Open_Duck_Mini). Upstream branch `v2` is left untouched at b23317a. All Altaay lab work lives ONLY on branch `altaay-lab`, ONLY in this `altaay_lab/` folder.

The robot: Open Duck Mini v2, an open source bipedal robot by Antoine Pirrone, inspired by Disney's BDX droid. About 42 cm tall, about 2.11 kg (sim mass), 14 Feetech STS3215 serial bus servos (5 per leg, 4 in the neck and head), Raspberry Pi Zero 2 W, BNO055 IMU, 2S 18650 pack. It walks with an RL policy trained in MuJoCo Playground and exported to ONNX.

Owner bot: **Legged Robots, Grok Bot agent of Ahmed Altaay**. The duck is one of four Altaay legged robots (with Minto, Tom and a humanoid, all in private lab repos).

Naming: "Mento" and "Minto" in older files and commits refer to the same owner bot, now named Legged Robots (Grok Bot agent of Ahmed Altaay).

## Current status (plain words)
- Nothing bought, nothing printed. Print-readiness pass done 2026-11-01 evening: no print-blocking blockers left. The first print is a short coupon session cut from the real parts (print/PRINT_PLAN.md) and it waits for Ahmed's OK (lab rule 4).
- Decisions made under Ahmed's delegation (DECISIONS.md D1 to D18): C001 servos with a 1-servo bench test first; Tenergy 32175 BMS; 15 A fuse kept; Pololu 2815 MOSFET main switch with the stock panel switch as its control; Castle CC BEC Pro at 7.2 V; servo power bypasses the Waveshare adapter (D15, belly splices, one power lead per chain); Pololu 5 V regulator on the head floor; GPIO wired to the Runtime code; projector LED resistor; software battery cut-off; SS-01 gold-contact foot switches with pull-ups (D17); one hip roll screw left out per leg (D18, upstream issue 17).
- Every part that is not in the upstream CAD has a measured seat inside the body (audit/free_space.py, audit/placements.json, MOUNTING.md). No STL edit is needed.
- Electrical verification (sim pass only): servo current budget from the stock walk (sim/CURRENT_BUDGET.md), ngspice model of the whole power path down to every servo (sim/POWER_PATH_SIM.md), electrical rule check of the netlist with 0 errors (audit/ERC_REPORT.md), and a hardware test plan with pass/fail numbers (TEST_PLAN.md).
- Wiring: machine-readable netlist (wiring/netlist.yaml) is the single source for the schematic, harness and pictorial drawings and for the rule check.
- Every upstream issue and PR (137) is triaged in UPSTREAM_ISSUES.md; the gaps that affect this build are listed first.
- Exploded 3D parts check (private artifact): https://claude.ai/artifact/PHSJH2PwQZLhZnTf9WgaMo (data script viewer/make_viewer_data.py). 52/52 printed parts, 14/14 servos, 58/58 inserts, 3/3 bearings found in the CAD.
- Sim: the stock BEST_WALK_ONNX_2 walks in MuJoCo with no falls (sim pass only). The upstream sim loop adds a +1.3 accelerometer bias that training and the robot do not; runs since 6:41 PM ET remove it (sim/SIM_WALK.md note).
- Known risks to measure on the bench: real servo hop resistance and voltage sag at the ankles (power sim gate), CC BEC Pro behavior below 7.2 V input (minimum not published), servo register 85 and firmware (upstream issue 48), BNO055 I2C glitches.
- Issue #48 question: posted upstream by aaltaay on 2026-11-01 1:08 PM ET (DECISIONS.md D1). No reply read in this pass.

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
| TEST_PLAN.md | Hardware tests with pass/fail numbers, from cable continuity to the walking voltage log. |
| UPSTREAM_ISSUES.md | Every upstream issue and PR triaged, gaps first. |
| sim/CURRENT_BUDGET.md, sim/current_budget.py | Servo current from the stock walk (sim pass only). |
| sim/POWER_PATH_SIM.md, sim/power_path_sim.py | ngspice model of the power path to every servo (sim pass only). |
| wiring/netlist.yaml | Single source of truth for every pin and wire; drawings are generated from it. |
| audit/erc.py, audit/ERC_REPORT.md, audit/continuity_checklist.csv | Electrical rule check of the netlist and the beep list for the cable test. |
| audit/free_space.py, audit/place_parts.py, audit/placements.json | Free space in the swept trunk volume and the seats of parts not in the CAD. |
| audit/bom_md_to_json.py | Rebuilds bom.json from BOM.md. |
| print/ | Slicer configs, coupon generator, slice script and PRINT_PLAN.md. |
| viewer/ | Data script for the exploded 3D parts check. |

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
Full text: [DECISIONS.md](DECISIONS.md). D1 to D18 are decided (D14 superseded by D15). Still Ahmed's call:
- OK to buy the test order (BOM.md "Needs test order") and OK for the coupon print session (print/PRINT_PLAN.md). Both need his yes (lab rules 4 and 7).
- Printer model (not in any lab file): the print package is printer-agnostic, bed at least 220 x 220 mm.

## Next steps
1. Ahmed reviews the pull request and the exploded view, then says yes or no to (a) the coupon print session and (b) the test order.
2. Coupon session: print the coupons and test parts, check them against the pass/fail list in print/PRINT_PLAN.md, write the results in history/.
3. Test order arrives: run TEST_PLAN.md sections 1 to 7 (cables, battery and BMS, BEC sweep, regulator, one servo with register 85 and firmware, Kelvin hop resistance).
4. Freeze: tag the design (STL pin, BOM, netlist, print settings) once the coupons and the bench gates pass, then the full print and the assembly map.
5. Staged power-up and the walking voltage log (TEST_PLAN.md sections 8 to 11).
6. Later lab step: self-docking and get-up after falls, in sim first (needs a pack voltage and current monitor).

## How to contribute without conflicts
- One owner per file. The owner bot of this repo is Legged Robots, Grok Bot agent of Ahmed Altaay. Do not edit another agent's files; copy them and ask the owner (through Ahmed) for changes.
- History is one new file per entry: `altaay_lab/history/YYYY-MM-DD_HHMM_<topic>.md` (time in America/New_York). Never edit an old entry; write a new one that supersedes it.
- Never use a shared running log that several agents append to.
- If a second agent works in parallel, use a branch and a small PR per change. Always `git pull` right before you commit and push.
- Commit as: `git -c user.name=aaltaay -c user.email=aaltaay@users.noreply.github.com commit ...`
- In this fork: only branch `altaay-lab`, only folder `altaay_lab/`. Never push to upstream `v2` and never open a PR to apirrone without Ahmed's OK.
- Pull right before every push: `git pull origin altaay-lab`, then `git push origin altaay-lab`.
- This repo is PUBLIC: no prices beyond the BOM, no personal data, no private Drive ids or PC paths beyond the archive names above.
