import os; os.environ.setdefault('MUJOCO_GL','egl')
import json,sys,numpy as np,mujoco as m, rest
from PIL import Image
def shot(qpos,fn,az=90,el=-10,dist=0.75,extra='',title=None):
    md=rest.model(extra,0.068,0.56); md.vis.global_.offwidth=800; md.vis.global_.offheight=600
    for g in range(md.ngeom):
        if md.geom_group[g]==3: md.geom_rgba[g]=[0.2,0.4,0.9,1]
    dd=m.MjData(md); dd.qpos[:]=qpos; m.mj_forward(md,dd)
    r=m.Renderer(md,600,800); cam=m.MjvCamera(); cam.lookat[:]=dd.xpos[m.mj_name2id(md,1,'trunk_assembly')]*[1,1,0.6]+[0,0,0.06]
    cam.azimuth=az; cam.elevation=el; cam.distance=dist
    opt=m.MjvOption(); opt.geomgroup[:]=[1,1,1,1,0,0]
    r.update_scene(dd,cam,opt); img=r.render(); Image.fromarray(img).save(fn); return fn
if __name__=='__main__':
    R=json.load(open(sys.argv[1]))
    for k,v in R.items():
        for az in (90,0): shot(v['qpos'],os.path.join(os.environ.get("FEET_SCRATCH") or os.path.join(__import__("tempfile").gettempdir(), "feet_scratch"),'feet_deep',f'{k}_{az}.png'),az=az)
