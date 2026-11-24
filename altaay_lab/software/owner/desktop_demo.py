"""Desktop demo of the setup page and the status page. Not the robot.

Binds loopback only. Prints the URLs and the pairing codes. Leaves the
processes up until you stop them.
"""

from __future__ import annotations

import os
import signal
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from altaay_lab.software.owner import store  # noqa: E402
from altaay_lab.software.owner.net import MockNet  # noqa: E402
from altaay_lab.software.owner.setup_flow import SetupSession  # noqa: E402
from altaay_lab.software.owner.web import serve_setup, serve_status  # noqa: E402

LOG = "\n".join([
    '{"t": 12.0, "kind": "dock_attempt", "mode": "dock", "pack_v": 11.20, "knee_c": 31.00}',
    '{"t": 40.0, "kind": "dock_result", "mode": "charge", "pack_v": 11.15, "knee_c": 31.50, "ok": true}',
    '{"t": 90.0, "kind": "fall", "mode": "getup", "pack_v": 10.90, "knee_c": 36.25, "falls": 1}',
    '{"t": 120.0, "mode": "wander", "pack_v": 10.86, "knee_c": 34.50, "falls": 1}',
    "",
])


def main(argv=None):
    del argv
    root = tempfile.mkdtemp(prefix="odm-desktop-demo-")
    setup_state = os.path.join(root, "setup")
    home_state = os.path.join(root, "home")
    os.makedirs(setup_state)
    os.makedirs(home_state)
    setup = SetupSession(setup_state, MockNet())
    setup_code = setup.begin()
    home = SetupSession(home_state, MockNet())
    home_code = home.begin()
    home.submit({
        "pairing_code": home_code,
        "name": "Duckie",
        "timezone": "UTC",
        "kid_mode": "kid",
        "home_ssid": "DemoNet",
        "home_open": "yes",
    })
    store.write_text(store.log_path(home_state), LOG, 0o644)
    setup_http = serve_setup(setup, "127.0.0.1", 0, allow_loopback=True, demo=True)
    status_http = serve_status(home_state, "127.0.0.1", 0, allow_loopback=True, demo=True)
    setup_port = setup_http.server_address[1]
    status_port = status_http.server_address[1]
    print("Desktop demo, not the robot.", flush=True)
    print("setup http://127.0.0.1:%s pairing %s" % (setup_port, setup_code), flush=True)
    print("status http://127.0.0.1:%s pairing %s" % (status_port, home_code), flush=True)
    print("log values are a demo log, not a measurement", flush=True)

    def stop(signum, frame):
        del signum, frame
        setup_http.shutdown()
        status_http.shutdown()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    setup_http.thread.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
