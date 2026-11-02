"""Power path circuit simulation with ngspice (sim pass only).

Builds a SPICE netlist of the whole power path, from the cells to every servo, and drives each of the 14 servos with
its own power trace from the MuJoCo walk (sim/current_budget.py with ODM_SAVE_TRACES=1). Every series resistance is a
parameter below with its source; values that are not published are marked ASSUMPTION and chosen on the high side.

Topology (cable ids from CABLE_MAP.md):
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
"""
import os, json, subprocess, tempfile
import numpy as np

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
                         # "star": servo power bypasses the adapter: BEC -> splice -> one 20 AWG power pair per chain, adapter carries data only
)
def wire(awg, mm): return CU[awg] * mm / 1000.0
L = dict(P1=120, P2=120, P6=80, P7=90 + 90, P8=170, P9=140, P10=150, P11=140, P13=550, S14=490, kit=150)   # mm (CABLE_MAP, MOUNTING)

CHAIN_L = ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle"]   # H3 side
CHAIN_N = ["neck_pitch", "head_pitch", "head_yaw", "head_roll"]                            # neck chain
CHAIN_R = ["right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]   # H5 side

def servo_power(npz, t0, t1):
    """returns per-servo (commanded motor voltage u_cmd, joint speed w) from the MuJoCo trace"""
    d = np.load(npz); F, W, dt = d["F"], d["W"], float(d["dt"]); names = list(d["names"])
    R = KT / KT_OVER_R
    u = np.clip(F * R / KT, -VIN_MODEL, VIN_MODEL)
    k0, k1 = int(t0 / dt), int(t1 / dt)
    return {n: (u[k0:k1, i], W[k0:k1, i]) for i, n in enumerate(names)}, dt

def build(pw, dt, vcell, pq, over=None):
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
        # splice next to the BEC, 60 mm of 16 AWG; branches: 20 AWG, 150 mm to each hip yaw servo, 180 mm to neck pitch, 1 contact each
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

def run_case(label, npz, t0, t1, vcell, pq=None, over=None):
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

if __name__ == "__main__":
    cases = []
    wb = os.path.join(TR, "trace_walk_backlash.npz"); wp = os.path.join(TR, "trace_walk_pushes.npz")
    TYP = dict(R_contact=0.005, kit_awg=24, R_cell=0.015, R_holder=0.010, R_adapter=0.005)   # typical corner
    for topo in (os.environ.get("ODM_TOPOS", "tnkr,y_at_adapter,star").split(",")):
        for vc, tag in ((4.2, "full"), (3.7, "nominal"), (3.3, "low")):
            cases.append(run_case(f"{topo}: walk, backlash, pack {tag}, high-side R", wb, 10.0, 16.0, vc, over=dict(topology=topo)))
            cases.append(run_case(f"{topo}: walk, backlash, pack {tag}, typical R", wb, 10.0, 16.0, vc, over=dict(TYP, topology=topo)))
        cases.append(run_case(f"{topo}: fall after a push, pack low, high-side R", wp, 9.5, 12.5, 3.3, over=dict(topology=topo)))
    json.dump(dict(params=P, lengths_mm=L, cases=cases), open(os.path.join(OUT, "power_path_sim.json"), "w"), indent=1)
    for c in cases:
        print(json.dumps({k: v for k, v in c.items() if k not in ("servo_V_min", "servo_V_mean", "servo_ms_below_6V", "servo_ms_below_4V5")}))
