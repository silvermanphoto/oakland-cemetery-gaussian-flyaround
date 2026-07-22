# Oakland Cemetery boundary cut — evidence for approval (v2)

> **SUPERSEDED (2026-07-22) → see `BOUNDARY_CUT_EVIDENCE_v4.md` / `.html`.** v4 rebuilds the complete
> cemetery footprint after Joel found the single OSM outline clips real cemetery ground (north notch +
> northeast), adds a full OSM sweep and a drone-content cross-check, and delivers v4a (48.25 ac, == v3)
> and v4b (50.37 ac, notch + NE added). This v2 document is kept for history only.

**Prepared 2026-07-21. Preparation and evidence only — no gaussians have been cut.**
This is the **v2** keep region, built to Joel's refined rule: keep the cemetery **plus the
entire road ring around it, out to the far sidewalk across the street on every side**, but
**cut every building that sits outside the cemetery walls**. The v1 corridor (a single 30 m
railway strip) is **superseded** — its figures are kept at the bottom for reference.

> Joel's words: *"in every case, i want the entire road around the cemetery all the way to the
> sidewalk across the street from the cemetery, but no buildings outside the cemetery walls kept."*

---

## 1. What v2 keeps and cuts

**KEEP =** the cemetery polygon, **plus a continuous street band that rings all four sides**:
- **South:** Memorial Drive out to the far sidewalk.
- **West:** Oakland Avenue out to the far sidewalk.
- **East:** Boulevard out to the far sidewalk.
- **North:** the **full railway bundle** (all parallel tracks, not just one strip) **plus the road
  beyond the rail**, out to the far sidewalk past it.

The band is **continuous from the wall outward** — wall, near sidewalk, road, far sidewalk are all
kept as one piece, so the earlier v1 questions about corridor width and bridging the gap are
**settled by definition** (the whole thing is in).

**CUT =** everything outside that band, **and every OSM building footprint that lies outside the
cemetery walls wherever it touches the band** — building faces at the sidewalk line are cut cleanly
at their footprint, leaving holes in the band where a building stood.

**Result:** keep area **303,549 m²** (the 195,268 m² cemetery plus ~108,000 m² of surrounding road
band), **33 exterior buildings subtracted**, keep region is 5 polygons with 7 building-holes.

---

## 2. How the band was built (all parameters tunable)

Everything is unioned in real-world metres with a proper geometry engine, then subtracted:

- **Perimeter roads:** every OSM road ringing the site, each buffered to reach its far sidewalk
  (16 m half-width for arterials like Memorial/Boulevard, ~11 m residential, ~7 m service), then
  **clipped to within 45 m of the cemetery wall** so side streets are trimmed at the far corner
  rather than followed off into the neighbourhood.
- **Railway:** the full adjacent bundle (all tracks within 150 m of the wall, buffered 12 m each and
  merged), clipped along the frontage plus 100 m each end.
- **Road beyond the rail (north):** roads within 28 m of the rail bundle are pulled in, so the band
  reaches the street on the far side of the tracks.
- **Sidewalks/footways:** buffered 2.5 m and added where mapped, to guarantee the far-sidewalk edge
  is included (where a separate sidewalk isn't mapped, the road buffer already reaches the building
  line, which is the effective far edge).
- **Buildings:** all OSM building footprints outside the walls are unioned and **subtracted** from
  the band.

The single knobs Joel can turn: the **45 m road ring** (how far past the wall the band reaches on
the street sides), the road half-widths, and the 28 m road-beyond-rail reach. Nothing else needs a
decision — the band is a clean ring by construction.

---

## 3. Georegistration fit (unchanged from v1)

The model frame is already real-world metric (RealityScan georeferenced it from the drone GPS).
Fit on **3,270 drone photo positions** in the exact coordinate frame the 36 tiles live in:

- Scale 0.999892 (1 unit = 1 m), rotation −0.002°, shift (−81.45 m E, −7.20 m N).
- **Residuals: median 0.23 m, p95 0.44 m, max 0.70 m, 3,270 points, zero outliers** — well under
  the 5 m stop-line.

*Provenance: `georegistration_transform.json`.*

## Cemetery area check (unchanged)

