# 2026-11-05 10:50 PM ET V1 track 8 phase 3, PR 24 review 4: the chest lead hole (D50; CAD check only)

Review finding: the 4 mm hole to be drilled behind the pad could not pass the bundle (six wires left the
pad: GND and SENSE each branched at the pad).
- The GND and SENSE branches now join at two splices inside the trunk, 60 mm from the pad: JGD (to DK2 G and BMS P-) and JSN
  (to the cell NTC and the wake branch). Only the four pad conductors pass the chest wall: 3 x 20 AWG and 1 x 26 AWG, a
  4.6 mm bundle (wiring/netlist.yaml DC1 to DC3, sheet 1, HARNESS_BUILD.md section 7).
- print/body_front.stl (twin/dock/chest_hole.py, section twin/dock/stl/chest_hole_section.png): one 6.0 mm hole at world
  (y 0, z 38) through the 10 mm chest wall, a 45 deg bell mouth 2 mm deep inside and a 0.8 mm chamfer at the pad, so the leads
  bend over a wide mouth. Re-sliced: 57.63 g, 3.97 h, no support. A grommet ring standing 2 mm proud inside was tried and
  dropped: the part prints +x up, so the ring hangs under the chest wall and needed 1.8 g of support inside the shell.
- The trunk grid and the routes were rebuilt on the new STL (self-check passed); cuts DC2 60 and 210 mm, DC3 60, 220, 120 and
  180 mm; cables3d, sheets, BOM_FULL, MOUNTING, DOCK_TWIN, DOCK_INTERFACE, PRINT_CHECK updated.
- Also fixed: the SW1 ON pin name in the netlist was unquoted YAML and lost its text; the ERC outputs and HARNESS_BUILD.md are
  regenerated (the dock cables get their own section).
