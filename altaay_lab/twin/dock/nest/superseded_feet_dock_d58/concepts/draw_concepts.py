"""Concept sketches for the Duckie dock (2D, not CAD). Units mm. Run: python3 draw_concepts.py"""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Ellipse, Circle, Polygon, FancyArrowPatch
import os
OUT = os.path.dirname(os.path.abspath(__file__))
FOOT_L, FOOT_W, FOOT_Y = 102, 41, 62.5   # sole 101.9 x 40.7 (print/foot_bottom_tpu.stl); centre y derived from DOCK_TWIN seat clearance
INK, LIVE, GNDC, PAD, GHOST = "#222", "#c0392b", "#2c3e50", "#d9d9d9", "#9aa"
plt.rcParams.update({"font.size": 7, "font.family": "DejaVu Sans"})

def dim(ax, p1, p2, text, off=(0, 0), c="#1f5fa8"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="<->", mutation_scale=6, color=c, lw=0.7))
    ax.text((p1[0]+p2[0])/2+off[0], (p1[1]+p2[1])/2+off[1], text, color=c, ha="center", va="center", fontsize=6.5,
            bbox=dict(fc="white", ec="none", pad=0.5))

def duck_side(ax, x=0, z=0, pose="stand", facing=1, alpha=1.0, color=INK):
    """Side silhouette. x = foot centre, facing +1 = looking +x."""
    f = facing; kw = dict(fill=False, ec=color, lw=1, alpha=alpha)
    ax.add_patch(Rectangle((x-FOOT_L/2, z), FOOT_L, 10, fc="#555", ec=color, alpha=alpha))
    if pose == "stand":
        hip, knee, tz = (x-5*f, z+175), (x+15*f, z+95), z+175
    elif pose == "crouch":
        hip, knee, tz = (x-35*f, z+100), (x+30*f, z+60), z+100
    else:  # sit back (hips behind feet)
        hip, knee, tz = (x-70*f, z+115), (x+10*f, z+80), z+115
    ax.plot([x, knee[0], hip[0]], [z+30, knee[1], hip[1]], color=color, lw=2, alpha=alpha)
    ax.add_patch(Ellipse((hip[0]+5*f, tz+45), 150, 110, **kw))           # trunk
    ax.add_patch(Rectangle((hip[0]+15*f-15, tz+95), 30, 45, **kw))       # neck
    hc = (hip[0]+40*f, tz+170)
    ax.add_patch(Ellipse(hc, 120, 75, **kw))                             # head
    ax.add_patch(Polygon([(hc[0]+55*f, hc[1]-5), (hc[0]+95*f, hc[1]-12), (hc[0]+55*f, hc[1]-22)], closed=True, **kw))  # bill
    ax.add_patch(Circle((hc[0]+40*f, hc[1]+8), 5, fc="#1f5fa8", ec="none", alpha=alpha))  # camera
    return hip, tz

def duck_top(ax, x=0, y=0, alpha=1.0, color=INK, feet_color="#555"):
    for s in (+1, -1):
        ax.add_patch(Rectangle((x-FOOT_L/2, y+s*FOOT_Y-FOOT_W/2), FOOT_L, FOOT_W, fc=feet_color, ec=color, alpha=alpha))
    ax.add_patch(Ellipse((x-10, y), 150, 150, fill=False, ec=color, lw=1, alpha=alpha))
    ax.add_patch(Polygon([(x+55, y+12), (x+95, y), (x+55, y-12)], fill=False, ec=color, alpha=alpha))

def floor(ax, x0, x1):
    ax.plot([x0, x1], [0, 0], color="#888", lw=1); ax.fill_between([x0, x1], -12, 0, color="#eee")

def setup(ax, title, xl, yl):
    ax.set_title(title, fontsize=8, loc="left", fontweight="bold"); ax.set_aspect("equal")
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_color("#ccc")

def arrow(ax, p1, p2, c="#27ae60"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=9, color=c, lw=1.4))

