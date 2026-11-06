"""Power path circuit simulation with ngspice (sim pass only).

Builds a SPICE netlist of the whole power path, from the cells to every servo, and drives each of the 14 servos with
its own power trace from the MuJoCo walk (sim/current_budget.py with ODM_SAVE_TRACES=1). Every series resistance is a
parameter below with its source; values that are not published are marked ASSUMPTION and chosen on the high side.

Topologies (over=dict(topology=...)):
  "as_built"      the robot as it is wired now, and the case verify/e6_power_path.py checks: D15 star (BEC -> P11 ->
                  belly splices SPV/SPG -> SP1, SP2, SP3 -> first servo of each chain) plus the D23 second feeds SP4 and
                  SP5 into BUS 1 of the ankle servos, with the data-lead grounds SD1/SD2 and the USB ground as wired.
                  Every length and gauge comes from wiring/netlist.yaml at run time (netlist_lengths() below). The
                  network is sim/power_fix.py option 3b (its option "ab" runs it with the netlist values), so there is
                  one model of the D23 wiring, not two. Resistances that the netlist does not give (contacts, cells,
                  holder, BMS, fuse, switch, BEC, kit cable gauge) are the parameters P below and the two corners.
  "star"          D15 as modelled when it was decided (SP leads 20 AWG, P11 200 mm, no second feeds, pack side
                  lengths L). Kept for history: it reproduces the D15 number (worst ankle 5.04 V, typical, nominal).
  "y_at_adapter"  D14 (superseded), "tnkr" the Tnkr wiring (superseded). Kept for history.

Topology of the earlier models (cable ids from CABLE_MAP.md):
  2 cells (OCV + R each) -> holder contacts -> BMS (R on the low side) -> P6 -> XT30 -> P7 + 15 A ATO fuse
  -> Pololu 2815 (R_on) -> switched bus node -> P10 -> Castle CC BEC Pro (behavioral: 7.2 V or Vin - dropout)
  -> two 3-pin output leads in parallel -> P11 -> adapter H1 -> adapter board -> H3 / H5
  H3 -> S1 -> ID20 -> S2 -> ID21 -> S3 -> ID22 -> S4 -> ID23 -> S5 -> ID24 -> S14 -> ID30 -> S11 -> ID31 -> S12 -> ID32 -> S13 -> ID33
  H5 -> S6 -> ID10 -> S7 -> ID11 -> S8 -> ID12 -> S9 -> ID13 -> S10 -> ID14
  switched bus -> P13 (20 AWG through the neck) -> 5 V regulator in the head (behavioral, constant output power)
  Returns are modelled with the same resistances as the supply side (separate ground conductors).

Each servo is a constant-power load P_i(t) = max(u_i * I_i, 0) from the BAM motor model (same as current_budget.py,
kt = 1.148, the highest-current value) plus a quiescent current. Constant power means the current rises when the
local voltage falls, which is the conservative choice for voltage drop.
Usage: ODM_TRACES=<folder with trace_*.npz> ODM_OUT=<folder> python3 sim/power_path_sim.py
  ODM_TOPOS   comma list of topologies (default as_built; tnkr,y_at_adapter,star re-run the history rows)
  ODM_PACKS   comma list of full, nominal, low (default all three)
  ODM_FALL    1 (default) adds the fall after a push (trace_walk_pushes.npz 9.5 to 12.5 s, low pack, high-side);
              0 leaves it out (use 0 for a trace whose push run does not fall)
  ODM_SAVE_V  1 keeps each case's servo voltages as v_<label>.npz in ODM_OUT (sim/plot_power_path.py reads them)
"""
import os, sys, json, subprocess, tempfile, hashlib, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NETLIST = os.path.join(HERE, "..", "wiring", "netlist.yaml")
TR = os.environ.get("ODM_TRACES", "/tmp/odm_traces")
OUT = os.environ.get("ODM_OUT", "/tmp/odm_power_sim"); os.makedirs(OUT, exist_ok=True)
VIN_MODEL = 7.4; KT = 1.148; KT_OVER_R = 3.23 / 7.4

