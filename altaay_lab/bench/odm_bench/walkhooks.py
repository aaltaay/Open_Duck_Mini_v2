"""Run the Runtime walk loop (scripts/v2_rl_walk_mujoco.py RLWalk) with lab hooks, unmodified.

How it plugs in, without editing a Runtime file:
  - RLWalk.run() calls self.get_obs() once per 50 Hz cycle (v2_rl_walk_mujoco.py line 253).
    A subclass overrides get_obs(): it runs the hooks first (voltage reads, guard, logging), all
    in the walk thread, so no second thread ever touches the bus, then calls the original.
  - When paused, run() skips get_obs() but still calls xbox_controller.get_last_command()
    (line 210); that call is wrapped so the hooks keep running while paused.
  - Stopping and holding a pose is done through the policy: self.policy is replaced by a proxy
    whose infer() returns the action that gives the wanted motor targets
    (targets = init_pos + action * action_scale, line 290). The loop, the HWI writes and the
    head command path stay the Runtime's own.
  - pypot is opened BEFORE RLWalk.__init__ opens rustypot (TIOCEXCL rule, odm_bench/bus.py).
  - hwi.io is wrapped by bus.CountingIO after start-up to count rustypot errors.
  - hard_stop() does not trust its own writes: torque off is a sync write with no reply, so it
    reads Torque Enable (register 40) back from every servo with pypot and writes torque off again
    until all read 0. If they do not, it says so loudly and the caller exits EXIT_TORQUE_ON.
  - Idle-time reads (idle_tasks, odm_bench/vsampler.py): RLWalk.run() ends every cycle with
    time.sleep(max(0, 1 / control_freq - took)) (v2_rl_walk_mujoco.py line 328). With idle tasks,
    the module's `time` name is replaced by _LoopClock, whose sleep() runs the tasks inside that
    sleep and returns when the sleep would have ended; every other time function is the real
    one. A task read starts only if it ends before the next cycle, so it never delays a control
    read or write. hwi.set_position_all is wrapped to note when each goal write returned
    (last_write_t, and write_log for the time count), the reference for the read phase.
The walk runs from the Runtime scripts/ folder, as the image launcher does, because RLWalk and
raw_imu.py open ./polynomial_coefficients.pkl and ./imu_calib_data.pkl relative to the CWD.
"""
import os
import sys
import time

import numpy as np

from . import bus, joints, paths, sts3215, vsampler

EXIT_TORQUE_ON = 10     # walk_with_guard.py and power_log.py: a hard stop could not confirm torque off


def read_torque_enable(io, ids, errors=None, singles=False):
    """Torque Enable (register 40) of `ids` with pypot: one SYNC READ (bus.sync_read_block keys each
    answer by the ID in its status packet, so a late reply from another servo cannot stand in for the
    one asked), then, if `singles`, one READ for each servo the sync read missed.
    Returns {id: value} for the servos that answered."""
    addr, size = sts3215.REG["torque_enable"]
    got, failed = bus.sync_read_block(io, ids, addr, size, errors)
    state = {i: d[0] for i, d in got.items() if i in ids}
    for i in failed if singles else ():
        try:
            sp = io._send_packet(io._protocol.DxlReadDataPacket(i, addr, size))
        except Exception:                  # noqa: BLE001 - timeout or garbage: no answer from this servo
            continue
        if sp is not None and sp.id == i and len(sp.parameters) == size:
            state[i] = sp.parameters[0]
    return state


def report_torque_check(rep, item, check):
    """Add the hard stop read-back to a report as a PASS/FAIL gate; True if torque off is confirmed."""
    rep.gate(item, "torque off confirmed: every servo reads Torque Enable (register 40) = 0 after the stop",
             check["ok"], {str(i): v for i, v in check["readback"].items()}, "0 on every servo",
             "walkhooks.hard_stop read-back")
    return check["ok"]


class WalkStop(Exception):
    """Raised inside the walk loop to leave RLWalk.run() (hard stop or a requested exit)."""

    def __init__(self, kind, reason):
        super().__init__(f"{kind}: {reason}")
        self.kind, self.reason = kind, reason


class _NoButtons:
    class _B:
        triggered = False
        is_pressed = False

    def __init__(self):
        for n in ("A", "B", "X", "Y", "LB", "RB", "dpad_up", "dpad_down"):
            setattr(self, n, _NoButtons._B())


