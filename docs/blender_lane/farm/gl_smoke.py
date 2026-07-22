# gl_smoke.py -- the definitive "is the RTX 3090 driving OpenGL in this session?" probe.
# Launched by GUI Blender (NOT --background), so a real GPU window/context exists.
# Queries the live GL renderer string, writes it to a file, then quits Blender.
#
# Interpretation of the result written to out\gl_smoke.txt:
#   renderer contains "NVIDIA" / "GeForce RTX 3090"  -> HARDWARE GL bound to the 3090. GO.
#   renderer contains "GDI Generic" / "Microsoft"    -> SOFTWARE GL (RDP virtual display). NO-GO,
#                                                        redirect the session to the physical
#                                                        console (see GUI_SESSION_SETUP.md).
import bpy, os, sys, time

OUT = r"C:\blender_lane\farm\out"
os.makedirs(OUT, exist_ok=True)
path = os.path.join(OUT, "gl_smoke.txt")

def grab():
    import gpu
    info = {
        "when": time.strftime("%Y-%m-%d %H:%M:%S"),
        "renderer": gpu.platform.renderer_get(),
        "vendor":   gpu.platform.vendor_get(),
        "version":  gpu.platform.version_get(),
        "backend":  str(gpu.platform.backend_type_get()),
    }
    # offscreen create is the same call that FAILS in --background; if it works here,
    # KIRI's offscreen GLSL render pipeline can run.
    try:
        off = gpu.types.GPUOffScreen(64, 64)
        off.free()
        info["offscreen_64x64"] = "OK"
    except Exception as e:
        info["offscreen_64x64"] = "FAIL: " + str(e)[:160]
    return info

def write_and_quit():
    try:
        info = grab()
        hw = ("NVIDIA" in info["renderer"].upper()) or ("RTX" in info["renderer"].upper())
        info["verdict"] = "HARDWARE-GL-3090-BOUND" if hw else "SOFTWARE-OR-VIRTUAL-GL"
        lines = ["%s = %s" % (k, info[k]) for k in
                 ("when", "verdict", "renderer", "vendor", "version", "backend", "offscreen_64x64")]
        with open(path, "w") as f:
            f.write("\n".join(lines) + "\n")
        print("[GL_SMOKE] " + " | ".join(lines), flush=True)
    except Exception as e:
        with open(path, "w") as f:
            f.write("GL_SMOKE ERROR: " + str(e) + "\n")
        print("[GL_SMOKE] ERROR " + str(e), flush=True)
    # quit on the next tick so the window has fully initialized its GL context
    try:
        bpy.ops.wm.quit_blender()
    except Exception:
        os._exit(0)
    return None

# run after the window/GL context is live (a short delay is safer than running inline)
bpy.app.timers.register(write_and_quit, first_interval=1.5)
