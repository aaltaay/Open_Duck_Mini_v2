import json,sys,numpy as np,trimesh
A=json.load(open(sys.argv[1])); S=json.load(open(sys.argv[2])); targets=sys.argv[3].split(',')
R='/workspace/tmp_odm/Open_Duck_Mini/mini_bdx/robots/open_duck_mini_v2/'; P='/workspace/tmp_odm/Open_Duck_Mini/print/'
parts=[];names=[]
for i in A['inst']:
    fn=i['mesh']; base=(P if fn.startswith('P:') else R)+fn.split(':')[-1]
    m=trimesh.load(base); m.apply_scale(1000) if m.extents.max()<5 else None
    m.apply_transform(np.array(i['T'])); parts.append(m); names.append(fn.split(':')[-1])
for s in S:
    segs=s['segs']
    if not any(x[2] in targets for x in segs): continue
    o=np.array(s['o']); ax=np.array(s['ax'])
    desc=' | '.join(f"{m}:{d}x{t1-t0:.1f}@{t0:.1f}" for t0,t1,m,k,d,i in segs)
    out=[]
    for sgn in (1,-1):
        hits=[]
        for n,m in zip(names,parts):
            loc,_,_=m.ray.intersects_location([o-ax*sgn*200],[ax*sgn],multiple_hits=True) if False else m.ray.intersects_location([o],[ax*sgn],multiple_hits=True)
            for l in loc: hits.append((round(float(np.dot(l-o,ax*sgn)),1),n))
        hits.sort(); out.append(hits[:6])
    print(desc); print('   +dir:',out[0]); print('   -dir:',out[1])
