import json, collections
S=json.load(open('sites.json'))
ELEC={'raspberrypizerow','board','bno055','usb_c_charger','power_switch','cell','bms','holder','sg90','antenna'}
def short(m): return m.replace('wj-wk00-0122topcabinetcase_95','SRV_top').replace('wj-wk00-0124bottomcase_45','SRV_bot').replace('wj-wk00-0123middlecase_56','SRV_mid').replace('left_knee_to_ankle_','k2a_')
cats=collections.Counter(); rows=[]
for s in S:
    segs=s['segs']; meshes={x[2] for x in segs}; inst={x[5] for x in segs}
    desc=' | '.join(f"{short(m)}:{k[0]}{d}x{t1-t0:.1f}@{t0:.1f}" for t0,t1,m,k,d,i in segs)
    ds=[(x[2],x[4],x[1]-x[0]) for x in segs]
    if 'roll_bearing' in meshes: c='bearing'
    elif meshes & {'drive_palonier','passive_palonier'}: c='horn'
    elif any(m.startswith('wj-') for m in meshes): c='servo_case' if len(inst)>1 else 'servo_internal'
    elif meshes <= ELEC: c='electronics_only'
    elif meshes & ELEC: c='electronics_mount'
    elif len(inst)==1: c='single_part'
    else: c='part_to_part'
    cats[c]+=1; rows.append((c,desc))
print(cats)
with open('sites.txt','w') as f:
    for c,d in sorted(rows): f.write(f"{c}: {d}\n")
