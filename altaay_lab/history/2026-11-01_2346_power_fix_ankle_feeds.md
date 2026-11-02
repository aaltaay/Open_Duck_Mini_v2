# Power path fix: second feed into each ankle; 3S held until the walking log

- When: 2026-11-01 11:46 PM (America/New_York)
- Source: this commit, branch claude/finish-pass; study by the power path sub-agent (agent PW); decision D23 by the Claude Code agent under Ahmed's delegation
- Written: 2026-11-01 by the Claude Code agent

- sim/POWER_FIX.md, sim/power_fix.py, 3 figures (sim pass only). Ankle time under 6 V at nominal charge, typical and high-side corner: baseline 23.9 and 67.0 %; 22 AWG made leads 21.7 and 61.7 %; a feed to the knee 4.4 and 18.6 %; a feed into each ankle's free BUS 1 port (3b) 5.8 and 20.5 %; a 3S pack with the BEC regulating 0 and 13.8 %; 3S plus 3b 0 and 0 %. No buck-boost part fits the seat. No 2S option passes the high-side corner, where the BEC output itself is under 6 V 5.7 % of the walk.
- The gate is lenient, not strict: in MuJoCo the walk speed follows the mean servo voltage (98 % of trained speed at 7.2 V, 79 % at 7.0 V, 47 % at 6.0 V); with 3b the robot walks at 65 to 79 % of trained speed, with 3S plus 3b at 83 to 93 %.
- D23: build 3b now (cables SP4 and SP5, a 22 AWG pair from the belly splices to BUS 1 of SV24 and SV14, no new purchases, +11.7 g). Hold the 3S pack until the TEST_PLAN 9 walking log on the real robot: 3 x 18650 do not fit the battery bay, so 3S means a pouch pack, a 3S BMS that is 2.8 mm too long for the slot, a 3S charger, a pack monitor and an over-voltage cut; the plan is in POWER_FIX.md.
- The netlist, BOM, TEST_PLAN and 3D routes follow in the next netlist pass.
