"""Power path fixes for the TEST_PLAN.md section 9 ankle gate (ngspice and MuJoCo, sim pass only).

Problem: with the D15 star wiring the ankle servos spend about a fifth (typical corner) to two thirds (high-side corner)
of a walk under 6.0 V at a nominal pack (7.4 V open circuit), against the 10 % gate of TEST_PLAN.md section 9.
Below about 7.5 V of pack the Castle CC BEC Pro is in dropout and passes its input through, so the servo bus follows
the pack minus every series resistance.

This script imports sim/power_path_sim.py: its parameters P, both resistance corners, the wire table, the
pack side lengths L, the BEC behaviour and the servo load model (voltage-limited H-bridge on the BAM motor model).
It rebuilds the servo side as wired in wiring/netlist.yaml at the time of the study (D15: BEC -> P11 16 AWG 60 mm ->
splices SPV/SPG -> SP1, SP2, SP3 22 AWG -> chains of kit cable hops) and adds each candidate fix:
  1m  power_path_sim.py star model as it is (SP leads 20 AWG, P11 200 mm), for reference
  1   baseline, as built (netlist): SP leads 22 AWG 150/150/180 mm, P11 60 mm
  2   22 AWG made leads on every leg hop (S2-S5, S7-S10; BOM contingency X1/X2), cut to the CABLE_MAP rule length
  3   second power feed per leg: 22 AWG pair from SPV/SPG down the thigh to the knee, spliced into a made S5 lead
      20 mm from the knee housing (the knee has no free port)
  3b  the same pair into the free BUS 1 port of the ankle servo (ID 24, ID 14); no splice in the chain
  4   2 + 3,  4b  2 + 3b
  5   buck-boost holding 7.4 V from the whole 2S range (ideal part, efficiency 0.90 ASSUMPTION: no fitting part found)
  6   3S pack, CC BEC Pro regulating 7.2 V over the whole pack range (3S BMS 30 mOhm, Tenergy 3S table)
  and the combinations 5 + 3b, 6 + 3b.
  ab  as built (added 2026-11-02 by agent PWR): option 3b (D23, decided) with every length and gauge read from
      wiring/netlist.yaml by power_path_sim.netlist_lengths(): SP4/SP5 at their cut lengths (not the 545 mm rule
      estimate of 3b), P11 as cut, the pack side as cut (P6, P7, P8, plus P9 and P14, which the earlier lengths left
      out), and the D15 data-lead grounds (SD1, SD2, adapter, USB ground) as wired. Same servo_net() chain and feed
      structure, same cell, BMS, switch, BEC, regulator and servo load models. power_path_sim.py topology "as_built"
      runs this option; verify/e6_power_path.py, e6b_hop_sweep.py and c7_current_ratings.py check it.
Metrics (both ankles, the worse is reported): minimum voltage and % of the walk under 6.0 V, time weighted as in
power_path_sim.py. A 50 Hz log samples the bus at one fixed phase of the 20 ms control period; because the servo
current peaks just after each 50 Hz command, the sampled % depends on that phase, so its worst and best phase are
reported too.

Option 7 (is the gate right?): MuJoCo walks of our 2.77 kg build (sim/added_mass_sim.py model) with a voltage-limited
servo: position gain and torque limit both scale with V/7.4 (PWM duty x bus voltage, the BAM model), (a) at fixed
bus voltages, (b) co-simulated with this power path (a Python DC solve of the same network every 2 ms, checked
against ngspice on the same trace).

Usage (from altaay_lab; one ngspice run at a time):
  ODM_TRACES=<trace_walk_backlash.npz, trace_walk_pushes.npz from sim/current_budget.py with ODM_SAVE_TRACES=1>
  ODM_TRACES_OURS=<the same cases at our mass: ODM_SCRATCH/added_mass/traces/ours from sim/added_mass_sim.py cases>
  ODM_SCRATCH=<folder for the added_mass_sim model copies> ODM_OUT=<folder for JSON and voltage traces>
  nice -n 10 python3 sim/power_fix.py STEP
  STEP: check (builder and solver checks), run (option matrix), extra (full pack, sensitivities, 24 s windows),
        sweep, sweep2 (hop resistance), rows (POWER_PATH_SIM.md star rows), dgnd (data-lead grounds), traces,
        bay (3S battery bay check), seat (second Pololu 2815 seat), cosim (option 7, MuJoCo), png, all
"""
import os, sys, json, subprocess, tempfile, time, copy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("ODM_OUT", "/tmp/odm_power_fix")          # power_path_sim.py creates its OUT folder on import
sys.path.insert(0, HERE)
import power_path_sim as PPS                                    # the model; not edited

OUT = os.environ["ODM_OUT"]; os.makedirs(OUT, exist_ok=True)
TR_STOCK = os.environ.get("ODM_TRACES", "/tmp/odm_traces")
TR_OURS = os.environ.get("ODM_TRACES_OURS", TR_STOCK)
P, CU, L, wire = PPS.P, PPS.CU, PPS.L, PPS.wire
KT, KT_OVER_R = PPS.KT, PPS.KT_OVER_R
RM = KT / KT_OVER_R
TYP = dict(R_contact=0.005, kit_awg=24, R_cell=0.015, R_holder=0.010, R_adapter=0.005)   # power_path_sim.py __main__
CORNERS = {"typical": TYP, "high-side": {}}
PACKS = {"full": 4.2, "nominal": 3.7, "low": 3.3}
WINDOW = (10.0, 16.0)                                          # walk, backlash model, as power_path_sim.py
FALL_WINDOW = (9.5, 12.5)

# ---- servo side lengths, mm ----
SP_MM = {"L": 150, "R": 150, "N": 180}          # SP1, SP2, SP3 cut lengths (wiring/netlist.yaml), 22 AWG
P11_MM = 60                                     # JB+ to SPV, 16 AWG (netlist)
# CABLE_MAP.md rule lengths of the leg kit hops (S2..S5 left, S7..S10 right), cut 5 mm above for made leads
HOP_RULE = {"L": [152.3, 176.2, 194.8, 208.7], "R": [152.3, 176.2, 194.3, 208.7]}
HOP_CUT = {k: [float(np.ceil(x / 5.0) * 5) for x in v] for k, v in HOP_RULE.items()}
# second feed: CABLE_MAP length rule (polyline + 2 x 22.6 + 2 x 20 + 10 mm per rad crossed). Belly splice to ID 20 is
# not measured; 64.8 mm is what the 150 mm SP1 cut implies under the same rule. Leg polylines and joint ranges from
# audit/cables.json: S2 56.6 (hip yaw 1.05 rad), S3 82.3 (hip roll 0.87), S4 92.1 / 91.6 (hip pitch 1.75),
# S5 92.1 (knee 3.14).
RULE_END = 2 * 22.6 + 2 * 20
SPV_TO_ID20 = 150 - RULE_END
INJ_KNEE_RULE = {"L": SPV_TO_ID20 + 56.6 + 82.3 + 92.1 + RULE_END + 10 * (1.05 + 0.87 + 1.75),
                 "R": SPV_TO_ID20 + 56.6 + 82.3 + 91.6 + RULE_END + 10 * (1.05 + 0.87 + 1.75)}
INJ_ANKLE_RULE = {k: v + 92.1 + 10 * 3.14 for k, v in INJ_KNEE_RULE.items()}
INJ_KNEE_MM = {k: float(np.ceil(v / 5.0) * 5) for k, v in INJ_KNEE_RULE.items()}
INJ_ANKLE_MM = {k: float(np.ceil(v / 5.0) * 5) for k, v in INJ_ANKLE_RULE.items()}
TAIL_MM = 20                                    # splice to housing tail, as JG20 (netlist)
# D15 data-lead grounds (netlist): SP1/SP2 G 130 mm and SP3 G 160 mm to JG20/JG10/JG30, then the 20 mm tail; SD1 G stem
# 30 mm (H3 to YG3), branch a 120 mm (YG3 to JG20), branch b 140 mm (YG3 to JG30); SD2 G 140 mm (H5 to JG10).
SPG_MM = {"L": 130, "R": 130, "N": 160}
SD_MM = dict(stem=30, a=120, b=140, sd2=140)
R_USB_GND = 0.25    # ohm, ASSUMPTION: Adafruit 3878 GND conductor (gauge not published; 0.9 m of 28 AWG = 0.19 ohm) plus 2 USB contacts
P12_MM = 130        # U3 GND to Pi pin 6, 20 AWG (netlist)

CHAINS = {"L": PPS.CHAIN_L, "R": PPS.CHAIN_R, "N": PPS.CHAIN_N}
ANKLES = ("left_ankle", "right_ankle")

# ---- options ----
OPTIONS = {
    "1m": dict(desc="baseline, power_path_sim.py star model as it is", legacy=True),
    "1": dict(desc="baseline, star wiring as built (netlist)"),
    "2": dict(desc="22 AWG made leads on every leg hop", hops="made"),
    "3": dict(desc="second feed per leg to the knee (spliced into a made S5)", inject="knee"),
    "3b": dict(desc="second feed per leg into the free ankle BUS 1 port", inject="ankle"),
    "4": dict(desc="2 + 3", hops="made", inject="knee"),
    "4b": dict(desc="2 + 3b", hops="made", inject="ankle"),
    "5": dict(desc="buck-boost 7.4 V from the 2S range (ideal part)", source="buckboost", V_set=7.4, eff=0.90),
    "5+3b": dict(desc="5 + 3b", source="buckboost", V_set=7.4, eff=0.90, inject="ankle"),
    "6": dict(desc="3S pack, CC BEC Pro at 7.2 V", cells=3, R_bms=0.030),
    "6+3b": dict(desc="6 + 3b", cells=3, R_bms=0.030, inject="ankle"),
    # as built: 3b with the netlist's lengths and gauges and the data-lead grounds (feeds where the netlist has them)
    "ab": dict(desc="as built: D15 star plus the D23 feeds SP4 and SP5, lengths and gauges from wiring/netlist.yaml", lengths="netlist",
               data_gnd=True),
}

_NET = {}
def net_len(reload=False):
    """wiring/netlist.yaml lengths for option "ab" (read once per process; reload=True reads the file again)"""
    if reload or "v" not in _NET:
        _NET["v"] = PPS.netlist_lengths()
    return _NET["v"]

