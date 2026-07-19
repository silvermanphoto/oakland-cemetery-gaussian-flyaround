# Oakland tiles → Unreal: crop, then import — how to run + what's verified

**Project 26-029 · UE 5.8 · NanoGS plugin · authored 2026-07-17.**

Two scripts turn the raw trained tiles into a seamless, correctly-placed Unreal
scene. They run **in order**, and the split matters: the first is CPU-only and
can run the moment training frees the box; the second opens the editor and needs
the GPU.

1. **`export_ue_tiles.ps1`** (Skychief, PowerShell, **CPU-only**) — crops each
   finished raw tile down to its non-overlapping grid cell and writes one clean
   PLY per tile to `H:\...\deliver\ue_tiles\<tile>.ply`.
2. **`ue_import_tiles.py`** (Unreal Editor Python) — imports those cropped PLYs as
   NanoGS splat assets and drops one actor per tile at world origin / identity, so
   the tiles reassemble seamlessly.

---

## Why the crop step exists (the seam problem)

The raw tiles were trained with a ~20% apron: a tile spans ~326 m where its cell
is only ~143 m, so **adjacent tiles overlap**. Imported raw they would
double-cover every seam. The export box-filters each tile to its exact cell so the
36 tiles tessellate with **no double-coverage** — the same thing the web pipeline
did for the 3×3 set.

**A tile's cell is derived from its gaussian centroid, never its name.** The raw
`out8k` tile name does not map cleanly to grid position (e.g. `out8k tile_0_0`
sits in the high-X column, not where "0_0" implies). So the export computes each
tile's centroid (`splat-transform --stats` → mean x/z), finds which of the 36
half-open cells it falls in, and crops to that cell. The grid edges were verified
2026-07-17 two independent ways (both matching to 0.1 m): recomputing them from
the COLMAP sparse points with `partition6.py`'s percentile math, and reading the
`tiles6\*\crop_aabb.json` boxes the tiles were actually trained against. If any
centroid maps outside the grid, or two tiles map to the same cell, the export
**stops** rather than cropping to a wrong cell.

> **splat-transform quirk baked into the export:** `splat-transform -B`
> (v3.0.0) interprets its X box-corners in a **negated-X** frame relative to the
> file, so the export passes the X min/max as `(-x1, -x0)`. Z and Y pass through.
> The *written* geometry is clean (kept gaussians keep their true positions), so
> the import story below is unaffected. Verified empirically (2026-07-17); re-check
> if splat-transform is ever upgraded.

## Step 1 — crop (CPU-only, safe alongside training)

```
powershell -File export_ue_tiles.ps1              # crop all settled tiles
powershell -File export_ue_tiles.ps1 -DryRun      # show the plan only
powershell -File export_ue_tiles.ps1 -Force       # re-crop everything
```

It is idempotent/restartable (skips already-cropped tiles, skips a tile still
being trained), read-only on `out8k`, writes only under `deliver\ue_tiles`, and
never touches the GPU. Each cropped tile is verified against its cell with a
`--stats` read of the written file (bounds inside the cell, count materially
reduced from the raw ~12M). There is **no LOD ladder** — NanoGS builds its
level-of-detail internally from the single source PLY (see below).

## Step 2 — import (opens the editor; needs the GPU free)

The importer discovers the cropped tiles by globbing
`H:\...\deliver\ue_tiles\*.ply` (11 present at authoring; the glob picks up the
rest as the crops finish). Pin an explicit set by filling the `TILES` dict at the
top — a one-line change. It imports each PLY into `/Game/OaklandTiles`, places one
actor per tile at **world origin with an identity transform**, and is
idempotent + logged.

**A. Editor Python console — recommended (and the surface verified against
source).** Open `OaklandFlyaround.uproject`, open the level you want the tiles in,
then in the Output Log command box (mode = **Python**) or **Tools > Execute Python
Script**:

```python
exec(open(r"H:\path\to\ue_import_tiles.py").read())
```

**B. Commandlet (headless-ish).**

```
UnrealEditor-Cmd.exe "H:\2026 Files\26-029 UE\OaklandFlyaround\OaklandFlyaround.uproject" ^
  -run=pythonscript -script="H:\path\to\ue_import_tiles.py"
```