def figure(name, title, side_fn, top_fn, strip_fns, note):
    fig = plt.figure(figsize=(11, 7.6))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.15, 0.85])
    a1 = fig.add_subplot(gs[0, :2]); a2 = fig.add_subplot(gs[0, 2])
    side_fn(a1); top_fn(a2)
    labels = ["1 walk in", "2 settle (charging)", "3 leave"]
    for i, fn in enumerate(strip_fns):
        a = fig.add_subplot(gs[1, i]); fn(a); a.set_title(labels[i], fontsize=8, loc="left")
    fig.suptitle(title, fontsize=11, fontweight="bold", x=0.01, ha="left")
    fig.text(0.01, 0.005, note, fontsize=6.5, color="#555", ha="left", va="bottom", wrap=True)
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    p = os.path.join(OUT, name); fig.savefig(p, dpi=130); plt.close(fig); print(p)

TAGS = "#444"
def tag_post_side(ax, x, h=230):
    ax.add_patch(Rectangle((x, 0), 10, h, fc="#bbb", ec=INK)); ax.add_patch(Rectangle((x-1, h-75), 12, 60, fc=TAGS))

# ---------------------------------------------------------------- C1 flat pad, sole contacts
def c1_side(ax):
    setup(ax, "Side view (a pass-through pad, the duck faces the room)", (-420, 520), (-60, 470)); floor(ax, -420, 520)
    ax.add_patch(Polygon([(-260, 0), (-230, 8), (230, 8), (260, 0)], fc=PAD, ec=INK))
    for xx in (-40, 40): ax.add_patch(Rectangle((xx-30, 8), 60, 1.5, fc=LIVE))
    duck_side(ax, 0, 8, "crouch")
    tag_post_side(ax, 300, 230)
    dim(ax, (-260, -35), (260, -35), "pad 520 (calc)")
    dim(ax, (-300, 0), (-300, 8), "8", off=(-18, 0))
    dim(ax, (330, 0), (330, 230), "tag posts 230", off=(40, 0))
    ax.text(-410, 430, "Crouched, belly not supported: torque must stay ON\n(servo heat over 6 h: BLOCKER) unless a support is added (see C2)", fontsize=6.5, color=LIVE)
    ax.text(-40, 30, "spring pins in soles", fontsize=6, ha="center")
    arrow(ax, (-400, 60), (-300, 60)); arrow(ax, (300, 60), (420, 60))
    ax.text(-400, 70, "in", fontsize=6); ax.text(390, 70, "out forward", fontsize=6)

def pad_top(ax, pockets=True, x0=-260, x1=260):
    ax.add_patch(Rectangle((x0, -150), x1-x0, 300, fc=PAD, ec=INK))
    for s in (+1, -1):
        if pockets:
            ax.add_patch(Rectangle((-FOOT_L/2-25, s*FOOT_Y-FOOT_W/2-20), FOOT_L+50, FOOT_W+40, fc="#c4c4c4", ec="#777", ls="--"))
    # strips along x: left foot (y +) CHG+, SENSE, GND ; right foot (y -) SYS, GND
    lanes = {+1: [("CHG+", LIVE, 12), ("SENSE", "#e67e22", 0), ("GND", GNDC, -12)], -1: [("SYS", LIVE, 6), ("GND", GNDC, -6)]}
    for s, ls in lanes.items():
        for nm, c, dy in ls:
            ax.add_patch(Rectangle((-90, s*FOOT_Y+dy-3.5), 180, 7, fc=c, ec="none"))
            ax.text(95, s*FOOT_Y+dy, nm, fontsize=5.5, va="center", color=c)