def params(corner, opt, extra=None):
    p = dict(P); p.update(CORNERS[corner]); p.update({k: v for k, v in opt.items() if k in P}); p.update(extra or {})
    return p

def servo_net(opt, p):
    """+ side of the servo network (the - side is its mirror: same resistances, separate ground conductors).
    returns edges [(name, a, b, R)], loads {servo: node}, probes [edge names with a current probe]"""
    legacy = opt.get("legacy", False)
    hop_kit = wire(p["kit_awg"], L["kit"]) + 2 * p["R_contact"] + p["R_servo_pcb"]
    edges, loads, probes = [], {}, []
    if opt.get("lengths") == "netlist":
        # as built (option "ab"): the 3b structure below with every length and gauge from wiring/netlist.yaml.
        # Hop = kit conductor + 2 contacts + the board pass-through; first lead and feed = 22 AWG lead + 1 contact (its
        # housing on the servo header; the splice end is solder); the feed also crosses the ankle board to the load node.
        N = net_len()
        edges.append(("lead", "src", "spl", p["R_bec_lead"] + wire(*N["P11p"])))
        for side, names in CHAINS.items():
            prev = "spl"
            for k, nm in enumerate(names):
                node = f"s_{nm}"; loads[nm] = node
                if k == 0:
                    r = wire(*N["sp_v"][side]) + p["R_contact"]; ename = f"sp_{side}"; probes.append(ename)
                else:
                    r = wire(p["kit_awg"], N["hop_mm"][side][k - 1]) + 2 * p["R_contact"] + p["R_servo_pcb"]; ename = f"hop_{nm}"
                    probes.append(ename)
                edges.append((ename, prev, node, r)); prev = node
            fd = N["feeds"].get(side)
            if fd:
                edges.append((f"inj_{side}", "spl", loads[fd["servo"]], wire(*fd["v"]) + p["R_contact"] + p["R_servo_pcb"]))
                probes.append(f"inj_{side}")
        probes.insert(0, "lead")
        return edges, loads, probes
    if legacy:   # exactly the power_path_sim.py star topology
        edges.append(("lead", "src", "h1", p["R_bec_lead"] + wire(16, L["P11"])))
        edges.append(("p11", "h1", "spl", wire(16, 60)))
        first = {"L": wire(20, 150) + p["R_contact"], "R": wire(20, 150) + p["R_contact"], "N": wire(20, 180) + p["R_contact"]}
    else:
        edges.append(("lead", "src", "spl", p["R_bec_lead"] + wire(16, P11_MM)))
        first = {k: wire(22, SP_MM[k]) + p["R_contact"] for k in SP_MM}
    for side, names in CHAINS.items():
        prev = "spl"
        for k, nm in enumerate(names):
            node = f"s_{nm}"; loads[nm] = node
            if k == 0:
                r = first[side]; ename = f"sp_{side}"; probes.append(ename)
            elif side != "N" and opt.get("hops") == "made":
                r = wire(22, HOP_CUT[side][k - 1]) + 2 * p["R_contact"] + p["R_servo_pcb"]; ename = f"hop_{nm}"
            else:
                r = hop_kit; ename = f"hop_{nm}"
            if side != "N" and k == 4 and opt.get("inject") == "knee":
                # made S5 with the feed spliced 20 mm from the knee housing: knee BUS 1 -> its board -> knee node
                j = f"j_{side}"; s5 = HOP_CUT[side][3]
                edges.append((f"inj_{side}", "spl", j, wire(22, INJ_KNEE_MM[side]))); probes.append(f"inj_{side}")
                edges.append((f"jk_{side}", j, loads[names[3]], wire(22, TAIL_MM) + p["R_contact"] + p["R_servo_pcb"]))
                edges.append((f"ja_{side}", j, node, wire(22, s5 - TAIL_MM) + p["R_contact"]))
                prev = node; continue
            edges.append((ename, prev, node, r)); prev = node
        if side != "N" and opt.get("inject") == "ankle":
            edges.append((f"inj_{side}", "spl", loads[names[4]], wire(22, INJ_ANKLE_MM[side]) + p["R_contact"] + p["R_servo_pcb"]))
            probes.append(f"inj_{side}")
    return edges, loads, probes

def source_R(p, cells):
    """pack side series resistance, + and - conductors, as in power_path_sim.build()"""
    rp = cells * p["R_cell"] + p["R_holder"] / 2 + wire(16, L["P1"]) + wire(16, L["P6"]) + p["R_xt30"] + wire(16, L["P7"]) + p["R_fuse"] + p["R_sw"]
    rn = p["R_holder"] / 2 + wire(16, L["P2"]) + p["R_bms"] + wire(16, L["P8"]) + p["R_xt30"]
    return rp, rn

def minus_edges(opt, p):
    """- side of option "ab" (as built): the mirror of servo_net() with the netlist's ground lengths. The SP grounds run
    SPG -> JG20/JG10/JG30 -> 20 mm tail -> first servo; with data_gnd the D15 data-lead grounds join there (SD1 stem from
    the adapter H3 G to YG3, branches to JG20 and JG30; SD2 from H5 G to JG10), the adapter copper joins H3 G and H5 G,
    and the USB cable ground runs from the adapter to the Pi and P12 into the regulator ground node "reg".
    Edges run from the BEC side outward: [(name, a, b, ohm)]."""
    N = net_len()
    plus, loads, _ = servo_net(opt, p)
    pe = {e[0]: e for e in plus}
    dg = opt.get("data_gnd")
    edges = [("lead", "src", "spl", p["R_bec_lead"] + wire(*N["P11n"]))]
    for side, names in CHAINS.items():
        s0 = loads[names[0]]
        tail = wire(*N["sp_tail"][side]) + p["R_contact"]
        if dg:
            edges += [(f"sp_{side}", "spl", f"jg_{side}", wire(*N["sp_g"][side])), (f"sp_{side}_tail", f"jg_{side}", s0, tail)]
        else:
            edges.append((f"sp_{side}", "spl", s0, wire(*N["sp_g"][side]) + tail))
        edges += [pe[f"hop_{nm}"] for nm in names[1:]]          # kit cable G conductor: as its V conductor
        fd = N["feeds"].get(side)
        if fd:
            edges.append((f"inj_{side}", "spl", loads[fd["servo"]], wire(*fd["g"]) + p["R_contact"] + p["R_servo_pcb"]))
    if dg:
        rdg, sd = opt.get("R_data_gnd", 0.0), N["sd"]
        edges += [("sd1a", "jg_L", "yg3", wire(*sd["a"]) + rdg), ("sd1b", "jg_N", "yg3", wire(*sd["b"]) + rdg),
                  ("h3", "yg3", "h3g", wire(*sd["stem"]) + p["R_contact"]), ("ad3", "h3g", "adg", p["R_adapter"] / 2),
                  ("h5", "jg_R", "h5g", wire(*sd["sd2"]) + p["R_contact"] + rdg), ("ad5", "h5g", "adg", p["R_adapter"] / 2)]
        if opt.get("usb_gnd", True):
            edges += [("usb", "adg", "pig", opt.get("R_usb", R_USB_GND)), ("p12", "pig", "reg", wire(*N["P12n"]))]
    return edges

def netlist_as_built(pw, dt, vcell, opt, p):
    """ngspice circuit of option "ab": the netlist() circuit with the netlist's pack side lengths (P9 and P14 in),
    the + side from servo_net() and the - side from minus_edges(); current probes on every lead, hop and feed, on the
    ground pieces and data grounds, and on P10 (BEC input) and P13 (5 V branch)"""
    N = net_len()
    n = len(next(iter(pw.values()))[0]); t = np.arange(n) * dt
    cells = opt.get("cells", 2)
    lines = [f"* Open Duck Mini v2 power path as built (sim/power_fix.py option ab, {N['source']['path']} {N['source']['sha256_10']})"]
    prev = "0"
    for c in range(1, cells + 1):
        top = "bplus" if c == cells else f"c{c}r"
        lines += [f"Vc{c} c{c} {prev} {vcell}", f"Rc{c} c{c} {top} {p['R_cell']}"]; prev = top
    p7 = sum(wire(*x) for x in N["P7"])
    lines += [f"Rhp bplus hp {p['R_holder']/2}", f"Rhn 0 hn {p['R_holder']/2}",
              f"Rp1 hp pp {wire(*N['P1']):.9g}", f"Rp2 hn bm {wire(*N['P2']):.9g}", f"Rbms bm pm {p['R_bms']}",
              f"Rp6 pp x1 {wire(*N['P6']) + p['R_xt30']:.9g}", f"Rp7 x1 swin {p7 + p['R_fuse']:.9g}",
              f"Rsw swin swo {p['R_sw']}", f"Rp9 swo bus {wire(*N['P9']):.9g}",
              f"Rp8 pm busn {wire(*N['P8']) + p['R_xt30'] + wire(*N['P14']):.9g}",
              "Vi_p10 bus bus_p10 0", f"Rp10p bus_p10 becip {wire(*N['P10p']):.9g}", f"Rp10n busn becin {wire(*N['P10n']):.9g}",
              f"Ebec beco becon value={{min({p['BEC_V']}, max(V(becip,becin) - {p['BEC_DROP']}, 0))}}",
              "Rbecon becon becin 1e-6", "Vbecs beco beco2 0",
              f"Bbecin becip becin I={{ V(beco,becon) * I(Vbecs) / ({p['BEC_EFF']} * max(V(becip,becin), 1)) }}",
              "Vi_p13 bus bus_p13 0", f"Rp13p bus_p13 regp {wire(*N['P13p']):.9g}", f"Rp13n busn regn {wire(*N['P13n']):.9g}",
              f"Breg regp regn I={{ {p['P_5V']} / ({p['REG_EFF']} * max(V(regp,regn), 1)) }}"]
    if "DC1" in N:
        # dock charge path (D43, D50): BMS P+ <- F2 fuse lead piece <- DK2 VOUT; DK2 blocks (1 GOhm) with its 100 k bypass;
        # the chest strip floats off the dock (1 TOhm to the pack minus keeps the node defined)
        (g1, l1), (g2, l2), (g3, l3) = N["DC1"]
        lines += [f"Rdc1c pp dc1f {wire(g3, l3) + p['R_fuse']:.9g}", f"Rdc1b dc1f dc1d {wire(g2, l2):.9g}",
                  "Rdk2 dc1d dc1s 1e9", "Rdk2by dc1d dc1s 100e3", f"Rdc1a dc1s dkp {wire(g1, l1):.9g}", "Rdkpfl dkp bm 1e12"]
    plus, loads, _ = servo_net(opt, p)
    def nd(x, s): return ("beco2" if s == "p" else "becon") if x == "src" else f"{x}{s}"
    probes = ["p10", "p13"]
    for name, a, b, r in plus:
        lines += [f"Vi_{name} {nd(a, 'p')} {nd(a, 'p')}_{name} 0", f"R{name}p {nd(a, 'p')}_{name} {nd(b, 'p')} {r:.9g}"]; probes.append(name)
    for name, a, b, r in minus_edges(opt, p):
        if name.startswith("hop_"):
            lines.append(f"R{name}n {nd(a, 'n')} {nd(b, 'n')} {r:.9g}")
        else:
            lines += [f"Vi_n_{name} {nd(a, 'n')} {nd(a, 'n')}_{name} 0", f"R{name}n {nd(a, 'n')}_{name} {nd(b, 'n')} {r:.9g}"]
            probes.append("n_" + name)
    nodes = {}
    for nm, node in loads.items():
        sp, sn = f"{node}p", f"{node}n"; nodes[nm] = (sp, sn); uc, ww = pw[nm]
        lines.append(f"Vu_{nm} u_{nm} 0 PWL(" + " ".join(f"{tt:.4f} {vv:.4f}" for tt, vv in zip(t, uc)) + ")")
        lines.append(f"Vw_{nm} w_{nm} 0 PWL(" + " ".join(f"{tt:.4f} {vv:.4f}" for tt, vv in zip(t, ww)) + ")")
        vl = f"max(V({sp},{sn}),0.5)"; ue = f"min(max(V(u_{nm}),-{vl}),{vl})"
        lines.append(f"B_{nm} {sp} {sn} I={{ max({ue}*({ue}-{KT}*V(w_{nm}))/{RM:.5f},0)/{vl} + {p['I_q']} }}")
    pr = ["v(bplus)", "v(pm)", "v(bus,busn)", "v(becip,becin)", "v(beco,becon)", "v(regp,regn)", "i(Vbecs)"]
    pr += [f"i(Vi_{x})" for x in probes] + [f"v({a},{b})" for a, b in nodes.values()]
    lines += [".options method=gear reltol=1e-3", f".tran {dt} {t[-1]:.4f}", ".control", "run",
              "wrdata {OUTFILE} " + " ".join(pr), "quit", ".endc", ".end"]
    return "\n".join(lines), pr, nodes, probes

