# Blender Lane — Oakland Cemetery Gaussian Flyaround (26-029)

**Purpose:** render the full 36-tile fused cemetery splat in Blender, at full
quality (principle 5). This document is the verified design + the staged canary
protocol. Nothing has been trained on, decimated, or run on Skychief's GPU —
staging only, because training is in flight.

**Written 2026-07-21.** All external claims below were checked against primary
sources on that date (addon repos, the authors' own docs, blender.org). Access
dates are in the Sources section.

---

## 1. The headline: can principle 5 be met as stated?

**Principle 5 as literally worded — "the entire tiled model into Blender for
rendering, at full quality, no decimation unless the machine literally
crashes" — cannot be met as one all-at-once scene on Skychief. The machine
*would* literally crash.** Here is the number that settles it, before any
software question:

- The 36 tiles total **135.7 million gaussians** (measured from the PLY headers,
  not estimated — see §2). At full spherical-harmonic degree-3 color, the raw
  gaussian data alone is **~32 GB of video memory**. Skychief's RTX 3090 has
  **24 GB**. The color coefficients by themselves (~24 GB) already fill the
  whole card. Add Blender's own overhead, the depth-sort buffers, and the frame
  buffer and you are far over 24 GB before a single pixel renders.
- In system memory it is just as bad: the raw data is ~34 GB, but every current
  Blender splat add-on expands each gaussian into extra structure (KIRI turns
  each one into a little mesh face), 2–5× the raw size — 68 to 170 GB against
  Skychief's **64 GB**. It would thrash and die.
- And no current Blender add-on is even built to hold that many at once: the two
  free ones comfortably handle a few million to low tens of millions; the paid
  one's own manual says it crashes past ~16 million. 135.7 million is 8–60×
  those ceilings.

So the literal "load all 36, full quality, one scene, one render" is off the
table on this hardware — this is exactly the "machine literally crashes" case
principle 5 tells us to bring to you with numbers first. **That is what this is.**

**But the deliverable is achievable at full quality — no gaussian ever thrown
away — at the next tier down:**

> **Per-shot region rendering.** The flyaround is a moving camera. Break its
> path into shots. For each shot, load only the *full-count* tiles the camera
> actually sees over that shot, render those frames at full degree-3 color,
> free them, move to the next shot. Every rendered frame is full quality. No
> tile is ever decimated — a tile that is off-screen or far in the distance is
> simply not loaded (or loaded at reduced *color* detail), which is runtime
> level-of-detail — the very thing principle 3 already asks for — not the
> permanent gaussian-count reduction principle 5 forbids.

This is the honest tier verdict: **full 36 loaded at once = no (crash);
per-shot region loading at full count = yes.** The canary (§6) measures exactly
how many tiles fit per shot on this machine so the shot list can be built from
real numbers, not guesses.

A paid escape hatch exists (rent a 48 GB+ cloud GPU, §4) but it raises only the
memory wall, not the add-on-architecture wall — so it does not, by itself, buy
the literal all-at-once render either. Detail in §7.

---

## 2. Ground truth — the tiles and the machine (measured, not assumed)

**The 36 tiles** (`Oakland Cemetery 36 Tiles PLY/`, read from the PLY headers):

- **135,708,869 gaussians total (~135.7 M)** across 36 tiles — *not* the
  200–430 M the brief assumed. This correction is load-bearing for everything
  below.
- Per tile: smallest **0.19 M** (`tile_0_5`), largest **7.90 M** (`tile_1_4`),
  average **3.77 M**. Full list in the manifest.
- **Full spherical-harmonic degree 3** (`f_dc_0..2` + `f_rest_0..44` = 48 color
  coefficients per gaussian) plus normals. That is **62 floats = 248 bytes per
  gaussian on disk**, 31.3 GiB total. These are *true view-dependent-color*
  tiles — so any add-on that renders only the flat base color (DC-only) is a
  real, visible quality loss, and is flagged as such below.
- One shared coordinate frame: up = −Y, ~1 unit = 1 m, ground at y ≈ −9, tiles
  butt together seamlessly at their cell edges (half-open grid — no gaussian
  belongs to two tiles).

**Skychief** (verified live, read-only, 2026-07-21):

| Resource | Value |
|---|---|
| System RAM | **63.9 GB** (~64 GB), 50.7 GB free at probe |
| CPU | 24 logical cores (Gigabyte X570S AERO G board) |
| GPU | RTX 3090, **24 GB VRAM** (nvidia-smi authoritative; WMI's "4 GB" is a known 32-bit reporting bug) |
| GPU state now | **95 % busy, 19.6 GB used, 4.7 GB free — training is running; do not touch** |
| Disk | C: 150 GB free, D: 147 GB free, **H: 35.4 TB free** (Blender work + tiles belong on H:) |
| Blender installed | **only 3.0 and 3.4** — no 4.x/5.x. **An install is required** (§5). |

---

## 3. The renderer candidates (verified 2026-07-21)

Three add-ons actually *render* existing splat PLYs in Blender. (Two others that
keep coming up — SkySplat and Gauss Cannon — are splat-*generation* / camera-path
utilities, not renderers, so they are out of scope here. Blender's own native
splat support is a design task only, not shipped — see the table.)

| Add-on | Price / License | Blender | How it renders | Degree-3 color? | Real count ceiling | Camera-anim render | Fit for us |
|---|---|---|---|---|---|---|---|
| **KIRI 3DGS Render** v5.0.0 (2026-06-05) | **Free**, Apache-2.0 | 4.2–5.1 (a "quick, untested" 5.2 patch exists) | Each gaussian → a mesh face driven by Geometry Nodes; renders in **real Cycles *and* EEVEE** | **Yes**, degree-3 with an SH-degree + diffuse-only toggle | **~2–3 M comfortable** per its own guidance ("Blender doesn't handle large data well"; recommends camera-cull + working on isolated parts); has an "Import as Points" proxy mode for big files | Yes ("Render Animation", image sequences) | **Best beauty** (true path-traced Cycles, real lighting/compositing/DoF/motion-blur, full color) but **lowest count ceiling** |
| **SplatForge** v (Blender 4.0+) | **$49 one-time** (Superhive) | 4.0+ | Custom **GLSL shader overlay** (OpenGL/Vulkan). Compatible *alongside* EEVEE/Cycles but the **splats are not lit by the scene** | **Yes**, degree 3 (SH-degree dropdown) | **~16 M / scene, then crashes** (the author's own docs); **no** LOD / culling / streaming; no motion-blur or DoF yet | Yes (Render Frame / Animation to file sequence) | **Highest documented ceiling + full color**, best for faithful splat *playback*; loses in-Blender lighting/DoF/MB (recover in comp) |
| **BlendSplat** (free) | **Free** (Gumroad) | 4.2+ (EEVEE-Next era) | Geometry Nodes + EEVEE, shader-side | **No — degree 2 only** (a view-dependent-color step-down on our degree-3 tiles) | "Millions" real-time, no stated hard cap | Yes | **Relighting + DoF + motion blur** in real-time EEVEE, free — but the degree-2 color is a quality compromise you'd have to approve |
| Blender **native** splat support | Free (future) | design task #159470, opened 2026-06-02 | Point-Cloud object + SH-degree property (planned) | Planned | — | — | **Not shipped.** Watch it; not usable now |

**The important contradiction, resolved:** SplatForge's store/review pages
advertise "up to 100 million splats, tested on RTX 4090, with LOD and culling."
Its **own documentation** (the author's doc repo) flatly says the opposite:
*"a limit of about 16 million Gaussians per scene. Adding more will cause a
crash,"* and describes **no** LOD, culling, or streaming. Primary source wins:
plan on **16 M**, not 100 M. Whether a newer build lifts that is an open
question the canary can settle cheaply before we ever spend the $49.

---

## 4. Recommended pipeline

**Recommendation: canary KIRI first (it is free, and it is the only path to
true Cycles beauty at full degree-3 color), and render the full flyaround as
per-shot region renders.** Reasoning:

1. Your stated goal is *rendering* a beautiful flyaround, and the Lidargraph
   sensibility rewards real path-traced light and compositing. **KIRI is the
   only candidate that renders splats through Cycles** — genuine ray-traced
   output, depth of field, motion blur, and compositing, at **full degree-3
   color**. That is the ceiling of quality among these tools.
2. It is **free and reputable** (Apache-2.0, actively maintained), so canarying
   it costs nothing but a GPU gap.
3. Its weakness is scale — each gaussian becomes a mesh face, so it is happiest
   around 2–3 M and needs its points-proxy mode or careful culling above that.
   That is *fine* for per-shot rendering, where a shot rarely needs many tiles
   sharp at once, and it is exactly what the canary measures.

**Paid options, surfaced per your standing rule (you buy, never me):**

- **SplatForge — $49 one-time** (Superhive / thefuture3d). Worth buying **if**
  the KIRI canary shows KIRI too heavy per tile *and* you want a fast, faithful
  splat-look flyaround rather than a path-traced one. It gives full degree-3
  color, the highest documented ceiling (~16 M/scene), and built-in camera
  animation export — at the cost of no in-Blender lighting/DoF/motion-blur
  (add those in compositing). Recommended **only after** the free canary tells
  us whether we even need it. Verify the 16-vs-100 M ceiling on our data before
  relying on the higher number.
- **Cloud GPU rental** (e.g. a 48 GB RTX A6000 at ~$0.33/hr, the rate this
  project already uses). Raises the memory wall so bigger shots — or, on an
  80 GB card, conceivably the whole 32 GB of gaussian data — fit in VRAM. **But
  it does not raise the add-on ceiling** (KIRI still chokes turning 135 M
  gaussians into 135 M mesh faces; SplatForge's own 16 M cap still applies).
  So renting a big card makes *larger shots* practical; it does **not** by
  itself deliver the literal all-36-at-once render. For a true single-scene
  city-scale splat render, the right tool is the game-engine path you already
  have (Unreal + NanoGS, principle 4), not a Blender add-on. Blender's strength
  here is the *rendered reel*, shot by shot.

**Install target: Blender 4.5 LTS** (free, blender.org). It is long-term
supported (to July 2027), sits squarely inside KIRI's supported range, and
covers SplatForge (4.0+) and BlendSplat (4.2+). Blender 5.1 is KIRI's own
stated favorite and is a fine alternative; avoid 5.2 for now (KIRI's 5.2 patch
is explicitly "not fully tested, likely buggy").

---

## 5. Memory arithmetic (the full worked numbers)

Render-side cost per gaussian at full degree-3 color ≈ 236 bytes (position,
rotation, scale, opacity, 48 color coefficients, fp32):

| Scope | Gaussians | VRAM (fp32, full color) | VRAM (fp16 color) |
|---|---|---|---|
| Smallest tile (`tile_0_5`) | 0.19 M | 0.04 GB | 0.03 GB |
| Average tile | 3.77 M | 0.89 GB | 0.60 GB |
| Largest tile (`tile_1_4`) | 7.90 M | 1.86 GB | 1.26 GB |
| **All 36** | **135.7 M** | **32.0 GB** | 21.6 GB |

- **All 36 at once needs ~32 GB — over the 24 GB card.** Half-precision color
  (~21.6 GB) *barely* fits the raw data but leaves nothing for sort buffers, the
  frame buffer, or Blender itself; it is not a real all-at-once path on 24 GB.
- On a **24 GB card, a shot's worth of tiles fits comfortably** — the raw data
  budget after leaving ~6 GB for overhead is ~76 M gaussians, i.e. roughly
  20 average tiles, *if the add-on could hold them*. In practice the add-on is
  the tighter limit (KIRI's mesh-per-gaussian; SplatForge's 16 M), so the real
  per-shot count is whatever the canary measures — likely a handful of tiles.
- **System RAM:** all-36 raw = 34 GB (fits 64 GB), but the add-on's in-memory
  expansion (KIRI 2–5×) pushes 68–170 GB — over 64 GB. Another reason all-36 is
  a crash, and another number the canary pins down per tile.
- **Linked collections / lazy loading:** yes, keep each tile as its own linked
  library (a natural 36-collection organization), *but be clear about what
  linking does and does not do* — Blender does **not** page linked data out of
  core. A linked-and-loaded collection is fully in RAM. So the lazy mechanism is
  **load a shot's subset → render → purge → next shot**, not "link all 36 and
  let culling sort it out." Culling cuts *draw* cost, never load/RAM cost.

---

## 6. The canary protocol (staged, not run)

**One full-count tile, measured end to end, before any fleet.** The canary is
already written and staged on Skychief in `C:\blender_lane\` (and mirrored in
this repo under `docs/blender_lane/`). It runs the moment the GPU has a gap —
**it will not run while training is in flight; it self-guards on that.**

**What runs, and the success criteria:**

1. **`run_canary.ps1`** (the Skychief wrapper):
   - **GPU-gap guard** — refuses to start unless the 3090 has ≥20 GB free and
     <15 % utilization, so it can never disturb a training run. (Right now it
     would correctly abort: only 4.7 GB free.)
   - **Blender locator** — finds a 4.5/5.1 install; if none, it prints the exact
     install step and stops (because only 3.0/3.4 are present today).
   - **A 2-second sampler** logging Blender's RAM and the card's VRAM to a CSV
     for the whole run — so we get *peak* RAM and *peak* VRAM, not a guess.
   - **A hard timeout kill** (default 25 min). If Blender hangs, it is killed
     cleanly and the log is kept — this is the crash-recovery path, deliberate,
     because crashing Blender on a too-big import is an expected canary outcome,
     not a failure of the run.
2. **`canary.py`** (headless inside Blender): installs+enables the KIRI add-on
   from the staged zip, **prints the add-on's real operator names** (so the
   full pipeline script uses the true API, not a guess), imports one tile, frames
   an oblique aerial camera on it (an above-and-back drone vantage, matching how
   the set was flown — the "start inside the sweet spot" rule for an aerial
   capture), renders one 1080p frame, and writes a JSON report with the gaussian
   count and the import/render wall-times.

**Run it three times to map the curve** (all in a single GPU gap):

- `tile_0_5` (0.19 M) — proves the whole path end to end, trivially.
- `tile_3_2` (4.3 M, the obelisk pilot cell) — a representative average tile.
- `tile_1_4` (7.90 M) — the largest tile; the real stress test.

For each, once the GPU is free:

The 36 tiles live on Skychief at
`H:\2026 Files\26-002 Oakland Cemetery Splat\deliver\ue_tiles\` (verified —
`tile_1_4.ply` is 1.87 GiB there). So:

```
powershell -NoProfile -ExecutionPolicy Bypass -File C:\blender_lane\run_canary.ps1 `
    -Tile "H:\2026 Files\26-002 Oakland Cemetery Splat\deliver\ue_tiles\tile_1_4.ply" `
    -Engine EEVEE -TimeoutMin 25
```

then repeat with `-Engine CYCLES` for a path-traced frame.

**What "canary passed" means (state up front):** the largest tile imports
without crashing, peak RAM stays safely under 64 GB, peak VRAM under ~22 GB, the
viewport is interactive enough to camera-animate, and *both* an EEVEE and a
Cycles frame render out looking like the cemetery. The three timings + two peak
figures become the anchors that size §7. If even the largest single tile blows
past RAM/VRAM in KIRI, that is the signal to (a) use KIRI's points-proxy for
placement + Cycles only for final, or (b) buy and canary SplatForge, or (c) rent
a bigger card — decided by the numbers, brought to you.

**Crash-recovery, concretely:** the wrapper's timeout-kill means a runaway
import ends as a killed process + a full log, never a wedged machine or a stuck
GPU allocation. Because the canary runs `--factory-startup` and writes only into
its own output folder, a crash leaves nothing to clean up. If Blender itself
segfaults on import, the exit code and the last log line tell us at which
gaussian count it died — which *is* the measurement we want.

---

## 7. Scaling to the full 36 tiles

Once the canary gives real per-tile RAM/VRAM/time anchors, the full flyaround
renders as **per-shot region jobs**, each at full count and full color:

1. **Author the camera path** for the whole flyaround (in Blender, or import the
   Unreal path). This is the one artistic step.
2. **Cut it into shots** (a few seconds each). For every shot, compute which
   tiles the camera frustum crosses over that shot's frames, plus a one-cell
   margin, using the tiles' known grid cells (derive placement from the file
   name per the README rule, never by centroid-guessing).
3. **Cap the tiles per shot at the canary-measured ceiling.** If a shot needs
   more tiles than fit, either split the shot, or load the *distant* tiles at a
   reduced *color* degree (degree-1 or flat) while the near tiles stay full
   degree-3 — a per-frame, non-destructive color LOD you approve once, not a
   decimation of any tile.
4. **Render each shot** in its own headless Blender process (load subset →
   render frames → purge → exit), so memory is fully reclaimed between shots and
   one shot crashing never takes the others down. These shot jobs are
   independent — they queue behind training on the 3090 and run in GPU gaps, or
   on a rented card, one at a time.
5. **Assemble** the shot frame-sequences into the final flyaround video.

This satisfies principle 5 to the letter that matters: **every rendered frame is
full quality and no tile's gaussians are ever decimated.** The only thing that
is never true — because the hardware cannot make it true — is all 135.7 M being
resident in one scene at one instant, which no frame of a flyaround ever needs.

**If you want the literal single-scene all-resident render anyway:** it needs a
card with ≥48 GB (for the ~32 GB of data) *and* a renderer that can hold 135 M
gaussians — which current Blender add-ons cannot. That combination points away
from Blender to the Unreal/NanoGS path you already have for the "one seamless
world" goal (principle 4). Blender's role is the beautiful *rendered reel*,
which the per-shot approach delivers at full quality. If you'd still like me to
price a specific big cloud card and prove the ceiling on it, say so and I'll
scope it as its own guarded, metered canary.

---

## 8. Open risks

- **KIRI's real per-tile ceiling on 24 GB is unmeasured.** Its own guidance
  (~2–3 M comfortable, mesh-per-gaussian) suggests even a 4–8 M tile may need
  the points-proxy or Cycles-only-for-final path. The canary settles it. *This
  is the single biggest unknown and the reason the canary exists.*
- **SplatForge's 16 M-vs-100 M ceiling** is an unresolved primary-source-vs-
  marketing contradiction. Do not pay the $49 on the marketing number; verify on
  our data first.
- **BlendSplat is degree-2 color** — using it means accepting a view-dependent-
  color step-down on degree-3 tiles. Flagged for your call, not chosen silently.
- **Headless add-on operators.** These add-ons are GUI-first; their import
  operators *should* work in background mode, but the canary is written to
  discover and log the real operator names and fail loudly (not silently) if an
  operator needs GUI context — so we learn the true API on the first cheap run.
- **Cycles and splats.** KIRI renders splats *as mesh* into Cycles, so a Cycles
  frame is a faithful-but-not-identical rendering of the raster splat look;
  EEVEE/shader tools match the native superspl.at look more literally. Which
  reads better is an eye judgment (yours) once the canary produces one of each.
- **The 5.2 question.** If you prefer to stay on the current Blender 5.2 LTS,
  KIRI only offers its "untested, likely buggy" 5.2 patch (also staged). 4.5 LTS
  or 5.1 avoids that entirely; recommended.
- **Skychief's wired link + clock** — standard project gotchas; use the login
  `Joel PC Login`, push scripts don't fight quoting, and the GPU must be free
  before the canary. All already handled in the staged scripts.

---

## 9. Sources (accessed 2026-07-21)

- KIRI 3DGS Render — GitHub `Kiri-Innovation/3dgs-render-blender-addon`
  (releases v5.0.0, README, `Blender_version_notes.txt`); product page
  `kiriengine.app/3d-tools/3dgs-render`.
- SplatForge — author docs `github.com/metropolik/splat_forge_doc` &
  `splatforge.cloud` (the 16 M ceiling, no-LOD, GLSL-overlay facts); store
  `superhivemarket.com/products/splatforge` and review `thefuture3d.com`
  (the $49 price and the contradicted 100 M claim).
- BlendSplat — `soerensc.gumroad.com/l/BlendSplat`, radiancefields.com,
  blenderartists.org thread (degree-2, relight/DoF/MB, EEVEE).
- SkySplat / Gauss Cannon — skysplat.org, `github.com/warpgatelabs/gauss-cannon`
  (confirmed generation/utility tools, not renderers).
- Blender native splat design task — `projects.blender.org/blender/blender/issues/159470`.
- Blender versions — blender.org/download/lts (5.2 LTS current 2026-07-14; 4.5
  LTS to 2027; 5.1 Mar 2026).
- Tile counts/format, Skychief specs — measured live from the PLY headers and a
  read-only Skychief probe, 2026-07-21 (this repo).

---

## 10. Lead's review note (Fable, 2026-07-21)

Reviewed in full; arithmetic re-derived and confirmed. One forward-looking
correction: this plan's counts are measured on the CURRENT (v1) tiles. The
final reel renders the REBUILT (v2, combined-solve) tiles, which the pilot
measured at ~1.27x the in-cell gaussian count (4.52M -> 5.71M on the pilot
cell). Projected v2 fused total ≈ 175M — the per-shot design is unaffected
(it scales per tile), the all-at-once verdict only strengthens, and the
canary's per-tile anchors should be read with a ~30% growth margin when
sizing v2 shots. Canary on v1 tiles remains valid and should run in the
first GPU gap as staged.
