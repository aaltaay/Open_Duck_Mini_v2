"""Bus reads on their own timer, run only while the walk loop sleeps (TEST_PLAN 9 voltage log).

Why a timer of its own: the servo current, and so the voltage dip, peaks just after each 50 Hz
goal write. A read made once per control cycle (the old power_log.py) always lands at the same
point of the 20 ms cycle, so its "% of samples under 6 V" depends on that point: 10 to 34 % on
the sim replay whose time-weighted answer is 21 % (sim/POWER_FIX.md, sim pass only).

Timer: one read at a random time inside each slot of `period_s` (stratified sampling). The
reads then have the same density at every moment, so they cannot lock to the 20 ms control
period, to the 540 ms gait (27 control cycles: Runtime scripts/polynomial_coefficients.pkl
period 0.54 s at 50 fps) or to anything else. A fixed period does lock: 27 ms is exactly 1/20
of the gait, so a fixed 27 ms timer repeats the same 20 points of the step cycle (sim replay,
60 s: off by up to 10.9 points when the loop runs at 20.0 ms; software/SOFTWARE.md section 6).

Rule: a read never delays a control write. The servo bus is one wire, so a read can only use
time the walk loop does not: the Runtime loop ends each cycle with time.sleep(1/50 - took)
(scripts/v2_rl_walk_mujoco.py RLWalk.run). walkhooks puts IdleScheduler.idle() in place of that
sleep. A read starts only if its expected time (the longest read of the last 0.5 s; see
TimedRead.cost_s) plus a 2 ms margin ends before the sleep would have ended; otherwise the slot
is skipped and counted. A read that has started runs to its end: cut short, its late replies
would reach rustypot's next send and panic it (G10; seen on the simulated bus under load). So a
read slower than expected can run into the next cycle; that is counted (overruns), never hidden.

Each slot ends as one record (on_slot callback), with its phase: the time from the last goal
write before the slot to the slot (or to the read start):
  read   the read ran; `result` is what read() returned
  busy   the slot's time passed while the walk loop was working (outside its sleep)
  own    the slot's time passed during this task's previous read
  room   the slot fell in the sleep, too close to its end for a read
Times come from `clock` (time.monotonic); `sleep` is the real time.sleep. Both can be replaced
(tests drive the scheduler with a virtual clock).

Counting in time (time_count): the goal writes (walkhooks write_log) give the exact share of the
walking time in each 1 ms bin of the time since the last write (the slots, uniform in time, give
the same in the mean); the reads in a bin give that bin's share under the threshold. The time
share is the sum over bins.
Bins never read (the busy end of each cycle, before the next goal write) take the share of the
last bins read (back from the last one until 50 readings); the voltage recovers toward the end of
each cycle (the current peaks just after the write), so this fill is high, not low, while
recovery_ok() holds. If the read part of the cycle ends inside a dip, the fill is the dip: the
count is then too high, never too low.
"""
import random
import time

STATUSES = ("read", "busy", "own", "room")


class SlotTimer:
    """Slot k is [t0 + k P, t0 + (k + 1) P); its read time is drawn uniformly inside it."""

    def __init__(self, period_s, seed=None):
        if period_s <= 0:
            raise ValueError("period must be > 0")
        self.period_s = float(period_s)
        self.rng = random.Random(seed)
        self.t0 = None
        self.k = 0
        self.due = None

    def start(self, t0):
        self.t0, self.k = float(t0), 0
        self.due = self.t0 + self.rng.random() * self.period_s

    def advance(self):
        self.k += 1
        self.due = self.t0 + (self.k + self.rng.random()) * self.period_s


def phase_of(t, st):
    """Time from the last goal write before t to t (st: walk_state() dict), or None."""
    lw, pw = st.get("last_write"), st.get("prev_write")
    if lw is not None and t >= lw:
        return t - lw
    if pw is not None and t >= pw:
        return t - pw
    return None


