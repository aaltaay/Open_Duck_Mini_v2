"""Docs check for the build guide and the owner's manual.

Links resolve to a file in the repo, or they are http(s).
The pages have no em dash and no en dash.
Every repo path they name exists.
They do not carry a price or a machine path.

Run from the repo root:
  python3 -m unittest discover -s altaay_lab/software/tests -v
"""
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(LAB)
DOCS = os.path.join(LAB, "docs")

EM_DASH = "\u2014"
EN_DASH = "\u2013"
LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)\)|!\[([^\]]*)\]\(([^)\s]+)\)")
PATH_RE = re.compile(r"(?:altaay_lab|\.\.)/[\w./+-]+")
PRICE_RE = re.compile(r"\$\s*\d")
LOCAL_RE = re.compile(
    r"/home/|/tmp/|/workspace|/opt/cursor|/agent/|F:\\|C:\\Users",
    re.IGNORECASE,
)


def _pages():
    names = sorted(
        name for name in os.listdir(DOCS) if name.endswith(".md")
    )
    if not names:
        raise AssertionError("no markdown pages in altaay_lab/docs")
    return [os.path.join(DOCS, name) for name in names]


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _strip_anchor(target):
    return target.split("#", 1)[0].strip()


def _exists(page_dir, rel):
    rel = rel.rstrip(".,);")
    if not rel:
        return True
    candidates = [
        os.path.normpath(os.path.join(page_dir, rel)),
        os.path.normpath(os.path.join(ROOT, rel)),
        os.path.normpath(os.path.join(LAB, rel)),
    ]
    if rel.startswith("altaay_lab/"):
        candidates.append(os.path.normpath(os.path.join(ROOT, rel)))
    return any(os.path.exists(c) for c in candidates)


class DocsCheck(unittest.TestCase):
    def test_pages_exist(self):
        names = {os.path.basename(p) for p in _pages()}
        self.assertIn("BUILD_GUIDE.md", names)
        self.assertIn("OWNERS_MANUAL.md", names)

    def test_no_em_dash(self):
        bad = []
        for path in _pages():
            text = _read(path)
            for i, line in enumerate(text.splitlines(), 1):
                if EM_DASH in line or EN_DASH in line or "&mdash;" in line or "&#8212;" in line:
                    bad.append("%s:%d" % (os.path.basename(path), i))
        self.assertEqual(bad, [], "em dash or en dash: %s" % ", ".join(bad))

    def test_links_and_paths_resolve(self):
        missing = []
        for path in _pages():
            text = _read(path)
            page_dir = os.path.dirname(path)
            for match in LINK_RE.finditer(text):
                target = match.group(2) or match.group(4)
                rel = _strip_anchor(target)
                if not rel:
                    continue
                if rel.startswith(("http://", "https://", "mailto:")):
                    self.assertIn("://", rel)
                    continue
                if not _exists(page_dir, rel):
                    missing.append("%s -> %s" % (os.path.basename(path), target))
            for match in PATH_RE.finditer(text):
                rel = match.group(0).rstrip(".,);")
                if not _exists(page_dir, rel):
                    missing.append("%s path %s" % (os.path.basename(path), rel))
        self.assertEqual(missing, [], "missing files: %s" % "; ".join(missing))

    def test_no_prices_or_local_paths(self):
        bad = []
        for path in _pages():
            text = _read(path)
            if PRICE_RE.search(text):
                bad.append(os.path.basename(path) + " has a price")
            if LOCAL_RE.search(text):
                bad.append(os.path.basename(path) + " has a local path")
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
