import json,numpy as np
s=json.load(open('stance.json')); t=json.load(open('sit.json'))
cases={'stand_best':s['best_tall'],'home':s['home'],'crouch':s['crouch'],'straight':s['straight'],'sit_low':t['low']}
# corners: central kt 1.21 (BAM), R 2.63 ohm loop, Rwc 10, Rba 11.6 (bare still air; docked = no walking airflow)
C={'central':dict(kt=1.21164,cf=1.0,R=2.5+0.13,Rwc=10,Rba=11.6),'high':dict(kt=0.765,cf=1.25,R=2.5+0.43,Rwc=15,Rba=11.6)}
out={}
for n,c in cases.items():
  out[n]={}
  for cn,p in C.items():
    rows={}; tot=0; worst=None
    for j,tau in c['tau'].items():
      I=abs(tau)/p['kt']*p['cf']
      P=I*I*p['R']; Pw=I*I*2.5
      dTb=P*p['Rba']+0.021*7.2*p['Rba']   # body rise (incl idle electronics)
      dTw=dTb+Pw*p['Rwc']
      rows[j]=dict(tau=round(tau,3),I=round(I,3),P=round(P,3),dT_body=round(dTb,1),dT_wind=round(dTw,1))
      tot+=I
      if worst is None or dTw>rows[worst]['dT_wind']: worst=j
    out[n][cn]=dict(rows=rows,I_motor_sum=round(tot,2),I_bus=round(tot+14*0.021,2),worst=worst,worst_dTw=rows[worst]['dT_wind'],worst_dTb=rows[worst]['dT_body'])
    print(n,cn,'sum',round(tot,2),'bus',round(tot+14*0.021,2),'worst',worst,rows[worst])
json.dump(out,open('therm.json','w'),indent=1)
