#!/usr/bin/env python3
"""Tables of ELECTRICAL_TWIN.md from the bus_events.py result files (sim pass only).

  python3 bus_tables.py --falls <falls.json> [<more falls json>] --getup <getup.json> --walk <walk.json> --out out/summary.json

Writes a small summary (out/summary.json, in git) and prints the tables: worst pack current per event against the
Tenergy 32175 over-current band (22 +/- 5 A after 8 +/- 4 ms), how many events would trip a board at each threshold,
the net servo bus power (regeneration), and the data ground offset per servo against the adapter receiver's 0.8 V VIL
(TI SN74LVC1G125 data sheet, VCC 3.0 to 3.6 V).
"""
import argparse, json, os

VIL_ADAPTER = 0.8      # V, SN74LVC1G125 (adapter U4, the receive buffer) at VCC 3.0 to 3.6 V


def load(paths, kind):
    out = []
    for p in paths:
        for r in json.load(open(p)):
            r["kind"] = kind; r["src"] = os.path.basename(p); out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--falls", nargs="+", required=True); ap.add_argument("--getup", nargs="+", required=True)
    ap.add_argument("--walk", nargs="+", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    R = load(a.falls, "fall") + load(a.getup, "getup") + load(a.walk, "walk")
    base = [r for r in R if r["hop_mohm"] is None]
    ev = {}
    for r in base:
        if r["kind"] == "walk":
            continue
        k = (r["kind"], r["trace"])
        e = ev.setdefault(k, dict(peak=0.0, h4=0.0, h8=0.0, h12=0.0))
        e["peak"] = max(e["peak"], r["pack_peak_A"]); e["h4"] = max(e["h4"], r["pack_held_4ms_A"])
        e["h8"] = max(e["h8"], r["pack_held_8ms_A"]); e["h12"] = max(e["h12"], r["pack_held_12ms_A"])
    trips = {thr: {d: sum(e[k] >= thr for e in ev.values()) for d, k in (("4ms", "h4"), ("8ms", "h8"), ("12ms", "h12"))}
             for thr in (17, 18, 19, 20, 21, 22)}
    by_kind = {}
    for (kind, tr), e in ev.items():
        b = by_kind.setdefault(kind, dict(n=0, peak=0.0, h4=0.0))
        b["n"] += 1; b["peak"] = max(b["peak"], e["peak"]); b["h4"] = max(b["h4"], e["h4"])
    walk = [r for r in base if r["kind"] == "walk"]
    S = dict(events=len(ev), by_kind=by_kind, trips_per_threshold=trips,
             largest_held_A={k: max(e[k] for e in ev.values()) for k in ("h4", "h8", "h12")},
             worst_events=sorted([dict(kind=k[0], trace=k[1], **{x: round(v, 2) for x, v in e.items()}) for k, e in ev.items()],
                                 key=lambda x: -x["h4"])[:8],
             walk_pack_peak_A=max(r["pack_peak_A"] for r in walk),
             regen=dict(walk_min_W=min(r["regen"]["net_bus_power_min_W"] for r in walk),
                        falls_min_W=min(r["regen"]["net_bus_power_min_W"] for r in base if r["kind"] == "fall"),
                        getup_min_W=min(r["regen"]["net_bus_power_min_W"] for r in base if r["kind"] == "getup"),
                        getup_largest_J=max(r["regen"]["largest_stretch_J"] for r in base if r["kind"] == "getup")),
             bec_in_min_V=dict(full=min(r["bec_in_min_V"] for r in base if r["pack"] == "full"),
                               nominal=min(r["bec_in_min_V"] for r in base if r["pack"] == "nominal")),
             servo_min_V=dict(typical=min(r["servo_min_V"] for r in base if r["corner"] == "typical"),
                              high_side=min(r["servo_min_V"] for r in base if r["corner"] == "high-side"),
                              runs_under_4V_typical=sum(r["servo_min_V"] < 4.0 for r in base if r["corner"] == "typical"),
                              runs_under_4V_high_side=sum(r["servo_min_V"] < 4.0 for r in base if r["corner"] == "high-side"),
                              runs=len(base)))
    gnd = {}
    for r in R:
        key = "%s, %s" % (r["kind"], r["corner"] if r["hop_mohm"] is None else "typical, hop %g mOhm" % r["hop_mohm"])
        g = gnd.setdefault(key, dict(runs=0, over_vil=0, max_V=0.0, at=None, min_V=0.0, servo={}))
        g["runs"] += 1; g["over_vil"] += r["gnd_offset_worst"]["V"] >= VIL_ADAPTER
        if r["gnd_offset_worst"]["V"] > g["max_V"]:
            g["max_V"], g["at"] = r["gnd_offset_worst"]["V"], r["gnd_offset_worst"]["servo"]
        g["min_V"] = min(g["min_V"], r["gnd_offset_min_V"])
        for s, v in r["gnd_offset_max_V"].items():
            g["servo"][s] = max(g["servo"].get(s, 0.0), v)
    S["ground_offset"] = gnd
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(S, open(a.out, "w"), indent=1)
    print("events %d; by kind %s" % (S["events"], by_kind))
    print("| Board trips at | delay 4 ms | 8 ms | 12 ms |\n|---|---|---|---|")
    for thr, t in trips.items():
        print("| %d A | %d | %d | %d |" % (thr, t["4ms"], t["8ms"], t["12ms"]))
    print("largest current held 4 / 8 / 12 ms:", S["largest_held_A"], "; walking pack peak", S["walk_pack_peak_A"])
    for e in S["worst_events"]:
        print("  ", e)
    print("regen", S["regen"]); print("BEC input min", S["bec_in_min_V"]); print("servo min", S["servo_min_V"])
    print("| Case | runs | largest offset (servo) | runs at or over 0.8 V | knees L / R | ankles L / R | head roll |\n|---|---|---|---|---|---|---|")
    for k, g in gnd.items():
        s = g["servo"]
        print("| %s | %d | %.2f V (%s) | %d | %.2f / %.2f | %.2f / %.2f | %.2f |" % (k, g["runs"], g["max_V"], g["at"], g["over_vil"],
              s["left_knee"], s["right_knee"], s["left_ankle"], s["right_ankle"], s["head_roll"]))


if __name__ == "__main__":
    main()
