"""C5: servo IDs agree everywhere.

Sources compared (joint name -> bus ID), every one read from its file on each run:
  netlist     wiring/netlist.yaml components SV10 to SV33 (joint name from the source text, ID from the id and ref)
  chains      the bus chains the netlist wires (first servo from SP1, SP2, SP3, then the kit cables BUS 1 -> BUS 2)
  WIRING.md   section 2 chain table
  CABLE_MAP   section A rows ("ID 21 L hip roll")
  viewer      SERVO_ID in viewer/make_viewer_data.py
  BOM_FULL    servo rows ("Feetech STS3215 C001, ID 10, right hip yaw")
  runtime     self.joints in mini_bdx_runtime/rustypot_position_hwi.py at 376de65 (what the robot runs)
  runtime cfg scripts/configure_all_motors.py joints (what sets the IDs), software/duck_config.altaay.json joint names
  bench       bench/odm_bench/joints.py JOINTS and CHAINS (bench agent)
  sim         sim/power_path_sim.py CHAIN_L, CHAIN_R, CHAIN_N (chain order in the power model)
  policy      MJCF actuator order (Open_Duck_Playground b9be205): the Runtime maps the 14 policy actions to joints in
              the order of self.joints, so that order must equal the actuator order
Usage: VERIFY_OUT=<folder outside the repo> python3 altaay_lab/verify/c5_servo_ids.py [--selftest]
"""
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402

JOINTS = ["left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle", "neck_pitch", "head_pitch",
          "head_yaw", "head_roll", "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle"]


def words(j):
    return j.replace("_", " ")


def short(text):
    """'L hip roll' / 'R ankle' / 'left hip yaw' / 'neck pitch' -> joint name"""
    t = text.lower().strip().replace("_", " ")
    t = re.sub(r"^l ", "left ", t)
    t = re.sub(r"^r ", "right ", t)
    t = t.replace(" ", "_")
    return t if t in JOINTS else None


def gather():
    S, notes = {}, []
    net = V.load_netlist()
    comps = {c["id"]: c for c in net["components"]}
    m = {}
    for cid, c in comps.items():
        if c.get("kind") == "servo" and re.fullmatch(r"SV\d+", cid):
            sid = int(cid[2:])
            j = next((x for x in sorted(JOINTS, key=len, reverse=True) if x in (c.get("source") or "")), None)
            if c.get("ref") != "ID%d" % sid:
                notes.append("netlist %s ref %s does not match its id" % (cid, c.get("ref")))
            m[j] = sid
    S["netlist"] = m
    # chains from the wires
    first = {}
    for w in net["wires"]:
        if w["cable"] in ("SP1", "SP2", "SP3") and w["to"].endswith(".BUS2.V"):
            first[w["cable"]] = int(w["to"].split(".")[0][2:])
    nxt = {}
    for w in net["wires"]:
        if w.get("gauge") == "kit cable" and w["from"].endswith(".V"):
            a, b = w["from"].split(".")[0], w["to"].split(".")[0]
            nxt[int(a[2:])] = int(b[2:])
    chains = {}
    for sp, s in sorted(first.items()):
        ch = [s]
        while ch[-1] in nxt and len(ch) < 20:
            ch.append(nxt[ch[-1]])
        chains[sp] = ch
    S["_chains_netlist"] = chains
    # WIRING.md section 2
    sec = V.md_section(V.lab("WIRING.md"), r"^2\. Servo bus")
    wm, wch = {}, {}
    for t in V.md_tables(V.lab("WIRING.md")):
        if not t["section"].startswith("2. Servo bus"):
            continue
        for r in t["rows"]:
            ch = r["Chain"]
            ids = [int(x) for x in re.findall(r"\b(\d{2})\b", ch)]
            for sid, name in re.findall(r"\b(\d{2}) ([A-Za-z_ ]+?)(?=,|$)", ch.split(":", 1)[1]):
                j = short(name.replace("L ", "left ").replace("R ", "right "))
                if j:
                    wm[j] = int(sid)
            sp = re.search(r"\b(SP\d)\b.*?ID (\d+)", r["Power (V, G)"])
            if sp:
                wch[sp.group(1)] = ids
    S["WIRING.md"] = wm
    S["_chains_wiring"] = wch
    # CABLE_MAP.md section A
    cm = {}
    for t in V.md_tables(V.lab("CABLE_MAP.md")):
        if not t["section"].startswith("A. Servo bus"):
            continue
        for r in t["rows"]:
            for col in ("From", "To"):
                for sid, name in re.findall(r"ID (\d+) ((?:[LR] )?(?:hip yaw|hip roll|hip pitch|knee|ankle|neck pitch|head pitch|head yaw|head roll))",
                                            r.get(col, "")):
                    j = short(name)
                    if j:
                        cm[j] = int(sid)
    S["CABLE_MAP.md"] = cm
    S["viewer"] = V.py_assign(V.lab("viewer", "make_viewer_data.py"), "SERVO_ID")
    bf = {}
    for t in V.md_tables(V.lab("BOM_FULL.md")):
        for r in t["rows"]:
            mm = re.match(r"Feetech STS3215 C001, ID (\d+), (.+)$", r.get("Item", ""))
            if mm:
                j = short(mm.group(2))
                bf[j] = int(mm.group(1))
    S["BOM_FULL.md"] = bf
    hwi = os.path.join(V.RUNTIME, "mini_bdx_runtime", "mini_bdx_runtime", "rustypot_position_hwi.py")
    if os.path.exists(hwi):
        S["runtime hwi"] = V.py_assign(hwi, "joints")
        S["_runtime_order"] = list(S["runtime hwi"])
        S["_runtime_init_order"] = list(V.py_assign(hwi, "init_pos"))
        S["runtime configure_all_motors"] = V.py_assign(os.path.join(V.RUNTIME, "scripts", "configure_all_motors.py"), "joints")
        try:
            S["_runtime_commit"] = subprocess.run(["git", "-C", V.RUNTIME, "rev-parse", "--short=7", "HEAD"],
                                                  capture_output=True, text=True).stdout.strip()
        except OSError:
            S["_runtime_commit"] = "?"
    cfg = json.load(open(V.lab("software", "duck_config.altaay.json")))
    S["_config_joints"] = list(cfg.get("joints_offsets", {}))
    bj = V.lab("bench", "odm_bench", "joints.py")
    if os.path.exists(bj):
        S["bench joints.py"] = V.py_assign(bj, "JOINTS")
        S["_chains_bench"] = V.py_assign(bj, "CHAINS")
    pp = V.lab("sim", "power_path_sim.py")
    S["_chains_sim"] = {k: V.py_assign(pp, k) for k in ("CHAIN_L", "CHAIN_N", "CHAIN_R")}
    xml = os.path.join(V.PLAYGROUND, "playground", "open_duck_mini_v2", "xmls", "open_duck_mini_v2.xml")
    if os.path.exists(xml):
        S["_mjcf_order"] = [a.get("joint") for a in ET.parse(xml).getroot().iter("position") if a.get("joint")]
    return S, notes


