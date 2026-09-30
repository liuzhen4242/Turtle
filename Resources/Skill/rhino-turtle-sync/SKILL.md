---
name: rhino-turtle-sync
description: Turtle 插件（Rhino 8）的"固化 + 同步 + 版本发布"全流程。当用户要求把 Rhino 里的最新状态固化进 Turtle 仓库、把仓库分发同步到 Rhino（Mac/Windows 任一平台）、升级版本号（如 1.1.0）、或询问"都同步了哪些东西/哪些更新了哪些没更新"时使用。核心：固化前必须逐条跑检查清单、让用户确认差异项，再按确认结果同步、git 提交推送。也用于排查 Turtle 在 Windows Rhino 上的工具列图标丢失、导入闪崩等问题。
---

# Turtle 固化同步流程

Turtle 是自研 Rhino 8 插件（仓库远端 `https://github.com/liuzhen4242/Turtle.git`）。**同步是单向的**：仓库（源）→ Rhino（分发）自动；Rhino（用户改动）→ 仓库需**手动固化**。本 skill 管理这个固化流程，**覆盖 Mac 与 Windows 双平台**。

## 核心守则

1. **固化前逐条检查、让用户确认**：每次固化先跑 `scripts/check_sync.py`（双平台自动检测）生成检查清单，把"哪些一致、哪些有差异"逐条列出给用户确认，确认后才动手。
2. **改 rui 前必须完全退出 Rhino**：Rhino 退出时会用自身状态覆盖 rui（Windows 进程名 `Rhinoceros.exe` / macOS `Rhinoceros`，强杀 `kill <pid>`；Mac 上 pkill 常受限）。改 rui 前先确认用户没有在用 Rhino。
3. **真正加载位是 packages 目录（Mac/Win 都如此）**：
   - Mac：`~/Library/Application Support/McNeel/Rhinoceros/packages/8.0/turtle/1.0.0|1.1.0/Turtle.rui`（小写 turtle）
   - Windows：`%APPDATA%\McNeel\Rhinoceros\packages\8.0\Turtle\1.0.0|1.1.0\Turtle.rui`（大写 Turtle）
   - **Windows 上 `8.0\UI\Turtle.rui` 目录不存在**；Mac 的 UI/MacPlugIns 目录 Rhino 根本不读——"改了很久没效果"的头号原因。
4. **写 McNeel 目录需 require_escalated**（沙箱外路径）。
5. **图标用内嵌数据，不用外部文件引用**：所有按钮图标必须是 rui 内嵌的 `<png>` 或 `<light><svg>` 数据。**禁止 `<svg_name>`（外部 SVG 文件引用）**——Windows Rhino 8 不渲染，且跨平台会因文件缺失/路径不同导致图标丢失。

## 资源清单（7 类，双平台位置）

| # | 类别 | 仓库位置 | Mac Rhino 位置 | Windows Rhino 位置 | 固化方向 |
|---|---|---|---|---|---|
| 1 | 工具列 rui | `Resources/Turtle.rui` | packages/8.0/turtle/{ver}/Turtle.rui（小写） | packages/8.0/Turtle/{ver}/Turtle.rui（大写） | 覆盖层 → 仓库 → 同步加载位，md5 校验 |
| 2 | Python 脚本 | `Scripts/*.py`（12 个） | `8.0/Scripts/` | `8.0/scripts/`（小写） | 双向，md5 校验 |
| 3 | 材质 rmtl | `Resources/Materials/` + `assets/materials/` | `8.0/Render Content/en_US/Turtle/` | `8.0/Localization/en-US|zh-CN/Render Content/Turtle/`（两语种） | **以仓库 63 个为准**（构成：29 贴图 + 34 Color）；**Rhino 里多余旧材质必须删除** |
| 4 | 快捷键 | `Resources/KeyTurtle.txt` | `8.0/settings/aliases`（可自动比对） | **Windows 无 aliases 文件**，只能 GUI「工具→选项→键盘→导入」 | **以最新为准**，只保留一份，两边同步都带最新 |
| 5 | 显示样式 ini | `Resources/DisplayStyles/`（13 个） | `8.0/settings/displaymodes/` | `8.0/DisplayModes/` | 以最后更新为准 |
| 6 | 模板 3dm | `Resources/Turtle.3dm` | `Rhinoceros/Template Files/Turtle.3dm` | `8.0/Localization/en-US|zh-CN/Template Files/`（两语种） | 以最后更新为准 |
| 7 | GH 电池 | `Grasshopper/`（ghuser + cs） | 嵌入 rhp | 嵌入 rhp | 用户没改则保持现状 |

## 固化流程（每次发布/同步）

### Step 1：跑检查清单（双平台）
```bash
python3 "<skill目录>/scripts/check_sync.py" [--repo <仓库路径>]
```
脚本按当前系统自动检测 Mac/Windows 路径。输出 7 类资源对比：✅ 一致 / ⚠️ 差异（含明细：缺哪些、多哪些、值不同）。

