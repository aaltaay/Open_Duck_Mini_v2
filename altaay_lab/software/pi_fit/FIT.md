# Does the stack fit a Pi Zero 2 W?

Written 2026-11-19. Pi 5 section added 2026-11-24. Nothing here ran on a duck. A number is cited, calc only, measured in emulation, measured on the fit host, or BLOCKER.

Verdict for the Zero 2 W: **does not fit** the stock Raspberry Pi OS Bookworm Lite image on a Pi Zero 2 W. The fixes below keep the walking math inside its 20 ms line after the voice process has started, and they fit a 512 MiB cap in this emulation. They do not fit the 417 MiB that the published 64-bit Lite image actually gives Linux.

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
- Voice runs one model per process, then that process exits. An in-process close does not return the RAM (LATENCY.md). The installed path (isolate true) is this same split. The 512 MiB peaks are those three model processes, not one process that keeps all three.
- The walk service pins CPU 0, sets a high priority, and caps ONNX at one thread. Voice sessions use one thread too.
- glibc arenas are capped with MALLOC_ARENA_MAX=2.
- zram is configured for the Pi (lz4, half of RAM) in software/pi_fit/zramswap.default. This kernel has no zram device, so the compression was not measured: BLOCKER. The swap in the table is a swap file, not zram.

No smaller Piper English file turned up in the published voice list. The low voice is already the small one, about 63 MB on disk. A different speech engine was not substituted.

## Boards

A 2 GB board that can physically replace the Zero is the recommendation. It is not a BOM change. Prices, sizes, and power are in software/pi_fit/BOARDS.md. D61 was not edited.

Ahmed later chose the Pi 5, 2 GB, and a new seat. That study is software/pi_fit/PI5_STUDY.md. The picture software/pi_fit/fit_chart.png is now the 2 GB cap. The Zero numbers above are unchanged.

## Pi 5, 2 GB cap

The cap in this section is 2048 MiB, the cited 2 GB chip (product page, LPDDR4X). A Bookworm Lite MemTotal for the 2 GB Pi 5 was not copied: BLOCKER. The run did not lock an OS ballast.

The prior full-stack peak, voice included, is 467.0 MiB (measured in emulation, the 512 MiB row above). 467.0 is under 2048. That is why the RAM row can fit a 2 GB board. Voice was not re-run here: the model files are not in this tree. A new voice peak is BLOCKER.

This session timed the walk policy, the autonomy loop, and one dock frame on the fit host, inside a 2048 MiB cgroup. It is not a Pi and not qemu-user. CoreMark 1.0, one thread, size 666, scored 28606 iterations/s (measured on the fit host). The official Pi 5 benchmark post gives Geekbench 6 single-core 774 at 16 KB pages and 764 at 4 KB pages (cited, https://www.raspberrypi.com/news/benchmarking-raspberry-pi-5/). A CoreMark iterations/s figure for the Pi 5 was not copied from a text source: BLOCKER. A cpu quota of 11155 us out of 100000 us was set from 3191 / 28606 (calc only, the cited Zero score over the host score). The walk inferences are shorter than that quota, so the quota did not stretch them. The times below are the fit host.

| | Value | Label |
|---|---|---|
| Cycles, after the first 20 | 926 | measured on the fit host |
| Work, median | 0.151 ms | measured on the fit host |
| Work, 99th percentile | 0.305 ms | measured on the fit host |
| Work, max | 0.879 ms | measured on the fit host |
| Work over 20 ms | 0 of 926 | measured on the fit host |
| Work plus the 5.18 ms bus, max | 6.06 ms | the 5.18 ms is calc only. 0.879 + 5.18 = 6.059 |
| Walk process high water | 79.6 MiB | measured on the fit host |
| Cgroup peak | 42.1 MiB | measured on the fit host |
| Camera frame | found, 0.902 s, 77.5 MiB | measured on the fit host |

Do not read this table as a Pi 5 deadline pass. The host is a different chip. The machine-readable summary is software/pi_fit/fit_result.json.