class _PolicyProxy:
    def __init__(self, walk):
        self.walk = walk

    def infer(self, obs):
        a = self.walk._real_policy.infer(obs)
        ov = self.walk._action_override
        return a if ov is None else np.asarray(ov(a), dtype=np.float32)


class _LoopClock:
    """Stands in for the `time` module inside v2_rl_walk_mujoco only: sleep() runs the idle
    tasks (IdleScheduler.idle) and returns when the plain sleep would have; the rest is `time`."""

    def __init__(self, scheduler):
        self._scheduler = scheduler

    def sleep(self, seconds):
        self._scheduler.idle(seconds)

    def __getattr__(self, name):
        return getattr(time, name)


def import_rlwalk(runtime_dir):
    paths.use_runtime(runtime_dir)
    import v2_rl_walk_mujoco  # noqa: E402  (Runtime scripts/, unmodified)
    return v2_rl_walk_mujoco


def build_walk_class(RLWalk):
    class HookedRLWalk(RLWalk):
        """RLWalk + hooks. hooks: objects with on_cycle(walk, t, paused)."""

        def __init__(self, onnx_model_path, hooks=(), no_commands=False, errors=None, stop_cfg=None,
                     idle_tasks=(), **kw):
            self._hooks = list(hooks)
            self._errors = errors
            self._action_override = None
            self._zero_cmd = False
            self._t0 = time.monotonic()
            self.t0_monotonic = None     # monotonic time of the first control cycle
            self._last_cycle_t = None
            self.cycle_dt = []
            self.write_dt = []           # per cycle: cycle start (get_obs entry) to the goal write's return
            self.cycles = 0
            self.paused_ticks = 0
            self.last_write_t = None     # monotonic time when the last goal write returned
            self.prev_write_t = None     # and the one before it
            self.write_log = None        # [(time, state)] of every goal write, when idle tasks run
            self.stop_cfg = dict(settle_s=1.0, double_support_cycles=3, double_support_timeout_s=4.0, blend_s=2.0)
            self.stop_cfg.update(stop_cfg or {})
            self._stop = None            # dict with the stop sequence state
            self.stop_log = []
            self.torque_check = None     # read-back result of the last hard_stop()
            kw["commands"] = not no_commands
            super().__init__(onnx_model_path, **kw)
            if no_commands:
                self.paused = False      # nothing could unpause it without a pad
            if errors is not None:
                self.hwi.io = bus.CountingIO(self.hwi.io, errors)
            self._real_policy = self.policy
            self.policy = _PolicyProxy(self)
            write = self.hwi.set_position_all

            def set_position_all(joints_positions):
                try:
                    return write(joints_positions)
                finally:
                    self.prev_write_t, self.last_write_t = self.last_write_t, time.monotonic()
                    if self._last_cycle_t is not None:      # list appends only: nothing slow on the control path
                        self.write_dt.append(self.last_write_t - self._last_cycle_t)
                    if self.write_log is not None:
                        self.write_log.append((self.last_write_t, self._state_now()))
            self.hwi.set_position_all = set_position_all
            self.idle = None
            if idle_tasks:
                self.write_log = []
                self.idle = vsampler.IdleScheduler(idle_tasks, ctx=self.walk_state)
                sys.modules[RLWalk.__module__].time = _LoopClock(self.idle)
            if self.commands:
                orig = self.xbox_controller.get_last_command

                def get_last_command():
                    res = orig()
                    if self.paused:
                        self.paused_ticks += 1
                        self._run_hooks(paused=True)
                    if self._zero_cmd:
                        return ([0.0] * 7, _NoButtons(), 0, 0)
                    return res
                self.xbox_controller.get_last_command = get_last_command

        # ---------------------------------------------------------------- hook plumbing
        def t(self):
            return time.monotonic() - self._t0

        def _run_hooks(self, paused):
            for h in self._hooks:
                h.on_cycle(self, self.t(), paused)

        def _state_now(self):
            return "paused" if self.paused else ("walk" if self._stop is None else self._stop["phase"])

        def walk_state(self):
            """For idle-task records: 'walk', 'paused' or the stop phase; the last two goal writes; the cycle."""
            return dict(state=self._state_now(), last_write=self.last_write_t, prev_write=self.prev_write_t,
                        cycle=self.cycles)

        def get_obs(self):
            now = time.monotonic()
            if self._last_cycle_t is not None:
                self.cycle_dt.append(now - self._last_cycle_t)
            else:
                self._t0 = now          # walk time starts at the first control cycle
                self.t0_monotonic = now
                if self.idle is not None:
                    self.idle.start(now)    # idle-task slots start with the walk
            self._last_cycle_t = now
            self.cycles += 1
            self._run_hooks(paused=False)
            if self._stop is not None:
                self._advance_stop()
            if self._zero_cmd:
                self.last_commands = [0.0] * 7
            return super().get_obs()

        # ---------------------------------------------------------------- soft stop
        def request_walk_stop(self, reason, then="hold", hold_s=2.0):
            """Zero command, step in place, freeze in double support, blend to init_pos, then
            hold (then="hold", battery walk stop) or, after hold_s standing, raise
            WalkStop("sink_off") so the caller sinks with low gains and turns torque off
            (then="sink_off", thermal warn). A second request can only make it stricter."""
            if self._stop is not None:
                if then == "sink_off" and self._stop.get("then") != "sink_off":
                    self._stop.update(then="sink_off", hold_s=hold_s, sink_reason=reason)
                    self.stop_log.append((round(self.t(), 3), "then_sink_off", reason))
                return
            self._zero_cmd = True
            self._stop = dict(phase="settle", t=self.t(), reason=reason, ds=0, then=then, hold_s=hold_s,
                              sink_reason=reason)
            self.stop_log.append((round(self.t(), 3), "settle", reason))
            if self.paused:
                # already holding still (A pressed): hold the last targets, then blend
                self._freeze("paused when the stop came")

        def _freeze(self, why):
            init = np.array(self.init_pos)
            frozen = np.array(self.motor_targets, dtype=float).copy()
            frozen[5:9] = frozen[5:9] - np.array(self.last_commands[3:7])   # head targets without command
            a0 = (frozen - init) / self.action_scale
            self._stop.update(phase="blend", t=self.t(), a0=a0)
            self.stop_log.append((round(self.t(), 3), "freeze", why))
            blend = max(1e-3, self.stop_cfg["blend_s"])

            def override(_a, walk=self):
                s = min(1.0, (walk.t() - walk._stop["t"]) / blend)
                return (1.0 - s) * walk._stop["a0"]
            self._action_override = override
            self.paused = False

        def _advance_stop(self):
            st, c = self._stop, self.stop_cfg
            if st["phase"] == "settle" and self.t() - st["t"] >= c["settle_s"]:
                st.update(phase="double_support", t=self.t())
                self.stop_log.append((round(self.t(), 3), "wait_double_support", ""))
            elif st["phase"] == "double_support":
                left, right = self.feet_contacts.get()
                st["ds"] = st["ds"] + 1 if (left and right) else 0
                if st["ds"] >= c["double_support_cycles"]:
                    self._freeze("both feet on the ground")
                elif self.t() - st["t"] >= c["double_support_timeout_s"]:
                    self._freeze("double support timeout")
            elif st["phase"] == "blend" and self.t() - st["t"] >= c["blend_s"]:
                st.update(phase="standing", t=self.t())
                self.stop_log.append((round(self.t(), 3), "standing", "holding init_pos"))
            elif st["phase"] == "standing" and st.get("then") == "sink_off" and self.t() - st["t"] >= st["hold_s"]:
                self.stop_log.append((round(self.t(), 3), "sink_off", "low gains, then torque off"))
                raise WalkStop("sink_off", st["sink_reason"])

        def stop_phase(self):
            return None if self._stop is None else self._stop["phase"]

        # ---------------------------------------------------------------- hard stop
        def hard_stop(self, pypot_io=None, low_gain_s=1.0, confirm_tries=30, retry_wait_s=0.3):
            """Low gains (the Runtime's low_torque_kps), wait, torque off. rustypot first (the
            Runtime's calls); pypot as the fallback if rustypot is dead (G10 panic). Then torque
            off is confirmed by reading register 40 back (_confirm_torque_off): up to
            confirm_tries reads, retry_wait_s apart (about 9 s with the defaults; on the simulated
            bus under load the stale traffic of a panic took up to 5 s to clear). Returns the steps
            taken; self.torque_check holds the read-back (ok False: the caller must not claim a
            safe state and exits EXIT_TORQUE_ON)."""
            done = []
            ids = list(self.hwi.joints.values())
            try:
                self.hwi.io.set_kps(ids, list(self.hwi.low_torque_kps))
                done.append("rustypot low kp")
                time.sleep(low_gain_s)
                self.hwi.turn_off()
                done.append("rustypot torque off sent")
            except BaseException as e:          # noqa: BLE001 - pyo3 PanicException included
                if isinstance(e, KeyboardInterrupt):
                    raise
                done.append(f"rustypot failed: {type(e).__name__}")
                if pypot_io is not None:
                    # sync writes only (convert=False: no model read first), retried: the bus may
                    # still carry garbage right after the failure
                    for attempt in range(5):
                        try:
                            pypot_io.set_P_coefficient({i: 2 for i in ids}, convert=False)
                            time.sleep(low_gain_s)
                            pypot_io._set_torque_enable({i: 0 for i in ids}, convert=False)
                            done.append(f"pypot low kp + torque off sent (attempt {attempt + 1})")
                            break
                        except Exception as e2:     # noqa: BLE001
                            done.append(f"pypot attempt {attempt + 1} failed: {type(e2).__name__}")
                            time.sleep(0.3)
            self._confirm_torque_off(pypot_io, ids, done, confirm_tries, retry_wait_s)
            self.stop_expression()
            return done

        def _confirm_torque_off(self, io, ids, done, tries, wait_s):
            """A sync write has no reply and can be lost: right after a G10 failure the bus may
            still carry garbage, and on the simulated bus a sync write once never landed
            (VERIFICATION.md E8). So: read register 40 of every servo; for the servos that do not
            read 0, wait wait_s, write torque off again and read again, up to `tries` reads. Each
            read starts with the drained flush of bus.make_flush_safe (tcdrain, then input flush),
            so the write is on its way before the read asks. A servo that never answers counts as
            not confirmed. Without a pypot handle nothing can be confirmed."""
            state = {i: None for i in ids}
            reads = 0
            if io is None:
                done.append("torque off NOT verified: no pypot handle to read register 40 back")
            else:
                errors = getattr(self, "_errors", None)
                pending = list(ids)
                while pending and reads < tries:
                    if reads:
                        time.sleep(wait_s)
                        try:
                            io._set_torque_enable({i: 0 for i in pending}, convert=False)
                        except Exception as e:     # noqa: BLE001
                            done.append(f"pypot torque off rewrite {reads} failed: {type(e).__name__}")
                    reads += 1
                    try:
                        # single READs for the servos the sync read missed on the last try only, so a
                        # bus that answers nothing costs one timeout per try, not one per servo
                        state.update(read_torque_enable(io, pending, errors, singles=reads == tries))
                    except Exception as e:         # noqa: BLE001 - closed port, OS error: no answer
                        done.append(f"read-back {reads} failed: {type(e).__name__}")
                    pending = [i for i in ids if state[i] != 0]
            still_on = [i for i in ids if state[i] not in (0, None)]
            no_answer = [i for i in ids if state[i] is None]
            ok = not still_on and not no_answer
            self.torque_check = dict(ok=ok, readback=state, still_on=still_on, no_answer=no_answer, reads=reads)
            if ok:
                done.append(f"read-back: register 40 = 0 on all {len(ids)} servos "
                            f"(read {reads}, {reads - 1} rewrite{'' if reads == 2 else 's'})")
                return True
            msg = (f"TORQUE OFF NOT CONFIRMED after {reads} read(s) of register 40: "
                   f"still on {still_on}, no answer {no_answer}")
            done.append(msg)
            bar = "!" * 78
            for stream in (sys.stdout, sys.stderr):
                print(f"{bar}\nHARD STOP: {msg}.\nThe robot may still hold torque. Switch it off at the main "
                      f"power switch before you touch it.\n{bar}", file=stream, flush=True)
            return False

        def stop_expression(self):
            """What RLWalk.run's KeyboardInterrupt handler stops (lines 331 to 337)."""
            for flag, name in (("antennas", "antennas"), ("eyes", "eyes"), ("projector", "projector")):
                if getattr(self.duck_config, flag, False) and hasattr(self, name):
                    try:
                        getattr(self, name).stop()
                    except Exception:            # noqa: BLE001
                        pass
            try:
                self.feet_contacts.stop()
            except Exception:                    # noqa: BLE001
                pass

        def loop_stats(self, budget_s=None):
            budget_s = budget_s or 1.0 / self.control_freq
            dts = np.array(self.cycle_dt[1:]) if len(self.cycle_dt) > 1 else np.array([])
            if not len(dts):
                return dict(cycles=self.cycles)
            out = dict(cycles=self.cycles, mean_hz=round(float(1 / dts.mean()), 2),
                       p50_ms=round(float(np.percentile(dts, 50) * 1e3), 2),
                       p99_ms=round(float(np.percentile(dts, 99) * 1e3), 2),
                       max_ms=round(float(dts.max() * 1e3), 2),
                       over_budget_frac=round(float((dts > budget_s * 1.05).mean()), 4))
            wd = np.array(self.write_dt[1:]) if len(self.write_dt) > 1 else np.array([])
            if len(wd):        # when the goal write ends, from the cycle start: what an in-cycle read delays
                out.update(write_p50_ms=round(float(np.percentile(wd, 50) * 1e3), 2),
                           write_p99_ms=round(float(np.percentile(wd, 99) * 1e3), 2))
            return out

    return HookedRLWalk


