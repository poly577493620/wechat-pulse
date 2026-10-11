param(
    [switch]$NoBrowser,
    [switch]$NoPrompt,
    [switch]$NoClipboard,
    [switch]$SetupOnly
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
$env:UV_CACHE_DIR = Join-Path $PSScriptRoot ".uv-cache"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $PSScriptRoot ".python"

function Assert-ProjectWritable {
    $probe = Join-Path $PSScriptRoot (".wepulse-write-test-" + [guid]::NewGuid().ToString("N") + ".tmp")
    try {
        [IO.File]::WriteAllText($probe, "write-test", [Text.UTF8Encoding]::new($false))
        Remove-Item -LiteralPath $probe -Force
    } catch {
        throw "当前账户没有项目目录的写入权限：$PSScriptRoot`n请右键该文件夹，选择 属性 → 安全 → 编辑，为当前账户勾选 修改；或者把项目解压到当前账户拥有写入权限的目录。不要长期以管理员身份运行 WePulse。"
    }
}

function Find-Uv {
    $command = Get-Command uv -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $links = @(
        (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\uv.exe"),
        (Join-Path $env:USERPROFILE ".local\bin\uv.exe")
    )
    foreach ($candidate in $links) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    $packageRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if (Test-Path -LiteralPath $packageRoot) {
        $packageUv = Get-ChildItem -LiteralPath $packageRoot -Directory -Filter "astral-sh.uv_*" -ErrorAction SilentlyContinue |
            ForEach-Object { Get-ChildItem -LiteralPath $_.FullName -Filter "uv.exe" -Recurse -File -ErrorAction SilentlyContinue } |
            Select-Object -First 1
        if ($packageUv) { return $packageUv.FullName }
    }
    return $null
}

function Ensure-Uv {
    $uv = Find-Uv
    if ($uv) { return $uv }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "未找到 uv 或 winget。请从 https://docs.astral.sh/uv/ 安装 uv 后重试。"
    }
    Write-Host "首次运行：正在通过 WinGet 安装 uv（用于自动管理 Python）……" -ForegroundColor Cyan
    & winget install --id=astral-sh.uv -e --accept-source-agreements --accept-package-agreements | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "uv 安装失败，WinGet 退出代码：$LASTEXITCODE" }
    $uv = Find-Uv
    if (-not $uv) { throw "uv 已安装但当前进程未找到它。请关闭窗口后重新双击 start-wepulse.cmd。" }
    return $uv
}

function Ensure-EnvironmentFile {
    $envPath = Join-Path $PSScriptRoot ".env"
    if (-not (Test-Path -LiteralPath $envPath)) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot ".env.example") -Destination $envPath
        $token = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
        $content = [IO.File]::ReadAllText($envPath)
        $content = $content.Replace("ADMIN_TOKEN=change-me", "ADMIN_TOKEN=$token")
        [IO.File]::WriteAllText($envPath, $content, [Text.UTF8Encoding]::new($false))
        Write-Host "已创建 .env 并生成随机管理令牌。" -ForegroundColor Green
        Write-Host "请在管理中心的“录入或更新微信读书 Cookie”区域安全保存 Cookie。" -ForegroundColor Yellow
    }
    return $envPath
}

function Test-WePulseHealth {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8765/health" -TimeoutSec 2
        return $response.status -eq "ok"
    } catch {
        return $false
    }
}

Assert-ProjectWritable
$uv = Ensure-Uv
$envPath = Ensure-EnvironmentFile
Write-Host "正在准备 WePulse 本地运行环境……" -ForegroundColor Cyan
& $uv sync --locked
if ($LASTEXITCODE -ne 0) { throw "依赖安装失败，uv 退出代码：$LASTEXITCODE" }

if ($SetupOnly) {
    Write-Host "本地运行环境准备完成。" -ForegroundColor Green
    exit 0
}

if (-not (Test-WePulseHealth)) {
    $pythonw = Join-Path $PSScriptRoot ".venv\Scripts\pythonw.exe"
    if (-not (Test-Path -LiteralPath $pythonw)) { throw "未找到本地 Python：$pythonw" }
    $dataDir = Join-Path $PSScriptRoot "data"
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    $process = Start-Process -FilePath $pythonw -ArgumentList "-m", "wepulse" -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $dataDir "service.out.log") -RedirectStandardError (Join-Path $dataDir "service.err.log")
    [IO.File]::WriteAllText((Join-Path $dataDir "wepulse.pid"), [string]$process.Id)
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Seconds 1
        if (Test-WePulseHealth) { $ready = $true; break }
        if ($process.HasExited) { break }
    }
    if (-not $ready) {
        $log = Join-Path $dataDir "service.err.log"
        throw "WePulse 未能启动。请查看日志：$log"
    }
}

$tokenLine = Get-Content -LiteralPath $envPath | Where-Object { $_ -like "ADMIN_TOKEN=*" } | Select-Object -First 1
if ($tokenLine) {
    $token = $tokenLine.Substring("ADMIN_TOKEN=".Length)
    if (-not $NoClipboard -and (Get-Command Set-Clipboard -ErrorAction SilentlyContinue)) {
        Set-Clipboard -Value $token
        Write-Host "管理令牌已复制到剪贴板，请在管理中心登录框粘贴；使用后可复制其他内容覆盖剪贴板。" -ForegroundColor Yellow
    } elseif (-not $NoClipboard) {
        Write-Host "管理令牌保存在 .env 的 ADMIN_TOKEN 中。" -ForegroundColor Yellow
    }
}
Write-Host "WePulse 已在后台运行：http://localhost:8765/admin" -ForegroundColor Green
if (-not $NoBrowser) { Start-Process "http://localhost:8765/admin" }
