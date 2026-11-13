#!/usr/bin/env python3
"""Training config for the 12 V STS3215 on a 3S pack, applied to the existing playground runner.

The trainer is Open_Duck_Playground at b9be205, playground/open_duck_mini_v2/runner.py.
This file does not replace it. It writes the actuator, the bus voltage, and the trunk
mass into the playground MJCF, then the runner trains as it always has.

The playground step has no supply voltage. The training torque is the 12 V sheet stall
scaled by the servo voltage from the existing 3S bus at the sheet no-load current.
Damping stays the mechanical damping that puts the no-load speed on the 12 V sheet.
The extra 70 g is the third P45B, added to the build trunk the sheet walk already uses.

  python3 altaay_lab/problems/train_sts12.py --write
  ODM_PLAYGROUND=<Open_Duck_Playground at b9be205> python3 altaay_lab/problems/train_sts12.py --apply
  ODM_PLAYGROUND=<Open_Duck_Playground at b9be205> python3 altaay_lab/problems/train_sts12.py --smoke

--write rebuilds the config from the sheet, the bus solver, and the mass budget.
--apply patches the playground checkout. --smoke is 8 envs and 480 steps, not a gait.
"""
import argparse
import json
import os
import sys
import xml.etree.ElementTree as ETXML

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LAB = os.path.abspath(os.path.join(HERE, ".."))
CFG_PATH = os.path.join(HERE, "train_sts12.json")
PIN = "b9be205ac64488c23504ca42e5ec790337adeec3"
ROBOT_FILES = ("open_duck_mini_v2.xml", "open_duck_mini_v2_backlash.xml")
# kp on the pin, plain scene and backlash scene. The sheet walk uses the backlash scene.
KP_PIN = {"open_duck_mini_v2.xml": 13.37, "open_duck_mini_v2_backlash.xml": 17.11}
DAMP_PIN, FRICT_PIN, TAU_PIN = 0.56, 0.068, 3.23
CELL_KG = 0.070
# Rear cell axis, trunk frame, metres. Same seat as problems/sts12_mass.py.
CELL_M = np.array([-0.15251, 0.001425, 0.0315])
# Feetech product page for ST-3215-C018, read 2026-11-12: no-load current 180 mA at 12 V.
I_NOLOAD = 0.180


def bus_voltage():
    """Servo volts on the 3S bus at the sheet no-load current. Calc only."""
    sys.path.insert(0, os.path.join(LAB, "twin", "electromech"))
    sys.path.insert(0, os.path.join(LAB, "sim"))
    os.environ.setdefault("TWIN_EM_SCRATCH", os.path.join(__import__("tempfile").gettempdir(), "twin_em"))
    import power_net as PN  # noqa: E402
    import sts12  # noqa: E402

    net = PN.Net(corner="typical", extra=dict(BEC_V=16.0), cell_model=sts12.Pack3S())
    y = net.solve(lambda v: np.full(len(PN.NAMES), I_NOLOAD), qm=0.0)
    volts = {n: float(v) for n, v in zip(PN.NAMES, net.servo_volts(y))}
    return volts, sts12


def actuators(volts, sts12):
    vin = min(volts.values())
    scale = sts12.TAU_12 / TAU_PIN
    speed_k = sts12.SPEED_K
    damp = DAMP_PIN * scale * speed_k
    frict = FRICT_PIN * scale * speed_k
    force = sts12.TAU_12 * vin / sts12.V_12
    w0_12 = (sts12.TAU_12 - frict) / damp
    w0_vin = (force - frict) / damp
    files = {}
    for name, kp0 in KP_PIN.items():
        files[name] = dict(kp=round(kp0 * scale * vin / sts12.V_12, 4))
    return dict(
        vin_V=round(vin, 4),
        stall_Nm_at_12V=round(sts12.TAU_12, 4),
        forcerange_Nm=round(force, 4),
        damping=round(damp, 4),
        frictionloss_Nm=round(frict, 4),
        armature=0.027,
        sheet_scale=round(scale, 4),
        speed_damping_factor=round(speed_k, 4),
        no_load_at_12V_rad_s=round(w0_12, 4),
        no_load_at_vin_rad_s=round(w0_vin, 4),
        kp=files,
    )


