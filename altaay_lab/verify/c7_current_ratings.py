"""C7: current ratings of every wire, contact and part on the servo power path as it is wired now (sim pass only):
D15 star plus the D23 second feeds SP4 and SP5, the network of sim/power_fix.py option "ab" (the one E6 runs).

A. Every conductor on the servo side that the netlist gives no current (P11 from the BEC splices to SPV, SP1 to SP5,
   the 11 kit cable hops; erc.py skips them) gets its current from the E5 MuJoCo traces (BAM motor model as
   sim/current_budget.py, kt 1.148, plus 0.05 A quiescent per servo as in sim/power_path_sim.py), taken at 6.0 V
   (power / 6.0 V, the D16 hard stop; the servos draw more current at a lower bus voltage, so this is an upper estimate).
   Each leg chain is a loop now (SP1/SP2 at the hip yaw servo, SP4/SP5 at the ankle), so the split over the conductors
   depends on their resistances: sim/power_fix.py current_split() gives it from the as-built network (DC, which holds at
   every time point because the network has no reactive part), in both resistance corners; the worse corner counts.
   Compared with the chassis ampacity of the gauge (the AMP table in audit/erc.py) with erc.py's rules: mean over the
   limit FAIL, worst 100 ms over the limit WARN, worst 20 ms over 2 x the limit WARN.
B. The 5264 / Mini-SPOX contact at the servo end of SP1 to SP5 and each kit cable plug against 3 A per contact ([I]
   Molex 08-70-1040 distributor listings, read via search index 2026-11-02; Molex sheet not read).
C. Ground network as wired: the - side of the same network with the SP1 to SP5 grounds, the D15 data-lead grounds (SD1
   stem and branches, SD2), the adapter ground copper and the USB cable ground to the Pi; the share of servo return
   current through the adapter, compared with E6's ngspice probes.
D. Fuse, holder, BMS, Pololu 2815, XT30, cells, the BEC, its output leads and the P cables (P1, P2, P6, P7, P8, P14, P9,
   P10, P11, P13) against the pack, BEC and branch currents of the E6 ngspice as-built cases (trained mass and our
   build when E6 ran it), and the stacked fall estimate of sim/CURRENT_BUDGET.md. The Pololu 2815 is rated 6.0 A
   continuous with its MOSFETs at 55 C and 16 A at 150 C (12 V, 22 C ambient, still air; https://www.pololu.com/product/2815
   read 2026-11-02 1:32 AM ET): 6.0 A is a heat point, so a sim RMS near or over it is a WARN tied to the TEST_PLAN.md 4.2
   heat check, never a silent pass. The netlist's written currents on these cables are compared with the as-built sim.

Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/c7_current_ratings.py   (after E5 and E6)
"""
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

KT, KT_OVER_R, VIN = 1.148, 3.23 / 7.4, 7.4
V_EVAL = 6.0
IQ = 0.05
MOLEX_A = 3.0
POLOLU = "https://www.pololu.com/product/2815, read 2026-11-02 1:32 AM ET"
CASES = ("walk_backlash", "walk_rough_backlash", "walk_pushes", "walk_side_0.2", "turn_1.0")
ORDER_PLUS = ["lead", "sp_L", "hop_left_hip_roll", "hop_left_hip_pitch", "hop_left_knee", "hop_left_ankle", "inj_L",
              "sp_R", "hop_right_hip_roll", "hop_right_hip_pitch", "hop_right_knee", "hop_right_ankle", "inj_R",
              "sp_N", "hop_head_pitch", "hop_head_yaw", "hop_head_roll"]
