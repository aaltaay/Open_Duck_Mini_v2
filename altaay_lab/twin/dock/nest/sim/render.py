#!/usr/bin/env python3
"""render.py: short clips of one good run and one failed run, re-simulated from their seeds. sim pass only.
  MUJOCO_GL=egl PYTHONDONTWRITEBYTECODE=1 python3 render.py [tag]     -> run_good.mp4, run_failed.mp4 (each under 5 MB)
The clip plays 2 x faster than real time (10 frames per simulated second, 20 fps playback), 480 x 360.
"""
import json
import os
import sys

os.environ.setdefault("MUJOCO_GL", "egl")
import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import imageio  # noqa: E402
import mujoco  # noqa: E402
import nest_run as NR  # noqa: E402


def clip(cfg, path, label):
    frames = []
    st = {}

    def rec(s):
        if s.k % 5:
            return
        if "r" not in st:
            md = s.model                       # colours for the clip only
            md.geom_rgba[s.g_floor] = [0.70, 0.66, 0.58, 1]
            md.geom_rgba[s.g_mat] = [0.93, 0.86, 0.62, 1]
            md.geom_rgba[s.g_wall] = [0.86, 0.84, 0.80, 1]
            md.vis.headlight.diffuse[:] = 0.45
            md.vis.headlight.ambient[:] = 0.35
            st["r"] = mujoco.Renderer(md, 360, 480)
            cam = mujoco.MjvCamera()
            cam.lookat[:] = [-0.35, 0.0, 0.08]
            cam.distance, cam.azimuth, cam.elevation = 2.2, -30, -28
            st["cam"] = cam
            opt = mujoco.MjvOption()
            opt.geomgroup[:] = [1, 1, 1, 0, 0, 0]
            st["opt"] = opt
        st["r"].update_scene(s.data, st["cam"], st["opt"])
        frames.append(st["r"].render().copy())
    cfg = dict(cfg, record=rec, trace=False)
    out = NR.Run(cfg).go()
    w = imageio.get_writer(path, fps=20, codec="libx264", quality=None, pixelformat="yuv420p", output_params=["-crf", "24"], macro_block_size=None)
    for f in frames:
        w.append_data(f)
    w.close()
    print(label, path, len(frames), "frames", "%.2f MB" % (os.path.getsize(path) / 1e6), "sits", [s["nest"]["ok"] for s in out["sits"]], "fell", out["fell"], out["fall_stage"])
    return dict(file=os.path.basename(path), cfg={k: v for k, v in cfg.items() if k not in ("record",)}, sits_ok=[s["nest"]["ok"] for s in out["sits"]], fell=out["fell"],
                fall_stage=out["fall_stage"], sim_seconds=out["t_total_s"], size_MB=round(os.path.getsize(path) / 1e6, 2))


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "main"
    R = [r for r in json.load(open(os.path.join(HERE, "nest_runs_%s.json" % tag)))["runs"] if "error" not in r]
    good = [r for r in R if r["sits"] and r["sits"][0]["nest"]["strict"] and not r["fell"] and len(r["sits"]) == 1 and r["cfg"]["noise"] == "mid"]
    bad = [r for r in R if r["fell"] and r["fall_stage"] not in ("walk_off", "walk_off_stand")] or \
          [r for r in R if r["sits"] and not any(s["nest"]["ok"] for s in r["sits"])] or [r for r in R if r["sits"] and not r["sits"][0]["nest"]["ok"]]
    meta = {}
    if good:
        good.sort(key=lambda r: r["t_total_s"])
        meta["good"] = clip(good[0]["cfg"], os.path.join(HERE, "run_good.mp4"), "good")
    if bad:
        bad.sort(key=lambda r: r["t_total_s"])
        meta["failed"] = clip(bad[0]["cfg"], os.path.join(HERE, "run_failed.mp4"), "failed")
    json.dump(dict(label="sim pass only", clips=meta), open(os.path.join(HERE, "render.json"), "w"), indent=1)