Under `-run=pythonscript` **no map is open by default**, and actor placement needs
a loaded level — so either prefer surface A, or set `OPEN_MAP` at the top.

> **Do not run step 2 before the GPU is free.** A live LichtFeld training job is on
> the box as of authoring. Importing tens of GB of cropped PLY into `.uasset` is
> disk/CPU/VRAM heavy and opens the editor.

## Why the import applies no transform (the coordinate convert)

NanoGS **bakes both conversions at import time**, once per splat (verified in
`PLYFileReader.cpp:341-373, 431-434`):

- **Axis, COLMAP y-down → UE z-up:** `UE.X = PLY.Z*100`, `UE.Y = PLY.X*100`,
  `UE.Z = -PLY.Y*100`. Our global frame is exactly COLMAP up = −Y (gravity +Y,
  ground y ≈ −9), which matches the reader's hardcoded assumption → tiles import
  **upright**. So the script pre-rotates nothing; actor rotation = identity.
- **Scale, meters → centimeters:** positions ×100 and scales `exp()`×100 are baked
  in. Our frame is ~1 unit ≈ 1 m → already correct. So no extra scale; actor scale
  = (1,1,1).

The actor Transform is identity **because** the axis flip and the ×100 scale are
already baked at import — the old "NanoGS converts at render time / the scale comes
from the actor Transform" story was wrong. And the export does **only** the crop
(no rotation, no scale, no pivot; the superspl.at web hacks `-s 0.05` /
pivot-to-origin are deliberately absent). A crop moves nothing, so every tile keeps
its true position and **one shared origin** — which is exactly why identity
placement reassembles them seamlessly.

**Verified live 2026-07-17:** each tile's centroid maps 1:1 to a distinct grid
cell, and cropped tiles land exactly inside their cell — e.g. cell x=2 →
x[−95.7 .. −11.6] and cell x=3 → x[−11.6 .. 81.2], the two meeting at the shared
edge −11.6 with **no overlap**. (Do **not** use `tiles6\<tile>\crop_aabb.json` for
actor placement — cells are used at crop time by centroid, never as placement
offsets; each cropped PLY already carries its own true positions.)

## After import: VRAM / LOD (a manual next step, not done by the script)

Even after cropping, 36 tiles at a few million gaussians each (~150M+ splats
total) far exceed VRAM. Before viewing the whole scene:

- cap rendered splats in the console: `gs.MaxRenderBudget <N>` (≈195 MB working
  buffers per 3M budget; `0` = unlimited), and/or
- enable per-asset **Nanite LOD**: Content Browser → Asset Actions → Nanite →
  Enable. This **re-reads the source PLY**, so keep the cropped
  `deliver\ue_tiles` PLYs in place until Nanite is built.

## Pending (GPU-gated) and a documented future refinement

- **Live in-editor execution was not run** (training holds the GPU). The importer
  is authored for correctness against the NanoGS source; confirm on a free box:
  the import produces upright, correctly-scaled, seam-free tiles;
  `spawn_actor_from_class` places the `NotPlaceable` actor; and
  `gaussian_splat_component` / `set_splat_asset` resolve as bound.
- **Floater prune (future, out of scope here).** The crop removes each tile's
  overlap apron but not mid-air/subsurface floaters that some raw tiles carry
  outside the ground band (e.g. a tile with content down to z ≈ −1000). A later
  refinement can add a lidar/opacity-based floater prune per the 26-014 gaussian
  pipeline, judged by eye; it is intentionally not part of this crop step.

## Assumptions flagged in `ue_import_tiles.py` (where the API was silent)

1. **`NotPlaceable` actor + programmatic spawn** — assumed `spawn_actor_from_class`
   is unaffected (NotPlaceable only hides from the Place panel). **Verify live.**
2. **Python name `gaussian_splat_component`** — from source UPROPERTY via UE
   snake_case binding. High confidence; not runtime-verified.
3. **Import-task plumbing** — assumed `import_asset_tasks` drives the factory and
   populates `imported_object_paths` (standard UE).
4. **Saving large `.uasset`s** (`save=True`) — assumed OK (streamed I/O); watch
   disk/time cost.
5. **Target map** — the script places into the current editor world (console) or
   `OPEN_MAP` (commandlet). **Confirm the target level.**
6. **`gs.MaxRenderBudget`** — deliberately **not** executed from the script; left
   as a documented manual step.