GND_NAMES = {"lead": "P11 G (BEC splice JB- to SPG)", "sp_L": "SP1 G (SPG to JG20)", "sp_L_tail": "SP1 G tail (JG20 to ID 20)",
             "sp_R": "SP2 G (SPG to JG10)", "sp_R_tail": "SP2 G tail (JG10 to ID 10)", "sp_N": "SP3 G (SPG to JG30)",
             "sp_N_tail": "SP3 G tail (JG30 to ID 30)", "inj_L": "SP4 G (SPG to ID 24 BUS 1)", "inj_R": "SP5 G (SPG to ID 14 BUS 1)",
             "sd1a": "SD1 branch a G (YG3 to JG20)", "sd1b": "SD1 branch b G (YG3 to JG30)", "h3": "SD1 stem G (adapter H3 G terminal)",
             "h5": "SD2 G (adapter H5 G terminal)", "ad3": "adapter ground copper H3 G side", "ad5": "adapter ground copper H5 G side",
             "usb": "USB cable ground (adapter to Pi)", "p12": "P12 G (Pi pin 6 to regulator)"}


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
    """mean, worst 100 ms, worst 20 ms and 2 ms maximum of |x| (a hop in a loop can carry current either way)"""
    y = np.abs(x)

    def mov(n):
        c = np.cumsum(np.insert(y, 0, 0.0))
        return (c[n:] - c[:-n]) / n
    return dict(mean=float(y.mean()), w100=float(mov(int(round(0.1 / dt))).max()), w20=float(mov(int(round(0.02 / dt))).max()),
                w2=float(y.max()))


def worse(a, b):
    return {k: max(a[k], b[k]) for k in a} if a else dict(b)


