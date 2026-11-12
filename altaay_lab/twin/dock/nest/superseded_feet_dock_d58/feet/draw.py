import json, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Polygon, FancyArrowPatch
from scipy.spatial import ConvexHull
from geo import *
from stance import body_minz

import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '')
S = json.load(open('stance.json')); T = json.load(open('sit.json'))
B = S['best_tall']
C = dict(sole='#d9773a', foot='#f2a65a', head='#f6d36b', trunk='#f8e3a3', leg='#e3d8c8')
MAT, MATE, POCK, PIN = '#bfe3d6', '#5aa58c', '#9fd3c2', '#c9a227'
NET = {'CHG+': '#d64545', 'SENSE': '#3b7dd8', 'SYS': '#e08a1e', 'GND': '#333333'}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9})

# geometry (mm, mat frame: x forward, y left, z up; origin = centre of the foot zones on the mat top)
FOOT_Y = 90.6; SOLE_L, SOLE_W = 101.9, 40.7
PAD_L, PAD_W, PAD_X = 44, 34, 26          # pad fore-aft, lateral, centre offset from sole centre
PIN_Y = np.arange(-18, 19, 6)             # 7 pins per zone, 6 mm pitch, across the foot
MAT_X0, MAT_X1, MAT_W, MAT_T, BEV = -200, 200, 300, 7, 35
POCK_L, POCK_W = 130, 70
NETS = {('L', 1): 'CHG+', ('L', -1): 'SENSE', ('R', 1): 'SYS', ('R', -1): 'GND'}

def duck_shift():
    m.mj_kinematics(mod, dat)
    xs, ys = [], []
    for g in SOLE:
        v = verts(g); xs += [v[:, 0].min(), v[:, 0].max()]; ys.append(v[:, 1].mean())
    return np.array([-(min(xs) + max(xs)) / 2, -np.mean(ys), 0.0])

def draw_duck(ax, axes, dx=0, dz=0, scale=1.0, alpha=1.0, flip=False, mat_t=MAT_T):
    sh = duck_shift()
    for kind, P, d, g in sorted(polys(axes, shift=sh), key=lambda t: t[2] * (-1 if flip else 1)):
        P = P.copy()
        if axes == (0, 2): P[:, 1] += mat_t
        ax.add_patch(Polygon(P * scale + [dx, dz], closed=True, fc=C[kind], ec='#7a6a55', lw=0.5,
                             joinstyle='round', alpha=alpha))

def mat_side(ax, x0=MAT_X0, x1=MAT_X1, dx=0):
    pts = [(x0 + dx, 0), (x0 + BEV + dx, MAT_T), (x1 - BEV + dx, MAT_T), (x1 + dx, 0)]
    ax.add_patch(Polygon(pts, fc=MAT, ec=MATE, lw=1.2))

def floor(ax, x0, x1):
    ax.plot([x0, x1], [0, 0], color='#8a7f72', lw=1.5)
    for x in np.arange(x0, x1, 25): ax.plot([x, x - 8], [0, -8], color='#b8afa3', lw=0.6)

def foot_zone(ax, side, y):
    ax.add_patch(FancyBboxPatch((-POCK_L / 2, y - POCK_W / 2), POCK_L, POCK_W, boxstyle='round,pad=0,rounding_size=22',
                                fc=POCK, ec=MATE, lw=1))
    # webbed duck-foot print inside the pocket (friendly cue)
    for s in (1, -1):
        ax.add_patch(Rectangle((s * PAD_X - PAD_L / 2, y - PAD_W / 2), PAD_L, PAD_W, fc='none', ec=NET[NETS[(side, s)]],
                               lw=0.8, ls=(0, (3, 2))))
        for py in PIN_Y: ax.add_patch(Circle((s * PAD_X, y + py), 1.6, fc=PIN, ec='#7a5f00', lw=0.5))
        ax.text(s * PAD_X, y + PAD_W / 2 + 4, NETS[(side, s)], ha='center', fontsize=7, color=NET[NETS[(side, s)]])