CU = {16: 13.17e-3, 20: 33.31e-3, 22: 52.96e-3, 24: 84.22e-3, 26: 133.9e-3}   # ohm/m, annealed copper at 20 C (AWG table)
P = dict(
    R_cell=0.020,        # ohm per cell, ASSUMPTION (Molicel P30B DC resistance not read in this session; high side)
    R_holder=0.030,      # ohm total spring contacts, ASSUMPTION = the bench pass limit (0.3 V at 10 A, POWER.md)
    R_bms=0.025,         # ohm, Tenergy 32175 "Main loop electrify resistance RSS<=25mOhm" (Tenergy page)
    R_xt30=0.001,        # ohm per contact, ASSUMPTION
    R_fuse=0.006,        # ohm, ASSUMPTION for a 15 A ATO blade cold resistance
    R_sw=0.013,          # ohm, Pololu 2815 combined MOSFET resistance max at 4.5 V gate (Pololu table); 8.6 mOhm at 10 V
    BEC_V=7.2, BEC_DROP=0.3, BEC_EFF=0.85,   # setpoint (D3); dropout and efficiency ASSUMPTION (not published by Castle)
    R_bec_lead=0.5 * CU[22] * 0.10,          # two output leads in parallel, ASSUMPTION 22 AWG x 100 mm each
    R_adapter=0.010,     # ohm, ASSUMPTION adapter board H1 to H3/H5 copper plus socket
    R_contact=0.020,     # ohm per Mini-SPOX/5264 contact, ASSUMPTION (high side)
    R_servo_pcb=0.005,   # ohm, ASSUMPTION servo board pass-through between its 2 bus ports
    kit_awg=26,          # ASSUMPTION: STS3215 kit cable conductor size not published, smallest plausible
    I_q=0.05,            # A per servo quiescent, ASSUMPTION (run again with 0.15 as the upper bound)
    P_5V=5.0, REG_EFF=0.85,                   # W at 5 V, average with margin (typical 3 W, peak 12 W per CABLE_MAP P13); efficiency ASSUMPTION
    topology="tnkr",     # "tnkr": neck chain off the left ankle via S14; "y_at_adapter": neck chain on its own lead from the adapter;
                         # "star": D15 as modelled at the decision (20 AWG SP leads, P11 200 mm; history);
                         # "as_built": D15 + D23 with every length and gauge from wiring/netlist.yaml (the checked case)
)
def wire(awg, mm): return CU[awg] * mm / 1000.0
# pack side lengths of the earlier models (CABLE_MAP, MOUNTING at the time). The as_built topology does not use them:
# it reads every length from wiring/netlist.yaml (netlist_lengths()).
L = dict(P1=120, P2=120, P6=80, P7=90 + 90, P8=170, P9=140, P10=150, P11=140, P13=550, S14=490, kit=150)   # mm (CABLE_MAP, MOUNTING)

