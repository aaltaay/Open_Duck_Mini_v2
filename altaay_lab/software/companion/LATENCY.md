# Voice latency

Written 2026-11-19. The runs are on an x86 cloud VM, not on the Pi. Nothing here was measured on a duck. A number is cited, calc only, measured on this VM, or BLOCKER.

The board is the Pi Zero 2 W: 1 GHz quad-core 64-bit Arm Cortex-A53, 512 MB SDRAM (cited, https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/). The mics are the two SPH0645LM4H boards and the speaker is the CMS0361KLX on the MAX98357A (BOM lines 3, E1, E2, E8). Capture is 48 kHz stereo S32_LE (cited, twin/companion/COMPANION.md section 2).

## What was timed

`latency_x86.json` is the script output. The machine line in that file was read from the VM: x86_64, 4 cores, 2400 MHz, Intel Xeon Processor. That is not a datasheet for the chip, and it is not the Pi.

The clip is Piper speech, `en_US-lessac-low`, saying "Hey Jarvis. Set a timer for five minutes." The file is 2.688 s at 16 kHz. Making that file took 0.054 s. It is synthetic speech in a real wav. Kid mode, cloud off. Both modes heard "hey jarvis set a timer for five minutes" and said "Timer set for 5 minutes."

| Mode | What it does | Median of 5, seconds | RSS after the runs |
|---|---|---|---|
| Sequential | Pi default. Wake, then speech to text, then speech out, one at a time. ONNX arenas off | 1.515 | 317.3 MB |
| Resident | All three models stay loaded | 0.774 | 422.7 MB |

The five sequential totals were 2.106, 1.394, 1.421, 1.544, 1.515 s. The first one paid a colder load. The five resident totals were 0.794, 0.755, 0.774, 0.778, 0.765 s. Loading the three resident models once took 0.610 s, and that load is not inside the 0.774 s.

One sequential repeat near the median (the 1.515 s one) split as: load wake 0.202, scan 0.238, load speech to text 0.200, decode 0.617, brain 0.000, load speech out 0.206, speak 0.049, prepare 0.003. One resident repeat (0.765 s) split as: scan 0.204, decode 0.527, brain 0.000, speak 0.031, prepare 0.004. Those splits are that repeat, not a median of each stage.

The process peak across the whole script, which ran the sequential set and then the resident set, was 492.9 MB. That peak is not the sequential mode by itself.

A separate probe on this same VM, not in the five-run table: with the default ONNX arena, wake plus Vosk plus Piper reached 522 MB RSS. With the arena off, the same three reached 418 MB, and Vosk plus Piper without the wake model reached 287 MB. Deleting the wake model did not hand the RAM back (217 MB loaded, 218 MB after the delete).

## Other checks on this VM

| Check | Number | Label |
|---|---|---|
| Open-Meteo weather for Chicago, no key | 0.518 s, "Chicago, United States is 65 F and mainly clear." | measured on this VM |
| Vosk on the public vosk-api example wav (132928 samples, 8.308 s) | 0.737 s, RTF 0.0887 | 0.737 and the sample count measured here. 8.308 is 132928 / 16000 and the RTF is 0.737 / 8.308, both calc only |

The example wav is digits, not a timer. The transcript was "one zero zero zero one nine oh two i no zero one eight zero three".

## Cited speed, then a clock scale

These are not runs on our duck.

- openWakeWord: one core of a Raspberry Pi 3 can run 15 to 20 models at once in real time (cited, https://github.com/dscripka/openWakeWord). The Pi 3 is a 1.2 GHz quad Cortex-A53 (cited, https://www.raspberrypi.com/products/raspberry-pi-3-model-b/). This board is 1.0 GHz. If that 15-model line scales with the clock, one core here would hold 15 x 1.0 / 1.2 = 12.5 models (calc only). We load one model. A timing next to the 50 Hz walk is BLOCKER.
- Vosk small English on a Pi 3B+: "it runs in realtime, so it takes about 60 seconds to decode 60 second file" (cited, https://github.com/alphacep/vosk-api/issues/331, nshmyrev). That is an RTF of about 1, and the "about" is in the source. The 3B+ is a 1.4 GHz Cortex-A53 (cited, https://www.raspberrypi.com/products/raspberry-pi-3-model-b-plus/). Same core family as this board. If the time scales with the clock, the RTF here is about 1 x 1.4 / 1.0 = 1.4 (calc only). The 2.688 s clip would then take about 3.8 s to decode (calc only, 2.688 x 1.4). The x86 decode above is not that number.
- Piper ONNX, low quality, on a Pi 4: RTF 0.494 (cited, https://github.com/rhasspy/piper/issues/33). That note does not state the Pi 4 clock, so this page does not scale it. Speech-out time on our board is BLOCKER. The x86 line above spoke the short reply in 0.031 s in one resident repeat.
- The small Vosk model is listed at 40M and is marked for Android and Raspberry Pi (cited, https://alphacephei.com/vosk/models). The unpacked folder on this VM was 68 MB (measured here). The Piper low voice file was 61 MB (measured here). The openWakeWord package models were 11 MB (measured here).

## RAM against 512 MB

317.3 MB after the sequential runs is under 512 MB (both numbers measured or cited as above). The difference is 194.7 MB (calc only, 512 - 317.3). The OS and the walk are not in the 317.3 MB. The emulation that puts the OS, the walk, the voice, and a dock frame in one 512 MB budget is software/pi_fit/FIT.md. A measurement on a Pi is still BLOCKER.

422.7 MB with all three models resident leaves 89.3 MB (calc only). That is not enough room to assume an OS, so the Pi config keeps `resident` false.

## Not claimed

- No row was measured on a Pi. SOFTWARE.md section 11 stays BLOCKER for the mic-to-sample delay and for Wi-Fi.
- The desktop clip `out/voice_desktop_demo.mp4` is a drawing of the personality targets. It is not the twin physics and not the robot. It is 6.30 s, 1280 by 720, 87239 bytes.
