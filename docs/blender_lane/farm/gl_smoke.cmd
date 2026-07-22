@echo off
REM gl_smoke.cmd -- run INSIDE the logged-in console session. Opens GUI Blender,
REM queries the live GL renderer, writes farm\out\gl_smoke.txt, quits, prints it.
REM This is the FIRST thing to run the moment a GUI session exists.
set "BL=C:\blender_lane\blender-5.1.2-windows-x64\blender.exe"
"%BL%" --python C:\blender_lane\farm\gl_smoke.py
echo ================ GL SMOKE RESULT ================
type C:\blender_lane\farm\out\gl_smoke.txt
echo ================================================
