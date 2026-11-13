"""Fault injection on the electrical and thermal twins. CPU only.

Ten product faults. Thermal rows call twin/thermal/twin_thermal.py through
thermal_cases.py. Electrical rows are arithmetic on numbers already in the
lab files. A sim row is not a hardware pass.

  python3 altaay_lab/test/fault_inject.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import thermal_cases as TC  # noqa: E402

LAB = TC.LAB
OUT = os.path.join(HERE, "results", "fault_inject.json")

# RPN = severity x occurrence x detection, each 1 to 10.
# Severity: effect if the fault happens. Occurrence: how available the fault
# is in the current design, not a field rate. Detection: whether the duck, as
# designed, notices before the harm. A script in this folder is not detection.
# SAE J1739 is the RPN form used here. The 2019 AIAG-VDA handbook ranks actions
# differently; this table keeps RPN because the playbook asked for RPN.
SCORES = [
    dict(id="ntc_open_short", S=8, O=4, D=8,
         title="Pack NTC open or short, and the charger IC does not see it"),
    dict(id="fall", S=7, O=6, D=6,
         title="Fall, get-up miss, structure under the lab margin"),
    dict(id="cable_chafe", S=8, O=4, D=7,
         title="Cable chafe to a low resistance, fuse rating not exceeded"),
    dict(id="limp_sit_slip", S=6, O=7, D=5,
         title="Limp sit slips or unloads the wells"),
    dict(id="pack_no_trip", S=9, O=3, D=7,
         title="Pack short and no 3S protector part is on the bill"),
    dict(id="camera_dock_miss", S=5, O=9, D=4,
         title="Camera misses the cloth at the sit"),
    dict(id="charger_stuck_on", S=8, O=3, D=6,
         title="Charger stays at 1 A past the end of charge"),
    dict(id="rail_on_while_docked", S=6, O=4, D=5,
         title="Servo rail turns on while the duck is still on the mat"),
    dict(id="pack_nuisance_trip", S=5, O=6, D=4,
         title="Walk peak sits inside the 13 A to 21 A watch band"),
    dict(id="pi_brownout", S=7, O=3, D=5,
         title="5 V rail collapses when the BEC output falls"),
    dict(id="bec_failure", S=7, O=3, D=4,
         title="BEC output collapses or the pass element shorts"),
]


def rpn_table():
    rows = []
    for s in SCORES:
        r = dict(s)
        r["RPN"] = s["S"] * s["O"] * s["D"]
        rows.append(r)
    rows.sort(key=lambda x: (-x["RPN"], x["id"]))
    return rows


def ntc_window():
    """LM393 window from CHARGER_BOARD.md. Chip TS is a fixed divider.

    Cold divider 10.0 kOhm over 28.0 kOhm. Hot divider 10.0 kOhm over 2.80 kOhm.
    NTC is the bottom of a 10.0 kOhm top. Open NTC is the top of the rail.
    Short NTC is 0 V. BQ24133 TS is 10.0 kOhm over 15.0 kOhm, fraction 0.60,
    which the chip treats as inside its own window (BQ24133_BOARD.md).
    """
    cold_th = 28000.0 / (10000.0 + 28000.0)
    hot_th = 2800.0 / (10000.0 + 2800.0)
    ts = 15000.0 / (10000.0 + 15000.0)

    def frac(r_ntc):
        if r_ntc is None:
            return 1.0
        return r_ntc / (10000.0 + r_ntc)

    def inhibit(r_ntc):
        f = frac(r_ntc)
        return f >= cold_th or f <= hot_th

    points = {
        "open": None,
        "short": 0.0,
        "at_0C": 31770.0,
        "at_25C": 10000.0,
        "at_60C": 2472.0,
    }
    rows = []
    for name, r in points.items():
        f = frac(r)
        rows.append(dict(
            name=name,
            r_ohm=r,
            fraction=round(f, 4),
            lm393_inhibits=inhibit(r),
            chip_ts_fraction=round(ts, 4),
            chip_ts_allows=0.488 < ts < 0.725,
        ))
    # Stuck comparator: the inhibit FET does not pull ISET down.
    stuck = dict(
        name="lm393_stuck_off",
        lm393_inhibits=False,
        charge_continues=True,
        chip_ts_still_allows=True,
        note="calc only. If the LM393 path fails, the fixed TS divider still looks valid.",
    )
    ok = {r["name"]: r["lm393_inhibits"] for r in rows}
    if not (ok["open"] and ok["short"] and ok["at_0C"] and ok["at_60C"] and not ok["at_25C"]):
        raise SystemExit("NTC window arithmetic does not match the board note")
    if abs(ts - 0.60) > 0.001:
        raise SystemExit("TS fraction %s" % ts)
    return dict(label="calc only", cold_th=round(cold_th, 4), hot_th=round(hot_th, 4), rows=rows, stuck=stuck)


def trips(i_a, dur_s, thresh_a, delay_s):
    return bool(i_a >= thresh_a and dur_s + 1e-12 >= delay_s)


def pack_and_fall():
    """Watch band 13 A to 21 A is calc only from the cited 17 A plus or minus 4 A.

    The 2S Tenergy band (17 A to 27 A, 8 ms plus or minus 4 ms) is a different
    board. No 3S protector part number is on the bill.
    """
    cases = []
    # Duration of the 15.57 A peak is not in the summary. A sustained value
    # (longer than 8 ms) is the case scored here.
    for name, i_a, dur in (
        ("run_C_peak_sustained", 15.57, 0.020),
        ("sts12_0.15_peak_sustained", 9.527, 0.020),
        ("old_2s_shove", 20.0, 0.013),
    ):
        row = dict(name=name, i_A=i_a, duration_s=dur, label="calc only")
        row["trips_at_13A_8ms"] = trips(i_a, dur, 13.0, 0.008)
        row["trips_at_17A_8ms"] = trips(i_a, dur, 17.0, 0.008)
        row["trips_at_21A_8ms"] = trips(i_a, dur, 21.0, 0.008)
        row["trips_at_17A_12ms"] = trips(i_a, dur, 17.0, 0.012)
        cases.append(row)
    return dict(
        label="calc only",
        band_A=[13.0, 21.0],
        band_note="Watch band in TWIN_CHECKLIST from the cited 17 A plus or minus 4 A. Not a 3S datasheet.",
        tenergy_2s_A=[17.0, 27.0],
        protector_part="BLOCKER. No 3S protector part number.",
        cases=cases,
    )


def chafe():
    """Full-pack short through a nick. Calc only.

    Path ohms are the lab's published parts: 3 x 15 mOhm cells, BMS 25 mOhm max,
    fuse 6 mOhm, XT30 2 mOhm, switch 13 mOhm at a 4.5 V gate, wires 8.8 mOhm.
    """
    r_path = 3 * 0.015 + 0.025 + 0.006 + 0.002 + 0.013 + 0.0088
    v = 12.6
    rows = []
    for r_nick in (1.0, 0.1, 0.05, 0.01):
        i = v / (r_path + r_nick)
        rows.append(dict(
            r_nick_ohm=r_nick,
            i_A=round(i, 2),
            p_nick_W=round(i * i * r_nick, 1),
            above_15A_fuse_rating=i > 15.0,
            above_21A_watch=i > 21.0,
        ))
    return dict(
        label="calc only",
        v_oc_V=v,
        r_path_ohm=round(r_path, 4),
        fuse_A=15.0,
        local_temperature="BLOCKER. The thermal twin has no nick node.",
        fuse_opening_time="BLOCKER. The fuse curve was not applied.",
        rows=rows,
    )


def pi_and_bec(sts):
    bus_min = sts["bus_min"]
    bec_min = sts["bec_out_min"]
    return dict(
        label="calc only for the threshold, sim pass only for the STS12 voltages",
        walk_bus_min_V=bus_min,
        walk_bec_out_min_V=bec_min,
        bench_input_floor_V=6.0,
        walk_above_floor=bus_min >= 6.0 and bec_min >= 6.0,
        injected_bus_V=5.4,
        injected_below_floor=5.4 < 6.0,
        pi_warning_voltage="BLOCKER. The Pi under-voltage threshold was not opened for this playbook.",
        bec_open="Servos go to 0 V. The netlist puts the Pi on the same switch, so the Pi goes with them.",
        bec_pass_short=(
            "A shorted pass element puts the pack on the servos. On this 3S walk the "
            "BEC is already in dropout, so the voltage is the walk voltage, not a new 16 V."
        ),
        holds_12v=sts["bec_in_min"] >= TC.V_REG_MIN,
    )


def charge_allowed(samples_on_cloth, signature_ok, leak_ok):
    """Specification rule. Not code on the duck. The charge program is unwritten."""
    return bool(samples_on_cloth > 0 and signature_ok and leak_ok)


def camera():
    # CAD check only, already in TWIN_CHECKLIST: the recorded sit sees 0 of 13
    # disc samples and 0 of 27 ring samples.
    samples = 0
    allowed = charge_allowed(samples, True, True)
    return dict(
        label="CAD check only for the miss, specification test for the rule",
        disc_samples_seen=samples,
        ring_samples_seen=0,
        charge_allowed=allowed,
        safety_rule_holds=allowed is False,
        mission="FAIL. The sit does not see the cloth, so this rule never starts a charge.",
        product_code="MISSING. Nest vision and the charge program are not written.",
    )


def limp():
    path = os.path.join(LAB, "twin", "sit", "rail_off_sit.json")
    doc = json.load(open(path))
    margin = float(doc["stripe_margin_mm"])
    rows = []
    for row in doc["rows"]:
        dy = abs(float(row["dy_mm"]))
        seated = (
            (not row["blew"])
            and dy <= margin
            and float(row["min_seat_N"]) >= 0.2
        )
        item = dict(
            name=row["name"],
            label="sim pass only",
            seconds=row["seconds"],
            dy_mm=row["dy_mm"],
            dx_mm=row["dx_mm"],
            min_seat_N=row["min_seat_N"],
            blew=row["blew"],
            lateral_inside=dy <= margin,
            wells_loaded=seated,
        )
        if "undock" in row:
            item["rail_return_min_seat_N"] = row["undock"]["hold_before_ramp_min_seat_N"]
            item["rail_return_keeps_wells"] = row["undock"]["hold_before_ramp_min_seat_N"] >= 0.2
        rows.append(item)
    return dict(
        label="sim pass only",
        source="altaay_lab/twin/sit/rail_off_sit.json",
        margin_mm=margin,
        margin_note="calc only, (20 mm stripe - 3 mm well) / 2",
        friction="BLOCKER. Sheet does not print unpowered friction.",
        rows=rows,
    )


def thermal_faults():
    """Sits. Charger loss 0.963 W is calc only from BQ24133_HEAT (1.00 A, 12.6 V, eta 0.929)."""
    print("thermal faults", flush=True)
    cut = TC.sit(0.963, 0.0, 0.0, 1.0, "central", 25.0, hours=6.0, n_cells=3)
    print(" cut rail", cut["cell_end_C"], cut["trunk_wall_end_C"], cut["knee_reading_max_C"], flush=True)
    if not (26.0 <= cut["cell_end_C"] <= 32.0):
        raise SystemExit("cut-rail cells %s C, expected near 28" % cut["cell_end_C"])
    if cut["knee_reading_max_C"] > 30.0:
        raise SystemExit("cut-rail knee %s C, expected the room" % cut["knee_reading_max_C"])
    rail_idle = TC.sit(0.963, 12.6, TC.I_IDLE_C001, 1.0, "central", 25.0, hours=6.0, n_cells=3)
    print(" rail 21 mA", rail_idle["cell_end_C"], rail_idle["knee_reading_max_C"], rail_idle["bec_case_end_C"], flush=True)
    rail_nl = TC.sit(0.963, 12.0, TC.I_NL_C018, 1.0, "central", 25.0, hours=6.0, n_cells=3)
    print(" rail 180 mA", rail_nl["cell_end_C"], rail_nl["knee_reading_max_C"], rail_nl["bec_case_end_C"], flush=True)
    if rail_nl["knee_reading_max_C"] <= rail_idle["knee_reading_max_C"]:
        raise SystemExit("180 mA case should be hotter than 21 mA")
    i_21 = 14 * TC.I_IDLE_C001
    i_180 = 14 * TC.I_NL_C018
    return dict(
        label="sim pass only",
        charger_W=0.963,
        charger_W_note="calc only, 12.6 V * 1.00 A * (1/0.929 - 1)",
        cut_rail_6h=cut,
        rail_on_c001_idle_6h=rail_idle,
        rail_on_c018_noload_6h=rail_nl,
        c018_noload_note=(
            "0.180 A is the C018 running no-load current at 12 V, cited. "
            "It is an upper bound if powered servos spin free. It is not the torque-off current. "
            "Torque-off current on the C018 is BLOCKER."
        ),
        termination_A=0.10,
        idle_21mA_total_A=round(i_21, 3),
        noload_180mA_total_A=round(i_180, 3),
        termination_blocked_at_21mA=i_21 > 0.10,
        termination_blocked_at_180mA=i_180 > 0.10,
        timer_h=6.35,
        timer_note="calc only, 68 nF * 5.6 min/nF. A stuck 1 A past that timer is a second fault.",
        overvoltage="BLOCKER in this thermal model. It does not integrate cell voltage.",
    )


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    sts = TC.pack_corner(TC.load_sts12(), "typical")
    doc = dict(
        label="sim pass only or calc only, per row",
        rpn=rpn_table(),
        ntc=ntc_window(),
        pack=pack_and_fall(),
        chafe=chafe(),
        pi_bec=pi_and_bec(sts),
        camera=camera(),
        limp=limp(),
        thermal=thermal_faults(),
    )
    # Specification checks that should hold on the numbers above.
    if doc["camera"]["charge_allowed"]:
        raise SystemExit("camera miss allowed a charge")
    if not doc["thermal"]["termination_blocked_at_21mA"]:
        raise SystemExit("21 mA idle should block 0.10 A termination")
    zero = [r for r in doc["limp"]["rows"] if r["name"] == "zero_joint_and_floor_friction"][0]
    if zero["wells_loaded"]:
        raise SystemExit("zero friction was scored as seated")
    train = [r for r in doc["limp"]["rows"] if r["name"] == "training_friction_mu_0.8"][0]
    if train.get("rail_return_keeps_wells", True):
        raise SystemExit("rail return should unload the wells in the filed sit")
    json.dump(doc, open(OUT, "w"), indent=1)
    print("top RPN", [(r["id"], r["RPN"]) for r in doc["rpn"][:5]])
    print("wrote", os.path.relpath(OUT, os.path.join(LAB, "..")))


if __name__ == "__main__":
    main()
