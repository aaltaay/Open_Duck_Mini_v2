# 2026-11-11 10:28 PM ET: the audit names the current wiring drawings

This follows history/2026-11-11_2226_complete_duck_audit.md. No nest files were edited. No GPU was started.

WIRING.md says the current drawings are wiring/sheets/, made by make_sheets.py, and that the older odm_v2 schematic, harness, and pictorial files are kept and are not the drawings to build from. The audit's first table had pointed at those older generators. It now points at wiring/sheets/make_sheets.py and make_dock_sheet.py, and step 1 says not to regenerate the old drawings.

The communications row now records two facts already in the repo: the Pi UART (pins 8 and 10) is unused, and SPI is not on the walking netlist (D57). WIRING.md section 1 still names P30B cells. The netlist rev note names the P45B pack. The netlist stays the source for the power tree.
