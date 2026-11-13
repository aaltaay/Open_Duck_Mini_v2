"""Power network of the Open Duck Mini v2 as built, solved at every physics step (sim pass only).

The network is not re-typed here: it is parsed from the ngspice circuit that sim/power_fix.py netlist_as_built()
writes for option "ab" (D15 star plus the D23 feeds SP4 and SP5, every length and gauge read from
wiring/netlist.yaml by sim/power_path_sim.py netlist_lengths(), the data-lead grounds SD1/SD2, the adapter copper,
the USB ground and P12). So the resistors, nodes and corner values are the ones VERIFICATION.md E6, E6b and C7 check.

Elements kept from that circuit:
  cells Vc1, Vc2 with Rc1, Rc2       here: a source v_c per cell; Rc1/Rc2 kept (lab corners) or set to 1 nOhm when
                                      the P30B surface gives the terminal volts (p30b.py)
  holder, P1, P2, BMS, P6/P8 + XT30, P7 + fuse, Pololu 2815, P9, P14, P10 (+/-), P13 (+/-), P11 + BEC leads, SP1..SP5,
  kit hops (cable + 2 contacts + servo board), data-lead grounds, adapter, USB ground, P12   all as resistors
  Ebec   BEC output = min(BEC_V, max(V(becip,becin) - BEC_DROP, 0)); solved in two linear modes (regulating, dropout)
The live 3S set point is BEC_SET_V (12.0 V). Superseded set points: 7.2 V (D3) and 16.0 V (pass-through).
Castle does not publish the minimum input or the behavior below the set point (BLOCKER). The 0.3 V dropout is an assumption.
  Bbecin BEC input current = V(beco,becon) I(Vbecs) / (BEC_EFF max(V(becip,becin), 1))
  Breg   5 V regulator input current = P_5V / (REG_EFF max(V(regp,regn), 1))
  B_<servo> servo supply current: a current sink set by the servo model (servo_sts3215.py), one per servo
Method: modified nodal analysis of the parsed circuit; for each BEC mode the response of every output used below to
each source (cell volts, BEC set point or dropout, the 2 converter currents, the 14 servo currents) is precomputed
once (a 20 x 18 matrix), then every step solves the small nonlinear source set by damped fixed-point iteration from
the last step's solution. No reactive parts: each step is a DC point, as each ngspice time point is.
"""
import os
import re
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.abspath(os.path.join(HERE, "..", "..", "sim"))
SCR = os.environ.get("TWIN_EM_SCRATCH", "/tmp/twin_em")
os.environ.setdefault("ODM_OUT", os.path.join(SCR, "pf_out"))     # power_path_sim.py creates its OUT folder on import
if SIM not in sys.path:
    sys.path.insert(0, SIM)
import power_path_sim as PPS                                       # noqa: E402  (lab model, read only)
sys.modules.setdefault("power_path_sim", PPS)
import power_fix as PF                                             # noqa: E402  (lab model, read only)

# Live 3S electrical set points. verify/check_power_limits.py reads these names.
# Superseded: BEC 7.2 V (D3) and BEC 16.0 V (the first 3S walks, pass-through).
BEC_SET_V = 12.0
PACK_V_MIN = 9.0
PACK_V_MAX = 12.6
NEST_V = 15.0
BEC_DROP_V = 0.3          # unpublished. BLOCKER. Not a Castle number.

NAMES = list(PPS.CHAIN_L + PPS.CHAIN_N + PPS.CHAIN_R)              # order of the servo sources in the solver
SERVO_ID = dict(zip(NAMES, PPS.CHAIN_IDS["L"] + PPS.CHAIN_IDS["N"] + PPS.CHAIN_IDS["R"]))
TYP = dict(PF.TYP)                                                 # typical corner (power_path_sim.py __main__)
CORNERS = {"typical": TYP, "high-side": {}}


def hop_extra(hop_mohm, corner="typical"):
    """R_contact that gives a kit hop of hop_mohm per conductor (cable + 2 contacts + board), as verify/e6b_hop_sweep.py"""
    p = PF.params(corner, PF.OPTIONS["ab"])
    kit = PF.net_len()["hop_mm"]["L"][0]
    fixed = PF.wire(p["kit_awg"], kit) + p["R_servo_pcb"]
    return dict(R_contact=(hop_mohm / 1000.0 - fixed) / 2.0)


