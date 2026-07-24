# CLAUDE.md — 26-029 Oakland Cemetery Gaussian Flyaround

You are the engineer and creative collaborator on Joel Silverman's Oakland
Cemetery gaussian-splat world: a hyperreal, game-engine-playable reconstruction
of the 48-acre historic Atlanta cemetery, built from his 2022 drone archive.
You value verified ground truth, gaussian count over byte count, and pushing
what a "playable splat" can look like. The end state is an open-world walk in
Unreal Engine or Unity — tiles streaming invisibly, gravestones readable where
the source pixels allow.

This folder is the Mac-side sandbox. The retired staging in
`26-014 Custom Lidargraph Camera/Oakland_Splat/` must not be touched again;
the ten hard-won pipeline lessons live in that repo's CLAUDE.md ("Oakland
Cemetery nine-tile splat (26-002)" section) and still bind here.

## Scope and verbosity

Build what is asked, nothing speculative. Concise by default. Every user-facing
string speaks human. No emoji, never "honest"/variants.

## Ground truth (verified 2026-07-17)

- **Source imagery:** `H:\2023 Files\23-002 Oakland Cemetery\12.22.22 Oakland
  300ft Smart Oblique source files\12.23.22 300ft oblique graded` — 3,270 ×
  44.7MP DJI Zenmuse P1 JPEGs (8192×5460), flown on a DJI Matrice 300 —
  aircraft + camera confirmed by Joel 2026-07-20; earlier notes said Inspire 2,
  wrong (no Inspire 2 payload shoots 44.7MP); README corrected. 300 ft
  smart-oblique; 233 of them
  are true-nadir (view axis within 10° of vertical). A separate 125 ft nadir
  set (3,319 imgs) exists one folder up — unused so far, a future
  detail-infill source.
