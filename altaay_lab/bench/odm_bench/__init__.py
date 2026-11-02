"""Shared helpers for the Altaay lab bench scripts (altaay_lab/bench/*.py).

Every script talks to the hardware through the same libraries and calls the Runtime uses
(Open_Duck_Mini_Runtime 376de65): pypot FeetechSTS3215IO for single-servo and register work
(scripts/configure_motor.py, check_voltage.py), rustypot through the Runtime HWI for the walk
loop (mini_bdx_runtime/rustypot_position_hwi.py), Adafruit Blinka and adafruit_bno055 for
the feet and the IMU (feet_contacts.py, raw_imu.py). Nothing here edits a Runtime file.
"""
