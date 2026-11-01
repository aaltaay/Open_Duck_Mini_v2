import json,sys
d=json.load(open(sys.argv[1]))
for f,r in d.items():
    if len(sys.argv)>2 and f not in sys.argv[2:]: continue
    print('==',f,r['extents'],'vol',r['volume_cm3'],'rot',r['rotated_to_align'],'wall',[round(x,2) for x in r['wall_min_p1_p5_med']])
    for ax,fs in r['features'].items():
        c=[x for x in fs if x['kind']!='other' and x['depth']>=0.6]
        from collections import Counter
        if c: print('  ',ax,'circ/hex (kind,d,depth):count',sorted(Counter((x['kind'],round(x['d'],1),round(x['depth'],1)) for x in c).items()))
        o=[x for x in fs if x['kind']=='other' and x['depth']>=1 and x['w']>2]
        if o: print('  ',ax,'other (w,l,depth):',sorted(Counter((round(x['w'],1),round(x['l'],1),round(x['depth'],1)) for x in o).items())[:12])
