# Proposed 5 V regulator change

Not applied. BOM.md was not edited. The live netlist `altaay_lab/wiring/netlist.yaml` was not edited. Changing U3 in that file needs Ahmed.

The nest charger proposal lives in `altaay_lab/PROPOSED_BOM_CHANGES.md`. This file sits next to the Pi 5 study so the two notes do not overwrite each other.

Nothing here was bought. A number is cited, calc only, chart read, or BLOCKER.

## Pick

Pololu D36V50F5, item 4091. https://www.pololu.com/product/4091

| Item | Value | Label |
|---|---|---|
| Output | 5 V with 4% accuracy | cited, the page. 4% of 5.00 V is 4.80 to 5.20 V, the same domain the netlist already uses |
| Input | 5.5 V to 50 V | cited. Minimum input is also subject to dropout, below |
| Table current | 5.5 A typical maximum | cited, and the table says this point is at 36 V in, not at 12 V |
| Current across the pack | about 7.5 A to about 8.2 A | chart read of the maximum-continuous-output-current graph (picture 0J10751 on that page). The 5 V trace is about 7.5 A near 5 to 6 V in and peaks about 8.2 A near 12 V. From 9.0 V to 12.6 V the trace is on that rise, so it stays above 5 A. This is a reading of the picture, not a table cell |
| Dropout at 5 A | about 1.0 V to 1.1 V on the 5 V trace | chart read, dropout graph 0J10753. 5.0 V plus about 1.1 V is about 6.1 V, under the 9.0 V pack floor |
| Efficiency | 80% to 95% | cited, the page, depending on voltages and load |
| Size | 25.4 by 25.4 by 9.5 mm | cited. The live part is 17.8 by 20.3 by 9 mm. A seat for this larger board was not checked |
| Header pins | 3 A each, 6 A combined per pair | cited. Above that, the page says solder thick wires to the board |
| Price and stock | $44.95, 0 in stock, status Rationed, backorders allowed | cited, the page on the day this note was written |

The pack window 9.0 to 12.6 V (netlist PACK_9V0_12V6) is inside 5.5 to 50 V and above the chart-read dropout. The landed nest note (circuitry/NEST_TWO_NET.md) keeps U3 on that pack domain, at J5IN, and does not put the 15.0 V nest on the 5 V pin. This part's 5.5 V to 50 V input also covers 15.0 V, so a later nest tie would not need a different regulator. This proposal does not make that tie.

## 5 V load sum

The cooler fan plugs into the Pi fan header, so its current is inside the Pi's 5 A supply allocation. The fan's own amps are not printed on the cooler page: left out of the sum, not added a second time.

| Load | Current | Label |
|---|---|---|
| Pi 5 supply allocation | 5 A | cited, https://www.raspberrypi.com/products/raspberry-pi-5/ (5 V / 5 A DC, USB-C, Power Delivery). This is the supply the board asks for, not a measured board current |
| Pi 5 minimum band | 0.80 A to 1.00 A | calc only, 4 W to 5 W from RP-010139-WP table 1, divided by 5.00 V. Not used in the sum below |
| Active Cooler | inside the 5 A | cited, 5 V fan header. Separate fan current was not on the page |
| One SG90, running | 90 mA | cited, SG90 product specification at 4.8 V, stall row on the same sheet. https://pan.baud-dance.com/d/%E7%BD%91%E7%AB%99%E6%96%87%E4%BB%B6/%E8%B5%84%E6%96%99%E5%8C%85/static/%E8%88%B5%E6%9C%BASG90%E8%A7%84%E6%A0%BC%E4%B9%A6.pdf |
| One SG90, stall | 750 mA plus or minus 10% | cited, same sheet, at 4.8 V. Idle-current cell on that sheet is blank. That sheet also says 1.3 kg.cm and 10 g plus or minus 5%. A different SG90 PDF lists 1.8 kgf.cm and 9 g and prints no stall current, so this stall figure is the sheet that states one, and the two sheets do not agree |
| Two SG90, stall | 1.500 A, span 1.350 A to 1.650 A | calc only, two times the cited stall |
| Two SG90, running | 0.180 A | calc only |
| MAX98357A quiescent | 2.75 mA typical, 3.35 mA maximum | cited, MAX98357A/MAX98357B electrical characteristics at VDD 5 V, Ta 25 C. Speaker current is not in this number |
| Amp current into the 8 ohm speaker | not read | BLOCKER |

