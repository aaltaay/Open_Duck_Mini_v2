"""phase2_check.py: the length (reach) check of the cables phase 2 changed (D10, D12, D13, SP1, SP2, SP4, SP5), calc only.
Same rule as cables3d/check_cables.py: every wire's cut >= its worst routed length over the range of the joints its cable
crosses + SLACK_MM (2 x 20 mm). check_cables.py itself goes over the 3 GB RAM cap of this session when it builds its grid
from an empty scratch folder, so its clearance and rub checks were not rerun for these cables (noted on each one).
Worst length: every joint the cable crosses at 5 values (lower limit, half, 0, half, upper limit), all combinations.
"""
import itertools
import json
import os

import numpy as np

from common import CABLES3D, scene

SLACK = 40.0
OLD = "/home/user/v1_out/3d/cables3d_head.json"      # cables3d.json of the phase 1 commit (check_cables.py chain results)
SPCUT = {"SP1": (150, 160), "SP2": (150, 150), "SP4": (400, 420), "SP5": (430, 450)}   # made leads: old cut, new cut
IDS = ("D10", "D12", "D13", "SP1", "SP2", "SP4", "SP5")


def main():
    S = scene()
    c3 = json.load(open(CABLES3D))
    out = {}
    H = {c["id"]: c for c in json.load(open(OLD))["cables"]}
    lead = json.load(open("/home/user/v1_out/3d/phase2_data_out.json"))
    for c in c3["cables"]:
        if c["id"] in SPCUT:   # chains through the SPV/SPG splices: keep check_cables.py's chain numbers, add the lead-in
            h, li, (c0, c1) = H[c["id"]], lead.get(c["id"] + " lead-in mm", 0.0), SPCUT[c["id"]]
            hw = {(w["from"], w["to"]): w for w in h["wires"]}
            for w in c["wires"]:
                ow = hw.get((w["from"], w["to"]))
                if not ow or "main" not in (w.get("runs") or []):
                    continue
                for k in ("length_max_mm", "length_zero_mm", "required_mm"):
                    if ow.get(k) is not None:
                        w[k] = round(ow[k] + li, 1)
                if w.get("cut_mm") == c0:
                    w["cut_mm"] = c1
                if ow.get("margin_mm") is not None:
                    w["margin_mm"] = round(ow["margin_mm"] - li + (c1 - c0), 1)
            m = round(h["margin_mm"] - li + (c1 - c0), 1)
            c.update(length_zero_mm=round(h["length_zero_mm"] + li, 1), length_max_mm=round((h.get("length_max_mm") or 0) + li, 1),
                     worst_mm=round(h["worst_mm"] + li, 1), required_mm=round(h["required_mm"] + li, 1), margin_mm=m,
                     check="pass with notes" if m >= 0 else "test fit",
                     findings=list(h.get("findings") or []) + ["phase 2: %.1f mm lead-in from the SPV and SPG splice bodies (power_splice box) "
                                                               "to the routed start; cut %d -> %d mm (made lead, no purchase); chain margin "
                                                               "%.1f mm (twin/complete3d/phase2_check.py, calc only)" % (li, c0, c1, m)])
            out[c["id"]] = (c["check"], c["worst_mm"], c["margin_mm"])
            continue
        if c["id"] not in IDS:
            continue
        joints = [j for j in (c.get("joints") or []) if j in S.joints]
        grid = [np.linspace(S.joints[j]["lo"], S.joints[j]["hi"], 5) for j in joints]
        cfgs = [dict(zip(joints, v)) for v in itertools.product(*grid)] if joints else [{}]
        Ts = [S.link_T(cfg) for cfg in cfgs]
        runlen = {}
        for r in c["runs"]:
            L = []
            for T in Ts:
                W = np.array([(T[q["link"]] @ np.r_[q["p"], 1.0])[:3] for q in r["points"]])
                L.append(float(np.sum(np.linalg.norm(np.diff(W, axis=0), axis=1))))
            runlen[r["name"]] = (L[0] if not joints else float(np.median(L)), min(L), max(L))
            r["length_zero_mm"] = round(float(np.sum(np.linalg.norm(np.diff(np.array(
                [(S.T0[q["link"]] @ np.r_[q["p"], 1.0])[:3] for q in r["points"]]), axis=0), axis=1))), 1)
            r["length_min_mm"], r["length_max_mm"] = round(min(L), 1), round(max(L), 1)
        worst_w, verdict = None, "pass"
        for w in c["wires"]:
            rs = w.get("runs") or ["main"]
            wl = sum(runlen[x][2] for x in rs if x in runlen)
            w["length_max_mm"] = round(wl, 1)
            w["length_zero_mm"] = round(sum(runlen[x][0] if not joints else [r for r in c["runs"] if r["name"] == x][0]["length_zero_mm"]
                                            for x in rs if x in runlen), 1)
            w["length_min_mm"] = round(sum(runlen[x][1] for x in rs if x in runlen), 1)
            w["required_mm"] = round(wl + SLACK, 1)
            cut = w.get("cut_mm")
            if cut:
                w["margin_mm"] = round(cut - wl - SLACK, 1)
                if cut < wl:
                    verdict = "fail"
                elif cut < wl + SLACK and verdict == "pass":
                    verdict = "test fit"
                if worst_w is None or w["margin_mm"] < worst_w["margin_mm"]:
                    worst_w = w
        main_r = [r for r in c["runs"] if r["name"] == c["runs"][0]["name"]][0]
        c.update(length_zero_mm=main_r["length_zero_mm"], length_max_mm=main_r["length_max_mm"], length_min_mm=main_r["length_min_mm"],
                 worst_mm=worst_w["length_max_mm"] if worst_w else None, required_mm=worst_w["required_mm"] if worst_w else None,
                 margin_mm=worst_w["margin_mm"] if worst_w else None, check=verdict if verdict != "pass" else "pass with notes",
                 findings=["length: worst wire %s mm + %d slack = %s mm against cut %s mm, margin %s mm (twin/complete3d/phase2_check.py, "
                           "calc only; %d joint poses)" % (worst_w["length_max_mm"], SLACK, worst_w["required_mm"], worst_w.get("cut_mm"),
                                                         worst_w["margin_mm"], len(cfgs)) if worst_w else "no cut length",
                           "clearance and rub checks of check_cables.py not rerun for this cable in phase 2 (RAM cap); the route "
                           "is the CAD-checked one named in its note"])
        out[c["id"]] = (c["check"], c["worst_mm"], c["margin_mm"])
    json.dump(c3, open(CABLES3D + ".tmp", "w"), indent=1)
    os.replace(CABLES3D + ".tmp", CABLES3D)
    print(json.dumps(out))


if __name__ == "__main__":
    main()
