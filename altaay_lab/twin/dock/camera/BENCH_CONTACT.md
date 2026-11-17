# Bench check: stainless on the nest foil

Nothing here was bought. Prices are the pages that were open. The belly sim presses two 304 plates, 6.0 mm by 2.2 mm, flush with the seat face. The ohms in that score are still the gold-dust assumption from CAMERA_DOCK.md, so this bench is the measurement for steel on the real foil. The earlier gold-pin bench is kept below. It is not this pair.

## What it answers

The dock model reads the MuJoCo force on each plate. A charge needs at least 0.294 N (30 g) on both poles. The lowest pole on a charging sit in the 40 docks was 0.77 N (sim pass only, seed 30). This bench presses a 304 coupon, the same size as one plate, onto the copper foil the nest BOM calls for, and reads the voltage drop at the charge current.

No force-versus-resistance curve for 304 on this foil was found. The sim does not pretend to have one.

## Parts, not ordered

| Part | Role | Price |
|---|---|---|
| 3M 1181 X 1/2 copper foil tape, DigiKey 111515 | The stripe. One short piece is enough. | 65.80 USD at quantity 1, the DigiKey listing shown 2026-11-15 |
| 304 sheet coupon, 6.0 mm by 2.2 mm by 0.5 mm | Stand-in for one belly plate. Not a bought contact. | A sheet price was not opened. BLOCKER. Cut from scrap if the lab already has 304. |
| Six US nickels, then twenty | 30 g, then 100 g. A nickel is 5.000 g (US Mint specification). | Already in a pocket. Not a purchase. |

100 g is 0.981 N (calc only, 0.100 kg times 9.80665). That is above the 0.77 N low pole. 30 g is the 0.294 N floor. A bench supply that can hold 1.006 A, and a meter on the contact itself (four wires, so the leads are not in the reading), are assumed to be in the lab. They are not priced here.

## Procedure

1. Stick about 40 mm of the 1181 tape on a flat non-metal board. Burnish it. This is the stripe.
2. Set the 304 coupon flat on the foil. Add six nickels on a small non-metal cap so the coupon sees 30 g (0.294 N). Do not let the coins touch the foil.
3. Drive 1.006 A through the coupon and the foil. Read the voltage on a second pair of wires landed on the coupon and on the foil, next to the contact, not at the supply clips.
4. Repeat with twenty nickels (100 g, 0.981 N).
5. Wipe the foil with a scrap of the nest felt so a little lint stays on it. Repeat the 100 g reading. That ratio is the dust factor. The sim assumed 5 times, on a gold figure, and this step is what replaces the assumption for steel.

## Pass

One contact passes when the drop at 1.006 A is under 0.10 V (under 0.099 ohm) at both 30 g and 100 g. Two such contacts plus the 0.038 ohm of both 22 AWG poles (NEST_V2.md, calc only) and the 0.0277 V of the ideal-diode bridge (BELLY_CONTACT.md, calc only) leave the BQ24133 inside the 4.5 V to 17 V window from the 15.0 V nest (calc only). A reading over 0.10 V at 30 g, or an open, is a fail. The felt-lint ratio is recorded either way.

This does not close the dust blocker. It is the number the blocker is asking for. It does not wear the coupon for 3,650 docks. Wear life stays BLOCKER.

## Earlier bench: gold pin on the foil

The sim that this replaced, for the record, pressed 0.9 mm gold domes. The procedure below is that pair. It is not the belly plate.

# Bench check: gold on the nest foil

Nothing here was bought. Prices are the pages that were open. The ohms in that score are still an assumption, so this bench is still the measurement of the real foil for a gold pin, not for the 304 plate.

## What it answers

The dock model stands a 1.5 mm gold dome 0.9 mm proud of the seat face and reads the MuJoCo force. The ohms in that score are a clean-gold figure times 5, not a curve for this foil. This bench presses a gold-plated pin onto the same kind of copper foil the nest BOM calls for, at a known force, and reads the voltage drop at the charge current.

The pair in the nest is gold on copper foil. No force-versus-resistance curve for that pair was found. The sim uses a clean-gold figure instead, and says so. This bench replaces that assumption for the real foil.

## Parts, not ordered

| Part | Role | Price |
|---|---|---|
| 3M 1181 X 1/2 copper foil tape, DigiKey 111515 | The stripe. One short piece is enough. | 65.80 USD at quantity 1, the DigiKey listing shown 2026-11-15 |
| Mill-Max 0906-0-15-20-76-14-11-0 | Gold over nickel spring pin, stand-in for the 3 mm well. Not the well. | 0.86 USD at quantity 1, DigiKey page opened 2026-11-12 (BOM.md) |
| Six US nickels, then twenty | 30 g, then 100 g. A nickel is 5.000 g (US Mint specification). | Already in a pocket. Not a purchase. |

A bench supply that can hold 1.006 A, and a meter on the contact itself (four wires, so the leads are not in the reading), are assumed to be in the lab. They are not priced here.

## Procedure

1. Stick about 40 mm of the 1181 tape on a flat non-metal board. Burnish it. This is the stripe.
2. Set the Mill-Max pin on the foil, tip down. Add six nickels on a small cap so the pin sees 30 g (0.294 N). Do not let the coins touch the foil.
3. Drive 1.006 A through the pin and the foil. Read the voltage on a second pair of wires landed on the pin body and on the foil, next to the contact, not at the supply clips.
4. Repeat with twenty nickels (100 g, 0.981 N).
5. Wipe the foil with a scrap of the nest felt so a little lint stays on it. Repeat the 100 g reading. That ratio is the dust factor. The sim assumed 5 times, and this step is what replaces the assumption.

## Pass

One contact passes when the drop at 1.006 A is under 0.10 V (under 0.099 ohm) at both 30 g and 100 g. Two such contacts plus the 0.038 ohm of both 22 AWG poles (NEST_V2.md, calc only) drop under 0.24 V. From the 15.0 V nest supply that leaves 14.76 V at the BQ24133, inside the 4.5 V to 17 V window (parts.yaml, the chip sheet). Heat in the two contacts is then under 0.20 W (calc only, I squared R).

A reading over 0.10 V at 30 g, or an open, is a fail. The felt-lint ratio is recorded either way. It is not a pass by itself.

This does not close the dust blocker. It is the number the blocker is asking for.
