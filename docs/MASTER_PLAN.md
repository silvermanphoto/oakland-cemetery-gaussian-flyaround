# Oakland Cemetery — Nine-Tile Gaussian-Splat Master Plan

**Target:** the highest-quality achievable 3D Gaussian-splat reconstruction of Oakland Cemetery (Atlanta, GA), ~48 acres, delivered to superspl.at as **nine dense tiles + one fused master**, with **zero floaters/artifacts** and **incredibly resolved detail** as the overriding priority.

**Inputs (verified ground truth):** 3,270 color-graded JPEGs, 8192×5460 px (44.7 MP), DJI "300 ft Smart Oblique" orbiting mission, 134.7 GB, one flat folder. Pose: one global RealityScan 2.2 solve → COLMAP text + undistorted images, single shared world frame, forced single shared intrinsics. Trainer: LichtFeld Studio v0.5.3 (CUDA 3DGS) on one RTX 3090 (24 GB), Windows ("Skychief"), tiles train sequentially.

**This document is the single source of truth.** It supersedes the individual research and design notes it was synthesized from. Where a research note and a review lens disagreed, the resolution adopted here is the binding one, and the reasoning is recorded in **§12, "How reviewer risks were addressed."**

---

## 1. Executive summary

The reconstruction is built in one continuous pipeline whose non-negotiable spine is: **pose quality → coverage-correct tiling → per-tile dense training → layered floater elimination with gates at every step → crop-then-concatenate fusion → dual-track delivery.** Every design choice is subordinated to two artist requirements in strict order: **(1) zero floaters/artifacts, then (2) maximum resolved detail.** Speed is the last constraint, spent only where it does not cost detail or cleanliness.

Six decisions define this plan and each resolves a reviewer objection that would otherwise have sunk the naive approach:

1. **Supervision resolution defaults to 3840 px, not 5472 px.** Output detail is bounded by the per-tile Gaussian *count* (the cap), not by supervision pixels beyond it. 5472 px roughly doubles per-iteration cost for detail a fixed 3-M cap largely cannot represent, and it is the single biggest budget risk. We hold 3840 px, spend the freed compute on Gaussian count and iterations, and reserve 5472/8192 px for **one** optional "hero" tile only. A **hard tile-1 pre-commit timing gate** vetoes any resolution the 9-tile budget cannot afford.

2. **Local-origin, gravity-up (Z-up) export is mandatory, not optional.** GPS priors stay ON during alignment (they keep 3,270 frames in one component and fix scale + gravity), but the solve is exported/transformed to a small local origin with gravity = +Z **before** any tiling. This protects float32 precision (in both training convergence *and* fusion) and makes the 3×3 grid slice a true horizontal plane.

3. **Tiles are trained "wide, cropped narrow," with the out-of-cell problem masked out.** Each tile is initialized from a generous expanded-cell SfM cloud, and every training frame carries a **unified ignore-mask** (sky ∪ transient objects ∪ out-of-cell footprint) so pixels the tile is not responsible for never reward a Gaussian. This is the same mask pass that kills sky floaters and moving people/cars.

4. **Seams are routed through low-content lanes, then measured before commitment.** The 3×3 boundaries are content-balanced and snapped onto paths/lawns (away from monuments and tree crowns), the training apron is 20 %, crops are half-open, and a **two-tile mini-merge co-registration gate** measures the actual seam offset before the remaining seven tiles are launched. A 3×3 grid has **12 edge-seams + 4 four-tile quad-junctions = 16 seam loci**, all inspected.

5. **The dense master never touches the browser.** A 3.5–4.5 GB master PLY cannot be imported into the SuperSplat web editor (a ~1 GB PLY already exhausts the tab). All human floater cleanup happens **per tile, before merge**; the master's only web form is a locally pre-decimated ~3–4 M-Gaussian SOG; the dense master ships download-only (CloudCompare / standalone LichtFeld `.html`).

6. **Acceptance is judged from the ground, not just from orbit.** The "no floaters" test adds an **eye-level interior metric** (authored path cameras, mid-air-Gaussian counting) as the binding gate, because the out-of-bounds stray test is blind to the canopy/mid-air fuzz that lives *inside* the scene bounds — exactly where a treed cemetery floaters.

### Timeline

| Phase | Work | Wall-clock | GPU? |
|---|---|---|---|
| **0** | Pre-flight + environment hardening | 1–2 h | no |
| **1** | Alignment re-run (tuned) + gate + local Z-up export | 4–10 h | yes (align) |
| **2** | Preprocessing: masks (sky+transient), footprint masks, depth maps, image pre-resize, partition | 8–16 h | yes (segmentation/depth) |
| **3** | Partition build (scripts) | <1 h | no |
| **4** | Pilot: most-treed tile bake-off + full timing tile + neighbor + two-tile gate → commit profile | 6–10 h | yes |
| **5** | Production: remaining 7 tiles, resumable queue | 20–35 h | yes |
| **6–8** | Per-tile floater surgery, crop, merge, decimate, SOG | 4–8 h | partial |
| **9** | superspl.at delivery (human does login/publish) | 2–4 h + human | no |

**Training core (pilot + nine tiles) fits the accepted 1–2 day continuous GPU window at the calibrated 3840 px profile (~26–45 h).** Honest end-to-end including front-loaded preprocessing and delivery is **~3–4 days**. This is stated plainly because the reviewers correctly flagged that "nine maximal tiles in 1–2 days" is only true for the *training* clock — preprocessing (re-align, masks, depth) also needs the one GPU and serializes ahead of training.

---

## 2. Conventions, paths, and machine facts

All work runs on **Skychief** (RTX 3090, Windows), driven over SSH from the Mac. Connection: `ssh "Joel PC Login@192.168.50.109"` (login name has spaces; passwordless via the Mac key; the remote shell is **PowerShell**). Push files with `scp local "Joel PC Login@192.168.50.109:C:/path"`; pull with base64-through-ssh. For any non-trivial command, **write a `.ps1`/`.py` locally and run it as a file** rather than fighting nested SSH quoting.

Data lives under the year/sequence rule: **`H:\2026 Files\26-0NN Oakland Cemetery Splat\`** (take the next free sequence number under `H:\2026 Files\`, or ask). The working root below is abbreviated `OAK = H:\2026 Files\26-0NN Oakland Cemetery Splat`.

```
OAK\
  raw\                      # the 3,270 source JPEGs (134.7 GB), read-only
  align\                    # RealityScan project + reports
  global\
    sparse\0\               # cameras.txt images.txt points3D.txt (LOCAL Z-up)
    undistorted\            # RealityScan undistorted images (shared by all tiles)
    transform.json          # the ONE recenter+gravity transform (pinned)
  masks\
    sky_transient\          # global per-frame sky∪transient ignore masks
  depth\                    # Depth-Anything-V2 per-frame maps (treed tiles)
  resized\tile_gx_gy\       # per-tile frames pre-resized to --max-width
  tiles\tile_gx_gy\
    sparse\0\               # per-tile cameras/images/points3D
    masks\                  # unified ignore = sky∪transient∪out-of-footprint
    images -> ..\..\global\undistorted   # junction, so 134 GB lives once
    crop_aabb.json          # tight half-open core-cell box
  out\tile_gx_gy\           # trained PLY + checkpoints + eval renders
  deliver\
    tiles_dense\  tiles_web\  master_dense.ply  master_web.sog
  logs\
