# Print mass study: lighter settings where strength allows

- When: 2026-11-01 11:38 PM (America/New_York)
- Source: this commit, branch claude/finish-pass; study by the print mass sub-agent (agent PM), after the mass budget showed the build 31 % over the trained model
- Written: 2026-11-01 by the Claude Code agent

- print/MASS_STUDY.md, print/mass_study.py, print/config_light/ (proposed configs; print/config/ and parts.csv unchanged in this commit). PrusaSlicer 2.7.2 on the 36 STLs (52 parts): upstream defaults 1090.5 g on the robot, current settings 1318.7 g, proposed 1190.4 g (saves 128.2 g; robot +25.2 % over the trained 2107.1 g instead of +31.3 %; centre of mass 0.5 mm forward, 2.9 mm up). Sim pass only.
- Proposed: 2 walls unless a rule needs more; insert bores and pilots in the insert parts get a solid ring (100 % infill modifier) instead of extra walls on the whole part. The head (4 walls), the neck chain (5 walls, 40 %), knee sheets, roll_motor_bottom, antenna holders, trunk_top and trunk_bottom, eyes, speaker stand and all spares stay heavy. A light head saves 48.7 g but the sim robot falls sooner on rough ground, so it stays.
- The side step tracking (0.25 against 0.46 trained) is not fixed by any print setting; it follows where the centre of mass sits.
- Decision D22 (adopt it, gated by light insert coupons in session S1) follows in the print package update.
