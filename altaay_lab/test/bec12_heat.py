"""3S BEC case temperature at a 12.0 V setpoint, and continuous-walk heat vs 60 C.

The published thermal tables never ran a 3S BEC case (twin/life/LIFE.md). The
3S walk on file (problems/sts12.json) used a 16 V setpoint, so the BEC stayed
in dropout. This script asks what a 12.0 V setpoint does on that same walk,
using twin/thermal/twin_thermal.py.

Run from the repo root:
  python3 altaay_lab/test/bec12_heat.py

Nothing here was measured on a board or a servo.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import thermal_cases as TC  # noqa: E402
import gate_p45b  # noqa: E402  (imported by thermal_cases; named for the CSV)

OUT_DIR = os.path.join(HERE, "results")
CSV = gate_p45b.OLD_CSV


def _fail(msg):
    raise SystemExit("sanity check failed: %s" % msg)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    doc = TC.load_sts12()
    kt = float(doc["sheet"]["kt_Nm_per_A"])
    if abs(kt - 1.0896) > 1e-6:
        _fail("sts12 Kt changed: %s" % kt)
    typical = TC.pack_corner(doc, "typical")
    high = TC.pack_corner(doc, "high-side")
    if typical["bec_in_min"] >= TC.V_REG_MIN:
        _fail("STS12 typical BEC input can hold 12.0 V; the dropout conclusion changed")
    if high["bec_in_min"] >= TC.V_REG_MIN:
        _fail("STS12 high-side BEC input can hold 12.0 V; the dropout conclusion changed")

    # Electrical point first, so a bad current is caught before the long runs.
    points = {}
    for name, pack in (("typical", typical), ("high-side", high)):
        for corner, p5 in (("central", 3.0), ("high", 5.0)):
            sp = TC.bec_split(pack["i_mean"], pack["bus_mean"], p5)
            drop = TC.dropout_loss_w(sp["i_bec_A"])
            reg, p_out = TC.regulate_loss_w(sp["i_bec_A"], 0.85 if corner == "central" else 0.80)
            points["%s|%s" % (name, corner)] = dict(
                label="calc only",
                i_pack_mean_A=pack["i_mean"],
                bus_mean_V=pack["bus_mean"],
                bec_in_min_V=pack["bec_in_min"],
                bec_out_mean_V=pack["bec_out_mean"],
                bec_out_min_V=pack["bec_out_min"],
                holds_12v=pack["bec_in_min"] >= TC.V_REG_MIN,
                **{k: round(v, 4) if isinstance(v, float) else v for k, v in sp.items()},
                dropout_loss_W=round(drop, 3),
                regulate_loss_W_if_it_held=round(reg, 3),
                regulate_pout_W_if_it_held=round(p_out, 3),
            )
    drop_w = points["typical|central"]["dropout_loss_W"]
    if not (0.8 <= drop_w <= 2.2):
        _fail("dropout loss %s W is outside 0.8 to 2.2" % drop_w)
    if points["typical|central"]["regulate_loss_W_if_it_held"] <= drop_w + 3:
        _fail("regulating loss should be several watts above the dropout loss")

    old = TC.session_regulating_loss(CSV, 0.85)
    if not (4.0 <= old["loss_mean_W"] <= 8.0):
        _fail("2S session regulating loss %s W is not the old ~5 W case" % old["loss_mean_W"])

    print("confirmation walk, existing CSV, central", flush=True)
    TC.apply_two_cell()
    confirm = []
    for room in (25.0, 32.0):
        row = gate_p45b.run_walk(CSV, "central", room, minutes=40.0)
        row["label"] = "sim pass only"
        row["note"] = (
            "Existing p45b_sheet session. Pack voltage in that file is the 2S bus "
            "(about 8.2 V). Not the 12 V gait. Friction heat omitted."
        )
        confirm.append(row)
        k = row["right_knee"]
        print(" confirm", room, "knee60", k["minutes_to_60C"], "max", k["reading_max_C"], flush=True)
    k25 = confirm[0]["right_knee"]["minutes_to_60C"]
    if k25 is None or not (2.0 <= k25 <= 5.0):
        _fail("confirmation knee 60 C time %s min, expected about 3.3" % k25)

    print("12 V setpoint walks", flush=True)
    walks = []
    for mode in ("dropout", "regulate"):
        corners = ("central", "high") if mode == "dropout" else ("central",)
        rooms = (25.0, 32.0) if mode == "dropout" else (25.0,)
        for corner in corners:
            for room in rooms:
                print(" ", mode, corner, room, flush=True)
                row = TC.walk_scaled(CSV, corner, room, typical, mode, minutes=40.0)
                walks.append(row)
                print(
                    "   bec", row["bec_case_end_C"],
                    "loss", row["bec_loss_mean_W"],
                    "knee60", row["minutes_to_reading_60C"],
                    "knee", row["knee_reading_max_C"],
                    "cell", row["cell_max_C"],
                    flush=True,
                )

    drop_rows = [r for r in walks if r["mode"] == "dropout" and r["corner"] == "central"]
    reg_row = [r for r in walks if r["mode"] == "regulate"][0]
    d25 = [r for r in drop_rows if r["room_C"] == 25.0][0]
    if not (d25["room_C"] < d25["bec_case_end_C"] < 80.0):
        _fail("dropout BEC case %s C" % d25["bec_case_end_C"])
    if d25["cell_max_C"] >= 80.0:
        _fail("dropout walk cells %s C" % d25["cell_max_C"])
    if reg_row["bec_case_end_C"] < d25["bec_case_end_C"] + 15.0:
        _fail("regulating case is not hotter than dropout")
    if d25["minutes_to_reading_60C"] is None:
        # A miss is a result, not a crash. The confirmation run still leaves 60 C.
        print("note: scaled 12 V reading did not reach 60 C in 40 min", flush=True)
    elif not (1.0 <= d25["minutes_to_reading_60C"] <= 20.0):
        _fail("12 V knee 60 C time %s min looks wrong" % d25["minutes_to_reading_60C"])

    out = dict(
        label="sim pass only for temperatures, calc only for the 12 V current scale",
        bec_setpoint_V=12.0,
        regulates_only_if_input_V=TC.V_REG_MIN,
        dropout_V=TC.V_DROP,
        dropout_note="0.30 V is the lab assumption. Castle publishes no dropout and no efficiency.",
        sts12_does_not_hold_12v=True,
        sts12_reason=(
            "Typical BEC input minimum is %.3f V and high-side is %.3f V, "
            "both under %.1f V, so a 12.0 V setpoint stays in dropout on that walk."
            % (typical["bec_in_min"], high["bec_in_min"], TC.V_REG_MIN)
        ),
        electrical=points,
        old_2s_session_if_regulated=old,
        confirmation_existing_csv=confirm,
        walks_12v_setpoint=walks,
        window=dict(
            servo_operating_C=[-20, 60],
            servo_torque_off_C=70,
            cell_discharge_C=[-40, 60],
            pla_hdt_edge_C=49,
            note="Servo and cell ends are the opened sheets. 49 C is the thermal twin PLA edge.",
        ),
        high_corner_note=(
            "The high corner stacks every pessimistic thermal parameter, including "
            "cf 1.25. A reading near 200 C is that stack, the same warning already "
            "in THERMAL_TWIN.md. It is not a temperature to quote as the knee."
        ),
    )
    path = os.path.join(OUT_DIR, "bec12_heat.json")
    json.dump(out, open(path, "w"), indent=1)
    print("wrote altaay_lab/test/results/bec12_heat.json")
    return out


if __name__ == "__main__":
    main()
