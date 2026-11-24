# In-duck nest charger

The pack on the netlist is 3S. It charges to 12.6 V (cited, Molicel P45B version 1.2, 4.2 V per cell, times 3). The MCP73213-A6S regulates at 8.40 V (cited, DS20002190C Table 2). 8.40 V cannot finish this pack, so that chip stays the 2S record in CHARGER_BOARD.md. The charger in the duck is the TI BQ24133 with CELL tied to VREF, which the same sheet lists as 12.6 V on SRN (cited, SLUSAF7D).

D61 is not edited. Awake while docked is kept. Torque off is the sit. The servo rail stays on.

`python3 altaay_lab/circuitry/check_nest_charge.py` checks the numbers below. `python3 altaay_lab/circuitry/nest_erc.py` runs that and audit/erc.py.

## Two nets

The mat is nest_v2: 20 mm foil, 5 mm felt, sun 190 mm from the wall. The duck touches it with five gold domes, 1.5 mm radius, 0.9 mm proud of the seat (the contact that charged in 38 of 40 camera docks, sim pass only, SEAT_CONTACTS.md). A dome can land on either stripe.

Each dome has two onsemi MBRS540T3G Schottky diodes (cited, MBRS540T3/D Rev. 13: 40 V, 5 A average, 0.50 V max at 5 A and 25 C). One anode is the dome and the cathode is the nest plus, so a dome on a plus stripe feeds the duck. One anode is ground and the cathode is the dome, so a dome on a minus stripe is the return. Ten diodes. The mat still has only two conductors, plus and minus.

After the five plus cathodes, a 5 A fuse (the existing F2, Littelfuse 0287005.PXCN) feeds two branches. One is the BQ24133 input, before that board's adapter sense resistor, so the charger measures only the pack. The other is DK6, the ideal diode that ORs the nest with the pack at the 2815. The i7C holds the servos at 12.0 V from either source (cited input 9 V to 36 V). The 5 V regulator sits on that same node. A later 5 A part for a Pi 5 can replace it without moving the nest. The present D30V30F5 graph is about 3.8 A, not 5 A. A 5 A output is pull request 111. This note does not change that regulator. The nest wire is already sized for the input current.

## What the duck draws while docked and awake

Calc only. One dome may carry a whole pole.

| Path | Current at 15.0 V |
|---|---|
| Charge, 12.6 V at 1.006 A, efficiency 0.929 (chart read, BQ24133_HEAT.md Figure 10-4) | 0.910 A |
| Fourteen servos at the 21 mA idle, 12.0 V, i7C at 0.94 | 0.250 A |
| A 5 V, 5 A branch at 0.94 | 1.773 A |
| Total | 2.933 A |

2.933 A is under the 5 A diode and under the 5 A fuse. Two diodes at the 0.50 V max drop 1.00 V, so the chip still sees 14.00 V, which is over the 13.6 V floor (12.6 plus the 1.0 V the EVM note asks for, cited in NEST3.md). The 0.50 V figure is the 5 A maximum, so the drop at 2.933 A is smaller. That smaller drop was not read off the curve. The 1.00 V is the bound.

The diode's minimum pad is 111 C/W and would put this bound over 150 C. The board uses the sheet's 700 mm2, 2 ounce pad, 64 C/W. The bound is then a 93.9 C rise, 133.9 C if the trunk air is 40 C, under the 150 C junction limit (calc only).

## Protection

- Reverse polarity. A stripe that is minus does not feed the charger plus. The return diode blocks a plus dome from shorting to ground. A reversed adapter only swaps the stripes, and the same diodes still sort them.
- ESD on the domes. One Littelfuse SMAJ16A per dome, cathode on the dome, anode on ground. Standoff 16.0 V, so 15.0 V does not conduct. Clamp 26.0 V at 15.4 A (cited, NEST3.md). The SMAJ series response is typically under 1.0 ps from 0 V to breakdown for a unidirectional part (cited, Littelfuse SMAJ page). IEC 61000-4-2 is 30 kV contact and 30 kV air (cited, CHARGER_BOARD.md, from the series table).
- The charger pin does not sit on that clamp. A TI TPS259470ARPW eFuse (cited, SLVSFC9C) is between the clamp and the BQ24133. Its IN absolute maximum is 28 V, so 26.0 V is inside that rating. Its OUT is the charger input and the awake feed.
- OVLO uses 140 kOhm over 10.0 kOhm. The rising threshold is 1.183 V to 1.223 V, typical 1.20 V (cited). The trip is 18.00 V typical and 18.345 V at the high threshold (calc only). Both are under the 20 V PVCC absolute maximum. The low trip is 17.745 V, above the 16.0 V standoff, so a nest inside the window does not trip. The sheet's OVLO response is 1.2 us typical. That is the disconnect in front of the charger. The charger's own 1 us deglitch is no longer what stands between PVCC and the 26 V clamp.
- Current limit is the cited 750 ohm row: 3.96 A minimum, 4.452 A typical, 4.84 A maximum. 2.933 A is under 3.96 A.
- Short on the mat. A second 0287005.PXCN sits in the cord pocket, in series with the adapter, ahead of the stripes. A coin across a 5 mm gap opens that fuse. The duck fuse is the second opening, after the diodes.

## What stays open

- Contact resistance of gold on foil, with dust. BLOCKER.
- Felt grade, and whether the 0.9 mm dome dents the top sheet. BLOCKER.
- The 5 V regulator versus a 5 A Pi. That supply is pull request 111. This charger does not change it.
- The signature that would keep the mat dark until the duck sits. The pocket fuse opens a short. It does not keep the stripes dark. BLOCKER.
- In-trunk theta of the BQ24133 is not the 35.7 C/W JEDEC number. The thermal run is twin/thermal/NEST_HEAT.md.
