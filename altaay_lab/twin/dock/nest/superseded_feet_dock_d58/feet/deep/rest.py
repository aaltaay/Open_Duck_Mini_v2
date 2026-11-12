"""Torque-off rest pose search (sim pass only). Model: ours_b (2.767 kg) with every visual mesh made a floor collider
(contype 0, conaffinity 1: robot touches floor/mat features, no self-collision). Entry: from the charging stance, position
control to the target over 3 s, hold 1 s. Then torque off (kp 0) and 35 s with 3 N pushes (0.2 s) at 10, 15, 20, 25 s.
Pads: pin rows fixed on the mat where the soles stood in the charging stance (7 pins at 6 mm pitch, rows at +/-26 mm);
a pad is 'made' if >=2 of its pins are under the pad outline and the pad surface there is within 1.0 mm of the mat
(pins stand 1.5 mm proud, the pad is 0.3 mm recessed, 0.2 mm kept for stroke)."""
import sys, json, itertools, numpy as np, mujoco as m
from multiprocessing import Pool
D=np.radians
SRC=os.path.join(os.environ.get("FEET_SCRATCH") or os.path.join(__import__("tempfile").gettempdir(), "feet_scratch"),'feet','model')  # the model folder, built outside the repo
def build(extra='', fric=0.068, damp=0.56, mu=0.8):
    x=open(SRC+'/scene_flat_terrain.xml').read()
    x=x.replace('friction="0.6" condim="3"/>',f'friction="{mu}" condim="3"/>\n{extra}')
    import os, hashlib
    p=SRC+'/_rest_'+hashlib.md5(x.encode()).hexdigest()[:8]+f'_{os.getpid()}.xml'
    open(p,'w').write(x); md=m.MjModel.from_xml_path(p); os.remove(p)
    return md
_cache={}
def model(extra, fric, damp, mu=0.8):
    k=(extra,fric,damp,mu)
    if k in _cache: return _cache[k]
    md=build(extra,fric,damp,mu)
    for g in range(md.ngeom):
        if md.geom_group[g]==2 and md.geom_contype[g]==0:
            md.geom_conaffinity[g]=1; md.geom_contype[g]=0; md.geom_friction[g]=[0.8,0.02,0.002]
            md.body_conaffinity[md.geom_bodyid[g]]|=1
    for j in range(1,md.njnt):
        md.dof_frictionloss[md.jnt_dofadr[j]]=fric; md.dof_damping[md.jnt_dofadr[j]]=damp
    _cache[k]=md; return md
LEG=['hip_yaw','hip_roll','hip_pitch','knee','ankle']
def targets(md,h,k,a,neck=0.0,head=0.0,roll=0.0):
    c=np.zeros(md.nu)
    for side,s in (('left',1),('right',-1)):
        c[m.mj_name2id(md,19,f'{side}_hip_pitch')]=s*h; c[m.mj_name2id(md,19,f'{side}_knee')]=k; c[m.mj_name2id(md,19,f'{side}_ankle')]=a
        c[m.mj_name2id(md,19,f'{side}_hip_roll')]=s*roll
    c[m.mj_name2id(md,19,'neck_pitch')]=neck; c[m.mj_name2id(md,19,'head_pitch')]=head
    return c
STANCE=(D(-15),D(5),0.0)
def sole_info(md,dd):
    out=[]
    for nm,b in (('left_foot_bottom_tpu','foot_assembly'),('right_foot_bottom_tpu','foot_assembly_2')):
        g=m.mj_name2id(md,5,nm); bi=m.mj_name2id(md,1,b)
        mid=md.geom_dataid[g]; a,n=md.mesh_vertadr[mid],md.mesh_vertnum[mid]
        vw=md.mesh_vert[a:a+n]@dd.geom_xmat[g].reshape(3,3).T+dd.geom_xpos[g]
        low=vw[vw[:,2]<vw[:,2].min()+0.002]
        R=dd.xmat[bi].reshape(3,3); p=dd.xpos[bi]
        c=((low-p)@R).mean(0); ax=np.argmax(abs(R[0,:])); f=np.zeros(3); f[ax]=np.sign(R[0,ax])
        nz=np.argmax(abs(R[2,:])); nn=np.zeros(3); nn[nz]=np.sign(R[2,nz])   # local 'up' of the sole
        l=np.cross(nn,f)
        out.append((bi,c,f,l))
    return out
