#!/bin/bash
# Run the fit workload in an aarch64 Bookworm root under qemu-user.
# Four cores. A memory cgroup. Each timed core is throttled so its CoreMark
# matches the cited Pi Zero 2 W score passed in as --cited-coremark.
#
#   bash run_cgroup.sh --rootfs ROOT --repo REPO --voice DIR --wav FILE \
#       --cited-coremark 3191 --measured-coremark 7341 --mem-mib 417 \
#       --ballast-mib 125.4 --mode spread --out result.json
#
# Labels: the process RSS is measured in emulation and includes qemu-user.
# The CoreMark target is cited. The quota is calc only from those two scores.
set -euo pipefail

ROOTFS=""
REPO=""
VOICE=""
WAV=""
OUT=""
CITED=""
MEASURED=""
MEM_MIB="417"
BALLAST_MIB="125.4"
MODE="spread"
PIPER="en_US-lessac-low.onnx"
QUOTA_US=""
SECONDS_RUN="180"

while [ $# -gt 0 ]; do
  case "$1" in
    --rootfs) ROOTFS=${2:?}; shift ;;
    --repo) REPO=${2:?}; shift ;;
    --voice) VOICE=${2:?}; shift ;;
    --wav) WAV=${2:?}; shift ;;
    --out) OUT=${2:?}; shift ;;
    --cited-coremark) CITED=${2:?}; shift ;;
    --measured-coremark) MEASURED=${2:?}; shift ;;
    --quota-us) QUOTA_US=${2:?}; shift ;;
    --mem-mib) MEM_MIB=${2:?}; shift ;;
    --ballast-mib) BALLAST_MIB=${2:?}; shift ;;
    --mode) MODE=${2:?}; shift ;;
    --piper) PIPER=${2:?}; shift ;;
    --seconds) SECONDS_RUN=${2:?}; shift ;;
    *) echo "unknown arg $1" >&2; exit 2 ;;
  esac
  shift
done

if [ -z "$ROOTFS" ] || [ -z "$REPO" ] || [ -z "$VOICE" ] || [ -z "$WAV" ] || [ -z "$OUT" ]; then
  echo "need --rootfs --repo --voice --wav --out" >&2
  exit 2
fi

if [ -z "$CITED" ] || [ -z "$MEASURED" ]; then
  echo "need --cited-coremark and --measured-coremark" >&2
  exit 2
