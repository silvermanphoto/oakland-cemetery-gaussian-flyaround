# Oakland Cemetery boundary cut — FINAL (Joel's hand-traced polygon)

**Prepared 2026-07-22. Preparation and evidence only — NO gaussians have been cut.**

The keep region is now composed from **Joel's own hand-traced boundary** — the authoritative source
that **supersedes all OSM-derived work (v1–v4)**. His trace was drawn in Google Earth, follows the
surrounding roads and the rail corridor (not the cemetery fence line), and is delivered as a single
13-corner WGS84 polygon in `Oakland Cemetery Boundary.geojson`. Because his trace **already includes the
street ring and the railway corridor**, the standing band/rail/no-holes machinery from v4 is **not**
applied — the only remaining rule is to subtract exterior building footprints. This is the final overlay
for a one-look nod.

---

## Headline

- **His trace = 64.96 acres (262,898 m²)** — matches his README's stated ~65 acres exactly. It sits between
  the cemetery's own 48-acre burial-ground figure and the City's 88-acre greenspace figure precisely because
  it follows the roads and rail corridor, taking in the railway up to Decatur Street on the north.
- **FINAL keep = 64.45 acres (260,832 m²)** — his polygon with **8 exterior buildings** subtracted
  (0.51 acre of footprints outside the cemetery wall but inside his trace). One keep polygon, 7 holes.
- **Every safety cross-check passed**, with two items flagged for his eye (below) — nothing was silently cut.

---

## 1. Transform verification (georegistration unchanged)

His WGS84 trace was carried into model coordinates through the **same proven georegistration** used for
every prior version — a 2D similarity fit on **3,270 drone photo positions**:

| quantity | value |
|---|---|
| scale | 0.99989 |
| rotation | −0.0017° |
| residual median | **0.227 m** |
| residual p95 | 0.438 m |
| residual max | 0.700 m |
| outliers | **0** |

**Area check:** transformed ENU area = **262,898 m² = 64.96 acres** — inside the ~65-acre / ~263k-m² target.
**Footprint check:** his model bounding box **X[−291.1, 378.6] Z[−163.9, 366.7]** sits well within the model's
own frame (X[−395.8, 466.9] Z[−337.8, 362.9]) and fully encloses the OSM cemetery box (X[−281.9, 360.6]
Z[−149.8, 256.4]). The trace lands sensibly on the model — see the ortho figure, where his black line wraps
the cemetery, the surrounding roads and the rail yard as drawn.

*Model frame: X = East, Z = North, up = −Y, 1 unit = 1 m. Provenance `georegistration_transform.json`.*

---

## 2. Safety cross-checks (reported, never silently cut)

### (a) Drone-proven cemetery zones vs his trace — one flag

Every v4 model-evidence candidate zone (the drone-proven grave areas) was tested against his trace:

| zone | area | inside his trace | outside | verdict |
|---|---|---|---|---|
| **north_notch** | 4,973 m² | **100.00%** | 0 | fully inside |
| north_central_dip | 889 m² | 100.00% | 0 | fully inside |
| ne_a | 616 m² | 100.00% | 0 | fully inside |
| ne_d | 237 m² | 100.00% | 0 | fully inside |
| ne_c | 124 m² | 100.00% | 0 | fully inside |
| **ne_b** | 1,824 m² | **78.57%** | **391 m² (0.097 ac)** | ⚠ small NE fringe outside |

