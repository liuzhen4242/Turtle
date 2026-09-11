#!/usr/bin/env python3
"""
ghuser 属性补丁工具：修改 .ghuser 文件内的 Category / SubCategory 等字段。

用途：Turtle 插件采用"视觉合并"方案，ghuser 的 Category 必须与 GHA 组件一致（turtle），
这样 GH 面板里会合并成同一个标签页。如果 GH 里重新导出了 ghuser，跑一次本脚本即可。

用法：
    python3 patch_ghuser.py <input.ghuser> <output.ghuser> [Category] [SubCategory]

原理：.ghuser 是 raw-deflate 压缩的 GH_IO 序列化流，字段格式为
      <fieldname>\xff\xff\xff\xff\x0a\x00\x00\x00<len><utf8 value>
      直接替换值并重新 deflate 压缩即可，GH 可正常读取。
"""
import sys
import zlib


def patch_str(data: bytes, name: bytes, new_val: str):
    marker = name + b'\xff\xff\xff\xff\x0a\x00\x00\x00'
    idx = data.find(marker)
    if idx < 0:
        raise ValueError(f"字段 {name.decode()} 未找到")
    vs = idx + len(marker)
    old_len = data[vs]
    old_val = data[vs + 1:vs + 1 + old_len]
    nb = new_val.encode('utf-8')
    patched = data[:vs] + bytes([len(nb)]) + nb + data[vs + old_len + 1:]
    return patched, old_val.decode()


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]
    new_cat = sys.argv[3] if len(sys.argv) > 3 else None
    new_sub = sys.argv[4] if len(sys.argv) > 4 else None

    raw = open(src, 'rb').read()
    inflated = zlib.decompress(raw, -15)

    if new_cat is not None:
        inflated, old = patch_str(inflated, b'Category', new_cat)
        print(f"Category: {old} -> {new_cat}")
    if new_sub is not None:
        inflated, old = patch_str(inflated, b'SubCategory', new_sub)
        print(f"SubCategory: {old} -> {new_sub}")

    comp = zlib.compressobj(level=-1, wbits=-15)
    out = comp.compress(inflated) + comp.flush()
    open(dst, 'wb').write(out)
    print(f"written: {dst} ({len(out)} bytes)")

    # 自校验
    back = zlib.decompress(out, -15)
    for name in (b'Category', b'SubCategory'):
        marker = name + b'\xff\xff\xff\xff\x0a\x00\x00\x00'
        i = back.find(marker)
        vs = i + len(marker)
        print(f"verify {name.decode()}: {back[vs + 1:vs + 1 + back[vs]].decode()}")


if __name__ == '__main__':
    main()
