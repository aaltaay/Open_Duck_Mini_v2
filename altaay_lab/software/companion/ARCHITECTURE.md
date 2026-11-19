# Companion architecture

Written 2026-11-12 ET. Wires published pieces. Does not fork the Runtime (D6). Does not start a cloud account. The demo in assistant.py is the first useful slice, and it runs with no hardware.

Where a new behavior would be specified, this note says details held for later.

## Pieces

```
mics (I2S, already fitted, 48 kHz)
    wake word, other thread          openWakeWord hey_jarvis, one model
    speech to text, other thread     Vosk small English
    local intent                     assistant.py
        timers, reminders, clock     local, no cloud
        weather                      Open-Meteo if the network works, no key
        go home                      existing software/dock states
        open question, mail, calendar
                                     only if adult and cloud is mock or live
            optional cloud chat      cloud "live", key from the environment
    speech out                       Piper en_US-lessac-low
    body                             personality engine, not the walk thread
```

The 50 Hz walk thread stays the Runtime loop (SOFTWARE.md section 1). Companion work does not take a turn inside that loop. The Pi default loads one speech model at a time (`resident` false) because all three at once were too heavy on an x86 VM for the 512 MB board. See LATENCY.md. Unpublished times in SOFTWARE.md section 11 stay BLOCKER.

## Assistant layer

Ahmed asked for a toy that talks and also does the assistant jobs: mail, calendar, reminders, and answers.

| Job | Where it runs | What this repo does |
|---|---|---|
| Wake word | Pi, other thread | openWakeWord `hey_jarvis`. Apache-2.0. Not measured on this Pi |
| Speech to text | Pi, other thread, if it fits | Vosk small English, Apache-2.0. Fit next to the walk is BLOCKER (LATENCY.md) |
| Speech out | Pi, other thread | Piper low voice. piper-tts 1.8.0 is GPL-3.0-or-later (that package's metadata). Timing on this Pi is BLOCKER |
| Timers, reminders, clock | Pi, local list | assistant.py stores them and speaks the reply |
| Weather | Pi, Open-Meteo, no key | Works when the network works. Kid mode included. Offline says so |
| Night light | Pi GPIO eyes already in the build | The demo sets eye_on. It does not drive a pin |
| Go home | Pi, existing dock program | The demo names APPROACH, STEER_DOCK, ACTIVATE_CHARGER |
| Open questions | Optional cloud | `cloud` is off, mock, or live. Live reads `ODM_CLOUD_API_KEY` from the environment. No key in this repo |
| Mail and calendar | Optional cloud | Mock records, or the live client if a key is set outside the repo. Kid mode refuses them |

The voice bus to copy is Wyoming, as Home Assistant Assist uses it (cited, https://www.home-assistant.io/integrations/wyoming/): one small protocol in front of a wake word, a speech engine, and Piper. Rhasspy (MIT) and OpenVoiceOS (Apache-2.0) are the other published stacks. This folder does not vendor them.

Kid mode is a flag (`mode="kid"` or `mode="adult"`). In kid mode the cloud tools are not called, and an open question stays on the local line. Timers, reminders, the clock, weather, the night-light flag, and the dock state names still work. How a home turns that flag on: details held for later.

The cloud switch is `cloud="off"`, `cloud="mock"`, or `cloud="live"`. Live calls an OpenAI-compatible `/chat/completions` URL from the config. The key is the environment variable named by `cloud_key_env` (default `ODM_CLOUD_API_KEY`). If that variable is empty, live does not open a socket. The mock's `complete` takes text and a tool list. It has no image argument and no audio argument. If a caller passes a credential argument, it raises and the error text does not include the value. A config file that contains a key is refused.

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
| Wake word on this Pi | none | BLOCKER. An x86 run is in LATENCY.md |
| Speech to text on this Pi | none | BLOCKER. An x86 run is in LATENCY.md |
| Speech out on this Pi | none | BLOCKER. An x86 run is in LATENCY.md |
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

Cloud-tied toys stop being companions when the vendor turns the servers off. This design keeps timers, reminders, the clock, the eye flag, and the existing dock state names working when `cloud="off"`. Weather needs the network and says so when it does not answer. An open question then uses the same local line as kid mode. It does not wait on a provider.

## A companion, not a speaker

The speech line is the assistant. The companion is the body that is already designed: the eye blink in the Runtime, the ear servos in twin/companion/COMPANION.md, and the head command ranges in the playground joystick task (head yaw -1.5 to 1.5 rad, cited, that file). The personality engine turns listening, thinking, speaking, done, and refused into named head poses. Safety and a low pack still come first. See software/personality/PERSONALITY.md.

## First demo

Name: a timer, a question, and go home.

No hardware. Checked by tests/test_assistant.py.

1. A wav stands in for the mic. Wake word is openWakeWord, then Vosk, then this assistant, then Piper.
2. "set a timer for 5 minutes" stores 5 and does not call the cloud. A stored timer fires on `poll`.
3. "remind me to stretch" stores the note locally. "remind me to stretch in 10 minutes" fires on `poll`.
4. "what time is it" answers from the clock. No cloud.
5. "what is the weather in Chicago" calls Open-Meteo when a client is fitted. No key. Kid mode included.
6. "What is a duck?" in kid mode, or with the cloud off, returns the local line and does not call the model.
7. The same question in adult mode with `cloud="mock"` returns the mock line. With `cloud="live"` it calls the configured endpoint only when the environment holds a key.
8. "check my email" in kid mode is refused. In adult mode with the mock, the record subject is "Mock inbox note".
9. "go home" returns the existing dock states APPROACH, STEER_DOCK, ACTIVATE_CHARGER. It does not train a policy and it does not run MuJoCo.
10. "good night" sets eye_on. It does not drive GPIO.

Pass for the text checks: `python3 -m unittest discover -s altaay_lab/software/companion/tests -v`. That is not a pass on the duck. The spoken timer on this VM is LATENCY.md. The drawing is `out/voice_desktop_demo.mp4` (desktop demo, not the robot).

## Held

Still held:

- How kid or adult mode is chosen.
- How a privacy choice is shown on the body.

Closed in software/personality/ (PERSONALITY.md). The engine is not on the 50 Hz walk thread. No cloud:

- How the body shows assistant state.
- How a reminder is carried to a person.
- What the body does while seated.
- When to walk home from the duck's own readings, beyond the guards already in software/SOFTWARE.md.

## Not claimed

- Sim pass only applies to training numbers in TRAINING.md, not to this demo. The text checks are Python with no physics. The drawing in out/voice_desktop_demo.mp4 is a desktop demo, not a sim pass and not the robot.
- No row in SOFTWARE.md section 11 was measured on a Pi. This note does not close any of them.
- Nest vision and a charge program are still unwritten (SOFTWARE.md section 10). Naming the old dock states does not close that gap. The personality clip in twin/out/videos/personality_demo.mp4 is sim pass only. It does not close that gap either.
- The mock is not a model and not an account.
