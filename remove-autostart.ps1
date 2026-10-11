$ErrorActionPreference = "Stop"
$task = Get-ScheduledTask -TaskName "WePulse" -ErrorAction SilentlyContinue
if ($task) {
    Unregister-ScheduledTask -TaskName "WePulse" -Confirm:$false
    Write-Host "已移除 WePulse 开机自启动任务。" -ForegroundColor Green
} else {
    Write-Host "没有找到 WePulse 开机自启动任务。" -ForegroundColor Yellow
}
