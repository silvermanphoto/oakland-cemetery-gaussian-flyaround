# Oakland Cemetery — Hyperreal Playable Splat Plan

**Goal:** push the existing nine-tile reconstruction to game-grade hyperrealism —
every gravestone individually readable where the source pixels allow it — and
deliver it as a walkable "open world" in Unreal Engine or Unity, with tiles
streaming in seamlessly. Continue from the trained model; do not start over.

**What we already have (the inheritance):** one global camera solve (all 3,270
frames, 100% registered), nine trained 12M-gaussian tiles (dense archival PLYs
on Skychief), a verified partition/crop/merge pipeline, and the proven
per-tile training recipe (mrnf, JPEG-on-NVMe feeding, 97% GPU).

---

## Why the current tiles don't read text — and what fixes it

Two ceilings bind today's tiles, in this order:

1. **Supervision resolution.** Training saw 3840-px downscales of the
   8192-px frames — the trainer literally never saw the letterforms you can
   read in the source. Fix: train at native (or 5472-px) supervision.
   LichtFeld v0.5.3 supports up to 8K supervision on this pipeline.
2. **Local gaussian density.** 12M gaussians over a ~290 m tile is superb at
   overview scale but thin at inscription scale. Fix: finer tiles — same 12M
   ceiling per tile, applied to a quarter (or ninth) of the ground area, so
   density per square meter multiplies by the subdivision factor.

A third ceiling to respect honestly: **the source pixels themselves.** At
300 ft the ground sampling is roughly 1–2 cm per pixel. Where you can read a
stone in the source photo, the splat can learn it; where the source is
borderline, no amount of training invents letters. The pilot's acceptance test
compares splat renders directly against source-photo crops of named stones so
we measure exactly this transfer.

---

## Stage 1 — Pilot: one sub-tile, continued training, native resolution

Pick a text-rich quarter of tile B2 (the obelisk sector). Then:

1. **Subdivide the partition** with the existing partition script at GRID=6
   (36 sub-tiles) — same global solve, same visibility rules, ~200–450 images
   per sub-tile. Nothing re-aligns; nothing retrains from zero.
2. **Continue-train, don't restart:** initialize from the parent tile's
   dense PLY cropped to the sub-tile's expanded bounds (`--init`), optionally
   loading the surrounding parent content frozen (`--add-splat --freeze
   --exclude-export`) so edges stay supported. Train `--strategy mrnf`,
   `--max-cap 12000000` (the proven safe ceiling), **`--max-width 5472`
   first, then a native-8192 A/B** on the same sub-tile.
3. **Feeding discipline:** re-encode the sub-tile's frames JPEG q95 to the
   NVMe at the chosen resolution (the PNG/CPU-decode trap cost 28× once).
4. **Gates measured on the pilot (the go/no-go for all 36):**
   - Legibility: render the same five named stones from splat and from source
     photos; letters that read in source must read in the render.
   - VRAM headroom through a densification burst at 5472/8192 px (12M fit in
     8.5 GB at 3840 px; expect roughly 12–16 GB at 5472; native 8192 is the
     risk case — if it overflows, 5472 is the production setting).
   - Wall-clock per sub-tile → honest total for 36.
   - Continued-vs-fresh check: one sub-tile trained from scratch as control,
     to confirm inheritance actually helps (it should converge much faster).

**Expected pilot cost:** roughly half a day including the A/B.

## Stage 2 — The one decision that could force retraining (assess, then decide)

The poses came from the default alignment recipe (feature budget tuned for
low-res video, ~0.9k features per megapixel). If the pilot's text is soft in a
way that looks like pose blur rather than resolution or density (double edges,
smearing on every stone in one direction), the fix is the tuned re-alignment
from the master plan (100k features/frame) — which produces new poses and
means retraining tiles against them. This is the only scenario that restarts
anything, and we only pay it if the pilot proves current poses are the
bottleneck. The pilot A/B makes this a measurement, not a guess.

## Stage 3 — Production: 36 sub-tiles (6×6), resumable queue

- Same queue machinery as the overnight run: skip-done markers, solo trainer
  on the GPU, prep staged ahead on NVMe, watcher with stall detection.
- Budget at 12M × 36 at 5472 px: expect roughly 2–3.5 h per sub-tile →
  **~3–5 days of continuous GPU**. (49 tiles at 7×7 is the same recipe and
  ~35% more hours; the pilot's numbers decide whether 36 or 49 is the right
  spend — beyond ~49 the returns fall below the source pixels' ceiling.)
- Yield: ~430M trained gaussians, ~200M+ in the cropped cores — a 4×
  density multiply over today, trained on 2× (or native) supervision.
- Each sub-tile gets the same finishing pass as today's tiles: crop to core,
  floater prune, verified bounds before anything ships.

## Stage 4 — LOD ladder and engine-ready export

For each sub-tile, export a three-step ladder with the existing transform
tooling (full / quarter / sixteenth density, plain concatenable PLYs, one
shared world frame, real meters — no per-tile scale tricks this time; the
engine handles navigation feel):

- **LOD0** full density (near-field, the readable-text experience)
- **LOD1** ~25% (mid-distance)
- **LOD2** ~6% (skyline/far)

Also export one whole-site LOD2 merge as the horizon backdrop.

## Stage 5 — The playable build (Unreal first, Unity as fallback)

- **Unreal Engine 5 + a 3DGS plugin** (current field: Volinga, XVERSE
  XV3DGS, Luma; pick after a one-day bake-off rendering our densest sub-tile
  at 60 fps target on the 3090). UE5's **World Partition** streams cells
  natively — each sub-tile becomes a cell asset; LOD swaps by distance; the
  shared world frame makes the seams invisible by construction, and we
  already proved seam-free crops at the current scale.
- **Unity fallback:** aras-p's UnityGaussianSplatting is the most mature
  open renderer; same tiling/LOD design applies.
- Player setup: walking character at eye level, collision from a coarse
  ground mesh (derivable from the SfM cloud), start position on the main
  avenue by the obelisk.
- Acceptance: walk from gate to obelisk reading stones along the way, 60 fps,
  no visible tile pops, no floaters at eye level.

## Stage 6 — Capture-gap honesty (optional future pass)

Wherever the pilot shows source pixels themselves are the limit (small
footstones, worn inscriptions), the durable fix is a supplemental
low-altitude or ground-level pass over those rows with the rig or drone,
merged into the same global frame via RealityScan registration. Flagged now
so expectations are set by physics, not hope.

---

## Cost and calendar (honest)

| Phase | GPU time | Calendar |
|---|---|---|
| Pilot sub-tile + A/B + control | ~4–6 h | half a day |
| (Only if poses prove weak: re-align + retrain baseline) | +8–14 h | +1 day |
| 36 sub-tiles production | ~70–125 h | 3–5 days unattended |
| LOD ladder + exports | ~6 h | overlaps |
| Engine bake-off + playable build | — | 1–2 days hands-on |

Disk: ~250–400 GB on the RAID for sub-tile outputs and LOD ladders.

## What I need from you

1. A go on the pilot (it's cheap and answers every open number).
2. Your engine preference — Unreal or Unity — or let the bake-off decide.
3. Five gravestones you want as the legibility benchmark (or I pick
   text-rich stones from the source set).
