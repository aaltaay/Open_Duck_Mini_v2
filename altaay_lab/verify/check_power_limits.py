#!/usr/bin/env python3
"""Fail a power-path set point that is outside a cited limit, or that the netlist
and the sim configs do not share.

Reads wiring/netlist.yaml, verify/part_limits.yaml, and the live set points in
altaay_lab Python and in problems/train_sts12.json. Stored sim outputs are not
configs. A sensitivity sweep (a dropout other than the design value, inside a
study list) is not the design set point.

  python3 altaay_lab/verify/check_power_limits.py
  python3 altaay_lab/verify/check_power_limits.py --prove

--prove shows the old 16 V set point failing and the 12.0 V set point passing,
then runs the tree. Exit 0 only when that proof holds and the tree has no FAIL.
"""
import glob
import json
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(LAB, ".."))
LIMITS = os.path.join(HERE, "part_limits.yaml")
NETLIST = os.path.join(LAB, "wiring", "netlist.yaml")

# 2S MCP73213 path. D61 is not edited. Not the 3S nest.
NEST_SKIP = {"altaay_lab/circuitry/check_charger.py"}


def rel(path):
    return os.path.relpath(path, ROOT)


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def near(a, b, tol=1e-6):
    return abs(float(a) - float(b)) <= tol


def inside(lo, hi, limit_lo, limit_hi):
    return float(lo) + 1e-6 >= float(limit_lo) and float(hi) <= float(limit_hi) + 1e-6


class Report:
    def __init__(self):
        self.fail = []
        self.open = []
        self.blocker = []

    def add_fail(self, text):
        self.fail.append(text)

    def add_open(self, text):
        self.open.append(text)

    def add_blocker(self, text):
        self.blocker.append(text)

    def ok(self):
        return not self.fail


def component(net, cid):
    for c in net["components"]:
        if c["id"] == cid:
            return c
    raise KeyError(cid)


def pin_of(comp, name):
    for p in comp["pins"]:
        if p["pin"] == name:
            return p
    raise KeyError(name)


def domain(net, name):
    return net["domains"][name]


def numbers_in_py():
    """Design literals. Comment lines and the word superseded are skipped.

    sim/power_path_sim.py BEC_V is the shared 2S default. It is not a 3S set point.
    It must stay 7.2 V so the two-cell runs still regulate. The 3S studies pass 12.0 V.
    """
    bec, drop, nest, pmin, pmax = [], [], [], [], []
    nest_2s = []
    legacy = []
    pps_rel = "altaay_lab/sim/power_path_sim.py"
    for path in glob.glob(os.path.join(LAB, "**", "*.py"), recursive=True):
        r = rel(path)
        text = open(path, encoding="utf-8").read().splitlines()
        for i, line in enumerate(text, 1):
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue
            if "superseded" in raw.lower():
                continue
            # problems/system_voltage.py ranks a straight wire by passing a
            # 30 V stand-in and a zero drop into the existing solver. That is
            # a study model, not the adopted Castle set point. The netlist
            # stays at 12.0 V.
            compact = raw.replace(" ", "")
            if r == "altaay_lab/problems/system_voltage.py" and (
                "BEC_V=30" in compact or "BEC_DROP=0.0" in compact or "BEC_DROP=0," in compact
            ):
                continue
            where = "%s:%d" % (r, i)
            m_drop = re.search(r"\bBEC_DROP\s*=\s*([0-9]+(?:\.[0-9]+)?)", raw)
            if r == pps_rel and m_drop:
                drop.append((where, float(m_drop.group(1))))
            m_bec = re.search(r"\bBEC_V\s*=\s*([0-9]+(?:\.[0-9]+)?)", raw)
            if r == pps_rel and m_bec:
                legacy.append((where, float(m_bec.group(1))))
                continue
            for rx, bucket in (
                (r"\bBEC_SET_V\s*=\s*([0-9]+(?:\.[0-9]+)?)", bec),
                (r"\bBEC_V\s*=\s*([0-9]+(?:\.[0-9]+)?)", bec),
                (r"\bbec_set_V\s*=\s*([0-9]+(?:\.[0-9]+)?)", bec),
                (r"\bBEC_DROP_V\s*=\s*([0-9]+(?:\.[0-9]+)?)", drop),
                (r"\bV_DROP\s*=\s*([0-9]+(?:\.[0-9]+)?)", drop),
                (r"\bPACK_V_MIN\s*=\s*([0-9]+(?:\.[0-9]+)?)", pmin),
                (r"\bPACK_V_MAX\s*=\s*([0-9]+(?:\.[0-9]+)?)", pmax),
            ):
                m = re.search(rx, raw)
                if m:
                    bucket.append((where, float(m.group(1))))
            m = re.search(r"\b(?:NEST_V|V_NEST)\s*=\s*([0-9]+(?:\.[0-9]+)?)", raw)
            if m:
                if r in NEST_SKIP:
                    nest_2s.append((where, float(m.group(1))))
                else:
                    nest.append((where, float(m.group(1))))
    return bec, drop, nest, nest_2s, pmin, pmax, legacy


