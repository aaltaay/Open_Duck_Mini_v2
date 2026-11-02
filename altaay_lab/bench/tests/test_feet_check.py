"""feet_check.py (TEST_PLAN 12) with the Runtime FeetContacts on scripted fake GPIO."""
from conftest import item, last_report, needs_runtime


def script(tmp_path, rows, name="feet.csv"):
    p = tmp_path / name
    p.write_text("t,left,right\n" + "\n".join(f"{t:.4f},{l},{r}" for t, l, r in rows) + "\n")
    return str(p)


def presses(n, t0=0.3, period=0.3, press=0.15, side="left", bounce=False, cross=False):
    """Scripted presses: 150 ms press, 150 ms release, like a hand press. Shorter ones make the
    test depend on the shared test machine's scheduling (a stalled poller misses them)."""
    rows, t = [], t0
    for _ in range(n):
        on = (1, 0) if side == "left" else (0, 1)
        if cross:
            on = (1, 1)
        if bounce:
            rows += [(t, *on), (t + 0.002, 0, 0), (t + 0.004, *on)]
        else:
            rows.append((t, *on))
        rows.append((t + press, 0, 0))
        t += period
    return rows, t


@needs_runtime
def test_open_and_stand(run):
    r, out = run("feet_check.py", "--open", "--seconds", "1", "--yes", env={"ODM_FAKE_FEET": "00"})
    assert item(last_report(out, "feet"), "12.open")["status"] == "PASS"
    r, out = run("feet_check.py", "--open", "--seconds", "1", "--yes", env={"ODM_FAKE_FEET": "10"})
    assert item(last_report(out, "feet"), "12.open")["status"] == "FAIL"
    r, out = run("feet_check.py", "--stand", "--seconds", "1.5", "--yes", env={"ODM_FAKE_FEET": "11"})
    assert item(last_report(out, "feet"), "12.stand")["status"] == "PASS"


@needs_runtime
def test_stand_flicker_fails(run, tmp_path):
    rows = [(0, 1, 1), (0.7, 1, 0), (0.705, 1, 1)]          # 5 ms flicker on the right foot
    r, out = run("feet_check.py", "--stand", "--seconds", "1.5", "--rate", "1000", "--yes",
                 env={"ODM_FAKE_FEET_SCRIPT": script(tmp_path, rows)})
    assert item(last_report(out, "feet"), "12.stand")["status"] == "FAIL"


@needs_runtime
def test_presses_pass(run, tmp_path):
    left, t = presses(20)
    right, _ = presses(20, t0=t + 0.2, side="right")
    r, out = run("feet_check.py", "--presses", "20", "--rate", "1000", "--yes", "--stuck-s", "1", "--timeout", "20",
                 env={"ODM_FAKE_FEET_SCRIPT": script(tmp_path, [(0, 0, 0)] + left + right)})
    rep = last_report(out, "feet")
    for k in ("12.left.count", "12.left.stuck", "12.left.other", "12.right.count", "12.right.other"):
        assert item(rep, k)["status"] == "PASS", (k, item(rep, k), r.stdout[-1500:])


@needs_runtime
def test_presses_catch_swap_bounce_and_missed(run, tmp_path):
    left, t = presses(10, cross=True)                        # both inputs change: swapped or shorted
    right, _ = presses(7, t0=t + 0.2, side="right", bounce=True)
    r, out = run("feet_check.py", "--presses", "10", "--rate", "2000", "--yes", "--timeout", "5",
                 env={"ODM_FAKE_FEET_SCRIPT": script(tmp_path, [(0, 0, 0)] + left + right)})
    rep = last_report(out, "feet")
    assert item(rep, "12.left.other")["status"] == "FAIL"
    assert item(rep, "12.right.count")["status"] == "FAIL"   # 7 of 10: missed presses
    assert item(rep, "12.right.chatter")["status"] == "WARN"
    assert r.returncode == 1
