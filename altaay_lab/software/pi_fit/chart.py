"""Draw the fit chart from a result JSON. No machine paths on the picture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def draw(report, dest):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1, figsize=(8.2, 6.4), constrained_layout=True)

    bars = report["bars"]
    names = [item["name"] for item in bars]
    values = [item["mib"] for item in bars]
    colors = [item.get("color") or ("#1a73e8" if item["label"] == "measured in emulation" else "#9aa0a6") for item in bars]
    ax = axes[0]
    ax.bar(range(len(names)), values, color=colors)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=20, ha="right")
    lines = report.get("ram_lines") or [
        {"mib": 417.0, "label": "417 MiB cited Linux-visible", "color": "#c5221f"},
        {"mib": 512.0, "label": "512 MiB cited chip", "color": "#188038"},
    ]
    for item in lines:
        ax.axhline(item["mib"], color=item.get("color", "#188038"), linestyle="--", linewidth=1, label=item["label"])
    ax.set_ylabel("MiB")
    ax.set_title(report.get("ram_title") or "RAM: gray is cited, blue is measured in emulation")
    ax.legend(fontsize=8, loc="upper right")

    work = report.get("during_work_ms") or []
    ax2 = axes[1]
    if work:
        ax2.plot(range(len(work)), work, color="#1a73e8", linewidth=0.8, label="walk work, measured in emulation")
    ax2.axhline(20.0, color="#c5221f", linestyle="--", linewidth=1, label="20 ms deadline")
    bus = report.get("bus_line_ms")
    if bus is not None:
        ax2.axhline(bus, color="#e37400", linestyle=":", linewidth=1, label="20 ms minus 5.18 ms bus (calc only)")
    ax2.set_ylabel("ms")
    ax2.set_xlabel("walk cycle during the voice request and the camera frame")
    ax2.set_title(report.get("work_title") or "Walk CPU time on one core throttled to the cited CoreMark")
    ax2.legend(fontsize=8, loc="upper right")
    fig.savefig(dest, dpi=120)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Draw the fit chart")
    parser.add_argument("--report", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    draw(report, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
