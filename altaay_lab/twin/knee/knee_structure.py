"""Structure check for STS3250 knees (D32). Sim pass only for the loads, FEA pass only for the factors, calc only for the
scaling.

1. Re-runs the structure twin's own load cases (twin/structure/st_loads.py: the five walk cases at the nominal start and the
   walk_pushes case, 15 N for 0.1 s every 3 s, seeds none and 1 to 3; 30 solver iterations) twice: with today's C001 knees and
   with STS3250 knees (servo_sts3250.py: torque limit 3.23 x 1.581 = 5.107 Nm at the scene's 7.4 V, damping 1.0025, +19.5 g at
   each knee). st_sim.py and st_loads.py are imported unchanged; only the compiled model's two knees are changed.
2. Takes the peak 6D loads at the knee and hip roll joints (the structure twin's own joint sensors, st_loads.summarize).
3. Scales the FEA factors of STRUCTURE_TWIN.md (linear elastic, so stress goes with load): the shin's knee sheet eye with the
   P2 split of that file (80 % in-plane from the knee torque, the rest from the bending), the thigh (the knee servo case
   holder) with the larger of the knee torque and bending ratios, roll_to_pitch with the larger of the hip roll bending and
   radial force ratios.
Run: ODM_PLAYGROUND=<Open_Duck_Playground at b9be205> ODM_SCRATCH=<scratch> python3 knee_structure.py run c001|sts3250
     python3 knee_structure.py report <scratch>
"""
import glob, importlib.util, json, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "structure"))
if not os.environ.get("ODM_PLAYGROUND"):
    c = sorted(glob.glob("/home/user/**/Open_Duck_Playground*/playground/open_duck_mini_v2/xmls", recursive=True))
    if c:
        os.environ["ODM_PLAYGROUND"] = c[0].split("/playground/open_duck_mini_v2")[0]

# FEA factors (walk, push) from twin/structure/STRUCTURE_TWIN.md: summary lines 10 to 11, table rows 155 to 157 and 175,
# proposals P1 and P3 (rows 380 to 381 and 398); hot case x 0.62 at 50 C (summary line 17)
SF = {"shin knee sheet eye (level 2)": (1.63, 1.07, "knee"), "shin knee sheet eye (level 1)": (1.56, 1.04, "knee"),
      "shin, P3 knee sheets 5 walls 40 % (level 1)": (1.82, 1.20, "knee"), "thigh, knee servo case holder (level 1)": (2.70, 1.74, "mount"),
      "roll_to_pitch (levels 1 to 3, lowest)": (1.48, 1.08, "hiproll"), "roll_to_pitch, P1 3 walls (level 1)": (1.84, 1.25, "hiproll")}


