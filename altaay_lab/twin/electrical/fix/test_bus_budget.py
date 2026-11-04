"""Tests for bus_budget.py (no robot, no sim): python3 test_bus_budget.py"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bus_budget as BB


def test_model_matches_twin_servo():
    # stall at 7.2 V: u = V, w = 0 -> V / R + I_q = 2.788 A (servo_sts3215.py: stall current V / R_M)
    i = BB.currents_from_torque([BB.TAU_TRAIN * 7.2 / 7.4], [0.0], 7.2)[0]
    assert abs(i - (7.2 / BB.R_M + BB.I_Q)) < 1e-9, i


def test_under_budget_untouched():
    rng = np.random.default_rng(0); b = BB.BusBudget()
    q = rng.normal(0, 0.3, 14); t = q + rng.normal(0, 0.01, 14); w = rng.normal(0, 1, 14)
    t2, info = b.limit(t, q, w)
    assert np.array_equal(t2, t) and info["cap_Nm"] is None


def test_over_budget_cut_to_budget():
    rng = np.random.default_rng(1); b = BB.BusBudget(budget_a=11.5)
    for _ in range(500):
        q = rng.normal(0, 0.3, 14); t = q + rng.normal(0, 0.5, 14); w = rng.normal(0, 3, 14)
        t2, info = b.limit(t, q, w)
        assert info["i_after_A"] <= 11.5 + 1e-6, info
        # never moves a target past the request, never flips a direction
        e0, e1 = t - q, t2 - q
        assert np.all(np.abs(e1) <= np.abs(e0) + 1e-12) and np.all(e0 * e1 >= -1e-15)
        # servos under the cap are untouched
        if info["cap_Nm"] is not None:
            small = np.abs(b.kp * e0) < info["cap_Nm"] - 1e-9
            assert np.allclose(t2[small], t[small])


def test_guard_clip_then_budget():
    g = BB.TargetGuard(init_targets=np.zeros(14))
    q = np.zeros(14); w = np.zeros(14)
    t2, info = g(np.full(14, 0.5), q, w)              # a 0.5 rad jump on every joint
    assert np.all(np.abs(t2) <= 5.24 * 0.02 + 1e-12)   # the training's clip: 0.105 rad per step
    assert info["i_after_A"] <= BB.BUDGET_A + 1e-6
    t3, _ = g(np.full(14, 0.5), q, w)                  # the next step starts from the sent targets
    assert np.all(t3 <= 2 * 5.24 * 0.02 + 1e-12)


def test_fall_hold():
    f = BB.FallHold(); q = np.full(14, 0.2)
    assert np.array_equal(f(np.ones(14), q, 30.0), np.ones(14))      # upright: the policy's targets pass
    assert np.array_equal(f(np.ones(14), q, 50.0), q)                # past 45 deg: hold the angles of that moment
    assert np.array_equal(f(np.ones(14), q * 3, 10.0), q)            # and keep holding until reset()
    f.reset(); assert np.array_equal(f(np.ones(14), q, 10.0), np.ones(14))


def test_speed():
    b = BB.BusBudget(budget_a=5.0); rng = np.random.default_rng(2)
    q = rng.normal(0, 0.3, 14); t = q + rng.normal(0, 0.5, 14); w = rng.normal(0, 3, 14)
    t0 = time.perf_counter()
    for _ in range(200):
        b.limit(t, q, w)
    ms = (time.perf_counter() - t0) / 200 * 1000
    print(f"limit(): {ms:.3f} ms per step on this machine")
    assert ms < 5.0


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("PASS", k)
