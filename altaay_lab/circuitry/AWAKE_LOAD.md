# Awake loads while the servo rail is off

2026-11-13 ET. Calc only for the currents. The sit with the rail off is twin/sit/RAIL_OFF_SIT.md. Nothing was bought.

## Where those loads are wired

The netlist puts the 5 V regulator and the BEC on the same switched node. Cable P9 is SW1.VOUT to the splice VSW. Cable P10 is VSW to the BEC input. Cable P13 is VSW to U3.VIN, the Pololu D30V30F5. U3 feeds the Pi, the camera, the two SG90s, and the amplifier (POWER.md section 7).

The rail cut in SERVO_RAIL.md holds that switch off. As the netlist is drawn, the Pi and the camera go off with the servos. They do not keep drawing from the pack. The charge sense then does not see them, and the 0.10 A termination is not blocked by them.

The netlist calls SW1 a Pololu 2813 and describes its ON pin as a pulse. SERVO_RAIL.md read the level behavior on the 2815 page. Whether holding ON low keeps a 2813 off was not re-read on the 2813 page. BLOCKER for that pin.

## If the duck stays awake from the pack

D50 keeps the duck running while it charges. If that current comes out of the pack, it is the same problem the servos had.

The Raspberry Pi documentation, as already cited in the thermal twin, gives the Zero 2 W as 350 mA typical, bare-board, active. That is 1.75 W at 5 V (calc only, 0.350 x 5). The D30V30F5 graph is cited as 94 to 97 percent. It was not read again at 12.6 V in and 5 V out, so the efficiency at that point is BLOCKER, and the range is what this note uses.

| Load | At the pack | Against 0.10 A |
|---|---|---|
| Pi, 1.75 W, 97 percent, 12.6 V | 0.143 A | above |
| Pi, 1.75 W, 94 percent, 10.8 V | 0.172 A | above |
| The lab's 3 W typical for the whole 5 V branch, 97 percent, 12.6 V | 0.245 A | above |

0.143 A does not fall through 0.10 A. Current termination does not happen. The camera, the SG90 idle, and the amplifier were not given new sheet numbers here. They are part of the 3 W typical, and they add to the Pi, they do not subtract. The 3.3 V parts (about 45 mA typical in POWER.md section 10) sit on the Pi's 3.3 V pin, so they are on top of the bare-board 350 mA. One line in that table, the BNO055 12.3 mA, was marked as not re-read. It is not needed. The Pi typical is already over 0.10 A.

`python3 altaay_lab/circuitry/check_awake_load.py` checks the arithmetic.

## The fix

Feed U3 from the nest, on the adapter side of the charger, and leave the BEC on the switch that stays off while docked. The charge sense is the battery current. The Pi current does not go through it.

The D30V30F5 input range recorded in the netlist, from the Pololu page, is 5 V to 45 V. The 15.0 V nest sits inside that range. At 94 percent, 1.75 W from 15.0 V is 0.124 A on the nest (calc only). The charge is 1.006 A and the input limit is 1.983 A (calc only, the BQ24133 dividers). 1.006 + 0.124 is 1.130 A, under 1.983 A.

When the duck gets up, the Pi is already on, because the nest has been running it. It writes the sit commands first. It then raises end-charge, which releases the hardware clamp and pulls ISET below 40 mV so the charger disables, and then raises the rail request. The switch input is the pack through DK7 only. DK6 does not join it, so the 15.0 V nest cannot reach the servos while the duck is still seated. The stand ramp runs after the rail is up. While end-charge is low, dock detect forces the rail off even if the rail request is high. The truth table is in circuitry/SERVO_RAIL.md.

When the nest contact opens, the pack has to pick up U3 through a diode so the 5 V rail does not drop, the same OR D50 used, and only for this branch. The protection board's own draw from the pack was not the number copied from the 3S board page. BLOCKER for that leftover, and it has to be under 0.10 A once the 5 V branch is off the pack.
