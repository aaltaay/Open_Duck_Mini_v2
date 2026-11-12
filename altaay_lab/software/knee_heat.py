"""Knee heat guard for the walk (knee heat study, first recommendation).

Pure logic. No servo bus, no Runtime import, no hardware. The walk calls it
from bench/walk_with_guard.py when that program is started with --knee-heat
(software/odm-walk-guard.service). The Runtime stays unmodified (D6).

Set points, not measurements:
  stop   55 C   warn and stop the walk. The study's cap. The same number as
                the older guard's warn when the factory limit is 70 C.
  restart 45 C  walk again only when every watched servo has two of its own
                readings strictly below this, taken after the stop. A cool
                group that does not include a hot servo does not clear it.
                45 C is the live twin's walk-again temperature (STATE.md,
                sim pass only). The study says a torque-on stand in a 32 C
                room can sit near 48 to 50 C, so 45 C may never arrive if
                torque stays on. Torque off is the rest that can cool.
A reading counts only after 2 samples in a row of that same servo, the same
confirmation the older temperature guard uses, so one bad sample cannot stop
or restart. Readings outside 0 to 120 C are dropped. A turn_off that raises
is not ignored: TorqueOffFailed asks the walk for the existing hard stop.

Posture "idle" or "sitting" is torque off even when the servos are cool
(the study: drop torque when the duck is not walking; the sit already
drops torque, D59). Posture "walking" may hold torque until a stop, and
may turn it back on only after a latched stop has cooled. Any other
posture is treated as idle.
"""

WARN_STOP_C = 55.0
RESTART_C = 45.0
CONFIRM_READS = 2
T_MIN_C = 0.0
T_MAX_C = 120.0
# Right knee 13, left knee 23 (software/servo_limits.json). The stop watches
# every servo id in the sample, not only these two.
KNEE_IDS = (13, 23)
POSTURES = ("walking", "idle", "sitting")


class TorqueOffFailed(Exception):
    """turn_off did not complete. The walk must hard-stop, not keep resting."""


class Decision:
    """torque is 'off' or 'allow'. events are the new ones this call."""

    def __init__(self, torque, events):
        self.torque = torque
        self.events = events


class KneeHeatGuard:
    def __init__(self, warn_c=WARN_STOP_C, restart_c=RESTART_C, confirm=CONFIRM_READS, watched=None):
        if not (restart_c < warn_c):
            raise ValueError("restart temperature must be below the stop")
        self.warn_c = float(warn_c)
        self.restart_c = float(restart_c)
        self.confirm = int(confirm)
        # None: every servo that has sent a valid reading. A tuple: those ids,
        # so a servo that has not answered since the stop cannot count as cool.
        self.watched = None if watched is None else tuple(watched)
        self.latched = False
        self.n_hot = {}
        self.n_below = {}
        self.seen = set()
        self.dropped = 0
        self.events = []
        self._torque = "allow"

    def check_start(self, temps):
        """False if any valid reading is already at the stop. Does not latch."""
        hot = {}
        for sid, v in (temps or {}).items():
            if v is None or not (T_MIN_C <= float(v) <= T_MAX_C):
                continue
            if float(v) >= self.warn_c:
                hot[sid] = float(v)
        return (not hot), hot

    def _event(self, t, name, sid, temp):
        thr = self.warn_c if name == "warn_stop" else self.restart_c
        if name == "torque_off":
            reason = "torque off: idle, sitting, or a heat rest"
        elif name == "warn_stop":
            reason = "servo %s at %s C, stop the walk (set point %s C)" % (sid, temp, self.warn_c)
        else:
            reason = "hottest %s C, below %s C, walk may start again" % (temp, self.restart_c)
        e = dict(t=None if t is None else round(float(t), 3), event=name, servo=sid,
                 temp_c=temp, threshold_c=thr, reason=reason)
        self.events.append(e)
        return e

    def update(self, t, temps, posture):
        new = []
        valid = {}
        just_latched = False
        for sid, v in (temps or {}).items():
            if v is None:
                continue
            v = float(v)
            if not (T_MIN_C <= v <= T_MAX_C):
                self.dropped += 1
                continue
            valid[sid] = v
            self.seen.add(sid)
            self.n_hot[sid] = self.n_hot.get(sid, 0) + 1 if v >= self.warn_c else 0
            if self.n_hot[sid] >= self.confirm and not self.latched:
                self.latched = True
                just_latched = True
                new.append(self._event(t, "warn_stop", sid, v))

        if just_latched:
            self.n_below = {}
        for sid, v in valid.items():
            if v >= self.restart_c:
                self.n_below[sid] = 0
            else:
                self.n_below[sid] = self.n_below.get(sid, 0) + 1

        if posture not in POSTURES:
            posture = "idle"

        required = self.watched if self.watched is not None else tuple(self.seen)
        fresh = bool(required) and all(self.n_below.get(i, 0) >= self.confirm for i in required)
        resumed = False
        if self.latched and posture == "walking" and fresh:
            self.latched = False
            self.n_hot = {k: 0 for k in self.n_hot}
            if valid:
                sid = max(valid, key=lambda i: valid[i])
                temp = valid[sid]
            else:
                sid, temp = None, None
            new.append(self._event(t, "resume", sid, temp))
            resumed = True

        if resumed:
            torque = "allow"
        elif posture != "walking" or self.latched:
            torque = "off"
        else:
            torque = "allow"

        if torque != self._torque:
            if torque == "off":
                hot_id = max(valid, key=lambda i: valid[i]) if valid else None
                hot_v = valid.get(hot_id) if hot_id is not None else None
                new.append(self._event(t, "torque_off", hot_id, hot_v))
            self._torque = torque
        return Decision(torque, new)


class TorqueGate:
    """Applies a Decision to a hardware object with turn_off and turn_on.

    While torque is off, position writes are skipped. A goal write can turn
    torque back on by itself (SOFTWARE.md section 8, not verified on a servo),
    so the rest does not send goals. Each 'off' decision sends turn_off again.
    """

    def __init__(self):
        self.hold_off = False
        self.skipped = 0
        self.writes = 0
        self.failures = 0

    def _call(self, hwi, name):
        fn = getattr(hwi, name, None)
        if fn is None:
            return
        try:
            fn()
        except Exception:
            self.failures += 1

    def apply(self, hwi, decision):
        if decision.torque == "off":
            self.hold_off = True
            fn = getattr(hwi, "turn_off", None)
            if fn is None:
                self.failures += 1
                raise TorqueOffFailed("the walk has no turn_off")
            try:
                fn()
            except Exception as err:
                self.failures += 1
                raise TorqueOffFailed(str(err)) from err
        elif self.hold_off:
            self.hold_off = False
            self._call(hwi, "turn_on")

    def filter_write(self, hwi, positions, write):
        if self.hold_off:
            self.skipped += 1
            return None
        self.writes += 1
        return write(positions)
