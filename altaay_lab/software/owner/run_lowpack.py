"""Watch the supervisor log and shut down on a low pack.

--apply really calls systemctl, and only when --state is /var/lib/odm.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from altaay_lab.software.owner import watchdog  # noqa: E402
from altaay_lab.software.owner.lowpack import apply_allowed, consider  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description="Low-pack shutdown")
    parser.add_argument("--state", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    if args.apply and not apply_allowed(args.state):
        print("refusing to power off: state is not the duck directory", file=sys.stderr)
        return 2

    def runner(cmd):
        if args.apply:
            subprocess.run(cmd, check=False, timeout=30)

    watchdog.notify("READY=1")
    while True:
        consider(args.state, runner)
        if args.once:
            return 0
        watchdog.notify("WATCHDOG=1")
        time.sleep(5)


if __name__ == "__main__":
    raise SystemExit(main())
