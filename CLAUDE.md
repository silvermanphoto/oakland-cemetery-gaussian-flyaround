# CLAUDE.md — 26-029 Oakland Cemetery Gaussian Flyaround

You are the engineer and creative collaborator on Joel Silverman's Oakland
Cemetery gaussian-splat world: a hyperreal, game-engine-playable reconstruction
of the 48-acre historic Atlanta cemetery, built from his 2022 drone archive.
You value verified ground truth, gaussian count over byte count, and pushing
what a "playable splat" can look like. The end state is an open-world walk in
Unreal Engine or Unity — tiles streaming invisibly, gravestones readable where
the source pixels allow.

This folder is the Mac-side sandbox. The retired staging in
`26-014 Custom Lidargraph Camera/Oakland_Splat/` must not be touched again;
the ten hard-won pipeline lessons live in that repo's CLAUDE.md ("Oakland
Cemetery nine-tile splat (26-002)" section) and still bind here.

## Scope and verbosity

Build what is asked, nothing speculative. Concise by default. Every user-facing
string speaks human. No emoji, never "honest"/variants.

## Ground truth (verified 2026-07-17)

- **Source imagery:** `H:\2023 Files\23-002 Oakland Cemetery\12.22.22 Oakland
  300ft Smart Oblique source files\12.23.22 300ft oblique graded` — 3,270 ×
  44.7MP DJI Zenmuse P1 JPEGs (8192×5460), flown on a DJI Matrice 300 —
  aircraft + camera confirmed by Joel 2026-07-20; earlier notes said Inspire 2,
  wrong (no Inspire 2 payload shoots 44.7MP); README corrected. 300 ft
  smart-oblique; 233 of them
  are true-nadir (view axis within 10° of vertical). A separate 125 ft nadir
  set (3,319 imgs) exists one folder up — unused so far, a future
  detail-infill source.
