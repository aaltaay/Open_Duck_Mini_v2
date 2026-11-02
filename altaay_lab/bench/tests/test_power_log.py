"""power_log.py (TEST_PLAN 8.1 inventory and 9 walking log) on the simulated bus."""
import power_log as pl
from conftest import DATA, IDS, ONNX, item, last_report, needs_libs, needs_walk
from fake_sts3215 import VoltageProfile


@needs_libs
def test_idle_inventory_pass(make_bus, run):
    bus = make_bus(reg85=0, volts=7.2)
    for s in bus.servos.values():
        s.mem[22] = 0                                 # configured: P 32, D 0, I 0
    r, out = run("power_log.py", "--idle", "--port", bus.path, "--seconds", "2")
    rep = last_report(out, "power_log")
    assert r.returncode == 0, r.stdout[-3000:]
    for k in ("8.1.ids", "8.1.fw", "8.1.r85", "8.1.pid", "9.v4.5", "9.checksum"):
        assert item(rep, k)["status"] == "PASS", item(rep, k)
    assert item(rep, "9.samples")["measured"] >= 80


@needs_libs
def test_idle_inventory_catches_reg85_firmware_and_missing(make_bus, run):
    bus = make_bus(ids=[i for i in IDS if i != 33], reg85=0, volts=7.2)
    bus.servos[24].mem[85] = 50
    bus.servos[13].mem[0], bus.servos[13].mem[1] = 3, 9
    r, out = run("power_log.py", "--idle", "--port", bus.path, "--seconds", "1")
    rep = last_report(out, "power_log")
    assert r.returncode == 1
    assert item(rep, "8.1.ids")["status"] == "FAIL" and "33" in item(rep, "8.1.ids")["measured"]
    assert item(rep, "8.1.r85")["measured"] == [24]
    assert item(rep, "8.1.fw")["status"] == "FAIL"


@needs_libs
def test_checksum_errors_fail_the_log(make_bus, run):
    bus = make_bus(reg85=0, volts=7.2)
    bus.fault(31).corrupt_next = 5
    r, out = run("power_log.py", "--idle", "--port", bus.path, "--seconds", "1")
    rep = last_report(out, "power_log")
    assert item(rep, "9.checksum")["status"] == "FAIL"
    assert item(rep, "9.checksum")["measured"] >= 1


def _rows(volts_by_id, n=100):
    rows = []
    for k in range(n):
        r = {"t_s": f"{k * 0.02:.3f}", "failed": ""}
        for i in IDS:
            r[f"v_{i}"] = f"{volts_by_id(i, k):.1f}"
            r[f"i_{i}"] = "0.5"
        rows.append(r)
    return rows


def test_analyze_gates():
    import odm_bench.report as R
    rep = R.Report("t", "9", "t")
    # right ankle under 6.0 V in 20% of samples, never under 4.5 V
    pl.analyze(_rows(lambda i, k: 5.8 if (i == 14 and k % 5 == 0) else 6.6), "nominal", rep)
    st = {i["item"]: i["status"] for i in rep.items}
    assert st["9.v4.5"] == "PASS" and st["9.ankle"] == "FAIL" and st["9.rate"] == "PASS"
    rep2 = R.Report("t", "9", "t")
    pl.analyze(_rows(lambda i, k: 4.4 if (i == 24 and k == 7) else 7.0), "full", rep2)
    st2 = {i["item"]: i["status"] for i in rep2.items}
    assert st2["9.v4.5"] == "FAIL" and st2["9.ankle"] == "INFO"


@needs_walk
def test_walking_log_on_sim_nominal_profile(make_bus, run, duck_config):
    """Sim pass only: servo voltages replay the star-wiring ngspice traces at a nominal pack
    (typical corner) while the real walk loop runs. The sim predicts the TEST_PLAN 9 ankle gate
    fails (30 to 34% of the walk under 6.0 V); no servo under 4.5 V; not worse than high-side."""
    bus = make_bus(reg85=0, volts=7.2)
    bus.set_profile(VoltageProfile(str(DATA / "sim_star_nominal_typical.csv")), delay_s=6.0)
    r, out = run("power_log.py", "--walk", "--seconds", "6", "--pack", "nominal", "--no-guard",
                 "--onnx_model_path", ONNX, "--duck_config_path", duck_config, "--serial_port", bus.path,
                 "--no-commands", timeout=180)
    rep = last_report(out, "power_log")
    assert item(rep, "9.v4.5")["status"] == "PASS", r.stdout[-3000:]
    assert item(rep, "9.ankle")["status"] == "FAIL"
    assert item(rep, "9.wiring")["status"] == "PASS"
    assert item(rep, "9.checksum")["status"] == "PASS"
    assert item(rep, "9.samples")["measured"] >= 200