def circuit_text(corner="typical", extra=None, vcell=3.7):
    """the ngspice text of sim/power_fix.py option ab for this corner (servo command sources are dummies)"""
    opt = PF.OPTIONS["ab"]
    ex = dict(CORNERS[corner]); ex.update(extra or {})
    # Design set point unless the caller passes a study override in extra.
    if not extra or "BEC_V" not in extra:
        ex["BEC_V"] = BEC_SET_V
    if not extra or "BEC_DROP" not in extra:
        ex["BEC_DROP"] = BEC_DROP_V
    p = PF.params("high-side", opt, ex)          # power_fix convention: "high-side" = P itself, the corner comes in extra
    pw = {n: (np.zeros(2), np.zeros(2)) for n in NAMES}
    cir, pr, nodes, probes = PF.netlist(pw, 0.002, vcell, opt, p)
    return cir, nodes, probes, p


class Net:
    """parsed as-built circuit with the precomputed responses; see the module docstring"""

    def __init__(self, corner="typical", extra=None, cell_model=None):
        self.corner = corner
        cir, nodes, probes, p = circuit_text(corner, extra)
        self.p = p
        self.servo_nodes = nodes                 # name -> (p node, n node)
        self.probes = probes
        self.cell_model = cell_model             # None: lab cells (OCV + Rc); else p30b.P30B (Rc set to 1 nOhm)
        R, V, B = [], [], {}
        E = None
        for line in cir.splitlines():
            t = line.split()
            if not t or t[0].startswith("*") or t[0].startswith("."):
                continue
            nm = t[0]
            if nm.startswith("Vu_") or nm.startswith("Vw_"):
                continue
            if nm[0] == "R":
                val = float(t[3])
                if nm in ("Rc1", "Rc2") and cell_model is not None:
                    val = 1e-9
                R.append((nm, t[1], t[2], val))
            elif nm[0] == "V":
                V.append((nm, t[1], t[2], float(t[3])))
            elif nm[0] == "E":
                E = (nm, t[1], t[2])
                m = re.search(r"min\(([0-9.]+),\s*max\(V\((\w+),(\w+)\)\s*-\s*([0-9.]+)", line)
                self.bec_v, self.bec_in = float(m.group(1)), (m.group(2), m.group(3))
                self.bec_drop = float(m.group(4))
            elif nm[0] == "B":
                B[nm] = (t[1], t[2])
        assert abs(self.bec_v - p["BEC_V"]) < 1e-12 and abs(self.bec_drop - p["BEC_DROP"]) < 1e-12
        self.bec_eff, self.reg_eff, self.p5 = p["BEC_EFF"], p["REG_EFF"], p["P_5V"]
        self.iq = p["I_q"]
        nodes_all = sorted({x for r in R for x in r[1:3]} | {x for v in V for x in v[1:3]} | {x for x in E[1:3]} |
                           {x for b in B.values() for x in b} - {"0"})
        nodes_all = [x for x in nodes_all if x != "0"]
        ix = {n: i for i, n in enumerate(nodes_all)}
        nn = len(nodes_all)
        vsrc = [v[0] for v in V] + [E[0]]
        nv = len(vsrc)
        N = nn + nv
        A = np.zeros((N, N))
        for _, a, b, r in R:
            g = 1.0 / r
            for x, y in ((a, b), (b, a)):
                if x != "0":
                    A[ix[x], ix[x]] += g
                    if y != "0":
                        A[ix[x], ix[y]] -= g
        for k, (nm, a, b, _) in enumerate(V + [(E[0], E[1], E[2], 0.0)]):
            col = nn + k
            if a != "0":
                A[ix[a], col] += 1.0; A[col, ix[a]] += 1.0
            if b != "0":
                A[ix[b], col] -= 1.0; A[col, ix[b]] -= 1.0
        self.ix, self.nn, self.vsrc = ix, nn, vsrc
        kE = nn + nv - 1
        # sources (columns): 0 cell volts (both cells), 1 E value, 2 I_bin, 3 I_reg, 4.. servo currents in NAMES order
        nsrc = 4 + len(NAMES)
        S = np.zeros((N, nsrc))
        for nm in ("Vc1", "Vc2"):
            S[nn + vsrc.index(nm), 0] = 1.0
        S[kE, 1] = 1.0
        def isrc(col, a, b):                     # current a -> b through the source: leaves a, enters b
            if a != "0": S[ix[a], col] -= 1.0
            if b != "0": S[ix[b], col] += 1.0
        isrc(2, *B["Bbecin"]); isrc(3, *B["Breg"])
        for j, n in enumerate(NAMES):
            isrc(4 + j, *B["B_" + n])
        # outputs (rows)
        def vdiff(a, b):
            row = np.zeros(N)
            if a != "0": row[ix[a]] += 1.0
            if b != "0": row[ix[b]] -= 1.0
            return row
        def icur(nm):
            row = np.zeros(N); row[nn + vsrc.index(nm)] = 1.0; return row
        out = [("v_bin", vdiff(*self.bec_in)), ("v_reg", vdiff(*B["Breg"])), ("v_out", vdiff(E[1], E[2])),
               ("i_bout", icur("Vbecs")), ("i_pack", -icur("Vc1")), ("v_pack", vdiff("bplus", "0")),
               ("v_bus", vdiff("bus", "busn"))]
        out += [("v_" + n, vdiff(*B["B_" + n])) for n in NAMES]
        amm = [v[0] for v in V if v[0].startswith("Vi_")]
        out += [("i_" + v[3:], icur(v)) for v in amm]
        self.out_names = [o[0] for o in out]
        C = np.array([o[1] for o in out])
        self.o = {n: i for i, n in enumerate(self.out_names)}
        self.osv = np.array([self.o["v_" + n] for n in NAMES])
        # mode reg: E value = BEC_V; mode drop: E row becomes V(beco)-V(becon) - V(becip)+V(becin) = -drop
        A_drop = A.copy()
        a, b = self.bec_in
        A_drop[kE, ix[a]] -= 1.0; A_drop[kE, ix[b]] += 1.0
        self.H = {"reg": C @ np.linalg.solve(A, S), "drop": C @ np.linalg.solve(A_drop, S)}
        self.nsrc = nsrc
        self.s = None
        self.mode = "reg"
        self.iters = []

    # ------------------------------------------------------------------------------------------------------------
    def e_value(self, mode):
        return self.bec_v if mode == "reg" else -self.bec_drop

    def solve(self, servo_current, vcell=None, qm=None, tol=1e-7, maxit=40):
        """one DC point. servo_current(v) -> supply current per servo (A, array in NAMES order) for servo volts v; if
        servo_current.slope exists it is called as servo_current.slope(v) -> (current, d current / d v).
        Cells: vcell (lab model, fixed OCV with Rc in the circuit) or the P30B surface at charge delivered qm.
        Newton on the 18 source values s = [cell volts, BEC value, I_bin, I_reg, 14 servo currents] with s = g(H s);
        the servo law's slope by a 0.1 mV difference; starts from the last step's solution.
        Returns the output vector (see out_names)."""
        cm = self.cell_model
        ns = self.nsrc
        if self.s is None:
            v0 = cm.v_cell(qm, 3.0) if cm is not None else vcell
            self.s = np.array([v0, self.e_value("reg"), 3.0, 0.8] + [0.1] * len(NAMES))
        if not hasattr(self, "_core"):
            rows = [self.o[k] for k in ("v_bin", "v_reg", "v_out", "i_bout", "i_pack")] + list(self.osv)
            self._core = {m: self.H[m][rows] for m in self.H}
            self._eye = np.eye(ns)
        s = self.s.copy()
        mode = self.mode
        flips = 0
        h = 1e-4
        for it in range(maxit):
            s[1] = self.e_value(mode)
            Hc = self._core[mode]
            yc = Hc @ s
            vbin, vreg, vout, ibout, ipk = yc[0], yc[1], yc[2], yc[3], yc[4]
            want = "reg" if vbin - self.bec_drop >= self.bec_v else "drop"
            if want != mode and flips < 4:         # BEC mode from the input it sees
                mode = want; flips += 1
                continue
            vs = yc[5:]
            g = np.empty(ns)
            vb = max(vbin, 1.0); vr = max(vreg, 1.0)
            g[0] = cm.v_cell(qm, ipk) if cm is not None else vcell
            g[1] = s[1]
            g[2] = vout * ibout / (self.bec_eff * vb)
            g[3] = self.p5 / (self.reg_eff * vr)
            sl = getattr(servo_current, "slope", None)
            if sl is not None:
                g[4:], dsv = sl(vs)
            else:
                g[4:] = servo_current(vs)
                dsv = None
            r = g - s
            if np.abs(r).max() < tol:
                break
            # Jacobian of g with respect to s: dg/dy (sparse) @ Hc
            J = np.zeros((ns, ns))
            if cm is not None:
                J[0] = -cm.slope(qm, ipk) * Hc[4]
            J[2] = (ibout / (self.bec_eff * vb)) * Hc[2] + (vout / (self.bec_eff * vb)) * Hc[3]
            if vbin > 1.0:
                J[2] -= (vout * ibout / (self.bec_eff * vb * vb)) * Hc[0]
            if vreg > 1.0:
                J[3] = -(self.p5 / (self.reg_eff * vr * vr)) * Hc[1]
            if dsv is None:
                dsv = (servo_current(vs + h) - g[4:]) / h
            J[4:] = dsv[:, None] * Hc[5:]
            J[1] = 0.0
            ds = np.linalg.solve(self._eye - J, r)
            s = s + ds
        s[1] = self.e_value(mode)
        y = self.H[mode] @ s
        self.s, self.mode = s, mode
        self.iters.append(it + 1)
        return y

    def servo_volts(self, y):
        return y[self.osv]


