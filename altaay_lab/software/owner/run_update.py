"""Apply a signed bundle, or run the desktop rollback demo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from altaay_lab.software.owner.update_flow import UpdateError, apply_update, demo_rollback  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description="Signed duck update")
    parser.add_argument("--state", default="")
    parser.add_argument("--bundle", default="")
    parser.add_argument("--public-key", default="")
    parser.add_argument("--demo-rollback", action="store_true")
    args = parser.parse_args(argv)
    if args.demo_rollback:
        result = demo_rollback()
        sys.stdout.write(result["text"])
        return 0 if result["rollback"]["rolled_back"] else 1
    if not args.state or not args.bundle:
        parser.error("--state and --bundle are required")
    try:
        result = apply_update(args.bundle, args.state, args.public_key or None)
    except UpdateError as exc:
        print("update refused: %s" % exc, file=sys.stderr)
        return 1
    if result["rolled_back"]:
        print("rolled back to %s" % result["version"])
        return 2
    print("now %s on slot %s" % (result["version"], result["slot"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
