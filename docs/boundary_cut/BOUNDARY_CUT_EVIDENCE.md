# Oakland Cemetery boundary cut — evidence for approval

**Prepared 2026-07-21. This is preparation and evidence only — no gaussians have been cut.**
Everything below lets you approve, in one look, a hard cut at the cemetery walls that
keeps the railway strip running along the north edge and drops everything else into black.

---

## 1. Georegistration fit — how the real world was aligned to the model

The splat model's coordinate frame turned out to already be real-world metric coordinates:
RealityScan georeferenced the alignment from the drone's own GPS, so recovering the
world↔model transform came out almost exactly to a 1:1, north-aligned map.

- **Fit:** 2D similarity, model horizontal plane (X, Z) → world East/North, from **3,270
  drone photo positions** (the 300ft set) matched to their GPS, in the exact coordinate
  frame the 36 tiles live in (the 300ft-only solve — confirmed by its bounds matching the
  tiling's global bounds).
- **Scale** = 0.999892 (1 model unit = 1 metre). **Rotation** = −0.002° (model X ≈ East,
  model Z ≈ North). **Shift** = (−81.45 m East, −7.20 m North).
- **Residuals: median 0.23 m, 95th percentile 0.44 m, max 0.70 m, across all 3,270 points,
  zero outliers.** Well under the 5 m stop-line and better than the 1–3 m that raw GPS would
  give — because the model was already georeferenced from that same GPS, so this is
  essentially confirming the georeference rather than discovering it. Either way the world
  coordinates land on the model to well under a metre.

*Provenance: `georegistration_transform.json`.*

---

## 2. Cemetery boundary — area sanity check

- Source: OpenStreetMap way **28912001**, name tag **"Oakland Cemetery"** (landuse=cemetery),
  fetched from the Overpass API.
- **Computed area = 195,268 m² = 48.3 acres.** The expected figure is ~48 acres (~194,000 m²).
  **Within 0.7% — passes.**

*Files: `oakland_cemetery.geojson`, raw `osm_cemetery_raw.json`.*

---

## 3. The railway kept alongside the cemetery

The rail beside Oakland is the **CSX "Atlanta Terminal Subdivision" main line plus the
near-wall yard tracks**, a bundle of parallel tracks running along the cemetery's
north-west edge and curving off to the north-east toward Hulsey Yard. Only the portion
**alongside the cemetery** is kept; the rest of the line (sweeping away to Hulsey) is cut.

- **Selection:** every rail way that comes within **150 m** of the cemetery boundary
  (11 OSM ways), then clipped along the corridor to the **cemetery's frontage plus 100 m at
  each end** — so the far reaches of the main line (2+ km away) are not kept.
- **Corridor:** a single centreline runs down the middle of that adjacent rail bundle, kept
  as a **30 m-wide strip (default; 15 m each side)**. **This width is the tunable parameter** —
  raise or lower it in one place and re-run.
- **Measurements for your decision:** the adjacent rail bundle is **45.8 m wide** across all
  its parallel tracks; the 30 m default corridor therefore captures the central tracks with
  ~8 m of the outermost track falling outside on each side. The corridor centreline sits
  **~14 m from the cemetery wall** at its closest, so it reads as attached to the north edge
  rather than floating away.

**Two choices that are yours to make (they are why this is an approval step, not a finished cut):**
1. **Width** — keep the 30 m default, or widen to ~50 m to swallow the full 45.8 m bundle
   (all parallel tracks), or narrow it to just the main pair.
2. **Connection** — leave the ~14 m gap so the rail strip sits just off the cemetery, or
   bridge it so the kept rail is one continuous piece with the cemetery.

*Files: `oakland_railway.geojson`, raw `osm_railway_raw.json`, `boundary_keep_polygon.json`
(the keep region in model coordinates — the assembly stage's input).*

---

## 4. The 36-cell decision surface

Each of the model's 36 tiles is classed by how much of it falls inside the keep region
(cemetery + railway corridor). This is the edge-ring worklist: **green tiles need no cutting,
gray tiles are dropped whole, and the orange tiles are where the wall actually passes through
and a cut has to be made.**

- **15 wholly inside** · **20 partially cut (edge ring)** · **1 wholly outside**

Grid below is oriented like the figure — north (row 5) at top, west (column 0) at left.
Each cell shows the percent of its area kept.

| row \ col | col 0 (W) | col 1 | col 2 | col 3 | col 4 | col 5 (E) |
|---|---|---|---|---|---|---|
| **row 5 (N)** | 0\_5 · 25% · partial | 1\_5 · 52% · partial | 2\_5 · 60% · partial | 3\_5 · 50% · partial | 4\_5 · 23% · partial | **5\_5 · 0% · OUT** |
| **row 4** | 0\_4 · 48% · partial | 1\_4 · 100% · IN | 2\_4 · 100% · IN | 3\_4 · 100% · IN | 4\_4 · 98% · partial | 5\_4 · 11% · partial |
| **row 3** | 0\_3 · 47% · partial | 1\_3 · 100% · IN | 2\_3 · 100% · IN | 3\_3 · 100% · IN | 4\_3 · 100% · IN | 5\_3 · 40% · partial |
| **row 2** | 0\_2 · 48% · partial | 1\_2 · 100% · IN | 2\_2 · 100% · IN | 3\_2 · 100% · IN | 4\_2 · 100% · IN | 5\_2 · 59% · partial |
| **row 1** | 0\_1 · 49% · partial | 1\_1 · 100% · IN | 2\_1 · 100% · IN | 3\_1 · 100% · IN | 4\_1 · 100% · IN | 5\_1 · 60% · partial |
| **row 0 (S)** | 0\_0 · 4% · partial | 1\_0 · 9% · partial | 2\_0 · 9% · partial | 3\_0 · 11% · partial | 4\_0 · 11% · partial | 5\_0 · 7% · partial |

Notes: the four central columns of rows 1–4 are the solid cemetery interior (all 100% keep).
The south row (row 0) is nearly all cut — only a thin 4–11% sliver of the cemetery's south
edge survives, so those tiles become thin edge rings. The east column and the north row are
the boundary-crossing tiles. Tile **5\_5** (far north-east corner) is the only tile that lies
entirely beyond both the cemetery and the kept rail — it is dropped whole.

*Full numeric table with cell bounds: `cell_table.json`.*

---

## 5. Figures

- **`fig_A_model_grid.png`** — the decision figure: the 6×6 grid in model coordinates with
  every cell shaded (green inside / orange partial / gray outside), the cemetery boundary,
  the railway corridor, and the drone camera footprint. This is the one-look approval image.
- **`fig_B_world_context.png`** — geographic sanity in real-world coordinates (north up):
  the cemetery, the kept corridor, and the whole rail line so you can see exactly which rail
  is kept (brown/blue, along the frontage) versus cut (light tan, running off to Hulsey Yard).
- **`diag_zoom.png`** — supporting zoom of the rail bundle beside the cemetery with a 150 m
  band, used to design the corridor.

---

## 6. What is not done / caveats

- **No gaussians have been cut.** This stage produces the keep polygon and the evidence only.
  The actual cut waits on your approval of the corridor width and connection choice above.
- **No photographic underlay.** The task allowed skipping it; warping the near-nadir flythrough
  frame onto the map is not straightforward (that render's camera pose is not in the solve's
  pose file), so the evidence is the clean schematic plus the real-world geographic figure.
- **Cell classification** is by dense sampling (45×45 points per tile); percentages are exact
  to that grid. Tiles at exactly 100% / 0% are wholly inside / outside; everything between is
  a genuine edge tile.
- The keep polygon is stored in **model coordinates** (`boundary_keep_polygon.json`), ready to
  feed the assembly/cut stage directly.