CHAIN_L = ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle"]   # H3 side
CHAIN_N = ["neck_pitch", "head_pitch", "head_yaw", "head_roll"]                            # neck chain
CHAIN_R = ["right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]   # H5 side
# servo IDs in chain order (netlist components SV20..SV33, Runtime HWI map; verify/c5_servo_ids.py checks the chains)
CHAIN_IDS = {"L": [20, 21, 22, 23, 24], "N": [30, 31, 32, 33], "R": [10, 11, 12, 13, 14]}
CHAIN_NAMES = {"L": CHAIN_L, "N": CHAIN_N, "R": CHAIN_R}


def netlist_lengths(path=None):
    """Every conductor of the servo power path as wiring/netlist.yaml builds it: (AWG, cut mm) per piece.
    Active cables only, looked up by their end pins, so a changed cut length is picked up and a changed topology
    (renamed splice, removed cable) stops the run with the reason. Solder splices are taken as 0 ohm."""
    import yaml
    path = os.path.abspath(path or NETLIST)
    raw = open(path, "rb").read()
    net = yaml.safe_load(raw.decode("utf-8"))
    act = {c["id"] for c in net["cables"] if c.get("status") == "active"}
    W = [w for w in net["wires"] if w["cable"] in act]
    used = []

    def awg(g):
        g = str(g)
        if "AWG" in g:
            return int(g.split("AWG")[0].strip().split()[-1])
        return g                                   # "kit cable", "BEC lead": not a published gauge

    def one(cable, frm, to):
        rows = [w for w in W if w["cable"] == cable and w["from"] == frm and w["to"] == to]
        if len(rows) != 1:
            raise ValueError("netlist.yaml: %d active wires %s %s -> %s (the as_built model expects 1)" % (len(rows), cable, frm, to))
        w = rows[0]
        used.append(dict(cable=cable, frm=frm, to=to, gauge=w["gauge"], cut_mm=w["cut_mm"]))
        return (awg(w["gauge"]), float(w["cut_mm"])) if w["cut_mm"] is not None else (awg(w["gauge"]), None)

    def any_cable(frm, to):
        rows = [w for w in W if w["from"] == frm and w["to"] == to]
        if len(rows) != 1:
            raise ValueError("netlist.yaml: %d active wires %s -> %s (the as_built model expects 1)" % (len(rows), frm, to))
        return rows[0]["cable"]

    d = {}
    d["P1"] = one("P1", "PACK.B+", "BMS.B+")
    d["P2"] = one("P2", "PACK.B-", "BMS.B-")
    d["P6"] = one("P6", "BMS.P+", "XT30.F+")
    d["P8"] = one("P8", "BMS.P-", "XT30.F-")
    # P7: XT30 male + -> JFI -> fuse holder line lead; fuse holder load lead -> JFO -> 2815 VIN (four pieces in series)
    if any(w["cable"] == "P7" and w["to"] == "DK7.VIN" for w in W):
        # D50: the fused pack reaches the 2813 through the DK7 ideal diode (Pololu 5383): P7 to DK7 VIN, then the 16 AWG
        # DC4 piece DK7 VOUT to SW1 VIN; the diode's own on-resistance is not in this model (not read: BLOCKER, it adds)
        d["P7"] = [one("P7", "XT30.M+", "JFI.S"), one("P7", "JFI.S", "F1.IN"), one("P7", "F1.OUT", "JFO.S"), one("P7", "JFO.S", "DK7.VIN"),
                   one("DC4", "DK7.VOUT", "SW1.VIN")]
    else:
        d["P7"] = [one("P7", "XT30.M+", "JFI.S"), one("P7", "JFI.S", "F1.IN"), one("P7", "F1.OUT", "JFO.S"), one("P7", "JFO.S", "SW1.VIN")]
    d["P14"] = one("P14", "XT30.M-", "G.S")
    # D43, D50: the dock charge input DC1 (chest CHG+ strip -> DK2 ideal diode -> F2 5 A fuse -> BMS P+). It joins the pack
    # side at BMS P+; off the dock DK2 blocks it (only the 100 k across DK2 joins the strip to the pack), so it carries no
    # walking current, but it is in the model so a changed charge path is read from the netlist like every other cable
    if any(w["cable"] == "DC1" for w in W):
        d["DC1"] = [one("DC1", "DKP.CHG", "DK2.VIN"), one("DC1", "DK2.VOUT", "F2.IN"), one("DC1", "F2.OUT", "BMS.P+")]
    d["P9"] = one("P9", "SW1.VOUT", "VSW.S")
    d["P10p"] = one("P10", "VSW.S", "U1.IN+"); d["P10n"] = one("P10", "G.S", "U1.IN-")
    d["P13p"] = one("P13", "VSW.S", "U3.VIN"); d["P13n"] = one("P13", "G.S", "U3.GND.1")
    d["P12n"] = one("P12", "U3.GND.2", "PI.6")
    d["P11p"] = one("P11", "JBP.S", "SPV.S"); d["P11n"] = one("P11", "JBN.S", "SPG.S")
    d["bec_leads"] = [one("P11", "U1.OUT%d%s" % (k, s), "JB%s.S" % ("P" if s == "+" else "N")) for k in (1, 2) for s in "+-"]
    first = {"L": "SP1", "R": "SP2", "N": "SP3"}
    jg = {"L": "JG20", "R": "JG10", "N": "JG30"}
    d["sp_v"], d["sp_g"], d["sp_tail"], d["hop_mm"], d["hop_cable"] = {}, {}, {}, {}, {}
    for side, ids in CHAIN_IDS.items():
        c, s0 = first[side], ids[0]
        d["sp_v"][side] = one(c, "SPV.S", "SV%d.BUS2.V" % s0)
        d["sp_g"][side] = one(c, "SPG.S", "%s.S" % jg[side])
        d["sp_tail"][side] = one(c, "%s.S" % jg[side], "SV%d.BUS2.G" % s0)
        hm, hc = [], []
        for a, b in zip(ids[:-1], ids[1:]):          # kit hop from servo a BUS 1 to servo b BUS 2 (V conductor)
            cab = any_cable("SV%d.BUS1.V" % a, "SV%d.BUS2.V" % b)
            g, mm = one(cab, "SV%d.BUS1.V" % a, "SV%d.BUS2.V" % b)
            one(cab, "SV%d.BUS1.G" % a, "SV%d.BUS2.G" % b)
            hm.append(mm); hc.append(cab)
        d["hop_mm"][side], d["hop_cable"][side] = hm, hc
    # second feeds (D23): any active wire from SPV.S into a servo port other than the first servo's BUS 2
    d["feeds"] = {}
    for w in W:
        if w["from"] == "SPV.S" and w["to"].startswith("SV") and w["to"].endswith(".V") and w["cable"] not in first.values():
            sid = int(w["to"][2:4]); side = [k for k, v in CHAIN_IDS.items() if sid in v]
            if not side:
                raise ValueError("netlist.yaml: feed %s goes to %s, not a chain servo" % (w["cable"], w["to"]))
            side = side[0]
            if side in d["feeds"]:
                raise ValueError("netlist.yaml: two second feeds on chain %s (the as_built model takes one per chain)" % side)
            port = w["to"].split(".")[1]
            d["feeds"][side] = dict(cable=w["cable"], servo=CHAIN_NAMES[side][CHAIN_IDS[side].index(sid)], servo_id=sid, port=port,
                                    v=one(w["cable"], "SPV.S", w["to"]), g=one(w["cable"], "SPG.S", w["to"][:-2] + ".G"))
    # D15 data-lead grounds: SD1 stem from adapter H3 G to YG3, branch a to JG20, branch b to JG30; SD2 G from H5 G to JG10
    d["sd"] = dict(stem=one("SD1", "U2.H3.G", "YG3.S"), a=one("SD1", "YG3.S", "JG20.S"), b=one("SD1", "YG3.S", "JG30.S"),
                   sd2=one("SD2", "U2.H5.G", "JG10.S"))
    # edge names of sim/power_fix.py servo_net() -> netlist cable ids
    cab = {"lead": "P11", "sp_L": "SP1", "sp_R": "SP2", "sp_N": "SP3"}
    for side, names in CHAIN_NAMES.items():
        for nm, c in zip(names[1:], d["hop_cable"][side]):
            cab["hop_" + nm] = c
        if side in d["feeds"]:
            cab["inj_" + side] = d["feeds"][side]["cable"]
    d["cable_of"] = cab
    d["used"] = used
    d["source"] = dict(path=os.path.relpath(path, os.path.join(HERE, "..", "..")), sha256_10=hashlib.sha256(raw).hexdigest()[:10],
                       mtime_utc=time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(os.path.getmtime(path))))
    for k in ("P1", "P2", "P6", "P8", "P14", "P9", "P10p", "P10n", "P13p", "P13n", "P12n", "P11p", "P11n"):
        if d[k][1] is None or not isinstance(d[k][0], int):
            raise ValueError("netlist.yaml: %s has no gauge or cut length (%s)" % (k, d[k]))
    return d