```

**Naming of the nine tiles by compass cell** (for human-readable deliverables): `NW N NE / W C E / SW S SE`, mapped from grid `(gx,gy)` with `gx∈{0,1,2}` = W→E and `gy∈{0,1,2}` = S→N.

**LichtFeld exe:** `C:\LidargraphCapture\lichtfeld\app\bin\LichtFeld-Studio.exe`. **Per the LichtFeld update policy, run `C:\LidargraphCapture\lichtfeld\check_update.cmd` and install any newer release before the first training run.**

---

## STAGE 0 — Pre-flight and environment hardening

A 9-tile batch is a multi-day unattended run on Windows. Harden it before spending a single GPU-hour, or a Windows Update reboot at tile 6 restarts the batch and an unbounded densification OOM at hour 4 wastes a tile.

**0.1 — Stay-awake, no-reboot, no-watchdog.**
- Disable sleep/hibernate for the run window: `powercfg /change standby-timeout-ac 0` and `powercfg /change hibernate-timeout-ac 0`.
- Pause Windows Update for the window (Settings → Windows Update → Pause), and set active hours; a forced restart mid-batch is the highest-probability catastrophe.
- **Raise the GPU driver TDR delay** so long 20 MP CUDA kernels are not killed as "hung." Set `HKLM\System\CurrentControlSet\Control\GraphicsDrivers\TdrDelay = 60` (DWORD, seconds) and `TdrDdiDelay = 60`, then reboot once before the batch. (A TDR at high resolution is a real, silent tile-killer.)

**0.2 — Thermal/power headroom.** Confirm the 3090 holds sustained 100 % load without throttling: run a 15-minute `nvidia-smi dmon` capture under a stress kernel and verify clocks are stable and temps < ~83 °C. A multi-day pinned run silently inflates wall-clock if it thermal-throttles. If marginal, cap the power limit (`nvidia-smi -pl <watts>`) to trade a little speed for stable clocks.

**0.3 — Disk.** Verify free space on the fast NVMe for: `global\undistorted` (undistorted set), `resized\` (per-tile downsized frames), `out\` (dense PLYs, ~0.35–0.5 GB/tile + checkpoints), and `deliver\`. Budget ~200–300 GB working headroom.

**0.4 — Tooling present.** `python` (3.10+ with numpy/scipy/plyfile/opencv/pillow), Node + `@playcanvas/splat-transform` (`npm i -g @playcanvas/splat-transform`), `3dgsconverter` (pip), CloudCompare, and the segmentation/depth environments (Stage 2). **On Skychief, bare `python` may be Python 2 — call the correct interpreter explicitly.**

**0.5 — Resumable-queue + watcher scaffolding.** Create the queue driver (§Stage 5) now and confirm it correctly *skips a tile whose output already exists*, so a reboot resumes at the next tile, never tile 1. Arm a local harness-tracked watcher on the Mac that re-launches the queue on unexpected exit (the project's "no idle waiting" discipline).

**Gate 0:** sleep/reboot disabled, TDR raised + rebooted, thermals verified stable, disk headroom confirmed, all tools resolve, queue skip-logic tested on a dummy output. Only then proceed.

---

## STAGE 1 — Alignment: keep-or-re-run decision, with measurable gates

> **Pose error IS the floater problem.** This is the project's own hard-won lesson (v1 haze traced to bad odometry poses; real SfM fixed it) and it is echoed by the aerial-3DGS literature ([StableGS](https://arxiv.org/html/2503.18458v1), [SparseGS](https://arxiv.org/pdf/2312.00206), [ARSGaussian](https://arxiv.org/pdf/2412.18380)). No LichtFeld flag recovers detail a weak solve never captured, and a loose solve floaters **every** tile. Alignment on the 3090 is single-digit hours — trivial insurance against a multi-day training batch.

### 1.1 Read the current default solve's three numbers first

The existing solve uses the **generic default recipe carried over from a 591-frame low-res video job**. Its cap of `sfmMaxFeaturesPerImage=40000` is only ~0.9 k features/megapixel on a 44.7 MP frame — it can *pass a connectivity gate while under-sampling the tie-point structure the artist is paying for.* Pull from its report: **(a) component count + fraction of 3,270 in the largest component, (b) % registered, (c) mean reprojection error (px),** and run the visual check in §1.4.

### 1.2 Keep-default gate (skip the re-run) — ALL must hold

| Metric | Keep-default threshold |
|---|---|
| Components | Exactly 1 (or one dominant holding ≥ 99 % of 3,270) |
| % registered | ≥ 95 % |
| Mean reprojection error | ≤ 1.0 px |
| Visual coverage | Points sit on headstones/walls/trunks; no thin coverage in dense areas or at future seams |

**Even if all four pass, prefer the tuned re-align for this detail-max, zero-floater deliverable** — the default's low feature cap leaves resolvable detail on the table. Keep the default *only* if the 1–2 day budget is genuinely at risk. **Recommended default action: run the tuned re-align (§1.3).**

### 1.3 The tuned re-align (PRIMARY path)

**PRE-FLIGHT (30 s, mandatory):** RealityScan 2.2 CLI tokens drift between builds. Run `RealityScan.exe -help` on the installed exe and confirm every `-set` key, `-selectMaximalComponent`, and `-exportRegistration` against the live build. The authoritative references are the [key/value table](https://rshelp.capturingreality.com/en-US/tutorials/setkeyvaluetable.htm) and the [command list](https://rshelp.capturingreality.com/en-US/tutorials/commandline_1.htm). Launching a multi-hour align on an unverified token wastes hours.

```bat
RealityScan.exe -headless ^
  -addFolder "%OAK%\raw" ^
  -set "sfmMaxFeaturesPerImage=100000" ^
  -set "sfmMaxFeaturesPerMpx=20000" ^
  -set "sfmPreselectorFeatures=40000" ^
  -set "sfmDetectorSensitivity=High" ^
  -set "sfmImageDownscaleFactor=1" ^
  -set "sfmImagesOverlap=Medium" ^
  -set "sfmDistortionModel=Brown4" ^
  -set "sfmEnableCameraPrior=true" ^
  -set "appIgnoreExifGPS=false" ^
  -set "appGroupCalibrationByExif=false" ^
  -selectAllImages ^
  -setConstantCalibrationGroups ^
  -align ^
  -selectMaximalComponent ^
  -exportRegistration "%OAK%\align\registration.csv" ^
  -save "%OAK%\align\oakland_align.rcproj"
