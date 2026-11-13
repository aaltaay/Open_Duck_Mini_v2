"""Pack current of the awake dock loads against the 0.10 A termination. Calc only.

  python3 altaay_lab/circuitry/check_awake_load.py
"""
I_PI_5V = 0.350       # cited, Raspberry Pi docs, Zero 2 W typical bare-board active
V_5 = 5.0
ETA = (0.94, 0.97)    # cited range on the D30V30F5 graph, not a point at this voltage
V_PACK = (10.8, 12.6)
V_NEST = 15.0
I_TERM = 0.10         # cited, one tenth of the 1.00 A fast charge
I_CHG = 1.006         # calc only, the ISET divider on the BQ24133 board
I_DPM = 1.983         # calc only, the ACSET divider
P_BRANCH = 3.0        # the lab's existing 5 V typical, POWER.md, not a new sheet


def pack_a(p_w, eta, v):
    return p_w / (eta * v)


def main():
    fails = []

    def check(name, ok, detail):
        print("%-32s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
        if not ok:
            fails.append(name)

    p_pi = I_PI_5V * V_5
    low = pack_a(p_pi, ETA[1], V_PACK[1])
    high = pack_a(p_pi, ETA[0], V_PACK[0])
    check("Pi watts are 1.75", abs(p_pi - 1.75) < 1e-9, "%.2f W" % p_pi)
    check("Pi at pack, best case, is 0.143 A", abs(low - 0.143) < 0.001, "%.3f A" % low)
    check("Pi at pack, low case, is 0.172 A", abs(high - 0.172) < 0.001, "%.3f A" % high)
    check("Pi pack current exceeds 0.10 A", low > I_TERM, "%.3f > %.2f" % (low, I_TERM))
    branch = pack_a(P_BRANCH, ETA[1], V_PACK[1])
    check("3 W branch at pack is 0.245 A", abs(branch - 0.245) < 0.001, "%.3f A" % branch)
    i_nest = pack_a(p_pi, ETA[0], V_NEST)
    check("Pi from a 15 V nest is 0.124 A", abs(i_nest - 0.124) < 0.001, "%.3f A" % i_nest)
    check("charge plus Pi fits under the input limit", I_CHG + i_nest < I_DPM,
          "%.3f + %.3f < %.3f" % (I_CHG, i_nest, I_DPM))
    if fails:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