def check_duck_config(path):
    """RLWalk asks on stdin when duck_config.json is missing (duck_config.py lines 35 to 47);
    a service has no stdin, so fail early with a clear message instead."""
    if not os.path.exists(os.path.expanduser(path)):
        raise SystemExit(f"duck config not found: {path}. Copy software/duck_config.altaay.json to "
                         f"~/duck_config.json and add your offsets (software/PI_SETUP.md step 9).")


def common_walk_args(ap, onnx_required=True):
    g = ap.add_argument_group("walk (same meaning as Runtime v2_rl_walk_mujoco.py)")
    g.add_argument("--onnx_model_path", required=onnx_required)
    g.add_argument("--duck_config_path", default=os.path.expanduser("~/duck_config.json"))
    g.add_argument("--serial_port", default="/dev/ttyACM0",
                   help="RLWalk takes it but the upstream CLI does not expose it")
    g.add_argument("-a", "--action_scale", type=float, default=0.25)
    g.add_argument("-p", type=int, default=30)
    g.add_argument("-i", type=int, default=0)
    g.add_argument("-d", type=int, default=0)
    g.add_argument("-c", "--control_freq", type=int, default=50)
    g.add_argument("--pitch_bias", type=float, default=0, help="deg")
    g.add_argument("--cutoff_frequency", type=float, default=None)
    g.add_argument("--no-commands", action="store_true",
                   help="run without an Xbox pad (zero command: the policy steps in place). "
                        "Upstream always needs the pad: --commands is store_true with default True")
    g.add_argument("--runtime", help="Runtime checkout (default ODM_RUNTIME_DIR or ~/Open_Duck_Mini_Runtime)")
    return g


