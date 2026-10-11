$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
$pythonw = Join-Path $PSScriptRoot ".venv\Scripts\pythonw.exe"
if (-not (Test-Path -LiteralPath $pythonw)) {
    throw "请先双击 start-wepulse.cmd 完成首次安装和启动。"
}

$powershell = (Get-Command powershell.exe -ErrorAction Stop).Source
$arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$(Join-Path $PSScriptRoot 'start-local.ps1')`" -NoBrowser -NoPrompt -NoClipboard"
$action = New-ScheduledTaskAction -Execute $powershell -Argument $arguments -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName "WePulse" -Description "登录 Windows 后在后台启动 WePulse" -Action $action -Trigger $trigger -Settings $settings -RunLevel Limited -Force | Out-Null
Write-Host "已安装开机登录自启动任务：WePulse" -ForegroundColor Green
Write-Host "服务会在当前用户登录 Windows 后自动在后台运行。"