def build_links():
    """Build-trunk inertials plus the 70 g cell. Reuses sim/mass_budget.py."""
    sim = os.path.join(LAB, "sim")
    if sim not in sys.path:
        sys.path.insert(0, sim)
    pg = os.environ.get("ODM_PLAYGROUND")
    if not pg:
        raise SystemExit("ODM_PLAYGROUND is not set. Point it at Open_Duck_Playground at b9be205.")
    import mass_budget as MB  # noqa: E402

    links = MB.build_budget()["links"]
    before = links["trunk_assembly"]
    links["trunk_assembly"] = before + MB.point_mass(CELL_KG, CELL_M)
    after = links["trunk_assembly"]
    out = {}
    for name, mass in links.items():
        I = mass.I
        out[name] = dict(
            mass=float(mass.m),
            pos=[float(x) for x in mass.c],
            fullinertia=[float(x) for x in (I[0, 0], I[1, 1], I[2, 2], I[0, 1], I[0, 2], I[1, 2])],
        )
    trunk = dict(
        mass_before_kg=round(float(before.m), 4),
        mass_after_kg=round(float(after.m), 4),
        com_before_m=[round(float(x), 5) for x in before.c],
        com_after_m=[round(float(x), 5) for x in after.c],
    )
    return out, trunk


def write_config():
    volts, sts12 = bus_voltage()
    act = actuators(volts, sts12)
    links, trunk = build_links()
    doc = dict(
        label="calc only for the actuator and the bus voltage. The trunk mass is the mass budget plus 70 g.",
        pipeline=dict(
            repo="https://github.com/apirrone/Open_Duck_Playground",
            pin=PIN,
            runner="playground/open_duck_mini_v2/runner.py",
            env="joystick",
            task="flat_terrain_backlash",
            num_timesteps=150000000,
            imitation_reward=True,
            max_motor_velocity_rad_s=5.24,
            ppo=dict(
                source="mujoco_playground.config.locomotion_params.brax_ppo_config",
                name="BerkeleyHumanoidJoystickFlatTerrain",
                num_envs=8192,
                unroll_length=20,
                num_minibatches=32,
                batch_size=256,
                num_evals=15,
                network=[512, 256, 128],
            ),
        ),
        sheet=dict(
            part="ST-3215-C018",
            source="https://www.feetech.cn/en/525603",
            stall_kgcm=30.0,
            stall_A=2.7,
            no_load_s_per_60deg=0.222,
            no_load_current_A=I_NOLOAD,
            no_load_rad_s=round(float(sts12.W0_12), 3),
            trained_no_load_rad_s=round(float(sts12.W0_BAM), 3),
        ),
        bus=dict(
            cells=3,
            bec_set_V=16.0,
            bec_drop_V=0.3,
            bec_drop_note="ASSUMPTION, Castle publishes none. Same constant the twin uses.",
            current_A_per_servo=I_NOLOAD,
            current_note="Sheet no-load current, every servo, charge 0 mAh. Not a walking current.",
            servo_V=volts,
            training_vin_V=act["vin_V"],
            training_vin_note="Lowest servo port on that solve. The MJCF class is one number, so every joint uses it.",
        ),
        actuator=act,
        mass=dict(
            added_kg=CELL_KG,
            cell_seat_m=[round(float(x), 5) for x in CELL_M],
            holder_kg=0.0,
            trunk=trunk,
            links=links,
        ),
        smoke=dict(
            num_envs=8,
            num_timesteps=480,
            unroll_length=5,
            num_minibatches=4,
            batch_size=8,
            num_evals=4,
            note="Same length as the earlier CPU smoke. Not a gait. Checkpoints are not kept.",
        ),
    )
    json.dump(doc, open(CFG_PATH, "w"), indent=1)
    json.dump(doc, sys.stdout, indent=1)
    print("\nwrote", os.path.basename(CFG_PATH), file=sys.stderr)
    return doc


def load_config():
    return json.load(open(CFG_PATH))


def apply_config(cfg, playground):
    xmls = os.path.join(playground, "playground", "open_duck_mini_v2", "xmls")
    act = cfg["actuator"]
    links = cfg["mass"]["links"]
    for name in ROBOT_FILES:
        path = os.path.join(xmls, name)
        tree = ETXML.parse(path)
        root = tree.getroot()
        for default in root.iter("default"):
            if default.get("class") != "sts3215":
                continue
            joint = default.find("joint")
            pos = default.find("position")
            joint.set("damping", f"{act['damping']:.4f}")
            joint.set("frictionloss", f"{act['frictionloss_Nm']:.4f}")
            pos.set("kp", f"{act['kp'][name]['kp']:.4f}")
            fr = act["forcerange_Nm"]
            pos.set("forcerange", f"-{fr:.4f} {fr:.4f}")
        for body in root.iter("body"):
            nm = body.get("name")
            if nm not in links:
                continue
            row = links[nm]
            inert = body.find("inertial")
            inert.set("mass", f"{row['mass']:.9g}")
            inert.set("pos", " ".join(f"{x:.9g}" for x in row["pos"]))
            inert.set("fullinertia", " ".join(f"{x:.9g}" for x in row["fullinertia"]))
        tree.write(path)
    return xmls


