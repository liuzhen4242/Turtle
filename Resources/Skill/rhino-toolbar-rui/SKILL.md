---
name: rhino-toolbar-rui
description: Rhino 8 插件工具栏（.rui 文件）图标的创建、修复与跨平台（Mac/Win）同步流程。当需要给 Rhino 工具栏按钮添加图标、按钮图标显示为默认蓝色或文字、修改 rui 后 Mac 上不生效、工具栏 dock 位置丢失/找不到、或需要把 rui 同步到 yak packages 加载位时使用。适用于 Turtle 等自研 Rhino 插件的工具栏开发与排障。
---

# Rhino Toolbar RUI 图标与同步

## 核心守则（动手前必读）

1. **改 rui 前必须完全退出 Rhino**。Rhino 退出时会用自身状态覆盖 rui；进程名是 `Rhinoceros`（不是 "Rhino 8"），用 `kill <pid>` / `kill -9 <pid>` 强杀（macOS 上 pkill 常受系统限制不可用）。先确认用户没有正在使用 Rhino。
2. **真正加载位是 yak 的 packages 目录（Mac/Win 都如此）**：
   - Mac：`~/Library/Application Support/McNeel/Rhinoceros/packages/8.0/turtle/{ver}/Turtle.rui`（小写）
   - Windows：`%APPDATA%\McNeel\Rhinoceros\packages\8.0\Turtle\{ver}\Turtle.rui`（大写）
   - 改 UI / MacPlugIns 目录的 rui，Rhino 根本不读——这是"改了很久没效果"的头号原因。
   - **Windows 上 `8.0\UI\Turtle.rui` 目录不存在**（旧 skill 说法有误，勿再按它找）。
3. 改完 rui 必须**同步 5 处**并校验 md5 一致（见"一键同步脚本"）。

## rui 的 5 个位置（Mac）

```text
1. ~/Library/Application Support/McNeel/Rhinoceros/8.0/UI/Turtle.rui
2. ~/Library/Application Support/McNeel/Rhinoceros/8.0/MacPlugIns/Turtle.rhp/Turtle.rui
3. ~/Library/Application Support/McNeel/Rhinoceros/MacPlugIns/Turtle.rhp/Turtle.rui
4. <rhinoPluging仓库>/Resources/Turtle.rui            （git 源）
5. ~/Library/Application Support/McNeel/Rhinoceros/packages/8.0/turtle/1.0.0/Turtle.rui   ← 真正加载位！
```

Windows 上加载位同样只有 packages 一份（`%APPDATA%\McNeel\Rhinoceros\packages\8.0\Turtle\{ver}\Turtle.rui`），改动直接生效（前提：Rhino 已完全退出）。

## 图标格式规范（Mac Rhino）

**可渲染**（二选一）：

```xml
<!-- 单张 32x32 PNG，name = "guid.png"（推荐，参考 color-turtle 白圆 837c614b） -->
<icon guid="837c614b-c763-41b8-98d4-dda7ffd07f3c" name="837c614b-c763-41b8-98d4-dda7ffd07f3c.png">
  <png>iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0…</png>
</icon>

<!-- material-co 风格：name 以 .svg 结尾但无 light/svg，3 张 png（16/24/32） -->
<icon guid="e8e6c9d1-…" name="be6272d0-….svg">
  <png>16x16</png><png>24x24</png><png>32x32</png>
</icon>
```

**不可渲染（Mac）**：Windows 风格 `<light><svg><rect/>…` —— Mac 上按钮显示文字。
**不可渲染（Windows）**：`<svg_name>` + `<light_svg>` 非标准结构 —— Windows 上按钮图标丢失/空白（2026-09-28 turtleMain 实证）。

## SVG 图标标准结构（Windows Rhino 8，2026-09-28 实证）

Rhino 8 标准 SVG 图标 = 内嵌数据，**不依赖外部文件**：

```xml
<icon guid="8ae148f0-…" name="085a64d7-….svg">
  <light>
    <svg width="22" height="17" viewBox="0 0 22 17" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="…"/>
    </svg>
  </light>
</icon>
```

