#!/usr/bin/env python3
"""Run D training model: the current duck on altaay-lab.

- Mass: sim/mass_budget.py build_budget() links as they are now (2.949 kg loaded,
  the same rollup the twin checks). No extra 70 g cell: the budget already has
  three P45B cells, so the old train_sts12.py +70 g would double count.
- Actuator: train_sts12.actuators() at the servo volts of the held 12.0 V rail
  (BEC_HOLD=1, i7C), sheet no-load current, charge 0. Calc only.
- Knee high stop 147 deg (register soft stop), low stop unchanged.
usage: ODM_PLAYGROUND=<pg> python apply_runD.py <repo_root> <out_json>
"""
import json, math, os, sys
import numpy as np
REPO = sys.argv[1]; OUT = sys.argv[2]
LAB = os.path.join(REPO, "altaay_lab")
sys.path.insert(0, os.path.join(LAB, "problems"))
os.environ.setdefault("TWIN_EM_SCRATCH", "/tmp/twin_em_runD")
os.environ.setdefault("ODM_OUT", "/tmp/duck_mass_runD")
os.environ.setdefault("ODM_SCRATCH", "/tmp/duck_mass_scratch_runD")
import train_sts12 as T
import xml.etree.ElementTree as ETXML

sys.path.insert(0, os.path.join(LAB, "twin", "electromech"))
sys.path.insert(0, os.path.join(LAB, "sim"))
import power_net as PN
import sts12
net = PN.Net(corner="typical", extra=dict(BEC_V=12.0, BEC_HOLD=1), cell_model=sts12.Pack3S())
y = net.solve(lambda v: np.full(len(PN.NAMES), T.I_NOLOAD), qm=0.0)
volts = {n: float(v) for n, v in zip(PN.NAMES, net.servo_volts(y))}
act = T.actuators(volts, sts12)

import mass_budget as MB
B = MB.build_budget()
links = {}
for name, m in B["links"].items():
    I = m.I
    links[name] = dict(mass=float(m.m), pos=[float(x) for x in m.c],
                       fullinertia=[float(x) for x in (I[0, 0], I[1, 1], I[2, 2], I[0, 1], I[0, 2], I[1, 2])])
rollup = float(sum(it.mass_g for it in B["items"]) / 1000.0)
cfg = dict(actuator=act, mass=dict(links=links, trunk=dict(mass_after_kg=round(links["trunk_assembly"]["mass"], 4))))
KNEE_HI = math.radians(147.0)
pg = os.environ["ODM_PLAYGROUND"]
xmls = T.apply_config(cfg, pg)
for name in T.ROBOT_FILES:
    path = os.path.join(xmls, name)
    tree = ETXML.parse(path)
    for j in tree.getroot().iter("joint"):
        if j.get("name") in ("left_knee", "right_knee"):
            lo = float(j.get("range").split()[0])
            j.set("range", "%.10g %.10g" % (lo, KNEE_HI))
    tree.write(path)
got = T.check_applied(pg, cfg)
import mujoco
assets = {}
for fn in os.listdir(xmls):
    if fn.endswith(".xml"):
        assets[fn] = open(os.path.join(xmls, fn), "rb").read()
for fn in os.listdir(os.path.join(xmls, "assets")):
    assets[fn] = open(os.path.join(xmls, "assets", fn), "rb").read()
model = mujoco.MjModel.from_xml_string(open(os.path.join(xmls, "scene_flat_terrain_backlash.xml")).read(), assets=assets)
kr = model.jnt_range[model.joint("left_knee").id].tolist()
doc = dict(label="calc only for actuator and bus; CAD mass model for mass",
           servo_V=volts, training_vin_V=act["vin_V"], actuator=act,
           loaded_total_kg=round(float(model.body_mass.sum()), 4), rollup_kg=round(rollup, 4),
           trunk_kg=got["trunk_kg"], knee_range_rad=kr, knee_range_deg=[math.degrees(x) for x in kr], check=got)
json.dump(doc, open(OUT, "w"), indent=1)
print(json.dumps({k: v for k, v in doc.items() if k != "servo_V"}, indent=1))