def make_walk(a, hooks, errors, extra_stop_cfg=None, idle_tasks=()):
    """Build HookedRLWalk from parsed args, from the Runtime scripts/ folder. idle_tasks:
    vsampler.TimedRead objects run inside the loop's own sleep (never delaying a control cycle)."""
    rt = paths.find_runtime(a.runtime)
    mod = import_rlwalk(rt)
    cls = build_walk_class(mod.RLWalk)
    onnx = os.path.abspath(os.path.expanduser(a.onnx_model_path))
    cfg = os.path.abspath(os.path.expanduser(a.duck_config_path))
    check_duck_config(cfg)
    os.chdir(rt / "scripts")
    walk = cls(onnx, hooks=hooks, no_commands=a.no_commands, errors=errors, stop_cfg=extra_stop_cfg,
               idle_tasks=idle_tasks, duck_config_path=cfg, serial_port=a.serial_port,
               control_freq=a.control_freq, pid=[a.p, a.i, a.d], action_scale=a.action_scale,
               pitch_bias=a.pitch_bias, cutoff_frequency=a.cutoff_frequency)
    return walk, rt


def ids_in_hwi_order():
    return list(joints.JOINTS.values())


def flush_stdout():
    try:
        sys.stdout.flush()
    except Exception:  # noqa: BLE001
        pass
