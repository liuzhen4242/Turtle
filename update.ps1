# Turtle 一键更新脚本
# 用法: 在项目根目录跑 .\update.ps1
# 流程: 关闭 Rhino -> 递增版本号 -> 编译 -> 打包 yak -> 卸载旧版 -> 安装新版 -> 启动 Rhino

$ErrorActionPreference = "Continue"
$projRoot = $PSScriptRoot
Set-Location $projRoot

Write-Host "=== [0/6] 关闭 Rhino ===" -ForegroundColor Cyan
Get-Process Rhino* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "`n=== [1/6] 递增版本号 ===" -ForegroundColor Cyan
$manifestPath = "bin\Release\net7.0\manifest.yml"
# 读取当前版本号
$manifest = Get-Content $manifestPath -Encoding UTF8
$versionLine = $manifest | Where-Object { $_ -match "^version:" } | Select-Object -First 1
$currentVersion = $versionLine -replace "version:\s*", ""
$parts = $currentVersion.Split(".")
$build = [int]$parts[2] + 1
$newVersion = "$($parts[0]).$($parts[1]).$build"
# 更新 manifest.yml
$manifest = $manifest -replace "^version:.*", "version: $newVersion"
$manifest | Set-Content $manifestPath -Encoding UTF8
Write-Host "版本: $currentVersion -> $newVersion" -ForegroundColor Green

Write-Host "`n=== [2/6] 编译 ===" -ForegroundColor Cyan
dotnet build -c Release
if ($LASTEXITCODE -ne 0) { Write-Host "编译失败" -ForegroundColor Red; exit 1 }
# 编译后重新写入 manifest（编译可能覆盖）
$manifest | Set-Content $manifestPath -Encoding UTF8

Write-Host "`n=== [3/6] 打包 yak ===" -ForegroundColor Cyan
$yakBuild = Join-Path $projRoot "yak_build"
Remove-Item "$yakBuild\*" -Force -ErrorAction SilentlyContinue
Copy-Item "bin\Release\net7.0\Turtle.rhp", "bin\Release\net7.0\Turtle.rui" -Destination $yakBuild
Copy-Item "bin\Release\net7.0\manifest.yml" -Destination $yakBuild -Force
Set-Location $yakBuild
& "C:\Program Files\Rhino 8\System\Yak.exe" build
Set-Location $projRoot

$yakFile = Get-ChildItem "$yakBuild\*.yak" | Select-Object -First 1
if (-not $yakFile) { Write-Host "打包失败" -ForegroundColor Red; exit 1 }
Write-Host "包: $($yakFile.Name)" -ForegroundColor Green

Write-Host "`n=== [4/6] 卸载旧版 ===" -ForegroundColor Cyan
& "C:\Program Files\Rhino 8\System\Yak.exe" uninstall Turtle

Write-Host "`n=== [5/6] 安装新版 ===" -ForegroundColor Cyan
& "C:\Program Files\Rhino 8\System\Yak.exe" install $yakFile.FullName

Write-Host "`n=== [6/6] 启动 Rhino ===" -ForegroundColor Cyan
Start-Process "C:\Program Files\Rhino 8\System\Rhino.exe" -ArgumentList "/nosplash"

Write-Host "`n✅ 完成！版本 $newVersion 已安装，Rhino 已启动。" -ForegroundColor Green