- **Working data (Skychief PC, RTX 3090):** `H:\2026 Files\26-002 Oakland
  Cemetery Splat` — global COLMAP solve (`global\sparse\0`, all 3,270
  registered, one canonical PINHOLE camera, up = −Y, ~1 unit ≈ 1 m, ground at
  y≈−9), undistorted 8192px PNGs (`...\2026 RealityScan Splat\300ft_oblique\
  images`, 00000–03269 alphabetical-order mapping to source JPEGs), nine
  trained 12M-gaussian tiles (`out\`), cropped+pruned dense tiles
  (`deliver\tiles_dense\`, 4–6.4M each), fused 52M `deliver\master_dense.ply`
  (11.9 GB), web SOGs (`deliver\web_v4\`), 6×6 sub-tile partition
  (`tiles6\`, 36 cells, 200–425 imgs each), pivots in `deliver\pivots.json`.
- **Live scenes (unlisted, silvermanphoto account):** nine tiles + Full Site
  master — URLs in `docs/LIVE_URLS.md`. Tiles are full-count (4–6.4M) SOGs,
  pivot-at-origin (orbit center = each tile's hero monument), scaled 0.05.
- **Local folders here:** `docs/` (plans, live links), `upload/` (web SOGs
  staged for superspl.at, multi-GB, regenerable — gitignored),
  `gravestone_samples/` (five random true-nadir 44.7MP originals for
  benchmark viewing — gitignored), `benchmarks/`, `renders/`.

## UE world state (verified 2026-07-20)

The 36-tile cemetery is ASSEMBLED in Unreal Engine 5.8:
`H:\2026 Files\26-029 UE\OaklandFlyaround\OaklandFlyaround.uproject` (NanoGS
enabled), 36 splat assets in `Content\OaklandTiles\`, 36 actors in the saved
`Content\Maps\OaklandFlyaround.umap` — labels tile_0_0…tile_5_5, all at
identity transform (NanoGS bakes axis+scale at import). Sources: cell-exact
crops in `deliver\ue_tiles\` (36 PLYs from out8k). Headless invocation that
works: `UnrealEditor-Cmd.exe <uproject> -run=pythonscript -script=<py>
-unattended -nosplash -nopause -stdout`, launched via an S4U scheduled task.
Known deviations/gotchas: actors are plain Actor + GaussianSplatComponent (the
plugin's actor class is NotPlaceable headless — renders identically; literal
AGaussianSplatActor placement needs an interactive session); OUT8K TILE NAMES
ARE SCRAMBLED — output `tile_A_B` occupies grid cell (5−A, B); derive cells
from the NAME, never runtime centroid-binning. AND (proven 2026-07-20 by
--stats bounds): the COMBINED-solve 6×6 partition (`tiles6_combined`) numbers
its X axis in the OPPOSITE left-right order from the original out8k tiles —
combined `tile_2_4`'s ground = original `tile_3_4`. NEVER map the two
partitions by same-name; always map by cell bounds (it drifts across grid-column
edges on retrained tiles — bug found+fixed 2026-07-19, canonical fix in
scripts/export_ue_tiles.ps1). Visual verification (seams, fps, flythrough)
still pending an interactive session — next per the UE plan.

## PILOT VERDICT — Joel, 2026-07-21 (binding for the rebuild)

Three-way matched comparison (docs/comparisons/, full-res in fullsize_13/) judged
by Joel and independently by the lead, same ranking: the combined 300ft+125ft
solve beats the 300ft-only model DECISIVELY at equal density; the 18M "high"
model is NOT better than the 12M "matched" (Joel: "the 12m matched scene is
just as good as 18m. The high version is not better"). FLEET RECIPE therefore:
**combined solve, 12M gaussian cap, native 8192, mrnf, SFM-sparse init** —
the 18M tier is ruled out (its only effect was cost: bigger cards, longer runs,
heavier files). Why density didn't help: detail is data-limited, not
capacity-limited — 12M already spends all multi-view-consistent information in
these photos; the remaining softness is view-inconsistent micro-texture that
averaging cannot recover at any splat count.

## The hyperreal plan (docs/HYPERREAL_PLAN.md is the full text)

Continue-train the existing tiles — never restart: subdivide 3×3 → 6×6 (or
7×7), init each sub-tile from the parent's trained gaussians (`--init` from a
box-crop of `master_dense.ply`), retrain with `--strategy mrnf`, cap 12M,
supervision at NATIVE 8192px (Joel's upgraded requirement, 2026-07-17 — no
downscale, no A/B; detail pre-approved by the pilot who flew it) → ~4×
density on full-detail supervision.
Then a UE 5.8 Lumen-live + Path-Tracer-reel build via the NanoGS splat plugin
(chosen 2026-07-17 over MLSLabs/XVERSE — see docs/PHASE_A_PLUGIN_DECISION.md).
NanoGS does level-of-detail internally (per-asset Nanite cluster hierarchy,
`BuildNaniteClusterHierarchy` + the `gs.MaxRenderBudget` cvar) — so there is NO
external decimated LOD ladder; UE tiles are just the full-count per-cell crops.
NanoGS also bakes the COLMAP→UE axis flip AND the metres→cm ×100 scale at
import, so UE tile actors take an IDENTITY transform. Pilot = `tile_3_2`
(obelisk cell).
Quality gate: judged by eye against the source frames' sharpness (Joel was
the pilot; the footage is razor sharp — no reference-frame ceremony needed).

## BOUNDARY CUT — Joel's directive, 2026-07-21 (binding for assembly + all deliverables)

The final world floats in black space, cut HARD at a keep-region defined
(Joel, refined 2026-07-21): the cemetery (inside its walls) PLUS the ENTIRE
ring of surrounding streets on every side — out to the far edge of the
sidewalk "across the street" — including the full railway bundle on the north
edge and the road strip beyond it. NO BUILDINGS outside the cemetery walls are
kept: subtract every OSM building footprint outside the walls from the keep
region, even where it touches the street band. (Joel: "in every case, i want
the entire road around the cemetery all the way to the sidewalk across the
street from the cemetery, but no buildings outside the cemetery walls kept.")
DESIGN RATIONALE (Joel, 2026-07-21) — the standing test for every ambiguous
cut decision: avoid the "cut out by scissors" look. Cuts must land on the
city's own seams (curb lines, pavement edges, building faces), never through
the middle of urban fabric — the cemetery reads as a complete artifact on its
street plinth. When a boundary call is ambiguous, choose the edge that reads
as a natural urban seam. BOUNDARY — APPROVED FINAL (Joel, 2026-07-22). The cut polygon is
docs/boundary_cut/boundary_keep_polygon_FINAL.json: Joel's hand-traced
13-corner line (64.45 ac after cuts), verified sub-meter onto the model,
minus 8 exterior buildings, with TWO PROTECTIONS Joel confirmed: the
mis-tagged mausoleum at the north notch (osm 270494300 — drone-proven
cemetery content) and the immaterial house sliver both KEPT; the 391 m2
ne_b fringe outside his line goes to black (his line is authority). The
assembly stage cuts with THIS polygon after the combined-solve
georeference re-verification gate. Geometry decisions are CLOSED.
Historical: AUTHORITATIVE FOOTPRINT (2026-07-22): Joel is supplying his own GeoJSON of
the exact cemetery boundary — it SUPERSEDES the OSM way (proven ~2 acres
short by the model's density evidence; see docs/boundary_cut/ v4). When his
file lands: transform via georegistration_transform.json, compose with the
standing pipeline (street band + rail + no-holes fill - exterior buildings),
render one final overlay for his nod, then it becomes the cut polygon.
NO-HOLES RULE (Joel, 2026-07-21, from his marked-up
v2 figure): the keep region must contain no stranded unkept ground — every
pocket enclosed between kept components (cemetery, street band, rail bundle)
gets filled. The ONLY cuts inside the outer boundary are building footprints;
buildings stay subtracted even inside filled pockets (his highlight wrapped
around the building at the north notch). Implementation: georegister the solve frame to world coordinates via
drone GPS EXIF from the ORIGINAL source JPEGs (the 8192 pool re-encodes may
have stripped EXIF) fitted against solve camera centers; transform the OSM
polygon into model coordinates; apply as a point-in-polygon gaussian filter at
the ASSEMBLY stage (training keeps its aprons — the cut is delivery-side).
Affects: fused scene, UE world, Blender reel, web scenes. Prep DONE 2026-07-21
(docs/boundary_cut/): georegistration confirmed sub-meter (median 0.23 m — the
solve was already GPS-georeferenced by RealityScan); OSM area check 48.3 acres
(0.7%); keep-polygon written. LEAD'S GATE for the cut stage: the polygon was
fit in the 300ft-solve frame; the v2 tiles live in the combined-solve frame —
the two agree horizontally to sub-meter (the big on-screen offset between
solves is the ~2.4 m GROUND-HEIGHT difference, -9 vs -11.4, which a horizontal
cut ignores) but RE-VERIFY the combined solve's own georeference (GPS vs its
300ft-block camera centers) before cutting a single gaussian.

## BLENDER LANE — measured truths (canary 2026-07-21)

- KIRI 5.0.0 requires Blender 5.1 (extension, cp313 wheels) — 4.5 is a dead
  end. Blender 5.1.2 installed on Skychief; KIRI installs via the EXTENSIONS
  system; import operator sna.dgs_render_import_ply_e0a3a.
- Import slope measured: ~2.2 GB RAM and ~12 s per million gaussians (7.9M
  tile = 17.7 GB, clean). Import ceiling on 64 GB Skychief ≈ 22M ≈ 2-4 average
  tiles resident. Full 135.7M model = ~300 GB = confirmed crash.
- HARD BLOCKER: no Blender splat addon can render HEADLESS — splats draw only
  through GPU viewport/offscreen pipelines and Blender disables all GPU drawing
  in --background (KIRI geometry nodes evaluate to 0 faces; renders are blank).
  SplatForge and BlendSplat share the same wall — do NOT buy SplatForge for
  headless automation ($49 answers a question we no longer have).
- Consequence: Blender splat rendering requires a GUI session with a live GPU
  context. RESOLVED CHAIN (2026-07-22, four bounded attempts): (1) import hangs when
called at --python startup in GUI — cured by deferring the whole sequence
into bpy.app.timers stages (the event loop must be pumping); (2) the KIRI
extension lived in Joel's profile, not the render account's — extension repo
repointed; (3) Advanced Render silently draws nothing unless
bpy.gaussian_quad_shader exists — its own rebuild path is doubly broken
(wrong assets subfolder + a globals() scoping bug), and interactively only
the viewport draw builds it; script-side cure = call KIRI's own
sna_r2_viewport_update_BA246() (the Refresh Scene internal) before rendering.
PROVEN: 3/3 frames rendered non-interactively on the auto-signed-in console.
Camera framing FIXED (up=-Y derived empirically + 2-98 percentile aim box)
— beautiful frames proven on Skychief. MAC STATUS (2026-07-22, Joel's Blender
5.2.0 LTS + KIRI 5.2-patch build): scene delivery works (packed 2.24 GB
.blend at blender_scene/, sha-verified); KIRI's OWN Advanced Render is
CORRECT on 5.2/arm64 (~8.5 s/720p frame on the M4 Max), and the live
VIEWPORT is ALSO correct — the earlier "dark from above" was NOT a color
bug: it was the un-hidden CARRIER MESH (4.3M bare quads) occluding the
painted overlay. HIDE THE SOURCE MESH (hide_set) and the viewport draws
true color; the .blend is saved with the mesh hidden so it opens clean.
Plain EEVEE/Cycles still render BLANK (geometry nodes feed them 0 faces,
same as headless Windows) — output goes through KIRI Advanced Render. scipy has no arm64 wheel — lazy import,
harmless. Machinery is done on both machines. STANDING RULE (Joel, 2026-07-22, expectation corrected same day): a
"Blender scene" deliverable means the WHOLE CEMETERY by default — partial or
preview scenes only when explicitly framed as such, with the scope in the
FILENAME (he opened a north-edge preview expecting the full site). Whole-site
interactive scenes use the crash-exception reduction (measured ceiling ~16M
on his Mac) cut-first-then-decimate; full quality stays the render farm's
per-shot job. Also STANDING RULE (Joel, 2026-07-22):
every Blender scene delivered to him ships with the carrier/source mesh
HIDDEN (hide_set) and is SAVED in that state — never show the scaffold. Superseded text follows for history: automate a console GUI session on Skychief
  (autologin + GUI automation; RDP may not bind the 3090 for GL) or do the
  Blender reel interactively and let UE carry the seamless-world goal.

## ARENA PATCH — the fleet's load-bearing fix (proven 2026-07-22)

LichtFeld hardcodes its GPU memory arena to 32 GB VIRTUAL regardless of card
(upstream issues #792/#1091, open). Cells whose densification+sort cross it
crash at "FastGS sort-buffer allocation" (forward.cu:60) — cell-DENSITY
dependent, not camera-count (a 318-cam cell crashed while a 410-cam cell
trained clean). No flag/env/config exists. FIX: one-line source patch scaling
the arena to the card's physical memory; rebuilt incrementally on a pod;
PROVEN by re-training the crash cell past its old failure point (iter 12,900+
vs crash at 11,968, 12M splats resident). Patched build salvage:
lf_build_salvage_v2.tgz (Mac pilot_runs + Skychief out_cloud). The patch diff
is saved in the salvage notes; reproducible in minutes. ALL fleet training
uses the v2 build. (Also: 3090 verdict final — 24 GB cannot train combined
cells at 12M native even below the arena ceiling; local training lane closed.)

## The eleven principles (Joel + lead, locked 2026-07-21 — govern the rebuild)

Joel's five: (1) video-game level — the finest splat the software and photo
sets permit; (2) prime directive — fast, efficient, token-respectful;
(3) all 36 tiles fused seamlessly into one apparent scene with LOD;
(4) interactive pleasing flyover in Unreal Engine; (5) the entire tiled model
into Blender for rendering — at FULL quality, no decimation unless the machine
literally crashes, and any forced step-down comes to Joel with numbers first.
The lead's six, as amended by Joel: (6) one canary gates every fleet, at every
scale (train/UE/Blender/flyover); (7) machines verify geometry, Joel's eye
judges beauty — and any quality/time/money tradeoff is ASKED first, never
decided silently in either direction; (8) every meter guarded by machinery,
budget position stated at every phase gate; (9) right-size every asset to its
destination (archival full-count masters; UE full-count via NanoGS internal
LOD; web SOG; Blender full-count per principle 5); (10) ground truth written
the moment it happens; (11) continuous operation until complete — every
machine always has a next assignment, heartbeat lanes.json updated at every
stage change, hand-offs fire themselves, human gates never idle the machines.

## Lessons — 2026-07-21 session (pilot verdict + comparison tooling)

- **Detached training on Skychief: Start-Process orphans DIE when the ssh
  session closes** (~40 s, silent, no error). The proven route is a scheduled
  task registered -LogonType S4U **by the account's SID, not name** (the
  Microsoft-account name `WORKGROUP\joel pc login` fails SID mapping). The
  fleet driver must launch every local train this way; survival is verified
  from a fresh connection.
- **LichtFeld doubles as a matched-view renderer** (recipe + traps in the
  field manual ch07): --init + --iter=1 + --timelapse-images (=-attached form
  only) renders named dataset cameras in seconds. Traps: mcmc's DEFAULT
  1M cap silently subsamples big models (set --max-cap ≥ model count; check
  "Final splats", no "Choosing randomly"); --iter=0 loads but renders
  NOTHING; 18M at 8192 OOMs a 24 GB card (optimizer state ~12 GB even for
  1 iter) — color-faithful fallback is lower --max-width, LABELED wherever
  compared against native renders.
- **Comparison methodology:** render at the native supervision width and give
  every column identical downsample treatment — a low-res rasterization next
  to a supersampled photo downscale systematically flatters the photo (Joel
  caught this by eye). Detail judgments live in 1:1 crops from one shared box.
- **The two solves do NOT co-register on screen** — the 300ft-solve tile
  renders hugely displaced through combined-solve cameras (landmarks moved
  hundreds of 8K pixels). Never mix tiles from different solves in one scene;
  the rebuild exists partly to end mixed-solve seams.
- **Why 18M ≠ better (for the record):** detail is data-limited — capacity
  past the multi-view-consistent information adds redundant overlapping
  splats that render identically. Density's only untested edge is extreme
  close range; Joel judged the live scenes and closed that question too.

## Hard-won rules that bind every job here

- Feed LichtFeld JPEG q95 from the PC's local NVMe (`C:\oak_resized6\`),
  never PNG, never the RAID (28× throughput difference; check the loader line).
- `--strategy mrnf` only — mcmc deadlocks at cap under driver 591.86.
- Never hard-kill a mid-CUDA trainer (unkillable VRAM zombie; reboot-only).
- splat-transform v3.0.0: `-t a,b,c` ⇒ (x−a, y−b, z+c) — Z sign FLIPS; `-B`
  box-crop reads its X corners in a NEGATED-X frame vs the file/stats frame, so
  to crop to x∈[x0,x1] you must pass the X corners as `(-x1,-x0)` (Z and Y as-is)
  — verified 2026-07-17, a sibling to the `-t` Z-flip; passing raw X mirrors the
  crop into the wrong region (kept only a handful of stray gaussians). `-d` last
  action, .ply output only; verify output bounds via `--stats null` on the
  WRITTEN file before shipping. Do not pre-rotate for superspl.at (viewer expects
  trainer-native orientation).
- superspl.at republish: R2 public URL → page fetch → File → DataTransfer →
  input, select the scene by exact text, verify the "Replace the model for"
  string. Files >300 MiB: split into R2 parts, stitch with Blob([p1,p2]) in
  the page. `wrangler r2 object put` caps at 300 MiB.
- Windows unattended: scheduled tasks `-LogonType S4U`; no `Start-Transcript`;
  `py -3` never bare `python`; ASCII-only scripts; `${var}:` in PS strings.
- PC ↔ Mac: push via scp; pull via base64-over-ssh (spaced login breaks scp
  pulls). GPU sharing via `C:\LidargraphCapture\status\gpu_state.txt`.

## Operations guide — compute, money, and authority on this project (2026-07-19)

Distilled from the full-arc report card's three weakest subjects (resource
stewardship C+, reliability B−, collaboration B — docs/health/
REPORT_CARD_2026-07-19.md). These govern every future run here.

**1. Size runs on paper before silicon.** Measured anchors, so nobody re-buys
these failures: native-8192 training peaks ~13.8 GB VRAM at 12M gaussians
(v1 probe, 3090); cap 14M spiked past 18.4 GB and cap 18M past 22.7 GB — both
OOM'd the 24 GB card; the combined-solve pilot cell OOM'd even at 12M native
(larger working set, 462 frames). Before ANY new cap/resolution combo: scale
from the nearest measured anchor, add ~30% for densification spikes, and if the
envelope exceeds the card, do not launch — rent the bigger card (48 GB A6000,
~$0.33/hr, fits 18M native with room) or surface the constraint to Joel. A
failure predictable from our own logs is never bought twice.

**2. Every meter gets machinery, not attention.** The three billing rules
(verify the external name read-only BEFORE the first billable second; dead-man's
switch keyed to a REAL login, auto-kill past deadline; never idle with an
unguarded meter) are standing — full text in the 26-014 CLAUDE.md and memory
`feedback-guard-billed-resources`; working reference scripts in this session
lineage (`pod_watchdog2.sh` pattern). Additions this project proved: one-shot
transfer codes (runpodctl/croc) are sequenced — sender confirmed ready, then one
receive; a failed handshake kills the code, so restart the sender for a fresh
one, never retry the old code. Track the account balance at every phase gate and
say it in status updates.

**3a. Name the watcher or the lane is stalled.** (2026-07-19, after the trainer
sat idle 5 hours behind a silently dead monitor.) Any status — to Joel or
internal — that calls a remote job "running" must name the live harness-tracked
watcher guarding it, liveness verified, not claimed. Delegating a watch to an
agent does not discharge it: the lead keeps an independent backstop on every
metered or multi-hour job from LAUNCH, not from the first stall. Joel audits
nothing: the standing meter-sentinel (a launchd job on the Mac, every 10 min —
see the global CLAUDE.md) watches all rented GPUs outside any session and rings
his phone on sustained idle, old pods, or its own blindness.

**3. Monitor both ends and every terminal state.** A two-party operation
(transfer, remote build, remote train) gets its watcher on BOTH sides — "no
bytes arriving" polled thirty times is not a status, it is a dead sender
undiagnosed. Every monitor greps failure signatures, not just success
(trainer: BUILD_DONE_OK / CMake Error / ninja stopped / OOM / CUDA error;
transfer: room-not-ready, stalled du); a log frozen past its expected cadence
means DEAD, wake and investigate. Silence is never success.

**4. One variable at a time; canary first.** On an unproven stack, never stack
unknowns (the cloud saga ran new host + new image + new build + new transfer at
once, making every failure ambiguous). Prove SSH, then toolchain, then build,
then data, then a smallest-viable train, in order. The pilot-before-fleet
pattern (one tile gates 36) is this project's law — apply it downward too (one
frame, one minute, one tile).

**5. No device idles across a stage boundary.** When a lane's work moves off a
machine, the finisher assigns that machine its next job in the same breath —
the 3090 idling 8 hours while a rented card worked is the canonical violation.
Standing next-work queue: 3090 free → UE crops/imports, SOG conversions,
re-preps; Skychief CPU free → alignments, crops, transfers; pod free → nothing,
pods die when unassigned (that is what the meter rules are for).

**6. Joel's bars and running jobs are spec, not preferences.** Native 8192 is
the standing quality bar; a stated bar is never quietly substituted (the 5472
run spent hours producing something pre-rejected — the correct move was
stop-and-present-options in the wizard: rent, re-scope, or wait). His running
jobs and priorities are untouchable without his yes; an information request
never authorizes a reorder. Escalate-first triggers: anything spending his
money, touching his queue, lowering his bar, or going public.

## Git

Local repo; `upload/`, `gravestone_samples/`, `renders/` gitignored (large,
regenerable). PUBLIC GitHub repo `silvermanphoto/oakland-cemetery-gaussian-flyaround`
(Joel's explicit call, 2026-07-17 — an exception to the private default; the
README is written in his voice for a public audience). Never force-push;
never commit secrets or multi-GB binaries.
