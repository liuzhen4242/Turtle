---
name: rhino-material-creator
description: 通过一张贴图图片创建 Rhino 8 材质（.rmtl 贴图材质），放入材质库 `~/Library/Application Support/McNeel/Rhinoceros/8.0/Render Content/en_US/Turtle/` 与仓库 `Resources/Materials/`（含 `assets/materials/` 镜像），并配合现有 rhino-material-button 技能生成 32x32 图标、登记到 material-turtle 工具列。当用户提供图片/贴图（如 en_US/Textures 或 Resources/Materials/img/ 下的 jpg/png），要求"把这个图做成 Rhino 材质""创建材质""材质库里加一个贴图材质"时使用。产出：<名称>.rmtl（内嵌贴图、zlib+base64）+ 材质库分发 + 图标 + rui 按钮 + 同步。
---

# Rhino Material Creator —— 图片 → 贴图材质

把一张贴图图片做成 Rhino 8 的 rmtl 贴图材质（自包含：贴图内嵌在 rmtl 内），并分发到材质库与仓库。

## 核心守则（动手前必读）

1. **改 rui / 写 McNeel 目录前必须完全退出 Rhino**。Rhino 退出时会用自身状态覆盖 rui；写 `Render Content` 目录前确认 Rhino 未运行（`pgrep -x Rhinoceros`）。
2. **贴图材质 rmtl 必须自包含**：贴图以 `zlib+base64` 内嵌在 rmtl 的 `<embedded-files>` 段。**不要用绝对路径引用**（历史教训：旧材质 filename 钉死 `D:\00-素材\Temple-模版\...`，Mac 上找不到 → 每次打开 3dm 都解包出 `*_embedded_files` 文件夹）。filename 一律用相对文件名。
3. **贴图源统一放 `~/Library/Application Support/McNeel/Rhinoceros/8.0/Render Content/en_US/Textures/`**（Rhino 用户级贴图库，已含 36 张 Turtle 贴图 + 内置贴图）。放仓库的镜像在 `Resources/Materials/img/`。
4. **图标规范**：32x32 PNG 缩略图 base64，rui 内嵌 `<png>`，禁止 `<svg_name>` 外部引用；图标 guid 与 macro_item 的 `bitmap_id` 一致。
5. **材质名 = rmtl 文件名**（不带扩展名）；工具列宏 `_-Materials\no\ni\n<材质名>\nEnterEnd`（注意 `i` 不是 `ni`）。

## Step 1：确认图片来源

- 已有贴图：`en_US/Textures/<图片>.jpg`（优先）或仓库 `Resources/Materials/img/<图片>.jpg`；
- 新贴图：先复制到上述两个位置之一再生成材质（保持"贴图源"单一约定）。

## Step 2：生成 rmtl

按 `rhino-material-button` 技能 Step 1 的内联 Python 代码执行（以 `Resources/Materials/co-concrate1.rmtl` 为模板）：读取图片 → zlib 压缩 → base64 → 替换 `<embedded-files>` 的 `<file>` 块；`filename` 参数改为相对文件名；`instance-name` 改为材质名；删除旧 `<thumbnail>` 段。

输出到：`en_US/Turtle/<名称>.rmtl`、仓库 `Resources/Materials/<名称>.rmtl`、`assets/materials/<名称>.rmtl`（Windows 输出到 `D:\00-素材\SoftTemple\Rhino\Turtle\Resources\Materials\` 与对应 Rhino 材质位）。

校验：`python3 -c "import xml.etree.ElementTree as ET; ET.parse('<输出>.rmtl'); print('OK')"`。

**纯色材质**（无贴图）：参照 `Resources/Materials/earth.rmtl`，不需要脚本，直接复制改 diffuse 颜色；图标用纯色 32x32 PNG。

## Step 3：生成图标（贴图缩略 32x32）

```bash
sips -z 32 32 "<图片路径>" --out /tmp/<名称>_icon.png && base64 < /tmp/<名称>_icon.png
```

## Step 4：登记 material-turtle 工具列

使用现有 `rhino-material-button` 技能（`/Users/zhenliu/study/coding/rhinoPluging/Resources/Skill/rhino-material-button/SKILL.md`）完成：
- 按钮三节点：`<tool_bar_item>` + `<macro_item bitmap_id=图标guid>` + `<icon>`（guid 用 `uuid.uuid4()` 全新生成）；
- 锚点 = material-turtle 最后一个按钮；
- 插入后 XML 校验，确认按钮数 +1（当前 34 个）。

## Step 5：同步与固化

```bash
python3 "<仓库>/Resources/Skill/rhino-turtle-sync/scripts/sync_resources.py"   # rui+材质+脚本+模板双向
```
git 固化由用户手动执行（`git add -A && git commit -m ... && git push origin main`）。

## 已知可复用事实

- material-turtle 工具列 guid：`3cdefd34-e8e5-4786-96d6-c0ee05e6467a`，当前 34 个按钮：w-wood1~3、gr-grass1~6、co-concrate1~4、m-aluminum、b-blacktop、bo-board1~4、br-brick1~4、r-roofing1~3、t-tile1~4、x-line12、x-line8、earth、stoneConcrete。
- 贴图材质 rmtl 模板：`Resources/Materials/co-concrate1.rmtl`（含 embedded-files 内嵌贴图）；纯色模板：`earth.rmtl`。
- 材质库三处：Mac `~/Library/Application Support/McNeel/Rhinoceros/8.0/Render Content/en_US/Turtle/`、仓库 `Resources/Materials/`、`assets/materials/`（分发镜像，rmtl+img 都要）。
- 贴图源：`en_US/Textures/`（36 张 Turtle 贴图已在此，2026-10-01 复制自 `Rhinoceros/Template Files/Turtle_embedded_files/`）；仓库镜像 `Resources/Materials/img/`。
- **历史坑**：旧材质 filename 指向 `D:\00-素材\Temple-模版\Rhino\Temple\2025-01-08-OpenLink_embedded_files\*.jpg`（Windows 遗留路径），Mac 上不可达 → Rhino 把 3dm 内嵌贴图解包出 `*_embedded_files`。修复方向：用本技能重新生成 rmtl（filename 改相对名）+ 贴图放 en_US/Textures + 加入 Rhino 搜索路径。
- 配合技能：rhino-material-button（图标+rui 按钮）、rhino-toolbar-rui（图标/覆盖层/同步）、rhino-turtle-sync（固化总流程）。
