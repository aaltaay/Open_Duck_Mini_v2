"""The dock checks fail closed (pytest): a check that cannot run is a failure, never a pass.
Run: python3 -m pytest -q altaay_lab/twin/dock/test_dock_checks.py
"""
import os, sys
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "verify"))
import dock_assembly as DA  # noqa: E402
import c12_dock  # noqa: E402


def test_interference_boolean_error_is_unchecked_and_fails_c12(monkeypatch):
    a = trimesh.creation.box(extents=(10, 10, 10)); b = trimesh.creation.box(extents=(10, 10, 10)); b.apply_translation((5, 0, 0))
    def boom(self, *k, **kw):
        raise RuntimeError("backend down")
    monkeypatch.setattr(trimesh.Trimesh, "intersection", boom)
    out = DA.interferences({"part_a": a, "part_b": b})
    assert out and out[0]["status"] == "UNCHECKED"
    A = {"dock": {"interferences": out}, "docked": {"interferences": []}, "motion": []}
    hits, mot = c12_dock.assembly_fail(A)
    assert hits, "C12 must fail on an UNCHECKED pair"


def test_seating_missing_host_is_unchecked(monkeypatch):
    real = DA.components
    monkeypatch.setattr(DA, "components", lambda state="dock": [c for c in real(state) if c["id"] != "dock_spine"])
    bad = DA.fastener_seating("dock")
    assert any("UNCHECKED" in str(x[2]) for x in bad)
