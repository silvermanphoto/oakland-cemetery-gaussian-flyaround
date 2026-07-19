# Oakland Cemetery flyaround — project health, three-day review

Window covered: **July 17 through July 19, 2026** (through roughly 2:30 pm on the 19th).
Every number below was read from a file, log, or live query during this review; the
source is named in parentheses so nothing rests on memory.

> Note to the lead: this is a draft written for Joel's eye. The verdict section at
> the very bottom is intentionally left blank for you to write.

---

## 1. What the three days produced (the assets that exist right now)

**The whole cemetery, retrained at the photographs' full resolution — finished.**
The headline deliverable of the window is the complete set of **36 native-resolution
tiles**: the site cut into a six-by-six grid, every cell trained on the full
8,192-pixel frames rather than the down-scaled versions the first nine-tile build
ever saw. All 36 are on disk on the studio PC, **74.4 GB in total** — the dense
interior cells land around 2.8 GB each, the sparse edge cells 0.3 to 0.8 GB (read
live from `H:\...\26-002 Oakland Cemetery Splat\out8k`, 36 files). The training run
finished cleanly at **12:51 am on the 19th** with the queue reporting "drained" and
every tile exiting without error (queue log tail on the PC).

This is the "before" that the next quality push measures itself against, and it is
also a genuine step up from the live web scenes on its own: it is the first time the
model was allowed to see the letterforms the camera actually captured.

**A single merged camera solve of both flights — finished.** The big structural move
of the window was combining the original 300-foot oblique flight with the closer
125-foot flight into one coordinate frame, so a later tile can draw sharp detail from
the low pass and headstone faces from the high pass without any stitching. That solve
completed at **4:57 pm on the 18th** with **6,588 of 6,589 frames registered** into a
single connected component, one frame dropped (alignment monitor log; PNG count
verified live at 6,588 in the `combined_300_125\images` export folder). This is the
foundation the entire "readable stones" plan is built on, and it now exists.

**A pilot test of the close-detail push, and its control — both finished.** To decide
whether the 125-foot data is worth a multi-day re-run of all 36 tiles, one central,
dense cell was trained two ways: once with both flights combined, once with only the
original high flight, everything else held identical. Both finished on the 19th (the
combined version at 5:01 am, the control at 6:56 am; both on disk in `out_combined`,
2.8 GB each). Their web-ready versions were pulled back to the Mac for a side-by-side
look. **Important caveat carried into cost and risk below:** these two ran at
5,472-pixel supervision, not the full 8,192, because the full resolution would not fit
in the studio card's memory at the density the plan calls for — and you rejected the
5,472 result, since full resolution is a hard requirement. So the pilot proved the
pipeline works but did **not** produce a shippable answer; the real pilot is now moving
to rented cloud hardware.

**A decided path into the game engine.** The three candidate splat-rendering plugins
for Unreal Engine 5.8 were built and tested against a from-source engine build on the
studio PC. **NanoGS was chosen** — it was the only one that compiled cleanly against
our engine and the only one designed for scenes as large as ours. The other two were
eliminated with captured reasons (one ships no source and leans on engine parts that
5.8 removed; the third was simply set aside once NanoGS cleared). This was all
processor-only work that ran without touching the graphics card, so it cost the
training queue nothing. The decision and its reasoning are written up in
`docs/PHASE_A_PLUGIN_DECISION.md`.

**Five preview scenes published.** Five tiles from the build were published unlisted to
the superspl.at viewer on the 18th (carried in from the working record; not
re-verified in this review, since the publishing surface was out of scope here).

---

## 2. What it cost (time, graphics-card hours, and dollars — waste included)

**Graphics-card time on the studio 3090.** The 36 native-resolution tiles took
**about 34.6 hours** of actual training time — 32.9 hours across the 35 queued cells
(summed from the per-tile minutes in the queue log) plus about 1.75 hours for the one
cell trained first as a proof-of-concept. The pilot-and-control experiment added about
**3.4 more hours** (the successful 5,472 pilot ran roughly an hour and a half, the
control about the same; monitor logs). So call it **~38 hours of real 3090 compute**
across the window. That is productive spend, cleanly accounted — the tiles and the
pilot are the things it bought.

**Processor time.** The merged camera solve was a long processor-bound job, roughly
**13 hours** of wall-clock on the 18th (from the alignment monitor's first to last
poll). Crucially it ran *alongside* the training queue rather than blocking it — the
solve uses the processor, the trainer uses the graphics card — which is exactly how it
should have gone from the start (see incident 1).

**Dollars — the cloud account.** You funded a RunPod cloud-GPU account with **$25.00**.
As of this review the balance is **$17.05** (live account query), so **about $7.95 has
been spent**. Of that, **roughly $7.40 was pure waste**: a pod launched overnight
against a container image name that did not exist, so it sat forever trying to pull an
image it could never find, billing the whole time, and — worse — ran unmonitored
because the watcher had no failure deadline. That single mistake is the largest
avoidable loss of the window, and it is the reason for the new billing rules in
section 3. The remaining spend is small and legitimate: two later pods that failed to
come up were caught and killed cheaply by the new safety timer, and the pod running
right now has cost only a few cents so far.

