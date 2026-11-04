# START HERE: Open Duck Mini v2 (Altaay lab fork)

Read this file first. It is written so a new agent on a different account can pick up the duck build with no other context.
Last written: 2026-11-01 2:18 PM ET by Legged Robots, Grok Bot agent of Ahmed Altaay. Updated 2026-11-01 about 7:00 PM ET by the Claude Code agent (print-readiness pass under Ahmed's delegation; branch claude/print-ready, pull request into altaay-lab). Updated 2026-11-02 about 12:10 AM ET by agent NL2 (final docs pass of the night session: status, the decisions up to D24, repo map, next steps). Updated 2026-11-02 about 5:20 AM ET by agent INT (integration pass after the PRT, PWR, SW and CAB jobs: status, decisions D1 to D25, the test order, verification). Updated 2026-11-02 about 6:33 AM ET by agent SFX (last fixes for PR 6: mass budget, (c) walk and power path re-runs on today's netlist, the TEST_PLAN 5 hop bands of lead decision L3, the cable test fit label, the full verification). Updated 2026-11-03 about 4:00 PM ET by the twin integration agent (blocker counts with the twin and gym BLOCKERs B36 to B41). Updated 2026-11-03 about 5:00 PM ET by the structure twin integration agent (blocker counts with the structure twin BLOCKERs B42 to B46). Updated 2026-11-03 about 10:40 PM ET by the twin wave 2 integration agent (open decisions: the GPU time approved and waiting for the RunPod key, and the heel-wheel question).

