$ErrorActionPreference = "Stop"
$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
Set-Location -LiteralPath $ProjectRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "未找到 Docker。请先安装并启动 Docker Desktop：https://www.docker.com/products/docker-desktop/" -ForegroundColor Red
    exit 1
}

docker compose version | Out-Null

if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
    $token = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
    $content = [IO.File]::ReadAllText((Join-Path $ProjectRoot ".env"))
    $content = $content.Replace("ADMIN_TOKEN=change-me", "ADMIN_TOKEN=$token")
    [IO.File]::WriteAllText((Join-Path $ProjectRoot ".env"), $content, [Text.UTF8Encoding]::new($false))
    Write-Host "已创建 .env 并生成随机管理令牌。" -ForegroundColor Green
    $cookie = Read-Host "可选：现在粘贴微信读书 Cookie，或直接回车稍后填写"
    if ($cookie) {
        $content = [IO.File]::ReadAllText((Join-Path $ProjectRoot ".env"))
        $content = $content.Replace("WEREAD_COOKIE=", "WEREAD_COOKIE=$cookie")
        [IO.File]::WriteAllText((Join-Path $ProjectRoot ".env"), $content, [Text.UTF8Encoding]::new($false))
    }
} else {
    Write-Host "检测到现有 .env，将保留已有配置。" -ForegroundColor Yellow
}

docker compose up -d --build
Write-Host ""
Write-Host "WePulse 已启动：" -ForegroundColor Green
Write-Host "  管理中心  http://localhost:8765/admin"
Write-Host "  使用说明  README.md"
Write-Host "  管理令牌  保存在 .env 的 ADMIN_TOKEN 中"
