# 2026-11-11 11:13 PM ET: contact twin for the nest pins, the cloth, and the felt

Labels: cited (catalog and material sheets opened for this entry), calc only, sim pass only and CAD check only where the nest and sit files already said so. No hardware. The nest sims were not re-run.

- New folder twin/contact/. CONTACT_TWIN.md, ct_model.py, test_ct_model.py, results.json. The nest folder, the checklist, the decisions, the bill, and TEST_PLAN.md were not edited. Proposed bench rows sit in the report, section 7.
- Spring S from the QA Technology 100-40 catalog: 0.85 N at the 3 mm seat stroke, 1.07 N at the plane-sit bumper stroke (4.55 mm). The sit's 27.5 N is mostly on the soles (22.85 N, sim pass only). The four pins carry 3.85 N. The seat block still has 0.85 N on the felt, so these springs do not lift it.
- Working loop, calc only, cloth at the Laird 3035-535 ceiling of 0.07 ohm per square and the probe's 20 mOhm: 0.050 ohm with all four pins (0.050 V and 0.050 W at 1.0 A, 0.39 W at 2.8 A). One pin missing still charges. Both pins of one pole, or any three, open the charge. A clean metal spot stays near 3 mOhm across this force range. Cloth life, felt grade, the dent depth, and the sole friction are BLOCKER.
- Air does not hold an arc at 8.40 V or at about 9.5 V. The minimum on the Paschen page that was opened is 327 V. Hot-plug energy is BLOCKER (capacitance not opened). The supply is still meant to be off until the duck is recognised.
- Checks: the contact unit tests pass, and c9_docs.py reports PASS with no new failure.
