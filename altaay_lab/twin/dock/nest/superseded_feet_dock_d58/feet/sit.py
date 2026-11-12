import numpy as np, json
from stance import *
best=None; rows=[]
for h in np.radians(np.arange(-70,31,2.5)):
  for k in np.radians(np.arange(0,90.1,2.5)):
    for a in np.radians(np.arange(-90,90.1,2.5)):
      p=flat_pose(h,k,a)
      if abs(np.degrees(p))>35: continue
      cx,x0,x1=support_ok()
      belly=body_minz(TRUNK)
      inside = x0<cx<x1
      rows.append((belly,h,k,a,p,cx-x0,x1-cx,inside))
rows=np.array(rows,dtype=float)
ins=rows[rows[:,7]>0]
i=ins[:,0].argmin(); print('lowest belly with COM over soles (mm):',ins[i,0]*1000,np.degrees(ins[i,1:5]),ins[i,5:7]*1000)
i=rows[:,0].argmin(); print('lowest any:',rows[i,0]*1000,np.degrees(rows[i,1:5]))
# limit at the corner: report which joints at limit
np.save('sit_rows.npy',rows)
