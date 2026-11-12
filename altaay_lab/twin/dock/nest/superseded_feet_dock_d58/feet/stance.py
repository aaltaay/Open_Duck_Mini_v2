"""Charging stance study, sim pass only. MuJoCo 3.17, lab model ours_b (2.767 kg)."""
import json, sys, numpy as np, mujoco as m
import os
D = os.path.join(os.environ.get("FEET_SCRATCH") or os.path.join(__import__("tempfile").gettempdir(), "feet_scratch"), 'feet', 'model', 'scene_flat_terrain.xml')  # the model folder, built outside the repo
mod = m.MjModel.from_xml_path(D)
dat = m.MjData(mod)
J = lambda n: mod.jnt_qposadr[m.mj_name2id(mod, 3, n)]
A = lambda n: m.mj_name2id(mod, 19, n)
LEG = ['hip_yaw', 'hip_roll', 'hip_pitch', 'knee', 'ankle']
TRUNK = m.mj_name2id(mod, 1, 'trunk_assembly')
FL, FR = m.mj_name2id(mod, 1, 'foot_assembly'), m.mj_name2id(mod, 1, 'foot_assembly_2')
SOLE = [m.mj_name2id(mod, 5, 'left_foot_bottom_tpu'), m.mj_name2id(mod, 5, 'right_foot_bottom_tpu')]

def geom_minz(g):
    mid = mod.geom_dataid[g]
    if mid < 0: return dat.geom_xpos[g][2]
    a, n = mod.mesh_vertadr[mid], mod.mesh_vertnum[mid]
    v = mod.mesh_vert[a:a + n] @ dat.geom_xmat[g].reshape(3, 3).T + dat.geom_xpos[g]
    return v[:, 2].min()

def body_minz(b):
    return min(geom_minz(g) for g in range(mod.ngeom) if mod.geom_bodyid[g] == b)

def setpose(h, k, a, pitch=0.0):
    q = mod.key_qpos[0].copy()
    for side, s in (('left', 1), ('right', -1)):
        q[J(f'{side}_hip_yaw')] = 0; q[J(f'{side}_hip_roll')] = 0
        q[J(f'{side}_hip_pitch')] = s * h; q[J(f'{side}_knee')] = k; q[J(f'{side}_ankle')] = a
    for n in ['neck_pitch', 'head_pitch', 'head_yaw', 'head_roll']: q[J(n)] = 0
    q[3:7] = [np.cos(pitch / 2), 0, np.sin(pitch / 2), 0]
    q[0:3] = [0, 0, 0.3]
    dat.qpos[:] = q; dat.qvel[:] = 0
    m.mj_kinematics(mod, dat)
    # flatten feet by trunk pitch (Newton on foot z axis x-component)
    return q

def flat_pose(h, k, a):
    p = 0.0
    for _ in range(30):
        setpose(h, k, a, p)
        R = dat.xmat[FL].reshape(3, 3)
        # sole normal: the axis of the foot frame closest to world z
        ax = np.argmax(abs(R[2, :])); n = R[:, ax] * np.sign(R[2, ax])
        err = np.arctan2(n[0], n[2])
        if abs(err) < 1e-6: break
        p -= err
    zmin = min(geom_minz(g) for g in SOLE)
    dat.qpos[2] -= zmin; m.mj_kinematics(mod, dat); m.mj_comPos(mod, dat)
    return p

def support_ok():
    m.mj_kinematics(mod, dat)
    com = dat.subtree_com[1]
    xs = []
    for g in SOLE:
        mid = mod.geom_dataid[g]; a, n = mod.mesh_vertadr[mid], mod.mesh_vertnum[mid]
        v = mod.mesh_vert[a:a + n] @ dat.geom_xmat[g].reshape(3, 3).T + dat.geom_xpos[g]
        xs.append(v[v[:, 2] < v[:, 2].min() + 0.002][:, 0])
    xs = np.concatenate(xs)
    return com[0], xs.min(), xs.max()

