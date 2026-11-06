#!/bin/bash
# Read-only check of a Pi set up with software/PI_SETUP.md. Changes nothing; prints OK / FAIL /
# WARN per step and exits 1 if any FAIL. Run as the walk user: bash check_pi_setup.sh
# Optional env: RT (Runtime dir), VENV (venv dir), LAB (this repo's altaay_lab dir).
RT=${RT:-$HOME/Open_Duck_Mini_Runtime}
VENV=${VENV:-$HOME/.virtualenvs/open-duck-mini-runtime}
LAB=${LAB:-$HOME/open_duck_mini_v2/altaay_lab}
PY="$VENV/bin/python"
fail=0
ok()   { echo "OK    $*"; }
bad()  { echo "FAIL  $*"; fail=1; }
warn() { echo "WARN  $*"; }

. /etc/os-release 2>/dev/null
[ "$VERSION_CODENAME" = "bookworm" ] && ok "OS: $PRETTY_NAME" || bad "OS is '$VERSION_CODENAME', need bookworm (step 1)"
[ "$(uname -m)" = "aarch64" ] && ok "64-bit kernel" || bad "not aarch64: $(uname -m) (step 1)"
CFG=/boot/firmware/config.txt
grep -Eq '^dtparam=i2c_arm=on' $CFG && ok "I2C enabled in $CFG" || \
  { grep -Eq '^dtoverlay=i2c-gpio.*bus=1' $CFG && ok "software I2C on bus 1 (step 4b)" || bad "I2C not enabled (step 4)"; }
[ -e /dev/i2c-1 ] && ok "/dev/i2c-1 present" || bad "/dev/i2c-1 missing (step 4, reboot?)"
if command -v i2cdetect >/dev/null; then
  i2cdetect -y 1 2>/dev/null | grep -q " 28" && ok "BNO055 answers at 0x28" || warn "no device at 0x28 (IMU wired and powered?)"
fi
grep -Eq '^dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4' $CFG && ok "ears on hardware PWM0/PWM1, GPIO12 and 13 (D53, step 4c)" || bad "ear PWM overlay missing (D53, step 4c)"
if command -v i2cdetect >/dev/null; then
  for a in 29 5a 5b; do i2cdetect -y 1 2>/dev/null | grep -q " $a" && ok "I2C device at 0x$a (D51, D54)" || warn "no device at 0x$a (wired and powered? step 4c)"; done
fi
grep -Eq '^enable_uart=1' $CFG && warn "enable_uart=1: the Pi UART is not used by this build (step 4)" || ok "Pi UART off (not used)"
grep -q 'console=serial0' /boot/firmware/cmdline.txt 2>/dev/null && warn "serial console on (not needed)" || ok "no serial console"
id -nG | grep -qw dialout && ok "user in dialout" || bad "user not in dialout (step 3)"
id -nG | grep -qw gpio && ok "user in gpio" || bad "user not in gpio (step 3)"
id -nG | grep -qw i2c && ok "user in i2c" || bad "user not in i2c (step 3)"
[ -e /dev/ttyACM0 ] && ok "/dev/ttyACM0 present" || warn "/dev/ttyACM0 missing (adapter plugged in? step 5)"
[ -e /dev/odm_servo_bus ] && ok "/dev/odm_servo_bus link present" || warn "udev link missing (optional, step 5)"
[ -x "$PY" ] && ok "venv python: $($PY --version 2>&1)" || bad "venv not found at $VENV (step 6)"
if [ -x "$PY" ]; then
  "$PY" - "$LAB/software/constraints-bookworm.txt" <<'EOF'
import sys
from importlib import metadata
bad = 0
for ln in open(sys.argv[1]):
    ln = ln.strip()
    if not ln or ln.startswith("#") or "==" not in ln:
        continue
    name, want = ln.split("==")
    try:
        have = metadata.version(name)
    except metadata.PackageNotFoundError:
        print(f"FAIL  {name} not installed (want {want})"); bad = 1; continue
    if have != want:
        print(f"WARN  {name} {have} (pinned {want})")
print("OK    pinned packages checked" if not bad else "FAIL  missing packages (step 7)")
try:
    import json
    d = json.loads(metadata.distribution("pypot").read_text("direct_url.json"))
    c = d.get("vcs_info", {}).get("commit_id")
    print(("OK    pypot at " if c == "f6d305e70e1640f66188b256dfd1dcfeb8ab8a59" else "WARN  pypot at ") + str(c))
except Exception as e:  # noqa: BLE001
    print(f"WARN  pypot commit unknown: {e}")
for mod in ("rustypot", "onnxruntime", "adafruit_bno055", "RPi.GPIO", "pypot.feetech", "board"):
    try:
        __import__(mod)
        print(f"OK    import {mod}")
    except Exception as e:  # noqa: BLE001
        print(f"FAIL  import {mod}: {e}")
EOF
fi
H=$(git -C "$RT" rev-parse HEAD 2>/dev/null)
[ "$H" = "376de65435c93486347cd601a31aa96951799896" ] && ok "Runtime at 376de65" || bad "Runtime at '$H' (step 6)"
[ -z "$(git -C "$RT" status --porcelain 2>/dev/null | grep -v '^??')" ] && ok "Runtime files unmodified (D6)" || bad "Runtime files modified (D6)"
[ -f "$HOME/duck_config.json" ] && ok "duck_config.json present" || bad "no ~/duck_config.json (step 9)"
[ -f "$RT/scripts/imu_calib_data.pkl" ] && ok "IMU calibration file in scripts/" || warn "no scripts/imu_calib_data.pkl (step 10)"
if [ -f "$HOME/BEST_WALK_ONNX_2.onnx" ]; then
  s=$(sha256sum "$HOME/BEST_WALK_ONNX_2.onnx" | cut -d' ' -f1)
  [ "$s" = "3c606f9381a1710cc8fecdb7442787dcbfce3ee9bc02a6f1224774ab2b3a1067" ] && ok "policy file checksum" || bad "policy checksum $s (step 8)"
else bad "no ~/BEST_WALK_ONNX_2.onnx (step 8)"; fi
systemctl is-enabled open-duck-walk.service >/dev/null 2>&1 && warn "image service open-duck-walk enabled (step 11)"
systemctl is-enabled odm-walk-guard.service >/dev/null 2>&1 && ok "odm-walk-guard enabled" || echo "INFO  odm-walk-guard not enabled (manual start)"
sudo -n -l /usr/bin/systemctl poweroff >/dev/null 2>&1 && ok "guard may power off (sudoers)" || warn "no sudoers line for poweroff (step 11)"
exit $fail
