<#
================================================================================
 export_ue_tiles.ps1  --  v2.0   (26-029 Oakland Cemetery Gaussian Flyaround)
 Runs on Skychief (Windows, PowerShell 5.1). CPU-ONLY. Read-only on the source.
================================================================================

 WHAT THIS DOES
   CROPS each finished native-8192 dense per-tile gaussian PLY down to its exact,
   non-overlapping grid cell, and writes one clean UE-ready PLY per tile:
       H:\...\deliver\ue_tiles\<tile>.ply
   The raw trained tiles were trained with a ~20% apron, so ADJACENT TILES
   OVERLAP (a tile spans ~326 m where a cell is ~143 m). Imported raw they would
   double-cover every seam. This crop removes each tile's apron so the 36 tiles
   tessellate with zero double-coverage -- exactly what the web pipeline did for
   the 3x3 set. There is NO LOD ladder here (see COORDINATE OWNERSHIP); NanoGS
   builds its level-of-detail INTERNALLY from the one source PLY.

 -----------------------------------------------------------------------------
 COORDINATE / SCALE OWNERSHIP  --  READ THIS BEFORE CHANGING ANYTHING
 (source-verified 2026-07-17; this block is IDENTICAL in ue_import_tiles.py)
 -----------------------------------------------------------------------------
   NanoGS's PLY importer BAKES BOTH conversions AT IMPORT TIME, once per splat
   (PLYFileReader.cpp:341-373, 431-434):
       * axis flip COLMAP y-down -> UE z-up:  UE.X = PLY.Z,  UE.Y = PLY.X,
                                              UE.Z = -PLY.Y
       * a fixed metres -> centimetres x100 on positions AND scales.
   The importer does NO recentering, so every splat keeps its true world position.

   Our global solve frame is exactly COLMAP up = -Y at ~1 unit = 1 metre, which
   MATCHES NanoGS's hardcoded assumption. So tiles import upright and metric-
   correct with ZERO pre-processing transform, and each tile's UE actor Transform
   stays IDENTITY precisely because the axis flip and the x100 scale are ALREADY
   baked at import (applying either here would double-apply and corrupt the scene).

   Therefore this PC-side export does ONLY a metric-frame CROP: each tile is
   box-filtered to its non-overlapping grid cell. It performs:
       * NO axis conversion, NO metre->cm scale,
       * NO rotation, NO scale (never -s), NO translation, NO pivot-to-origin,
       * and NONE of the superspl.at web-viewer hacks (no -s 0.05, no pivot).
   A crop is a pure box filter in the true metric frame -- it deletes the apron
   gaussians but MOVES nothing, so every kept gaussian keeps its true position and
   all tiles keep ONE shared origin. That shared origin is exactly why identity
   placement in UE reassembles them seamlessly. The old "UE converts at render
   time / the scale comes from the actor Transform" story was WRONG -- the convert
   and the x100 scale are import-time bakes, and the actor Transform is identity
   BECAUSE of that.
 -----------------------------------------------------------------------------

 HOW A TILE'S CELL IS DERIVED (the tile NAME is NOT trustworthy)
   The out8k tile name does not map cleanly to grid position (e.g. out8k
   tile_0_0 content sits in the HIGH-X column, not where "0_0" implies). So we
   NEVER crop by parsing the name. Instead, for each tile we:
     1. compute its gaussian CENTROID (splat-transform --stats -> data.mean x/z),
     2. find which of the 36 half-open cells the centroid falls in,
     3. crop that tile to that cell's bounds.
   The 6x6 grid edges below are in the solve's metric frame. They were verified
   2026-07-17 two independent ways, both matching to 0.1 m: (a) recomputing them
   from global\sparse\0\points3D.txt with partition6.py's exact percentile math
   (P1/P99 core, then percentile(core,100*i/6) for i=1..5, outer edges = min/max),
   and (b) reading tiles6\<tile>\crop_aabb.json (the boxes the tiles were actually
   trained against). If a tile's centroid maps OUTSIDE the extent, or two tiles
   map to the SAME cell, the script STOPS without cropping -- a collision means
   the partition assumption is broken and cropping would land tiles in wrong cells.

   Cell (i = x-index, j = z-index), half-open [xe[i],xe[i+1]) x [ze[j],ze[j+1]):
   interior boundaries use the exact edge so adjacent tiles meet with no overlap
   and no gap; the OUTER side of a rim cell extends to +/-100000 (mirrors
   partition6.py's crop_aabb rim = +/-1e6) so densified rim content is not clipped.
   Y (up) is always unbounded (+/-100000).

 splat-transform -B QUIRK: IT NEGATES X (verified empirically 2026-07-17)
   splat-transform v3.0.0 (daf6338) interprets the X corners of --filter-box in a
   NEGATED-X frame relative to the file (the frame --stats reports and the frame of
   the edges above). It reads X negated into its internal frame and writes it back
   negated, so the OUTPUT FILE geometry is CLEAN (kept gaussians keep their true
   stored X) -- but the -B ARGUMENT's X-min/X-max must be given as (-x1_cell,
   -x0_cell). Z and Y pass through unchanged. Proven by three controlled crops:
   passing the raw cell box mirrored the output to the wrong (negative) X cell;
   passing (-x1,-x0) landed tile_2_0 exactly in cell x=3 (x[-11.6..81.2]) and
   tile_3_0 exactly in cell x=2 (x[-95.7..-11.6]), the two meeting at the shared
   edge -11.6 with no overlap. (Sibling finding: 26-002 lesson notes -t flips Z;
   -B flips X. If splat-transform is ever upgraded, RE-VERIFY this sign.) Because
   the written file is clean, the UE identity-placement story is unaffected.

 TRAINING SAFETY (a live GPU trainer may be on this box)
   * Every splat-transform call is forced onto the CPU (-g cpu): this export never
     contends for the training GPU. (The crop is CPU-only; it does NOT need the
     GPU window -- that window is for the UE import step.)
   * Read-only on out8k. Writes ONLY under deliver\ue_tiles.
   * A source tile is processed ONLY once fully written and settled: accepted only
     when file length == header + VertexCount*VertexStride AND it last changed at
     least QuiescenceSeconds ago. A tile still being trained fails that and is
     skipped this pass; re-running picks up newly-finished tiles (idempotent /
     restartable).
   * Never launches the editor, trains, or touches the GPU / gpu_state.txt.

 USAGE
   powershell -File export_ue_tiles.ps1                 # crop all settled tiles
   powershell -File export_ue_tiles.ps1 -DryRun         # show the plan only
   powershell -File export_ue_tiles.ps1 -Force          # re-crop everything
   powershell -File export_ue_tiles.ps1 -Tiles tile_3_2 # one/some tiles

 LIVE VERIFICATION: the centroid->cell mapping, the edge cross-check, and the
 crop itself were proven on real finished tiles 2026-07-17 (2 tiles cropped, their
 written bounds confirmed inside distinct non-overlapping cells with reduced
 gaussian counts). The full 36-tile pass runs after training frees the box.
