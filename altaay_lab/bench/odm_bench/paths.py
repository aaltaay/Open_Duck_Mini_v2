"""Where things are: this repo, the Runtime checkout, the log folder.

Paths are relative to this file, so the scripts run from any working directory. The Runtime is
found from --runtime, then ODM_RUNTIME_DIR, then ~/Open_Duck_Mini_Runtime (the Pi layout in
software/PI_SETUP.md), then /home/user/upstream/Open_Duck_Mini_Runtime (lab container).
Logs go to --out, then ODM_BENCH_OUT, then ~/odm_bench_logs.
"""
import os
import sys
import time
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parents[1]
LAB_DIR = BENCH_DIR.parent
REPO_DIR = LAB_DIR.parent

RUNTIME_PIN = "376de65435c93486347cd601a31aa96951799896"   # D6, README.md upstream pins
_CANDIDATES = ("~/Open_Duck_Mini_Runtime", "/home/user/upstream/Open_Duck_Mini_Runtime")


def find_runtime(explicit=None):
    """Return the Runtime checkout folder (the one holding mini_bdx_runtime/ and scripts/)."""
    for c in (explicit, os.environ.get("ODM_RUNTIME_DIR")) + _CANDIDATES:
        if not c:
            continue
        p = Path(c).expanduser()
        if (p / "mini_bdx_runtime" / "mini_bdx_runtime").is_dir() and (p / "scripts").is_dir():
            return p.resolve()
    raise SystemExit("Runtime checkout not found. Pass --runtime or set ODM_RUNTIME_DIR "
                     "(software/PI_SETUP.md step 6 clones it to ~/Open_Duck_Mini_Runtime).")


def use_runtime(runtime_dir):
    """Make the Runtime importable the same way the image launcher does.

    The 0.2.3 launcher puts $PROJECT_DIR/mini_bdx_runtime first on PYTHONPATH and runs the walk
    from scripts/ (docs/RELEASE_GUIDE.md lines 162 to 167). We add scripts/ too, so
    v2_rl_walk_mujoco.RLWalk can be imported. No .pyc is written into the checkout.
    """
    sys.dont_write_bytecode = True
    rt = Path(runtime_dir)
    for p in (rt / "scripts", rt / "mini_bdx_runtime"):
        s = str(p)
        if s in sys.path:
            sys.path.remove(s)
        sys.path.insert(0, s)
    return rt


def runtime_commit(runtime_dir):
    """Read the checked-out commit without running git (detached HEAD or a branch ref)."""
    git = Path(runtime_dir) / ".git"
    try:
        head = (git / "HEAD").read_text().strip()
    except OSError:
        return None
    if not head.startswith("ref:"):
        return head
    ref = head.split(None, 1)[1]
    f = git / ref
    if f.exists():
        return f.read_text().strip()
    packed = git / "packed-refs"
    if packed.exists():
        for line in packed.read_text().splitlines():
            if line.endswith(" " + ref):
                return line.split()[0]
    return None


def out_dir(explicit=None, sub=None):
    base = Path(explicit or os.environ.get("ODM_BENCH_OUT") or "~/odm_bench_logs").expanduser()
    d = base / sub if sub else base
    d.mkdir(parents=True, exist_ok=True)
    return d


def stamp():
    return time.strftime("%Y%m%d_%H%M%S")
