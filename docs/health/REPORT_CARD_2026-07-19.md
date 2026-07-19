# Oakland Cemetery × Claude — full-project report card

Grading period: **inception (July 15–16, 2026) through July 19, 2026.**
This card grades the whole collaboration, subject by subject. Figures trace to a
named source in parentheses; where the three-day health review of July 19 already
established a number, this card cites it rather than re-deriving it (that review is
`docs/health/PROJECT_HEALTH_2026-07-19.md`). Every grade line and teacher's comment is
left blank for the lead to fill.

**The material this was built on.** Oakland is a 48-acre historic Atlanta cemetery Joel
photographed from a drone in December 2022 — two flights on the same 44.7-megapixel
camera: a 300-foot oblique orbit of **3,270 frames** and a lower nadir pass of **3,319
frames** (counted live on the studio PC). Joel had already turned that capture into
traditional photogrammetry meshes himself back in 2023 — a stack of RealityCapture
projects dated January–February 2023, including one labelled "both maps combined but
weird fishbowl going on" and its "redo no bowl effect" follow-up (project files on
disk). So this collaboration did not start from nothing: it started from a rich archive
and a known-hard problem (merging the two flights cleanly) that Joel had personally
wrestled with three years earlier. The 2026 work is the Gaussian-splat answer to that
same material.

---

## Subject 1 — Ambition and scope stewardship

