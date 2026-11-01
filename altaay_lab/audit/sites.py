import sys
import json, numpy as np, trimesh
A=json.load(open(sys.argv[1]))
R='/workspace/tmp_odm/Open_Duck_Mini/mini_bdx/robots/open_duck_mini_v2/'
W=[]
for k,i in enumerate(A['inst']):
    T=np.array(i['T'])
    for f in A['feats'][i['mesh']]:
        p0=(T@np.r_[f['p0'],1])[:3]; p1=(T@np.r_[f['p1'],1])[:3]
        a=p1-p0; L=np.linalg.norm(a)
        if L<1e-6: continue
        W.append(dict(i=k,mesh=i['mesh'].split(':')[-1].replace('.stl',''),kind=f['kind'],d=f['d'],p0=p0,p1=p1,ax=a/L,L=L))
print('world feats',len(W))
# coaxial clustering
def linedist(p,o,a): v=p-o; return np.linalg.norm(v-np.dot(v,a)*a)
sites=[]
for w in sorted(W,key=lambda w:-w['L']):
    for s in sites:
        if abs(abs(np.dot(s['ax'],w['ax']))-1)<1e-3 and linedist(w['p0'],s['o'],s['ax'])<0.35 and linedist(w['p1'],s['o'],s['ax'])<0.35:
            # also require overlap/adjacency along axis within 40mm
            t=[np.dot(w['p0']-s['o'],s['ax']),np.dot(w['p1']-s['o'],s['ax'])]
            if min(t)<s['tmax']+40 and max(t)>s['tmin']-40:
                s['m'].append(w); s['tmin']=min(s['tmin'],*t); s['tmax']=max(s['tmax'],*t); break
    else:
        t=[0,w['L']]
        sites.append(dict(o=w['p0'],ax=w['ax'],m=[w],tmin=0,tmax=w['L']))
out=[]
for s in sites:
    segs=[]
    for w in s['m']:
        t=sorted([np.dot(w['p0']-s['o'],s['ax']),np.dot(w['p1']-s['o'],s['ax'])])
        segs.append((round(t[0],1),round(t[1],1),w['mesh'],w['kind'],w['d'],w['i']))
    segs.sort()
    out.append(dict(o=s['o'].round(1).tolist(),ax=s['ax'].round(3).tolist(),segs=segs))
json.dump(out,open(sys.argv[2],'w'),default=str)
print('sites',len(out))
