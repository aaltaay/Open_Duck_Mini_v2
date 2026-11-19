# Does the stack fit a Pi Zero 2 W?

Written 2026-11-19. Nothing here ran on a duck. A number is cited, calc only, measured in emulation, or BLOCKER.

Verdict: **does not fit** the stock Raspberry Pi OS Bookworm Lite image on a Pi Zero 2 W. The fixes below keep the walking math inside its 20 ms line after the voice process has started, and they fit a 512 MiB cap in this emulation. They do not fit the 417 MiB that the published 64-bit Lite image actually gives Linux.

The picture is software/pi_fit/fit_chart.png. The machine-readable summary is software/pi_fit/fit_result.json.

## What was emulated

qemu-user aarch64 on Debian Bookworm, four host cores. This is not qemu-system raspi3b and not a Pi. Each timed core was held to a quota of 45700 us out of 100000 us. Under that quota a CoreMark 1.0 run scored 3195.4 iterations/s (measured in emulation). The cited Pi Zero 2 W result is 3191 at 1.00 GHz on Debian 11.8 32-bit (https://www.altocumulus.org/~hallgren/Computers/coremark). 3195.4 / 3191 = 1.001 (calc only). The same binary with no quota scored 7341.7 iterations/s (measured in emulation), which is faster than the Pi, so the quota is required.

The chip is a 1 GHz quad Cortex-A53 with 512 MB SDRAM, 65 mm by 30 mm (cited, https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/).

Bookworm Lite 64-bit on a Zero 2 W reported 417.0 MiB total, 125.4 MiB used, and 291.6 MiB available (cited, https://docs.printercow.com/guide/32bit-vs-64bit.html, snapshot updated 4 May 2025). The run locked 125.4 MiB to stand in for that used figure. The lock is the cited size, not a boot of Raspberry Pi OS. An idle aarch64 Python under qemu-user was 29.1 MiB (measured in emulation). How much of that is the translator, rather than Python, was not separated: BLOCKER.

The walk is the stock BEST_WALK_ONNX_2 policy, input 101, output 14, one thread, ONNX Runtime 1.18.1, the same call shape as the Runtime's OnnxInfer with awd on. The Runtime file was not edited. The USB servo time is not in the measured work. SOFTWARE.md section 6 counts 5.18 ms of bus if each USB read is 1 ms (calc only). The real USB round trip is still BLOCKER.

Voice is sequential: wake, then Vosk small English, then Piper lessac low, each in its own process so the RAM comes back when that process exits. The clip is a 3 s tone, not a person, and the wake word did not fire. The three models still ran. The dock frame is the 400 by 695 detector in twin/dock/camera/camera_dock.py. It found the drawn mark. Personality and the autonomy supervisor stepped on a thread of the walk process.

## RAM

| Run | What | Peak | Swap | Label |
|---|---|---|---|---|
| Before the fixes, cap 417 MiB | One process, walk and voice and camera on one throttled core | 417.0 MiB, the cap | 125.8 MiB | measured in emulation. Stopped while Vosk was loading, so there is no deadline trace for this row |
| After the fixes, cap 417 MiB | Walk pinned to one core, voice stages and the camera on the other cores | 417.0 MiB, the cap | 108.4 MiB | measured in emulation, from the sampler |
| After the fixes, cap 512 MiB | Same spread | 467.0 MiB | 0.33 MiB | measured in emulation, from the sampler |

417.0 + 108.4 = 525.4 MiB touched on the tight cap (calc only). That is over the 512 MB chip as well as over the 417 MiB Linux can see. The 512 MiB cap did not force that spill: the sampler peak there is 467.0 MiB. Process peaks are not a sum. On that run the walk process peaked at 124.2 MiB, wake at 242.3 MiB, speech to text at 220.3 MiB, speech out at 225.3 MiB, and the camera at 80.7 MiB (each measured in emulation).

## Walk deadline

The Runtime treats a cycle as late when the work, not the sleep, passes 20 ms. On the 512 MiB run, 8880 cycles ran while the voice stages and the camera frame were in progress.

| | Value | Label |
|---|---|---|
| Work, median | 1.47 ms | measured in emulation |
| Work, 99th percentile | 2.35 ms | measured in emulation |
| Work samples over 20 ms | 1 of 8880, at 20.6 ms, in the first 20 cycles | measured in emulation |
| Work plus the 5.18 ms bus, over 20 ms, after those first 20 cycles | 0 of 8860 | the 5.18 ms is calc only. The tail max work is 6.2 ms, and 6.2 + 5.18 = 11.4 ms (calc only) |
| Period, 99th percentile | 20.34 ms | measured in emulation |
| Periods over 21 ms after the first 20 cycles | 15 of 8860, longest 23.2 ms | measured in emulation |

The first cycles are late because the voice process is being created. After that, the walking math stays inside the 20 ms line even with the calc-only bus added. A real USB round trip longer than the 1 ms assumption could still break that. That time is BLOCKER.

## Fixes that were tried

These are in the install and the voice path. They are why the 512 MiB row is lower than the first row.

- The wake loader does not import the openWakeWord trainer, so scikit-learn stays out.
- Voice runs one model per process, then that process exits. An in-process close does not return the RAM (LATENCY.md).
- The walk service pins CPU 0, sets a high priority, and caps ONNX at one thread. Voice sessions use one thread too.
- glibc arenas are capped with MALLOC_ARENA_MAX=2.
- zram is configured for the Pi (lz4, half of RAM) in software/pi_fit/zramswap.default. This kernel has no zram device, so the compression was not measured: BLOCKER. The swap in the table is a swap file, not zram.

No smaller Piper English file turned up in the published voice list. The low voice is already the small one, about 63 MB on disk. A different speech engine was not substituted.

## Boards

A 2 GB board that can physically replace the Zero is the recommendation. It is not a BOM change. Prices, sizes, and power are in software/pi_fit/BOARDS.md. D61 was not edited.
