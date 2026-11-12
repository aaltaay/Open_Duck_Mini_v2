# 2026-11-12 1:25 PM ET: the blind re-sit now uses the IMU heading, and the two scores are named

Labels: sim pass only. The flush box is calc only. Nothing ran on hardware. 190 mm stays the approved
distance. The 6:45 AM and 6:48 AM entries are kept as written.

- The 35 of 540 and the 380 of 540 are different tests. 35 is the old sun-and-ring pin rule. 380 is the
  seat centre inside the flush box (+/-254 mm along the wall, +/-161 mm deep). twin/dock/blind/BLIND_WALK.md
  says so in the first paragraphs. The flush box is the headline.
- A review found the 180 degree turn never updated the blind estimate, so a re-sit still thought the duck
  faced the wall. The turn itself is unchanged. After it, the estimate heading is the pre-turn estimate
  plus the simulated IMU yaw. The matrices were re-run.
- At 190 mm the first sit did not move: flush box 380 of 540, old pins 35 of 540, 0 falls. Within 3 sits
  is 383 of 540 on the flush box and 43 of 540 on the old pins (the backwards heading had given 98).
- At 215 mm, study only: 2 falls, flush box 370 and 373 of 540, old pins 26 and 50 of 540.
