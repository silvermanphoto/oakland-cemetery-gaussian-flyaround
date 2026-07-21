# run_canary.ps1  --  Skychief-side wrapper for the Oakland Blender-lane canary.
# STAGED, NOT RUN. Run ONLY in a GPU gap between trainings (it self-guards).
#
# What it does:
#   1. Refuses to run unless the RTX 3090 is idle enough (no training in flight).
#   2. Locates a Blender 4.5 / 5.1 install (errors clearly if none -> install step).
#   3. Starts a 2-second sampler of Blender's RAM (WorkingSet64) and nvidia-smi VRAM.
#   4. Launches Blender headless on ONE tile + engine, with a hard timeout kill
#      (crash-recovery: a hang becomes a clean kill + full log, never a wedged GPU).
#   5. Prints peak RAM, peak VRAM, render time, and the canary report.
#
# Usage (once Blender is installed and the GPU is free):
#   powershell -NoProfile -ExecutionPolicy Bypass -File C:\blender_lane\run_canary.ps1 `
#       -Tile "H:\...\tile_1_4.ply" -Engine EEVEE -TimeoutMin 25
#
param(
    [string]$Tile     = "",
    [string]$Engine   = "EEVEE",           # EEVEE | CYCLES
    [int]   $TimeoutMin = 25,
    [int]   $MinFreeVramMB = 20000,        # require ~20GB free => training not running
    [int]   $MaxBusyUtil   = 15,           # abort if GPU util above this (%)
    [string]$Blender  = "",                # optional explicit blender.exe
    [string]$AddonZip = "C:\blender_lane\3dgs_render_by_kiri_engine_5.0.0.zip",
    [string]$OutDir   = ""
)
$ErrorActionPreference = "Stop"
$smi = "C:\Windows\System32\nvidia-smi.exe"

function Get-Gpu {
    $line = (& $smi --query-gpu=memory.free,memory.used,utilization.gpu --format=csv,noheader,nounits) | Select-Object -First 1
    $p = $line -split "," | ForEach-Object { [int]($_.Trim()) }
    return @{ FreeMB = $p[0]; UsedMB = $p[1]; Util = $p[2] }
}

# ---- 1. GPU-gap guard ------------------------------------------------------
$g = Get-Gpu
Write-Host ("GPU now: free={0}MB used={1}MB util={2}%" -f $g.FreeMB, $g.UsedMB, $g.Util)
if ($g.FreeMB -lt $MinFreeVramMB -or $g.Util -gt $MaxBusyUtil) {
    Write-Host "ABORT: GPU is busy (training likely running). Canary must run only in a GPU gap." -ForegroundColor Yellow
    exit 10
}

# ---- 2. locate Blender -----------------------------------------------------
if (-not $Blender) {
    $roots = @("C:\Program Files\Blender Foundation")
    $cands = @()
    foreach ($r in $roots) {
        if (Test-Path $r) {
            $cands += Get-ChildItem $r -Directory -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -match "Blender (4\.5|5\.1|5\.0|4\.[3-9])" } |
                ForEach-Object { Join-Path $_.FullName "blender.exe" } |
                Where-Object { Test-Path $_ }
        }
    }
    $Blender = $cands | Select-Object -Last 1
}
if (-not $Blender -or -not (Test-Path $Blender)) {
    Write-Host "ERROR: No Blender 4.5/5.1 found. INSTALL STEP REQUIRED (free, blender.org):" -ForegroundColor Red
    Write-Host "  Blender 4.5 LTS  ->  https://www.blender.org/download/lts/4-5/   (recommended, supported to 2027)"
    Write-Host "  or Blender 5.1   ->  https://www.blender.org/download/releases/  (KIRI's own recommended target)"
    Write-Host "  NOTE: only Blender 3.0 and 3.4 are currently installed on Skychief; neither runs the 3DGS addons."
    exit 11
}
Write-Host ("Blender: " + $Blender)