OSM way **28912001 "Oakland Cemetery"** → **195,268 m² = 48.3 acres**, within **0.7%** of the
~48-acre spec. Passes.

---

## 4. The 36-cell decision surface (v2)

Each tile is classed by the **exact fraction of its area** inside the v2 keep region. The street
band lifts every edge tile compared with v1 — the south row roughly tripled, the west column and
the corners all gained, and no tile is wholly outside any more (v1's lone outside tile, 5_5, is now
clipped by the north rail band).

- **16 wholly inside** · **20 partially cut (edge ring)** · **0 wholly outside**

North (row 5) at top, west (column 0) at left — matches the figure. Each cell shows percent kept.

| row \ col | col 0 (W) | col 1 | col 2 | col 3 | col 4 | col 5 (E) |
|---|---|---|---|---|---|---|
| **row 5 (N)** | 0\_5 · 37% · partial | 1\_5 · 74% · partial | 2\_5 · 84% · partial | 3\_5 · 79% · partial | 4\_5 · 48% · partial | 5\_5 · 3% · partial |
| **row 4** | 0\_4 · 57% · partial | 1\_4 · 100% · IN | 2\_4 · 100% · IN | 3\_4 · 100% · IN | 4\_4 · 100% · IN | 5\_4 · 33% · partial |
| **row 3** | 0\_3 · 58% · partial | 1\_3 · 100% · IN | 2\_3 · 100% · IN | 3\_3 · 100% · IN | 4\_3 · 100% · IN | 5\_3 · 56% · partial |
| **row 2** | 0\_2 · 58% · partial | 1\_2 · 100% · IN | 2\_2 · 100% · IN | 3\_2 · 100% · IN | 4\_2 · 100% · IN | 5\_2 · 71% · partial |
| **row 1** | 0\_1 · 62% · partial | 1\_1 · 100% · IN | 2\_1 · 100% · IN | 3\_1 · 100% · IN | 4\_1 · 100% · IN | 5\_1 · 75% · partial |
| **row 0 (S)** | 0\_0 · 14% · partial | 1\_0 · 23% · partial | 2\_0 · 22% · partial | 3\_0 · 22% · partial | 4\_0 · 26% · partial | 5\_0 · 20% · partial |

The four central columns of rows 1–4 are the solid cemetery interior (16 tiles at 100%). Every
other tile is an edge tile the wall or band passes through — the south row now keeps a 14–26% road
strip (was a 4–11% sliver), and the corner tile 5_5 keeps a 3% rail clip.

*Full numeric table with cell bounds: `cell_table_v2.json`.*

---

## 5. Figures (v2)

- **`fig_A_model_grid_v2.png`** — the decision figure: 6×6 grid in model coordinates, each cell
  shaded by keep fraction, the v2 keep region filled green, the cemetery boundary, and the
  subtracted buildings hatched red. This is the one-look approval image.
- **`fig_B_world_context_v2.png`** — real-world coordinates (north up): the green keep region
  ringing the cemetery, all neighbourhood buildings in grey with the subtracted ones hatched red,
  and the road/rail network for context. Shows exactly where the band reaches and which buildings
  are cut out.

**Superseded v1 figures** (single 30 m railway corridor, no road ring): `fig_A_model_grid.png`,
`fig_B_world_context.png`, `diag_zoom.png`. Kept for reference; do not use for the cut.

---

## 6. What is not done / caveats

- **No gaussians have been cut.** This produces the v2 keep polygon and evidence only.
- **Keep polygon has holes.** `boundary_keep_polygon_v2.json` is a list of polygons, each with an
  exterior ring and hole rings (the subtracted buildings), in model coordinates — the cut stage's
  input.
- **Far-sidewalk edge** is taken as the road buffer reaching the building line, augmented by mapped
  footways where present. Where OSM has no separate sidewalk, the building line is the effective far
  edge (buildings are subtracted there anyway).
- **No photographic underlay** (allowed by the task; the flythrough frame's pose isn't in the solve).
- **Cell percentages are exact** (polygon-area intersection, not sampled).
- A few thin band tendrils follow side streets ~45 m to the first corner and the rail frontage
  ~100 m past the cemetery — both intended (the ring is clipped near the far corners, not run into
  the city). The 45 m ring is the one dial to turn if Joel wants the street sides tighter or looser.