def main():
    R = V.Result("C7", "Current ratings: every wire, contact and part on the servo power path as wired now (D15 plus the D23 "
                 "feeds SP4 and SP5) vs the simulated currents (sim pass only)",
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/c7_current_ratings.py",
                 "P11, SP1 to SP5 and the 11 kit cable hops vs gauge ampacity (erc.py table), with the as-built current split "
                 "(each leg a loop through SP4/SP5) in both corners; their 5264 / Mini-SPOX contacts (3 A); return current in "
                 "the SP grounds, the D15 data-lead grounds, the adapter and the USB ground; fuse, holder, BMS, Pololu 2815 "
                 "(TEST_PLAN 4.2 heat check), XT30, cells, BEC, BEC leads and the P cables vs the E6 as-built ngspice currents; "
                 "the netlist's written currents vs the sim",
                 "Real servo currents (CURRENT_BUDGET.md: up to 2 x sim until a bench log), temperature rise inside the "
                 "body, connector wear, real contact and hop resistance (TEST_PLAN.md sections 3 to 5 and 9)")
    tr = os.path.join(V.out_dir(), "e5_current")
    net = V.load_netlist()
    T = V.erc_tables()
    AMP, KIT = T["AMP"], T["KIT_AWG"]
    R.inp(V.lab("audit", "erc.py"), V.lab("wiring", "netlist.yaml"), V.lab("sim", "CURRENT_BUDGET.md"), V.lab("sim", "power_fix.py"),
          V.lab("sim", "power_path_sim.py"), V.lab("TEST_PLAN.md"))
    cases = [c for c in CASES if os.path.exists(os.path.join(tr, "trace_%s.npz" % c))]
    if not cases:
        R.not_run("no traces from E5 in %s" % tr)
        return R.write()
    os.environ["ODM_OUT"] = os.path.join(V.out_dir(), "c7_split")
    sys.path.insert(0, V.lab("sim"))
    import power_fix as PF  # noqa: E402
    split = {cn: PF.current_split(cn) for cn in ("typical", "high-side")}
    names = split["typical"]["names"]
    cab = split["typical"]["cable_of"]
    nl = PF.net_len()
    R.ev("traces: %s (E5 run); servo supply current = positive electrical power / %.1f V + %.2f A quiescent (an upper estimate; "
         "on the 7.4 V basis of CURRENT_BUDGET.md the currents are %.2f x these); split over the as-built network (sim/power_fix.py "
         "option ab, netlist %s sha256 %s), both corners, the worse counts" % (", ".join(cases), V_EVAL, IQ, V_EVAL / VIN,
                                                                                nl["source"]["path"], nl["source"]["sha256_10"]))
    # ---------------------------------------------------------------- A and B: + side conductors
    plus = {}            # edge -> worst windows over cases and corners
    pcase = {}           # edge -> (case, corner) of the worst 100 ms
    minus = {}
    minus_bk = {}        # walk_backlash, typical: ground share
    for case in cases:
        I, dt = supply_currents(os.path.join(tr, "trace_%s.npz" % case))
        M = np.array([I[n] for n in names])
        for cn, sp in split.items():
            en, A = sp["plus"]
            X = A @ M
            for k, e in enumerate(en):
                w = windows(X[k], dt)
                if e not in plus or w["w100"] > plus[e]["w100"]:
                    pcase[e] = (case, cn)
                plus[e] = worse(plus.get(e), w)
            en, A = sp["minus"]
            X = A @ M
            for k, e in enumerate(en):
                w = windows(X[k], dt)
                minus[e] = worse(minus.get(e), w)
                if case == "walk_backlash" and cn == "typical":
                    minus_bk[e] = w
            if case == "walk_backlash" and cn == "typical":
                minus_bk["_total"] = windows(M.sum(0), dt)

    def gauge_of(edge):
        c = cab[edge]
        if edge == "lead":
            return "%d AWG" % nl["P11p"][0]
        for w in net["wires"]:
            if w["cable"] == c and w.get("net") == "SERVO_7V2":
                return w["gauge"]
        return None
    over100, over20, overc, overc_mean = [], [], [], []
    for e in ORDER_PLUS:
        if e not in plus:
            continue
        wv = plus[e]
        g = gauge_of(e)
        awg = V.awg_of(g, KIT)
        lim = AMP.get(awg)
        label = "%s%s" % (cab[e], " (BEC splice JB+ to SPV, 16 AWG; the BEC leads are in part D)" if e == "lead" else
                          " (second feed, %s)" % nl["feeds"][e[-1]]["servo"].replace("_", " ") if e.startswith("inj_") else "")
        R.ev("%s (%s%s): mean %.2f A, worst 100 ms %.2f A, 20 ms %.2f A, 2 ms %.2f A; limit %.1f A (%d AWG); worst 100 ms in %s, %s corner" % (
            label, g, ", assumed %d AWG" % KIT if "kit" in str(g) else "", wv["mean"], wv["w100"], wv["w20"], wv["w2"], lim, awg,
            pcase[e][0], pcase[e][1]))
        if wv["mean"] > lim:
            R.find("FAIL", "%s mean %.2f A over the %d AWG limit %.1f A" % (cab[e], wv["mean"], awg, lim))
        elif wv["w100"] > lim:
            over100.append("%s %.2f A" % (cab[e], wv["w100"]))
        if wv["w20"] > 2 * lim:
            over20.append("%s %.2f A" % (cab[e], wv["w20"]))
        if e == "lead":
            continue          # solder splices at both ends: no crimp contact
        if wv["mean"] > MOLEX_A:
            R.find("FAIL", "%s: %.2f A mean through one 5264 / Mini-SPOX contact (3 A)" % (cab[e], wv["mean"]))
        elif wv["w100"] > MOLEX_A:
            overc.append("%s %.2f A" % (cab[e], wv["w100"]))
            overc_mean.append(wv["mean"])
    if over100:
        R.find("WARN", "kit cable hops over the 26 AWG chassis limit (2.2 A) in the worst 100 ms with the as-built split (means are "
               "under it): %s. The kit cable gauge is not published; 26 AWG is the smallest plausible (erc.py KIT_AWG)" % ", ".join(over100),
               fix="measure one hop (TEST_PLAN.md section 5) and the kit wire gauge on the first servo (TO1); if it is 26 AWG, "
                   "use 22 AWG made leads for the hops listed here (BOM contingency X1/X2)")
    if over20:
        R.find("WARN", "worst 20 ms over 2 x the 26 AWG limit (erc.py rule), as built: %s" % ", ".join(over20))
    if overc:
        R.find("WARN", "current through one 5264 / Mini-SPOX contact over its 3 A rating ([I] distributor listings) in the worst "
               "100 ms, as built (means %.1f to %.1f A): %s" % (min(overc_mean), max(overc_mean), ", ".join(overc)),
               fix="read the Molex 08-70-1040 / 50-37-5033 sheet for the 3-circuit and short-time rating; log Present Current of "
                   "the servos in TEST_PLAN.md section 9")
    # ---------------------------------------------------------------- C: ground network as wired
    tot = minus_bk["_total"]["mean"]
    for e in ("lead", "sp_L", "sp_L_tail", "inj_L", "sp_R", "sp_R_tail", "inj_R", "sp_N", "sp_N_tail", "sd1a", "sd1b", "h3", "h5",
              "ad3", "ad5", "usb", "p12"):
        if e not in minus:
            continue
        w, b = minus[e], minus_bk[e]
        R.ev("ground network, %s: walk_backlash typical %.2f A mean (%.0f %% of all servo return current), worst over cases and "
             "corners %.2f A mean, %.2f A worst 100 ms, %.2f A max" % (GND_NAMES[e], b["mean"], 100 * b["mean"] / tot, w["mean"],
                                                                       w["w100"], w["w2"]))
    ad = max(("h3", "h5", "ad3", "ad5"), key=lambda e: minus.get(e, {"w100": 0})["w100"])
    e6p = {}
    pj = [os.path.join(V.out_dir(), "e6_power", t, "power_path_sim.json") for t in ("trained", "ours")]
    e6 = [(t, json.load(open(p))) for t, p in zip(("trained mass (E5)", "our build (C8)"), pj) if os.path.exists(p)]
    for tn, d in e6:
        for c in d["cases"]:
            for k, v in c.get("branch_A", {}).items():
                o = e6p.get(k)
                if not o or v["max_100ms"] > o["max_100ms"]:
                    e6p[k] = dict(v, case="%s, %s" % (tn, c["label"].replace("as_built: ", "")))
    if "n_h3" in e6p:
        R.ev("E6 ngspice probes (as built, worst case): adapter H3 G %.2f A RMS, %.2f A worst 100 ms; H5 G %.2f A RMS, %.2f A worst "
             "100 ms; USB ground %.2f A RMS, %.2f A worst 100 ms (%s)" % (e6p["n_h3"]["rms"], e6p["n_h3"]["max_100ms"], e6p["n_h5"]["rms"],
                                                                          e6p["n_h5"]["max_100ms"], e6p["n_usb"]["rms"], e6p["n_usb"]["max_100ms"],
                                                                          e6p["n_h3"]["case"]))
    if minus[ad]["w100"] > 0.1:
        R.find("WARN", "D15 says no servo current through the adapter, but the data-lead grounds make it a parallel return path: as "
               "built %.2f A worst 100 ms through %s (DC split, 6.0 V currents)%s; harmless against the adapter's MAX:6A header "
               "marking and the 3 A contacts" % (minus[ad]["w100"], GND_NAMES[ad],
                                                  "; ngspice %.2f A worst 100 ms in the adapter H3 G lead" % e6p["n_h3"]["max_100ms"]
                                                  if "n_h3" in e6p else ""),
               fix="if it must be zero, drop the GND wire of one adapter socket lead (keep one ground reference) or state in "
                   "WIRING.md section 2 that some return current flows through SD1, SD2 and the adapter ground",
               where="altaay_lab/WIRING.md section 2, DECISIONS.md D15")
    # ---------------------------------------------------------------- D: power parts at the E6 as-built currents
    comps = {c["id"]: c for c in net["components"]}
    if not e6:
        R.find("WARN", "E6 output not found: power parts not checked against the ngspice currents")
        R.key("as built: %d hops over the 26 AWG kit limit and %d contacts over 3 A in the worst 100 ms; power parts not checked "
              "(no E6 output)" % (len(over100), len(overc)))
        return R.write()
    walk = [(tn, c) for tn, d in e6 for c in d["cases"] if "walk" in c["label"]]
    walkfn = [(tn, c) for tn, c in walk if "pack low" not in c["label"]]
    allc = [(tn, c) for tn, d in e6 for c in d["cases"]]

    def top(rows, key, sub=None):
        f = (lambda c: c[key]) if sub is None else (lambda c: c["branch_A"][key][sub])
        tn, c = max(rows, key=lambda x: f(x[1]))
        return f(c), "%s, %s" % (tn, c["label"].replace("as_built: ", ""))
    rms, rms_at = top(walkfn, "pack_A_rms")
    rms_low, rms_low_at = top(walk, "pack_A_rms")
    mean, mean_at = top(walkfn, "pack_A_mean")
    w100, w100_at = top(walkfn, "pack_A_max_100ms")
    pk, pk_at = top(allc, "pack_A_max")
    bec_max, bec_max_at = top(allc, "bec_out_A_max")
    bec_rms, bec_rms_at = top(walkfn, "bec_out_A_rms")
    p10 = top(walkfn, "p10", "rms"); p10w = top(walkfn, "p10", "max_100ms"); p10m = top(walkfn, "p10", "mean")
    p13 = top(walkfn, "p13", "rms"); p13w = top(walkfn, "p13", "max_100ms"); p13m = top(walkfn, "p13", "mean")
    R.ev("E6 ngspice as-built cases (%s): walking at full and nominal pack: pack mean up to %.2f A, RMS up to %.2f A (%s), worst 100 ms "
         "%.2f A; at the low pack (6.6 V, past the battery guard) RMS up to %.2f A (%s); any case 2 ms max %.2f A (%s); BEC out RMS up "
         "to %.2f A, max %.2f A; BEC input (P10) RMS %.2f A; 5 V branch (P13) RMS %.2f A" % (
             " and ".join(tn for tn, _ in e6), mean, rms, rms_at, w100, rms_low, rms_low_at, pk, pk_at, bec_rms, bec_max, p10[0], p13[0]))
    fall = 17.0   # sim/CURRENT_BUDGET.md: falls up to about 17 A for about 20 ms with every allowance stacked, low pack
    bms = comps["BMS"]["ratings"]
    sw = comps["SW1"]["ratings"]
    tp = open(V.lab("TEST_PLAN.md"), encoding="utf-8").read()
    s4 = re.search(r"^## 4\..*?(?=^## )", tp, re.M | re.S)
    s42 = re.search(r"^2\. Pololu 2815.*$", s4.group(0) if s4 else "", re.M)
    heat = bool(s42 and re.search(r"10 minutes at 6\.0 A", s42.group(0)) and re.search(r"under 50 C", s42.group(0)))
    rows = [
        ("fuse 15 A ATO (F1)", rms, 15.0 * 0.75, "RMS vs 75% of rating ([I] Littelfuse derating rule of thumb, not read this session)"),
        ("fuse holder 20 A (F1)", rms, comps["F1"]["ratings"]["holder_a"], "RMS"),
        ("BMS working current (Tenergy 10 A)", rms, float(bms["i_work_a"]), "RMS"),
        ("BMS over-current trip, lowest of 22 +/- 5 A", pk, 17.0, "2 ms max, any case"),
        ("main switch Pololu 2815, 6.0 A continuous at 55 C", rms, sw["i_cont_55c_a"], "RMS walking"),
        ("main switch Pololu 2815, 16 A continuous at 150 C", pk, sw["i_cont_150c_a"], "2 ms max, any case"),
        ("XT30U 15 A", rms, comps["XT30"]["ratings"]["i_cont_a"], "RMS"),
        ("cells 30 A continuous each", pk, comps["PACK"]["ratings"]["cell_i_cont_a"], "2 ms max"),
        ("BEC 20 A peak", bec_max, comps["U1"]["ratings"]["i_peak_a"], "2 ms max, any case"),
        ("BEC 15 A continuous (with 5 mph air)", bec_rms, 15.0, "RMS walking"),
        ("BEC output leads, 5 A per 3-pin lead, 2 leads", bec_rms / 2, 5.0, "RMS per lead, equal split as the netlist; 2 ms max %.2f A" % (bec_max / 2)),
    ]
    for name, val, lim, basis in rows:
        margin = (lim - val) / lim * 100.0
        R.ev("%s: %.2f A (%s) vs %.2f A, margin %.0f%%" % (name, val, basis, lim, margin))
        if "2815, 6.0 A" in name:
            if margin < 10:
                R.find("WARN", "main switch Pololu 2815: as-built sim pack RMS %.2f A while walking (%s), %.0f %% of its 6.0 A continuous "
                       "rating at 55 C (Pololu: 12 V, 22 C ambient, still air; 16 A at 150 C; %s); %.2f A at the low pack. 6.0 A is a "
                       "heat point, not a limit: the board on foam tape inside the body runs warmer than Pololu's test (sim pass only)" % (
                           val, rms_at, 100 * val / lim, POLOLU, rms_low),
                       fix=("TEST_PLAN.md 4.2 heat check: 10 minutes at 6.0 A (TE4) on its seat with the foam tape, board under 50 C; over "
                            "50 C fit a second 2815 in parallel below the first (sim/POWER_FIX.md)" if heat else
                            "add the heat check to TEST_PLAN.md 4.2: 10 minutes at 6.0 A (TE4) on its seat with the foam tape, board under "
                            "50 C; over 50 C fit a second 2815 in parallel below the first (sim/POWER_FIX.md)"),
                       where="altaay_lab/TEST_PLAN.md 4.2")
            continue
        if val > lim:
            R.find("FAIL", "%s: %.2f A over %.2f A" % (name, val, lim))
        elif margin < 10:
            R.find("WARN", "%s: %.2f A against %.2f A, %.0f%% margin (sim pass only)" % (name, val, lim, margin),
                   fix="bench check before assembly")
    R.ev("TEST_PLAN.md 4.2 has the 10-minute 6.0 A heat check of the 2815 (board under 50 C): %s" % heat)
    # P cables: ampacity at the as-built currents, and the netlist's written currents vs the sim
    pc = {"P1": ("pack", "PACK.B+", "BMS.B+"), "P2": ("pack", "PACK.B-", "BMS.B-"), "P6": ("pack", "BMS.P+", "XT30.F+"),
          "P8": ("pack", "BMS.P-", "XT30.F-"), "P7": ("pack", "XT30.M+", "JFI.S"), "P14": ("pack", "XT30.M-", "G.S"),
          "P9": ("pack", "SW1.VOUT", "VSW.S"), "P10": ("p10", "VSW.S", "U1.IN+"), "P11": ("lead", "JBP.S", "SPV.S"),
          "P13": ("p13", "VSW.S", "U3.VIN")}
    cur = dict(pack=(mean, w100), p10=(p10m[0], p10w[0]), p13=(p13m[0], p13w[0]),
               lead=(top(walkfn, "lead", "mean")[0], top(walkfn, "lead", "max_100ms")[0]))
    stale = []
    for c, (src, a, b) in pc.items():
        ws = [w for w in net["wires"] if w["cable"] == c and w["from"] == a and w["to"] == b]
        if not ws:
            R.find("WARN", "netlist wire %s %s -> %s not found (C7 P cable list)" % (c, a, b))
            continue
        w = ws[0]
        awg = V.awg_of(w["gauge"], KIT)
        lim = AMP.get(awg)
        m, x = cur[src]
        R.ev("%s (%s, %s to %s): as built %.2f A mean, %.2f A worst 100 ms (walking, ngspice); limit %.1f A; netlist writes "
             "i_mean_a %s, i_peak_a %s" % (c, w["gauge"], a, b, m, x, lim, w.get("i_mean_a"), w.get("i_peak_a")))
        if m > lim:
            R.find("FAIL", "%s mean %.2f A over the %d AWG limit %.1f A" % (c, m, awg, lim))
        elif x > lim:
            R.find("WARN", "%s worst 100 ms %.2f A over the %d AWG limit %.1f A" % (c, x, awg, lim))
        if c == "P13":
            continue          # 5 V branch: the netlist writes the 3 W typical load, the sim holds 5 W (P_5V, with margin)
        if w.get("i_mean_a") is None or w["i_mean_a"] < 0.9 * m:
            stale.append("%s i_mean_a %s (sim %.2f)" % (c, w.get("i_mean_a"), m))
    for e in ("sp_L", "sp_R", "sp_N", "inj_L", "inj_R"):
        ws = [w for w in net["wires"] if w["cable"] == cab[e] and w.get("net") == "SERVO_7V2"]
        if ws and ws[0].get("i_mean_a") is None:
            stale.append("%s i_mean_a null (C7 split %.2f, worst 100 ms %.2f)" % (cab[e], plus[e]["mean"], plus[e]["w100"]))
    if stale:
        R.find("WARN", "wiring/netlist.yaml current fields on the servo power path are lower than the as-built sim or empty (audit/erc.py "
               "checks ampacity only on these written values): %s" % "; ".join(stale),
               fix="write the as-built currents of this check (walking, nominal pack) into i_mean_a and i_peak_a of those wires",
               where="altaay_lab/wiring/netlist.yaml")
    R.ev("stacked fall estimate (CURRENT_BUDGET.md): about %.0f A for about 20 ms vs BMS trip 17 to 27 A after 4 to 12 ms" % fall)
    R.find("WARN", "falls with every allowance stacked reach about 17 A for 20 ms (CURRENT_BUDGET.md), the bottom of the "
           "Tenergy trip band (22 +/- 5 A after 8 +/- 4 ms): a fall at a low pack can open the BMS (sim pass only; known)",
           fix="keep TEST_PLAN.md section 3.3 (pulse test) and log BMS cut-outs in section 9", where="TEST_PLAN.md")
    u2 = [w for w in net["wires"] if w["from"].startswith("U2.") or w["to"].startswith("U2.")]
    pw = [w for w in u2 if w["net"] in ("SERVO_7V2", "VSW", "PACK_P", "PACK_F")]
    R.ev("adapter U2: %d wires, %d on a power net (D15: none)" % (len(u2), len(pw)))
    if pw:
        R.find("FAIL", "power wire on the adapter: %s" % [(w["cable"], w["from"], w["to"]) for w in pw])
    if "sp_L" in e6p:
        R.ev("cross-check, E6 ngspice worst 100 ms (actual bus voltage) vs this split (6.0 V currents): SP1 %.2f vs %.2f A, SP4 %.2f vs %.2f A, "
             "SP2 %.2f vs %.2f A, SP5 %.2f vs %.2f A, SP3 %.2f vs %.2f A" % tuple(
                 v for e in ("sp_L", "inj_L", "sp_R", "inj_R", "sp_N") for v in (e6p[e]["max_100ms"], plus[e]["w100"])))
    R.key("as built (SP4/SP5 in): every mean under its limit; worst 100 ms over the 26 AWG kit limit on %d hops and over 3 A on %d "
          "contacts; Pololu 2815 at %.0f %% of its 6.0 A (55 C) rating, sim RMS %.2f A walking (%.2f A at the low pack): TEST_PLAN 4.2 heat "
          "check; adapter ground %.2f A worst 100 ms" % (len(over100), len(overc), 100 * rms / sw["i_cont_55c_a"], rms, rms_low,
                                                          minus[ad]["w100"]))
    return R.write()


if __name__ == "__main__":
    main()
