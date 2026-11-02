"""PASS / FAIL summary in TEST_PLAN.md terms, printed and saved as JSON.

Status words:
  PASS, FAIL   an automatic check against a TEST_PLAN.md (or cited) limit
  WARN         outside an advisory limit; does not fail the test
  INFO         a value to write down (TEST_PLAN: "log every measured value in a new history/ file")
  MANUAL       a step a person must do or confirm (meter, load rig, observation)
  INCOMPLETE   a gating check could not run or its result is not valid
Exit code: 1 if any FAIL, else 2 if any INCOMPLETE, else 0.
"""
import json
import platform
import sys
import time

ORDER = ("FAIL", "INCOMPLETE", "WARN", "PASS", "INFO", "MANUAL")


class Report:
    def __init__(self, script, section, title):
        self.script, self.section, self.title = script, section, title
        self.items = []
        self.started = time.time()
        self.data = {}

    def add(self, item, desc, status, measured=None, limit=None, source=None):
        assert status in ORDER, status
        self.items.append(dict(item=str(item), desc=desc, status=status,
                               measured=measured, limit=limit, source=source))
        return status

    def gate(self, item, desc, ok, measured=None, limit=None, source=None):
        return self.add(item, desc, "PASS" if ok else "FAIL", measured, limit, source)

    def overall(self):
        st = {i["status"] for i in self.items}
        if "FAIL" in st:
            return "FAIL"
        if "INCOMPLETE" in st:
            return "INCOMPLETE"
        return "PASS"

    def exit_code(self):
        return {"PASS": 0, "FAIL": 1, "INCOMPLETE": 2}[self.overall()]

    def render(self):
        w = max([len(i["item"]) for i in self.items] + [4])
        lines = [f"== {self.title} (TEST_PLAN.md section {self.section}) ==",
                 f"{'item'.ljust(w)}  status      check / measured / limit"]
        for i in self.items:
            meas = "" if i["measured"] is None else f" | measured {i['measured']}"
            lim = "" if i["limit"] is None else f" | limit {i['limit']}"
            src = "" if not i["source"] else f" [{i['source']}]"
            lines.append(f"{i['item'].ljust(w)}  {i['status']:<10}  {i['desc']}{meas}{lim}{src}")
        lines.append(f"OVERALL: {self.overall()}")
        return "\n".join(lines)

    def to_dict(self):
        return dict(script=self.script, section=self.section, title=self.title,
                    started=time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(self.started)),
                    host=platform.node(), python=sys.version.split()[0], argv=sys.argv[1:],
                    overall=self.overall(), items=self.items, data=self.data)

    def save(self, path):
        with open(path, "w") as fh:
            json.dump(self.to_dict(), fh, indent=1, default=str)
        return path

    def finish(self, out_dir=None, name=None, quiet=False):
        if not quiet:
            print(self.render())
        if out_dir is not None:
            p = self.save(f"{out_dir}/{name or self.script}_{time.strftime('%Y%m%d_%H%M%S')}.json")
            if not quiet:
                print(f"report: {p}")
        return self.exit_code()


def confirm(prompt, assume_yes=False):
    """Ask the operator; --yes answers yes (tests and repeat runs)."""
    if assume_yes:
        print(f"{prompt} [yes: --yes]")
        return True
    try:
        return input(f"{prompt} [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:
        return False
