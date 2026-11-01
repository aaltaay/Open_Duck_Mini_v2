# DECISIONS (open questions for Ahmed)

D1. Servo variant. Deep dive done (SERVO_DEEP_DIVE.md). Evidence says apirrone uses the STS3215 7.4 V 1:345 "19 kg.cm" (C001), confidence about 85%. His own BAM identification implies about 5.43 rad/s no load, which matches the C001 datasheet (52 RPM = 5.45 rad/s at 7.4 V), and the sim and policy were trained on that model. The earlier "about 2.7 rad/s" note was wrong; it came from issue #48, not from a datasheet. Issue #48 tracking looks like a servo setup, firmware or supply problem, not a gear ratio problem. Options: (a) buy C001 as written and bench test 1 or 2 first (recommended), (b) C046 or C044 for legs (not recommended: mismatches the trained policy), (c) also ask upstream the draft question in SERVO_DEEP_DIVE.md section 7 (not posted, needs your OK).

D2. Accept Feetech under the lab rule? Spec gives rated torque but no thermal duty curve. Warranty is 12 months, 6 months for motor, gears and housing, with round-trip freight paid by us and over-voltage excluded. A sim model exists (MJCF plus BAM). Accept, or require a duty test in the lab first?

D3. Supply voltage. A full 2S pack is 8.4 V, above the 6 to 7.4 V servo rating, and over-voltage voids the Feetech warranty (issue #51). Options: keep as designed, add a buck stage, or use the 12 V STS3215 C018 (redesign, not as-is).

D4. Generic Chinese power parts (BMS, UBEC, charger, holder) have no spec or warranty. Swap the UBEC for Pololu D36V28F5 (US, spec'd)? Swapping changes the as-is build.

D5. Lab-rule features not in the design (docking, get-up, stairs). Build v2 strictly as-is first and add these as a separate lab fork later, or add them before the first build?

D6. Runtime and Playground have no license. Ask upstream to add one before we modify or redistribute code from them? (No message sent; needs Ahmed approval.)

D7. Pi Zero 2 W is out of stock at US resellers (2026-11-01). Wait, pay eBay prices (about $82+), or test a different board (not as-is)?

## Decided
- 2026-11-01 12:51 PM ET (Ahmed): The Open Duck Mini v2 is EXEMPT from the lab 15-step stair rule (see GAPS.md B7). Self-docking and get-up after falls are not exempted.
- 2026-11-01 12:53 PM ET (Ahmed, answers D5): Build v2 stock first, exactly as designed. Add self-docking and get-up after falls later as a separate lab step.
