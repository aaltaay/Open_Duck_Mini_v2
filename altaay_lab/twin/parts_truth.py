#!/usr/bin/env python3
"""One parts file for the duck that will be built.

Derived from wiring/netlist.yaml, verify/part_limits.yaml, and bom/order/
(ORDER.md plus the part identities in ORDER.csv). Prices are not copied.
The charger TS resistors come from circuitry/bq24133_board.yaml because the
netlist charger part names that board.

  python3 altaay_lab/twin/parts_truth.py --write
  python3 altaay_lab/twin/parts_truth.py --check

The twin loads altaay_lab/twin/parts.yaml and nothing else for these numbers.
"""
import csv
import json
import os
import re
import sys
import tempfile

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(LAB, ".."))
PARTS_PATH = os.path.join(HERE, "parts.yaml")
NETLIST = os.path.join(LAB, "wiring", "netlist.yaml")
LIMITS = os.path.join(LAB, "verify", "part_limits.yaml")
ORDER_MD = os.path.join(LAB, "bom", "order", "ORDER.md")
ORDER_CSV = os.path.join(LAB, "bom", "order", "ORDER.csv")
BOARD = os.path.join(LAB, "circuitry", "bq24133_board.yaml")
GUARD = os.path.join(LAB, "bench", "battery_guard.py")
POWER_NET = os.path.join(LAB, "twin", "electromech", "power_net.py")
LIMITS_JSON = os.path.join(LAB, "software", "servo_limits.json")


def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def component(net, cid):
    for c in net["components"]:
        if c["id"] == cid:
            return c
    raise KeyError(cid)


def near(a, b, tol=1e-6):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= tol
    return a == b


def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            return False
        return all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return near(a, b)