def split_matrix(edges, loads, names, sink=True):
    """DC current split of a resistive network fed at "src" (no reactive parts, so it holds at every time point):
    A (edges x names) with edge currents = A @ I, where I is each servo's current, drawn out of its node (sink=True,
    + side) or returned into it (sink=False, - side). Positive = from the edge's first node to its second."""
    nodes = sorted({x for e in edges for x in e[1:3]} - {"src"}); ix = {nn: i for i, nn in enumerate(nodes)}
    G = np.zeros((len(nodes), len(nodes)))
    for _, a, b, r in edges:
        g = 1.0 / r
        for x, y in ((a, b), (b, a)):
            if x != "src":
                G[ix[x], ix[x]] += g
                if y != "src":
                    G[ix[x], ix[y]] -= g
    Z = np.linalg.inv(G)
    A = np.zeros((len(edges), len(names)))
    for j, nm in enumerate(names):
        v = Z[:, ix[loads[nm]]] * (-1.0 if sink else 1.0)
        for e, (_, a, b, r) in enumerate(edges):
            A[e, j] = ((0.0 if a == "src" else v[ix[a]]) - (0.0 if b == "src" else v[ix[b]])) / r
    return A

def current_split(corner, opt=None, extra=None):
    """+ and - side current split of option "ab" for verify/c7_current_ratings.py: dict(names, plus=(edge names, A),
    minus=(edge names, A), cable_of). The USB ground path returns through P12, P13 and P10 grounds to the BEC (edge ret5)."""
    opt = opt or OPTIONS["ab"]; p = params(corner, opt, extra)
    plus, loads, _ = servo_net(opt, p)
    minus = minus_edges(opt, p)
    if any(e[2] == "reg" for e in minus):
        N = net_len(); minus = minus + [("ret5", "reg", "src", wire(*N["P13n"]) + wire(*N["P10n"]))]
    names = list(PPS.CHAIN_L + PPS.CHAIN_N + PPS.CHAIN_R)
    return dict(names=names, plus=([e[0] for e in plus], split_matrix(plus, loads, names, True)),
                minus=([e[0] for e in minus], split_matrix(minus, loads, names, False)), cable_of=net_len()["cable_of"], p=p)

def netlist(pw, dt, vcell, opt, p):
    if opt.get("lengths") == "netlist":
        return netlist_as_built(pw, dt, vcell, opt, p)
    n = len(next(iter(pw.values()))[0]); t = np.arange(n) * dt
    cells = opt.get("cells", 2)
    lines = ["* Open Duck Mini v2 power path, fix study (generated by sim/power_fix.py)"]
    prev = "0"
    for c in range(1, cells + 1):
        top = "bplus" if c == cells else f"c{c}r"
        lines += [f"Vc{c} c{c} {prev} {vcell}", f"Rc{c} c{c} {top} {p['R_cell']}"]; prev = top
    lines += [f"Rhp bplus hp {p['R_holder']/2}", f"Rhn 0 hn {p['R_holder']/2}",
              f"Rp1 hp pp {wire(16, L['P1'])}", f"Rp2 hn bm {wire(16, L['P2'])}", f"Rbms bm pm {p['R_bms']}",
              f"Rp6 pp x1 {wire(16, L['P6']) + p['R_xt30']}", f"Rp7 x1 swin {wire(16, L['P7']) + p['R_fuse']}",
              f"Rsw swin bus {p['R_sw']}", f"Rp8 pm busn {wire(16, L['P8']) + p['R_xt30']}",
              f"Rp10p bus becip {wire(16, L['P10'])}", f"Rp10n busn becin {wire(16, L['P10'])}"]
    if opt.get("source") == "buckboost":
        vs, eff = opt["V_set"], opt["eff"]
        lines.append(f"Ebec beco becon value={{ {vs} }}")
    else:
        vs, eff = p["BEC_V"], p["BEC_EFF"]
        lines.append(f"Ebec beco becon value={{min({vs}, max(V(becip,becin) - {p['BEC_DROP']}, 0))}}")
    lines += ["Rbecon becon becin 1e-6", "Vbecs beco beco2 0",
              f"Bbecin becip becin I={{ V(beco,becon) * I(Vbecs) / ({eff} * max(V(becip,becin), 1)) }}",
              f"Rp13p bus regp {wire(20, L['P13'])}", f"Rp13n busn regn {wire(20, L['P13'])}",
              f"Breg regp regn I={{ {p['P_5V']} / ({p['REG_EFF']} * max(V(regp,regn), 1)) }}"]
    edges, loads, probes = servo_net(opt, p)
    def nd(x, s): return ("beco2" if s == "p" else "becon") if x == "src" else f"{x}{s}"
    dg = opt.get("data_gnd")
    for name, a, b, r in edges:
        for s in "pn":
            if s == "p" and name in probes:
                lines += [f"Vi_{name} {nd(a, s)} {nd(a, s)}_{name} 0", f"R{name}{s} {nd(a, s)}_{name} {nd(b, s)} {r:.9g}"]
            elif s == "n" and dg and name in ("sp_L", "sp_R", "sp_N"):
                side = name[-1]   # SP ground to the JG splice, then the tail into the first servo
                lines += [f"R{name}n {nd(a, s)} jg_{side}n {wire(22, SPG_MM[side]):.9g}",
                          f"R{name}nt jg_{side}n {nd(b, s)} {wire(22, TAIL_MM) + p['R_contact']:.9g}"]
            else:
                lines.append(f"R{name}{s} {nd(a, s)} {nd(b, s)} {r:.9g}")
    dprobes = []
    if dg:
        rdg = opt.get("R_data_gnd", 0.0)      # optional series resistor in each data-lead ground (the fix studied for item 4)
        lines += [f"Rsd1a jg_Ln yg3 {wire(22, SD_MM['a']) + rdg:.9g}", f"Rsd1b jg_Nn yg3 {wire(22, SD_MM['b']) + rdg:.9g}",
                  "Vi_h3 yg3 yg3_h3 0", f"Rsd1s yg3_h3 h3g {wire(22, SD_MM['stem']) + p['R_contact']:.9g}", f"Rad3 h3g adg {p['R_adapter'] / 2:.9g}",
                  "Vi_h5 jg_Rn jg_Rn_h5 0", f"Rsd2 jg_Rn_h5 h5g {wire(22, SD_MM['sd2']) + p['R_contact'] + rdg:.9g}", f"Rad5 h5g adg {p['R_adapter'] / 2:.9g}"]
        if opt.get("usb_gnd", True):
            lines += ["Vi_usb adg adg_usb 0", f"Rusb adg_usb pig {opt.get('R_usb', R_USB_GND):.9g}", f"Rp12n pig regn {wire(20, P12_MM):.9g}"]
            dprobes.append("usb")
        dprobes = ["h3", "h5"] + dprobes
    nodes = {}
    for nm, node in loads.items():
        sp, sn = f"{node}p", f"{node}n"; nodes[nm] = (sp, sn); uc, ww = pw[nm]
        lines.append(f"Vu_{nm} u_{nm} 0 PWL(" + " ".join(f"{tt:.4f} {vv:.4f}" for tt, vv in zip(t, uc)) + ")")
        lines.append(f"Vw_{nm} w_{nm} 0 PWL(" + " ".join(f"{tt:.4f} {vv:.4f}" for tt, vv in zip(t, ww)) + ")")
        vl = f"max(V({sp},{sn}),0.5)"; ue = f"min(max(V(u_{nm}),-{vl}),{vl})"
        lines.append(f"B_{nm} {sp} {sn} I={{ max({ue}*({ue}-{KT}*V(w_{nm}))/{RM:.5f},0)/{vl} + {p['I_q']} }}")
    pr = ["v(bplus)", "v(pm)", "v(bus,busn)", "v(becip,becin)", "v(beco,becon)", "v(regp,regn)", "i(Vbecs)"]
    probes = probes + dprobes
    pr += [f"i(Vi_{x})" for x in probes] + [f"v({a},{b})" for a, b in nodes.values()]
    lines += [".options method=gear reltol=1e-3", f".tran {dt} {t[-1]:.4f}", ".control", "run",
              "wrdata {OUTFILE} " + " ".join(pr), "quit", ".endc", ".end"]
    return "\n".join(lines), pr, nodes, probes

