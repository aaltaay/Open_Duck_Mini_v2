# 2026-11-11 9:36 PM ET: sit is stationary, walk heat uses RMS current

This supersedes the sit temperatures and the walk cell temperatures in history/2026-11-11_2126_p45b_sheet_thermal.md. Those used a walking airflow during the sit, and they squared the mean pack current. Both are fixed. Sim pass only. The charger watts are still calc only.

The docked sit now uses the stationary state. No walking air on the servos or the shell. Cells at 6 hours: 31.5 C and 33.7 C in a 25 C room (1.9 W and 3.2 W), 38.3 C and 40.4 C in a 32 C room, and 42.4 C in the pessimistic corner at 32 C and 3.2 W. Servo readings 27.6 C to 34.7 C. Trunk wall 28.6 C to 37.6 C. All still inside the cell charge window, the servo operating range, and under the 49 C to 57 C heat-deflection band. The charger can still stay in the trunk during a sit on this model.

Walk resistive heat now uses the RMS pack and BEC current in each 5 s bin. The right knee still reaches 60 C at 3.3 minutes (25 C) and 2.5 minutes (32 C), central corner. Central cells reach 49.7 C and 56.4 C. The pessimistic corner at 32 C reaches 63.9 C at the cells at 33 minutes if the walk is not cut. The knee body, if the torque stays on, is still 94.7 C and 101.6 C.

The pack session itself did not change: 42.9 minutes to an open circuit of 3.30 V per cell, no fall, trained actuator (sim pass only).
