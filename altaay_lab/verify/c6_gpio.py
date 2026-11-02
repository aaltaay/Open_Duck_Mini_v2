"""C6: GPIO pins agree between the netlist, WIRING.md section 3, CABLE_MAP.md, HARNESS_BUILD.md, decision D9 and the
Runtime code at 376de65, and every BCM number sits on the physical header pin the docs name (pinout.xyz map).

Function -> BCM GPIO in each source:
  runtime   feet_contacts.py, eyes.py, projector.py, antennas.py (board.Dxx), imu.py / raw_imu.py (board.SCL, board.SDA)
  netlist   PI pin names ("GPIO22 left foot") and where each PI pin's wire goes (FSL*, RL->LEDL, SGL, BNO.SDA, ...)
  WIRING.md section 3 table (Pi pin, Signal, Goes to)
  D9        DECISIONS.md text ("feet left GPIO22 (pin 15), ...")
  CABLE_MAP D rows ("Pi pin 15 (GPIO22)")
Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/c6_gpio.py [--selftest]
"""
import copy
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

FUNCS = ["left foot", "right foot", "left eye", "right eye", "projector", "left antenna", "right antenna", "I2C SDA", "I2C SCL",
         "I2S BCLK", "I2S LRC", "I2S DIN"]
# fixed by the Pi hardware (pinout.xyz): I2C1 on GPIO2/3, PCM (I2S) CLK 18, FS 19, DOUT 21
HW = {"I2C SDA": 2, "I2C SCL": 3, "I2S BCLK": 18, "I2S LRC": 19, "I2S DIN": 21}


def classify(text):
    t = text.lower()
    for f, pats in (("left foot", ["left foot", "fsl"]), ("right foot", ["right foot", "fsr"]), ("left eye", ["left eye", "ledl", "rl."]),
                    ("right eye", ["right eye", "ledr", "rr."]), ("projector", ["projector", "ledp", "rp."]),
                    ("left antenna", ["left antenna", "sgl"]), ("right antenna", ["right antenna", "sgr"]),
                    ("I2C SDA", ["sda"]), ("I2C SCL", ["scl"]), ("I2S BCLK", ["bclk"]), ("I2S LRC", ["lrc"]), ("I2S DIN", ["din"])):
        if any(p in t for p in pats):
            return f
    return None


