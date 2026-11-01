import json, collections
S=json.load(open('sites.json'))
SERVO=('wj-',)
def anchor_type(m,d,L):
    if m=='drive_palonier' and abs(d-2.5)<0.2: return 'horn_M3_tapped(drive)'
    if m=='passive_palonier' and abs(d-2.5)<0.2: return 'horn_M3_tapped(passive)'
    if abs(d-4.0)<0.15 and L>=5.0: return 'M3_insert_bore'
    if m.startswith('wj-') and d<2.1: return 'servo_case_pilot'
    return None
res=[]
for s in S:
    segs=[dict(t0=a,t1=b,m=m,k=k,d=d,i=i) for a,b,m,k,d,i in s['segs']]
    used=set()
    for j,sg in enumerate(segs):
        # clearance hole in a printed (non servo, non horn) part
        if sg['m'].startswith('wj-') or 'palonier' in sg['m']: continue
        if not (2.4<=sg['d']<=3.7): continue
        if anchor_type(sg['m'],sg['d'],sg['t1']-sg['t0']): continue
        # find head recess of same instance adjacent
        for h in segs:
            if h['i']==sg['i'] and h['d']>=3.9 and (abs(h['t1']-sg['t0'])<0.45 or abs(h['t0']-sg['t1'])<0.45):
                if anchor_type(h['m'],h['d'],h['t1']-h['t0'])=='M3_insert_bore' and h['m'] not in ('battery_pack_lid',): continue
                direction = 1 if abs(h['t1']-sg['t0'])<0.45 else -1
                head_face = h['t1'] if direction==1 else h['t0']
                # walk
                cand=[x for x in segs if x['i']!=sg['i'] and anchor_type(x['m'],x['d'],x['t1']-x['t0'])]
                cand=[x for x in cand if (x['t0']-head_face)*direction>=-0.5 or (x['t1']-head_face)*direction>=-0.5]
                if not cand: res.append((sg['m'],round(sg['d'],1),round(h['d'],1),'NO_ANCHOR',None,None,None)); break
                cand.sort(key=lambda x: min((x['t0']-head_face)*direction,(x['t1']-head_face)*direction))
                a=cand[0]
                near=min((a['t0']-head_face)*direction,(a['t1']-head_face)*direction)
                far=max((a['t0']-head_face)*direction,(a['t1']-head_face)*direction)
                res.append((sg['m'],round(sg['d'],1),round(h['d'],1),anchor_type(a['m'],a['d'],a['t1']-a['t0']),a['m'],round(near,1),round(far,1)))
                break
        else:
            res.append((sg['m'],round(sg['d'],1),None,'NO_HEAD_SEAT',None,None,None))
c=collections.Counter(res)
for k,v in sorted(c.items(),key=lambda kv:(str(kv[0][3]),kv[0][0])): print(v,k)
print(sum(c.values()))
json.dump([list(k)+[v] for k,v in c.items()],open('screws.json','w'))
