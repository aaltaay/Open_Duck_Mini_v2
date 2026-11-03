"""Structure twin, part 1: loads at every joint of our build from MuJoCo (sim pass only).

What it does
1. Writes a copy of the Playground MJCF for our build (2.65 kg, D22 print profile) with sim/added_mass_sim.py
   write_variant and sim/mass_budget.py build_budget, both imported unchanged.
2. Adds, in every body that holds an actuated joint, a site at the joint origin (child side, z = joint axis) with a
   MuJoCo force and torque sensor: the full 6D load the parent link passes to the child link through that joint
   (servo case, bearings, horns and screws in series). Adds accelerometer sites at every link centre of mass.
3. For falls (collide=True): every printed part mesh also collides with the floor (convex hull, contype 0,
   conaffinity 2, priority 2, so it never touches the robot itself and its own solref sets the contact
   stiffness; the floor gets contype 3). The feet keep the upstream TPU sole contact.
4. run(): the control loop of added_mass_sim.run (upstream MjInfer, BEST_WALK_ONNX_2, 50 Hz, accelerometer bias
   removed), with a physics time step that can be changed, sensor logging at every physics step, contact force
   per body, and a ring buffer of full states so a fall can be replayed from before the first hit with a stiffer
   contact and a smaller time step (impact sweep).

Paths: ODM_PLAYGROUND (Open_Duck_Playground at b9be205), ODM_SCRATCH (scratch folder, outside the repo).
"""
import os, sys, json, copy, time
import xml.etree.ElementTree as ET
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "../.."))
REPO = os.path.abspath(os.path.join(LAB, ".."))
SCR_ROOT = os.environ.get("ODM_SCRATCH", "/tmp/odm_twin_structure")
os.environ["ODM_SCRATCH"] = os.path.join(SCR_ROOT, "sim")          # added_mass_sim writes its models under here
sys.path.insert(0, os.path.join(LAB, "sim"))
import mujoco
import added_mass_sim as AM          # unchanged lab file: write_variant, the run loop it copies, CASES
CB, MB, MI = AM.CB, AM.MB, AM.MI

JOINTS = ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
          "neck_pitch", "head_pitch", "head_yaw", "head_roll",
          "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]
# printed parts that may hit the floor in a fall (MJCF visual mesh names); feet keep the upstream sole contact
FALL_MESHES = ("body_back", "body_front", "body_middle_bottom", "body_middle_top", "trunk_top", "trunk_bottom",
               "head", "head_bot_sheet", "head_pitch_to_yaw", "head_yaw_to_roll", "neck_left_sheet", "neck_right_sheet",
               "left_antenna_holder", "right_antenna_holder", "left_cache", "right_cache", "left_roll_to_pitch",
               "right_roll_to_pitch", "roll_motor_bottom", "roll_motor_top", "left_knee_to_ankle_left_sheet",
               "left_knee_to_ankle_right_sheet", "leg_spacer", "foot_top", "foot_side")


def _budget():
    return MB.build_budget()


