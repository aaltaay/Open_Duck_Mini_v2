#!/usr/bin/env python3
"""Rule check of dock_netlist.yaml (calc only): every pin is wired or marked nc, every wire joins two pins of the same
net, each wire's gauge carries its peak current, the gate board's nets each join two or more pins, and the gate
thresholds from its resistor values (the NTC window in deg C for a 10 k B3950 NTC, the pack-voltage window in V).
Run: python3 altaay_lab/twin/dock/dock_erc.py   (exit 1 on an ERROR)
"""
import collections, math, os, re, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
D = yaml.safe_load(open(os.path.join(HERE, "dock_netlist.yaml")))
AMP = {"16 AWG": 10.0, "20 AWG": 5.0, "26 AWG": 1.0}   # [L] the robot ERC's chassis-wiring limits (audit/erc.py), silicone wire


def val(txt):
    """value of a resistor text: '10 k', or '26.7 k = 22 k + 4.7 k in series' (the sum of the kit parts is used)"""
    if "=" in txt:
        parts = re.findall(r"([0-9.]+)\s*([kM]?)", txt.split("=")[1].split(" in series")[0])
        return sum(float(a) * {"": 1, "k": 1e3, "M": 1e6}[b] for a, b in parts)
    m = re.match(r"\s*([0-9.]+)\s*([kM]?)", txt)
    return float(m.group(1)) * {"": 1, "k": 1e3, "M": 1e6}[m.group(2)]


def main():
    err, warn, info = [], [], []
    pins = {f"{c['id']}.{p['pin']}": (c, p) for c in D["components"] for p in c["pins"]}
    used = collections.Counter()
    for w in D["wires"]:
        for end in (w["from"], w["to"]):
            if end not in pins:
                err.append(f"wire {w['from']}-{w['to']}: {end} is not a pin"); continue
            used[end] += 1
            if pins[end][1].get("net") != w["net"]:
                err.append(f"wire {w['from']}-{w['to']}: {end} is on net {pins[end][1].get('net')}, the wire says {w['net']}")
        lim = AMP.get(w["gauge"])
        if lim is None:
            err.append(f"wire {w['from']}-{w['to']}: gauge {w['gauge']} unknown")
        elif (w.get("i_peak_a") or 0) > lim:
            err.append(f"wire {w['from']}-{w['to']}: {w['i_peak_a']} A over the {lim} A of {w['gauge']}")
    for ref, (c, p) in pins.items():
        mated = any(i.get("kind") == "mated" and ref.endswith("." + i["a"]) for i in c.get("internal", []))
        if p["dir"] == "nc":
            if used[ref]:
                err.append(f"{ref} is nc but wired")
        elif not used[ref] and not mated and c["id"] != "AD":
            err.append(f"{ref} ({p['label']}) has no wire")
    # gate board
    gb = D["gate_board"]
    nets = collections.defaultdict(list)
    for part in gb["parts"]:
        for pin, net in part["pins"].items():
            nets[net].append(f"{part['ref']}.{pin}")
    for t, net in gb["terminals"].items():
        nets[net].append(f"terminal {t}")
    for n, ps in nets.items():
        if len(ps) < 2:
            err.append(f"gate net {n} has one pin only: {ps}")
    R = {p["ref"]: val(p["part"]) for p in gb["parts"] if p["ref"].startswith("R")}
    vref = 2.495
    va = [vref * (R["R4"] + R["R5"]) / (R["R3"] + R["R4"] + R["R5"]), vref * R["R5"] / (R["R3"] + R["R4"] + R["R5"])]   # cold, hot
    def ntc_c(v):   # V_sense = vref x Rn / (10 k + Rn)
        rn = 10e3 * v / (vref - v)
        return 1.0 / (1 / 298.15 + math.log(rn / 10e3) / 3950.0) - 273.15
    t_cold, t_hot = ntc_c(va[0]), ntc_c(va[1])
    vb = [vref * (R["R7"] + R["R8"]) / (R["R6"] + R["R7"] + R["R8"]), vref * R["R8"] / (R["R6"] + R["R7"] + R["R8"])]
    k_direct = R["R10"] / (R["R9"] + R["R10"])
    k_duck = R["R10"] / (R["R9"] + R["R10"] + 100e3)     # through the duck's 100 k across DK2 (charger off)
    info.append("NTC window (10 k B3950, 10 k from %.3f V): on from %.1f C (%.3f V) down to %.1f C (%.3f V); open reads %.2f V, short 0 V: both off"
                % (vref, t_hot, va[1], t_cold, va[0], vref))
    info.append("pack window through the duck's 100 k (charger off): on from %.2f V to %.2f V; charger on (direct): off above %.2f V; a coin or nothing reads 0 V"
                % (vb[1] / k_duck, vb[0] / k_duck, vb[0] / k_direct))
    if not (40.0 <= t_hot <= 47.0 and 0.0 <= t_cold <= 8.0):   # the DOCK_TWIN 5 to 45 C window, to the resistor steps of the kit
        err.append("NTC window %.1f to %.1f C is not about 5 to 45 C" % (t_cold, t_hot))
    if not (4.6 <= vb[1] / k_duck <= 5.4 and vb[0] / k_direct >= 8.48):
        err.append("pack window %.2f V low / %.2f V high (direct) is off" % (vb[1] / k_duck, vb[0] / k_direct))
    t_pulse = 1.1 * R["R17"] * 1e-6
    info.append("wake one-shot 1.1 x R17 x C4 = %.0f ms" % (t_pulse * 1000))
    print("dock ERC: %d ERROR, %d WARN" % (len(err), len(warn)))
    for x in err: print("ERROR", x)
    for x in info: print("INFO", x)
    return dict(errors=err, warnings=warn, info=info, t_hot=round(t_hot, 1), t_cold=round(t_cold, 1), v_lo=round(vb[1] / k_duck, 2), v_hi_direct=round(vb[0] / k_direct, 2))


if __name__ == "__main__":
    r = main()
    sys.exit(1 if r["errors"] else 0)
