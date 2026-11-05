# 2026-11-05 4:35 AM ET V1 track 8: review fixes for the dock behaviour and the dock sim, acceptance re-run (sim pass only)

The lead forwarded the Codex reviews of the duck repo PR 20 (3 P1 items in software/dock/autodock/duck_autodock.py) and the
shared lab gym PR 24 (1 item in the dock sim). All four were real and are fixed, each with a test:
- Undock timeout: do_undock() used the docking start time, so after a charge longer than dock_timeout the first guard failed and
  the duck stayed on the seat. It now has its own budget (undock_timeout 90 s from the undock start).
- Undock detections: start() turns the tag detections off once docked and do_undock() never turned them on, so back_off() ran
  blind. They are on for the retreat and off at the end.
- ENTER gate waived: once the sidesteps ran out, STEER_DOCK entered the last mile whatever the lateral error. It now fails the
  state (retry). The last-mile check point follows the same rule: no walk-in outside 20 mm and 4 deg after its checks.
- The sim's settle gain (gym side): the crouch callback wrote kp 4 back on every step, so the settle never relaxed to kp 2
  (9 of the 60 acc8 episodes). Retargeted; the sim now also honours the detections switch and checks an undock after every dock.
- Tests: 15 unit tests here (4 new; the 4 fail on the previous code), and a gym test of the settle gain.
- Re-run acc10, all three floors, all fixes in: hard 18/20, train 16/20, soft 10/20 docked within 3 tries (the same as acc8; no
  outcome changed, the gates never ran out of corrections); undock 19/19, 16/16 and 0/10 (every soft-floor undock falls on the
  back pulses, as the stock policy's back step does there). Acceptance still not met; twin/dock/DOCK_TWIN.md sections 3 and 4.
