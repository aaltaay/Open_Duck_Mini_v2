import trimesh, numpy as np, json, sys, glob, os
from collections import defaultdict
STEP=0.2
def align(m):
    n=m.face_normals; a=m.area_faces
    if a[np.abs(n).max(1)>0.999].sum()/a.sum()>0.1: return m, False
    # align largest facet normal to z, next orthogonal largest to x
    fa=m.facets_area; fn=m.facets_normal
    o=np.argsort(-fa); z=fn[o[0]]
    x=None
    for i in o[1:]:
        if abs(np.dot(fn[i],z))<0.02: x=fn[i]-np.dot(fn[i],z)*z; break
    if x is None: x=np.cross(z,[1,0,0]) if abs(z[0])<0.9 else np.cross(z,[0,1,0])
    x/=np.linalg.norm(x); y=np.cross(z,x)
    R=np.eye(4); R[:3,:3]=np.vstack([x,y,z])
    m=m.copy(); m.apply_transform(R); return m, True
def rings(m, axis):
    lo,hi=m.bounds[0][axis],m.bounds[1][axis]
    hs=np.arange(lo+STEP/2,hi,STEP)
    normal=np.zeros(3); normal[axis]=1
    origin=m.bounds[0].copy()
    secs=m.section_multiplane(plane_origin=origin, plane_normal=normal, heights=hs-lo)
    out=[]
    for h,s in zip(hs,secs):
        if s is None: continue
        try: polys=s.polygons_full
        except Exception: continue
        for p in polys:
            for r in p.interiors:
                c=np.array(r.coords)[:-1]
                if len(c)<3: continue
                poly=__import__('shapely.geometry',fromlist=['Polygon']).Polygon(c)
                A=poly.area; P=poly.length
                circ=4*np.pi*A/P**2
                cen=np.array(poly.centroid.coords[0])
                d=np.linalg.norm(c-cen,axis=1)
                # simplify vertices count
                simp=poly.simplify(0.05)
                nv=len(simp.exterior.coords)-1
                rr=poly.minimum_rotated_rectangle
                xs,ys=rr.exterior.coords.xy
                e=sorted([np.hypot(xs[1]-xs[0],ys[1]-ys[0]),np.hypot(xs[2]-xs[1],ys[2]-ys[1])])
                kind='circle' if (circ>0.95 and nv>6) else ('hex' if nv==6 and circ>0.88 else 'other')
                out.append(dict(h=float(h),kind=kind,cx=float(cen[0]),cy=float(cen[1]),
                    d=float(2*d.mean()) if kind=='circle' else float(2*d.max()),
                    flats=float(e[0]),w=float(e[0]),l=float(e[1]),area=float(A)))
    return out
def cluster(rs):
    # group by kind, center (0.4mm), size (0.15mm); then contiguous h runs
    groups=[]
    for r in sorted(rs,key=lambda r:r['h']):
        placed=False
        for g in groups:
            q=g[-1]
            if q['kind']==r['kind'] and abs(q['cx']-r['cx'])<0.4 and abs(q['cy']-r['cy'])<0.4 and abs(q['d']-r['d'])<0.25 and abs(q['w']-r['w'])<0.4 and r['h']-q['h']<STEP*1.6:
                g.append(r); placed=True; break
        if not placed: groups.append([r])
    feats=[]
    for g in groups:
        feats.append(dict(kind=g[0]['kind'],cx=round(np.mean([x['cx'] for x in g]),2),cy=round(np.mean([x['cy'] for x in g]),2),
            d=round(float(np.median([x['d'] for x in g])),2),w=round(float(np.median([x['w'] for x in g])),2),l=round(float(np.median([x['l'] for x in g])),2),
            z0=round(g[0]['h']-STEP/2,2),z1=round(g[-1]['h']+STEP/2,2),depth=round(len(g)*STEP,2)))
    return feats
def wall(m,n=4000):
    pts,fi=trimesh.sample.sample_surface(m,n,seed=1)
    nrm=m.face_normals[fi]
    org=pts-nrm*1e-3
    loc,ri,ti=m.ray.intersects_location(org,-nrm,multiple_hits=False)
    th=np.full(n,np.nan); th[ri]=np.linalg.norm(loc-org[ri],axis=1)
    th=th[~np.isnan(th)]
    return float(np.min(th)),float(np.percentile(th,1)),float(np.percentile(th,5)),float(np.median(th))
def orient(m):
    res=[]
    for ax in range(3):
        for sgn in (1,-1):
            up=np.zeros(3); up[ax]=sgn  # this axis points up
            nz=m.face_normals@up
            zc=m.triangles_center@up
            zmin=(m.vertices@up).min()
            bed=(np.abs(zc-zmin)<0.05)&(nz<-0.999)
            over=(nz<-np.cos(np.radians(45)))&~bed
            other=[i for i in range(3) if i!=ax]
            res.append(dict(up=('+' if sgn>0 else '-')+'xyz'[ax],bed_area=float(m.area_faces[bed].sum()),overhang_area=float(m.area_faces[over].sum()),
                footprint=[round(float(m.extents[other[0]]),1),round(float(m.extents[other[1]]),1)],height=round(float(m.extents[ax]),1)))
    return res
if __name__=='__main__':
    out={}
    for f in sys.argv[1:]:
        m0=trimesh.load(f)
        if m0.extents.max()<1: m0.apply_scale(1000)
        m,rot=align(m0)
        rec=dict(file=os.path.basename(f),rotated_to_align=rot,extents=[round(float(x),2) for x in m.extents],volume_cm3=round(m.volume/1000,2),area_cm2=round(m.area/100,1),watertight=bool(m.is_watertight),
                 bounds=[[round(float(v),2) for v in b] for b in m.bounds])
        rec['features']={}
        for ax in range(3):
            rec['features']['xyz'[ax]]=cluster(rings(m,ax))
        rec['wall_min_p1_p5_med']=wall(m)
        rec['orient']=orient(m)
        out[rec['file']]=rec
        print(rec['file'],flush=True)
    json.dump(out,open(sys.argv[0].replace('measure.py','meas_%s.json'%os.environ.get('TAG','print')),'w'),indent=1)
