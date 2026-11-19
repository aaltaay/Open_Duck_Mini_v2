# Companion software

Notes and a first demo for a duck that is useful at home. The walk, the guards, and the dock program already in this repo stay as they are. This folder names the published pieces to reuse and wires a local assistant demo on top.

| File | What it is |
|---|---|
| USEFULNESS.md | Ranked home behaviors, the published block to reuse, and what this Pi can run |
| ARCHITECTURE.md | How those blocks sit together, including the assistant layer and the first demo |
| DATASETS.md | Public motion, speech, and vision sets. Nothing new was collected |
| TRAINING.md | The free CPU training smoke and the paid GPU run that still waits for an OK |
| LATENCY.md | x86 timings for wake, speech to text, and speech out, plus the clock scale toward this Pi |
| assistant.py | Timers, reminders, clock, weather, a mock or live cloud model, kid mode. Body poses come from software/personality/ |
| pipeline.py | Wake, speech to text, the assistant, speech out. Not the walk thread |
| ../personality/ | Mood, expressions, and the choice to go home, sit, or nap. Off the walk thread |
| install_voice.sh | Pi install for the models. Models are not committed |
| mock_llm.py | The mock cloud model. No network and no credentials |
| cloud_llm.py | Optional live model. The key stays in the environment |
| tests/ | Checks for the assistant and the pipeline. No hardware |
| out/voice_desktop_demo.mp4 | Desktop drawing of one spoken timer. Not the robot |

Run the demo checks from the repo root:

```bash
python3 -m unittest discover -s altaay_lab/software/companion/tests -v
python3 -m unittest discover -s altaay_lab/software/personality/tests -v
```

The spoken path needs the models from `install_voice.sh`. Those files are not in git. LATENCY.md is the x86 timing. A Pi timing is still BLOCKER.

Labels: cited, calc only, sim pass only, or BLOCKER. A behavior that has not been run on a duck is not hardware-proven.

Still held: how kid or adult mode is chosen, and how a privacy choice is shown on the body. The body poses, the reminder carry, the seated look, and walking home from a low pack are in software/personality/PERSONALITY.md.
