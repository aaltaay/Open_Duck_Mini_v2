# Dock re-run on the installed domes

2026-11-24. Sim pass only. The walk loads sts12_runD_policy.onnx. The dome height is gold_dome_install.json: 0.9 mm proud, 1.5 mm radius, the same five wells. The mat is nest v2. D61 was not edited.

Short check, one frame, marker in view: body-frame error 6.1 mm, yaw error 0.01 deg. That is not a dock rate.

Two seeds, the camera dock, osmesa:

| Seed | Result | Time | Seat to sun |
|---|---|---|---|
| 1 | charging dock | 28.1 s | 161.3 mm |
| 2 | charging dock | 33.0 s | 232.7 mm |

2 of 2 charged. Median time 30.5 s. This is not the 40-seed batch. The earlier 38 of 40 remains the larger sample (SEAT_CONTACTS.md). sim_dock_charge.mp4 is seed 1, labeled SIM, 35 s.

Contact ohms are still an assumption. BLOCKER for a hardware dock.
