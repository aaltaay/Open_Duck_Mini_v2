# PI_SETUP: blank SD card to a walking Open Duck Mini v2 (Altaay lab build)

Written 2026-11-02 by the Claude Code software agent (agent S). Nothing here was run on a real Pi: every step is cited to the Runtime docs or code, to the vendor, or to a lab test on the simulated bus (software/SOFTWARE.md). Steps that could not be checked are marked UNVERIFIED.

Tags: [U] upstream file and line (Open_Duck_Mini_Runtime at 376de65 unless named), [I] internet page, [L] our own file or test.

Conventions: the Pi user is called `duck` below (pick your own in step 1 and replace it everywhere, including software/odm-walk-guard.service). `RT` = `~/Open_Duck_Mini_Runtime`. `LAB` = `~/open_duck_mini_v2/altaay_lab`.

## 0. The 0.2.3 image ("Added ISO release") or a manual install?

What commit 376de65 is: documentation only. It adds docs/INSTALL.md and docs/RELEASE_GUIDE.md and 8 lines in README.md [U `git show --stat 376de65`]. The image itself is a release asset, version 0.2.3 [U README.md line 5], made by MaxMakesStuff [U README.md line 7] from a configured SD card with the RELEASE_GUIDE steps [U docs/RELEASE_GUIDE.md lines 1-15]:
- Raspberry Pi OS Lite 64-bit Bookworm, tested only on the Pi Zero 2 W [U docs/INSTALL.md line 3, README.md line 7]; flash the .zip, not the .iso inside [U INSTALL.md line 25].
- Published logins: user `bdxv2` password `ilovemyduck`; Wi-Fi `Duckspot` / `12345678`; fallback hotspot `Openduck` [U INSTALL.md lines 43-73], key `openduck1234` in the guide [U RELEASE_GUIDE.md line 42].
- Autostart `open-duck-walk.service`: at boot GPIO22 low starts the walk, GPIO27 low the head puppet [U RELEASE_GUIDE.md lines 67-68, 89-104]; `Restart=always`, `RestartSec=5` [U RELEASE_GUIDE.md lines 242-243]; needs a paired Xbox pad [U INSTALL.md line 130].
- Not readable from this session: the release page itself (asset name, size, checksum) and the Runtime, pypot and Blinka versions inside the image. UNVERIFIED.

Decision for this build: **manual install (steps 1 to 13), not the image.** Reasons:
1. D6 pins the Runtime at 376de65; the image's contents cannot be checked against that pin before flashing.
2. In our wiring GPIO22 is the left foot and GPIO27 the right foot (D9, D17), so a robot standing on the floor at power-on starts the bare walk with no battery or temperature guard, and `Restart=always` restarts it 5 s after any stop. That defeats the D16 guard (step 11 replaces it).
3. The image ships public default passwords.
Fallback, if the manual install fails: flash the image, change all three passwords [U INSTALL.md lines 52-55, 80-84], run `sudo systemctl disable --now open-duck-walk.service`, then continue from step 8 and run software/check_pi_setup.sh (step 13) to see what the image contains.

## 1. Flash Raspberry Pi OS Lite 64-bit **Bookworm** (not the current default)