def summary_lengths(d):
    """short text of the netlist values the as_built model used"""
    f = lambda x: "%s %s mm" % (("%d AWG" % x[0]) if isinstance(x[0], int) else x[0], ("%g" % x[1]) if x[1] is not None else "as shipped")   # noqa: E731
    s = ["P1 %s" % f(d["P1"]), "P2 %s" % f(d["P2"]), "P6 %s" % f(d["P6"]), "P7 %d AWG %g mm (%s)" % (
        d["P7"][0][0], sum(x[1] for x in d["P7"]), " + ".join("%g" % x[1] for x in d["P7"])), "P8 %s" % f(d["P8"]),
         "P14 %s" % f(d["P14"]), "P9 %s" % f(d["P9"]), "P10 %s" % f(d["P10p"]), "P11 %s plus the BEC leads (as shipped)" % f(d["P11p"]),
         "P13 %s" % f(d["P13p"])]
    for side, c in (("L", "SP1"), ("R", "SP2"), ("N", "SP3")):
        s.append("%s V %s, G %s + tail %s" % (c, f(d["sp_v"][side]), f(d["sp_g"][side]), f(d["sp_tail"][side])))
    for side, fd in sorted(d["feeds"].items()):
        s.append("%s to %s %s: V %s, G %s" % (fd["cable"], fd["servo"].replace("_", " "), fd["port"], f(fd["v"]), f(fd["g"])))
    s.append("kit hops %s mm" % ", ".join("%s %g" % (c, mm) for side in ("L", "R", "N") for c, mm in zip(d["hop_cable"][side], d["hop_mm"][side])))
    s.append("SD1 G stem %s, a %s, b %s; SD2 G %s" % (f(d["sd"]["stem"]), f(d["sd"]["a"]), f(d["sd"]["b"]), f(d["sd"]["sd2"])))
    return "; ".join(s)


