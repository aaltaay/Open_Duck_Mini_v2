# What a person at home actually uses

Written 2026-11-12 ET. This is a reading list plus a reuse list. It is not a claim that this duck does these jobs yet. Nothing here was run on a Pi or on a servo.

Labels: cited (a paper, a product page, or a file already in this repo), calc only, sim pass only, BLOCKER (not measured, or not written).

The board is the Pi Zero 2 W already in the build: 1 GHz quad-core 64-bit Arm Cortex-A53, 512 MB SDRAM, 2.4 GHz 802.11 b/g/n, CSI-2 camera connector (cited, https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/). The camera is the Camera Module 3 already fitted. The field of that camera is the one in twin/camera/CAMERA_TWIN.md. A person is not scored there (TWIN_CHECKLIST.md). The mics are the two I2S boards in twin/companion/COMPANION.md. The walk loop is the Runtime at 50 Hz on the main thread (software/SOFTWARE.md section 1, from PR 37). Pi CPU time for that loop is UNVERIFIED (SOFTWARE.md section 8). Extra models go on another thread, or they do not go on this duck.

## Rank

Ranked for a toy that also has to be worth keeping: answer and remind first, then the life-like motion that makes it a companion, then the jobs that only matter if the first two exist. Offline is a rule on every row, not a separate trick.

| Rank | Behavior | Why it is on the list | Block to reuse | On this Pi |
|---|---|---|---|---|
| 1 | React to a voice and answer | A desk toy that only plays wears off. A home robot is kept when it is useful | openWakeWord, Wyoming, Vosk or a later speech engine, Piper, optional cloud chat | Wake word is plausible beside the walk. Speech and chat timing on this board are BLOCKER |
| 2 | Reminders and timers | The practical job a voice product already does, and it needs no cloud | A local list in this folder's demo. No new library | Runs. No model |
| 3 | Expressive idle | People write about a robot pet as alive, and a desk toy is kept for that | Existing eye blink, ear servos, reference-motion polynomials | Eyes and ears are already in the build. New motion is not |
| 4 | Greet and look at you | Social rapport is a large share of what people say about a robot pet | Existing head yaw command range, camera already fitted | Direction from the mics is calc only. A person finder is BLOCKER |
| 5 | Go home and charge | A companion that dies in the hallway is not useful the next day | Existing dock state machine in software/dock | The state list is written. Nest vision is BLOCKER |
| 6 | Follow | Pet robots are expected to come along. Tricks alone do not keep an owner | Existing walk commands in the playground joystick task | Not a person-follow. BLOCKER |
| 7 | Play | Play is in the robot-pet posts. It fades if there is nothing else | Existing reference motions, not a new game | Not designed here |
| 8 | Night light | A small local job the eye beads can already do | Existing eye outputs (software/SOFTWARE.md section 12) | A flag in the demo. Not run on a bead |
| 9 | Check on pets | Asked of a home camera. Not what the cited pet studies say people keep a robot for | A person or animal model would be new | BLOCKER. No model is selected |
| 10 | Mail and calendar | The assistant half of "talks and helps". It dies if the cloud dies, so it sits last | Gmail API and Google Calendar API, OAuth 2.0. Mock only in this repo | Not on the Pi. Optional cloud. No key in this repo |

## What the sources say

AIBO forum study. Friedman, Kahn, and Hagman, CHI 2003, DOI 10.1145/642611.642660, https://old.vsdesign.org/publications/pdf/friedman03hardwarecompanions.pdf (cited, the PDF pages read for this note). They collected 6,438 postings. 3,119 postings from 182 participants said something directly about AIBO and were coded. The paper's result line: technological essences 75 percent, life-like essences 49 percent, mental states 60 percent, social rapport 59 percent. Moral standing was rare. Posts they quote talk about wandering, playing with a ball, and the robot as a companion. So life-like motion and play are why a toy pet gets talked about. They are not, by themselves, a home assistant.

Home acceptance. de Graaf, Ben Allouch, and van Dijk, "Why Would I Use This in My Home? A Model of Domestic Social Robot Acceptance", Human-Computer Interaction, 2019, DOI 10.1080/07370024.2017.1312406 (cited, the paper record). The question of the paper is the rank above: a robot in a home has to be worth using. This note does not copy their coefficients.

Eilik reviews. https://antonrobots.com/eilik-review/ (cited, the page read for this note). The standard robot works without Wi-Fi or a cloud connection. The page says its job is personality, and that it will not follow you or become a general-purpose assistant. https://ankicozmorobot.com/eilik-desktop-companion-robot/ (cited, the page read) lists over 100 reactions and expressions, and puts Vector in the other column as an assistant with a subscription. People praise the offline toy. They also name the missing assistant.

Loona. One owner's review, not a study: https://www.reddit.com/r/loona_robot/comments/1540irq/a_dads_review_of_loona_fun_for_a_few_hours/ (cited). The title is that it is fun for a few hours. The post says it is fun to borrow, not to own, and that the hardware and tricks are polished. Follow, games, and a cute walk are not enough.

