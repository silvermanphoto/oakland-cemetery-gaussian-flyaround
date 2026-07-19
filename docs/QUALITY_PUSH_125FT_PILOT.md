# Quality push: the 125-foot integration (readable stones)

Joel's ask (2026-07-18), after seeing the native-8192 tiles: push through to
the next level — gravestone text that survives a close zoom, grass that reads
as grass. This is the record of why and how.

## Diagnosis — two different problems

**Gravestone text falling apart** is primarily a *source-resolution* limit, not
a training limit. At 300 ft, a ~1-inch engraved letter lands on roughly 1-2
pixels in the photograph. No gaussian count can reconstruct detail the pixels
never held. Fix = more source resolution first, density second.

**Grass looking splatty** has a real floor: a grass blade (~1-3 mm) is below the
ground sample distance even at 125 ft (~0.6 cm/px). Aerial capture never
resolved individual blades. More density makes the lawn read as fine texture at
walking distance; at nose-to-the-lawn zoom it stays blobs. Accepted limit —
density is aimed at the stones.

## The unlock — footage already shot

`H:\2023 Files\23-002 Oakland Cemetery\01.27.23_Oakland_Ortho_125ft Model\
11.16.22 Master Photoset for 125ft Ortho\Color Graded JPEGs use these` —
**3,319 frames, DJI Zenmuse P1, 8192x5460 (44.7 MP), flown 125 ft** (11-16-22).
Same physical camera and lens as the 300-ft obliques (12-22-22), both bare
winter light. 125 ft is 2.4x closer than 300 ft => ~2.4x linear ground detail,
~6x the pixels on any given inscription.

- 300-ft **obliques** supply the vertical headstone *faces* (nadir only sees
  tops).
- 125-ft **nadir** supplies razor detail on ledger stones, paths, walls,
  everything flat and top-engraved.
- Combined, both altitudes and both angles in one solve.

## The three levers, ranked by impact

1. **Add the 125-ft set to the solve** (the big one) — 6,589 frames, one
   coordinate frame.
2. **More gaussian density where the new detail now exists** — higher cap +
   more iterations, so the added sharpness is actually represented.
3. **Newest LichtFeld** — check the Supporter portal for a build allowing a
   higher stable ceiling than 12M (policy: check before every train).

## Plan (pilot-first, then commit)

1. **Combined solve** — new RealityScan scene, add both image folders, single
   shared Zenmuse P1 calibration, align all 6,589, export COLMAP + undistort to
   a NEW dir (`...\2026 RealityScan Splat\combined_300_125\`). v1 solve
   untouched. Recipe: `run_align_combined.cmd` (mirrors the proven
   `align_scene.cmd`). GPU-heavy; runs when the v1 queue is paused.
2. **Pilot tile = `tile_2_4`** (CORRECTED 2026-07-19 — the 6×6 partition of the
   combined solve auto-picked its densest interior cell, which is tile_2_4, not
   the tile_2_3 first penciled in; 462 cameras see it, both altitudes). Train
   FRESH from the combined solve's own sparse points (not continue — a 300-ft
   continue would anchor to coarse detail): `mrnf`, sh3, native 8192px,
   `--enable-mip`.
   **Density reality check (2026-07-19, learned by crashing):** the original
   cap-20M/iter-40k spec does NOT fit the 3090 at native 8192 — cap 18M ran the
   24 GB card out of memory at 22.7 GB, cap 14M at 18.4 GB; even cap 12M (the
   v1-proven setting) failed on THIS tile's larger combined working set. Native
   8192 for the pilot therefore runs on a rented 48 GB cloud card, two variants:
   **cap 12M / iter 20k** (matched to v1 — isolates the source-resolution
   variable) and **cap 18M / iter 20k** (density headroom). The 3090's ceiling
   at native 8192 is ~12M gaussians — sizing table, not a guess.
   **Altitude note:** the drone's own capture folders name the low pass
   "Oakland150ft-nadir" — the flight was likely 150 ft, not the 125 ft the later
   project folders say. Detail multiplier ~2× linear (~4× pixels on a stone),
   not 2.4×. Doc title kept for continuity.
3. **Judge** — crop+prune+SOG+publish, side-by-side vs v1 `tile_2_3`. Joel
   decides before the full 36-tile re-run commits days of GPU.

## Decisions locked

- Fresh train from the combined solve, not continue-train (reverses the earlier
  continue-train plan — justified: the 125-ft data is the whole point, and
  continuing from a 300-ft tile would anchor the coarse detail we're beating).
- v1 native-8192 queue is paused safely (only when no LichtFeld trainer is
  running — never mid-CUDA) and resumed after the pilot; its tiles stay the
  honest "before" and an interim native-8192 refresh for the live scenes.
- Pilot cell tile_2_3; density dials cap 20M / iter 40k as the first attempt.