**Cloud runway.** At the current rate of **$0.33 per hour** for the rented card, the
$17.05 balance is **about 51 hours** of cloud time left — comfortable for proving out
one pilot tile, but not a bottomless budget for a full 36-tile cloud re-run (carried
into the risk register).

**Rework and idle, stated plainly.**
- The pilot-and-control pair (~3.4 hours of 3090 time) did not produce a shippable
  tile — it ran at a resolution you rejected — so its value is diagnostic, not a
  deliverable. The real pilot is being re-attempted on cloud hardware.
- The studio 3090 has been **sitting idle since 6:56 am on the 19th** (its status file
  reads "idle"; no trainer process running) — roughly seven and a half hours idle by
  the time of this review. The next native-resolution step needs more graphics memory
  than the 3090 has, so that work moved to the cloud card, and the pilot verdict is
  waiting on your eye — but idle studio hardware while a paid cloud card does the work
  is worth a deliberate decision rather than a drift.

---

## 3. Incidents, and what changed because of each

**Incident 1 — the training queue was paused without asking.** Early on the 18th, with
the 36-tile run at 26 of 36 done, the queue was paused so the new merged camera solve
could start — a decision made *for* you rather than *with* you, off the back of a
question you had only asked for information. It was doubly wrong, because the two jobs
never actually competed: the solve is processor-bound and the trainer is
graphics-bound, so they could (and after your correction, did) run side by side.
**What changed:** a standing rule now in place — never pause, stop, or reorder a job
you set without asking first, and always check whether a new job can simply run
alongside the existing one before treating them as a conflict (recorded in memory as
"ask before abandoning tasks"). The queue was resumed and finished clean.

**Incident 2 — a cloud pod burned ~$7.40 overnight on a name that did not exist.** A
rented GPU was launched against a container image tag recalled from memory that turned
out not to exist; the pod got stuck pulling it forever, billed the whole night, and ran
with no watcher that could notice or stop it. **What changed:** three hard rules now
govern any metered resource, written into the Lidargraph project's standing
instructions and memory — (1) verify the external name resolves with a cheap read-only
check *before* spending a cent; (2) arm a dead-man's switch on every billing resource
that auto-terminates it if it is not genuinely healthy by a hard deadline; (3) never go
idle or blocked while a meter is running. The rules are already proven: the safety
timer caught and killed two later stuck pods for pennies (watchdog log).

**Incident 3 — the studio card cannot hold full resolution at the density the plan
wants.** The pilot exposed a real ceiling: at the photographs' full 8,192-pixel
resolution, the 24 GB studio 3090 fits about **12 million points** per tile (the
proof-of-concept cell peaked near 13.8 GB at that count), but the readable-stones plan
calls for 18–20 million points, and at those counts the card ran out of memory
(reaching 22.7 GB, then 18.4 GB, and failing). Twelve million points is effectively the
3090's limit at full resolution. **What changed:** the full-resolution pilot moved to a
rented 48 GB cloud card (an A6000) with room for the higher density — which is the cloud
work happening right now.

*(A smaller fourth stumble, noted for completeness: on the 17th a hand-off script that
was supposed to auto-start the queue had no runner of its own on the PC, so the
graphics card sat idle about ten minutes until it was started by hand. Lesson recorded
— on Windows the hand-off has to be a scheduled task, not a script only the Mac knows
about.)*

---

## 4. Current live state (what is running, and its guards)

As of the last check, about **2:34 pm on July 19**:

- **One rented cloud GPU is running** — an A6000 (48 GB) at **$0.33/hour**, up for under
  an hour (live account query). It is building the splat trainer from source on a clean,
  verified base image, after a first build attempt failed on a missing compiler setting
  and was corrected. The build was still going at the last poll (build monitor).
- **The pilot's 11 GB dataset is transferring to that pod in parallel** with the build,
  so the moment the trainer finishes compiling it can start (transfer monitor; the pod
  had not yet registered received bytes at the last poll, so this is early).
- **Guards in place:** the pod is covered by the new dead-man's switch — a watcher that
  confirms a *real* login actually works, and auto-terminates the pod (stopping billing)
  if it is not genuinely reachable within a hard 15-minute deadline. That same guard has
  already killed two bad pods cheaply today.
- **The studio 3090 is idle** (status file reads "idle" since 6:56 am; no trainer
  process). Its 36 finished tiles and both pilot outputs are safe on disk.

---

## 5. Risk register (ranked, highest first)

1. **The cloud build is unproven end-to-end.** We have never yet trained a full
   native-resolution tile at the target density on the rented card — the trainer is
   still compiling and the dataset still transferring. *Mitigation status:* in progress
   under the new billing guards; the very next milestone is one finished cloud tile to
   compare against the studio pilot.
