# DECISIONS (open questions for Ahmed)

D1. Servo variant. BOM text "7.4V 19kg.cm" means STS3215 C001 (1:345, about 2.7 rad/s no load). Upstream issue #48 (open) reports only 31 to 49% joint tracking with this variant and asks whether C044 (1:191) or C046 (1:147) was used. Options: (a) C001 as written, (b) C046 for legs, (c) ask upstream first. Recommendation: (c), then buy one of each for a bench test.

D2. Accept Feetech under the lab rule? Spec gives rated torque but no thermal duty curve. Warranty is 12 months, 6 months for motor, gears and housing, with round-trip freight paid by us and over-voltage excluded. A sim model exists (MJCF plus BAM). Accept, or require a duty test in the lab first?

D3. Supply voltage. A full 2S pack is 8.4 V, above the 6 to 7.4 V servo rating, and over-voltage voids the Feetech warranty (issue #51). Options: keep as designed, add a buck stage, or use the 12 V STS3215 C018 (redesign, not as-is).

D4. Generic Chinese power parts (BMS, UBEC, charger, holder) have no spec or warranty. Swap the UBEC for Pololu D36V28F5 (US, spec'd)? Swapping changes the as-is build.

D5. Lab-rule features not in the design (docking, get-up, stairs). Build v2 strictly as-is first and add these as a separate lab fork later, or add them before the first build?

D6. Runtime and Playground have no license. Ask upstream to add one before we modify or redistribute code from them? (No message sent; needs Ahmed approval.)

D7. Pi Zero 2 W is out of stock at US resellers (2026-11-01). Wait, pay eBay prices (about $82+), or test a different board (not as-is)?

## Decided
- 2026-11-01 12:51 PM ET (Ahmed): The Open Duck Mini v2 is EXEMPT from the lab 15-step stair rule (see GAPS.md B7). Self-docking and get-up after falls are not exempted.
