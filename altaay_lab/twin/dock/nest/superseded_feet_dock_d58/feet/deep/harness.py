"""Shared harness: lab current_budget MjInfer (upstream, unmodified) on the ours_b model, scene variants. sim pass only."""
import os, sys, shutil, numpy as np
SCR=os.environ.get("FEET_SCRATCH") or os.path.join(__import__("tempfile").gettempdir(), "feet_scratch")  # scratch folder outside the repo
SRC=SCR+'/feet/model'; WORK=SCR+'/feet_deep'
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..','..','..','..','sim'))  # altaay_lab/sim, relative to this file
os.environ.setdefault("ODM_OUT", WORK+'/cb_out')
import mujoco
import current_budget as CB
MI=CB.MI
_DIR=[SRC]
def _ga():
    a={}
    for f in os.listdir(SRC+'/assets'): a[f]=open(SRC+'/assets/'+f,'rb').read()
    for f in os.listdir(_DIR[0]):
        if f.endswith('.xml'): a[f]=open(_DIR[0]+'/'+f,'rb').read()
    return a
CB.base.get_assets=_ga; sys.modules["playground.open_duck_mini_v2.base"].get_assets=_ga
import playground.open_duck_mini_v2.mujoco_infer_base as MIB; MIB.base.get_assets=_ga

MATTOP="0.8 0.02 0.002"
def scene(name, floor_mu=0.6, soft=False, mat_h=0.0, bevel=0.035, foot_dm=0.0):
    d=f'{WORK}/models/{name}'
    if os.path.exists(d+'/scene.xml'): return d
    os.makedirs(d,exist_ok=True)
    for f in os.listdir(SRC):
        if f.endswith('.xml'): shutil.copy(SRC+'/'+f,d)
    if foot_dm:
        import xml.etree.ElementTree as ET
        p=d+'/open_duck_mini_v2.xml'; tr=ET.parse(p)
        for bd in tr.getroot().iter('body'):
            if bd.get('name') in ('foot_assembly','foot_assembly_2'):
                it=bd.find('inertial'); it.set('mass',f"{float(it.get('mass'))+foot_dm:.7f}")
        tr.write(p)
    sr='solref="0.05 1" solimp="0.6 0.9 0.01"' if soft else ''
    mat=''
    if mat_h>0:
        L,W=0.2,0.15; t=L-bevel; h=mat_h
        v=[]
        for y in (-W,W):
            v+= [(-L,y,0),(L,y,0),(-t,y,h),(t,y,h)]
        vs=' '.join(f'{a:.4f} {b:.4f} {c:.4f}' for a,b,c in v)
        zc=h*(2*L+2*2*t)/(3*(2*L+2*t))
        mat=f'<geom name="mat" pos="0 0 {zc:.6f}" type="mesh" mesh="matmesh" rgba="0.55 0.75 0.55 1" friction="{MATTOP}" contype="1" conaffinity="1" priority="2"/>'
        matasset=f'<mesh name="matmesh" vertex="{vs}"/>'
    else: matasset=''
    xml=f'''<mujoco model="scene"><include file="open_duck_mini_v2.xml"/>
<asset>{matasset}</asset>
<worldbody><body name="floor"><geom name="floor" size="0 0 0.01" type="plane" contype="1" conaffinity="0" priority="1" friction="{floor_mu} 0.02 0.002" condim="3" {sr}/>
</body>{mat}</worldbody>
<keyframe><key name="home" qpos="0 0 0.15 1 0 0 0 0.002 0.053 -0.63 1.368 -0.784 0 0 0 0 -0.003 -0.065 0.635 1.379 -0.796" ctrl="0.002 0.053 -0.63 1.368 -0.784 0 0 0 0 -0.003 -0.065 0.635 1.379 -0.796"/></keyframe></mujoco>'''
    open(d+'/scene.xml','w').write(xml)
    return d