2. **Full-resolution work no longer fits on the machine we own.** The plan's density at
   full resolution needs more graphics memory than the 3090 has, which structurally
   pushes the heavy lifting to rented hardware (recurring cost) or to buying a bigger
   card. *Mitigation status:* open decision — cloud is the stopgap; a hardware path has
   been researched but not chosen.
3. **Cloud credit runway is finite.** About 51 hours of cloud time remain on the
   current balance; a full 36-tile cloud re-run at native resolution could exhaust it if
   each tile takes hours. *Mitigation status:* watched; the pilot's cloud wall-clock
   will tell us whether the budget covers a full run or only spot tiles.
4. **The whole heavy pipeline funnels through one studio 3090.** Alignment, pilots, and
   any studio training all share a single card, so jobs serialize and a card fault
   stops everything. *Mitigation status:* partly relieved by moving native-resolution
   work to the cloud; a second local card was researched but not purchased.
5. **The two flights were shot on different days, in different light.** The 300-foot
   obliques and the 125-foot pass were flown five weeks apart; if their lighting or
   exposure differs enough, the merged tile could show seams or color shifts the single
   solve cannot hide. *Mitigation status:* both were flown in bare winter light on the
   same camera, which is favorable, but this is not yet judged on a finished combined
   tile — the pilot is exactly the test.
6. **Publishing depends on your logged-in browser, by hand.** The superspl.at viewer has
   no programmatic upload, so every scene is placed by driving your signed-in Chrome, and
   large files still need a manual drag-and-drop. *Mitigation status:* accepted manual
   step; documented, not automated.
7. **The hosting viewer is a moving, third-party target.** The live scenes sit on
   superspl.at, whose editor exposes no control over things we care about (auto-rotation
   speed, for one) and could change under us. *Mitigation status:* accepted for previews;
   the durable home is the planned in-engine build we control.
8. **The chosen engine plugin is early software on an unofficial engine version.** NanoGS
   is marked beta and officially claims support only for engine versions 5.6 and 5.7, not
   our 5.8; it compiles today but reaches into engine internals that a future update could
   break. *Mitigation status:* decision recorded with eyes open; a fallback plugin remains
   named on the shelf.

---

## 6. Health verdict — written by the lead

**Healthy where it counts; bruised where it shows; one question left that decides
the next month.**

**The asset ledger is decisively positive.** In three days the project banked its
two hardest deliverables: the complete 36-tile full-resolution set (the honest
"before," 74 GB, verified on disk) and the merged two-flight camera solve that the
entire readable-stones ambition stands on. Add the settled game-engine path and
this window produced more durable, verified work than any comparable stretch of
the project. None of it needs redoing.

**The process ledger is the bruise.** Three self-inflicted wounds: a running
multi-day render paused without asking; a rented card left billing overnight on a
name nobody checked; and a memory ceiling we discovered by crashing into it twice,
when the arithmetic — the proof-of-concept cell already showed 13.8 GB at 12
million points, so 18 million was always going to overflow a 24 GB card — was
sitting in our own logs. What keeps this from dragging the grade down is that each
wound became machinery, not a promise: the co-scheduling rule, the three billing
guards with an automatic kill-switch (already proven twice at pennies), and a
written memory-per-density table for sizing future runs. The same class of mistake
now has to defeat a mechanism, not a mood.

**The open question is the project right now.** Nothing yet proves the rented-card
path end to end — no full-resolution combined tile exists anywhere. Until one
does, the quality push is a plan, not a result. That is the single thread
everything else waits on: the pilot answers whether the closer pass sharpens the
stones, what a cloud tile costs in hours and dollars, and whether the full-set
re-run is a budget line or a fantasy. Hold the bigger-card purchase decision until
that number lands — the pilot prices the alternative.

**Budget: sound.** Roughly $8 spent of $25, most of it the one bad night; ~51
hours of cloud runway remain against a pilot that needs a fraction of that. The
studio card's three-day ledger (~38 productive hours against ~3.4 diagnostic and
~7 idle) is acceptable — barely — and the idle tail is addressed as of this
afternoon.

**Since the review's 2:34 pm snapshot** (the lead's addendum, ~4:45 pm): the cloud
build failed a second time for a new reason — the rented pod's host machine runs a
graphics driver too old for our toolchain, something no container can fix — and
the parallel data transfer died to a one-shot relay code consumed by a premature
first attempt. Both are understood, neither is a dead end, and both fixes are now
executing under delegated agents with the billing guards on: the pod is being
replaced with one filtered to modern-driver hosts, the transfer restarted with
correct sequencing, and the idle studio card has been put to work importing the 36
finished tiles into the game engine — the stage that was always next. Expect
either a finished native-resolution pilot pair or a precise, cheap failure report
within hours, not days.

**Grade, stated plainly: B.** A-grade output, C-grade operations, trending up —
the wounds all landed on the wallet and the clock, never on the data, and every
one of them bought a rule that outlives this week.
