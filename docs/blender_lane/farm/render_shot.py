# render_shot.py -- per-shot full-quality KIRI splat render controller.
# Runs inside a GUI Blender session (NOT --background) so the RTX 3090 GL context is live.
#
#   blender.exe --python render_shot.py -- <shot.json>
#
# One Blender process renders exactly ONE shot, then quits -> crash-safe isolation.
# The queue runner (run_queue.ps1) launches one of these per shot and enforces the watchdog.
#
# What it does, in order:
#   1. Parse the shot JSON.
#   2. MEMORY GUARD: read each tile's PLY vertex count from the header (exact, no import),
#      project RAM = total_million * gb_per_million; ABORT before importing if it exceeds budget.
#   3. Enable the KIRI extension; log the live GL renderer (proves the 3090 is bound).
#   4. Import each tile via KIRI's real operator sna.dgs_render_import_ply_e0a3a.
#   5. Build a camera and key it along the shot's path (explicit keyframes OR auto_orbit).
#   6. Set KIRI render properties (SH degree, color, animation) + scene resolution/frame range.
#   7. Trigger KIRI Advanced Render (sna.dgs_render_advanced_render_147af) -- the offscreen
#      GLSL pipeline that needs a live GPU context (works in GUI, impossible headless).
#   8. Poll for output frames (handles a modal/async render) with a watchdog; harvest any
#      frames written to the temp dir into output_dir; write a shot_result.json; quit.
#
# UNVERIFIED-UNTIL-FIRST-GUI-RUN (documented, defensively handled here):
#   - KIRI's exact output-path / resolution property names. We set every plausible one and
#     DUMP the full property list to render_shot.log so the first real run reveals the truth.
#   - Whether Advanced Render is synchronous or modal. The timer-poll handles both.
#   - Whether the operator needs a VIEW_3D context. We try a context override, then a plain call.
import bpy, sys, os, json, time, glob, shutil, tempfile, traceback

def log(m):
    print("[SHOT] " + str(m), flush=True)

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
def hard_quit(code=0):
    # Under GUI Blender, sys.exit() does NOT reliably end the process (the event loop
    # keeps running). os._exit guarantees the process exits so the queue's WaitForExit
    # returns immediately on abort paths instead of waiting for the watchdog.
    try:
        bpy.ops.wm.quit_blender()
    except Exception:
        pass
    os._exit(code)

if not argv:
    log("FATAL: no shot json given (blender --python render_shot.py -- shot.json)")
    os._exit(2)
SHOT_JSON = argv[0]

with open(SHOT_JSON) as f:
    shot = json.load(f)

SHOT_ID   = shot.get("shot_id", os.path.splitext(os.path.basename(SHOT_JSON))[0])
TILE_DIR  = shot["tile_dir"]
TILES     = shot["tiles"]
OUT_DIR   = shot["output_dir"]
RES       = shot.get("resolution", [1920, 1080])
SH_DEG    = int(shot.get("sh_degree", 3))
BUDGET_GB = float(shot.get("mem_budget_gb", 45.0))
GB_PER_M  = float(shot.get("gb_per_million_gaussians", 2.2))
CAM       = shot.get("camera", {})
os.makedirs(OUT_DIR, exist_ok=True)

LOGP = os.path.join(OUT_DIR, "render_shot.log")
def flog(m):
    log(m)
    try:
        with open(LOGP, "a") as f:
            f.write(time.strftime("%H:%M:%S ") + str(m) + "\n")
    except Exception:
        pass

result = {"shot_id": SHOT_ID, "shot_json": SHOT_JSON, "ok": False, "started": time.strftime("%Y-%m-%d %H:%M:%S")}
t_all = time.time()

def dump_result(extra=None):
    if extra:
        result.update(extra)
    result["wall_s"] = round(time.time() - t_all, 1)
    with open(os.path.join(OUT_DIR, "shot_result.json"), "w") as f:
        json.dump(result, f, indent=2)
    flog("RESULT -> shot_result.json  ok=%s" % result.get("ok"))

# ---------- 2. MEMORY GUARD (read PLY vertex counts from headers; no import) ----------
def ply_vertex_count(path):
    # binary PLY header is ASCII up to "end_header"; find "element vertex N"
    n = 0
    with open(path, "rb") as f:
        for _ in range(80):
            line = f.readline()
            if not line:
                break
            s = line.decode("ascii", "ignore").strip()
            if s.startswith("element vertex"):
                n = int(s.split()[-1])
            if s == "end_header":
                break
    return n