The Runtime README says "Raspberry Pi OS Lite (64-bit)" [U README.md line 15]. Today that is Trixie, with Python 3.13. onnxruntime 1.18.1, numpy 1.26.4 and pygame 2.6.0, all pinned by the Runtime [U setup.cfg lines 19-26], have no cp313 aarch64 wheel [I pypi.org JSON for each, read 2026-11-02], so the install fails (as in Runtime PR #43, UPSTREAM_ISSUES.md G11). Bookworm has Python 3.11.2 [I bookworm .info manifest below], and every pinned package has a cp311 aarch64 wheel.

1. On the PC, download `2026-10-06-raspios-bookworm-arm64-lite.img.xz` (422 MB) from https://downloads.raspberrypi.com/raspios_oldstable_lite_arm64/images/raspios_oldstable_lite_arm64-2026-10-06/ [I].
2. Check it: SHA-256 `9e938c5a6981c3f498b3b564c527f3e1fd58ef20bbf703be0eea748384a6c1af` [I the .sha256 file in that folder].
3. Raspberry Pi Imager: Device "Raspberry Pi Zero 2 W", Operating System "Use custom", pick the .img.xz, storage = the 32 GB card (BOM). In OS customisation [U README.md lines 17-23]: hostname `duck`, user `duck` with your own password, your Wi-Fi with country US, Services: enable SSH. (Imager offers customisation for custom images: UNVERIFIED for your Imager version; if it does not, attach a screen and keyboard for step 2 [U README.md lines 25-31].)

## 2. First boot, SSH, system packages

```bash
ssh duck@duck.local
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y git python3-pip python3-virtualenvwrapper python3-dev i2c-tools
```
- git, python3-pip, python3-virtualenvwrapper: [U README.md lines 35-43].
- python3-dev: headers to build RPi.GPIO 0.7.1 in step 7 (sdist only [I pypi.org RPi.GPIO]); gcc is already in the image [I bookworm .info: build-essential, gcc-12]. [L]
- i2c-tools: `i2cdetect` for step 4 [L].
- Optional camera: `sudo apt install -y python3-picamzero` [U README.md line 41] (not needed to walk).

Then add to the end of `~/.bashrc` [U README.md lines 45-51] and log in again:
```bash
export WORKON_HOME=$HOME/.virtualenvs
export PROJECT_HOME=$HOME/Devel
source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
```

## 3. Groups

```bash
id
sudo usermod -aG dialout,gpio,i2c duck    # only the ones missing from `id`; log out and in
```
The serial port, GPIO and I2C need these groups for a non-root user. Whether Imager's first user already has them: UNVERIFIED (check with `id`).

## 4. config.txt and raspi-config (I2C, serial, UART, audio)

```bash
sudo raspi-config nonint do_i2c 0          # I2C on: dtparam=i2c_arm=on, i2c-dev in /etc/modules
sudo raspi-config nonint do_serial_cons 1  # no login shell on the Pi UART
sudo raspi-config nonint do_serial_hw 1    # Pi UART off: enable_uart=0
sudo reboot
```
- I2C: [U README.md line 55]; what `do_i2c 0` writes: raspi-config bookworm branch aabbd96 (the 20250813 package in the image) lines 1315-1343 [I github.com/RPi-Distro/raspi-config]. The BNO055 hangs on GPIO2/GPIO3, pins 3 and 5 (WIRING.md section 3).
- Speed: keep the default 100 kHz (`i2c_arm_baudrate` default 100000 [I raspberrypi/linux rpi-6.12.y overlays README line 309]); the README's "TODO set 400KHz ?" was never done [U README.md line 57].
- Serial and UART: the servo bus is the USB adapter (/dev/ttyACM0), not the Pi UART (WIRING.md section 3: pins 8 and 10 unused). `do_serial_cons` and `do_serial_hw` behaviour: raspi-config bookworm lines 1383-1413 [I]. Leave Bluetooth on: the Xbox pad needs it (no `disable-bt` overlay).
- Audio (only if `"speaker": true` later): the README points to the Adafruit MAX98357A guide [U README.md lines 101-106]. In our wiring SD is not connected (WIRING.md section 3), so use `dtoverlay=max98357a,no-sdmode` in /boot/firmware/config.txt; without `no-sdmode` the overlay claims GPIO4 [I overlays README lines 3303-3309].
- Check after the reboot: `ls /dev/i2c-1` and, with the IMU wired, `i2cdetect -y 1` shows 28.

### 4b. Only if bench/imu_check.py finds glitches (TEST_PLAN 10.1)
Pi hardware I2C and the BNO055 clock stretching can corrupt reads (UPSTREAM_ISSUES.md G2, outside evidence). Move it to software I2C on the same pins, keeping bus number 1 so the Runtime's `busio.I2C(board.SCL, board.SDA)` still finds it (Blinka maps SCL/SDA to bus 1 [I Adafruit_Blinka bcm283x/pin.py `i2cPorts = ((1, SCL, SDA), ...)`]). In /boot/firmware/config.txt replace `dtparam=i2c_arm=on` with:
```
dtparam=i2c_arm=off
dtoverlay=i2c-gpio,bus=1,i2c_gpio_sda=2,i2c_gpio_scl=3,i2c_gpio_delay_us=2
```
[I overlays README lines 2215-2233: i2c-gpio params, `bus` sets /dev/i2c-<n>, delay 2 us = about 100 kHz]. Reboot and run imu_check.py again.

### 4c. V1 freeze (2026-11-06 ET): ear PWM and the new I2C parts (D51, D53, D54)
Ears on hardware PWM (D53). In /boot/firmware/config.txt:
```
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```
- GPIO12 is PWM0 and GPIO13 is PWM1 in alt function 0 (func=4); the overlay's default pins are 18 and 19, which are the I2S BCLK and LRCLK here, so the plain overlay would break the audio (expression study 4.4, from the raspberrypi/linux rpi-6.6.y overlays README, pwm-2chan). Keep the onboard analogue audio off: it uses both PWM channels (same README).
- Check: `ls /sys/class/pwm/pwmchip0` lists `export`, and `raspi-gpio get 12,13` (or `pinctrl get 12,13`) shows a0 PWM0 and PWM1.
- BLOCKER for the software: the Runtime's antennas.py drives GPIO12 and 13 through Blinka pwmio, which on a Pi Zero 2 W is RPi.GPIO software PWM (expression study, Blinka 9.2.0 pwmio.py line 25). With this overlay the pins belong to the PWM block, so antennas.py has to write the hardware channels (sysfs /sys/class/pwm/pwmchip0/pwm0 and pwm1, 20 ms period, 1.0 to 2.0 ms duty) instead. That is a Runtime change, and D6 keeps the Runtime unmodified: Ahmed's call (STATE.md open questions). Stop the pulses after each move so the analogue SG90 idles quietly (expression study 4.4).
I2C bus 1 after the freeze: `i2cdetect -y 1` shows 28 (BNO055), 29 (VL53L4CD cliff ToF), 5a (MPR121 head) and 5b (MPR121 body). The BNO055 ADR pin must stay low: at 0x29 it would clash with the ToF (perception study 3.1). The ToF interrupt is GPIO17 (pin 11), an input; polling the ToF every walk cycle is the default and the interrupt is optional.

## 5. Servo bus adapter and udev

Jumper on B (USB) [I Waveshare wiki "USB Control"], H1 screw terminal not connected (D15). Plug the adapter into the Pi data micro-USB port.
```bash
ls -l /dev/ttyACM0
udevadm info -q property -n /dev/ttyACM0 | grep -E 'ID_VENDOR_ID|ID_MODEL_ID|ID_USB_DRIVER'
```
Expect 1a86 / 55d3 / cdc_acm: the adapter's bridge is a CH343P [I Waveshare "Bus Servo Adapter (A)-Sch.pdf"], USB ID 1a86:55d3 [I WCHSoftGroup/ch343ser_linux driver/ch343.c line 2432], and CH343 chips work with the standard CDC-ACM driver as /dev/ttyACM* [I ch343ser_linux README]. Do not install WCH's own driver: it renames the port to /dev/ttyCH343USB0 [I same README] and the Runtime opens /dev/ttyACM0 [U rustypot_position_hwi.py line 9].
- The README's udev rule targets FTDI chips (`DRIVER=="ftdi_sio"`, latency_timer) [U README.md lines 59-67]: it never matches this adapter. Harmless; skip it. Its "udev rules for the motor control board" section is a TODO [U README.md lines 69-71].
- Optional fixed name, our rule: `sudo cp $LAB/software/99-odm-servo-bus.rules /etc/udev/rules.d/ && sudo udevadm control --reload && sudo udevadm trigger` gives /dev/odm_servo_bus (the Runtime keeps using /dev/ttyACM0).
- Rule from SOFTWARE.md section 3: one program holds the port at a time. rustypot opens it exclusively (TIOCEXCL), so `check_voltage.py` cannot run while the walk runs, unless as root.

## 6. Runtime at 376de65 (D6: unmodified)

```bash
mkvirtualenv -p python3 open-duck-mini-runtime          # README.md lines 113-116
workon open-duck-mini-runtime
cd ~ && git clone https://github.com/apirrone/Open_Duck_Mini_Runtime
cd Open_Duck_Mini_Runtime
git checkout 376de65435c93486347cd601a31aa96951799896  # README says `git checkout v2`; v2 is at this commit today
```
[U README.md lines 118-125]. The pin is the D6 rule; `git ls-remote` showed refs/heads/v2 = 376de65 on 2026-11-02 [L].

Then this lab's bench scripts (sparse: only the two lab folders plus the root files, which include the policy):
```bash
cd ~ && git clone --depth 1 --branch altaay-lab --filter=blob:none --sparse https://github.com/aaltaay/Open_Duck_Mini_v2.git open_duck_mini_v2
cd open_duck_mini_v2 && git sparse-checkout set altaay_lab/bench altaay_lab/software
```
(The fork is public, START_HERE.md. The branch name assumes this work is merged into altaay-lab: UNVERIFIED until the lead merges it.)

## 7. Python packages (pinned)

```bash
workon open-duck-mini-runtime
cd ~/Open_Duck_Mini_Runtime
pip install -c ~/open_duck_mini_v2/altaay_lab/software/constraints-bookworm.txt -e .
pip install -c ~/open_duck_mini_v2/altaay_lab/software/constraints-bookworm.txt RPi.GPIO==0.7.1
pip freeze | grep -E 'pypot|rustypot|onnxruntime|numpy|Blinka'
```
- `pip install -e .` is the README step [U README.md line 124]; setup.cfg pins rustypot 0.1.0, onnxruntime 1.18.1, numpy 1.26.4, adafruit-circuitpython-bno055 5.4.13, scipy 1.15.1, pygame 2.6.0, openai 1.70.0 and pypot from the support-feetech-sts3215 branch [U setup.cfg lines 18-26].
- The constraints file pins the rest from one resolve of that setup.cfg on Python 3.11 [L software/constraints-bookworm.txt]. Two choices in it: Adafruit-Blinka 9.2.0 and PlatformDetect 3.89.1. Blinka is not pinned upstream. Version 10.0 (2026-10-26) moved Pi GPIO to the `gpiod>=2.2.2` bindings, which it does not install [I Blinka 10.1.0 README lines 95-155]. 9.2.0 was current at the Runtime pin date and uses RPi.GPIO for digitalio and pwmio on this chip [I Blinka 9.2.0 wheel: bcm283x/pin.py line 7, pwmio.py line 25]. The README's Pi 5 note (`pip uninstall -y RPi.GPIO`) shows upstream venvs had RPi.GPIO [U README.md lines 127-132].
- pypot must show `@f6d305e70e1640f66188b256dfd1dcfeb8ab8a59` (branch head, 2025-06-16, the version all lab tests ran) [L]. If the branch moved: `pip install --no-deps --force-reinstall "pypot @ git+https://github.com/pollen-robotics/pypot@f6d305e70e1640f66188b256dfd1dcfeb8ab8a59"`.
- pypot pulls opencv-contrib-python (a large wheel) [U pypot setup.py]; the 32 GB card avoids Runtime issue #30 (UPSTREAM_ISSUES.md G11).

## 8. Policy file

The policy is BEST_WALK_ONNX_2.onnx [U README.md lines 174-178], at the root of the hardware repo (upstream commit 981750b, 2025-04-02; it came with the sparse clone in step 6):
```bash
cp ~/open_duck_mini_v2/BEST_WALK_ONNX_2.onnx ~/
sha256sum ~/BEST_WALK_ONNX_2.onnx   # 3c606f9381a1710cc8fecdb7442787dcbfce3ee9bc02a6f1224774ab2b3a1067 [L], 884177 bytes
```

## 9. duck_config.json

```bash
cp ~/open_duck_mini_v2/altaay_lab/software/duck_config.altaay.json ~/duck_config.json
```
The Runtime reads ~/duck_config.json [U README.md lines 153-159, duck_config.py line 12]. If the file is missing, it asks on stdin and exits [U duck_config.py lines 35-47]; in a service there is no stdin. Our file has the keys of example_config.json [U]. Differences: all expression features off for the first walks (eyes, projector, antennas, speaker are fitted; the antennas twitch, G15). `imu_upside_down: false` because the BNO055 sits flat with the chip up (MOUNTING.md); step 10 proves it. Offsets start at 0 and come from step 10.4.

## 10. Calibration and bench checks (TEST_PLAN.md order)

Every bench script: `--help`, PASS/FAIL summary with TEST_PLAN item numbers, JSON report in ~/odm_bench_logs. Run them with the venv active: `workon open-duck-mini-runtime; cd ~/open_duck_mini_v2/altaay_lab/bench`.

1. **Adapter and each servo, one at a time, servo alone on the bench supply** (TEST_PLAN 6, 7):
   `python first_servo_check.py --configure <ID> --fix-config` with the joint's ID from SOFTWARE.md section 2 (left 20 to 24, neck 30 to 33, right 10 to 14). It runs the Runtime's own scripts/configure_motor.py [U], then reads back registers 41, 44, 46, 84, 85, 86, firmware, P/D/I, and runs the speed test. `--fix-config` writes configure_motor.py's values again and reads them back if any were lost (SOFTWARE.md section 3). For the test-order servo (TO1) add `--thermal` with the 1.5 Nm rig (D2; read SOFTWARE.md section 5 first: 1.5 Nm is at the servo's own 2 A protection). Power-cycle once and run `--steps 7.1` to see register 85 still at 0.
   Fit each horn at the zero the configure step leaves (goal 0 [U configure_motor.py line 76]) (UPSTREAM_ISSUES.md G6).
