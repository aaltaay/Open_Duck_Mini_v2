#!/usr/bin/env python3
"""CAD check of two nest-lid fixes. Does not write the nest STL.

Reuses the box profile already in twin/dock/nest/cad/nest_parts.py.
Rejected: room-side axes at BX0+6 (on the chamfer, no lid left).
Kept: room-side axes stay at BX0+14, wall-side axes move to the mirror
about the tray centre, so the four axes are symmetric and both heads
sit on the flat top.

Engagement reuses BOM 16 (M3 x 5.7 insert) and BOM 17a (M3x8). A longer
insert does not help an M3x6, because that screw only reaches 4.0 mm.
"""
import json
import os
import sys

import numpy as np
from shapely.geometry import Polygon

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, "..", ".."))
NEST = os.path.join(LAB, "twin", "dock", "nest", "cad")
sys.path.insert(0, NEST)
import nestcad_lib as N  # noqa: E402
import nest_parts as P  # noqa: E402

# Head sizes already cited in fasteners/FASTENERS.md section 8.
BUTTON_DK, BUTTON_K = 5.70, 1.65   # ISO 7380 M3
SHCS_DK, SHCS_K = 5.68, 3.00       # DIN 912 M3 knurl dk, k max
INSERT_THREAD = 5.7                # BOM 16, CNC Kitchen M3 x 5.7
TIP_GAP = 0.3                      # fasteners.json meta margin_mm
RULE = 4.5                         # 1.5 x d, the rule FASTENERS.md already uses
LID_T = float(N.BOX["lid"])
BORE_NOW = float(N.INSERT_DEPTH)


def tray_centre():
    return (P.BX0 + P.BX1) / 2.0


def profile():
    """Lid cross-section in (x, z), the part of box_profile above the split."""
    z_split = P.BZ1 - LID_T
    full = P.box_profile()
    # Clip to the lid band by intersecting a tall box in x and the z range.
    band = Polygon([(P.BX0 - 5, z_split), (P.BX1 + 5, z_split), (P.BX1 + 5, P.BZ1 + 1), (P.BX0 - 5, P.BZ1 + 1)])
    lid = full.intersection(band)
    return lid, z_split


def head_on_flat(x, dk):
    """The head disk must lie on the flat top, inboard of the chamfer."""
    c = N.BOX["chamfer"] - 1.0
    flat0 = P.BX0 + c
    r = dk / 2.0
    return (x - r) >= flat0 - 1e-6 and (x + r) <= P.BX1 + 1e-6, round(x - r - flat0, 2), round(P.BX1 - (x + r), 2)


def lid_thickness_at(lid, x):
    """Length of the lid polygon cut by a vertical line at this x."""
    from shapely.geometry import LineString
    cut = lid.intersection(LineString([(x, P.BZ1 - LID_T - 1.0), (x, P.BZ1 + 1.0)]))
    return round(float(cut.length), 2)


def engage(length, bore):
    reach = length - LID_T
    bottoms = reach > bore - TIP_GAP + 1e-9
    # Thread used is the lesser of how far the screw enters and the insert thread.
    used = min(reach, INSERT_THREAD)
    return {"length_mm": length, "bore_mm": bore, "reach_mm": round(reach, 2),
            "engaged_mm": round(used, 2), "bottoms": bool(bottoms),
            "meets_4_5": (not bottoms) and used + 1e-9 >= RULE, "label": "calc"}


