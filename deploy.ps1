# Turtle — 一键部署脚本
# 用法：右键 -> 使用 PowerShell 运行，或终端里 .\deploy.ps1
# 作用：资源同步 → 编译 → 打包 yak → 卸载旧版 → 安装新版
# 以后每次改了代码/资源，跑这一个脚本就够了

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$yakExe = "C:\Program Files\Rhino 8\System\Yak.exe"

Write-Host "==> [1/5] 资源同步 (assets -> Resources)..." -ForegroundColor Cyan
& (Join-Path $root "distribute.ps1")

Write-Host "==> [2/5] 编译 Release..." -ForegroundColor Cyan
Set-Location $root
& dotnet build -c Release --nologo 2>&1 | Select-Object -Last 3
if ($LASTEXITCODE -ne 0) { Write-Host "编译失败！" -ForegroundColor Red; exit 1 }

Write-Host "==> [3/5] 打包 yak..." -ForegroundColor Cyan
$buildDir = Join-Path $root "yak_build"
New-Item -ItemType Directory -Path $buildDir -Force | Out-Null
Remove-Item (Join-Path $buildDir "*") -Force -ErrorAction SilentlyContinue
Copy-Item (Join-Path $root "bin\Release\net7.0\Turtle.rhp") $buildDir
Copy-Item (Join-Path $root "bin\Release\net7.0\Turtle.rui") $buildDir
Copy-Item (Join-Path $root "bin\Release\net7.0\manifest.yml") $buildDir
Set-Location $buildDir
& $yakExe build 2>&1 | Out-Null
$yakFile = Get-ChildItem (Join-Path $buildDir "*.yak") | Select-Object -First 1
if (-not $yakFile) { Write-Host "yak 打包失败！" -ForegroundColor Red; exit 1 }
Write-Host "  包: $($yakFile.Name)" -ForegroundColor Green

Write-Host "==> [4/5] 卸载旧版..." -ForegroundColor Cyan
& $yakExe uninstall Turtle 2>&1 | Out-Null

Write-Host "==> [5/5] 安装新版..." -ForegroundColor Cyan
& $yakExe install $yakFile.FullName 2>&1 | Out-Null

Write-Host ""
Write-Host "==> 部署完成！请重启 Rhino 使插件更新生效。" -ForegroundColor Green
Write-Host "    安装位置: %APPDATA%\McNeel\Rhinoceros\packages\8.0\Turtle\1.0.0\" -ForegroundColor Gray
