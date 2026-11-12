import os; os.environ.setdefault('MUJOCO_GL','egl')
import json,numpy as np,rest,render,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
D=np.radians; S=os.path.join(os.environ.get("FEET_SCRATCH") or os.path.join(__import__("tempfile").gettempdir(), "feet_scratch"),'feet_deep','')
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'')
st=rest.run(('st',(D(-15),D(5),0,0,0,0),{'no_off':True}))
nestin=rest.run(('n',(D(20),D(70),D(-75),0,0,0),{'no_off':True}))
N=json.load(open('res_nest.json')); nest=N['model fric 0.068 damp 0.56']['r']
RB=json.load(open('res_rollback.json'))['2.0']
frames=[(st['qpos'],'1 stand on the pads\n(torque on, 0.9 A)'),(nestin['qpos'],'2 fold to the nest\n(torque on, max 0.39 Nm)'),(nest['qpos'],'3 torque off: settles\n(peak 0.003 m/s, holds 3 N pushes)'),(RB['qpos'],'4 wake: roll to the back\n(0.4 m/s), then back get-up')]
ims=[]
for q,t in frames:
    fn=render.shot(q,S+'seq.png',az=120,el=-12,dist=0.95); im=Image.open(fn).resize((400,300)); ims.append((im,t))
W=Image.new('RGB',(1600,380),'white'); d=ImageDraw.Draw(W)
try: f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
except: f=None
for i,(im,t) in enumerate(ims):
    W.paste(im,(i*400,0)); d.multiline_text((i*400+10,305),t,fill='black',font=f)
W.save(OUT+'D3_safe_off_sequence.png')
# views of the nest
a=Image.open(render.shot(nest['qpos'],S+'n1.png',az=90,el=-5,dist=0.7)).resize((400,300)); b=Image.open(render.shot(nest['qpos'],S+'n2.png',az=160,el=-20,dist=0.7)).resize((400,300))
W=Image.new('RGB',(800,340),'white'); W.paste(a,(0,0)); W.paste(b,(400,0)); d=ImageDraw.Draw(W)
d.multiline_text((10,303),'Nest rest pose, torque off (sim pass only):\nrests on the tail, both knees, both heel edges and the back of the head; no sole pad is made.',fill='black',font=f); W.save(OUT+'D2_nest_rest_pose.png')
# walk-on error scatter
R=json.load(open('res_main.json')); fig,ax=plt.subplots(1,3,figsize=(13,4.3),sharey=True)
for k,mo in enumerate(['direct','shuffle','adjust']):
    for fl,c in (('hard','#1b6ca8'),('train','#d1495b'),('tile','#2e933c')):
        rr=[r for r in R if r['floor']==fl and r['mode']==mo and r.get('hist')]
        F=np.array([r['hist'][-1]['feet'] for r in rr])
        ax[k].scatter(F[:,:,0].ravel()*1000,(np.abs(F[:,:,1])-0.0894).ravel()*1000,s=14,c=c,label=fl,alpha=.8)
    ax[k].add_patch(plt.Rectangle((-20,-27),40,54,fill=False,ec='k',lw=1.5)); ax[k].add_patch(plt.Rectangle((-35,-40),70,80,fill=False,ec='gray',ls='--'))
    ax[k].set_title(f'{mo}: success (current window) '+', '.join(f"{fl} {sum(r['hist'][-1]['score']['L0_1row'] for r in R if r['floor']==fl and r['mode']==mo and r.get('hist'))}/20" for fl in ('hard','train','tile')),fontsize=9)
    ax[k].set_xlabel('foot fore-aft error mm (+ = too far)'); ax[k].grid(alpha=.3)
ax[0].set_ylabel('foot lateral error mm (+ = outward)'); ax[0].legend(fontsize=8)
fig.suptitle('Walk-on stop error per foot, 2 mm mat, stock walk, 20 seeds per floor (sim pass only). Solid box: current pad window +/-20 x +/-27 mm. Dashed: +/-35 x +/-40 mm needed for 95 %',fontsize=9)
fig.tight_layout(); fig.savefig(OUT+'D1_walkon_error.png',dpi=110)
# mat trip
T=json.load(open('res_mattrip.json'))
import itertools
fig,ax=plt.subplots(figsize=(9,3.8)); labs=[];vals=[]
for (fl,h,b),g in itertools.groupby([r for r in T if r['vx']==0.15],key=lambda r:(r['fl'],r['h'],r['bev'])):
    g=list(g); labs.append(f"{fl}\n{h*1000:.0f} mm/{b*1000:.0f}"); vals.append((sum(r['crossed'] for r in g),sum(r['fell'] for r in g)))
x=np.arange(len(labs)); ax.bar(x-.2,[v[0] for v in vals],.4,label='crossed (of 6)',color='#2e933c'); ax.bar(x+.2,[v[1] for v in vals],.4,label='fell (of 6)',color='#d1495b')
ax.set_xticks(x); ax.set_xticklabels(labs,fontsize=7); ax.legend(); ax.set_title('Mat walk-over, stock walk at 0.15 m/s command, mat height / bevel length (sim pass only)',fontsize=9)
fig.tight_layout(); fig.savefig(OUT+'D4_mat_trip.png',dpi=110)