tile_paths = [os.path.join(TILE_DIR, t) for t in TILES]
counts = {}
total = 0
for p in tile_paths:
    if not os.path.exists(p):
        flog("FATAL: tile missing: %s" % p)
        dump_result({"error": "tile missing: %s" % p})
        hard_quit(0)
    c = ply_vertex_count(p)
    counts[os.path.basename(p)] = c
    total += c
total_m = total / 1e6
proj_gb = total_m * GB_PER_M
result["gaussian_counts"] = counts
result["gaussian_total"] = total
result["projected_ram_gb"] = round(proj_gb, 1)
flog("tiles=%d  gaussians=%.2fM  projected RAM=%.1f GB (budget %.1f GB, %.2f GB/M)" %
     (len(TILES), total_m, proj_gb, BUDGET_GB, GB_PER_M))
if proj_gb > BUDGET_GB:
    flog("ABORT (memory guard): projected %.1f GB > budget %.1f GB. Split this shot into fewer tiles." %
         (proj_gb, BUDGET_GB))
    dump_result({"error": "memory_guard_abort", "aborted": True})
    hard_quit(0)   # clean exit -> queue marks 'skipped_oom' and continues

# ---------- 3. enable KIRI + log the live GL renderer ----------
import addon_utils
try:
    import gpu
    result["gl_renderer"] = gpu.platform.renderer_get()
    result["gl_vendor"]   = gpu.platform.vendor_get()
    hw = ("NVIDIA" in result["gl_renderer"].upper()) or ("RTX" in result["gl_renderer"].upper())
    result["gl_hardware"] = hw
    flog("GL renderer = %s  (hardware/3090 = %s)" % (result["gl_renderer"], hw))
    if not hw:
        flog("WARNING: GL renderer is not the NVIDIA 3090 -> KIRI's GPU render will be software/blank. "
             "Redirect this session to the physical console (tscon /dest:console) or use a console login.")
except Exception as e:
    flog("GL query note: %s" % e)

for m in addon_utils.modules():
    if "dgs_render" in getattr(m, "__name__", "").lower():
        try:
            addon_utils.enable(m.__name__, default_set=True, persistent=True)
            flog("enabled KIRI: %s" % m.__name__)
        except Exception as e:
            flog("KIRI enable note: %s" % e)

# clear the default scene objects without touching prefs (keeps KIRI loaded)
for o in list(bpy.data.objects):
    try:
        bpy.data.objects.remove(o, do_unlink=True)
    except Exception:
        pass

# ---------- 4. import tiles ----------
t = time.time()
for p in tile_paths:
    flog("import %s ..." % os.path.basename(p))
    ti = time.time()
    bpy.ops.sna.dgs_render_import_ply_e0a3a(filepath=p)
    flog("  imported in %.1fs" % (time.time() - ti))
result["import_s"] = round(time.time() - t, 1)
result["objects_after_import"] = len(bpy.data.objects)

# ---------- compute world bbox of imported geometry ----------
import mathutils
mins = [1e18, 1e18, 1e18]
maxs = [-1e18, -1e18, -1e18]
for o in bpy.data.objects:
    if o.type in ("MESH", "POINTCLOUD"):
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            for i in range(3):
                mins[i] = min(mins[i], w[i]); maxs[i] = max(maxs[i], w[i])
center = mathutils.Vector([(mins[i] + maxs[i]) / 2 for i in range(3)])
size = mathutils.Vector([maxs[i] - mins[i] for i in range(3)])
result["bbox_min"] = [round(x, 2) for x in mins]
result["bbox_max"] = [round(x, 2) for x in maxs]
flog("imported bbox min=%s max=%s center=(%.1f,%.1f,%.1f)" %
     (result["bbox_min"], result["bbox_max"], center.x, center.y, center.z))

# ---------- 5. build camera + keyframes ----------
UP = CAM.get("up_axis", "Y").upper()
up_vec = {"X": mathutils.Vector((1, 0, 0)),
          "Y": mathutils.Vector((0, 1, 0)),
          "Z": mathutils.Vector((0, 0, 1))}.get(UP, mathutils.Vector((0, 1, 0)))

cam_data = bpy.data.cameras.new(SHOT_ID + "_cam")
cam_data.lens = float(CAM.get("lens_mm", 35))
if "sensor_mm" in CAM:
    cam_data.sensor_width = float(CAM["sensor_mm"])
