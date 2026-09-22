# Turtle 一键更新脚本
# 用法: 在项目根目录跑 .\update.ps1
# 流程: 关闭 Rhino -> 递增版本号 -> 编译 -> 打包 yak -> 卸载旧版 -> 安装新版 -> 启动 Rhino

$ErrorActionPreference = "Continue"
$projRoot = $PSScriptRoot
Set-Location $projRoot

Write-Host "=== [0/5] 关闭 Rhino ===" -ForegroundColor Cyan
Get-Process Rhino* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "`n=== [1/5] 编译 ===" -ForegroundColor Cyan
dotnet build -c Release
if ($LASTEXITCODE -ne 0) { Write-Host "编译失败" -ForegroundColor Red; exit 1 }

Write-Host "`n=== [2/5] 打包 yak ===" -ForegroundColor Cyan
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

Write-Host "`n=== [3/5] 卸载旧版 ===" -ForegroundColor Cyan
& "C:\Program Files\Rhino 8\System\Yak.exe" uninstall Turtle

Write-Host "`n=== [4/5] 安装新版 ===" -ForegroundColor Cyan
& "C:\Program Files\Rhino 8\System\Yak.exe" install $yakFile.FullName

Write-Host "`n=== [5/5] 启动 Rhino ===" -ForegroundColor Cyan
Start-Process "C:\Program Files\Rhino 8\System\Rhino.exe" -ArgumentList "/nosplash"

Write-Host "`n✅ 完成！Rhino 已启动，插件自动加载。" -ForegroundColor Green
