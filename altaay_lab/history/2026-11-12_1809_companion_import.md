# 2026-11-12 6:09 PM ET: companion import uses the package path

The Codex review on PR 51 said `from altaay_lab.software.companion.assistant import Assistant` failed because assistant.py imported mock_llm as a top-level name, and the tests hid that by putting the folder on the module path.

- assistant.py now imports the mock with a package-relative import.
- The demo tests import altaay_lab.software.companion from the repo root and do not change the module path.
- 12 tests passed again. No hardware.
