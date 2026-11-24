"""Home-network status page. Refuses any peer that is not on a home network."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from altaay_lab.software.owner import store, watchdog  # noqa: E402
from altaay_lab.software.owner.net import STATUS_PORT  # noqa: E402
from altaay_lab.software.owner.peers import choose_status_bind  # noqa: E402
from altaay_lab.software.owner.web import serve_status  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description="Duck home status page")
    parser.add_argument("--state", required=True)
    parser.add_argument("--bind", default="")
    parser.add_argument("--lan", action="store_true")
    parser.add_argument("--port", type=int, default=STATUS_PORT)
    parser.add_argument("--allow-loopback", action="store_true")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args(argv)
    if store.load_owner(args.state) is None:
        print("setup is not finished")
        return 0
    host = choose_status_bind(args.bind, args.lan)
    if args.lan and not host:
        print("no home network address yet", file=sys.stderr)
        return 1
    if not host:
        host = "127.0.0.1"
    loop = bool(args.allow_loopback or args.demo or host == "127.0.0.1")
    httpd = serve_status(args.state, host, args.port, allow_loopback=loop, demo=args.demo or loop)
    bound = httpd.server_address
    print("status listening on %s:%s" % (bound[0], bound[1]), flush=True)
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
