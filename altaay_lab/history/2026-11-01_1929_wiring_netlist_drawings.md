# Wiring: netlist as the single source, schematic, harness and pictorial drawings, rule check clean

- When: 2026-11-01 7:29 PM (America/New_York)
- Source: this commit, branch claude/print-ready
- Written: 2026-11-01 by the Claude Code agent (drawings by its wiring sub-agent)

- wiring/netlist.yaml: 56 components, 224 pins, 118 conductors, 45 active cables (4 removed), every pin with label, domain, connector, pitch and source tag [U]/[L]/[I], every wire with gauge, colour, cut length and expected current.
- Drawings generated from the netlist (scripts stop if a cable is missing): odm_v2_wiring_pictorial (A2, every part drawn with its real terminals, every wire terminal to terminal), odm_v2_schematic (A3, with the Pi header table), odm_v2_harness (A3, body regions, joints crossed, cut list). The old odm_v2_wiring drawing is kept and marked superseded in WIRING.md.
- Decisions drawn: D8 to D13, D15 (servo power bypasses the adapter), D17 (7:24 PM ET: Omron SS-01 gold-contact foot switches, SS-10 fallback, plus a 2.2 kOhm pull-up per foot, because the feet go into the policy observation and the SS-10 needs a 160 mA minimum load).
- Electrical rule check (audit/erc.py): 0 errors, 0 warnings on the final netlist; it caught all 3 faults planted on purpose (a net short, 5 V on a 3.3 V GPIO, a 20 AWG wire in a 22 to 28 AWG crimp). It writes the beep list for the cable test (audit/continuity_checklist.csv).
- BOM: line 13 (SS-01 preferred), line 13b (2.2 kOhm pack); build total $837.14 (audit/bom_totals.py recomputes all totals).
- TEST_PLAN.md section 12: foot switch checks.
