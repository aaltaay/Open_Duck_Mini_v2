"""nestlib.py: shared harness for the "go to the nest" sim (Sim N3 of NATURAL_DOCK_IDEAS.md). sim pass only.

Reuses, read only:
  twin/sit/sit_model.py, sit_sim.py   the repo sit model (2.8078 kg), the SIT.md section 5 path (DOWN, SIT, UP, rise logic)
  sim/added_mass_sim.py, current_budget.py   the stock walk loop (upstream MjInfer, BEST_WALK_ONNX_2, unmodified) and the
                                             BAM current model
  sim/power_fix.py option 7           the voltage model: position gain and torque limit both scale with V / 7.4
  dock/feet/deep/harness.py, dock.py  the 50 Hz step, feet pose, the settle march and feet-together stop, resume()
  dock/natural/coverage.py            the zone rules (pin margin 3 mm, no pin on the wrong zone)

World frame (m): the sun centre is the origin, the wall face is the plane x = +0.190, the room is at x < 0.
The duck walks in heading +x, turns, and sits heading -x (pi).
"""
import json
import os
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))  # altaay_lab, relative to this file
SCR = os.environ.get("NEST_SCRATCH") or os.path.join(__import__("tempfile").gettempdir(), "nestsim")  # scratch folder outside the repo
MODEL = os.path.join(SCR, "model")
os.environ.setdefault("ODM_SCRATCH", os.path.join(MODEL, "am_scratch"))
sys.path.insert(0, os.path.join(LAB, "twin", "sit"))
sys.path.insert(0, os.path.join(LAB, "sim"))
sys.path.insert(0, os.path.dirname(HERE))

import contextlib  # noqa: E402
import io  # noqa: E402

import mujoco  # noqa: E402
import sit_model as SM  # noqa: E402
import sit_sim as S  # noqa: E402

with contextlib.redirect_stdout(io.StringIO()):
    import added_mass_sim as AM  # noqa: E402
CB = AM.CB
MI = CB.MI
D = np.radians

# ---------------------------------------------------------------- geometry (NATURAL_DOCK_IDEAS.md section 6 A and B, figs.py)
WALL_X = float(os.environ.get("NEST_WALL_X", "0.190"))   # sun centre, m from the wall. Default 0.190 (the approved concept).
# NEST_WALL_X is a study override only. It does not change the approved 190 mm in any design record.
MAT_H = 0.002             # 2 mm felt
MAT_R = 0.247             # nest about 49 cm across
MAT_BACK = 0.022          # the felt starts 22 mm from the wall (figs.py)
RIM_D0, RIM_D1, RIM_H, RIM_HALF = 0.022, 0.072, 0.030, 0.227     # soft rim: 22 to 72 mm from the wall, 30 mm high (figs.py)
RC, GAP, ROUT = 0.050, 0.032, 0.235                                # sun disc radius, felt gap, ring outer radius
RING_BACK = 0.074                                                  # the ring ends 74 mm from the wall (figs.py)
RUG_A, RUG_B, RUG_HALF = (0.140, 0.250), (0.282, 0.520), 0.280     # pond rug bands, distance from the wall
TIP_M = 0.003                                                      # coverage.py: a pin counts 3 mm inside its zone
# spring pins (est; the study gives "about 1 N each" and "a long-travel pin" for the bumper, part is a BLOCKER there)
PIN_Y = 0.010
PIN_F0, PIN_F1 = 0.6, 1.4          # N at first touch and at full travel (1.0 N mid stroke)
PIN_L = dict(seat=0.0020, bump=0.0050)   # m the pin stands proud of its block = its working travel
STAND = S.STAND
KT = CB.KTS[0]
RM = KT / CB.KT_OVER_R


def on_mat(x, y):
    return (np.hypot(x, y) < MAT_R) & (x < WALL_X - MAT_BACK)


HF_HALF, HF_CELL, HF_DROP = 0.26, float(os.environ.get("NEST_CELL", "0.005")), 0.001
# The archived field covers +/-260 mm, which holds the 247 mm upper felt. The lower felt is 267 mm, so the stepped
# and tapered edges need a wider field. The default ("one") stays at 260 mm, cell for cell, with the archived runs.


def field_half():
    if edge_mode() == "one":
        return HF_HALF
    return HF_HALF + TREAD + HF_CELL          # 267 mm tread plus one cell, still on the 5 mm grid


# NEST_EDGE selects the room-side edge. "one" is the archived field (one 2 mm rise). "steps" is the CAD edge:
# two 1 mm rises, 20 mm apart (lower felt radius 267 mm, upper 247 mm; cad/nestcad_lib.py BASE_R, TOP_R, FELT_T).
# "taper" is a straight ramp from the floor to 2 mm across that same 20 mm band. The back cut stays WALL_X - MAT_BACK.
EDGE_MODES = ("one", "steps", "taper")
TREAD = 0.020                 # m, the lower felt sticks out past the upper felt