class TimedRead:
    """A bus read on its own SlotTimer. read(end_by) gets the time one margin before the next cycle
    (a read that must not touch the bus after it may use it; a bus read should run to its end) and
    returns anything; it may raise. A read that ends more than late_tol_s after the next cycle was
    due is counted as an overrun."""

    def __init__(self, name, read, period_s=0.027, seed=27, margin_s=0.002, first_cost_s=0.0045,
                 cost_hold_s=0.5, late_tol_s=0.0005, on_slot=None, clock=time.monotonic):
        self.name, self.read = name, read
        self.timer = SlotTimer(period_s, seed)
        self.margin_s = float(margin_s)
        self.first_cost_s = float(first_cost_s)
        self.cost_hold_s = float(cost_hold_s)
        self.late_tol_s = float(late_tol_s)
        self.on_slot = on_slot
        self.clock = clock
        self.recent = []                 # (end time, duration s) of the last reads
        self.counts = {s: 0 for s in STATUSES}
        self.read_s = []                 # every read duration (s)
        self.overruns = []               # (slot, s past the end of the sleep)
        self.errors = 0

    # ------------------------------------------------------------------ timer
    @property
    def due(self):
        return self.timer.due

    @property
    def period_s(self):
        return self.timer.period_s

    def started(self):
        return self.timer.t0 is not None

    def start(self, t0):
        self.timer.start(t0)

    def cost_s(self):
        """Expected time of the next read: the longest read that ended in the last cost_hold_s.
        If none did, the last read's time halved for every cost_hold_s since it ended, but not
        below the first guess. So a slow read keeps the next reads away for a while, and no read,
        however slow, can stop all later reads (it would if the estimate never came down: a read
        longer than the whole sleep would never let another start). Before any read: the first guess."""
        if not self.recent:
            return self.first_cost_s
        now = self.clock()
        held = [d for t, d in self.recent if now - t <= self.cost_hold_s]
        if held:
            return max(held)
        t_last, d_last = self.recent[-1]
        return max(self.first_cost_s, d_last * 0.5 ** int((now - t_last) // self.cost_hold_s))

    # ------------------------------------------------------------------ records
    def _record(self, status, st, **kw):
        self.counts[status] += 1
        if self.on_slot is not None:
            rec = dict(task=self.name, slot=self.timer.k, due=self.timer.due, status=status,
                       state=st.get("state"), cycle=st.get("cycle"), last_write=st.get("last_write"),
                       phase=phase_of(self.timer.due, st))
            rec.update(kw)
            self.on_slot(rec)
        self.timer.advance()

    def expire(self, now, why, ctx=None):
        """Every slot whose time is before `now` and that was not read is closed as `why`."""
        st = None
        while self.started() and self.timer.due < now:
            st = st or (ctx() if ctx else {})
            self._record(why, st)

    def fire(self, now, deadline, ctx=None):
        """The slot is due (due <= now < deadline): read if the read can end before the deadline."""
        cost = self.cost_s()
        st = ctx() if ctx else {}
        lw = st.get("last_write")
        room = None if lw is None else deadline - cost - self.margin_s - lw
        if now + cost + self.margin_s > deadline:
            self._record("room", st, room=room)
            return
        t_start = self.clock()
        err = None
        try:
            result = self.read(deadline - self.margin_s)
        except Exception as e:           # noqa: BLE001 - a failed read is a record, not a crash
            result, err = None, f"{type(e).__name__}: {e}"
            self.errors += 1
        t_end = self.clock()
        dur = t_end - t_start
        self.read_s.append(dur)
        self.recent.append((t_end, dur))
        if len(self.recent) > 64:
            self.recent.pop(0)
        if t_end > deadline + self.late_tol_s:
            self.overruns.append((self.timer.k, t_end - deadline))
        self._record("read", st, t_read=t_start, read_s=dur, left_s=deadline - t_end, room=room,
                     phase=phase_of(t_start, st), result=result, error=err)

    def stats(self):
        n = sum(self.counts.values())
        rs = sorted(self.read_s)
        out = dict(period_ms=round(self.period_s * 1e3, 3), slots=n, **self.counts,
                   coverage=round(self.counts["read"] / n, 4) if n else None,
                   overruns=len(self.overruns),
                   overrun_max_ms=round(max(o for _, o in self.overruns) * 1e3, 3) if self.overruns else 0.0,
                   read_errors=self.errors, margin_ms=round(self.margin_s * 1e3, 3))
        if rs:
            out.update(read_ms_mean=round(sum(rs) / len(rs) * 1e3, 3),
                       read_ms_p99=round(rs[min(len(rs) - 1, int(0.99 * len(rs)))] * 1e3, 3),
                       read_ms_max=round(rs[-1] * 1e3, 3))
        return out


class IdleScheduler:
    """Runs TimedRead tasks inside the walk loop's sleep and never past its end.

    idle(seconds) replaces time.sleep(seconds) at the end of each Runtime cycle. `ctx()` returns
    dict(state=..., last_write=..., prev_write=..., cycle=...) for the records."""

    def __init__(self, tasks, clock=time.monotonic, sleep=time.sleep, ctx=None):
        self.tasks = list(tasks)
        self.clock, self._sleep, self.ctx = clock, sleep, ctx
        self.calls = 0
        self.idle_s = 0.0

    def start(self, t0):
        for t in self.tasks:
            if not t.started():
                t.start(t0)

    def idle(self, seconds):
        now = self.clock()
        deadline = now + max(0.0, seconds)
        self.calls += 1
        self.idle_s += max(0.0, seconds)
        self.start(now)                  # no-op once started (walkhooks starts it at the first cycle)
        for t in self.tasks:
            t.expire(now, "busy", self.ctx)
        while True:
            now = self.clock()
            pending = [t for t in self.tasks if t.due < deadline]
            if not pending:
                break
            task = min(pending, key=lambda t: t.due)
            if task.due > now:
                self._sleep(min(task.due, deadline) - now)
                continue
            task.fire(now, deadline, self.ctx)
            after = self.clock()
            for t in self.tasks:
                t.expire(after, "own", self.ctx)
        rest = deadline - self.clock()
        if rest > 0:
            self._sleep(rest)


# ---------------------------------------------------------------------- counting in time
def _bin(ph, bin_ms, n_bins):
    return min(n_bins, int(ph // bin_ms))


def write_weights(rows, states=("walk", ""), bin_ms=1.0, n_bins=20, max_gap_s=0.5):
    """Time (ms) in each phase bin, from the goal writes ('write' rows: t_s, state): every gap
    between two writes, the first one in a walking state and at most max_gap_s long, covers phases
    0 to its length. None if the rows hold no writes."""
    w = sorted((float(r["t_s"]), r.get("state", "")) for r in rows
               if r.get("status") == "write" and _f(r.get("t_s")) is not None)
    if len(w) < 2:
        return None
    out = [0.0] * (n_bins + 1)
    for (t1, s1), (t2, _) in zip(w, w[1:]):
        gap = (t2 - t1) * 1e3
        if s1 not in states or not 0 < gap <= max_gap_s * 1e3:
            continue
        for b in range(n_bins):
            out[b] += max(0.0, min((b + 1) * bin_ms, gap) - b * bin_ms)
        out[n_bins] += max(0.0, gap - n_bins * bin_ms)
    return out if sum(out) > 0 else None


def time_count(rows, ids, threshold=6.0, states=("walk", ""), bin_ms=1.0, n_bins=20, fill_min=50, fill_bins=None,
               latch_ms=None, after_ms=0.0):
    """Count time under `threshold` per servo from slot rows (power_log.py CSV rows as dicts).

    Only rows whose state is in `states` count (paused and stop phases do not). The time in each
    phase bin comes from the goal writes when the rows hold them (write_weights), else from the
    phases of the slots (uniform in time, so the same in the mean, with more scatter). For servo i:
      time_frac    sum over bins of (bin share of the walking time) x (bin readings under / readings):
                   the gate value (module doc)
      sampled_frac readings under / readings      (U: share of the sampled time)
      walk_frac    readings under / walk slots    (L: unsampled time counted as above; L <= true)
    Rows without any phase (a fixed-rate log, no control loop) give time_frac = sampled_frac.
    Bin n_bins holds every phase of n_bins x bin_ms or more (late cycles).
    latch_ms {id: ms}, after_ms: a reading that started at phase p is binned at
    max(p, after_ms) + latch_ms[id], the moment the servo is taken to read its register (power_log
    gives the bus model: the goal write's bytes first, then the request, then the replies ahead of
    that servo). If the servo reads earlier than that, the count can only come out higher."""
    walk = [r for r in rows if r.get("state", "") in states and r.get("status") != "write"]
    n_slots = len(walk)
    weights = write_weights(rows, states, bin_ms, n_bins)
    if weights is None:
        weights = [0.0] * (n_bins + 1)
        for r in walk:
            ph = _f(r.get("phase_ms"))
            if ph is not None and ph >= 0:
                weights[_bin(ph, bin_ms, n_bins)] += 1.0
    total = sum(weights)
    out = {}
    for i in ids:
        vals, late, late_under = [], 0, 0
        reads_b, under_b = [0] * (n_bins + 1), [0] * (n_bins + 1)
        for r in walk:
            if r.get("status", "read") not in ("read", "cycle"):
                continue
            v = _f(r.get(f"v_{i}"))
            if v is None:
                continue
            vals.append(v)
            ph, room = _f(r.get("phase_ms")), _f(r.get("room_ms"))
            if ph is not None and ph >= 0:
                b = _bin(max(ph, after_ms) + (latch_ms or {}).get(i, 0.0), bin_ms, n_bins)
                reads_b[b] += 1
                under_b[b] += v < threshold
            if ph is not None and room and room > 0 and ph >= room * 2.0 / 3.0:
                late += 1
                late_under += v < threshold
        n = len(vals)
        under = sum(v < threshold for v in vals)
        frac, filled, fill = _phase_weighted(weights, reads_b, under_b, total, fill_min, fill_bins)
        if frac is None and n:
            frac = under / n
        out[i] = dict(slots=n_slots, sampled=n, under=under, time_frac=frac,
                      sampled_frac=under / n if n else None,
                      walk_frac=under / n_slots if n_slots else None,
                      coverage=n / n_slots if n_slots else None,
                      filled_bins=filled, fill_frac=fill,
                      v_min=min(vals) if vals else None, v_mean=sum(vals) / n if n else None,
                      late=late, late_frac=late_under / late if late else None,
                      bins=[(k * bin_ms, (weights[k] / total if total else None), reads_b[k],
                             (under_b[k] / reads_b[k] if reads_b[k] else None)) for k in range(n_bins + 1)])
    return out


def _phase_weighted(slots_b, reads_b, under_b, n_phase, fill_min, fill_bins):
    """Sum over phase bins of (bin weight / total weight) x (share of the bin's reads under).
    A bin with weight but no reads takes the pooled share of the nearest read bins before it
    (until fill_min reads; at most fill_bins bins if set), or after it if none comes before.
    Returns (frac, filled bins, last fill value)."""
    if not n_phase or not any(reads_b):
        return None, [], None
    nb = len(slots_b)
    share = [None] * nb
    for k in range(nb):
        if reads_b[k]:
            share[k] = under_b[k] / reads_b[k]
    filled, fill = [], None
    for k in range(nb):
        if share[k] is not None or not slots_b[k]:
            continue
        idx = [j for j in range(k - 1, -1, -1) if reads_b[j]] or [j for j in range(k + 1, nb) if reads_b[j]]
        n = u = 0
        for j in idx[:fill_bins] if fill_bins else idx:
            n += reads_b[j]
            u += under_b[j]
            if n >= fill_min:
                break
        share[k] = fill = u / n
        filled.append(k)
    frac = sum(slots_b[k] / n_phase * share[k] for k in range(nb) if slots_b[k])
    return frac, filled, fill


def recovery_ok(d):
    """True if the readings in the last third of each cycle's sampled window are not more often
    under the threshold than all readings (within two standard errors): the voltage is
    recovering when sampling stops, so the fill of the unread bins is not low. None if it cannot
    be told (no readings, or none in a late third)."""
    u, n_late, f_late = d["sampled_frac"], d["late"], d["late_frac"]
    if u is None or not n_late:
        return None
    se = (max(u * (1 - u), 1.0 / n_late) / n_late) ** 0.5
    return f_late <= u + 2 * se


def _f(x):
    if x in ("", None):
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None
