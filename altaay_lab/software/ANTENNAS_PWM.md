# Ear PWM: overlay, and a question for Ahmed

STATE.md open question 10 (asked 2026-11-06, D53): the ears on hardware PWM need the Runtime file antennas.py to write the PWM channels instead of Blinka software PWM. D6 keeps the Runtime unmodified. This note does not change that file.

## What is already wired

The netlist puts the right ear on GPIO12 (PWM0) and the left ear on GPIO13 (PWM1). The domain PWM_3V3 says 50 Hz, 1 to 2 ms. PI_SETUP.md step 4c adds:

```
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

antennas.py at commit 376de65 already does this arithmetic: pulse = 1.5 ms + 0.5 ms * command, clamped to the 16-bit duties 3277 and 6553, on GPIO13 (left, sign +1) and GPIO12 (right, sign -1). Those two constants are that file's 1 ms and 2 ms ends. On a 20 ms period they land at 1000076 ns and 1999847 ns (calc only: duty times 20000000, integer-divided by 65535). Both sit inside 1 ms to 2 ms. The command is -1 to 1 (software/personality/limits.py).

## What this overlay does

software/hw_pwm.py writes `/sys/class/pwm/pwmchip0` (or `ODM_PWM_CHIP` in a test). It uses that same duty formula. `deinit` writes enable 0 so the pulse stops after a move (PI_SETUP.md 4c).

software/hw_pwm_sitecustomize.py is copied into the venv by software/install_pi.sh. It wraps `import pwmio` only when `ODM_HW_PWM=1`. The installed walk unit gets that variable. The copy of odm-walk-guard.service in the repo does not, so copying the unit by hand does not turn the overlay on.

The bench day-one antenna step uses hw_pwm.py directly. It does not import the Runtime.

## Question for Ahmed

OK to leave the ears on this overlay, with antennas.py still the Blinka version, until you say the one Runtime file may change?

Until that answer, the walk uses hardware PWM only when the installed unit sets `ODM_HW_PWM=1`. The file antennas.py stays the upstream file. Nothing in the Runtime checkout is written.

## Not a servo joint

The ears are the stock SG90 PWM parts (BOM line 14, GAPS.md B10a). They are not the 14 bus joints. Pulse width stays inside the antennas.py clamp. No other pulse width is commanded.
