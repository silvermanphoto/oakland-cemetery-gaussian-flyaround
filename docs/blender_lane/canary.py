# canary.py  --  Blender headless canary for the Oakland Cemetery Blender lane (26-029)
# Runs INSIDE Blender:  blender --background --factory-startup --python canary.py -- <tile.ply> <ENGINE> <outdir>
#   <ENGINE> = EEVEE | CYCLES
# Job: enable the KIRI 3DGS Render addon, import ONE full-count tile, frame an
#      oblique aerial camera on it, render one frame, and log timings + the
#      addon's real operator names. Memory/VRAM peaks are sampled by the PS wrapper.
#
# Nothing here is destructive; it writes only into <outdir>. Designed so a crash
# is a clean process exit with a full log, not a hung GUI.

import bpy, sys, os, time, json, traceback, addon_utils

def log(msg):
    print("[CANARY] " + str(msg), flush=True)

# ---- args after the "--" ---------------------------------------------------
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
tile     = argv[0] if len(argv) > 0 else ""
engine   = (argv[1] if len(argv) > 1 else "EEVEE").upper()
outdir   = argv[2] if len(argv) > 2 else os.path.dirname(tile)
addonzip = argv[3] if len(argv) > 3 else ""   # optional: install this addon zip if not already present
os.makedirs(outdir, exist_ok=True)

report = {"tile": tile, "engine": engine, "steps": {}, "ok": False}
t_all = time.time()

def dump_report():
    report["wall_total_s"] = round(time.time() - t_all, 1)
    p = os.path.join(outdir, "canary_report.json")
    with open(p, "w") as f:
        json.dump(report, f, indent=2)
    log("REPORT -> " + p)