**规则**：
1. **禁止 `<svg_name>`**（外部 SVG 文件引用）。它依赖外部文件存在且路径可寻——Windows 上缺失即图标丢失，跨平台（Mac/Win）必然踩坑。**一切图标用 rui 内嵌数据**：`<png>base64</png>` 或 `<light><svg>…</svg></light>`。
2. **把旧结构 `<svg_name>xxx.svg</svg_name><light_svg>&lt;svg…&gt;&lt;/svg&gt;</light_svg>` 改成标准结构**：用 XML ElementTree 重建——解析 `light_svg` 文本（ET 已自动反转义为 `<svg>` 标记）→ `ET.fromstring()` 成元素 → 建 `<light>` 子节点挂入 → 删 `svg_name`/`light_svg`。ET 写回时 SVG 带命名空间会变成 `<ns0:svg>`（根已有 `xmlns:ns0="http://www.w3.org/2000/svg"` 声明），**Windows Rhino 8 可正常渲染**（exportToSu 单测→批量 17 个全通过）。
   - 不要用字符串替换改 rui（易把 `<` 写成 `&lt;` 文本而非元素）。
   - 生成脚本参考：`fix_icon_test2.py` / `fix_icons_batch.py`（Windows workspace 根）。
3. 同一份 rui 内嵌 SVG/PNG → **Mac/Win 渲染行为可能不同**（Mac 上 `<light><svg>` 显示文字、PNG 可渲染），所以**跨平台首选 `<png>base64</png>`**；若坚持 SVG，Windows 用 `<light><svg>`、Mac 需另测。
4. 图标 guid 必须与 `macro_item` 的 `bitmap_id` 一致，`name` 建议用 `guid.png` 或 `guid.svg`。
5. 工具栏按钮的宏定义在 `<macros><macro_item bitmap_id="图标guid">`，图标定义在 `<icons><icon guid="同guid">`——两者用 guid 关联。

## 真实贴图图标方案（material-turtle）

**背景**：从其它工具列复制按钮时，即使 32 个图标 guid 全新建，若源图的 PNG 内容本就是同一张图（如 material-ma 的 32 个"木"字 logo 全部同 md5），结果仍是"所有按钮图标一样"。**根因是源图无区分度，不是共享/继承 bug**。

**解决**：每个材质按钮用其**真实材质贴图**的 32x32 缩略图作为图标。

关键路径与事实：
- 材质贴图实际存放（Mac）：`~/Library/Application Support/McNeel/Rhinoceros/Template Files/OpenLink2.0_embedded_files/`——Rhino 从 3dm 模板解包的 embedded files。rmtl 里 `bitmap-texture` 引用的是 Windows 绝对路径（`D:\…`、`\\l\…`），Mac 上不可用，**取图一律用解包目录**。
- 32 个 material-ma 材质与其贴图一一对应（Blacktop New.jpg / Wood_Floor*.jpg / Grass Dark&Light Green.jpg / Beadboard.jpg / Brick_*.jpg / Roofing_*.jpg / Tile_*.jpg / Sand.png 等）。
- 生成步骤（PIL）：
  1. 打开贴图 → `resize((32,32), Image.LANCZOS)` → 存 RGB PNG → base64
  2. right 图标 = left 向白混合 55%（`Image.blend(img, white, 0.55)`）作亮化版
  3. 同类多序号（grass×6 / brick×4 / tile×4…）用同一贴图 + `ImageEnhance.Brightness/Color` 微调区分
  4. 缺贴图的材质（贴图在 Windows 项目目录）→ 用同类相近贴图替代（如 gr-grass5/6 → Grass Light/Dark Green ±亮度）
