"""First-boot page. --live is the Pi. Without it, nothing starts a radio."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from altaay_lab.software.owner import store, watchdog  # noqa: E402
from altaay_lab.software.owner.net import AP_ADDRESS, SETUP_PORT, LiveNet, MockNet  # noqa: E402
from altaay_lab.software.owner.setup_flow import AlreadySetup, SetupSession  # noqa: E402
from altaay_lab.software.owner.web import serve_setup  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description="Duck first-boot setup page")
    parser.add_argument("--state", required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--bind", default="")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args(argv)
    if store.load_owner(args.state):
        print("setup already saved")
        return 0
    net = LiveNet(args.state) if args.live else MockNet()
    session = SetupSession(args.state, net)
    try:
        session.begin()
    except AlreadySetup:
        print("setup already saved")
        return 0
    if args.live:
        host, port, loop = AP_ADDRESS, SETUP_PORT, False
    else:
        host, port, loop = (args.bind or "127.0.0.1"), args.port, True
    demo = bool(args.demo or not args.live)
    httpd = serve_setup(session, host, port, allow_loopback=loop, demo=demo)
    bound = httpd.server_address
    print("setup listening on %s:%s" % (bound[0], bound[1]), flush=True)
    print("pairing code %s" % session.code, flush=True)
    watchdog.notify("READY=1")
    try:
        while httpd.thread.is_alive():
            watchdog.notify("WATCHDOG=1")
            httpd.thread.join(5)
    finally:
        httpd.shutdown()
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