```

Why the load-bearing settings ([RealityScan align settings](https://rshelp.capturingreality.com/en-US/appbasics/alignsettings.htm)):
- **`sfmMaxFeaturesPerImage=100000`** — on a 44.7 MP frame this is the *binding* cap; it lifts effective density from ~0.9 k to ~2.2 k features/Mpx (the detail-max sweet spot for headstones/ironwork). `sfmMaxFeaturesPerMpx=20000` is deliberately generous so the per-image cap governs.
- **`sfmDetectorSensitivity=High`, NOT Ultra.** Clean color-graded JPEGs are well-textured, so High extracts more *real* features; **Ultra fabricates false tie-points on repetitive headstone rows / brick / ironwork / canopy**, causing false matches and drift. Ultra is a failure-only escalation (§1.6). (Two general research threads suggested Ultra; the dedicated alignment research overrules them — High.)
- **`sfmImageDownscaleFactor=1`** — full res; any downscale discards the exact detail the whole job optimizes for.
- **`-setConstantCalibrationGroups` + `appGroupCalibrationByExif=false`** — one physical DJI camera → one forced shared-intrinsics group; identical intrinsics across all nine tiles.
- **GPS priors ON but LEFT LOOSE** (default ~10/10/20 m, soft). Non-RTK GPS is a *soft* constraint that keeps 3,270 frames in one component over 48 acres and fixes scale + gravity-up. **Never tighten prior accuracy to force meter-level positions — it warps the bundle and adds drift.**

### 1.4 GO/NO-GO gate (run the instant alignment finishes)

**Connectivity passing is necessary but NOT sufficient.** Pull the three metrics *and* do the visual check.

**NO-GO — re-align (escalate, §1.6) if ANY hold:** > 1 meaningful component; < 95 % registered; mean reprojection > 1.5 px (hard fail > 2.0 px); visibly thin/missing coverage in dense headstone or tree areas, or along any future 3×3 seam.

**Accept for a detail-max deliverable:** 1 component, ≥ 99 % registered (aim ~100 %), mean reprojection ≤ ~1.0 px, clean coverage in dense zones and at seams. **Record component count, % registered, and mean reprojection into this plan's run log as acceptance evidence before ANY LichtFeld GPU time.** Never train on unvalidated poses. Keep RealityScan's internal *max feature reprojection error* at its documented ≤ 3 px tie-point ceiling (distinct from the mean reprojection error above — do not confuse them).

**Visual coverage check:** project the sparse `points3D` into 8–10 sample images spanning the site; points must sit *on* headstones/walls/trunks, and coverage must not be visibly thin in the densest headstone areas or at the future seam lines.

### 1.5 COLMAP export + the coordinate-frame fix (do NOT skip)

Export the accepted solve to **COLMAP text** (`cameras.txt`, `images.txt`, `points3D.txt`) **+ undistorted images** into `OAK\global\`. Also export `registration.csv` (camera centers) for fast seam-line placement.

**1.5a — Verify a single shared camera line.** After undistortion, COLMAP-format exports frequently emit a PINHOLE/SIMPLE_PINHOLE camera **per image** even when params are identical, which breaks the "copy `cameras.txt` verbatim" tiling step. Check: if `cameras.txt` has N>1 lines, confirm all PARAMS are byte-identical, then **canonicalize** — rewrite to a single `CAMERA_ID` and remap every `images.txt` `CAMERA_ID` reference to it. Pin the canonical `cameras.txt`.

**1.5b — Local origin + gravity-up (mandatory, primary path).** GPS-on export can produce **georeferenced UTM/ECEF coordinates in the millions of meters**; 3DGS stores positions as **float32**, which loses precision at that magnitude and (i) blurs/stalls position gradients during *training*, and (ii) misregisters tiles at *fusion*. In ECEF, no axis is even "up," which silently breaks the horizontal 3×3 slice. **Make local Z-up export the primary instruction:**

1. Inspect the first lines of `points3D.txt`. If coordinates are **site-local** (extent < ~10 km, small values) *and* Z is gravity-up → proceed unchanged.
2. Otherwise compute **ONE rigid transform** `T = R·(x − c)`: recenter to the point-cloud centroid `c`, and rotate `R` so gravity = **+Z**. Recover gravity by RANSAC-fitting the dominant ground plane to the SfM points (or from the GPS-prior up direction), then align its normal to +Z. Apply `T` **identically** to `points3D`, all camera poses in `images.txt`, and record `T` in `global\transform.json`. This one transform is reused for every tile, every crop AABB, the SfM reference clouds used for pruning, and the SuperSplat upright bake — **never recomputed per tile.**
3. **Plumb test:** render/inspect a known vertical (an obelisk, a mausoleum wall) and confirm it is vertical in the transformed frame. Confirm coordinate magnitudes are now small (float32-clean).

**Gate 1:** accepted solve metrics recorded; single canonical `cameras.txt`; coordinates local + Z-up verified by the plumb test; `transform.json` pinned. The dense `points3D.txt` is now both the **training init seed** *and* the **fine floater-surgery reference** (the coarse public USGS aerial LiDAR is bare-earth/building-tops only — used **strictly** as a ground-plane/bounds prior downstream, never for mid-air surgery).

### 1.6 Escalation ladder (only if the tuned re-align still fails Gate 1)

Apply in order, re-running Gate 1 after each: (1) `sfmImagesOverlap=High`; (2) features → `sfmMaxFeaturesPerImage=120000`, `sfmPreselectorFeatures=60000`; (3) `sfmDetectorSensitivity=Ultra` (last resort — accept false-tie-point risk); (4) manual component bridging (disable all, enable images near the seam, align the subset, re-enable) and verify any GPS-forced merge by eye.

---

## STAGE 2 — Preprocessing (front-loaded, before any tile trains)

Everything here is a one-time cost that must finish **before** training, because it competes for the same single GPU and, done inline, would stall the batch. Segmentation and depth run on downscaled frames; image pre-resize is I/O-bound.

### 2.1 Unified masks — sky ∪ transient (global, per frame)

Sky/background is the #1 aerial floater source (low-opacity Gaussians hover near cameras where depth is undefined); moving **people and cars over a multi-hour cemetery flight** are the #2–3 transient source that no sky mask catches. Generate **one ignore-mask per undistorted frame** covering **sky ∪ person ∪ car/vehicle**, using a semantic segmenter on ADE20K classes (SegFormer-B4/B5 or Mask2Former; [SegFormer](https://huggingface.co/docs/transformers/model_doc/segformer)) or SAM + text prompts. Write to `masks\sky_transient\<frame>.png` (255 = ignore).

- Run the segmenter on frames downscaled to ~2048 px, then upscale masks to the training resolution; the mask contract is per-pixel, so **the mask must match the resolution LichtFeld trains on** (verify on the pilot — original vs internally-resized).
- **Validate on ~15 sample frames BEFORE trusting the batch:** obelisk tops, mausoleum roofs, and tree crowns must **not** be masked. A mask that clips structure punches permanent holes. Dilate transient masks slightly (people/cars have soft edges + shadows).

**Gate 2.1:** 15-frame visual check passes (zero structure clipped); mask count == frame count.

### 2.2 Depth maps for the treed tiles (Depth-Anything-V2)

Canopy parallax fuzz is the hardest floater class and the one cure that repels wrong-depth Gaussians is **depth supervision**. Precompute one monocular depth map per undistorted frame with **[Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2)** into `depth\<frame>.png`. These feed LichtFeld's scale-invariant `--depth-loss-mode pearson`. Generate for **all** frames (cheap to reuse); depth loss is applied selectively to the treed tiles and is **pilot-gated** (§4). This is a real GPU pass — budget it in Phase 2, off the training clock.

### 2.3 Per-tile image pre-resize (prevents an I/O-bound run)

At 3840 px a tile's ~600 frames cannot be RAM-cached, and re-decoding 44.7 MP JPEGs from the shared 134 GB folder on every random access makes the GPU wait on JPEG decode — which would silently make the tile-1 timing gate measure disk, not compute. **Pre-resize each tile's assigned frames ONCE to the chosen `--max-width` into `resized\tile_gx_gy\` on the fast NVMe** (after Stage 3 assigns cameras). Point each tile's `--images` at its pre-resized folder. Confirm GPU utilization stays > 90 % on the pilot; if it sags, the bottleneck is I/O and every batch estimate is meaningless until fixed.

### 2.4 Global exposure equalization (anti-seam appearance prep)

Because we train with per-tile appearance modeling **OFF** to avoid seam whack-a-mole (§4.4), harmonize exposure once, globally, across the flight: apply a single flight-wide exposure/tone equalization to the undistorted set (or confirm the existing color-grade already did this). This absorbs the exposure/white-balance drift that per-tile `--ppisp` would otherwise chase into phantom haze — but does it *once, globally*, so it cannot differ between neighboring tiles.

---

## STAGE 3 — The nine-tile partition (content-aware, coverage-correct)

Tile on the **reconstructed ground footprint (`points3D` XY), not the cameras.** The orbiting obliques sit ~91 m up and *outside* the site, so camera XY is a biased, inflated ring; the thing to subdivide is the surface.

### 3.1 Content-balanced, lane-snapped boundaries

Equal-thirds boundaries overload the dense center tile and slice through monuments and tree crowns. Instead:

1. Robust extent from the **2nd/98th percentile** of `points3D` X and Y (rejects far-field junk that would stretch the grid).
2. Place the two interior cut lines per axis near the **33rd and 67th percentiles of point count** (so each column/row carries ~equal Gaussian load), not at geometric thirds.
3. **Snap each cut line to the nearest low-density lane** within a ±10 % search window — the local minimum of point density, which corresponds to a **brick path or open lawn**. This routes seams away from mausoleums, obelisk rows, and retaining walls (continuous surfaces whose independent per-tile reconstruction would show a geometric step at a razor cut) and away from mature tree crowns (parallax-inconsistent canopy split between two tiles). Inspect the candidate lines against the SfM cloud and nudge by eye before committing.
4. **Outer perimeter of edge/corner tiles → ±∞** for both selection and crop, so the site edge is never clipped.

### 3.2 Camera assignment — visibility first, unioned, with a track-validity gate

Orbiting obliques image across boundaries; center-in-box assignment starves tile rims and breeds edge floaters. **Assign by visibility, unioned with two fallbacks**, against each tile's **expanded** cell (core + 20 % apron per side):

1. **Visibility vote (primary):** keep every camera that observes **≥ K = 60** SfM points whose XY lies inside the expanded cell (built from the `points3D` track lists).
2. **Camera-center-in-cell (secondary):** camera center `C = −Rᵀt` inside the expanded cell (catches close-standing frames).
3. **Ground-plane look-at footprint (tertiary):** project the optical axis to the ground plane and test the hit point (catches sky-heavy frames that vote weakly).

**Track-validity gate (mandatory — silent-failure guard):** before trusting the vote, verify `points3D.txt` **tracks are non-empty**, that track IMAGE_IDs are a subset of `images.txt` IDs, and that on a sample tile the visibility-selected set **materially exceeds** the center-in-box set. RealityScan filters low-accuracy points on export and has a history of COLMAP-export ID quirks; if tracks are thin/empty the vote silently collapses to center-only. If tracks are unusable, **promote the ground-plane look-at footprint to primary** rather than falling through to center-only. Never launch nine training runs on an unvalidated assignment.

**Apron = 20 % per side** (raised from 15 %). The apron must exceed the local inter-view baseline near a boundary so a seam Gaussian is co-observed by cameras assigned to *both* neighbors — that is what makes the seam well-constrained instead of starved. 20 % also buys margin for the geometric-seam concern; it costs only redundant compute on shared ground, which the core-crop discards.

**Min-views guard:** every tile must reach **≥ 300** assigned frames (expect ~500–1000 with the union; center tile highest). A tile below 300 auto-widens (apron 0.20 → 0.25, then K 60 → 40); if still short, it signals a genuine coverage hole (a poorly-flown corner) → **inspect that cell's cameras rather than lowering the guard further.**

### 3.3 Build nine COLMAP sub-datasets (no image duplication)

For each tile write a tiny `sparse\0\`: **`cameras.txt` copied verbatim** (canonical single intrinsics), a subset **`images.txt`** (pose line kept, **second line blanked** so filtered POINT3D_IDs cannot trip strict loaders), and a **`points3D.txt` filtered to the expanded cell** (the SfM init seed). Junction `tiles\tile_gx_gy\images` → `global\undistorted` so the 134 GB lives once. Record each tile's **tight, half-open core AABB** to `crop_aabb.json` now, for the post-training crop.

**Half-open crop intervals `[x0, x1)`** so a shared boundary plane is owned by exactly one tile and exact-boundary Gaussians are never duplicated into both.

**Runnable partition script** (stock Python; operates on the LOCAL Z-up COLMAP text):

```python
import os, json, numpy as np
from collections import defaultdict