def _power_fix():
    """sim/power_fix.py, imported on first use: it imports this file, and its option "ab" is the as_built network."""
    me = sys.modules.get(__name__)
    if me is not None:
        sys.modules.setdefault("power_path_sim", me)    # so power_fix binds to this module, not a second copy
    os.environ.setdefault("ODM_OUT", OUT)
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import power_fix
    return power_fix

def servo_power(npz, t0, t1):
    """returns per-servo (commanded motor voltage u_cmd, joint speed w) from the MuJoCo trace"""
    d = np.load(npz); F, W, dt = d["F"], d["W"], float(d["dt"]); names = list(d["names"])
    R = KT / KT_OVER_R
    u = np.clip(F * R / KT, -VIN_MODEL, VIN_MODEL)
    k0, k1 = int(t0 / dt), int(t1 / dt)
    return {n: (u[k0:k1, i], W[k0:k1, i]) for i, n in enumerate(names)}, dt

def build(pw, dt, vcell, pq, over=None):
    if (over or {}).get("topology") == "as_built":
        # D15 + D23 as wired: sim/power_fix.py option "ab" (its option 3b network with the netlist lengths and gauges)
        PF = _power_fix()
        p = PF.params("high-side", PF.OPTIONS["ab"], dict(over, I_q=pq))   # "high-side" = P itself; over carries a corner
        cir, pr, nodes, _ = PF.netlist(pw, dt, vcell, PF.OPTIONS["ab"], p)
        return cir, pr, nodes, p
    p = dict(P); p["I_q"] = pq; p.update(over or {})
    n = len(next(iter(pw.values()))[0]); t = np.arange(n) * dt
    RM = KT / KT_OVER_R
    hop = wire(p["kit_awg"], L["kit"]) + 2 * p["R_contact"] + p["R_servo_pcb"]
    hop14 = wire(22, L["S14"]) + 2 * p["R_contact"]
    hopY = wire(22, 200) + 3 * p["R_contact"]     # Y-lead variant: 200 mm made lead from the adapter, one extra crimp at the Y
    lines = ["* Open Duck Mini v2 power path (generated by sim/power_path_sim.py)",
             f"Vc1 c1 0 {vcell}", f"Rc1 c1 c1r {p['R_cell']}", f"Vc2 c2 c1r {vcell}", f"Rc2 c2 bplus {p['R_cell']}",
             f"Rhp bplus hp {p['R_holder']/2}", f"Rhn 0 hn {p['R_holder']/2}",
             f"Rp1 hp pp {wire(16, L['P1'])}", f"Rp2 hn bm {wire(16, L['P2'])}", f"Rbms bm pm {p['R_bms']}",
             f"Rp6 pp x1 {wire(16, L['P6']) + p['R_xt30']}", f"Rp7 x1 swin {wire(16, L['P7']) + p['R_fuse']}",
             f"Rsw swin bus {p['R_sw']}", f"Rp8 pm busn {wire(16, L['P8']) + p['R_xt30']}",
             f"Rp10p bus becip {wire(16, L['P10'])}", f"Rp10n busn becin {wire(16, L['P10'])}",
             # BEC: output = min(setpoint, Vin - drop), input current = Pout / (eff * Vin)
             f"Ebec beco becon value={{min({p['BEC_V']}, max(V(becip,becin) - {p['BEC_DROP']}, 0))}}",
             "Rbecon becon becin 1e-6",
             "Vbecs beco beco2 0",
             f"Bbecin becip becin I={{ V(beco,becon) * I(Vbecs) / ({p['BEC_EFF']} * max(V(becip,becin), 1)) }}",
             f"Rlp beco2 h1p {p['R_bec_lead'] + wire(16, L['P11'])}", f"Rln becon h1n {p['R_bec_lead'] + wire(16, L['P11'])}",
             f"Rh3p h1p a3p {p['R_adapter']}", f"Rh3n h1n a3n {p['R_adapter']}",
             f"Rh5p h1p a5p {p['R_adapter']}", f"Rh5n h1n a5n {p['R_adapter']}",
             # 5 V branch: P13 through the neck to the regulator in the head
             f"Rp13p bus regp {wire(20, L['P13'])}", f"Rp13n busn regn {wire(20, L['P13'])}",
             f"Breg regp regn I={{ {p['P_5V']} / ({p['REG_EFF']} * max(V(regp,regn), 1)) }}"]
    nodes = {}
    def chain(names, start_p, start_n, tag, first=None):
        prev_p, prev_n = start_p, start_n
        for k, nm in enumerate(names):
            r = first if (k == 0 and first is not None) else hop
            sp, sn = f"s{tag}{k}p", f"s{tag}{k}n"
            lines.append(f"R{tag}{k}p {prev_p} {sp} {r}"); lines.append(f"R{tag}{k}n {prev_n} {sn} {r}")
            uc, ww = pw[nm]
            lines.append(f"Vu_{nm} u_{nm} 0 PWL(" + " ".join(f"{tt:.4f} {vv:.4f}" for tt, vv in zip(t, uc)) + ")")
            lines.append(f"Vw_{nm} w_{nm} 0 PWL(" + " ".join(f"{tt:.4f} {vv:.4f}" for tt, vv in zip(t, ww)) + ")")
            # voltage-limited H-bridge: applied voltage capped at the local bus; supply current = u*I/Vbus, no regen credit
            vl = f"max(V({sp},{sn}),0.5)"
            ue = f"min(max(V(u_{nm}),-{vl}),{vl})"
            lines.append(f"B_{nm} {sp} {sn} I={{ max({ue}*({ue}-{KT}*V(w_{nm}))/{RM:.5f},0)/{vl} + {p['I_q']} }}")
            nodes[nm] = (sp, sn); prev_p, prev_n = sp, sn
    if p["topology"] == "star":
        # D15 as modelled at the decision (history): the BEC leads and 140 mm of P11 to "h1", then 60 mm of 16 AWG to
        # the splice; branches 20 AWG, 150 mm to each hip yaw servo, 180 mm to neck pitch, 1 contact each. The netlist
        # builds the SP leads in 22 AWG and adds SP4/SP5: that wiring is topology "as_built", not this one.
        lines.append(f"Rspp h1p spp {wire(16, 60) - (p['R_bec_lead'] + wire(16, L['P11'])) * 0 + 0}")
        lines.append(f"Rspn h1n spn {wire(16, 60)}")
        bL = wire(20, 150) + p["R_contact"]; bN = wire(20, 180) + p["R_contact"]
        chain(CHAIN_L, "spp", "spn", "L", first=bL); chain(CHAIN_R, "spp", "spn", "R", first=bL)
        chain(CHAIN_N, "spp", "spn", "N", first=bN)
    else:
        chain(CHAIN_L, "a3p", "a3n", "L"); chain(CHAIN_R, "a5p", "a5n", "R")
    if p["topology"] == "star":
        pass
    elif p["topology"] == "tnkr":
        chain(CHAIN_N, f"sL{len(CHAIN_L)-1}p", f"sL{len(CHAIN_L)-1}n", "N", first=hop14)
    else:
        chain(CHAIN_N, "a3p", "a3n", "N", first=hopY)
    probes = ["v(bplus)", "v(pp)", "v(pm)", "v(bus,busn)", "v(becip,becin)", "v(beco,becon)", "v(h1p,h1n)", "v(regp,regn)",
              "i(Vbecs)"] + [f"v({a},{b})" for a, b in nodes.values()]
    lines += [".options method=gear reltol=1e-3", f".tran {dt} {t[-1]:.4f}",
              ".control", "run", f"wrdata {{OUTFILE}} " + " ".join(probes), "quit", ".endc", ".end"]
    return "\n".join(lines), probes, nodes, p