def c1_top(ax):
    setup(ax, "Top view: 5 strips, 4 nets", (-300, 330), (-230, 230)); pad_top(ax)
    duck_top(ax, 0, 0, alpha=0.35)
    for s in (+1, -1):
        ax.add_patch(Rectangle((290, s*120-8), 10, 16, fc=TAGS))
    dim(ax, (-260, -190), (260, -190), "520")
    dim(ax, (-285, -150), (-285, 150), "300", off=(-12, 0))
    dim(ax, (-130, FOOT_Y-20.5-20), (-130, FOOT_Y+20.5+20), "pocket 81\n(+/-20)", off=(-28, 0))
    dim(ax, (-90, -215), (90, -215), "strips 180 (+/-39 fore-aft)")
    ax.text(-255, 200, "left foot: CHG+, SENSE, GND\nright foot: SYS, GND", fontsize=6)

def strip_c1(phase):
    def f(ax):
        setup(ax, "", (-420, 520), (-30, 460)); floor(ax, -420, 520)
        ax.add_patch(Polygon([(-260, 0), (-230, 8), (230, 8), (260, 0)], fc=PAD, ec=INK)); tag_post_side(ax, 300)
        if phase == 0: duck_side(ax, -330, 0, "stand"); arrow(ax, (-260, 300), (-80, 300))
        if phase == 1: duck_side(ax, 0, 8, "crouch"); ax.text(0, 440, "SENSE ok -> gate on", ha="center", fontsize=6, color=LIVE)
        if phase == 2: duck_side(ax, 380, 0, "stand", alpha=0.9); arrow(ax, (150, 300), (330, 300)); ax.text(60, 440, "walk out between the posts", fontsize=6)
    return f

# ---------------------------------------------------------------- C2 cradle
def cradle_side(ax, duck=True):
    ax.add_patch(Polygon([(-300, 0), (-200, 20), (180, 20), (280, 0)], fc=PAD, ec=INK))  # ramp + deck + exit ramp
    ax.add_patch(Polygon([(-60, 20), (-60, 100), (-15, 110), (25, 100), (25, 20)], fc="#b5b5b5", ec=INK))  # saddle
    for xx in (-40, 40): ax.add_patch(Rectangle((xx+40-30, 20), 60, 1.5, fc=LIVE))
    ax.add_patch(Rectangle((290, 0), 10, 230, fc="#bbb", ec=INK)); ax.add_patch(Rectangle((289, 155), 12, 60, fc=TAGS))
    if duck: duck_side(ax, 40, 20, "crouch")

def c2_side(ax):
    setup(ax, "Side view: pass-through deck, foot pockets, belly saddle (torque OFF while docked)", (-360, 420), (-70, 470)); floor(ax, -360, 420)
    cradle_side(ax)
    dim(ax, (-300, -40), (280, -40), "580 incl. both ramps")
    dim(ax, (-330, 0), (-330, 20), "20", off=(-15, 0))
    dim(ax, (-100, 0), (-100, 110), "saddle 110", off=(-35, 0))
    dim(ax, (330, 0), (330, 230), "tag posts 230 at y +/-150", off=(0, 0))
    ax.text(-350, 440, "Saddle top 110 (the sim crouch set the belly on a 112 seat with 7 to 22 N, DOCK_TWIN 5)\nFeet in 2 mm-deep pockets; the sole pins see belly-relieved weight", fontsize=6.3)

