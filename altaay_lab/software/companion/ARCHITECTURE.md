# Companion architecture

Written 2026-11-12 ET. Wires published pieces. Does not fork the Runtime (D6). Does not start a cloud account. The demo in assistant.py is the first useful slice, and it runs with no hardware.

Where a new behavior would be specified, this note says details held for later.

## Pieces

```
mics (I2S, already fitted)
    wake word on the Pi, other thread     openWakeWord, or the Wyoming wake service
    speech to text on the Pi              Vosk, if a later bench says it fits
    local intent                          this folder's demo, today with text instead of speech
        timers, reminders, night light    local, no cloud
        go home                           existing software/dock states
        open question, mail, calendar     only if adult and cloud is on
            optional cloud chat           tool calls. This repo: mock_llm.py
    speech out                            Piper, when a bench says it fits
    body                                  existing walk loop, eyes, ears, head commands
```

The 50 Hz walk thread stays the Runtime loop (SOFTWARE.md section 1). Companion work does not take a turn inside that loop. The link table from PR 37 is SOFTWARE.md section 11. Unpublished times there stay BLOCKER.

## Assistant layer

Ahmed asked for a toy that talks and also does the assistant jobs: mail, calendar, reminders, and answers.

| Job | Where it runs | What this repo does |
|---|---|---|
| Wake word | Pi | Named: openWakeWord. Not installed here |
| Speech to text | Pi, if it fits | Named: Vosk. Fit is BLOCKER |
| Speech out | Pi | Named: Piper. Timing is BLOCKER |
| Timers and reminders | Pi, local list | assistant.py stores them |
| Night light | Pi GPIO eyes already in the build | The demo sets eye_on. It does not drive a pin |
| Go home | Pi, existing dock program | The demo names APPROACH, STEER_DOCK, ACTIVATE_CHARGER. Those names are the existing state machine (software/dock). Nest vision is still unwritten (SOFTWARE.md section 10) |
| Open questions | Optional cloud | Mock only |
| Mail and calendar | Optional cloud, OAuth 2.0 to the Gmail API and the Google Calendar API | Mock records only. No client id, no secret, no token |

The voice bus to copy is Wyoming, as Home Assistant Assist uses it (cited, https://www.home-assistant.io/integrations/wyoming/): one small protocol in front of a wake word, a speech engine, and Piper. Rhasspy (MIT) and OpenVoiceOS (Apache-2.0) are the other published stacks. This folder does not vendor them.

Kid mode is a flag on the demo (`mode="kid"` or `mode="adult"`). In kid mode the cloud tools are not called. Timers, reminders, the night-light flag, and the dock state names still work. How a home turns that flag on: details held for later.

The cloud switch is `cloud="off"` or `cloud="mock"`. A live provider is not a choice in this code. The mock's `complete` takes text and a tool list. It has no image argument and no audio argument. If a caller passes a credential argument, it raises and the error text does not include the value.

## Pi and cloud

| Stays on the Pi | May use the cloud |
|---|---|
| Wake word, local intent, timers, reminders, eye flag, dock state machine, walk policy, IMU | Open questions, mail, calendar |

Mail and calendar are the jobs that stop when the network stops. The local jobs do not call them.

## Latency

| Step | Number | Label |
|---|---|---|
| Walk period | 20 ms (50 Hz) | cited, the Runtime, SOFTWARE.md section 1 |
| Servo bytes in one cycle | 3.18 ms on the wire | calc only, SOFTWARE.md section 6 |
| I2S sample | 20.8 us | cited, COMPANION.md |
| Wake word on this Pi | none | BLOCKER |
| Speech to text on this Pi | none | BLOCKER |
| Speech out on this Pi | none | BLOCKER |
| Wi-Fi round trip | none | BLOCKER, SOFTWARE.md section 11 |

Until those BLOCKER rows are measured, the demo answers in text. A later bench can put a time on each row. Do not fill them with a guess.

## Privacy and the camera

- The camera is the one already fitted. Frames are not an input to the mock, and this design does not upload them.
- The wake word, when it is installed, runs on the Pi. This demo does not send audio anywhere, because it takes text.
- Mail and calendar, if a later program turns the cloud on, send text through OAuth. They do not send the camera.
- How a privacy choice is shown on the body: details held for later.
- No credential is stored in this folder.

## Kid-safe mode

Kid mode refuses mail, calendar, and open questions. The spoken line is the local one: timers and reminders still work. Adult mode may call the mock. How the mode is chosen: details held for later.

## Offline

Cloud-tied toys stop being companions when the vendor turns the servers off. The Eilik pages cited in USEFULNESS.md treat "works with no cloud" as the reason to buy that toy. This design keeps timers, reminders, the eye flag, and the existing dock state names working when `cloud="off"`. An open question then uses the same local line as kid mode. It does not wait on a provider.

## A companion, not a speaker

The speech line is the assistant. The companion is the body that is already designed: the eye blink in the Runtime, the ear servos in twin/companion/COMPANION.md, and the head command ranges in the playground joystick task (head yaw -1.5 to 1.5 rad, cited, that file). The demo's hello and night-light lines do not add a new pose.

How the body shows assistant state: details held for later.

## First demo

Name: a timer, a question, and go home.

No hardware. Checked by tests/test_assistant.py.

1. Text stands in for wake word plus speech to text.
2. "set a timer for 5 minutes" stores 5 and does not call the mock.
3. "remind me to stretch" stores the note locally.
4. "What is a duck?" in kid mode, or with the cloud off, returns the local line and does not call the mock.
5. The same question in adult mode with `cloud="mock"` returns the mock line.
6. "check my email" in kid mode is refused. In adult mode with the mock, the record subject is "Mock inbox note".
7. "go home" returns the existing dock states APPROACH, STEER_DOCK, ACTIVATE_CHARGER. It does not train a policy and it does not run MuJoCo.
8. "good night" sets eye_on. It does not drive GPIO.

Pass for this demo: those checks pass on a machine with the repo and Python. That is not a pass on the duck.

## Held

Details held for later:

- How kid or adult mode is chosen.
- How the body shows assistant state.
- How a privacy choice is shown on the body.
- How a reminder is carried to a person.
- What the body does while seated.
- When to walk home from the duck's own readings, beyond the guards already in software/SOFTWARE.md.

## Not claimed

- Sim pass only applies to training numbers in TRAINING.md, not to this demo. The demo is a Python check with no physics.
- No row in SOFTWARE.md section 11 was measured on a Pi. This note does not close any of them.
- Nest vision and a charge program are still unwritten (SOFTWARE.md section 10). Naming the old dock states does not close that gap.
- The mock is not a model and not an account.