def sampled_frac(tt, v, period=0.02, step=0.002, thr=6.0):
    """fraction of 50 Hz samples under thr, for every sampling phase in the 20 ms control period"""
    out = []
    for off in np.arange(0.0, period - 1e-9, step):
        g = np.arange(tt[0] + off, tt[-1], period); out.append(float((np.interp(g, tt, v) < thr).mean()))
    return out

def vtag(on, mass, pk, cn):
    return f"v_{on.replace('+', 'p')}_{'ours' if mass.startswith('our') else 'stock'}_{pk}_{cn}"

def run(label, npz, t0, t1, vcell, opt, corner, extra=None, save=None, save_dir=None):
    p = params(corner, opt, extra)
    p["I_q"] = p.get("I_q", P["I_q"])
    if opt.get("legacy") and not opt.get("own"):   # the power_path_sim.py function itself (option 1m)
        r = PPS.run_case(label, npz, t0, t1, vcell, over=dict(CORNERS[corner], topology="star", **(extra or {})))
        return dict(label=label, option="1m", corner=corner, pack_cell_ocv=vcell, complete=r["window_ms"] >= (t1 - t0) * 1000 - 5,
                    ankle_V_min=min(r["servo_V_min"][a] for a in ANKLES),
                    ankle_pct_below_6V=round(max(r["servo_ms_below_6V"][a] for a in ANKLES) / r["window_ms"] * 100, 1),
                    worst_servo=r["worst_servo"], worst_servo_V_min=r["worst_servo_V_min"],
                    any_servo_ms_below_4V5=max(r["servo_ms_below_4V5"].values()), bec_out_V_mean=r["bec_out_V_mean"],
                    bec_out_A_max=r["bec_out_A_max"], pack_A_mean=r["pack_A_mean"], pack_A_max=r["pack_A_max"], raw=r)
    pw, dt = PPS.servo_power(npz, t0, t1)
    cir, pr, nodes, probes = netlist(pw, dt, vcell, opt, p)
    with tempfile.TemporaryDirectory() as td:
        f = os.path.join(td, "c.cir"); outf = os.path.join(td, "o.txt")
        open(f, "w").write(cir.replace("{OUTFILE}", outf))
        rr = subprocess.run(["ngspice", "-b", f], capture_output=True, text=True, timeout=3600)
        if not os.path.exists(outf):
            raise RuntimeError(rr.stdout[-2000:] + rr.stderr[-2000:])
        A = np.loadtxt(outf)
    cols = A[:, 1::2]; tt = A[:, 0]; wts = np.diff(tt, append=tt[-1])
    def tmean(x): return float((x * wts).sum() / wts.sum())
    def tms(mask): return round(float(wts[mask].sum() * 1000.0), 1)
    def max_win(x, sec):   # worst moving average over sec (1 ms grid)
        g = np.arange(tt[0], tt[-1], 0.001); y = np.interp(g, tt, x); n = int(round(sec / 0.001))
        c = np.cumsum(np.insert(y, 0, 0.0)); return float(((c[n:] - c[:-n]) / n).max()) if len(y) > n else float(y.max())
    res = {x: cols[:, i] for i, x in enumerate(pr)}
    sv = {nm: res[f"v({a},{b})"] for nm, (a, b) in nodes.items()}
    win = float(tt[-1] - tt[0]) * 1000.0
    asb = opt.get("lengths") == "netlist"
    rP2 = wire(*net_len()["P2"]) if asb else wire(16, L["P2"])
    pack_I = res["v(pm)"] / (p["R_holder"] / 2 + rP2 + p["R_bms"])
    def bstats(x):
        # as built: each leg chain is a loop (SP1/SP2 at the top, SP4/SP5 at the ankle), so a hop's current can flow
        # either way: windows and maxima of |I| (the heating current); "mean" stays signed
        y = np.abs(x) if asb else x
        d = dict(mean=round(tmean(x), 3), rms=round(float(np.sqrt(tmean(x ** 2))), 3), max_100ms=round(max_win(y, 0.1), 3),
                 max_20ms=round(max_win(y, 0.02), 3), max=round(float(y.max()), 3))
        if asb:
            d["mean_abs"] = round(tmean(np.abs(x)), 3)
        return d
    ms6 = {k: tms(v < 6.0) for k, v in sv.items()}
    samp = {a: sampled_frac(tt, sv[a]) for a in ANKLES}
    worst = min(sv, key=lambda k: sv[k].min())
    out = dict(label=label, option=None, corner=corner, pack_cell_ocv=vcell, cells=opt.get("cells", 2), complete=win >= (t1 - t0) * 1000 - 5,
               window_ms=round(win, 1), ankle_V_min=round(float(min(sv[a].min() for a in ANKLES)), 3),
               ankle_pct_below_6V=round(max(ms6[a] for a in ANKLES) / win * 100, 1),
               ankle_pct_below_6V_50Hz_worst_phase=round(100 * max(max(v) for v in samp.values()), 1),
               ankle_pct_below_6V_50Hz_best_phase=round(100 * max(min(v) for v in samp.values()), 1),
               worst_servo=worst, worst_servo_V_min=round(float(sv[worst].min()), 3),
               any_servo_pct_below_6V=round(max(ms6.values()) / win * 100, 1),
               any_servo_ms_below_4V5=max(tms(v < 4.5) for v in sv.values()),
               pack_terminal_V_min=round(float(res["v(bplus)"].min()), 3), bus_V_mean=round(tmean(res["v(bus,busn)"]), 3),
               bec_in_V_min=round(float(res["v(becip,becin)"].min()), 3),
               bec_out_V_mean=round(tmean(res["v(beco,becon)"]), 3), bec_out_V_min=round(float(res["v(beco,becon)"].min()), 3),
               bec_out_A_mean=round(tmean(res["i(Vbecs)"]), 3), bec_out_A_max=round(float(res["i(Vbecs)"].max()), 3),
               pack_A_mean=round(tmean(pack_I), 3), pack_A_max=round(float(pack_I.max()), 3),
               pack_A_rms=round(float(np.sqrt(tmean(pack_I ** 2))), 3), reg5_in_V_min=round(float(res["v(regp,regn)"].min()), 3),
               pack_A_max_100ms=round(max_win(pack_I, 0.1), 3), pack_A_max_20ms=round(max_win(pack_I, 0.02), 3),
               bus_V_min=round(float(res["v(bus,busn)"].min()), 3), switch_W_mean=round(tmean(pack_I ** 2) * p["R_sw"], 3),
               branch_A={x: bstats(res[f"i(Vi_{x})"]) for x in probes},
               bec_out_A_max_100ms=round(max_win(res["i(Vbecs)"], 0.1), 3), bec_out_A_rms=round(float(np.sqrt(tmean(res["i(Vbecs)"] ** 2))), 3),
               servo_V_min={k: round(float(v.min()), 3) for k, v in sv.items()},
               servo_V_mean={k: round(tmean(v), 3) for k, v in sv.items()}, servo_pct_below_6V={k: round(v / win * 100, 1) for k, v in ms6.items()},
               servo_ms_below_6V=ms6, servo_ms_below_4V5={k: tms(v < 4.5) for k, v in sv.items()})
    if save:   # save = file name (no extension) for the voltage time series
        np.savez_compressed(os.path.join(save_dir or OUT, f"{save}.npz"), t=tt, names=np.array(list(sv)), V=np.array([sv[k] for k in sv]),
                            bec=res["v(beco,becon)"], pack_I=pack_I, label=label, branches=np.array(probes),
                            I=np.array([res[f"i(Vi_{x})"] for x in probes]) if probes else np.zeros((0, len(tt))))
    return out

# ---------------------------------------------------------------------------------------------------------------------
# case matrix
# ---------------------------------------------------------------------------------------------------------------------
def traces():
    return {"trained mass": TR_STOCK, "our 2.77 kg build": TR_OURS}

SAVE_FOR = ("1", "3", "3b", "5", "6", "6+3b")

def save_traces():
    """voltage time series for the plots: our build, nominal pack, both corners"""
    for on in SAVE_FOR:
        for cn in CORNERS:
            run(f"{on} traces {cn}", os.path.join(TR_OURS, "trace_walk_backlash.npz"), *WINDOW, PACKS["nominal"], OPTIONS[on], cn,
                save=vtag(on, "our", "nominal", cn))

def run_all(opts=None, packs=("nominal", "low"), save_for=SAVE_FOR):
    rows = []
    for on in (opts or OPTIONS):
        opt = OPTIONS[on]
        for mass, tr in traces().items():
            npz = os.path.join(tr, "trace_walk_backlash.npz")
            for pk in packs:
                for cn in CORNERS:
                    t = time.time()
                    lab = f"{on}: {opt['desc']}; walk backlash, {mass}, pack {pk}, {cn} R"
                    r = run(lab, npz, *WINDOW, PACKS[pk], opt, cn, save=vtag(on, mass, pk, cn) if (on in save_for and pk == "nominal") else None)
                    r.update(option=on, mass=mass, pack=pk, case="walk_backlash"); rows.append(r)
                    print(f"{on:5s} {mass:18s} {pk:8s} {cn:9s} ankle min {r['ankle_V_min']:.2f} V, <6 V {r['ankle_pct_below_6V']:5.1f} % "
                          f"(50 Hz {r.get('ankle_pct_below_6V_50Hz_best_phase', '-')}-{r.get('ankle_pct_below_6V_50Hz_worst_phase', '-')} %), "
                          f"BEC out {r['bec_out_V_mean']:.2f} V mean, {r['bec_out_A_max']:.1f} A max, complete {r['complete']} ({time.time() - t:.0f} s)", flush=True)
        # fall after a push (trained mass falls at 10.68 s), low pack, high-side: peak currents for part ratings
        if on != "1m":
            r = run(f"{on}: fall after a push, trained mass, pack low, high-side R", os.path.join(TR_STOCK, "trace_walk_pushes.npz"),
                    *FALL_WINDOW, PACKS["low"], opt, "high-side")
            r.update(option=on, mass="trained mass", pack="low", case="fall_after_push"); rows.append(r)
            print(f"{on:5s} fall after push: ankle min {r['ankle_V_min']:.2f} V, BEC out {r['bec_out_A_max']:.1f} A max, pack {r['pack_A_max']:.1f} A max, "
                  f"branches {json.dumps({k: v['max'] for k, v in r['branch_A'].items()})}", flush=True)
    return rows

