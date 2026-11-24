"""One camera frame on a Pi 5, through libcamera and picamera2.

The Pi 5 camera connectors are 22-pin MIPI. Camera Module 3 stays the
15-pin module, on an adapter cable. This capture is the day-one check.
Mock mode does not call it.
"""

from __future__ import annotations


def capture_frame():
    """Return JPEG bytes, or None when picamera2 is not installed."""
    try:
        from picamera2 import Picamera2
    except ImportError:
        return None
    camera = Picamera2()
    try:
        camera.configure(camera.create_still_configuration())
        camera.start()
        data = camera.capture_buffer("main")
    finally:
        camera.close()
    if data is None:
        return None
    return bytes(data)