def hold(h, k, a, T=4.0, kp=None, torque_off=False):
    p = flat_pose(h, k, a)
    dat.qpos[2] += 0.0005
    ctrl = np.zeros(mod.nu)
    for side, s in (('left', 1), ('right', -1)):
        ctrl[A(f'{side}_hip_pitch')] = s * h; ctrl[A(f'{side}_knee')] = k; ctrl[A(f'{side}_ankle')] = a
    dat.ctrl[:] = ctrl
    gp = mod.actuator_gainprm.copy(); bp = mod.actuator_biasprm.copy()
    if torque_off:
        mod.actuator_gainprm[:, 0] = 0; mod.actuator_biasprm[:, 1] = 0
    m.mj_forward(mod, dat)
    z0 = dat.qpos[2]; taus = []
    for i in range(int(T / mod.opt.timestep)):
        m.mj_step(mod, dat)
        if i * mod.opt.timestep > T - 1.0: taus.append(dat.actuator_force.copy())
    mod.actuator_gainprm[:] = gp; mod.actuator_biasprm[:] = bp
    up = dat.xmat[TRUNK].reshape(3, 3)[2, 2]
    tau = np.mean(taus, 0)
    belly = body_minz(TRUNK)
    # sole normal forces
    f = np.zeros(6); fz = [0.0, 0.0]
    for c in range(dat.ncon):
        con = dat.contact[c]
        for i, g in enumerate(SOLE):
            if g in (con.geom1, con.geom2):
                m.mj_contactForce(mod, dat, c, f); fz[i] += f[0]
    return dict(h=h, k=k, a=a, trunk_pitch_deg=float(np.degrees(p)), base_z=float(dat.qpos[2]), z0=float(z0),
                upright=float(up), belly_mm=float(belly * 1000), sole_N=[float(x) for x in fz],
                tau={mod.actuator(i).name: float(tau[i]) for i in range(mod.nu)},
                sumabs=float(np.abs(tau).sum()), maxabs=float(np.abs(tau).max()))

if __name__ == '__main__':
    out = {}
    # 1. scan standing poses: ankle chosen to keep trunk roughly level is not forced; scan h,k with a = -(h+k)+off
    res = []
    for h in np.radians(np.arange(-40, 11, 5)):
        for k in np.radians(np.arange(0, 91, 5)):
            for da in np.radians(np.arange(-15, 16, 5)):
                a = -(h + k) + da
                if not (-1.57 < a < 1.57): continue
                p = flat_pose(h, k, a)
                if abs(np.degrees(p)) > 20: continue
                cx, x0, x1 = support_ok()
                if not (x0 + 0.01 < cx < x1 - 0.01): continue
                r = hold(h, k, a, T=3.0)
                if r['upright'] < 0.97 or abs(r['base_z'] - r['z0']) > 0.01: continue
                r['com_margin_mm'] = float(min(cx - x0, x1 - cx) * 1000)
                res.append(r)
    res.sort(key=lambda r: r['sumabs'])
    out['scan_n'] = len(res)
    tall = [r for r in res if r['base_z'] > 0.95 * max(x['base_z'] for x in res)]
    out['best_any'] = res[0]; out['best_tall'] = sorted(tall, key=lambda r: r['sumabs'])[0]
    out['home'] = hold(-0.63, 1.368, -0.784, T=4)
    out['crouch'] = hold(np.radians(-40), np.radians(80), np.radians(-40), T=4)
    out['straight'] = hold(0, 0, 0, T=4)
    # torque off from the best tall pose and straight legs
    b = out['best_tall']
    out['off_best'] = hold(b['h'], b['k'], b['a'], T=4, torque_off=True)
    out['off_straight'] = hold(0, 0, 0, T=4, torque_off=True)
    out['off_slight_hyper'] = hold(0.05, -0.05, 0, T=4, torque_off=True)
    json.dump(out, open(sys.argv[1], 'w'), indent=1)
    for kk in ['best_any', 'best_tall', 'home', 'crouch', 'straight', 'off_best', 'off_straight', 'off_slight_hyper']:
        r = out[kk]; print(kk, {x: (round(v, 3) if isinstance(v, float) else v) for x, v in r.items() if x != 'tau'})
        print('   ', {x: round(v, 3) for x, v in r['tau'].items() if abs(v) > 0.005})