Sum using the Pi's 5 A allocation, two stalls at 750 mA, and the amp's 3.35 mA maximum, and leaving the speaker current out:

5.000 + 1.500 + 0.00335 = 6.503 A (calc only).

With the stall tolerance: 6.353 A to 6.653 A (calc only).

The same sum with running current instead of stall is 5.183 A (calc only).

6.653 A is under the chart-read floor of about 7.5 A across 9.0 to 12.6 V in, by about 0.8 A (chart read against calc only). It is over the 6 A combined rating of one header-pin pair, so the wires to VIN and VOUT should be soldered, which is what the Pololu page says for higher power. The speaker current is still missing, so the sum can move up when that number is read.

## Seat for this regulator

CAD check only. The part is 25.4 by 25.4 by 9.5 mm (cited, the Pololu page). With a 2.4 mm plate under it the keep-out is 11.9 by 25.4 by 25.4 mm, the thin side fore and aft. Origin in the print frame: x -30, y -16, z -84. That box clears the print shells by 4.5 mm (body_middle_bottom; the others are at least 8 mm) and clears the hip sweep by 6.21 mm (right hip yaw at -0.175 rad, bottom case). It sits in front of the Pi keep-out with more than 2 mm between the two boxes. The live netlist is not changed.

## Nest rail

circuitry/NEST_TWO_NET.md, now on altaay-lab, says a later 5 V 5 A regulator can replace U3 when its input accepts the pack window and its output stays on net 5V. It also says the 5 V seat ties U3.VIN to J5IN and drops the VSW feed, and that this does not put the nest on the 5 V pin. The Pi stays a pack-domain load.

This proposal is that replacement. VIN is J5IN, domain PACK_9V0_12V6. VOUT stays on net 5V. The 5 V load sum above is on the pack side, so it does not add to the nest dome current. The live netlist still names the D30V30F5 until Ahmed changes it.

## Netlist study variant

Proposed U3 block. Not copied into `wiring/netlist.yaml`. Pin names VIN, GND, VOUT, EN, and PG stay so the existing splices still name the same pins. VRP is new on this part and is left unconnected.

```yaml
  - id: U3
    ref: U3
    part: Pololu D36V50F5 5 V step-down regulator (item 4091)
    kind: regulator
    region: body seat
    ratings:
      v_out: "5 V, 4% (4.80 to 5.20 V)"
      v_in: "5.5 to 50 V, dropout on top of that"
      i_cont_a: "table 5.5 A at 36 V in; chart read about 7.5 A to about 8.2 A from 9.0 to 12.6 V in"
      size_mm: "25.4 x 25.4 x 9.5"
      header_pin_a: "3 A per pin, 6 A per pair; solder wires above that"
      price_usd: 44.95
      stock: "0, rationed, backorders allowed"
    pins:
      - {pin: "VIN", name: input from J5IN, domain: PACK_9V0_12V6}
      - {pin: "GND.1", name: ground, domain: GND}
      - {pin: "GND.2", name: ground, domain: GND}
      - {pin: "VOUT", name: 5 V out, domain: 5V}
      - {pin: "EN", name: enable, on by default}
      - {pin: "PG", name: power good, open drain}
      - {pin: "VRP", name: input after reverse protection, left open}
    source: "https://www.pololu.com/product/4091 ; proposed, not applied"
```
