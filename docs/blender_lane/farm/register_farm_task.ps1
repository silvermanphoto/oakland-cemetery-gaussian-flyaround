# register_farm_task.ps1 -- OPTIONAL. Registers an INTERACTIVE, on-demand scheduled task
# that runs the shot queue inside the logged-in console session, so you can kick the farm
# off remotely (schtasks /Run) without a physical double-click.
#
# RUN THIS ONCE, FROM the logged-in console session (it registers for the current user).
# It is INTERACTIVE + "run only when user is logged on" -- the opposite of the S4U tasks
# used for headless training. GUI Blender needs the interactive console session; an S4U
# "run whether or not logged on" task has NO desktop and its GL would be software/blank.
#
# After registering, start the farm from the Mac with:
#   ssh skychief "schtasks /Run /TN OaklandBlenderFarm"
# (this only surfaces GUI Blender if a console session is currently logged in.)
$TN = "OaklandBlenderFarm"
$user = "$env:USERDOMAIN\$env:USERNAME"
Write-Output "Registering interactive task '$TN' for $user (must be the logged-in console user)."

$action    = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\blender_lane\farm\run_queue.ps1"
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Highest
$settings  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 12) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $TN -Action $action -Principal $principal -Settings $settings -Force

Write-Output "Registered. Run on demand:  schtasks /Run /TN $TN"
Write-Output "Remove later:               schtasks /Delete /TN $TN /F"
