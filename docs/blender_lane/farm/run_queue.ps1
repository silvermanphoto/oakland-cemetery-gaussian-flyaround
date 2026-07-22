# run_queue.ps1 -- sequential, unattended shot queue runner for the Blender render farm.
# MUST run INSIDE the logged-in console session (so its child GUI Blender gets the 3090 GL
# context). Start it from the console by double-clicking run_farm.cmd, or on-demand via the
# interactive scheduled task (register_farm_task.ps1).
#
# Reads queue.json, renders each pending shot in its OWN Blender process (crash-safe
# isolation), enforces a per-shot watchdog (backstop over render_shot.py's own watchdog),
# checks free RAM before each launch, and writes queue.json + farm_status.json after every
# shot so progress is always visible and a crash resumes where it left off.
$ErrorActionPreference = "Continue"
$FARM   = "C:\blender_lane\farm"
$QUEUE  = Join-Path $FARM "queue.json"
$STATUS = Join-Path $FARM "farm_status.json"
$BL     = "C:\blender_lane\blender-5.1.2-windows-x64\blender.exe"

function Write-Status($obj) { $obj | ConvertTo-Json -Depth 6 | Out-File -Encoding ASCII $STATUS }
function Now() { (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") }

if (!(Test-Path $QUEUE)) { Write-Output "No queue.json at $QUEUE"; exit 1 }
if (!(Test-Path $BL))    { Write-Output "Blender not found at $BL"; exit 1 }

$q = Get-Content $QUEUE -Raw | ConvertFrom-Json
$shots = @($q.shots)
Write-Output ("[QUEUE] " + $shots.Count + " shots; " + (($shots | Where-Object {$_.state -eq 'pending'}).Count) + " pending.")

$done = 0; $failed = 0; $skipped = 0
for ($i = 0; $i -lt $shots.Count; $i++) {
    $s = $shots[$i]
    if ($s.state -ne "pending") { continue }
    $shotPath = $s.shot
    if (!(Test-Path $shotPath)) { $s.state = "missing"; continue }

    $shot = Get-Content $shotPath -Raw | ConvertFrom-Json
    $shotId = $shot.shot_id
    $outDir = $shot.output_dir
    $watchdog = [double]($shot.watchdog_s); if (-not $watchdog) { $watchdog = 1800 }
    $procTimeout = [int]($watchdog + 180)   # backstop over render_shot.py's own quit

    # free-RAM gate (import needs ~2.2 GB per million gaussians; guard also lives in the py)
    $os = Get-CimInstance Win32_OperatingSystem
    $freeGB = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
    Write-Output ("[QUEUE] shot " + ($i+1) + "/" + $shots.Count + "  " + $shotId + "  freeRAM=" + $freeGB + "GB  watchdog=" + $watchdog + "s")
    Write-Status @{ updated=(Now); running=$shotId; index=($i+1); total=$shots.Count; done=$done; failed=$failed; skipped=$skipped; freeRAM_GB=$freeGB }

    if (Test-Path $outDir) { Remove-Item (Join-Path $outDir "*.png") -ErrorAction SilentlyContinue }
    else { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }

    $s.state = "running"; $s.started = (Now)
    ($q | ConvertTo-Json -Depth 6) | Out-File -Encoding ASCII $QUEUE

    # one Blender process per shot; GUI mode; wait with a hard timeout backstop
    $t0 = Get-Date
    $p = Start-Process -FilePath $BL -ArgumentList @("--python", (Join-Path $FARM "render_shot.py"), "--", $shotPath) -PassThru
    $exited = $p.WaitForExit($procTimeout * 1000)
    if (-not $exited) {
        Write-Output ("[QUEUE] " + $shotId + " exceeded " + $procTimeout + "s -> killing")
        try { $p.Kill() } catch {}
        Start-Sleep -Seconds 3
        $s.state = "failed_timeout"
        $failed++
    } else {
        # read the shot result the python wrote
        $rp = Join-Path $outDir "shot_result.json"
        if (Test-Path $rp) {
            $r = Get-Content $rp -Raw | ConvertFrom-Json
            if ($r.aborted)      { $s.state = "skipped_oom"; $skipped++ }
            elseif ($r.ok)       { $s.state = "done"; $s.frames = $r.n_frames; $done++ }
            elseif ($r.timed_out){ $s.state = "failed_render_timeout"; $failed++ }
            else                 { $s.state = "failed"; $s.error = ("" + $r.error); $failed++ }
        } else {
            $s.state = "failed_no_result"   # Blender crashed before writing result
            $failed++
        }
    }
    $s.finished = (Now)
    $s.wall_s = [math]::Round(((Get-Date) - $t0).TotalSeconds, 0)
    ($q | ConvertTo-Json -Depth 6) | Out-File -Encoding ASCII $QUEUE
    Write-Output ("[QUEUE] " + $shotId + " -> " + $s.state + " (" + $s.wall_s + "s)")
}

Write-Status @{ updated=(Now); running=$null; done=$done; failed=$failed; skipped=$skipped; total=$shots.Count; finished=$true }
Write-Output ("[QUEUE] COMPLETE. done=" + $done + " failed=" + $failed + " skipped=" + $skipped)
