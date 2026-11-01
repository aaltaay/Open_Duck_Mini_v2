import yourdfpy,numpy as np,json,collections,trimesh
U='/workspace/tmp_odm/Open_Duck_Mini/mini_bdx/robots/open_duck_mini_v2/robot.urdf'
r=yourdfpy.URDF.load(U,load_meshes=False)
A=json.load(open('assembly.json'))
J={}
for j in r.robot.joints:
    if j.type=='revolute':
        T=r.get_transform(j.child); ax=T[:3,:3]@np.array(j.axis)
        J[j.name]=dict(p=T[:3,3]*1000,ax=ax,parent=j.parent,child=j.child,rng=j.limit.upper-j.limit.lower)
# link parent map
par={j.child:(j.parent,j.name) for j in r.robot.joints}
def chain(l):
    out=[]
    while l in par: out.append(l); l=par[l][0]
    return out+[l]
# servos: top case instances, horn point local (-25.5,*,0) ; use middle case center
serv=[]
for i in A['inst']:
    if i['mesh'].endswith('topcabinetcase_95.stl'):
        T=np.array(i['T']); horn=(T@[-25.5,5.0,0,1])[:3]; ctr=(T@[-13,-10,0,1])[:3]; far=(T@[9.6,-10,0,1])[:3]
        jn=min(J,key=lambda k:np.linalg.norm(J[k]['p']-horn) if 'antenna' not in k else 1e9)
        serv.append(dict(link=i['link'],joint=jn,dist=float(np.linalg.norm(J[jn]['p']-horn)),ctr=ctr,far=far))
for s in serv: print('servo on',s['link'],'drives',s['joint'],'horn-to-joint %.1f'%s['dist'])
def inst_ctr(mesh,link=None):
    R='/workspace/tmp_odm/Open_Duck_Mini/mini_bdx/robots/open_duck_mini_v2/'
    for i in A['inst']:
        if i['mesh'].endswith(mesh) and (link is None or i['link']==link):
            m=trimesh.load(R+mesh); m.apply_scale(1000) if m.extents.max()<5 else None
            m.apply_transform(np.array(i['T'])); return m.bounds.mean(0),i['link']
S={s['joint']:s for s in serv}
ids={'left_hip_yaw':20,'left_hip_roll':21,'left_hip_pitch':22,'left_knee':23,'left_ankle':24,'right_hip_yaw':10,'right_hip_roll':11,'right_hip_pitch':12,'right_knee':13,'right_ankle':14,'neck_pitch':30,'head_pitch':31,'head_yaw':32,'head_roll':33}
def node(name):
    if name in S: return S[name]['ctr'],S[name]['link']
    return inst_ctr(*name)
def route(a,b):
    pa,la=node(a); pb,lb=node(b)
    ca,cb=chain(la),chain(lb); common=next(l for l in ca if l in cb)
    js=[par[l][1] for l in ca[:ca.index(common)]]+[par[l][1] for l in reversed(cb[:cb.index(common)])]
    pts=[pa]+[J[j]['p'] for j in js]+[pb]
    L=sum(np.linalg.norm(np.subtract(pts[k+1],pts[k])) for k in range(len(pts)-1))
    return L,float(np.linalg.norm(pb-pa)),js
pairs=[('ADP',('board.stl','trunk_assembly'),'left_hip_yaw'),('',  'left_hip_yaw','left_hip_roll'),('','left_hip_roll','left_hip_pitch'),('','left_hip_pitch','left_knee'),('','left_knee','left_ankle'),
('ADP',('board.stl','trunk_assembly'),'right_hip_yaw'),('','right_hip_yaw','right_hip_roll'),('','right_hip_roll','right_hip_pitch'),('','right_hip_pitch','right_knee'),('','right_knee','right_ankle'),
('ADP',('board.stl','trunk_assembly'),'neck_pitch'),('','neck_pitch','head_pitch'),('','head_pitch','head_yaw'),('','head_yaw','head_roll'),
('PI',('raspberrypizerow.stl',None),('board.stl','trunk_assembly')),('PI',('raspberrypizerow.stl',None),('bno055.stl',None)),('PI',('raspberrypizerow.stl',None),('foot_bottom_pla.stl','foot_assembly')),('PI',('raspberrypizerow.stl',None),('foot_bottom_pla.stl','foot_assembly_2')),
('PI',('raspberrypizerow.stl',None),('sg90.stl',None)),('PI',('raspberrypizerow.stl',None),('usb_c_charger.stl',None)),('PI',('raspberrypizerow.stl',None),('power_switch.stl',None)),('PI',('raspberrypizerow.stl',None),('bms.stl',None)),
('BMS',('bms.stl',None),('holder.stl',None)),('BMS',('bms.stl',None),('usb_c_charger.stl',None)),('BMS',('bms.stl',None),('power_switch.stl',None)),('SW',('power_switch.stl',None),('board.stl','trunk_assembly'))]
out=[]
for tag,a,b in pairs:
    L,d,js=route(a,b)
    slack={j:round(float(J[j]['rng']),2) for j in js}
    print(f"{str(a):45s} -> {str(b):45s} polyline {L:6.1f} straight {d:6.1f} joints {slack}")
    out.append(dict(a=str(a),b=str(b),poly=round(L,1),straight=round(d,1),joints=slack))
json.dump(out,open('cables.json','w'),indent=1)