- 替换进 rui：按 `macro_item` 的 `bitmap_id` 定位 `<icon guid="ID" name="ID.png">…<png>旧</png>…</icon>` 块，文本替换 `<png>…</png>`；left = 原图，right = 亮化版。
- 校验：64 个 icon 的 md5 **应全部唯一**；XML 校验；再同步 5 处。
- 产物事实：material-turtle = guid `3cdefd34-e8e5-4786-96d6-c0ee05e6467a`，32 按钮；生成脚本 `/tmp/gen_material_turtle.py`，图标数据 `/tmp/mt_real_icons.json`。

## 颜色宏规范（color-turtle）

颜色按钮宏格式：`_-Properties O C O\nR,G,B[,A]\nEnter\nEnter\n_SelNone`

规则：
- **非透明材质只给 RGB（3 个值）**——不带 alpha。写成 `,100` / `,0` 都是错的，会污染透明度。
- **透明材质才给 4 个值 `R,G,B,A`**——Turtle 系列统一 alpha=`120`。
- 判定标准与材质文件 `Color_{R}_{G}_{B}_A{A}.rmtl` 对应：`A0` → 宏写 RGB；`A120` → 宏写 `RGB,120`。

color-turtle（guid `c479780d-9ee4-4ab2-8d20-a7a37a356c74`）31 按钮：索引 00–23 非透明（去 alpha），24–30 透明（alpha=120）。

## 排查流程（图标显示为蓝色/文字时）

按顺序排查，每步都有明确结论：

1. **确认 Rhino 实际加载的 rui**：对 5 处 rui 跑 md5。若 packages 位与其余不一致 → 它是旧版 → 用新版覆盖（先备份 `.bak-yakold`）。
   - 蓝色 = `bitmap_id` 悬空（图标 guid 在 rui 里不存在）
   - 文字 = 图标 guid 存在但 icon 不被加载（最常见：Rhino 读的是另一份 rui；其次：格式不被渲染）