**Only `ne_b` extends past his line — by 391 m² (≈0.1 acre)** on the far northeast edge. This was the
*weakest-evidence* candidate zone in v4 (density 88, vertical structure 12 m — "cemetery edge, grave rows to
the perimeter drive"). The zoom figure (`fig_zoom_outside_FINAL.png`) shows why his line is defensible there:
the 391 m² sits right **at the perimeter drive where the cemetery abuts the built neighborhood** — his trace
follows that drive as the edge. The OSM way clips *far more* of this same zone than his trace does. **His call:**
if he wants that last sliver in, nudge the NE corner out to the drive; otherwise his line stands.

The two v4 borderline zones (never added) also fall as expected: `nw_corner` (454 m²) is 100% inside his trace;
`east_boulevard` (2,709 m²) is 71% inside — its outer third is the Boulevard streetscape beyond his line, correct.

### (b) OSM cemetery way vs his trace

The OSM cemetery way (28912001, 48.25 ac) is **100.000% inside his trace** — 0 m² outside. His hand trace is a
strict superset of the mapped cemetery, exactly as intended.

### (c) South edge along Memorial Drive

His README notes the closing southern segment was added after the fact. It **does** include a Memorial Drive
band — his south edge sits at model **Z = −163.9**, about **14 m south of the cemetery wall** (Z = −149.8), so the
street in front is enclosed. But it is **tighter than the old v3/v4b band**, which reached the far sidewalk at
**Z = −194.8** (~31 m further south). The difference — **14,347 m² (3.55 ac)** of southern band that v4b kept and
his trace drops — is drawn on the overlay as the blue dotted band so he can see exactly what changes. Overall his
trace is tighter than v4b's generous 45 m road ring + rail bundle everywhere (16,700 m²/16.8 ac less keep region),
while reaching slightly *further north* into the rail corridor toward Decatur (3,293 m² his trace adds). **His trace
is authority; this is shown, not corrected.**

---

## 3. FINAL composition — his polygon MINUS exterior buildings

1. **cemetery/keep input** — Joel's hand-traced polygon, as-is (it already contains the street ring + rail corridor).
2. **− exterior buildings** — every OSM building footprint that lies **outside the OSM cemetery way** and **inside
   his trace** is subtracted (hatched red on the overlay). **8 buildings** subtracted, 0.51 acre.
3. **no fill / no band step** — his single polygon has no holes and already spans the streets and rail, so none of
   v4's band, rail-bundle, or no-holes-fill logic runs.

**Integrity guard (2 buildings PROTECTED, flagged):** the literal "outside the OSM way" rule would have cut two
footprints that actually sit on **drone-proven cemetery ground**; both are kept, not cut (green cross-hatch on the
overlay + `fig_zoom_protected_FINAL.png`):

| osm_id | OSM tag | area | in his trace | in OSM cemetery | in drone cemetery zone | what it is |
|---|---|---|---|---|---|---|
| **270494300** | commercial | **1,293 m²** | 100% | 0% | 61% | the **large white building at the north notch** — the mausoleum-scale structure the v4 evidence flagged. Cutting it would delete real cemetery content. **Protecting it is the clear save.** |
| 270876888 | house | 128 m² | **4%** | 0% | 51% | a small neighborhood house at the NE fringe; his trace already excludes 96% of it, so protecting the ~5 m² sliver is immaterial either way. |

The big one (270494300) is why this guard exists: a 1,293 m² cemetery building, mis-tagged "commercial" in OSM and
sitting just north of the OSM line, would have been silently subtracted by the letter of the rule. The drone shows
it is cemetery ground, so it stays. This is the "no gaussians wrongly cut" principle in action — surfaced, not
silently applied. If Joel reads either footprint differently, it flips with one word.

**FINAL keep region = 64.45 acres (260,832 m²)** — 1 polygon, 7 interior holes (the subtracted buildings).

---

## 4. Per-cell fate (36 render tiles) — final vs v4b

Each tile classed by exact area fraction inside the keep region. **16 wholly inside · 20 partial · 0 outside** —
same split as v4b, and **no tile flips class**. His tighter boundary lowers every partial tile's fraction by a few
points (nothing new drops out, nothing new comes in):

| change | tiles |
|---|---|
| interior 16 tiles | stay **100% inside** |
| south row (row 0) | −8 to −11% (his tighter Memorial Dr band): `tile_*_0` now 7–16% |
| east column drops | `tile_5_4` 47→24%, `tile_5_3` 66→50%, `tile_4_5` 77→65% (his NE line vs v4b's wider ring) |
| all other partials | −2 to −6% |

Full numeric table: `cell_table_FINAL.json` (vs `cell_table_v4b.json`).

---

## 5. Figures

- **`fig_ortho_FINAL.png`** — the one-look figure. Joel's black trace on the drone true-colour ortho: it wraps the
  cemetery + street ring + rail corridor; the OSM way (green) and the drone-proven cemetery zones (purple) nest inside;
  8 buildings (red hatch) are cut.
- **`fig_overlay_FINAL.png`** — the decision overlay in model coordinates: his trace (bold black), OSM way (green),
  drone-proven zones (purple), buildings cut (red hatch), the **2 protected cemetery buildings** (green cross-hatch),
  the superseded v4b outline (grey dashed), the v4b-only south band (blue dots), and all 36 tiles coloured by fate.
- **`fig_zoom_outside_FINAL.png`** — the single flag: the `ne_b` NE fringe (391 m²) that falls just outside his line,
  on the drone ortho, sitting at the perimeter drive against the built neighborhood.

---

## 6. Deliverables & status

- **No gaussians have been cut.** This produces the FINAL keep polygon + evidence only.
- `boundary_keep_polygon_FINAL.json` — the keep region in model XZ (exterior + 7 building holes), same format as v4,
  plus his source WGS84 trace, the transform, and the protected-building ids.
- `cell_table_FINAL.json` — the 36-tile fate table.
- **v1–v4 are superseded** by this document and `boundary_keep_polygon_FINAL.json`.
- Recommended next step: Joel's one-look nod on the ortho + overlay, and a yes/no on the single `ne_b` NE fringe.
