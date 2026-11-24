"""systemd entry for walk, supervisor, voice, and perception."""

from __future__ import annotations

import argparse
import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from altaay_lab.software.owner.service import install_stop, serve, serve_walk  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description="Duck owner service")
    parser.add_argument("--role", required=True, choices=("walk", "supervisor", "voice", "perception"))
    parser.add_argument("--state", required=True)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--home", default=os.environ.get("ODM_HOME", "/home/duck"))
    args = parser.parse_args(argv)
    stop = threading.Event()
    install_stop(stop)
    if args.role == "walk" and not args.mock:
        return serve_walk(args.state, args.home, stop)
    return serve(args.role, args.state, stop)


if __name__ == "__main__":
    raise SystemExit(main())
