# Print-readiness pass: decisions D1 to D16, power path verified in sim, every part seated

- When: 2026-11-01 7:01 PM (America/New_York); work from about 5:40 PM, when Ahmed delegated the decisions
- Source: this commit, branch claude/print-ready, pull request into altaay-lab
- Written: 2026-11-01 by the Claude Code agent, under Ahmed's delegation ("The majority of the decisions you're going to have to make ... If something fails, you don't ask me. You just improvise", objective: reach the 3D printing phase)

- Decisions D1 to D16 in DECISIONS.md: C001 servos with a 1-servo bench test first; Feetech accepted with a thermal test; Tenergy 32175 BMS; 15 A fuse kept; Pololu 2815 main switch controlled by the stock panel switch; Pololu D30V30F5 5 V regulator on the head floor; servo power bypasses the Waveshare adapter (belly splices, one lead per chain); GPIO wired to the Runtime code; projector LED resistor; software battery cut-off; Pi Zero 2 W kit fallback.
- Sim (sim pass only): servo current budget from the stock walk (sim/CURRENT_BUDGET.md), ngspice model of the power path to every servo (sim/POWER_PATH_SIM.md). Found and fixed: the upstream sim loop adds a +1.3 accelerometer bias that training and the robot do not have.
- Placement: free space over the swept trunk volume; BEC Pro, fuse holder, MOSFET switch, splices and USB slack all seated with no STL edit (audit/free_space.py, audit/place_parts.py, audit/placements.json, MOUNTING.md).
- Blockers: 17 of 29 cleared or decided (B1, B11, B12, B13, B22, B24, B28 in this pass), none print-blocking (HARDWARE_AUDIT.md section 6).
- BOM: build $836.39, with expression $918.79, with tools $1057.46, test order $216.81 (shipping and tax excluded). Nothing bought.
- Upstream: all 137 issues and PRs in the 4 upstream repos triaged (UPSTREAM_ISSUES.md); doc contradictions it found are fixed.
- New: TEST_PLAN.md (hardware tests with pass/fail numbers), audit/erc.py (electrical rule check), viewer/make_viewer_data.py (exploded 3D parts check, private artifact https://claude.ai/artifact/PHSJH2PwQZLhZnTf9WgaMo).
- Correction: clock times first written in this pass were wrong and were fixed before this commit (real times from file timestamps).
