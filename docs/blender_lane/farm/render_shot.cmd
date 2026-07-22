@echo off
REM render_shot.cmd <shot.json> -- render ONE shot in a fresh GUI Blender process.
REM Launched once per shot by run_queue.ps1 (crash-safe isolation). GUI mode (no
REM --background) so KIRI's GPU render pipeline has the live RTX 3090 context.
set "BL=C:\blender_lane\blender-5.1.2-windows-x64\blender.exe"
"%BL%" --python C:\blender_lane\farm\render_shot.py -- %1