def edge_mode():
    m = os.environ.get("NEST_EDGE", "one")
    if m not in EDGE_MODES:
        raise SystemExit("NEST_EDGE must be one, steps or taper, got %r" % m)
    return m


def _sample_for_height(z):
    """hfield sample (0 to 1) whose top is z metres above the floor.
    The geom sits at -HF_DROP and the field rises MAT_H + HF_DROP, so sample 1 is MAT_H above the floor and sample 0
    is HF_DROP below it (the floor plane carries the duck there)."""
    return (z + HF_DROP) / (MAT_H + HF_DROP)


def hfield_data():
    """the mat as a height field (cells HF_CELL). Sample 1 is on the mat, MAT_H above the floor. Sample 0 is outside.
    Default (NEST_EDGE=one, or unset): 1 inside the nest outline, 0 outside. The 2 mm edge is one cell wide
    (2 mm over 5 mm: a steep chamfer, not a knife edge). That default is the field the archived runs used.
    NEST_EDGE=steps: 1 mm on the 20 mm tread, 2 mm inside the upper felt. Each rise is still one cell.
    NEST_EDGE=taper: a linear ramp from 0 at the outer radius to 2 mm at the upper-felt radius."""
    half = field_half()
    n = int(round(2 * half / HF_CELL)) + 1
    g = np.linspace(-half, half, n)
    X, Y = np.meshgrid(g, g)                      # row = y, column = x
    mode = edge_mode()
    if mode == "one":
        return n, on_mat(X, Y).astype(np.float32)
    r = np.hypot(X, Y)
    back = X < WALL_X - MAT_BACK
    inner = (r < MAT_R) & back
    outer = (r < MAT_R + TREAD) & back
    if mode == "steps":
        h1 = _sample_for_height(0.001)            # 1 mm above the floor
        h = np.where(inner, 1.0, np.where(outer, h1, 0.0))
    else:
        # 0 at the outer radius, 1 (2 mm) at the upper felt, flat inside
        h = np.clip((MAT_R + TREAD - r) / TREAD, 0.0, 1.0)
        h = np.where(outer, h, 0.0)
    return n, h.astype(np.float32)


def scene_xml(mat=True, wall=True):
    n, _ = hfield_data()
    half = field_half()
    rim = ('<geom name="rim" type="box" pos="%.4f 0 %.4f" size="%.4f %.4f %.4f" rgba="0.72 0.80 0.64 1" contype="2" conaffinity="0"/>'
           % (WALL_X - 0.5 * RIM_D1, RIM_H / 2, 0.5 * RIM_D1, RIM_HALF, RIM_H / 2))       # filled back to the wall: a solid block
    wl = ('<geom name="wall" type="box" pos="%.4f 0 0.3" size="0.02 1.2 0.3" rgba="0.91 0.89 0.85 1" contype="2" conaffinity="0"/>' % (WALL_X + 0.02))
    hf = ('<geom name="mat" type="hfield" hfield="mat" pos="0 0 %.4f" contype="1" conaffinity="0" priority="2" friction="0.8" condim="3" rgba="0.96 0.89 0.68 1"/>'
          % (-HF_DROP))
    return f'''<mujoco model="scene"><include file="open_duck_mini_v2.xml"/>
<visual><headlight diffuse="0.7 0.7 0.7" ambient="0.4 0.4 0.4" specular="0 0 0"/><global offwidth="640" offheight="480"/></visual>
<asset>{'<hfield name="mat" nrow="%d" ncol="%d" size="%.3f %.3f %.4f 0.004"/>' % (n, n, half, half, MAT_H + HF_DROP) if mat else ''}
<texture type="skybox" builtin="gradient" rgb1="0.98 0.98 0.96" rgb2="0.98 0.98 0.96" width="64" height="64"/></asset>
<worldbody><light pos="-0.5 0 2.5" dir="0.2 0 -1" directional="true"/>
<body name="floor"><geom name="floor" size="0 0 0.01" type="plane" contype="1" conaffinity="0" priority="1" friction="0.6" condim="3" rgba="0.86 0.83 0.77 1"/>
{hf if mat else ''}
{'<geom name="matplane" type="plane" size="0 0 0.01" pos="0 0 %.4f" contype="1" conaffinity="0" priority="2" friction="0.8" condim="3" rgba="0 0 0 0"/>' % MAT_H if mat else ''}
</body>
<body name="walls">{(wl + rim) if wall else ''}
<geom name="sun" type="cylinder" pos="0 0 {MAT_H + 0.0003:.4f}" size="{RC} 0.0002" rgba="0.90 0.72 0.25 1" contype="0" conaffinity="0"/>
</body></worldbody>
<keyframe><key name="home" qpos="0 0 0.15 1 0 0 0 0.002 0.053 -0.63 1.368 -0.784 0 0 0 0 -0.003 -0.065 0.635 1.379 -0.796" ctrl="0.002 0.053 -0.63 1.368 -0.784 0 0 0 0 -0.003 -0.065 0.635 1.379 -0.796"/></keyframe></mujoco>'''