def run_as_built(label, npz, t0, t1, vcell, pq=None, over=None):
    """the as_built topology through sim/power_fix.py run() (time-weighted gates, 50 Hz phase samples, branch currents);
    returns this file's case keys plus power_fix's (ankle_pct_below_6V, branch_A, ...)"""
    PF = _power_fix()
    ex = {k: v for k, v in (over or {}).items() if k != "topology"}
    if pq is not None:
        ex["I_q"] = pq
    tag = None
    if os.environ.get("ODM_SAVE_V"):
        tag = "v_%s" % "".join(ch if ch.isalnum() else "_" for ch in label)[:80]
    r = PF.run(label, npz, t0, t1, vcell, PF.OPTIONS["ab"], "high-side", extra=ex, save=tag, save_dir=OUT)
    r.update(topology="as_built", cell_ocv=vcell, pack_ocv=2 * vcell, servo_quiescent_A=ex.get("I_q", P["I_q"]),
             overrides=over or {}, trace=os.path.abspath(npz), window_s=[t0, t1], netlist=PF.net_len()["source"],
             netlist_values=summary_lengths(PF.net_len()))
    return r

def run_case(label, npz, t0, t1, vcell, pq=None, over=None):
    if (over or {}).get("topology") == "as_built":
        return run_as_built(label, npz, t0, t1, vcell, pq, over)
    pq = P["I_q"] if pq is None else pq
    pw, dt = servo_power(npz, t0, t1)
    cir, probes, nodes, P_used = build(pw, dt, vcell, pq, over)
    with tempfile.TemporaryDirectory() as td:
        f = os.path.join(td, "c.cir"); outf = os.path.join(td, "o.txt")
        open(f, "w").write(cir.replace("{OUTFILE}", outf))
        r = subprocess.run(["ngspice", "-b", f], capture_output=True, text=True, timeout=1800)
        if not os.path.exists(outf):
            raise RuntimeError(r.stdout[-2000:] + r.stderr[-2000:])
        A = np.loadtxt(outf)
    cols = A[:, 1::2]   # wrdata writes time,value pairs
    tt = A[:, 0]; wts = np.diff(tt, append=tt[-1])          # ngspice uses variable steps: weight every sample by its step
    def tmean(x): return float((x * wts).sum() / wts.sum())
    def tms(mask): return round(float(wts[mask].sum() * 1000.0), 1)
    res = {pr: cols[:, i] for i, pr in enumerate(probes)}
    sv = {nm: res[f"v({a},{b})"] for nm, (a, b) in nodes.items()}
    pack_I = res["v(pm)"] / (P_used["R_holder"] / 2 + wire(16, L["P2"]) + P_used["R_bms"])   # current in the return path
    worst = min(sv, key=lambda k: sv[k].min())
    if os.environ.get("ODM_SAVE_V"):      # optional: keep the time series for plots (sim/plot_power_path.py)
        tag = "".join(ch if ch.isalnum() else "_" for ch in label)[:80]
        np.savez_compressed(os.path.join(OUT, "v_%s.npz" % tag), t=tt, pack_I=pack_I, names=np.array(list(sv)),
                            V=np.array([sv[k] for k in sv]), label=label)
    out = dict(label=label, cell_ocv=vcell, pack_ocv=2 * vcell, servo_quiescent_A=pq, overrides=over or {},
               pack_terminal_V_min=round(float(res["v(bplus)"].min()), 3),
               bus_V_min=round(float(res["v(bus,busn)"].min()), 3), bus_V_mean=round(tmean(res["v(bus,busn)"]), 3),
               bec_out_V_min=round(float(res["v(beco,becon)"].min()), 3), bec_out_V_mean=round(tmean(res["v(beco,becon)"]), 3),
               bec_out_A_mean=round(tmean(res["i(Vbecs)"]), 3), bec_out_A_max=round(float(res["i(Vbecs)"].max()), 3),
               adapter_H1_V_min=round(float(res["v(h1p,h1n)"].min()), 3),
               reg5_in_V_min=round(float(res["v(regp,regn)"].min()), 3),
               pack_A_mean=round(tmean(pack_I), 3), pack_A_max=round(float(pack_I.max()), 3),
               pack_A_rms=round(float(np.sqrt(tmean(pack_I ** 2))), 3),
               switch_W_mean=round(tmean(pack_I ** 2) * P_used["R_sw"], 3),
               window_ms=round(float((tt[-1] - tt[0]) * 1000.0), 1),
               worst_servo=worst, worst_servo_V_min=round(float(sv[worst].min()), 3),
               servo_V_min={k: round(float(v.min()), 3) for k, v in sv.items()},
               servo_V_mean={k: round(tmean(v), 3) for k, v in sv.items()},
               servo_ms_below_6V={k: tms(v < 6.0) for k, v in sv.items()},
               servo_ms_below_4V5={k: tms(v < 4.5) for k, v in sv.items()})
    return out

