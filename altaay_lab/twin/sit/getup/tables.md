| pose class (rest poses) | V | floor mu | base d6179ae | sit 758f297 |
|---|---|---|---|---|
| back (39) | 7.2 | 1.0 | 39 of 39 | 0 of 39 |
| back (39) | 7.2 | 0.6 | 39 of 39 | 0 of 39 |
| back (39) | 6 | 1.0 | 35 of 39 | 0 of 39 |
| back (39) | 6 | 0.6 | 39 of 39 | 0 of 39 |
| side (17) | 7.2 | 1.0 | 17 of 17 | 0 of 17 |
| side (17) | 7.2 | 0.6 | 17 of 17 | 0 of 17 |
| side (17) | 6 | 1.0 | 16 of 17 | 0 of 17 |
| side (17) | 6 | 0.6 | 17 of 17 | 0 of 17 |
| front (18) | 7.2 | 1.0 | 11 of 18 | 0 of 18 |
| front (18) | 7.2 | 0.6 | 8 of 18 | 0 of 18 |
| front (18) | 6 | 1.0 | 5 of 18 | 0 of 18 |
| front (18) | 6 | 0.6 | 11 of 18 | 0 of 18 |
| **all** | both | both | **254 of 296** | **0 of 296** |

| class, terrain (rest poses) | 7.2 V, mu 1.0 | 7.2 V, mu 0.6 | 6.0 V, mu 1.0 | 6.0 V, mu 0.6 |
|---|---|---|---|---|
| back, flat (12) | 12 -> 0 of 12 | 12 -> 0 of 12 | 12 -> 0 of 12 | 12 -> 0 of 12 |
| back, obstacles (12) | 12 -> 0 of 12 | 12 -> 0 of 12 | 11 -> 0 of 12 | 12 -> 0 of 12 |
| back, ramps up (15) | 15 -> 0 of 15 | 15 -> 0 of 15 | 12 -> 0 of 15 | 15 -> 0 of 15 |
| side, flat (10) | 10 -> 0 of 10 | 10 -> 0 of 10 | 9 -> 0 of 10 | 10 -> 0 of 10 |
| side, obstacles (4) | 4 -> 0 of 4 | 4 -> 0 of 4 | 4 -> 0 of 4 | 4 -> 0 of 4 |
| side, ramps up (3) | 3 -> 0 of 3 | 3 -> 0 of 3 | 3 -> 0 of 3 | 3 -> 0 of 3 |
| front, flat (6) | 6 -> 0 of 6 | 6 -> 0 of 6 | 5 -> 0 of 6 | 6 -> 0 of 6 |
| front, ramps down (12) | 5 -> 0 of 12 | 2 -> 0 of 12 | 0 -> 0 of 12 | 5 -> 0 of 12 |

| set | what changes | back | side | front | all | cases |
|---|---|---|---|---|---|---|
| base_sts3250_high | base model (d6179ae), STS3250 knees | 152 of 156 | 67 of 68 | 35 of 72 | 254 of 296 | all 296 |
| base_sitmass_sts3250_high | base + the sit masses (+39.1 g): mass alone | 156 of 156 | 68 of 68 | 33 of 72 | 257 of 296 | all 296 |
| base_cad_sts3250_high | base + its own CAD contacts as software limits (3 deg inside) | 0 of 156 | 0 of 68 | 0 of 72 | 0 of 296 | all 296 |
| sit_noclamp+nhfree_sts3250_high | sit, no software clamp, neck and head stops at the base ranges | 155 of 156 | 68 of 68 | 35 of 72 | 258 of 296 | all 296 |
| sit_noclamp_sts3250_high | sit, no software clamp (designed stops only) | 0 of 156 | 0 of 68 | 0 of 72 | 0 of 296 | all 296 |
| sit+nhfree_sts3250_high | sit, software clamp, neck and head stops at the base ranges (CAD clamps only) | 0 of 156 | 0 of 68 | 0 of 72 | 0 of 296 | all 296 |
| sit_clamp-ankle+nhfree_sts3250_high | as above, ankle clamp only | 0 of 156 | 0 of 68 | 0 of 72 | 0 of 296 | all 296 |
| sit_clamp-knee+nhfree_sts3250_high | as above, knee clamp only | 0 of 100 | 0 of 44 | 0 of 30 | 0 of 174 | 174 (subset, see text) |
| sit_clamp-yaw+nhfree_sts3250_high | as above, head yaw clamp only | 84 of 84 | 36 of 36 | 18 of 39 | 138 of 159 | 159 (subset, see text) |
| sit_clamp-hip+nhfree_sts3250_high | as above, hip clamps only | 37 of 38 | 20 of 20 | 9 of 18 | 66 of 76 | our build's 38 rests, mu 1.0, both V |
| sit_noclamp+nhfree+noparts_sts3250_high | sit, no clamp, neck and head free, seat and bumper collision off | 4 of 4 | 0 of 0 | 35 of 72 | 39 of 76 | the 72 front cases + 4 |
| sit_sts3250_high | **sit PR model as built (all of it)** | 0 of 156 | 0 of 68 | 0 of 72 | 0 of 296 | all 296 |
| gym_ours_c001 | the shared lab gym (overlay gym/overlays/duck) 'ours' model (2.6528 kg), C001 knees: the GETUP.md reference | 76 of 76 | 40 of 40 | 18 of 36 | 134 of 152 | our build's 38 rests, mu 1.0 and 0.6, both V |
| sit_c001 | sit PR model, C001 knees | 0 of 38 | 0 of 20 | 0 of 18 | 0 of 76 | our build's 38 rests, mu 1.0, both V |
