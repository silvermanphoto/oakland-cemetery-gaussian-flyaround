# 26-029 Oakland Cemetery Gaussian Flyaround

A hyperreal, game-playable gaussian-splat world of Historic Oakland Cemetery,
Atlanta — built from Joel Silverman's 2022 drone archive (3,270 photographs,
DJI Inspire 2, 300 ft). Nine trained tiles are live on superspl.at
(links in `docs/LIVE_URLS.md`); the current push is finer tiles at native
photo detail, ending in an open-world walk in Unreal Engine or Unity.

- `docs/` — the master plan, the hyperreal plan, live scene links.
- `upload/` — web-ready splat files staged for superspl.at (not in git).
- `gravestone_samples/` — full-resolution nadir reference photos (not in git).
- `benchmarks/` — legibility comparisons: splat renders vs source photos.
- `renders/` — stills and turntables (not in git).

Heavy data (camera solve, trained tiles, dense masters) lives on the Skychief
PC at `H:\2026 Files\26-002 Oakland Cemetery Splat`. Read `CLAUDE.md` for the
working rules; the training pipeline's full lesson log is in the
`26-014 Custom Lidargraph Camera` repo.