def gather():
    S = {}
    rt = os.path.join(V.RUNTIME, "mini_bdx_runtime", "mini_bdx_runtime")
    if os.path.isdir(rt):
        g = lambda f, n: int(V.py_assign_attr(os.path.join(rt, f), n)[1:])   # noqa: E731  'D22' -> 22
        S["runtime"] = {"left foot": g("feet_contacts.py", "LEFT_FOOT_PIN"), "right foot": g("feet_contacts.py", "RIGHT_FOOT_PIN"),
                        "left eye": g("eyes.py", "LEFT_EYE_PIN"), "right eye": g("eyes.py", "RIGHT_EYE_PIN"),
                        "projector": g("projector.py", "PROJECTOR_GPIO"), "left antenna": g("antennas.py", "LEFT_ANTENNA_PIN"),
                        "right antenna": g("antennas.py", "RIGHT_ANTENNA_PIN")}
        for f in ("imu.py", "raw_imu.py"):
            src = open(os.path.join(rt, f)).read()
            if "busio.I2C(board.SCL, board.SDA)" in src:
                S["runtime"].update({"I2C SDA": 2, "I2C SCL": 3})
            else:
                S["runtime_i2c_missing"] = f
    # netlist: pin number and GPIO number from the PI pin name, function from the far end of its wires
    net = V.load_netlist()
    pi = next(c for c in net["components"] if c["id"] == "PI")
    pins = {p["pin"]: p for p in pi["pins"]}
    ends = {}
    for w in net["wires"]:
        for a, b in (("from", "to"), ("to", "from")):
            if w[a].startswith("PI."):
                ends.setdefault(w[a][3:], []).append(w[b])
    nl, nl_pin = {}, {}
    for pn, p in pins.items():
        m = re.match(r"GPIO(\d+)", p.get("name") or "")
        if not m:
            continue
        far = " ".join(ends.get(pn, []))
        f = classify(far) or classify(p.get("name"))
        if f:
            nl[f] = int(m.group(1))
            nl_pin[f] = int(pn)
            fn = classify(p.get("name"))
            if fn and fn != f:
                S.setdefault("_conflicts", []).append("netlist PI.%s is named '%s' but wired to %s" % (pn, p.get("name"), far))
    S["netlist"], S["_netlist_pin"] = nl, nl_pin
    # WIRING.md section 3
    wm, wm_pin = {}, {}
    for t in V.md_tables(V.lab("WIRING.md")):
        if not t["section"].startswith("3. Raspberry Pi"):
            continue
        for r in t["rows"]:
            m = re.match(r"GPIO(\d+)", r.get("Signal", ""))
            if not m or not r["Pi pin"].isdigit():
                continue
            f = classify(r["Goes to"]) or classify(r["Signal"])
            if f:
                wm[f], wm_pin[f] = int(m.group(1)), int(r["Pi pin"])
    S["WIRING.md"], S["_WIRING.md_pin"] = wm, wm_pin
    # D9
    d9 = re.search(r"^- D9 GPIO mapping\..*$", open(V.lab("DECISIONS.md")).read(), re.M)
    dd, dd_pin = {}, {}
    if d9:
        t = d9.group(0)
        for f, pat in (("left foot", r"feet left GPIO(\d+) \(pin (\d+)\)"), ("right foot", r"feet left GPIO\d+ \(pin \d+\), right GPIO(\d+) \(pin (\d+)\)"),
                       ("left eye", r"eyes left GPIO(\d+) \(pin (\d+)\)"), ("right eye", r"eyes left GPIO\d+ \(pin \d+\), right GPIO(\d+) \(pin (\d+)\)"),
                       ("projector", r"projector GPIO(\d+) \(pin (\d+)\)"), ("left antenna", r"antennas left GPIO(\d+) \(pin (\d+)\)"),
                       ("right antenna", r"antennas left GPIO\d+ \(pin \d+\), right GPIO(\d+) \(pin (\d+)\)")):
            m = re.search(pat, t)
            if m:
                dd[f], dd_pin[f] = int(m.group(1)), int(m.group(2))
    S["D9"], S["_D9_pin"] = dd, dd_pin
    # CABLE_MAP D rows
    cm, cm_pin = {}, {}
    for t in V.md_tables(V.lab("CABLE_MAP.md")):
        for r in t["rows"]:
            if not re.fullmatch(r"D\d+", r.get("ID", "")):
                continue
            text = " ".join(r.get(k, "") for k in ("From", "To"))
            for pn, g in re.findall(r"pin (\d+) \(GPIO(\d+)\)", text):
                f = classify(r.get("To", "") + " " + r.get("From", ""))
                if f:
                    cm[f], cm_pin[f] = int(g), int(pn)
    S["CABLE_MAP.md"], S["_CABLE_MAP.md_pin"] = cm, cm_pin
    # HARNESS_BUILD.md: "PI.15 (U4 GPIO22 left foot)" and "(pin 15)"
    hb, hb_pin = {}, {}
    for pn, g, name in re.findall(r"PI\.(\d+) \(U4 GPIO(\d+) ([^)]*)\)", open(V.lab("HARNESS_BUILD.md")).read()):
        f = classify(name)
        if f:
            hb[f], hb_pin[f] = int(g), int(pn)
    S["HARNESS_BUILD.md"], S["_HARNESS_BUILD.md_pin"] = hb, hb_pin
    return S


