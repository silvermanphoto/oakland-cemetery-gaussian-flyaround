# Handoff — Blender engineering session for the Oakland Cemetery splat world

Paste-ready prompt for a fresh Claude session dedicated to Blender work on this
project. Written 2026-07-22.

---

You are taking over **Blender engineering** for Joel Silverman's Oakland
Cemetery gaussian-splat world. Work in the project sandbox
`/Users/joelsilverman/Desktop/2026 Files/26-029 OAKLAND CEMETERY GAUSSIAN
FLYAROUND` — **read its `CLAUDE.md` first; it is the project law** (the eleven
principles, plus every hard-won Blender convention). Do not touch the GPU
fleet, the rented pods, or the Skychief training queue — a separate session
runs those; coordinate only by updating `CLAUDE.md`.

**The scene:** `blender_scene/2026 Oakland Splat Blender v1.blend` (~4.2 GB) —
the entire cemetery, 16 million gaussians, rendered through the KIRI "3DGS
Render" addon on Joel's M4 Max (Blender 5.2 LTS). It is v1 quality (built from
the first-generation tiles, cut to Joel's hand-traced boundary, then reduced to
the Mac's measured ~16M interactive ceiling); a higher-quality regeneration
from the v2 fleet tiles comes later, so treat the current scene as the working
stage, not the final artifact.

Non-negotiable conventions (details and reasons in CLAUDE.md):
1. Everything is parented to the `Oakland_Root` empty (rotated −90° X so Z is
   up). Transform the ROOT only — and after ANY root transform, re-run the
   KIRI refresh (`sna_r2_viewport_update_BA246()` in the addon module) because
   the display textures bake world-space.
2. The carrier/source meshes (`chunk_00`–`chunk_03`) stay HIDDEN and the file
   is saved that way. An unhidden carrier mesh occludes the splats and reads
   as a "dark/blank" scene.
3. The embedded `oakland_view_guard.py` text enforces Joel's navigation rails
   (no under-ground views, no flips, capped zoom-out, leashed pivot). On a
   manual open Blender asks once to Allow Execution — Joel clicks Allow;
   from script, just `exec` the text datablock.
4. KIRI import hangs above ~5M gaussians per PLY — always import in ≤4M
   chunks. Plain EEVEE/Cycles render blank; output goes through KIRI's
   Advanced Render.
5. MCP bridge on port 9876. If it's dead: QGIS sometimes squats the port, and
   the reliable relaunch is the CLI route —
   `nohup /Applications/Blender.app/Contents/MacOS/Blender "<the .blend>" -P
   /tmp/start_mcp_and_serve.py &` (that script auto-starts the server). If the
   viewport ever goes blank with "StructRNA … has been removed" errors, the
   PROCESS is poisoned — quit and relaunch fresh; the file is fine.
6. Shot grammar (Joel's own finding): splat quality is per-surface — tall
   vertical content (trees, monuments) reads volumetric even side-on; the
   ground smears at grazing angles. Compose low shots against verticals,
   never along bare ground.
7. If a save creates a multi-GB `.blend1` backup, delete it — Joel wants no
   duplicate 4 GB files on his drive.
8. Speak to Joel in plain human language (no jargon-as-nouns, no emoji, never
   the word "honest"), use the question wizard for choices, and record any new
   ground truth in `CLAUDE.md` the moment it's learned.

Start by opening the scene (CLI route above), confirming the world draws with
a viewport screenshot, and asking Joel what he wants to build first.
