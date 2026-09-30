# OpenLink 博客常见问题速查

> 按症状排查；每条都来自真实踩坑。排查顺序：先看错误类型 → 定位 → 修复 → 重启 dev 验证。

## 1. dev 崩溃 / 页面打不开（最高频）

### 症状：dev 启动报 `[InvalidContentEntryDataError] ... does not match collection schema`
即 `src/content/blog` 或 `src/content/projects` 下某篇 .md 的 frontmatter 不符合 `src/content.config.ts` 的 schema。**dev 会直接退出，页面打不开**。

**逐条排查**（按频率）：

| 原因 | 报错特征 | 修复 |
|---|---|---|
| 新文章缺 `title` | `title: Required` / `Expected string, received undefined` | 补完整 frontmatter（见 frontmatter 规范） |
| 空值 `update:` | `update: Did not match union. Expected type "date", received "object"` | YAML 空值 → null，zod `.optional()` 只接受 undefined 不接受 null → **删除整行 `update:`**（空值）。`check_frontmatter.py --fix` 可自动删 |
| 空值 `date:`/其他字段 | `Expected type "date", received "object"` | 删除空行或填真实日期 |
| `name` 旧字段 | 无（schema 忽略） | 删除（旧版字段已废弃，并入 title） |
| 图片/资源路径错 | 构建时报文件不存在 | 检查 `![](...)` 相对路径 |

**修复步骤**：
1. `python <skill>/scripts/check_frontmatter.py <仓库根> --fix` 自动修复确定性项
2. 剩余问题（缺 title/titleEn/description/category）按文章内容补齐
3. 重启 dev 验证

### 症状：dev 正常但某页面 404
- 文章放错位置：`blog/` 根目录下的 `.md` 不匹配 glob（`*/*.md`），**不会渲染**。每篇文章必须在 `src/content/blog/public/<文章名>/<文章名>.md`
- status 为 `hidden`（线上不生成）/ `private`（列表隐藏）/ `draft`（列表隐藏）
- slug 与文件夹名不一致（URL = 文件夹名，中文转小写 slug）

### 症状：修改代码后 dev 报错
- Tailwind v4 / astro.config 改动后必须重启 dev（配置热更新会漏报）
- 新依赖未安装（package.json 改了但没 `npm install`）→ 先 install 再重启

## 2. 双机（Windows / Mac）git 同步

**仓库**：
- OpenLink：`D:\03-开合\OpenLink`（Win）/ `~/study/coding/OpenLink`（Mac），remote `github.com/liuzhen4242/OPenLink.git`
- Herschel（参考站）：`F:\Herschel-blog`（Win），remote `github.com/liuzhen4242/herschel-blog.git`

**日常流程**：
1. 改完 → `git add <相关文件>` + `git commit -m "..."` + `git push origin main`
2. 另一台机器 → `git pull origin main`
3. 冲突时用户原则：**本地未提交改动不必保留，以远程为准**（`git checkout -- <冲突文件>` 或 `git reset --hard origin/main`，先确认无用户新工作）

**坑**：
- 只有一台机器 push 过，另一台忘记 pull → 那台 dev 里看到的是旧内容，schema 错误也可能由此产生（远程已修，本地旧文件还在）→ **先 `git pull` 再排障**
- push 前确认 `git status`，别把无关文件（`.obsidian/`、`projects/a-info/`、调试脚本）卷进提交
- 文章内容改动只 add 对应 `.md` 文件

## 3. 沙箱 / 命令执行环境

| 场景 | 处理 |
|---|---|
| 读写仓库（`D:\03-开合\OpenLink`、`F:\Herschel-blog` 等可写目录外） | 命令带 `require_escalated` + 写明授权原因 |
| Mac 沙箱内 `curl localhost` 连不上（返回 000） | 网络隔离，`curl` 验证也需 `require_escalated` |
| Windows 沙箱内 `curl localhost` 正常 | `use_default` 即可 |
| git 写 `.git`（fetch/pull/commit/push） | 需 `require_escalated` |
| 后台启动 dev 被回收（nohup 方式） | 用后台任务方式（`run_in_background: true`），不要用 `nohup &` |
| PowerShell 读中文文件乱码 | 用 `[IO.File]::ReadAllText($p, [Text.Encoding]::UTF8)`；脚本写文件用 UTF-8（有中文时 Windows 建议带 BOM） |
| Bash for 循环遇中文/空格路径拆碎 | 用 `find -print0 | while read -r -d ''` 或 Python glob |

## 4. frontmatter 规范（用户规则）

```yaml
---
title: "中文主标题"          # 必填，中文；H1 / SEO 用
titleEn: "English Title"      # 英文标题；只给其一则自动翻译补齐
date: "YYYY-MM-DD"
description: "一句话摘要（写真实内容，勿留占位符）"
author: "zhenliu"             # 或数组 ["a","b"]；默认 zhenliu
category:
  - 分类1                     # 可多个，任意字符串
status: "public"              # public/private/hidden/draft
---
```

- 文章名（文件夹名/文件名）= 中文 title
- 旧字段 `name` 已废弃（并入 title），见到就删
- 占位符 `Article English Title` / `一句话摘要` / `文章中文标题` 必须替换为真实值
- `update`/`notes` 可选；**不要写空值**（`update:` 空行会崩 dev）
- 博客放 `blog/public/<文章名>/`，草稿放 `blog/draft/`，项目放 `projects/<项目名>/`

## 5. 历史踩坑记录（按时间）

- **深汕大塘空 `update` 致 dev 崩溃**：Windows 端停在旧 commit + 文件空 update → schema 崩 → `git pull` 同步远程修复 + 删空行
- **archiCAD `Untitled.md` 缺 title**：Obsidian 新建未命名文件没写 frontmatter → 补标准头部（title=导入CAD如何调色，titleEn 翻译）
- **Rhino 布局空文件在 `blog/` 根**：不渲染 → 移到 `public/Rhino 布局与联动2D软件/` + 补 frontmatter
- **Turtle 日志合并**：日志文章并入要点文档后删除原文；版本更新段补记录
- **批量改 frontmatter 后 title 丢失中文**：博客去 `name` 时若 title 是英文，中文名会丢 → 迁移规则：中文→`title`，英文→`titleEn`
- **Herschel 借鉴**：三栏布局（左标题树/中正文/右注释）、黑白模式、Navbar 吸顶 z-index 100、标题树点击常亮——实现参照 `F:\Herschel-blog`