def c2_top(ax):
    setup(ax, "Top view", (-330, 320), (-200, 200))
    ax.add_patch(Rectangle((-300, -150), 580, 300, fc=PAD, ec=INK))
    ax.add_patch(Rectangle((-300, -150), 100, 300, fc="#e8e8e8", ec=INK, ls=":")); ax.text(-250, 0, "ramp in", rotation=90, ha="center", va="center")
    ax.add_patch(Rectangle((180, -150), 100, 300, fc="#e8e8e8", ec=INK, ls=":")); ax.text(230, 0, "ramp out", rotation=90, ha="center", va="center")
    ax.add_patch(Rectangle((-60, -20), 85, 40, fc="#b5b5b5", ec=INK))
    lanes = {+1: [("CHG+", LIVE, 12), ("SENSE", "#e67e22", 0), ("GND", GNDC, -12)], -1: [("SYS", LIVE, 6), ("GND", GNDC, -6)]}
    for s, ls in lanes.items():
        ax.add_patch(Rectangle((40-FOOT_L/2-15, s*FOOT_Y-FOOT_W/2-15), FOOT_L+30, FOOT_W+30, fc="#c4c4c4", ec="#777", ls="--"))
        for nm, c, dy in ls: ax.add_patch(Rectangle((-10, s*FOOT_Y+dy-3.5), 100, 7, fc=c))
    duck_top(ax, 40, 0, alpha=0.35)
    for sy in (1, -1): ax.add_patch(Rectangle((290, sy*150-8), 10, 16, fc=TAGS))
    dim(ax, (-300, -180), (280, -180), "580"); dim(ax, (-30, -20), (-30, 20), "40", off=(-12, 0))
    dim(ax, (110, FOOT_Y-35.5), (110, FOOT_Y+35.5), "pocket 71\n(+/-15)", off=(32, 0))

def strip_c2(phase):
    def f(ax):
        setup(ax, "", (-500, 480), (-30, 460)); floor(ax, -500, 480); cradle_side(ax, duck=False)
        if phase == 0: duck_side(ax, -400, 0, "stand"); arrow(ax, (-330, 300), (-120, 300))
        if phase == 1: duck_side(ax, 40, 20, "crouch"); ax.text(-200, 440, "crouch onto saddle, torque off", fontsize=6)
        if phase == 2:
            duck_side(ax, 360, 0, "stand", alpha=0.9); arrow(ax, (120, 300), (330, 300))
            ax.text(-300, 440, "stand up, step over the saddle end, walk out forward", fontsize=6)
    return f

# ---------------------------------------------------------------- C3 nest
def nest_side(ax, duck=True, x=0):
    ax.add_patch(Polygon([(x-250, 0), (x-250, 105), (x-110, 115), (x-100, 105), (x-100, 0)], fc="#b5b5b5", ec=INK))
    ax.add_patch(Rectangle((x-250, 105), 10, 140, fc="#b5b5b5", ec=INK))  # low back with tags
    ax.add_patch(Rectangle((x-248, 170), 8, 55, fc=TAGS))
    ax.add_patch(Rectangle((x-185, 113), 70, 2, fc=LIVE))
    if duck: duck_side(ax, x-40, 0, "sit")

def c3_side(ax):
    setup(ax, "Side view: a stool behind the duck, contacts under the butt", (-420, 300), (-70, 470)); floor(ax, -420, 300)
    nest_side(ax)
    dim(ax, (-250, -40), (-100, -40), "150"); dim(ax, (-290, 0), (-290, 115), "seat 115", off=(-28, 0))
    dim(ax, (-410, 0), (-410, 245), "back 245", off=(25, 0))
    ax.text(-410, 440, "Hip pitch flexes to drop the butt back 60 to 70 mm: no such pose is trained (BLOCKER)", fontsize=6.3, color=LIVE)

def c3_top(ax):
    setup(ax, "Top view", (-290, 160), (-190, 190))
    ax.add_patch(Rectangle((-250, -110), 150, 220, fc="#b5b5b5", ec=INK))
    for i, (nm, c) in enumerate([("CHG+", LIVE), ("SENSE", "#e67e22"), ("GND", GNDC), ("SYS", LIVE)]):
        ax.add_patch(Rectangle((-205+i*18, -60), 12, 120, fc=c)); ax.text(-199+i*18, 66, nm, rotation=90, fontsize=5, ha="center", va="bottom")
    duck_top(ax, -40, 0, alpha=0.35)
    dim(ax, (-250, -150), (-100, -150), "150"); dim(ax, (-270, -110), (-270, 110), "220", off=(-14, 0))
    dim(ax, (-120, -60), (-120, 60), "strips 120\n(+/-60 lat)", off=(28, 0))

