"""systemd notify, without libsystemd.

WatchdogSec is a set point on the unit files (15 s, 30 s on first-boot setup).
If NOTIFY_SOCKET is unset, the calls do nothing so a desktop demo can run.
"""

from __future__ import annotations

import os
import socket


def notify(message):
    addr = os.environ.get("NOTIFY_SOCKET")
    if not addr:
        return False
    if addr.startswith("@"):
        addr = "\0" + addr[1:]
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        sock.sendto(str(message).encode("utf-8"), addr)
    finally:
        sock.close()
    return True