def order_rows():
    with open(ORDER_CSV, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    out = []
    for row in rows:
        out.append(dict(
            line_id=row["line_id"].strip(),
            part=row["part"].strip(),
            mpn=(row.get("maker_part_number") or "").strip(),
            need=row.get("need") or "",
            maps_to=row.get("maps_to") or "",
            blocker=(row.get("blocker") or "").strip(),
        ))
    return out


def row_for(rows, token):
    hits = [r for r in rows if token in [t.strip() for t in r["maps_to"].split(";")]]
    return hits


def num_in(text, rx):
    m = re.search(rx, text)
    if not m:
        return None
    return float(m.group(1))


_MASS = {"done": False, "v": None}


def mass_pair():
    """MuJoCo loaded total and the BOM item rollup. None when the playground pin is not set."""
    if _MASS["done"]:
        return _MASS["v"]
    _MASS["done"] = True
    pg = os.environ.get("ODM_PLAYGROUND")
    if not pg or not os.path.isdir(pg):
        _MASS["v"] = None
        return None
    sim = os.path.join(LAB, "sim")
    if sim not in sys.path:
        sys.path.insert(0, sim)
    os.environ.setdefault("ODM_OUT", os.path.join(tempfile.gettempdir(), "duck_mass"))
    os.environ.setdefault("ODM_SCRATCH", os.path.join(tempfile.gettempdir(), "duck_mass_scratch"))
    import mass_budget as MB
    import added_mass_sim as AM
    built = MB.build_budget()
    rollup = round(float(sum(it.mass_g for it in built["items"]) / 1000.0), 4)
    trunk = round(float(built["links"]["trunk_assembly"].m), 4)
    folder = AM.write_variant("parts_truth", built["links"])
    model = AM.model_check(folder, "scene_flat_terrain_backlash.xml")
    loaded = round(float(model.body_mass.sum()), 4)
    _MASS["v"] = dict(mujoco_kg=loaded, rollup_kg=rollup, trunk_kg=trunk)
    return _MASS["v"]


def mass_kg():
    pair = mass_pair()
    if pair is None:
        return None
    return pair["mujoco_kg"]


def joint_limits():
    doc = json.load(open(LIMITS_JSON, encoding="utf-8"))
    out = {}
    for name, row in doc["joints"].items():
        out[name] = dict(
            soft_lo_deg=float(row["soft_lo_deg"]),
            soft_hi_deg=float(row["soft_hi_deg"]),
            hard_lo_deg=float(row["hard_lo_deg"]),
            hard_hi_deg=float(row["hard_hi_deg"]),
        )
    return out


def derive():
    net = load_yaml(NETLIST)
    limits = load_yaml(LIMITS)["parts"]
    rows = order_rows()
    board = load_yaml(BOARD)
    order_md = open(ORDER_MD, encoding="utf-8").read()
    guard = open(GUARD, encoding="utf-8").read()
    power = open(POWER_NET, encoding="utf-8").read()
    checker = open(os.path.join(LAB, "circuitry", "check_bq24133.py"), encoding="utf-8").read()

    pack = component(net, "PACK")
    bms = component(net, "BMS")
    chg = component(net, "CHG")
    reg = component(net, "U1")
    fuse = component(net, "F1")
    bead = component(net, "RT1")
    breakers = [c for c in net["components"] if c.get("kind") == "breaker"]
    domain = net["domains"]["PACK_9V0_12V6"]
    servo_d = net["domains"]["SERVO_12V0"]

    feeds = {}
    for w in net["wires"]:
        src = str(w.get("from") or "")
        if src.endswith(".OUT") and src.split(".")[0] in ("EFL", "EFR", "EFN"):
            feeds.setdefault(w.get("cable"), []).append(src)

    cells = limits["p45b"]
    pcm = limits["pcm_l04s30"]
    reg_lim = limits["servo_reg"]
    fuse_lim = limits["fuse"]
    br_lim = limits["tps259827"]
    chg_lim = limits["bq24133"]
    servo_lim = limits["sts3215_c018"]
    rest = limits["rest_rule"]

    bec = row_for(rows, "NL:U1")
    bms_row = row_for(rows, "NL:BMS")
    cell_row = row_for(rows, "NL:PACK")
    fuse_row = row_for(rows, "NL:F1")
    br_row = row_for(rows, "NL:EFL")
    servo_row = [r for r in rows if r["line_id"] == "servo"]
    servo_ids = []
    if servo_row:
        servo_ids = [t.split(":", 1)[1] for t in servo_row[0]["maps_to"].split(";") if t.strip().startswith("NL:SV")]
    by_id = {c["id"]: c for c in net["components"]}
    servo_parts = sorted({(by_id[i]["part"] if i in by_id else "MISSING") for i in servo_ids})

    board_r = {c["id"]: c for c in board["components"]}
    bead_ohms = [float(x) for x in re.findall(r"ts_frac\(([0-9.]+)\)", checker)]
    cold_m = re.search(r"0 C bead is above ([0-9.]+)", checker)
    hot_m = re.search(r"60 C bead is below ([0-9.]+)", checker)
    beta_m = re.search(r"B25/50\s+([0-9]+)", bead.get("part") or "")
    r25_m = re.search(r"([0-9]+)\s*kOhm at 25 C", bead.get("part") or "", re.I)

    walk_guard = num_in(guard, r"self\.pack_walk_min_v\s*=\s*([0-9.]+)")
    walk_net = num_in(power, r"WALK_PACK_MIN_V\s*=\s*([0-9.]+)")

    pair = mass_pair() or {}
    robot_kg = pair.get("mujoco_kg")
    trunk_kg = pair.get("trunk_kg")
    rollup_kg = pair.get("rollup_kg")
    if robot_kg is None and os.path.exists(PARTS_PATH):
        prior = load_yaml(PARTS_PATH).get("mass", {})
        robot_kg = prior.get("robot_kg")
        trunk_kg = trunk_kg if trunk_kg is not None else prior.get("trunk_kg")
        rollup_kg = rollup_kg if rollup_kg is not None else prior.get("rollup_kg")
    doc = dict(
        derived_from=[
            rel(NETLIST),
            rel(LIMITS),
            rel(ORDER_MD),
            rel(ORDER_CSV),
            rel(BOARD),
            rel(GUARD),
            rel(LIMITS_JSON),
            "altaay_lab/sim/mass_budget.py",
        ],
        cells=dict(
            name=cells["name"],
            order_mpn=(cell_row[0]["mpn"] if cell_row else ""),
            order_need=(cell_row[0]["need"] if cell_row else ""),
            count=int(str(pack["ratings"]["cells"]).rstrip("S")),
            series=int(cells["series"]),
            capacity_ah=float(pack["ratings"]["capacity_ah"]),
            v_charge=float(cells["v_charge"]),
            v_cut=float(cells["v_cut"]),
            i_cont_a=float(cells["i_cont_a"]),
            i_charge_max_a=float(cells["i_charge_max_a"]),
            source=cells["source"],
        ),
        pack=dict(
            v_min=float(domain["v_min"]),
            v_max=float(domain["v_max"]),
            walk_stop_v=float(pack["ratings"]["walk_stop_v"]),
            walk_stop_guard_v=walk_guard,
            walk_stop_power_net_v=walk_net,
            uv_cell_v=float(pcm["v_uv_cell"]),
            uv_tol_v=float(pcm["v_uv_tol"]),
            sheet_floor_v=float(cells["series"]) * float(cells["v_cut"]),
        ),
        regulator=dict(
            part=reg["part"],
            order_mpn=(bec[0]["mpn"] if bec else ""),
            v_set=float(reg["ratings"]["v_out"]),
            v_out_min=float(reg_lim["v_out_min"]),
            v_out_max=float(reg_lim["v_out_max"]),
            v_out_tol=float(reg_lim["v_out_tol"]),
            v_in_min=float(reg_lim["v_in_min"]),
            v_in_max=float(reg_lim["v_in_max"]),
            eff_min=float(reg_lim["eff_min"]),
            eff_max=float(reg_lim["eff_max"]),
            eff_used=float(reg_lim["eff_min"]),
            holds=reg_lim.get("below_setpoint_status") == "holds",
            i_out_12v_at_10vin_a=float(reg_lim["i_out_12v_at_10vin_a"]),
            mass_g=float(reg["ratings"]["mass_g"]),
            servo_v_min=float(servo_d["v_min"]),
            servo_v_max=float(servo_d["v_max"]),
            source=reg_lim["source"],
        ),
        fuse=dict(
            part=fuse["part"],
            order_mpn=(fuse_row[0]["mpn"] if fuse_row else ""),
            i_fuse_a=float(fuse["ratings"]["fuse_a"]),
            i_holder_a=float(fuse["ratings"]["holder_a"]),
            v_max=float(fuse["ratings"]["v_max"]),
            limit_i_a=float(fuse_lim["i_fuse_a"]),
            limit_v=float(fuse_lim["v_max"]),
        ),
        breakers=dict(
            ids=[c["id"] for c in breakers],
            order_mpn=(br_row[0]["mpn"] if br_row else ""),
            order_need=(br_row[0]["need"] if br_row else ""),
            feeds=feeds,
            r_ilim_ohm=float(br_lim["r_ilim_ohm"]),
            ilim_typ_25c_a=float(br_lim["ilim_typ_25c_a"]),
            ilim_min_25c_a=float(br_lim["ilim_min_25c_a"]),
            ilim_max_25c_a=float(br_lim["ilim_max_25c_a"]),
            v_in_max=float(br_lim["v_in_max"]),
            source=br_lim["source"],
        ),
        protection=dict(
            part=bms["part"],
            order_mpn=(bms_row[0]["mpn"] if bms_row else ""),
            i_work_a=float(bms["ratings"]["i_work_a"]),
            i_charge_a=float(bms["ratings"]["i_charge_a"]),
            v_charge=float(bms["ratings"]["v_charge"]),
            fit_status=pcm.get("fit_status"),
            limit_i_discharge_a=float(pcm["i_discharge_cont_a"]),
            source=pcm["source"],
        ),
        charger=dict(
            part=chg["part"],
            i_charge_a=float(chg["ratings"]["i_charge_a"]),
            v_charge=float(chg_lim["v_charge_3cell"]),
            v_nest=float(chg["ratings"]["v_nest"]),
            i_min_a=float(chg_lim["i_charge_min_a"]),
            i_max_a=float(chg_lim["i_charge_max_a"]),
            v_in_min=float(chg_lim["v_in_min"]),
            v_in_max=float(chg_lim["v_in_max"]),
            order_md_names_bq24133=("BQ24133" in order_md),
            source=chg_lim["source"],
        ),
        ntc=dict(
            part=bead["part"],
            beta=(float(beta_m.group(1)) if beta_m else None),
            r_25_ohm=(float(r25_m.group(1)) * 1000.0 if r25_m else None),
            bias_ohm=float(board_r["RTS"]["value_ohm"]),
            parallel_ohm=float(board_r["RTB"]["value_ohm"]),
            bead_ohm_0c=(bead_ohms[0] if len(bead_ohms) > 0 else None),
            bead_ohm_25c=(bead_ohms[1] if len(bead_ohms) > 1 else None),
            bead_ohm_60c=(bead_ohms[2] if len(bead_ohms) > 2 else None),
            stop_cold_frac=(float(cold_m.group(1)) if cold_m else None),
            stop_hot_frac=(float(hot_m.group(1)) if hot_m else None),
            cold_c=0.0,
            hot_c=60.0,
        ),
        servos=dict(
            count=len(servo_ids),
            ids=servo_ids,
            order_need=(servo_row[0]["need"] if servo_row else ""),
            order_mpn=(servo_row[0]["mpn"] if servo_row else ""),
            netlist_part_text=servo_parts,
            i_stall_12v_a=float(servo_lim["i_stall_12v_a"]),
            i_noload_12v_a=float(servo_lim["i_noload_12v_a"]),
            joint_limits=joint_limits(),
            joint_limit_source=rel(LIMITS_JSON),
        ),
        rest=dict(
            stop_c=float(rest["stop_c"]),
            resume_c=float(rest["resume_c"]),
            note=rest["source_note"],
        ),
        mass=dict(
            regulator_g=float(reg["ratings"]["mass_g"]),
            robot_kg=robot_kg,
            mass_label="CAD mass model",
            robot_note="Whole duck. MuJoCo body masses must match the mass-model item rollup. Trunk is the trunk body only. Includes 3 P45B cells, the i7C, the PCM, the BQ24133 board, and 3 breakers.",
            trunk_kg=trunk_kg,
            rollup_kg=rollup_kg,
            stock_kg=2.1071,
        ),
    )
    return doc


def problems(doc=None):
    """Hard disagreements and datasheet overruns. Empty means the file matches."""
    doc = doc if doc is not None else derive()
    bad = []

    def fail(text):
        bad.append(text)

    c = doc["cells"]
    if c["count"] != c["series"]:
        fail("cell count %s disagrees with the cited series %s" % (c["count"], c["series"]))
    if str(c["order_need"]) not in ("", str(c["count"])):
        fail("order cell need %s disagrees with the pack count %s" % (c["order_need"], c["count"]))
    def squash(text):
        return re.sub(r"[^A-Za-z0-9]", "", text or "").upper()

    if c["order_mpn"] and squash(c["order_mpn"]) not in squash(c["name"]):
        fail("order cell %s is not the cited cell %s" % (c["order_mpn"], c["name"]))

    p = doc["pack"]
    if not (c["series"] * c["v_cut"] - 1e-6 <= p["v_min"] and p["v_max"] <= c["series"] * c["v_charge"] + 1e-6):
        fail("pack window is outside the cell charge and cut voltages")
    for key in ("walk_stop_v", "walk_stop_guard_v", "walk_stop_power_net_v"):
        if p[key] is None or abs(float(p[key]) - float(p["walk_stop_v"])) > 1e-6:
            fail("walk cutoff %s is %s, not the netlist walk stop %s" % (key, p[key], p["walk_stop_v"]))
    if p["walk_stop_v"] + 1e-9 < p["v_min"]:
        fail("walk cutoff is under the pack domain minimum")

    r = doc["regulator"]
    if r["order_mpn"] and r["order_mpn"].lower() not in r["part"].lower():
        fail("order regulator %s is not in the netlist part" % r["order_mpn"])
    if r["v_set"] < r["v_out_min"] - 1e-9 or r["v_set"] > r["v_out_max"] + 1e-9:
        fail("regulator set point is outside the cited output range")
    if r["eff_used"] < r["eff_min"] - 1e-9 or r["eff_used"] > r["eff_max"] + 1e-9:
        fail("regulator efficiency used by the twin is outside the cited band")
    if p["v_min"] + 1e-9 < r["v_in_min"] or p["v_max"] > r["v_in_max"] + 1e-9:
        fail("pack window is outside the regulator input range")
    if r["servo_v_min"] + 1e-6 < r["v_set"] * (1.0 - r["v_out_tol"]) or r["servo_v_max"] > r["v_set"] * (1.0 + r["v_out_tol"]) + 1e-6:
        fail("servo domain is outside the regulator tolerance band")

    f = doc["fuse"]
    if abs(f["i_fuse_a"] - f["limit_i_a"]) > 1e-6 or abs(f["v_max"] - f["limit_v"]) > 1e-6:
        fail("fuse ratings disagree with the cited fuse limits")
    if f["order_mpn"] and f["order_mpn"] not in f["part"]:
        fail("order fuse %s is not in the netlist fuse" % f["order_mpn"])
    if p["v_max"] > f["v_max"] + 1e-9:
        fail("pack max is above the fuse voltage")

    b = doc["breakers"]
    if b["ids"] != ["EFL", "EFR", "EFN"]:
        fail("breaker ids are not EFL, EFR, EFN")
    if str(b["order_need"]) not in ("", "3"):
        fail("order breaker need is not 3")
    need = {"SP1": "EFL.OUT", "SP2": "EFR.OUT", "SP3": "EFN.OUT", "SP4": "EFL.OUT", "SP5": "EFR.OUT"}
    for cable, src in need.items():
        got = b["feeds"].get(cable) or []
        if src not in got:
            fail("feed %s does not leave %s" % (cable, src))
    if b["ilim_typ_25c_a"] < b["ilim_min_25c_a"] or b["ilim_typ_25c_a"] > b["ilim_max_25c_a"]:
        fail("breaker typical limit is outside the cited 25 C band")

    prot = doc["protection"]
    if prot["order_mpn"] and prot["order_mpn"] not in prot["part"]:
        fail("order protection board is not the netlist board")
    if abs(prot["i_work_a"] - prot["limit_i_discharge_a"]) > 1e-6:
        fail("protection current disagrees with the cited continuous discharge")
    if prot["fit_status"] != "seated":
        fail("protection board fit_status is not seated")

    ch = doc["charger"]
    if not (ch["i_min_a"] - 1e-9 <= ch["i_charge_a"] <= ch["i_max_a"] + 1e-9):
        fail("charge current is outside the BQ24133 fast-charge range")
    if ch["i_charge_a"] > c["i_charge_max_a"] + 1e-9:
        fail("charge current is above the cell maximum")
    if not (ch["v_in_min"] - 1e-9 <= ch["v_nest"] <= ch["v_in_max"] + 1e-9):
        fail("nest voltage is outside the BQ24133 input range")
    if abs(ch["v_charge"] - c["series"] * c["v_charge"]) > 1e-6:
        fail("charger voltage is not series times the cell charge voltage")
    if not ch["order_md_names_bq24133"]:
        fail("ORDER.md does not name the BQ24133")

    n = doc["ntc"]
    for key in ("beta", "r_25_ohm", "bias_ohm", "parallel_ohm", "bead_ohm_0c", "bead_ohm_25c", "bead_ohm_60c", "stop_cold_frac", "stop_hot_frac"):
        if n[key] is None:
            fail("NTC field %s was not found in the sources" % key)
    if n["r_25_ohm"] and n["bead_ohm_25c"] and abs(n["r_25_ohm"] - n["bead_ohm_25c"]) > 1e-6:
        fail("bead 25 C resistance disagrees between the netlist and the charger check")

    s = doc["servos"]
    if str(s["order_need"]) not in ("", str(s["count"])):
        fail("order servo need disagrees with the servo ids on that order line")
    if s["count"] != 14:
        fail("servo count is %s" % s["count"])
    missing = [i for i in s["ids"] if i not in {c["id"] for c in load_yaml(NETLIST)["components"]}]
    if missing:
        fail("order servos missing from the netlist: %s" % ", ".join(missing))
    fresh = joint_limits()
    got = s.get("joint_limits") or {}
    if set(got) != set(fresh):
        fail("joint limits do not match software/servo_limits.json")
    else:
        for name, row in fresh.items():
            for key, val in row.items():
                if not near(got[name].get(key), val, 1e-6):
                    fail("joint %s %s disagrees with servo_limits.json" % (name, key))
    if not isinstance(doc["mass"].get("robot_kg"), (int, float)):
        fail("whole-duck mass is missing from the CAD mass model")
    pair = mass_pair()
    if pair is not None:
        if abs(pair["mujoco_kg"] - pair["rollup_kg"]) > 0.005:
            fail("MuJoCo total %.4f kg differs from the BOM mass rollup %.4f kg" % (pair["mujoco_kg"], pair["rollup_kg"]))
        if abs(float(doc["mass"]["robot_kg"]) - pair["mujoco_kg"]) > 0.005:
            fail("parts mass %.4f kg disagrees with the MuJoCo loaded total %.4f kg" % (float(doc["mass"]["robot_kg"]), pair["mujoco_kg"]))

    rest = doc["rest"]
    if rest["stop_c"] <= rest["resume_c"]:
        fail("rest stop is not above the resume temperature")
    return bad


def load():
    if not os.path.exists(PARTS_PATH):
        raise SystemExit("missing %s (run parts_truth.py --write)" % rel(PARTS_PATH))
    return load_yaml(PARTS_PATH)


def check():
    live = derive()
    bad = list(problems(live))
    if not os.path.exists(PARTS_PATH):
        bad.append("parts.yaml is missing")
        return bad
    saved = load()
    if not same(saved, live):
        bad.append("parts.yaml disagrees with the netlist, the limits file, or the order")
    bad.extend(problems(saved))
    # unique, keep order
    out = []
    for row in bad:
        if row not in out:
            out.append(row)
    return out


def write():
    doc = derive()
    bad = problems(doc)
    if bad:
        for row in bad:
            print("FAIL", row)
        raise SystemExit(1)
    text = yaml.safe_dump(doc, sort_keys=False, allow_unicode=False)
    if "\u2014" in text or "\u2013" in text:
        raise SystemExit("parts file contains a dash that is not a hyphen")
    with open(PARTS_PATH, "w", encoding="utf-8") as f:
        f.write("# One parts file. Generated by altaay_lab/twin/parts_truth.py --write.\n")
        f.write("# Prices are not in this file. Do not edit by hand.\n")
        f.write(text)
    print("wrote %s" % rel(PARTS_PATH))
    return 0


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--write" in argv:
        return write()
    bad = check()
    if bad:
        for row in bad:
            print("FAIL", row)
        return 1
    print("PASS parts file matches the netlist, the limits, and the order")
    return 0


if __name__ == "__main__":
    sys.exit(main())
