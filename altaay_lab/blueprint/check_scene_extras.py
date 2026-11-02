#!/usr/bin/env python3
"""Check altaay_lab/viewer/scene_extras.json against the robot meshes: report every item whose box centre or more
than half of its 27 box sample points lie inside a printed or CAD part (zero pose). Read-only.
Usage: python3 altaay_lab/blueprint/check_scene_extras.py"""
import json
import os
import sys

sys.dont_write_bytecode = True
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from scene3d import Scene, LAB  # noqa: E402

EXPECTED = {  # item id prefix -> part keys the item may sit inside by design
    "microsd": {"raspberrypizerow"}, "horn-SG90": {"left_antenna_holder", "right_antenna_holder", "sg90"},
    "plug-": {"servo_bottom", "servo_mid"}, "msx-SV": {"servo_bottom", "servo_mid"}, "crimp-SV": {"servo_bottom", "servo_mid"},
    "fpc-D12-PI-CSI": {"raspberrypizerow"},              # FPC end inside the Pi CSI connector
    "kapton-BMS": {"bms", "body_back", "battery_pack_lid"},  # skin over the board in its sandwich slot
    "sj-BMS": {"bms"},                                  # upstream bms.stl body kept in the same slot (marked replaced)
    "sj-BNO": {"bno055"},                               # CAD board is 3.0 mm thick, the real PCB 1.6 mm
}


def main():
    s = Scene()
    items = json.load(open(os.path.join(LAB, "viewer", "scene_extras.json")))["items"]
    meshes = [(i, s.world_mesh(i)) for i in s.inst]
    bad = 0
    for it in items:
        c = np.array(it["center_mm"], float)
        R = np.array(it["rotation_3x3"], float)
        L, W, H = it["dims_local_mm"]
        g = np.array(np.meshgrid([-0.45, 0, 0.45], [-0.45, 0, 0.45], [-0.45, 0, 0.45])).reshape(3, -1).T
        pts = c + (g * np.array([W, H, L])) @ R.T
        hits = {}
        for i, m in meshes:
            if np.any(m.bounds[1] < pts.min(0)) or np.any(m.bounds[0] > pts.max(0)):
                continue
            ins = m.contains(pts) if m.is_watertight else np.zeros(len(pts), bool)
            if ins.any():
                hits[i["key"]] = int(ins.sum())
        ok_keys = next((v for k, v in EXPECTED.items() if it["id"].startswith(k)), set())
        worst = {k: v for k, v in hits.items() if k not in ok_keys}
        if worst and (max(worst.values()) > 13 or any(m.contains([c])[0] for i, m in meshes
                                                       if i["key"] in worst and m.is_watertight)):
            bad += 1
            print("%-28s inside %s" % (it["id"], worst))
    print("%d of %d items embedded in a part" % (bad, len(items)))


if __name__ == "__main__":
    main()
