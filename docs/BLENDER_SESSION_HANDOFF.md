# Handoff — the Blender-only session for the Oakland splat world

Rewritten 2026-07-24 (supersedes the 07-22 version). Paste the prompt at the
bottom into a fresh conversation in this repo. Scope: Blender engineering
ONLY — the fleet training, cloud pods, and assembly orchestration stay with
the original session; the two coordinate through CLAUDE.md, never directly.

## The scene, exactly as saved (verified live 2026-07-24)

`blender_scene/2026 Oakland Splat Blender v1.blend` (~4.2 GB), Blender 5.2 LTS
on the M4 Max, KIRI "3DGS Render" addon v5.0.0 (current; no newer upstream).

Object tree:
- `Oakland_Turntable` (empty at the georeferenced obelisk axis −0.091, −12.042)
  → `Oakland_Root` (empty, −90° X: Z-up convention) → four chunk pairs
  `chunk_00..03_roadfix` (MESH carriers, 4M gaussians each, HIDDEN — standing
  rule) + `chunk_XXSplat_ProxY` (the drawn splats). 16M total, cut on the
  corrected full-perimeter boundary (roads to far sidewalks, rail floaters
  gone).
- `Oakland_CamOrbit` (empty at the obelisk) → `oakland_whole_site_cam`
  (ORTHO camera; carries a stale leftover action — harmless, playback is off).
- `Sun_7PM` (sun lamp at the true late-July 7 PM Atlanta geometry, currently
  hidden; child `Sun_marker` orange sphere = its visible handle; position is
  cosmetic for sun lamps, only rotation matters). The golden "sunset world"
  datablock exists unassigned (scene world = None).
- Embedded text `oakland_view_guard.py` (v4, 375 lines, auto-runs on load
  after the one-time Allow Execution prompt).
- Timeline: 1–1440 at 24 fps = one 1-RPM revolution keyed on the turntable
  (LINEAR + cyclic). Autoplay OFF; spacebar spins. Undo: 4 steps / 512 MB.

## The four load-bearing systems