Reachy Mini. https://github.com/pollen-robotics/reachy_mini (cited, the README read). Apache-2.0 for the code. Hardware files are Creative Commons BY-SA-NC. The README's first apps are a conversation app powered by large language models, a radio, and a hand tracker that follows a hand. That is the same split as the rank: talk, and a simple follow. The wireless kit uses a Compute Module 4, not this Pi Zero 2 W. It is not a benchmark for our board.

## Blocks, license, link

| Block | Job | License | Link |
|---|---|---|---|
| Open Duck Mini Runtime walk loop and ONNX policy, pin 376de65 | Walk, and the command frame the policy was trained in | No LICENSE file at that pin (altaay_lab/README.md). Use it unmodified (D6) | https://github.com/apirrone/Open_Duck_Mini_Runtime |
| Open Duck Playground joystick task, pin b9be205 | Velocity commands and head command ranges. lin vel x -0.15 to 0.15 m/s, lin vel y -0.2 to 0.2 m/s, head yaw -1.5 to 1.5 rad (cited, joystick.py default_config at that pin) | No LICENSE file at that pin (altaay_lab/README.md). D6 | https://github.com/apirrone/Open_Duck_Playground |
| Reference-motion polynomials in that playground tree | Idle and gait timing the trainer already imitates | Same pin. Not copied into this repo | playground path `playground/open_duck_mini_v2/data/polynomial_coefficients.pkl` at b9be205 |
| software/dock state machine, port of osrf/autodock | Walk on, turn, sit, for the earlier dock | Apache-2.0 (software/dock/THIRD_PARTY.md) | https://github.com/osrf/autodock |
| py_trees | A behavior tree, if a later program wants one. The demo does not import it. The dock code is already a state machine | BSD-3-Clause (LICENSE read) | https://github.com/splintered-reality/py_trees |
| openWakeWord | On-device wake word | Apache-2.0 (README read) | https://github.com/dscripka/openWakeWord |
| Wyoming, with Home Assistant Assist | The local voice bus: wake word, speech to text, speech to text out | Assist and Wyoming docs read. Core LICENSE file not opened this session | https://www.home-assistant.io/integrations/wyoming/ and https://www.home-assistant.io/voice_control/about_wake_word/ |
| Rhasspy | Older open voice stack. Same author as Piper | MIT (LICENSE read) | https://github.com/rhasspy/rhasspy |
| OpenVoiceOS (ovos-core) | Another open voice stack | Apache-2.0 (LICENSE read) | https://github.com/OpenVoiceOS/ovos-core |
| Vosk | Small on-device speech to text | Apache-2.0 (COPYING read) | https://github.com/alphacep/vosk-api |
| Piper | On-device speech out | MIT (LICENSE.md read) | https://github.com/rhasspy/piper |
| whisper.cpp | Heavier speech to text. Not claimed on this Pi | MIT is the published whisper.cpp license. The file was not re-opened this session | https://github.com/ggml-org/whisper.cpp |
| Optional cloud chat model with tool calls | Open questions, and tool calls for mail and calendar | The provider's own terms. Not chosen. The demo is a mock | none |
| Gmail API and Google Calendar API | Mail and calendar | Google's API terms. OAuth 2.0. No client and no token in this repo | https://developers.google.com/gmail/api and https://developers.google.com/calendar/api |
| OpenCV YuNet | Face box, if a later look step needs one | Apache-2.0 for OpenCV. Model card not re-read this session | https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet |
| MediaPipe face and pose | Another published detector | Apache-2.0 | https://github.com/google-ai-edge/mediapipe |

whisper.cpp's license line above is the published project license as commonly shipped. This session did not open that LICENSE file, so treat the SPDX as unchecked until someone opens it. Do not block the rest of the table on it. Vosk is the speech engine named for this Pi. whisper.cpp stays off the board until a measurement exists.

## What this hardware can run

Cited near this board, not a run on our duck:

- openWakeWord: a single core of a Raspberry Pi 3 can run 15 to 20 models at once in real time (cited, the project README, https://github.com/dscripka/openWakeWord). A Pi 3 is a faster A53 than this Zero 2 W. A timing on our Pi, next to the 50 Hz walk, is BLOCKER.
- The walk itself is designed as a 50 Hz loop. One control cycle is 318 bytes, 3.18 ms on the wire at 1 Mbaud (calc only, SOFTWARE.md section 6). USB time and Pi CPU time are BLOCKER (SOFTWARE.md sections 6 and 8).
- I2S capture is 48 kHz, one sample 20.8 us (cited, COMPANION.md section 2). A 2-channel direction estimate was 21 ms on an x86 box (calc only, COMPANION.md section 7). The Pi number is BLOCKER.
- 512 MB is the whole RAM (cited, the product page). A chat model of a few hundred MB plus the walk, the OS, and a speech engine was not fitted. On-device chat is BLOCKER. The assistant's open questions are the optional cloud client, and in this repo that client is the mock.
- Face and person frames per second on this Pi were not opened. BLOCKER. The camera link's frame rate on this duck is already BLOCKER (SOFTWARE.md section 11).

Night light, timers, reminders, and the dock state names do not need a new model.
