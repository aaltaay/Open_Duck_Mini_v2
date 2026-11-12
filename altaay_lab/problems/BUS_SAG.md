# Bus sag on the sheet-stall walk

Sim pass only for every walk. Copper ohms are calc only from the annealed-copper table in sim/power_path_sim.py and the lengths named below. The cell lines are cited. Nothing was bought. No new gait. The electromechanical twin was called, not rewritten.

Run: `python3 altaay_lab/problems/bus_sag.py`

Every walk is the backlash model, command 0.15 m/s, sheet servo, P45B pack, 20 s budget. Knee volts are the lowest sample in the twin's V_min bins, up to the fall.

## As built

| Corner | Fall | Left knee | Right knee |
|---|---|---|---|
| typical | 3.56 s | 5.785 V | 5.889 V |
| high-side | 3.42 s | 5.269 V | 5.244 V |

A flat 7.4 V on every servo, from the earlier stall run, does not fall in 20 s (sim pass only, problems/STALL.md). These walks are on the as-built bus.

One conductor from the splice to the knee, with no parallel feed, is 0.096 ohm on the typical corner (24 AWG hops, 5 milliohm contacts) and 0.224 ohm on the high-side corner (26 AWG hops, 20 milliohm contacts). The SP4 and SP5 copper, 22 AWG at the netlist cuts of 420 mm and 450 mm, is 0.022 ohm and 0.024 ohm. The feed is the small resistor. The chain is the large one.

## Each change

22 AWG is the thickest gauge the harness note's Mini-SPOX terminal takes (22 to 28 AWG, cited there). The kit hops are 24 AWG on the typical corner and 26 AWG on the high-side corner. The 16 AWG feed keeps a 50 mm 22 AWG tail so that terminal still fits. 16 AWG is already the gauge of P11. The route-worst lengths, 348 mm and 377 mm, are the numbers already written on the SP4 and SP5 wire lines, before the slack those lines add. The knee star uses the 420 mm knee-injection length already in sim/power_fix.py and lands that feed on the knee instead of the ankle. The 470 uF is the per-servo figure assumed in twin/electrical/ELECTRICAL_TWIN.md. Its ESR is 0 in this run, which is the bound that helps the capacitor most.

| Change | Typical fall | Typical knee dips | High-side fall | High-side knee dips |
|---|---|---|---|---|
| Hops to 22 AWG | 3.52 s | 5.758 V, 5.811 V | 3.46 s | 5.091 V, 5.200 V |
| Feeds cut down to the route worst | 3.54 s | 5.706 V, 5.817 V | 3.46 s | 5.096 V, 5.285 V |
| 16 AWG feed, 22 AWG tail | 3.58 s | 5.977 V, 6.002 V | 3.46 s | 5.218 V, 5.344 V |
| Star feed to the knee | 3.56 s | 5.901 V, 5.980 V | 3.46 s | 5.339 V, 5.432 V |
| 470 uF at each knee, ESR 0 | 3.54 s | 5.871 V, 5.857 V | 3.40 s | 5.362 V, 5.552 V |
| Cell pulses at the cited 7 mOhm AC | 3.54 s | 6.041 V, 6.036 V | 3.44 s | 5.227 V, 5.393 V |
| All of the wire changes together | 3.56 s | 6.093 V, 6.087 V | 3.50 s | 5.395 V, 5.477 V |

No row walks 20 s. The largest dip move is the stacked wire change: typical knees 6.09 V against 5.79 V as built, high-side 5.40 V and 5.48 V against 5.27 V and 5.24 V. The fall stays at 3.5 s. There is no smallest change in this set that walks 20 s on both corners, because none of them do.

The capacitor time constant at 0.5 ohm is 0.235 ms (calc only, 470 uF times 0.5 ohm). A control step is 20 ms. The capacitor is finished long before the knee sag. The walk times match the as-built fall.

## Pack sag, fresh cell

The digitized discharge figure, calc only. Pack sag is twice the cell sag. Open circuit at 0 mAh on that figure is 4.175 V per cell.

| Where | Pack current | Pack sag |
|---|---|---|
| Full | 2 A | 0.073 V |
| Full | 5 A | 0.177 V |
| Full | 10 A | 0.302 V |
| Open circuit 3.30 V per cell (3861 mAh on the figure) | 2 A | 0.070 V |
| Same | 5 A | 0.168 V |
| Same | 10 A | 0.273 V |

The sheet's DC pulse is 15 milliohm at 50 percent SOC (cited). Two cells at 5 A are 0.150 V. The figure at 5 A is 0.177 V full and 0.168 V at 3.30 V per cell. The AC line is 7 milliohm at 30 percent SOC (cited). That lower resistance was run above, and the walk still falls.

A walk that starts at that 3.30 V open circuit, same sheet servo and the as-built bus: fall at 2.98 s typical and 2.96 s high-side (sim pass only). Knee dips 4.725 V and 4.629 V typical, 4.347 V and 4.207 V high-side. Pack terminal mean 6.445 V and 6.446 V at about 4.9 A. Open circuit of the pack is 6.60 V, so the sag in that run is 0.155 V (calc only, 6.60 minus 6.445).

## Worn cells

The electromechanical twin already cites about 93 percent capacity after 300 cycles at 1 C. That sentence has no resistance. The digitized figure has no worn curve. A worn internal resistance is BLOCKER. It was not invented here. A higher resistance than the fresh figure would sag more, and the fresh figure already falls.
