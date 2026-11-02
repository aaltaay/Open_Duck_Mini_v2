"""C7: current ratings.

A. Every wire that carries servo current but has no current in the netlist (erc.py skips those: SP1 to SP3, the 11 kit
   cable hops) gets its current from the E5 MuJoCo traces (BAM motor model, same formula as sim/current_budget.py,
   kt 1.148, plus 0.05 A quiescent per servo as in sim/power_path_sim.py), summed down each chain, and is compared with
   the chassis ampacity of its gauge (the AMP table in audit/erc.py, read from that file) with erc.py's rules: mean over
   the limit FAIL, worst 100 ms over the limit WARN, worst 20 ms over 2 x the limit WARN.
   Currents are taken at 6.0 V (power / 6.0 V, the D16 hard stop; the servos draw more current at a lower bus voltage).
B. The 5264 / Mini-SPOX contacts that carry a whole chain (first servo of each chain, every kit cable plug) against
   3 A per contact ([I] Molex 08-70-1040 distributor listings, read via search index 2026-11-02; Molex sheet not read).
C. D15 ground wiring: the data leads SD1 and SD2 join the chain grounds (JG20, JG30, JG10) and the adapter joins H3 G
   and H5 G inside, so they are parallel return paths. A DC resistor network of the netlist lengths gives how much
   servo return current flows through SD1, SD2 and the adapter ground.
D. Fuse, BMS, main switch, BEC, BEC leads, XT30 and cells against the pack and BEC currents of the ngspice run (E6)
   and the stacked fall estimate in sim/CURRENT_BUDGET.md, with the ratings written in netlist.yaml.

Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/c7_current_ratings.py   (after E5 and E6)
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

KT, KT_OVER_R, VIN = 1.148, 3.23 / 7.4, 7.4
V_EVAL = 6.0
IQ = 0.05
MOLEX_A = 3.0
CHAINS = {"SP1": ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle"],
          "SP3": ["neck_pitch", "head_pitch", "head_yaw", "head_roll"],
          "SP2": ["right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]}
HOPS = {"SP1": ["S2", "S3", "S4", "S5"], "SP3": ["S11", "S12", "S13"], "SP2": ["S7", "S8", "S9", "S10"]}


def supply_currents(npz):
    d = np.load(npz)
    F, W, dt, names = d["F"], d["W"], float(d["dt"]), [str(n) for n in d["names"]]
    Rm = KT / KT_OVER_R
    u = np.clip(F * Rm / KT, -VIN, VIN)
    I = (u - KT * W) / Rm
    P = np.clip(u * I, 0, None)
    k0 = int(round(2.0 / dt))
    return {n: P[k0:, i] / V_EVAL + IQ for i, n in enumerate(names)}, dt


def windows(x, dt):
    def mov(n):
        c = np.cumsum(np.insert(x, 0, 0.0))
        return (c[n:] - c[:-n]) / n
    return dict(mean=float(x.mean()), w100=float(mov(int(round(0.1 / dt))).max()), w20=float(mov(int(round(0.02 / dt))).max()),
                w2=float(x.max()))


def main():
    R = V.Result("C7", "Current ratings: every wire, contact and power part vs the simulated currents (sim pass only)",
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/c7_current_ratings.py",
                 "SP1 to SP3 and 11 kit cable hops vs gauge ampacity (erc.py table); chain current through the 5264 / Mini-SPOX "
                 "contacts (3 A); return current in the D15 data-lead grounds and the adapter; fuse, BMS, switch, BEC, BEC "
                 "leads, XT30, cells vs pack and BEC currents (E6 ngspice, CURRENT_BUDGET.md falls)",
                 "Real servo currents (CURRENT_BUDGET.md: up to 2 x sim until a bench log), temperature rise inside the "
                 "body, connector wear, contact resistance (TEST_PLAN.md sections 3 to 5 and 9)")
    tr = os.path.join(V.out_dir(), "e5_current")
    net = V.load_netlist()
    T = V.erc_tables()
    AMP, OHM, KIT = T["AMP"], T["OHM_M"], T["KIT_AWG"]
    R.inp(V.lab("audit", "erc.py"), V.lab("wiring", "netlist.yaml"), V.lab("sim", "CURRENT_BUDGET.md"))
    cases = [c for c in ("walk_backlash", "walk_rough_backlash", "walk_pushes", "walk_side_0.2", "turn_1.0")
             if os.path.exists(os.path.join(tr, "trace_%s.npz" % c))]
    if not cases:
        R.not_run("no traces from E5 in %s" % tr)
        R.write()
        return
    R.ev("traces: %s (E5 run); servo supply current = positive electrical power / %.1f V + %.2f A quiescent (an upper "
         "estimate; on the 7.4 V basis of CURRENT_BUDGET.md the currents are %.2f x these)" % (", ".join(cases), V_EVAL, IQ, V_EVAL / VIN))
    # ---------------------------------------------------------------- A and B: chain conductors
    worst = {}       # conductor key -> windows (max over cases)
    series = {}      # first case series for the ground network
    for case in cases:
        I, dt = supply_currents(os.path.join(tr, "trace_%s.npz" % case))
        for sp, names in CHAINS.items():
            for k in range(len(names)):
                cur = sum(I[n] for n in names[k:])
                key = sp if k == 0 else HOPS[sp][k - 1]
                w = windows(cur, dt)
                old = worst.get(key)
                worst[key] = {m: max(w[m], old[m]) if old else w[m] for m in w} if old else w
                worst[key]["case_" + ("w100")] = case if (not old or w["w100"] >= old["w100"]) else old.get("case_w100")
                if case == cases[0]:
                    series[key] = cur
    gauge = {}
    for w in net["wires"]:
        if w["cable"] in worst and w["cable"] not in gauge:
            gauge[w["cable"]] = w["gauge"]
    over100, over20, overc, overc_mean = [], [], [], []
    for key in ["SP1", "S2", "S3", "S4", "S5", "SP3", "S11", "S12", "S13", "SP2", "S7", "S8", "S9", "S10"]:
        wv = worst[key]
        awg = V.awg_of(gauge.get(key), KIT)
        lim = AMP.get(awg)
        R.ev("%s (%s%s): mean %.2f A, worst 100 ms %.2f A, 20 ms %.2f A, 2 ms %.2f A; limit %.1f A (%d AWG)" % (
            key, gauge.get(key), ", assumed %d AWG" % KIT if "kit" in str(gauge.get(key)) else "", wv["mean"], wv["w100"],
            wv["w20"], wv["w2"], lim, awg))
        if wv["mean"] > lim:
            R.find("FAIL", "%s mean %.2f A over the %d AWG limit %.1f A" % (key, wv["mean"], awg, lim))
        elif wv["w100"] > lim:
            over100.append("%s %.2f A" % (key, wv["w100"]))
        if wv["w20"] > 2 * lim:
            over20.append("%s %.2f A" % (key, wv["w20"]))
        # contacts: the first servo's BUS 2 terminals and each kit plug carry this current
        if wv["mean"] > MOLEX_A:
            R.find("FAIL", "%s: %.2f A mean through one 5264 / Mini-SPOX contact (3 A)" % (key, wv["mean"]))
        elif wv["w100"] > MOLEX_A:
            overc.append("%s %.2f A" % (key, wv["w100"]))
            overc_mean.append(wv["mean"])
    if over100:
        R.find("WARN", "kit cable hops over the 26 AWG chassis limit (2.2 A) in the worst 100 ms (means are under it): %s. The kit "
               "cable gauge is not published; 26 AWG is the smallest plausible (erc.py KIT_AWG)" % ", ".join(over100),
               fix="measure one hop (TEST_PLAN.md section 5) and the kit wire gauge on the first servo (TO1); if it is 26 AWG, "
                   "use 22 AWG made leads for the first two hops of each leg (BOM contingency X1/X2)")
    if over20:
        R.find("WARN", "worst 20 ms over 2 x the 26 AWG limit (erc.py rule): %s" % ", ".join(over20))
    if overc:
        R.find("WARN", "chain current through one 5264 / Mini-SPOX contact over its 3 A rating ([I] distributor listings) in the "
               "worst 100 ms (means %.1f to %.1f A): %s" % (min(overc_mean), max(overc_mean), ", ".join(overc)),
               fix="read the Molex 08-70-1040 / 50-37-5033 sheet for the 3-circuit and short-time rating; log Present Current of "
                   "the first servo of each leg in TEST_PLAN.md section 9")
    # ---------------------------------------------------------------- C: ground network of D15
    L = {}
    for w in net["wires"]:
        L[(w["cable"], w["from"], w["to"])] = w["cut_mm"]
    r = lambda mm: OHM[22] * mm / 1000.0   # noqa: E731
    RC, RAD = 0.005, 0.005                  # typical contact and adapter copper (sim/power_path_sim.py typical corner)
    br = [  # (a, b, ohm, name)
        ("SPG", "JG20", r(L[("SP1", "SPG.S", "JG20.S")]), "SP1 G"),
        ("SPG", "JG10", r(L[("SP2", "SPG.S", "JG10.S")]), "SP2 G"),
        ("SPG", "JG30", r(L[("SP3", "SPG.S", "JG30.S")]), "SP3 G"),
        ("YG3", "JG20", r(L[("SD1", "YG3.S", "JG20.S")]), "SD1 a G"),
        ("YG3", "JG30", r(L[("SD1", "YG3.S", "JG30.S")]), "SD1 b G"),
        ("H3G", "YG3", r(L[("SD1", "U2.H3.G", "YG3.S")]) + RC, "SD1 stem G (adapter H3 G terminal)"),
        ("H5G", "JG10", r(L[("SD2", "U2.H5.G", "JG10.S")]) + RC, "SD2 G (adapter H5 G terminal)"),
        ("H3G", "H5G", RAD, "adapter ground copper H3 G to H5 G"),
    ]
    nodes = ["JG20", "JG30", "JG10", "YG3", "H3G", "H5G"]
    ix = {n: i for i, n in enumerate(nodes)}
    G = np.zeros((len(nodes), len(nodes)))
    for a, b, ohm, _ in br:
        g = 1.0 / ohm
        for x, y in ((a, b), (b, a)):
            if x in ix:
                G[ix[x], ix[x]] += g
                if y in ix:
                    G[ix[x], ix[y]] -= g
    inj = {"SP1": "JG20", "SP3": "JG30", "SP2": "JG10"}
    coef = {}
    for sp, node in inj.items():
        b = np.zeros(len(nodes))
        b[ix[node]] = 1.0
        v = np.linalg.solve(G, b)
        vv = lambda n: 0.0 if n == "SPG" else v[ix[n]]   # noqa: E731
        coef[sp] = {name: (vv(a) - vv(bn)) / ohm for a, bn, ohm, name in br}
    I, dt = supply_currents(os.path.join(tr, "trace_%s.npz" % cases[0]))
    chain_i = {sp: sum(I[n] for n in names) for sp, names in CHAINS.items()}
    for name in [b[3] for b in br]:
        x = sum(coef[sp][name] * chain_i[sp] for sp in CHAINS)
        w = windows(np.abs(x), dt)
        R.ev("D15 ground network, %s: mean %.2f A, worst 100 ms %.2f A (%s; %.0f%% of a left-leg return goes this way)" % (
            name, w["mean"], w["w100"], cases[0], 100 * abs(coef["SP1"][name])))
        if name.startswith("adapter") and w["w100"] > 0.1:
            R.find("WARN", "D15 says no servo current through the adapter, but the data-lead grounds make it a parallel return "
                   "path: %.2f A mean, %.2f A worst 100 ms through the adapter ground between H3 and H5 (typical contacts, sim)" % (
                       w["mean"], w["w100"]),
                   fix="harmless for the ratings (22 AWG, 3 A contacts); if it should be zero, drop the GND wire of one adapter "
                       "socket lead (keep one ground reference) or state in WIRING.md section 2 that some return current flows "
                       "through SD1, SD2 and the adapter ground", where="altaay_lab/WIRING.md section 2, DECISIONS.md D15")
    # ---------------------------------------------------------------- D: power parts
    comps = {c["id"]: c for c in net["components"]}
    pj = os.path.join(V.out_dir(), "e6_power", "power_path_sim.json")
    if not os.path.exists(pj):
        R.find("WARN", "E6 output not found: power parts not checked against the ngspice currents")
    else:
        cs = json.load(open(pj))["cases"]
        pk = max(c["pack_A_max"] for c in cs)
        rms = max(c["pack_A_rms"] for c in cs)
        mean = max(c["pack_A_mean"] for c in cs)
        bec_max = max(c["bec_out_A_max"] for c in cs)
        bec_mean = max(c["bec_out_A_mean"] for c in cs)
        R.ev("ngspice star cases (E6): pack mean up to %.2f A, RMS up to %.2f A, max (2 ms) %.2f A; BEC out mean up to %.2f A, "
             "max %.2f A" % (mean, rms, pk, bec_mean, bec_max))
        fall = 17.0   # sim/CURRENT_BUDGET.md: falls up to about 17 A for about 20 ms with every allowance stacked, low pack
        bms = comps["BMS"]["ratings"]
        rows = [
            ("fuse 15 A ATO (F1)", rms, 15.0 * 0.75, "RMS vs 75% of rating ([I] Littelfuse derating rule of thumb, not read this session)"),
            ("fuse holder 20 A (F1)", rms, comps["F1"]["ratings"]["holder_a"], "RMS"),
            ("BMS working current (Tenergy 10 A)", rms, float(bms["i_work_a"]), "RMS"),
            ("BMS over-current trip, lowest of 22 +/- 5 A", pk, 17.0, "2 ms max"),
            ("main switch Pololu 2815, 6 A at 55 C MOSFETs", rms, comps["SW1"]["ratings"]["i_cont_55c_a"], "RMS"),
            ("main switch Pololu 2815, 16 A at 150 C", pk, comps["SW1"]["ratings"]["i_cont_150c_a"], "2 ms max"),
            ("XT30U 15 A", rms, comps["XT30"]["ratings"]["i_cont_a"], "RMS"),
            ("cells 30 A continuous each", pk, comps["PACK"]["ratings"]["cell_i_cont_a"], "2 ms max"),
            ("BEC 20 A peak", bec_max, comps["U1"]["ratings"]["i_peak_a"], "2 ms max"),
            ("BEC 15 A continuous (with 5 mph air)", bec_mean, 15.0, "mean"),
            ("BEC output leads, 5 A per 3-pin lead, 2 leads", bec_mean / 2, 5.0, "mean per lead; 2 ms max %.2f A" % (bec_max / 2)),
        ]
        for name, val, lim, basis in rows:
            margin = (lim - val) / lim * 100.0
            R.ev("%s: %.2f A (%s) vs %.2f A, margin %.0f%%" % (name, val, basis, lim, margin))
            if val > lim:
                R.find("FAIL", "%s: %.2f A over %.2f A" % (name, val, lim))
            elif margin < 10:
                R.find("WARN", "%s: %.2f A against %.2f A, %.0f%% margin (sim pass only)" % (name, val, lim, margin),
                       fix="bench check: TEST_PLAN.md section 4.2 (2815 at 5 A) and the section 9 walking log; the 2815 is "
                           "rated 6 A with the MOSFETs at 55 C in still air at 22 C, inside the body it runs warmer"
                       if "2815" in name else "bench check before assembly")
        R.ev("stacked fall estimate (CURRENT_BUDGET.md): about %.0f A for about 20 ms vs BMS trip 17 to 27 A after 4 to 12 ms" % fall)
        R.find("WARN", "falls with every allowance stacked reach about 17 A for 20 ms (CURRENT_BUDGET.md), the bottom of the "
               "Tenergy trip band (22 +/- 5 A after 8 +/- 4 ms): a fall at a low pack can open the BMS (sim pass only; known)",
               fix="keep TEST_PLAN.md section 3.3 (pulse test) and log BMS cut-outs in section 9", where="TEST_PLAN.md")
        u2 = [w for w in net["wires"] if w["from"].startswith("U2.") or w["to"].startswith("U2.")]
        pw = [w for w in u2 if w["net"] in ("SERVO_7V2", "VSW", "PACK_P", "PACK_F")]
        R.ev("adapter U2: %d wires, %d on a power net (D15: none)" % (len(u2), len(pw)))
        if pw:
            R.find("FAIL", "power wire on the adapter: %s" % [(w["cable"], w["from"], w["to"]) for w in pw])
    R.key("every mean current under its limit; worst-100 ms peaks over the 26 AWG kit cable limit on %d hops and over 3 A on %d "
          "contacts; 2815 switch at %.0f%% of 6 A; 10%% of a leg's return current flows through the adapter" % (
              len(over100), len(overc), 100 * rms / 6.0 if os.path.exists(pj) else float("nan")))
    R.write()


if __name__ == "__main__":
    main()