SPARSE   = r"OAK\global\sparse\0"
SHARED   = r"..\..\global\undistorted"
OUT      = r"OAK\tiles"
GRID     = 3
OVERLAP  = 0.20            # apron fraction of core cell width, per side
K_VOTE   = 60             # min SfM points-in-cell for a visibility vote
MIN_IMGS = 300
PLO, PHI = 2, 98
INF      = 1e12

def qvec2R(qw,qx,qy,qz):
    return np.array([
        [1-2*(qy*qy+qz*qz), 2*(qx*qy-qz*qw),   2*(qx*qz+qy*qw)],
        [2*(qx*qy+qz*qw),   1-2*(qx*qx+qz*qz), 2*(qy*qz-qx*qw)],
        [2*(qx*qz-qy*qw),   2*(qy*qz+qx*qw),   1-2*(qx*qx+qy*qy)]])

cam_txt = open(f"{SPARSE}/cameras.txt").read()   # single canonical intrinsics

imgs = {}
lines = [l for l in open(f"{SPARSE}/images.txt") if l.strip() and not l.startswith("#")]
for i in range(0, len(lines), 2):
    h = lines[i].split(); iid = int(h[0])
    qw,qx,qy,qz = map(float, h[1:5]); t = np.array(h[5:8], float)
    R = qvec2R(qw,qx,qy,qz); C = -R.T @ t; d = R.T @ np.array([0,0,1.])
    imgs[iid] = {"hdr": lines[i].rstrip("\n"), "C": C, "dir": d}

pid_xyz = {}; pid_imgs = defaultdict(set)
for l in open(f"{SPARSE}/points3D.txt"):
    if l.startswith("#") or not l.strip(): continue
    s = l.split(); pid = int(s[0]); pid_xyz[pid] = np.array(s[1:4], float)
    tr = s[8:]
    for j in range(0, len(tr), 2): pid_imgs[pid].add(int(tr[j]))

# --- TRACK-VALIDITY GATE ---
assert any(len(v) for v in pid_imgs.values()), "points3D tracks are empty -> promote look-at to primary"
assert set().union(*pid_imgs.values()) <= set(imgs), "track IMAGE_IDs not a subset of images.txt IDs"

P = np.array(list(pid_xyz.values()))
px = np.sort(P[:,0]); py = np.sort(P[:,1])
p2  = np.array([np.percentile(P[:,0],PLO),  np.percentile(P[:,1],PLO)])
p98 = np.array([np.percentile(P[:,0],PHI),  np.percentile(P[:,1],PHI)])
z_ground = np.median(P[:,2])

def content_cuts(sorted_axis, lo, hi):
    # cut near 33rd/67th COUNT percentiles, then snap to nearest low-density lane
    core = sorted_axis[(sorted_axis>=lo)&(sorted_axis<=hi)]
    cand = [np.percentile(core,33.3), np.percentile(core,66.7)]
    span = hi-lo
    snapped=[]
    for c in cand:
        w0,w1 = c-0.10*span, c+0.10*span             # +/-10% search window
        win = core[(core>=w0)&(core<=w1)]
        # local density minimum via coarse histogram
        hgram,edges = np.histogram(win, bins=20)
        lane = 0.5*(edges[hgram.argmin()]+edges[hgram.argmin()+1]) if len(win) else c
        snapped.append(lane)
    return sorted(snapped)

cx = content_cuts(px, p2[0], p98[0])   # 2 vertical cut lines (W|C, C|E)
cy = content_cuts(py, p2[1], p98[1])   # 2 horizontal cut lines (S|C, C|N)
xedges = [-INF, cx[0], cx[1], INF]
yedges = [-INF, cy[0], cy[1], INF]

def in_box(pt, x0,x1,y0,y1): return (x0<=pt[0]<x1) and (y0<=pt[1]<y1)   # half-open

for gy in range(GRID):
  for gx in range(GRID):
    cx0,cx1 = xedges[gx], xedges[gx+1]
    cy0,cy1 = yedges[gy], yedges[gy+1]
    fw = (cx1-cx0) if abs(cx1-cx0)<INF else (p98[0]-p2[0])/GRID
    fh = (cy1-cy0) if abs(cy1-cy0)<INF else (p98[1]-p2[1])/GRID
    apron, k = OVERLAP, K_VOTE
    while True:
        ex0,ex1 = cx0-apron*fw, cx1+apron*fw
        ey0,ey1 = cy0-apron*fh, cy1+apron*fh
        keep = [pid for pid,xyz in pid_xyz.items() if in_box(xyz,ex0,ex1,ey0,ey1)]
        vote = defaultdict(int)
        for pid in keep:
            for iid in pid_imgs[pid]: vote[iid]+=1
        sel = {iid for iid,v in vote.items() if v>=k}
        for iid,dd in imgs.items():
            if in_box(dd["C"],ex0,ex1,ey0,ey1): sel.add(iid); continue
            if dd["dir"][2] < -1e-3:
                s_=(z_ground-dd["C"][2])/dd["dir"][2]; hit=dd["C"]+s_*dd["dir"]
                if s_>0 and in_box(hit,ex0,ex1,ey0,ey1): sel.add(iid)
        if len(sel)>=MIN_IMGS or (apron>=0.25 and k<=40): break
        if apron<0.25: apron=0.25
        else:          k=40

    td = f"{OUT}/tile_{gx}_{gy}/sparse/0"; os.makedirs(td, exist_ok=True)
    open(f"{td}/cameras.txt","w").write(cam_txt)
    with open(f"{td}/images.txt","w") as f:
        for iid in sorted(sel): f.write(imgs[iid]["hdr"]+"\n\n")     # blank line 2
    with open(f"{td}/points3D.txt","w") as f:
        for pid in keep:
            x,y,z = pid_xyz[pid]; f.write(f"{pid} {x} {y} {z} 128 128 128 0\n")
    json.dump({"x0":cx0,"y0":cy0,"z0":-INF,"x1":cx1,"y1":cy1,"z1":INF},
              open(f"{OUT}/tile_{gx}_{gy}/crop_aabb.json","w"))
    ln = f"{OUT}/tile_{gx}_{gy}/images"
    if not os.path.exists(ln): os.symlink(SHARED, ln)  # Windows: use a directory junction
    print(f"tile {gx}_{gy}: images={len(sel)} pts={len(keep)} apron={apron} K={k}")
