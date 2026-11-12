"""Runtime turn_on(): kp 2 of 32 for 1 s, then init pos. Effect on the charging stance (sim pass only; sim kp scaled 2/32)."""
import json,numpy as np,mujoco as m,rest
D=np.radians
st=rest.run(('st',(D(-15),D(5),0,0,0,0),{'no_off':True}))
md=rest.model('',0.068,0.56); tr=m.mj_name2id(md,1,'trunk_assembly'); res={}
for scale in (2/32,4/32,8/32,1.0):
    dd=m.MjData(md); dd.qpos[:]=st['qpos']; m.mj_forward(md,dd)
    q=np.array([dd.qpos[md.jnt_qposadr[md.actuator_trnid[i,0]]] for i in range(md.nu)]); dd.ctrl[:]=q
    gp=md.actuator_gainprm.copy(); bp=md.actuator_biasprm.copy()
    md.actuator_gainprm[:,0]*=scale; md.actuator_biasprm[:,1]*=scale
    z0=dd.xpos[tr][2]; vz=0
    for i in range(500): m.mj_step(md,dd); vz=max(vz,abs(dd.qvel[2]))
    up=dd.xmat[tr][8]; z1=dd.xpos[tr][2]
    md.actuator_gainprm[:]=gp; md.actuator_biasprm[:]=bp
    pads=rest.pad_state(md,dd,rest.sole_info(md,dd),{})if False else None
    res[scale]=dict(up=float(up),sag_mm=float((z0-z1)*1000),vz=float(vz))
    print('kp x%.3f: after 1 s trunk up %.2f, sag %.0f mm, peak vz %.2f m/s'%(scale,up,(z0-z1)*1000,vz))
json.dump({str(k):v for k,v in res.items()},open('res_lowkp.json','w'))
