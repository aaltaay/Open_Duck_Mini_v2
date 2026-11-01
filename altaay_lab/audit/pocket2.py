import trimesh,numpy as np,json,collections
A=json.load(open('assembly.json'))
R='/workspace/tmp_odm/Open_Duck_Mini/mini_bdx/robots/open_duck_mini_v2/'
cache={}
def load(n):
    if n not in cache:
        m=trimesh.load(R+n)
        if m.extents.max()<5: m.apply_scale(1000)
        cache[n]=m
    return cache[n].copy()
inst=[]
for k,i in enumerate(A['inst']):
    n=i['mesh'].split(':')[-1]; m=load(n); m.apply_transform(np.array(i['T'])); inst.append((k,n,m))
cases=[x for x in inst if x[1].startswith('wj-')]
printed=[x for x in inst if not x[1].startswith('wj-') and x[1] not in('drive_palonier.stl','passive_palonier.stl','roll_bearing.stl','cell.stl','board.stl','bms.stl','usb_c_charger.stl','power_switch.stl','bno055.stl','raspberrypizerow.stl','holder.stl','sg90.stl','antenna.stl')]
# servo CAD size: group cases by consecutive triplets sharing same T rotation
caseT=[np.array(A['inst'][k]['T']) for k,_,_ in cases]
# extents of combined case in its own frame
grp=collections.defaultdict(list)
for (k,n,m),T in zip(cases,caseT): grp[tuple(np.round(T[:3,3]/5).astype(int))].append((n,m,T))
print('servo groups',len(grp))
for key,g in list(grp.items())[:1]:
    T=g[0][2]; Ti=np.linalg.inv(T); u=trimesh.util.concatenate([x[1].copy().apply_transform(Ti) for x in g])
    print('CAD case extents (local)',u.extents.round(2),[x[0] for x in g])
worst=[]
rng=np.random.default_rng(0)
for k,n,m in cases:
    pts=m.sample(4000,seed=1) if 'seed' in trimesh.sample.sample_surface.__code__.co_varnames else m.sample(4000)
    for k2,n2,p in printed:
        lo,hi=p.bounds; b=np.all((pts>lo-1)&(pts<hi+1),axis=1)
        if not b.any(): continue
        sd=trimesh.proximity.signed_distance(p,pts[b])
        worst.append((round(float(sd.max()),2),k,n,n2))
worst.sort(reverse=True)
agg={}
for w,k,n,n2 in worst: agg.setdefault(n2,[]).append(w)
json.dump({a:[max(v),sum(1 for x in v if x>-0.3)] for a,v in agg.items()},open("pocket_agg.json","w"),indent=0)
print(open("pocket_agg.json").read())
