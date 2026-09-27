# Turtle 开发日志

记录工具栏（rui）开发、排障与分发过程中踩过的坑和固化下来的流程，供后续继续做 toolbar 时复用。

## 2026-09-27 宏库清理 + 手动修改固化（commit 96091ba）

### 背景
- Rhino 宏选择器里残留 "Macro 04 (沥青)"、"Macro 05 (混凝土-白色)" 等旧名宏，
  来自从旧 material-ma / material-co 复制按钮时带入的宏定义（script 已指向正确材质，
  但 text/tooltip 还是旧名）。
- 用户在 Rhino 里手动加了 4 个新按钮（align page / cameraMove / lineWidthScale / surToHatch）
  和主工具列图标 + batchCapture 右键宏，修改只在运行中的 Rhino 会话里，重启即丢。

### 宏库清理（改 git 源 Resources/Turtle.rui）
- material-turtle 32 个宏：`<text>` 和 `<tooltip>` 从 "Macro 04/05"、"沥青/混凝土-白色/混凝土4"
  统一改为 script 中的材质名（b-blacktop / m-aluminum / w-wood1~3 / gr-grass1~6 /
  co-concrate1~4 / bo-board1~4 / br-brick1~4 / r-roofing1~3 / t-tile1~4 / x-line8 / x-line12）。
- color-material-turtle 31 个宏：缺 `<text>` 的补上 `<text> = 材质名`（Color_{R}_{G}_{B}_A{A}）。
- 检查口径：宏库里 `text 缺失`、`text 以 "Macro 0" 开头且不含 "|"`、`tooltip 含 沥青/混凝土` 均为问题项。
- 宏库总数 115 → 121（+6 新宏），残留旧名 = 0。

### 用户手动修改固化（关键流程）
**原理**：Rhino 运行中的工具栏修改存在内存会话，只有**正常退出（Cmd+Q）**时才会写入
覆盖层 `~/Library/Application Support/McNeel/Rhinoceros/8.0/settings/Scheme__Default/
Turtle_7338352c-….xml`。强杀（kill）会丢修改。

固化步骤：
1. 用户正常退出 Rhino → 覆盖层生成（~50KB）
2. 解析覆盖层 `<tool_bars>`（modified=True 的按钮与新增按钮）、`<icons>`、`<macros>`
3. 合并进源 rui：
   - 新增宏（无 source_guid 的 `<macro guid=…>`）→ 转成 `<macro_item guid=… bitmap_id=…>` 追加进 `<macros>`
   - 新增按钮（无 source_guid 的 `<tool_bar_item guid=…>`）→ 追加到主工具列末尾
   - 修改宏（`source_guid` + `bitmap_guid`）→ 更新源宏的 bitmap_id
   - 修改按钮（`source_guid` + 新 left_macro/right_macro）→ 更新源按钮
   - 图标：覆盖层 `<icon guid=…>`（Rhino 标准 svg_name + light_svg 格式）→ 追加进 `<icons>`
4. XML 校验 → rui_sync.py 同步 5 处 → git commit

本次固化内容：
- 主工具列 14 → 18 按钮：新增 align page（左 alignPage.py / 右 lineWidthScale.py）、
  cameraMove、lineWidthScale、surToHatch
- lineSplit / moveLayer / selectFilter 按钮宏加 bitmap_id（新图标）
- batchCapture 加右键宏 batchCapturesSnapshots（batchCapturesSnapshots.py）
- 修正 cameraMove 拼写（用户写的 CmaeraMove → cameraMove，与 cameraMove.py 对齐）
- 新宏 text 统一为功能名（align page / lineWidthScale / cameraMove / surToHatch / batchCapturesSnapshots）

### 脚本分发位置（重要）
- Rhino 8 的 `! _-RunPythonScript "xxx.py"` 命令按文件名在
  `~/Library/Application Support/McNeel/Rhinoceros/8.0/Scripts/` 查找脚本。
- 本次把 Scripts/*.py 共 11 个（含新写的 4 个）全部复制到该目录，按钮命令才可用。
- **以后新增/修改脚本：源文件放仓库 `Scripts/`，分发复制到 Rhino `8.0/Scripts/`。**

### 教训 / 备忘
- 覆盖层合并的锚点替换容易误删原始按钮——用**精确锚点**（含相邻按钮完整文本）并核对
  合并后按钮总数（14+4=18，且 selectFilter 必须还在）。
- 用户手动加的图标在覆盖层是 Rhino 标准格式（svg_name + light_svg），照搬即可；
  Mac 能否渲染待用户重启验证（若显示文字再转 png 方案）。
- 改 rui 前必须完全退出 Rhino；从运行中会话提取修改必须等覆盖层生成。
