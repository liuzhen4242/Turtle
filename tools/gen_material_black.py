#!/usr/bin/env python3
"""生成 Color_0_0_0_A120.rmtl 并分发到 git 源与 Mac 加载位"""
import shutil, os

src = "/Users/zhenliu/Library/Application Support/McNeel/Rhinoceros/8.0/Render Content/en_US/Turtle/Color_74_74_74_A120.rmtl"
with open(src, "r", encoding="utf-8-sig") as f:
    text = f.read()

new_text = text.replace("0.290196,0.290196,0.290196,1", "0,0,0,1", 1)

# 校验：parameters-v8 的 diffuse 已替换且透明度保留
v8 = new_text.split("<parameters-v8>")[1].split("</parameters-v8>")[0]
assert "0,0,0,1" in v8, "diffuse 未替换"
assert "0.470588" in v8, "transparency 丢失"

dests = [
    "/Users/zhenliu/study/coding/rhinoPluging/Resources/Materials/Color_0_0_0_A120.rmtl",
    "/Users/zhenliu/Library/Application Support/McNeel/Rhinoceros/8.0/Render Content/en_US/Turtle/Color_0_0_0_A120.rmtl",
    "/Users/zhenliu/Library/Application Support/McNeel/Rhinoceros/8.0/Render Content/zh_CN/Turtle/Color_0_0_0_A120.rmtl",
]
for d in dests:
    os.makedirs(os.path.dirname(d), exist_ok=True)
    with open(d, "w", encoding="utf-8-sig") as f:
        f.write(new_text)
    print(f"已写入: {d}")

# 校验文件一致性
md5s = set()
for d in dests:
    with open(d, "rb") as f:
        md5s.add(hash(f.read()))
print(f"\n{len(dests)} 个文件已生成，内容一致: {len(md5s) == 1}")