1. **KIRI render path.** The live splats draw through a GLSL overlay
   (`draw_gaussians` POST_VIEW handler), NOT geometry nodes and NOT Blender's
   normal pipeline — scene lights, world, color management, and EEVEE/Cycles
   do not touch the live splats (the addon's own Advanced Render is the
   output path; plain renders come out blank). After ANY transform of
   `Oakland_Root`/chunks, or whenever the model blanks, run the refresh:
   `importlib.import_module("bl_ext.user_default.dgs_render_by_kiri_engine")
   .sna_r2_viewport_update_BA246()` (also the panel's Refresh Scene button).
   Panel-section switches tear the display down (expected; refresh restores).
   "StructRNA ... has been removed" errors = the PROCESS is poisoned — quit
   Blender and relaunch; the file is fine.

2. **Guard v4 (the embedded text) — the crown jewel.** Three jobs:
   (a) pinned opening view (Joel's obelisk ORTHO framing; numbers in its
   DEFAULT_VIEW dict) + navigation rails (pitch 0–88°, roll 0, zoom ≤950,
   pivot leashed); (b) autoplay disabled (`play_done: True`); (c) the
   **sort-on-rest fix** for the 3D/not-3D popping: it suppresses the addon's
   broken position-only auto-sort (orbit never sorted → flat melt; pan sorted
   every frame at ~2.9 s → freeze), watches every viewport's view matrix plus
   splat transforms, and ~0.45 s after stillness fires exactly ONE re-sort —
   computed on a worker thread (~2 s, GIL-free numpy) with only the ~0.36 s
   GPU upload on the main thread, so the app never freezes. Drags run ~90 ms
   a frame; release snaps crisp. Runtime switches: `bpy._oakland_async_off =
   True` forces the simple blocking sort; counters `bpy._oakland_sort_fires`
   / `_oakland_sort_applies`. Durable copy: `renders/ghosting_fix/
   oakland_view_guard_v4.py`. If you edit the guard, keep all three jobs.

3. **Turntable.** 1 RPM about the obelisk axis, model-spin design (the spin
   tolerates brief staleness; the guard sorts once when playback stops).
   Parenting used `matrix_parent_inverse = T(−pivot)` computed EXPLICITLY —
   never read `matrix_world` right after setting a location (stale reads
   shifted the whole model once).

4. **Lighting previz.** Splats are pre-lit captures: no live lamp affects
   them, ever. The sanctioned relight path is the addon's **Light Bake**
   (panel → Edit mode → Light Bake section: Store → Bake → Apply; shadow
   strength / colorize / ambient controls; bakes lamp warmth AND cast
   shadows into a managed copy of the colors; minutes at 16M). `Sun_7PM` is
   pre-aimed at the true 7 PM geometry for exactly this. Scene grading and
   the sunset world only affect the addon's offline renders, not the live
   view. For real always-live relighting, Chaos Vantage 3.3 (studio PC,
   free tier) is the recorded alternative.

## House rules that bite

- Blender 5.2 moved animation curves: `action.fcurves` is gone — reach them
  via `action.layers[].strips[].channelbags[].fcurves`.
- KIRI import hangs above ~5M gaussians per PLY — import in ≤4M chunks.
- Screenshots can show stale buffers — force truth with
  `bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)` first.
- Every save spawns a multi-GB `.blend1` — delete it (Joel's no-duplicates
  rule).
- MCP bridge port 9876 (QGIS sometimes squats it). Reliable relaunch:
  `nohup /Applications/Blender.app/Contents/MacOS/Blender "<the .blend>" -P
  /tmp/start_mcp_and_serve.py &`.
- All Joel-facing language human: no jargon-as-nouns, no emoji, never
  "honest"/variants; use the question wizard for enumerable choices; record
  new ground truth in CLAUDE.md immediately.

## Coordination with the fleet session

The original session still runs the 36-cell training fleet, assembly, and the
Unreal flyover. When its v2 tiles finish, a NEW full-quality scene gets
regenerated and the current chunks replaced — so engineer presentation
(views, lighting, animation, guard), don't rebuild content. Never touch
`~/.claude/sentinel/*`, RunPod pods, the fleet queue, or Skychief's fleet
dirs from the Blender session.

---

## Paste this into the new conversation

You are taking over BLENDER ENGINEERING ONLY for Joel Silverman's Oakland
Cemetery gaussian-splat world, in "/Users/joelsilverman/Desktop/2026 Files/
26-029 OAKLAND CEMETERY GAUSSIAN FLYAROUND". Read docs/
BLENDER_SESSION_HANDOFF.md FIRST — it is your complete inheritance (scene
inventory, the four load-bearing systems, the API gotchas) — then CLAUDE.md
for the project law. The fleet/training/Unreal orchestration belongs to a
DIFFERENT session: never touch pods, the fleet queue, the billing sentinel,
or Skychief's fleet folders; coordinate only by updating CLAUDE.md.

The scene: blender_scene/2026 Oakland Splat Blender v1.blend — the whole
cemetery, 16M gaussians via the KIRI addon, with a pinned obelisk opening
view, navigation rails, a parked 1-RPM turntable (spacebar), a pre-aimed
7 PM sun for Light Bake previz, and the sort-on-rest fix that cured the
3D/not-3D popping (all inside the embedded oakland_view_guard.py — protect
it). Blender talks through the MCP bridge on port 9876; if it is down, the
handoff has the relaunch command. Hard rules: refresh the KIRI display after
any root transform; carrier meshes stay hidden; imports in ≤4M chunks;
delete the .blend1 after saves; screenshots need a forced redraw first;
speak to Joel in plain human language and wizard his choices.

Start by confirming the bridge is up, screenshot the scene to verify it
draws, and ask Joel what to build first.
