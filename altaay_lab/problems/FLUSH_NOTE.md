# The charger note still names the spring pins

The charger file was not edited. No new board is drawn here. This is a reading of two files that are already merged.

circuitry/CHARGER_BOARD.md (PR 40) still says the four spring pins, the gold disc, and the pale gold ring stay as drawn in twin/dock/nest/. The wire list in that file says four spring pins under the body, two in the seat block and two in the belly bumper. circuitry/charger_board.yaml says the four spring pins are off this board. circuitry/charger_board.kicad_sch says the same.

twin/dock/flush/FLUSH_CONTACTS.md (PR 41) is already the flush-contact version. It puts five wells in the seat, on stripes, with the Mill-Max 0906 in the mat, and it says the merged charger board is the pack charger, not the per-pin mat switch. The bumper is not a contact in that study, because it hangs 2.9 mm up.

The sentences the charger file's owner would change, using only that flush study, are the ones that name the spring pins, the disc, and the ring. The chip, the 8.40 V, the 1.00 A program, and the 6 hour timer do not depend on which contact feeds the two splices. The mat switch is still not this chip, which the flush study already says.

The 0.80 ohm round-trip budget in the charger note is for the spring-pin path. The flush study's clean-lab pin figure is 20 milliohm, and dirt on that contact is BLOCKER in that study. This note does not replace the 0.80 ohm.

Nothing here is a new contact, a new diode network, or a new seat for the board. The seat and the board mass stay BLOCKER, as CHARGER_BOARD.md already has them.
