"""Read the supervisor JSON-lines log for the home page.

Missing fields stay missing. This module does not invent a voltage.
"""

from __future__ import annotations

import json
import os

from . import store

# Set point. The page shows the tail of a long log. Not a measurement.
TAIL_BYTES = 256 * 1024
# Set point. The download is the tail if the file is larger than this.
DOWNLOAD_BYTES = 8 * 1024 * 1024
DOCK_KINDS = ("dock_attempt", "dock_result", "dock_abort")


def read_tail(file_path, limit):
    if not file_path or not os.path.isfile(file_path):
        return "", False
    size = os.path.getsize(file_path)
    with open(file_path, "rb") as handle:
        if size > limit:
            handle.seek(size - limit)
            data = handle.read(limit)
            return data.decode("utf-8", errors="replace"), True
        return handle.read().decode("utf-8", errors="replace"), False


def summarize(text):
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    pack = None
    knee = None
    falls = None
    fall_events = 0
    mode = None
    docks = []
    for row in rows:
        if "pack_v" in row and row["pack_v"] is not None:
            pack = row["pack_v"]
        if "knee_c" in row and row["knee_c"] is not None:
            knee = row["knee_c"]
        if "falls" in row and row["falls"] is not None:
            falls = row["falls"]
        if row.get("kind") == "fall":
            fall_events += 1
        if row.get("mode"):
            mode = row["mode"]
        if row.get("kind") in DOCK_KINDS:
            docks.append({
                "t": row.get("t"),
                "kind": row.get("kind"),
                "ok": row.get("ok", ""),
                "pack_v": row.get("pack_v"),
            })
    if falls is None:
        falls = fall_events if rows else None
    return {
        "pack_v": pack,
        "knee_c": knee,
        "falls": falls,
        "mode": mode,
        "docks": docks[-5:],
        "rows": len(rows),
    }


def status_summary(state):
    text, trimmed = read_tail(store.log_path(state), TAIL_BYTES)
    body = summarize(text)
    body["trimmed"] = trimmed
    return body


def log_download(state):
    text, trimmed = read_tail(store.log_path(state), DOWNLOAD_BYTES)
    return text, trimmed