def lily(ax, x, y, r=28):
    ax.add_patch(Circle((x, y), r, fc='#8fcf9f', ec='#4f9a63', lw=1))
    ax.add_patch(Polygon([(x, y), (x + r * 1.05, y - 6), (x + r * 1.05, y + 6)], fc='white', ec='none'))

def mat_top(ax, dims=True):
    W = MAT_W / 2
    ax.add_patch(FancyBboxPatch((MAT_X0, -W), MAT_X1 - MAT_X0, MAT_W, boxstyle='round,pad=0,rounding_size=60',
                                fc=MAT, ec=MATE, lw=1.5))
    ax.add_patch(FancyBboxPatch((MAT_X0 + BEV, -W + BEV), MAT_X1 - MAT_X0 - 2 * BEV, MAT_W - 2 * BEV,
                                boxstyle='round,pad=0,rounding_size=35', fc='none', ec=MATE, lw=0.6, ls=':'))
    for side, y in (('L', FOOT_Y), ('R', -FOOT_Y)): foot_zone(ax, side, y)
    # flat centre tag (flush print) and two low lily-pad posts on side ears
    ax.add_patch(Rectangle((-30, -30), 60, 60, fc='white', ec='black', lw=1))
    rng = np.random.default_rng(3)
    for i in range(6):
        for j in range(6):
            if (i in (0, 5) or j in (0, 5)) or rng.random() < 0.5:
                ax.add_patch(Rectangle((-30 + 7.5 + i * 7.5, -30 + 7.5 + j * 7.5), 7.5, 7.5, fc='black', ec='none'))
    for s in (1, -1):
        lily(ax, 150, s * 172)
        ax.add_patch(Rectangle((140, s * 172 - 25), 6, 50, fc='white', ec='black', lw=0.8))
    if dims:
        def dim(p0, p1, txt, off, vert=False):
            ax.annotate('', p0, p1, arrowprops=dict(arrowstyle='<->', color='#555', lw=0.7))
            mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
            ax.text(mx + (off if vert else 0), my + (0 if vert else off), txt, ha='center', va='center', fontsize=7,
                    color='#333', rotation=90 if vert else 0, bbox=dict(fc='white', ec='none', pad=0.5, alpha=0.8))
        dim((MAT_X0, -W - 22), (MAT_X1, -W - 22), '400 (mat body)', 0)
        dim((MAT_X1 + 18, -W), (MAT_X1 + 18, W), '300', 0, vert=True)
        dim((-POCK_L / 2, FOOT_Y + 46), (POCK_L / 2, FOOT_Y + 46), '130 pocket', 0)
        dim((-90, -FOOT_Y), (-90, FOOT_Y), 'feet at y +/-90.6 (181)', -10, vert=True)
        dim((MAT_X0, 125), (MAT_X0 + BEV, 125), '35 bevel', 8)
        ax.text(0, 0, '', fontsize=7)
        ax.text(38, 0, 'tag id 0\n60 mm, flush', ha='left', va='center', fontsize=7)
        ax.text(150, 210, 'tag posts on lily pads\n110 mm tall, tags 50 mm', ha='center', fontsize=7)
        ax.text(-300, 0, 'walk ON\n-->', ha='center', fontsize=10, color='#2f7a5f', fontweight='bold')
        ax.text(300, 0, 'walk OFF\n-->', ha='center', fontsize=10, color='#2f7a5f', fontweight='bold')

# ---------- F1 side and top on the mat ----------
pose(B['h'], B['k'], B['a'])
fig, ax = plt.subplots(1, 2, figsize=(14, 7.2), gridspec_kw=dict(width_ratios=[1, 1.25]))
a = ax[0]; floor(a, -260, 260); mat_side(a); draw_duck(a, (0, 2))
for s in (1, -1):
    for py in [0]: a.add_patch(Rectangle((s * PAD_X - 1.2, MAT_T - 1.5), 2.4, 3, fc=PIN, ec='#7a5f00', lw=0.4))
a.add_patch(Rectangle((146 - 3, MAT_T), 6, 110, fc='#4f9a63', ec='none'))
a.add_patch(Rectangle((146 - 25, MAT_T + 75), 50, 50, fc='white', ec='black', lw=0.8))
a.text(0, -30, 'standing tall: hip pitch -15, knee +5, ankle 0 deg; trunk tilted 10 deg nose-up\n'
       'mat 7 mm, 35 mm bevels both ends (no ramp); pins stand 1.5 mm proud in the pockets', ha='center', fontsize=8)
