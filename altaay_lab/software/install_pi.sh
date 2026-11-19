#!/bin/bash
# One install for the duck Pi. Idempotent. A check runs at the end.
#
#   bash software/install_pi.sh --mock --prefix /tmp/odm-root
#   bash software/install_pi.sh
#
# --mock fills a prefix and does not call apt, sudo, or git clone.
# A second run leaves the installed files unchanged and still runs the check.
#
# Installs: Runtime pin 376de65 (real mode clones it), the walk policy,
# personality, dock, the knee-heat and battery guards, the walk service,
# the udev rule, the poweroff sudoers line, and the ear PWM overlay.
# The Runtime tree is not edited (D6).
set -euo pipefail

MOCK=0
PREFIX=""
USER_NAME=""
HOME_DIR=""
RUNTIME_PIN=376de65435c93486347cd601a31aa96951799896
POLICY_SHA=3c606f9381a1710cc8fecdb7442787dcbfce3ee9bc02a6f1224774ab2b3a1067

while [ $# -gt 0 ]; do
  case "$1" in
    --mock) MOCK=1 ;;
    --prefix) PREFIX=${2:?}; shift ;;
    --user) USER_NAME=${2:?}; shift ;;
    --home) HOME_DIR=${2:?}; shift ;;
    -h|--help)
      sed -n '2,16p' "$0"
      exit 0
      ;;
    *) echo "FAIL  unknown argument $1" >&2; exit 2 ;;
  esac
  shift
done

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
LAB=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
REPO=$(CDPATH= cd -- "$LAB/.." && pwd)

if [ "$MOCK" = 1 ]; then
  USER_NAME=${USER_NAME:-duck}
  HOME_DIR=${HOME_DIR:-/home/duck}
  if [ -z "$PREFIX" ]; then
    echo "FAIL  --mock needs --prefix" >&2
    exit 2
  fi
else
  USER_NAME=${USER_NAME:-$(id -un)}
  HOME_DIR=${HOME_DIR:-$HOME}
fi

# Files land under PREFIX when it is set (the mock root, or a staging root).
# On the Pi, PREFIX is empty and paths are absolute.
root() { printf '%s%s' "$PREFIX" "$1"; }

changed=0
note_same() { echo "unchanged $*"; }
note_new() { echo "installed $*"; changed=1; }

