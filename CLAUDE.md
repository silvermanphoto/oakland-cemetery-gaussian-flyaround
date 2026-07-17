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
  44.7MP DJI Inspire 2 JPEGs (8192×5460), 300 ft smart-oblique; 233 of them
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

## The hyperreal plan (docs/HYPERREAL_PLAN.md is the full text)

Continue-train the existing tiles — never restart: subdivide 3×3 → 6×6 (or
7×7), init each sub-tile from the parent's trained gaussians (`--init` from a
box-crop of `master_dense.ply`), retrain with `--strategy mrnf`, cap 12M,
supervision at 5472px (native-8192 A/B pending) → ~4× density on 2×+ detail.
Then LOD ladders per sub-tile and an Unreal Engine 5 World Partition build
(Unity aras-p renderer as fallback). Pilot = `tile_3_2` (obelisk cell).
Legibility gate: render vs source-photo crops of named stones — letters
readable in source must read in the splat.

## Hard-won rules that bind every job here

- Feed LichtFeld JPEG q95 from the PC's local NVMe (`C:\oak_resized6\`),
  never PNG, never the RAID (28× throughput difference; check the loader line).
- `--strategy mrnf` only — mcmc deadlocks at cap under driver 591.86.
- Never hard-kill a mid-CUDA trainer (unkillable VRAM zombie; reboot-only).
- splat-transform v3.0.0: `-t a,b,c` ⇒ (x−a, y−b, z+c); `-d` last action,
  .ply output only; verify output bounds via `--stats null` on the WRITTEN
  file before shipping. Do not pre-rotate for superspl.at (viewer expects
  trainer-native orientation).
- superspl.at republish: R2 public URL → page fetch → File → DataTransfer →
  input, select the scene by exact text, verify the "Replace the model for"
  string. Files >300 MiB: split into R2 parts, stitch with Blob([p1,p2]) in
  the page. `wrangler r2 object put` caps at 300 MiB.
- Windows unattended: scheduled tasks `-LogonType S4U`; no `Start-Transcript`;
  `py -3` never bare `python`; ASCII-only scripts; `${var}:` in PS strings.
- PC ↔ Mac: push via scp; pull via base64-over-ssh (spaced login breaks scp
  pulls). GPU sharing via `C:\LidargraphCapture\status\gpu_state.txt`.

## Git

Local repo; `upload/`, `gravestone_samples/`, `renders/` gitignored (large,
regenerable). Private GitHub remote under silvermanphoto pending Joel's
go-ahead (repo name suggestion: `jls-oakland-flyaround`). Never force-push;
never commit secrets or multi-GB binaries.
