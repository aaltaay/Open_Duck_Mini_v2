"""E8: run the bench test suite (altaay_lab/bench/tests, bench agent) on its simulated servo bus.

The suite needs a Python with the Runtime's pinned packages (rustypot 0.1.0, pypot, onnxruntime): set ODM_TEST_PYTHON
to it (software/SOFTWARE.md section 7 builds one). Without it the rustypot and pypot tests skip, and this check says
how many ran. pytest runs with -p no:cacheprovider and no bytecode, so nothing is written into the repo.
Usage: VERIFY_OUT=<folder outside the repo> [ODM_TEST_PYTHON=<python>] python3 altaay_lab/verify/e8_bench_pytest.py
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlib as V  # noqa: E402


def has(py, mods):
    r = subprocess.run([py, "-c", "import " + ", ".join(mods)], capture_output=True)
    return r.returncode == 0


def main():
    R = V.Result("E8", "Bench scripts on a simulated servo bus (pytest altaay_lab/bench/tests)",
                 "VERIFY_OUT=<out> ODM_TEST_PYTHON=<python with rustypot, pypot> python3 altaay_lab/verify/e8_bench_pytest.py",
                 "The bench agent's tests: STS3215 protocol, first-servo check, battery guard, power log, feet, IMU, thermal "
                 "guard and the Runtime cross-check, against a fake STS3215 bus on a pty and fake Blinka pins",
                 "Real servos, real USB adapter timing, real GPIO (TEST_PLAN.md sections 6 to 12)")
    tests = V.lab("bench", "tests")
    if not os.path.isdir(tests) or not any(f.startswith("test_") for f in os.listdir(tests)):
        R.not_run("altaay_lab/bench/tests has no test files yet (bench agent output not landed)")
        R.write()
        return
    R.inp(*[os.path.join(tests, f) for f in sorted(os.listdir(tests)) if f.endswith(".py")])
    py = os.environ.get("ODM_TEST_PYTHON", sys.executable)
    libs = has(py, ["rustypot", "pypot.feetech", "onnxruntime", "pytest"])
    R.ev("test python %s: rustypot, pypot, onnxruntime, pytest importable: %s" % (py, libs))
    if not has(py, ["pytest"]):
        R.not_run("pytest not importable in %s (set ODM_TEST_PYTHON)" % py)
        R.write()
        return
    env = dict(os.environ, ODM_RUNTIME_DIR=V.RUNTIME, PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run(["nice", "-n", "10", py, "-B", "-m", "pytest", tests, "-q", "-p", "no:cacheprovider", "-rfEs",
                        "--basetemp", os.path.join(V.out_dir(), "e8_pytest_tmp")],
                       cwd=V.REPO, env=env, capture_output=True, text=True, timeout=3600)
    log = p.stdout + p.stderr
    open(os.path.join(V.out_dir(), "e8_pytest.txt"), "w").write(log)
    summ = [ln for ln in log.splitlines() if re.search(r"\d+ (passed|failed|skipped|error)", ln)]
    last = summ[-1] if summ else log.strip().splitlines()[-1] if log.strip() else "no output"
    R.ev("pytest: %s (exit %d)" % (last.strip("= "), p.returncode))
    R.key("pytest: " + last.strip("= "))
    counts = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed|skipped|errors?|xfailed|xpassed)", last)}
    failed_lines = [ln for ln in log.splitlines() if ln.startswith(("FAILED", "ERROR"))]
    for ln in failed_lines:
        if "panic_after_checksum" not in ln:
            R.find("FAIL", "bench test: " + ln[:300], fix="see the bench agent's test output in the verify folder", where="altaay_lab/bench")
    n_bad = counts.get("failed", 0) + counts.get("error", 0) + counts.get("errors", 0)
    if n_bad > len(failed_lines):
        R.find("FAIL", "pytest reports failures it does not name: " + last)
    # timing-sensitive safety test (rustypot panic -> pypot torque off): run it again a few times under the current load
    race = "test_rustypot_panic_after_checksum_error_is_caught"
    if race in open(os.path.join(tests, "test_battery_guard.py")).read() and libs:
        n_rep = int(os.environ.get("VERIFY_RACE_REPEATS", "3"))
        fails = 1 if any(race in ln for ln in failed_lines) else 0
        for k in range(n_rep):
            q = subprocess.run(["nice", "-n", "10", py, "-B", "-m", "pytest", os.path.join(tests, "test_battery_guard.py"), "-q",
                                "-p", "no:cacheprovider", "-k", race, "--basetemp", os.path.join(V.out_dir(), "e8_race_%d" % k)],
                               cwd=V.REPO, env=env, capture_output=True, text=True, timeout=600)
            fails += q.returncode != 0
        R.ev("race test %s: %d failed of %d runs (the suite run plus %d alone)" % (race, fails, n_rep + 1, n_rep))
        if fails:
            R.find("FAIL", "%s failed in %d of %d runs: after a rustypot panic the pypot fallback reports 'torque off (attempt 1)' "
                   "but the fake servos keep torque enabled (register 40 = 1): the sync write can be lost while the bus still "
                   "carries garbage, and nothing reads it back" % (race, fails, n_rep + 1),
                   fix="bench/odm_bench/walkhooks.py hard_stop(): after pypot_io._set_torque_enable(...), read register 40 back "
                       "from every servo and break only when all read 0; otherwise retry (the 5 attempts), and report the ids "
                       "still on", where="altaay_lab/bench/odm_bench/walkhooks.py")
    sk = counts.get("skipped", 0)
    if sk:
        reasons = sorted({m.group(1) for m in re.finditer(r"SKIPPED \[\d+\] [^:]+:\d+: (.*)", log)})
        R.find("WARN", "%d tests skipped: %s" % (sk, "; ".join(reasons)[:300]),
               fix=None if libs else "run with ODM_TEST_PYTHON set to a Python that has the Runtime's pinned packages")
    if p.returncode not in (0, 1) and not R.fails():
        R.find("FAIL", "pytest exit %d: %s" % (p.returncode, log[-300:]))
    if not counts.get("passed"):
        R.not_run("no test passed or ran: " + last)
    R.write()


if __name__ == "__main__":
    main()
