# Oakland Cemetery, in gaussians

In December 2022 I flew a DJI Matrice 300 carrying the Zenmuse P1 camera
over Historic Oakland Cemetery in
Atlanta — 48 acres of Victorian garden cemetery, the city's oldest, where
Margaret Mitchell and Maynard Jackson are buried under some of the best
funerary sculpture in the South. The mission was a 300-foot smart-oblique
pattern: 3,270 photographs at 44.7 megapixels, orbiting obliques plus a
nadir pass, shot in flat winter light on a morning cold enough to keep the
grounds empty.

Three and a half years later, those photographs became this: a set of
gaussian-splat reconstructions you can spin around in a browser, built as
nine tiles that share one camera solve, plus a fused whole-site model.
The current work is pushing it further. A finer 6×6 cut — 36 tiles trained
at the photographs' full native resolution — is now live, and a second
flight from that winter (a low-altitude pass with the same camera) has been
fused into the solve, sharpening the ground truth for the next generation
of tiles. It ends in a walkable open-world build in a game engine.

The live scenes are listed in [docs/LIVE_URLS.md](docs/LIVE_URLS.md) and
the 36-tile set in [docs/LIVE_URLS_36_tiles.md](docs/LIVE_URLS_36_tiles.md).
Start with the center tile: the Confederate Obelisk sits at its orbit
center, which is no accident.

## How it was built

Everything below runs on one RTX 3090 in a Windows tower, driven remotely.

**Alignment.** All 3,270 frames go through RealityScan as a single project —
one solve, one shared lens model, every frame registered. That single
coordinate frame is the load-bearing decision: because every tile lives in
the same solve, tiles trained independently still meet at their seams
without any stitching, alignment, or blending step. The solve exports in
COLMAP text format with undistorted frames.

**Tiling.** The site is cut 3×3 on the ground plane, cuts placed by point
density rather than geometry so each tile carries similar content. Each tile
trains on the cameras that actually look into it (computed from where each
camera's axis meets the ground — at 300 feet every camera can *see* every
tile, so naive visibility tests select the whole flight). Tiles train with a
20% apron of extra context, then get cropped back to their exact cell with
half-open bounds so no gaussian is owned twice.

**Training.** LichtFeld Studio, 12 million gaussians per tile, the `mrnf`
densification strategy, roughly 25 minutes per tile once the input pipeline
is right. "Right" matters more than it sounds: feeding the trainer PNGs
starves the GPU at 20% while CPUs decode; the same frames as JPEG on local
NVMe hit 97% GPU. That one change was a 28× difference in throughput.

**Cleanup.** Each trained tile is cropped to its core cell and pruned four
ways — opacity floor, oversized-gaussian cull, distance-from-surface against
the photogrammetry cloud, and a statistical outlier pass. The removed mass
sits tens of meters from any real surface, which is how you know it was
haze and not headstone.

**Delivery.** Tiles publish to superspl.at as SOG files at full gaussian
count. Two viewer lessons that cost real debugging time: the viewer orbits
the model's origin, so each tile is translated to put its most prominent
monument at zero before export (a 3-meter-cell prominence map finds obelisks
and ignores tree canopy); and the viewer's pan and zoom speeds assume small
scenes, so a tile spanning 290 meters is scaled down 20× or navigation
feels dead.

## What's in this repository

    docs/                the build plans and the live scene links
    benchmarks/          render-versus-photograph comparisons as they land
    upload/              staged web files      (not in git — multi-GB)
    gravestone_samples/  full-res reference frames  (not in git)
    renders/             stills and turntables (not in git)

The heavy assets — the camera solve, nine dense tiles at 4–6.4M gaussians
each, and the fused 52-million-gaussian master (11.9 GB) — live on the
training machine, not here. This repo is the paper trail: the plans, the
decisions, and the numbers that made it work.

## Where it's going

The nine tiles are becoming thirty-six, each retrained from its parent's
gaussians (continued training, not from scratch) at 5472-pixel supervision —
the original training only ever saw 3840-pixel downscales, which means the
inscriptions my camera captured never reached the model. After that: LOD
ladders per tile and an Unreal Engine World Partition build, streaming tiles
as you walk, one unified cemetery.

— Joel Silverman · [silvermanphoto.com](https://www.silvermanphoto.com)
