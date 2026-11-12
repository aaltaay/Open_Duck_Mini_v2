"""Pushes on the frozen charging stance, torque on (position hold, no balance controller). sim pass only."""
import json,numpy as np,mujoco as m,rest
D=np.radians; out=[]
st=rest.run(('st',(D(-15),D(5),0,0,0,0),{'no_off':True}))
md=rest.model('',0.068,0.56); tr=m.mj_name2id(md,1,'trunk_assembly')
for dirn,v in (('front',(1,0,0)),('back',(-1,0,0)),('side',(0,1,0))):
    for F in (3,5,8,12,16,20,25):
        dd=m.MjData(md); dd.qpos[:]=st['qpos']; m.mj_forward(md,dd)
        q=np.array([dd.qpos[md.jnt_qposadr[md.actuator_trnid[i,0]]] for i in range(md.nu)]); dd.ctrl[:]=q
        for i in range(200): m.mj_step(md,dd)
        p0=dd.qpos[:2].copy(); fell=False
        for i in range(2000):
            dd.xfrc_applied[:]=0
            if i<100: dd.xfrc_applied[tr,:3]=np.array(v)*F
            m.mj_step(md,dd)
            if dd.xmat[tr][8]<0.5: fell=True
        out.append(dict(dir=dirn,F=F,fell=fell,slide_mm=float(np.linalg.norm(dd.qpos[:2]-p0)*1000)))
    print(dirn,[(o['F'],o['fell'],round(o['slide_mm'],1)) for o in out if o['dir']==dirn])
json.dump(out,open('res_push.json','w'))
