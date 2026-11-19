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

# One core for the walk policy. The Runtime file is not edited. The cap
# applies only when the service sets ODM_ORT_THREADS.
_threads = os.environ.get("ODM_ORT_THREADS", "").strip()
if _threads:
    _n = int(_threads)

    class _OrtCap:
        def find_module(self, fullname, path=None):
            if fullname == "onnxruntime":
                return self
            return None

        def load_module(self, fullname):
            self.find_module = lambda *args, **kwargs: None
            if self in sys.meta_path:
                sys.meta_path.remove(self)
            import importlib

            module = importlib.import_module(fullname)
            original = module.InferenceSession

            class _Session(original):
                def __init__(self, *args, **kwargs):
                    options = kwargs.get("sess_options")
                    if options is None:
                        options = module.SessionOptions()
                        kwargs["sess_options"] = options
                    options.intra_op_num_threads = _n
                    options.inter_op_num_threads = 1
                    super().__init__(*args, **kwargs)

            module.InferenceSession = _Session
            sys.modules[fullname] = module
            return module

    sys.meta_path.insert(0, _OrtCap())