fi
case "$WAV" in
  "$VOICE"/*) ;;
  *) echo "wav must sit inside the voice directory" >&2; exit 2 ;;
esac

QUOTA=$(python3 - "$MEASURED" "$CITED" <<'PY'
import sys
measured = float(sys.argv[1])
cited = float(sys.argv[2])
share = cited / measured
if share > 1.0:
    share = 1.0
print(max(1000, int(round(share * 100000))))
PY
)

if [ -n "${QUOTA_US:-}" ]; then
  QUOTA=$QUOTA_US
fi

PARENT=/sys/fs/cgroup/odm-fit
MEM=$PARENT/mem
# Drop a previous tree if this shell still owns it.
if [ -d "$MEM" ]; then
  sudo find "$MEM" -name cgroup.procs -exec sh -c 'for p in $(cat "$1" 2>/dev/null); do kill "$p" 2>/dev/null || true; done' _ {} \; || true
  sudo find "$PARENT" -depth -type d -exec rmdir {} \; 2>/dev/null || true
fi
sudo mkdir -p "$MEM/ballast" "$MEM/walk" "$MEM/voice" "$MEM/camera"
echo "0-3" | sudo tee "$PARENT/cpuset.cpus" >/dev/null
echo "0" | sudo tee "$PARENT/cpuset.mems" >/dev/null
echo '+cpuset +cpu +memory' | sudo tee "$PARENT/cgroup.subtree_control" >/dev/null
echo "0-3" | sudo tee "$MEM/cpuset.cpus" >/dev/null
echo "0" | sudo tee "$MEM/cpuset.mems" >/dev/null
echo '+cpuset +cpu +memory' | sudo tee "$MEM/cgroup.subtree_control" >/dev/null
# Bytes. 1 MiB is 1024*1024, matching the cited top "MiB" column.
python3 - "$MEM_MIB" <<'PY' | sudo tee "$MEM/memory.max" >/dev/null
import sys
print(int(round(float(sys.argv[1]) * 1024 * 1024)))
PY
echo 0 | sudo tee "$MEM/memory.peak" >/dev/null || true
# Allow swap so a spill is visible. A spill fails the RAM rule.
if [ -f "$MEM/memory.swap.max" ]; then
  echo max | sudo tee "$MEM/memory.swap.max" >/dev/null || true
fi
echo "3" | sudo tee "$MEM/ballast/cpuset.cpus" >/dev/null
echo "0" | sudo tee "$MEM/ballast/cpuset.mems" >/dev/null
echo "0" | sudo tee "$MEM/walk/cpuset.cpus" >/dev/null
echo "0" | sudo tee "$MEM/walk/cpuset.mems" >/dev/null
echo "${QUOTA} 100000" | sudo tee "$MEM/walk/cpu.max" >/dev/null
echo "1" | sudo tee "$MEM/voice/cpuset.cpus" >/dev/null
echo "0" | sudo tee "$MEM/voice/cpuset.mems" >/dev/null
echo "${QUOTA} 100000" | sudo tee "$MEM/voice/cpu.max" >/dev/null
echo "2" | sudo tee "$MEM/camera/cpuset.cpus" >/dev/null
echo "0" | sudo tee "$MEM/camera/cpuset.mems" >/dev/null
echo "${QUOTA} 100000" | sudo tee "$MEM/camera/cpu.max" >/dev/null

BYTES=$(python3 - "$BALLAST_MIB" <<'PY'
import sys
print(int(round(float(sys.argv[1]) * 1024 * 1024)))
PY
)
BALLAST=$ROOTFS/usr/local/bin/odm-ballast
if [ ! -x "$BALLAST" ]; then
  echo "missing ballast binary" >&2
  exit 1
fi

sudo mkdir -p "$ROOTFS/mnt/repo" "$ROOTFS/mnt/voice" "$ROOTFS/mnt/out" "$ROOTFS/proc" "$ROOTFS/sys"
sudo mountpoint -q "$ROOTFS/proc" || sudo mount --bind /proc "$ROOTFS/proc"
sudo mountpoint -q "$ROOTFS/sys" || sudo mount --bind /sys "$ROOTFS/sys"
sudo mkdir -p "$ROOTFS/sys/fs/cgroup"
sudo mountpoint -q "$ROOTFS/sys/fs/cgroup" || sudo mount --bind /sys/fs/cgroup "$ROOTFS/sys/fs/cgroup"
sudo mountpoint -q "$ROOTFS/mnt/repo" || sudo mount --bind "$REPO" "$ROOTFS/mnt/repo"
sudo mountpoint -q "$ROOTFS/mnt/voice" || sudo mount --bind "$VOICE" "$ROOTFS/mnt/voice"
sudo mkdir -p "$(dirname "$OUT")"
sudo mountpoint -q "$ROOTFS/mnt/out" || sudo mount --bind "$(dirname "$OUT")" "$ROOTFS/mnt/out"

# Start ballast inside its cgroup. Root can raise the lock limit.
sudo sh -c "ulimit -l unlimited; echo \$\$ > /tmp/odm-ballast.pid; echo \$\$ > '$MEM/ballast/cgroup.procs'; exec '$BALLAST' '$BYTES'" >/tmp/odm-ballast.log 2>&1 &
sleep 0.4
if ! grep -q locked /tmp/odm-ballast.log; then
  echo "ballast did not lock" >&2
  cat /tmp/odm-ballast.log >&2 || true
  if [ -f /tmp/odm-ballast.pid ]; then kill "$(cat /tmp/odm-ballast.pid)" 2>/dev/null || true; fi
  exit 1
fi

SPREAD_FLAG=""
if [ "$MODE" = "spread" ]; then
  SPREAD_FLAG="--spread"
fi
OUT_NAME=$(basename "$OUT")
set +e
ENV_EXTRA="PYTHONPATH=/mnt/repo"
if [ "$MODE" = "spread" ]; then
  ENV_EXTRA="$ENV_EXTRA MALLOC_ARENA_MAX=2"
fi
sudo sh -c "ulimit -l unlimited; echo \$\$ > '$MEM/walk/cgroup.procs'; exec chroot '$ROOTFS' /usr/bin/qemu-aarch64-static /usr/bin/env $ENV_EXTRA /opt/odm/bin/python3 -m altaay_lab.software.pi_fit.workload --role stack --policy /mnt/repo/BEST_WALK_ONNX_2.onnx --voice-dir /mnt/voice --piper '$PIPER' --wav /mnt/voice/$(basename "$WAV") --seconds '$SECONDS_RUN' --threads 1 --walk-cpu 0 --auto-cpu 0 --voice-cgroup '$MEM/voice' --camera-cgroup '$MEM/camera' --mem-cgroup '$MEM' $SPREAD_FLAG --out /mnt/out/$OUT_NAME"
CODE=$?
set -e
if [ -f /tmp/odm-ballast.pid ]; then
  kill "$(cat /tmp/odm-ballast.pid)" 2>/dev/null || true
fi

PEAK=$(cat "$MEM/memory.peak" 2>/dev/null || echo 0)
SWAP=$(cat "$MEM/memory.swap.peak" 2>/dev/null || echo 0)
python3 - "$OUT" "$CODE" "$PEAK" "$SWAP" "$QUOTA" "$MEM_MIB" "$BALLAST_MIB" "$MODE" "$CITED" "$MEASURED" <<'PY'
import json, sys
path, code, peak, swap, quota, mem, ballast, mode, cited, measured = sys.argv[1:]
try:
    report = json.loads(open(path, encoding="utf-8").read())
except Exception:
    report = {"label": "measured in emulation", "error": "no workload json"}
report["cgroup"] = {
    "label": "measured in emulation",
    "exit_code": int(code),
    "memory_peak_mib": int(peak) / (1024.0 * 1024.0),
    "swap_peak_mib": int(swap) / (1024.0 * 1024.0) if str(swap).isdigit() else None,
    "cpu_quota_us": int(quota),
    "cpu_period_us": 100000,
    "mem_limit_mib": float(mem),
    "ballast_mib": float(ballast),
    "ballast_label": "cited size locked, not a live Raspberry Pi OS boot",
    "mode": mode,
    "cited_coremark": float(cited) if cited else None,
    "measured_coremark": float(measured) if measured else None,
    "coremark_label": "cited target, measured in emulation, quota is calc only",
}
try:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle)
        handle.write("\n")
except OSError:
    alt = path + ".cgroup.json"
    with open(alt, "w", encoding="utf-8") as handle:
        json.dump(report["cgroup"], handle)
        handle.write("\n")
print(json.dumps({"exit": int(code), "peak_mib": report["cgroup"]["memory_peak_mib"], "swap_mib": report["cgroup"]["swap_peak_mib"]}))
PY
# The workload writes the result and returns 0. A later merge that cannot
# replace a root-owned file should not hide that result.
if [ -s "$OUT" ]; then
  exit 0
fi
exit "$CODE"
