# Oakland Cemetery boundary cut — ASSEMBLY PRE-GATE: combined-solve georeference re-verification

**Prepared 2026-07-22. Verification only — NO gaussians have been cut. Flagged for the lead's review.**

## Verdict: **FAIL** — the keep outline must be re-expressed before any tile is cut

The keep outline (Joel's hand-traced boundary) was turned into map coordinates using the coordinate system of **one** photo set — the 300-foot oblique flight. But the actual 3D tiles now waiting to be cut (the v2 fleet) are built in a **different** coordinate system: the combined 300-foot **+** 125-foot solve, which the software computed independently. Each of those two coordinate systems is, on its own, accurately pinned to real-world GPS (both land within about a fifth of a metre of the drone's recorded positions). The problem is that they are pinned **independently**, so relative to each other they sit at a slight angle and scale — about **1.22° of rotation and 0.66% of scale**, plus a shift of a few metres.

Carried across that gap, the 13 corners of the outline land **5.9 to 21.2 metres** away from where they belong. The recorded gate expected them to agree to under a metre; they do not. Cutting the tiles with the outline's original numbers would move the boundary by up to a **car-length-and-a-half in the wrong direction** — deleting real cemetery on the far (north-east) side and keeping non-cemetery ground elsewhere. This is exactly the mistake the gate exists to catch.

**The fix is already prepared:** `boundary_keep_polygon_FINAL_c2.json` is the same outline re-expressed in the tiles' own coordinate system, so every corner now lands in the right place. It is offered for the lead to bless — it is **not** self-approved.

---

## 1. The two coordinate systems, side by side

Both fits use the identical method (a 2-D similarity onto the drone GPS, same tangent-plane reference). The **300-foot** fit was reproduced here from scratch and matched the recorded transform to the last decimal, which proves the method is faithful before it is trusted on the combined solve.

| quantity | 300-foot-only solve (where the outline was drawn) | combined 300+125 solve (where the tiles live) |
|---|---|---|
| scale (m per model unit) | 0.999892 | 0.993345 |
| rotation vs GPS north | -0.0017° | 1.2212° |
| GPS-fit residual (median) | **0.227 m** | **0.211 m** |
| GPS-fit residual (p95 / max) | 0.438 / 0.700 m | 0.435 / 0.674 m |
| drone photos used (inliers/total) | 3270/3270 | 3270/3270 |

The takeaway: **each solve is excellent on its own** (both about 0.2 m to GPS, every photo an inlier), so neither is broken. They simply are not the **same** coordinate system — and the outline was built in only one of them.

**Difference between the two frames (300-foot → combined):** scale 1.006591 (a 0.66% stretch), rotation -1.2230°, shift [8.15, -10.37] m. A rotation of one-and-a-quarter degrees across a 380 m-wide site is what grows into ~20 m at the far corners.

---

## 2. Corner-by-corner displacement (the gate measurement)

For each of the 13 outline corners: where the stored outline puts it (300-foot frame), where it truly belongs in the tiles' frame (combined), and how far apart those are. Distances are metres on the ground.

| corner | latitude | longitude | stored X,Z (300-ft) | correct X,Z (combined) | displacement |
|---:|---:|---:|---:|---:|---:|
| 1 | 33.746767 | -84.375220 | (-291.1, -151.7) | (-288.1, -156.8) | **5.92 m** |
| 2 | 33.748060 | -84.375166 | (-286.1, -8.4) | (-280.0, -12.7) | **7.49 m** |
| 3 | 33.750227 | -84.375179 | (-287.3, 232.1) | (-276.0, 229.3) | **11.63 m** |
| 4 | 33.750502 | -84.375193 | (-288.6, 262.5) | (-276.7, 260.0) | **12.21 m** |
| 5 | 33.750593 | -84.374290 | (-204.9, 272.6) | (-192.2, 268.4) | **13.39 m** |
| 6 | 33.751441 | -84.371151 | (86.0, 366.7) | (102.6, 356.9) | **19.30 m** |
| 7 | 33.750982 | -84.370740 | (124.0, 315.8) | (139.8, 304.8) | **19.20 m** |
| 8 | 33.749761 | -84.370076 | (185.6, 180.3) | (198.8, 167.1) | **18.68 m** |
| 9 | 33.749481 | -84.369791 | (212.1, 149.4) | (224.8, 135.4) | **18.89 m** |
| 10 | 33.748558 | -84.368776 | (306.1, 46.9) | (317.2, 30.3) | **20.01 m** |
| 11 | 33.748098 | -84.368160 | (363.1, -4.2) | (373.5, -22.4) | **20.95 m** |
| 12 | 33.747981 | -84.367994 | (378.6, -17.0) | (388.7, -35.7) | **21.22 m** |
| 13 | 33.746658 | -84.368019 | (376.2, -163.9) | (383.3, -183.4) | **20.72 m** |

**Maximum displacement = 21.22 m** (corner 12, the east/north side farthest from the frames' shared pivot). Pass threshold is under 1 m; every corner exceeds it, the smallest by nearly six-fold.

---

## 3. Independent confirmation (a second, unrelated method)

To be sure this is a real frame difference and not an artefact of the GPS fit, the two solves' camera positions were aligned **directly to each other**, using no GPS at all — just the 3,270 cameras they share. That alignment returns the very same frame difference (scale 1.006591, rotation -1.2230°) and fits with a residual of about **0.03 m** — meaning the two coordinate systems are related by an almost-perfect rigid rotation-and-scale. Two independent methods agreeing to the centimetre make the ~6–21 m corner errors trustworthy, and make the re-expressed `_c2` outline exact.

---

## 4. What was produced, and the recommendation

- **`boundary_keep_polygon_FINAL_c2.json`** — the FINAL keep region (one outer ring + 7 building holes) with **every vertex moved into the combined-solve coordinate system** via the measured frame difference. Same acreage and shape; only the coordinate numbers change so they match the tiles. This is the outline the assembly stage should cut with.

- The original `boundary_keep_polygon_FINAL.json` stays as the record of the 300-foot-frame version; it **must not** be used to cut the v2 tiles.

- **Recommendation for the lead:** the gate result is unambiguous (FAIL); the corrected `_c2` outline is ready and independently checked. It is flagged here rather than self-blessed — a one-look nod (or a request for a visual overlay on a tile) is all that stands between this and a correct cut.

---

## 5. Method & provenance

- Combined solve: `H:\2023 Files\23-002 Oakland Cemetery\2026 RealityScan Splat\combined_300_125\sparse\0` — 6588 registered images named `00000.png`–`06587.png`. The 300-foot block is the first 3270 (`00000`–`03269`), complete with no gaps; the single dropped frame (6,589 source photos → 6,588 registered) is a 125-foot frame and never enters this check.

- Camera centres extracted on the studio PC (read-only); GPS read from the drone photo EXIF in the same export order used to build the solves; 2-D similarity fit and all displacement maths reproduced independently on the Mac.

- Method mirrors the original georeference fit exactly (`analyze.py`); the 300-foot reproduction matched the recorded `georegistration_transform.json` to 0.00e+00 on scale, rotation, translation, and residual.

- Figures/data: `boundary_keep_polygon_FINAL_c2.json`, `ASSEMBLY_GATE_EVIDENCE.html` (displacement map), working `gate_results.json`.
