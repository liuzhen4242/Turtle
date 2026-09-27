#!/usr/bin/env python3
"""新增 2 个绿色（黄绿 140,205,80 + 草绿 88,220,40）到 color-turtle 与 color-material-turtle"""
import re, base64, io, uuid, os
from PIL import Image

ROOT = "/Users/zhenliu/study/coding/rhinoPluging"
RUI = os.path.join(ROOT, "Resources/Turtle.rui")

with open(RUI, "r", encoding="utf-8") as f:
    content = f.read()

# ============ 1. 从现有绿色图标生成新颜色图标 ============
def extract_icon_png(content, bmp_guid):
    iidx = content.find(bmp_guid, content.find("<icons>"))
    iseg = content[iidx:iidx+2500]
    pm = re.search(r'<png>(.*?)</png>', iseg, re.S)
    if not pm:
        raise Exception(f"icon {bmp_guid} png not found")
    return pm.group(1)

def recolor_icon(src_b64, new_rgb):
    """把原图标所有非透明像素 RGB 改为 new_rgb，保留 alpha"""
    img = Image.open(io.BytesIO(base64.b64decode(src_b64))).convert("RGBA")
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a > 0:
                px[x, y] = (new_rgb[0], new_rgb[1], new_rgb[2], a)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

# 查现有绿色 macro 的 bitmap_id
def macro_bitmap(content, macro_guid):
    mm = re.search(r'<macro_item guid="%s"[^>]*bitmap_id="([^"]+)"' % macro_guid, content)
    return mm.group(1)

# color-turtle 圆形图标源：灰绿 [15] macro=eeafd776；color-material-turtle 方形图标源：灰绿 [15] macro=76b30f69
ct_src_bmp = macro_bitmap(content, "eeafd776-4426-4ec4-93f1-e18348c41d87") if False else None
# 直接用 guid 前缀查（避免猜全 guid，先用已知 8 位定位）
def find_macro_bitmap_by_prefix(content, prefix8):
    mm = re.search(r'<macro_item guid="%s[^"]*"[^>]*bitmap_id="([^"]+)"' % prefix8, content)
    if not mm:
        # 有的顺序是 bitmap_id 在前
        mm = re.search(r'<macro_item guid="%s[^"]*"[^>]*\n\s*<bitmap_id>([^<]+)</bitmap_id>' % prefix8, content)
    return mm.group(1) if mm else None

ct_graygreen_bmp = find_macro_bitmap_by_prefix(content, "eeafd776")
cmt_graygreen_bmp = find_macro_bitmap_by_prefix(content, "76b30f69")
print("color-turtle 灰绿 bitmap:", ct_graygreen_bmp)
print("color-material-turtle 灰绿 bitmap:", cmt_graygreen_bmp)

# 生成图标：黄绿 140,205,80 / 草绿 88,220,40
NEW_COLORS = {
    "yellow_green": (140, 205, 80),
    "grass_green": (88, 220, 40),
}

ct_src = extract_icon_png(content, ct_graygreen_bmp)
cmt_src = extract_icon_png(content, cmt_graygreen_bmp)

icons = {}
for name, rgb in NEW_COLORS.items():
    icons[f"ct_{name}"] = recolor_icon(ct_src, rgb)
    icons[f"cmt_{name}"] = recolor_icon(cmt_src, rgb)
    # 校验
    for k, b in [(f"ct_{name}", icons[f"ct_{name}"]), (f"cmt_{name}", icons[f"cmt_{name}"])]:
        img = Image.open(io.BytesIO(base64.b64decode(b)))
        colors = img.getcolors(maxcolors=100000)
        colors.sort(reverse=True)
        print(f"{k}: 主要色={colors[0][1][:3]} count={colors[0][0]}")

# ============ 2. 生成新 guid ============
guids = {}
for prefix in ["item_ct_yg", "macro_ct_yg", "icon_ct_yg",
               "item_ct_gg", "macro_ct_gg", "icon_ct_gg",
               "item_cmt_yg", "macro_cmt_yg", "icon_cmt_yg",
               "item_cmt_gg", "macro_cmt_gg", "icon_cmt_gg"]:
    guids[prefix] = str(uuid.uuid4())
for k, v in guids.items():
    print(f"{k} = {v}")

# ============ 3. 构造 XML 片段 ============
# color-turtle 黄绿（插在灰绿 item=9faf6a16 之后）
item_ct_yg = f"""      <tool_bar_item guid="{guids['item_ct_yg']}">
        <left_macro_id>{guids['macro_ct_yg']}</left_macro_id>
      </tool_bar_item>"""
macro_ct_yg = f"""    <macro_item guid="{guids['macro_ct_yg']}" bitmap_id="{guids['icon_ct_yg']}">
      <text>
        <locale_1033>Macro G-R55-B31 | L80</locale_1033>
      </text>
      <tooltip>
        <locale_1033>G-R55-B31 | L80</locale_1033>
      </tooltip>
      <button_text>
        <locale_1033>G-R55-B31 | L80</locale_1033>
      </button_text>
      <script>-Properties O C O
140,205,80
Enter
Enter
_SelNone</script>
    </macro_item>"""
icon_ct_yg = f"""    <icon guid="{guids['icon_ct_yg']}" name="{guids['icon_ct_yg']}.png">
      <png>{icons['ct_yellow_green']}</png>
    </icon>"""

# color-turtle 草绿（插在亮黄绿 item=c5f527b5 之后）
item_ct_gg = f"""      <tool_bar_item guid="{guids['item_ct_gg']}">
        <left_macro_id>{guids['macro_ct_gg']}</left_macro_id>
      </tool_bar_item>"""
