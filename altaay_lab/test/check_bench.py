"""Compare a bench record to a twin prediction or to a TEST_PLAN gate.

A not_run record is a skip, not a pass. A match is not a hardware pass of the
duck: it only says the filled numbers sit inside the stated band.

  python3 altaay_lab/test/check_bench.py --self-test
  python3 altaay_lab/test/check_bench.py RECORD.yaml --predict PREDICT.yaml
  python3 altaay_lab/test/check_bench.py RECORD.yaml --gates

Hop gates, TEST_PLAN section 5:
  2S: pass at most 28 mOhm, warn through 40 mOhm, fail over 40, per conductor.
  3S: pass at most 100 mOhm per conductor (the line already in that section).

Walk-log gates, TEST_PLAN section 9, apply to the 2S build (6.0 V and 4.5 V).
The 12 V duck uses the page floor of 4.0 V as a hard fail, and otherwise
compares to the twin prediction. Do not score a 12 V log with the 6.0 V gate.
"""
import argparse
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(HERE, "records", "templates")


def load(path):
    with open(path) as f:
        doc = yaml.safe_load(f)
    if not isinstance(doc, dict):
        raise SystemExit("not a mapping: %s" % path)
    return doc


def check_templates():
    names = sorted(os.listdir(TEMPLATES))
    docs = []
    for name in names:
        if not name.endswith((".yaml", ".yml")):
            continue
        doc = load(os.path.join(TEMPLATES, name))
        for key in ("record_id", "test_plan", "status", "rows"):
            if key not in doc:
                raise SystemExit("%s missing %s" % (name, key))
        if doc["status"] != "not_run":
            raise SystemExit("%s template must stay not_run" % name)
        docs.append(doc)
    if len(docs) < 5:
        raise SystemExit("expected several templates, found %d" % len(docs))
    return docs


def hop_gate(mohm, pack):
    if pack == "2S":
        if mohm <= 28.0:
            return "PASS"
        if mohm <= 40.0:
            return "WARN"
        return "FAIL"
    if pack == "3S":
        if mohm <= 100.0:
            return "PASS"
        return "FAIL"
    raise SystemExit("pack must be 2S or 3S")


def walk_gate(row, pack):
    """row has min_V and, for 2S, pct_under_6V."""
    if pack == "2S":
        if row["min_V"] < 4.5:
            return "FAIL"
        if row.get("pct_under_6V", 0.0) > 10.0:
            return "FAIL"
        return "PASS"
    if pack == "3S":
        if row["min_V"] < 4.0:
            return "FAIL"
        return "COMPARE"
    raise SystemExit("pack must be 2S or 3S")


def compare(record, predict):
    if record.get("status") == "not_run":
        return dict(result="SKIP", mismatches=[], unmatched=[], compared=0)
    by_id = {r["id"]: r for r in predict.get("rows", [])}
    mismatches = []
    unmatched = []
    compared = 0
    for row in record.get("rows", []):
        if row.get("value") is None:
            continue
        pred = by_id.get(row["id"])
        if pred is None:
            unmatched.append(row["id"])
            continue
        compared += 1
        err = abs(float(row["value"]) - float(pred["predict"]))
        tol = float(pred["tol_abs"])
        if err > tol:
            mismatches.append(dict(id=row["id"], value=row["value"], predict=pred["predict"], tol_abs=tol, err=round(err, 4)))
    # A measured record with nothing checked is not a pass. A filled id the
    # prediction does not name is an error, not a skip.
    if unmatched or compared == 0 or mismatches:
        result = "FAIL"
    else:
        result = "PASS"
    return dict(result=result, mismatches=mismatches, unmatched=unmatched, compared=compared)


def score_gates(record):
    """Return printed lines and whether any measured hop or walk row failed."""
    pack = record.get("pack")
    lines = []
    failed = False
    for row in record.get("rows", []):
        if row.get("value") is None:
            lines.append("%s SKIP" % row["id"])
            continue
        if str(row["id"]).startswith("hop"):
            verdict = hop_gate(float(row["value"]), pack)
        elif str(row["id"]).startswith("walk"):
            verdict = walk_gate(row["value"], pack)
        else:
            lines.append("%s SKIP" % row["id"])
            continue
        lines.append("%s %s" % (row["id"], verdict))
        if verdict == "FAIL":
            failed = True
    return lines, failed


