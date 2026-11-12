"""Walk-on to stop on the feet mat, stock walk policy, 4 floors x 20 seeds x 3 stop strategies. sim pass only."""
import sys, json, numpy as np
from multiprocessing import Pool
from harness import *
D=np.radians
FLOORS={'hard':dict(floor_mu=1.0),'train':dict(floor_mu=0.6),'tile':dict(floor_mu=0.4),'soft':dict(floor_mu=0.8,soft=True)}
MATMU={'hard':'0.8','train':'0.8','tile':'0.5','soft':'0.8'}
POCKET_Y=0.0894   # half of the measured stance spacing 178.7 mm (sim)
def stance_targets(names):
    t=np.zeros(14)
    for side,sg in (('left',1),('right',-1)):
        t[names.index(f'{side}_hip_pitch')]=sg*D(-15); t[names.index(f'{side}_knee')]=D(5)
    return t
def go(s,c1,n):
    c0=s.data.ctrl.copy(); s.policy_on=False
    for i in range(n): a=(i+1)/n; a=0.5-0.5*np.cos(np.pi*a); s.data.ctrl[:]=c0*(1-a)+c1*a; s.step()
def resume(s):
    m=s.m; go(s,m.default_actuator.copy(),40)
    m.last_action[:]=0; m.last_last_action[:]=0; m.last_last_last_action[:]=0
    m.motor_targets=m.default_actuator.copy(); m.prev_motor_targets=m.default_actuator.copy(); s.policy_on=True
def est(s):
    """camera / tag estimate: truth + noise (4 mm, 1 deg)"""
    f=s.feet_pose(); mid=f[:,:2].mean(0); yaw=f[:,2].mean()
    return mid+s.rng.normal(0,0.004,2), yaw+s.rng.normal(0,D(1)), f
def approach(s,lead,vmax=0.15):
    for k in range(1500):
        if k%5==0: mid,yaw,_=est(s)
        dist=-mid[0]
        if dist<lead: return True
        if s.fallen: return False
        yd=np.arctan2(-mid[1],max(dist,0.25))*(dist>0.3)
        wz=np.clip(-1.5*(yaw-yd),-0.6,0.6)
        vy=np.clip(-1.2*mid[1],-0.1,0.1) if dist<0.45 else 0.0
        vx=vmax
        s.step((vx,vy,wz))
    return False
def settle(s,mode):
    if mode=='direct': n0,need=10,15
    else: n0,need=75,4         # march in place 1.5 s, then wait for feet together
    for i in range(n0): s.step((0,0,0))
    best=None
    for i in range(150):
        s.step((0,0,0)); F=s.foot_forces(); f=s.feet_pose()
        stg=abs(f[0,0]-f[1,0])*1000
        if min(F)>5 and stg<need: break
    go(s,stance_targets(s.m.actuator_names),50)
    for i in range(75): s.step()
def layouts():
    L={}
    pins_y=np.arange(-18,19,6)/1000
    L['L0_1row']=[0.0]
    L['L1_2rows_pm7']=[-0.007,0.007]
    L['L2_3rows_pm12']=[-0.012,0,0.012]
    return {k:(v,pins_y) for k,v in L.items()}
PAD=dict(cx=0.026,hx=0.022,hy=0.017,margin=0.001)
def score(f):
    """per layout: True if every pad sees >=2 own pins and no zone pin touches the other pad of that foot"""
    res={}
    for name,(rows,py) in layouts().items():
        ok=True
        for j,ysg in enumerate((1,-1)):
            fx,fy,fyaw=f[j]; c,sn=np.cos(fyaw),np.sin(fyaw)
            for zone_sgn in (1,-1):   # toe zone at +x, heel zone at -x
                P=np.array([(zone_sgn*PAD['cx']+r, ysg*POCKET_Y+p) for r in rows for p in py])
                lx=(P[:,0]-fx)*c+(P[:,1]-fy)*sn; ly=-(P[:,0]-fx)*sn+(P[:,1]-fy)*c
                def on(sg): return (abs(lx-sg*PAD['cx'])<PAD['hx']-PAD['margin'])&(abs(ly)<PAD['hy']-PAD['margin'])
                if on(zone_sgn).sum()<2 or on(-zone_sgn).sum()>0: ok=False
        res[name]=ok
    return res
