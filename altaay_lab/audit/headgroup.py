import json, numpy as np, trimesh
from feat3d import features
A=json.load(open('assembly.json'))
R='/workspace/tmp_odm/Open_Duck_Mini/mini_bdx/robots/open_duck_mini_v2/'
P='/workspace/tmp_odm/Open_Duck_Mini/print/'
Th=np.linalg.inv(np.array([i for i in A['inst'] if i['mesh']=='head.stl'][0]['T']))
inst=[]; feats={}
# URDF instances near head (in head frame) that are not printed parts in print/
for i in A['inst']:
    T=Th@np.array(i['T'])
    mm=trimesh.load(R+i['mesh']); mm.apply_scale(1000); mm.apply_transform(T); c=mm.bounds.mean(0)
    if i['mesh'] in ('sg90.stl','antenna.stl','board.stl','raspberrypizerow.stl','wj-wk00-0122topcabinetcase_95.stl','wj-wk00-0124bottomcase_45.stl','drive_palonier.stl','passive_palonier.stl','roll_bearing.stl','zz'):
        if -100<c[0]<130 and abs(c[1])<110 and 90<c[2]<200:
            inst.append(dict(mesh='U:'+i['mesh'],T=T.tolist()))
for f in ['head','left_eye','right_eye','bulb','flash_light_module','flash_reflector_interface','speaker_stand','speaker_interface','head_bot_sheet','head_roll_mount','left_antenna_holder','right_antenna_holder']:
    inst.append(dict(mesh='P:'+f+'.stl',T=np.eye(4).tolist()))
M=np.diag([1,-1,1,1.]); inst.append(dict(mesh='P:bulb.stl',T=M.tolist(),mirror=True))
for i in inst:
    fn=i['mesh']
    if fn in feats: continue
    m=trimesh.load((R if fn[0]=='U' else P)+fn[2:]); m.apply_scale(1000) if m.extents.max()<5 else None
    feats[fn]=features(m)
json.dump(dict(inst=inst,feats=feats),open('assembly_head.json','w'))
from collections import Counter; print(Counter(i['mesh'] for i in inst))