def build_model(name, collide=False, body_solref=(0.02, 1.0), body_friction=0.6, B=None):
    """write the instrumented model folder; returns (folder, budget)"""
    B = B or _budget()
    pl = json.load(open(os.path.join(LAB, "audit/placements.json")))
    boxes = [("trunk_assembly", np.array(p["center_mm"]) / 1000, np.array(p["dims_xyz_mm"]) / 1000, "0.85 0.1 0.1 1") for p in pl]
    d = AM.write_variant(name, B["links"], boxes)
    for rf in AM.ROBOT_FILES:
        path = os.path.join(d, rf); tree = ET.parse(path); root = tree.getroot()
        sens = ET.SubElement(root, "sensor")
        for body in root.iter("body"):
            nm = body.get("name")
            js = [j.get("name") for j in body.findall("joint") if j.get("name") in JOINTS]
            if js:
                s = ET.SubElement(body, "site"); s.set("name", "st_" + js[0]); s.set("pos", "0 0 0"); s.set("group", "5")
            if nm in B["links"] and B["links"][nm].m > 0:
                s = ET.SubElement(body, "site"); s.set("name", "acc_" + nm); s.set("group", "5")
                s.set("pos", " ".join(f"{v:.6g}" for v in B["links"][nm].c))
            if collide:
                for g in list(body.findall("geom")):
                    if g.get("class") == "visual" and g.get("mesh") in FALL_MESHES:
                        c = ET.SubElement(body, "geom")
                        for k in ("type", "pos", "quat", "mesh"):
                            if g.get(k) is not None: c.set(k, g.get(k))
                        c.set("name", f"col_{nm}_{g.get('mesh')}_{len(body.findall('geom'))}")
                        c.set("contype", "0"); c.set("conaffinity", "2"); c.set("group", "4"); c.set("priority", "2")
                        c.set("solref", f"{body_solref[0]:.6g} {body_solref[1]:.6g}"); c.set("friction", f"{body_friction} 0.005 0.0001")
                        c.set("rgba", "0 0 0 0"); c.set("mass", "0")
        for j in JOINTS:
            if root.find(f".//site[@name='st_{j}']") is None: continue
            f = ET.SubElement(sens, "force"); f.set("name", "F_" + j); f.set("site", "st_" + j)
            t = ET.SubElement(sens, "torque"); t.set("name", "T_" + j); t.set("site", "st_" + j)
        for nm in B["links"]:
            if root.find(f".//site[@name='acc_{nm}']") is not None:
                a = ET.SubElement(sens, "accelerometer"); a.set("name", "A_" + nm); a.set("site", "acc_" + nm)
        tree.write(path)
    if collide:
        for sc in os.listdir(d):
            if sc.startswith("scene") and sc.endswith(".xml"):
                p = os.path.join(d, sc); tree = ET.parse(p)
                for g in tree.getroot().iter("geom"):
                    if g.get("name") == "floor": g.set("contype", "3")
                tree.write(p)
    return d, B


