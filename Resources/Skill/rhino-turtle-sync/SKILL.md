---
name: rhino-turtle-sync
description: Turtle 插件（Rhino 8）的"固化 + 同步 + 版本发布"全流程。当用户要求把 Rhino 最新状态固化进 Turtle 仓库、把仓库分发同步到 Rhino（Mac/Windows 任一平台）、升级版本号、或询问"都同步了哪些/哪些更新了"时使用。也用于排查工具列图标丢失、导入闪崩等。
---

# Turtle 固化同步流程

Turtle 是自研 Rhino 8 插件（仓库远端 `https://github.com/liuzhen4242/Turtle.git`）。**同步是单向的**：仓库（源）→ Rhino（分发）自动；Rhino（用户改动）→ 仓库需**手动固化**。本 skill 管理固化流程，**覆盖 Mac 与 Windows 双平台**。

## 核心守则

1. **固化前逐条检查、让用户确认**：先跑 `scripts/check_sync.py`（双平台自动检测）生成检查清单，把"哪些一致、哪些有差异"逐条列出给用户确认，确认后才动手。
2. **改 rui 前必须完全退出 Rhino**（Win 进程 `Rhinoceros.exe` / Mac `Rhinoceros`，强杀 `kill <pid>`；Mac pkill 常受限）。
3. **真正加载位是 packages 目录（Mac/Win 都如此）**：
   - Mac：`~/Library/Application Support/McNeel/Rhinoceros/packages/8.0/turtle/{ver}/Turtle.rui`（小写 turtle）
   - Win：`%APPDATA%\McNeel\Rhinoceros\packages\8.0\Turtle\{ver}\Turtle.rui`（大写 Turtle）
   - **Win 上 `8.0\UI\Turtle.rui` 目录不存在**；Mac 的 UI/MacPlugIns 目录 Rhino 根本不读——"改了很久没效果"的头号原因。
4. **写 McNeel 目录需 require_escalated**（沙箱外路径）。
5. **图标用 rui 内嵌数据（`<png>` 或 `<light><svg>`），禁止 `<svg_name>` 外部引用**——Win 不渲染、跨平台丢图标。详见 rhino-toolbar-rui skill。

## 版本治理（用户拍板 2026-10-15）

- **只维护 1.1.0，1.0 已废弃**（双端 packages 已删 1.0 目录）。勿再碰 1.0。
- 版本号只有用户明确要求才升；平时固化内容不升版本。
- **workspace 里的 check_sync.py / rui_sync.py 是旧版**（只认 1.0.0 或 UI 目录）；**权威版在仓库 git**（双平台、认当前版本）。跑前先核对脚本版本目录与实际一致。

## 资源清单（7 类，双平台位置）

| # | 类别 | 仓库位置 | Mac Rhino 位置 | Windows Rhino 位置 | 固化方向 |
|---|---|---|---|---|---|
| 1 | 工具列 rui | `Resources/Turtle.rui` | packages/8.0/turtle/{ver}/Turtle.rui（小写） | packages/8.0/Turtle/{ver}/Turtle.rui（大写） | 覆盖层 → 仓库 → 同步加载位，md5 校验 |
| 2 | Python 脚本 | `Scripts/*.py` | `8.0/Scripts/` | `8.0/scripts/`（小写） | 双向，md5 校验 |
| 3 | 材质 rmtl | `Resources/Materials/` + `assets/materials/` | `8.0/Render Content/en_US/Turtle/` | `8.0/Localization/en-US|zh-CN/Render Content/Turtle/`（两语种） | **以仓库 63 个为准**；Rhino 多余旧材质备份后删 |
| 4 | 快捷键 | `Resources/KeyTurtle.txt` | `8.0/settings/aliases`（可自动比对） | **Win 无 aliases 文件**，只能 GUI「工具→选项→键盘→导入」 | **以最新为准**，只保留一份 |
| 5 | 显示样式 ini | `Resources/DisplayStyles/`（13 个） | `8.0/settings/displaymodes/` | `8.0/DisplayModes/` | 以最后更新为准 |
| 6 | 模板 3dm | `Resources/Turtle.3dm` | `Rhinoceros/Template Files/Turtle.3dm` | `8.0/Localization/en-US|zh-CN/Template Files/`（两语种） | 以最后更新为准 |
| 7 | GH 电池 | `Grasshopper/` | 嵌入 rhp | 嵌入 rhp | 用户没改则保持现状 |

