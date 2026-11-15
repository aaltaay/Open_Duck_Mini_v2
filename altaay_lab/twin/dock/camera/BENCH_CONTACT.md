# Bench check: gold on the nest foil

Nothing here was bought. Prices are the pages that were open. The sim now presses the well disks. This bench is still the measurement of the real foil, because the sim ohms are an assumption.

## What it answers

The dock model puts a 3 mm gold disk on each well and reads the MuJoCo force. The ohms in that score are a clean-gold figure times 5, not a curve for this foil. This bench presses a gold-plated pin onto the same kind of copper foil the nest BOM calls for, at a known force, and reads the voltage drop at the charge current.

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
