"""Nest sit: robustness of the torque-off sit and the rise back to the stance. sim pass only."""
import json,numpy as np,mujoco as m, rest
D=np.radians
P=(D(20),D(70),D(-75),0,0,0)
out={}
def tail_info(r,opt):
    md=rest.model(opt.get('extra',''),opt.get('fric',0.068),opt.get('damp',0.56)); dd=m.MjData(md); dd.qpos[:]=r['qpos']; m.mj_forward(md,dd)
    tr=m.mj_name2id(md,1,'trunk_assembly'); R=dd.xmat[tr].reshape(3,3); p=dd.xpos[tr]
    res=[]
    for i in range(dd.ncon):
        c=dd.contact[i]
        for g in (c.geom1,c.geom2):
            bn=md.body(md.geom_bodyid[g]).name
            if bn in('trunk_assembly','head_assembly','foot_assembly','foot_assembly_2','knee_and_ankle_assembly','knee_and_ankle_assembly_3'):
                res.append((bn,np.round((c.pos-p)@R*1000,0).tolist(),np.round(c.pos[:2]*1000,0).tolist()))
    pitch=np.degrees(np.arcsin(-np.clip(R[2,0],-1,1)))
    return res,float(pitch)
cases={'model fric 0.068 damp 0.56':{},'power-off est: fric 0.068 damp 0.05':{'damp':0.05},'stiff gears est: fric 0.2 damp 0.05':{'fric':0.2,'damp':0.05},'slow entry 6 s':{'T_entry':6.0},'smooth mat mu 0.4':{'mu':0.4}}
for k,opt in cases.items():
    r=rest.run(('nest',P,opt)); ti,pitch=tail_info(r,opt)
    out[k]=dict(r=r,contacts=ti,trunk_pitch_deg=pitch)
    print(k,'| entry up %.2f vz_off %.3f final up %.2f pitch %.1f drift %.1f mm creep %.2f deg'%(r['entry_up'],r['off_vz_peak'],r['final_up'],pitch,r['base_drift_mm_last10s'],r['joint_creep_deg_last10s']),'pads',r['pads_final'])
    for c in ti: print('    ',c)
# rise from the settled nest
r=out['model fric 0.068 damp 0.56']['r']
md=rest.model('',0.068,0.56); dd=m.MjData(md); dd.qpos[:]=r['qpos']; m.mj_forward(md,dd)
q=np.array([dd.qpos[md.jnt_qposadr[md.actuator_trnid[i,0]]] for i in range(md.nu)])
tr=m.mj_name2id(md,1,'trunk_assembly')
seq=[(q,0.5),(rest.targets(md,*P),2.5),(rest.targets(md,D(0),D(40),D(-40)),2.0),(rest.targets(md,*rest.STANCE),2.0)]
dd.ctrl[:]=q; cur=q.copy(); taumax=np.zeros(md.nu); log=[]
for tgt,T in seq:
    n=int(T/md.opt.timestep)
    for i in range(n):
        s=(i+1)/n; s=0.5-0.5*np.cos(np.pi*s); dd.ctrl[:]=cur*(1-s)+tgt*s; m.mj_step(md,dd); taumax=np.maximum(taumax,abs(dd.actuator_force))
    cur=tgt.copy(); log.append(float(dd.xmat[tr][8]))
for i in range(1000): m.mj_step(md,dd)
up=float(dd.xmat[tr][8])
names=[md.actuator(i).name for i in range(md.nu)]
print('rise: up after each stage',np.round(log,2),'final up %.2f trunk z %.0f mm'%(up,dd.xpos[tr][2]*1000),'peak tau',{names[i]:round(taumax[i],2) for i in np.argsort(-taumax)[:5]})
out['rise']=dict(up_stages=log,final_up=up,peak_tau={names[i]:float(taumax[i]) for i in range(md.nu)},qpos=dd.qpos.tolist())
json.dump(out,open('res_nest.json','w'),default=float)
