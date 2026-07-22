# probe_session.ps1 -- READ ONLY. Gathers everything needed to decide the minimal
# path to a persistent console GUI session with real RTX 3090 OpenGL on Skychief.
# Changes NOTHING. Prints delimited, ASCII-only blocks.
$ErrorActionPreference = "Continue"

Write-Output "===== SESSIONS (qwinsta) ====="
qwinsta 2>&1 | Out-String

Write-Output "===== quser ====="
quser 2>&1 | Out-String

Write-Output "===== AUTOLOGON (Winlogon, read only) ====="
$wl = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
$w = Get-ItemProperty -Path $wl -ErrorAction SilentlyContinue
Write-Output ("AutoAdminLogon = " + $w.AutoAdminLogon)
Write-Output ("DefaultUserName = " + $w.DefaultUserName)
Write-Output ("DefaultDomainName = " + $w.DefaultDomainName)
Write-Output ("DefaultPassword set? = " + [bool]($w.PSObject.Properties.Name -contains 'DefaultPassword'))
Write-Output ("AutoLogonCount = " + $w.AutoLogonCount)

Write-Output "===== RDP / TERMINAL SERVICES (read only) ====="
$ts = Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" -ErrorAction SilentlyContinue
Write-Output ("fDenyTSConnections = " + $ts.fDenyTSConnections + "  (0 = RDP enabled)")
$gp = Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" -ErrorAction SilentlyContinue
Write-Output ("Policy bUseHWGraphicsAdaptersForRDS = " + $gp.bEnumerateHWBeforeSW + " / hwGPU policy present? " + [bool]$gp)

Write-Output "===== LOCAL USERS ====="
Get-LocalUser | Select-Object Name,Enabled,@{n='LastLogon';e={$_.LastLogon}} | Format-Table -AutoSize | Out-String
Write-Output "-- Administrators group members --"
Get-LocalGroupMember -Group "Administrators" -ErrorAction SilentlyContinue | Select-Object Name,ObjectClass | Format-Table -AutoSize | Out-String
Write-Output "-- Remote Desktop Users group members --"
Get-LocalGroupMember -Group "Remote Desktop Users" -ErrorAction SilentlyContinue | Select-Object Name,ObjectClass | Format-Table -AutoSize | Out-String

Write-Output "===== GPU: nvidia-smi display + driver ====="
$smi = "C:\Windows\System32\nvidia-smi.exe"
if (Test-Path $smi) {
  & $smi --query-gpu=name,driver_version,display_mode,display_active,utilization.gpu,memory.used,memory.free --format=csv 2>&1 | Out-String
} else {
  Write-Output "nvidia-smi not at System32; trying PATH"
  nvidia-smi --query-gpu=name,driver_version,display_mode,display_active,memory.free --format=csv 2>&1 | Out-String
}

Write-Output "===== VIDEO CONTROLLERS (all adapters, incl RDP virtual) ====="
Get-CimInstance Win32_VideoController | Select-Object Name,@{n='DriverVer';e={$_.DriverVersion}},CurrentHorizontalResolution,CurrentVerticalResolution,VideoModeDescription | Format-Table -AutoSize | Out-String

Write-Output "===== MONITORS ATTACHED (hardware GL needs a display or dummy plug) ====="
$mon = Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorBasicDisplayParams -ErrorAction SilentlyContinue
if ($mon) { Write-Output ("Physical monitor(s) reporting EDID: " + ($mon | Measure-Object).Count) }
else { Write-Output "No WmiMonitorBasicDisplayParams -> likely NO physical monitor / EDID (headless)." }
Get-CimInstance Win32_DesktopMonitor -ErrorAction SilentlyContinue | Select-Object Name,MonitorType,ScreenWidth,ScreenHeight | Format-Table -AutoSize | Out-String

Write-Output "===== BLENDER 5.1.2 ====="
$bl = "C:\blender_lane\blender-5.1.2-windows-x64\blender.exe"
Write-Output ("blender.exe exists? " + (Test-Path $bl) + "  -> " + $bl)
if (Test-Path $bl) { & $bl --version 2>&1 | Select-Object -First 3 | Out-String }

Write-Output "===== KIRI EXTENSION FOLDER ====="
$ext = "$env:APPDATA\Blender Foundation\Blender\5.1\extensions\user_default"
Write-Output ("extensions/user_default exists? " + (Test-Path $ext) + " -> " + $ext)
if (Test-Path $ext) { Get-ChildItem $ext -ErrorAction SilentlyContinue | Select-Object Name | Format-Table -AutoSize | Out-String }

Write-Output "===== TILES (source PLYs) ====="
$td = "H:\2026 Files\26-002 Oakland Cemetery Splat\deliver\ue_tiles"
Write-Output ("tile dir exists? " + (Test-Path $td) + " -> " + $td)
if (Test-Path $td) {
  $plys = Get-ChildItem $td -Filter *.ply -ErrorAction SilentlyContinue
  Write-Output ("PLY count = " + ($plys | Measure-Object).Count)
  $t32 = Join-Path $td "tile_3_2.ply"
  Write-Output ("tile_3_2.ply exists? " + (Test-Path $t32) + "  size_GB=" + [math]::Round(((Get-Item $t32 -ErrorAction SilentlyContinue).Length/1GB),2))
}

Write-Output "===== FREE RAM NOW ====="
$os = Get-CimInstance Win32_OperatingSystem
Write-Output ("Free RAM GB = " + [math]::Round($os.FreePhysicalMemory/1MB,1) + " / total GB = " + [math]::Round($os.TotalVisibleMemorySize/1MB,1))

Write-Output "===== PROBE DONE ====="