_A = {}
_HULL = {}


def _assets():
    if "a" not in _A:
        _A["a"] = dict(SM.assets(os.path.join(MODEL, "sit")))
    return _A["a"]


def _hook():
    ga = _assets
    AM.CB.base.get_assets = ga
    sys.modules["playground.open_duck_mini_v2.base"].get_assets = ga
    AM._get_assets = ga


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


CAL_FILE = os.path.join(HERE, "calib.json")


def load_cal():
    return json.load(open(CAL_FILE)) if os.path.exists(CAL_FILE) else {}


class Sim:
    """one duck in the nest world; 50 Hz control steps, 500 Hz physics"""

    def __init__(self, seed=0, x0=-1.0, y0=0.0, yaw0=0.0, mu_mat=0.8, mu_floor=0.6, volt=7.4, pins_on=True, mat=True, wall=True,
                 pin_scale=1.0, record=None):
        _hook()
        os.makedirs(os.path.join(SCR, "scenes"), exist_ok=True)
        import hashlib
        xml = scene_xml(mat, wall)
        p = os.path.join(SCR, "scenes", "scene_%s.xml" % hashlib.md5(xml.encode()).hexdigest()[:12])
        if not os.path.exists(p):
            open(p + ".tmp%d" % os.getpid(), "w").write(xml)
            os.replace(p + ".tmp%d" % os.getpid(), p)
        with contextlib.redirect_stdout(io.StringIO()):
            m = MI.MjInfer(p, CB.REF, CB.ONNX, standing=False)
        _g0 = m.get_accelerometer
        m.get_accelerometer = lambda dd, _g=_g0: (lambda a: (a.__setitem__(0, a[0] - 1.3), a)[1])(np.array(_g(dd), float))
        self.m, self.model, self.data = m, m.model, m.data
        md, dd = self.model, self.data
        if mat:
            md.hfield_data[:] = hfield_data()[1].ravel()
        self.rng = np.random.default_rng(seed)
        self.fb = fb = m._floating_base_qpos_addr
        qa = np.array(m.actuator_joint_qpos_addr).ravel()
        dd.qpos[qa] += self.rng.uniform(-0.03, 0.03, len(qa))          # the training start jitter, as added_mass_sim.run
        dd.qpos[fb], dd.qpos[fb + 1] = x0, y0
        dd.qpos[fb + 3:fb + 7] = [np.cos(yaw0 / 2), 0, 0, np.sin(yaw0 / 2)]
        dd.qpos[fb + 2] += 0.013 + (MAT_H if (mat and on_mat(x0, y0)) else 0.0)   # the home pose has the soles 12 mm in the floor: start them just clear
        self.volt, self.s = volt, volt / 7.4
        self.kp0 = md.actuator_gainprm[:, 0].copy()
        self.fr0 = md.actuator_forcerange.copy()
        md.actuator_forcerange[:] = self.fr0 * self.s
        self.torque(True)
        gid = lambda n: mujoco.mj_name2id(md, mujoco.mjtObj.mjOBJ_GEOM, n)  # noqa: E731
        self.g_floor, self.g_mat, self.g_wall, self.g_rim = gid("floor"), gid("mat"), gid("wall"), gid("rim")
        md.geom_friction[self.g_floor, 0] = mu_floor
        self.hull = []
        if self.g_mat >= 0:
            md.geom_friction[self.g_mat, 0] = mu_mat
            self.g_matplane = gid("matplane")
            md.geom_friction[self.g_matplane, 0] = mu_mat
        self.mu_mat, self.mu_floor, self.has_mat = mu_mat, mu_floor, mat
        self.mat_mode("field")
        # collision sets: walking = the stock set (soles, seat, bumper against the floor and mat) and every robot part
        # against the wall and rim; sitting = sit_sim.model(): every printed part also touches the floor
        self.robot_geoms = [g for g in range(md.ngeom) if md.geom_bodyid[g] > 0 and md.body(md.geom_bodyid[g]).name not in ("floor", "walls")
                            and md.geom_group[g] in (2, 3)]
        # collision set (physics): the stock one, soles, seat block and bumper against the floor and the mat, plus the
        # same parts against the wall and the rim. The other printed parts (visual meshes, 98,000 vertices, no hulls) are
        # checked against the wall and the rim by geometry at 50 Hz (clearance of their convex hull points), not by physics:
        # MuJoCo 3.17 ignores a runtime contype on a geom that was non-colliding at compile time unless the mid-phase is off
        # and the body flags are set, and then the mesh-box tests cost 50 x the run time.
        self.col = [g for g in self.robot_geoms if md.geom_group[g] == 3 and (md.geom_conaffinity[g] or md.geom_contype[g])]
        for g in self.col:
            md.geom_conaffinity[g] |= 2
            md.body_conaffinity[md.geom_bodyid[g]] |= 2               # the broad phase filters on the body's flags
        for g in self.robot_geoms:
            if md.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH:
                continue
            mid = int(md.geom_dataid[g])
            if mid not in _HULL:
                V = md.mesh_vert[md.mesh_vertadr[mid]:md.mesh_vertadr[mid] + md.mesh_vertnum[mid]]
                try:
                    from scipy.spatial import ConvexHull
                    V = V[ConvexHull(V).vertices]
                except Exception:
                    pass
                _HULL[mid] = np.array(V, float)
            self.hull.append((g, _HULL[mid], md.body(md.geom_bodyid[g]).name))
        self.trunk = md.body("trunk_assembly").id
        self.feet = [md.body("foot_assembly").id, md.body("foot_assembly_2").id]
        self.soles = [gid(n) for n in S.SOLES]
        self.g_seat = gid("sit_seat_trunk_assembly_1_collision")
        self.g_bump = gid("sit_bumper_trunk_assembly_1_collision")
        self.gyro_adr = m.gyro_addr
        self.pins_on, self.pin_scale = pins_on, pin_scale
        cal = load_cal()
        self.pin_body = cal.get("pin_body")            # {name: [x, y, z] trunk body frame}, axis
        self.pin_axis = np.array(cal["pin_axis"]) if cal.get("pin_axis") else None
        self.pin_state = {}
        mujoco.mj_forward(md, dd)
        self._sole_frames()
        self.t, self.policy_on, self.fallen, self.tfall, self.fall_stage = 0.0, True, False, None, None
        self.stage = "init"
        self.sitting = False
        self.imu_yaw = 0.0
        self.gyro_bias = 0.0
        self.gyro_scale = 1.0
        self.events = dict(wall=[], rim=[], edge=[])
        self._last_evt = {}
        self.cur = {}                                   # stage -> [n, sum_bus, max_bus_20ms, max_servo]
        self._bus20 = []
        self.trace = []                                 # (t, x, y, yaw, stage) at 10 Hz
        self.record = record
        self.k = 0
        self.min_wall_clear = (9.0, "", "")
        self.min_rim_clear = (9.0, "", "")
        self.has_wall = wall

    # ---------------------------------------------------------- actuators
    def torque(self, on):
        md = self.model
        md.actuator_gainprm[:, 0] = self.kp0 * self.s if on else 0.0
        md.actuator_biasprm[:, 1] = -self.kp0 * self.s if on else 0.0
        self.torque_on = on

    def mat_mode(self, mode):
        """'field': the mat is the height field (walking, the edge). 'plane': the mat top is a plane at 2 mm, used only
        while the duck sits wholly on the mat: the repo's sit was built and checked on a plane (sit_sim.py), and on the
        height field the resting sit pose depends on the cell size (a contact artefact, see NEST_SIM.md)."""
        if not self.has_mat:
            return
        self.model.geom_contype[self.g_mat] = 1 if mode == "field" else 0
        self.model.geom_contype[self.g_matplane] = 0 if mode == "field" else 1
        self.mode = mode

    def wholly_on_mat(self, margin=0.010):
        """soles and the place the seat block and bumper will land, all at least `margin` inside the mat outline"""
        dd = self.data
        pts = []
        for g, V, bn in self.hull:
            if g in self.soles:
                pts.append((V @ dd.geom_xmat[g].reshape(3, 3).T + dd.geom_xpos[g])[:, :2])
        (x, y, yaw), _, _ = self.trunk_pose()
        c, sn = np.cos(yaw), np.sin(yaw)
        pts.append(np.array([[x + c * d - sn * w, y + sn * d + c * w] for d in (-0.175, -0.10, 0.03) for w in (-0.045, 0.045)]))
        P = np.vstack(pts)
        r = np.hypot(P[:, 0], P[:, 1])
        return bool((r < MAT_R - margin).all() and (P[:, 0] < WALL_X - MAT_BACK - margin).all())

    def sit_collisions(self, on):
        """kept as a hook: against the floor and the mat the collision set is the stock one in the walk and in the sit
        (soles, seat block, bumper). On a flat floor no other part comes within 5 mm of the floor in a sit and stand
        cycle (checked once, see NEST_SIM.md)."""
        return

    def clearance(self):
        """smallest gap (m) from any robot part to the wall face and to the rim block (negative = inside), by geometry"""
        dd = self.data
        best_w, best_r = (9.0, ""), (9.0, "")
        for g, V, bn in self.hull:
            c = dd.geom_xpos[g]
            if c[0] < WALL_X - 0.45:
                continue
            W = V @ dd.geom_xmat[g].reshape(3, 3).T + c
            i = W[:, 0].argmax()
            cw = WALL_X - W[i, 0]
            if cw < best_w[0]:
                best_w = (float(cw), bn)
            sel = (W[:, 2] < RIM_H) & (abs(W[:, 1]) < RIM_HALF)
            if sel.any():
                cr = (WALL_X - RIM_D1) - W[sel, 0].max()
                if cr < best_r[0]:
                    best_r = (float(cr), bn)
        return best_w, best_r

    # ---------------------------------------------------------- poses
    def _sole_frames(self):
        """per foot: the sole geom centre in the foot body frame and the foot's forward axis (body x). The harness of
        feet/deep took the mean of the lowest sole vertices at the start pose, which moves with the start jitter."""
        md, dd = self.model, self.data
        self.sf = []
        for g, b in zip(self.soles, self.feet):
            R = dd.xmat[b].reshape(3, 3)
            c = R.T @ (dd.geom_xpos[g] - dd.xpos[b])
            self.sf.append((c, np.array([1.0, 0.0, 0.0])))

    def feet_pose(self):
        out = []
        for (c, f), b in zip(self.sf, self.feet):
            R = self.data.xmat[b].reshape(3, 3)
            p = self.data.xpos[b]
            cw, fw = p + R @ c, R @ f
            out.append((cw[0], cw[1], np.arctan2(fw[1], fw[0])))
        return np.array(out)

    def trunk_pose(self):
        R = self.data.xmat[self.trunk].reshape(3, 3)
        p = self.data.xpos[self.trunk]
        return np.array([p[0], p[1], np.arctan2(R[1, 0], R[0, 0])]), float(p[2]), float(R[2, 2])

    def stagger(self):
        """left foot ahead of the right foot along the mean foot heading, mm"""
        f = self.feet_pose()
        h = np.arctan2(np.sin(f[:, 2]).sum(), np.cos(f[:, 2]).sum())
        return ((f[0, 0] - f[1, 0]) * np.cos(h) + (f[0, 1] - f[1, 1]) * np.sin(h)) * 1000

    def foot_forces(self):
        F = [0.0, 0.0]
        md, dd = self.model, self.data
        for i in range(dd.ncon):
            c = dd.contact[i]
            for j, b in enumerate(self.feet):
                if md.geom_bodyid[c.geom1] == b or md.geom_bodyid[c.geom2] == b:
                    f = np.zeros(6)
                    mujoco.mj_contactForce(md, dd, i, f)
                    F[j] += f[0]
        return F

    # ---------------------------------------------------------- pins
    def pins(self, apply=False):
        """the 4 belly pins as sprung contacts on the trunk: per pin the tip xy (world), compression (m) and force (N)"""
        dd = self.data
        if apply:
            dd.qfrc_applied[:] = 0
        if self.pin_body is None:
            return {}
        R = dd.xmat[self.trunk].reshape(3, 3)
        p = dd.xpos[self.trunk]
        A = R @ self.pin_axis
        out = {}
        for nm, pb in self.pin_body.items():
            L = PIN_L[nm[:4]]
            P = p + R @ np.array(pb)
            if A[2] > -0.3:
                out[nm] = dict(xy=[float(P[0]), float(P[1])], comp=0.0, F=0.0)
                continue
            # tip xy on the surface: first guess the floor, then the mat height there
            h = 0.0
            for _ in range(2):
                s = (P[2] - h) / (-A[2])
                tip = P + A * s
                h = MAT_H if (self.has_mat and on_mat(tip[0], tip[1])) else 0.0
            s = (P[2] - h) / (-A[2])
            tip = P + A * s
            comp = float(np.clip(L - s, 0.0, L))
            F = (PIN_F0 + (PIN_F1 - PIN_F0) * comp / L) * self.pin_scale if (L - s) > 0 else 0.0
            if apply and self.pins_on and F > 0:
                mujoco.mj_applyFT(self.model, dd, np.array([0, 0, F]), np.zeros(3), np.array([tip[0], tip[1], h]), self.trunk, dd.qfrc_applied)
            out[nm] = dict(xy=[float(tip[0]), float(tip[1])], comp=comp, F=float(F), gap=float(s))
        return out

    # ---------------------------------------------------------- physics
    def _phys(self):
        md, dd = self.model, self.data
        if self.pins_on and self.pin_body is not None and dd.xpos[self.trunk][2] < 0.12:
            self.pin_state = self.pins(apply=True)
        elif self.pin_state:
            dd.qfrc_applied[:] = 0
            self.pin_state = {}
        mujoco.mj_step(md, dd)
        self.t += md.opt.timestep
        # servo current (BAM model, current_budget.electrical with the bus voltage of this run)
        if self.torque_on:
            F = dd.actuator_force
            w = dd.qvel[self.m.actuator_qvel_addr]
            u = np.clip(F * RM / KT, -self.volt, self.volt)
            I = (u - KT * w) / RM
            bus = float(np.clip(u * I, 0, None).sum() / self.volt)
            imax = float(np.abs(I).max())
        else:
            bus, imax = 0.0, 0.0
        c = self.cur.setdefault(self.stage, [0, 0.0, 0.0, 0.0])
        c[0] += 1
        c[1] += bus
        c[3] = max(c[3], imax)
        self._bus20.append(bus)
        if len(self._bus20) == 10:
            c[2] = max(c[2], float(np.mean(self._bus20)))
            self._bus20 = []
        # contacts with the wall, the rim, and the mat edge
        n = dd.ncon
        if n:
            g1, g2 = dd.contact.geom1[:n], dd.contact.geom2[:n]
            for key, gw in (("wall", self.g_wall), ("rim", self.g_rim)):
                if gw < 0:
                    continue
                hit = np.where((g1 == gw) | (g2 == gw))[0]
                if len(hit) and self.t - self._last_evt.get(key, -9) > 0.3:
                    i = hit[0]
                    og = g2[i] if g1[i] == gw else g1[i]
                    self.events[key].append(dict(t=round(self.t, 2), stage=self.stage, body=md.body(md.geom_bodyid[og]).name,
                                                 geom=mujoco.mj_id2name(md, mujoco.mjtObj.mjOBJ_GEOM, og) or "geom%d" % og))
                if len(hit):
                    self._last_evt[key] = self.t
            if self.g_mat >= 0:
                hit = np.where(((g1 == self.g_mat) | (g2 == self.g_mat)))[0]
                for i in hit:
                    if abs(dd.contact.frame[i, 2]) < 0.99:          # the contact normal is tilted: the one-cell edge face of the mat
                        if self.t - self._last_evt.get("edge", -9) > 0.3:
                            og = g2[i] if g1[i] == self.g_mat else g1[i]
                            self.events["edge"].append(dict(t=round(self.t, 2), stage=self.stage, body=md.body(md.geom_bodyid[og]).name))
                        self._last_evt["edge"] = self.t
                        break

    def _after(self):
        dd = self.data
        self.k += 1
        # simulated IMU yaw: the gyro rate about the vertical, with a bias and a scale error (est), integrated at 50 Hz
        w = dd.sensordata[self.gyro_adr:self.gyro_adr + 3]
        Rs = dd.site_xmat[self.m.imu_site_id].reshape(3, 3)
        wz = float((Rs @ w)[2])
        self.imu_yaw += (wz * self.gyro_scale + self.gyro_bias) * 0.02
        (x, y, yaw), z, up = self.trunk_pose()
        if not self.fallen and (up < 0.5 or (not self.sitting and z < 0.10)):
            self.fallen, self.tfall, self.fall_stage = True, self.t, self.stage
        if self.has_wall and x > WALL_X - 0.6:
            (cw, bw), (cr, br) = self.clearance()
            if cw < self.min_wall_clear[0]:
                self.min_wall_clear = (cw, bw, self.stage)
            if cr < self.min_rim_clear[0]:
                self.min_rim_clear = (cr, br, self.stage)
        if self.k % 5 == 0:
            self.trace.append((round(self.t, 2), round(float(x), 4), round(float(y), 4), round(float(yaw), 4), self.stage))
        if self.record is not None:
            self.record(self)

    def step(self, cmd=(0, 0, 0)):
        """one 50 Hz control period with the walk policy (verbatim MjInfer.run() control logic, as added_mass_sim.run)"""
        m = self.m
        for _ in range(m.decimation):
            self._phys()
        if self.policy_on:
            m.commands = list(cmd) + [0, 0, 0, 0]
            m.imitation_i = (m.imitation_i + m.phase_frequency_factor) % m.PRM.nb_steps_in_period
            ph = m.imitation_i / m.PRM.nb_steps_in_period * 2 * np.pi
            m.imitation_phase = np.array([np.cos(ph), np.sin(ph)])
            obs = m.get_obs(self.data, m.commands)
            a = m.policy.infer(obs)
            m.last_last_last_action = m.last_last_action.copy()
            m.last_last_action = m.last_action.copy()
            m.last_action = a.copy()
            m.motor_targets = m.default_actuator + a * m.action_scale
            if MI.USE_MOTOR_SPEED_LIMITS:
                lim = m.max_motor_velocity * (m.sim_dt * m.decimation)
                m.motor_targets = np.clip(m.motor_targets, m.prev_motor_targets - lim, m.prev_motor_targets + lim)
                m.prev_motor_targets = m.motor_targets.copy()
            self.data.ctrl = m.motor_targets.copy()
        self._after()

    def go(self, c1, T):
        """policy off: cosine ramp of the position targets to c1 over T s (sit_sim.ramp, at the physics rate)"""
        self.policy_on = False
        c0 = self.data.ctrl.copy()
        n = max(1, int(round(T / 0.002)))
        for i in range(n):
            s = 0.5 - 0.5 * np.cos(np.pi * (i + 1) / n)
            self.data.ctrl[:] = c0 * (1 - s) + c1 * s
            self._phys()
            if (i + 1) % 10 == 0:
                self._after()

    def hold(self, T):
        self.policy_on = False
        for i in range(int(round(T / 0.002))):
            self._phys()
            if (i + 1) % 10 == 0:
                self._after()

    def resume(self):
        """back to the walk policy from a held pose (dock.py resume())"""
        m = self.m
        self.go(m.default_actuator.copy(), 0.8)
        m.last_action[:] = 0
        m.last_last_action[:] = 0
        m.last_last_last_action[:] = 0
        m.motor_targets = m.default_actuator.copy()
        m.prev_motor_targets = m.default_actuator.copy()
        self.policy_on = True

    # ---------------------------------------------------------- the moves
    def settle(self, restep=True):
        """stop and deal with foot stagger. The stock policy stands still about 0.4 s after a zero command (it does not
        march in place), so: zero command 1 s, wait for both feet loaded and the trunk at rest; if the feet are staggered
        by more than 15 mm, one settle step (a 0.3 s side-step command and a new stop, up to 2 times); then freeze into
        the SIT.md stance (policy off, 1 s ramp, 1.5 s hold)."""
        tries = 0
        while True:
            for _ in range(50):
                self.step((0, 0, 0))
            for i in range(50):
                self.step((0, 0, 0))
                if min(self.foot_forces()) > 5 and np.linalg.norm(self.data.qvel[:3]) < 0.02:
                    break
            stg0 = float(self.stagger())
            if not restep or abs(stg0) < 15 or tries >= 2 or self.fallen:
                break
            tries += 1
            for _ in range(15):
                self.step((0, 0.07 * (1 if tries % 2 else -1), 0))
        self.go(S.targets(self.model, *STAND), 1.0)
        self.hold(1.5)
        return dict(resteps=tries, stagger_before_stance_mm=stg0, stagger_mm=float(self.stagger()))

    def sit_down(self, t_off=3.0):
        """the SIT.md section 5 path (sit_sim.DOWN, SIT), 0.5 s, torque off, t_off s to settle"""
        md = self.model
        self.sit_collisions(True)
        self.sitting = True
        self.sit_surface = getattr(self, "force_surface", None) or ("plane" if (self.has_mat and self.wholly_on_mat()) else "field")
        self.mat_mode(self.sit_surface)
        for (h, k, a, n, hd), T in S.DOWN:
            self.go(S.targets(md, h, k, a, n, hd), T)
        self.go(S.targets(md, *S.SIT), 1.5)
        self.hold(0.5)
        self.torque(False)
        self.hold(t_off)

    def stand_up(self, T=1.5):
        """sit_sim.rise(): torque on at the present angles, roll and yaw back to 0, the UP path, the stance"""
        md, dd = self.model, self.data
        q = np.array([dd.qpos[md.jnt_qposadr[md.actuator_trnid[i, 0]]] for i in range(md.nu)])
        c = np.clip(q, md.actuator_ctrlrange[:, 0], md.actuator_ctrlrange[:, 1])
        dd.ctrl[:] = c
        self.torque(True)
        self.hold(0.3)
        hp = np.degrees(q[S.aid(md, "left_hip_pitch")])
        n, hd = S.NH
        self.go(S.targets(md, hp, 147, -92, n, hd, 0.0, 0.0), 1.0)
        for w in S.UP:
            self.go(S.targets(md, *w, n, hd, 0.0, 0.0), T)
        self.go(S.targets(md, *STAND, 0, 0, 0.0, 0.0), 1.5)
        self.hold(1.0)
        self.sitting = False
        self.sit_collisions(False)
        self.mat_mode("field")

    # ---------------------------------------------------------- reports
    def contact_forces(self):
        """normal force per robot geom against the world, N"""
        md, dd = self.model, self.data
        F = {}
        for i in range(dd.ncon):
            w = np.zeros(6)
            mujoco.mj_contactForce(md, dd, i, w)
            if w[0] <= 0:
                continue
            c = dd.contact[i]
            for g in (c.geom1, c.geom2):
                if md.geom_bodyid[g] > 0 and md.body(md.geom_bodyid[g]).name not in ("floor", "walls"):
                    n = mujoco.mj_id2name(md, mujoco.mjtObj.mjOBJ_GEOM, g) or "geom%d" % g
                    F[n] = F.get(n, 0.0) + float(w[0])
        return F

    def joints_on_stops(self):
        md, dd = self.model, self.data
        out = {}
        for i in range(dd.nefc):
            if dd.efc_type[i] == mujoco.mjtConstraint.mjCNSTR_LIMIT_JOINT:
                j = dd.efc_id[i]
                out[mujoco.mj_id2name(md, mujoco.mjtObj.mjOBJ_JOINT, j)] = round(abs(float(dd.efc_force[i])), 3)
        return out

    def current_report(self):
        out = {}
        for k, (n, sb, mb, mi) in self.cur.items():
            out[k] = dict(secs=round(n * 0.002, 2), bus_mean_A=round(sb / max(n, 1), 3), bus_peak_20ms_A=round(mb, 3), servo_peak_A=round(mi, 3))
        return out


