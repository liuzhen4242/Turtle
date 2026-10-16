# Turtle 一键更新脚本
# 用法: 在项目根目录跑 .\update.ps1
# 流程: 关闭 Rhino -> 递增版本号 -> 编译 -> 打包 yak -> 卸载旧版 -> 安装新版 -> 启动 Rhino

$ErrorActionPreference = "Continue"
$projRoot = $PSScriptRoot
# 路径安全校验：确保 $projRoot 非空、非盘符根、且确为 Turtle 项目根（防止误删扩大范围）
if ([string]::IsNullOrWhiteSpace($projRoot)) {
    Write-Host "项目根目录为空，中止" -ForegroundColor Red; exit 1
}
if (-not (Test-Path -LiteralPath $projRoot)) {
    Write-Host "项目根目录不存在: [$projRoot]" -ForegroundColor Red; exit 1
}
$projRoot = [System.IO.Path]::GetFullPath($projRoot)
if ($projRoot -eq ([System.IO.Path]::GetPathRoot($projRoot))) {
    Write-Host "项目根目录不能是盘符根: [$projRoot]" -ForegroundColor Red; exit 1
}
if (-not (Test-Path -LiteralPath (Join-Path $projRoot "Turtle.csproj"))) {
    Write-Host "未检测到 Turtle.csproj，[$projRoot] 不是 Turtle 项目根，中止" -ForegroundColor Red; exit 1
}
Set-Location $projRoot

Write-Host "=== [0/5] 关闭 Rhino ===" -ForegroundColor Cyan
Get-Process Rhino* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "`n=== [1/5] 编译 ===" -ForegroundColor Cyan
dotnet build -c Release
if ($LASTEXITCODE -ne 0) { Write-Host "编译失败" -ForegroundColor Red; exit 1 }

Write-Host "`n=== [2/5] 打包 yak ===" -ForegroundColor Cyan
$yakBuild = Join-Path $projRoot "yak_build"
# 安全校验：$yakBuild 必须位于项目根内，且项目根已确认为 Turtle 项目
if (-not $yakBuild.StartsWith($projRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    Write-Host "yak_build 路径异常，中止" -ForegroundColor Red; exit 1
}
if (Test-Path "$yakBuild\manifest.yml") { Copy-Item "$yakBuild\manifest.yml" "$yakBuild\manifest.yml.bak" -Force -ErrorAction SilentlyContinue }
Remove-Item "$yakBuild\*" -Force -ErrorAction SilentlyContinue
# 打包 6 件套：dll / rhp / rui / deps.json / pdb / manifest.yml（.NET7 插件需 deps.json）
Copy-Item "bin\Release\net7.0\Turtle.dll" -Destination $yakBuild
Copy-Item "bin\Release\net7.0\Turtle.rhp", "bin\Release\net7.0\Turtle.rui" -Destination $yakBuild
Copy-Item "bin\Release\net7.0\Turtle.deps.json" -Destination $yakBuild
Copy-Item "bin\Release\net7.0\Turtle.pdb" -Destination $yakBuild
# manifest 用之前备份的 yak_build 版本（带顶层 id，name 大写 Turtle），不要用 bin 里的
if (Test-Path "$yakBuild\manifest.yml.bak") { Move-Item "$yakBuild\manifest.yml.bak" "$yakBuild\manifest.yml" -Force }
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