```

### 3.4 Per-tile unified ignore-masks (the out-of-cell cure)

For each `(tile, frame)`, build the **unified ignore-mask = sky ∪ transient ∪ out-of-expanded-cell footprint**, into `tiles\tile_gx_gy\masks\<frame>.png`:

- Start from the global `masks\sky_transient\<frame>.png`.
- **Add the out-of-cell footprint:** project the tile's expanded-cell SfM points into the frame, take their dilated 2D convex hull as the "keep" region, and mark everything outside it as ignore. This stops a frame assigned to tile A (that also images tile-B headstones) from spawning wrong-depth Gaussians in empty air to explain far pixels its init cloud does not cover — the floaters that land *inside* the core cell and survive the spatial crop. Pair with the generous expanded-cell init so any kept out-of-cell pixel still has real-depth points to explain it.
- **Escalation (pilot-gated):** if inside-cell floaters persist despite the footprint mask, train tiles with a **frozen coarse global background splat** (`--add-splat=<coarse_global> --freeze --exclude-export`) so far content is absorbed by fixed real-depth geometry. Build the coarse global once (~1 h, whole site, low cap ~0.5 M, low res). This is belt-and-suspenders, not the default.

**Gate 3:** every tile ≥ 300 frames; aprons overlap; seam lines sit on paths/lawns; `crop_aabb.json` + junction present per tile; unified masks generated and spot-checked (structure not clipped, out-of-cell correctly ignored).

---

## STAGE 4 — Pilot tile gate (before committing the other eight)

Pick the **most-treed / most-complex cell** as the pilot so the gate stresses the worst case (canopy is where budget, VRAM peaks, and floaters all bite hardest). This stage converts every "unverified" assumption into a measured fact and **vetoes the batch profile if the numbers don't fit.**

### 4.1 On-device verifications (the unverified assumptions, settled here)

Run these on the pilot, at reduced iterations where noted, and do not launch the eight until each is answered:
- **Flag/token names:** confirm the exact LichtFeld v0.5.3 tokens — `--images` vs an inferred `images/` under `--data-path`; `--max-cap`, `--strategy` values `mrnf`/`igs+`/`mcmc`; `--mask-mode` semantics (`ignore` = "pixels contribute no loss"); `--add-splat`/`--freeze`/`--exclude-export`; and later `splat-transform` `-B`/`-V`/`-d`/`-H` and `LichtFeld convert`. Read them from `--help`, don't assume.
- **Does `--max-cap` actually bound `mrnf`/`igs+`?** It is documented primarily for `mcmc`. Watch the live Gaussian count approach 3 M on the HUD; if the edge-aware strategy does **not** stop at the cap, a canopy tile can densify unbounded and OOM. If unbounded → fall back to `mcmc` (which enforces the cap) on canopy-heavy tiles, or throttle via lower `--max-width`.
- **PEAK VRAM through a post-densification burst.** The real 24 GB OOM driver is the rasterizer's transient buffers (per-tile Gaussian lists, sorted keys, per-pixel blend + backward gradient state), which spike during a densification burst at full-res backward, not at steady state. Watch **peak**, not average, through at least one burst past ~15–30 k. Keep a hard **4 GB reserve** below 24 GB. If peak comes within ~2 GB of the ceiling on the canopy tile, drop that tile one resolution rung rather than gambling on the burst.
- **I/O:** GPU utilization stays > 90 % on the pre-resized set (else fix I/O before batch).
- **Mask contract:** masks align to what LichtFeld actually trains on (original vs internally-resized) — verify a rendered eval frame respects the mask.
- **`images.txt` blank line-2 ingests cleanly** (no strict-loader track error). If it errors, fall back to remapping observations to surviving POINT3D_IDs.

### 4.2 Strategy bake-off (~15 k iters each)

A/B **`mrnf` vs `igs+` vs `mcmc`** on the pilot, scored by (a) held-out PSNR **and** (b) a by-eye **canopy-fuzz + floater count from the authored eye-level interior views** (§10), not just an exterior orbit. Expectations and the resolution of the "edge-aware may worsen canopy" concern:
- **`mrnf`** (project-proven Walk B strategy; Sobel edge-map + SSIM error-map densification) — places Gaussians on true structure, suppresses planar stipple. Default expectation.
- **`igs+`** ([ImprovedGS+](https://arxiv.org/html/2603.08661v1); Long-Axis-Split + Canny/Laplacian NMS importance) — claims +quality, ~13 % fewer Gaussians, ~27 % faster vs MCMC at equal budget; most detail-aggressive on stone lettering/ironwork.
- **`mcmc`** ([3DGS-MCMC](https://arxiv.org/html/2404.09591v1), [ref impl](https://github.com/ubc-vision/3dgs-mcmc)) — bounded cap + opacity-L1 + relocation; the **floater-conservative** option and the honest choice for a **canopy-heavy** tile where edge-aware densification risks pouring Gaussians into leaves. Allow **per-tile strategy**: edge-aware for stone-dominated tiles, `mcmc`+opacity-reg for canopy-dominated ones, decided by the pilot's canopy-vs-stone measurement (below).

### 4.3 Canopy-vs-stone allocation + lettering legibility (the 3×3-sufficiency check)

The 3×3 grid is an artist-fixed decision, but a 3-M cap can be eaten by foliage and starve the headstone lettering the artist actually prizes. Measure it on the pilot: build a distance-to-SfM histogram split by class (canopy vs stone, using the segmentation masks projected to 3D), and **inspect headstone lettering + ironwork legibility on held-out views.** Outcomes:
- Lettering legible, canopy not runaway → commit 3×3 as-is.
- Stone under-resolved / canopy dominates the budget → the honest levers, in order: (1) per-tile `--max-cap` scaling with in-cell stone-point count; (2) `mcmc`+opacity-reg on canopy tiles to free budget for stone; (3) **present the artist a go/no-go on sub-dividing only the single densest cell** into 2×2 internal training units that are merged back into that one cell's deliverable (this preserves the "nine tiles" deliverable while buying lettering-grade density where it's needed). Do not silently accept under-resolved stone.

### 4.4 Appearance policy (anti-seam, decided here)

Train **`--ppisp` and `--bilateral-grid` OFF** for all master-destined tiles. Rationale: per-tile appearance models are learned independently and bake different exposure per tile, producing a visible color/brightness **step at the 12 seams** even when geometry aligns — a "no artifacts" violation on the master, and a whack-a-mole to fix (re-fitting one boundary shifts a tile's global appearance and breaks its others). The input JPEGs are color-graded and Stage 2.4 applies one global exposure equalization, so per-tile appearance modeling is largely redundant. **Pilot check:** A/B the pilot with appearance OFF; if unacceptable mid-air haze appears (residual exposure drift), escalate to a **single uniform `--bilateral-grid` ON across all tiles** (spatially smooth, least seam-prone) rather than per-tile `--ppisp`. The standalone tile deliverables use the same appearance-OFF training — one set of tiles serves both tracks.

### 4.5 Iteration count (resolving the plateau contradiction)

The "115 k plateau" from the project's prior overnight run was **Brush (wgpu/Metal)**, a different trainer with a different LR schedule — **do not import it into LichtFeld.** LichtFeld's on-device proven range is the **Walk B recipe: 30 k–60 k**, and its LR/densification schedule scales to the `--iter` you give (so there is no fixed "dip at 30 k" when 30 k *is* the total). Anchor **`--iter 30000`** as the calibrated baseline; on the pilot, read held-out PSNR every 5 k and **confirm the plateau for THIS trainer.** Raise to 45–60 k only if the pilot's curve shows meaningful detail still accruing and the 9-tile budget affords it. If a longer schedule is chosen and it exhibits a post-restart dip, ensure the stop lands on the **recovered** side of it — never inside the trough.

### 4.6 Timing → batch-profile pre-commit gate (HARD)

Run the chosen strategy **full-length once** on the pilot and record wall-clock + peak VRAM. **Pre-commit rule:** `9 × (measured per-tile hours) ≤ ~40 h` (leaving margin inside a 48 h window, and accounting for the pilot itself). If it overruns → step resolution down (`5472 → 4096 → 3840 → 3072`) or iterations down until it fits. If the pilot finishes **< ~2.7 h** with ≥ 6 GB VRAM headroom → the profile may be pushed up (raise `--max-cap` toward 3.5–4 M, or promote one hero tile to 5472/8192 px). **Do not set 5472 px as the batch default on paper** — 3840 px is the default; 5472 px is earned only by a fast pilot.

### 4.7 Two-tile co-registration mini-merge gate (before the other seven)

Make the pilot's **immediate neighbor** the second tile trained. Then crop both to their core cells, concatenate, and **measure the seam**: pick a feature straddling the boundary (a curb, a path edge, a wall) and quantify the geometric offset across the cut in CloudCompare; render across the seam for a density ridge / crack / color step. This turns "will nine independent tiles line up?" from faith into a ~$2 test. **Only launch the remaining seven if the measured seam offset is within tolerance and no ridge/step appears.** If a geometric step appears, escalate: verify the transform frame is shared, widen the apron, and if needed co-optimize the seam pair with the neighbor loaded frozen (`--add-splat=<neighbor> --freeze --exclude-export`). If a color step appears, it's the appearance policy — confirm §4.4 held.

**Gate 4:** flags/token/cap/VRAM/I-O/mask/ingest verified; strategy committed (possibly per-tile); appearance policy fixed; `--iter` calibrated; batch profile passes the timing pre-commit; two-tile seam within tolerance. **This is the point of no return into the batch.**

---

## STAGE 5 — Production training (remaining seven tiles)

### 5.1 The committed per-tile command (3840 px baseline)

```bat
C:\LidargraphCapture\lichtfeld\app\bin\LichtFeld-Studio.exe ^
  --headless --train ^
  --data-path  "%OAK%\tiles\tile_%GX%_%GY%" ^
  --images     "%OAK%\resized\tile_%GX%_%GY%" ^
  --output-path "%OAK%\out\tile_%GX%_%GY%" ^
  --output-name oakland_tile_%GX%_%GY% ^
  --strategy %STRATEGY% ^        REM mrnf (stone) or mcmc (canopy), per pilot
  --iter 30000 ^                 REM pilot-calibrated (up to 45-60k if it fits)
  --max-cap 3000000 ^           REM pilot may raise to 3.5-4M if cap honored + VRAM headroom
  --sh-degree 3 ^
  --max-width 3840 ^            REM default; 5472/8192 hero-tile only
  -r 1 ^
  --enable-mip ^
  --centralize off ^           REM keep the single shared world frame (fusion = concat)
  --min-opacity 0.005 ^        REM low floor: protect thin ironwork/lettering
  --mask-mode ignore ^         REM unified sky∪transient∪out-of-footprint mask
  --use-depth-loss --depth-loss-mode pearson --depth-loss-weight 0.05 ^  REM treed tiles, pilot-gated
  --eval --test-every 20 ^
  --save-checkpoint-every 10000
