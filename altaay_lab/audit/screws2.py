import sys
import json, collections, numpy as np, trimesh
S=json.load(open(sys.argv[2])); A=json.load(open(sys.argv[1]))
R='/workspace/tmp_odm/Open_Duck_Mini/mini_bdx/robots/open_duck_mini_v2/'
cache={}; parts=[]
for i in A['inst']:
    if i['mesh'] not in cache:
        fn=i['mesh']; base=('/workspace/tmp_odm/Open_Duck_Mini/print/' if fn.startswith('P:') else R)+fn.split(':')[-1]
        m=trimesh.load(base); m.apply_scale(1000) if m.extents.max()<5 else None; cache[i['mesh']]=m
    m=cache[i['mesh']].copy(); m.apply_transform(np.array(i['T'])); parts.append(m)
W=trimesh.util.concatenate(parts)
from trimesh.ray.ray_triangle import RayMeshIntersector
RI=RayMeshIntersector(W)
def anchor_type(m,d,L):
    if m=='drive_palonier' and abs(d-2.5)<0.2: return 'horn(drive)'
    if m=='passive_palonier' and abs(d-2.5)<0.2: return 'horn(passive)'
    if abs(d-4.0)<0.15 and L>=5.0: return 'M3 insert'
    if m.startswith('wj-') and d<2.1: return 'servo pilot'
    if abs(d-2.0)<0.1 and L>=4.5 and not m.startswith('wj-'): return 'plastic pilot 2.0'
    return None
rows=[]
for s in S:
    o=np.array(s['o']); ax=np.array(s['ax'])
    segs=[dict(t0=a,t1=b,m=m,k=k,d=d,i=i) for a,b,m,k,d,i in s['segs']]
    for sg in segs:
        m=sg['m']
        if m.startswith('wj-') or 'palonier' in m: continue
        if not (2.4<=sg['d']<=3.7): continue
        if anchor_type(m,sg['d'],sg['t1']-sg['t0']): continue
        heads=[h for h in segs if h['i']==sg['i'] and 3.9<=h['d']<=7.1 and (abs(h['t1']-sg['t0'])<0.45 or abs(h['t0']-sg['t1'])<0.45) and not (abs(h['d']-4.0)<0.15 and h['t1']-h['t0']>=5.0)]
        if heads:
            h=heads[0]; direction=1 if abs(h['t1']-sg['t0'])<0.45 else -1
            hf=h['t1'] if direction==1 else h['t0']; seat=f"recess d{h['d']}"
        else:
            # flat-face head: head sits at the outer end of the clearance hole; choose side facing away from an anchor
            seat='flat face'
            hf=None
            for direction,face in ((1,sg['t0']),(-1,sg['t1'])):
                c=[x for x in segs if x['i']!=sg['i'] and anchor_type(x['m'],x['d'],x['t1']-x['t0']) and (x['t0']-face)*direction>0]
                if c: hf=face; break
            if hf is None: continue
        cand=[x for x in segs if x['i']!=sg['i'] and anchor_type(x['m'],x['d'],x['t1']-x['t0']) and max((x['t0']-hf)*direction,(x['t1']-hf)*direction)>0.3]
        if not cand:
            rows.append(dict(part=m,clr=sg['d'],seat=seat,anchor='NONE',into=None,near=None,far=None,free=None)); continue
        cand.sort(key=lambda x:min((x['t0']-hf)*direction,(x['t1']-hf)*direction)); a=cand[0]
        near=min((a['t0']-hf)*direction,(a['t1']-hf)*direction); far=max((a['t0']-hf)*direction,(a['t1']-hf)*direction)
        org=o+ax*hf; d=ax*direction
        # first hit along axis (start a hair inside)
        locs,_,_=RI.intersects_location([org+d*0.05],[d],multiple_hits=True)
        dist=sorted(np.dot(l-org,d) for l in locs) if len(locs) else []
        free=next((x for x in dist if x>0.1),None)
        rows.append(dict(part=m,clr=round(sg['d'],1),seat=seat,anchor=anchor_type(a['m'],a['d'],a['t1']-a['t0']),into=a['m'],near=round(near,1),far=round(far,1),free=None if free is None else round(free,1)))
json.dump(rows,open(sys.argv[3],'w'))
c=collections.Counter((r['anchor'],r['part'],r['into'],r['clr'],r['seat'],r['near'],r['far'],r['free']) for r in rows)
for k,v in sorted(c.items(),key=lambda kv:[str(x) for x in kv[0]]): print(v,k)
print(len(rows))