class Sim:
    """one MjInfer instance with logging; mirrors added_mass_sim.run step by step"""
    def __init__(self, folder, scene, start_dz=0.0, seed=None, xy_range=0.0, dt=0.002, iterations=None):
        AM._ASSET_DIR[0] = folder
        m = MI.MjInfer(os.path.join(folder, scene), CB.REF, CB.ONNX, standing=False)
        if start_dz:
            m.data.qpos[m._floating_base_qpos_addr + 2] += start_dz
        if seed is not None:
            rng = np.random.default_rng(seed)
            qa = np.array(m.actuator_joint_qpos_addr).ravel()
            m.data.qpos[qa] += rng.uniform(-0.03, 0.03, len(qa))
            m.data.qpos[m._floating_base_qpos_addr:m._floating_base_qpos_addr + 2] += rng.uniform(-xy_range, xy_range, 2)
        mujoco.mj_forward(m.model, m.data)
        if CB.ACC_OFFSET_FIX:
            _ga = m.get_accelerometer
            def _ga_fixed(d, _ga=_ga):
                a = np.array(_ga(d), dtype=float); a[0] -= 1.3; return a
            m.get_accelerometer = _ga_fixed
        self.m = m; self.model = m.model; self.data = m.data
        if iterations: self.model.opt.iterations = iterations; self.model.opt.ls_iterations = max(iterations, 10)
        self.set_dt(dt)
        md = self.model
        self.trunk = md.body("trunk_assembly").id
        self.fb = m._floating_base_qpos_addr
        self.sF = {j: md.sensor_adr[md.sensor("F_" + j).id] for j in JOINTS}
        self.sT = {j: md.sensor_adr[md.sensor("T_" + j).id] for j in JOINTS}
        self.sA = {}
        for i in range(md.nsensor):
            n = md.sensor(i).name
            if n.startswith("A_"): self.sA[n[2:]] = md.sensor_adr[i]
        self.body_names = [md.body(i).name for i in range(md.nbody)]
        self.geom_body = md.geom_bodyid.copy()
        self.floor_geoms = set(i for i in range(md.ngeom) if md.geom(i).name == "floor")
        self.col_geoms = [i for i in range(md.ngeom) if md.geom(i).name.startswith("col_")]
        self.t = 0.0; self.k = 0; self.fallen = False; self.falls = []
        self.ring = []

    def set_dt(self, dt):
        self.dt = dt; self.model.opt.timestep = dt; self.m.sim_dt = dt
        self.m.decimation = int(round(0.02 / dt)); self.counter = 0

    def set_body_solref(self, tc, dr=1.0):
        for g in self.col_geoms: self.model.geom_solref[g] = [tc, dr]

    def policy_state(self):
        m = self.m
        return dict(la=m.last_action.copy(), lla=m.last_last_action.copy(), llla=m.last_last_last_action.copy(),
                    mt=np.array(m.motor_targets).copy(), pmt=np.array(m.prev_motor_targets).copy(), ii=m.imitation_i,
                    ip=np.array(m.imitation_phase).copy(), cmd=list(m.commands))

    def snapshot(self):
        d = self.data
        return dict(t=self.t, k=self.k, qpos=d.qpos.copy(), qvel=d.qvel.copy(), act=d.act.copy(), ctrl=d.ctrl.copy(),
                    qacc_ws=d.qacc_warmstart.copy(), time=d.time, counter=self.counter, fallen=self.fallen,
                    falls=list(self.falls), pol=self.policy_state())

    def restore(self, s):
        d = self.data; m = self.m
        d.qpos[:] = s["qpos"]; d.qvel[:] = s["qvel"]; d.act[:] = s["act"]; d.ctrl[:] = s["ctrl"]
        d.qacc_warmstart[:] = s["qacc_ws"]; d.time = s["time"]
        self.t = s["t"]; self.k = s["k"]; self.fallen = s["fallen"]; self.falls = list(s["falls"])
        p = s["pol"]
        m.last_action = p["la"].copy(); m.last_last_action = p["lla"].copy(); m.last_last_last_action = p["llla"].copy()
        m.motor_targets = p["mt"].copy(); m.prev_motor_targets = p["pmt"].copy(); m.imitation_i = p["ii"]
        m.imitation_phase = p["ip"].copy(); m.commands = list(p["cmd"])
        mujoco.mj_forward(self.model, d)

    def contacts(self):
        """per body: summed contact force on the body (world, N) and deepest penetration (m), body-floor only"""
        md, d = self.model, self.data
        out = {}; f6 = np.zeros(6)
        for i in range(d.ncon):
            c = d.contact[i]
            g1, g2 = c.geom1, c.geom2
            if g1 in self.floor_geoms: gb, sgn = g2, 1.0
            elif g2 in self.floor_geoms: gb, sgn = g1, -1.0
            else: continue
            mujoco.mj_contactForce(md, d, i, f6)
            fr = np.array(c.frame).reshape(3, 3)            # rows: normal, tangent1, tangent2 (world)
            fw = fr.T @ f6[:3]                                 # force on geom2 from geom1, world
            # force on the robot geom: if robot is geom2 it gets +fw, else -fw
            fw = fw * sgn
            b = self.geom_body[gb]
            o = out.setdefault(b, [np.zeros(3), 0.0, 0])
            o[0] += fw; o[1] = min(o[1], c.dist); o[2] += 1
        return out

    def step(self, schedule, pushes=None):
        m, model, data = self.m, self.model, self.data
        self.t += self.dt
        t = self.t
        data.xfrc_applied[:] = 0
        if pushes:
            for (t0, t1, fvec) in pushes:
                if t0 <= t < t1: data.xfrc_applied[self.trunk, :3] = fvec
        mujoco.mj_step(model, data)
        self.k += 1; self.counter += 1
        if self.counter % m.decimation == 0:
            m.commands = schedule(t)
            m.imitation_i += 1.0 * m.phase_frequency_factor
            m.imitation_i = m.imitation_i % m.PRM.nb_steps_in_period
            ph = m.imitation_i / m.PRM.nb_steps_in_period * 2 * np.pi
            m.imitation_phase = np.array([np.cos(ph), np.sin(ph)])
            obs = m.get_obs(data, m.commands)
            action = m.policy.infer(obs)
            m.last_last_last_action = m.last_last_action.copy()
            m.last_last_action = m.last_action.copy()
            m.last_action = action.copy()
            m.motor_targets = m.default_actuator + action * m.action_scale
            if MI.USE_MOTOR_SPEED_LIMITS:
                m.motor_targets = np.clip(m.motor_targets,
                    m.prev_motor_targets - m.max_motor_velocity * 0.02,
                    m.prev_motor_targets + m.max_motor_velocity * 0.02)
                m.prev_motor_targets = m.motor_targets.copy()
            data.ctrl = m.motor_targets.copy()
            pos = data.qpos[self.fb:self.fb + 3]; quat = data.qpos[self.fb + 3:self.fb + 7]
            R = np.zeros(9); mujoco.mju_quat2Mat(R, quat); upz = R[8]
            if (pos[2] < 0.10 or upz < 0.5) and not self.fallen:
                self.fallen = True; self.falls.append(round(t, 4))
            if self.fallen and pos[2] > 0.13 and upz > 0.8: self.fallen = False

    def record(self):
        d = self.data
        F = np.array([d.sensordata[self.sF[j]:self.sF[j] + 3] for j in JOINTS])
        T = np.array([d.sensordata[self.sT[j]:self.sT[j] + 3] for j in JOINTS])
        A = {b: d.sensordata[a:a + 3].copy() for b, a in self.sA.items()}
        return F, T, A