def _sts():
    spec = importlib.util.spec_from_file_location("servo_sts3250_st", os.path.join(HERE, "servo_sts3250.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def patch_knees(S):
    """after st_sim.Sim builds its MjInfer model, make its two knees STS3250s (the actuator part is the same in both bands)"""
    import mujoco
    K = _sts(); mdl = K.model("high"); orig = S.Sim.__init__

    def init(self, *a, **k):
        orig(self, *a, **k)
        objs = [self] + list(vars(self).values())
        m = next(getattr(o, "model") for o in objs if isinstance(getattr(o, "model", None), mujoco.MjModel))
        acts = [m.actuator(n).id for n in ("left_knee", "right_knee")]
        joints = [int(m.actuator_trnid[i, 0]) for i in acts]
        self.knee_info = K.apply_knees(m, acts, [int(m.jnt_dofadr[j]) for j in joints], joints, mdl)
    S.Sim.__init__ = init


def run(knee):
    import st_sim as S, st_loads as LD
    if knee == "sts3250":
        patch_knees(S)
    folder, _ = S.build_model("st_knee_" + knee)
    res = []
    cases = [(c, None) for c in LD.WALK] + [([c for c in S.AM.CASES if c[0] == "walk_pushes"][0], sd) for sd in (None, 1, 2, 3)]
    for c, sd in cases:
        t = time.time()
        R = S.run_logged(folder, c[1], c[2], c[3], c[4], c[5], seed=sd, iterations=LD.ITER)
        s = LD.summarize(R, f"{c[0]}_s{sd or 0}")
        J = s["joints"]
        res.append(dict(case=c[0], seed=sd, set="push" if c[0] == "walk_pushes" else "walk", falls=s.get("falls"), wall_s=round(time.time() - t, 1),
                        loads={j: {q: J[j][q]["peak"] for q in ("M_axis", "M_bend", "F_radial", "F_axial")} for j in ("left_knee", "right_knee", "left_hip_roll", "right_hip_roll")}))
        print(json.dumps(res[-1]), flush=True)
    out = os.path.join(S.SCR_ROOT, f"knee_structure_{knee}.json"); json.dump(res, open(out, "w"), indent=1)
    return out


def peaks(rows, which):
    P = {}
    for r in rows:
        if r["set"] != which or r["case"] == "stand_in_place":
            continue
        for side in ("left", "right"):
            for g, j in (("knee", f"{side}_knee"), ("hiproll", f"{side}_hip_roll")):
                for q, v in r["loads"][j].items():
                    P[f"{g}_{q}"] = max(P.get(f"{g}_{q}", 0.0), float(v))
    return P


def report(scr):
    A = json.load(open(os.path.join(scr, "knee_structure_c001.json"))); B = json.load(open(os.path.join(scr, "knee_structure_sts3250.json")))
    out = dict(peaks={}, ratio={}, sf={})
    for w in ("walk", "push"):
        a, b = peaks(A, w), peaks(B, w)
        out["peaks"][w] = dict(c001={k: round(v, 3) for k, v in a.items()}, sts3250={k: round(b[k], 3) for k in a})
        out["ratio"][w] = {k: round(b[k] / a[k], 3) for k in a if a[k] > 0}
    for part, (sw, sp, g) in SF.items():
        row = {}
        for w, s0 in (("walk", sw), ("push", sp)):
            r = out["ratio"][w]
            if g == "knee":
                f = 0.8 * r["knee_M_axis"] + 0.2 * r["knee_M_bend"]
            elif g == "mount":
                f = max(r["knee_M_axis"], r["knee_M_bend"])
            else:
                f = max(r["hiproll_M_bend"], r["hiproll_F_radial"])
            row[w] = dict(before=s0, load_factor=round(f, 3), after=round(s0 / f, 2), after_hot_50C=round(0.62 * s0 / f, 2))
        out["sf"][part] = row
    out["falls"] = dict(c001=sum(int(bool(r["falls"])) for r in A), sts3250=sum(int(bool(r["falls"])) for r in B))
    # P2 (a thicker knee sheet eye, STRUCTURE_TWIN.md P2 rule: 80 % of the stress goes with 1 / t, the rest with 1 / t^2;
    # today 3.6 mm): the thickness that brings the shin back to 2 walking and in push, with the STS3250 loads
    p2 = {}
    for w, s0 in (("walk", 1.63), ("push", 1.07)):
        r = out["ratio"][w]; f = 0.8 * r["knee_M_axis"] + 0.2 * r["knee_M_bend"]
        for t in np.arange(3.6, 9.01, 0.1):
            g = 0.8 * (3.6 / t) + 0.2 * (3.6 / t) ** 2
            if s0 / (f * g) >= 2.0:
                p2[w] = dict(eye_mm=round(float(t), 1), sf=round(s0 / (f * g), 2)); break
    out["p2_eye_thickness_for_sf2"] = p2
    return out


if __name__ == "__main__":
    if sys.argv[1] == "run":
        print(run(sys.argv[2]))
    else:
        r = report(sys.argv[2]); os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
        json.dump(r, open(os.path.join(HERE, "out", "structure.json"), "w"), indent=1); print(json.dumps(r, indent=1))
