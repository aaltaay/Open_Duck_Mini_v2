#!/usr/bin/env python3
"""Bus events of the V1 duck: falls and get-ups through the as-built power network (sim pass only).

Input: npz traces with F (actuator torque, Nm) and W (joint speed, rad/s), shape (n, 14), and dt (s), in the order
GYM_ORDER (the Playground MJCF actuator order). They come from the shared lab gym (overlay gym/overlays/duck): its
get-up twin's 1 ms logs (getup/evaluate.py fine_run) and v1_elec/fall_traces.py (falls of the collision duck). Optional
keys: t (s) and t_fall (s): the window then starts 0.5 s before the fall.

Each trace is replayed open loop through the as-built network of twin/electromech/power_net.py (D15 star plus the D23
feeds, every length from wiring/netlist.yaml, the P30B pack of p30b.py), with the servo law of sim/power_path_sim.py and
the twin's replay(): commanded volts u = F R / kt, capped at the servo's own bus volts, supply current
max(u (u - kt w) / R, 0) / V + 0.05 A. Reported per pack state and resistance corner:
  1. pack current against the Tenergy 32175 over-current band: 22 +/- 5 A after 8 +/- 4 ms, release "Cut load"
     (Tenergy product page, read 2026-11-04). 'held N ms' = the largest current the pack carried for N ms on end.
  2. signed servo bus power, sum over the 14 servos of u (u - kt w) / R: negative = the servos push energy back
     into the bus (regeneration), with the energy of the longest net negative stretch.
  3. servo data ground offset: V(servo ground) - V(adapter ground) on the resistive ground network of
     sim/power_fix.py minus_edges() (the SP grounds, the kit hop grounds, SP4/SP5 grounds, the D15 data-lead grounds,
     the adapter copper, the USB ground to the Pi and P12), each servo's return current injected at its ground node.

  python3 bus_events.py --out <json> <trace.npz> [...]         (hop bands: --hops 28 40)
"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
EM = os.path.join(HERE, "..", "electromech")
sys.path.insert(0, EM)
os.environ.setdefault("TWIN_EM_SCRATCH", os.environ.get("ELEC_SCRATCH", "/tmp/duck_v1_elec"))
import numpy as np
import power_net as PN          # noqa: E402  (as-built network, read only)
import p30b                     # noqa: E402
import servo_sts3215 as SV      # noqa: E402

GYM_ORDER = ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle", "neck_pitch", "head_pitch",
             "head_yaw", "head_roll", "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]
BMS = dict(lo=(17.0, 0.004), nom=(22.0, 0.008), hi=(27.0, 0.012))     # (A, s): 22 +/- 5 A after 8 +/- 4 ms
PACK_Q = {"full": 0.0, "nominal": 1481.0}                             # mAh used (twin/electromech pack states)


def held(x, n):
    """largest value x stays at or above for n samples on end"""
    if len(x) < n:
        return float(x.min())
    from numpy.lib.stride_tricks import sliding_window_view as sw
    return float(sw(x, n).min(1).max())


def longest_over(x, thr, dt):
    m = np.concatenate([[0], (x >= thr).astype(np.int8), [0]]); dm = np.diff(m)
    s, e = np.where(dm == 1)[0], np.where(dm == -1)[0]
    return float((e - s).max() * dt) if len(s) else 0.0


def ground_matrix(corner, extra=None):
    """Z (servo ground nodes x servo return currents): V(s_k) - V(adg) per A returned by each servo (ohm)"""
    PF = PN.PF
    opt = PF.OPTIONS["ab"]
    ex = dict(PN.CORNERS[corner]); ex.update(extra or {})
    p = PF.params("high-side", opt, ex)
    edges = PF.minus_edges(opt, p)
    N = PF.net_len()
    edges = edges + [("ret5", "reg", "src", PF.wire(*N["P13n"]) + PF.wire(*N["P10n"]))]   # as current_split()
    _, loads, _ = PF.servo_net(opt, p)
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
    Zs = Zi[np.ix_(cols, cols)]                  # node volts at servo grounds per A injected at servo grounds
    Za = Zi[ix["adg"], cols]                     # adapter ground node
    return Zs - Za[None, :]


def replay(F, W, dt, corner, qm, extra=None):
    Rm = SV.R_M
    u_cmd = np.clip(F * Rm / SV.KT, -SV.V_TRAIN, SV.V_TRAIN)
    net = PN.Net(corner, extra, cell_model=p30b.P30B())
    iq = net.iq
    n = len(F)
    out = dict(i_pack=np.zeros(n), v_bin=np.zeros(n), v_out=np.zeros(n), v_pack=np.zeros(n), vs=np.zeros((n, 14)),
               isup=np.zeros((n, 14)), psig=np.zeros((n, 14)))
    for k in range(n):
        uc, ww = u_cmd[k], W[k]

        def law(v, uc=uc, ww=ww):
            vl = np.maximum(v, 0.5); ue = np.clip(uc, -vl, vl)
            return np.maximum(ue * (ue - SV.KT * ww) / Rm, 0.0) / vl + iq
        y = net.solve(law, qm=qm)
        vs = net.servo_volts(y)
        vl = np.maximum(vs, 0.5); ue = np.clip(uc, -vl, vl)
        out["psig"][k] = ue * (ue - SV.KT * ww) / Rm
        out["isup"][k] = law(vs); out["vs"][k] = vs
        for kk in ("i_pack", "v_bin", "v_out", "v_pack"):
            out[kk][k] = y[net.o[kk]]
    return out


def summarize(r, dt, Zg):
    ip = r["i_pack"]
    s = dict(pack_peak_A=round(float(ip.max()), 2))
    for ms in (4, 8, 12):
        s[f"pack_held_{ms}ms_A"] = round(held(ip, int(round(ms / 1000 / dt))), 2)
    s["bms"] = {k: dict(threshold_A=a, delay_ms=t * 1000, longest_over_ms=round(longest_over(ip, a, dt) * 1000, 1),
                        trips=bool(longest_over(ip, a, dt) >= t - 1e-9)) for k, (a, t) in BMS.items()}
    s["bec_out_min_V"] = round(float(r["v_out"].min()), 3); s["bec_in_min_V"] = round(float(r["v_bin"].min()), 3)
    s["servo_min_V"] = round(float(r["vs"].min()), 3)
    pn = r["psig"].sum(1)
    neg = pn < 0; E = 0.0; Emax = 0.0; L = 0; Lmax = 0
    for k in range(len(pn)):
        if neg[k]:
            E += -pn[k] * dt; L += 1; Emax = max(Emax, E); Lmax = max(Lmax, L)
        else:
            E = 0.0; L = 0
    s["regen"] = dict(net_bus_power_min_W=round(float(pn.min()), 2), braking_power_min_W=round(float(np.minimum(r["psig"], 0).sum(1).min()), 2),
                      net_negative_share=round(float(neg.mean()), 4), largest_stretch_J=round(Emax, 4), longest_stretch_ms=round(Lmax * dt * 1000, 1))
    off = r["isup"] @ Zg.T                                            # (n, 14) volts
    s["gnd_offset_max_V"] = dict(zip(PN.NAMES, np.round(off.max(0), 3).tolist()))
    s["gnd_offset_min_V"] = round(float(off.min()), 3)
    k = int(np.argmax(off.max(1)))
    s["gnd_offset_worst"] = dict(servo=PN.NAMES[int(np.argmax(off[k]))], V=round(float(off[k].max()), 3), t_index=k)
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("traces", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--packs", nargs="+", default=list(PACK_Q))
    ap.add_argument("--corners", nargs="+", default=["typical", "high-side"])
    ap.add_argument("--hops", nargs="*", type=float, default=[], help="hop resistance per conductor (mOhm), typical corner")
    ap.add_argument("--window", nargs=2, type=float, default=None, help="t0 t1 (s): replay this window instead of the fall")
    a = ap.parse_args()
    perm = np.array([GYM_ORDER.index(n) for n in PN.NAMES])
    res = []
    cases = [(c, None, None) for c in a.corners] + [("typical", h, PN.hop_extra(h, "typical")) for h in a.hops]
    for path in a.traces:
        d = np.load(path)
        F = np.asarray(d["F"], float)[:, perm]; W = np.asarray(d["W"], float)[:, perm]; dt = float(d["dt"])
        k0, k1 = 0, len(F)
        if a.window:
            k0, k1 = int(a.window[0] / dt), int(a.window[1] / dt)
        elif "t_fall" in d.files and float(d["t_fall"]) > 0:
            t = np.asarray(d["t"], float); k0 = int(np.searchsorted(t, float(d["t_fall"]) - 0.5))
        F, W = F[k0:k1], W[k0:k1]
        for corner, hop, extra in cases:
            Zg = ground_matrix(corner, extra)
            for pk in a.packs:
                r = replay(F, W, dt, corner, PACK_Q[pk], extra)
                s = dict(trace=os.path.basename(path), corner=corner, hop_mohm=hop, pack=pk, window_s=round(len(F) * dt, 3),
                         window=a.window)
                s.update(summarize(r, dt, Zg))
                res.append(s)
                b = s["bms"]
                print(f"{s['trace'][:34]:34s} {corner:9s} hop {hop} {pk:7s} pack peak {s['pack_peak_A']:5.2f} A, held 4/8/12 ms "
                      f"{s['pack_held_4ms_A']:5.2f}/{s['pack_held_8ms_A']:5.2f}/{s['pack_held_12ms_A']:5.2f} A; over 17 A "
                      f"{b['lo']['longest_over_ms']} ms; BEC out min {s['bec_out_min_V']} V; net bus P min "
                      f"{s['regen']['net_bus_power_min_W']} W ({s['regen']['largest_stretch_J']} J); gnd offset "
                      f"{s['gnd_offset_worst']['V']} V at {s['gnd_offset_worst']['servo']}", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
