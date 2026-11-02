# 3D completeness: connectors, splices, solder joints and small parts for the exploded view

- When: 2026-11-01 10:17 PM (America/New_York)
- Source: this commit, branch claude/every-part; work by the 3D completeness sub-agent (agent BP), on Ahmed's ask that the 3D design include everything end to end
- Written: 2026-11-01 by the Claude Code agent

- viewer/scene_extras.json: 166 items the viewer draws as solid small parts, each linked to a BOM_FULL row: 48 connector bodies (Mini-SPOX housings and crimps, kit plugs, XT30 halves, USB plugs, FPC ends, the Pi header, the amp terminal block), 64 solder joints, 13 splices, 14 heat shrink sleeves, 5 resistors, 6 foam pads, eye glass discs and the reflector in their measured seats, the microSD, the ATO fuse, SG90 horns and the kapton wrap. Cable ends: 236 of 236 accounted for (212 drawn bodies, 24 are parts' own leads). Several connector sizes are UNVERIFIED stand-ins (drawings not reachable from this session).
- viewer/MISSING_3D.md: what is still not drawn (cable ties until the cable routing lists them, 62 screws without a length in the schedule, retention for the power splices, speaker and LED beads) and a seat-fit table.
- Seat fixes found once the 1.1 mm foam tape is counted: BEC Pro 2.8 mm lower, fuse holder 0.9 mm to -x, Pololu 2815 2.4 mm to -x, USB coil 1.9 mm to +y, 5 V regulator and amp 0.6 mm up; the P3 strap joint has no room where the holder presses on body_back; the reflector stands 4.8 mm proud of its seat. Being applied to the placements and the viewer next.
- blueprint/: make_scene_extras.py (generator), scene3d.py, check_scene_extras.py (collision check: 1 of 166 embedded, the P3 strap joint), coverage.json.