def numbers_in_json():
    bec, drop = [], []
    for path in glob.glob(os.path.join(LAB, "**", "*.json"), recursive=True):
        if os.path.getsize(path) > 2_000_000:
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        if "bec_set_V" not in text and "bec_drop_V" not in text:
            continue
        doc = json.loads(text)

        def walk(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == "bec_set_V" and isinstance(v, (int, float)):
                        bec.append((rel(path), float(v)))
                    elif k == "bec_drop_V" and isinstance(v, (int, float)):
                        drop.append((rel(path), float(v)))
                    else:
                        walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)

        walk(doc)
    return bec, drop


def netlist_setpoints(net):
    u1 = component(net, "U1")
    u3 = component(net, "U3")
    bec_in = pin_of(u1, "IN+")["domain"]
    bec_out = pin_of(u1, "OUT1+")["domain"]
    u3_in = pin_of(u3, "VIN")["domain"]
    v_out = float(u1["ratings"]["v_out"])
    part = u1["part"]
    m = re.search(r"set to ([0-9]+(?:\.[0-9]+)?) V", part)
    part_v = float(m.group(1)) if m else None
    note_v = []
    for item in u1.get("internal") or []:
        mm = re.search(r"set to ([0-9]+(?:\.[0-9]+)?) V", item.get("note") or "")
        if mm:
            note_v.append(float(mm.group(1)))
    return dict(bec_in=bec_in, bec_out=bec_out, u3_in=u3_in, v_out=v_out, part_v=part_v, note_v=note_v)