a.set_title('Side: Duckie standing on the charging mat (sim pose, mm)', fontsize=10)
a.set_xlim(-270, 270); a.set_ylim(-50, 530); a.set_aspect('equal'); a.axis('off')
a = ax[1]; mat_top(a, dims=True); draw_duck(a, (0, 1), alpha=0.55)
a.set_title('Top: feet on the two pockets, tag between the feet, posts out of the walk-off path', fontsize=10)
a.set_xlim(-340, 340); a.set_ylim(-260, 235); a.set_aspect('equal'); a.axis('off')
fig.tight_layout(); fig.savefig(OUT + 'F1_side_top_on_mat.png', dpi=130); plt.close(fig)

# ---------- F2 sole underside ----------
fig, ax = plt.subplots(1, 2, figsize=(12, 5.6))
m.mj_kinematics(mod, dat)
for a, (side, g) in zip(ax, (('L', SOLE[0]), ('R', SOLE[1]))):
    v = verts(g) * 1000; cx = (v[:, 0].min() + v[:, 0].max()) / 2; cy = v[:, 1].mean()
    P = v[:, :2] - [cx, cy]; h = ConvexHull(P)
    a.add_patch(Polygon(P[h.vertices], fc='#e9a46a', ec='#9a5a2a', lw=1.5))
    for s in (1, -1):
        net = NETS[(side, s)]
        a.add_patch(FancyBboxPatch((s * PAD_X - PAD_L / 2, -PAD_W / 2), PAD_L, PAD_W, boxstyle='round,pad=0,rounding_size=5',
                                   fc='#c8ccd0', ec=NET[net], lw=2))
        a.text(s * PAD_X, 0, f'{net}\n316L 0.3 mm\n44 x 34', ha='center', va='center', fontsize=8)
        a.add_patch(Circle((s * PAD_X, PAD_W / 2 - 5), 1.6, fc='#666'))  # wire via / rivet
    a.annotate('', (-PAD_X + PAD_L / 2, -26), (PAD_X - PAD_L / 2, -26), arrowprops=dict(arrowstyle='<->', lw=0.7))
    a.text(0, -31, '8 gap', ha='center', fontsize=7)
    a.annotate('', (-50.95, 29), (50.95, 29), arrowprops=dict(arrowstyle='<->', lw=0.7)); a.text(0, 32, '101.9', ha='center', fontsize=7)
    a.annotate('', (58, -20.35), (58, 20.35), arrowprops=dict(arrowstyle='<->', lw=0.7)); a.text(62, 0, '40.7', rotation=90, va='center', fontsize=7)
    a.text(0, -44, ('LEFT sole, from below' if side == 'L' else 'RIGHT sole, from below') +
           '\npads recessed 0.3 mm under the TPU tread: the floor wears the TPU, not the pads', ha='center', fontsize=8)
    a.text(48, 24, 'toe ->', fontsize=8, color='#555'); a.text(-62, 24, 'heel', fontsize=8, color='#555')
    a.set_xlim(-70, 75); a.set_ylim(-52, 40); a.set_aspect('equal'); a.axis('off')
fig.suptitle('Sole underside: 2 pads per foot, 4 nets (heel pads SENSE and GND break first when a foot lifts)', fontsize=11)
fig.tight_layout(); fig.savefig(OUT + 'F2_sole_pads.png', dpi=130); plt.close(fig)