TYP = dict(R_contact=0.005, kit_awg=24, R_cell=0.015, R_holder=0.010, R_adapter=0.005)   # typical corner
PACK_CELL_V = {"full": 4.2, "nominal": 3.7, "low": 3.3}
DOC_HEADER = ("| Pack, corner | Trace | Bus mean | BEC out mean | Pack current mean / max / RMS | Lowest servo: min (mean) | "
              "Ankle time under 6.0 V | Knees (L / R), head roll: time under 6.0 V | Any servo under 4.5 V |\n"
              "|---|---|---|---|---|---|---|---|---|")

def doc_row(c, trace):
    """one row of the as-built table in sim/POWER_PATH_SIM.md (verify/e6_power_path.py reads it back)"""
    lab = c["label"].split(": ", 1)[1]
    pk = [k for k in PACK_CELL_V if f"pack {k}" in lab][0]
    corner = "typical" if lab.endswith("typical R") else "high-side"
    name = (f"fall after a push, {pk} ({2 * PACK_CELL_V[pk]:.1f} V), {corner} (3 s)" if lab.startswith("fall")
            else f"{pk} ({2 * PACK_CELL_V[pk]:.1f} V), {corner}")
    w = c["worst_servo"]; s6 = c["servo_pct_below_6V"]
    return (f"| {name} | {trace} | {c['bus_V_mean']:.2f} V | {c['bec_out_V_mean']:.2f} V | {c['pack_A_mean']:.1f} / {c['pack_A_max']:.1f} / "
            f"{c['pack_A_rms']:.2f} A | {w.replace('_', ' ')} {c['worst_servo_V_min']:.2f} V ({c['servo_V_mean'][w]:.2f} V) | "
            f"{c['ankle_pct_below_6V']:.1f} % (50 Hz: {c['ankle_pct_below_6V_50Hz_best_phase']:.1f} to {c['ankle_pct_below_6V_50Hz_worst_phase']:.1f} %) | "
            f"{s6['left_knee']:.1f} / {s6['right_knee']:.1f} %, {s6['head_roll']:.1f} % | {c['any_servo_ms_below_4V5']:.0f} ms |")