def self_test():
    check_templates()
    if hop_gate(28.0, "2S") != "PASS" or hop_gate(40.0, "2S") != "WARN" or hop_gate(40.1, "2S") != "FAIL":
        raise SystemExit("2S hop gates")
    if hop_gate(100.0, "3S") != "PASS" or hop_gate(100.1, "3S") != "FAIL":
        raise SystemExit("3S hop gates")
    if walk_gate(dict(min_V=5.0, pct_under_6V=9.0), "2S") != "PASS":
        raise SystemExit("2S walk pass")
    if walk_gate(dict(min_V=5.0, pct_under_6V=11.0), "2S") != "FAIL":
        raise SystemExit("2S walk time")
    if walk_gate(dict(min_V=4.4, pct_under_6V=0.0), "2S") != "FAIL":
        raise SystemExit("2S walk floor")
    if walk_gate(dict(min_V=9.3), "3S") != "COMPARE":
        raise SystemExit("3S walk should compare to the twin, not use 6 V")
    if walk_gate(dict(min_V=3.9), "3S") != "FAIL":
        raise SystemExit("3S page floor")
    predict = dict(rows=[dict(id="bec_case_C", predict=50.0, tol_abs=15.0)])
    blank = dict(status="not_run", rows=[dict(id="bec_case_C", value=None)])
    inside = dict(status="measured", rows=[dict(id="bec_case_C", value=55.0)])
    outside = dict(status="measured", rows=[dict(id="bec_case_C", value=80.0)])
    if compare(blank, predict)["result"] != "SKIP":
        raise SystemExit("blank should skip")
    if compare(inside, predict)["result"] != "PASS":
        raise SystemExit("inside band should pass the compare")
    if compare(outside, predict)["result"] != "FAIL":
        raise SystemExit("outside band should fail the compare")
    wrong_id = dict(status="measured", rows=[dict(id="case_C_10min_5A", value=999.0)])
    missed = compare(wrong_id, predict)
    if missed["result"] != "FAIL" or missed["unmatched"] != ["case_C_10min_5A"] or missed["compared"] != 0:
        raise SystemExit("unmatched filled id must fail: %s" % missed)
    empty = dict(status="measured", rows=[dict(id="bec_case_C", value=None)])
    if compare(empty, predict)["result"] != "FAIL":
        raise SystemExit("measured record with no values must fail")
    lines, failed = score_gates(dict(status="measured", pack="3S", rows=[dict(id="hop_vplus_mohm", value=200.0)]))
    if (not failed) or lines != ["hop_vplus_mohm FAIL"]:
        raise SystemExit("3S 200 mOhm hop must fail the gate: %s" % lines)
    lines, failed = score_gates(dict(status="measured", pack="3S", rows=[dict(id="hop_vplus_mohm", value=20.0)]))
    if failed or lines != ["hop_vplus_mohm PASS"]:
        raise SystemExit("3S 20 mOhm hop must pass: %s" % lines)
    print("self-test PASS: templates, hop gates, walk gates, compare")
    return 0


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument("record", nargs="?")
    p.add_argument("--predict")
    p.add_argument("--gates", action="store_true")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.record:
        raise SystemExit("give a record, or --self-test")
    record = load(args.record)
    if args.gates:
        if record.get("status") == "not_run":
            print("SKIP not_run")
            return 0
        lines, failed = score_gates(record)
        print("\n".join(lines))
        return 1 if failed else 0
    if not args.predict:
        raise SystemExit("give --predict or --gates")
    result = compare(record, load(args.predict))
    print(result["result"])
    for name in result.get("unmatched") or []:
        print("unmatched %s" % name)
    for m in result["mismatches"]:
        print(m)
    return 0 if result["result"] in ("PASS", "SKIP") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
