"""Shared helpers for the V1 holes job (track 2e). CAD check only, calc only.

The scene is the lab scene of altaay_lab/fasteners/fastlib.py (robot.urdf at zero joint angles, print/ STLs swapped in,
head internals on the head.stl transform), loaded READ ONLY from a scratch worktree of the duck repo at 0b1cab5
(REPO below, found from this file; ODM_REPO overrides). Outputs and heavy caches go to OUT (ODM_HOLES_OUT, default ~/v1_out/holes, outside the repo).
"""
import json, os, sys, pickle
import numpy as np

REPO = os.environ.get("ODM_REPO", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
LAB = os.path.join(REPO, "altaay_lab")
OUT = os.environ.get("ODM_HOLES_OUT", os.path.join(os.path.expanduser("~"), "v1_out", "holes"))
SCENE = os.path.join(OUT, "scene")
DATA = os.path.join(OUT, "data")
sys.path.insert(0, os.path.join(LAB, "fasteners"))
os.makedirs(DATA, exist_ok=True)

CUT_STATUS = ("LEAVE OUT (D38 screw cut)", "LEAVE OUT (D18)", "NOT FITTED")


def fitted(x):
    """fasteners.json row fitted today (same rule as twin/screws/screws_twin.py)"""
    return x.get("status") not in ("NOT FITTED", "LEAVE OUT (D18)") and not x.get("leave_out")


def load_fj():
    return json.load(open(os.path.join(LAB, "fasteners", "fasteners.json")))


def scene():
    from fastlib import Scene
    return Scene(SCENE)


def sites_cached(S):
    fn = os.path.join(SCENE, "sites.pkl")
    if os.path.exists(fn):
        return pickle.load(open(fn, "rb"))
    sites, W = S.sites()
    pickle.dump((sites, W), open(fn, "wb"))
    return sites, W


def basis(a):
    a = np.asarray(a, float); a = a / np.linalg.norm(a)
    t = np.array([0, 0, 1.0]) if abs(a[2]) < 0.9 else np.array([1.0, 0, 0])
    u = np.cross(a, t); u /= np.linalg.norm(u)
    return a, u, np.cross(a, u)


def jdump(obj, name):
    def ser(v):
        if isinstance(v, np.ndarray):
            return v.tolist()
        if isinstance(v, (np.floating,)):
            return float(v)
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, (np.bool_,)):
            return bool(v)
        raise TypeError(type(v))
    json.dump(obj, open(os.path.join(DATA, name), "w"), indent=1, default=ser)