## 固化流程（每次发布/同步）

1. **跑检查清单**：`python3 "<skill目录>/scripts/check_sync.py" [--repo <仓库路径>]` → 输出 7 类 ✅一致 / ⚠️差异。
2. **逐条向用户确认**：快捷键以最新 aliases 覆盖仓库；材质以仓库 63 个为准（删多余前先备份）；显示样式/模板哪边最新以哪边为准。
3. **固化（Rhino → 仓库）**：快捷键（Mac）`cp "8.0/settings/aliases" Resources/KeyTurtle.txt`；材质 `cp Rhino材质目录/*.rmtl` → 仓库两处（旧文件备份 `.bak-<时间戳>`，gitignore 已忽略 `*.bak-*`）。
4. **同步分发（仓库 → Rhino）**：rui/脚本/材质/显示样式/模板各按上表复制到加载位，md5 校验。**先确认 Rhino 已完全退出**。
5. **版本与发布**：升版本改 `manifest.yml`（根 + yak_build）→ `dotnet build -c Release` → `cd yak_build && "/Applications/Rhino 8.app/Contents/Resources/bin/yak" build`。版本号只有用户明确要求才升。
6. **git 提交推送**：`cd <仓库> && git add -A && git commit -m "…" && git push origin main`。

## 双平台已知事实

- 仓库：Mac `/Users/zhenliu/study/coding/rhinoPluging`；Win `D:\00-素材\SoftTemple\Rhino\Turtle`。
- 5 个工具列：turtleMain、color-turtle、color-material-turtle、material-turtle、mouseTurtle（guid 见 rhino-toolbar-rui skill）。
- **材质库 63 个**（2026-09-28 核对）：29 个贴图材质（b-blacktop、bo-board×4、br-brick×4、co-concrate×4、gr-grass×6、m-aluminum、r-roofing×3、t-tile×4、x-line8、x-line12）+ 34 个 `Color_{R}_{G}_{B}_A{A}` 颜色材质。
  - **⚠️ 清理 Rhino 材质目录时禁止只按 `^Color_` 保留**——会误删 29 个贴图材质（material-turtle 按钮引用它们）。以仓库 `Resources/Materials` 文件集合为准对比删多余。
