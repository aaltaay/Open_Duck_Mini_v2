#!/usr/bin/env python3
"""The stock walk (Runtime v2_rl_walk_mujoco.py RLWalk, unmodified) with two guards:
the D16 battery guard (battery_guard.py) and the servo temperature guard (odm_bench/thermal.py).

What it adds around the Runtime loop (details in odm_bench/walkhooks.py):
  1. Before any torque: Present Voltage and Present Temperature of all 14 servos and each
     servo's Max Temperature Limit (register 13), with pypot (check_voltage.py's library).
     Refuses to start: exit 4 if the idle servo median is under 6.8 V, exit 9 if a servo is
     already at its warn temperature (limit - 15 C).
  2. Every --period seconds (default 0.25 s) one staggered SYNC READ of registers 62 and 63
     (voltage and temperature) from half of the servos (odm_bench/sampler.py: 71 bytes, 0.71 ms
     of wire time), inside the walk thread between two control cycles: each servo every 0.5 s.
  3. Battery walk stop (debounced, D16): zero command, the policy steps in place for 1 s, the
     pose freezes when both feet read contact for 3 cycles (or after 4 s), then blends to the
     Runtime standing pose (HWI.init_pos) over 2 s and holds it. The pad cannot restart it.
  4. Thermal warn (any servo at its limit - 15 C on 2 reads): the same stop, then after 2 s of
     standing a slow sink with the Runtime's low gains (HWI.low_torque_kps) for 2 s, then torque
     off (HWI.turn_off). No power off. Exit 7.
  5. Battery hard stop: low gains for 1 s, torque off, then --poweroff-cmd
     (default "sudo -n /usr/bin/systemctl poweroff", allowed by the sudoers line in PI_SETUP.md).
     Exit 6.
  6. Thermal stop (any servo at its limit - 8 C on 2 reads): low gains for 0.5 s, torque off,
     no power off. Exit 8.
  7. A rustypot panic (UPSTREAM_ISSUES.md G10) -> torque off through the pypot handle, exit 3.
  8. After every stop in 4 to 7, Torque Enable (register 40) is read back from all 14 servos and
     torque off is written again until all read 0 (walkhooks.hard_stop). If a servo still reads 1
     or never answers: a loud message, report item 11.torque_off FAIL, exit 10.
  9. With --knee-heat (software/knee_heat.py, the boot service): a servo at 55 C on 2 reads
     warns and stops the walk, torque goes off, and goal writes stop so a write cannot turn
     torque back on. Idle (the pad pause) and a caller that says the duck is sitting are torque
     off even when cool. The walk may start again only after every joint id has 2 of its own
     readings under 45 C. A failed turn_off raises WalkStop("knee_torque_off") so main() runs
     hard_stop (exit 11). The older thermal stop (limit minus 8 C) still exits.
  Ctrl-C behaves like upstream (servos keep their last targets) unless --torque-off-on-exit.
Logs: <out>/walk_guard/guard_<time>.csv (every guard tick), thermal_<time>.csv (hottest servo
every second) and a JSON report with the TEST_PLAN 11 items.
Exit codes: 0 normal end, 1 failed check, 3 bus failure, 4 battery too low to start, 5 no servo
answered, 6 battery hard stop (power off requested), 7 thermal warn stop, 8 thermal stop,
9 too hot to start, 10 torque off not confirmed after a stop (takes the place of 3, 6, 7, 8 or 11),
11 knee-heat turn_off failed and the hard stop ran.
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from odm_bench import bus, joints, paths, report, sampler, thermal, walkhooks  # noqa: E402
import battery_guard as bg  # noqa: E402


class GuardHook:
    """Reads voltage and temperature at the guard period and turns guard events into walk actions."""

    def __init__(self, guard, reader, log, max_seconds=0, thermal_guard=None, thermal_log=None, quiet=False,
                 knee=None, gate=None):
        self.guard, self.reader, self.log = guard, reader, log
        self.tg, self.tlog = thermal_guard, thermal_log
        self.knee, self.gate = knee, gate
        self._armed = False
        self.next_t = 0.0
        self.max_seconds = max_seconds
        self.read_ms = []
        self.medians = []
        self.quiet = quiet

    def _arm(self, walk):
        """Skip goal writes while the knee-heat rest holds torque off. Installed once."""
        if self._armed or self.gate is None:
            return
        self._armed = True
        write = walk.hwi.set_position_all
        gate = self.gate

        def set_position_all(positions, write=write, walk=walk, gate=gate):
            return gate.filter_write(walk.hwi, positions, write)

        walk.hwi.set_position_all = set_position_all

    def on_cycle(self, walk, t, paused):
        if self.gate is not None:
            self._arm(walk)
        if self.max_seconds and t >= self.max_seconds:
            raise walkhooks.WalkStop("timeout", f"--max-seconds {self.max_seconds} reached")
        if walk.stop_phase() == "standing" and self.guard.state == bg.STOPPING:
            self.guard.set_state(bg.STANDING)
        if t < self.next_t:
            return
        self.next_t = t + self.guard.cfg.period_s
        res = self.reader.read()
        volts, temps = res if isinstance(res, tuple) else (res, {})
        if self.reader.last_duration_s is not None:
            self.read_ms.append(self.reader.last_duration_s * 1e3)
        events = self.guard.update(t, volts)
        if self.tg is not None:
            events += self.tg.update(t, temps)
            self._log_hottest(t)
        if self.knee is not None:
            # Pad pause is idle. A sit program passes posture "sitting" to KneeHeatGuard
            # itself; this walk only sees walking and the pad pause.
            import knee_heat
            posture = "idle" if paused else "walking"
            decision = self.knee.update(t, temps, posture)
            try:
                self.gate.apply(walk.hwi, decision)
            except knee_heat.TorqueOffFailed as err:
                raise walkhooks.WalkStop(
                    "knee_torque_off", "torque off failed during the heat rest: %s" % err) from err
            events += decision.events
        if self.guard.last_median is not None and volts:
            self.medians.append(self.guard.last_median)
        names = ";".join(e["event"] for e in events)
        vtxt = ",".join("" if not volts or volts.get(i) is None else f"{volts[i]:.1f}" for i in joints.IDS)
        med = "" if self.guard.last_median is None else f"{self.guard.last_median:.2f}"
        rms = f"{self.read_ms[-1]:.2f}" if self.read_ms else ""
        self.log.write(f"{t:.3f},{walk.cycles},{med},{self.guard.state},{walk.stop_phase() or ''},"
                       f"{int(paused)},{rms},{names},{vtxt}\n")
        self.log.flush()
        for e in events:
            print(f"[guard] t {e['t']} s {e['event']}: {e['reason']}", flush=True)
            if e["event"] == "walk_stop":
                walk.request_walk_stop(e["reason"])
            elif e["event"] == "thermal_warn" and self.knee is None:
                walk.request_walk_stop(e["reason"], then="sink_off", hold_s=2.0)
            elif e["event"] == "thermal_warn":
                pass  # --knee-heat owns the 55 C stop and can resume; no stand, no exit
            elif e["event"] == "hard_stop":
                raise walkhooks.WalkStop("hard_stop", e["reason"])
            elif e["event"] == "thermal_stop":
                raise walkhooks.WalkStop("thermal_stop", e["reason"])

    def _log_hottest(self, t):
        if not self.tg.due_log(t):
            return
        h = self.tg.hottest()
        if h is None:
            return
        sid, temp, lim, margin = h
        line = (f"{t:.2f},{sid},{joints.NAME.get(sid, '')},{temp},{lim},{self.tg.warn[sid]:g},{self.tg.stop[sid]:g},"
                f"{margin}")
        if self.tlog is not None:
            self.tlog.write(line + "\n")
            self.tlog.flush()
        if not self.quiet:
            print(f"[thermal] t {t:.0f} s hottest {joints.NAME.get(sid, sid)} (ID {sid}) {temp} C, "
                  f"warn at {self.tg.warn[sid]:g} C", flush=True)


def _load_knee_heat():
    """Import software/knee_heat.py without a machine path baked into the file."""
    soft = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "software"))
    if soft not in sys.path:
        sys.path.insert(0, soft)
    import knee_heat
    return knee_heat


def startup_checks(rep, pyio, smp, guard, errors, tcfg, knee_guard=None):
    """Before torque-on: voltages, temperatures and register 13 of every servo."""
    volts, temps = smp.read_all()
    if not volts:
        rep.add("11.start", "no servo answered the start read", "FAIL", None, "14 servos", "check_voltage.py calls")
        return None, 5
    ok, med = guard.check_start(volts)
    rep.add("11.start", f"start check: idle median of {len(volts)} servos", "PASS" if ok else "FAIL",
            round(med, 2) if med is not None else None, f">= {guard.cfg.start_min_v} V", "battery_guard.py start rule")
    missing = [i for i in joints.IDS if i not in volts]
    if missing:
        rep.add("11.ids", "servos that did not answer the start read", "WARN", missing)
    if not ok:
        print(f"battery too low to start walking (idle median {med} V < {guard.cfg.start_min_v} V): charge first")
        return None, 4
    limits, fallback = thermal.read_limits(pyio, joints.IDS, bus, errors)
    tg = thermal.ThermalGuard(limits, tcfg)
    rep.add("T.limits", "Max Temperature Limit (register 13) per servo", "INFO",
            {str(k): v for k, v in limits.items()}, None, "read before torque-on")
    if fallback:
        rep.add("T.fallback", f"register 13 unreadable: default {thermal.DEFAULT_LIMIT_C} C used", "WARN", fallback)
    cool, hot = tg.check_start(temps)
    rep.add("T.start", "every servo under its warn temperature before walking", "PASS" if cool else "FAIL",
            {str(k): v for k, v in temps.items()} if not cool else f"max {max(temps.values())} C",
            f"< limit - {tcfg.warn_margin_c:g} C", "odm_bench/thermal.py")
    if not cool:
        print(f"servo(s) too hot to start: {hot}; let them cool")
        return None, 9
    if knee_guard is not None:
        k_ok, k_hot = knee_guard.check_start(temps)
        rep.add("K.start", "every servo under the 55 C knee-heat stop before walking",
                "PASS" if k_ok else "FAIL",
                {str(k): v for k, v in k_hot.items()} if not k_ok else "under 55 C",
                "< 55 C", "software/knee_heat.py")
        if not k_ok:
            print(f"servo(s) at the knee-heat stop: {k_hot}; let them cool")
            return None, 9
    return tg, 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    walkhooks.common_walk_args(ap)
    bg.add_guard_args(ap)
    ap.set_defaults(period=0.25)
    t = ap.add_argument_group("temperature guard (odm_bench/thermal.py)")
    t.add_argument("--warn-margin-c", type=float, default=15.0, help="stop walking at limit minus this")
    t.add_argument("--stop-margin-c", type=float, default=8.0, help="torque off at limit minus this")
    t.add_argument("--groups", type=int, default=2, help="staggered read groups (2 = 7 servos per tick)")
    t.add_argument("--no-thermal", action="store_true")
    t.add_argument("--knee-heat", action="store_true",
                   help="55 C walk stop, torque off when idle or sitting, resume below 45 C "
                        "(software/knee_heat.py). The boot service passes this.")
    ap.add_argument("--poweroff-cmd", default="sudo -n /usr/bin/systemctl poweroff",
                    help="run after a battery hard stop; '' to skip")
    ap.add_argument("--dry-run", action="store_true", help="print the power off command instead of running it")
    ap.add_argument("--max-seconds", type=float, default=0, help="end the walk after this many seconds (bench)")
    ap.add_argument("--torque-off-on-exit", action="store_true")
    ap.add_argument("--settle-s", type=float, default=1.0)
    ap.add_argument("--blend-s", type=float, default=2.0)
    ap.add_argument("--out", help="log folder (default ODM_BENCH_OUT or ~/odm_bench_logs)")
    a = ap.parse_args(argv)

    out = paths.out_dir(a.out, "walk_guard")
    rep = report.Report("walk_with_guard", "11", "Stock walk with the battery and temperature guards")
    errors = bus.BusErrors()
    cfg = bg.config_from_args(a)
    tcfg = thermal.ThermalConfig(warn_margin_c=a.warn_margin_c, stop_margin_c=a.stop_margin_c)
    guard = bg.BatteryGuard(cfg, state=bg.WALKING)
    knee = None
    gate = None
    if a.knee_heat:
        knee_mod = _load_knee_heat()
        knee = knee_mod.KneeHeatGuard(watched=joints.IDS)
        gate = knee_mod.TorqueGate()

    # 1. pypot first (before rustypot takes the port exclusively), then the start checks
    pyio = bus.open_pypot(a.serial_port, sync_read=True, errors=errors)
    try:
        pyio.get_model(joints.IDS)        # cache the models now, while the bus is quiet
    except Exception:                     # noqa: BLE001
        pass
    smp = sampler.GuardSampler(pyio, groups=a.groups, errors=errors)
    tg, code = startup_checks(rep, pyio, smp, guard, errors, tcfg, knee_guard=knee)
    if code:
        rep.finish(out)
        return code
    if a.no_thermal:
        tg = None
        rep.add("T.off", "temperature guard disabled (--no-thermal)", "WARN")
    stamp = paths.stamp()
    log_path = out / f"guard_{stamp}.csv"
    log = open(log_path, "w")
    log.write("t_s,cycle,median_v,guard_state,stop_phase,paused,read_ms,event," +
              ",".join(f"v_{i}" for i in joints.IDS) + "\n")
    tlog = open(out / f"thermal_{stamp}.csv", "w")
    tlog.write("t_s,hottest_id,joint,temp_c,limit_c,warn_c,stop_c,margin_to_warn_c\n")
    hook = GuardHook(guard, smp, log, a.max_seconds, tg, tlog, knee=knee, gate=gate)
    walk, rt = walkhooks.make_walk(a, [hook], errors, dict(settle_s=a.settle_s, blend_s=a.blend_s))
    rep.data["runtime"] = dict(dir=str(rt), commit=paths.runtime_commit(rt), pin=paths.RUNTIME_PIN)
    code = 0
    try:
        walk.run()
        rep.add("11.exit", "walk loop ended (Ctrl-C)", "INFO")
        if a.torque_off_on_exit:
            walk.hwi.turn_off()
    except walkhooks.WalkStop as e:
        if e.kind == "hard_stop":
            done = walk.hard_stop(pyio)
            rep.add("11.hard_stop", f"battery hard stop: {e.reason}", "INFO", "; ".join(done))
            log.close()
            if a.poweroff_cmd:
                if a.dry_run:
                    print(f"[dry run] would run: {a.poweroff_cmd}")
                else:
                    print(f"running: {a.poweroff_cmd}", flush=True)
                    subprocess.run(a.poweroff_cmd, shell=True, check=False)
            code = 6
        elif e.kind == "sink_off":
            done = walk.hard_stop(pyio, low_gain_s=2.0)
            rep.add("T.warn_stop", f"thermal warn: stood, then sank and torque off: {e.reason}", "INFO", "; ".join(done))
            code = 7
        elif e.kind == "thermal_stop":
            done = walk.hard_stop(pyio, low_gain_s=0.5)
            rep.add("T.stop", f"thermal stop: {e.reason}", "INFO", "; ".join(done))
            code = 8
        elif e.kind == "knee_torque_off":
            done = walk.hard_stop(pyio, low_gain_s=0.5)
            rep.add("K.torque_off_failed", f"heat rest could not turn torque off: {e.reason}", "FAIL",
                    "; ".join(done))
            code = 11
        else:
            rep.add("11.exit", f"walk ended: {e.reason}", "INFO")
            if a.torque_off_on_exit:
                walk.hwi.turn_off()
    except BaseException as e:   # noqa: BLE001 - rustypot PanicException is a BaseException
        if isinstance(e, KeyboardInterrupt):
            raise
        done = walk.hard_stop(pyio, low_gain_s=0.5)
        rep.add("11.bus", f"walk loop crashed: {type(e).__name__}: {e}", "FAIL", "; ".join(done),
                None, "UPSTREAM_ISSUES.md G10")
        code = 3
    finally:
        for f in (log, tlog):
            if not f.closed:
                f.close()
    if walk.torque_check is not None and not walkhooks.report_torque_check(rep, "11.torque_off", walk.torque_check):
        code = walkhooks.EXIT_TORQUE_ON
    knee_events = knee.events if knee else []
    for ev in guard.events + (tg.events if tg else []) + knee_events:
        if ev["event"] in ("warn_stop", "resume", "torque_off"):
            item = f"K.{ev['event']}"
        elif ev["event"].startswith("thermal"):
            item = f"T.{ev['event']}"
        else:
            item = f"11.{ev['event']}"
        rep.add(item, ev["reason"], "INFO", ev.get("value", ev.get("temp_c")), None, f"t {ev['t']} s")
    rep.add("11.stop", "stop sequence", "INFO", walk.stop_log or "none")
    if tg:
        rep.add("T.max", "hottest reading per servo during the run", "INFO",
                {str(k): v for k, v in sorted(tg.max_seen.items())})
    st = walk.loop_stats()
    rep.add("11.loop", "control loop (cycle period)", "INFO", st)
    if hook.read_ms:
        rep.add("11.read_ms", "guard read time per tick (mean / max ms)", "INFO",
                f"{sum(hook.read_ms) / len(hook.read_ms):.2f} / {max(hook.read_ms):.2f}")
    if st.get("over_budget_frac") is not None:
        rep.add("11.budget", "cycles over the 20 ms budget (+5%)",
                "PASS" if st["over_budget_frac"] <= 0.05 else "WARN", st["over_budget_frac"], "<= 0.05",
                "lab advisory limit")
    rep.add("11.errors", "bus errors (pypot and rustypot)", "INFO", errors.snapshot())
    rep.data.update(events=guard.events, thermal_events=tg.events if tg else [],
                    knee_heat_events=knee.events if knee else [], config=cfg.as_dict(),
                    thermal_config=tcfg.as_dict(), log=str(log_path), stop_log=walk.stop_log, loop=st,
                    torque_check=walk.torque_check)
    rc = rep.finish(out)
    return code or rc


if __name__ == "__main__":
    sys.exit(main())