2. **IMU**, robot still: `cd ~/Open_Duck_Mini_Runtime/scripts && python calibrate_imu.py` [U calibrate_imu.py line 5]. Run it from scripts/: it writes imu_calib_data.pkl to the current folder, and the walk loads it from scripts/ [U raw_imu.py lines 71, 76]. Then `python imu_check.py` (10.1, 1000 reads) and `python imu_check.py --tilt` (10.2). If 10.1 fails, do step 4b.
3. **Assembled robot on the bench supply**, torque off: `python power_log.py --idle --port /dev/ttyACM0 --seconds 10` (8.1: all 14 IDs, same firmware, register 85 = 0). The Runtime's `python ~/Open_Duck_Mini_Runtime/scripts/check_motors.py` moves joints one at a time if you want to see each [U check_motors.py].
4. **Offsets, hanging-robot rule (Runtime issue 32, UPSTREAM_ISSUES.md G6).** find_soft_offsets.py moves all 14 joints to zero at once, quickly [U find_soft_offsets.py lines 12-31]; on one build the head swung and broke a part. Before running it: the robot hangs on a stand with both feet off the ground; nothing is within reach of any leg or of the head (head yaw and pitch sweep); one hand is on the bench supply off switch. Then `cd ~/Open_Duck_Mini_Runtime/scripts && python find_soft_offsets.py` [U README.md lines 161-170]. Copy the printed offsets into ~/duck_config.json.
5. **Feet** (TEST_PLAN 12): `python feet_check.py --open` (hanging), `python feet_check.py --presses 200`, then on the floor `python feet_check.py --stand`. (TEST_PLAN 12 names scripts/fc_test.py: do not run it, it starts the walk and the OpenAI client, SOFTWARE.md section 2.)
6. **Hanging walk** (TEST_PLAN 8.4, bench supply 8 A limit): `python walk_with_guard.py --onnx_model_path ~/BEST_WALK_ONNX_2.onnx --no-commands --max-seconds 20 --dry-run`.
7. **Battery guard on the bench** (TEST_PLAN 11): bench supply at the XT30, robot hanging, torque off; `python battery_guard.py --monitor --state standing`, lower the supply in 0.1 V steps from 7.4 V and note the servo median at which walk_stop and hard_stop print; repeat with `--state walking`. This replaces the sim mapping in SOFTWARE.md section 5 with a measured one.
8. **Floor walk with the voltage log** (TEST_PLAN 9): pad paired (step 12); `python power_log.py --walk --pack full --pack-ocv <meter V> --onnx_model_path ~/BEST_WALK_ONNX_2.onnx` and again with `--pack nominal`. The log reads on its own timer, only in the walk loop's idle time (SOFTWARE.md section 6): its report gives the share of the walk it read (9.coverage) and any read that ran into the next control cycle (9.delay). If 9.time6 says INCOMPLETE for too few readings, log longer (`--seconds 120`).

