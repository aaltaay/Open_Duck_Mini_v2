# Servo upgrade options, a contingency if the TO1 heat test fails

- When: 2026-11-01 10:53 PM (America/New_York)
- Source: this commit, branch claude/every-part; research by the servo upgrade sub-agent (agent SU) after Ahmed asked what a hot servo would mean
- Written: 2026-11-01 by the Claude Code agent

- SERVO_UPGRADE_OPTIONS.md: the Feetech STS3250 (12 V, 50 kg.cm) and STS3235 (12 V, 30 kg.cm) share the STS3215 body (45.22 x 24.72 x 35 mm, same spline and horns, Feetech drawings, matched to the URDF meshes), so the printed parts stay; their aluminium cases are tapped M2, so the self-tapping case screws become M2 machine screws.
- Only the STS3250 is usable on our 7.2 V bus (about 4.7 rad/s and 30 kg.cm estimated, against 5.3 rad/s and 19 kg.cm for the C001; behaviour at 7.2 V UNVERIFIED). The 12 V STS3215 and STS3235 need a 3S pack, which means reprinting the battery bay, a 3S BMS, charger and BEC setting.
- Sim (pass only): the knee heat comes from the stock gait, not our extra mass (3.55 W at the trained mass against 3.74 W ours); walking slower cuts it only 11 to 12 %. Any new servo needs a BAM identification and a policy retrain.
- Decision threshold from the TO1 knee thermal resistance: up to 6 K/W change nothing; 6 to 11 K/W keep the C001 with a 50 % walk duty and the temperature guard; 11 to 19 K/W STS3250 on both knees; above 19 K/W STS3250 on all 10 leg joints. Nothing is bought until the TO1 result.
