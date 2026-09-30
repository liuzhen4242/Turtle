#!/usr/bin/env python3
"""OpenLink 博客 frontmatter 检查 / 修复脚本（跨 Windows / Mac 可用）

用法:
  python check_frontmatter.py <仓库根目录>          # 只检查
  python check_frontmatter.py <仓库根目录> --fix     # 检查 + 自动修复

检查规则（与用户 frontmatter 规范一致）:
  - title  必须存在且为中文（主标题）
  - titleEn 应为英文；缺失 / 占位符（Article English Title）时提示
  - date / description / status 应存在
  - category 应存在且至少一个子项
  - 禁止占位符: "一句话摘要"、"文章中文标题"
  - 禁止旧字段: name 行、空值 update 行（空 update 会被 YAML 解析为 null，
    导致 zod union 校验失败 → dev 崩溃，必须删除）

--fix 自动删除 name 行与空 update 行（确定性安全修复）；
缺失 title / titleEn / description / category 等需要语义判断，
脚本只标记，由 AI 依据文章内容补齐。
"""
import os, re, sys, glob

PLACEHOLDER_TITLES = ("Article English Title", "一句话摘要", "文章中文标题")
REQUIRED_KEYS = ("date", "description", "status")


def parse_frontmatter(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return None, None
    return m.group(1), m


def get_field(fm, key):
    m = re.search(rf"^({key})\s*:\s*(.*)$", fm, re.M)
    if not m:
        return None, None
    return m.group(1), m.group(2).strip()


def category_has_items(fm):
    m = re.search(r"^category\s*:\s*$", fm, re.M)
    if not m:
        return False  # 字段缺失
    rest = fm[m.end():]
    # 下一个顶层字段或空行前，是否出现至少一个 "- item"
    mm = re.match(r"(?:\s*\n)?((?:\s*-\s*.+\n?)+)", rest)
    return bool(mm and mm.group(1).strip())


def collect_files(root):
    files = []
    content = os.path.join(root, "src", "content")
    if not os.path.isdir(content):
        print(f"❌ 找不到 {content}，请传入仓库根目录")
        sys.exit(2)
    for sub in ("blog", "projects"):
        base = os.path.join(content, sub)
        if os.path.isdir(base):
            files += glob.glob(os.path.join(base, "**", "*.md"), recursive=True)
    return sorted(f for f in files if "._" not in os.path.basename(f))


def check_all(files, root):
    issues = []
    for f in files:
        rel = os.path.relpath(f, root).replace("\\", "/")
        txt = open(f, encoding="utf-8").read()
        fm, _ = parse_frontmatter(txt)
        if fm is None:
            issues.append((rel, "无 frontmatter 块"))
            continue

        _, tval = get_field(fm, "title")
        ten_key, teval = get_field(fm, "titleEn")

        if tval is None:
            issues.append((rel, "缺 title（schema 必填，dev 会崩溃）"))
        elif not re.search(r"[\u4e00-\u9fff]", tval):
            issues.append((rel, f"title 非中文: {tval}"))

        if ten_key is None:
            issues.append((rel, "缺 titleEn（建议补英文，或由 AI 翻译）"))
        elif teval and teval.strip('"') in PLACEHOLDER_TITLES:
            issues.append((rel, f"titleEn 占位符: {teval}"))

        for k in REQUIRED_KEYS:
            kk, _ = get_field(fm, k)
            if kk is None:
                issues.append((rel, f"缺 {k}"))

        if not category_has_items(fm):
            issues.append((rel, "category 缺失或为空（建议至少一个子项）"))

        for ph in ("一句话摘要", "文章中文标题"):
            if re.search(rf"^{ph}\s*:", fm, re.M):
                issues.append((rel, f"description/title 占位符: {ph}"))

        if get_field(fm, "name")[0]:
            issues.append((rel, "残留旧字段 name（应删除）"))

        uk, uv = get_field(fm, "update")
        if uk is not None and uv == "":
            issues.append((rel, "update 空值（YAML→null，schema 校验失败→dev 崩溃，应删行）"))
    return issues


def fix_auto(files, root):
    fixed = []
    for f in files:
        txt = open(f, encoding="utf-8").read()
        m = re.match(r"^(---\r?\n)(.*?)(\r?\n---)", txt, re.S)
        if not m:
            continue
        fm = m.group(2)
        new_fm = re.sub(r"^name\s*:.*$\n?", "", fm, flags=re.M)
        new_fm = re.sub(r"^update\s*:\s*$\n?", "", new_fm, flags=re.M)
        if new_fm != fm:
            txt = m.group(1) + new_fm + m.group(3) + txt[m.end():]
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(txt)
            fixed.append(os.path.relpath(f, root).replace("\\", "/"))
    return fixed


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = args[0] if args else os.getcwd()
    fix = "--fix" in sys.argv

    files = collect_files(root)
    issues = check_all(files, root)

    if not issues:
        print(f"✅ 全部 {len(files)} 个文件 frontmatter 合规（title 中文 / titleEn 英文 / 字段齐全 / 无占位符）")
        return 0

    print(f"⚠️  发现 {len(issues)} 个问题（共 {len(files)} 个文件）：")
    for rel, msg in issues:
        print(f"  [{msg}] {rel}")

    if fix:
        fixed = fix_auto(files, root)
        print(f"\n🔧 已自动修复 {len(fixed)} 个文件（删除 name / 空 update）：")
        for rel in fixed:
            print(f"  - {rel}")
        print("\n剩余问题需由 AI 依据文章内容补齐（补 title/titleEn/description/category 等）。")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
