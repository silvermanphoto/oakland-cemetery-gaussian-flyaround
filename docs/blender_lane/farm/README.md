# Oakland Blender Render Farm — package (C:\blender_lane\farm\)

Per-shot, full-quality KIRI splat render farm for the 36-tile Oakland model.
**Everything here is STAGED, not run.** It becomes operational the instant a GUI
console session with real RTX 3090 OpenGL exists on Skychief (see the Mac doc
`docs/blender_lane/GUI_SESSION_SETUP.md`).

## Why a GUI session is required (the wall)

No current Blender splat addon (KIRI, SplatForge, BlendSplat) can render **headless**:
splats draw only through the GPU viewport / offscreen-GLSL pipeline, and Blender
hard-disables all GPU drawing under `--background` (measured 2026-07-21: KIRI's
"Advanced Render" returns 0 files in 0.0 s headless; a plain `GPUOffScreen(64,64)`
throws "GPU functions for drawing are not available in background mode"). So the
render farm runs GUI Blender inside a logged-in session that owns the 3090.

Verified on Skychief: the **console session's active display adapter IS the RTX 3090
at 3840×2160 with an attached monitor/EDID** — so a logged-in console gives real
hardware GL. The only missing ingredient is a logged-in user (the enabler doc).

## Run order (once a session exists)

1. **GL smoke test** — `gl_smoke.cmd`. Opens GUI Blender, prints the live GL renderer.
   PASS = renderer contains `NVIDIA` / `RTX 3090`. FAIL = `GDI Generic` / `Microsoft`
   (software GL → the session is virtual/RDP, redirect it to the physical console).
2. **First render (smoke shot)** — `run_farm.cmd` (double-click on the console) renders
   the queued 3-frame `smoke_tile_3_2` shot. Frames land in `out\smoke_tile_3_2\`.
3. **Production** — add shot JSONs to `shots\`, list them in `queue.json`, run the queue.

## Files

| file | role |
|---|---|
| `gl_smoke.py` / `gl_smoke.cmd` | the definitive "is the 3090 driving GL?" probe |
| `render_shot.py` | per-shot controller: mem-guard → import tiles → key camera → KIRI Advanced Render → harvest frames → quit |
| `render_shot.cmd` | launches one GUI Blender for one shot |
| `run_queue.ps1` | sequential unattended runner; one Blender per shot; watchdog; writes `queue.json` + `farm_status.json` |
| `run_farm.cmd` | double-click console entry point for the whole queue |
| `register_farm_task.ps1` | OPTIONAL — registers an interactive on-demand task so the queue can be kicked off remotely |
| `probe_session.ps1` | read-only session/GPU/tile diagnostics (already run) |
| `shots\smoke_tile_3_2.json` | the first-test shot definition |
| `queue.json` | the run list |
| `out\` | frames + `render_shot.log` + `shot_result.json` per shot |

## Safety rails baked in

- **Memory guard** (in `render_shot.py`): reads each tile's PLY vertex count from the
  header (exact, no import), projects RAM = `gaussians_million × 2.2 GB` (the measured
  slope). If it exceeds `mem_budget_gb` it **aborts cleanly before importing** — the
  queue marks the shot `skipped_oom` and moves on. Split such a shot into fewer tiles.
- **Crash-safe isolation**: one Blender process per shot. A crash kills only that shot;
  the queue continues and `queue.json` records the outcome so a rerun resumes.
- **Watchdogs, two layers**: `render_shot.py` self-quits at `watchdog_s`; `run_queue.ps1`
  kills the process at `watchdog_s + 180 s` as a backstop for a hung Blender.
- **Free-RAM gate**: the runner logs free RAM before each launch.
- **Live status**: `farm_status.json` updates after every shot (running / done / failed /
  skipped counts) for at-a-glance progress.

## Shot JSON schema

```jsonc
{
  "shot_id": "walkA_seg03",
  "tile_dir": "H:\\2026 Files\\26-002 Oakland Cemetery Splat\\deliver\\ue_tiles",
  "tiles": ["tile_3_2.ply", "tile_3_3.ply"],   // the tiles this shot's frustum crosses
  "output_dir": "C:\\blender_lane\\farm\\out\\walkA_seg03",
  "resolution": [3840, 2160],
  "sh_degree": 3,                                // full view-dependent color (tiles are SH3)
  "mem_budget_gb": 45.0,                         // ~50 GB usable of 64; leave headroom
  "gb_per_million_gaussians": 2.2,               // measured import slope
  "watchdog_s": 1800,
  "camera": {
    "lens_mm": 35, "sensor_mm": 36, "clip_start": 0.1, "clip_end": 100000.0,
    "up_axis": "Y",                              // model up-axis (see note below)

    // PRIMARY interface — explicit world-space keyframes along the path segment:
    "keyframes": [
      { "frame": 1, "location": [ 120.6, 40.0, -38.1 ], "look_at": [ 30.6, -7.0, -38.1 ] },
      { "frame": 2, "location": [  95.0, 38.0, -70.0 ], "look_at": [ 30.6, -7.0, -38.1 ] },
      { "frame": 3, "location": [  40.0, 36.0, -95.0 ], "look_at": [ 30.6, -7.0, -38.1 ] }
    ]
    // Each keyframe: "location" [x,y,z] world coords; aim with EITHER "look_at" [x,y,z]
    // (camera points at the target) OR "rotation_euler" [rx,ry,rz] radians. Blender
    // interpolates location+rotation between keyframes → the frame range 1..N renders.

    // CONVENIENCE (used by the smoke shot) — auto_orbit, computed from the imported bbox:
    // "auto_orbit": { "frames": 3, "arc_deg": 30, "dist_factor": 1.25,
    //                 "height_factor": 0.5, "az_start_deg": 40 }
  }
}
```

Coordinate frame (from the 36-tile solve): 1 unit ≈ 1 m; the horizontal plane is X–Z;
Y is the vertical axis. Ground sits at y ≈ −9. tile_3_2 (obelisk cell) spans
X:[−14.5, 75.8], Z:[−69.0, −7.2], center ≈ (30.6, −7, −38.1). **Up-sign note:** the
trainer/COLMAP frame is y-down, so true "up" may be **−Y**; the smoke shot aims at the
cell center so it frames regardless, and `render_shot.log` prints the real bbox on the
first run — set explicit-keyframe heights from that, and flip `up_axis` to `-Y` if
frame 1 renders upside-down.

## Full-model strategy (principle 5 — full quality, no decimation)

All 36 tiles (135.7M gaussians) in one scene is not feasible on this box (≈300 GB RAM,
≈32 GB VRAM at SH3 > the 24 GB card — the "machine literally crashes" trigger). The
farm delivers **full quality with zero gaussian loss** by rendering **per shot**: each
shot loads only the full-count tiles its camera frustum crosses, renders at SH3, quits,
and the next shot loads the next set. Runtime frustum culling/LOD on distant tiles is
principle-3 (allowed); the asset is never decimated (principle 5 honored). Bring Joel
the measured true render-VRAM/time per tile from the first GUI runs before scaling up.