def run_extra():
    """sensitivities and the full pack for the baseline and the candidates"""
    rows = []
    for on in ("1", "3b", "4b", "5", "6", "6+3b", "5+3b"):
        for mass, tr in traces().items():
            npz = os.path.join(tr, "trace_walk_backlash.npz")
            for cn in CORNERS:
                r = run(f"{on}: full pack, {mass}, {cn}", npz, *WINDOW, PACKS["full"], OPTIONS[on], cn)
                r.update(option=on, mass=mass, pack="full", case="walk_backlash"); rows.append(r)
                print(f"full {on:5s} {mass:18s} {cn:9s} ankle min {r['ankle_V_min']:.2f}, <6 V {r['ankle_pct_below_6V']:.1f} %", flush=True)
    sens = [("BEC dropout 0.6 V", dict(BEC_DROP=0.6)), ("BEC dropout 0.1 V", dict(BEC_DROP=0.1)), ("servo quiescent 0.15 A", dict(I_q=0.15)),
            ("hop contacts 40 mOhm", dict(R_contact=0.040)),
            # split the corners: which half (pack side or servo side) sets the high-side result
            ("pack side typical, servo side high-side", dict(R_cell=0.015, R_holder=0.010)),
            ("pack side high-side, servo side typical", dict(R_cell=0.020, R_holder=0.030)),
            ("welded pack (holder 3 mOhm)", dict(R_holder=0.003))]
    for on in ("1", "3b", "4b", "6+3b"):
        for nm, ex in sens:
            for cn in CORNERS:
                if nm == "hop contacts 40 mOhm" and cn == "typical": continue
                if nm.startswith("pack side typical") and cn == "typical": continue
                if nm.startswith("pack side high-side") and cn == "high-side": continue
                r = run(f"{on}: {nm}, our build, nominal, {cn}", os.path.join(TR_OURS, "trace_walk_backlash.npz"), *WINDOW, PACKS["nominal"], OPTIONS[on], cn, extra=ex)
                r.update(option=on, mass="our 2.77 kg build", pack="nominal", case="sensitivity: " + nm); rows.append(r)
                print(f"sens {on:5s} {nm:24s} {cn:9s} ankle min {r['ankle_V_min']:.2f}, <6 V {r['ankle_pct_below_6V']:.1f} %", flush=True)
    # longer and lighter walks for the baseline and 3b: forward walk without the backlash model, whole 26 s after the settle
    for on in ("1", "3b", "4b"):
        for cn in CORNERS:
            for case, tr, win in (("walk_forward_0.15", TR_OURS, (4.0, 28.0)), ("walk_backlash", TR_OURS, (4.0, 28.0))):
                r = run(f"{on}: {case} {win}, our build, nominal, {cn}", os.path.join(tr, f"trace_{case}.npz"), *win, PACKS["nominal"], OPTIONS[on], cn)
                r.update(option=on, mass="our 2.77 kg build", pack="nominal", case=f"{case} {win[0]:.0f}-{win[1]:.0f} s"); rows.append(r)
                print(f"long {on:5s} {case:18s} {cn:9s} ankle min {r['ankle_V_min']:.2f}, <6 V {r['ankle_pct_below_6V']:.1f} %", flush=True)
    return rows

def hop_sweep():
    """largest hop resistance per conductor that keeps the ankles under the gate, baseline and 3b, nominal, our build"""
    rows = []
    npz = os.path.join(TR_OURS, "trace_walk_backlash.npz")
    for on in ("1", "3b"):
        for rc in (0.0, 0.005, 0.010, 0.015, 0.020, 0.030, 0.040):
            p = params("typical", OPTIONS[on]); hop = wire(24, L["kit"]) + 2 * rc + p["R_servo_pcb"]
            r = run(f"{on}: hop sweep R_contact {rc}", npz, *WINDOW, PACKS["nominal"], OPTIONS[on], "typical", extra=dict(R_contact=rc))
            r.update(option=on, mass="our 2.77 kg build", pack="nominal", case="hop sweep", hop_mOhm=round(hop * 1000, 1), R_contact=rc); rows.append(r)
            print(f"sweep {on:3s} contact {rc*1000:4.0f} mOhm hop {hop*1000:5.1f} mOhm: ankle min {r['ankle_V_min']:.2f}, <6 V {r['ankle_pct_below_6V']:.1f} %", flush=True)
    return rows

def hop_sweep2():
    """the same for the knee feed (3) and the regulated bus with the ankle feed (6+3b), both corners of the pack side"""
    rows = []
    npz = os.path.join(TR_OURS, "trace_walk_backlash.npz")
    for on in ("3", "3b", "6+3b"):
        for cn in CORNERS:
            for rc in (0.005, 0.010, 0.020, 0.030, 0.040, 0.060):
                if on == "3b" and cn == "typical": continue          # done in hop_sweep()
                p = params(cn, OPTIONS[on]); hop = wire(p["kit_awg"], L["kit"]) + 2 * rc + p["R_servo_pcb"]
                r = run(f"{on}: hop sweep R_contact {rc} {cn}", npz, *WINDOW, PACKS["nominal"], OPTIONS[on], cn, extra=dict(R_contact=rc))
                r.update(option=on, mass="our 2.77 kg build", pack="nominal", case="hop sweep", hop_mOhm=round(hop * 1000, 1), R_contact=rc); rows.append(r)
                print(f"sweep2 {on:5s} {cn:9s} contact {rc*1000:4.0f} mOhm hop {hop*1000:5.1f} mOhm: ankle min {r['ankle_V_min']:.2f}, <6 V {r['ankle_pct_below_6V']:.1f} %", flush=True)
    return rows

def star_rows():
    """rows for the sim/POWER_PATH_SIM.md results table: D15 star as built (22 AWG SP leads), trained-mass traces as there"""
    out = []
    npz = os.path.join(TR_STOCK, "trace_walk_backlash.npz")
    cases = [(pk, cn, npz, WINDOW) for pk in ("full", "nominal", "low") for cn in ("typical", "high-side")]
    cases.append(("low", "high-side", os.path.join(TR_STOCK, "trace_walk_pushes.npz"), FALL_WINDOW))
    for pk, cn, f, win in cases:
        r = run(f"star rows {pk} {cn} {win}", f, *win, PACKS[pk], OPTIONS["1"], cn)
        w = r["worst_servo"]; ms6 = r["servo_ms_below_6V"][w] / 1000; ms45 = r["servo_ms_below_4V5"][w] / 1000
        name = "fall after a push, low (6.6 V), high-side (3 s)" if win == FALL_WINDOW else f"{pk} ({2 * PACKS[pk]:.1f} V), {cn}"
        row = (f"| Star (D15 as built, 22 AWG power leads), {name} | {r['bus_V_mean']:.2f} V | {r['bec_out_V_mean']:.2f} V | "
               f"{r['pack_A_mean']:.1f} / {r['pack_A_max']:.1f} / {r['pack_A_rms']:.1f} A | {w.replace('_', ' ')} {r['worst_servo_V_min']:.2f} V, "
               f"{r['servo_V_mean'][w]:.2f} V | {ms6:.2f} s | {ms45:.2f} s |")
        out.append(dict(case=name, row=row, result={k: v for k, v in r.items() if k not in ("servo_V_mean",)})); print(row, flush=True)
    return out

def data_ground_study():
    """item from the verification agent: how much servo return current crosses the adapter through the D15 data-lead
    grounds (SD1, SD2) and the USB cable, baseline and with the ankle feed; and two ways to stop it"""
    rows = []
    npz = os.path.join(TR_OURS, "trace_walk_backlash.npz")
    variants = [("data grounds as wired (D15)", dict(data_gnd=True)),
                ("data grounds, USB ground path left out", dict(data_gnd=True, usb_gnd=False)),
                ("10 ohm in each data-lead ground", dict(data_gnd=True, R_data_gnd=10.0))]
    for on in ("1", "3", "3b"):
        for cn in CORNERS:
            for vn, ex in variants:
                if on != "3b" and vn.startswith("10 ohm"): continue
                opt = dict(OPTIONS[on], **ex)
                r = run(f"{on}: {vn}, {cn}", npz, *WINDOW, PACKS["nominal"], opt, cn)
                r.update(option=on, mass="our 2.77 kg build", pack="nominal", case="data ground: " + vn); rows.append(r)
                b = r["branch_A"]
                print(f"dgnd {on:3s} {cn:9s} {vn:40s} ankle min {r['ankle_V_min']:.2f} <6 V {r['ankle_pct_below_6V']:.1f} % | "
                      + " ".join(f"{k} {v['rms']:.3f}/{v['max_100ms']:.3f}/{v['max']:.3f}" for k, v in b.items() if k in ("h3", "h5", "usb", "sp_L", "inj_L")), flush=True)
    return rows