def run_logged(folder, scene, schedule, dur, pushes=None, start_dz=0.0, seed=None, xy_range=0.0, dt=0.002,
               iterations=None, log_every=1, contacts=True):
    """the added_mass_sim.run case with the joint loads logged; returns arrays (time, F, T, acc, contacts, base)"""
    S = Sim(folder, scene, start_dz, seed, xy_range, dt, iterations)
    n = int(round(dur / dt)); nl = n // log_every
    tt = np.zeros(nl); FF = np.zeros((nl, len(JOINTS), 3)); TT = np.zeros((nl, len(JOINTS), 3))
    names = list(S.sA.keys()); AA = np.zeros((nl, len(names), 3))
    feet = [S.model.body("foot_assembly").id, S.model.body("foot_assembly_2").id]
    GRF = np.zeros((nl, 2, 3)); BC = np.zeros((nl, S.model.nbody, 3)); PEN = np.zeros((nl, S.model.nbody))
    base = np.zeros((nl, 7)); q = np.zeros((nl, len(JOINTS)))
    qa = np.array(S.m.actuator_joint_qpos_addr).ravel()
    li = 0
    for k in range(n):
        S.step(schedule, pushes)
        if (k + 1) % log_every: continue
        if li >= nl: break
        F, T, A = S.record()
        tt[li] = S.t; FF[li] = F; TT[li] = T; AA[li] = [A[b] for b in names]
        base[li] = S.data.qpos[S.fb:S.fb + 7]; q[li] = S.data.qpos[qa]
        if contacts:
            for b, (f, pen, nc) in S.contacts().items():
                BC[li, b] = f; PEN[li, b] = pen
            GRF[li, 0] = BC[li, feet[0]]; GRF[li, 1] = BC[li, feet[1]]
        li += 1
    return dict(t=tt, F=FF, T=TT, A=AA, acc_names=names, GRF=GRF, BC=BC, PEN=PEN, base=base, q=q,
                falls=S.falls, joints=JOINTS, body_names=S.body_names, dt=dt * log_every)


if __name__ == "__main__":
    d, B = build_model("st_ours")
    print("model folder", d)
    S = Sim(d, "scene_flat_terrain.xml")
    print("mass", round(float(S.model.body_subtreemass[1]), 4), "kg", "nsensor", S.model.nsensor)
