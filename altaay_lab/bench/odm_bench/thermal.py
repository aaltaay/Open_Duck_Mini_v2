"""Servo temperature guard (scope addition 2026-11-02; mirrors the D16 battery guard).

Why: the lab sim puts knee copper loss while walking at 3 to 5.5 times the rated 1.06 W, and
Feetech publishes no thermal resistance, so heat is the main servo risk (coordinator note).

Inputs: Present Temperature (register 63, 1 C steps) of the 14 servos, read in the same SYNC READ
as Present Voltage (62..63, odm_bench/sampler.py), and each servo's own Max Temperature Limit
(register 13), read once before torque-on.

Thresholds per servo, from its own limit L (both margins are lab choices, flags):
  warn  = L - 15 C  -> stop walking: safe stand (walkhooks stop sequence), then a slow sink with
                       the Runtime's own low gains (HWI.low_torque_kps = 2; the Runtime has no sit
                       pose: HWI has init_pos = standing and zero_pos = straight legs), then torque
                       off (HWI.turn_off). No power off: the battery is fine and the logs stay.
  stop  = L - 8 C   -> hard stop: low gains for 0.5 s, torque off, at any moment.
Where the margins come from:
  - L itself: at L the servo unloads its own torque (register 19 Unload Condition = 44 includes
    the temperature bit, REGISTER_REFERENCE.md factory read), one joint at a time, uncontrolled.
    The factory L read there is 70 C (12 V units, firmware 3.10); ours is read per servo.
  - L - 10 C is the lab's continuous-duty edge: D2 passes the servo only if a 10 minute 1.5 Nm
    hold stays at least 10 C under L.
  - warn at L - 15 C stops the walk 5 C before that edge, because the reading keeps rising after
    the stop: the sensor is not the winding, and standing still still draws holding current.
  - stop at L - 8 C acts 8 C before the servo's own cut-out: room for the 1 C register step, the
    0.5 s read interval, the 2-read confirmation and the 0.5 s low-gain sink. If a standing robot
    goes on heating 7 C past the warn level, something is wrong (a bind, a stall) and torque must
    go. The heating rate in C per second is not published: check both margins against the
    TEST_PLAN 7.3 log (rise rate at 1.5 Nm) before trusting them (SOFTWARE.md section 5).
A reading must pass a threshold on 2 reads in a row of the same servo (one bad read cannot stop
the robot). Readings outside 0 to 120 C are dropped (counted).
"""

DEFAULT_LIMIT_C = 70        # REGISTER_REFERENCE.md factory value, used only if register 13 cannot be read


class ThermalConfig:
    def __init__(self, **kw):
        self.warn_margin_c = 15.0
        self.stop_margin_c = 8.0
        self.confirm_reads = 2
        self.t_min_c = 0.0
        self.t_max_c = 120.0
        self.log_period_s = 1.0
        for k, v in kw.items():
            if not hasattr(self, k):
                raise TypeError(f"unknown thermal option {k}")
            setattr(self, k, v)

    def as_dict(self):
        return dict(vars(self))


class ThermalGuard:
    """Pure logic. limits: {servo id: Max Temperature Limit in C}. update(t, temps) with
    temps = {id: C} (any subset; staggered reads) returns new events:
    thermal_warn (stop walking, stand, sink, torque off) and thermal_stop (torque off now)."""

    def __init__(self, limits, cfg=None):
        self.cfg = cfg or ThermalConfig()
        self.limits = dict(limits)
        self.warn = {i: L - self.cfg.warn_margin_c for i, L in self.limits.items()}
        self.stop = {i: L - self.cfg.stop_margin_c for i, L in self.limits.items()}
        self.n_warn = {i: 0 for i in self.limits}
        self.n_stop = {i: 0 for i in self.limits}
        self.latest = {}
        self.max_seen = {}
        self.events = []
        self.dropped = 0
        self.warned = False
        self.stopped = False
        self.next_log_t = 0.0

    def _event(self, t, name, sid, temp, thr):
        e = dict(t=round(t, 3), event=name, servo=sid, temp_c=temp, threshold_c=thr, limit_c=self.limits.get(sid),
                 reason=f"servo {sid} at {temp} C >= {thr:g} C (limit {self.limits.get(sid)} C - "
                        f"{self.cfg.warn_margin_c if name == 'thermal_warn' else self.cfg.stop_margin_c:g} C)")
        self.events.append(e)
        return e

    def check_start(self, temps):
        """True if every servo is under its warn level before walking starts."""
        hot = {i: v for i, v in temps.items() if i in self.warn and v is not None and v >= self.warn[i]}
        return not hot, hot

    def update(self, t, temps):
        new = []
        if self.stopped:
            return new
        for sid, v in (temps or {}).items():
            if sid not in self.limits or v is None:
                continue
            if not (self.cfg.t_min_c <= v <= self.cfg.t_max_c):
                self.dropped += 1
                continue
            self.latest[sid] = v
            self.max_seen[sid] = max(v, self.max_seen.get(sid, v))
            self.n_stop[sid] = self.n_stop[sid] + 1 if v >= self.stop[sid] else 0
            self.n_warn[sid] = self.n_warn[sid] + 1 if v >= self.warn[sid] else 0
            if self.n_stop[sid] >= self.cfg.confirm_reads:
                new.append(self._event(t, "thermal_stop", sid, v, self.stop[sid]))
                self.stopped = True
                break
            if not self.warned and self.n_warn[sid] >= self.cfg.confirm_reads:
                new.append(self._event(t, "thermal_warn", sid, v, self.warn[sid]))
                self.warned = True
        return new

    def hottest(self):
        """(id, temp, limit, margin to warn) of the servo closest to its own warn level."""
        if not self.latest:
            return None
        sid = max(self.latest, key=lambda i: self.latest[i] - self.warn[i])
        return sid, self.latest[sid], self.limits[sid], round(self.warn[sid] - self.latest[sid], 1)

    def due_log(self, t):
        if t >= self.next_log_t:
            self.next_log_t = t + self.cfg.log_period_s
            return True
        return False


def read_limits(io, ids, bus_mod, errors=None):
    """Register 13 of every servo with pypot (one READ each, before torque-on).
    Returns ({id: limit}, [ids that fell back to DEFAULT_LIMIT_C])."""
    limits, fallback = {}, []
    for i in ids:
        try:
            limits[i] = bus_mod.read_reg(io, i, "max_temperature_limit")
        except Exception as e:  # noqa: BLE001
            limits[i] = DEFAULT_LIMIT_C
            fallback.append(i)
            if errors is not None:
                errors.add("pypot", "temp_limit_read", i, repr(e))
    return limits, fallback