## What this is
This repo is a public fork of [apirrone/Open_Duck_Mini](https://github.com/apirrone/Open_Duck_Mini). Upstream branch `v2` is left untouched at b23317a. All Altaay lab work lives ONLY on branch `altaay-lab`, ONLY in this `altaay_lab/` folder.

The robot: Open Duck Mini v2, an open source bipedal robot by Antoine Pirrone, inspired by Disney's BDX droid. About 42 cm tall, about 2.11 kg (sim mass) (the lab build is about 2.65 kg by the mass budget, sim/MASS_BUDGET.md, not weighed), 14 Feetech STS3215 serial bus servos (5 per leg, 4 in the neck and head), Raspberry Pi Zero 2 W, BNO055 IMU, 2S 18650 pack. It walks with an RL policy trained in MuJoCo Playground and exported to ONNX.

Owner bot: **Legged Robots, Grok Bot agent of Ahmed Altaay**. The duck is one of four Altaay legged robots (with Minto, Tom and a humanoid, all in private lab repos).

Naming: "Mento" and "Minto" in older files and commits refer to the same owner bot, now named Legged Robots (Grok Bot agent of Ahmed Altaay).

## Current status (plain words)
- Nothing bought, nothing printed. Phase: digital twin first. Ahmed, 2026-11-03: nothing is printed until the full digital twin is done (twin/, STATE.md). The coupon print (print/PRINT_PLAN.md: S1 11 coupons, 41.2 g PLA, 4.14 h; S2 one TPU sole) waits for that and for Ahmed's OK (lab rule 4).
- Decisions D1 to D25 are made (DECISIONS.md), most under Ahmed's delegation: C001 servos with a 1-servo bench test first; Tenergy 32175 BMS; 15 A fuse kept; Pololu 2815 MOSFET main switch with the stock panel switch as its control; Castle CC BEC Pro at 7.2 V; servo power bypasses the Waveshare adapter (D15, belly splices, one power lead per chain); Pololu 5 V regulator on the head floor; GPIO wired to the Runtime code; LED resistors; software battery cut-off (D16); SS-01 gold-contact foot switches with pull-ups (D17); screw fixes D18 to D21; light print profile (D22); second power feeds into both ankles, 3S pack held until the walking log (D23); a drilled hole for the projector leads (D24); cable retention on 75 tie points with stick-on mounts, three drilled tie-hole pairs and bundle ties checked at the test fit, joint loops at 3 x OD and twisted made cables (D25). Lead decisions under Ahmed's delegation (DECISIONS.md D21 and D23 notes): L1 the walking log times every servo; L2 the BelMetric lines join the test order as TO17; L3 the TEST_PLAN 5 hop bands per conductor: pass up to 28 mOhm, warn over 28 up to 40 mOhm (the walking log decides, the 3S plan is made ready), fail over 40 mOhm.
- Every part not in the upstream CAD has a measured seat (audit/placements.json, MOUNTING.md); every screw, insert and washer is in the fastener schedule (fasteners/); every cable is routed in 3D with its ties (cables3d/, 75 tie points). No STL edit: D20, D24 and D25 are drill steps after printing.
- Blockers: 22 of 46 cleared or decided; none blocks the coupon print (HARDWARE_AUDIT.md section 6). B36 to B41 come from the twins and the shared lab gym (sim pass only; STATE.md). B42 to B46 come from the structure twin (FEA pass only, on sim pass only loads; STATE.md); B42 and B43 wait for DECISIONS.md D26, open for Ahmed.
- Electrical verification (sim pass only): current budget (sim/CURRENT_BUDGET.md), ngspice power path to every servo as wired, D15 plus the D23 ankle feeds with the netlist lengths (sim/POWER_PATH_SIM.md 'As built') and the ankle fix study (sim/POWER_FIX.md), electrical rule check with 0 errors (audit/ERC_REPORT.md), wiring sheets from the netlist, and a hardware test plan with pass/fail numbers (TEST_PLAN.md). VERIFICATION.md runs every check that needs no robot: the last full run (2026-11-02 6:19 to 6:32 AM ET) gives 22 checks, 22 PASS, 0 FAIL, 0 NOT RUN, with 21 WARN findings (risks and test fits to measure on the bench; sim and test pass only).
- Bench software: the walking voltage log (TEST_PLAN 9, bench/power_log.py --walk) reads every servo on its own timer inside the walk loop's sleep and counts time under 6 V for every servo; 63 bench tests pass on a simulated servo bus (software/SOFTWARE.md section 6, VERIFICATION.md E8).
- Wiring: wiring/netlist.yaml is the single source for the sheets, the harness build sheet and the rule check.
- Every upstream issue and PR (137) is triaged in UPSTREAM_ISSUES.md; the gaps that affect this build are listed first.
- Exploded 3D parts check (private artifact): https://claude.ai/artifact/PHSJH2PwQZLhZnTf9WgaMo (data script viewer/make_viewer_data.py). 52/52 printed parts, 14/14 servos, 58/58 inserts, 3/3 bearings found in the CAD; 62 cable runs: 59 pass, 3 test fit (D12, S2 and S7 reach with less than the 40 mm slack; TEST_PLAN 1.4 decides).
- Sim: the stock BEST_WALK_ONNX_2 walks in MuJoCo with no falls on flat ground at the trained mass and at our heavier build, slower: the build is 2.65 kg, 26 % over the trained 2.107 kg; the walks ran at 2.77 kg and at 2.64 kg, and the print/MASS_STUDY.md (c) walk again at 2.65 kg (2652.8 g) (sim pass only; sim/MASS_BUDGET.md, print/MASS_STUDY.md). The upstream sim loop adds a +1.3 accelerometer bias that training and the robot do not; lab runs remove it (sim/SIM_WALK.md note).
- Known risks to measure on the bench: knee servo heat (TO1 thermal hold; SERVO_UPGRADE_OPTIONS.md if it fails), knee, ankle and head roll voltage sag on 2S (TEST_PLAN 9; with SP4/SP5 the knees and the head roll dip most; a servo hop over 28 mOhm per conductor, the TEST_PLAN 5 warn band, makes a knee over 10 % under 6 V likely), CC BEC Pro dropout, the Pololu 2815 at 99 % of its 6 A (55 C) rating in sim (TEST_PLAN 4.2), servo register 85 and firmware (upstream issue 48), BNO055 I2C glitches, hip yaw past 21.7 deg outside the walk (TEST_PLAN 8.2a).
- Issue #48 question: posted upstream by aaltaay on 2026-11-01 1:08 PM ET (DECISIONS.md D1). No reply read.

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
| DECISIONS.md | Decisions D1 to D25 with reasons (D1 through D7 began as open questions). |
| BOM.md, bom.json | US BOM with item prices (no shipping), longevity and lab change lines. |
| GAPS.md | Gap list vs lab rules (B7 is the stair exemption reason). |
| REFERENCES.md | Sources. |
| SERVO_DEEP_DIVE.md | STS3215 variant analysis and the issue #48 question draft (section 7). |
| POWER.md, WIRING.md, wiring/ | Power design (BEC, fuse), wiring tables, older drawings (wiring/sheets/ supersede them). |
| sim/SIM_WALK.md, sim/run_stock_walk.py, sim/*.png | Stock walk check in MuJoCo and two stills. |
| HARDWARE_AUDIT.md | Full audit and the 46 BLOCKERS. |
| PRINT_CHECK.md | Print checks per part. |
| CABLE_MAP.md | Every cable, length and route. |
| MOUNTING.md | Inserts, screws, bearings per part. |
| audit/ | Measurement scripts (measure.py, screws.py, pocket.py, sites.py, cables.py, mkbom.py and others) and their json data. |
| history/ | One dated file per milestone. |
| TEST_PLAN.md | Hardware tests with pass/fail numbers, from cable continuity to the walking voltage log. |
| UPSTREAM_ISSUES.md | Every upstream issue and PR triaged, gaps first. |
| sim/CURRENT_BUDGET.md, sim/current_budget.py | Servo current from the stock walk (sim pass only). |
| sim/POWER_PATH_SIM.md, sim/power_path_sim.py | ngspice model of the power path to every servo; topology as_built (the default) reads wiring/netlist.yaml (sim pass only). |
| wiring/netlist.yaml | Single source of truth for every pin and wire; drawings are generated from it. |
| audit/erc.py, audit/ERC_REPORT.md, audit/continuity_checklist.csv | Electrical rule check of the netlist and the beep list for the cable test. |
| audit/free_space.py, audit/place_parts.py, audit/placements.json | Free space in the swept trunk volume and the seats of parts not in the CAD. |
| audit/bom_md_to_json.py | Rebuilds bom.json from BOM.md. |
| print/ | Slicer configs, coupon generator, slice script and PRINT_PLAN.md. |
| viewer/ | Data script for the exploded 3D parts check. |
| BOM_FULL.md | Every part in the robot, one row per item, each tied to its BOM.md purchase line (generated by viewer/make_viewer_data.py --write-bom; do not edit by hand). |
| fasteners/ | Fastener schedule: every screw, insert and washer found in the CAD, with size, length, clearance and joint sweep checks and exploded-view poses (FASTENERS.md, fasteners.json, scripts). |
| cables3d/ | Every cable routed in 3D with seats, ties and joint loops (CABLES_3D.md, cables3d.json; route, seat and tie, check and render scripts). |
| software/ | Pi setup from a blank SD card to walking (PI_SETUP.md) and software notes (SOFTWARE.md). |
| bench/ | TEST_PLAN 6 to 12 scripts, battery and temperature guards, simulated-bus tests. |
| verify/ | Every check that runs without the robot: run_all.sh, one script per check; report.py writes VERIFICATION.md. |
| VERIFICATION.md | Verification matrix: result, evidence and proposed fix per check (generated by verify/report.py). |
| wiring/sheets/ | Clean wiring drawings, one subsystem per sheet, generated from the netlist (WIRING_SHEETS.md, make_sheets.py). |
| HARNESS_BUILD.md | Cable-by-cable harness build sheet: cut lengths, colours, end treatments, continuity tests (wiring/make_harness_build.py). |
| SERVO_UPGRADE_OPTIONS.md | Stronger servos in the same body, if the TO1 heat test fails (contingency only). |
| sim/MASS_BUDGET.md, sim/ADDED_MASS_SIM.md, sim/RUNTIME_THERMAL.md | Mass budget (2.65 kg build), the walk with the real mass and runtime and servo heat (both run on the 2.77 kg build before D22; sim pass only). |
| sim/POWER_FIX.md, sim/power_fix.py | Ankle voltage fix options and the 3S plan behind D23 (sim pass only). |
| print/MASS_STUDY.md, print/mass_study.py, print/config_light/ | Lightest print settings that keep the strength and fit rules (D22). |
| viewer/scene_extras.json | Connectors, splices, solder joints and small parts the exploded view draws (from blueprint/). |
| blueprint/ | Generator and collision check for viewer/scene_extras.json, plus coverage.json. |
| SOURCING_2026-11-02.md | Sourcing pass: missing purchase lines and stock rechecks (applied to BOM.md). |

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
Full text: [DECISIONS.md](DECISIONS.md). D1 to D25 are decided (D14 superseded by D15). Still Ahmed's call, most important first:
1. Rented GPU time, capped at $20, to train a walk policy at our real mass and on small terrain, and a get-up policy: asked and approved 2026-11-03 (Ahmed: "go ahead and do a run pod"; STATE.md), waiting for the RunPod key; nothing ran or was spent. Lab rule 7.
2. On hold until the twin is done (Ahmed, 2026-11-03): OK to start the coupon print session (print/PRINT_PLAN.md: S1 11 coupons, 41.2 g PLA, 4.14 h; S2 one TPU sole, 17.6 g, 2.19 h)? Lab rule 4.
3. OK to buy the test order (BOM.md "Needs test order", 17 lines, $231.50)? Lab rule 7.
4. Printer model (not in any lab file): the print package is printer-agnostic, bed at least 220 x 220 mm.
5. Before the right leg prints: D26 (roll_to_pitch and the knee sheet eye, HARDWARE_AUDIT B42 and B43) and the floor for the first walks (B45).
6. Keep developing the heel-wheel version in sim (the roll-to-walk switch, the wheel mounts)? (asked 2026-11-03; STATE.md)

## Next steps
1. Ahmed says yes or no to (a) the coupon print session and (b) the test order.
2. Coupon session: print the coupons and test parts (with the D22 light insert coupons and the T1 eye screw stack), check them against print/PRINT_PLAN.md, write the results in history/.
3. Test order arrives: TEST_PLAN.md sections 1 to 7 (cables, battery and BMS, BEC sweep and dropout, Pololu 2815 heat, regulator, one servo with register 85, firmware and the thermal hold, Kelvin hop resistance: pass up to 28 mOhm per conductor, warn up to 40, fail over 40).
4. First leg print and its checks (D18, D19, the B33 foot_side fit), then the other plates; the drill steps after printing (D20, D24, D25); freeze tag (STL pin, BOM, netlist, print settings) and the assembly map.
5. Harness build and the test fit (TEST_PLAN.md 1.3 to 1.5: sleeves, twist, loops, the 75 tie points, the fixed-length D12, S2 and S7 at both joint limits, ankle plugs).
6. Staged power-up with the hip yaw and head yaw limits, then the walking voltage log (TEST_PLAN.md sections 8 to 12). The log decides the 3S pack (D23).
7. Later lab step: self-docking, in sim first (needs a pack voltage and current monitor). Get-up after falls already works in sim with scripted programs (sim pass only; STATE.md Done); the real knee and hip stops are a BLOCKER.

## How to contribute without conflicts
- One owner per file. The owner bot of this repo is Legged Robots, Grok Bot agent of Ahmed Altaay. Do not edit another agent's files; copy them and ask the owner (through Ahmed) for changes.
- History is one new file per entry: `altaay_lab/history/YYYY-MM-DD_HHMM_<topic>.md` (time in America/New_York). Never edit an old entry; write a new one that supersedes it.
- Never use a shared running log that several agents append to.
- Merge after every job (Ahmed, 2026-11-01 late evening): when a job is done, open its PR into altaay-lab, merge it, then delete the branch on GitHub and locally. No branch is left behind; the only long-lived branches are altaay-lab and the upstream v1 and v2.
- If a second agent works in parallel, use a branch and a small PR per change. Always `git pull` right before you commit and push.
- Commit as: `git -c user.name=aaltaay -c user.email=aaltaay@users.noreply.github.com commit ...`
- In this fork: only branch `altaay-lab`, only folder `altaay_lab/`. Never push to upstream `v2` and never open a PR to apirrone without Ahmed's OK.
- Pull right before every push: `git pull origin altaay-lab`, then `git push origin altaay-lab`.
- This repo is PUBLIC: no prices beyond the BOM, no personal data, no private Drive ids or PC paths beyond the archive names above.
