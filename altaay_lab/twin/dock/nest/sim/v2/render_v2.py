#!/usr/bin/env python3
"""render_v2.py: one clip of a 7.2 V run that fell at the mat edge with the old controller and docks with the new one.
Re-simulated from its seed with the v2 controller. sim pass only.
  MUJOCO_GL=egl PYTHONDONTWRITEBYTECODE=1 python3 render_v2.py [tag] [seed]    -> run_v2_pass.mp4, render_v2.json
640 x 480, 2 x real time (10 frames per simulated second, 20 fps). The camera follows the duck at 0.95 m (the old clips
used a fixed camera at 2.2 m), so the duck is about twice as large in the frame. The clip ends 1 s after torque off.
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
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import nest_run_v2 as R2  # noqa: E402

TXT = dict(init="start", approach="approach: steer to the line (floor)", stage="staging: stand, look, turn on the spot", cross="cross the mat edge: forward only, no turn",
           walk_on="on the mat: steer to the turn spot", fine="fine moves on the mat", turn="turn 180 deg", settle="stop and settle", sit="sit down, then torque off", rest="torque off, at rest")


def clip(cfg, path):
    frames, st = [], {}
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except Exception:
        font = ImageFont.load_default()

    def rec(s):
        if s.k % 5 or s.stage in ("walk_off_stand", "walk_off", "stand_up", "shuffle") or st.get("stop"):
            return
        if s.stage == "rest":
            st["rest"] = st.get("rest", 0) + 1
            if st["rest"] > 10:
                st["stop"] = True
        if "r" not in st:
            md = s.model
            md.geom_rgba[s.g_floor] = [0.70, 0.66, 0.58, 1]
            md.geom_rgba[s.g_mat] = [0.93, 0.86, 0.62, 1]
            md.geom_rgba[s.g_wall] = [0.86, 0.84, 0.80, 1]
            md.vis.headlight.diffuse[:] = 0.45
            md.vis.headlight.ambient[:] = 0.35
            st["r"] = mujoco.Renderer(md, 480, 640)
            cam = mujoco.MjvCamera()
            cam.distance, cam.azimuth, cam.elevation = 0.95, -35, -24
            st["cam"] = cam
            opt = mujoco.MjvOption()
            opt.geomgroup[:] = [1, 1, 1, 0, 0, 0]
            st["opt"] = opt
            st["look"] = np.array([s.trunk_pose()[0][0], s.trunk_pose()[0][1]])
        p = s.trunk_pose()[0]
        st["look"] += 0.15 * (p[:2] - st["look"])                      # the camera follows the duck, smoothed
        st["cam"].lookat[:] = [st["look"][0] + 0.05, st["look"][1], 0.09]
        st["r"].update_scene(s.data, st["cam"], st["opt"])
        im = Image.fromarray(st["r"].render())
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 640, 30], fill=(252, 252, 251))
        d.text((8, 5), "%4.1f s   %s" % (s.t, TXT.get(s.stage, s.stage)), fill=(11, 11, 11), font=font)
        frames.append(np.asarray(im).copy())
    out = R2.Run2(dict(cfg, record=rec, trace=False)).go()
    w = imageio.get_writer(path, fps=20, codec="libx264", quality=None, pixelformat="yuv420p", output_params=["-crf", "23"], macro_block_size=None)
    for f in frames:
        w.append_data(f)
    w.close()
    return dict(file=os.path.basename(path), cfg={k: v for k, v in cfg.items() if k != "record"}, frames=len(frames), sits_ok=[s["nest"]["ok"] for s in out["sits"]], fell=out["fell"],
                fall_stage=out["fall_stage"], sim_seconds_to_first_sit=out.get("t_first_sit_s"), size_MB=round(os.path.getsize(path) / 1e6, 2), frame_px=[640, 480],
                camera="follows the duck at 0.95 m (old clips: fixed at 2.2 m, 480 x 360)")


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "v2"
    old = {r["cfg"]["seed"]: r for r in json.load(open(os.path.join(R2.L.PARENT, "nest_runs_main.json")))["runs"]}
    new = [r for r in json.load(open(os.path.join(HERE, "nest_runs_%s.json" % tag)))["runs"] if "error" not in r]
    cand = [r for r in new if old[r["cfg"]["seed"]].get("fell") and old[r["cfg"]["seed"]]["fall_stage"] == "walk_on" and r["cfg"]["volt"] == 7.2 and not r["fell"]
            and r.get("sits") and len(r["sits"]) == 1 and r["sits"][0]["nest"]["strict"]]
    if len(sys.argv) > 2:
        cand = [r for r in cand if r["cfg"]["seed"] == int(sys.argv[2])]
    cand.sort(key=lambda r: r["t_first_sit_s"])
    r = cand[0]
    o = old[r["cfg"]["seed"]]
    meta = clip(r["cfg"], os.path.join(HERE, "run_v2_pass.mp4"))
    meta["old_controller_same_seed"] = dict(fell=o["fell"], fall_stage=o["fall_stage"], fall_t_s=o["fall_t"])
    meta["same_as_matrix_run"] = bool(meta["sits_ok"] == [s["nest"]["ok"] for s in r["sits"]] and not meta["fell"])
    print(meta)
    json.dump(dict(label="sim pass only", clip=meta), open(os.path.join(HERE, "render_v2.json"), "w"), indent=1)
