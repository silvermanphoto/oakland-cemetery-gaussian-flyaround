# Blender lane canary — staged scripts (26-029)

Staged, NOT run (training was in flight on Skychief). See `../BLENDER_LANE_PLAN.md`.

These are mirrored on Skychief at `C:\blender_lane\` alongside the KIRI addon zips.

- `run_canary.ps1` — Skychief wrapper. Self-guards on a GPU gap (won't run while
  training), locates Blender 4.5/5.1 (errors if only 3.0/3.4 present = install
  step), samples RAM+VRAM every 2s, launches the headless canary with a hard
  timeout-kill (crash-recovery), prints peak RAM/VRAM + render times + report.
- `canary.py` — headless Blender script. Installs+enables the KIRI 3DGS addon
  from the staged zip, logs the addon's real operator names, imports ONE tile,
  frames an oblique aerial camera, renders one EEVEE and one Cycles frame,
  writes canary_report.json with counts + timings.
- `download_kiri.ps1` — the staging downloader (already run; KIRI zips are on
  Skychief).

Run (only once Blender is installed AND the GPU is free), per tile/engine:

    powershell -NoProfile -ExecutionPolicy Bypass -File C:\blender_lane\run_canary.ps1 `
        -Tile "H:\2026 Files\26-002 Oakland Cemetery Splat\deliver\ue_tiles\tile_1_4.ply" -Engine EEVEE

Verified tile location on Skychief: H:\2026 Files\26-002 Oakland Cemetery Splat\deliver\ue_tiles\ (36 PLYs).

Canary tiles (map the curve): tile_0_5 (0.19M), tile_3_2 (4.3M), tile_1_4 (7.90M).
