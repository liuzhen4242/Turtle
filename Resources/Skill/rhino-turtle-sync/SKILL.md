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

## 版本治理（用户拍板 2026-10-15）

- **用户明确"以后不用再管 1.0 版本，已经进入 1.1"**：Win 端当前只有 1.0.0（`%APPDATA%\McNeel\Rhinoceros\packages\8.0\Turtle\1.0.0\`），1.1.0 目录不存在；部署目标是 Win 1.1.0（从 Mac 拿 1.1.0 产物）。**做同步/分发时，凡涉及加载位覆盖，必须同时覆盖当前生效版本目录；是否删除旧 1.0.0 目录需用户拍板。**
- 版本号只有用户明确要求才升，平时固化内容不升版本。
- **check_sync.py / rui_sync.py 里的版本号/路径已过时**（旧脚本只认 1.0.0 或 UI 目录），跑之前先核对脚本中的版本目录与实际一致，必要时按当前版本修正。

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

## 双端取最新合并 + 覆盖层独有内容固化（2026-10-15 实证）

**核心问题**：Win 与 Mac 两端工具列各自有独有修改，仓库 rui 是唯一权威。用户在某台机器 Rhino 里手动追加的按钮（如 Win mouseTurtle 的 Cage/CageEdit/SoftEdit）**只存在该机的覆盖层里，仓库 rui 没有**——这是"另一台机器看不到新按钮"的根因。

**规则**：
1. **覆盖层是独有修改的唯一来源**：Win `%APPDATA%\McNeel\Rhinoceros\8.0\settings\Scheme__Default\Turtle_7338352c-….xml` / Mac `OpenLink_7338352c-….xml`。先备份到 `Resources\.bak-scheme-*`。
2. **合并方向**：覆盖层独有的宏/图标 → 合并进仓库 rui（转标准格式，见 rhino-toolbar-rui skill）→ git push → 另一端 pull 后同步加载位。**双端都取最新合并**。
3. **覆盖层独有内容必须固化，否则丢失**：重启或加载位被覆盖层旧版覆盖后，未固化的独有按钮会消失。
4. **合并产物**：mouseTurtle 新增 2 按钮（4宏+2图标）已并入仓库（commit `735c17f`）。

## git 推送验证方法（Win，2026-10-15 实证）

- **`git status -sb` 的 `[ahead N]` 不可靠**：它是本地 `origin/main` tracking 引用的状态，`git push <url>` 用完整 URL 推送后 tracking 不一定会刷新，仍显示 `[ahead 1]`——**不能据此判断推送是否成功**。
- **正确验证**：用带代理 `ls-remote` 对比远程 main 与本地 HEAD 的完整哈希是否一致：
  ```powershell
  git -C <仓库> -c http.proxy=http://127.0.0.1:7890 ls-remote https://github.com/liuzhen4242/Turtle.git main
  git -C <仓库> rev-parse HEAD
  ```
  两者 40 位哈希一致 = 推送成功。
- **PowerShell 会把 git stderr 当 NativeCommandError 显示**：`git push` 输出 "Everything up-to-date" 且 `$LASTEXITCODE=0` 即为成功，红色 RemoteException 是误报，不要当作失败。
- **PowerShell stdout 被吞的坑**：`git … 2>&1 | Out-String` 有时不显示输出；改用 `$x = git … 2>&1; Write-Output $x` 捕获。
- **推送命令**：`git -C <仓库> -c http.proxy=http://127.0.0.1:7890 push https://github.com/liuzhen4242/Turtle.git main`（SSH remote 不通、https 直连被 reset，必须带代理）。

## 双端工具列"取最新合并"的完整闭环（2026-10-15 实证，含覆盖层）

**用户手动加在 Rhino UI 里的按钮，落在覆盖层 `settings/Scheme__Default/Turtle_7338352c-….xml`，不写进加载位 rui，也不随 git 分发** —— 这是"Mac 有某按钮、Win 没有"（或反之）的根因。完整固化闭环：

1. **发现**：比对加载位 rui 与覆盖层的 `tool_bar_items`，找出覆盖层独有/新增按钮。详见 rhino-toolbar-rui skill"覆盖层独有按钮的固化"。
2. **合并**：把覆盖层的 `<macro>+<svg_name>/<light_svg>` 转成仓库 rui 的 `<macro_item>+<png>` 跨平台格式，合入仓库 rui（脚本操作，XML 校验）。
3. **同步 Mac 加载位**：`packages/8.0/turtle/1.1.0/Turtle.rui`（写 McNeel 目录需提权）。
4. **git push**（Mac 也需代理）：`git -c http.proxy=http://127.0.0.1:7890 push origin main`。
5. **同步 Win 加载位**：在 Win 端 `git pull` 后，覆盖 `packages/8.0/Turtle/1.1.0/Turtle.rui`（先备份）。
6. **版本治理**：1.0.0 已废弃（2026-10-15 从 Mac/Win packages 删除），**只维护 1.1.0**，勿再碰 1.0。

