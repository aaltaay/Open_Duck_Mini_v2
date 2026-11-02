# Fastener schedule: every screw, insert and washer found in the CAD, checked and posed

- When: 2026-11-01 10:26 PM (America/New_York)
- Source: this commit, branch claude/every-part; work by the fastener sub-agent (agent F)
- Written: 2026-11-01 by the Claude Code agent

- fasteners/: fasteners.json and fasteners.csv (413 records: 355 screws and 58 inserts, one record per instance with link, pose in the link frame, size, length, head, BOM line and check results), FASTENERS.md (totals, counts against the BOM, 23 findings, schedule by subassembly, a ledger of all 531 hole stacks, 265 used and 266 empty with a reason each), VIEWER_NOTE.md, 2 PNGs, scripts (make, sweep, report, render).
- 342 screws to fit: 221 bought, 59 from the servo bags, 56 factory fitted servo case screws, 6 from the SG90 bags; 2 D18 screws and 11 idle screws stay out; 8 washers new; no nuts, pins or bought standoffs.
- Holes were rebuilt from print/ because print/head.stl and roll_to_pitch differ from the URDF meshes by up to 5.0 mm; that resolved the 6 unknown anchors.
- Build-blocking findings (not print-blocking): (1) the 8 thigh to hip pitch idle horn screws sit in 0.8 mm recesses and a DIN 912 head overlaps roll_to_pitch by 1.19 mm at every hip pitch angle (2 more hit from 18.9 deg): ISO 7380 button heads clear; (2) 24 M3 heads sit in 5.5 mm recesses in the neck chain parts, DIN 912 heads are 5.50 to 5.68 mm: drill to 6.0 mm; (3) the eye pilots are blind (3.0 mm behind a 1.5 mm skin): M2.5x8 needs a 0.5 mm washer. Decisions D19 to D21 follow in the docs pass.
- BOM counts change: 17a 28, 17d 78, 17e 28, 17h 30 by size; new lines for 10 M3x6 ISO 7380, 4 M2.5x5 (speaker_interface has 4 holes, B8 said none) and 8 M2.5 washers.
