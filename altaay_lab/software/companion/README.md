# Companion software

Notes and a first demo for a duck that is useful at home. The walk, the guards, and the dock program already in this repo stay as they are. This folder names the published pieces to reuse and wires a local assistant demo on top.

| File | What it is |
|---|---|
| USEFULNESS.md | Ranked home behaviors, the published block to reuse, and what this Pi can run |
| ARCHITECTURE.md | How those blocks sit together, including the assistant layer and the first demo |
| DATASETS.md | Public motion, speech, and vision sets. Nothing new was collected |
| TRAINING.md | The free CPU training smoke and the paid GPU run that still waits for an OK |
| assistant.py | The demo: timers, reminders, a mock cloud model, kid mode as a flag |
| mock_llm.py | The mock cloud model. No network and no credentials |
| tests/ | Checks for that demo. No hardware |

Run the demo checks from the repo root:

```bash
python3 -m unittest discover -s altaay_lab/software/companion/tests -v
```

Labels: cited, calc only, sim pass only, or BLOCKER. A behavior that has not been run on a duck is not hardware-proven.

Details held for later: how kid or adult mode is chosen, how the body shows assistant state, how a privacy choice is shown on the body, how a reminder is carried to a person, what the body does while seated, and when to walk home beyond the guards already in software/SOFTWARE.md.
