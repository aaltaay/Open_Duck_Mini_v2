"""Item 7: +7 g per foot (pads, rivets) on the stock walk. sim pass only. 10 seeds x (forward 0.15 for 16 s, turn 1.0 for 6 s, side 0.2 for 6 s)."""
import json,numpy as np
from harness import *
out={}
for dm in (0.0,0.007):
    d=scene(f'fm_{int(dm*1000)}',floor_mu=0.6,foot_dm=dm)
    R=[]
    for sd in range(10):
        s=Sim(d,sd); x0=s.trunk_pose()[0].copy()
        for i in range(100): s.step((0.15,0,0))
        p1=s.trunk_pose()[0].copy()
        for i in range(600): s.step((0.15,0,0))
        p2=s.trunk_pose()[0].copy(); y1=s.trunk_pose()[1]
        for i in range(300): s.step((0,0,1.0))
        y2=s.trunk_pose()[1]
        for i in range(300): s.step((0,0.2,0))
        R.append(dict(v=float(np.linalg.norm((p2-p1)[:2])/12),turn=float(np.unwrap([y1,y2])[1]-y1),fell=s.fallen))
    out[dm]=R
    print('dm',dm,'falls',sum(r['fell'] for r in R),'vx %.4f +- %.4f'%(np.mean([r['v'] for r in R]),np.std([r['v'] for r in R])))
m0=open(d+'/open_duck_mini_v2.xml').read().count('0.0956'); print('check mass edit', m0)
json.dump({str(k):v for k,v in out.items()},open('res_footmass.json','w'))