================================================================================
#>

[CmdletBinding()]
param(
    [string]   $SrcRoot        = "H:\2026 Files\26-002 Oakland Cemetery Splat\out8k",
    [string]   $OutRoot        = "H:\2026 Files\26-002 Oakland Cemetery Splat\deliver\ue_tiles",
    [string]   $SplatTransform = "C:\Users\JLS_Macintosh\AppData\Roaming\npm\splat-transform.cmd",
    # 6x6 grid edges (solve metric frame). VERIFIED 2026-07-17 against partition6.py
    # (points3D.txt recompute) AND tiles6\*\crop_aabb.json -- do not edit casually.
    [double[]] $XEdges = @(-388.99149233321907, -181.8077576667134, -95.67941263786484, -11.58917699595743, 81.2319898457765, 198.8322994374814, 466.81791208465825),
    [double[]] $ZEdges = @(-337.8148049530573, -127.13953752396628, -69.81079313857475, -8.166835977695882, 61.06325816595935, 137.98436851869337, 362.8916582525708),
    [double]   $Rim               = 100000.0,  # rim-cell outer bound + y half-extent (m)
    [int]      $QuiescenceSeconds = 30,        # min seconds since last write before a source tile is trusted
    [string[]] $Tiles          = @(),          # empty = all tiles under SrcRoot; else a subset of tile names
    [switch]   $Force,                         # re-crop even if outputs already exist and match
    [switch]   $DryRun                         # print the plan; write nothing, run no splat-transform
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

# ------------------------------------------------------------------ logging ----
$script:LogFile = $null
function Log {
    param([string]$Message, [string]$Level = "INFO")
    $line = "{0}  [{1}]  {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level, $Message
    switch ($Level) {
        "WARN"  { Write-Host $line -ForegroundColor Yellow }
        "ERROR" { Write-Host $line -ForegroundColor Red }
        "OK"    { Write-Host $line -ForegroundColor Green }
        default { Write-Host $line }
    }
    if ($script:LogFile) { Add-Content -LiteralPath $script:LogFile -Value $line }
}

# ------------------------------------------------ PLY header / completeness ----
# Reads the first <=64 KB of a PLY, parses vertex count, byte stride, and the
# byte offset where binary data begins. Header is pure ASCII, so a character
# index into the decoded header equals its byte offset.
function Get-PlyHeaderInfo {
    param([string]$Path)
    $result = [ordered]@{ Ok = $false; VertexCount = 0; Stride = 0; DataOffset = 0; PropCount = 0; Error = "" }
    $fs = [System.IO.File]::OpenRead($Path)
    try {
        # $fs.Length is Int64; these tiles are ~3 GB, so never cast it to Int32.
        $max = [int][Math]::Min([int64]65536, $fs.Length)
        $buf = New-Object byte[] $max
        $read = $fs.Read($buf, 0, $max)
    } finally { $fs.Close() }

    $text = [System.Text.Encoding]::ASCII.GetString($buf, 0, $read)
    $ehIdx = $text.IndexOf("end_header")
    if ($ehIdx -lt 0) { $result.Error = "no end_header in first 64 KB (header incomplete or not a PLY)"; return $result }

    # Data begins right after 'end_header' + its end-of-line bytes.
    $afterEh = $ehIdx + 10   # length of "end_header"
    $eolLen = 0
    if ($afterEh -lt $read -and $buf[$afterEh] -eq 0x0D -and ($afterEh + 1) -lt $read -and $buf[$afterEh + 1] -eq 0x0A) { $eolLen = 2 }
    elseif ($afterEh -lt $read -and $buf[$afterEh] -eq 0x0A) { $eolLen = 1 }
    $result.DataOffset = $afterEh + $eolLen

    # Byte size per PLY scalar type.
    $sizeOf = @{
        char = 1; uchar = 1; int8 = 1; uint8 = 1;
        short = 2; ushort = 2; int16 = 2; uint16 = 2;
        int = 4; uint = 4; int32 = 4; uint32 = 4; float = 4; float32 = 4;
        double = 8; float64 = 8
    }

    $headerText = $text.Substring(0, $ehIdx)
    $stride = 0; $props = 0
    foreach ($raw in ($headerText -split "`n")) {
        $ln = $raw.Trim()
        if ($ln -match '^element\s+vertex\s+(\d+)') { $result.VertexCount = [int64]$Matches[1]; continue }
        if ($ln -match '^property\s+(\S+)\s+(\S+)$') {
            $t = $Matches[1].ToLower()
            if ($sizeOf.ContainsKey($t)) { $stride += $sizeOf[$t] } else { $stride += 4; $result.Error = "unknown property type '$t' assumed 4 bytes" }
            $props++
        }
    }
    $result.Stride = $stride
    $result.PropCount = $props
    if ($result.VertexCount -le 0 -or $result.Stride -le 0) { $result.Error = "could not parse vertex count / stride"; return $result }
    $result.Ok = $true
    return $result
}

# A PLY is "complete" when its length is exactly header + count*stride. A file
# mid-write (or truncated) is strictly smaller and fails this. This is the
# training-safe gate AND the per-output integrity check in one.
function Test-PlyComplete {
    param([string]$Path)
    $out = [ordered]@{ Complete = $false; VertexCount = 0; Reason = "" }
    if (-not (Test-Path -LiteralPath $Path)) { $out.Reason = "missing"; return $out }
    $info = Get-PlyHeaderInfo -Path $Path
    if (-not $info.Ok) { $out.Reason = $info.Error; return $out }
    $expected = [int64]$info.DataOffset + ([int64]$info.VertexCount * [int64]$info.Stride)
    $actual = (Get-Item -LiteralPath $Path).Length
    $out.VertexCount = $info.VertexCount
    if ($actual -eq $expected) { $out.Complete = $true }
    else { $out.Reason = ("size {0} != expected {1} (still writing / truncated)" -f $actual, $expected) }
    return $out
}

# ----------------------------------------------------- splat-transform stats ----
# Runs `splat-transform -g cpu <file> --stats json null` (CPU-only, discards
# output) and parses gaussian count + x/y/z min/max/MEAN off the WRITTEN file.
# The MEAN of x and z is the tile centroid used to assign its grid cell.
function Get-SplatStats {
    param([string]$Path)
    $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try {
        $raw = & $SplatTransform -g cpu $Path --stats json null 2>$null
    } finally { $ErrorActionPreference = $prev }
    $joined = ($raw -join "`n")
    $a = $joined.IndexOf('{'); $b = $joined.LastIndexOf('}')
    if ($a -lt 0 -or $b -le $a) { throw "could not locate JSON in --stats output for $Path" }
    $json = $joined.Substring($a, $b - $a + 1) | ConvertFrom-Json

    $cols = $json.stats[0].columns
    $ix = [Array]::IndexOf($cols, 'x'); $iy = [Array]::IndexOf($cols, 'y'); $iz = [Array]::IndexOf($cols, 'z')
    if ($ix -lt 0 -or $iy -lt 0 -or $iz -lt 0) { throw "x/y/z columns not found in --stats output for $Path" }
    $mn = $json.stats[0].data.min; $mx = $json.stats[0].data.max; $me = $json.stats[0].data.mean
    return [ordered]@{
        Count = [int64]$json.numGaussians
        Xmin = [double]$mn[$ix]; Xmax = [double]$mx[$ix]; Xmean = [double]$me[$ix]
        Ymin = [double]$mn[$iy]; Ymax = [double]$mx[$iy]; Ymean = [double]$me[$iy]
        Zmin = [double]$mn[$iz]; Zmax = [double]$mx[$iz]; Zmean = [double]$me[$iz]
    }
}

function Format-Bounds {
    param($s)
    return ("x[{0:N3} .. {1:N3}]  y[{2:N3} .. {3:N3}]  z[{4:N3} .. {5:N3}]" -f $s.Xmin, $s.Xmax, $s.Ymin, $s.Ymax, $s.Zmin, $s.Zmax)
}

# ---------------------------------------------------------- cell derivation ----
# Half-open cell index: largest i with edges[i] <= c, clamped to 0..5.
# Returns @{ Index; Outside } (Outside = centroid falls beyond the extent).
function Get-CellIndex {
    param([double[]]$Edges, [double]$C)
    $i = 0
    for ($k = 0; $k -lt 6; $k++) { if ($C -ge $Edges[$k]) { $i = $k } }
    $outside = ($C -lt $Edges[0]) -or ($C -ge $Edges[6])
    return [ordered]@{ Index = $i; Outside = $outside }
}

# CLEAN cell box for cell (i = x-index, j = z-index) in the file/stats frame (the
# region we KEEP): interior edges exact, rim outer to +/-Rim, y unbounded. This is
# what the manifest records and what the output is verified against. The negated-X
# argument actually passed to -B is derived from this at the call site.
function Get-CellBox {
    param([int]$I, [int]$J)
    $x0 = if ($I -eq 0) { -$Rim } else { $XEdges[$I] }
    $x1 = if ($I -eq 5) {  $Rim } else { $XEdges[$I + 1] }
    $z0 = if ($J -eq 0) { -$Rim } else { $ZEdges[$J] }
    $z1 = if ($J -eq 5) {  $Rim } else { $ZEdges[$J + 1] }
    return [ordered]@{ X0 = $x0; Y0 = -$Rim; Z0 = $z0; X1 = $x1; Y1 = $Rim; Z1 = $z1 }
}

# =============================================================================
#  MAIN
# =============================================================================
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " Oakland UE tile export  --  CROP each tile to its grid cell" -ForegroundColor Cyan
Write-Host " Non-overlapping cells (no double-coverage). NO LOD ladder." -ForegroundColor Cyan
Write-Host " NO axis convert, NO scale, NO pivot -- import-time bake owns those." -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path -LiteralPath $SrcRoot)) { Write-Host "Source root not found: $SrcRoot" -ForegroundColor Red; exit 2 }
if (-not (Test-Path -LiteralPath $SplatTransform)) { Write-Host "splat-transform not found: $SplatTransform" -ForegroundColor Red; exit 2 }

