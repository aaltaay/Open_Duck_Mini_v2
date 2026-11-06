# 2026-11-05 9:26 PM ET V1 track 8 phase 3 follow-up: dock wiring merged, routed, drawn and seated (D50; CAD check only)

The lead asked to finish D50 before the merge.
- wiring/netlist.yaml: the dock components (chest pad DKP, DK2, F2, RT1, WK1, DK6, DK7) and cables DC1 to DC4; P7 now ends at
  DK7, SW1 VIN is the OR node PACK_OR; SW1 ON takes the wake branch.
- 3D routes for DC1 to DC4 (twin/dock/seats/route2.py, dock_cables3d.py) in cables3d/cables3d.json; cuts from the routes.
- Sheet 1 (power) draws the dock region; all five sheets regenerated (150 of 150 wires in full).
- BOM_FULL rows for DK1 to DK7 (viewer/bom_full.py), viewer placeholders for the pad and the four boards, C1 map entries.
- Seats (twin/dock/dock_seats.json, close-ups dock_seats.png): DK2 on the inner face of body_front, the 5 A holder standing on
  the left inner side wall, DK6 and DK7 under trunk_top beside the 2813; VHB only, no screw or hole added (D42, D39).
- U3 (Pololu D30V30F5) takes 5 to 45 V in: 9.2 V passes.
- Checks against origin/altaay-lab: C1, C3, C4, C6, C9, C10, E4 with no new FAIL; viewer test STATE loaded, ERRORS none.
