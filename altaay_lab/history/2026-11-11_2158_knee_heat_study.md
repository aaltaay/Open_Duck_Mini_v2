# 2026-11-11 9:58 PM ET: knee heat check

The 3.3 minute and 94.7 C knee figures were checked by hand against the P45B backlash walk log and the STS3215 sheet. Calc only, except the log and the older twin numbers, which stay sim pass only. Nothing was bought. No policy was trained. STATE.md was not edited. No decision record was edited. Nothing under twin/dock/nest/ was edited.

The thermal row in TWIN_CHECKLIST.md had said the right knee reading reaches 60 C at 3.3 minutes (25 C) and 2.5 minutes (32 C), and that if the torque stays on the right knee body reaches 94.7 C and 101.6 C. That wording is replaced by the row in this commit. The study is twin/thermal/KNEE_HEAT_STUDY.md.

Verdict: the 94.7 C body is OVERSTATED. It is the model with the 70 C torque-off switched off and with copper resistance rising at a frozen current. With the torque-off left on, the case peaks near 64 C. The 3.3 minutes is the short end of the same model (the crossing is 3.22 minutes; 3.3 is the next 10 second sample). Cold resistance gives 4.6 minutes. The plain walk's published copper gives about 6 to 8 minutes. The old 10 minutes was the plain walk reaching 70 C, not a different current. Continuous walking in this model still leaves 60 C inside about 8 minutes.

The walk current in the first 4 minutes is 1.45 A RMS, not the 2.5 A stall. The extra mass is not the cause (knee RMS torque 2.18 Nm against 2.19 Nm). The heat is the stiff walk: the knee is on the torque stop about a quarter of the time, and an 8 degree miss at the backlash gain is about 2.4 Nm.

Recommendation: torque-off rests and a 55 C stop now. Keep the STS3250 path for a long walk, after one unit is measured, and do not walk the stock policy on it. A retrain was not run.
