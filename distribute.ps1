# Turtle — 资源分发脚本
# 用法：右键 -> 使用 PowerShell 运行，或终端里 .\distribute.ps1
# 作用：把 assets/ 里的源文件分发到 Resources/ 分发目录（只复制，不移动，assets 原件保留）
#
# 为什么有这个脚本：
#   assets/  = 源文件存档（你平时放新文件的地方，所有原始素材都在这里）
#   Resources/ = 随插件分发的目录（用户拿到插件包时带走的）
#   每次往 assets/ 里放了新文件/改了源文件，跑一次本脚本即可同步到 Resources/

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "==> Turtle 资源分发..." -ForegroundColor Cyan

# 1. ini 显示样式：assets/ini -> Resources/DisplayStyles
$srcIni  = Join-Path $root "assets\ini"
$dstIni  = Join-Path $root "Resources\DisplayStyles"
if (Test-Path $srcIni) {
    New-Item -ItemType Directory -Path $dstIni -Force | Out-Null
    $iniCount = @(Get-ChildItem (Join-Path $srcIni "*.ini")).Count
    Copy-Item (Join-Path $srcIni "*.ini") $dstIni -Force
    Write-Host "  [ini] $iniCount 个显示样式 -> Resources\DisplayStyles" -ForegroundColor Green
} else {
    Write-Host "  [ini] assets\ini 不存在，跳过" -ForegroundColor Yellow
}

# 2. 材质文件：assets/materials -> Resources/Materials
$srcMat = Join-Path $root "assets\materials"
$dstMat = Join-Path $root "Resources\Materials"
if (Test-Path $srcMat) {
    New-Item -ItemType Directory -Path $dstMat -Force | Out-Null
    $matCount = @(Get-ChildItem (Join-Path $srcMat "*.rmtl")).Count
    Copy-Item (Join-Path $srcMat "*.rmtl") $dstMat -Force
    Write-Host "  [材质] $matCount 个材质 -> Resources\Materials" -ForegroundColor Green
} else {
    Write-Host "  [材质] assets\materials 不存在，跳过" -ForegroundColor Yellow
}

# 3. 工具栏：assets/rui -> Resources（若 assets 里有 rui 则同步）
$srcRui = Join-Path $root "assets\rui"
$dstRui = Join-Path $root "Resources"
if (Test-Path $srcRui) {
    Copy-Item (Join-Path $srcRui "*.rui") $dstRui -Force
    Write-Host "  [rui] assets\rui -> Resources\" -ForegroundColor Green
} else {
    Write-Host "  [rui] assets\rui 不存在，跳过（Resources\Turtle.rui 保持现状）" -ForegroundColor Yellow
}

# 4. ghuser：Grasshopper/ 是嵌入文件，不从 assets 覆盖
#    （assets/ghuser 是未 patch 的原件，Grasshopper/Arrows.ghuser 是分发用版本，需要手动 patch 后放置）
Write-Host "  [ghuser] 注意：assets\ghuser 是原件，Grasshopper\Arrows.ghuser 是分发版，"
Write-Host "           改原件后需用 tools\patch_ghuser.py 打补丁再覆盖到 Grasshopper\，本脚本不自动处理。" -ForegroundColor Yellow

Write-Host ""
Write-Host "分发完成。Resources/ 目录内容如下：" -ForegroundColor Cyan
Get-ChildItem (Join-Path $root "Resources") -Recurse -File | ForEach-Object { Write-Host "  " $_.FullName.Replace($root + "\", "") }
