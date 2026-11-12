#!/usr/bin/env python3
"""Figures for the life note. Numbers come from heat.json and the published FEA tables."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
H = json.load(open(os.path.join(HERE, "heat.json")))


def _walk(room):
    for w in H["walks"]:
        if w["room_C"] == room:
            return w
    raise SystemExit(room)


def fig_servos():
    names = ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
             "neck_pitch", "head_pitch", "head_yaw", "head_roll",
             "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]
    a, b = _walk(22.0), _walk(32.0)
    ya = [a["servos"][n]["reading_max_C"] for n in names]
    yb = [b["servos"][n]["reading_max_C"] for n in names]
    # extra rows the model resolves, same units
    extra = [("BEC case", a["bec_case_max_C"], b["bec_case_max_C"]),
             ("cells", a["cells_max_C"], b["cells_max_C"]),
             ("head air", a["head_air_max_C"], b["head_air_max_C"]),
             ("trunk wall", a["trunk_wall_max_C"], b["trunk_wall_max_C"])]
    labels = names + [e[0] for e in extra]
    ya += [e[1] for e in extra]
    yb += [e[2] for e in extra]
    fig, ax = plt.subplots(figsize=(8.2, 7.2))
    y = range(len(labels))
    ax.barh([i - 0.18 for i in y], ya, height=0.36, color="#1f4e79", label="22 C room")
    ax.barh([i + 0.18 for i in y], yb, height=0.36, color="#c47b2b", label="32 C room")
    ax.axvline(60, color="#833", lw=1, label="60 C servo operating line")
    ax.axvline(55, color="#3d6b4f", lw=1, ls="--", label="55 C guard stop")
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Peak in a 40 minute unguarded backlash walk, C")
    ax.set_xlim(0, 130)
    ax.set_title("Closed shell, central corner, sim pass only\nServo bars are the internal reading. Winding node omitted.")
    ax.legend(fontsize=8, loc="lower right")
    ax.invert_yaxis()
    fig.tight_layout()
    p = os.path.join(HERE, "heat_walk.png")
    fig.savefig(p, dpi=120)
    plt.close()
    return p


def fig_modes():
    """Peak of the parts a person can point at, four uses, two rooms."""
    def sit(mode, room):
        for s in H["sits"]:
            if s["mode"] == mode and s["room_C"] == room:
                return s
        raise SystemExit((mode, room))

    modes = [("walk, no guard", None), ("idle, torque off", "idle_torque_off"),
             ("idle, torque on", "idle_torque_on"), ("charging, 3.50 W", "charge_6v0")]
    series = [("right knee reading", "#1f4e79"), ("BEC case", "#c47b2b"), ("cells", "#3d6b4f")]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.4), sharey=True)
    for ax, room in zip(axes, (22.0, 32.0)):
        w = _walk(room)
        vals = {
            "walk, no guard": (w["servos"]["right_knee"]["reading_max_C"], w["bec_case_max_C"], w["cells_max_C"]),
        }
        for title, mode in modes[1:]:
            s = sit(mode, room)
            vals[title] = (s["servos"]["right_knee"]["reading_end_C"], s["bec_case_end_C"], s["cells_end_C"])
        xs = range(len(modes))
        width = 0.25
        for k, (lab, col) in enumerate(series):
            ax.bar([i + (k - 1) * width for i in xs], [vals[m[0]][k] for m in modes], width=width, color=col, label=lab)
        ax.axhline(60, color="#833", lw=1)
        ax.set_xticks(list(xs))
        ax.set_xticklabels([m[0] for m in modes], rotation=20, ha="right", fontsize=8)
        ax.set_title("%g C room" % room)
        ax.set_ylim(0, 130)
    axes[0].set_ylabel("Temperature, C")
    axes[1].legend(fontsize=8, loc="upper right")
    fig.suptitle("Sim pass only. Charging bar uses 3.50 W in the trunk (calc only watts).", fontsize=10)
    fig.tight_layout()
    p = os.path.join(HERE, "heat_modes.png")
    fig.savefig(p, dpi=120)
    plt.close()
    return p


def fig_sf():
    # Current-print voxel FEA, TOPOLOGY.md. Walk margin 2. Soft-fall margin 1.2.
    rows = [
        ("shin drive eye", 0.79, 0.46),
        ("roll to pitch", 1.43, 0.54),
        ("thigh sheets", 1.78, 0.70),
        ("neck sheets", 5.20, 0.38),
        ("head roll mount", 52.49, 1.03),
        ("foot top", 3.86, 2.76),
        ("hip roll stage", 16.74, 2.33),
    ]
    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    y = range(len(rows))
    ax.barh([i - 0.18 for i in y], [r[1] for r in rows], height=0.36, color="#1f4e79", label="walk SF")
    ax.barh([i + 0.18 for i in y], [r[2] for r in rows], height=0.36, color="#8c4a3a", label="soft-fall worst SF")
    ax.axvline(2.0, color="#1f4e79", lw=1, label="walk margin 2")
    ax.axvline(1.2, color="#8c4a3a", lw=1, ls="--", label="fall margin 1.2")
    ax.set_yticks(list(y))
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlabel("Safety factor, room-temperature PLA, FEA pass only")
    ax.set_xlim(0, 8)
    ax.set_title("Current print STLs. Head walk bar is 52 and hip walk bar is 17, both cut at 8.")
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.22)
    p = os.path.join(HERE, "stress_sf.png")
    fig.savefig(p, dpi=120)
    plt.close()
    return p


if __name__ == "__main__":
    for p in (fig_servos(), fig_modes(), fig_sf()):
        print(p, os.path.getsize(p))
