import trimesh, numpy as np
from shapely.geometry import Polygon
STEP=0.2
def rings3d(m, axis):
    lo,hi=m.bounds[0][axis],m.bounds[1][axis]
    hs=np.arange(lo+STEP/2,hi,STEP)
    normal=np.zeros(3); normal[axis]=1
    origin=m.bounds[0].copy()
    secs=m.section_multiplane(plane_origin=origin, plane_normal=normal, heights=hs-lo)
    out=[]
    for h,s in zip(hs,secs):
        if s is None: continue
        T=s.metadata.get('to_3D', np.eye(4))
        try: polys=s.polygons_full
        except Exception: continue
        for p in polys:
            for r in p.interiors:
                c=np.array(r.coords)[:-1]
                if len(c)<3: continue
                poly=Polygon(c); A=poly.area; P=poly.length
                circ=4*np.pi*A/P**2
                cen=np.array(poly.centroid.coords[0])
                nv=len(poly.simplify(0.05).exterior.coords)-1
                d=np.linalg.norm(c-cen,axis=1)
                kind='circle' if (circ>0.95 and nv>6) else ('hex' if nv==6 and circ>0.88 else None)
                if kind is None: continue
                c3=(T@np.r_[cen,0,1])[:3]
                out.append(dict(h=float(h),kind=kind,c=c3,d=float(2*d.mean()) if kind=='circle' else float(2*d.max())))
    return out
def cluster3d(rs,axis):
    groups=[]
    other=[i for i in range(3) if i!=axis]
    for r in sorted(rs,key=lambda r:r['h']):
        for g in groups:
            q=g[-1]
            if q['kind']==r['kind'] and np.abs(q['c'][other]-r['c'][other]).max()<0.4 and abs(q['d']-r['d'])<0.25 and r['h']-q['h']<STEP*1.6:
                g.append(r); break
        else: groups.append([r])
    out=[]
    for g in groups:
        if len(g)*STEP<0.5: continue
        c=np.mean([x['c'] for x in g],axis=0)
        p0=c.copy(); p0[axis]=g[0]['h']-STEP/2
        p1=c.copy(); p1[axis]=g[-1]['h']+STEP/2
        out.append(dict(kind=g[0]['kind'],d=round(float(np.median([x['d'] for x in g])),2),p0=p0,p1=p1))
    return out
def features(m):
    """returns features in m's original frame"""
    n=m.face_normals; a=m.area_faces
    R=np.eye(4)
    if a[np.abs(n).max(1)>0.999].sum()/a.sum()<=0.1:
        fa=m.facets_area; fn=m.facets_normal
        o=np.argsort(-fa); z=fn[o[0]]; x=None
        for i in o[1:]:
            if abs(np.dot(fn[i],z))<0.02: x=fn[i]-np.dot(fn[i],z)*z; break
        if x is None: x=np.cross(z,[1,0,0]) if abs(z[0])<0.9 else np.cross(z,[0,1,0])
        x/=np.linalg.norm(x); y=np.cross(z,x); R[:3,:3]=np.vstack([x,y,z])
    ma=m.copy(); ma.apply_transform(R); Ri=np.linalg.inv(R)
    out=[]
    for ax in range(3):
        for f in cluster3d(rings3d(ma,ax),ax):
            out.append(dict(kind=f['kind'],d=f['d'],p0=(Ri@np.r_[f['p0'],1])[:3].tolist(),p1=(Ri@np.r_[f['p1'],1])[:3].tolist()))
    return out