if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path $OutRoot | Out-Null
    $script:LogFile = Join-Path $OutRoot "_export_log.txt"
}
Log ("Source : {0}" -f $SrcRoot)
Log ("Output : {0}" -f $OutRoot)
Log ("X edges: {0}" -f (($XEdges | ForEach-Object { "{0:N1}" -f $_ }) -join ", "))
Log ("Z edges: {0}" -f (($ZEdges | ForEach-Object { "{0:N1}" -f $_ }) -join ", "))
if ($DryRun) { Log "DRY RUN -- planning only, nothing is written and no crop is run." "WARN" }
if ($Force)  { Log "FORCE -- existing crops will be rebuilt." "WARN" }

# Discover candidate tiles (a dir under SrcRoot holding hyper8k_<name>.ply).
$tileDirs = Get-ChildItem -LiteralPath $SrcRoot -Directory | Sort-Object Name
if ($Tiles.Count -gt 0) { $tileDirs = $tileDirs | Where-Object { $Tiles -contains $_.Name } }

# --- settle gate: keep only fully-written, quiescent tiles -------------------
$settled = @()
foreach ($dir in $tileDirs) {
    $name = $dir.Name
    $srcPly = Join-Path $dir.FullName ("hyper8k_{0}.ply" -f $name)
    if (-not (Test-Path -LiteralPath $srcPly)) { continue }
    $chk = Test-PlyComplete -Path $srcPly
    if (-not $chk.Complete) {
        Log ("{0}: source still writing / incomplete ({1}) -- skipping this pass." -f $name, $chk.Reason) "WARN"; continue
    }
    $ageOk = ((Get-Date) - (Get-Item -LiteralPath $srcPly).LastWriteTime).TotalSeconds -ge $QuiescenceSeconds
    if (-not $ageOk) {
        Log ("{0}: source finished under {1}s ago; leaving it to settle -- pick up next run." -f $name, $QuiescenceSeconds) "WARN"; continue
    }
    $settled += [ordered]@{ Name = $name; Ply = $srcPly; Count = $chk.VertexCount }
}
Log ("Settled source tiles this pass: {0} ({1})" -f $settled.Count, (($settled | ForEach-Object { $_.Name }) -join ", "))
if ($settled.Count -eq 0) { Log "Nothing settled to crop this pass." "WARN"; exit 0 }

