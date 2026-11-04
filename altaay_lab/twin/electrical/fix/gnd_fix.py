#!/usr/bin/env python3
"""Far servo data ground with and without a ground return lead to the head (sim pass only; fix for the head roll margin).

The ground network is track 1's (../bus_events.py ground_matrix: sim/power_fix.py minus_edges(), as built, plus the 5 V
return), here with one more edge: a ground-only lead "GR" from the BEC splice (node spl) to the free bus connector of the
last neck-chain servo, head_roll, made like the D23 leg feeds (sim/power_fix.py minus_edges "inj" edges: wire + one
contact + the servo board). Default 22 AWG, 650 mm: P13's 550 mm route from the trunk into the head (netlist P13n) plus
100 mm to the head roll servo (design length, cut to fit; --len to vary). Servo return currents per 1 ms are track 1's:
bus_events.replay() solves the as-built network every 1 ms (full and nominal pack), so "before" is track 1's number.
  python3 gnd_fix.py --out <json> <trace.npz> [...]
"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import numpy as np
import bus_events as BE         # noqa: E402  (track 1, read only)
PN = BE.PN


def ground_matrix(corner, extra=None, gr=None):
    """BE.ground_matrix() with the optional GR lead (awg, mm): Z (servo ground nodes x servo return currents), ohm"""
    PF = PN.PF
    opt = PF.OPTIONS["ab"]
    ex = dict(PN.CORNERS[corner]); ex.update(extra or {})
    p = PF.params("high-side", opt, ex)
    edges = PF.minus_edges(opt, p)
    N = PF.net_len()
    edges = edges + [("ret5", "reg", "src", PF.wire(*N["P13n"]) + PF.wire(*N["P10n"]))]
    _, loads, _ = PF.servo_net(opt, p)
    if gr:
        edges.append(("gr_head", "spl", loads["head_roll"], PF.wire(*gr) + p["R_contact"] + p["R_servo_pcb"]))
    nodes = sorted({x for e in edges for x in e[1:3]} - {"src"}); ix = {n: i for i, n in enumerate(nodes)}
    G = np.zeros((len(nodes), len(nodes)))
    for _, a, b, r in edges:
        g = 1.0 / r
        for x, y in ((a, b), (b, a)):
            if x != "src":
                G[ix[x], ix[x]] += g
                if y != "src":
                    G[ix[x], ix[y]] -= g
    Zi = np.linalg.inv(G)
    cols = [ix[loads[n]] for n in PN.NAMES]
    return Zi[np.ix_(cols, cols)] - Zi[ix["adg"], cols][None, :]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("traces", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--awg", type=int, default=22)
    ap.add_argument("--len", type=float, nargs="+", default=[650.0])
    a = ap.parse_args()
    perm = np.array([BE.GYM_ORDER.index(n) for n in PN.NAMES])
    cases = [("typical", None, None), ("high-side", None, None), ("typical", 40, PN.hop_extra(40, "typical"))]
    Z = {}
    for c, h, ex in cases:
        Z[(c, h, None)] = ground_matrix(c, ex)
        for L in a.len:
            Z[(c, h, L)] = ground_matrix(c, ex, (a.awg, L))
    res = {}
    for path in a.traces:
        d = np.load(path)
        F = np.asarray(d["F"], float)[:, perm]; W = np.asarray(d["W"], float)[:, perm]
        k0 = 0
        if "t_fall" in d.files and float(d["t_fall"]) > 0:
            k0 = int(np.searchsorted(np.asarray(d["t"], float), float(d["t_fall"]) - 0.5))
        Ic = {}
        for c, h, ex in cases:
            for pk in ("full", "nominal"):
                Ic[(c, h, pk)] = BE.replay(F[k0:], W[k0:], float(d["dt"]), c, BE.PACK_Q[pk], ex)["isup"]
        for (c, h, L), Zg in Z.items():
          for pk in ("full", "nominal"):
            off = Ic[(c, h, pk)] @ Zg.T
            key = f"{c}|hop {h}|GR {L}"
            r = res.setdefault(key, dict(max_V={n: -9.0 for n in PN.NAMES}, min_V=9.0, worst=None))
            mx = off.max(0)
            for n, v in zip(PN.NAMES, mx):
                if v > r["max_V"][n]:
                    r["max_V"][n] = round(float(v), 3)
                    if n == "head_roll":
                        r["worst"] = os.path.basename(path) + " " + pk
            r["min_V"] = round(min(r["min_V"], float(off.min())), 3)
    for k, r in res.items():
        print(f"{k:32s} head_roll max {r['max_V']['head_roll']:.3f} V, worst servo max {max(r['max_V'].values()):.3f} V, "
              f"min {r['min_V']:.3f} V  ({r['worst']})")
    json.dump(dict(awg=a.awg, len_mm=a.len, n_traces=len(a.traces), cases=res), open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