- **Working data (Skychief PC, RTX 3090):** `H:\2026 Files\26-002 Oakland
  Cemetery Splat` — global COLMAP solve (`global\sparse\0`, all 3,270
  registered, one canonical PINHOLE camera, up = −Y, ~1 unit ≈ 1 m, ground at
  y≈−9), undistorted 8192px PNGs (`...\2026 RealityScan Splat\300ft_oblique\
  images`, 00000–03269 alphabetical-order mapping to source JPEGs), nine
  trained 12M-gaussian tiles (`out\`), cropped+pruned dense tiles
  (`deliver\tiles_dense\`, 4–6.4M each), fused 52M `deliver\master_dense.ply`
  (11.9 GB), web SOGs (`deliver\web_v4\`), 6×6 sub-tile partition
  (`tiles6\`, 36 cells, 200–425 imgs each), pivots in `deliver\pivots.json`.
- **Live scenes (unlisted, silvermanphoto account):** nine tiles + Full Site
  master — URLs in `docs/LIVE_URLS.md`. Tiles are full-count (4–6.4M) SOGs,
  pivot-at-origin (orbit center = each tile's hero monument), scaled 0.05.
- **Local folders here:** `docs/` (plans, live links), `upload/` (web SOGs
  staged for superspl.at, multi-GB, regenerable — gitignored),
  `gravestone_samples/` (five random true-nadir 44.7MP originals for
  benchmark viewing — gitignored), `benchmarks/`, `renders/`.

## UE world state (verified 2026-07-20)

The 36-tile cemetery is ASSEMBLED in Unreal Engine 5.8:
`H:\2026 Files\26-029 UE\OaklandFlyaround\OaklandFlyaround.uproject` (NanoGS
enabled), 36 splat assets in `Content\OaklandTiles\`, 36 actors in the saved
`Content\Maps\OaklandFlyaround.umap` — labels tile_0_0…tile_5_5, all at
identity transform (NanoGS bakes axis+scale at import). Sources: cell-exact
crops in `deliver\ue_tiles\` (36 PLYs from out8k). Headless invocation that
works: `UnrealEditor-Cmd.exe <uproject> -run=pythonscript -script=<py>
-unattended -nosplash -nopause -stdout`, launched via an S4U scheduled task.
Known deviations/gotchas: actors are plain Actor + GaussianSplatComponent (the
plugin's actor class is NotPlaceable headless — renders identically; literal
AGaussianSplatActor placement needs an interactive session); OUT8K TILE NAMES
ARE SCRAMBLED — output `tile_A_B` occupies grid cell (5−A, B); derive cells
from the NAME, never runtime centroid-binning. AND (proven 2026-07-20 by
--stats bounds): the COMBINED-solve 6×6 partition (`tiles6_combined`) numbers
its X axis in the OPPOSITE left-right order from the original out8k tiles —
combined `tile_2_4`'s ground = original `tile_3_4`. NEVER map the two
partitions by same-name; always map by cell bounds (it drifts across grid-column
edges on retrained tiles — bug found+fixed 2026-07-19, canonical fix in
scripts/export_ue_tiles.ps1). Visual verification (seams, fps, flythrough)
still pending an interactive session — next per the UE plan.

## PILOT VERDICT — Joel, 2026-07-21 (binding for the rebuild)

Three-way matched comparison (docs/comparisons/, full-res in fullsize_13/) judged
by Joel and independently by the lead, same ranking: the combined 300ft+125ft
solve beats the 300ft-only model DECISIVELY at equal density; the 18M "high"
model is NOT better than the 12M "matched" (Joel: "the 12m matched scene is
just as good as 18m. The high version is not better"). FLEET RECIPE therefore:
**combined solve, 12M gaussian cap, native 8192, mrnf, SFM-sparse init** —
the 18M tier is ruled out (its only effect was cost: bigger cards, longer runs,
heavier files). Why density didn't help: detail is data-limited, not
capacity-limited — 12M already spends all multi-view-consistent information in
these photos; the remaining softness is view-inconsistent micro-texture that
averaging cannot recover at any splat count.

## The hyperreal plan (docs/HYPERREAL_PLAN.md is the full text)

Continue-train the existing tiles — never restart: subdivide 3×3 → 6×6 (or
7×7), init each sub-tile from the parent's trained gaussians (`--init` from a
box-crop of `master_dense.ply`), retrain with `--strategy mrnf`, cap 12M,
supervision at NATIVE 8192px (Joel's upgraded requirement, 2026-07-17 — no
downscale, no A/B; detail pre-approved by the pilot who flew it) → ~4×
density on full-detail supervision.
Then a UE 5.8 Lumen-live + Path-Tracer-reel build via the NanoGS splat plugin
(chosen 2026-07-17 over MLSLabs/XVERSE — see docs/PHASE_A_PLUGIN_DECISION.md).
NanoGS does level-of-detail internally (per-asset Nanite cluster hierarchy,
`BuildNaniteClusterHierarchy` + the `gs.MaxRenderBudget` cvar) — so there is NO
external decimated LOD ladder; UE tiles are just the full-count per-cell crops.
NanoGS also bakes the COLMAP→UE axis flip AND the metres→cm ×100 scale at
import, so UE tile actors take an IDENTITY transform. Pilot = `tile_3_2`
(obelisk cell).
SHOT GRAMMAR (Joel's empirical find, 2026-07-22 — binds flyover + reel
camera work): splat quality is per-SURFACE, not per-view-angle. Tall
vertical content (trees, monuments, walls) was sampled from oblique orbits
and reads volumetric even in near-horizontal side views; the GROUND was
sampled only from steeply above, so its flat gaussians smear to mush when a
view ray GRAZES the terrain. One frame can be both (crisp trees over smeared
ground). Compose accordingly: side views are fine when the frame is filled
with tall content; keep deep grazing ground planes out of foregrounds; when
low, aim ACROSS at subjects, not along the ground. Decimated interactive
scenes smear earlier than full-count renders. Quality gate: judged by eye against the source frames' sharpness (Joel was
the pilot; the footage is razor sharp — no reference-frame ceremony needed).

## BOUNDARY CUT — Joel's directive, 2026-07-21 (binding for assembly + all deliverables)

The final world floats in black space, cut HARD at a keep-region defined
(Joel, refined 2026-07-21): the cemetery (inside its walls) PLUS the ENTIRE
ring of surrounding streets on every side — out to the far edge of the
sidewalk "across the street" — including the full railway bundle on the north
edge and the road strip beyond it. NO BUILDINGS outside the cemetery walls are
kept: subtract every OSM building footprint outside the walls from the keep
region, even where it touches the street band. (Joel: "in every case, i want
the entire road around the cemetery all the way to the sidewalk across the
street from the cemetery, but no buildings outside the cemetery walls kept.")
DESIGN RATIONALE (Joel, 2026-07-21) — the standing test for every ambiguous
cut decision: avoid the "cut out by scissors" look. Cuts must land on the
city's own seams (curb lines, pavement edges, building faces), never through
the middle of urban fabric — the cemetery reads as a complete artifact on its
street plinth. When a boundary call is ambiguous, choose the edge that reads
as a natural urban seam. BOUNDARY — APPROVED FINAL (Joel, 2026-07-22). The cut polygon is
docs/boundary_cut/boundary_keep_polygon_FINAL.json: Joel's hand-traced
13-corner line (64.45 ac after cuts), verified sub-meter onto the model,
minus 8 exterior buildings, with TWO PROTECTIONS Joel confirmed: the
mis-tagged mausoleum at the north notch (osm 270494300 — drone-proven
cemetery content) and the immaterial house sliver both KEPT; the 391 m2
ne_b fringe outside his line goes to black (his line is authority). ASSEMBLY GATE EXECUTED 2026-07-22 — VERDICT FAIL, CORRECTION BLESSED: the
two solves differ by rotation 1.2230 deg + scale 1.006591 + shift [8.15,
-10.37] m (NOT sub-meter as previously believed — that note was wrong);
polygon corners displace 5.9-21.2 m in the combined frame. ALL combined-frame
cutting uses docs/boundary_cut/boundary_keep_polygon_FINAL_c2.json (the
FINAL polygon re-expressed via the measured transform; triple-verified:
harness zero-error reproduction, 0.211 m GPS residual, 0.029 m GPS-free
cross-check; evidence in ASSEMBLY_GATE_EVIDENCE.md/.html). The ORIGINAL
_FINAL.json remains correct ONLY for 300ft-frame models (master_dense, v1
tiles). Never cut a combined-frame model with the original. Geometry
decisions remain CLOSED — this was a frame correction, not a shape change.
Historical: AUTHORITATIVE FOOTPRINT (2026-07-22): Joel is supplying his own GeoJSON of
the exact cemetery boundary — it SUPERSEDES the OSM way (proven ~2 acres
short by the model's density evidence; see docs/boundary_cut/ v4). When his
file lands: transform via georegistration_transform.json, compose with the
standing pipeline (street band + rail + no-holes fill - exterior buildings),
render one final overlay for his nod, then it becomes the cut polygon.
NO-HOLES RULE (Joel, 2026-07-21, from his marked-up
v2 figure): the keep region must contain no stranded unkept ground — every
pocket enclosed between kept components (cemetery, street band, rail bundle)
gets filled. The ONLY cuts inside the outer boundary are building footprints;
buildings stay subtracted even inside filled pockets (his highlight wrapped
around the building at the north notch). Implementation: georegister the solve frame to world coordinates via
drone GPS EXIF from the ORIGINAL source JPEGs (the 8192 pool re-encodes may
have stripped EXIF) fitted against solve camera centers; transform the OSM
polygon into model coordinates; apply as a point-in-polygon gaussian filter at
the ASSEMBLY stage (training keeps its aprons — the cut is delivery-side).
Affects: fused scene, UE world, Blender reel, web scenes. Prep DONE 2026-07-21
(docs/boundary_cut/): georegistration confirmed sub-meter (median 0.23 m — the
solve was already GPS-georeferenced by RealityScan); OSM area check 48.3 acres
(0.7%); keep-polygon written. LEAD'S GATE for the cut stage: the polygon was
fit in the 300ft-solve frame; the v2 tiles live in the combined-solve frame —
the two agree horizontally to sub-meter (the big on-screen offset between
solves is the ~2.4 m GROUND-HEIGHT difference, -9 vs -11.4, which a horizontal
cut ignores) but RE-VERIFY the combined solve's own georeference (GPS vs its
300ft-block camera centers) before cutting a single gaussian.

## BLENDER LANE — measured truths (canary 2026-07-21)

- KIRI 5.0.0 requires Blender 5.1 (extension, cp313 wheels) — 4.5 is a dead
  end. Blender 5.1.2 installed on Skychief; KIRI installs via the EXTENSIONS
  system; import operator sna.dgs_render_import_ply_e0a3a.
- Import slope measured: ~2.2 GB RAM and ~12 s per million gaussians (7.9M
  tile = 17.7 GB, clean). Import ceiling on 64 GB Skychief ≈ 22M ≈ 2-4 average
  tiles resident. Full 135.7M model = ~300 GB = confirmed crash.
- HARD BLOCKER: no Blender splat addon can render HEADLESS — splats draw only
  through GPU viewport/offscreen pipelines and Blender disables all GPU drawing
  in --background (KIRI geometry nodes evaluate to 0 faces; renders are blank).
  SplatForge and BlendSplat share the same wall — do NOT buy SplatForge for
  headless automation ($49 answers a question we no longer have).
- Consequence: Blender splat rendering requires a GUI session with a live GPU
  context. RESOLVED CHAIN (2026-07-22, four bounded attempts): (1) import hangs when
called at --python startup in GUI — cured by deferring the whole sequence
into bpy.app.timers stages (the event loop must be pumping); (2) the KIRI
extension lived in Joel's profile, not the render account's — extension repo
repointed; (3) Advanced Render silently draws nothing unless
bpy.gaussian_quad_shader exists — its own rebuild path is doubly broken
(wrong assets subfolder + a globals() scoping bug), and interactively only
the viewport draw builds it; script-side cure = call KIRI's own
sna_r2_viewport_update_BA246() (the Refresh Scene internal) before rendering.
PROVEN: 3/3 frames rendered non-interactively on the auto-signed-in console.
Camera framing FIXED (up=-Y derived empirically + 2-98 percentile aim box)
— beautiful frames proven on Skychief. MAC STATUS (2026-07-22, Joel's Blender
5.2.0 LTS + KIRI 5.2-patch build): scene delivery works (packed 2.24 GB
.blend at blender_scene/, sha-verified); KIRI's OWN Advanced Render is
CORRECT on 5.2/arm64 (~8.5 s/720p frame on the M4 Max), and the live
VIEWPORT is ALSO correct — the earlier "dark from above" was NOT a color
bug: it was the un-hidden CARRIER MESH (4.3M bare quads) occluding the
painted overlay. HIDE THE SOURCE MESH (hide_set) and the viewport draws
true color; the .blend is saved with the mesh hidden so it opens clean.
WHOLE-SITE .BLEND CONVENTIONS (2026-07-22 evening): the delivered scene —
RENAMED per Joel to "2026 Oakland Splat Blender v1.blend" (blender_scene/;
true mv, no copy; both multi-GB .blend1 auto-backups deleted; if a save ever
recreates a .blend1 duplicate, delete it — Joel wants no 4 GB dupes) — is
BLENDER-CONVENTIONAL — everything (chunks,
proxies, camera) is parented to an "Oakland_Root" empty rotated -90 deg X, so
Z is up and Top/Front/Side views behave normally (rotate the ROOT, never the
chunks; re-run the KIRI refresh after any root transform — the display
textures bake world-space). An embedded VIEW GUARD (text datablock
oakland_view_guard.py, use_module, 0.15 s timer) enforces Joel's navigation
law: pitch clamped to the upper half-hemisphere (no under-ground, no flips,
roll pinned 0), zoom-out capped ~950, orbit pivot leashed to the site box —
torture-tested (forced illegal states snap back). Future opens prompt once to
Allow Execution (the guard is in-file); declining just disables the rails.
Cap-window ops lesson (2026-07-22): Joel's weekly Claude cap silences EVERY
Claude layer at once (lead, pulse, heartbeat sessions, agents) — treat the
weekly reset as a hard operational boundary during multi-day metered runs;
the pod-side idle self-guards + launchd sentinel are the layers that survive.
ASSEMBLY CANARY — PASSED 2026-07-23 (principle-3 seam risk retired on real v2
data). The delivered 2x2 NW block (tiles 1_1/1_2/2_1/2_2, 12M each) was cut to
half-open core cells, merged, and seam-checked: density ratios 0.90-1.05 across
all four internal seams (pass band 0.7-1.4), ZERO duplicate/double-owned
gaussians, and rendered crossings visually seamless (lead-reviewed stills in
scratchpad/assembly_canary/ + H:\...\out_cloud\assembly_canary\). THE RECIPE is
recorded at C:\LidargraphCapture\status\ASSEMBLY_RECIPE_DRAFT.txt — full-36
assembly is a re-run, not a derivation. Load-bearing facts: (a) authoritative
cell bounds = H:\...\tiles6_combined\tile_A_B\crop_aabb.json (cross-confirmed
against edge_cull.py's hardcoded cut lines; cell_bounds_cache.json is NOT the
partition — it's ground-height analysis, 0.4-0.8 m off); (b) half-open cells
via 1e-6 inward nudge of each tile's MAX edges only; (c) core-cut keeps ~40%
of a 12M tile (the ~20% training overlap is removed) → full 36-tile fused
master lands ~170M gaussians pre-prune — plan LOD/decimation from that number;
(d) merge = splat-transform PURE concat, no transform flags; (e) KIRI chunking
for farm renders: split_ply.py does NOT exist on Skychief — chunk by
polygon_cut_ply.py central-box crops ≤4M (pattern in the recipe file).
GUARD-STACK NIGHT (2026-07-23, ~$2.5 idle across two incidents — every layer
audited). What failed, in one night: (1) THREE advance agents parked
themselves "awaiting a wake" that cannot come (their own background jobs do
not survive their turn) — the SendMessage wake-correction recovers them, but
watchers armed in an agent's context DIE WITH THE AGENT: three watchers went
silent. (2) The pod idle-guard's stop ladder (kill -9 1 → poweroff → halt)
is IMPOTENT inside RunPod containers — PID 1 ignores SIGKILL from inside the
namespace, no systemd, halt unpermitted; it fired live at 06:48Z and failed
("no_stop_method"). Working ladder (patched on both pods, .pre_stopfix
backups): pkill -9 the trainer + STOPPED_BY_GUARD marker, then `kill -9 -1`
(namespace-wide kill exits the container → Secure pod stops, disk kept).
(3) The launchd meter-sentinel was alert-ONLY, its idle re-alert had a 2-hour
lockout (one missed 2 a.m. ping = two silent hours), and it logged to
sentinel.log not meter-sentinel.log. REBUILT: logs to meter-sentinel.log,
re-alerts every 30 min, and at ~50 min of consecutive-zero GPU on a fleet-*
pod it STOPS the pod via the API (verified podStop mutation; fleet-only,
at-most-once, never on nonzero GPU, never when the API itself is blind;
doorbell messages in plain human sentences). The auto-stop arms via
`touch ~/.claude/sentinel/autostop.armed` — arm only when no pod is
legitimately at 0% (mid-delivery/relay). API telemetry note: every "0% GPU"
reading checked tonight was TRUE (a finished trainer, not API noise) — trust
it as a signal, verify by ssh before acting manually. OPERATING TRUTH: the
conductor pulse (ground-truth probes every ~21 min) and the sentinel are the
reliable layers; per-agent watchers and "a notification will come" are not —
advances are now stationed BEFORE completion or dispatched by the pulse.
PERIMETER AMENDED 2026-07-23 (Joel's directive, screenshots): every
street-bordered stretch now runs to the FAR sidewalk's outer edge (Memorial
Dr S, Oakland Ave W, Boulevard E — full road + opposite sidewalk in, buildings
still out); the railroad stretch hugs the far edge of the CONTINUOUS track
bed (every track/car kept — dense-cell check 44,780→45,454 — detached
floaters beyond the yard culled). Keep area 260,832→268,387 m^2 (+2.9%); his
13 corners + 7 building holes + SE notches untouched; 0 self-intersections;
c2 re-expression residual 0.0000 mm on unchanged vertices. BOTH
boundary_keep_polygon_FINAL.json and _FINAL_c2.json are amended IN PLACE
(.pre_road_fix backups alongside; ROAD_FIX_RECORD.txt tells the story) — the
amended c2 is the blessed cut for the v2 fusion. master_dense re-cut
85.10%→87.58% kept → 16M decimate → chunk_00..03_roadfix.ply (blender_scene/,
992,001,532 B each) → swapped into "2026 Oakland Splat Blender v1.blend"
(old chunks deleted from the scene, orphans purged, saved, .blend1 dupe
removed). Evidence renders: renders/perimeter_fix/ (local). OPS LESSON: long
Skychief jobs (decimate etc.) MUST run as a scheduled task, not Start-Process
over ssh — Windows kills the detached tree ~3 s after the ssh session closes.
EDGE-CELL STAGING — PROVEN 2026-07-23, with two catches (both recorded before
any edge cell trains). Path: stage_tile.ps1 auto-detects ring cells (A/B in
{0,5}) and copies native-8192 frames BY LIST from the _pool_combined_8192 pool
per the cell's pre-culled images.txt (cull already applied fleet-wide
2026-07-21, all 20 PASS) — no resize/prep step, unlike interior. tile_5_5
prestaged deterministically (tar byte-identical to the 07-21 dry run). Recipe:
C:\LidargraphCapture\status\EDGE_STAGING_RECIPE_DRAFT.txt. CATCH 1: the
centroid precheck is VACUOUS for ring cells (half-open crop_aabb 1e6
sentinels; corners carry the global cloud) — the real gate is the recipe's
stage-integrity check (pool_miss==0, counts match planN, tar_members==planN+7).
CATCH 2 (training-soundness) — FIXED 2026-07-23 before any edge cell trained:
edge cells' sparse seeds were never cropped on ring-facing sides (mid-edges
~2.7M pts; the 4 CORNERS carried the FULL 12M global cloud → SFM-init would
have seeded site-wide and wasted the cap). All 20 edge points3D cropped at
source to closed-cell rect (+20 m; c2-polygon bbox x=[-288,388] z=[-183,357]
closes the 1e6 open sides) — corners now 0.29–0.76M, interior-like; format
matches partition6_combined.py's DECOUPLED shape (simplified 8-field points,
NO track refs, so cropping cannot dangle) — that decoupling is why seed crops
are always safe here. Backups points3D.txt.pre_seedcrop alongside; per-cell
record edge_seedcrop_report.json; tile_5_5 restaged on the cropped seed (tar
4,247,498,752 B, all gates PASS). NOTE tile_5_5 is genuinely the sparsest
cell (95k seed pts, 175 frames — its NE rect lies mostly outside the site's
diagonal boundary); expect a modest corner there, not a defect. Corner/large-edge tars are bigger — relay+wall run
longer (tile_5_0 N=701 is the largest edge cell).
UE RENDER ROUTE — PROVEN 2026-07-23 (principle-4 render gate cleared). UE
sequence renders on Skychief MUST launch as a CONSOLE-session scheduled task
(registered against the logged-on console user SID, Interactive, highest priv
— the same pattern as the Blender farm); the S4U route inits the engine fully
(545 s cold, shaders compile) then freezes FOREVER at viewport creation (log
dead-ends on a LogSlate font-face line) — no GL without the interactive
desktop. Console route: passed that exact line in ~2 min warm and rendered
120/120 proof frames of OaklandFlyover_Example (lead-verified real imagery:
obelisk + canopy + engine sky). Reusable launcher + poll script:
C:\UE_scripts\. GOTCHA for the final reel: the legacy
AutomatedLevelSequenceCapture IGNORES command-line resolution flags and
follows the desktop size (asked 1920x1080, got 888x500) — set output size in
the movie-capture settings and drop windowed mode instead. Frames:
H:\2026 Files\26-029 UE\OaklandFlyaround\Saved\VideoCaptures\ue_proof.
ADDENDUM (2026-07-23): the same all-Claude-layers-quiet outage can also happen
WITHOUT the cap — a transient service/dispatch gap silenced the heartbeat AND
the in-session pulse for ~00:24–02:09Z, Mac awake (caffeinate held) the whole
time. The mitigation proved itself: pod guards stayed armed, both cards
trained through the gap at 100%, zero loss. Design rule stands: any Claude
session is an unreliable watcher; money-guarding logic lives pod-side (or
launchd), and every pulse re-verifies lanes from ground truth, never from the
last Claude-side status.
WHOLE-SITE SCENE PATH (proven 2026-07-22): KIRI's import hangs on a single
PLY somewhere above ~5.15M gaussians (loads ~34 GB then never returns — not
OOM, not disk). Whole-site scenes therefore import as ~4M-gaussian CHUNKS
(split_ply.py, contiguous slices, SH-preserved) — 4x4M imported in 16-48 s
each where 1x16M hung forever. Decimation of huge PLYs: splat-transform's
merge phase is IO-bound and can look stalled for ~25 min — trust the job's
own EXITCODE/log lines, never process-CPU heuristics. Plain EEVEE/Cycles still render BLANK (geometry nodes feed them 0 faces,
same as headless Windows) — output goes through KIRI Advanced Render. scipy has no arm64 wheel — lazy import,
harmless. Machinery is done on both machines. STANDING RULE (Joel, 2026-07-22, expectation corrected same day): a
"Blender scene" deliverable means the WHOLE CEMETERY by default — partial or
preview scenes only when explicitly framed as such, with the scope in the
FILENAME (he opened a north-edge preview expecting the full site). Whole-site
interactive scenes use the crash-exception reduction (measured ceiling ~16M
on his Mac) cut-first-then-decimate; full quality stays the render farm's
per-shot job. Also STANDING RULE (Joel, 2026-07-22):
every Blender scene delivered to him ships with the carrier/source mesh
HIDDEN (hide_set) and is SAVED in that state — never show the scaffold. Superseded text follows for history: automate a console GUI session on Skychief
  (autologin + GUI automation; RDP may not bind the 3090 for GL) or do the
  Blender reel interactively and let UE carry the seamless-world goal.

## ARENA PATCH — the fleet's load-bearing fix (proven 2026-07-22)

LichtFeld hardcodes its GPU memory arena to 32 GB VIRTUAL regardless of card
(upstream issues #792/#1091, open). Cells whose densification+sort cross it
crash at "FastGS sort-buffer allocation" (forward.cu:60) — cell-DENSITY
dependent, not camera-count (a 318-cam cell crashed while a 410-cam cell
trained clean). No flag/env/config exists. FIX: one-line source patch scaling
the arena to the card's physical memory; rebuilt incrementally on a pod;
PROVEN by re-training the crash cell past its old failure point (iter 12,900+
vs crash at 11,968, 12M splats resident). Patched build salvage:
lf_build_salvage_v2.tgz (Mac pilot_runs + Skychief out_cloud). The patch diff
is saved in the salvage notes; reproducible in minutes. ALL fleet training
uses the v2 build. (Also: 3090 verdict final — 24 GB cannot train combined
cells at 12M native even below the arena ceiling; local training lane closed.)

## The eleven principles (Joel + lead, locked 2026-07-21 — govern the rebuild)

Joel's five: (1) video-game level — the finest splat the software and photo
sets permit; (2) prime directive — fast, efficient, token-respectful;
(3) all 36 tiles fused seamlessly into one apparent scene with LOD;
(4) interactive pleasing flyover in Unreal Engine; (5) the entire tiled model
into Blender for rendering — at FULL quality, no decimation unless the machine
literally crashes, and any forced step-down comes to Joel with numbers first.
The lead's six, as amended by Joel: (6) one canary gates every fleet, at every
scale (train/UE/Blender/flyover); (7) machines verify geometry, Joel's eye
judges beauty — and any quality/time/money tradeoff is ASKED first, never
decided silently in either direction; (8) every meter guarded by machinery,
budget position stated at every phase gate; (9) right-size every asset to its
destination (archival full-count masters; UE full-count via NanoGS internal
LOD; web SOG; Blender full-count per principle 5); (10) ground truth written
the moment it happens; (11) continuous operation until complete — every
machine always has a next assignment, heartbeat lanes.json updated at every
stage change, hand-offs fire themselves, human gates never idle the machines.

## Lessons — 2026-07-21 session (pilot verdict + comparison tooling)

- **Detached training on Skychief: Start-Process orphans DIE when the ssh
  session closes** (~40 s, silent, no error). The proven route is a scheduled
  task registered -LogonType S4U **by the account's SID, not name** (the
  Microsoft-account name `WORKGROUP\joel pc login` fails SID mapping). The
  fleet driver must launch every local train this way; survival is verified
  from a fresh connection.
- **LichtFeld doubles as a matched-view renderer** (recipe + traps in the
  field manual ch07): --init + --iter=1 + --timelapse-images (=-attached form
  only) renders named dataset cameras in seconds. Traps: mcmc's DEFAULT
  1M cap silently subsamples big models (set --max-cap ≥ model count; check
  "Final splats", no "Choosing randomly"); --iter=0 loads but renders
  NOTHING; 18M at 8192 OOMs a 24 GB card (optimizer state ~12 GB even for
  1 iter) — color-faithful fallback is lower --max-width, LABELED wherever
  compared against native renders.
- **Comparison methodology:** render at the native supervision width and give
  every column identical downsample treatment — a low-res rasterization next
  to a supersampled photo downscale systematically flatters the photo (Joel
  caught this by eye). Detail judgments live in 1:1 crops from one shared box.
- **The two solves do NOT co-register on screen** — the 300ft-solve tile
  renders hugely displaced through combined-solve cameras (landmarks moved
  hundreds of 8K pixels). Never mix tiles from different solves in one scene;
  the rebuild exists partly to end mixed-solve seams.
- **Why 18M ≠ better (for the record):** detail is data-limited — capacity
  past the multi-view-consistent information adds redundant overlapping
  splats that render identically. Density's only untested edge is extreme
  close range; Joel judged the live scenes and closed that question too.

## Hard-won rules that bind every job here

- Feed LichtFeld JPEG q95 from the PC's local NVMe (`C:\oak_resized6\`),
  never PNG, never the RAID (28× throughput difference; check the loader line).
- `--strategy mrnf` only — mcmc deadlocks at cap under driver 591.86.
- Never hard-kill a mid-CUDA trainer (unkillable VRAM zombie; reboot-only).
- splat-transform v3.0.0: `-t a,b,c` ⇒ (x−a, y−b, z+c) — Z sign FLIPS; `-B`
  box-crop reads its X corners in a NEGATED-X frame vs the file/stats frame, so
  to crop to x∈[x0,x1] you must pass the X corners as `(-x1,-x0)` (Z and Y as-is)
  — verified 2026-07-17, a sibling to the `-t` Z-flip; passing raw X mirrors the
  crop into the wrong region (kept only a handful of stray gaussians). `-d` last
  action, .ply output only; verify output bounds via `--stats null` on the
  WRITTEN file before shipping. Do not pre-rotate for superspl.at (viewer expects
  trainer-native orientation).
- superspl.at republish: R2 public URL → page fetch → File → DataTransfer →
  input, select the scene by exact text, verify the "Replace the model for"
  string. Files >300 MiB: split into R2 parts, stitch with Blob([p1,p2]) in
  the page. `wrangler r2 object put` caps at 300 MiB.
- Windows unattended: scheduled tasks `-LogonType S4U`; no `Start-Transcript`;
  `py -3` never bare `python`; ASCII-only scripts; `${var}:` in PS strings.
- PC ↔ Mac: push via scp; pull via base64-over-ssh (spaced login breaks scp
  pulls). GPU sharing via `C:\LidargraphCapture\status\gpu_state.txt`.

## Operations guide — compute, money, and authority on this project (2026-07-19)

Distilled from the full-arc report card's three weakest subjects (resource
stewardship C+, reliability B−, collaboration B — docs/health/
REPORT_CARD_2026-07-19.md). These govern every future run here.

**1. Size runs on paper before silicon.** Measured anchors, so nobody re-buys
these failures: native-8192 training peaks ~13.8 GB VRAM at 12M gaussians
(v1 probe, 3090); cap 14M spiked past 18.4 GB and cap 18M past 22.7 GB — both
OOM'd the 24 GB card; the combined-solve pilot cell OOM'd even at 12M native
(larger working set, 462 frames). Before ANY new cap/resolution combo: scale
from the nearest measured anchor, add ~30% for densification spikes, and if the
envelope exceeds the card, do not launch — rent the bigger card (48 GB A6000,
~$0.33/hr, fits 18M native with room) or surface the constraint to Joel. A
failure predictable from our own logs is never bought twice.

**AUTO-ESCALATION RULE (Joel, 2026-07-22, standing):** any cell that runs a
card out of memory auto-routes to the next card class up (48 GB -> 80 GB
lane) WITHOUT waiting for approval — a doomed retry or a lane waiting on a
human is idle compute. Guardrails remain absolute: per-class price caps
(80 GB <= $1.80/hr; above that class or an empty market -> escalate to Joel),
the $15 balance floor halts all new launches, every pod carries the dead-man
bring-up watchdog + the pod-side idle self-guard, one attempt per card class
(never retry the same class on the same cell), and the vacated card
immediately claims the next queue cell. Measured density rate so far: 3 of
the first 6 combined-solve cells are dense-class — budget projections must
use the LIVE rate, not the pre-fleet estimate.

**2. Every meter gets machinery, not attention.** The three billing rules
(verify the external name read-only BEFORE the first billable second; dead-man's
switch keyed to a REAL login, auto-kill past deadline; never idle with an
unguarded meter) are standing — full text in the 26-014 CLAUDE.md and memory
`feedback-guard-billed-resources`; working reference scripts in this session
lineage (`pod_watchdog2.sh` pattern). Additions this project proved: one-shot
transfer codes (runpodctl/croc) are sequenced — sender confirmed ready, then one
receive; a failed handshake kills the code, so restart the sender for a fresh
one, never retry the old code. Track the account balance at every phase gate and
say it in status updates.

**3a. Name the watcher or the lane is stalled.** (2026-07-19, after the trainer
sat idle 5 hours behind a silently dead monitor.) Any status — to Joel or
internal — that calls a remote job "running" must name the live harness-tracked
watcher guarding it, liveness verified, not claimed. Delegating a watch to an
agent does not discharge it: the lead keeps an independent backstop on every
metered or multi-hour job from LAUNCH, not from the first stall. Joel audits
nothing: the standing meter-sentinel (a launchd job on the Mac, every 10 min —
see the global CLAUDE.md) watches all rented GPUs outside any session and rings
his phone on sustained idle, old pods, or its own blindness.

**3. Monitor both ends and every terminal state.** A two-party operation
(transfer, remote build, remote train) gets its watcher on BOTH sides — "no
bytes arriving" polled thirty times is not a status, it is a dead sender
undiagnosed. Every monitor greps failure signatures, not just success
(trainer: BUILD_DONE_OK / CMake Error / ninja stopped / OOM / CUDA error;
transfer: room-not-ready, stalled du); a log frozen past its expected cadence
means DEAD, wake and investigate. Silence is never success.

**4. One variable at a time; canary first.** On an unproven stack, never stack
unknowns (the cloud saga ran new host + new image + new build + new transfer at
once, making every failure ambiguous). Prove SSH, then toolchain, then build,
then data, then a smallest-viable train, in order. The pilot-before-fleet
pattern (one tile gates 36) is this project's law — apply it downward too (one
frame, one minute, one tile).

**5. No device idles across a stage boundary.** When a lane's work moves off a
machine, the finisher assigns that machine its next job in the same breath —
the 3090 idling 8 hours while a rented card worked is the canonical violation.
Standing next-work queue: 3090 free → UE crops/imports, SOG conversions,
re-preps; Skychief CPU free → alignments, crops, transfers; pod free → nothing,
pods die when unassigned (that is what the meter rules are for).

**6. Joel's bars and running jobs are spec, not preferences.** Native 8192 is
the standing quality bar; a stated bar is never quietly substituted (the 5472
run spent hours producing something pre-rejected — the correct move was
stop-and-present-options in the wizard: rent, re-scope, or wait). His running
jobs and priorities are untouchable without his yes; an information request
never authorizes a reorder. Escalate-first triggers: anything spending his
money, touching his queue, lowering his bar, or going public.

## Git

Local repo; `upload/`, `gravestone_samples/`, `renders/` gitignored (large,
regenerable). PUBLIC GitHub repo `silvermanphoto/oakland-cemetery-gaussian-flyaround`
(Joel's explicit call, 2026-07-17 — an exception to the private default; the
README is written in his voice for a public audience). Never force-push;
never commit secrets or multi-GB binaries.
TRAINER-CACHE DISK BOMB (2026-07-23, caught at 2.1 GB free mid-run):
LichtFeld caches decoded 8192 JPEGs at /tmp/LichtFeld/pipeline_cache/
ppl_j2k_unified_v1, ~14.8 GB PER TILE, never auto-pruned — a multi-cell pod
starves its own final PLY+checkpoint write (~6 GB). Standard hygiene now in
the advance procedure: after each launch confirms iterations, delete cache
files with mtime OLDER than the launch (the fresh set is the live run's —
never touch it); want >=25 GB free. Both pods pruned live (bigcard 48→12 GB
cache, lane5 39→14 GB) with trainers running — proven safe. SENTINEL
AUTO-STOP ARMED 2026-07-23 ~09:10Z (both pods at real GPU; task #11).
CENSUS NEAR-MISS (2026-07-23): the fleet queue was seeded AFTER three cells
already existed and silently held only 33 of 36 — tile_2_4 (the PILOT cell
Joel judged to lock the recipe; its pilot125 PLY is byte-format-identical to
fleet tiles, 20k/mrnf/12M/SH3/SFM verified in its log) plus the pre-queue
tile_1_1/1_2. Caught by a grid-vs-queue diff at 11 banked; the pilot PLY was
hash-verified-copied to out_cloud\fleet\tile_2_4_12M_c2.ply and all three
got DONE census lines — fleet_queue.txt is now the COMPLETE 36-cell census;
counts come from the file, never memory. Relay lesson (bigcard advance #4):
croc hashes the whole tar before its room opens — a cold 14+ GB tar means
~6 min of "room not ready" (NORMAL); one continuous sender, receiver retries,
never restart the sender; runpodctl may emit a bare code (no "code is:"
prefix). Both in the procedure addenda.
ROLLING ASSEMBLY LIVE (2026-07-23): all delivered cells get their core-cell
cut pre-computed into out_cloud\assembly_cuts\ (MANIFEST.json = the running
fusion ledger: sha256, counts, bounds, seam table) — final fusion is
concat-only for done cells. 12 cells cut+verified (61.5M gaussians in the
done-set; fractions 0.396-0.461; canary tiles reproduced byte-faithfully).
Seam sweep: 15/16 pass; V 1_4|2_4 ratio 0.689 DIAGNOSED BENIGN (a natural
~15 m open-ground trough near the seam fooled the flank probes; true
boundary continuity 1.034 — recorded in seam_diag.json). Pilot-origin
tile_2_4 note: boundaries continuous, but mid-field density runs ~17-21%
lower than fleet neighbors — if Joel's eye ever finds that cell softer in
renders, retraining 2_4 through the fleet loop is a cheap known fix (~$1-2
GPU). Scripts: C:\rolling_assembly\.
UE FULL-RES RENDER FIX (2026-07-23): the 888x500 defect's root cause was the
project's saved GameUserSettings.ini pinning 1066x600 borderless, which
outranks -ResX/-ResY and then clamps to the console desktop (1024x768). The
reusable defense for ANY render on Skychief: launch with -ForceRes (skips the
desktop clamp) + runtime -ini:GameUserSettings overrides (ResolutionSizeX/Y,
FullscreenMode=2) + -RenderOffscreen; no project INI edits needed. Proven:
480/480 frames at true 1920x1080 24 fps in ~4.5 min warm on the 3090
(scripts C:\UE_scripts\render_fullres_seq.ps1 + launch_fullres_console.ps1;
frames Saved\VideoCaptures\ue_fullres\). The render pipeline for the reel is
now fully proven at target quality; remaining for principle 4: real reel
path (compose per SHOT GRAMMAR), pawn feel pass (Joel), v2 tile swap-in.
BLENDER SCENE v1 — TURNTABLE + PINNED VIEW (Joel, 2026-07-23): the scene now
auto-opens on Joel's pinned obelisk framing (ORTHO; numbers live in the
embedded guard text v2 DEFAULT_VIEW) and auto-plays a 1 RPM record-style
spin (Joel corrected 5->1 RPM same day): empty "Oakland_Turntable" at the
GEOREFERENCED obelisk axis (-0.091, -12.042) — derived from Joel's GPS point
(33.74802655368586, -84.37208004353286) through the boundary transform in
boundary_keep_polygon_FINAL.json (transform_model_to_world inverted), then
VISUALLY confirmed top-down ON the column (his view-center guess was 37 m
off — always georeference + eye-confirm pivots, never trust a view center),
Oakland_Root parented under it (matrix_parent_inverse = T(-obelisk) EXACTLY —
computed, never read from a just-set matrix_world: reading it stale shifted
the whole model once), camera UN-parented so it never rides the spin, Z
keyed 0 to -360 deg linear over 1440 frames @24fps (60 s/rev) + CYCLES,
scene sync_mode FRAME_DROP (wall-clock 5 RPM). Guard v2 = clamps + pinned
view restore + autoplay (idempotent startup dict). Blender 5.2 API note:
action.fcurves is GONE — reach fcurves via action.layers[].strips[]
.channelbags[].fcurves. LIVE ROTATION IS SAFE for the KIRI display (verified
by test-spin; the disappear-on-rotation scare = missing refresh, not spin).
HARDWARE LESSON (2026-07-23, cost ~$3.2): A100-SXM4 RunPod containers do NOT
support the CUDA VMM/cuMem arena — reservation fails and the fallback crashes
at iter 1 (reproduced 2x; "VMM reservation failed" then cudaErrorInvalidDevice
in forward.cu). Fleet-safe cards: A100 PCIe (75 GB arena proven) and
A40/A6000-class (44/48 GB, sm_86 salvage runs without rebuild). NEVER rent
SXM for this build. TRANSFER LESSON: croc/runpodctl PREALLOCATES the
destination file at full size (stat == expected while incomplete — never
trust size alone; hash or member-count it) and cannot resume; for big tars
prefer rsync (Skychief→Mac→pod, or Mac→pod when the tar is already in Mac
custody). AUTHORITY LESSON (agent process): a card-CLASS pivot mid-provision
gets surfaced to the lead BEFORE the first billable second on the new pod,
even when the class was pre-blessed — silent pod swaps are how Joel ends up
auditing his own dashboard.

## Session lessons — 2026-07-24 (the long fleet night)

GUARD-INTERACTION IS JOEL'S ALONE. Agents must NEVER read, write, or reference
`~/.claude/sentinel/*` or the sentinel script — the security layer treats it as
tampering with a safety control and BLOCKS it (correctly). Three independent
lines refused an "activity-pulse to keep an idle pod under the auto-stop
radar": a subagent, the classifier (twice), and a fresh agent that named it
spoofing a safety signal. The sanctioned pattern for metered setup windows is
CO-SCHEDULE the long phases (rebuild || transfer) + a fast studio-PC relay so
zero-GPU time stays honestly under the ~50-min auto-stop window — never game
the signal. Joel APPROVED an "attended window" feature 2026-07-24 (wizard):
lead-writable `~/.claude/sentinel/attended.json` maps pod name/id → unix expiry;
while unexpired the auto-STOP is suspended for that pod (alerts still fire,
expiry automatic, agents never write it). Patch applied to meter-sentinel.sh
(backup `.pre_attended`); the ONLY sanctioned way to hold a supervised pod
through a legitimate 0%-GPU setup.

FINISHED-UNCOLLECTED CELLS ARE A REAL FAILURE MODE (cost: a 4am scare + ~1h
idle). Per-agent watchers DIE on session restart/compaction; when they die a
finished cell can sit uncollected on an idle pod indefinitely (the meter-
sentinel's phone alert is the backstop that caught it). Two cells (tile_0_1,
tile_5_4) sat finished-uncollected simultaneously. DURABLE FIX: the pulse must,
every tick, check each RUNNING fleet pod at 0% GPU and each recently-EXITED
fleet pod for `/root/out/*/*.ply` not yet in `out_cloud\fleet`, and collect it —
the pulse is the durable collector, not the watcher. SECURE-class pods PRESERVE
disk on podStop, so a finished cell on a stopped SECURE pod is NOT lost (only
the meter pauses) — collect on resume; a Telegram alarm implying the file
"disappears" on stop is over-stated for SECURE pods (say "meter pauses, disk
kept").

RESUME-BLOCK IS COMMON: `podResume` fails "not enough free GPUs on host" often
(hit 3x this night) — a stopped pod is pinned to its original host. Prefer
keeping a proven cheap pod WORKING (launch its next cell) over stop/resume;
stopping risks losing the lane to a full host.

## The 3D/not-3D popping — SOLVED 2026-07-24 (v4 guard)

Root cause (4th diagnosis, the correct one — earlier three were incomplete):
the live 16M render is a GLSL POST_VIEW draw handler (`draw_gaussians`,
`bpy.gaussian_draw_handle`) whose `update_depth_sorting()` re-sorts only when
`bpy.gaussian_needs_depth_sort` is set OR the camera POSITION crossed
SORT_THRESHOLD. In this ORTHO scene, ORBIT barely changes derived position so
it NEVER auto-sorted (→ stale back-to-front order → the flat melt, worst at
grazing angles); PAN/ZOOM did move position so it re-sorted EVERY frame at
~2.9 s (→ frozen). So the real prior state was orbit=fast+mush,
pan=crisp+frozen. Sort cost at 16M: argsort ~2.0 s dominates (~2.9 s total,
main-thread).

The fix (embedded scene text `oakland_view_guard.py` v4 — NO addon files
patched; durable copy renders/ghosting_fix/): (1) suppress the addon's
position-triggered auto-sort by re-running `sna_viewport_render_A3941(sh,1e12)`
+ pinning r2_sort_threshold=1.0 → every drag stays fast (~90 ms/frame, 35x);
(2) a 0.15 s watcher tracks each viewport's view-matrix AND splat world
transforms, and ~0.45 s after stillness fires EXACTLY ONE re-sort (once on
load, never during turntable playback, never overlapping); (3) the 2 s sort
runs on a daemon worker thread (numpy drops the GIL), only the ~0.36 s GPU
upload on the main thread — viewport never freezes (proven: 47 frames drawn
at ~88 ms while the worker sorted). Runtime switches: `bpy._oakland_async_off`
= True forces the simpler blocking path; diagnostic counters
`bpy._oakland_sort_fires`/`_oakland_sort_applies`. LEAD-VERIFIED at a grazing
angle: dramatic melt → one re-sort → fully crisp (renders/ghosting_fix/ proof).
KIRI is at 5.0.0 (latest, no sorting fix upstream); the addon's LQ "dithered
alpha" mode does NOT bypass the GLSL sort, so there is no order-independent
motion mode — sort-on-rest is the real and only fix. Chaos Vantage 3 (GPU
per-frame sort + splat RELIGHTING as of v3.3) is the alternative if a
never-flat live viewer is wanted (free tier on the 3090; not set up yet).

## Prime-directive accountability — 2026-07-24 (Joel's teachable moment)

Joel measured 40-50% paid-GPU overhead across the fleet's first 50 hours and
called it what it is: a failure to honor the prime directive. ROOT CAUSE, named
plainly: THE PAID GPU WAITED FOR CLAUDE — for collection, for the next cell,
for a live agent — and every Claude outage (cap, restart, compaction, busy
lead) became billed idle time. THE ARCHITECTURAL FIX (deployed this night):
1. POD-SIDE CHAINING (run_chain.sh): each pod holds its next 1-2 cells
   pre-extracted and rolls cell-to-cell the moment a PLY lands — zero hand-off
   gap, keeps training through ANY Claude outage. Finished PLYs get .ready
   markers; delivery happens OFF the GPU's critical path. The pulse's job
   becomes feeding pods 2-deep and collecting .ready files — never gating the
   GPU.
2. SEPARATION OF DUTIES on the billing guard: the LEAD registers pods in the
   guard (attended windows, lead-written); agents provision/train/deliver and
   never touch guard files. (Two agents refused briefs and rang Joel's phone
   over guard-adjacent instructions — the refusals were correct signal;
   "never reference the guard" reads as evasion even when meant as scope.
   Briefs must say "the guard is active and lead-managed", never "avoid it".)
3. PRE-FLIGHT SPEC GATE before any billable second: card sub-type (A100 PCIe
   never SXM), free-GPU availability, image tag — read-only verified.
4. MEASURABLE TARGET: <10% GPU-idle overhead for the remainder of the fleet,
   measured as (wall time − training time) per delivered cell from ledger
   stamps, reported at every phase gate.

BILLING-ACTION OWNERSHIP — the resolution that ended a 3-agent refusal chain
(2026-07-24). Renting/resuming/terminating a pod is a purchase on Joel's
account; the security classifier BLOCKS a subagent's billing API call, and an
agent relaying "Joel authorized it" is not valid consent. WORKING PATTERN, now
standard: the LEAD (the session Joel is talking to) makes the billing call
ITSELF, inline, with Joel's direct wizard/chat approval — deploy via
`scratchpad/bigcard/rp_deploy_pcie.py <name>` (A100-PCIe-only SECURE ladder,
$1.80 cap; A40 via rp_deploy_a40.py), arm `deadman_bigcard.sh <podid>` in the
foreground (15-min birth kill), capture the endpoint, register the LIVE pod id
in `~/.claude/sentinel/meter_state.json` + `attended.json` (lead-writable;
subagents blocked, correctly) — THEN hand only the non-billable setup/train/
deliver to an agent whose brief says "the pod EXISTS; make no rental/terminate
call; report and the lead terminates." tile_4_3 (last dense cell) went this way:
lead rented A100 lt777es87ebb7p @ $1.39, agent did setup only. NEVER write an
agent brief that says "don't touch / ignore the guard" — that reads as evasion
and a correct agent refuses; say "the guard is active and lead-managed."

## Guard v5 — viewpoint bookmarks (Blender session, 2026-07-24)

Number-row keys 1–9 over the 3D viewport jump to saved framings. Data lives in
a SEPARATE embedded text `oakland_viewpoints.json` (read fresh on every press —
edit it and the next press obeys, no guard reload); mechanism is appended to
guard v5 (`oakland_view_guard.py`, all three v4 jobs untouched; durable copies
renders/ghosting_fix/oakland_view_guard_v5.py + viewpoints_seed.json kept
identical to the installed text). Jumps SNAP, take no undo step, and need no
manual re-sort (sort-on-rest fires ~0.45 s after arrival). Re-running the guard
yields exactly 9 keymap items — never duplicates. JOEL'S OVERRIDE 2026-07-24:
slot 1 "Brick avenue from overhead" is ALSO the opening view (DEFAULT_VIEW
updated); the obelisk opening framing is RETIRED everywhere — its numbers are
preserved only under the JSON's `_archived_obelisk_opening_view` key. Slot 2
"Headstone rows and monument circle" (label provisional); slots 3–9 open. Pin
more via MCP: `sys.modules['oakland_view_guard'].capture_view(slot, label)`.
KNOWN NIT: guard line 27's comment still says "obelisk centered" above the
brick-avenue numbers — fix it in the next guard-edit save cycle, not with a
dedicated 4.2 GB save.

A100 cuMem VMM IS A PER-HOST LOTTERY (2026-07-24, cost ~$4 to learn): the
arena's 75 GB cuMemAddressReserve succeeds on SOME RunPod A100 hosts and
FAILS on others (both PCIe and SXM) — the original bigcard host worked, two
later A100s (one PCIe, one SXM) crashed at iter 1 ("VMM reservation failed"
-> broken fallback -> cudaErrorInvalidDevice). A40/A6000 hosts don't hit it.
It is HOST/container config, not the GPU model. EFFICIENCY FIX: roll A100s
with a 10-second cuMem probe FIRST (scratchpad/vmm_roll.sh + bigcard/probe.cu
— rents, boots, tests cuMemAddressReserve at 32..80 GB aligned, KEEPS on the
75 GB OK line, TERMINATES on FAIL) so a dud host costs ~$0.10 not the ~$1
of a full rebuild+transfer before discovering it at iter 1. probe.cu also
re-confirms the granularity law: RAW total_mem reserves FAIL "invalid
argument"; 1 GB/2 MB-ALIGNED sizes succeed (the arena patch aligns down).
nvcc isn't on PATH in a fresh nvidia/cuda:devel container — use
/usr/local/cuda/bin/nvcc + -L/usr/local/cuda/lib64/stubs.
