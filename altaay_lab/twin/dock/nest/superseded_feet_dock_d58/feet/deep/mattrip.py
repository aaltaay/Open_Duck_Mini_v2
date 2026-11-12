"""Item 8: does the bevelled mat trip the stock walk? straight walk at cmd 0.15 and 0.10 over the whole mat. sim pass only"""
import sys,json,numpy as np
from multiprocessing import Pool
from harness import *
FL={'hard':dict(floor_mu=1.0),'soft':dict(floor_mu=0.8,soft=True)}
def run(a):
    fl,h,bev,vx,seed=a
    d=scene(f'trip_{fl}_{int(h*1000)}_{int(bev*1000)}',mat_h=h,bevel=bev,**FL[fl])
    rng=np.random.default_rng(seed)
    s=Sim(d,seed,x0=-0.75+rng.uniform(-0.05,0.05),y0=rng.uniform(-0.03,0.03),yaw0=np.radians(rng.uniform(-3,3)))
    for k in range(int(16*50)):
        s.step((vx,0,0))
        if s.fallen: break
    x=s.trunk_pose()[0][0]
    return dict(fl=fl,h=h,bev=bev,vx=vx,seed=seed,fell=s.fallen,x=float(x),crossed=bool(x>0.25))
if __name__=='__main__':
    J=[(fl,h,b,vx,sd) for fl in FL for (h,b) in [(0,0.035),(0.007,0.035),(0.007,0.070),(0.007,0.100),(0.005,0.035),(0.003,0.035),(0.003,0.015),(0.002,0.020)] for vx in (0.15,0.10) for sd in range(6)]
    for fl in FL:
        for (h,b) in set((j[1],j[2]) for j in J): scene(f'trip_{fl}_{int(h*1000)}_{int(b*1000)}',mat_h=h,bevel=b,**FL[fl])
    with Pool(4) as p: R=p.map(run,J)
    json.dump(R,open('res_mattrip.json','w'))
    import itertools
    for k,g in itertools.groupby(R,key=lambda r:(r['fl'],r['h'],r['bev'],r['vx'])):
        g=list(g); print(k,'crossed',sum(r['crossed'] for r in g),'/',len(g),'falls',sum(r['fell'] for r in g),'x',[round(r['x'],2) for r in g])