# ---------------------------------------------------------------------------------------------------------------
# validation helper: the same circuit in ngspice with the servo B sources replaced by recorded currents
# ---------------------------------------------------------------------------------------------------------------
def ngspice_same_currents(t, I, corner="typical", extra=None, vcell=3.7, label="same_currents"):
    """t: (n,) s; I: (n, 14) servo supply currents in NAMES order. Lab cells (OCV vcell, Rc). Returns (t_ng, V_ng (14, m))
    with the servo port volts at the ngspice time points."""
    cir, nodes, probes, p = circuit_text(corner, extra, vcell)
    lines = []
    for line in cir.splitlines():
        tk = line.split()
        if tk and (tk[0].startswith("Vu_") or tk[0].startswith("Vw_")):
            continue
        if tk and tk[0].startswith("B_"):
            nm = tk[0][2:]
            j = NAMES.index(nm)
            pwl = " ".join("%.5f %.6f" % (tt, ii) for tt, ii in zip(t - t[0], I[:, j]))
            lines.append("I_%s %s %s PWL(%s)" % (nm, tk[1], tk[2], pwl))
            continue
        if line.startswith(".tran"):
            line = ".tran %g %.5f" % (float(t[1] - t[0]), float(t[-1] - t[0]))
        if line.startswith("wrdata"):
            line = "wrdata {OUTFILE} " + " ".join("v(%s,%s)" % nodes[n] for n in NAMES) + " v(beco,becon) v(bus,busn)"
        lines.append(line)
    with tempfile.TemporaryDirectory() as td:
        f = os.path.join(td, "c.cir"); outf = os.path.join(td, "o.txt")
        open(f, "w").write("\n".join(lines).replace("{OUTFILE}", outf))
        r = subprocess.run(["ngspice", "-b", f], capture_output=True, text=True, timeout=3600)
        if not os.path.exists(outf):
            raise RuntimeError(r.stdout[-2000:] + r.stderr[-2000:])
        A = np.loadtxt(outf)
    tt = A[:, 0]
    cols = A[:, 1::2]
    return tt, cols[:, :len(NAMES)].T, cols[:, len(NAMES)], cols[:, len(NAMES) + 1]