def strip_c3(phase):
    def f(ax):
        setup(ax, "", (-420, 380), (-30, 460)); floor(ax, -420, 380); nest_side(ax, duck=False)
        if phase == 0:
            duck_side(ax, 120, 0, "stand", facing=-1, alpha=0.4); duck_side(ax, 60, 0, "stand", facing=1)
            ax.text(-100, 440, "walk in facing the nest, then TURN 180\n(about 11 s of left pulses, calc)", fontsize=6, color=LIVE)
            arrow(ax, (250, 300), (160, 300))
        if phase == 1: duck_side(ax, -40, 0, "sit"); ax.text(0, 440, "back about 60 mm (blind) and sit", fontsize=6, color=LIVE)
        if phase == 2: duck_side(ax, 200, 0, "stand"); arrow(ax, (60, 300), (300, 300)); ax.text(0, 440, "stand and walk forward", fontsize=6)
    return f

# ---------------------------------------------------------------- C4 wireless
def c4_side(ax):
    setup(ax, "Side view: coil under a belly saddle (feet coils too small and too far apart)", (-360, 420), (-70, 470)); floor(ax, -360, 420)
    ax.add_patch(Polygon([(-300, 0), (-200, 15), (180, 15), (280, 0)], fc=PAD, ec=INK))
    ax.add_patch(Rectangle((-80, 15), 120, 90, fc="#b5b5b5", ec=INK))
    ax.add_patch(Rectangle((-65, 95), 90, 6, fc="#8e44ad")); ax.text(-20, 80, "Tx coil", ha="center", fontsize=6, color="#8e44ad")
    ax.add_patch(Rectangle((290, 0), 10, 230, fc="#bbb", ec=INK)); ax.add_patch(Rectangle((289, 155), 12, 60, fc=TAGS))
    duck_side(ax, 40, 15, "crouch")
    ax.text(-20, 125, "Rx coil in belly, gap <= 5", ha="center", fontsize=6, color="#8e44ad")
    dim(ax, (-300, -40), (280, -40), "580"); dim(ax, (-110, 0), (-110, 105), "saddle 105", off=(-35, 0))
    ax.text(-350, 440, "Needs 17.4 W typ, 24.6 W peak at the duck (calc): above Qi EPP 15 W.\nA 30 W-class pair or charging only (SYS from pack) would be needed", fontsize=6.3, color=LIVE)

def c4_top(ax):
    setup(ax, "Top view", (-330, 320), (-200, 200))
    ax.add_patch(Rectangle((-300, -150), 580, 300, fc=PAD, ec=INK)); ax.add_patch(Rectangle((-80, -60), 120, 120, fc="#b5b5b5", ec=INK))
    ax.add_patch(Circle((-20, 0), 25, fill=False, ec="#8e44ad", lw=2)); ax.add_patch(Circle((-20, 0), 10, fill=False, ec="#8e44ad"))
    duck_top(ax, 40, 0, alpha=0.35)
    dim(ax, (-45, -75), (5, -75), "50 coil"); dim(ax, (-300, -180), (280, -180), "580")
    ax.text(-290, 165, "Alignment: about +/-5 to 10 mm for a 50 mm coil pair (estimate)", fontsize=6, color=LIVE)

def strip_c4(phase):
    def f(ax):
        setup(ax, "", (-500, 480), (-30, 460)); floor(ax, -500, 480)
        ax.add_patch(Polygon([(-300, 0), (-200, 15), (180, 15), (280, 0)], fc=PAD, ec=INK)); ax.add_patch(Rectangle((-80, 15), 120, 90, fc="#b5b5b5", ec=INK))
        ax.add_patch(Rectangle((290, 0), 10, 230, fc="#bbb", ec=INK))
        if phase == 0: duck_side(ax, -400, 0, "stand"); arrow(ax, (-330, 300), (-120, 300))
        if phase == 1: duck_side(ax, 40, 15, "crouch"); ax.text(-250, 440, "crouch, coil found by FOD/ping", fontsize=6)
        if phase == 2: duck_side(ax, 360, 0, "stand"); arrow(ax, (120, 300), (330, 300)); ax.text(-300, 440, "stand and walk out forward (as C2)", fontsize=6)
    return f