- 显示样式 13 个：Arctic(×3)、CAD、OnlyShadow、OutLine(×3)、RaytraceHardeShadow、Shaded、ShadowLine、Sketchup、Wireframe。
- KeyTurtle 当前 271 条，格式 `别名=宏`。
- **⚠️ 跨平台 md5 差异是行尾导致（正常，勿误判）**：Win CRLF vs Mac LF（git autocrlf）。**同平台内 md5 必须一致**；跨平台比对应先归一化行尾，或直接以文件集合/内容语义为准。
- **Win 专属坑**：`8.0\settings\Scheme__Default\` 残留旧版 Turtle 覆盖层 `Turtle_7338352c-….xml`（含已删旧按钮 guid 引用）会导致**导入工具列闪崩**——备份到 `Resources\.bak-scheme-*` 后删除。Rhino 退出会写回状态：改完重启前核对 packages rui 的 md5 未被覆盖。

## 双端取最新合并（覆盖层 → 仓库 → 分发）

**核心问题**：Win 与 Mac 两端工具列各自有独有修改，仓库 rui 是唯一权威。用户在 Rhino UI 手动加的按钮**只写在覆盖层** `settings/Scheme__Default/Turtle_7338352c-….xml`（Win）/ `OpenLink_7338352c-….xml`（Mac），**不写加载位 rui、不随 git 分发** → 这是"一端有、另一端没有"的根因。**覆盖层独有内容必须固化进仓库 rui 才能跨平台。**

**闭环**：
1. 备份仓库 rui 为 `.bak-merge-<时间戳>`；备份覆盖层到 `Resources\.bak-scheme-*`。
2. 比对加载位 rui 与覆盖层 `tool_bar_items`，找覆盖层独有/新增按钮（格式转换细节见 rhino-toolbar-rui skill）。
3. 把覆盖层 `<macro>+<svg_name>/<light_svg>` 转成仓库 `<macro_item>+<png>` 跨平台格式，合入仓库 rui（XML 校验）。
4. 同步 Mac 加载位 → git push → 另一端 pull 后同步加载位。**双端都取最新合并**。
5. 版本治理：1.0 已废弃，只维护 1.1.0。

## 脚本搜索路径一致性（2026-10-16 实证：同事装后"按钮功能都不能用"）

**症状**：同事 Win11+Rhino8 装 yak 后，**toolbar 有了、但大量按钮功能不可用**（脚本找不到）。

**根因（两个坑叠加）**：
1. **释放路径 ≠ Rhino 搜索路径**：工具列按钮宏用**相对文件名**（`! _-RunPythonScript "layerout.py"`），Rhino 只在自己的 scripts 搜索目录 `%APPDATA%\McNeel\Rhinoceros\8.0\scripts` 找相对名。但插件旧版把脚本释放到 `%AppData%\Turtle\Scripts`——**两处不一致**，同事机器没有脚本进 Rhino scripts 目录 → 按钮全部找不到脚本。自己机器能用，是因为**曾手动把脚本也放进过 Rhino scripts 目录**（不是插件放的）。
2. **宏写死用户名路径**：`KeyTurtle.txt` 里 `wa/NewAlias/stop` 3 条曾写死 `C:\Users\Liuzhen\...\vis_watch.py`，换机器（用户名 `scl`）必失效。

**修复（已完成，commit a9957f4）**：
- `TurtlePlugin.cs` 的 `ExtractEmbeddedScripts()` 改为**双路径释放**：脚本同时写到
  `%AppData%\McNeel\Rhinoceros\8.0\scripts`（按钮宏相对名能找到）+ `%AppData%\Turtle\Scripts`（别名宏 `{RHINO_SCRIPTS}` 用）。
- `KeyTurtle.txt` 写死的 3 条改 `{RHINO_SCRIPTS}\vis_watch.py` 占位符（插件注册时替换成实际路径，跨机器通用）。

**排查要点**：
- 检查按钮宏形态：相对名 `"xxx.py"` = 依赖 Rhino scripts 搜索路径；绝对路径 = 依赖写死路径。**rui 里不应有任何写死的 `C:\Users\...` 或 `D:\...` 路径**（用 Grep 搜 `Users\\|:[A-Za-z]:\\` 验证）。
- 检查 `KeyTurtle.txt` 是否有写死用户名路径的条目（应全用 `{RHINO_SCRIPTS}` 占位符）。
- 装新版后应看到 `...\Rhinoceros\8.0\scripts` 出现插件的 26 个 py（alignPage、layerout、surToHatch 等）。

## git 推送验证（Win，2026-10-15 实证）

- **`git status -sb` 的 `[ahead N]` 不可靠**：`git push <url>` 用完整 URL 推送后 tracking 不刷新，仍显示 `[ahead 1]`——**不能据此判断推送是否成功**。
- **正确验证**：带代理 `ls-remote` 对比远端 main 与本地 HEAD 完整哈希：
  ```powershell
  git -C <仓库> -c http.proxy=http://127.0.0.1:7890 ls-remote https://github.com/liuzhen4242/Turtle.git main
  git -C <仓库> rev-parse HEAD
  ```
  两者 40 位哈希一致 = 推送成功。
- **PowerShell 把 git stderr 当 NativeCommandError 显示**：`git push` 输出 "Everything up-to-date" 且 `$LASTEXITCODE=0` 即成功，红色 RemoteException 是误报。
- **PowerShell stdout 被吞**：`git … 2>&1 | Out-String` 可能不显示输出；改用 `$x = git … 2>&1; Write-Output $x`。
- **推送命令**：`git -C <仓库> -c http.proxy=http://127.0.0.1:7890 push https://github.com/liuzhen4242/Turtle.git main`（SSH 不通、https 直连被 reset，必须带代理）。

## 关联 skill 分工

- **rhino-toolbar-rui**：管 rui 细节（图标格式、覆盖层固化格式转换、排障速查：Error loading 根因 / 右键缺失真相 / 图标蓝色文字 / dock 丢失）。
- **rhino-turtle-sync**：管固化同步总流程（本文件）。
- 两者配合：工具栏/图标问题查 rui skill，固化同步流程查本 skill。