def pad_state(md,dd,SI,pins):
    res={}
    names=[('L','toe','CHG+'),('L','heel','SENSE'),('R','toe','SYS'),('R','heel','GND')]
    for (side,end,net) in names:
        j=0 if side=='L' else 1; bi,c,f,l=SI[j]
        R=dd.xmat[bi].reshape(3,3); p=dd.xpos[bi]
        cnt=0
        for P in pins[(side,end)]:
            # find the sole point above pin P: solve in the sole plane (iterate on local x,y)
            loc=np.array([0.0,0.0])
            for _ in range(3):
                w=p+R@(c+loc[0]*f+loc[1]*l)
                fw=R@f; lw=R@l
                d=np.array([P[0]-w[0],P[1]-w[1]])
                A=np.array([[fw[0],lw[0]],[fw[1],lw[1]]])
                loc=loc+np.linalg.lstsq(A,d,rcond=None)[0]
            pc=0.026 if end=='toe' else -0.026
            inside=abs(loc[0]-pc)<0.021 and abs(loc[1])<0.016
            z=(p+R@(c+loc[0]*f+loc[1]*l))[2]
            if inside and z<0.0010+FLOOR_Z: cnt+=1
        res[net]=cnt
    return res
FLOOR_Z=0.0
def floor_contacts(md,dd):
    B={}
    for i in range(dd.ncon):
        c=dd.contact[i]; f=np.zeros(6); m.mj_contactForce(md,dd,i,f)
        for g in (c.geom1,c.geom2):
            b=md.body(md.geom_bodyid[g]).name
            if b!='world' and b!='floor': B[b]=B.get(b,0)+f[0]
    return {k:round(v,1) for k,v in B.items() if v>0.2}
