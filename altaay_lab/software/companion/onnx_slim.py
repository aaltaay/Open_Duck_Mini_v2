"""Turn off ONNX Runtime's CPU memory arena before a speech model loads.

software/companion/LATENCY.md records the resident size with and without
this switch. The switch is a set point so the voice process stays closer
to the 512 MB board. It does not change the model.
"""

from __future__ import annotations


def install():
    import onnxruntime as ort

    if getattr(ort, "_odm_slim", False):
        return
    original = ort.InferenceSession

    class SlimSession(original):
        def __init__(self, *args, **kwargs):
            options = kwargs.get("sess_options")
            if options is None:
                options = ort.SessionOptions()
                kwargs["sess_options"] = options
            options.enable_cpu_mem_arena = False
            options.enable_mem_pattern = False
            super().__init__(*args, **kwargs)

    ort.InferenceSession = SlimSession
    ort._odm_slim = True