def judge(limits, becs, drops, nests, pack, servo, five, u3_domain, pack_domain, flags):
    """becs, drops, nests are lists of floats. pack and servo and five are (lo, hi) or None.
    flags: bms_2s, charger_2s, pack_drawing_2s (bool)."""
    rep = Report()
    bec_part = limits["parts"]["castle_bec"]
    cells = limits["parts"]["p45b"]
    fuse = limits["parts"]["fuse"]
    sw = limits["parts"]["pololu_2815"]
    reg = limits["parts"]["pololu_4892"]
    chg = limits["parts"]["bq24133"]
    pi = limits["parts"]["pi_zero_2w"]
    bms = limits["parts"]["tenergy_32175"]

    if len(set(round(v, 6) for v in becs)) != 1:
        rep.add_fail("BEC set point disagrees: %s" % ", ".join("%.3f" % v for v in becs))
    for v in becs:
        if v + 1e-6 < bec_part["v_out_min"] or v > bec_part["v_out_max"] + 1e-6:
            rep.add_fail(
                "BEC set point %.3f V is outside the cited output range %.1f V to %.1f V "
                "(Castle chart 4.9 V, POWER.md also cites 4.8 V, both cap at 12.5 V)"
                % (v, bec_part["v_out_min"], bec_part["v_out_max"]))
        elif v + 1e-6 < bec_part["v_out_min_also_cited"]:
            rep.add_fail("BEC set point %.3f V is under the POWER.md minimum %.1f V" % (v, bec_part["v_out_min_also_cited"]))

    if len(set(round(v, 6) for v in drops)) != 1:
        rep.add_fail("design dropout disagrees: %s" % ", ".join("%.3f" % v for v in drops))

    if len(set(round(v, 6) for v in nests)) != 1:
        rep.add_fail("3S nest voltage disagrees: %s" % ", ".join("%.3f" % v for v in nests))
    for v in nests:
        if not inside(v, v, chg["v_in_min"], chg["v_in_max"]):
            rep.add_fail("nest %.3f V is outside the BQ24133 recommended input %.1f V to %.1f V" % (v, chg["v_in_min"], chg["v_in_max"]))
        if v > chg["v_abs_pvcc"] + 1e-6 or v > chg["v_abs_avcc"] + 1e-6:
            rep.add_fail("nest %.3f V is above a BQ24133 absolute maximum (PVCC %.0f V, AVCC %.0f V)" % (v, chg["v_abs_pvcc"], chg["v_abs_avcc"]))

    if pack is None:
        rep.add_fail("no live pack voltage domain")
    else:
        lo, hi = pack
        string_lo = cells["series"] * cells["v_cut"]
        string_hi = cells["series"] * cells["v_charge"]
        if not inside(lo, hi, string_lo, string_hi):
            rep.add_fail("pack %.3f V to %.3f V is outside %dS P45B %.1f V to %.1f V (calc only, %d times the cell limits)"
                         % (lo, hi, cells["series"], string_lo, string_hi, cells["series"]))
        if hi > fuse["v_max"] + 1e-6:
            rep.add_fail("pack max %.3f V is above the fuse %.0f V" % (hi, fuse["v_max"]))
        if not inside(lo, hi, sw["v_min"], sw["v_max"]):
            rep.add_fail("pack %.3f V to %.3f V is outside the Pololu 2815 %.1f V to %.0f V" % (lo, hi, sw["v_min"], sw["v_max"]))
        if not inside(lo, hi, reg["v_in_min"], reg["v_in_max"]):
            rep.add_fail("pack %.3f V to %.3f V is outside the Pololu D30V30F5 input %.0f V to %.0f V" % (lo, hi, reg["v_in_min"], reg["v_in_max"]))
        if hi > bec_part["v_in_max"] + 1e-6:
            rep.add_fail("pack max %.3f V is above the Castle surface input max %.1f V" % (hi, bec_part["v_in_max"]))
        if u3_domain != pack_domain:
            rep.add_fail("U3 VIN domain %s is not the pack domain %s" % (u3_domain, pack_domain))

    if servo is None or pack is None:
        rep.add_fail("no live servo voltage domain")
    else:
        slo, shi = servo
        if becs and not all(near(shi, v) for v in becs):
            rep.add_fail("servo domain max %.3f V is not the BEC set point" % shi)
        for rng in limits["parts"]["sts3215_c018"]["ranges"]:
            if not rng["adopted"]:
                if slo + 1e-6 < rng["v_min"] or shi > rng["v_max"] + 1e-6:
                    rep.add_open(
                        "servo domain %.3f V to %.3f V is outside the %s citation (%.1f V to %.1f V, %s). "
                        "The 12 V study uses the adopted page and Waveshare ranges."
                        % (slo, shi, rng["id"], rng["v_min"], rng["v_max"], rng["source"]))
                continue
            if not inside(slo, shi, rng["v_min"], rng["v_max"]):
                rep.add_fail("servo domain %.3f V to %.3f V is outside %s %.1f V to %.1f V (%s)"
                             % (slo, shi, rng["id"], rng["v_min"], rng["v_max"], rng["source"]))

    if five is None:
        rep.add_fail("no 5 V domain")
    else:
        flo, fhi = five
        acc = reg["v_out_accuracy"]
        rlo = reg["v_out"] * (1.0 - acc)
        rhi = reg["v_out"] * (1.0 + acc)
        if not inside(flo, fhi, rlo, rhi) or not inside(pi["v_nom"], pi["v_nom"], flo, fhi):
            rep.add_fail("5 V domain %.3f V to %.3f V does not hold the Pi nominal %.1f V inside the regulator %.0f percent band %.2f V to %.2f V"
                         % (flo, fhi, pi["v_nom"], acc * 100, rlo, rhi))

    if pack is not None and flags.get("bms_2s"):
        ov = 2.0 * (bms["v_ov_cell"] + bms["v_ov_tol"])
        rep.add_open(
            "pack %.3f V to %.3f V is outside the Tenergy 32175 2S board (over-charge about %.2f V, cited). "
            "A 3S protection board is not selected. problems/STS12.md. Tenergy 32007 is only a cited candidate."
            % (pack[0], pack[1], ov))
    if pack is not None and flags.get("charger_2s"):
        rep.add_open("netlist CHG is still the 8.4 V 2S charger. The pack domain goes to %.1f V. The 3S charger in the later notes is the BQ24133." % pack[1])
    if flags.get("pack_drawing_2s"):
        rep.add_open("netlist PACK still says 2S and 6.0 V to 8.4 V. The live domain is the 3S window. The third cell is not drawn in this harness.")

    if becs:
        top = max(becs)
        rep.add_blocker(
            "Castle does not publish the CC BEC Pro minimum input or the behavior below the set point. "
            "A 3S pack at about 9.0 V to 12.6 V is under a %.1f V set point for most of the discharge. "
            "Full charge is 12.6 V. With the 0.3 V dropout assumption, the sim regulates only when the BEC input is at least %.1f V. "
            "Below that the sim follows the input minus 0.3 V. The real part might shut off instead. "
            "Motion RC lists 16 V to 40 V input. That is not used as a gate, because Castle's own chart rates 2S to 8S and does not print a minimum voltage."
            % (top, top + 0.3))
    rep.add_blocker("BEC dropout 0.3 V and efficiency are assumptions. Castle publishes neither.")
    rep.add_blocker("Pi Zero 2 W input tolerance around 5 V was not copied from the product brief. The 5 V domain is the regulator 4 percent band.")
    return rep


