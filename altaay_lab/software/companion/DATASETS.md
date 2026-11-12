# Datasets already public

Written 2026-11-12 ET. Nothing new was recorded. Nothing in this list was downloaded into the repo. Files over 5 MB stay at the upstream URL. A hash below is of a file that already ships in a pinned public tree. It was not copied here (D6).

## Motion

| Set | What it is | License | Where | This session |
|---|---|---|---|---|
| Reference motions for the mini | Polynomials the playground imitates when USE_IMITATION_REWARD is true | No LICENSE file in the playground or the generator at the pins in altaay_lab/README.md. D6: do not republish | Generator https://github.com/apirrone/Open_Duck_reference_motion_generator at 3d7bc6fd. The file used by training is `playground/open_duck_mini_v2/data/polynomial_coefficients.pkl` in Open_Duck_Playground at b9be205 | sha256 `5850c0610ed89e2860e7047f9ee27d8412462e1199752952c3c2a0efd2cb7a25` (computed from that pin). The file is about 3 MB. Not stored here |

The gait period 0.54 s already cited from that reference motion stays in the lab notes that computed it. This file does not recompute it.

## Speech

| Set | What it is | License | Where | This session |
|---|---|---|---|---|
| Mozilla Common Voice | Read speech, many speakers | CC0 | https://commonvoice.mozilla.org/en/datasets | Not downloaded |
| LibriSpeech | Read audiobooks | CC BY 4.0 | https://www.openslr.org/12 | Not downloaded |
| Speech Commands | Short command words, the usual wake-word and command set | CC BY 4.0. Paper: Warden, arXiv:1804.03209, https://arxiv.org/abs/1804.03209 | https://www.tensorflow.org/datasets/catalog/speech_commands | Not downloaded |

openWakeWord's own training page, as Home Assistant describes it, builds wake-word clips with Piper and mixes them with noise (cited, https://www.home-assistant.io/voice_control/about_wake_word/). That is the published way to make a wake word. This session did not train one.

## Vision

| Set | What it is | License | Where | This session |
|---|---|---|---|---|
| COCO | Photos with person boxes, if a later detector needs them | CC BY 4.0 | https://cocodataset.org/#termsofuse | Not downloaded |

No camera frames from this project exist. twin/camera/CAMERA_TWIN.md is geometry, not a dataset. Collecting a new set is out of this pass.

## Not a dataset

The mock inbox and the mock calendar in mock_llm.py are two canned records. They are not mail and not a calendar export.
