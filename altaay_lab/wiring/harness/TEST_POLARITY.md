# Continuity and polarity

Do `TEST_PLAN.md` section 2 first. That section is the meter method: ohms, not the beep, subtract the probe reading, under 1 ohm on a wire, over 1 Mohm between two different nets on one plug. This file adds the rows for the plugs named in `WIRES.md`. Power stays off. The battery XT30 stays open.

The Klein meter numbers in TEST_PLAN section 2 stay the ones cited there. They are not copied here as a new measurement.

## 1. Lever groups

1. Ground lever to switched plus lever: over 1 Mohm.
2. Servo plus lever to servo ground lever: over 1 Mohm.
3. Every red wire you meant for a plus lever reads through to the other reds in that same lever, under 1 ohm, and does not read through to any black lever.
4. The jumper between the big servo lever and the small servo lever reads under 1 ohm. Plus jumper must not read to the ground jumper.

## 2. XT30

1. Pack socket plus cup to the pad B+: under 1 ohm.
2. Pack socket minus cup to the pad B-: under 1 ohm.
3. Plus cup to minus cup: over 1 Mohm.
4. Neck XT30 on cable P13: the body half plus reads to the switched plus lever, the head half plus reads to the regulator pad printed VIN. They read to each other only when the XT30 is mated. Unplug it and they must not read through.

The XT30 amp rating is still the [I] note on BOM line 12. This test does not clear that. BLOCKER for a cited continuous rating.

## 3. Servo plugs

1. On a power plug, with the latch up, the black hole reads to the servo ground lever. The red hole reads to the servo plus lever. The yellow hole, if it has a wire, reads to the adapter data pin and not to plus.
2. Adapter data plugs: middle hole empty. No wire, no reading.
3. SP4 and SP5: signal hole empty. Red and black only.
4. A kit hop: unplug one end. Each conductor reads end to end, under 1 ohm, and the three conductors do not read to each other.
5. Kit cable gauge is not published. BLOCKER. The plug test above does not need the gauge.

Match the hole order to a kit cable before you call the polarity good. The Feetech order is pin 1 ground, pin 2 plus, pin 3 signal. The card in step 8 does not measure which side of the shell is pin 1.

## 4. Pi plugs

1. 5-pin plug, housing 0022012057. Empty hole sits on pin 7. If it sits on another pin, the plug is backwards. Remove it and turn it.
2. Pin 1 red reads to the BNO055 pad printed VIN.
3. Pin 3 blue reads to the pad printed SDA.
4. Pin 5 yellow reads to the pad printed SCL.
5. Pin 9 black reads to the pad printed GND.
6. Pin 1 must not read to pin 9.
7. Eye plug: pin 16 white is the right eye, pin 18 yellow is the left eye, pin 20 black is ground. White must not read to yellow.
8. Soldered thick wires: pin 2 red reads to the regulator pad printed VOUT. Pin 6 black reads to the regulator ground pad. Pin 4 red reads to the head 5 V splice. Pin 14 black reads to the head ground splice.
9. Feet: pin 15 green is the left foot, pin 13 white is the right foot. Green must not read to white. Both foot commons read to pin 9.
10. Charger 2-pin plug: blue is pin 29, green is pin 31. Blue reads to charger pad JPI.STAT. Green reads to pad JPI.EN. They must not read to each other.

26 AWG insulation versus the 1.57 mm maximum is still BLOCKER, as `WIRES.md` says. If you soldered an end because the wire was fat, test that soldered end the same way.

## 5. Bought cables

1. USB lead: it only enters the Pi socket marked USB, and the adapter end only enters the adapter. No ohm check through the data pairs. The plugs are the key.
2. Camera ribbon: do not probe the contacts with the ohms leads. Which face goes down is BLOCKER until the sheet in the bag is read.

## 6. Do not test as if they were connected

The five seat wells have no far plug. Do not expect a reading from a well to the pack. If a well reads to the pack, stop. That wire should not be tied yet.

## 7. Polarity list, short

| Plug | Plus or signal | Ground | Must not |
|---|---|---|---|
| XT30 | red cup | black cup | red reading to black |
| Servo power | red, pin 2 | black, pin 1 | red reading to black |
| Servo data | yellow | black | yellow reading to red |
| 5-pin Pi | red on pin 1 | black on pin 9 | empty hole off pin 7 |
| Eye | white pin 16, yellow pin 18 | black pin 20 | white reading to yellow |
| Charger | blue pin 29, green pin 31 | joins the 5-pin black | blue reading to green |
| Levers | red group | black group | red group reading to black group |
