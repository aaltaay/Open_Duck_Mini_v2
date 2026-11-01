import yourdfpy, trimesh, numpy as np, json
from feat3d import features
R='/workspace/tmp_odm/Open_Duck_Mini/mini_bdx/robots/open_duck_mini_v2/'
u=yourdfpy.URDF.load(R+'robot.urdf', load_meshes=False, build_scene_graph=True)
inst=[]
for ln,link in u.link_map.items():
    Tl=u.get_transform(ln)
    for v in link.visuals:
        fn=v.geometry.mesh.filename.replace('package:///','').replace('package://','')
        T=Tl@(v.origin if v.origin is not None else np.eye(4)); T=T.copy(); T[:3,3]*=1000
        inst.append(dict(link=ln,mesh=fn,T=T.tolist()))
feats={}
for fn in sorted(set(i['mesh'] for i in inst)):
    m=trimesh.load(R+fn); m.apply_scale(1000)
    feats[fn]=features(m)
json.dump(dict(inst=inst,feats=feats),open('assembly.json','w'))
print(len(inst),sum(len(v) for v in feats.values()))
