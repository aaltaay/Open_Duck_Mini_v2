"""V1 track 8 phase 3 (D50) seats and routes of the duck-side dock parts, CAD check only. Run in order: vox, vox_print, pick3, route2, views (each takes the scratch folder as argv[1]; search.py holds the shared box tests)."""
import os, sys
LAB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.chdir(OUT)
import numpy as np, json
from scipy import ndimage
import sys; sys.path.insert(0, '.')
d = np.load('occ.npz'); occ, lo, h = d['occ'].copy(), d['lo'], float(d['h'])
C3 = json.load(open(os.path.join(LAB, 'cables3d', 'cables3d.json')))
# existing cable tubes in the trunk as occupied
G = lambda p: np.round((np.array(p) - lo) / h).astype(int)
for c in C3['cables']:
    for r in c['runs']:
        P = [q['p'] for q in r['points'] if q['link'] == 'trunk_assembly']
        rad = max(1, int(np.ceil(r.get('d_mm', c.get('d_mm', 2)) / 2)))
        for a, b in zip(P[:-1], P[1:]):
            n = int(np.linalg.norm(np.subtract(b, a))) + 1
            for t in np.linspace(0, 1, n + 1):
                i = G(np.add(a, np.multiply(t, np.subtract(b, a))))
                sl = tuple(slice(max(0, i[k] - rad), i[k] + rad + 1) for k in range(3)); occ[sl] = True
np.savez_compressed('occ_cab.npz', occ=occ, lo=lo, h=h)
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'search.py')).read().split('inner = dict')[0].replace("d = np.load('occ.npz'); occ, lo, h = d['occ'], d['lo'], float(d['h'])", ''))
dp=np.load('occ_print.npz')['occ']
IP=np.pad(dp.astype(np.int32),((1,0),(1,0),(1,0))).cumsum(0).cumsum(1).cumsum(2)
def cntp(a,b):
    (x0,y0,z0),(x1,y1,z1)=a,b
    return (IP[x1,y1,z1]-IP[x0,y1,z1]-IP[x1,y0,z1]-IP[x1,y1,z0]+IP[x0,y0,z1]+IP[x0,y1,z0]+IP[x1,y0,z0]-IP[x0,y0,z0])
def touchp(c,dims,gap=1.6):
    out=[]
    for k,s in [(k,s) for k in range(3) for s in (-1,1) if np.prod([dims[j] for j in range(3) if j!=k])>=900]:
        p=np.array(c,float); p[k]+=s*(dims[k]/2+gap); dd=np.array(dims,float); dd[k]=0.6
        a=idx(p-dd/2); b=np.maximum(idx(p+dd/2),idx(p-dd/2)+1)
        if (a>=0).all() and (b<=np.array(dp.shape)).all() and cntp(a,b)>0.8*np.prod(b-a): out.append((k,s))
    return out
def scan(dims_list, rx, ry, rz, face=None, score=None, avoid=()):
    best = None
    for dims in dims_list:
        for x in np.arange(*rx, 1.0):
            for y in np.arange(*ry, 1.0):
                for z in np.arange(*rz, 1.0):
                    c = np.array((x, y, z))
                    if any(np.all(np.abs(c - a[0]) < (np.array(dims) + np.array(a[1])) / 2 + 1) for a in avoid): continue
                    if not free_box(c, dims): continue
                    t = touchp(c, dims)
                    if not t or (face and face not in t): continue
                    s = score(c)
                    if best is None or s < best[0]: best = (s, c.tolist(), list(dims), t)
    return best
out = {}
import sys
if 0: out['DK2'] = scan([(3, 13, 8), (3, 8, 13)], (25, 36), (-12, 13), (12, 33), face=(0, 1), score=lambda c: abs(c[1]) + abs(c[2] - 24))
vin = np.array([-107.8, 14.0, 29.0])
out['DK7']=[0,[-104.0,13.0,45.0],[8,13,3],[[2,1]]]
if 0: out['DK7'] = scan([(3, 8, 13), (3, 13, 8), (8, 3, 13), (13, 3, 8), (13, 8, 3), (8, 13, 3)], (-114, -94), (0, 30), (10, 50), score=lambda c: np.linalg.norm(c - vin))
a7 = (np.array(out['DK7'][1]), out['DK7'][2])
out['DK6']=[0,[-104.0,1.0,45.0],[13,8,3],[[2,1]]]
if 0: out['DK6'] = scan([(3, 8, 13), (3, 13, 8), (8, 3, 13), (13, 3, 8), (13, 8, 3), (8, 13, 3)], (-114, -94), (0, 30), (10, 50), score=lambda c: np.linalg.norm(c - vin), avoid=[a7])
out['DK2']=[0,[33.0,0.0,24.0],[3,13,8],[[0,1]]]
av=[(np.array(out[k][1]),out[k][2]) for k in ('DK2','DK6','DK7')]
mid = np.array([-80.0, 0.0, 20.0])
out['F2'] = scan([(52, 18, 18), (18, 52, 18), (18, 18, 52)], (-112, 30), (-45, 46), (-14, 80), score=lambda c: np.linalg.norm(c - mid), avoid=av)
json.dump(out, open('picked.json', 'w'), indent=1); print(json.dumps(out))
