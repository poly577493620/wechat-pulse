$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
$pidPath = Join-Path $PSScriptRoot "data\wepulse.pid"
if (-not (Test-Path -LiteralPath $pidPath)) {
    Write-Host "未找到运行记录；WePulse 可能已经停止。" -ForegroundColor Yellow
    exit 0
}
$servicePid = [int]([IO.File]::ReadAllText($pidPath).Trim())
$process = Get-Process -Id $servicePid -ErrorAction SilentlyContinue
if (-not $process) {
    Remove-Item -LiteralPath $pidPath -Force
    Write-Host "WePulse 已经停止。" -ForegroundColor Yellow
    exit 0
}
$expected = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".venv\Scripts\pythonw.exe"))
try { $actual = [IO.Path]::GetFullPath($process.Path) } catch { $actual = "" }
if ($actual -ne $expected) {
    throw "PID $servicePid 不属于当前项目，为安全起见未终止该进程。"
}
Stop-Process -Id $servicePid
Remove-Item -LiteralPath $pidPath -Force
Write-Host "WePulse 已停止。" -ForegroundColor Green