macro_ct_gg = f"""    <macro_item guid="{guids['macro_ct_gg']}" bitmap_id="{guids['icon_ct_gg']}">
      <text>
        <locale_1033>Macro G-R35-B16 | L86</locale_1033>
      </text>
      <tooltip>
        <locale_1033>G-R35-B16 | L86</locale_1033>
      </tooltip>
      <button_text>
        <locale_1033>G-R35-B16 | L86</locale_1033>
      </button_text>
      <script>-Properties O C O
88,220,40
Enter
Enter
_SelNone</script>
    </macro_item>"""
icon_ct_gg = f"""    <icon guid="{guids['icon_ct_gg']}" name="{guids['icon_ct_gg']}.png">
      <png>{icons['ct_grass_green']}</png>
    </icon>"""

# color-material-turtle 黄绿（插在 Color_128_175_129_A0 item=9d1be1c5 之后）
item_cmt_yg = f"""      <tool_bar_item guid="{guids['item_cmt_yg']}">
        <left_macro_id>{guids['macro_cmt_yg']}</left_macro_id>
      </tool_bar_item>"""
macro_cmt_yg = f"""    <macro_item guid="{guids['macro_cmt_yg']}" bitmap_id="{guids['icon_cmt_yg']}">
      <text>
        <locale_1033>Macro Color_140_205_80_A0</locale_1033>
      </text>
      <tooltip>
        <locale_1033>Color_140_205_80_A0</locale_1033>
      </tooltip>
      <button_text>
        <locale_1033>Color_140_205_80_A0</locale_1033>
      </button_text>
      <script>_-Materials
o
ni
Color_140_205_80_A0
enterend</script>
    </macro_item>"""
icon_cmt_yg = f"""    <icon guid="{guids['icon_cmt_yg']}" name="{guids['icon_cmt_yg']}.png">
      <png>{icons['cmt_yellow_green']}</png>
    </icon>"""

# color-material-turtle 草绿（插在 Color_155_236_0_A0 item=ee68441d 之后）
item_cmt_gg = f"""      <tool_bar_item guid="{guids['item_cmt_gg']}">
        <left_macro_id>{guids['macro_cmt_gg']}</left_macro_id>
      </tool_bar_item>"""
macro_cmt_gg = f"""    <macro_item guid="{guids['macro_cmt_gg']}" bitmap_id="{guids['icon_cmt_gg']}">
      <text>
        <locale_1033>Macro Color_88_220_40_A0</locale_1033>
      </text>
      <tooltip>
        <locale_1033>Color_88_220_40_A0</locale_1033>
      </tooltip>
      <button_text>
        <locale_1033>Color_88_220_40_A0</locale_1033>
      </button_text>
      <script>_-Materials
o
ni
Color_88_220_40_A0
enterend</script>
    </macro_item>"""
icon_cmt_gg = f"""    <icon guid="{guids['icon_cmt_gg']}" name="{guids['icon_cmt_gg']}.png">
      <png>{icons['cmt_grass_green']}</png>
    </icon>"""

# ============ 4. 执行插入 ============
# 4.1 color-turtle：灰绿 item（9faf6a16）后插黄绿；亮黄绿 item（c5f527b5）后插草绿
def full_item(content, item_guid_prefix):
    m = re.search(r'(<tool_bar_item guid="%s[^"]*">.*?</tool_bar_item>)' % item_guid_prefix, content, re.S)
    assert m, f"item {item_guid_prefix} not found"
    return m.group(1)

ct_graygreen = full_item(content, "9faf6a16")
ct_yellowgreen = full_item(content, "c5f527b5")
content = content.replace(ct_graygreen, ct_graygreen + "\n" + item_ct_yg, 1)
content = content.replace(ct_yellowgreen, ct_yellowgreen + "\n" + item_ct_gg, 1)

# 4.2 color-material-turtle：灰绿 item（9d1be1c5）后插黄绿；亮黄绿 item（ee68441d）后插草绿
cmt_graygreen = full_item(content, "9d1be1c5")
cmt_yellowgreen = full_item(content, "ee68441d")
content = content.replace(cmt_graygreen, cmt_graygreen + "\n" + item_cmt_yg, 1)
content = content.replace(cmt_yellowgreen, cmt_yellowgreen + "\n" + item_cmt_gg, 1)

# 4.3 宏插入 </macros> 前
assert "</macros>" in content
content = content.replace("</macros>", "\n".join([
    macro_ct_yg, macro_ct_gg, macro_cmt_yg, macro_cmt_gg,
    "  </macros>"]), 1)

# 4.4 图标插入 </icons> 前
assert "</icons>" in content
content = content.replace("</icons>", "\n".join([
    icon_ct_yg, icon_ct_gg, icon_cmt_yg, icon_cmt_gg,
    "  </icons>"]), 1)

# ============ 5. 写回 + 校验 ============
with open(RUI, "w", encoding="utf-8") as f:
    f.write(content)

import xml.dom.minidom as minidom
minidom.parseString(content)
print("\nXML 校验通过")

for tb, cnt in [("c479780d-9ee4-4ab2-8d20-a7a37a356c74", 34), ("97eb5b7a-db48-4cf8-abe0-c06216ace898", 34)]:
    m = re.search(r'<tool_bar guid="%s".*?</tool_bar>' % tb, content, re.S)
    n = len(re.findall(r'<tool_bar_item guid=', m.group(0)))
    print(f"tool_bar {tb[:8]}: {n} items (期望 {cnt})")

# 保存 guid 供后续使用
import json
with open("/tmp/new_green_guids.json", "w") as f:
    json.dump(guids, f, indent=2)
print("\nguid 已保存 /tmp/new_green_guids.json")