def check_applied(playground, cfg):
    import mujoco

    xmls = os.path.join(playground, "playground", "open_duck_mini_v2", "xmls")
    assets = {}
    for fn in os.listdir(xmls):
        if fn.endswith(".xml"):
            assets[fn] = open(os.path.join(xmls, fn), "rb").read()
    for fn in os.listdir(os.path.join(xmls, "assets")):
        assets[fn] = open(os.path.join(xmls, "assets", fn), "rb").read()
    scene = os.path.join(xmls, "scene_flat_terrain_backlash.xml")
    model = mujoco.MjModel.from_xml_string(open(scene).read(), assets=assets)
    bid = model.body("trunk_assembly").id
    got = dict(
        trunk_kg=round(float(model.body_mass[bid]), 4),
        damping=round(float(model.dof_damping[model.jnt_dofadr[model.joint("left_knee").id]]), 4),
        friction=round(float(model.dof_frictionloss[model.jnt_dofadr[model.joint("left_knee").id]]), 4),
        force=round(float(model.actuator_forcerange[model.actuator("left_knee").id, 1]), 4),
        kp=round(float(model.actuator_gainprm[model.actuator("left_knee").id, 0]), 4),
    )
    want = cfg["actuator"]
    assert got["trunk_kg"] == cfg["mass"]["trunk"]["mass_after_kg"], got
    assert got["damping"] == want["damping"], got
    assert got["friction"] == want["frictionloss_Nm"], got
    assert got["force"] == want["forcerange_Nm"], got
    assert got["kp"] == want["kp"]["open_duck_mini_v2_backlash.xml"]["kp"], got
    return got


def smoke(playground, cfg):
    """8 envs, 480 steps, on the patched checkout. Not a gait."""
    os.environ.setdefault("JAX_PLATFORMS", "cpu")
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    # The runner loads the reference polynomial with a path relative to the playground root.
    # Logs go to an absolute folder so they are not mixed into that checkout.
    work = os.path.join(__import__("tempfile").gettempdir(), "sts12_smoke")
    os.makedirs(work, exist_ok=True)
    os.chdir(playground)
    if playground not in sys.path:
        sys.path.insert(0, playground)
    from mujoco_playground.config import locomotion_params
    import playground.open_duck_mini_v2.runner as duck_runner

    real = locomotion_params.brax_ppo_config
    sm = cfg["smoke"]

    def wrapped(name):
        c = real(name)
        c.num_envs = sm["num_envs"]
        c.unroll_length = sm["unroll_length"]
        c.num_minibatches = sm["num_minibatches"]
        c.batch_size = sm["batch_size"]
        c.num_evals = sm["num_evals"]
        return c

    locomotion_params.brax_ppo_config = wrapped
    args = argparse.Namespace(
        output_dir=os.path.join(work, "out"),
        num_timesteps=sm["num_timesteps"],
        env="joystick",
        task=cfg["pipeline"]["task"],
        restore_checkpoint_path=None,
    )
    import time

    t0 = time.time()
    runner = duck_runner.OpenDuckMiniV2Runner(args)
    runner.policy_params_fn = lambda *a, **k: None
    marks = []
    orig = runner.progress_callback

    def cb(num_steps, metrics):
        marks.append((time.time(), int(num_steps), float(metrics["eval/episode_reward"])))
        orig(num_steps, metrics)

    runner.progress_callback = cb
    runner.train()
    t1 = time.time()
    train_s = marks[-1][0] - marks[0][0] if len(marks) >= 2 else None
    steps = sm["num_timesteps"]
    row = dict(
        label="sim pass only",
        wall_s=round(t1 - t0, 1),
        train_s=None if train_s is None else round(train_s, 1),
        steps=steps,
        envs=sm["num_envs"],
        evals=[dict(t_s=round(t - t0, 1), step=n, reward=round(r, 2)) for t, n, r in marks],
        steps_per_s=None if not train_s else round(steps / train_s, 3),
    )
    print(json.dumps(row, indent=1))
    return row


def main():
    p = argparse.ArgumentParser(description="12 V / 3S training config for the playground runner")
    p.add_argument("--write", action="store_true", help="rebuild train_sts12.json")
    p.add_argument("--apply", action="store_true", help="patch the playground checkout")
    p.add_argument("--check", action="store_true", help="load the patched backlash scene")
    p.add_argument("--smoke", action="store_true", help="480-step CPU smoke, not a gait")
    args = p.parse_args()
    if args.write:
        cfg = write_config()
    else:
        cfg = load_config()
    pg = os.environ.get("ODM_PLAYGROUND")
    if args.apply or args.check or args.smoke:
        if not pg:
            raise SystemExit("ODM_PLAYGROUND is not set.")
        apply_config(cfg, pg)
    if args.check or args.smoke:
        print(json.dumps(check_applied(pg, cfg), indent=1))
    if args.smoke:
        smoke(pg, cfg)


if __name__ == "__main__":
    main()