### Step 2：逐条向用户确认
把清单逐条列出，明确"哪些更新了、哪些没更新"，让用户确认固化方向。用户裁决优先：
- **快捷键**：以 Rhino 最新 aliases 覆盖仓库 `Resources/KeyTurtle.txt`（Windows 上用户 GUI 导入后无法比对，提示即可）
- **材质**：删仓库旧/重复，换成 63 个新命名（`assets/materials` + `Resources/Materials` 两处）；**同步时若 Rhino 目录有多余旧材质，先备份再删除**
- **显示样式/模板**：哪边最后更新以哪边为准

### Step 3：固化（Rhino → 仓库）
- **快捷键（Mac）**：`cp "8.0/settings/aliases" Resources/KeyTurtle.txt`
- **材质**：`cp Rhino材质目录/*.rmtl` → `assets/materials/` + `Resources/Materials/`（先备份旧文件为 `.bak-<时间戳>`，gitignore 已忽略 `*.bak-*`）
- **显示样式/模板**：按用户裁决复制

### Step 4：同步分发（仓库 → Rhino）
- **rui**：`copy 仓库Resources/Turtle.rui → packages/{ver}/Turtle.rui`（Mac/Win 各自的 packages 位），md5 校验。**先确认 Rhino 已完全退出**。
- **脚本**：`Scripts/*.py` → 各自 Scripts/scripts 目录，md5 校验
- **材质**：仓库两处 → Rhino 材质目录（Mac 一语种 / Windows 两语种）；**多余旧材质备份后删除**
- **显示样式**：`Resources/DisplayStyles/*.ini` → 各自目录
- **模板**：`Resources/Turtle.3dm` → 各自 Template Files（Windows 两语种）

### Step 5：版本与发布
- 升版本时改 `manifest.yml`（根 + yak_build）→ 编译 `dotnet build -c Release`（net48）→ yak 打包
- 打包：`cd yak_build && "/Applications/Rhino 8.app/Contents/Resources/bin/yak" build`
- **用户裁决：版本号只有用户明确要求才升**，平时固化内容不升版本。

### Step 6：git 提交推送
```bash
cd <仓库> && git add -A && git commit -m "描述固化内容" && git push origin main
```
**Windows 推送必须带代理**：`git -c http.proxy=http://127.0.0.1:7890 push https://github.com/liuzhen4242/Turtle.git main`（SSH remote 不通、https 直连被 reset）。推送超时转后台，用 TaskOutput 收尾确认。

## 双平台已知事实

- 仓库：Mac `/Users/zhenliu/study/coding/rhinoPluging`；Windows `D:\00-素材\SoftTemple\Rhino\Turtle`
- 5 个工具列：turtleMain、color-turtle、color-material-turtle、material-turtle、mouseTurtle（guid 见 rhino-toolbar-rui skill）
- **材质库 63 个的准确构成（2026-09-28 核对）**：29 个贴图材质（b-blacktop、bo-board×4、br-brick×4、co-concrate×4、gr-grass×6、m-aluminum、r-roofing×3、t-tile×4、x-line8、x-line12）+ 34 个 `Color_{R}_{G}_{B}_A{A}` 颜色材质（A0=非透明 / A120=透明）。
  - **⚠️ 清理 Rhino 材质目录时禁止只按 `^Color_` 保留**——否则会误删 29 个贴图材质（material-turtle 按钮引用它们）。正确做法：以仓库 `Resources/Materials` 的文件集合为准，对比后删多余。
- 材质命名规则：`Color_{R}_{G}_{B}_A{A}.rmtl`（A0=非透明 / A120=透明），当前共 63 个
- 显示样式 13 个：Arctic(×3)、CAD、OnlyShadow、OutLine(×3)、RaytraceHardeShadow、Shaded、ShadowLine、Sketchup、Wireframe
- KeyTurtle 当前 271 条，格式 `别名=宏`（Rhino aliases 格式）
- **⚠️ 跨平台 md5 差异是行尾导致（正常现象，勿误判）**：Windows 仓库/分发文件为 CRLF、Mac 为 LF（git autocrlf 差异），同一 commit 在两台的 md5 不同（如 rui：Win `3ef222…` vs Mac `97de9b…`）。**同平台内 md5 必须一致**；跨平台比对应先把两文件行尾归一化再比，或直接以文件集合/内容语义为准。
- **Windows 专属坑**：
  - `8.0\settings\Scheme__Default\` 下残留旧版 Turtle 覆盖层 `Turtle_7338352c-….xml`（含已删除的旧按钮 guid 引用）会导致**导入工具列闪崩**——删除覆盖层即可（先备份到 `Resources\.bak-scheme-*`）
  - turtleMain 图标曾用非标准 `<svg_name>`+`<light_svg>` 结构 → Windows 上全部图标丢失；改为标准 `<light><svg>` 内嵌后恢复（详见 rhino-toolbar-rui skill）
  - Rhino 退出会写回状态：改 rui 前确认进程已完全结束；改完重启前可再核对 packages rui 的 md5 未被覆盖
- rhino-toolbar-rui skill（图标/覆盖层/颜色宏规范）与 rhino-turtle-sync 配合使用：前者管 rui 细节，后者管固化同步总流程
