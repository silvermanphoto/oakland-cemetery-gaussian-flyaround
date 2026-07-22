# Oakland Cemetery boundary cut — evidence for approval (v4)

**Prepared 2026-07-22. Preparation and evidence only — no gaussians have been cut.**

This is **v4**, built to answer Joel's review of the v3 overlay: *the cemetery polygon is
**not** all of Oakland Cemetery — the single OpenStreetMap outline is missing real cemetery
ground, especially the inward **notch on the north boundary** and the **northeast**.* v4 rebuilds
the complete footprint from two independent sources — a full map sweep **and** the drone's own 3D
reconstruction — and delivers two variants for Joel's one-look confirmation. **v3 is superseded.**

---

## Headline

**Joel is right.** The map's single outline clips real cemetery ground on the north and northeast.
The drone data proves it: dense grave-and-monument content continues well beyond the map line in
exactly the two places he marked, and reads nothing like the flat, empty rail yard on the other side
of the wall.

- **The map has nothing extra to give.** A complete OpenStreetMap sweep (cemetery areas *and*
  relations, grave-yards, anything named Oakland, for 700 m around the site) returns **one** cemetery
  outline (way 28912001) plus one **interior** sector (the Confederate Burial Grounds). There are no
  separate section polygons a single fetch missed. So the missing ground can only be recovered from
  the model — the map cannot supply it.
- **The drone shows ~2 acres of cemetery the map omits.** Reconstructed-content density, vertical
  structure (trees/monuments) and true colour all match the cemetery interior in the north notch and
  along the northeast edge, and are unlike the adjacent rail/street.

**Two variants delivered:**