# ---------------------------------------------------------------- zone scoring (the rules of coverage.py on the sim's pin tips)
def score_nest(pins, need_force=True):
    """pins: {seat_L, seat_R, bump_L, bump_R: dict(xy, F)}; world m, the sun centre is the origin.
    lenient (coverage.ok_concentric): at least one seat pin on the sun and one bumper pin on the ring, no pin on the wrong zone.
    strict: all four pins on their own zone. A pin counts when its spring is compressed (F > 0)."""
    r = {k: float(np.hypot(*v["xy"])) for k, v in pins.items()}
    made = {k: (v["F"] > 0 or not need_force) for k, v in pins.items()}
    ring_ok = {k: (WALL_X - v["xy"][0]) > RING_BACK + TIP_M for k, v in pins.items()}
    ring_any = {k: (WALL_X - v["xy"][0]) > RING_BACK - TIP_M for k, v in pins.items()}
    seat = [k for k in pins if k.startswith("seat")]
    bump = [k for k in pins if k.startswith("bump")]
    seat_on = [made[k] and r[k] < RC - TIP_M for k in seat]
    seat_bad = [made[k] and (RC + GAP - TIP_M < r[k] < ROUT + TIP_M) and ring_any[k] for k in seat]
    bump_on = [made[k] and (RC + GAP + TIP_M < r[k] < ROUT - TIP_M) and ring_ok[k] for k in bump]
    bump_bad = [made[k] and r[k] < RC + TIP_M for k in bump]
    bridge = bool(any(seat_bad) or any(bump_bad))
    return dict(ok=bool(any(seat_on) and any(bump_on) and not bridge), strict=bool(all(seat_on) and all(bump_on)), bridge=bridge,
                seat_on=int(sum(seat_on)), bump_on=int(sum(bump_on)), r_mm={k: round(v * 1000, 1) for k, v in r.items()})


