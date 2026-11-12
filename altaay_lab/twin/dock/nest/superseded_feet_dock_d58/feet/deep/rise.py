import json,numpy as np,mujoco as m, rest
D=np.radians
N=json.load(open('res_nest.json'))
r=N['model fric 0.068 damp 0.56']['r']
def tryseq(seq,label):
    md=rest.model('',0.068,0.56); dd=m.MjData(md); dd.qpos[:]=r['qpos']; m.mj_forward(md,dd)
    q=np.array([dd.qpos[md.jnt_qposadr[md.actuator_trnid[i,0]]] for i in range(md.nu)])
    tr=m.mj_name2id(md,1,'trunk_assembly'); cur=q.copy(); dd.ctrl[:]=q; taumax=np.zeros(md.nu); ups=[]
    for tg,T in seq:
        tgt=rest.targets(md,*tg); n=int(T/md.opt.timestep)
        for i in range(n):
            s=(i+1)/n; s=0.5-0.5*np.cos(np.pi*s); dd.ctrl[:]=cur*(1-s)+tgt*s; m.mj_step(md,dd); taumax=np.maximum(taumax,abs(dd.actuator_force))
        cur=tgt; ups.append(round(float(dd.xmat[tr][8]),2))
    for i in range(1500): m.mj_step(md,dd)
    names=[md.actuator(i).name for i in range(md.nu)]
    print(label,'ups',ups,'final up %.2f z %.0f'%(dd.xmat[tr][8],dd.xpos[tr][2]*1000),{names[i]:round(taumax[i],2) for i in np.argsort(-taumax)[:4]})
    return dict(ups=ups,final_up=float(dd.xmat[tr][8]),peak={names[i]:float(taumax[i]) for i in range(md.nu)},qpos=dd.qpos.tolist())
O={}
nest=(D(20),D(70),D(-75),0,0,0)
for neck in (0.0,D(40)):
  for hp in (30,40,50):
    seq=[(nest[:3]+(neck,0,0),1.0),((D(hp),D(90),D(-82.5),neck,0,0),2.5),((D(hp),D(90),D(-82.5),neck,0,0),1.0),((D(-15),D(5),0,0,0,0),3.0)]
    O[f'neck{int(np.degrees(neck))}_hp{hp}']=tryseq(seq,f'neck {np.degrees(neck):.0f} hip {hp}')
json.dump(O,open('res_rise.json','w'))

print('--- dynamic rock forward')
for T in (0.25,0.4,0.6):
  for ank in (-90,-75,-60):
    seq=[((D(30),D(90),D(ank),D(65),D(45),0),T),((D(30),D(90),D(ank),D(65),D(45),0),1.5),((D(30),D(90),D(-82.5),D(30),0,0),1.0),((D(-15),D(5),0,0,0,0),3.0)]
    O[f'rock_T{T}_a{ank}']=tryseq(seq,f'rock T {T} ankle {ank}')
json.dump(O,open('res_rise.json','w'))