def evaluate(S, notes, R):
    for n in notes:
        R.find("FAIL", n)
    ref = S.get("runtime hwi")
    if ref is None:
        R.find("FAIL", "Runtime HWI not found at %s (set ODM_RUNTIME)" % V.RUNTIME)
        ref = S["netlist"]
    else:
        R.ev("Runtime at %s (pin 376de65): %s" % (S.get("_runtime_commit"), ", ".join("%s %d" % (k, v) for k, v in ref.items())))
        if S.get("_runtime_commit") not in ("376de65", None):
            R.find("FAIL", "Runtime checkout is %s, not the pinned 376de65" % S.get("_runtime_commit"))
    if len(set(ref.values())) != 14 or set(ref) != set(JOINTS):
        R.find("FAIL", "reference map is not 14 distinct joints and IDs: %s" % ref)
    partial = {"WIRING.md"}      # names only the first and last servo of each chain; the chain ID order is checked below
    for src, mp in S.items():
        if src.startswith("_") or src == "runtime hwi":
            continue
        names = [j for j in JOINTS if j in mp] if src in partial else JOINTS
        bad = {j: (mp.get(j), ref.get(j)) for j in names if mp.get(j) != ref.get(j)}
        extra = sorted(set(mp) - set(JOINTS))
        if bad or extra:
            R.find("FAIL", "%s disagrees with the Runtime: %s%s" % (src, ", ".join("%s %s vs %s" % (j, a, b) for j, (a, b) in bad.items()),
                                                                     (" extra " + str(extra)) if extra else ""),
                   fix="make %s match rustypot_position_hwi.py self.joints" % src)
        elif src in partial:
            R.ev("%s: %d of 14 joints named, all match (the others appear only as IDs in the chain list)" % (src, len(names)))
        else:
            R.ev("%s: 14 of 14 joints match" % src)
    # chains
    want = {"SP1": [20, 21, 22, 23, 24], "SP2": [10, 11, 12, 13, 14], "SP3": [30, 31, 32, 33]}
    for name in ("_chains_netlist", "_chains_wiring"):
        got = S.get(name, {})
        if got != want:
            R.find("FAIL", "%s chains %s, expected %s (D15)" % (name[8:], got, want))
        else:
            R.ev("%s chains: SP1 %s, SP2 %s, SP3 %s" % (name[8:], *(got[k] for k in ("SP1", "SP2", "SP3"))))
    if "_chains_bench" in S:
        b = S["_chains_bench"]
        ok = b.get("left_leg") == want["SP1"] and b.get("right_leg") == want["SP2"] and b.get("neck") == want["SP3"]
        R.ev("bench CHAINS match the netlist: %s" % ok)
        if not ok:
            R.find("FAIL", "bench/odm_bench/joints.py CHAINS %s differ from the netlist" % b)
    inv = {v: k for k, v in ref.items()}
    sim = S["_chains_sim"]
    for k, sp in (("CHAIN_L", "SP1"), ("CHAIN_R", "SP2"), ("CHAIN_N", "SP3")):
        exp = [inv[i] for i in want[sp]]
        if sim[k] != exp:
            R.find("FAIL", "sim/power_path_sim.py %s %s, netlist chain %s" % (k, sim[k], exp))
    R.ev("power sim chain order matches the netlist chains: %s" % all(sim[k] == [inv[i] for i in want[sp]] for k, sp in
                                                                     (("CHAIN_L", "SP1"), ("CHAIN_R", "SP2"), ("CHAIN_N", "SP3"))))
    # policy action order
    if "_mjcf_order" in S and "_runtime_order" in S:
        same = S["_mjcf_order"] == S["_runtime_order"] == S["_runtime_init_order"]
        R.ev("policy action order: MJCF actuators == Runtime self.joints order == init_pos order: %s" % same)
        if not same:
            R.find("FAIL", "MJCF actuator order %s differs from the Runtime joint order %s" % (S["_mjcf_order"], S["_runtime_order"]))
    else:
        R.find("WARN", "MJCF or Runtime not found: policy action order not checked")
    cj = S["_config_joints"]
    if sorted(cj) != sorted(JOINTS):
        R.find("FAIL", "software/duck_config.altaay.json joints_offsets names differ: %s" % sorted(set(cj) ^ set(JOINTS)))
    else:
        R.ev("software/duck_config.altaay.json: 14 joint offsets, names match the Runtime")