## 11. Autostart

There is no autostart in a manual install. Start walks by hand over SSH until steps 10.6 to 10.8 pass. Then:
```bash
sudo visudo -f /etc/sudoers.d/odm-poweroff          # paste the line from software/odm-poweroff.sudoers
sudo cp ~/open_duck_mini_v2/altaay_lab/software/odm-walk-guard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable odm-walk-guard.service        # starts at the next boot
```
- The sudoers line lets the guard power off after a battery hard stop and nothing else (walk_with_guard.py `--poweroff-cmd` default `sudo -n /usr/bin/systemctl poweroff`) [L].
- The unit runs walk_with_guard.py --knee-heat with `Restart=no`, so a guard stop stays a stop. --knee-heat is the 55 C walk stop in software/knee_heat.py (SOFTWARE.md section 5). The image's unit uses `Restart=always` [U RELEASE_GUIDE.md lines 232-249]. It needs the pad: without one the Runtime's XBoxController raises before any motion [U xbox_controller.py line 30].
- On the 0.2.3 image: `sudo systemctl disable --now open-duck-walk.service` first. The hotspot fallback service can stay [U INSTALL.md lines 43-55].
- Stop a running walk: `sudo systemctl stop odm-walk-guard`. Note: like the upstream Ctrl-C, servos keep their last targets (SOFTWARE.md section 2).

## 12. Xbox pad (needed for the walk with commands)

```bash
bluetoothctl            # then: scan on / pair <MAC> / trust <MAC> / connect <MAC>
python ~/Open_Duck_Mini_Runtime/mini_bdx_runtime/mini_bdx_runtime/xbox_controller.py
```
[U README.md lines 74-99; INSTALL.md lines 101-118]. If the pad keeps dropping, add `Privacy = device` to /etc/bluetooth/main.conf (Mini issue #38, UPSTREAM_ISSUES.md G11). BOM.md has no pad line yet (G9). Buttons: A pause, X projector, B sound, LB sprint, Y head mode (README warns it can break the head) [U README.md lines 182-189].

## 13. Check the whole set-up

```bash
bash ~/open_duck_mini_v2/altaay_lab/software/check_pi_setup.sh
```
Read-only. It checks the OS, I2C, the UART, groups, the adapter, the pinned packages and the pypot commit, the imports, the Runtime commit and that its files are unmodified (D6), the duck config, the IMU calibration file, the policy checksum, the services and the sudoers line [L]. It exits 1 on any FAIL.