# --- PASS 1: centroid -> cell for every settled tile, then 1:1 collision gate -
# Centroids are cached in each tile's manifest, so already-exported tiles cost
# no re-scan. A collision (two tiles -> same cell) or an out-of-extent centroid
# means the partition assumption is broken: STOP, crop nothing.
Log "Pass 1: centroid -> cell mapping ..."
$map = @{}          # name -> @{ Cx; Cz; I; J; Stats(optional) }
$cellOwner = @{}    # "i_j" -> name (collision detection)
$fatal = $false
foreach ($t in $settled) {
    $name = $t.Name
    $manifest = Join-Path (Join-Path $OutRoot $name) ("{0}.ue_export.json" -f $name)
    $cx = $null; $cz = $null; $stats = $null
    if (-not $Force -and (Test-Path -LiteralPath $manifest)) {
        try {
            $m = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
            $srcItem = Get-Item -LiteralPath $t.Ply
            if (($m.source.length -eq $srcItem.Length) -and ($m.source.mtimeUtc -eq $srcItem.LastWriteTimeUtc.ToString("o"))) {
                $cx = [double]$m.centroid.x; $cz = [double]$m.centroid.z
            }
        } catch { }
    }
    if ($null -eq $cx) {
        $stats = Get-SplatStats -Path $t.Ply
        $cx = $stats.Xmean; $cz = $stats.Zmean
    }
    $ci = Get-CellIndex -Edges $XEdges -C $cx
    $cj = Get-CellIndex -Edges $ZEdges -C $cz
    if ($ci.Outside -or $cj.Outside) {
        Log ("{0}: centroid x={1:N3} z={2:N3} falls OUTSIDE the grid extent -- refusing to crop." -f $name, $cx, $cz) "ERROR"
        $fatal = $true; continue
    }
    $key = "{0}_{1}" -f $ci.Index, $cj.Index
    if ($cellOwner.ContainsKey($key)) {
        Log ("COLLISION: {0} and {1} both map to cell (x={2},z={3}) -- refusing to crop." -f $cellOwner[$key], $name, $ci.Index, $cj.Index) "ERROR"
        $fatal = $true
    } else {
        $cellOwner[$key] = $name
    }
    $map[$name] = [ordered]@{ Cx = $cx; Cz = $cz; I = $ci.Index; J = $cj.Index; Stats = $stats }
    Log ("  {0,-9} centroid x={1,9:N3} z={2,9:N3} -> cell(x={3},z={4})" -f $name, $cx, $cz, $ci.Index, $cj.Index)
}
if ($fatal) {
    Log "STOP: centroid->cell mapping is not 1:1 / in-extent. No tiles cropped this pass." "ERROR"
    exit 3
}
Log ("Pass 1 OK: {0} tiles -> {1} distinct cells (1:1)." -f $settled.Count, $cellOwner.Count) "OK"

