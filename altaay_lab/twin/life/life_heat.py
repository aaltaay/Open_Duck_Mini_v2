#!/usr/bin/env python3
"""Closed-shell heat map for the finished duck.

Reuses altaay_lab/twin/thermal/twin_thermal.py and gate_p45b.py. No new thermal
model. The walk current is the existing P45B backlash session. The charger
watts are the 2.30 W and 3.50 W calc in circuitry/CHARGER_BOARD.md (PR 40),
not the older 1.9 W to 3.2 W band. The 55 C stop and 45 C restart are
software/knee_heat.py (PR 37). Torque-off rest is that file's idle posture.

Rooms are 22 C and 32 C. A 25 C walk is run only as a check against
gate_p45b.json (right knee 3.33 min to 60 C, body 94.67 C).

Every temperature this file prints is sim pass only. It is not a measurement.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
THERM = os.path.abspath(os.path.join(HERE, "..", "thermal"))
sys.path.insert(0, THERM)
import gate_p45b as G  # noqa: E402
import twin_thermal as TT  # noqa: E402

# Published stand row, tables.md "stand_in_place", full pack, sim pass only.
# Order is TT.NAMES. Board and copper are the table, not a new motor model.
STAND_CU = np.array([0.00, 0.31, 0.01, 0.88, 0.00, 0.00, 0.02, 0.00, 0.00, 0.00, 0.36, 0.02, 0.58, 0.04])
STAND_BOARD = np.array([0.00, 0.02, 0.00, 0.05, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.02, 0.00, 0.03, 0.00])
# Published backlash row, same file, used only as the electrical_point reference.
BACK_CU = np.array([0.13, 0.71, 1.49, 4.74, 1.52, 0.24, 1.21, 1.11, 0.65, 0.25, 0.57, 1.06, 5.17, 1.64])
BACK_BOARD = np.array([0.01, 0.04, 0.08, 0.25, 0.08, 0.01, 0.06, 0.06, 0.03, 0.01, 0.03, 0.05, 0.27, 0.09])
IDLE_W = 0.15  # table idle column, 21 mA at the servo volts used for that table


def _cross(t, y, thr):
    m = np.where(np.asarray(y) >= thr)[0]
    if not len(m):
        return None
    return round(float(t[m[0]]) / 60.0, 2)


def _servo_pack(cu, board, idle):
    z = np.zeros(14)
    return dict(P_cu25=np.asarray(cu, float), P_board=np.asarray(board, float), P_fric=z, P_idle=np.full(14, idle), i2=z)


def _trunk_idle(c, charge_a, charger_w):
    """Same trunk terms as gate_p45b._trunk_sit. charge_a is 0 when not charging."""
    p_servo = 14 * G.I_IDLE * G.V_BUS
    bec_loss = p_servo * (1.0 / G.ETA_BEC - 1.0)
    i = charge_a
    return dict(cells=2 * i * i * TT.PARAMS["R_cell"], holder=i * i * c["R_holder"], bms=i * i * c["R_bms"],
                fuse=i * i * TT.PARAMS["R_fuse"], xt30=i * i * TT.PARAMS["R_xt30"], switch=0.0,
                wires=i * i * TT.PARAMS["R_wires"], bec=bec_loss, bec_leads=0.0, logic=0.15, charger=charger_w)


def _pack_from_run(r, c, heats):
    t = r["t"]
    servos = {}
    for j, n in enumerate(TT.NAMES):
        servos[n] = dict(reading_max_C=round(float(r["max_Ts"][j]), 2),
                         body_max_C=round(float(r["max_Tb"][j]), 2),
                         winding_max_C=round(float(r["max_Tw"][j]), 2),
                         reading_end_C=round(float(r["Ts"][-1, j]), 2),
                         body_end_C=round(float(r["Tb"][-1, j]), 2),
                         minutes_to_55C=_cross(t, r["Ts"][:, j], 55.0),
                         minutes_to_60C=_cross(t, r["Ts"][:, j], 60.0),
                         minutes_to_70C=_cross(t, r["Ts"][:, j], 70.0))
    bec, mos, wall = [], [], []
    for i, key in enumerate(r["state"]):
        H = heats[key]
        hs = TT.hot_spots(H["trunk"], float(r["trunk_air"][i]), c, None)
        bec.append(hs["bec_case"])
        mos.append(hs["switch_mosfets"])
    out = dict(servos=servos,
               cells_max_C=round(float(np.max(r["cells"])), 2),
               cells_end_C=round(float(r["cells"][-1]), 2),
               trunk_air_max_C=round(float(np.max(r["trunk_air"])), 2),
               trunk_air_end_C=round(float(r["trunk_air"][-1]), 2),
               trunk_wall_max_C=round(float(np.max(r["trunk_wall"])), 2),
               trunk_wall_end_C=round(float(r["trunk_wall"][-1]), 2),
               head_air_max_C=round(float(np.max(r["head_air"])), 2),
               head_air_end_C=round(float(r["head_air"][-1]), 2),
               bec_case_max_C=round(float(np.max(bec)), 2),
               bec_case_end_C=round(float(bec[-1]), 2),
               switch_max_C=round(float(np.max(mos)), 2),
               minutes_to_cell_60C=_cross(t, r["cells"], 60.0),
               minutes_to_wall_49C=_cross(t, r["trunk_wall"], 49.0),
               walk_share=round(float(r["walk_share"]), 4))
    # hottest resolved node, winding included but flagged
    hot_name, hot_c, hot_kind = None, -1e9, None
    for n, s in servos.items():
        for kind, key in (("reading", "reading_max_C"), ("body", "body_max_C"), ("winding", "winding_max_C")):
            if s[key] > hot_c:
                hot_name, hot_c, hot_kind = n, s[key], kind
    for kind, key in (("cells", "cells_max_C"), ("trunk_wall", "trunk_wall_max_C"),
                      ("trunk_air", "trunk_air_max_C"), ("head_air", "head_air_max_C"),
                      ("bec_case", "bec_case_max_C"), ("switch", "switch_max_C")):
        if out[key] > hot_c:
            hot_name, hot_c, hot_kind = kind, out[key], "part"
    out["hottest"] = dict(name=hot_name, C=hot_c, kind=hot_kind)
    return out


def _run(heats, sched, c, Ta, t_end, dt, guard=None):
    # Closed shell: the model exchanges no air unless G_vent is set. Leave it unset.
    r = TT.simulate(sched, heats, None, c, Ta, t_end=t_end, dt=dt, guard=guard, record=10.0)
    return _pack_from_run(r, c, heats)


def walk_case(Ta, minutes=40.0):
    path = G.OLD_CSV
    S = G._csv_walk(path)
    c = dict(TT.CORNERS["central"])
    tbin = S["t"]
    r_loop = 2.63  # gate_p45b: this file's name contains "sheet" but the session is the BAM actuator.
    # gate_p45b.py sets r_loop to 2.96 when "sheet" is in the filename. The published
    # 94.67 C body used 2.63 ohm (gate_p45b.json r_loop_ohm for the matching rows is 2.63
    # only if the path did not contain "sheet"). This CSV lives under p45b_sheet, so the
    # current gate_p45b.py would pick 2.96. The published file records 2.63 and 94.67 C.
    # Match the published file, not the filename test. Checked below at 25 C.

    def sched(t, tbin=tbin):
        return int(np.clip(np.searchsorted(tbin, t), 0, len(tbin) - 1))

    heats = {}
    for i in range(len(tbin)):
        i2 = np.nan_to_num(S["im"][i]) ** 2
        ip = float(S["i_pack"][i])
        ib = float(S["i_bec"][i])
        vb = float(S["v_bec"][i])
        bec_loss = max(vb * float(S["i_bec_mean"][i]), 0.0) * (1.0 / c["eta_bec"] - 1.0)
        trunk = dict(cells=2 * ip * ip * TT.PARAMS["R_cell"], holder=ip * ip * c["R_holder"],
                     bms=ip * ip * c["R_bms"], fuse=ip * ip * TT.PARAMS["R_fuse"],
                     xt30=ip * ip * TT.PARAMS["R_xt30"], switch=ip * ip * TT.sw_R_on(vb + 0.3, c),
                     wires=ip * ip * TT.PARAMS["R_wires"], bec=bec_loss, bec_leads=ib * ib * 0.004,
                     logic=0.15, charger=0.0)
        servo = dict(i2=i2, P_cu25=i2 * TT.PARAMS["R_w25"],
                     P_board=i2 * max(r_loop - TT.PARAMS["R_w25"], 0.0),
                     P_fric=np.zeros(14), P_idle=np.full(14, G.I_IDLE * vb))
        heats[i] = dict(servo=servo, trunk=trunk, head=c["P5V"])
    t_end = min(float(tbin[-1]), minutes * 60.0)
    out = _run(heats, sched, c, Ta, t_end, 0.5)
    out.update(room_C=Ta, minutes=round(t_end / 60.0, 2), r_loop_ohm=r_loop, mode="walk_backlash_p45b")
    return out


def _held_first_minutes(S, minutes=4.0):
    """RMS over the first minutes of the session, held steady.

    KNEE_HEAT_STUDY.md uses the first 4 minutes of this log (1.45 A on the
    right knee) held steady for the duty-cycle calc. Same window, every servo.
    """
    m = S["t"] <= minutes * 60.0
    if not np.any(m):
        m = np.ones(len(S["t"]), dtype=bool)
    im = np.sqrt(np.nanmean(np.nan_to_num(S["im"][m]) ** 2, axis=0))
    ip = float(np.sqrt(np.nanmean(S["i_pack"][m] ** 2)))
    ib = float(np.sqrt(np.nanmean(S["i_bec"][m] ** 2)))
    # bec loss uses mean output power, as gate_p45b.run_walk does
    p_bec = float(np.nanmean(np.maximum(S["v_bec"][m] * S["i_bec_mean"][m], 0.0)))
    vb = float(np.nanmean(S["v_bec"][m]))
    return dict(im=im, i_pack=ip, i_bec=ib, p_bec=p_bec, v_bec=vb)


def duty_case(Ta, minutes=90.0):
    """Stop at 55 C, torque off until 45 C. Thresholds from knee_heat.py."""
    S = G._csv_walk(G.OLD_CSV)
    c = dict(TT.CORNERS["central"])
    H = _held_first_minutes(S, 4.0)
    r_loop = 2.63
    i2 = H["im"] ** 2
    bec_loss = H["p_bec"] * (1.0 / c["eta_bec"] - 1.0)
    trunk = dict(cells=2 * H["i_pack"] ** 2 * TT.PARAMS["R_cell"], holder=H["i_pack"] ** 2 * c["R_holder"],
                 bms=H["i_pack"] ** 2 * c["R_bms"], fuse=H["i_pack"] ** 2 * TT.PARAMS["R_fuse"],
                 xt30=H["i_pack"] ** 2 * TT.PARAMS["R_xt30"], switch=H["i_pack"] ** 2 * TT.sw_R_on(H["v_bec"] + 0.3, c),
                 wires=H["i_pack"] ** 2 * TT.PARAMS["R_wires"], bec=bec_loss, bec_leads=H["i_bec"] ** 2 * 0.004,
                 logic=0.15, charger=0.0)
    servo = dict(i2=i2, P_cu25=i2 * TT.PARAMS["R_w25"],
                 P_board=i2 * max(r_loop - TT.PARAMS["R_w25"], 0.0),
                 P_fric=np.zeros(14), P_idle=np.full(14, G.I_IDLE * H["v_bec"]))
    heats = {"walk": dict(servo=servo, trunk=trunk, head=c["P5V"]),
             "off": dict(servo=_servo_pack(np.zeros(14), np.zeros(14), G.I_IDLE * G.V_BUS),
                         trunk=_trunk_idle(c, 0.0, 0.0), head=c["P5V"])}
    guard = dict(stop=55.0, resume=45.0, rest="off")
    out = _run(heats, lambda t: "walk", c, Ta, minutes * 60.0, 1.0, guard=guard)
    rk = int(np.where(np.array(TT.NAMES) == "right_knee")[0][0])
    out.update(room_C=Ta, minutes=minutes, mode="duty_55_45_torque_off",
               walk_minutes=round(out["walk_share"] * minutes, 2),
               held_right_knee_A=round(float(H["im"][rk]), 3),
               held_pack_rms_A=round(H["i_pack"], 3))
    return out


def sit_case(Ta, charger_w, charge_a, mode, hours=6.0):
    c = dict(TT.CORNERS["central"])
    servo = _servo_pack(np.zeros(14), np.zeros(14), G.I_IDLE * G.V_BUS)
    heats = {"off": dict(servo=servo, trunk=_trunk_idle(c, charge_a, charger_w), head=c["P5V"])}
    out = _run(heats, lambda t: "off", c, Ta, hours * 3600.0, 2.0)
    out.update(room_C=Ta, charger_W=charger_w, charge_A=charge_a, mode=mode, hours=hours)
    return out


def torque_on_idle(Ta, hours=3.0):
    """Standing with torque on, watts from tables.md, trunk scaled by electrical_point."""
    c = dict(TT.CORNERS["central"])
    p_stand = float(STAND_CU.sum() + STAND_BOARD.sum() + IDLE_W * 14)
    p_back = float(BACK_CU.sum() + BACK_BOARD.sum() + IDLE_W * 14)
    ep = TT.electrical_point(p_stand, p_back, "full", c, False)
    trunk = TT.trunk_losses(ep, c)
    trunk["charger"] = 0.0
    servo = _servo_pack(STAND_CU, STAND_BOARD, IDLE_W)
    heats = {"stand": dict(servo=servo, trunk=trunk, head=c["P5V"])}
    out = _run(heats, lambda t: "stand", c, Ta, hours * 3600.0, 2.0)
    out.update(room_C=Ta, mode="idle_torque_on", hours=hours,
               P_stand_W=round(p_stand, 2), P_back_ref_W=round(p_back, 2),
               pack_rms_A=round(float(ep["pack_rms"]), 2), bec_loss_W=round(float(ep["P_bec_loss"]), 2))
    return out


def main():
    os.makedirs(HERE, exist_ok=True)
    doc = dict(label="sim pass only",
               tool="altaay_lab/twin/thermal/twin_thermal.py simulate(), P45B constants from gate_p45b.py",
               charger_W=[2.30, 3.50],
               charger_source="circuitry/CHARGER_BOARD.md calc only, 9.5 V times 1.00 A at a 7.2 V and a 6.0 V pack",
               guard="software/knee_heat.py stop 55 C, restart 45 C, torque off",
               closed_shell="no G_vent term; the thermal model already has no air exchange through the leg and neck openings",
               pi="chip temperature is BLOCKER. Head air is the 5 V branch node, not the chip.",
               winding_note="The winding node is the model's 2.5 J/K guess. Do not read it as a measured copper temperature.",
               check_25C=None, walks=[], duties=[], sits=[])
    print("check 25 C", flush=True)
    chk = walk_case(25.0)
    rk = chk["servos"]["right_knee"]
    doc["check_25C"] = dict(minutes_to_60C=rk["minutes_to_60C"], body_max_C=rk["body_max_C"],
                            reading_max_C=rk["reading_max_C"], published_min=3.33, published_body=94.67)
    print("check", doc["check_25C"], flush=True)
    if rk["minutes_to_60C"] is None or abs(rk["minutes_to_60C"] - 3.33) > 0.25 or abs(rk["body_max_C"] - 94.67) > 1.0:
        doc["check_25C"]["ok"] = False
        print("SANITY FAIL", flush=True)
    else:
        doc["check_25C"]["ok"] = True
    for Ta in (22.0, 32.0):
        print("walk", Ta, flush=True)
        doc["walks"].append(walk_case(Ta))
        print("duty", Ta, flush=True)
        doc["duties"].append(duty_case(Ta))
        print("idle off", Ta, flush=True)
        doc["sits"].append(sit_case(Ta, 0.0, 0.0, "idle_torque_off"))
        print("idle on", Ta, flush=True)
        doc["sits"].append(torque_on_idle(Ta))
        for w, mode in ((2.30, "charge_7v2"), (3.50, "charge_6v0")):
            print("charge", w, Ta, flush=True)
            doc["sits"].append(sit_case(Ta, w, 1.0, mode))
    path = os.path.join(HERE, "heat.json")
    json.dump(doc, open(path, "w"), indent=1)
    print("wrote", path)


if __name__ == "__main__":
    main()