def run(args):
    name,(h,k,a,neck,head,roll),opt=args
    md=model(opt.get('extra',''),opt.get('fric',0.068),opt.get('damp',0.56),opt.get('mu',0.8))
    dd=m.MjData(md)
    # start in the charging stance, soles flat (pitch from the stance study: trunk 10 deg nose-up)
    q=md.key_qpos[0].copy(); c0=targets(md,*STANCE)
    for i in range(md.nu): q[md.jnt_qposadr[md.actuator_trnid[i,0]]]=c0[i]
    pit=D(-10.0); q[3:7]=[np.cos(pit/2),0,np.sin(pit/2),0]; q[0:3]=[0,0,0.3]
    dd.qpos[:]=q; m.mj_kinematics(md,dd)
    zmin=min(dd.geom_xpos[g][2] for g in range(1)) 
    # drop to touch: lower until the lowest sole vertex is at 0
    SI=None
    def lowest():
        z=1
        for nm in ('left_foot_bottom_tpu','right_foot_bottom_tpu'):
            g=m.mj_name2id(md,5,nm); mid=md.geom_dataid[g]; a0,n=md.mesh_vertadr[mid],md.mesh_vertnum[mid]
            z=min(z,(md.mesh_vert[a0:a0+n]@dd.geom_xmat[g].reshape(3,3).T+dd.geom_xpos[g])[:,2].min())
        return z
    # flatten feet
    for _ in range(20):
        m.mj_kinematics(md,dd); R=dd.xmat[m.mj_name2id(md,1,'foot_assembly')].reshape(3,3)
        ax=np.argmax(abs(R[2,:])); n=R[:,ax]*np.sign(R[2,ax]); e=np.arctan2(n[0],n[2]); pit-=e
        dd.qpos[3:7]=[np.cos(pit/2),0,np.sin(pit/2),0]
    m.mj_kinematics(md,dd); dd.qpos[2]-=lowest()-0.0003
    dd.ctrl[:]=c0; m.mj_forward(md,dd)
    for i in range(500): m.mj_step(md,dd)
    SI=sole_info(md,dd)
    # pins where the soles stand now
    pins={}
    for j,side in enumerate('LR'):
        bi,c,f,l=SI[j]; R=dd.xmat[bi].reshape(3,3); p=dd.xpos[bi]
        for end,pc in (('toe',0.026),('heel',-0.026)):
            pins[(side,end)]=[(p+R@(c+pc*f+y*l))[:2] for y in np.arange(-0.018,0.0181,0.006)]
    pads0=pad_state(md,dd,SI,pins)
    trunk=m.mj_name2id(md,1,'trunk_assembly')
    c1=targets(md,h,k,a,neck,head,roll); T=opt.get('T_entry',3.0); n=int(T/md.opt.timestep)
    vmax_entry=0
    for i in range(n):
        s=(i+1)/n; s=0.5-0.5*np.cos(np.pi*s); dd.ctrl[:]=c0*(1-s)+c1*s; m.mj_step(md,dd)
        vmax_entry=max(vmax_entry,np.linalg.norm(dd.qvel[0:3]))
    for i in range(500): m.mj_step(md,dd)
    up_entry=dd.xmat[trunk][8]
    pads_entry=pad_state(md,dd,SI,pins); fc_entry=floor_contacts(md,dd)
    tau_entry=np.abs(dd.actuator_force).copy()
    if opt.get('no_off'): return dict(qpos=dd.qpos.round(5).tolist(),pads_entry=pads_entry,contacts=fc_entry,tau_max=float(tau_entry.max()))
    # torque off
    md2=md; gp=md.actuator_gainprm.copy(); bp=md.actuator_biasprm.copy()
    md.actuator_gainprm[:,0]=0; md.actuator_biasprm[:,1]=0; md.actuator_biasprm[:,2]=0
    vmax_off=0; P=[(10,(3,0,0)),(15,(-3,0,0)),(20,(0,3,0)),(25,(0,-3,0))]; pos25=None; mindown={}
    t=0; N=int(35/md.opt.timestep)
    for i in range(N):
        t=i*md.opt.timestep; dd.xfrc_applied[:]=0
        for t0,F in P:
            if t0<=t<t0+0.2: dd.xfrc_applied[trunk,:3]=F
        m.mj_step(md,dd)
        if t<9.5: vmax_off=max(vmax_off,abs(dd.qvel[2]))
        if abs(t-25.5)<1e-9 or (pos25 is None and t>=25.5): pos25=dd.qpos.copy()
        if i%250==0:
            ps=pad_state(md,dd,SI,pins)
            for kk,v in ps.items(): mindown[kk]=min(mindown.get(kk,99),v)
    md.actuator_gainprm[:]=gp; md.actuator_biasprm[:]=bp
    creep=float(np.abs(dd.qpos[7:]-pos25[7:]).max()); drift=float(np.linalg.norm(dd.qpos[0:3]-pos25[0:3])*1000)
    pads=pad_state(md,dd,SI,pins)
    R=dd.xmat[trunk].reshape(3,3)
    return dict(name=name,pose_deg=[round(float(np.degrees(v)),1) for v in (h,k,a,neck,head,roll)],opt={k_:v for k_,v in opt.items() if k_!='extra'},
        extra=bool(opt.get('extra')),pads_stance=pads0,entry_up=float(up_entry),entry_vmax=float(vmax_entry),pads_entry=pads_entry,contacts_entry=fc_entry,
        tau_entry_max=float(tau_entry.max()),tau_entry_sum=float(tau_entry.sum()),
        off_vz_peak=float(vmax_off),final_up=float(R[2,2]),final_fwd_z=float(R[2,0]),trunk_z_mm=float(dd.xpos[trunk][2]*1000),
        pads_final=pads,pads_min_during=mindown,contacts_final=floor_contacts(md,dd),joint_creep_deg_last10s=round(np.degrees(creep),2),base_drift_mm_last10s=round(drift,2),
        qpos=dd.qpos.round(4).tolist())
if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='grid':
        J=[]
        for h in D(np.arange(-60,31,15)):
            for k in D(np.arange(30,91,15)):
                for a in D(np.arange(-90,91,30)):
                    J.append((f'g',(h,k,a,0,0,0),{}))
        with Pool(int(sys.argv[2])) as p: R=p.map(run,J)
        json.dump(R,open('res_rest_grid.json','w'))
