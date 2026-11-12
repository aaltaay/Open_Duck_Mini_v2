# 2026-11-12 6:06 PM ET: companion software, a local assistant demo, and a CPU training smoke

Labels: the demo tests are Python checks with no hardware. The training numbers are sim pass only. Cited pages are named in the new notes. Nothing was spent.

- New folder altaay_lab/software/companion/. Ranked home behaviors, the published blocks to reuse, and an architecture that keeps timers and reminders on the duck and puts open questions, mail, and calendar behind an optional cloud client. The client in the repo is a mock. No key.
- Where a new body or privacy behavior would be specified, the notes say details held for later.
- Demo checks: 12 passed (timer, reminder, kid mode, offline, mock mail, existing dock state names, night-light flag).
- Training: the shared lab gym trainer was not launched. A CPU smoke of the upstream playground pin b9be205, flat terrain, imitation reward on, ran 480 env steps on 8 envs in 148.5 s (sim pass only). Five eval rewards stayed near 12 and did not climb. Not a policy. No checkpoint stored. The paid GPU scope stays the one in COMPLETE_DUCK_AUDIT.md and still waits for Ahmed's OK.
