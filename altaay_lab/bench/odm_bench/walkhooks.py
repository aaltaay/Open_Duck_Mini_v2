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
The walk runs from the Runtime scripts/ folder, as the image launcher does, because RLWalk and
raw_imu.py open ./polynomial_coefficients.pkl and ./imu_calib_data.pkl relative to the CWD.
"""
import os
import sys
import time

import numpy as np

from . import bus, joints, paths


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


def import_rlwalk(runtime_dir):
    paths.use_runtime(runtime_dir)
    import v2_rl_walk_mujoco  # noqa: E402  (Runtime scripts/, unmodified)
    return v2_rl_walk_mujoco


def build_walk_class(RLWalk):
    class HookedRLWalk(RLWalk):
        """RLWalk + hooks. hooks: objects with on_cycle(walk, t, paused)."""

        def __init__(self, onnx_model_path, hooks=(), no_commands=False, errors=None, stop_cfg=None, **kw):
            self._hooks = list(hooks)
            self._errors = errors
            self._action_override = None
            self._zero_cmd = False
            self._t0 = time.monotonic()
            self._last_cycle_t = None
            self.cycle_dt = []
            self.cycles = 0
            self.paused_ticks = 0
            self.stop_cfg = dict(settle_s=1.0, double_support_cycles=3, double_support_timeout_s=4.0, blend_s=2.0)
            self.stop_cfg.update(stop_cfg or {})
            self._stop = None            # dict with the stop sequence state
            self.stop_log = []
            kw["commands"] = not no_commands
            super().__init__(onnx_model_path, **kw)
            if no_commands:
                self.paused = False      # nothing could unpause it without a pad
            if errors is not None:
                self.hwi.io = bus.CountingIO(self.hwi.io, errors)
            self._real_policy = self.policy
            self.policy = _PolicyProxy(self)
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

        def get_obs(self):
            now = time.monotonic()
            if self._last_cycle_t is not None:
                self.cycle_dt.append(now - self._last_cycle_t)
            else:
                self._t0 = now          # walk time starts at the first control cycle
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
        def hard_stop(self, pypot_io=None, low_gain_s=1.0):
            """Low gains (the Runtime's low_torque_kps), wait, torque off. rustypot first (the
            Runtime's calls); pypot as the fallback if rustypot is dead (G10 panic)."""
            done = []
            ids = list(self.hwi.joints.values())
            try:
                self.hwi.io.set_kps(ids, list(self.hwi.low_torque_kps))
                done.append("rustypot low kp")
                time.sleep(low_gain_s)
                self.hwi.turn_off()
                done.append("rustypot torque off")
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
                            done.append(f"pypot low kp + torque off (attempt {attempt + 1})")
                            break
                        except Exception as e2:     # noqa: BLE001
                            done.append(f"pypot attempt {attempt + 1} failed: {type(e2).__name__}")
                            time.sleep(0.3)
            self.stop_expression()
            return done

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
            return dict(cycles=self.cycles, mean_hz=round(float(1 / dts.mean()), 2),
                        p50_ms=round(float(np.percentile(dts, 50) * 1e3), 2),
                        p99_ms=round(float(np.percentile(dts, 99) * 1e3), 2),
                        max_ms=round(float(dts.max() * 1e3), 2),
                        over_budget_frac=round(float((dts > budget_s * 1.05).mean()), 4))

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


def make_walk(a, hooks, errors, extra_stop_cfg=None):
    """Build HookedRLWalk from parsed args, from the Runtime scripts/ folder."""
    rt = paths.find_runtime(a.runtime)
    mod = import_rlwalk(rt)
    cls = build_walk_class(mod.RLWalk)
    onnx = os.path.abspath(os.path.expanduser(a.onnx_model_path))
    cfg = os.path.abspath(os.path.expanduser(a.duck_config_path))
    check_duck_config(cfg)
    os.chdir(rt / "scripts")
    walk = cls(onnx, hooks=hooks, no_commands=a.no_commands, errors=errors, stop_cfg=extra_stop_cfg,
               duck_config_path=cfg, serial_port=a.serial_port, control_freq=a.control_freq,
               pid=[a.p, a.i, a.d], action_scale=a.action_scale, pitch_bias=a.pitch_bias,
               cutoff_frequency=a.cutoff_frequency)
    return walk, rt


def ids_in_hwi_order():
    return list(joints.JOINTS.values())


def flush_stdout():
    try:
        sys.stdout.flush()
    except Exception:  # noqa: BLE001
        pass