**校验推送是否成功的通用法**（Mac/Win 一致）：
```bash
git -c http.proxy=http://127.0.0.1:7890 fetch origin main && \
git rev-parse HEAD && git rev-parse origin/main
# 两个 40 位哈希一致 = 已推送成功
```

## "Error loading - Turtle.rhp" 弹窗根因：packages 残留旧版备份目录（2026-10-15 实证）

**症状**：打开 Win Rhino 时弹出 "Done installing plug-ins / Loaded - Turtle.rhp / Error loading - Turtle.rhp" 三个同时出现。

**根因**：Rhino 的包扫描器会把 `packages\8.0\` 下**所有以 `Turtle` 开头的目录**都当作 Turtle 包处理，扫描每个目录里的 `.rhp` 并尝试加载。当 `packages\8.0\` 下同时存在：
- `Turtle\`（当前 1.1.0，`manifest.txt`=1.1.0）✅
- `Turtle.bak-before110-…`（残留备份，`manifest.txt`=1.0.0，内含 `1.0.0\Turtle.rhp`）❌

Rhino 会同时加载 1.1.0（成功 → "Loaded"）和备份里的 1.0.0 rhp（旧版/缺失依赖 → "Error loading"）——这正是"Loaded 与 Error loading 同时出现"的矛盾现象来源。

**处理（2026-10-15 已做）**：
1. 确认 Rhino 已完全退出。
2. 把 `packages\8.0\Turtle.bak-before110-…` 整个目录**移出 packages**（移到仓库 `Resources\.bak-packages-before110-…` 保留，完全可逆），而非直接删除。
3. 移出后 `packages\8.0\` 下只剩 `Turtle\`（1.1.0），重启 Rhino 弹窗应消失。

**教训**：**任何 `packages\8.0\` 下以 `Turtle` 开头（含 `Turtle.bak-*` / `Turtle.*`）的目录都可能被 Rhino 扫描加载**。升级/备份时不要把旧版包以 `Turtle.bak-*` 形式留在 packages 目录里，应移出到仓库或其他 Rhino 不扫描的位置。

## 按钮右键功能缺失真相：右宏从未固化，Win 从无（2026-10-15 实证）

**症状**：用户反馈"部分按钮右键功能丢失"（如 cameraMove），Win Rhino 里右键 Tooltip/Command 全空。

**真相（已用 git 历史 + 全部备份 rui 逐一核验）**：
- **cameraMove（按钮 `3dab8b26`）在所有 rui 历史版本里都只有 `<left_macro_id>`（左键 `af12646c`=cameraMove.py），从未有 `<right_macro_id>`**。包括：git 最早提交（`2f6ad41` 1.1.0 固化）、`Turtle.rui.bak-icon-test`（9/28）、两次合并备份、当前 22 按钮版。
- **Win 覆盖层 `Turtle_7338352c.xml` 也不含 cameraMove**（覆盖层只有 CPlane Top、Grasshopper 两个 Rhino 内置命令 macro）。
- **结论**：这些按钮的右键功能**从未固化进仓库/加载位 rui**。最可能来源是用户在 **Mac Rhino 界面**手动加的右键（存在 Mac 覆盖层，不随 git 分发），Win 端从没有过。**不是本次合并丢失的**。

**处理**：用户在 Win 端自行重写右键即可（Rhino 里右键按钮 → 编辑 → 设置右键命令）。若要让右键跨平台生效，需在 Mac 覆盖层提取右键宏 → 固化进仓库 rui（转标准 `<macro_item>`+`<right_macro_id>`）→ 同步双端。

**排查方法**（判断某按钮右键是否曾存在）：
```python
# 在某 rui 中查按钮 tool_bar_item 是否有 right_macro_id
import re
text = open('Turtle.rui', encoding='utf-8-sig').read()
tb = re.search(r'<tool_bar guid="55f2b50c-4258-4c1b-9bba-133cd6b0f251".*?</tool_bar>', text, re.S).group(0)
for it in re.finditer(r'<tool_bar_item guid="3dab8b26[^"]*".*?</tool_bar_item>', tb, re.S):
    print(re.sub(r'\s+',' ', it.group(0)))  # 只有 left_macro_id = 无右键
```
- 覆盖层含某按钮 = 该按钮的修改在覆盖层里（不随 git 分发）。覆盖层按钮需固化进仓库才能跨平台同步。