def main():
    R = V.Result("C5", "Servo IDs agree everywhere (netlist, WIRING.md, CABLE_MAP, viewer, BOM_FULL, Runtime code and config, bench, sim, policy order)",
                 "VERIFY_OUT=<out> python3 altaay_lab/verify/c5_servo_ids.py",
                 "14 joint to ID pairs in 10 sources, the 3 bus chains (netlist wires, WIRING.md, bench, power sim), "
                 "MJCF actuator order vs Runtime action order, Runtime checkout commit",
                 "IDs written into real servos (TEST_PLAN.md section 7.1, section 8.1 check_motors.py)")
    R.inp(V.lab("wiring", "netlist.yaml"), V.lab("WIRING.md"), V.lab("CABLE_MAP.md"), V.lab("viewer", "make_viewer_data.py"),
          V.lab("BOM_FULL.md"), V.lab("software", "duck_config.altaay.json"), V.lab("bench", "odm_bench", "joints.py"),
          V.lab("sim", "power_path_sim.py"))
    S, notes = gather()
    evaluate(S, notes, R)
    R.key("14 joint IDs agree in %d ID maps (netlist, WIRING.md, CABLE_MAP, viewer, BOM_FULL, Runtime HWI, configure_all_motors, "
          "bench): %s; chains agree in netlist, WIRING.md, bench, power sim; MJCF actuator order = Runtime action order: %s" % (
              sum(1 for k in S if not k.startswith("_")), not R.fails(), S.get("_mjcf_order") == S.get("_runtime_order")))
    if "--selftest" in sys.argv or os.environ.get("VERIFY_SELFTEST") == "1":
        import copy
        T = copy.deepcopy(S)
        T["viewer"]["left_knee"], T["viewer"]["left_ankle"] = 24, 23
        T["_chains_sim"]["CHAIN_L"] = T["_chains_sim"]["CHAIN_L"][::-1]
        R2 = V.Result("C5x", "", "", "", "")
        evaluate(T, [], R2)
        caught = len(R2.fails())
        R.ev("self-test: 2 injected faults (viewer IDs 23 and 24 swapped, power sim left chain reversed) -> %d FAIL findings" % caught)
        if caught < 2:
            R.find("FAIL", "self-test: the check missed an injected fault")
    R.write()


if __name__ == "__main__":
    main()
