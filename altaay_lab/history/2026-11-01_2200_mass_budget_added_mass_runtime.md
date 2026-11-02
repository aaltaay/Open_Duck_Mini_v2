# Mass budget, walk sim with the real mass, runtime and servo heat (sim pass only)

- When: 2026-11-01 10:00 PM (America/New_York)
- Source: this commit, branch claude/every-part; work by the sim sub-agent (agent M)
- Written: 2026-11-01 by the Claude Code agent

- sim/MASS_BUDGET.md (mass_budget.py): the build is about 2.77 kg against 2.107 kg in the trained MuJoCo model (+31 %): screws and inserts 196 g, wires 108 g and lab power parts 59 g are not in the CAD at all; printed parts are 267 g heavier at our wall counts; 193 g of items are UNVERIFIED. Whole-robot centre of mass about 2.6 mm back, 1.1 mm left, 3.0 mm up.
- sim/ADDED_MASS_SIM.md (added_mass_sim.py): the stock policy still walks on flat ground with the real mass (no falls in any case, 7 runs each), slower; the side step tracking halves (0.23 against 0.46). Rough terrain: 6 of 7 falls against 4 of 7 for the trained mass. Margin: +60 % trunk mass is fine; the robot tips backward standing once the centre of mass is 4 to 6 mm further back than estimated.
- sim/RUNTIME_THERMAL.md (runtime_thermal.py): continuous walking to the D16 stop about 31 min (typical), 26 min (conservative), 18 min (servos at 1.5 x sim power). Knee copper loss 3.1 to 5.8 W against the 1.06 W rated: servo heat is the risk to measure. No thermal resistance is published (BLOCKER until the TO1 bench run).
- Follow-ups being applied: TEST_PLAN 7.3 becomes a current-based thermal hold (1.5 A), TEST_PLAN 8 gains step 0 (weigh the robot and find its centre of mass before the first walk); D2, CURRENT_BUDGET.md and SIM_WALK.md wording in the next docs pass.
