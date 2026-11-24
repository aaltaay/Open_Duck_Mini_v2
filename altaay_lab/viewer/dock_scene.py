"""The wall and paddle dock viewer moved to the archive.

The scene to build is nest_scene.py. This file keeps the old import path.
"""
import importlib.util
import os

_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "archive", "wall_paddle_dock", "dock_scene.py"))
_spec = importlib.util.spec_from_file_location("dock_scene_archive", _PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

build = _mod.build
check_refs = _mod.check_refs
write = _mod.write
read_glb = _mod.read_glb