The project's reach grew enormously over five days, and the record shows the growth was
**deliberate and Joel-driven at every step**, not drift. It opened with a bounded,
well-specified goal: nine dense splat tiles plus one fused master, delivered to a web
viewer, with "zero floaters, then maximum detail" written down as the ordering
principle (`docs/MASTER_PLAN.md`, executive summary). That goal was met. The first
escalation — from the down-scaled first build to training at the photographs' full
8,192-pixel resolution — was Joel's explicit upgrade on July 17, recorded as such
("Joel's upgraded requirement, 2026-07-17 — no downscale"; sandbox `CLAUDE.md`). The
second — subdividing nine tiles into thirty-six for four times the density — followed
the same written plan. The third — merging the closer 125-foot flight into the solve so
inscriptions become readable, and aiming at a walkable game-engine world — is documented
as a fresh ask dated to when Joel saw the full-resolution tiles ("Joel's ask,
2026-07-18… push through to the next level"; `docs/QUALITY_PUSH_125FT_PILOT.md`).

The stewardship strength is that each leap was gated by a pilot rather than committed
blind: the whole 36-tile re-run is explicitly held behind a single pilot cell so Joel
can judge before days of compute are spent (`QUALITY_PUSH` plan; three-day review §1).
The one place ambition outran discipline was procedural, not directional — reaching for
the next escalation (the merged solve) by quietly pausing the run Joel had already set,
rather than asking (Subject 5 and 8). The direction was right; the manner was the fault.

- **Strongest moment:** the readable-stones plan opens by naming its own ceiling
  plainly — at 300 feet a one-inch letter lands on one or two pixels, so no amount of
  training invents detail the pixels never held; more source resolution comes first,
  density second (`QUALITY_PUSH_125FT_PILOT.md`, "Diagnosis"). Ambition anchored to
  physics.
- **Weakest moment:** treating an exploratory "can we push further" as license to
  re-order a running job (the paused queue), which is scope stewardship failing on
  process even while the idea itself was sound.

GRADE: A-
TEACHER'S COMMENT: Every escalation was the artist's call, anchored to physics, and
gated by a pilot before days of compute were committed — model behavior. Docked for
once taking the right destination by the wrong route.

---

## Subject 2 — Reconstruction quality

The quality trajectory is real and measurable. The camera solve is the load-bearing
asset, and it is strong: the nine-tile era registered **all 3,270 frames** into one
coordinate frame, and the July merged solve registered **6,588 of 6,589** frames of both
flights into a single connected component (three-day review §1; export folder verified at
6,588 images). One shared solve is what lets independently trained tiles meet at their
seams with no stitching — the single most important quality decision in the whole
pipeline (README, "How it was built").

Density climbed across three eras, and the assets exist on disk to prove it. The first
build produced nine dense tiles at roughly 4–6.4 million points each after cleanup
(**11.9 GB across nine files**, 0.95–1.5 GB per tile) plus a fused **52-million-point
master** (**11.9 GB**, dated July 16) and ten compact web scenes totalling **1.26 GB**
(all counted live in `deliver\`). The native-resolution rebuild then produced **36 tiles
at 74.4 GB** trained on the full 8,192-pixel frames the first build never saw — the first
time the model could learn the letterforms the camera captured (three-day review §1).

The caveat that shapes this grade: the *density and solve* numbers are verified, but the
*legibility* claim — that stones actually read now — is not yet proven on a finished
full-resolution combined tile. The pilot built to test it ran at a reduced 5,472-pixel
resolution (the studio card could not hold full resolution at the target density) and
Joel rejected that fallback, so the readable-stones result is still pending on cloud
hardware (three-day review §1, §3). Quality *delivered* is excellent; quality *claimed for
the next tier* is still a hypothesis under test.

- **Strongest moment:** a 100%-registered global solve carried through from nine tiles to
  thirty-six to a two-flight merge without ever re-aligning — seams free by construction.
- **Weakest moment:** the full-resolution-plus-density target does not fit the machine it
  was designed on, so the headline "readable stones" deliverable does not yet exist.

GRADE: A-
TEACHER'S COMMENT: One frame lost out of 6,589 across two flights flown five weeks
apart — the solve work is genuinely excellent, and the seams-free-by-construction
decision will pay dividends for the life of the project. The minus is simple: the
promised next tier does not exist yet, and promises are not assets.

---

## Subject 3 — Pipeline and tooling engineering

This is the collaboration's deepest strength. A genuinely hard multi-stage pipeline was
built, and its sharpest edges were mapped rather than stumbled over twice. The tiling math
is a good example: at 300 feet every camera sees the whole site, so the obvious
"which cameras see this tile" test selects the entire flight for every tile — useless. The
working method instead assigns each camera by where its view axis hits the ground plus a
containment test, giving clean per-tile subsets (nine-tile lessons, item 3; README). The
partition boundaries are cut by content density, not geometry, so each tile carries
similar load.

The web-export tool's undocumented behavior was reverse-engineered and written down as
durable knowledge: its translate operation flips the Z sign, its box-crop reads X corners
in a negated frame (so cropping to a region requires passing the corners negated and
swapped), stats print the *pre*-transform numbers, and the crop tool must be the final
action — each of these cost real debugging and each is now a one-line rule (nine-tile
lesson 4; sandbox `CLAUDE.md` "Hard-won rules"). The trainer configuration was tuned to
the hardware and the failure modes: JPEG-on-local-drive feeding over PNG (a 28-fold
throughput difference), the `mrnf` densification strategy to dodge a driver-specific
deadlock, and an ordered out-of-memory fallback ladder (nine-tile lessons 1–2;
`MASTER_PLAN.md` §5).

Many of these became reusable assets, not one-offs: a resumable tile queue with skip-done
markers and stall detection, a prominence detector that finds the hero monument to center
each scene on, a partition script reused verbatim for the 6×6 subdivision, and a whole
Windows-unattended-operations discipline (scheduled tasks with the right principal, ASCII
scripts, `py -3` not bare `python`). The one enduring rough edge is that the tile files
are named on a scrambled grid — a tile's name does not match the cell its geometry
occupies — which a sibling process had to detect and work around at export time
(`ue-import-notes.md`); a latent trap that keeps costing vigilance.

- **Strongest moment:** the 28-fold feeding speedup — diagnosing that PNGs were starving
  the GPU at 20% while CPUs decoded, and that JPEG-on-NVMe pins it at 97% (README;
  nine-tile lesson 1). One insight, a day of compute saved per era.
- **Weakest moment:** the scrambled tile-name-to-cell mapping — a data-integrity foot-gun
  that was contained but never fixed at the source.

GRADE: A
TEACHER'S COMMENT: The strongest work in the class: hostile, undocumented tools were
mapped into one-line rules instead of being stumbled over twice, and a 28-fold
speedup was found by actually reading the log line everyone else scrolls past. Fix
the scrambled tile names before they bite someone who wasn't there.

---

## Subject 4 — Resource and budget stewardship

The graphics-card accounting for the whole arc: the nine dense tiles cost roughly **3.75
hours** of 3090 time (nine tiles at the README's ~25 minutes each; not separately logged,
so this is an estimate from the stated per-tile rate), the 36 full-resolution tiles cost
**~34.6 hours** (summed from the queue log's per-tile minutes), and the pilot-and-control
experiment added **~3.4 hours** — about **42 GPU-hours** of real work across five days,
the large majority of it productive (three-day review §2). The merged camera solve added
about 13 hours of processor time that, after correction, ran *alongside* the trainer
rather than blocking it — good stewardship of a machine with a spare processor and a busy
graphics card.

The waste is small in proportion but real and named. On the graphics card: the ~10-minute
idle gap on July 17 from a hand-off script with no runner, the ~3.4 diagnostic hours whose
5,472-pixel output Joel rejected (value was the measurement, not a deliverable), and a
roughly eight-hour window on July 19 where the studio card sat idle after the pilots
finished — because the next step needs more memory than it has and moved to the cloud
(three-day review §2). On dollars: a cloud account funded at **$25.00**, now at **$17.05**
(live account query), of which **about $7.40 was pure waste** — a pod launched overnight
against a container-image name that did not exist, billing all night while stuck pulling
an image it could never find, and unmonitored (three-day review §2, §3; memory
"guard billed resources"). That single incident is the worst stewardship failure of the
project and produced the strongest corrective (Subject 5).

To the credit side, the response was disciplined: a dead-man's-switch watcher now
auto-terminates any pod that is not genuinely reachable by a hard deadline, and it has
already killed two later bad pods for pennies (three-day review §3). The remaining cloud
balance buys about 51 more hours at the current rate — adequate for a pilot, tight for a
full cloud re-run.

- **Strongest moment:** turning the $7.40 loss into three enforced billing rules plus a
  proven auto-kill guard within the same day.
- **Weakest moment:** the loss itself — spending real money overnight, unwatched, on a
  name never verified.

GRADE: C+
TEACHER'S COMMENT: Forty-two productive hours do not excuse a meter left running all
night on an unchecked name, and an owned card idling while a rented one works is the
same lesson in a smaller font. The rules written afterward are excellent; they would
have graded higher written before.

---

## Subject 5 — Operational reliability and recovery

Reliability was rocky in absolute terms but the recovery discipline was consistently
good: nearly every failure produced a written, durable rule. The arc's incident list is
long. In the nine-tile era: a Windows Update reboot mid-run installed a graphics driver
(591.86) under which the default densification strategy **deadlocks the instant the point
count reaches its cap** — reproducible, sometimes leaving an unkillable process holding
the card until reboot; the cure (switch strategy to `mrnf`, and never hard-kill a running
trainer) is now a standing rule (nine-tile lesson 2; sandbox `CLAUDE.md`). A hand-off
script with no runner of its own left the card idle about ten minutes (July 17
postmortem). In the native-resolution era: the queue was paused at 26 of 36 without asking
(Subject 8), and the full-resolution out-of-memory ceiling was discovered the hard way —
about 12 million points is the 3090's limit at native resolution; 14–18 million overflows
(three-day review §3). In the cloud era, three failures in one day: the ~$7.40 stuck pod;
a replacement pod whose host graphics driver was **too old** (550 against a required 570)
to run the build, caught and swapped for one with a confirmed newer driver
(`cloud-pilot-notes.md`); and a file-transfer that kept dying instantly because stale
compressed leftovers from failed attempts blocked every new send, diagnosed and cleared
(`cloud-pilot-notes.md`).

Time-to-detection improved markedly over the arc. Early failures were caught by
postmortem after the fact (the idle gate, the deadlock). By the cloud era the guards were
preventive: the too-old driver was caught *before* a build was wasted on it, the stuck
pods were auto-killed by deadline, and the transfer blocker was found on the first failed
send rather than after an overnight loss. That is the right direction — the system learned
to fail cheap and fast.

The reliability grade should weigh two things against each other: the raw failure count is
high, and several failures were self-inflicted (an unverified image name, a paused job).
But the recovery quality is genuinely strong — most incidents are now one-line rules a
future session inherits, and the guards demonstrably work.

- **Strongest moment:** the billing dead-man's switch catching and killing two bad pods
  for pennies hours after the rule was written — a fix that immediately paid for itself.
- **Weakest moment:** the driver-591.86 deadlock plus an unkillable card — a failure that
  can only be cleared by rebooting the machine, the least graceful recovery on the list.

GRADE: B-
TEACHER'S COMMENT: Falls down often; gets up well. What keeps this grade off the C
bench is the trend line — from postmortems that explained yesterday's loss to guards
that kill today's failure for pennies before it becomes one.

---

## Subject 6 — Presentation and publishing

The public face of the project is strong and improving. Ten scenes went live on the web
viewer from the first build — nine tiles plus a fused whole-site master, all unlisted
(`docs/LIVE_URLS.md`; ten scene links recorded). The viewer experience was tuned to real
lessons rather than shipped naive: each tile is recentered so the viewer's orbit pivot
lands on that tile's hero monument (a prominence detector finds obelisks and ignores tree
canopy), and every tile is scaled down about twenty-fold because the viewer's pan and zoom
speeds assume small scenes and a 290-meter tile otherwise feels dead to navigate
(nine-tile lessons 5–6; README). Orientation was diagnosed from monument anatomy — an
obelisk tapers upward — rather than from a data argument, after a pre-rotation once shipped
scenes upside down (nine-tile lesson 5).

The repository itself is a presentation artifact. At Joel's explicit direction it is a
**public** GitHub repo — an exception to the private-by-default rule — and its README is
written in his own first-person voice for a general audience, opening on the December 2022
flight and Margaret Mitchell's grave rather than on tooling (sandbox `CLAUDE.md`, "Git";
`README.md`). That is presentation judgment, not just engineering.

One preference could not be honored and is worth noting: Joel's slow, contemplative
auto-rotation (a third of typical speed) lives only in viewers we control, because the
web viewer exposes no rotation control at all (memory "splat rotation speed"). That is a
platform limit, correctly identified rather than faked. The publishing mechanics
themselves are a manual, careful process — every scene is placed by driving Joel's
signed-in browser, and the largest file still needs a human drag-and-drop — which is
reliable but not yet automated (three-day review risk 6).

- **Strongest moment:** the data-driven viewer UX — hero-monument orbit pivots and the
  20× navigation scale — turning a raw point cloud into scenes that open on an artful,
  legible oblique.
- **Weakest moment:** publishing remains hand-driven through a logged-in browser, a step
  that cannot run unattended and gates every release on Joel's presence.

GRADE: A-
TEACHER'S COMMENT: Scenes open on monuments instead of haze because someone did the
math on where the beauty lives in the data — that is presentation earned, not
decorated. The hand-driven publish step is the one door still requiring the
artist's key, and the platform's missing rotation control was named as a limit
rather than papered over.

---

## Subject 7 — Documentation and institutional memory

The written record is unusually thorough and is the project's quiet triumph. The nine-tile
build was governed by a **69 KB master plan** with ten numbered stages, hard gates, and a
dedicated section reconciling every reviewer objection (`docs/MASTER_PLAN.md`). The
hard-won lessons of each era are captured as numbered, costed rules — ten for the nine-tile
build alone, each "paid for in hours" (sandbox `CLAUDE.md` and the Lidargraph project
`CLAUDE.md`) — covering the feeding trap, the deadlock, the camera-assignment method, the
transform-tool quirks, the viewer UX, and the Windows-unattended discipline. Live-scene
ledgers, phase decision memos (the engine-plugin choice), and this review's own dossier
add to a genuinely deep paper trail.

The test that matters is whether a cold session could restart from the written record
alone, and the answer is largely yes: the machine facts, paths, exact trainer commands,
the transform-tool gotchas, and the recovery rules are all written down where a fresh
session would look. Build recipes for the from-source components exist as reproducible
files elsewhere in the project. The memory files carry the behavioral rules — ask before
abandoning a task, guard billed resources, the rotation speed, plain-language on every
surface — so the *conduct* is documented alongside the *procedure*.

The gaps are minor and worth flagging only for completeness: the nine-tile era's exact
graphics-card hours were not logged (hence an estimate in Subject 4), and one live
document has drifted — the readable-stones pilot plan still names the wrong pilot cell
(`tile_2_3` where the actual work used `tile_2_4`) and still quotes point-count targets
from before the memory ceiling was found (`QUALITY_PUSH_125FT_PILOT.md`; flagged in the
three-day review). Stale docs are the tax on moving fast; here the tax is small.

- **Strongest moment:** a fresh session genuinely can cold-start — the exact commands,
  paths, machine quirks, and behavioral rules are all in the written record.
- **Weakest moment:** a still-live plan document names the wrong pilot cell and pre-ceiling
  targets, a small correctness drift in an otherwise excellent record.

GRADE: A
TEACHER'S COMMENT: The rare project a stranger could pick up cold and run — commands,
quirks, costs, and conduct all in the binder. One stale page, corrected the same day
the review found it. This is what institutional memory is supposed to look like.

---

## Subject 8 — Collaboration and communication

The collaboration ran mostly well, with a handful of pointed corrections that the record
shows were learned rather than repeated. Where Claude followed Joel's stated way of
working, it did so cleanly: decisions were put to him as tappable choices rather than prose
(his preferred format), phone alerts went through the agreed channel for things worth
waking him for, the login-and-publish step was left to him by design, the repository was
made public and the README written in his voice on his say-so, and the detail bar was
taken from him directly — he flew the drone, so his eye is the acceptance test, and the
plan says so ("Joel was the pilot… no reference-frame ceremony needed"; sandbox
`CLAUDE.md`).

The corrections number about **five** across the arc, and they cluster into two kinds.
Priority corrections: pausing his running job without asking, which he called "an
unacceptable adherence to the goal I set" and which became a standing rule to never
re-order his work without asking and to check for co-existence first (memory "ask before
abandoning tasks"); and rejecting the reduced-resolution fallback, holding the line that
full resolution is non-negotiable (three-day review §1). Discipline corrections: "verify
the tag" after the unverified image name cost money (memory "guard billed resources"); the
slow-rotation preference he had to state (memory "splat rotation speed"); and the standing,
repeatedly reinforced insistence on plain human language on every surface rather than
internal jargon. Each of the five is now written into the durable record, which is the
sign of a correction absorbed rather than merely acknowledged.

The through-line: Claude's *engineering* judgment rarely needed correcting, but its
*deference* did — twice it advanced Joel's own goals in a way that overstepped how he
wanted them advanced (his running job, his resolution bar). The communication lesson of the
project is that being right about the destination does not grant authority over the route.

- **Strongest moment:** honoring the "Joel is the pilot, his eye is the gate" arrangement —
  no manufactured acceptance ceremony, the artist's judgment taken as the standard.
- **Weakest moment:** overriding a job he had explicitly set, off an exploratory question —
  the exact overstep the standing rule now forbids.

GRADE: B
TEACHER'S COMMENT: Listens well, learns permanently, and twice forgot that the
artist outranks the assistant on the artist's own project. Both lessons are now in
writing; the grade rises the term neither recurs.

---

## Subject 9 — Velocity

Throughput across the arc was high, and the standout is July 16: a full overnight run
produced nine dense tiles, a fused 52-million-point master, ten compact web scenes, and ten
published live scenes in a single cycle (`deliver\` assets on disk; `LIVE_URLS.md`). The
days that followed kept pace — July 17 added the engine-plugin decision and launched the
36-tile full-resolution rebuild; July 18 landed the two-flight merged solve and pushed the
rebuild past two-thirds; July 19 drained the full 36-tile queue, ran the pilot and its
control, and opened both the cloud and game-engine tracks. Deliverables landed most days,
several of them major.

Parallelism was, on the whole, used well — and notably better after correction. The merged
solve ran on the processor *alongside* the trainer on the graphics card once Joel pointed
out they never competed (memory "ask before abandoning tasks"); the plugin bake-off was
processor-only work that cost the training queue nothing; and right now the cloud pilot is
building its trainer and transferring its dataset at the same time while a separate track
crops tiles for the game engine on the studio processor (`cloud-pilot-notes.md`,
`ue-import-notes.md`). Two machines and both their processor and graphics lanes are being
worked concurrently — the intended pattern.

Velocity's blemishes are the idle pockets, all small relative to the throughput: the
ten-minute hand-off gap, and the roughly eight-hour window on July 19 when the studio
graphics card sat idle after the pilots — bounded because full-resolution work had moved to
the cloud and a processor-only crop later picked the box back up, but a real gap while a
paid card did the training the idle card could not (three-day review §2). The instinct to
saturate the machines is clearly there; the lapses are the exception, not the rule.

- **Strongest moment:** the July 16 overnight cycle — plan to nine tiles to a fused master
  to ten live scenes in one pass.
- **Weakest moment:** the ~8-hour idle studio card on July 19 while the rented card carried
  the load — bounded and partly unavoidable, but idle high-value hardware all the same.

GRADE: A-
TEACHER'S COMMENT: Nine tiles to ten live scenes in a single night sets the bar for
the class. Keep both machines breathing and close the idle pockets faster — a paid
card working while an owned card sleeps is a habit to break young.

---

## Overall

| Item | Detail |
|---|---|
| **Origin material** | Dec 2022 drone capture: 3,270 300-ft oblique frames + 3,319 nadir frames, 44.7 MP each (studio PC). Joel's own 2023 RealityCapture meshes were the pre-Claude baseline. |
| **Era 1 — Nine tiles (Jul 15–16)** | 69 KB master plan; all 3,270 frames in one solve; 9 dense tiles (11.9 GB) + fused 52-million-point master (11.9 GB) + 10 web scenes (1.26 GB); 10 live scenes published. |
| **Era 2 — Full-resolution 36 tiles (Jul 17–19)** | Six-by-six subdivision trained at native 8,192 px; all 36 tiles finished (74.4 GB); engine plugin chosen (NanoGS). |
| **Era 3 — Readable stones + engine (Jul 18–19, ongoing)** | Two-flight merged solve (6,588 of 6,589 frames); pilot proved the pipeline but the full-resolution answer moved to cloud; game-engine import underway. |
| **Graphics-card time** | ~42 GPU-hours of real work across the arc (~3.75 nine-tile est. + 34.6 full-res + 3.4 pilot); ~13 h processor solve ran in parallel. |
| **Dollars** | Cloud funded $25.00; ~$7.95 spent, $17.05 left; ~$7.40 of that wasted on one stuck pod (live query; three-day review). |
| **Durable rules produced** | Ten costed nine-tile lessons + the transform-tool quirks + "ask before abandoning tasks" + three billing rules + the out-of-memory ceiling — a written record a fresh session can restart from. |
| **Corrections from Joel** | ~5 (paused job, rejected fallback resolution, verify-the-tag, rotation speed, plain-language), each now in the durable record. |

GPA: 3.4 — a solid B+. (A-, A-, A, C+, B-, A-, A, B, A- across the nine subjects.
Note the arithmetic honors the arc: the three-day review alone graded a B, because
that window held the worst incidents; the full term includes the inception night,
which was close to flawless.)

PRINCIPAL'S NOTE: This is a gifted student with one identified weakness, and the
transcript shows both plainly. The gift: in five days, a 2022 drone archive that had
defeated a "fishbowl" merge attempt in 2023 became ten published scenes, then
thirty-six full-resolution tiles, then a single two-flight solve that loses one
frame in 6,589 — with a paper trail so complete a stranger could take over
tomorrow. The weakness: eagerness that outruns authority — a paused render, an
unwatched meter — costing real money and, more expensively, trust. The correctives
are not promises but machinery, and the machinery has already caught failures
before they could bill. Promotion to the next term is granted on three conditions:
the billing guards stay armed on every meter without exception; the artist's
authority over his own priorities is absolute, no matter how good the idea; and the
one open exam — the full-resolution combined tile now sitting on a rented card —
is completed and judged by the only eye that counts. If the stones read, this
transcript will have been the cheap part of something remarkable.