# ---------------------------------------------------------------------------------------------------------------------
# Python DC solve of the same network (for the MuJoCo co-simulation), checked against ngspice
# ---------------------------------------------------------------------------------------------------------------------
class Net:
    """quasi-static solve of the netlist() circuit: it has no reactive parts, so each ngspice time point is a DC point.
    + and - conductors mirror each other, so a servo sees V_out - 2 x (transfer impedance of the + side) x currents."""
    def __init__(self, opt, corner, vcell, extra=None):
        self.opt = opt; p = self.p = params(corner, opt, extra)
        edges, loads, _ = servo_net(opt, p)
        nodes = sorted({x for e in edges for x in e[1:3]} - {"src"}); ix = {n: i for i, n in enumerate(nodes)}
        G = np.zeros((len(nodes), len(nodes)))
        for _, a, b, r in edges:
            g = 1.0 / r
            for x, y in ((a, b), (b, a)):
                if x != "src": G[ix[x], ix[x]] += g
                if x != "src" and y != "src": G[ix[x], ix[y]] -= g
        Zall = np.linalg.inv(G)
        self.names = list(PPS.CHAIN_L + PPS.CHAIN_N + PPS.CHAIN_R)
        li = [ix[loads[n]] for n in self.names]
        self.Z2 = 2.0 * Zall[np.ix_(li, li)]
        cells = opt.get("cells", 2); rp, rn = source_R(p, cells)
        self.V0 = cells * vcell; self.Rs = rp + rn; self.R10 = 2 * wire(16, L["P10"]); self.R13 = 2 * wire(20, L["P13"])
        self.bb = opt.get("source") == "buckboost"
        self.Vset = opt["V_set"] if self.bb else p["BEC_V"]; self.eff = opt["eff"] if self.bb else p["BEC_EFF"]
        self.V = np.full(len(self.names), min(self.Vset, self.V0 - 0.3)); self.Iin = 0.0; self.I5 = p["P_5V"] / (p["REG_EFF"] * self.V0)
    def loads(self, u, w, V):
        vl = np.maximum(V, 0.5); ue = np.clip(u, -vl, vl)
        return np.maximum(ue * (ue - KT * w) / RM, 0.0) / vl + self.p["I_q"]
    def solve(self, u, w, iters=30, tol=1e-5):
        p = self.p; V = self.V.copy()
        for _ in range(iters):
            I = self.loads(u, w, V); Iout = I.sum()
            for _ in range(4):        # source side: pack, P10, BEC input current, 5 V branch
                vbus = self.V0 - self.Rs * (self.Iin + self.I5); vin = vbus - self.R10 * self.Iin
                vout = self.Vset if self.bb else min(self.Vset, max(vin - p["BEC_DROP"], 0.0))
                self.Iin = vout * Iout / (self.eff * max(vin, 1.0))
                self.I5 = p["P_5V"] / (p["REG_EFF"] * max(vbus - self.R13 * self.I5, 1.0))
            Vn = vout - self.Z2 @ I
            d = np.abs(Vn - V).max(); V = 0.5 * V + 0.5 * Vn
            if d < tol: break
        self.V = V; self.vout = vout; self.Iout = Iout
        return V

def check_builder():
    """this file's netlist with the power_path_sim.py star values must give the power_path_sim.py numbers"""
    npz = os.path.join(TR_STOCK, "trace_walk_backlash.npz"); out = []
    for cn in CORNERS:
        a = run("check 1m", npz, *WINDOW, PACKS["nominal"], OPTIONS["1m"], cn)
        b = run("check own builder, legacy values", npz, *WINDOW, PACKS["nominal"], dict(legacy=True, own=True), cn)
        out.append(dict(corner=cn, power_path_sim=(a["ankle_V_min"], a["ankle_pct_below_6V"], a["bec_out_V_mean"], a["bec_out_A_max"]),
                        power_fix=(b["ankle_V_min"], b["ankle_pct_below_6V"], b["bec_out_V_mean"], b["bec_out_A_max"])))
    return out

def check_solver(on="1", corner="high-side", pk="nominal"):
    """open-loop replay of one trace through Net and through ngspice; returns the largest servo voltage difference"""
    npz = os.path.join(TR_OURS, "trace_walk_backlash.npz"); opt = OPTIONS[on]
    tag = "check_" + vtag(on, "our", pk, corner)
    run(f"check {on} {corner} {pk}", npz, *WINDOW, PACKS[pk], opt, corner, save=tag)
    d = np.load(os.path.join(OUT, tag + ".npz"))
    pw, dt = PPS.servo_power(npz, *WINDOW)
    net = Net(opt, corner, PACKS[pk]); names = net.names
    U = np.array([pw[n][0] for n in names]).T; W = np.array([pw[n][1] for n in names]).T
    tg = np.arange(U.shape[0]) * dt; Vpy = np.zeros_like(U)
    for k in range(U.shape[0]): Vpy[k] = net.solve(U[k], W[k])
    sp = {n: np.interp(tg, d["t"], d["V"][list(d["names"]).index(n)]) for n in names}
    diff = max(float(np.abs(Vpy[:, i] - sp[n])[5:].max()) for i, n in enumerate(names))
    a = names.index("right_ankle")
    return dict(option=on, corner=corner, pack=pk, max_abs_diff_V=round(diff, 4),
                ankle_min_py=round(float(Vpy[:, a].min()), 3), ankle_min_ngspice=round(float(sp["right_ankle"].min()), 3))

# ---------------------------------------------------------------------------------------------------------------------
# option 7: MuJoCo walk with a voltage-limited servo (our build, sim/added_mass_sim.py model copies)
# ---------------------------------------------------------------------------------------------------------------------
def cosim_walk(folder, scene, cmd, dur, supply, seed=None, start_dz=0.0):
    """supply: float (fixed bus voltage for every servo) or a Net (co-simulated). Returns gait and voltage statistics."""
    import mujoco
    import added_mass_sim as AM
    CB = AM.CB; MI = CB.MI
    AM._ASSET_DIR[0] = folder
    m = MI.MjInfer(os.path.join(folder, scene), CB.REF, CB.ONNX, standing=False)
    if seed is not None:
        rng = np.random.default_rng(seed); qa = np.array(m.actuator_joint_qpos_addr).ravel()
        m.data.qpos[qa] += rng.uniform(-0.03, 0.03, len(qa))
    mujoco.mj_forward(m.model, m.data)
    _ga = m.get_accelerometer
    def _ga_fixed(d, _ga=_ga):
        a = np.array(_ga(d), dtype=float); a[0] -= 1.3; return a
    m.get_accelerometer = _ga_fixed                      # as current_budget.py (accelerometer bias removed)
    model, data = m.model, m.data
    names = list(m.actuator_names); fb = m._floating_base_qpos_addr; qv = m.actuator_qvel_addr
    kp0 = model.actuator_gainprm[:, 0].copy(); fr0 = model.actuator_forcerange.copy()
    net = supply if isinstance(supply, Net) else None
    order = [names.index(n) for n in net.names] if net else None
    V = np.full(model.nu, 7.4 if net else float(supply))
    if net: V[order] = net.V
    nsteps = int(dur / m.sim_dt); log = []; Vlog = np.zeros((nsteps, model.nu), np.float32); Ulog = np.zeros((nsteps, model.nu), np.float32)
    falls, fallen, counter = [], False, 0
    sched = CB.sched_const(list(cmd) + [0, 0, 0, 0])
    for k in range(nsteps):
        t = (k + 1) * m.sim_dt
        s = V / 7.4                                       # PWM duty x bus voltage: gain and torque limit scale together
        model.actuator_gainprm[:, 0] = kp0 * s; model.actuator_biasprm[:, 1] = -kp0 * s
        model.actuator_forcerange[:, 0] = fr0[:, 0] * s; model.actuator_forcerange[:, 1] = fr0[:, 1] * s
        mujoco.mj_step(model, data)
        counter += 1
        if counter % m.decimation == 0:
            m.commands = sched(t)
            m.imitation_i += 1.0 * m.phase_frequency_factor
            m.imitation_i = m.imitation_i % m.PRM.nb_steps_in_period
            ph = m.imitation_i / m.PRM.nb_steps_in_period * 2 * np.pi
            m.imitation_phase = np.array([np.cos(ph), np.sin(ph)])
            obs = m.get_obs(data, m.commands); action = m.policy.infer(obs)
            m.last_last_last_action = m.last_last_action.copy(); m.last_last_action = m.last_action.copy(); m.last_action = action.copy()
            m.motor_targets = m.default_actuator + action * m.action_scale
            if MI.USE_MOTOR_SPEED_LIMITS:
                m.motor_targets = np.clip(m.motor_targets, m.prev_motor_targets - m.max_motor_velocity * (m.sim_dt * m.decimation),
                                          m.prev_motor_targets + m.max_motor_velocity * (m.sim_dt * m.decimation))
                m.prev_motor_targets = m.motor_targets.copy()
            data.ctrl = m.motor_targets.copy()
            pos = data.qpos[fb:fb + 3].copy(); quat = data.qpos[fb + 3:fb + 7].copy()
            R = np.zeros(9); mujoco.mju_quat2Mat(R, quat); R = R.reshape(3, 3); upz = R[2, 2]
            if (pos[2] < 0.10 or upz < 0.5) and not fallen: fallen = True; falls.append(round(t, 2))
            if fallen and pos[2] > 0.13 and upz > 0.8: fallen = False
            yaw = np.arctan2(R[1, 0], R[0, 0]); pitch = np.arcsin(-np.clip(R[2, 0], -1, 1)); roll = np.arctan2(R[2, 1], R[2, 2])
            log.append((t, pos[0], pos[1], pos[2], yaw, pitch, roll, 0, 0, 0, float(fallen)))
        u = data.actuator_force / KT_OVER_R              # applied motor voltage, already under V by the scaled limit
        w = data.qvel[qv]
        Ulog[k] = u
        if net:
            V[order] = net.solve(u[order], w[order])
        Vlog[k] = V
    res = dict(F=None, W=None, names=names, dt=m.sim_dt, falls=falls, log=np.array(log))
    model.actuator_gainprm[:, 0] = kp0; model.actuator_biasprm[:, 1] = -kp0; model.actuator_forcerange[:] = fr0
    g = AM.gait_stats(dict(res, F=np.zeros((nsteps, model.nu))), cmd)
    k0 = int(round(4.0 / m.sim_dt))
    ank = [names.index(a) for a in ANKLES]; knees = [names.index(a) for a in ("left_knee", "right_knee")]
    sat = np.abs(Ulog[k0:]) >= 0.999 * Vlog[k0:]
    out = dict(falls=[f for f in falls if f > 1.0], vx=g.get("vx"), vy=g.get("vy"), wz=g.get("wz"), track_lin=g.get("track_lin"), track_yaw=g.get("track_yaw"),
               pitch_mean_deg=g.get("pitch_mean_deg"), pitch_rms_deg=g.get("pitch_rms_deg"), roll_rms_deg=g.get("roll_rms_deg"), z_mean=g.get("z_mean"),
               knee_sat_pct=round(100 * float(sat[:, knees].mean()), 1), ankle_V_min=round(float(Vlog[k0:, ank].min()), 3),
               ankle_pct_below_6V=round(100 * float((Vlog[k0:, ank] < 6.0).mean(0).max()), 1),
               V_mean=round(float(Vlog[k0:].mean()), 3))
    return out