def main():
    lid, z_split = profile()
    cx = tray_centre()
    room = P.BX0 + 14.0
    wall = 2 * cx - room
    # The jack stand-in already in nest_parts.STANDINS occupies y 68 to 88 on the +y end.
    # A post of radius 4 at y 84 enters that box. y = 68 - 4 - 2 keeps a 2 mm gap.
    jack = P.STANDINS["jack"]
    jack_lo_y = jack["c"][1] - jack["size"][1] / 2.0
    post_y = round(jack_lo_y - 4.0 - 2.0, 2)
    posts = [(room, post_y), (room, -post_y), (wall, post_y), (wall, -post_y)]
    rejected = P.BX0 + 6.0
    rows = []
    for name, x, dk in (
        ("as drawn, room side", P.LID_POSTS[0][0], BUTTON_DK),
        ("as drawn, wall side", P.LID_POSTS[2][0], BUTTON_DK),
        ("rejected BX0+6", rejected, BUTTON_DK),
        ("proposed room side, button head", room, BUTTON_DK),
        ("proposed wall side, button head", wall, BUTTON_DK),
        ("proposed room side, socket head", room, SHCS_DK),
        ("proposed wall side, socket head", wall, SHCS_DK),
    ):
        flat_ok, room_margin, wall_margin = head_on_flat(x, dk)
        rows.append({"name": name, "x_mm": round(x, 2), "lid_thickness_mm": lid_thickness_at(lid, x),
                     "head_on_flat": flat_ok, "flat_margin_room_mm": room_margin,
                     "flat_margin_wall_mm": wall_margin, "label": "cad"})
    # Mirror of the proposed four about the tray centre.
    worst = 0.0
    for x, y in posts:
        mx, my = 2 * cx - x, -y
        worst = max(worst, min(np.hypot(mx - a, my - b) for a, b in posts))
    # Terminals stay where nest_parts puts them.
    term = [(P.POST_X, P.TAB_Y), (P.POST_X, -P.TAB_Y)]
    term_gap = min(np.hypot(x - a, y - b) for x, y in posts for a, b in term)
    out = {
        "label": "cad for the profile, calc for engagement",
        "source": "twin/dock/nest/cad/nest_parts.py box_profile, not a new shape",
        "tray_centre_x_mm": round(cx, 2),
        "chamfer_flat_starts_x_mm": round(P.BX0 + (N.BOX["chamfer"] - 1.0), 2),
        "lid_split_z_mm": round(z_split, 2),
        "positions": rows,
        "proposed_posts_xy": [[round(a, 2), round(b, 2)] for a, b in posts],
        "mirror_error_about_tray_centre_mm": round(float(worst), 2),
        "nearest_terminal_mm": round(float(term_gap), 2),
        "post_y_mm": post_y,
        "why_y": "jack stand-in y starts at %.2f; post radius 4 mm; 2 mm gap; same number both sides so the pattern still mirrors" % jack_lo_y,
        "engagement": {
            "M3x6_bore_5.8": engage(6.0, BORE_NOW),
            "M3x6_deeper_bore_6.3": engage(6.0, 6.3),
            "M3x6_longer_insert_does_not_change_reach": engage(6.0, 8.0),
            "M3x8_bore_5.8_bottoms": engage(8.0, BORE_NOW),
            "M3x8_deeper_bore_6.3": engage(8.0, 6.3),
        },
        "sleeve_note": {
            "published_gap_over_button_head_mm": 2.85,
            "source": "NEST_CAD.md, cited, not re-measured on the sleeve mesh",
            "button_k_mm": BUTTON_K,
            "socket_k_mm": SHCS_K,
            "socket_gap_if_sleeve_stays_mm": round(2.85 - (SHCS_K - BUTTON_K), 2),
            "label": "calc",
        },
    }
    json.dump(out, open(os.path.join(HERE, "lid_check.json"), "w"), indent=1)
    write_fig(out, jack)
    print(json.dumps({k: out[k] for k in ("proposed_posts_xy", "mirror_error_about_tray_centre_mm", "nearest_terminal_mm", "post_y_mm", "engagement")}, indent=1))


def write_fig(out, jack):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.4, 5.6))
    # Lid top outline: flat top starts at the chamfer.
    x0, x1 = P.BX0, P.BX1
    y0, y1 = -N.BOX["half_len"], N.BOX["half_len"]
    ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=1.0, color="#333"))
    flat = out["chamfer_flat_starts_x_mm"]
    ax.plot([flat, flat], [y0, y1], color="#888", lw=1, label="chamfer, flat top starts")
    lo = np.array(jack["c"]) - np.array(jack["size"]) / 2
    ax.add_patch(plt.Rectangle((lo[0], lo[1]), jack["size"][0], jack["size"][1],
                               fill=True, color="#f4c7c3", lw=0, label="jack stand-in"))
    drawn = np.array(P.LID_POSTS)
    prop = np.array(out["proposed_posts_xy"])
    ax.scatter(drawn[:, 0], drawn[:, 1], c="#1f4e79", s=40, zorder=3, label="as drawn")
    ax.scatter([P.BX0 + 6], [84], c="#b00020", marker="x", s=60, zorder=3, label="BX0+6, no lid")
    ax.scatter(prop[:, 0], prop[:, 1], facecolors="none", edgecolors="#2e7d32", s=80, zorder=4, label="proposed")
    ax.scatter([out["tray_centre_x_mm"]], [0], marker="+", c="#333", s=80, label="tray centre")
    ax.set_aspect("equal")
    ax.set_xlabel("x mm, toward the wall")
    ax.set_ylabel("y mm, along the wall")
    ax.set_title("Nest lid screws. CAD check of the existing profile.")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2, fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "lid_proposal.png"), dpi=140, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()
