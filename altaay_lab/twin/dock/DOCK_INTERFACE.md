# DOCK_INTERFACE (track 8, the V1 self-charging dock)

Version 5, 2026-11-05 (replaces versions 1 to 4, which lived outside the repo): awake while docked (D50). Details:
DOCK_TWIN.md sections 2, 6 and 11. Labels: sim pass only, calc only, CAD check only. Nothing bought or printed.

## 1. Decisions
- Contacts (D43); 2S1P Molicel P45B, 8.40 V CV (D44); simplest, cheapest, most reliable (D45); awake while docked (D50).
- Charger in the dock: Microchip MCP73213 (1.1 A, 6 h timer, 10 % end of charge). The faster option is the TI BQ24610 (2.0 A).
- Hardware gate, no microcontroller and no Wi-Fi: seat microswitch in series with the gate switch, NTC window 5 to 45 C,
  pin-voltage window 5.0 to 8.45 V. The gate feeds both the charger and the SYS pin.
- The docked duck stays on: the dock supply (SYS, 9 V) runs it through an ideal-diode OR at the 2813 input; the pack only
  charges. Torque off while docked. The 2813 OFF is still a full shutdown; the 555 wake pulse stays for that mode.

## 2. Contacts (dock: six Mill-Max 0932 spring pins on the sprung, swivelling paddle; duck: four strips on the chest)
| name | dock pins (paddle face; dock z, mm) | duck strip (100 mm wide, trunk z) | carries |
|---|---|---|---|
| CHG+ | 1, y 0, z 214.35 | 58.5 to 76 | charge current (1.1 A) through DK2 (Pololu 5382) and a 5 A fuse to the pack |
| SENSE | 1, y 0, z 194.85 | 39 to 56.5 | 10 k NTC in the cell seat to GND; the wake branch (3.9 V zener, diode, 10 k) to the 2813 ON pin |
| GND | 2, y +/- 3 mm, z 175.35 | 19.5 to 37 | charge and SYS return (about 2.1 A) |
| SYS | 2, y +/- 3 mm, z 155.85 | 0 to 17.5 | the gated 9 V: about 1.0 A typical, 1.8 A peak, through DK6 (Pololu 5382) to the 2813 input |
Window: fore-aft 0 to 40 mm into the paddle, lateral +/- 46.5 mm (single pins +/- 49.5), vertical +/- 8.25 mm, yaw +/- 10 deg.

## 3. Duck-side parts
Pad 100 x 76 x 0.8 mm FR4 ENIG on the flat chest face of body_front (no STL change; one 4 mm lead hole drilled after
printing); DK2, DK3/DK4 (5 A fuse), DK5 (NTC, wake parts, 100 k), DK6 (SYS diode), DK7 (Pololu 5383, pack side, between the
fuse and the 2813). Wiring: wiring/netlist.yaml (cables DC1 to DC4); seats: dock_seats.json. About 13 g with the leads.

## 4. What the battery job is asked for
1. The pack monitor reports charge current and the cell temperature to the Pi.
2. The NTC in the cell seat: 10 k, B 3950, lead to the chest pad.
