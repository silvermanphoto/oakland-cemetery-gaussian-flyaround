# Stage the free KIRI 3DGS Render addon into C:\blender_lane (network only, no GPU touched).
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$base = "https://github.com/Kiri-Innovation/3dgs-render-blender-addon/releases/download/v5.0.0"
$dest = "C:\blender_lane"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$files = @(
  "3dgs_render_by_kiri_engine_5.0.0.zip",
  "3dgs_render_by_kiri_engine_5.0.0_blender5.2_patch.zip",
  "Blender_version_notes.txt",
  "3DGS.render.5.0.Update.log.txt"
)
foreach ($f in $files) {
  $out = Join-Path $dest $f
  if (Test-Path $out) { Write-Output ("SKIP (exists): " + $f); continue }
  Write-Output ("Downloading: " + $f)
  Invoke-WebRequest -Uri ($base + "/" + $f) -OutFile $out
}
Write-Output "---STAGED---"
Get-ChildItem $dest | Select-Object Name,Length | ForEach-Object { Write-Output ($_.Name + "  " + [math]::Round($_.Length/1MB,2) + " MB") }
