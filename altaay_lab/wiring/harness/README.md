# Harness

How the wires plug together. The electrical list is still `wiring/netlist.yaml`. This folder does not replace it. It names the plug on each end, using parts already on the bill or already published for this duck.

What this reuses:

- `wiring/netlist.yaml` for every active conductor, pin, color, cut, joint, and current.
- `docs/assembly_guide.md` for the header solder method on the thick power wires, and for the warning that its eye and antenna picture is swapped against the code. This duck follows the netlist (decision D9), not that swapped picture.
- BOM lines 12, 21, 22, 22b, 22c, and 26b for XT30, Mini-SPOX, KK 254, and WAGO 221.
- Molex 2695 series chart and the 08-50-0114 / 2759 sheet, cited in `WIRES.md`.
- WAGO 221-413 and 221-415 sheets, cited in `WIRES.md`.
- `CABLE_MAP.md` for the Mini-SPOX 3.0 A figure on 22 AWG, recorded there from the Molex 5263 page on 2026-11-02.
- `HARNESS_BUILD.md` for the rule to label both ends before a cable goes in.
- `TEST_PLAN.md` section 2 for the meter method. The extra rows are in `TEST_POLARITY.md`.
- `circuitry/charger_board.yaml` pins JPI.STAT, JPI.EN, JPI.V3, and JPI.GND (PR 40).
- `twin/dock/flush/FLUSH_CONTACTS.md` for the five wells (PR 41). The diode part is not chosen there, so it is not chosen here.
- `software/SOFTWARE.md` section 11 for which link has a wire (PR 37). Wi-Fi and Bluetooth have no wire.
- Cable D12, the bought 300 mm camera ribbon (PR 38). That work did not add a wire.
- WireViz 0.4.1 for the two plug drawings under `wireviz/`.

A new distribution board is not in this folder. The WAGO 221 levers already bought are the distribution nodes. One lever body holds at most 5 wires. The servo plus node and the servo ground node have 6 wires each, so each uses one 221-415 and one 221-413. Ground uses one 221-415. Switched plus uses one 221-413. That uses the pocket pack already on the bill. Count is in `WIRES.md`.

No screw is added. No hole is opened. D39 and D42 are unchanged.

Read `PLUG_GUIDE.md` to build it. Read `WIRES.md` for one row per wire. Read `TEST_POLARITY.md` before the battery goes in.

Rebuild the wire list with `python3 altaay_lab/wiring/harness/make_harness.py`. Rebuild the step pictures with `python3 altaay_lab/wiring/harness/draw_steps.py`. Rebuild the WireViz drawings with WireViz 0.4 on the two `.yml` files.