def tree_report():
    limits = load_yaml(LIMITS)
    net = load_yaml(NETLIST)
    sp = netlist_setpoints(net)
    bec_py, drop_py, nest_py, nest_2s, pmin, pmax, legacy = numbers_in_py()
    bec_js, drop_js = numbers_in_json()

    becs = [sp["v_out"]]
    if sp["part_v"] is None:
        becs.append(float("nan"))
    else:
        becs.append(sp["part_v"])
    becs.extend(sp["note_v"])
    becs.extend(v for _, v in bec_py)
    becs.extend(v for _, v in bec_js)

    drops = [v for _, v in drop_py] + [v for _, v in drop_js]
    nests = [v for _, v in nest_py]
    if len(pmin) != 1 or len(pmax) != 1:
        pack_consts = None
    else:
        pack_consts = (pmin[0][1], pmax[0][1])

    din = domain(net, sp["bec_in"])
    dout = domain(net, sp["bec_out"])
    d5 = domain(net, "5V")
    pack = (float(din["v_min"]), float(din["v_max"]))
    servo = (float(dout["v_min"]), float(dout["v_max"]))
    five = (float(d5["v_min"]), float(d5["v_max"]))

    rep = Report()
    if din.get("superseded") or dout.get("superseded"):
        rep.add_fail("BEC pins sit on a superseded domain (%s, %s)" % (sp["bec_in"], sp["bec_out"]))
    if domain(net, sp["u3_in"]).get("superseded"):
        rep.add_fail("U3 VIN sits on superseded domain %s" % sp["u3_in"])
    if pack_consts is None:
        rep.add_fail("power_net PACK_V_MIN / PACK_V_MAX missing or repeated")
    elif not (near(pack[0], pack_consts[0]) and near(pack[1], pack_consts[1])):
        rep.add_fail("pack domain %.3f V to %.3f V disagrees with power_net %.3f V to %.3f V"
                     % (pack[0], pack[1], pack_consts[0], pack_consts[1]))
    if any(v != v for v in becs):
        rep.add_fail("U1 part line has no 'set to N V'")
        becs = [v for v in becs if v == v]
    if not legacy:
        rep.add_fail("sim/power_path_sim.py has no 2S BEC_V default")
    for where, v in legacy:
        if not near(v, 7.2):
            rep.add_fail("%s BEC_V is %.3f V. The shared 2S default stays 7.2 V. The 3S studies pass 12.0 V in extra." % (where, v))

    pack_rec = component(net, "PACK")
    chg = component(net, "CHG")
    bms = component(net, "BMS")
    flags = dict(
        bms_2s="32175" in bms["part"],
        charger_2s="8.4" in str(chg["ratings"].get("output", "")),
        pack_drawing_2s=str(pack_rec["ratings"].get("cells", "")).startswith("2"),
    )
    judged = judge(limits, becs, drops, nests, pack, servo, five, sp["u3_in"], sp["bec_in"], flags)
    rep.fail.extend(judged.fail)
    rep.open.extend(judged.open)
    rep.blocker.extend(judged.blocker)
    if nest_2s:
        rep.add_open("2S nest in %s is %.1f V (D61, not edited). The 3S nest is the other NEST_V / V_NEST literals." % (nest_2s[0][0], nest_2s[0][1]))
    return rep, dict(becs=becs, drops=drops, nests=nests, pack=pack, servo=servo, u3=sp["u3_in"], pack_domain=sp["bec_in"])


