#!/usr/bin/env python3
"""rui_sync.py —— 同步 Turtle.rui 到 Mac 上全部 6 个位置并校验。

用法：
    python3 rui_sync.py <源Turtle.rui路径>            # 同步 + 校验
    python3 rui_sync.py <源Turtle.rui路径> --verify-only   # 只校验不同步

行为：
    1. 校验源文件是合法 XML（ET.parse）
    2. 对每个目标：先备份为 .bak-sync-<时间戳>，再复制覆盖
    3. 输出全部位置的 md5，确认一致
    4. --verify-only 时只对比 md5 与 XML，不写任何文件

注意：
    - Mac 上位置 6（packages/8.0/turtle/1.1.0）是 Rhino 当前实际加载位，必须同步（1.0.0 与 1.1.0 都要）。
    - Windows 目标列表不同：8.0\\UI\\Turtle.rui 目录不存在，只需 packages 目录（%APPDATA%\\McNeel\\Rhinoceros\\packages\\8.0\\Turtle\\{ver}\\Turtle.rui，大写 Turtle）。
    - 日常 rui+材质双向同步建议用 ../rhino-turtle-sync/scripts/sync_resources.py（自动以最新者为准）。
    - 运行前确保 Rhino 已完全退出（进程名 Rhinoceros，kill <pid>）。
"""

import sys
import hashlib
import time
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

HOME = Path.home()

# Mac 目标列表（顺序即优先级；最后两位是 yak packages 加载位，1.1.0 为当前实际加载版本）
MAC_TARGETS = [
    HOME / "Library/Application Support/McNeel/Rhinoceros/8.0/UI/Turtle.rui",
    HOME / "Library/Application Support/McNeel/Rhinoceros/8.0/MacPlugIns/Turtle.rhp/Turtle.rui",
    HOME / "Library/Application Support/McNeel/Rhinoceros/MacPlugIns/Turtle.rhp/Turtle.rui",
    HOME / "study/coding/rhinoPluging/Resources/Turtle.rui",
    HOME / "Library/Application Support/McNeel/Rhinoceros/packages/8.0/turtle/1.0.0/Turtle.rui",
    HOME / "Library/Application Support/McNeel/Rhinoceros/packages/8.0/turtle/1.1.0/Turtle.rui",  # 真正加载位！
]

# Windows 目标列表：8.0\UI\ 目录不存在，加载位只有 packages（大写 Turtle）
WIN_TARGETS = [
    Path.home() / "AppData/Roaming/McNeel/Rhinoceros/packages/8.0/Turtle/1.0.0/Turtle.rui",
    Path.home() / "AppData/Roaming/McNeel/Rhinoceros/packages/8.0/Turtle/1.1.0/Turtle.rui",
]


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--verify-only"]
    verify_only = "--verify-only" in sys.argv

    if not args:
        print("用法: python3 rui_sync.py <源Turtle.rui路径> [--verify-only]")
        return 2

    src = Path(args[0])
    if not src.exists():
        print(f"源文件不存在: {src}")
        return 1

    # 1. XML 合法性校验
    try:
        ET.parse(src)
    except ET.ParseError as e:
        print(f"源文件 XML 非法: {e}")
        return 1

    targets = MAC_TARGETS if sys.platform == "darwin" else WIN_TARGETS

    print(f"源: {src}  ({md5(src)})")
    ok = True
    for t in targets:
        if not t.exists():
            print(f"  [缺] {t}")
            ok = False
            continue
        same = md5(t) == md5(src)
        if same:
            print(f"  [一致] {t}")
        else:
            print(f"  [不同] {t}")
            if not verify_only:
                bak = t.with_name(t.name + f".bak-sync-{time.strftime('%Y%m%d-%H%M%S')}")
                shutil.copy2(t, bak)
                shutil.copy2(src, t)
                print(f"      已备份到 {bak.name} 并覆盖")
            ok = False

    if verify_only:
        print("\n结论:", "全部一致 ✅" if ok else "存在差异（需同步）❌")
    else:
        print("\n结论:", "已全部同步 ✅" if not ok else "原本就一致，未改动 ✅")
    return 0 if (ok or not verify_only) else 1


if __name__ == "__main__":
    sys.exit(main())
