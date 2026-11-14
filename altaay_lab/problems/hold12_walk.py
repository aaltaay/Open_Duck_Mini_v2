#!/usr/bin/env python3
"""Short run C walk at a held 12.0 V servo rail. Sim pass only. CPU only.

Same sheet patch as problems/sts12.py. One corner, 10 s, 0.15 m/s.
The 3S set point is held (D65 buck-boost), not the Castle dropout model.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault(
    "ODM_ONNX",
    os.path.join(HERE, "retrain_sts12", "sts12_runC_policy.onnx"),
)
sys.path.insert(0, HERE)
import sts12  # noqa: E402


def main():
    r = sts12.ET.run(
        mass="ours", walk="backlash", cmd=(0.15, 0.0, 0.0), dur=10.0,
        supply="net", corner="typical", extra=dict(BEC_V=12.0, BEC_HOLD=1),
        cell="p45b3", q0=0.0, servo_mode="sheet", guard=None,
        keep_full=False, stop_on_fall=True, t_stats=0.0, label="hold12",
    )
    knees = sts12.knees_of(r)
    fall = r["falls"] or "none"
    gait = r.get("gait") or {}
    print("label sim pass only")
    print("fall", fall)
    print("dur_s", r.get("dur_s"))
    print("gait", gait)
    print("knees", knees)
    path = os.path.join(HERE, "HOLD12_WALK.md")
    text = "\n".join([
        "# Held 12.0 V walk",
        "",
        "Sim pass only. CPU only. Run C policy, backlash, typical corner, 10 s, command 0.15 m/s.",
        "The servo rail is held at 12.0 V (D65). This is not a hardware pass.",
        "",
        "| Item | Value |",
        "|---|---|",
        "| Fall | %s |" % fall,
        "| Duration | %s s |" % r.get("dur_s"),
        "| Forward speed vx | %s m/s |" % gait.get("vx"),
        "| Tracking ratio | %s |" % gait.get("track_lin"),
        "| Knee min L / R | %s / %s V |" % (
            knees.get("left_knee"), knees.get("right_knee")),
        "| Pack peak | %s A |" % knees.get("i_pack_peak_A"),
        "| Rail minimum | %s V |" % knees.get("v_bec_out_min_V"),
        "",
    ])
    open(path, "w", encoding="utf-8").write(text)
    print("wrote", path)


if __name__ == "__main__":
    main()
