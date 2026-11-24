# Owner setup, updates, and the home page

Nothing here has run on a robot. The desktop pages are a demo, not the duck.
The Runtime is not edited (D6). antennas.py is not edited. The ear PWM overlay
stays the environment variable on the walk unit.

## What the owner does

1. The setup service speaks an 8 character pairing code (set point). There is
   no factory password and no cloud account.
2. The temporary network name starts with Duckie-. Its passphrase is that code.
   The page is at 192.168.4.1 (set point) and only answers that temporary network.
3. The page asks for the code, a name, a timezone, kid mode, and the home Wi-Fi.
   Kid mode is the default. Only the word adult turns it off.
4. Saving closes the temporary network and joins the home Wi-Fi. The passphrase
   is stored in a root-only file. It is not placed on a command line.
5. The status service listens on port 8080 (set point) and only answers a
   device on the home network. It asks for the pairing code again. It shows
   battery, last docks, falls, and knee temperature from the supervisor log,
   and it can download that log. It does not invent a voltage.

The camera stays on the duck. Frames are not uploaded. The microphone stays
on the duck. Audio is not uploaded.

A pack-voltage sensor on the Pi is BLOCKER. A light on the body that shows
the camera is on is BLOCKER.

## Updates

Bundles are tar files. manifest.json is signed with Ed25519. openssl checks
the signature against software/owner/update_public_key.pem. A private key is
not in this repository. Tests mint a key in a temporary directory and delete it.

Two slots, a and b. After the pointer moves, the walk guards and one supervisor
step run. If either fails, the pointer moves back. That rollback is measured
in emulation. Never done on hardware.

The public key in the tree has no private half stored here. A production key
a maintainer can sign with is BLOCKER until that private half is created
offline and this public file is replaced with its pair.

## Services

systemd units, copied by install_pi.sh and not enabled:

| Unit | Job |
|---|---|
| odm-setup.service | First boot. Watchdog 30 s (set point). |
| odm-status.service | Home page. Watchdog 15 s (set point). |
| odm-supervisor.service | Supervisor role. Watchdog 15 s. Restart limit 3 in 300 s (set points). |
| odm-voice.service | Voice role. Same watchdog and restart limit. |
| odm-perception.service | Camera role. Same watchdog and restart limit. |
| odm-walk.service | Walk wrapper. Same watchdog and restart limit. Guard exits are not restarted. |
| odm-lowpack.service | Powers off at or under 10.0 V (cited). |
| odm-walk-guard.service | The older unit. Restart=no, unchanged. Do not enable it together with odm-walk.service. |

The low-pack path stops walk, perception, voice, then the supervisor, then
powers off. It does not power off while the log says the duck is charging.
It does not power off when the log has no voltage. --apply is refused unless
the state directory is the duck's /var/lib/odm, so a test cannot power the
machine off.

## Tests

```bash
python3 -m unittest discover -s altaay_lab/software/owner/tests -q
```

The rollback demo, which is not the robot:

```bash
python3 -m altaay_lab.software.owner.run_update --demo-rollback
```