# ---------------------------------------------------------------- C5 current wall (for comparison)
def wall_side(ax, duck=True):
    ax.add_patch(Rectangle((-110, 0), 95, 112, fc="#b5b5b5", ec=INK)); ax.add_patch(Rectangle((-15, 0), 45, 90, fc="#b5b5b5", ec=INK))
    ax.add_patch(Rectangle((75, 10), 8, 450, fc="#bbb", ec=INK)); ax.add_patch(Rectangle((0, 140), 12, 90, fc="#999", ec=INK))
    ax.add_patch(Rectangle((73, 350), 12, 40, fc=TAGS))
    if duck: duck_side(ax, -95, 0, "crouch")

def c5_side(ax):
    setup(ax, "Side view (today, DOCK_TWIN 2): the duck faces the wall", (-400, 300), (-70, 490)); floor(ax, -400, 300)
    wall_side(ax)
    dim(ax, (130, 0), (130, 460), "mast 460", off=(30, 0)); dim(ax, (-150, 0), (-150, 112), "seat 112", off=(-28, 0))
    dim(ax, (0, 250), (40, 250), "40 travel", off=(0, 12))

def c5_top(ax):
    setup(ax, "Top view", (-260, 160), (-180, 180))
    ax.add_patch(Rectangle((-110, -20), 140, 40, fc="#b5b5b5", ec=INK)); ax.add_patch(Rectangle((75, -140), 8, 280, fc="#bbb", ec=INK))
    ax.add_patch(Rectangle((0, -55), 12, 110, fc="#999", ec=INK)); duck_top(ax, -95, 0, alpha=0.35)
    dim(ax, (110, -140), (110, 140), "280", off=(18, 0)); dim(ax, (-20, -55), (-20, 55), "paddle 110", off=(-30, 0))

def strip_c5(phase):
    def f(ax):
        setup(ax, "", (-750, 250), (-30, 480)); floor(ax, -750, 250); wall_side(ax, duck=False)
        if phase == 0: duck_side(ax, -400, 0, "stand"); arrow(ax, (-330, 300), (-150, 300))
        if phase == 1: duck_side(ax, -95, 0, "crouch"); ax.text(-600, 440, "chest onto paddle, belly on seat", fontsize=6)
        if phase == 2: duck_side(ax, -600, 0, "stand", alpha=0.9); arrow(ax, (-150, 120), (-520, 120), c=LIVE); ax.text(-700, 440, "back off about 0.55 m (weak walk)", fontsize=6, color=LIVE)
    return f

N = "Concept sketch, not CAD. Dimensions in mm; duck from print/foot_bottom_tpu.stl (sole 101.9 x 40.7) and DOCK_TWIN.md; dock sizes are calc proposals."
figure("C1_feet_flat_pad.png", "C1  Feet contacts on a flat pass-through pad", c1_side, c1_top, [strip_c1(i) for i in range(3)], N)
figure("C2_feet_cradle.png", "C2  Feet contacts + low ramp and belly saddle (cradle)", c2_side, c2_top, [strip_c2(i) for i in range(3)], N)
figure("C3_butt_nest.png", "C3  Butt contacts on a low seat (nest)", c3_side, c3_top, [strip_c3(i) for i in range(3)], N)
figure("C4_wireless.png", "C4  Wireless coil under a belly saddle", c4_side, c4_top, [strip_c4(i) for i in range(3)], N)
figure("C5_current_wall.png", "C5  Current wall and sprung paddle (for comparison)", c5_side, c5_top, [strip_c5(i) for i in range(3)], N)
