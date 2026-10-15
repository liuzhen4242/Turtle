---
name: rhino-toolbar-rui
description: Rhino 8 自研插件（Turtle）工具栏 .rui 的图标创建/修复、跨平台（Mac/Win）同步与排障。当按钮图标显示为默认蓝色/文字、改 rui 后不生效、工具栏 dock 丢失、双端工具栏不一致，或需要把覆盖层独有按钮固化进 rui 时使用。
---

# Rhino Toolbar RUI 图标与同步

## 核心守则（动手前必读）

1. **改 rui 前必须完全退出 Rhino**（进程名 `Rhinoceros`；macOS 用 `kill <pid>`，pkill 常受限）。Rhino 退出时会用自身状态覆盖 rui。
2. **真正加载位是 yak packages 目录（Mac/Win 都如此）**，改别处的 rui 不生效：
   - Mac：`~/Library/Application Support/McNeel/Rhinoceros/packages/8.0/turtle/{ver}/Turtle.rui`（小写 turtle）
   - Win：`%APPDATA%\McNeel\Rhinoceros\packages\8.0\Turtle\{ver}\Turtle.rui`（大写 Turtle）
   - **Win 上 `8.0\UI\Turtle.rui` 目录不存在**；Mac 的 UI/MacPlugIns 目录 Rhino 也不读。
3. 改完必须**同步全部加载位并校验 md5 一致**（见"同步脚本"）。
4. **版本治理：只维护 1.1.0，1.0 已废弃**（2026-10-15 双端 packages 已删 1.0）。勿再碰 1.0。

## 图标格式（跨平台）

**首选 `<png>base64</png>`**（单张 32x32 PNG，`name="guid.png"`）——Mac/Win 都渲染，最稳：
```xml
<icon guid="837c614b-…" name="837c614b-….png"><png>iVBOR…</png></icon>
```
或用标准 `<light><svg>…</svg></light>`（Win 渲染；**Mac 上显示文字**，需另测）。

**规则**：
- **禁止 `<svg_name>`（外部 SVG 文件引用）**：Win 不渲染，跨平台会因文件缺失丢图标。图标一律 rui 内嵌数据。
- icon 的 `guid` 必须 = `macro_item` 的 `bitmap_id`；`name` 用 `guid.png`/`guid.svg`。
- 工具栏按钮宏在 `<macros><macro_item bitmap_id="图标guid">`，图标在 `<icons><icon guid="同guid">`，两者用 guid 关联。
- **Mac 覆盖层图标是 `<svg_name>+<light_svg>` 非标准结构**，固化进仓库时必须转成 `<png>` 或 `<light><ns0:svg>`。

**SVG→PNG（macOS 免装库）**：`qlmanage -t -s 32 -o <目录> icon.svg` → 生成 `icon.svg.png` → base64。

## 颜色宏规范（color-turtle）

宏格式：`_-Properties O C O\nR,G,B[,A]\nEnter\nEnter\n_SelNone`
- **非透明材质只给 3 个值 RGB**（不带 alpha）。
- **透明材质才给 4 个值 `R,G,B,A`**（Turtle 统一 alpha=120）。
- 判定：材质文件 `Color_{R}_{G}_{B}_A{A}.rmtl` → `A0` 写 RGB、`A120` 写 `RGB,120`。

## 排障速查

