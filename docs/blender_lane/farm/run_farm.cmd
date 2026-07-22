@echo off
REM run_farm.cmd -- double-click this FROM the logged-in console session (physical
REM login, autologin, or a session redirected to console via tscon) to run the whole
REM shot queue. Its child GUI Blender processes then render on the RTX 3090.
title Oakland Blender Render Farm
powershell -NoProfile -ExecutionPolicy Bypass -File C:\blender_lane\farm\run_queue.ps1
echo.
echo Queue finished. See farm\out\ for frames and farm_status.json for the summary.
pause
