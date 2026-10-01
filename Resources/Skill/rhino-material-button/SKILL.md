---
name: rhino-material-button
description: Rhino 8 Turtle 插件"把一张贴图 jpg / 一个 rmtl 材质做成工具列按钮"的全流程。当用户提供一张贴图（如 Resources/Materials/img/*.jpg）或材质文件，要求把它做成 material-turtle 等工具列上的按钮、图标用该贴图缩略图时使用。产出：生成 rmtl 贴图材质 + 32x32 图标 base64 + 插入 rui（macro/icon/tool_bar_item）+ 分发材质 + 同步 rui 到全部加载位 + git 固化。
---

# Rhino Material → Toolbar Button

把一张贴图或一个材质，做成 Turtle 工具列（默认 material-turtle）上的独立按钮，图标用该贴图的 32x32 缩略图。

## 核心守则（动手前必读）

1. **改 rui 前必须完全退出 Rhino**。Rhino 退出时会用自身状态覆盖 rui；先确认用户没有在用 Rhino。
2. **图标一律 rui 内嵌 `<png>base64</png>`**，禁止 `<svg_name>` 外部引用（跨平台丢失）。图标 guid 必须与 `macro_item` 的 `bitmap_id` 一致。
3. **按钮三节点**（缺一不可，用 guid 关联）：
   - `<tool_bar_item guid><left_macro_id>宏guid</left_macro_id></tool_bar_item>`
   - `<macro_item guid bitmap_id="图标guid"><text><locale_1033>名称</locale_1033></text><script>_-Materials\no\ni\n<材质名>\nEnterEnd</script></macro_item>`
   - `<icon guid="图标guid" name="图标guid.png.svg"><png>base64</png></icon>`
4. **材质名 = rmtl 文件名**（不带扩展名）。宏里的材质名必须与 rmtl 文件名一致。
5. 材质宏规范：`_-Materials\no\ni\n<材质名>\nEnterEnd`（注意是 `i` 不是 `ni`）。

## 前置：判断材质类型

- **纯色材质**（无贴图）：参照 `Resources/Materials/earth.rmtl`（rcm-basic-material，simulation 里 `<diffuse>` 给颜色）。图标 = 纯色 32x32 方块（PIL RGB，透明项 RGBA + 黑描边），base64 约 136 字符。
- **贴图材质**（有 jpg）：参照 `Resources/Materials/co-concrate1.rmtl`。结构：rcm-basic-material + `<texture ... child-slot-name="bitmap-texture">` 子节点 + simulation 含 `Texture-1-filename` + 末尾 `<embedded-files><file compression="zlib" encoding="base64">` 内嵌贴图。图标 = 贴图 32x32 缩略。

## Step 1：生成贴图材质 rmtl（贴图材质路径）

在仓库 `Resources/Materials/` 用脚本生成 `<名称>.rmtl`：

```python
import zlib, base64, re
# 以 co-concrate1.rmtl 为模板
tpl = open('Resources/Materials/co-concrate1.rmtl', encoding='utf-8').read()
jpg = open('<贴图路径>', 'rb').read()
comp = zlib.compress(jpg)
b64 = base64.b64encode(comp).decode()
# 1) 把 filename 统一替换为相对名（跨平台不依赖绝对路径）
old_path = 'D:\\00-素材\\Temple-模版\\Rhino\\Temple\\2025-01-08-OpenLink_embedded_files\\Concrete_Aggregate_Smoke.jpg'
t = tpl.replace(old_path, '<文件名>.jpg')
# 2) 改 instance-name
t = t.replace('instance-name="Concrete_Aggregate_Smoke"', 'instance-name="<名称>"')
# 3) 替换 embedded-files 的 file 块
fb = re.search(r'<file name="[^"]*" original-size="\d+" compressed-size="\d+" compression="zlib" encoding="base64">[^<]*</file>', t)
new = f'<file name="<文件名>.jpg" original-size="{len(jpg)}" compressed-size="{len(comp)}" compression="zlib" encoding="base64">{b64}</file>'
t = t[:fb.start()] + new + t[fb.end():]
# 4) 去掉旧材质 thumbnail
t = re.sub(r'<thumbnail.*?</thumbnail>\n', '', t, flags=re.S)
open('Resources/Materials/<名称>.rmtl', 'w', encoding='utf-8').write(t)
```

校验：`python3 -c "import xml.etree.ElementTree as ET; ET.parse('...'); print('OK')"`。

## Step 2：生成 32x32 图标 base64（贴图缩略）

```bash
sips -z 32 32 "<贴图路径>" --out /tmp/<名称>_icon.png   # Mac
base64 < /tmp/<名称>_icon.png | wc -c                 # 记下 base64 内容
```
纯色材质则用 PIL 生成纯色 32x32 PNG（`Image.new('RGB',(32,32),color)`）。

## Step 3：插入 rui（Resources/Turtle.rui）

在 material-turtle 段追加三个节点，锚点用当前最后一个按钮：

```python
import base64, uuid
rui = open('Resources/Turtle.rui', encoding='utf-8').read()
b64 = <Step2 的 base64>
mac, icon, tb = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
# macro：锚点 = 上一按钮的 script 结束
# icon：锚点 = 上一按钮 icon 的 name=guid.png.svg 块
# tool_bar_item：material-turtle 最后一个 </tool_bar_item> 后追加
```

要求：guid 全部用 `uuid.uuid4()` 全新生成（避免继承/共享）；插入后 XML 校验；确认 material-turtle 按钮数 +1。

## Step 4：分发材质 + 同步 rui（需 require_escalated）

```bash
# 材质分发（Mac 材质库 + 仓库 assets 镜像）
cp "Resources/Materials/<名称>.rmtl" "/Users/zhenliu/Library/Application Support/McNeel/Rhinoceros/8.0/Render Content/en_US/Turtle/<名称>.rmtl"
cp "Resources/Materials/<名称>.rmtl" "assets/materials/<名称>.rmtl"
cp "Resources/Materials/img/<贴图>.jpg" "assets/materials/img/<贴图>.jpg"   # 先 mkdir -p

# 同步 rui（6 处，含 1.0.0 与 1.1.0）——推荐直接用双向脚本，一步完成 rui+材质：
python3 "<skill目录>/../../rhino-turtle-sync/scripts/sync_resources.py"
# 或单独同步 rui（rui_sync.py 已包含 1.1.0，无需再手动 cp）：
python3 "<skill目录>/../../rhino-toolbar-rui/scripts/rui_sync.py" "Resources/Turtle.rui"
```

`rui_sync.py` 已同步到 1.0.0 与 1.1.0（当前实际加载版本）。校验 6 处 md5 一致。

## Step 5：git 固化

```bash
cd /Users/zhenliu/study/coding/rhinoPluging && git add -A && git commit -m "<名称>材质按钮…" && git push origin main
```
Mac 直连推送。若带其它未提交文件（如脚本），一并确认后提交。

## 已知可复用事实

- material-turtle 工具列 guid：`3cdefd34-e8e5-4786-96d6-c0ee05e6467a`。
- 已用本流程做成按钮的节点（可作锚点参照）：earth（macro `9f095955…` / icon `50747c2a-b731-4db3-a9cc-2f4f57fa49c3`）、stoneConcrete（图标 = stoneConcrete.jpg 32x32 缩略，material-turtle 第 34 按钮）。
- 材质 rmtl 源在 `Resources/Materials/`，img 贴图在 `Resources/Materials/img/`；`assets/materials/` 是分发镜像（rmtl + img 都要）。
- 配合 rhino-toolbar-rui（图标/同步/覆盖层排障）与 rhino-turtle-sync（固化总流程）使用。
