"""Copied into the venv as sitecustomize.py by software/install_pi.sh.

It does nothing unless ODM_HW_PWM=1. The Runtime tree is not modified.
"""

import os
import sys

if os.environ.get("ODM_HW_PWM") == "1":
    root = os.environ.get("ODM_LAB_SOFTWARE", "")
    if root and root not in sys.path:
        sys.path.insert(0, root)
    import hw_pwm

    hw_pwm.install_import_hook(os.environ.get("ODM_PWM_CHIP"))
