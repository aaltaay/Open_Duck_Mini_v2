import numpy as np, json
from stance import *
r=np.load('sit2.npy')
for name,sel in [('margin15',(r[:,5]>.015)&(r[:,6]>.015)),('margin15_level15',(r[:,5]>.015)&(r[:,6]>.015)&(abs(np.degrees(r[:,4]))<15))]:
  s=r[sel]; i=s[:,0].argmin(); print(name,round(s[i,0]*1000,1),np.round(np.degrees(s[i,1:5]),1),np.round(s[i,5:8]*1000,1))
out={}
s=r[(r[:,5]>.015)&(r[:,6]>.015)]; i=s[:,0].argmin(); low=s[i]
h,k,a=low[1:4]
out['low']=hold(h,k,a,T=4)
print({x:v for x,v in out['low'].items() if x!='tau'}); print({x:round(v,3) for x,v in out['low']['tau'].items() if abs(v)>.01})
# rise path: interpolate to best tall stand, quasi static holds at 6 points
b=json.load(open('stance.json'))['best_tall']
path=[]
for t in np.linspace(0,1,6):
  rr=hold(h+(b['h']-h)*t,k+(b['k']-k)*t,a+(b['a']-a)*t,T=2.5)
  path.append(dict(t=float(t),maxabs=rr['maxabs'],up=rr['upright'],belly=rr['belly_mm'],knee=rr['tau']['left_knee'],ank=rr['tau']['left_ankle'],hip=rr['tau']['left_hip_pitch']))
  print(path[-1])
out['path']=path; out['low_pose_deg']=list(np.degrees(low[1:5]))
json.dump(out,open('sit.json','w'),indent=1)
