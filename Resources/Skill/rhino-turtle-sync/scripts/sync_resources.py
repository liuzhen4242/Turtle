#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_resources.py —— Turtle 插件「rui + 材质 + 脚本」双向同步（Mac / Windows）

原则（简化版）：
    · 以“修改时间最新”的文件为准，覆盖其它位置；
    · 被覆盖的文件先备份为 <原文件名>.bak-sync-<时间戳>（.gitignore 已忽略 *.bak-*）；
    · 全程 md5 校验：同名内容不同、单侧新增都会被发现；
    · 材质贴图子目录（Mac: Rhino pic/ ↔ 仓库 img/）按“内容去重”补缺，不删除。

用法：
    python3 sync_resources.py                    # 同步 rui + 材质 + 脚本
    python3 sync_resources.py --check            # 只检查差异，不写任何文件
    python3 sync_resources.py --rui              # 只同步 rui
    python3 sync_resources.py --materials        # 只同步材质
    python3 sync_resources.py --scripts          # 只同步 Python 脚本

注意：改 rui 前必须完全退出 Rhino（检测到 Rhinoceros 进程运行时自动跳过 rui 并提示）。
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

IS_WIN = os.name == "nt"
HOME = Path.home()

# ---------- 平台路径 ----------
if IS_WIN:
    REPO = Path(r"D:\00-素材\SoftTemple\Rhino\Turtle")
    APPDATA = Path(os.environ.get("APPDATA", ""))
    PKG = APPDATA / "McNeel" / "Rhinoceros" / "packages" / "8.0" / "Turtle"   # 注意大写
    RUI_LOCATIONS = [
        REPO / "Resources" / "Turtle.rui",
        PKG / "1.0.0" / "Turtle.rui",
        PKG / "1.1.0" / "Turtle.rui",
    ]
    MATERIAL_LOCATIONS = [
        APPDATA / "McNeel" / "Rhinoceros" / "8.0" / "Localization" / "en-US" / "Render Content" / "Turtle",
        APPDATA / "McNeel" / "Rhinoceros" / "8.0" / "Localization" / "zh-CN" / "Render Content" / "Turtle",
        REPO / "Resources" / "Materials",
        REPO / "assets" / "materials",
    ]
    SCRIPTS_LOCATIONS = [
        APPDATA / "McNeel" / "Rhinoceros" / "8.0" / "scripts",   # 注意小写 scripts
        REPO / "Scripts",
    ]
    TEXTURE_PAIRS = []   # Windows 材质子目录结构未确认，暂不同步贴图
else:
    REPO = Path("/Users/zhenliu/study/coding/rhinoPluging")
    R8 = HOME / "Library/Application Support/McNeel/Rhinoceros/8.0"
    RHINO_BASE = HOME / "Library/Application Support/McNeel/Rhinoceros"
    PKG = RHINO_BASE / "packages" / "8.0" / "turtle"   # 注意小写
    RUI_LOCATIONS = [
        R8 / "UI" / "Turtle.rui",
        R8 / "MacPlugIns" / "Turtle.rhp" / "Turtle.rui",
        RHINO_BASE / "MacPlugIns" / "Turtle.rhp" / "Turtle.rui",
        REPO / "Resources" / "Turtle.rui",
        PKG / "1.0.0" / "Turtle.rui",
        PKG / "1.1.0" / "Turtle.rui",
    ]
    MATERIAL_LOCATIONS = [
        R8 / "Render Content" / "en_US" / "Turtle",
        REPO / "Resources" / "Materials",
        REPO / "assets" / "materials",
    ]
    SCRIPTS_LOCATIONS = [
        R8 / "scripts",          # 注意小写 scripts
        REPO / "Scripts",
    ]
    TEXTURE_PAIRS = [
        (R8 / "Render Content" / "en_US" / "Turtle" / "pic", REPO / "Resources" / "Materials" / "img"),
        (R8 / "Render Content" / "en_US" / "Turtle" / "pic", REPO / "assets" / "materials" / "img"),
    ]

PLATFORM = "Windows" if IS_WIN else "Mac"

# Rhino 系统自带脚本（非 Turtle 插件内容），同步脚本时必须排除
EXCLUDE_SCRIPTS = {"RhinoStartup.py", "RhinoWorkspaceStartup.py", "workspace_startup.py"}


def md5(p: Path):
    try:
        return hashlib.md5(p.read_bytes()).hexdigest()
    except OSError:
        return None


def backup(p: Path, ts: str):
    bak = p.with_name(p.name + f".bak-sync-{ts}")
    shutil.copy2(p, bak)
    return bak


def rhino_running() -> bool:
    """检测 Rhino 进程是否在运行（Mac 进程名 Rhinoceros / Win Rhinoceros.exe）"""
    try:
        if IS_WIN:
            out = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Rhinoceros.exe"],
                capture_output=True, text=True, timeout=10).stdout
            return "Rhinoceros.exe" in out
        out = subprocess.run(["pgrep", "-x", "Rhinoceros"], capture_output=True, timeout=5)
        return out.returncode == 0
    except Exception:
        return False   # 检测失败时不阻止


