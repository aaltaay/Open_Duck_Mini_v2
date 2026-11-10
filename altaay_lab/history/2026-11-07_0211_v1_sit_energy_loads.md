# 2026-11-07 2:11 AM ET: stop loads by the energy method, the mass-case model fix (D59)

Labels: calc only (the loads), sim pass only (the impact speeds and the balance gate). Nothing bought or printed.

- The sim's hard-limit impulses are no longer design loads: every stop takes the energy method (impact speed from the
  sim, the stack compliance of sitlib.STOP_STACK), with the compliant-stop sim as the cross-check (2 to 6 x higher on
  the push impacts, within 7 % on the torque-on neck shove). Scripts in, single runs validated; the full runs and the
  stress table on them are open (twin/sit/SIT.md section 4).
- Codex: a mass case (balance +-5 %, the held body of the head shoves) is now its own compiled model variant; the
  balance gate rerun on it: PASS, CoM 75.6 mm inside the footprint in the worst case.
- The head and neck stop redesign is measured and written up (SIT.md section 4), not built: handed over.