def score_rug(pins, shift=0.0, need_force=True):
    """the pond rug bands; shift (m) moves the landing away from the wall (a rug-specific aim point).
    ok: seat on the sand band (plus), bumper on the blue band (minus), no pin on the wrong band (no bridge chip needed)."""
    made = {k: (v["F"] > 0 or not need_force) for k, v in pins.items()}
    d = {k: WALL_X - (v["xy"][0] - shift) for k, v in pins.items()}
    y = {k: v["xy"][1] for k, v in pins.items()}

    def inb(k, B, m_):
        return made[k] and (B[0] + m_ < d[k] < B[1] - m_) and abs(y[k]) < RUG_HALF - m_
    seat = [k for k in pins if k.startswith("seat")]
    bump = [k for k in pins if k.startswith("bump")]
    seat_on = [inb(k, RUG_A, TIP_M) for k in seat]
    bump_on = [inb(k, RUG_B, TIP_M) for k in bump]
    seat_bad = [inb(k, RUG_B, -TIP_M) for k in seat]
    bump_bad = [inb(k, RUG_A, -TIP_M) for k in bump]
    bridge = bool(any(seat_bad) or any(bump_bad))
    return dict(ok=bool(any(seat_on) and any(bump_on) and not bridge), strict=bool(all(seat_on) and all(bump_on)), bridge=bridge)