```

**Flags deliberately OFF, and why (not oversights):**
- **`--enable-sparsity` OFF** — its ADMM prune removes ~60 % of Gaussians (default `--prune-ratio 0.6`), the opposite of "maximally dense," and it deletes the ironwork/lettering the artist prizes. Floater removal is done by masking + edge-aware strategy + the *targeted* Stage-6 prunes. Web-lightening is a **separate export** (Stage 8), never a prune of the dense master.
- **`--ppisp` / `--bilateral-grid` OFF** — anti-seam policy (§4.4); global exposure equalization handles drift once.
- **`--random` OFF** — init from the dense SfM cloud (SFM-init beat lidar-cloud init on held-out PSNR in the project's prior run).

Appearance/mask/depth switches follow the pilot's decisions; a **stone-dominated** tile may run `--strategy mrnf` without depth loss, a **canopy-dominated** tile `--strategy mcmc --opacity-reg` (verify the exact opacity-reg flag on the pilot) with depth loss ON.

### 5.2 Resumable queue + early-abort

Drive the eight (nine incl. pilot re-runs) as a **PowerShell queue that skips any tile whose `out\tile_*` already contains a finished PLY**, so a reboot resumes at the next tile. Save an in-tile checkpoint every 10 k iters so a mid-tile crash resumes near the failure, not from zero. Arm the Mac-side watcher to re-launch the queue on unexpected exit.

- **Early-abort gate:** if a tile's first held-out eval (~5–10 k) sits **> ~2 dB below** its neighbors, **kill and re-check its camera assignment/coverage** — a weak eval is almost always a starved-edge selection problem, not a trainer problem. Do not ride a doomed tile 3+ hours.
- **VRAM hard-kill:** arm a per-tile watchdog that kills + restarts at the next OOM ladder rung if VRAM crosses the reserve line, so an over-densifying canopy tile is caught, not left to die at hour 4.

### 5.3 OOM fallback ladder (cap is cut LAST — it buys detail)

1. `--max-width 3840 → 3072`
2. `-r 1 → -r 2` (half-res supervision)
3. only then `--max-cap 3,000,000 → 2,500,000 → 2,000,000`

If OOM strikes mid-run, restart the tile at the next rung from its last checkpoint; do not try to resume a crashed job in place.

### 5.4 Per-tile time estimate

At 3840 px / 30 k on the 3090 the planning estimate is **~2.5–4.5 h/tile (unverified until the pilot measures it)**; nine tiles ≈ **~26–40 h**. A single hero tile at 5472 px adds ~5–8 h. These are the numbers the §4.6 gate confirms or vetoes — they are not committed on paper.

---

## STAGE 6 — Floater elimination protocol (ordered, gated)

Governing rule: **make floaters not-form (Stages 1–5 upstream + in-training controls), then remove survivors with targeted, evidence-gated prunes — never a global density cut.** The four floater sources, in impact order, and where each is already cured:

| # | Source | Primary cure (stage) | Gate |
|---|---|---|---|
| 1 | Sky / background | unified ignore-mask, `--mask-mode ignore` (2.1/5.1) | zero opaque Gaussians above skyline (§10.2) |
| 2 | Exposure/WB drift | global exposure equalization + appearance-OFF (2.4/4.4) | no mid-air haze between structures; no seam color step |
| 3 | Canopy parallax / transients | transient mask + depth loss + `mcmc` on canopy tiles (2.1/2.2/5.1) | canopy fuzz gone from eye-level interior view (§10.6) |
| 4 | Thin far-field haze | out-of-footprint mask + Stage-6 prune (3.4/6.1) | far-field p99 distance-to-SfM small (§10.3) |

### 6.1 Post-training targeted prune (per tile, before crop, on the DENSE PLY)

Thresholds are expressed against **ONE global scale reference** — the master-AABB diagonal (or a true metric recovered by measuring a known headstone width in CloudCompare) — **not each tile's own diagonal**, so cleaning is identical across all nine. Run the low end first, **inspect ironwork/lettering/twigs on held-out views**, then tighten only if floaters remain.

```python
import numpy as np
from plyfile import PlyData, PlyElement
from scipy.spatial import cKDTree
def sigmoid(a): return 1/(1+np.exp(-a))

def prune(inp, outp, sfm_xyz, GLOBAL_DIAG,
          opacity_min=0.12, scale_frac=0.01, dist_frac=0.005, sor_k=20, sor_std=2.0):
    v = PlyData.read(inp)['vertex'].data
    xyz = np.stack([v['x'],v['y'],v['z']],1)
    keep  = sigmoid(v['opacity']) >= opacity_min                     # (1) translucent haze
    smax  = np.exp(np.stack([v['scale_0'],v['scale_1'],v['scale_2']],1)).max(1)
    keep &= smax < scale_frac * GLOBAL_DIAG                          # (2) giant smears
    d,_   = cKDTree(sfm_xyz).query(xyz)
    keep &= d < dist_frac * GLOBAL_DIAG                              # (3) far from any real surface
    kt = cKDTree(xyz); dd,_ = kt.query(xyz, k=sor_k+1)              # (4) statistical outliers
    m  = dd[:,1:].mean(1); keep &= m < m.mean() + sor_std*m.std()
    PlyData([PlyElement.describe(v[keep],'vertex')]).write(outp)
    print(inp, 'kept', round(float(keep.mean()),4))
```

Starting thresholds (tune, don't blindly apply): opacity `sigmoid ≥ 0.12`; scale `> 1 % of global diag` removed; distance-to-SfM `> 0.5 % of global diag` removed; SOR k=20 / std 2.0. No-code alternative: `3dgsconverter -i tile.ply -o clean.ply -f 3dgs --min_opacity 12 --density_sensitivity 0.6 --sor_intensity 5` ([3dgsconverter](https://github.com/francescofugazzi/3dgsconverter)).

**Note on the distance prune's weakness under canopy:** near sparse foliage SfM points, real canopy fuzz can sit close to a point and pass criterion 3 — which is exactly why the depth-loss + transient mask (upstream) and the **eye-level interior gate** (§10.6) are the real canopy backstops, not this distance prune alone.

**Gate 6 (per criterion):** kept-fraction reasonable (~0.6–0.9; a criterion removing a *large* fraction is over-tuned — back off); **removed-mass p90 distance-to-SfM is large** (removed Gaussians provably sit far from any surface — the project's proven surgery signature); **detail-retention:** held-out PSNR after prune within **~0.3–0.5 dB** of pre-prune (loosened from an unrealistic 0.15 dB), and ironwork/lettering/twigs **still present and sharp** on held-out views. If they thin, loosen `opacity_min`/`dist_frac` and re-run.

### 6.2 Workflow order (archival integrity)

Do automated + any manual cleanup **per tile, FIRST**, then build the master by concatenating the **already-cleaned** tiles. Never merge dirty tiles and re-clean the master by hand — the master and the nine tile scenes would disagree.

---

## STAGE 7 — Crop and fuse

### 7.1 Crop each cleaned tile to its half-open core cell

```bat
splat-transform "%OAK%\out\tile_%GX%_%GY%.clean.ply" ^
  -B x0,y0,z0,x1,y1,z1 ^                      REM from crop_aabb.json (full Z; ±INF on perimeter sides)
  "%OAK%\deliver\tiles_dense\tile_%GX%_%GY%.ply"
```

`-B` = filter-box, removes Gaussians outside the box ([splat-transform](https://github.com/playcanvas/splat-transform)). Use the tile's **full Z extent** so tall obelisks/trees are not clipped; only X/Y are the cell boundary. Half-open ownership (Stage 3) guarantees no boundary duplication. For XY-only crop keeping all Z regardless of point range, use the numpy `plyfile` mask variant instead of `-B`. **Spot-check tall/steep seams in 3D** (terraced sections): confirm a low tile's tall tree or a high tile's foundation doesn't cross a neighbor's column at a height where both hold content.

### 7.2 Concatenate into the dense archival master

```bat
splat-transform ^
  "%OAK%\deliver\tiles_dense\tile_0_0.ply" ... "%OAK%\deliver\tiles_dense\tile_2_2.ply" ^
  "%OAK%\deliver\master_dense.ply"
