import json,numpy as np,mujoco as m, rest
D=np.radians
R={}
for nm,p in [('sit_a',(D(30),D(90),D(-82.5),0,0,0)),('sit_b',(D(15),D(45),D(-60),0,0,0)),('sit_c',(D(30),D(60),D(-60),0,0,0)),('sit_d',(D(20),D(70),D(-75),0,0,0))]:
    r=rest.run((nm,p,{}))
    md=rest.model('',0.068,0.56); dd=m.MjData(md); dd.qpos[:]=r['qpos']; m.mj_forward(md,dd)
    pts={}
    for i in range(dd.ncon):
        c=dd.contact[i]; f=np.zeros(6); m.mj_contactForce(md,dd,i,f)
        b=md.body(md.geom_bodyid[c.geom1 if md.geom_bodyid[c.geom1]!=0 else c.geom2]).name
        if b in('world','floor'): b=md.body(md.geom_bodyid[c.geom2]).name
        pts.setdefault(b,[]).append((c.pos[:2].round(4).tolist(),round(f[0],2)))
    print(nm,'up %.2f'%r['final_up'],'vz %.2f'%r['off_vz_peak'],'trunk z %.0f'%r['trunk_z_mm'],'pads',r['pads_final'],'entry pads',r['pads_entry'],'entry up %.2f'%r['entry_up'],'tau entry max %.2f'%r['tau_entry_max'])
    for b,v in pts.items():
        P=np.array([x[0] for x in v]); F=np.array([x[1] for x in v]); print('   ',b,'N %.1f'%F.sum(),'x %.0f..%.0f y %.0f..%.0f mm'%(P[:,0].min()*1e3,P[:,0].max()*1e3,P[:,1].min()*1e3,P[:,1].max()*1e3))
    R[nm]=r
json.dump(R,open('res_sitgeo.json','w'))