def run(args):
    floor,seed,mode,mat_h=args
    d=scene(f'{floor}_m{int(mat_h*1000)}_b{int(BEV*1000)}',mat_h=mat_h,bevel=BEV,**FLOORS[floor])
    import harness; 
    rng=np.random.default_rng(1000+seed)
    s=Sim(d,seed,x0=-1.05+rng.uniform(-0.03,0.03),y0=rng.uniform(-0.04,0.04),yaw0=D(rng.uniform(-6,6)))
    out=dict(floor=floor,seed=seed,mode=mode,mat_h=mat_h)
    ok=approach(s,LEAD)
    if not ok: out.update(fell=bool(s.fallen),stage='approach_fail'); return out
    tries=0; hist=[]; ncorr=0
    def correct():
        nonlocal ncorr
        for it in range(4):
            for i in range(40): s.step((0,0,0))
            mid,yaw,_=est(s); ex=-mid[0]-BIAS_X; ey=-mid[1]
            moved=False
            if abs(yaw)>D(2.5):
                n=int(np.clip(abs(yaw)/0.45*50,6,40))
                for i in range(n): s.step((0,0,-0.6*np.sign(yaw)))
                moved=True; continue
            if abs(ey)>0.008:
                n=int(np.clip(abs(ey)/0.05*50,6,30))
                for i in range(n): s.step((0,0.1*np.sign(ey),0))
                moved=True
            if abs(ex)>0.006:
                n=int(np.clip(abs(ex)/0.07*50,5,40)) if ex>0 else int(np.clip(abs(ex)/0.05*50,5,40))
                for i in range(n): s.step((0.15*np.sign(ex) if ex>0 else -0.1,0,0))
                moved=True
            ncorr+=moved
            if not moved: break
    while True:
        if mode!='direct': correct()
        if s.fallen: break
        pre=s.feet_pose().round(4).tolist()
        settle(s,'direct' if mode=='direct' else 'march'); tries+=1
        f=s.feet_pose(); sc=score(f)
        hist.append(dict(pre=pre,feet=f.round(4).tolist(),score=sc,fell=s.fallen))
        if s.fallen: break
        if mode!='adjust' or sc['L0_1row'] or tries>=3: break
        resume(s)
    out.update(fell=s.fallen,stage='dock',tries=tries,hist=hist,ncorr=ncorr,t_dock=s.t)
    # walk off forward 1 m
    if not s.fallen:
        resume(s)
        for i in range(450): s.step((0.15,0,0))
        out['walkoff_fell']=s.fallen; out['walkoff_x']=float(s.trunk_pose()[0][0])
    return out
import os
LEAD=float(os.environ.get("LEAD","0")); BEV=float(os.environ.get("BEV","0.02")); BIAS_X=float(os.environ.get("BIAS_X","0"))
if __name__=='__main__':
    tag=sys.argv[1]; modes=sys.argv[3].split(','); floors=sys.argv[4].split(','); mat=float(sys.argv[5]); N=int(sys.argv[6])
    jobs=[(f,s,mo,mat) for f in floors for mo in modes for s in range(N)]
    for f in floors: scene(f'{f}_m{int(mat*1000)}_b{int(BEV*1000)}',mat_h=mat,bevel=BEV,**FLOORS[f])
    with Pool(4) as p: R=p.map(run,jobs)
    json.dump(R,open(f'res_{tag}.json','w'))
    for f in floors:
        for mo in modes:
            rr=[r for r in R if r['floor']==f and r['mode']==mo]
            fe=[np.array(r['hist'][-1]['feet']) for r in rr if r.get('hist')]
            if fe:
                fe=np.array(fe); ex=fe[:,:,0]*1000; ey=(np.abs(fe[:,:,1])-POCKET_Y)*1000*np.array([1,1]); yw=np.degrees(fe[:,:,2])
                h=fe[:,:,2].mean(1); stg=((fe[:,0,0]-fe[:,1,0])*np.cos(h)+(fe[:,0,1]-fe[:,1,1])*np.sin(h))*1000
            print(f,mo,'n',len(rr),'falls',sum(r['fell'] for r in rr),'walkoff falls',sum(r.get('walkoff_fell',0) for r in rr),
                  {k:sum(r['hist'][-1]['score'][k] for r in rr if r.get('hist') and not r['fell']) for k in layouts()},
                  'x mean %.1f sd %.1f |max| %.1f'%(ex.mean(),ex.std(),abs(ex).max()),'y(out+) mean %.1f |max| %.1f'%(ey.mean(),abs(ey).max()),
                  'yaw |max| %.1f'%abs(yw).max(),'stagger mean|.| %.1f max %.1f'%(abs(stg).mean(),abs(stg).max()),
                  'tries',[r.get('tries') for r in rr])