def sync_group(files, label, check=False, ts=None) -> int:
    """一组文件同步为同一内容：以 mtime 最新者为准，覆盖其它或补齐缺失；返回差异/覆盖数。"""
    existing = [p for p in files if p.is_file()]
    if not existing:
        print(f"  ⚠️ {label}: 所有位置均不存在，跳过")
        return 0
    newest = max(existing, key=lambda p: p.stat().st_mtime)
    hashes = {p: md5(p) for p in existing}
    uniq = {h for h in hashes.values() if h}
    missing = [p for p in files if not p.is_file()]
    if len(uniq) <= 1 and not missing:
        return 0
    targets = [p for p in existing if p is not newest and hashes[p] != hashes[newest]] + missing
    print(f"  ⚠️ {label}: 以最新者为准 -> {newest}")
    n = 0
    for p in targets:
        existed = p.is_file()
        if check:
            print(f"     将{'覆盖' if existed else '补齐'}: {p}")
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            if existed:
                backup(p, ts)
            shutil.copy2(newest, p)
            print(f"     已{'备份并覆盖' if existed else '补齐'}: {p}")
        n += 1
    return n


def sync_files(dirs, suffix, label, check=False, ts=None, exclude=()) -> int:
    """按后缀同步一组目录：同名取最新者；单侧新增复制到其它目录。材质/脚本通用。"""
    names = set()
    for d in dirs:
        if d.is_dir():
            names.update(f for f in os.listdir(d) if f.endswith(suffix) and f not in exclude)
    if not names:
        print(f"  ⚠️ {label}目录均为空或不存在")
        return 0
    n = 0
    for name in sorted(names):
        paths = [d / name for d in dirs if (d / name).is_file()]
        if len(paths) == 1:
            src = paths[0]
            missing = [d for d in dirs if not (d / name).exists()]
            if not missing:
                continue
            if check:
                print(f"  ⚠️ 单侧新增: {name} 仅存在于 {src.parent}，缺于 {len(missing)} 处")
                n += 1
            else:
                for d in missing:
                    d.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, d / name)
                    print(f"     复制: {name} -> {d}")
                n += 1
            continue
        n += sync_group(paths, f"{label} {name}", check, ts)
    return n


def sync_texture_pair(a: Path, b: Path, check=False, ts=None) -> int:
    """贴图子目录内容去重：把 a/b 中对方缺失的内容复制过去，不删除。"""
    if not a.is_dir() and not b.is_dir():
        return 0
    a.mkdir(parents=True, exist_ok=True)
    b.mkdir(parents=True, exist_ok=True)
    skip = {".DS_Store", "Thumbs.db"}
    bh = {md5(p): p for p in b.iterdir() if p.is_file() and p.name not in skip}
    ah = {md5(p): p for p in a.iterdir() if p.is_file() and p.name not in skip}
    n = 0
    for h, p in ah.items():
        if h not in bh:
            t = b / p.name
            if check:
                print(f"  ⚠️ 贴图缺于 {b}: {p.name}")
            else:
                shutil.copy2(p, t)
                print(f"     复制贴图: {p.name} -> {b}")
            n += 1
    for h, p in bh.items():
        if h not in ah:
            t = a / p.name
            if check:
                print(f"  ⚠️ 贴图缺于 {a}: {p.name}")
            else:
                shutil.copy2(p, t)
                print(f"     复制贴图: {p.name} -> {a}")
            n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description="Turtle rui + 材质 + 脚本双向同步")
    ap.add_argument("--check", action="store_true", help="只检查差异，不写任何文件")
    ap.add_argument("--rui", action="store_true", help="只处理 rui")
    ap.add_argument("--materials", action="store_true", help="只处理材质")
    ap.add_argument("--scripts", action="store_true", help="只处理 Python 脚本")
    args = ap.parse_args()
    ts = time.strftime("%Y%m%d-%H%M%S")

    only = args.rui or args.materials or args.scripts
    do_rui = args.rui or not only
    do_mat = args.materials or not only
    do_scripts = args.scripts or not only
    mode = "检查（只读）" if args.check else "同步"
    print(f"平台: {PLATFORM} | 模式: {mode} | 仓库: {REPO}")

    # 启动校验：仓库路径必须存在，防止在错误的机器/路径下静默误跑
    if not REPO.is_dir():
        print(f"❌ 仓库路径不存在: {REPO}")
        print("   请确认：Mac 上应为 /Users/zhenliu/study/coding/rhinoPluging，Windows 上应为 D:\\00-素材\\SoftTemple\\Rhino\\Turtle")
        print("   若实际路径不同，请修改脚本顶部的 REPO 常量后再运行。")
        return 2
    if not (REPO / "Resources" / "Turtle.rui").is_file():
        print(f"⚠️ 仓库 Resources/Turtle.rui 不存在，将只做 Rhino 侧位置之间的同步")

    n = 0
    if do_rui:
        print("\n=== 1. 工具列 rui ===")
        if rhino_running():
            print("  ⚠️ 检测到 Rhino（Rhinoceros）正在运行，跳过 rui。请完全退出 Rhino 后重试。")
        else:
            n += sync_group(RUI_LOCATIONS, "rui", args.check, ts)
    if do_mat:
        print("\n=== 2. 材质（.rmtl）===")
        n += sync_files(MATERIAL_LOCATIONS, ".rmtl", "材质", args.check, ts)
        if TEXTURE_PAIRS:
            print("\n=== 3. 材质贴图子目录（内容去重补缺）===")
            for a, b in TEXTURE_PAIRS:
                n += sync_texture_pair(a, b, args.check, ts)
    if do_scripts:
        print("\n=== 4. Python 脚本（.py）===")
        n += sync_files(SCRIPTS_LOCATIONS, ".py", "脚本", args.check, ts, exclude=EXCLUDE_SCRIPTS)

    print("\n" + "=" * 50)
    if n:
        print("⚠️ 存在差异，请查看上方清单" if args.check else "✅ 同步完成，被覆盖处已备份为 .bak-sync-<时间戳>")
        return 1 if args.check else 0
    print("✅ 全部一致，无需操作")
    return 0


if __name__ == "__main__":
    sys.exit(main())