| 症状 | 根因 / 处理 |
|---|---|
| 图标显示**蓝色** | `bitmap_id` 悬空（icon guid 在 rui 里不存在） |
| 图标显示**文字/空白** | icon 存在但未被加载：最常见是 Rhino 读的是另一份 rui（packages 位与其它处 md5 不一致 → 覆盖）；其次格式不被渲染 |
| **重启又变旧** | 覆盖层 `settings/Scheme__Default/Turtle_7338352c-….xml` 含旧图标 override，启动覆盖新 rui → 备份后删除覆盖层（dock 可能重置） |
| 工具列**不显示/面板空白** | 三层：rui `tool_bar_groups` 残留空 `<item>` + 覆盖层残留旧引用 + `containers.xml` 残留旧 dock_bar → 备份后清理，重写 `tool_bar_groups` 为各工具列 `<tool_bar_reference>` |
| **"Error loading Turtle.rhp"** 弹窗 | `packages\8.0\` 下残留 `Turtle.bak-*` 旧版备份目录（含旧 rhp）被包扫描器当作包加载 → **移出 packages**（移到仓库 `Resources\.bak-*`），勿留在 packages |
| 按钮**右键功能丢失** | 右宏从未固化进 rui（如 cameraMove 历史上只有 `left_macro_id`），Win 覆盖层也不含。**Win 从无此功能，非合并丢失**。右键跨平台需从 Mac 覆盖层提取固化 |

**决定性测试**：把一个已知能渲染的 icon（如 color-turtle 白圆 `837c614b`）逐字复制、只换 guid 放进目标按钮。若仍不显示 → 不是图标数据问题，是加载文件/机制层问题。

## 双端取最新合并（覆盖层 → 仓库 rui）

**核心**：用户在 Rhino UI 手动加的按钮**只写在覆盖层** `Scheme__Default/Turtle_7338352c-….xml`（各机独立），**不写加载位 rui、不随 git 分发** → 这是"Mac 有、Win 没有"（或反之）的根因。**需固化进仓库 rui 才能跨平台同步。**

**步骤**（仓库 `Resources/Turtle.rui` 为唯一权威）：
1. 备份仓库 rui 为 `.bak-merge-<时间戳>`。
2. 比对加载位 rui 与覆盖层 `tool_bar_items`，找出覆盖层**新增/独有** item（`<tool_bar source_guid=… modified="True">` 下无 `source_guid=` 的 item）。
3. 格式转换：
   - 按钮：覆盖层 `<tool_bar_item guid="X"><left_macro guid="A"/><right_macro guid="B"/>` → 仓库 `<tool_bar_item guid="X"><left_macro_id>A</left_macro_id><right_macro_id>B</right_macro_id>`
   - 宏：覆盖层 `<macro guid="A" bitmap_guid="I">` → 仓库 `<macro_item guid="A" bitmap_id="I"><text><locale_1033>名</locale_1033></text><script>宏</script>`
   - 图标：`<svg_name>+<light_svg>` → `<png>base64</png>` 或 `<light><ns0:svg>`
4. 插入位置：工具列 `<tool_bar>` 末尾（最后一个 `tool_bar_item` 后）+ `<macros>` 末尾 + `<icons>` 末尾。
5. 校验 XML + 同步加载位（md5 一致）+ git add/commit/push。

**注意**：bitmap 引用 **Rhino 内置图标**（如 `2e271e15`=Cage）时**无 icon 定义是正常的**，Rhino 自动解析，不要误加 icon。只有非内置新图标才需加 `<icon>`。

**ns0 坑**：`ET.register_namespace("ns0", …)` 会报 `ValueError: Prefix format reserved`（ns0 是保留前缀）。手动把元素 tag 改字面量 `ns0:` 前缀即可（ET.tostring 自动保留字面量前缀），且**必须给根 svg 手动 `root.set("xmlns:ns0", SVG_NS)`**。

## 同步脚本

```bash
python3 scripts/rui_sync.py <源Turtle.rui路径> [--verify-only]
```
备份每个目标为 `.bak-sync-<时间戳>` 后复制、校验 XML + 输出各位置 md5。**注意：workspace 里的 rui_sync.py 是旧版（Mac 单平台/认 1.0.0）；权威版在仓库 git。**

## 已知可复用事实

- 库 guid `7338352c-119d-4898-aee3-911514067977`；5 个工具列 guid：
  - turtleMain `55f2b50c-4258-4c1b-9bba-133cd6b0f251`（22 按钮）
  - color-turtle `c479780d-9ee4-4ab2-8d20-a7a37a356c74`（31 按钮）
  - color-material-turtle `97eb5b7a-db48-4cf8-abe0-c06216ace898`
  - material-turtle `3cdefd34-e8e5-4786-96d6-c0ee05e6467a`（32 按钮，图标=真实材质贴图缩略图）
  - mouseTurtle `0809495b-bb53-4007-82e5-a2a92c27003d`
- color-turtle 可渲染白圆：guid `837c614b-…`，单张 32x32 PNG（base64 头 `iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0`）。
- **右键排查**：某按钮是否曾有右键 → 看其 `tool_bar_item` 是否含 `<right_macro_id>`（只含 `left_macro_id` = 无右键）。
- 插件加载日志：Mac `~/.config/Turtle/onload.log`。