2. **决定性测试**：把一个已知能渲染的 icon（如 color-turtle 白圆 837c614b）逐字复制、只换 guid 放进目标按钮。若仍不显示 → 不是图标数据问题，是加载文件/机制层问题。
3. **检查覆盖层**：`~/Library/Application Support/McNeel/Rhinoceros/8.0/settings/Scheme__Default/OpenLink_7338352c-….xml`（guid 7338352c=Turtle 库）内含旧图标 `light_svg` override 与工具栏布局修改，启动时覆盖新 rui → 症状"重启又变旧"。删除它 → 图标恢复读 rui，但工具栏 dock 可能重置。
4. **检查 dock**：工具栏浮动位置在 `settings/Scheme__Default/containers.xml`（`dock_bar` 的 `dock_location`/`float_point`/`visible`）。删覆盖层后会出现"Window 里勾选可见但找不到面板"。
5. **Windows 覆盖层闪崩（2026-09-28 实证）**：`%APPDATA%\McNeel\Rhinoceros\8.0\settings\Scheme__Default\` 下残留旧版 Turtle 覆盖层 `Turtle_7338352c-….xml`（内含**已被 Mac 重做换掉的旧按钮 guid** 引用，如 `609e6fcc…`），而新版 rui 库 guid 仍为 `7338352c-119d-4898-aee3-911514067977` → 导入/加载工具列时 Rhino 合并覆盖层遇到不存在的按钮引用 → **闪崩**。处理：备份到 `Resources\.bak-scheme-*` 后删除覆盖层（Mac/Win 同法）。
6. **Windows turtleMain 图标全丢（2026-09-28 已修复）**：18 个 icon 全为非标准 `<svg_name>+<light_svg>`（无 `<png>`）→ Windows 不渲染。已全部重建为标准 `<light><svg>`（见上"SVG 图标标准结构"）。**教训：新做工具列时图标一律内嵌 `<png>` 或标准 `<light><svg>`，禁止 `<svg_name>` 外部引用。**

## 双端取最新合并流程（2026-10-15 实证）

**场景**：Win 与 Mac 两边的 Turtle 工具列都有各自独有修改，需要"以最新为准"合并进仓库 rui，让两端都有。

**Win 侧独有内容的唯一来源是覆盖层**：`%APPDATA%\McNeel\Rhinoceros\8.0\settings\Scheme__Default\Turtle_7338352c-….xml`（Mac 端对应 `OpenLink_7338352c-….xml`）。用户在当前机器 Rhino 里手动追加的按钮只存在覆盖层里，仓库 rui 没有。**若不同步覆盖层→仓库，重启或加载位覆盖后这些独有按钮就丢了。**

**合并步骤**（仓库 `Resources/Turtle.rui` 为唯一权威，major_ver=5）：
1. 备份仓库 rui 为 `.bak-merge-<时间戳>`（写仓库目录需 require_escalated）
2. 读覆盖层全文，找出用户新增的宏与图标：覆盖层里是 `<macro guid=… bitmap_guid=…>`（非仓库的 `<macro_item bitmap_id=…>`）+ `<icon guid=…><light_svg>…</light_svg>`（转义文本）
3. 判断是全新工具列还是既有工具列追加按钮：
   - 全新工具列 → 整体搬运 tool_bar + 全部宏/图标
   - **既有工具列追加**（最常见，如 mouseTurtle）→ 只把新增的 macro_item + icon 加进仓库，并在对应工具列 `<tool_bar guid=…>` 末尾追加 `tool_bar_item`（`<left_macro_id>`/`<right_macro_id>` 引用宏 guid）
4. 宏转标准：仓库宏格式 `<macro_item guid="…" bitmap_id="…"><text><locale_1033>…</locale_1033></text><tooltip>…</tooltip><button_text>…</button_text><script>! _命令</script></macro_item>`
5. 图标转标准：见下"覆盖层 light_svg → 标准 light/ns0 转换"
6. 插入位置：仓库 rui 的 `<macros>` 末尾（`</macros>` 前）、`<icons>` 末尾（`</icons>` 前）、工具列 `<tool_bar>` 末尾（最后一个 `tool_bar_item` 之后）
7. 校验：`ET.parse` 合法、新 guid 出现次数符合预期（宏 guid=2 处、icon guid=3~4 处含 name 引用）、XML 结构完整
8. 同步加载位（Mac/Win 各自 packages，md5 一致）→ git add/commit/push

**关键判断：bitmap 引用 Rhino 内置图标是正常现象**。仓库 rui 里有 16 个 `macro_item` 的 `bitmap_id` 无对应 `<icon>` 定义（03190633/04ba084f/2e271e15/2fc898a9… 等），这些是引用 Rhino 内置图标（如 `2e271e15`=Cage），Rhino 自动解析，**无需新增 icon，不算悬空 bitmap**。只有非内置的新图标才需要加 `<icon>` 定义。

### 覆盖层 light_svg → 标准 light/ns0 转换（2026-10-15 实证）

覆盖层图标是 `<icon guid=…><light_svg>&lt;svg…&gt;&lt;/svg&gt;</light_svg></icon>`（转义文本）。转成仓库标准 `<icon guid="…" name="…svg"><light><ns0:svg …>…</ns0:svg></light></icon>`：

```python
import re, xml.etree.ElementTree as ET
SVG_NS = "http://www.w3.org/2000/svg"

def extract_light_svg(overlay_text, guid):
    m = re.search(r'<icon guid="' + re.escape(guid) + r'".*?</icon>', overlay_text, re.S)
    lm = re.search(r"<light_svg>(.*?)</light_svg>", m.group(0), re.S)
    txt = lm.group(1)
    # 反转义（&lt; &gt; &amp; &quot; &apos; &#10; &#13;）
    txt = txt.replace("&#10;", "\n").replace("&#13;", "\r")
    txt = txt.replace("&lt;", "<").replace("&gt;", ">")
    txt = txt.replace("&quot;", '"').replace("&apos;", "'").replace("&amp;", "&")
    return txt

def ns0fy(el):
    if isinstance(el.tag, str) and el.tag.startswith("{" + SVG_NS + "}"):
        el.tag = "ns0:" + el.tag[len(SVG_NS)+2:]
    for c in el:
        ns0fy(c)

