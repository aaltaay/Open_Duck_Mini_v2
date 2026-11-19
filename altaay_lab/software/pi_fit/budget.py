"""Deadline and RAM rules for the walk fit check.

The 20 ms period is the Runtime control rate of 50 Hz. A cycle misses when
the measured work is longer than that. SOFTWARE.md section 6 adds 5.18 ms
of bus time when each USB read is taken as 1 ms. That bus add is calc only.
The real USB round trip is still BLOCKER, so a pass here is not a hardware pass.
"""

from __future__ import annotations

PERIOD_S = 0.020
# Calc only. SOFTWARE.md section 6, control part at 1 ms USB per read.
BUS_ASSUMED_S = 0.00518

# Cited. Raspberry Pi product page: 512 MB SDRAM.
CHIP_MIB = 512.0
# Cited. Bookworm Lite 64-bit top snapshot on a Zero 2 W: Mem total 417.0,
# used 125.4, available 291.6. https://docs.printercow.com/guide/32bit-vs-64bit.html
VISIBLE_MIB = 417.0
OS_USED_MIB = 125.4


def percentile(values, pct):
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (float(pct) / 100.0)
    lo = int(rank)
    hi = min(lo + 1, len(ordered) - 1)
    frac = rank - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def work_stats(work_s):
    work_s = list(work_s)
    cpu_miss = sum(1 for item in work_s if item > PERIOD_S)
    bus_miss = sum(1 for item in work_s if item + BUS_ASSUMED_S > PERIOD_S)
    return {
        "n": len(work_s),
        "misses_cpu": cpu_miss,
        "misses_cpu_plus_bus": bus_miss,
        "p50_s": percentile(work_s, 50),
        "p99_s": percentile(work_s, 99),
        "max_s": max(work_s) if work_s else None,
        "bus_assumed_s": BUS_ASSUMED_S,
        "bus_label": "calc only",
        "period_s": PERIOD_S,
    }


def period_jitter(period_s):
    period_s = list(period_s)
    if not period_s:
        return {"n": 0, "p50_s": None, "p99_s": None, "min_s": None, "max_s": None, "span_s": None}
    return {
        "n": len(period_s),
        "p50_s": percentile(period_s, 50),
        "p99_s": percentile(period_s, 99),
        "min_s": min(period_s),
        "max_s": max(period_s),
        "span_s": max(period_s) - min(period_s),
    }


def slice_stats(work_s, period_s, start, end):
    """Stats for cycles whose index is in [start, end)."""
    start = max(0, int(start))
    end = max(start, int(end))
    return {
        "work": work_stats(work_s[start:end]),
        "period": period_jitter(period_s[start:end]),
        "index": [start, end],
    }


def ram_fits(peak_mib, swap_mib, limit_mib):
    if peak_mib is None or limit_mib is None:
        return False
    if swap_mib is not None and float(swap_mib) > 1.0:
        return False
    return float(peak_mib) <= float(limit_mib) + 0.05


def cpu_fits(stats):
    """True when no cycle misses, counting the calc-only bus add."""
    if not stats or stats.get("n", 0) < 1:
        return False
    return int(stats.get("misses_cpu_plus_bus") or 0) == 0


def verdict(baseline_ok, fixed_ok):
    if baseline_ok:
        return "fits"
    if fixed_ok:
        return "fits with fixes"
    return "does not fit"


def quota_us(measured_coremark, cited_coremark, period_us=100000):
    """CPU quota so an emulated core matches a cited CoreMark score.

    Returns microseconds of quota per period. Calc only from the two scores.
    """
    if measured_coremark <= 0 or cited_coremark <= 0:
        raise ValueError("coremark scores must be positive")
    share = float(cited_coremark) / float(measured_coremark)
    if share > 1.0:
        share = 1.0
    return max(1000, int(round(share * period_us)))