if (-not $Tile) { Write-Host "ERROR: -Tile <path to a .ply> required."; exit 12 }
if (-not (Test-Path $Tile)) { Write-Host ("ERROR: tile not found: " + $Tile); exit 12 }
if (-not $OutDir) { $OutDir = "C:\blender_lane\canary_out\" + (Split-Path $Tile -LeafBase) + "_" + $Engine }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$metrics = Join-Path $OutDir "canary_metrics.csv"
$blog    = Join-Path $OutDir "blender_stdout.log"
$canary  = "C:\blender_lane\canary.py"

# ---- 3. background sampler (RAM + VRAM every 2s) ---------------------------
"iso,blender_ram_mb,vram_used_mb,vram_free_mb,util" | Out-File -Encoding ascii $metrics
$sampler = Start-Job -ScriptBlock {
    param($metrics, $smi)
    while ($true) {
        try {
            $bl = Get-Process blender -ErrorAction SilentlyContinue | Sort-Object WorkingSet64 -Descending | Select-Object -First 1
            $ram = if ($bl) { [math]::Round($bl.WorkingSet64/1MB) } else { 0 }
            $line = (& $smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader,nounits) | Select-Object -First 1
            $p = $line -split "," | ForEach-Object { $_.Trim() }
            ("{0},{1},{2},{3},{4}" -f (Get-Date -Format o), $ram, $p[0], $p[1], $p[2]) |
                Out-File -Append -Encoding ascii $metrics
        } catch {}
        Start-Sleep -Seconds 2
    }
} -ArgumentList $metrics, $smi

# ---- 4. launch Blender headless with a hard timeout ------------------------
Write-Host ("Launching canary: tile=" + (Split-Path $Tile -Leaf) + " engine=" + $Engine + " timeout=" + $TimeoutMin + "min")
$args = @("--background","--factory-startup","--python",$canary,"--",$Tile,$Engine,$OutDir,$AddonZip)
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$proc = Start-Process -FilePath $Blender -ArgumentList $args -PassThru -NoNewWindow `
        -RedirectStandardOutput $blog -RedirectStandardError ($blog + ".err")
if (-not $proc.WaitForExit($TimeoutMin * 60 * 1000)) {
    Write-Host ("TIMEOUT after {0} min -- killing Blender (crash-recovery path)." -f $TimeoutMin) -ForegroundColor Yellow
    try { $proc.Kill($true) } catch { try { taskkill /PID $proc.Id /T /F | Out-Null } catch {} }
    $timedout = $true
} else { $timedout = $false }
$sw.Stop()
Stop-Job $sampler -ErrorAction SilentlyContinue | Out-Null
Receive-Job $sampler -ErrorAction SilentlyContinue | Out-Null
Remove-Job $sampler -Force -ErrorAction SilentlyContinue | Out-Null

# ---- 5. summarize ----------------------------------------------------------
Write-Host "================ CANARY SUMMARY ================"
Write-Host ("wall_clock_s     : {0}" -f [math]::Round($sw.Elapsed.TotalSeconds,1))
Write-Host ("blender_exit     : {0}" -f ($(if($timedout){"TIMED_OUT/KILLED"}else{$proc.ExitCode})))
if (Test-Path $metrics) {
    $rows = Import-Csv $metrics
    if ($rows) {
        $peakRam  = ($rows | Measure-Object blender_ram_mb -Maximum).Maximum
        $peakVram = ($rows | Measure-Object vram_used_mb  -Maximum).Maximum
        Write-Host ("peak_blender_RAM : {0} MB ({1} GB)" -f $peakRam, [math]::Round($peakRam/1024,1))
        Write-Host ("peak_VRAM_used   : {0} MB ({1} GB)" -f $peakVram, [math]::Round($peakVram/1024,1))
    }
}
$rep = Join-Path $OutDir "canary_report.json"
if (Test-Path $rep) { Write-Host "---- canary_report.json ----"; Get-Content $rep }
Write-Host ("full blender log : " + $blog)
Write-Host ("metrics csv      : " + $metrics)
Write-Host "==============================================="
# GPU-gap guard released; nothing left resident.
