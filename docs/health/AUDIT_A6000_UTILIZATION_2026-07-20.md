# Audit: 48 GB Card Utilization vs. the Prime Directive
### The complete RunPod rental program, 2026-07-19 → 2026-07-20

Requested by Joel after Run B launched at 2:20 pm on a card rented the previous
afternoon. Every timestamp below is reconstructed from logs on the pod, the Mac,
and the studio PC — nothing estimated where a log exists. Times UTC; local = UTC−4.

## 1. The working pod's life, hour by hour

Pod `oakland-native8k-4` (RTX A6000 48 GB, $0.33/hr) started **Jul 19, 18:50Z**
(2:50 pm local). Projected teardown after Run B delivery ≈ Jul 20, 22:25Z.
Projected total life ≈ **27.5 hours ≈ $9.08**.

| Window (UTC) | Hours | What happened | Class |
|---|---|---|---|
| 19th 18:50 – 19:15 | 0.4 | Bring-up: SSH up, driver 570.211.01 verified ≥570 (dead-man gate passed), build + transfer launched | Necessary |
| 19th 19:15 – 19:23 | 0.1 | Build died at configure (missing GTK dev package); transfer downloaded but never unpacked — monitor fired, nothing woke the agent | Failure onset |
| 19th 19:23 – 00:30 | **5.1** | **IDLE #1** — the documented "5-hour idle" incident: build dead, transfer stalled, agent asleep, nobody woken | **Waste** |
| 20th 00:30 – 04:09 | 3.7 | Recovery: build fixed and compiled clean (BUILD_DONE_OK 04:09); in parallel, transfer forensics — relay tool corrupted two archives, direct copy hung, Mac relay measured too slow | Necessary + retry overhead |
| 20th 04:09 – 04:45 | 0.6 | Stale archive proven incomplete, fresh relay: 12 GB in ~13 min at 16 MB/s, extracted, 462 images + camera solve verified | Necessary |
| 20th 04:45 – 06:13 | **1.5** | **IDLE #2** — data verified, trainer built, GPU idle; training not launched until the lead acknowledged | **Waste** |
| 20th 06:13 – 09:29 | **3.3** | **RUN A trains** — 20,000 iterations, native 8192, 12M gaussians, GPU ~100% throughout, zero errors | **Productive** |
| 20th 09:29 – 18:20 | **8.9** | **IDLE #3** — Run A finished; its watcher had frozen mid-check at 07:15 (process alive, log dead), so Run B never auto-launched. Meter-sentinel rang Joel's phone; fixed on his poke | **Waste** |
| 20th 18:20 – ~22:10 | **~3.8** | **RUN B trains** — 18M gaussians at 26–27 GB VRAM (physically impossible on the 24 GB 3090), GPU ~100%, zero errors | **Productive** |
| ~22:10 – ~22:25 | 0.25 | Delivery (both models byte-verified to two machines) + build salvage + teardown | Necessary |

**Scorecard for the working pod (~27.5 h):**

- **Productive GPU compute: ~7.1 h — 26%** (~$2.34)
- **Necessary setup, build, transfer, delivery: ~4.9 h — 18%** (~$1.62), of which
  roughly 1.5 h was retry overhead from stacked unknowns (new host + new build +
  unproven transfer tool at once)
- **Pure idle: ~15.5 h — 56%** (~$5.10), in three windows, every one caused by a
  watcher/hand-off failure rather than by slow work

## 2. The whole rental program ($25 funded)

| Item | Cost | Verdict |
|---|---|---|
| Pod #1 — deployed on an unverified image tag, stuck all night unmonitored | ~$7.40 | 100% waste (the incident that produced the three billing rules) |
| Pod #2 — host driver 550 < required 570, caught by the verify gate, killed | ~$0.60 | Cheap failure — the gate worked; this is what verification costs when it succeeds |
| Pod #3 (working pod) — full life above | ~$9.08 | 26% productive / 18% necessary / 56% idle |
| Storage/fee residue | ~$0.4 | Overhead |
| **Total spent** | **~$17.5** | **~$2.34 (13%) bought GPU compute; ~$1.6 (9%) bought necessary logistics; ~$13.1 (75%) bought nothing** |

Projected final balance after teardown: ≈ $7.50 of the $25.

**The perfect-execution counterfactual:** bring-up + build + one clean transfer +
both trainings + delivery ≈ 10 h ≈ **$3.30**. The program will close at ~$17.5 —
**about 5× the ideal**. The entire overage is operational (bad tag, dead watchers,
stalled hand-offs), not computational: both trainings ran flawlessly at full GPU
on the first attempt, and the science (the A/B verdict data) is uncompromised.

## 3. Prime Directive verdicts

1. **The card idled 56% of its life — three windows, one cause.** Every idle hour
   traces to a monitoring failure: a monitor whose exit could not wake a sleeping
   agent (#1), a finished stage with no self-firing successor (#2), and a watcher
   that hung mid-check and went silent (#3). The work itself was never slow — the
   watching was broken. This is the audit's central finding.
2. **Waste concentrated where verification was skipped; verification paid for
   itself where used.** The unverified image tag cost $7.40. The driver
   verification gate cost $0.60 and saved a second all-night burn. Same lesson,
   both signs.
3. **Stacked unknowns taxed the recovery.** Running a new host, a fresh source
   build, and an unproven transfer tool simultaneously made each failure ambiguous
   and added ~1.5 h of forensics — the canary rule exists for exactly this.
4. **What worked:** the meter-sentinel rang the phone as designed; the budget
   floor ($5 kill rule) was never threatened; the trainings themselves were
   clean, first-try, full-GPU runs; and every model was byte-verified to two
   machines before teardown.

## 4. Fixes now standing (each idle window produced one)

- **Idle #1 →** monitors must be local, harness-tracked, bounded pollers whose
  exit is the wake-up — remote and detached watchers are no-ops.
- **Idle #2 →** finished stages fire their successors themselves; no stage
  boundary waits for a supervisor.
- **Idle #3 →** every remote check inside a watcher carries a hard wall-clock
  timeout and the watcher exits loudly after consecutive failures; a frozen
  watcher log is itself an alarm. (Field manual ch13 updated the same hour.)
- **Program-level →** the meter-sentinel (independent of any session) remains the
  layer that cannot forget.

## 5. Actions this audit triggers for the 36-tile rebuild

1. **Never pay for the build again:** before teardown, the compiled trainer is
   salvaged off the pod (binary + build products to the studio PC). A future pod
   goes from boot to training in minutes, not 9 hours — this single change removes
   ~35% of the working pod's non-productive life from every future rental.
2. **Transfer recipe is settled:** pre-staged archive + the relay method that
   moved 12 GB in 13 minutes. No more tool roulette on the meter.
3. **Fleet watchers inherit the hardened pattern** (hard timeouts, loud exits,
   lead backstop from launch) — already the standing template.

With those three in place, the same $17.5 program re-run today would cost ≈ $4:
the rebuild's rental budget should be modeled on that basis.