def run_cosim(seeds=(None, 1)):
    import added_mass_sim as AM
    V = AM.variants(); folder = V["ours"][0]
    cases = [("walk_forward_0.15", "scene_flat_terrain.xml", (0.15, 0, 0)), ("walk_backlash", "scene_flat_terrain_backlash.xml", (0.15, 0, 0)),
             ("turn_1.0", "scene_flat_terrain.xml", (0, 0, 1.0))]
    rows = []
    for vbus in (7.4, 7.2, 7.0, 6.6, 6.2, 6.0, 5.6, 5.2, 4.8, 4.4, 4.0):
        for case, scene, cmd in cases:
            for sd in seeds:
                r = cosim_walk(folder, scene, cmd, 20.0, vbus, seed=sd); r.update(kind="fixed bus", V_bus=vbus, case=case, seed=sd); rows.append(r)
                tr = r["track_lin"] if r["track_lin"] is not None else r["track_yaw"]
                print(f"fixed {vbus:.1f} V {case:18s} seed {sd}: falls {r['falls']} track {tr if tr is None else round(tr, 2)} "
                      f"pitch {r['pitch_mean_deg']} knee sat {r['knee_sat_pct']} %", flush=True)
    for on, packs in (("1", ("nominal", "low")), ("3", ("nominal",)), ("3b", ("nominal",)), ("6+3b", ("nominal", "low"))):
        for cn in CORNERS:
            for pk in packs:
                for case, scene, cmd in cases[:2]:
                    for sd in seeds:
                        net = Net(OPTIONS[on], cn, PACKS[pk])
                        r = cosim_walk(folder, scene, cmd, 20.0, net, seed=sd); r.update(kind="co-simulated", option=on, corner=cn, pack=pk, case=case, seed=sd); rows.append(r)
                        print(f"cosim {on:5s} {cn:9s} {pk:8s} {case:18s} seed {sd}: falls {r['falls']} track {r['track_lin']} ankle min {r['ankle_V_min']:.2f} "
                              f"<6 V {r['ankle_pct_below_6V']} % pitch {r['pitch_mean_deg']}", flush=True)
    return rows

# ---------------------------------------------------------------------------------------------------------------------
def summary_table(rows):
    """per option: worst over the two traces of ankle min and % under 6 V, nominal and low pack, both corners"""
    out = {}
    for on in OPTIONS:
        d = {}
        for pk in ("nominal", "low"):
            for cn in CORNERS:
                rs = [r for r in rows if r["option"] == on and r["pack"] == pk and r["corner"] == cn and r.get("case") == "walk_backlash" and "mass" in r]
                if not rs: continue
                d[f"{pk}, {cn}"] = dict(ankle_V_min=min(r["ankle_V_min"] for r in rs), ankle_pct_below_6V=max(r["ankle_pct_below_6V"] for r in rs),
                                        pct_50Hz_worst=max(r.get("ankle_pct_below_6V_50Hz_worst_phase", float("nan")) for r in rs),
                                        complete=all(r["complete"] for r in rs), any_servo_ms_below_4V5=max(r["any_servo_ms_below_4V5"] for r in rs),
                                        bec_out_A_max=max(r["bec_out_A_max"] for r in rs), per_mass={r["mass"]: (r["ankle_V_min"], r["ankle_pct_below_6V"]) for r in rs})
        out[on] = d
    return out

def plots(rows, cos):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    S = summary_table(rows)
    opts = [o for o in OPTIONS if o != "1m"]
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.9), sharey=False)
    x = np.arange(len(opts)); wdt = 0.2
    cols = {"nominal, typical": "#4a6fa5", "nominal, high-side": "#c0392b", "low, typical": "#7fa7d9", "low, high-side": "#e59a8f"}
    for i, (k, c) in enumerate(cols.items()):
        y = [S[o].get(k, {}).get("ankle_pct_below_6V", np.nan) for o in opts]
        axs[0].bar(x + (i - 1.5) * wdt, y, wdt, color=c, label=k)
        y2 = [S[o].get(k, {}).get("ankle_V_min", np.nan) for o in opts]
        axs[1].bar(x + (i - 1.5) * wdt, y2, wdt, color=c, label=k)
    axs[0].axhline(10, color="k", lw=0.8, ls="--"); axs[0].text(len(opts) - 0.5, 11, "gate 10 %", fontsize=7, ha="right")
    axs[0].axhline(5, color="k", lw=0.6, ls=":"); axs[0].text(len(opts) - 0.5, 6, "margin 5 %", fontsize=7, ha="right")
    axs[1].axhline(6.0, color="k", lw=0.8, ls="--"); axs[1].axhline(4.5, color="k", lw=0.6, ls=":")
    for a, yl in zip(axs, ("ankle time under 6.0 V (% of the walk)", "ankle minimum (V)")):
        a.set_xticks(x); a.set_xticklabels(opts, fontsize=8); a.set_ylabel(yl, fontsize=8); a.grid(alpha=0.3, axis="y"); a.tick_params(labelsize=7)
        a.set_xlabel("option (POWER_FIX.md table)", fontsize=8)
    axs[1].set_ylim(2, 7.6); axs[0].legend(fontsize=7, loc="upper right", ncol=2)
    fig.suptitle("Ankle supply per option, walk with the backlash model, worse of trained mass and our build (ngspice, sim pass only)", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "power_fix_options.png"), dpi=80); plt.close(fig)
    # voltage traces: baseline, 3b, 6+3b at nominal pack, high-side corner (our build), right ankle
    fig, ax = plt.subplots(1, 1, figsize=(10, 3.4))
    for on, c in (("1", "#c0392b"), ("3", "#e67e22"), ("3b", "#4a6fa5"), ("6", "#7d3c98"), ("6+3b", "#1e8449")):
        f = os.path.join(OUT, vtag(on, "our", "nominal", "high-side") + ".npz")
        if not os.path.exists(f): continue
        d = np.load(f); i = list(d["names"]).index("right_ankle"); sel = d["t"] <= 3.0
        ax.plot(d["t"][sel], d["V"][i][sel], lw=0.7, color=c, label=f"{on}: {OPTIONS[on]['desc']}")
    ax.axhline(6.0, color="k", lw=0.8, ls="--"); ax.axhline(4.5, color="k", lw=0.6, ls=":")
    ax.set_xlabel("time in the window (s)", fontsize=8); ax.set_ylabel("right ankle supply (V)", fontsize=8); ax.grid(alpha=0.3); ax.tick_params(labelsize=7)
    ax.legend(fontsize=7, loc="lower right", ncol=2)
    ax.set_title("Right ankle, nominal pack, high-side corner, our build, first 3 s of the window (ngspice, sim pass only)", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "power_fix_ankle_trace.png"), dpi=80); plt.close(fig)
    if cos:
        fig, axs = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw=dict(width_ratios=[1, 1.25]))
        fx = [r for r in cos if r["kind"] == "fixed bus"]; nseed = len({r["seed"] for r in fx})
        ref = {}
        for case, c in (("walk_forward_0.15", "#4a6fa5"), ("walk_backlash", "#c0392b"), ("turn_1.0", "#1e8449")):
            vs = sorted({r["V_bus"] for r in fx})
            tr = [np.mean([(r["track_lin"] if r["track_lin"] is not None else r["track_yaw"]) for r in fx if r["V_bus"] == v and r["case"] == case and not r["falls"]] or [np.nan]) for v in vs]
            nf = [sum(1 for r in fx if r["V_bus"] == v and r["case"] == case and r["falls"]) for v in vs]
            ref[case] = tr[vs.index(7.4)]
            axs[0].plot(vs, tr, "o-", color=c, ms=3, lw=1, label=case)
            for v, n in zip(vs, nf):
                if n: axs[0].plot(v, 0.02, "x", color=c, ms=7); axs[0].text(v + 0.08, 0.05, f"{n}/{nseed} fell", color=c, fontsize=6, ha="right")
        axs[0].set_xlabel("bus voltage at every servo (V)", fontsize=8); axs[0].set_ylabel("speed tracking (measured / command)", fontsize=8)
        axs[0].axvline(6.0, color="k", lw=0.6, ls="--"); axs[0].invert_xaxis(); axs[0].legend(fontsize=7); axs[0].grid(alpha=0.3); axs[0].tick_params(labelsize=7)
        axs[0].set_title("fixed bus voltage", fontsize=8)
        cs = [r for r in cos if r["kind"] == "co-simulated" and r["pack"] == "nominal"]
        groups = [(o, cn) for o in ("1", "3", "3b", "6+3b") for cn in ("typical", "high-side")]
        x = np.arange(len(groups)); wdt = 0.38
        for j, (case, c) in enumerate((("walk_forward_0.15", "#4a6fa5"), ("walk_backlash", "#c0392b"))):
            y = [np.mean([r["track_lin"] for r in cs if r["option"] == o and r["corner"] == cn and r["case"] == case and not r["falls"]] or [np.nan]) for o, cn in groups]
            a6 = [np.mean([r["ankle_pct_below_6V"] for r in cs if r["option"] == o and r["corner"] == cn and r["case"] == case] or [np.nan]) for o, cn in groups]
            axs[1].bar(x + (j - 0.5) * wdt, y, wdt, color=c, label=f"{case} (line: same walk at 7.4 V)")
            axs[1].hlines(ref[case], -0.5, len(groups) - 0.5, color=c, lw=0.8, ls="--")
            for xi, yi, ai in zip(x, y, a6):
                axs[1].text(xi + (j - 0.5) * wdt, yi + 0.01, f"{ai:.0f}%", fontsize=5.5, ha="center", color=c)
        axs[1].set_xticks(x); axs[1].set_xticklabels([f"{o}\n{cn}" for o, cn in groups], fontsize=7)
        axs[1].set_ylabel("speed tracking (measured / command)", fontsize=8); axs[1].set_ylim(0, 1.0); axs[1].grid(alpha=0.3, axis="y"); axs[1].tick_params(labelsize=7)
        axs[1].legend(fontsize=6.5, loc="upper left"); axs[1].set_title("co-simulated power path, nominal pack (numbers: ankle time under 6.0 V)", fontsize=8)
        fig.suptitle("Our 2.77 kg build, stock policy, servo gain and torque limit scale with the bus voltage (MuJoCo + power path, sim pass only)", fontsize=9)
        fig.tight_layout(); fig.savefig(os.path.join(HERE, "power_fix_voltage_walk.png"), dpi=80); plt.close(fig)