```

Pure concatenation — all nine already share the one local Z-up frame, so **no ICP/transform** (the single shared RealityScan solve is what makes this seamless; this is the payoff of `--centralize off` everywhere). `master_dense.ply` (~14–20 M Gaussians, ~3.5–4.5 GB) is the **archival master of record** — kept on the PC / R2, **never uploaded to the web viewer.**

### 7.3 Seam gate on the dense master (all 16 loci)

Render across each of the **12 edge-seams + 4 quad-junctions.** Require **no density ridge, no crack, no color/brightness step.** A density ridge → apron wasn't cropped (re-crop to tight AABB). A color step → appearance divergence (should not occur under §4.4; if it does, the fix is at training, not a post-hoc recolor). The 4 quad-junctions (four independently-trained tiles meeting at a point) are the hardest case — inspect all four explicitly.

---

## STAGE 8 — Build the web master (count reduction, then SOG)

The web viewer's bottleneck is the **per-frame depth sort over every Gaussian**, not file size — so the master needs **count reduction**, not just byte compression. Desktop discrete GPUs are comfortable to ~4 M @ 30–60 fps.

Reduce count by **importance-weighted** culling (drop translucent haze + tiny Gaussians first), then decimate toward ~3–4 M, then export SOG:

```bat
splat-transform "%OAK%\deliver\master_dense.ply" -V opacity,gt,0.15 "%OAK%\deliver\master_pruned.ply"
splat-transform "%OAK%\deliver\master_pruned.ply" -d 25% "%OAK%\deliver\master_web.sog"
```

`-V` = filter-value (comparators lt/lte/gt/gte/eq/neq, on opacity and scale_*); `-d` = decimate to a percentage. **Verify the `-d` token on the pilot;** if absent, iterate opacity/scale `-V` thresholds until the count lands ≤ 4 M, then export SOG. Confirm the output count (`--info`, or reload in SuperSplat). A mild `-H 2` (keep two SH bands) is a cheap secondary size/memory lever; reserve `-H 0` (flat color) as a last resort (it flattens stone/foliage specularity). SOG is Morton-ordered, GPU-ready, ~10.5 B/Gaussian, full SH3 ([SOG format](https://developer.playcanvas.com/user-manual/gaussian-splatting/formats/sog/)); its in-browser decode needs WebGPU, but the published SuperSplat viewer auto-falls-back to WebGL, so keep a `.spz`/`.compressed.ply` backup only if targeting old browsers.

**Expected sizes** (pin from real Stage-5 counts): one core-cropped tile ~1.5–2.3 M → dense `.ply` ~350–540 MB, web `.sog` ~16–24 MB; master dense ~3.5–4.5 GB; **master web (decimated ~3–4 M) ~32–42 MB.**

---

## STAGE 9 — Delivery to superspl.at (ten scenes; human does login/publish)

**Two tracks.** Nine tiles = the detail deliverable (each ~2 M, web-fine, shipped **dense, unsparsified**); master = the overview (decimated web SOG + download-only dense archival). **The dense master never enters the browser editor** — a ~1 GB PLY already OOMs the SuperSplat tab ([issue #606](https://github.com/playcanvas/supersplat/issues/606)), and a 3.5–4.5 GB master cannot import, sweep, or publish there at all.

### 9.1 Per-tile web export + final human sweep (per tile, before any master step)

For each tile, convert the dense cropped PLY to a light web form first, then open in the editor:

```bat
splat-transform "%OAK%\deliver\tiles_dense\tile_%GX%_%GY%.ply" "%OAK%\deliver\tiles_web\tile_%GX%_%GY%.sog"
```

Open `tile_*.sog` in the SuperSplat editor ([editing](https://developer.playcanvas.com/user-manual/gaussian-splatting/editing/supersplat/editing-splats/)); use box/sphere/lasso + opacity/scale filters to delete any survivors the automated pass missed. **Archival-sync rule:** if the human deletes anything here, capture the deletion as a box/sphere region and **re-apply it programmatically to the dense `tile_*.ply`** (`splat-transform -B`/`-S`), so the dense archival tile stays byte-consistent with the swept web tile — then rebuild the master from the re-synced dense tiles. Do not let the only zero-floater copy be the lossy SOG.

### 9.2 Authored initial cameras (the "start inside the sweet spot" rule, adapted for aerial)

This is an **aerial orbital** capture — there is no ground-level walk path, so the project's "start inside the sweet spot" rule is adapted faithfully: the initial camera sits **on the oblique orbital shell the drone flew**, at mid-altitude, **upright** (gravity-up baked from `transform.json`), **framing a signature feature** (e.g., the Bell Tower / a notable obelisk cluster) — never outside the whole site looking at a haze-ball. Author one initial view per published scene. Separately author **eye-level interior test cameras** along the paths for the floater gate (§10.6) — these do not exist in the aerial set and must be hand-set.

### 9.3 Publish (human)

Per scene ([publishing](https://github.com/playcanvas/supersplat/wiki/Publishing-your-Splats-to-the-Web)): open superspl.at/editor, log in (Joel does the PlayCanvas + superspl.at login himself — **Claude never creates accounts or pays**), **Import** the scene's `.sog`, set the authored initial camera, **File → Publish**, fill Title (human name, e.g. "Oakland Cemetery — NW tile" / "Oakland Cemetery — Master (whole site)") + one-line Description, leave **Listed unchecked** (link-only, matching the unlisted-showcase convention), Publish, copy the URL. **Pre-convert to `.sog` locally first** so publish is fast and the master's count/SH are controlled — publishing a raw multi-GB PLY triggers client-side compression that has taken 11+ hours in the wild. Repeat for all nine tiles + the master = **ten scenes.**

**Human note to confirm before publishing:** free-tier PlayCanvas project/storage limits for ten scenes — verify the account tier supports ten published scenes.

### 9.4 Fallback ladder if the master is still too heavy

In order, stop at the first that renders smoothly: (1) tighten the count cut toward ~2.5–3 M (detail loss acceptable — the *tiles* carry detail); (2) strip SH to band 2 then 1; (3) a custom PlayCanvas LOD-streaming viewer hosted off-site (heavier lift, only if the artist insists on a near-full-density web master); (4) **ship the nine dense tiles as the primary web experience and the master as a download-only dense `.ply`/`.sog` / standalone LichtFeld `.html`** — the deliver-both requirement is still met, with the master as a download rather than a live scene.

### 9.5 Showcase

Collect the ten URLs into the project record and onto the published **joelsilverman.com/lidargraph-camera** showcase (per the 26-021 site runbook: cactus accent `#74c4a4`, Cormorant Garamond / Calluna Sans, full brand system — public pages never use the simple-report style; big files to R2 with CORS; preview branch then main). Project navigation = clickable previous/next thumbnails; all text concise and human.

---

## STAGE 10 — The "no floaters" acceptance test

A deliverable passes only when **all criteria hold, on each of the nine tiles AND the master.** Criteria 1–4 are programmatic; 5–8 are by-eye. The out-of-bounds test alone is explicitly **not sufficient** — it is blind to the mid-air/canopy fuzz that lives inside the scene bounds, which is exactly where a treed cemetery floaters.