# System paths need root on the Pi. A prefix (the mock root) is written as the
# current user. Home files stay user-owned either way.
priv() {
  dest=$1
  shift
  if [ -n "${ODM_PRIV_SH:-}" ]; then
    "$ODM_PRIV_SH" "$dest" "$@"
    return
  fi
  if [ -z "$PREFIX" ] && [ "$(id -u)" -ne 0 ]; then
    case "$dest" in
      /etc/*|/boot/*|/var/*) sudo "$@" ; return ;;
    esac
  fi
  "$@"
}

apply_mode() {
  dest=$1
  case "$dest" in
    */sudoers.d/*) priv "$dest" chmod 0440 "$dest" ;;
    /etc/*|/boot/*|/var/*) priv "$dest" chmod 0644 "$dest" ;;
  esac
}

copy_if_changed() {
  src=$1
  dst=$2
  priv "$dst" mkdir -p "$(dirname -- "$dst")"
  if [ -f "$dst" ] && priv "$dst" cmp -s "$src" "$dst"; then
    note_same "$dst"
  else
    priv "$dst" cp "$src" "$dst"
    apply_mode "$dst"
    note_new "$dst"
  fi
}

grep_q() {
  pattern=$1
  file=$2
  priv "$file" grep -q -e "$pattern" "$file"
}

ensure_line() {
  file=$1
  line=$2
  priv "$file" mkdir -p "$(dirname -- "$file")"
  tmp=$(mktemp)
  if [ -f "$file" ]; then
    priv "$file" cat "$file" > "$tmp"
  else
    printf '%s\n' "# written by altaay_lab/software/install_pi.sh" > "$tmp"
  fi
  if grep -Fxq "$line" "$tmp"; then
    note_same "$file :: $line"
    rm -f "$tmp"
    return 0
  fi
  printf '%s\n' "$line" >> "$tmp"
  priv "$file" cp "$tmp" "$file"
  apply_mode "$file"
  rm -f "$tmp"
  note_new "$file :: $line"
}

if [ "$MOCK" = 0 ]; then
  if ! dpkg -s git python3-pip python3-venv python3-dev i2c-tools >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y git python3-pip python3-venv python3-dev i2c-tools
  else
    note_same "apt packages"
  fi
fi

RT=$(root "$HOME_DIR/Open_Duck_Mini_Runtime")
if [ "$MOCK" = 1 ]; then
  mkdir -p "$RT/.git"
  pinfile=$RT/.git/HEAD
  if [ -f "$pinfile" ] && [ "$(tr -d '[:space:]' < "$pinfile")" = "$RUNTIME_PIN" ]; then
    note_same "$pinfile"
  else
    printf '%s\n' "$RUNTIME_PIN" > "$pinfile"
    note_new "$pinfile"
  fi
  marker=$RT/MOCK_CHECKOUT
  if [ ! -f "$marker" ]; then
    printf '%s\n' "mock hardware checkout marker. pin only. not a Runtime tree." > "$marker"
    changed=1
  else
    note_same "$marker"
  fi
else
  if [ ! -d "$RT/.git" ]; then
    git clone https://github.com/apirrone/Open_Duck_Mini_Runtime "$RT"
    changed=1
  fi
  head=$(git -C "$RT" rev-parse HEAD)
  dirty=$(git -C "$RT" status --porcelain | grep -v '^??' || true)
  if [ -n "$dirty" ]; then
    echo "FAIL  Runtime files are modified (D6)" >&2
    exit 1
  fi
  if [ "$head" != "$RUNTIME_PIN" ]; then
    git -C "$RT" fetch --tags origin
    git -C "$RT" checkout "$RUNTIME_PIN"
    changed=1
  else
    note_same "Runtime at $RUNTIME_PIN"
  fi
fi

policy_src=$REPO/BEST_WALK_ONNX_2.onnx
policy_dst=$(root "$HOME_DIR/BEST_WALK_ONNX_2.onnx")
if [ ! -f "$policy_src" ]; then
  echo "FAIL  policy file missing at repo root BEST_WALK_ONNX_2.onnx" >&2
  exit 1
fi
copy_if_changed "$policy_src" "$policy_dst"

config_src=$LAB/software/duck_config.altaay.json
config_dst=$(root "$HOME_DIR/duck_config.json")
if [ -f "$config_dst" ]; then
  note_same "$config_dst"
else
  copy_if_changed "$config_src" "$config_dst"
fi

# Boot config. Software I2C matches the netlist I2C note. Skip the pair when
# hardware I2C is already turned on, so a second style is not appended.
cfg=$(root "/boot/firmware/config.txt")
if [ -f "$cfg" ] && grep -Eq '^dtparam=i2c_arm=on' "$cfg"; then
  echo "WARN  hardware I2C already on; netlist asks for dtoverlay=i2c-gpio,bus=1"
else
  ensure_line "$cfg" "dtparam=i2c_arm=off"
  ensure_line "$cfg" "dtoverlay=i2c-gpio,bus=1,i2c_gpio_sda=2,i2c_gpio_scl=3,i2c_gpio_delay_us=2"
fi
ensure_line "$cfg" "enable_uart=0"
ensure_line "$cfg" "dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4"
ensure_line "$cfg" "dtoverlay=max98357a,no-sdmode"

copy_if_changed "$LAB/software/99-odm-servo-bus.rules" "$(root "/etc/udev/rules.d/99-odm-servo-bus.rules")"

sudoers_src=$(mktemp)
sed "s/^duck /$USER_NAME /" "$LAB/software/odm-poweroff.sudoers" > "$sudoers_src"
copy_if_changed "$sudoers_src" "$(root "/etc/sudoers.d/odm-poweroff")"
rm -f "$sudoers_src"

unit_src=$(mktemp)
sed -e "s|^User=duck|User=$USER_NAME|" \
    -e "s|/home/duck|$HOME_DIR|g" \
    "$LAB/software/odm-walk-guard.service" > "$unit_src"
if ! grep -q '^Environment=ODM_HW_PWM=1' "$unit_src"; then
  printf '\n%s\n%s\n' \
    "Environment=ODM_HW_PWM=1" \
    "Environment=ODM_LAB_SOFTWARE=$HOME_DIR/open_duck_mini_v2/altaay_lab/software" \
    >> "$unit_src"
fi
copy_if_changed "$unit_src" "$(root "/etc/systemd/system/odm-walk-guard.service")"
rm -f "$unit_src"

copy_if_changed "$LAB/software/pi_fit/zramswap.default" "$(root "/etc/default/zramswap")"

site=$(root "$HOME_DIR/.virtualenvs/open-duck-mini-runtime/lib/python3.11/site-packages/sitecustomize.py")
copy_if_changed "$LAB/software/hw_pwm_sitecustomize.py" "$site"

if [ "$MOCK" = 0 ]; then
  venv=$HOME_DIR/.virtualenvs/open-duck-mini-runtime
  if [ ! -x "$venv/bin/python" ]; then
    python3 -m venv "$venv"
    changed=1
  else
    note_same "$venv"
  fi
  if ! "$venv/bin/python" -c 'import rustypot' >/dev/null 2>&1; then
    # shellcheck disable=SC1091
    "$venv/bin/pip" install -c "$LAB/software/constraints-bookworm.txt" -e "$RT"
    "$venv/bin/pip" install -c "$LAB/software/constraints-bookworm.txt" 'RPi.GPIO==0.7.1'
    changed=1
  else
    note_same "venv packages"
  fi
fi

stamp=$(root "/var/lib/odm/installed.json")
stamp_body=$(mktemp)
cat > "$stamp_body" <<EOF
{
  "runtime_pin": "$RUNTIME_PIN",
  "policy_sha256": "$POLICY_SHA",
  "components": [
    "runtime",
    "policy",
    "personality",
    "dock",
    "knee_heat",
    "battery_guard",
    "walk_service",
    "antennas_overlay"
  ],
  "mock": $MOCK
}
EOF
copy_if_changed "$stamp_body" "$stamp"
rm -f "$stamp_body"

fail=0
ok() { echo "OK    $*"; }
bad() { echo "FAIL  $*"; fail=1; }

echo "== install check =="
[ -f "$LAB/software/personality/engine.py" ] && ok "personality" || bad "personality missing"
[ -f "$LAB/software/dock/autodock/duck_autodock.py" ] && ok "dock" || bad "dock missing"
[ -f "$LAB/software/knee_heat.py" ] && ok "knee heat guard" || bad "knee_heat.py missing"
[ -f "$LAB/bench/battery_guard.py" ] && ok "battery guard" || bad "battery_guard.py missing"
[ -f "$LAB/bench/walk_with_guard.py" ] && ok "walk_with_guard.py" || bad "walk program missing"
grep -q 'rustypot==0.1.0' "$LAB/software/constraints-bookworm.txt" && ok "constraints pin rustypot 0.1.0" || bad "constraints"

head_txt=$(tr -d '[:space:]' < "$RT/.git/HEAD" || true)
if [ "$MOCK" = 1 ]; then
  [ "$head_txt" = "$RUNTIME_PIN" ] && ok "Runtime pin $RUNTIME_PIN" || bad "Runtime pin '$head_txt'"
else
  got=$(git -C "$RT" rev-parse HEAD)
  [ "$got" = "$RUNTIME_PIN" ] && ok "Runtime at $RUNTIME_PIN" || bad "Runtime at $got"
  [ -z "$(git -C "$RT" status --porcelain | grep -v '^??' || true)" ] && ok "Runtime files unmodified (D6)" || bad "Runtime files modified (D6)"
fi

sum=$(sha256sum "$policy_dst" | awk '{print $1}')
[ "$sum" = "$POLICY_SHA" ] && ok "policy checksum" || bad "policy checksum $sum"
[ -f "$config_dst" ] && ok "duck_config.json" || bad "duck_config.json missing"

unit=$(root "/etc/systemd/system/odm-walk-guard.service")
grep_q '--knee-heat' "$unit" && ok "service passes --knee-heat" || bad "service missing --knee-heat"
grep_q 'walk_with_guard.py' "$unit" && ok "service starts walk_with_guard.py" || bad "service missing walk program"
grep_q '^Environment=ODM_HW_PWM=1' "$unit" && ok "service sets the ear PWM overlay" || bad "service missing ODM_HW_PWM"
grep_q 'CPUAffinity=0' "$unit" && ok "walk pinned to cpu 0" || bad "walk pin"
grep_q 'ODM_ORT_THREADS=1' "$unit" && ok "walk onnx threads" || bad "walk onnx threads"
grep_q 'ALGO=lz4' "$(root "/etc/default/zramswap")" && ok "zram config" || bad "zram config"
grep_q "User=$USER_NAME" "$unit" && ok "service user $USER_NAME" || bad "service user"

grep_q '1a86' "$(root "/etc/udev/rules.d/99-odm-servo-bus.rules")" && ok "udev rule" || bad "udev rule"
grep_q 'systemctl poweroff' "$(root "/etc/sudoers.d/odm-poweroff")" && ok "poweroff sudoers" || bad "sudoers"
grep_q 'dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4' "$cfg" && ok "ear PWM overlay in config.txt" || bad "pwm overlay"
grep_q 'dtoverlay=max98357a,no-sdmode' "$cfg" && ok "I2S amp overlay" || bad "amp overlay"
grep -q 'ODM_HW_PWM' "$site" && ok "sitecustomize overlay" || bad "sitecustomize"

python3 -m py_compile "$LAB/software/hw_pwm.py" "$LAB/bench/day_one.py" "$LAB/bench/mock_hw.py" \
  && ok "day-one programs compile" || bad "compile"

if [ "$MOCK" = 0 ] && [ -f /etc/os-release ]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  if [ "${VERSION_CODENAME:-}" = "bookworm" ]; then
    RT=$HOME_DIR/Open_Duck_Mini_Runtime \
      VENV=$HOME_DIR/.virtualenvs/open-duck-mini-runtime \
      LAB=$LAB \
      bash "$LAB/software/check_pi_setup.sh" || fail=1
  else
    echo "WARN  not bookworm; skipped check_pi_setup.sh"
  fi
fi

if [ "$fail" -eq 0 ]; then
  echo "OVERALL: PASS"
else
  echo "OVERALL: FAIL"
fi
if [ "$changed" -eq 0 ]; then
  echo "unchanged install tree"
fi
exit "$fail"