class Sim:
    def __init__(self, d, seed=0, x0=0.0, y0=0.0, yaw0=0.0):
        _DIR[0]=d
        m=MI.MjInfer(d+'/scene.xml', CB.REF, CB.ONNX, standing=False)
        _ga0=m.get_accelerometer
        m.get_accelerometer=lambda dd,_g=_ga0: (lambda a:(a.__setitem__(0,a[0]-1.3),a)[1])(np.array(_g(dd),float))
        self.m=m; self.model=m.model; self.data=m.data
        fb=m._floating_base_qpos_addr; self.fb=fb
        rng=np.random.default_rng(seed); self.rng=rng
        qa=np.array(m.actuator_joint_qpos_addr).ravel(); self.qa=qa
        self.data.qpos[qa]+=rng.uniform(-0.03,0.03,len(qa))
        self.data.qpos[fb]=x0; self.data.qpos[fb+1]=y0
        self.data.qpos[fb+3:fb+7]=[np.cos(yaw0/2),0,0,np.sin(yaw0/2)]
        self.data.qpos[fb+2]+=0.002
        mujoco.mj_forward(self.model,self.data)
        self.t=0.0; self.k=0; self.policy_on=True; self.fallen=False; self.tfall=None
        md=self.model
        self.trunk=md.body('trunk_assembly').id
        self.feet=[md.body('foot_assembly').id, md.body('foot_assembly_2').id]
        self.soles=[mujoco.mj_name2id(md,5,'left_foot_bottom_tpu'),mujoco.mj_name2id(md,5,'right_foot_bottom_tpu')]
        self._sole_frames()
    def _sole_frames(self):
        md,dd=self.model,self.data; self.sf=[]
        for g,b in zip(self.soles,self.feet):
            mid=md.geom_dataid[g]; a,n=md.mesh_vertadr[mid],md.mesh_vertnum[mid]
            vw=md.mesh_vert[a:a+n]@dd.geom_xmat[g].reshape(3,3).T+dd.geom_xpos[g]
            low=vw[vw[:,2]<vw[:,2].min()+0.002]
            R=dd.xmat[b].reshape(3,3); p=dd.xpos[b]
            loc=(low-p)@R
            c=loc.mean(0)
            # forward axis: body axis best aligned with world x at start
            ax=np.argmax(abs(R[0,:])); f=np.zeros(3); f[ax]=np.sign(R[0,ax])
            self.sf.append((c,f))
    def feet_pose(self):
        out=[]
        for (c,f),b in zip(self.sf,self.feet):
            R=self.data.xmat[b].reshape(3,3); p=self.data.xpos[b]
            cw=p+R@c; fw=R@f
            out.append((cw[0],cw[1],np.arctan2(fw[1],fw[0])))
        return np.array(out)
    def trunk_pose(self):
        fb=self.fb; q=self.data.qpos[fb+3:fb+7]
        R=np.zeros(9); mujoco.mju_quat2Mat(R,q); R=R.reshape(3,3)
        return self.data.qpos[fb:fb+3].copy(), np.arctan2(R[1,0],R[0,0]), R[2,2]
    def foot_forces(self):
        F=[0.0,0.0]; md,dd=self.model,self.data
        for i in range(dd.ncon):
            c=dd.contact[i]
            for j,b in enumerate(self.feet):
                if md.geom_bodyid[c.geom1]==b or md.geom_bodyid[c.geom2]==b:
                    f=np.zeros(6); mujoco.mj_contactForce(md,dd,i,f); F[j]+=f[0]
        return F
    def step(self, cmd=(0,0,0)):
        """one 50 Hz control period"""
        m=self.m
        for _ in range(m.decimation):
            mujoco.mj_step(self.model,self.data); self.t+=m.sim_dt
        if self.policy_on:
            m.commands=list(cmd)+[0,0,0,0]
            m.imitation_i=(m.imitation_i+m.phase_frequency_factor)%m.PRM.nb_steps_in_period
            ph=m.imitation_i/m.PRM.nb_steps_in_period*2*np.pi
            m.imitation_phase=np.array([np.cos(ph),np.sin(ph)])
            obs=m.get_obs(self.data,m.commands); a=m.policy.infer(obs)
            m.last_last_last_action=m.last_last_action.copy(); m.last_last_action=m.last_action.copy(); m.last_action=a.copy()
            m.motor_targets=m.default_actuator+a*m.action_scale
            if MI.USE_MOTOR_SPEED_LIMITS:
                m.motor_targets=np.clip(m.motor_targets,m.prev_motor_targets-m.max_motor_velocity*(m.sim_dt*m.decimation),m.prev_motor_targets+m.max_motor_velocity*(m.sim_dt*m.decimation))
                m.prev_motor_targets=m.motor_targets.copy()
            self.data.ctrl=m.motor_targets.copy()
        p,yaw,upz=self.trunk_pose()
        if (p[2]<0.10 or upz<0.5) and not self.fallen: self.fallen=True; self.tfall=self.t