def bay_check():
    """option 6: can a 3S pack go where the 2S holder is? Ray casts from the holder.stl box (upstream CAD, zero pose,
    trunk frame) outward in +-x, +-y, +-z against every other part, then tests 3S layouts in that free box."""
    import itertools, trimesh, yourdfpy
    R = os.path.join(HERE, "../../mini_bdx/robots/open_duck_mini_v2/")
    u = yourdfpy.URDF.load(os.path.join(R, "robot.urdf"), load_meshes=False, build_scene_graph=True)
    u.update_cfg({n: 0.0 for n in u.actuated_joint_names})
    Tl0 = u.get_transform("trunk_assembly").copy(); Tl0[:3, 3] *= 1000.0; Ti = np.linalg.inv(Tl0)
    hold, others = None, []
    for ln, link in u.link_map.items():
        Tl = u.get_transform(ln)
        for v in link.visuals:
            fn = os.path.basename(v.geometry.mesh.filename)
            T = Tl @ (v.origin if v.origin is not None else np.eye(4)); T = T.copy(); T[:3, 3] *= 1000.0
            m = trimesh.load(os.path.join(R, fn), force="mesh"); m.apply_scale(1000.0); m.apply_transform(Ti @ T)
            if fn == "holder.stl": hold = m
            else: others.append(m)
    lo, hi = hold.bounds
    inter = trimesh.ray.ray_triangle.RayMeshIntersector(trimesh.util.concatenate(others))
    free = {}
    for ax in range(3):
        for sgn in (-1, 1):
            oa = [a for a in range(3) if a != ax]
            P0 = []
            for p_, q_ in itertools.product(*[np.linspace(lo[a] + 1.0, hi[a] - 1.0, 13) for a in oa]):
                pt = np.zeros(3); pt[oa[0]] = p_; pt[oa[1]] = q_; pt[ax] = (hi[ax] if sgn > 0 else lo[ax]) - sgn * 2.0; P0.append(pt)
            P0 = np.array(P0); D = np.zeros_like(P0); D[:, ax] = sgn
            locs, idx, _ = inter.intersects_location(P0, D, multiple_hits=True)
            dist = np.full(len(P0), np.inf)
            for Lc, i in zip(locs, idx):
                d = (Lc[ax] - P0[i, ax]) * sgn - 2.0
                if d > -1.9: dist[i] = min(dist[i], d)
            free[("-+"[sgn > 0]) + "xyz"[ax]] = dict(min_mm=round(float(dist.min()), 2), median_mm=round(float(np.median(dist)), 2))
    env = [round(float(hi[a] - lo[a] + max(free["+" + "xyz"[a]]["min_mm"], 0) + max(free["-" + "xyz"[a]]["min_mm"], 0)), 1) for a in range(3)]
    cands = {"3 x 18650 side by side (holder about 77 x 60 x 21 mm)": [77, 60, 21], "3 x 18650 in a triangle (about 70 x 39 x 36 mm)": [70, 39, 36],
             "3 x 18650 end to end (about 200 x 19 x 19 mm)": [200, 19, 19], "3S pouch pack 76 x 41 x 20 mm (the whole free box)": env}
    fits = {k: any(np.all(np.array(pp) <= np.array(env) + 1e-6) for pp in itertools.permutations(d)) for k, d in cands.items()}
    return dict(holder_box_mm=dict(lo=lo.round(2).tolist(), hi=hi.round(2).tolist(), size=(hi - lo).round(2).tolist()), free_from_holder_faces=free,
                free_box_mm=env, candidates={k: dict(dims_mm=cands[k], fits=bool(v)) for k, v in fits.items()})

def switch_seat_check():
    """coordinator item: a second Pololu 2815 in parallel needs a seat. Ray casts from the 2815 seat box
    (audit/placements.json) outward over the CAD parts at the zero pose and the hip yaw, hip roll and neck pitch limits
    (the poses of audit/free_space.py), plus the other lab part boxes; returns the free distance per direction."""
    import itertools, trimesh, yourdfpy
    R = os.path.join(HERE, "../../mini_bdx/robots/open_duck_mini_v2/")
    pl = {q["id"]: q for q in json.load(open(os.path.join(HERE, "../audit/placements.json")))}
    u = yourdfpy.URDF.load(os.path.join(R, "robot.urdf"), load_meshes=False, build_scene_graph=True)
    lim = {j.name: (j.limit.lower, j.limit.upper) for j in u.robot.joints if j.type == "revolute"}
    cache = {}
    def scene(cfg):
        u.update_cfg(cfg); Tl0 = u.get_transform("trunk_assembly").copy(); Tl0[:3, 3] *= 1000.0; Ti = np.linalg.inv(Tl0); ms = []
        for ln, link in u.link_map.items():
            Tl = u.get_transform(ln)
            for v in link.visuals:
                fn = os.path.basename(v.geometry.mesh.filename)
                if fn not in cache:
                    m = trimesh.load(os.path.join(R, fn), force="mesh"); m.apply_scale(1000.0); cache[fn] = m
                T = Tl @ (v.origin if v.origin is not None else np.eye(4)); T = T.copy(); T[:3, 3] *= 1000.0
                m = cache[fn].copy(); m.apply_transform(Ti @ T); ms.append(m)
        return trimesh.util.concatenate(ms)
    base = {n: 0.0 for n in u.actuated_joint_names}
    cfgs = [base] + [dict(base, **{j: q}) for j in ("left_hip_yaw", "right_hip_yaw", "left_hip_roll", "right_hip_roll", "neck_pitch") for q in lim[j]]
    sw = pl["mosfet_switch"]; c = np.array(sw["center_mm"]); d = np.array(sw["dims_xyz_mm"]); lo, hi = c - d / 2, c + d / 2
    others = [pl[k] for k in pl if k != "mosfet_switch"]; free = {}
    for cfg in cfgs:
        inter = trimesh.ray.ray_triangle.RayMeshIntersector(scene(cfg))
        for ax in range(3):
            for sgn in (-1, 1):
                oa = [a for a in range(3) if a != ax]; P0 = []
                for a_, b_ in itertools.product(*[np.linspace(lo[a] + 0.5, hi[a] - 0.5, 9) for a in oa]):
                    pt = np.zeros(3); pt[oa[0]] = a_; pt[oa[1]] = b_; pt[ax] = hi[ax] if sgn > 0 else lo[ax]; P0.append(pt)
                P0 = np.array(P0); D = np.zeros_like(P0); D[:, ax] = sgn
                locs, idx, _ = inter.intersects_location(P0, D, multiple_hits=False)
                dist = np.full(len(P0), np.inf)
                for Lc, i in zip(locs, idx): dist[i] = min(dist[i], (Lc[ax] - P0[i, ax]) * sgn)
                for q in others:
                    qc = np.array(q["center_mm"]); qd = np.array(q.get("box_with_margin_mm", q["dims_xyz_mm"])); qlo, qhi = qc - qd / 2, qc + qd / 2
                    for i, pt in enumerate(P0):
                        if all(qlo[a] <= pt[a] <= qhi[a] for a in oa):
                            t_ = (qlo[ax] - pt[ax]) if sgn > 0 else (pt[ax] - qhi[ax])
                            if t_ >= 0: dist[i] = min(dist[i], t_)
                k = ("-+"[sgn > 0]) + "xyz"[ax]; free[k] = round(min(free.get(k, np.inf), float(dist.min())), 1)
    return dict(seat_box_mm=dict(lo=lo.round(1).tolist(), hi=hi.round(1).tolist()), free_mm=free, poses=len(cfgs),
                second_board_below_fits=bool(free["-z"] >= d[2] + 1.0), second_board_stacked_fits=bool(free["+x"] >= d[0] + 1.5))

def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "run"
    J = lambda n: os.path.join(OUT, f"power_fix_{n}.json")
    R = {k: json.load(open(J(k))) for k in ("run", "extra", "sweep", "sweep2", "check", "cosim", "rows", "dgnd", "bay") if os.path.exists(J(k))}
    if what in ("bay", "all"):
        R["bay"] = bay_check(); print(json.dumps(R["bay"], indent=1)); json.dump(R["bay"], open(J("bay"), "w"), indent=1)
    if what in ("seat", "all"):
        R["seat"] = switch_seat_check(); print(json.dumps(R["seat"])); json.dump(R["seat"], open(J("seat"), "w"), indent=1)
    meta = dict(inj_knee_mm=INJ_KNEE_MM, inj_ankle_mm=INJ_ANKLE_MM, inj_knee_rule_mm=INJ_KNEE_RULE, inj_ankle_rule_mm=INJ_ANKLE_RULE,
                hop_cut_mm=HOP_CUT, sp_mm=SP_MM, p11_mm=P11_MM, params=P, typical=TYP, window=WINDOW)
    if what in ("run", "all"):
        R["run"] = run_all(); json.dump(dict(meta=meta, rows=R["run"], summary=summary_table(R["run"])), open(J("run"), "w"), indent=1)
    if what in ("extra", "all"):
        R["extra"] = run_extra(); json.dump(R["extra"], open(J("extra"), "w"), indent=1)
    if what in ("sweep", "all"):
        R["sweep"] = hop_sweep(); json.dump(R["sweep"], open(J("sweep"), "w"), indent=1)
    if what in ("check", "all"):
        R["check"] = dict(builder=check_builder(), solver=[check_solver("1", "high-side"), check_solver("3b", "typical"), check_solver("6+3b", "high-side", "low")])
        print(R["check"]); json.dump(R["check"], open(J("check"), "w"), indent=1)
    if what in ("cosim", "all"):
        R["cosim"] = run_cosim(); json.dump(R["cosim"], open(J("cosim"), "w"), indent=1, default=float)
    if what in ("traces", "all"):
        save_traces()
    if what in ("rows", "all"):
        R["rows"] = star_rows(); json.dump(R["rows"], open(J("rows"), "w"), indent=1)
    if what in ("dgnd", "all"):
        R["dgnd"] = data_ground_study(); json.dump(R["dgnd"], open(J("dgnd"), "w"), indent=1)
    if what in ("sweep2", "all"):
        R["sweep2"] = hop_sweep2(); json.dump(R["sweep2"], open(J("sweep2"), "w"), indent=1)
    if what in ("png", "all"):
        rows = R["run"]["rows"] if isinstance(R.get("run"), dict) else R.get("run", [])
        plots(rows, R.get("cosim"))
    print("wrote", OUT)

if __name__ == "__main__":
    main()