cam_data.clip_start = float(CAM.get("clip_start", 0.1))
cam_data.clip_end = float(CAM.get("clip_end", 100000.0))
cam = bpy.data.objects.new(SHOT_ID + "_cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

def aim(location, look_at):
    loc = mathutils.Vector(location)
    tgt = mathutils.Vector(look_at)
    cam.location = loc
    cam.rotation_euler = (tgt - loc).to_track_quat('-Z', UP).to_euler()

# Build the keyframe list. PRIMARY interface = explicit world-space keyframes.
# Convenience for the canary = auto_orbit computed from the imported bbox.
kfs = []
if "keyframes" in CAM and CAM["keyframes"]:
    for k in CAM["keyframes"]:
        frame = int(k["frame"])
        loc = k["location"]
        if "look_at" in k:
            kfs.append((frame, loc, k["look_at"], None))
        else:
            kfs.append((frame, loc, None, k.get("rotation_euler")))
elif "auto_orbit" in CAM:
    ao = CAM["auto_orbit"]
    frames = int(ao.get("frames", 3))
    arc = float(ao.get("arc_deg", 40.0))
    dist_f = float(ao.get("dist_factor", 1.2))
    height_f = float(ao.get("height_factor", 0.55))
    az0 = float(ao.get("az_start_deg", 45.0))
    import math
    # horizontal plane = the two non-up axes
    axes = [0, 1, 2]
    up_i = {"X": 0, "Y": 1, "Z": 2}[UP]
    h_axes = [a for a in axes if a != up_i]
    hr = math.sqrt((size[h_axes[0]]) ** 2 + (size[h_axes[1]]) ** 2) / 2.0 or 10.0
    R = dist_f * hr
    H = height_f * hr
    for i in range(frames):
        az = math.radians(az0 + (arc * i / max(1, frames - 1)))
        loc = [0.0, 0.0, 0.0]
        loc[h_axes[0]] = center[h_axes[0]] + R * math.cos(az)
        loc[h_axes[1]] = center[h_axes[1]] + R * math.sin(az)
        loc[up_i] = center[up_i] + H
        kfs.append((i + 1, loc, [center.x, center.y, center.z], None))
else:
    # fallback: a single oblique frame on the bbox
    diag = size.length or 10.0
    loc = [center.x + diag * 0.55, center.y + diag * 0.55, center.z - diag * 0.75]
    kfs.append((1, loc, [center.x, center.y, center.z], None))

frame_nums = [k[0] for k in kfs]
f_start, f_end = min(frame_nums), max(frame_nums)
for (frame, loc, look_at, rot) in kfs:
    bpy.context.scene.frame_set(frame)
    if look_at is not None:
        aim(loc, look_at)
    else:
        cam.location = mathutils.Vector(loc)
        if rot:
            cam.rotation_euler = mathutils.Euler(rot)
    cam.keyframe_insert(data_path="location", frame=frame)
    cam.keyframe_insert(data_path="rotation_euler", frame=frame)
result["frames"] = [f_start, f_end]
result["n_frames"] = f_end - f_start + 1
flog("camera keyed: frames %d..%d (%d frames), up=%s" % (f_start, f_end, result["n_frames"], UP))

# ---------- 6. scene + KIRI render properties ----------
scn = bpy.context.scene
scn.render.resolution_x = int(RES[0])
scn.render.resolution_y = int(RES[1])
scn.render.resolution_percentage = 100
scn.render.image_settings.file_format = 'PNG'
scn.frame_start = f_start
scn.frame_end = f_end
scn.render.filepath = os.path.join(OUT_DIR, "frame_")

props = getattr(scn, "sna_dgs_scene_properties", None)
if props is None:
    flog("FATAL: scn.sna_dgs_scene_properties missing -> KIRI not enabled. Aborting.")
    dump_result({"error": "kiri_props_missing"})
    hard_quit(0)

# DUMP the full KIRI property list so the first GUI run reveals the real output/res property names.
try:
    names = [p.identifier for p in props.bl_rna.properties if not p.is_readonly or True]
    flog("KIRI sna_dgs_scene_properties (%d): %s" % (len(names), ", ".join(names)))
    result["kiri_props"] = names
except Exception as e:
    flog("prop dump note: %s" % e)

def setp(name, val):
    try:
        setattr(props, name, val)
        flog("  set %s = %s" % (name, val))
    except Exception as e:
        flog("  set %s FAILED: %s" % (name, str(e)[:100]))

# The r2_* names are verified from the KIRI 5.0.0 canary; others are best-effort and
# will simply no-op+log if the real name differs (revealed by the dump above).
setp("r2_animation", result["n_frames"] > 1)
setp("r2_color", True)
setp("r2_depth", False)
setp("r2_comp", False)
setp("r2_transforms", False)
setp("r2_delete_temp_files", False)   # KEEP temp frames so we can harvest them
setp("r2_sh_degree", SH_DEG)
# plausible output/resolution props -- set ONLY if KIRI actually exposes them
# (names differ across builds; the dump above is the source of truth).
_known = result.get("kiri_props", []) or []
for nm, vl in (("r2_output_path", OUT_DIR), ("r2_folder", OUT_DIR), ("r2_path", OUT_DIR),
               ("r2_res_x", int(RES[0])), ("r2_res_y", int(RES[1])),
               ("r2_resolution_x", int(RES[0])), ("r2_resolution_y", int(RES[1]))):
    if nm in _known:
        setp(nm, vl)

TEMP_RENDER = os.path.join(tempfile.gettempdir(), "gaussian_render")

# ---------- 7. trigger KIRI Advanced Render (needs the live GPU context) ----------
def find_view3d_override():
    for win in bpy.context.window_manager.windows:
        scr = win.screen
        for area in scr.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        return {"window": win, "screen": scr, "area": area, "region": region}
    return None

def call_advanced_render():
    op = bpy.ops.sna.dgs_render_advanced_render_147af
    ov = find_view3d_override()
    try:
        if ov:
            with bpy.context.temp_override(**ov):
                op()
            flog("advanced_render called with VIEW_3D override")
        else:
            op()
            flog("advanced_render called (no VIEW_3D override found)")
        return True
    except Exception as e:
        flog("advanced_render EXC: %s" % str(e)[:300])
        flog(traceback.format_exc()[:1200])
        return False

flog("calling KIRI Advanced Render ...")
result["render_called"] = call_advanced_render()
t_render0 = time.time()

# ---------- 8. poll for output frames with a watchdog (handles sync OR modal render) ----------
WATCHDOG_S = float(shot.get("watchdog_s", 1800))
EXPECT = result["n_frames"]

def harvest():
    got = []
    for d in (OUT_DIR, TEMP_RENDER):
        if os.path.isdir(d):
            for pat in ("*.png", "*.PNG", "*.jpg", "*.exr"):
                for fp in glob.glob(os.path.join(d, "**", pat), recursive=True):
                    got.append(fp)
    # copy any temp-dir frames into OUT_DIR
    for fp in got:
        if os.path.dirname(fp) != OUT_DIR and TEMP_RENDER in fp:
            try:
                shutil.copy2(fp, os.path.join(OUT_DIR, os.path.basename(fp)))
            except Exception:
                pass
    out_frames = sorted(set(glob.glob(os.path.join(OUT_DIR, "*.png")) +
                            glob.glob(os.path.join(OUT_DIR, "*.PNG"))))
    return out_frames

def poll():
    elapsed = time.time() - t_render0
    frames = harvest()
    n = len(frames)
    if n >= EXPECT and EXPECT > 0:
        flog("DONE: %d/%d frames after %.1fs" % (n, EXPECT, elapsed))
        result["ok"] = True
        result["render_s"] = round(elapsed, 1)
        result["frames_written"] = frames
        dump_result()
        try:
            bpy.ops.wm.quit_blender()
        except Exception:
            os._exit(0)
        return None
    if elapsed > WATCHDOG_S:
        flog("WATCHDOG TIMEOUT at %.0fs with %d/%d frames -> quitting" % (elapsed, n, EXPECT))
        result["ok"] = (n > 0)
        result["render_s"] = round(elapsed, 1)
        result["frames_written"] = frames
        result["timed_out"] = True
        dump_result()
        try:
            bpy.ops.wm.quit_blender()
        except Exception:
            os._exit(0)
        return None
    return 3.0   # poll every 3s

# If the render was synchronous, frames may already exist -> one harvest, then timer confirms.
bpy.app.timers.register(poll, first_interval=2.0)
flog("polling for output (expect %d frames, watchdog %.0fs) ..." % (EXPECT, WATCHDOG_S))
