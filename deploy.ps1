# Turtle — 一键部署脚本
# 用法：右键 -> 使用 PowerShell 运行，或终端里 .\deploy.ps1
# 作用：资源同步 → 编译 → 打包 yak → 卸载旧版 → 安装新版
# 以后每次改了代码/资源，跑这一个脚本就够了

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$yakExe = "C:\Program Files\Rhino 8\System\Yak.exe"
# 路径安全校验：确保 $root 非空、非盘符根、且确为 Turtle 项目根
if ([string]::IsNullOrWhiteSpace($root)) {
    Write-Host "项目根目录为空，中止" -ForegroundColor Red; exit 1
}
if (-not (Test-Path -LiteralPath $root)) {
    Write-Host "项目根目录不存在: [$root]" -ForegroundColor Red; exit 1
}
$root = [System.IO.Path]::GetFullPath($root)
if ($root -eq ([System.IO.Path]::GetPathRoot($root))) {
    Write-Host "项目根目录不能是盘符根: [$root]" -ForegroundColor Red; exit 1
}
if (-not (Test-Path -LiteralPath (Join-Path $root "Turtle.csproj"))) {
    Write-Host "未检测到 Turtle.csproj，[$root] 不是 Turtle 项目根，中止" -ForegroundColor Red; exit 1
}

Write-Host "==> [1/5] 资源同步 (assets -> Resources)..." -ForegroundColor Cyan
& (Join-Path $root "distribute.ps1")

Write-Host "==> [2/5] 编译 Release..." -ForegroundColor Cyan
Set-Location $root
& dotnet build -c Release --nologo 2>&1 | Select-Object -Last 3
if ($LASTEXITCODE -ne 0) { Write-Host "编译失败！" -ForegroundColor Red; exit 1 }

Write-Host "==> [3/5] 打包 yak..." -ForegroundColor Cyan
$buildDir = Join-Path $root "yak_build"
# 安全校验：$buildDir 必须位于项目根内
if (-not $buildDir.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
    Write-Host "yak_build 路径异常，中止" -ForegroundColor Red; exit 1
}
New-Item -ItemType Directory -Path $buildDir -Force | Out-Null
# 先备份 manifest（带顶层 id），再清空打包目录
if (Test-Path (Join-Path $buildDir "manifest.yml")) { Copy-Item (Join-Path $buildDir "manifest.yml") (Join-Path $buildDir "manifest.yml.bak") -Force -ErrorAction SilentlyContinue }
Remove-Item (Join-Path $buildDir "*") -Force -ErrorAction SilentlyContinue
# 打包 6 件套：dll / rhp / rui / deps.json / pdb / manifest.yml（缺一不可，.NET7 插件需 deps.json）
Copy-Item (Join-Path $root "bin\Release\net7.0\Turtle.dll") $buildDir
Copy-Item (Join-Path $root "bin\Release\net7.0\Turtle.rhp") $buildDir
Copy-Item (Join-Path $root "bin\Release\net7.0\Turtle.rui") $buildDir
Copy-Item (Join-Path $root "bin\Release\net7.0\Turtle.deps.json") $buildDir
Copy-Item (Join-Path $root "bin\Release\net7.0\Turtle.pdb") $buildDir
# manifest 用备份回来的 yak_build 版本（带顶层 id，name 大写 Turtle），不要用 bin 里的（MakeRhp 不产 manifest）
if (Test-Path (Join-Path $buildDir "manifest.yml.bak")) { Move-Item (Join-Path $buildDir "manifest.yml.bak") (Join-Path $buildDir "manifest.yml") -Force }
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
Write-Host "    安装位置: %APPDATA%\McNeel\Rhinoceros\packages\8.0\Turtle\{版本}\" -ForegroundColor Gray