# ---------- F3 leg wiring ----------
import json as _j
cab = {c['id']: c for c in _j.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..', 'cables3d', 'cables3d.json')))['cables']}
pose(B['h'], B['k'], B['a']); m.mj_kinematics(mod, dat); sh = duck_shift()
fig, ax = plt.subplots(1, 2, figsize=(13, 7.5), gridspec_kw=dict(width_ratios=[1, 1]))
for a, axes in zip(ax, ((0, 2), (1, 2))):
    floor(a, -200, 200)
    for kind, P, d, g in sorted(polys(axes, shift=sh), key=lambda t: t[2]):
        a.add_patch(Polygon(P, fc=C[kind], ec='#7a6a55', lw=0.4, alpha=0.75))
    for cid, col in (('D3', '#d64545'), ('D4', '#e08a1e')):
        c = cab[cid]; pts = []
        for p in c['points']:
            bi = m.mj_name2id(mod, 1, p['link'])
            if p['link'] in ('head_assembly', 'head_pitch_to_yaw', 'neck_yaw_assembly', 'neck_pitch_assembly'): continue
            w = dat.xmat[bi].reshape(3, 3) @ (np.array(p['p']) / 1000) + dat.xpos[bi] + sh
            pts.append(w * 1000)
        pts = np.array(pts); a.plot(pts[:, axes[0]], pts[:, axes[1]], color=col, lw=2.2, solid_capstyle='round')
        for sl in c['service_loops']:
            j = sl['joints'][0]
            if 'head' in j or 'neck' in j: continue
            ji = m.mj_name2id(mod, 3, j); bi = mod.jnt_bodyid[ji]
            jp = (dat.xanchor[ji] + sh) * 1000
            a.add_patch(Circle((jp[axes[0]], jp[axes[1]]), 9, fc='none', ec=col, lw=1.2, ls='--'))
            if axes == (0, 2) and cid == 'D3':
                a.text(jp[0] + 14, jp[2] + {'left_hip_roll': 14, 'left_hip_pitch': -10}.get(j, 0), f"{j.replace('left_', '')}: loop r {sl['radius_mm']} mm, swing {np.degrees(sl['angle_rad']):.0f} deg",
                       fontsize=7.5, va='center', bbox=dict(fc='white', ec='none', alpha=0.8, pad=0.5))
    a.set_aspect('equal'); a.axis('off')
ax[0].set_xlim(-190, 230); ax[0].set_ylim(-20, 330); ax[1].set_xlim(-200, 200); ax[1].set_ylim(-20, 330)
ax[0].set_title('Side: 2 new wires ride the existing foot-switch bundle D3 (left) / D4 (right)', fontsize=10)
ax[1].set_title('Front view (duck left on the right): one bundle per leg, 5 flex points (hip yaw, roll, pitch, knee, ankle)', fontsize=10)
fig.text(0.5, 0.03, 'Left leg adds CHG+ (26 AWG) and SENSE (30 AWG); right leg adds SYS and GND (24 AWG each), all fine-strand silicone. '
         'Route lengths and loop radii from cables3d (D3 route 625 to 774 mm Pi to foot).\n'
         'Loops are sized for the existing 3.5 mm bundle; adding 2 wires keeps the loop radius at 10.4 to 15.1 mm = 6.5 to 9 x the 24 AWG OD. '
         'Flex life of this loop: no data (BLOCKER).', ha='center', fontsize=8)
fig.savefig(OUT + 'F3_leg_wiring.png', dpi=130); plt.close(fig)

# ---------- F4 mat top with dimensions ----------
fig, a = plt.subplots(figsize=(11, 7.5))
mat_top(a, dims=True)
for s, side in ((1, 'L'), (-1, 'R')):
    a.add_patch(Rectangle((-SOLE_L / 2, s * FOOT_Y - SOLE_W / 2), SOLE_L, SOLE_W, fc='none', ec='#9a5a2a', lw=1, ls='--'))
a.text(0, FOOT_Y - 45, 'LEFT foot zone', ha='center', fontsize=8, color='#2f7a5f')
a.text(0, -FOOT_Y + 41, 'RIGHT foot zone', ha='center', fontsize=8, color='#2f7a5f')
a.text(-195, -232, 'Pockets 1 mm deep, 6 deg sides (a cue, not a trap). Each zone: 7 spring pins in a row across the foot, 6 mm pitch.\n'
       'Window: fore-aft +/-20 mm, lateral +/-27 mm (2 or more pins on the pad), yaw +/-4 deg costs 6 mm at the pins.\n'
       'Dashed brown: the sole at nominal. Whole mat is dead until the hardware gate sees the battery NTC + duck signature.', fontsize=8)
a.set_xlim(-350, 350); a.set_ylim(-245, 240); a.set_aspect('equal'); a.axis('off')
a.set_title('Charging mat, top view (mm). 7 mm thick, lily-pond look', fontsize=11)
fig.tight_layout(); fig.savefig(OUT + 'F4_mat_top.png', dpi=130); plt.close(fig)

# ---------- F5 strip ----------
fig, ax = plt.subplots(1, 4, figsize=(16, 5))
home = S['home']
frames = [('1 walk on (forward, tags in view)', (home['h'], home['k'], home['a']), -110, ''),
          ('2 stop on the pockets, stand tall', (B['h'], B['k'], B['a']), 0, 'gate checks NTC + SYS signature'),
          ('3 charge (torque ON, 0.9 A bus)', (B['h'], B['k'], B['a']), 0, 'charging, eyes dim, listening'),
          ('4 walk off forward (or turn left)', (home['h'], home['k'], home['a']), 190, 'heel lifts: SENSE/GND break first')]
for a, (t, p, dx, note) in zip(ax, frames):
    floor(a, -300, 330); mat_side(a)
    a.add_patch(Rectangle((146 - 3, MAT_T), 6, 110, fc='#4f9a63', alpha=.5)); a.add_patch(Rectangle((121, MAT_T + 75), 50, 50, fc='white', ec='k', lw=0.8, alpha=.5))
    a.text(146, MAT_T + 135, 'post (beside the path)', ha='center', fontsize=7, color='#4f9a63')
    pose(*p); draw_duck(a, (0, 2), dx=dx)
    if '3' in t:
        a.add_patch(Circle((0 + 40, 330), 14, fc='#7bd389', ec='#2f7a5f')); a.text(40, 330, '+', ha='center', va='center', fontsize=14, color='white')
    if '1' in t or '4' in t:
        a.annotate('', (dx + 120, 280), (dx + 40, 280), arrowprops=dict(arrowstyle='->', lw=2, color='#2f7a5f'))
    a.text(0, -40, note, ha='center', fontsize=8); a.set_title(t, fontsize=9)
    a.set_xlim(-300, 330); a.set_ylim(-55, 520); a.set_aspect('equal'); a.axis('off')
fig.suptitle('Walk on, stop, stand, charge, walk off forward. No backing up.', fontsize=11)
fig.tight_layout(); fig.savefig(OUT + 'F5_walk_on_off_strip.png', dpi=120); plt.close(fig)

# ---------- F6 lowest sit with soles flat ----------
lp = T['low']; pose(lp['h'], lp['k'], lp['a'])
fig, ax = plt.subplots(1, 2, figsize=(12, 6.5))
for a, (pp, ttl) in zip(ax, (((lp['h'], lp['k'], lp['a']), f"Lowest sit, soles flat: belly {lp['belly_mm']:.0f} mm above the mat"),
                             ((B['h'], B['k'], B['a']), 'Charging stance for comparison: belly 157 mm'))):
    floor(a, -220, 220); mat_side(a, -200, 200); pose(*pp); draw_duck(a, (0, 2))
    m.mj_kinematics(mod, dat); bz = body_minz(TRUNK) * 1000 + MAT_T
    a.annotate('', (-150, MAT_T), (-150, bz), arrowprops=dict(arrowstyle='<->', color='#d64545'))
    a.plot([-160, 120], [bz, bz], color='#d64545', lw=0.6, ls='--')
    a.text(-155, (bz + MAT_T) / 2, f'{bz - MAT_T:.0f}', color='#d64545', ha='right', va='center')
    a.set_title(ttl, fontsize=10); a.set_xlim(-220, 220); a.set_ylim(-60, 520); a.set_aspect('equal'); a.axis('off')
ax[0].text(0, -45, 'hip pitch +30 (limit), knee 90 (limit), ankle -82.5, trunk tilted 37 deg nose-down.\nThe belly cannot reach the floor: knee and hip pitch limits stop it (the shins already sit lower than the belly).', ha='center', fontsize=8)
fig.tight_layout(); fig.savefig(OUT + 'F6_lowest_sit.png', dpi=120); plt.close(fig)
print('ok')
