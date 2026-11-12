import numpy as np, json
from stance import *
OTH=[b for b in range(2,17) if b not in (TRUNK,FL,FR)]
rows=[]
for h in np.radians(np.arange(-70,31,2.5)):
  for k in np.radians(np.arange(0,90.1,2.5)):
    for a in np.radians(np.arange(-90,90.1,2.5)):
      if abs(a)>1.5708 or not(-1.2217<=h<=0.5236): continue
      p=flat_pose(h,k,a)
      if abs(np.degrees(p))>45: continue
      cx,x0,x1=support_ok()
      if not(x0<cx<x1): continue
      oth=min(body_minz(b) for b in OTH)
      if oth< -0.0005: continue
      rows.append((body_minz(TRUNK),h,k,a,p,cx-x0,x1-cx,oth))
rows=np.array(rows); np.save('sit2.npy',rows)
o=rows[:,0].argsort()
for i in o[:8]: print(round(rows[i,0]*1000,1),np.round(np.degrees(rows[i,1:5]),1),np.round(rows[i,5:8]*1000,1))
lev=rows[np.abs(np.degrees(rows[:,4]))<10]; i=lev[:,0].argmin(); print('level trunk (+/-10):',lev[i,0]*1000,np.degrees(lev[i,1:5]),lev[i,5:8]*1000)
