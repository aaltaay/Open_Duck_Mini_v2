#!/usr/bin/env python3
"""ERC for the two-net nest. The set-point checks live in check_nest_charge.py.

Also runs audit/erc.py and fails if that report has an ERROR.

  python3 altaay_lab/circuitry/nest_erc.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(LAB, ".."))


def main():
    chk = subprocess.run([sys.executable, os.path.join(HERE, "check_nest_charge.py")], cwd=ROOT)
    erc = subprocess.run([sys.executable, os.path.join(LAB, "audit", "erc.py")], cwd=ROOT,
                         capture_output=True, text=True)
    tail = "\n".join(erc.stdout.splitlines()[-8:])
    print(tail)
    bad = "ERROR" in erc.stdout and "0 ERROR" not in erc.stdout
    # The report line is "Findings: N ERROR".
    for line in erc.stdout.splitlines():
        if line.startswith("Findings:"):
            print(line)
            bad = not line.startswith("Findings: 0 ERROR")
    if chk.returncode != 0 or erc.returncode != 0 or bad:
        print("nest ERC FAIL")
        return 1
    print("nest ERC PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
