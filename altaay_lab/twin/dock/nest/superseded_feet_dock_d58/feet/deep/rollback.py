import json,numpy as np,mujoco as m, rest
D=np.radians
N=json.load(open('res_nest.json')); r=N['model fric 0.068 damp 0.56']['r']
md=rest.model('',0.068,0.56); dd=m.MjData(md); dd.qpos[:]=r['qpos']; m.mj_forward(md,dd)
q=np.array([dd.qpos[md.jnt_qposadr[md.actuator_trnid[i,0]]] for i in range(md.nu)])
tr=m.mj_name2id(md,1,'trunk_assembly'); hd=m.mj_name2id(md,1,'head_assembly')
out={}
for T in (1.0,2.0):
    dd.qpos[:]=r['qpos']; dd.qvel[:]=0; m.mj_forward(md,dd); cur=q.copy(); vpk=0; hv=0
    for tg,TT in [((D(-30),D(30),D(0),D(-20),0,0),T),((D(-30),D(30),D(0),D(-20),0,0),1.0)]:
        tgt=rest.targets(md,*tg); n=int(TT/md.opt.timestep)
        for i in range(n):
            s=(i+1)/n; s=0.5-0.5*np.cos(np.pi*s); dd.ctrl[:]=cur*(1-s)+tgt*s; m.mj_step(md,dd)
            vpk=max(vpk,np.linalg.norm(dd.cvel[tr][3:])); hv=max(hv,np.linalg.norm(dd.cvel[hd][3:]))
        cur=tgt
    R=dd.xmat[tr].reshape(3,3)
    out[T]=dict(trunk_v_peak=float(vpk),head_v_peak=float(hv),up=float(R[2,2]),qpos=dd.qpos.tolist())
    print('roll back T',T,'trunk v peak %.2f m/s head v peak %.2f, final trunk z-axis z %.2f, x-axis z %.2f'%(vpk,hv,R[2,2],R[2,0]), rest.floor_contacts(md,dd))
json.dump(out,open('res_rollback.json','w'))
