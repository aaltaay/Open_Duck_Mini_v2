# Day one on the duck

Nothing here has run on a robot. The mock run is the one CI uses.

## Install

On the Pi, from a checkout of this repo:

```bash
bash altaay_lab/software/install_pi.sh
```

The script is idempotent. It clones the Runtime at 376de65 if that checkout is missing, copies the walk policy, leaves an existing duck_config.json in place, and installs the walk service, the poweroff sudoers line, the udev rule, and the ear PWM overlay. The service file is copied and not enabled, so the walk does not start at boot until PI_SETUP.md step 11. Personality, the dock, the knee-heat guard, and the battery guard stay in this repo. The script checks them, then runs software/check_pi_setup.sh on Bookworm.

A second run prints `unchanged` for files that already match and still prints the check.

The Runtime files are not edited (D6). The ear question for Ahmed is software/ANTENNAS_PWM.md.

Without a Pi:

```bash
bash altaay_lab/software/install_pi.sh --mock --prefix /tmp/odm-root
```

That fills the prefix and runs the same check. It does not call apt or clone.

## Bench

```bash
python3 altaay_lab/bench/day_one.py --mock --out /tmp/odm-dayone
```

The first lines say `hardware: mock hardware`. Each step prints PASS or FAIL and writes a JSON report under the output folder. Steps: bus, limits, voltage, camera, imu, eyes, antennas, speaker, mic, charge.

On the Pi, with the adapter on `/dev/ttyACM0` and a meter:

```bash
python3 altaay_lab/bench/day_one.py --port /dev/ttyACM0 --bec-volts 12.00 --rail-5v 5.00 --charge-ohm 1000000000
```

The servo rail pass band is 11.52 V to 12.48 V (netlist SERVO_12V0, 12.0 V plus or minus 4 percent). The 5 V rail pass band is 4.80 V to 5.20 V (netlist domain 5V). Angle limits are software/servo_limits.json `raw_soft` (label calc). A 7.2 V reading fails. That set point is superseded.

Camera frame rate, eye current, SG90 speed, mic latency, and pin-on-cloth ohms are BLOCKER. The script records them and does not invent a pass line.

## Tests

```bash
python3 -m unittest discover -s altaay_lab/software/tests -v
```
