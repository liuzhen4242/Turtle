# Turtle — Windows 一键编译
# 用法：右键 -> 使用 PowerShell 运行，或终端里 .\build.ps1

$ErrorActionPreference = "Stop"

Write-Host "==> 检查 .NET SDK..." -ForegroundColor Cyan
$dotnet = Get-Command dotnet -ErrorAction SilentlyContinue
if (-not $dotnet) {
    Write-Host "未找到 dotnet，请先安装 .NET 7 SDK: https://dotnet.microsoft.com/download" -ForegroundColor Red
    exit 1
}

Write-Host "==> 还原依赖并编译 Release..." -ForegroundColor Cyan
dotnet build -c Release

if ($LASTEXITCODE -ne 0) {
    Write-Host "编译失败！请检查上方错误信息。" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "编译成功：" -ForegroundColor Green
$rhp = Join-Path $PSScriptRoot "bin\Release\net7.0\Turtle.rhp"
Write-Host "  RHP: $rhp"
Write-Host "把 Turtle.rhp 和 Turtle.rui 放在同一文件夹，拖进 Rhino 窗口即可加载。" -ForegroundColor Yellow
