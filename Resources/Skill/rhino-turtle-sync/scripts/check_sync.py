#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Turtle 固化前检查清单生成器（Mac / Windows 双平台自动检测）
对比 仓库 与 当前机器 Rhino 各资源，输出"哪些一致 / 哪些有差异"的清单，
供固化流程逐条向用户确认。运行方式：
    python3 check_sync.py [--repo <仓库路径>]
仓库路径缺省自动探测（Mac: /Users/zhenliu/study/coding/rhinoPluging；Win: D:\\00-素材\\SoftTemple\\Rhino\\Turtle）。
"""
import argparse
import hashlib
import os
import re
import sys

IS_WIN = os.name == "nt"

# ---------- 平台路径 ----------
if IS_WIN:
    REPO = r"D:\00-素材\SoftTemple\Rhino\Turtle"
    RHINO_BASE = os.path.join(os.environ.get("APPDATA", ""), "McNeel", "Rhinoceros")
    RHINO8 = os.path.join(RHINO_BASE, "8.0")
    # rui 真正加载位：packages 目录（8.0\UI\ 在 Windows 上不存在）
    RUI_TARGETS = [
        os.path.join(RHINO_BASE, "packages", "8.0", "Turtle", "1.0.0", "Turtle.rui"),
        os.path.join(RHINO_BASE, "packages", "8.0", "Turtle", "1.1.0", "Turtle.rui"),
    ]
    SCRIPTS_DIR = os.path.join(RHINO8, "scripts")          # 注意大小写 scripts
    MATERIAL_DIRS = [                                      # 中英文都要放
        os.path.join(RHINO8, "Localization", "en-US", "Render Content", "Turtle"),
        os.path.join(RHINO8, "Localization", "zh-CN", "Render Content", "Turtle"),
    ]
    DISPLAY_DIR = os.path.join(RHINO8, "DisplayModes")
    TEMPLATE_DIRS = [
        os.path.join(RHINO8, "Localization", "en-US", "Template Files"),
        os.path.join(RHINO8, "Localization", "zh-CN", "Template Files"),
    ]
    HAS_ALIASES_FILE = False          # Windows 无 settings\aliases，快捷键只能 GUI 导入
else:
    REPO = "/Users/zhenliu/study/coding/rhinoPluging"
    RHINO_BASE = os.path.expanduser("~/Library/Application Support/McNeel/Rhinoceros")
    RHINO8 = os.path.join(RHINO_BASE, "8.0")
    RUI_TARGETS = [
        os.path.join(RHINO8, "UI", "Turtle.rui"),
        os.path.join(RHINO8, "MacPlugIns", "Turtle.rhp", "Turtle.rui"),
        os.path.join(RHINO_BASE, "MacPlugIns", "Turtle.rhp", "Turtle.rui"),
        os.path.join(RHINO_BASE, "packages", "8.0", "turtle", "1.0.0", "Turtle.rui"),
        os.path.join(RHINO_BASE, "packages", "8.0", "turtle", "1.1.0", "Turtle.rui"),
    ]
    SCRIPTS_DIR = os.path.join(RHINO8, "Scripts")
    MATERIAL_DIRS = [os.path.join(RHINO8, "Render Content", "en_US", "Turtle")]
    DISPLAY_DIR = os.path.join(RHINO8, "settings", "displaymodes")
    TEMPLATE_DIRS = [os.path.join(RHINO_BASE, "Template Files")]
    HAS_ALIASES_FILE = True

PLATFORM = "Windows" if IS_WIN else "Mac"


def md5(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except OSError:
        return None


def listdir(d, suffix=None):
    try:
        fs = os.listdir(d)
    except OSError:
        return []
    if suffix:
        fs = [f for f in fs if f.endswith(suffix)]
    return sorted(fs)


def check_rui():
    print(f"=== 1. 工具列 rui（{PLATFORM} 加载位）===")
    src = os.path.join(REPO, "Resources", "Turtle.rui")
    src_md5 = md5(src)
    ok = True
    for t in RUI_TARGETS:
        if not os.path.exists(t):
            print(f"  ℹ️ 跳过（目录不存在）: {t}")
            continue
        m = md5(t)
        state = "✅ 一致" if m == src_md5 else "⚠️ 不同"
        if m != src_md5:
            ok = False
        print(f"  {state}  {t}")
    print(f"  源 md5: {src_md5[:12]}…  结论: {'✅ 全部一致' if ok else '⚠️ 需要同步'}")
    return ok


def check_scripts():
    print("\n=== 2. Python 脚本 ===")
    repo_scripts = os.path.join(REPO, "Scripts")
    repo_files = listdir(repo_scripts, ".py")
    if not repo_files:
        print("  ⚠️ 仓库 Scripts/ 为空或不存在")
        return False
    diff = []
    for f in repo_files:
        rm, hm = md5(os.path.join(repo_scripts, f)), md5(os.path.join(SCRIPTS_DIR, f))
        if rm != hm:
            diff.append(f)
    if not diff:
        print(f"  ✅ 仓库 {len(repo_files)} 个脚本与 Rhino 全部一致")
        return True
    print(f"  ⚠️ {len(diff)} 个脚本有差异: {diff}")
    return False


def check_materials():
    print("\n=== 3. 材质库（以仓库 Resources/Materials 为准，md5 级对比）===")
    repo_mat = os.path.join(REPO, "Resources", "Materials")
    repo_assets = os.path.join(REPO, "assets", "materials")
    rp_files = listdir(repo_mat, ".rmtl")
    ra_files = listdir(repo_assets, ".rmtl")
    ok = True
    for d in MATERIAL_DIRS:
        rhino_files = listdir(d, ".rmtl")
        if set(rp_files) == set(rhino_files):
            print(f"  ✅ {d} 与仓库文件集合一致（{len(rhino_files)} 个）")
        else:
            ok = False
            only_r = sorted(set(rp_files) - set(rhino_files))
            only_h = sorted(set(rhino_files) - set(rp_files))
            print(f"  ⚠️ {d}: 仓库 {len(rp_files)} vs Rhino {len(rhino_files)}")
            if only_r: print(f"     仓库多余: {only_r[:6]}")
            if only_h: print(f"     仓库缺少: {only_h[:6]}")
        # 同名文件内容级对比（防同名但内容不同漏检）
        content_diff = []
        for f in set(rp_files) & set(rhino_files):
            if md5(os.path.join(repo_mat, f)) != md5(os.path.join(d, f)):
                content_diff.append(f)
        if content_diff:
            ok = False
            print(f"  ⚠️ {d}: {len(content_diff)} 个同名文件内容不同: {content_diff[:6]}")
    if set(rp_files) != set(ra_files):
        ok = False
        print(f"  ⚠️ Resources/Materials({len(rp_files)}) 与 assets/materials({len(ra_files)}) 不一致")
    else:
        print(f"  ✅ 仓库两处材质一致（{len(rp_files)} 个）")
    return ok


def norm_aliases(path):
    d = {}
    try:
        for line in open(path, encoding="utf-8-sig").read().splitlines():
            line = line.strip()
            if not line:
                continue
            m = re.match(r"^([^=\s]+)\s*[=\s]\s*(.*)$", line)
            if m:
                d[m.group(1).strip()] = m.group(2).strip()
    except OSError:
        pass
    return d


def check_aliases():
    print("\n=== 4. 快捷键 KeyTurtle.txt ===")
    repo_key = os.path.join(REPO, "Resources", "KeyTurtle.txt")
    if not os.path.exists(repo_key):
        print("  ⚠️ 仓库缺 KeyTurtle.txt")
        return False
    repo_d = norm_aliases(repo_key)
    if not HAS_ALIASES_FILE:
        print(f"  ℹ️ {PLATFORM} 无 settings/aliases 文件，快捷键只能经 Rhino GUI「工具→选项→键盘→导入」导入 KeyTurtle.txt（{len(repo_d)} 条）。无法自动比对。")
        return True
    rhino_aliases = os.path.join(RHINO8, "settings", "aliases")
    rhino_d = norm_aliases(rhino_aliases)
    if repo_d == rhino_d:
        print(f"  ✅ 仓库 KeyTurtle.txt 与 Rhino 当前别名一致（{len(repo_d)} 条）")
        return True
    only_r = sorted(set(rhino_d) - set(repo_d))
    only_p = sorted(set(repo_d) - set(rhino_d))
    diff_v = [k for k in rhino_d if k in repo_d and repo_d[k] != rhino_d[k]]
    print(f"  ⚠️ 不一致: Rhino 独有 {len(only_r)}、仓库独有 {len(only_p)}、值不同 {len(diff_v)}")
    if only_r: print(f"     Rhino 独有: {only_r[:10]}")
    if only_p: print(f"     仓库独有: {only_p[:10]}")
    if diff_v: print(f"     值不同: {diff_v[:10]}")
    return False


def check_display_styles():
    print("\n=== 5. 显示样式 ini ===")
    repo_ds = os.path.join(REPO, "Resources", "DisplayStyles")
    repo_files = listdir(repo_ds, ".ini")
    rhino_files = listdir(DISPLAY_DIR, ".ini")
    missing = [f for f in repo_files if f not in rhino_files]
    if not missing:
        print(f"  ✅ 仓库 {len(repo_files)} 个 ini 均已同步到 Rhino displaymodes")
        return True
    print(f"  ⚠️ 仓库 {len(repo_files)} 个，Rhino 缺 {len(missing)} 个: {missing}")
    return False


def check_template():
    print("\n=== 6. 模板 Turtle.3dm ===")
    repo_t = os.path.join(REPO, "Resources", "Turtle.3dm")
    rm = md5(repo_t)
    ok = True
    for d in TEMPLATE_DIRS:
        rhino_t = os.path.join(d, "Turtle.3dm")
        hm = md5(rhino_t)
        if rm == hm:
            print(f"  ✅ {d} 与仓库一致")
        else:
            ok = False
            print(f"  ⚠️ {d} 不一致（需确认哪边最新）")
    return ok


def check_gh():
    print("\n=== 7. GH 电池（保持现状）===")
    gh = os.path.join(REPO, "Grasshopper")
    files = listdir(gh)
    print(f"  ℹ️ 仓库 Grasshopper/: {files}")
    return True


def main():
    global REPO
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    args = ap.parse_args()
    REPO = args.repo

    print(f"平台: {PLATFORM} | 仓库: {REPO}")
    results = [
        ("工具列 rui", check_rui()),
        ("脚本", check_scripts()),
        ("材质", check_materials()),
        ("快捷键", check_aliases()),
        ("显示样式", check_display_styles()),
        ("模板", check_template()),
        ("GH", check_gh()),
    ]
    print("\n" + "=" * 50)
    print("固化检查清单汇总：")
    for name, ok in results:
        print(f"  {'✅' if ok else '⚠️'} {name}")
    if all(ok for _, ok in results):
        print("\n✅ 全部一致，无需固化")
    else:
        print("\n⚠️ 存在差异项，请逐条向用户确认后固化")
    sys.exit(0)


if __name__ == "__main__":
    main()