try:
    # ---- 1. clean scene ----------------------------------------------------
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # ---- 2. find + enable the KIRI 3DGS addon ------------------------------
    # After install the addon registers under a top-level module name. Discover it.
    t = time.time()
    candidates = []
    for m in addon_utils.modules():
        name = getattr(m, "__name__", "")
        bli  = getattr(m, "bl_info", {}) or {}
        label = (bli.get("name", "") + " " + name).lower()
        if any(k in label for k in ("kiri", "3dgs", "gaussian", "splat")):
            candidates.append(name)
    if not candidates and addonzip and os.path.exists(addonzip):
        log("No 3DGS addon registered yet; installing zip: " + addonzip)
        try:
            bpy.ops.preferences.addon_install(filepath=addonzip, overwrite=True)
            addon_utils.modules_refresh()
            for m in addon_utils.modules():
                name = getattr(m, "__name__", "")
                bli  = getattr(m, "bl_info", {}) or {}
                label = (bli.get("name", "") + " " + name).lower()
                if any(k in label for k in ("kiri", "3dgs", "gaussian", "splat")):
                    candidates.append(name)
            log("After install, candidates: " + repr(candidates))
        except Exception as e:
            log("addon_install failed: " + str(e))
    log("Addon module candidates: " + repr(candidates))
    report["steps"]["addon_candidates"] = candidates
    enabled = []
    for name in candidates:
        try:
            addon_utils.enable(name, default_set=True, persistent=True)
            enabled.append(name)
        except Exception as e:
            log("enable failed for %s: %s" % (name, e))
    report["steps"]["addon_enabled"] = enabled
    report["steps"]["addon_enable_s"] = round(time.time() - t, 1)
    if not enabled:
        log("WARNING: no KIRI/3DGS addon enabled. Is the zip installed into THIS Blender?")

    # ---- 3. list every operator the addon exposes (so the full pipeline knows the API) ----
    ops_found = []
    for grp in dir(bpy.ops):
        try:
            mod = getattr(bpy.ops, grp)
            for op in dir(mod):
                token = (grp + "." + op).lower()
                if any(k in token for k in ("kiri", "3dgs", "gaussian", "splat", "gs_")):
                    ops_found.append(grp + "." + op)
        except Exception:
            pass
    log("Operators matching kiri/3dgs/gaussian/splat: " + repr(ops_found))
    report["steps"]["operators"] = ops_found

    # ---- 4. import the tile -----------------------------------------------
    # KIRI's import operator name isn't guaranteed across versions; try the
    # discovered candidates in a sensible order, then a couple of known guesses.
    import_guesses = [o for o in ops_found if "import" in o.lower()]
    import_guesses += [
        "kiri.import_gaussian_splatting", "object.import_gaussian_splatting",
        "kiri_3dgs.import_ply", "gs.import_ply", "import_scene.gaussian_splatting",
    ]
    n_before = len(bpy.data.objects)
    t = time.time()
    imported_via = None
    for guess in import_guesses:
        grp, _, op = guess.partition(".")
        fn = getattr(getattr(bpy.ops, grp, None), op, None)
        if fn is None:
            continue
        for kwargs in ({"filepath": tile}, {"filepath": tile, "directory": os.path.dirname(tile),
                        "files": [{"name": os.path.basename(tile)}]}):
            try:
                log("Trying import operator %s(%s)" % (guess, ",".join(kwargs.keys())))
                fn(**kwargs)
                imported_via = guess
                break
            except Exception as e:
                log("  -> %s failed: %s" % (guess, str(e)[:200]))
        if imported_via:
            break
    report["steps"]["import_operator_used"] = imported_via
    report["steps"]["import_s"] = round(time.time() - t, 1)
    new_objs = [o for o in bpy.data.objects if o.type in ("MESH", "POINTCLOUD", "EMPTY")]
    report["steps"]["objects_after_import"] = len(bpy.data.objects)
    report["steps"]["objects_delta"] = len(bpy.data.objects) - n_before

    if not imported_via:
        log("NO import operator succeeded. Logged the addon's real API above; "
            "edit import_guesses once the correct name is known, then re-run.")
        dump_report()
        sys.exit(3)

    # ---- 5. frame an oblique aerial camera on the imported geometry --------
    import mathutils, math
    # combined world-space bbox of imported objects
    mins = [1e18, 1e18, 1e18]; maxs = [-1e18, -1e18, -1e18]
    for o in bpy.data.objects:
        if o.type in ("MESH", "POINTCLOUD"):
            for c in o.bound_box:
                w = o.matrix_world @ mathutils.Vector(c)
                for i in range(3):
                    mins[i] = min(mins[i], w[i]); maxs[i] = max(maxs[i], w[i])
    center = mathutils.Vector([(mins[i] + maxs[i]) / 2 for i in range(3)])
    diag = mathutils.Vector([maxs[i] - mins[i] for i in range(3)]).length or 10.0
    report["steps"]["bbox_min"] = [round(x, 2) for x in mins]
    report["steps"]["bbox_max"] = [round(x, 2) for x in maxs]
    report["steps"]["bbox_diag"] = round(diag, 2)
    # Data frame: up = -Y (from README). Put the camera high on +Y-up side, pulled
    # back and to a corner for a drone-oblique read; distance ~1.2x the diagonal.
    up = mathutils.Vector((0, -1, 0))              # world up for this data
    dist = diag * 1.2
    cam_pos = center + mathutils.Vector((dist * 0.55, -dist * 0.75, dist * 0.55))
    cam_data = bpy.data.cameras.new("CanaryCam"); cam_data.clip_end = max(10000.0, dist * 10)
    cam = bpy.data.objects.new("CanaryCam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    d = (center - cam_pos)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam.location = cam_pos
    bpy.context.scene.camera = cam

    # ---- 6. render one frame ----------------------------------------------
    scn = bpy.context.scene
    scn.render.resolution_x = 1920
    scn.render.resolution_y = 1080
    scn.render.image_settings.file_format = 'PNG'
    if engine == "CYCLES":
        scn.render.engine = 'CYCLES'
        try:
            prefs = bpy.context.preferences.addons['cycles'].preferences
            prefs.compute_device_type = 'OPTIX'
            prefs.get_devices()
            for dev in prefs.devices:
                dev.use = (dev.type in ('OPTIX', 'CUDA'))
            scn.cycles.device = 'GPU'
        except Exception as e:
            log("Cycles GPU setup note: " + str(e))
        scn.cycles.samples = 64
    else:
        scn.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, 'RenderEngine') else 'BLENDER_EEVEE'
        # 5.x uses BLENDER_EEVEE_NEXT; fall back if unavailable
        try:
            scn.render.engine = 'BLENDER_EEVEE_NEXT'
        except Exception:
            scn.render.engine = 'BLENDER_EEVEE'

    out_png = os.path.join(outdir, "canary_%s.png" % engine.lower())
    scn.render.filepath = out_png
    t = time.time()
    bpy.ops.render.render(write_still=True)
    report["steps"]["render_s"] = round(time.time() - t, 1)
    report["steps"]["render_png"] = out_png
    report["ok"] = os.path.exists(out_png)
    log("RENDER done in %ss -> %s" % (report["steps"]["render_s"], out_png))

    dump_report()

except Exception as e:
    log("FATAL: " + str(e))
    log(traceback.format_exc())
    report["fatal"] = str(e)
    dump_report()
    sys.exit(1)
