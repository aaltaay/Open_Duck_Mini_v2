# Run D eval (sim pass only)

Nothing here was measured on hardware.

- sweep.py: 60 s constant-command walks. Set ODM_ONNX to the policy file before starting. The script assigns that path onto current_budget after import, because that module freezes ONNX at import.
- sweep60_D_300482560.json: the run D sweep. The onnx field is the export name 2026_11_14_201938_300482560.onnx. That export is filed as ../sts12_runD_policy.onnx (final step 300,482,560).
- twin_C/: run C comparison session, make-twin style.
- twin_D/: run D comparison session, make-twin style.

The numbers are in ../RUN_D.md. The live `make twin` report is altaay_lab/twin/out/REPORT.md.

The merged report before the policy pin (30.07 walking minutes, 17.48 A pack peak) was the stock BEST_WALK_ONNX_2 policy and is superseded.

A sentence inside twin_D/REPORT.md still says a held current levels off near 59 C. That sentence came from the report writer and does not match this session's table: 0 rests, knee peak 38.4 C (sim pass only). The live report uses the session peak.