def print_report(title, rep):
    print(title)
    for kind, rows in (("FAIL", rep.fail), ("OPEN", rep.open), ("BLOCKER", rep.blocker)):
        for row in rows:
            print("  %s  %s" % (kind, row))
    if not rep.fail:
        print("  no FAIL")
    print("")


def prove():
    limits = load_yaml(LIMITS)
    # Old bug: sims at 16 V, netlist still at 7.2 V. Pack window was the 2S domain.
    old = judge(
        limits, becs=[7.2, 16.0], drops=[0.3], nests=[15.0],
        pack=(6.0, 8.4), servo=(6.0, 7.4), five=(4.8, 5.2),
        u3_domain="PACK_6V0_8V4", pack_domain="PACK_6V0_8V4",
        flags=dict(bms_2s=False, charger_2s=False, pack_drawing_2s=False))
    only16 = judge(
        limits, becs=[16.0], drops=[0.3], nests=[15.0],
        pack=(9.0, 12.6), servo=(9.0, 12.0), five=(4.8, 5.2),
        u3_domain="PACK_9V0_12V6", pack_domain="PACK_9V0_12V6",
        flags=dict(bms_2s=False, charger_2s=False, pack_drawing_2s=False))
    fixed = judge(
        limits, becs=[12.0], drops=[0.3], nests=[15.0],
        pack=(9.0, 12.6), servo=(9.0, 12.0), five=(4.8, 5.2),
        u3_domain="PACK_9V0_12V6", pack_domain="PACK_9V0_12V6",
        flags=dict(bms_2s=False, charger_2s=False, pack_drawing_2s=False))
    print_report("OLD 7.2 V and 16 V (the bug):", old)
    print_report("OLD 16 V alone, other values already at the 3S window:", only16)
    print_report("FIXED 12.0 V set point:", fixed)
    caught = (not old.ok()) and any("16.000" in row or "16 V" in row or "disagrees" in row for row in old.fail)
    caught16 = (not only16.ok()) and any("16.000" in row for row in only16.fail)
    fixed_ok = fixed.ok()
    print("proof old pair fails: %s" % ("yes" if caught else "NO"))
    print("proof 16 V alone fails: %s" % ("yes" if caught16 else "NO"))
    print("proof 12.0 V set point passes: %s" % ("yes" if fixed_ok else "NO"))
    print("")
    live, _info = tree_report()
    print_report("THIS TREE:", live)
    if caught and caught16 and fixed_ok and live.ok():
        print("PROVE PASS")
        return 0
    print("PROVE FAIL")
    return 1


def main():
    if "--prove" in sys.argv:
        return prove()
    rep, info = tree_report()
    print_report("power limits:", rep)
    print("bec values: %s" % ", ".join("%.3f" % v for v in info["becs"]))
    print("2S shared default stays 7.2 V in sim/power_path_sim.py")
    print("pack domain %s: %.3f V to %.3f V" % (info["pack_domain"], info["pack"][0], info["pack"][1]))
    print("servo domain: %.3f V to %.3f V" % info["servo"])
    print("U3 VIN domain: %s" % info["u3"])
    print("nest: %s" % ", ".join("%.3f" % v for v in info["nests"]))
    print("dropout: %s" % ", ".join("%.3f" % v for v in info["drops"]))
    if rep.ok():
        print("PASS")
        return 0
    print("FAIL  %d" % len(rep.fail))
    return 1


if __name__ == "__main__":
    sys.exit(main())