| variant | cemetery footprint | total keep region | what it is |
|---|---|---|---|
| **v4a** (conservative) | **48.25 acres** (195,268 m²) | **77.9 acres** (315,335 m²) | OpenStreetMap outline only — **identical to v3** (the sweep found nothing to add) |
| **v4b** (likely Joel's intent) | **50.37 acres** (203,834 m²) | **81.0 acres** (327,656 m²) | outline **+ the notch + the northeast**, confirmed against the drone content |

> Joel's "48 acres" describes the **map outline** (48.25 ac) essentially exactly — but the drone
> shows the *physical* cemetery is a little larger (~50 ac) because the outline is drawn slightly
> inside the true wall on the north and northeast. Reported, not assumed.

---

## 1. Full OpenStreetMap sweep (Step 1)

One polite, cached Overpass query for **every** cemetery-related element within ~700 m: `landuse=cemetery`
**ways and relations**, `amenity=grave_yard`, any relation named *Oakland*, and any `cemetery=*` tag.

**Result — two elements, and only one is a footprint:**

| element | id | tag | area | note |
|---|---|---|---|---|
| Oakland Cemetery | way **28912001** | `landuse=cemetery`, `barrier=wall` | **195,268 m² = 48.25 ac** | the one outline (the whole thing) |
| Confederate Burial Grounds and Memorials | way **302181500** | `cemetery=sector` | interior | a **section inside** the wall — adds nothing to the footprint |

There is **no multipolygon relation**, **no separate section polygons**, **no `grave_yard`**. Joel's
hypothesis that a single-way fetch missed separate section polygons doesn't hold for this site — OSM
maps Oakland as **one boundary way with interior sectors**. **The union of all OSM cemetery geometry
is just way 28912001.** So **v4a == v3**, and the only way to recover the missing ground is the model.

*Raw: `osm_cemetery_sweep_raw.json`.*

---

## 2. Model-evidence cross-check — the drone knows where the graves are (Step 2)

The combined photogrammetry solve's **12.0 million reconstructed 3D points** were binned into a 2 m
top-down grid over the whole site. Three signals per cell — **point density**, **vertical extent**
(tree/monument structure, up-axis spread), and **mean true colour** — cleanly separate cemetery from
everything around it:

| region | density (pts / 2 m cell) | vertical structure | colour | reads as |
|---|---|---|---|---|
| **Cemetery interior** (baseline) | **181** | **19.9 m** | warm olive (135,125,92) | dense graves + monuments + trees |
| The **north notch** (outside the map line) | **110** | 12–30 m | (133,128,107) | **cemetery** — matches the interior |
| Beyond the **north wall** (rail yard) | **8** | **0.9 m** | flat grey | **not cemetery** — flat, empty |
| **South** street (Memorial Dr) | 87 | 15.6 m | neutral grey asphalt | street (already kept as band) |

The contrast is stark: the notch is **~14× denser** and has **~14× more vertical structure** than the
rail yard on the other side of the same wall. This is the whole argument in one line — *the drone data
distinguishes cemetery from not-cemetery where the map cannot.*

The two-panel figure `fig_content_ortho_v4.png` (true-colour ortho + density heatmap) and the zoom
`fig_zoom_notch_ne_v4.png` show it directly: **grave rows and a large white mausoleum sit north of the
green map line**, and grave rows continue **east of the map's northeast diagonal** up to a perimeter
drive — with parking lots and buildings (correctly excluded) beyond.

### Candidate cemetery zones (added in v4b — confirm by eye)

Contiguous, cemetery-textured content lying **outside** the map line, **within ~55 m** of it, on the
**north/northeast** sides (where the neighbour is rail/open, so the signal is unambiguous):

| zone | where | area | density | structure | verdict |
|---|---|---|---|---|---|
| **north_notch** | the re-entrant on the north edge (Joel's box) | **4,973 m²** | 124 | 30 m | **strong cemetery** — grave grid + white monument |
| **ne_b** | NE band along the map diagonal | 1,824 m² | 88 | 12 m | cemetery edge (grave rows to the perimeter drive) |
| north_central_dip | the inward dip at X≈100 | 889 m² | 106 | **49 m** | **strong cemetery** — mature-tree canopy |
| ne_a | NE, mid | 616 m² | 111 | 37 m | **strong cemetery** |
| ne_d | NE, small | 237 m² | 98 | 34 m | strong (structured) |
| ne_c | NE, small | 124 m² | 97 | 10 m | cemetery edge |
| **total added (v4b)** | | **≈ 8,660 m² = 2.12 acres** | | | cemetery 48.25 → **50.37 ac** |

**Detected but *not* added (flagged for Joel's eye):**

| zone | where | area | why held out |
|---|---|---|---|
| east_boulevard | far east, along Boulevard | 2,709 m² | density 85 + neutral-grey colour = **Boulevard streetscape**, not cemetery interior (kept as band anyway) |
| nw_corner | NW corner top | 454 m² | low structure (7 m), non-green — paved/edge, ambiguous |

These two are drawn on the overlay in **grey dashed / yellow dashed** so Joel can pull them in if his
eye disagrees. They're kept either way (they fall in the road band), so including or excluding them
does not change the cut — only the "cemetery vs surrounding" label.

---

## 3. How each variant is composed

Both variants take the same **standing pipeline** as v3, changing only the cemetery input:

1. **cemetery input** — v4a: the OSM outline. v4b: the outline **unioned with the six confirmed
   candidate zones**.
2. **+ street band** — every perimeter road buffered to its far sidewalk, clipped to a 45 m ring.
3. **+ rail bundle** — the full adjacent track bundle along the north frontage.
4. **no-holes fill** — every stranded interior ground pocket filled (only building footprints stay cut).
5. **− exterior buildings** — OSM building footprints outside the cemetery are subtracted last.

v4b subtracts **45** exterior buildings vs v4a's **36** — not because it cuts cemetery structures, but
because the enlarged northeast footprint now reaches the far side of Boulevard and correctly clips the
buildings there.

*Georegistration (unchanged from v1): fit on 3,270 drone photo positions — scale 0.99989, rotation
−0.002°, residuals median **0.23 m**, p95 0.44 m, max 0.70 m, zero outliers. Provenance
`georegistration_transform.json`.*

---

## 4. The 36-cell decision surface (v4a vs v4b)

Each tile classed by exact area fraction inside the keep region. The 16 interior tiles stay 100%; the
candidate zones lift the **north row and the east column** (where they sit) and change nothing else.
North (row 5) at top, west (col 0) at left. `v4a% / v4b%`.

| row \ col | col 0 (W) | col 1 | col 2 | col 3 | col 4 | col 5 (E) |
|---|---|---|---|---|---|---|
| **row 5 (N)** | 39 / 39 | 74 / 74 | 87 / 88 | 91 / **96** | 57 / **77** | 3 / 6 |
| **row 4** | 57 / 57 | 100 | 100 | 100 | 100 | 35 / **47** |
| **row 3** | 59 / 59 | 100 | 100 | 100 | 100 | 59 / **66** |
| **row 2** | 62 / 62 | 100 | 100 | 100 | 100 | 72 / 72 |
| **row 1** | 66 / 66 | 100 | 100 | 100 | 100 | 75 / 75 |
| **row 0 (S)** | 15 | 25 | 22 | 22 | 27 | 21 |

Both variants: **16 wholly inside · 20 partial · 0 wholly outside**. The gains are exactly where Joel
pointed — tile 4_5 (+20%), 5_4 (+12%), 3_5 (+5%), 5_3 (+8%) — the north-notch and northeast edge.

*Full numeric tables: `cell_table_v4a.json`, `cell_table_v4b.json`.*

---

## 5. Figures

- **`fig_content_ortho_v4.png`** — the proof. Left: drone true-colour top-down ortho (each cell = mean
  colour of the 3D points), OSM line in green, candidate cemetery in purple, Joel's notch box dotted.
  Right: point-density heatmap — bright = dense monuments/trees (cemetery), dark = flat rail/open.
- **`fig_zoom_notch_ne_v4.png`** — zoom of the disputed north + northeast edge. Grave rows and a large
  white monument clearly sit **outside** the green map line; purple is what v4b adds back.
- **`fig_overlay_v4.png`** — the composite decision overlay in model coordinates: current v3 keep
  (green), candidate cemetery (purple, confirm by eye), detected-but-street-like (grey dashed, not
  added), other band additions (gold), buildings cut (red hatch), OSM cemetery line (dark green).

---

## 6. Keep polygons & what's not done

- **No gaussians have been cut.** This produces the v4a / v4b keep polygons and evidence only.
- `boundary_keep_polygon_v4a.json` and `boundary_keep_polygon_v4b.json` — lists of polygons (exterior
  + hole rings for the subtracted buildings) in model coordinates, ready for the cut stage. Same format
  as v3.
- **v4a is a drop-in for v3** (the sweep confirmed nothing to add). **v4b is the recommended footprint**
  once Joel confirms the purple zones by eye against the ortho.
- The two grey/yellow-dashed borderline zones are Joel's call — flagged, not baked in.
