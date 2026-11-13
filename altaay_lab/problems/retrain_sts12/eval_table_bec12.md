Sim pass only. 60 s sheet walk, 12 V STS3215, 3S P45B, BEC set point 12.0 V, 70 g cell, both corners, run C policy. CPU only. MuJoCo 3.3.4. No retrain. The 16 V table stays in eval_table.md. That set point is superseded. Every number in the table is sim pass only.

The pack sags under 12.3 V while walking, so the 12.0 V set point is in dropout for the loaded steps (the 0.3 V dropout is an assumption, BLOCKER). That is why these rows sit close to the 16 V table: both runs follow the pack once the input is under the set point.

| Cmd m/s | Corner | Fall | Body speed m/s | Flight phase (frac) | Double support frac | Action rate | Joint jerk RMS rad/s3 | Pitch RMS deg | Roll RMS deg | Knee min V L / R | Pack peak A | Pack 100 ms peak A | BEC out min V |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.1 | typical | none in 60 s | -0.0 | no (0.0) | 1.0 | 0.00238 | 48.6 | 0.331 | 0.477 | 10.936 / 10.955 | 8.956 | 5.96 | 11.15 |
| 0.1 | high-side | none in 60 s | -0.0 | no (0.0) | 1.0 | 0.0024 | 48.5 | 0.324 | 0.474 | 10.631 / 10.673 | 8.903 | 5.91 | 10.977 |
| 0.15 | typical | none in 60 s | 0.1075 | no (0.0) | 0.4643 | 0.14776 | 613.2 | 0.559 | 3.486 | 10.837 / 10.953 | 8.956 | 6.337 | 11.123 |
| 0.15 | high-side | none in 60 s | 0.1044 | no (0.0) | 0.4786 | 0.153 | 602.6 | 0.567 | 3.467 | 10.49 / 10.52 | 8.903 | 6.371 | 10.977 |
| 0.2 | typical | none in 60 s | 0.1483 | no (0.0) | 0.4352 | 0.22303 | 701.6 | 0.573 | 3.563 | 10.43 / 10.588 | 10.883 | 8.816 | 10.783 |
| 0.2 | high-side | none in 60 s | 0.1406 | no (0.0) | 0.451 | 0.22027 | 688.7 | 0.558 | 3.48 | 9.983 / 10.275 | 10.522 | 8.527 | 10.591 |
| 0.25 | typical | none in 60 s | 0.1735 | no (0.0) | 0.4178 | 0.26717 | 743.7 | 0.694 | 3.536 | 10.107 / 10.204 | 13.122 | 10.251 | 10.477 |
| 0.25 | high-side | none in 60 s | 0.1651 | no (0.0) | 0.4378 | 0.27046 | 725.5 | 0.714 | 3.488 | 9.682 / 9.882 | 12.625 | 10.047 | 10.311 |
| 0.3 | typical | none in 60 s | 0.1955 | no (0.0) | 0.4013 | 0.29126 | 779.5 | 0.883 | 3.643 | 10.021 / 10.05 | 14.073 | 11.294 | 10.387 |
| 0.3 | high-side | none in 60 s | 0.1901 | no (0.0) | 0.4229 | 0.3043 | 758.2 | 0.949 | 3.565 | 9.346 / 9.398 | 14.851 | 11.734 | 10.038 |
| 0.4 | typical | none in 60 s | 0.2519 | no (0.0) | 0.3325 | 0.34267 | 817.8 | 1.313 | 3.933 | 9.794 / 9.827 | 15.599 | 13.081 | 10.172 |
| 0.4 | high-side | none in 60 s | 0.2393 | no (0.0) | 0.3492 | 0.34278 | 789.4 | 1.316 | 3.89 | 9.344 / 9.367 | 15.107 | 12.516 | 9.96 |
| seq 0.1/0.2/0.4/0.2/0.1 | typical | none in 60 s | 0.1181 | no (0.0) | 0.611 | 0.17023 | 597.4 | 1.417 | 3.029 | 9.926 / 9.93 | 15.837 | 13.064 | 10.309 |
|  | segments | 0.1: 0.0003, 0.2: 0.1488, 0.4: 0.2546, 0.2: 0.1466, 0.1: 0.0003 m/s | | | | | | | | | | | |
| seq 0.1/0.2/0.4/0.2/0.1 | high-side | none in 60 s | 0.1134 | no (0.0) | 0.6186 | 0.17152 | 585.5 | 1.406 | 2.994 | 9.464 / 9.488 | 14.948 | 12.465 | 10.086 |
|  | segments | 0.1: 0.0003, 0.2: 0.1403, 0.4: 0.2449, 0.2: 0.1402, 0.1: 0.0003 m/s | | | | | | | | | | | |
