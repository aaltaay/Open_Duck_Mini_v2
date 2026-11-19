# 2026-11-19 1:55 PM ET: a voice pipeline beside the walk

Labels: unit tests are Python checks with no hardware. The timings in software/companion/LATENCY.md were measured on an x86 VM, not on the Pi. Cited clocks and the scale from a Pi 3 or Pi 3B+ are marked there. Nothing was spent. D61 was not edited.

- The companion now runs wake word (openWakeWord hey_jarvis), speech to text (Vosk small English), the assistant, and speech out (Piper low). It is not on the 50 Hz walk thread.
- Kid mode still refuses mail, calendar, and open questions. Timers, reminders, the clock, and weather still work. Weather uses Open-Meteo and no key. A live cloud model is off unless a key is set in the environment.
- The Pi config loads one model at a time. On this VM that path used 317.3 MB after the runs, under the cited 512 MB board, with the OS and the walk not included. All three models resident used 422.7 MB on the same VM.
- A spoken "hey jarvis, set a timer for five minutes" was heard and answered on this VM. Median of 5 sequential runs: 1.515 s for a 2.688 s clip. The drawing is software/companion/out/voice_desktop_demo.mp4 (desktop demo, 720p, 87239 bytes). Not the robot.
