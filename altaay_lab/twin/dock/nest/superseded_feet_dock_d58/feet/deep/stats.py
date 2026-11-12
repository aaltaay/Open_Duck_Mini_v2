import json,sys,numpy as np
from dock import POCKET_Y
R=json.load(open(sys.argv[1]))
for fl in ['hard','train','tile']:
  for mo in ['direct','shuffle','adjust']:
    rr=[r for r in R if r['floor']==fl and r['mode']==mo and r.get('hist')]
    F=np.array([r['hist'][-1]['feet'] for r in rr]); P=np.array([r['hist'][-1]['pre'] for r in rr])
    ex=F[:,:,0]*1000; ey=(np.abs(F[:,:,1])-POCKET_Y)*1000; yw=np.degrees(F[:,:,2])
    sh=(F-P)[:,:,0]*1000
    print(fl,mo,'n',len(rr),'per-foot x p95 %.1f'%np.percentile(abs(ex),95),'y p95 %.1f'%np.percentile(abs(ey),95),'yaw p95 %.1f'%np.percentile(abs(yw),95),
      'standup slip x L %.1f R %.1f (mean), |max| %.1f'%(sh[:,0].mean(),sh[:,1].mean(),abs(sh).max()),'t_dock mean %.0f s'%np.mean([r['t_dock'] for r in rr]))