root = ET.fromstring(extract_light_svg(overlay, "a89cccd5-…"))
ns0fy(root)
root.set("xmlns:ns0", SVG_NS)          # 手动加声明！嵌入 <light> 后不会自动补
svg_xml = ET.tostring(root, encoding="unicode")   # 输出 <ns0:svg ...>
```

**⚠️ 坑（2026-10-15 实证）**：`ET.register_namespace("ns0", SVG_NS)` 会报 `ValueError: Prefix format reserved for internal use`——`ns0` 是 Python 保留前缀。**不要调用 register_namespace**，因为 ns0fy 已经把元素 tag 改成了字面量 `ns0:` 前缀，`ET.tostring` 序列化时自动保留字面量前缀，无需注册。同时**必须给根 svg 手动 `root.set("xmlns:ns0", SVG_NS)`**，否则嵌入 `<light>` 后序列化不带命名空间声明，Rhino 解析报错。

## 一键同步脚本

```bash
# 把源 rui 同步到 5 处（含 packages 加载位），并做 XML + md5 校验
python3 scripts/rui_sync.py <源Turtle.rui路径>
# 只校验不同步
python3 scripts/rui_sync.py <源Turtle.rui路径> --verify-only
```

脚本先备份每个目标为 `.bak-sync-<时间戳>`，再复制、校验 XML 合法性、输出 5 处 md5。Windows 上目标列表不同，脚本需按平台调整（见脚本内注释）。

## GUI 验证流程（Mac）

- 命令行 `_-Toolbar`：库名必须输 **Turtle**（输 color-material-turtle 会报 not found）→ Show → color-material-turtle → Yes；或 Window → Containers 勾选。
- AX 操作注意：菜单卡住（AXCancel）用多次 esc 或点击其它菜单项切换；元素索引每次观察后重排，不可跨观察复用；屏幕锁定时报 MAC_GUI_ERROR_7_0，等解锁再操作。
- 插件加载日志：`~/.config/Turtle/onload.log`（确认插件 OnLoad 与"Mac 跳过 ToolbarFiles API"）。

## 删除旧工具列后「Toolbars 面板空白/工具栏不显示」的根因（2026-09-27 验证）

**症状**：脚本从 rui 删除旧工具列（tool_bar + tool_bar_reference + 孤儿宏/图标）后，重启 Rhino，Toolbars 面板空白/变灰，但库本身加载正常（`_-Toolbar` → Library → List 能看到 4 个工具列名）。

**根因（三层）**：
1. **rui 的 `tool_bar_groups` 残留**：删除脚本只清了 `tool_bars`/`tool_bar_reference`，但 `tool_bar_groups` 里还留着 4 个**无 `tool_bar_reference` 的空 `<item>`**（引用已删工具列的位置），且新工具列**从未在组中** → 重启后默认不显示。
2. **覆盖层残留旧引用**：`settings/Scheme__Default/Turtle_7338352c-….xml` 被 Rhino 重写后仍引用已删工具列（`<tool_bar source_guid=…modified="True">`、deleted_items、已删宏的 right_macro）→ 删覆盖层（备份后）可消除，图标恢复读 rui，dock 可能重置。
3. **containers.xml 残留旧 dock_bar**：已删工具列的 dock_bar 浮动记录仍在 → 清理引用已删 guid 的 dock_bar 块（备份后）。

**修复（按序）**：备份 → 删覆盖层 → 清理 containers.xml 旧 dock_bar → **重写 rui 的 tool_bar_groups**：清空残留 `<item>`，4 个工具列全部写 `<tool_bar_reference guid="…"><dock_bar_info visible="1" dock_location="top"/></tool_bar_reference>` → 同步 5 处 → 重启验证。

**GUI 验证/恢复显示（已验证可用）**：
- `_-Toolbar` → 选 Library → 输入 `Turtle` → List（确认库加载路径 packages/8.0/turtle/1.0.0/Turtle.rui 且 4 工具列名齐全）→ Toolbar → Show → 输入工具列名 → Yes。
- **坑**：在「Choose toolbar option:」对话框里直接输入+回车会把文字送进命令行报 `Unknown command`；正确顺序：set_value 填入 → 点 Show 按钮 → 对话框变「Toolbar name:」→ 再 set_value 填入 + 回车 → 出现「Show toolbar "xxx"?」→ 点 Yes。
- Show 后状态**持久化在 containers.xml**（每个工具列一个 `<dock_bar><tabs selected_item=工具列guid><tool_bar guid=… file=库guid/></tabs>` 块，`visible="True"`），重启后保持；**Show 操作不会重新生成覆盖层**。检查 containers.xml 是否含 4 个工具列 dock_bar 即可确认持久化。
- 库名必须输 `Turtle`（输 color-material-turtle 会 not found）。

## 已知可复用的事实

- color-turtle 能渲染的白圆：guid `837c614b-c763-41b8-98d4-dda7ffd07f3c`，单张 32x32 PNG（base64 624 字符，头 `iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0`）。
- color-material-turtle 31 色映射：索引 0–30，24–30 为 A120 半透明 + 黑描边。
- **turtleMain（guid `55f2b50c-4258-4c1b-9bba-133cd6b0f251`，18 按钮）图标 guid**（2026-09-28 已全部重建为 `<light><svg>`）：085a64d7(exportToSu)、44d0f4e8(visWatch)、6b6047cb(batchCapture)、d366577d(cameraMove)、a6a2748a(outline)、db370ed7(whiteLine)、932f3250(blackLine)、cdd2c994(originalColor)、d3f790ae(dropToGround)、b9f49354(intersect)、4c4d52a5(lineSplit)、625988a0(mapping)、76d4dfac(colorToMat)、148f3971(moveLayer)、2e986a61(selectFilter)、c502c50c(alignPage)、b33e09ce(lineWidthScale)、ec35e7f9(surToHatch)。
- 7 个工具栏 guid 见 `Resources/Turtle.rui` `<tool_bars>` 节；color-material-turtle = `97eb5b7a-db48-4cf8-abe0-c06216ace898`；color-turtle = `c479780d-9ee4-4ab2-8d20-a7a37a356c74`；material-ma = `bdffc206-d14b-4148-b797-c342c98591e5`；material-turtle = `3cdefd34-e8e5-4786-96d6-c0ee05e6467a`（32 按钮、64 宏+图标全新建、图标为真实贴图缩略）；mouseTurtle = `0809495b-bb53-4007-82e5-a2a92c27003d`。
- **mouseTurtle 新增的 4 个变形/软编辑宏（2026-10-15 从 Win 覆盖层合并）**：
  - `52de8b18-d30a-463a-8933-ff8aa909e82b` → `! _Cage`，bitmap `2e271e15`（**引用 Rhino 内置 Cage 图标，无 icon 定义，正常**）
  - `86457227-6f7e-4eeb-87bf-c297abcfdcec` → `! _CageEdit`，bitmap `24ac3c20-cecc-4dfc-9ba9-3af71a049257`（新增 icon）
  - `40f5d7fa-3db3-41fb-b965-9fdfdd360786` → `! _SoftEditCrv`，bitmap `a89cccd5-1a9f-4c72-bf17-cf3569a448e4`（新增 icon）
  - `29dac961-3ddb-4178-8768-06aa1ecc4f66` → `! _SoftEditSrf`，bitmap `a89cccd5-1a9f-4c72-bf17-cf3569a448e4`（新增 icon）
  - 追加的 2 个按钮：`49826fe0-dbfe-45a0-92ca-a612dc93bcb1`（left=CageEdit right=Cage）、`6008e4bc-b0a3-4765-badc-f9ca09b36b65`（left=SoftEditCrv right=SoftEditSrf）
  - 合并后仓库 rui 4547 行，md5（Win）`4E4C4584F3E97BEE2358204C63723E5D`；合并脚本 `merge_win_toolbar.py`