# --- PASS 2: crop each tile to its cell, verify, write manifest --------------
$summary = [ordered]@{ exported = 0; skippedDone = 0; failed = 0 }
foreach ($t in $settled) {
    $name = $t.Name
    $srcPly = $t.Ply
    $srcCount = $t.Count
    $mm = $map[$name]
    $box = Get-CellBox -I $mm.I -J $mm.J

    $tileOut  = $OutRoot
    $outPly   = Join-Path $tileOut ("{0}.ply" -f $name)
    $manifest = Join-Path (Join-Path $OutRoot $name) ("{0}.ue_export.json" -f $name)

    # idempotency: skip if a matching, complete crop already exists.
    if (-not $Force -and (Test-Path -LiteralPath $manifest)) {
        try {
            $m = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
            $srcItem = Get-Item -LiteralPath $srcPly
            $srcMatch = ($m.source.length -eq $srcItem.Length) -and ($m.source.mtimeUtc -eq $srcItem.LastWriteTimeUtc.ToString("o"))
            $cellMatch = ([int]$m.cell.xIndex -eq $mm.I) -and ([int]$m.cell.zIndex -eq $mm.J)
            $outOk = (Test-PlyComplete -Path $outPly).Complete
            if ($srcMatch -and $cellMatch -and $outOk) {
                Log ("{0}: already cropped to cell(x={1},z={2}) and matches source -- skipping. (use -Force)" -f $name, $mm.I, $mm.J) "OK"
                $summary.skippedDone++; continue
            }
        } catch { }
    }

    # -B interprets X in a NEGATED-X frame (see header quirk note): to keep file-x
    # in [X0,X1], the box X-min/X-max must be (-X1,-X0). Z and Y pass through.
    # {0:R} = round-trip formatting so the edge values keep full double precision.
    $filterArg = "{0:R},{1:R},{2:R},{3:R},{4:R},{5:R}" -f (-$box.X1), $box.Y0, $box.Z0, (-$box.X0), $box.Y1, $box.Z1
    Log ("{0}: cropping {1:N0} gaussians ({2:N2} GB) -> cell(x={3},z={4}) keep file-x[{5:N3}..{6:N3}] z[{7:N3}..{8:N3}]" -f $name, $srcCount, ((Get-Item -LiteralPath $srcPly).Length/1GB), $mm.I, $mm.J, $box.X0, $box.X1, $box.Z0, $box.Z1)
    Log ("{0}:   CMD: splat-transform -g cpu -w <src> -B `"{1}`" {2}   (X negated per -B convention)" -f $name, $filterArg, $outPly)

    if ($DryRun) { $summary.exported++; continue }

    try {
        New-Item -ItemType Directory -Force -Path (Split-Path $manifest -Parent) | Out-Null
        Get-ChildItem -LiteralPath $tileOut -Filter ("{0}.tmp.ply" -f $name) -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
        $outTmp = Join-Path $tileOut ("{0}.tmp.ply" -f $name)

        # CROP: -B is a box filter (min corner, max corner) in the NEGATED-X frame;
        # -g cpu keeps it off the training GPU. No other action -- no scale, no
        # rotate, no translate. The written file's geometry is CLEAN (see header).
        & $SplatTransform -g cpu -w $srcPly -B $filterArg $outTmp
        if ($LASTEXITCODE -ne 0) { throw "splat-transform crop exit $LASTEXITCODE" }
        if (-not (Test-PlyComplete -Path $outTmp).Complete) { throw "crop output failed completeness check" }
        Move-Item -LiteralPath $outTmp -Destination $outPly -Force

        # verify the WRITTEN file: count reduced + bounds inside the assigned cell.
        $s = Get-SplatStats -Path $outPly
        Log ("{0}:   WRITTEN {1:N0} gaussians (kept {2:P1} of {3:N0})  {4}" -f $name, $s.Count, ($s.Count / [double]$srcCount), $srcCount, (Format-Bounds $s)) "OK"

        $eps = 0.5
        $okx = ($mm.I -eq 0 -or $s.Xmin -ge ($XEdges[$mm.I] - $eps)) -and ($mm.I -eq 5 -or $s.Xmax -le ($XEdges[$mm.I + 1] + $eps))
        $okz = ($mm.J -eq 0 -or $s.Zmin -ge ($ZEdges[$mm.J] - $eps)) -and ($mm.J -eq 5 -or $s.Zmax -le ($ZEdges[$mm.J + 1] + $eps))
        if (-not $okx) { Log ("{0}: WRITTEN x bounds [{1:N3}..{2:N3}] not inside cell x-edges -- check crop." -f $name, $s.Xmin, $s.Xmax) "WARN" }
        if (-not $okz) { Log ("{0}: WRITTEN z bounds [{1:N3}..{2:N3}] not inside cell z-edges -- check crop." -f $name, $s.Zmin, $s.Zmax) "WARN" }
        if ($s.Count -ge $srcCount) { Log ("{0}: WRITTEN count {1:N0} not less than source {2:N0} -- apron not removed?" -f $name, $s.Count, $srcCount) "WARN" }

        # per-tile manifest (human ledger + idempotency key + centroid cache).
        $srcItem = Get-Item -LiteralPath $srcPly
        $mObj = [ordered]@{
            tile = $name
            exportedUtc = (Get-Date).ToUniversalTime().ToString("o")
            coordinateFrame = "RAW trained metric solve frame (COLMAP up=-Y, ~1 unit=1 m, one shared origin), CROPPED to this tile's non-overlapping grid cell. NO axis convert, NO scale, NO rotate, NO translate, NO pivot -- a crop moves nothing. NanoGS bakes the COLMAP->UE axis flip AND the x100 m->cm scale AT IMPORT; the UE actor Transform is IDENTITY because of that."
            source = [ordered]@{ path = $srcPly; length = $srcItem.Length; mtimeUtc = $srcItem.LastWriteTimeUtc.ToString("o"); gaussians = $srcCount }
            centroid = [ordered]@{ x = $mm.Cx; z = $mm.Cz }
            cell = [ordered]@{ xIndex = $mm.I; zIndex = $mm.J }
            cropBox = [ordered]@{ x0 = $box.X0; y0 = $box.Y0; z0 = $box.Z0; x1 = $box.X1; y1 = $box.Y1; z1 = $box.Z1 }
            filterBoxArg = $filterArg   # the exact -B string (X negated per splat-transform convention)
            output = [ordered]@{ file = "$name.ply"; gaussians = $s.Count; keptFraction = ($s.Count / [double]$srcCount)
                                 bounds = [ordered]@{ xmin=$s.Xmin; xmax=$s.Xmax; ymin=$s.Ymin; ymax=$s.Ymax; zmin=$s.Zmin; zmax=$s.Zmax } }
        }
        $mObj | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifest -Encoding UTF8
        Log ("{0}: done -> {1}" -f $name, $outPly) "OK"
        $summary.exported++
    }
    catch {
        Log ("{0}: FAILED -- {1}" -f $name, $_.Exception.Message) "ERROR"
        $summary.failed++
    }
}

Write-Host ""
Log ("Summary: {0} cropped, {1} already-done skipped, {2} failed." -f `
     $summary.exported, $summary.skippedDone, $summary.failed) $(if ($summary.failed -gt 0) { "ERROR" } else { "OK" })

if ($summary.failed -gt 0) { exit 1 } else { exit 0 }