def evaluate(S, R):
    for c in S.get("_conflicts", []):
        R.find("FAIL", c)
    ref = S.get("runtime")
    if not ref:
        R.find("FAIL", "Runtime code not found at %s (set ODM_RUNTIME)" % V.RUNTIME)
        return
    if S.get("runtime_i2c_missing"):
        R.find("FAIL", "Runtime %s does not open busio.I2C(board.SCL, board.SDA)" % S["runtime_i2c_missing"])
    ref = dict(ref, **{k: v for k, v in HW.items() if k not in ref})
    R.ev("Runtime 376de65 / Pi hardware: " + ", ".join("%s GPIO%d" % (f, ref[f]) for f in FUNCS))
    for src in ("netlist", "WIRING.md", "D9", "CABLE_MAP.md", "HARNESS_BUILD.md"):
        mp = S.get(src, {})
        pmap = S.get("_%s_pin" % src) or S.get("_netlist_pin" if src == "netlist" else "", {})
        need = FUNCS if src in ("netlist", "WIRING.md") else [f for f in FUNCS if f not in HW or f in mp]
        if src == "D9":
            need = FUNCS[:7]
        if src == "CABLE_MAP.md":
            need = [f for f in FUNCS[:7]]
        bad = ["%s GPIO%s vs GPIO%s" % (f, mp.get(f), ref[f]) for f in need if mp.get(f) != ref[f]]
        badpin = ["%s GPIO%d on pin %s, header map says pin %d" % (f, mp[f], pmap.get(f), V.BCM_TO_PIN[mp[f]])
                  for f in mp if f in pmap and V.BCM_TO_PIN.get(mp[f]) != pmap[f]]
        if bad or badpin:
            R.find("FAIL", "%s: %s" % (src, "; ".join(bad + badpin)),
                   fix="wire and document to the Runtime code at 376de65 (D9)", where="altaay_lab/" + src if src.endswith(".md") else None)
        else:
            R.ev("%s: %d of %d functions on the Runtime GPIO and the right header pin" % (src, len(need), len(need)))
    used = {}
    for f, g in S["netlist"].items():
        used.setdefault(g, []).append(f)
    dup = {g: fs for g, fs in used.items() if len(fs) > 1}
    if dup:
        R.find("FAIL", "netlist uses one GPIO for two functions: %s" % dup)
    pins = S["_netlist_pin"]
    R.ev("netlist header pins used for signals: %s" % ", ".join("%d %s" % (pins[f], f) for f in sorted(pins, key=pins.get)))


def main():
    R = V.Result("C6", "GPIO pins agree (netlist, WIRING.md section 3, CABLE_MAP, HARNESS_BUILD, D9, Runtime code at 376de65)",
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/c6_gpio.py",
                 "12 Pi signals (2 feet, 2 eyes, projector, 2 antennas, I2C SDA/SCL, 3 I2S) in 6 sources; BCM to header pin "
                 "map (pinout.xyz); the far end of every netlist GPIO wire (left foot goes to the left foot switches); no GPIO used twice",
                 "Pi device tree settings (I2S overlay, PWM for the antennas), real wiring (TEST_PLAN.md sections 2 and 12)")
    R.inp(V.lab("wiring", "netlist.yaml"), V.lab("WIRING.md"), V.lab("DECISIONS.md"), V.lab("CABLE_MAP.md"), V.lab("HARNESS_BUILD.md"))
    S = gather()
    evaluate(S, R)
    R.key("12 Pi signals on the same GPIO and header pin in the netlist, WIRING.md, HARNESS_BUILD.md, CABLE_MAP.md, D9 and the "
          "Runtime code: %s" % (not R.fails()))
    if "--selftest" in sys.argv or os.environ.get("VERIFY_SELFTEST") == "1":
        T = copy.deepcopy(S)
        T["WIRING.md"]["left eye"], T["WIRING.md"]["right eye"] = T["WIRING.md"]["right eye"], T["WIRING.md"]["left eye"]
        T["_netlist_pin"]["left foot"] = 11
        R2 = V.Result("C6x", "", "", "", "")
        evaluate(T, R2)
        R.ev("self-test: 2 injected faults (WIRING.md eyes swapped, netlist left foot on pin 11) -> %d FAIL findings" % len(R2.fails()))
        if len(R2.fails()) < 2:
            R.find("FAIL", "self-test: the check missed an injected fault")
    R.write()


if __name__ == "__main__":
    main()