if __name__ == "__main__":
    sys.modules.setdefault("power_path_sim", sys.modules["__main__"])
    cases = []
    wb = os.path.join(TR, "trace_walk_backlash.npz"); wp = os.path.join(TR, "trace_walk_pushes.npz")
    packs = [k for k in os.environ.get("ODM_PACKS", "full,nominal,low").split(",") if k]
    for topo in (os.environ.get("ODM_TOPOS", "as_built").split(",")):
        for tag in packs:
            vc = PACK_CELL_V[tag]
            cases.append(run_case(f"{topo}: walk, backlash, pack {tag}, high-side R", wb, 10.0, 16.0, vc, over=dict(topology=topo)))
            cases.append(run_case(f"{topo}: walk, backlash, pack {tag}, typical R", wb, 10.0, 16.0, vc, over=dict(TYP, topology=topo)))
        if os.environ.get("ODM_FALL", "1") == "1":
            cases.append(run_case(f"{topo}: fall after a push, pack low, high-side R", wp, 9.5, 12.5, 3.3, over=dict(topology=topo)))
    meta = dict(params=P, lengths_mm=L, typical=TYP, traces=os.path.abspath(TR), cases=cases)
    if any(c.get("topology") == "as_built" for c in cases):
        nl = _power_fix().net_len()
        meta.update(netlist=nl["source"], netlist_values=summary_lengths(nl), netlist_wires_used=nl["used"], cable_of_edge=nl["cable_of"])
    json.dump(meta, open(os.path.join(OUT, "power_path_sim.json"), "w"), indent=1)
    for c in cases:
        print(json.dumps({k: v for k, v in c.items() if k not in ("servo_V_min", "servo_V_mean", "servo_ms_below_6V", "servo_ms_below_4V5",
                                                                   "servo_pct_below_6V", "branch_A", "netlist_values", "overrides")}))
    ab = [c for c in cases if c.get("topology") == "as_built"]
    if ab:   # the as-built table rows for sim/POWER_PATH_SIM.md
        print(DOC_HEADER)
        for c in ab:
            print(doc_row(c, os.environ.get("ODM_TRACE_LABEL", os.path.basename(os.path.abspath(TR)))))