1. **Out-of-bounds stray render.** Render 24 orbit views (every 15°) + 6 upward/horizon views against a **solid magenta `#FF00FF`** background (absent from the scene). Count Gaussians whose center lies outside the scene AABB expanded 5 %. **Pass:** 0 visible against magenta in any frame; out-of-bounds count < 0.01 % of total (none with `sigmoid(opacity) > 0.1`).
2. **Above-skyline.** On the 6 upward/horizon renders, **zero** Gaussians with `sigmoid(opacity) > 0.1` above the detected skyline (verifies the #1 sky source is dead).
3. **Distance-from-surface distribution.** Nearest-SfM-point distance p99 **< 0.5 % of the global diagonal** (essentially every surviving Gaussian on real geometry). Any tail beyond → back to Stage 6. (Weak under sparse canopy — paired with #6.)
4. **Detail retention.** Cleaned deliverable's held-out PSNR within **~0.3–0.5 dB** of the pre-Stage-6 tile — guards "no floaters" from silently becoming "no ironwork."
5. **Exterior-orbit by-eye.** Full 360° exterior orbit: no mid-air haze, no sky sheets, no orphan specks on flat surfaces.
6. **Interior (eye-level) by-eye + programmatic — THE BINDING GATE.** From authored eye-level path cameras (§9.2): programmatically count mid-air/unsupported Gaussians (alpha/depth-discontinuity islands, or high multi-view depth disagreement); require **zero floaters between structures, no canopy fuzz.** Ironwork, headstone lettering, and thin twigs still present and sharp.
7. **Seam gate.** All **12 edge-seams + 4 quad-junctions**: no density ridge, crack, or color step.
8. **View-consistency (specular popping).** On the interior orbit, no flickering/popping specular Gaussians (SH3 + very low `--min-opacity` on polished granite/ironwork can create view-dependent pops that read as artifacts though they aren't floaters).

**A deliverable failing any single criterion is not shippable** — trace the failure to its stage (sky→2.1/5.1, haze→2.4/4.4, canopy→2.2/5.1, far-field/mid-air→6, seam→7, popping→lower SH or raise min-opacity locally) and re-run from there.

---

## 12. How reviewer risks were addressed

Every **critical** and **high** risk from the three adversarial lenses, and the binding resolution:

### Lens 1 — Geometry, seams & tile consistency

| Risk | Resolution |
|---|---|
| Geometric seam step from independent per-tile training (razor-cut through continuous surfaces) | Seams **content-balanced and snapped to low-content lanes** (paths/lawns), away from monuments/crowns (§3.1); apron raised to **20 %** (§3.2); **half-open** crops (§3.3); **two-tile mini-merge measurement gate** before committing seven (§4.7); frozen-neighbor co-optimization as documented escalation. |
| Out-of-cell frame content seeds floaters INSIDE the core cell (crop can't remove) | **Train-wide, crop-narrow** + **unified ignore-mask including the out-of-expanded-cell footprint** (§3.4/5.1) so out-of-cell pixels reward no Gaussian; generous expanded-cell init; frozen coarse-global-background escalation. |
| Partition assumes gravity-aligned Z-up world RealityScan may not export | **Local-origin + gravity-up transform mandatory before tiling** (§1.5b): RANSAC ground-plane → rotate gravity to +Z, one shared `transform.json`, plumb-test verified; per-region ground handled by the visibility vote (ground-model-free). |
| No quantitative early co-registration gate before all nine | **Two-tile mini-merge gate** measures the actual seam offset in CloudCompare before the other seven launch (§4.7). |
| Equal-thirds ignores content density / slices objects | **Content-balanced boundaries + lane-snapping**, per-tile cap scaling, densest/most-treed cell is the pilot (§3.1/4.3). |
| Double-density band / inclusive crop bounds | **Half-open `[x0,x1)` ownership** (§3.3) — no boundary duplication. |
| Per-tile diagonal → inconsistent thresholds; manual master edits don't propagate | **One global scale reference** for all prune thresholds (§6.1); **clean tiles first, then concatenate** (§6.2); manual SuperSplat deletes re-applied to dense PLYs (§9.1). |
| *Missed:* seam topology miscounted | Corrected to **12 edge-seams + 4 quad-junctions = 16 loci**, all inspected (§7.3/10.7). |
| *Missed:* verify one shared camera line | **Canonicalization step** (§1.5a). |
| *Missed:* upright bake identical across all ten | One `transform.json` reused everywhere (§1.5b/9.2). |
| *Missed:* blank images.txt line-2 may trip loader | **Pilot ingest check** + remap fallback (§4.1). |

### Lens 2 — VRAM, compute budget & convergence

| Risk | Resolution |
|---|---|
| Budget under-estimated ~2–3× at 5472 px | **Default 3840 px**; **hard tile-1 timing pre-commit gate** (`9× measured ≤ ~40 h` else step down); 5472/8192 px hero-tile only (§4.6/1). |
| VRAM asserted from wrong number (param memory, not rasterizer transient peak) | **Measure PEAK VRAM through a post-densification burst on the pilot**, 4 GB reserve; OOM ladder cuts resolution before cap (§4.1/5.3). |
| `--max-cap` may not bound `mrnf`/`igs+` | **Verified on the pilot** by watching the count approach the cap; `mcmc` fallback if unbounded (§4.1). |
| Iterations contradict max detail (115 k plateau vs 50–55 k) | **115 k was Brush, not LichtFeld** — anchor LichtFeld's proven **30 k–60 k**, plateau confirmed on the pilot for THIS trainer; stop on the recovered side of any dip (§4.5). |
| Compute spent on resolution a fixed cap can't exploit | **Hold 3840 px, spend freed compute on count + iterations**; 5472 px hero-only (§1/4.6). |
| 3 M/tile may be binding; canopy eats it, starving lettering | **Canopy-vs-stone allocation measured on the pilot**; per-tile cap scaling, `mcmc` on canopy tiles, and an artist go/no-go to sub-divide only the densest cell (§4.3). |
| Dataset I/O makes the run CPU/disk-bound | **Pre-resize each tile's frames once to NVMe**; verify GPU util > 90 % on the pilot (§2.3/4.1). |
| Not crash-survivable (reboot/TDR/OOM) | **Stage 0 hardening** (no auto-reboot, TDR raised, thermal check) + **resumable skip-existing queue + 10 k checkpoints + watcher** (§0/5.2). |
| Max-dense vs zero-floaters tension in strategy | **Decided on the pilot** — read the settled count, judge detail by eye; per-tile strategy (§4.2/4.3). |
| Eval rendering unbudgeted time/VRAM at 20 MP | Eval at reduced frequency (every 5 k for the plateau read) counted in the pilot wall-clock (§4.6). |
| *Missed:* float32 UTM precision affects TRAINING convergence, not just fusion | Local-origin transform applied **before training** (§1.5b). |
| *Missed:* power/thermal for multi-day 3090 | **Thermal headroom check + optional power cap** (§0.2). |
| *Missed:* pilot cost not carved from budget | Pilot explicitly in the timeline and the `9×` pre-commit math (§1/4.6). |

### Lens 3 — Floater sufficiency & superspl.at deliverability

| Risk | Resolution |
|---|---|
| Canopy/transient under-cured; edge-aware may worsen canopy | **Transient mask (person/car) added to the mask pass**; **depth loss ON for treed tiles**; **`mcmc` A/B on the most-treed pilot scored from eye-level**; per-tile strategy (§2.1/2.2/4.2). |
| Dense master undeliverable through the browser editor | **Master never enters the editor**; per-tile cleanup before merge; master ships as pre-decimated SOG + download-only dense archival (§9/8). |
| Browser deletions don't propagate to dense PLY | **Automated-pruned dense PLY is the record of truth**; manual deletes re-applied programmatically to keep both in sync (§6.2/9.1). |
| GPS-on export breaks float32 + Z-up | **Local-origin Z-up export made primary**, with a hard pre-tiling magnitude + plumb check (§1.5b). |
| Visibility assignment depends on tracks that may be empty (silent) | **Track-validity gate**; promote look-at footprint to primary if tracks unusable (§3.2). |
| Verification gates false-pass (blind to inside-scene fuzz; aerial-only PSNR) | **Eye-level interior floater metric added as the binding gate**; authored path cameras; loosened PSNR tolerance (§10.6/10.4). |
| Budget covers only training | **Preprocessing front-loaded off the training clock**; honest ~3–4 day end-to-end stated (§1/2). |
| Per-tile appearance → 12 seams | **`--ppisp`/`--bilateral-grid` OFF for master-destined tiles** + one global exposure equalization; uniform bilateral-grid escalation only (§4.4/2.4). |
| `--max-cap` silently ignored → mid-run OOM | **Pilot cap-honoring check + per-tile VRAM hard-kill/checkpoint** (§4.1/5.2). |
| *Missed:* oblique-only weak eye-level coverage | Flagged; eye-level gate authored; **nadir set available to fold into ground/canopy-floor regions** if the interior gate fails (§9.2/10.6). |
| *Missed:* superspl.at initial camera must be authored | **Authored per scene**, aerial-adapted (§9.2). |
| *Missed:* specular popping | **View-consistency acceptance criterion** (§10.8). |
| *Missed:* free-tier scene limits | Human confirms account tier before publishing ten scenes (§9.3). |
| *Missed:* mask resolution contract | Verified on the pilot (§4.1). |
| *Missed:* metric thresholds | One global scale reference, optionally a real metric from a measured headstone width (§6.1). |

---

## 13. Final acceptance checklist (tied to artist requirements)

**Delivered artifacts**
- [ ] Nine **dense** tile PLYs (archival, record of truth) + nine web `.sog` tiles.
- [ ] One **dense** master PLY (download-only archival) + one decimated master `.sog` (web).
- [ ] Ten published superspl.at scenes (nine tiles + master), each **Unlisted**, each with an authored upright initial camera on the orbital shell framing a signature feature.
- [ ] Ten URLs collected + the joelsilverman.com/lidargraph-camera showcase updated (full brand system, cactus accent, previous/next thumbnail nav).

**Zero floaters/artifacts (hard requirement)** — Stage-10 acceptance test passes on **every** tile AND the master:
- [ ] Out-of-bounds stray render clean; zero above-skyline opaque Gaussians.
- [ ] Distance-to-SfM p99 within threshold; detail retained within ~0.3–0.5 dB.
- [ ] Exterior orbit clean; **eye-level interior view clean (binding)** — no mid-air/canopy fuzz.
- [ ] All 16 seam loci: no ridge, crack, or color step; no specular popping.

**Incredibly resolved detail (overriding priority)**
- [ ] Headstone lettering + ironwork legible on held-out views (pilot-measured; densest cell sub-divided if the artist approved it).
- [ ] Tiles shipped maximally dense (no sparsity prune on archival); master decimation contained to the overview only.

**Process integrity**
- [ ] Alignment gate metrics recorded before any GPU time; local Z-up frame verified.
- [ ] Tile-1 timing pre-commit gate passed; two-tile seam gate passed before batch.
- [ ] Data under `H:\2026 Files\26-0NN …`; work committed/pushed; no secrets/build-artifacts in git.
- [ ] Human performed all superspl.at login/publish/payment; Claude created no accounts and paid nothing.

---

## Appendix A — Open items requiring live-machine data (planning-only limits)

These cannot be settled from planning; they are the pilot/first-run reads this plan is built to gate on:
1. The current default solve's three gate metrics (component count, % registered, mean reprojection) — decides keep vs re-align.
2. Whether RealityScan's export is site-local or UTM/ECEF (decides if the §1.5b transform is applied).
3. Exact LichtFeld v0.5.3 + RealityScan 2.2 + splat-transform token spellings on the installed builds.
4. Whether `--max-cap` bounds `mrnf`/`igs+`; measured peak VRAM through a densification burst; real per-tile wall-clock; GPU utilization on the pre-resized set.
5. Canopy-vs-stone Gaussian allocation and headstone-lettering legibility at 3×3 / 3 M — decides whether the densest cell is sub-divided.
6. Whether 20 % apron closes all seams or a tile needs 25 % / frozen-neighbor co-optimization.
7. Whether the eye-level interior gate is satisfiable from oblique-only coverage or the nadir set must be folded into ground/canopy-floor regions.
