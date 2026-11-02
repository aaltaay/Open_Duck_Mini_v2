#!/usr/bin/env bash
# Run every check that works without the physical robot and write altaay_lab/VERIFICATION.md.
#
#   bash altaay_lab/verify/run_all.sh            everything (about 25 minutes on the shared 4-CPU box)
#   bash altaay_lab/verify/run_all.sh --quick    skip the MuJoCo, ngspice, CAD-sweep and viewer runs; reuse their
#                                                results from an earlier full run in the same VERIFY_OUT
# Settings (environment):
#   VERIFY_OUT       results folder, outside the repo (default ${TMPDIR:-/tmp}/odm_verify)
#   ODM_RUNTIME      Open_Duck_Mini_Runtime checkout at 376de65 (default /home/user/upstream/Open_Duck_Mini_Runtime)
#   ODM_PLAYGROUND   Open_Duck_Playground checkout at b9be205 (default /home/user/upstream/Open_Duck_Playground)
#   ODM_TEST_PYTHON  Python with rustypot 0.1.0 and pypot for the bench tests (default: python3)
# Nothing in the repo is written except altaay_lab/VERIFICATION.md. Scripts of other agents that write files are run
# on copies or pointed at VERIFY_OUT. Sims run under nice -n 10.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
export VERIFY_OUT="${VERIFY_OUT:-${TMPDIR:-/tmp}/odm_verify}"
export PYTHONDONTWRITEBYTECODE=1
QUICK=0
[ "${1:-}" = "--quick" ] && QUICK=1
mkdir -p "$VERIFY_OUT"
cd "$REPO" || exit 1
PY="${PYTHON:-python3}"
log() { echo "[$(TZ=America/New_York date '+%H:%M:%S ET')] $*"; }
run() {
  log "$1"
  nice -n 10 "$PY" -B "$HERE/$1" || log "  $1 exited with $? (its result file says why)"
}
log "results in $VERIFY_OUT"
if [ "$QUICK" = 1 ]; then
  export VERIFY_REUSE=1
else
  rm -f "$VERIFY_OUT"/*.json
fi
# 1. existing checks that are quick
run e1_erc.py
run e2_bom_scripts.py
# 2. new cross-checks that need nothing heavy
run c5_servo_ids.py
run c6_gpio.py
run c2_connectors.py
# 3. viewer build (CAD counts; C1 and C9 read its manifest)
[ "$QUICK" = 1 ] && [ -f "$VERIFY_OUT/E4.json" ] && log "e4_viewer.py skipped (--quick)" || run e4_viewer.py
run c1_bom_coverage.py
run c9_docs.py
# 4. sims (sim pass only)
run e5_current_budget.py
run e6_power_path.py
[ "$QUICK" = 1 ] && [ -f "$VERIFY_OUT/E6b.json" ] && log "e6b_hop_sweep.py skipped (--quick)" || run e6b_hop_sweep.py
run c7_current_ratings.py
run c8_policy_mass.py
# 5. CAD sweep of the hip roll screw, fasteners, cables, sheets, bench tests
[ "$QUICK" = 1 ] && [ -f "$VERIFY_OUT/E7.json" ] && log "e7_hip_roll.py skipped (--quick)" || run e7_hip_roll.py
run e9_joint_envelope.py
run c11_hip_yaw_envelope.py
run c4_fasteners.py
run c3_cables3d.py
run c10_sheets.py
run e8_bench_pytest.py
# 6. the page
log "report"
"$PY" -B "$HERE/report.py" --write "$REPO/altaay_lab/VERIFICATION.md"
