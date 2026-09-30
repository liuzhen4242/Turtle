---
name: openlink-blog-sync
description: OpenLink 博客（Astro，双机 Windows/Mac 协作）的日常维护与同步：git 提交推送、跨机拉取同步、frontmatter 检查与自动修复、博客文章标题中英文补齐、dev 服务器启动与崩溃排障。当用户要求"同步/提交博客""git 上去/推上去""检查/统一文章 frontmatter 或标题""dev 打不开/挂了/启动""文章格式不一致"以及涉及 OpenLink 或 Herschel 博客仓库操作时使用。
---

# OpenLink 博客同步与维护

## 仓库信息

| 项目 | Windows | Mac | 远程 |
|---|---|---|---|
| OpenLink | `D:\03-开合\OpenLink` | `~/study/coding/OpenLink` | `github.com/liuzhen4242/OPenLink.git` |
| Herschel（参考站） | `F:\Herschel-blog` | - | `github.com/liuzhen4242/herschel-blog.git` |

- 博客文章：`src/content/blog/public/<文章名>/<文章名>.md`；草稿：`src/content/blog/draft/`；项目：`src/content/projects/<项目名>/`
- schema：`src/content.config.ts`；写作指南：博客内《OpenLink 博客写作指南》

## 1. git 同步流程

双机协作：在哪台改，就在哪台 push；另一台 pull。

```
git status                     # 先看改动，避免卷入无关文件
git add <本次相关的文件>        # 只 add 文章/代码改动；跳过 .obsidian/、a-info/、调试脚本
git commit -m "feat: ..."
git push origin main
# 另一台机器：
git pull origin main
```

- 冲突时按用户原则：**本地未提交改动不保留，以远程为准**（先确认非用户新工作，再 `git checkout -- <文件>` 或 `git reset --hard origin/main`）
- 推送前确认 `origin/main` 最新（`git fetch` + 对比），避免旧机器覆盖新内容

## 2. frontmatter 检查与修复

规范（用户规则）：`title` 中文主标题、`titleEn` 英文、`date`、`description`、`category`、`status`；旧字段 `name` 已废弃；占位符（`Article English Title`/`一句话摘要`/`文章中文标题`）必须替换；**空值 `update:` 会崩 dev**。

运行检查脚本（跨平台）：

```bash
python <skill目录>/scripts/check_frontmatter.py <仓库根目录>        # 只检查
python <skill目录>/scripts/check_frontmatter.py <仓库根目录> --fix   # 自动修复确定性项
```

- `--fix` 自动删除 `name` 行与空 `update` 行
- 剩余问题（缺 title/titleEn/description/category、占位符）由 AI 依据文章内容补齐：
  - 只有中文名 → 补 `titleEn` 英文翻译
  - 只有英文名 → 补 `title` 中文翻译
  - 缺 description → 从正文首段概括一句话
  - 缺 category → 按文章主题给合理分类（设计/工厂/Rhino/博客/AI/archiCAD…）

## 3. dev 启动

```bash
# Windows (PowerShell)：Set-Location 到仓库后
npx astro dev --port 4321 --host 127.0.0.1
# Mac (bash)：cd 到仓库后
npx astro dev --port 4321 --host 127.0.0.1
```

- 用后台任务方式启动（`run_in_background`），不要 `nohup &`（会被回收）
- 启动后 `curl http://127.0.0.1:4321/` 验证（Mac 沙箱内 curl 需提权；Windows 直接可）
- **dev 启动失败 → 先看报错是否 `InvalidContentEntryDataError`**：这是某篇 .md frontmatter 不合 schema，用 check_frontmatter.py 定位修复，再重启

## 4. 常见问题速查

详见 `references/troubleshooting.md`，重点：

1. **dev 崩**：frontmatter 不合 schema（缺 title / 空 update / 占位符）→ 检查脚本修复
2. **双机不同步**：另一台旧 commit + 旧文件 → 先 `git pull` 再排障
3. **404**：文章放错位置（`blog/` 根目录不渲染）/ status 非 public / slug 不符
4. **沙箱限制**：读写仓库、git 写 .git、Mac curl localhost 都要提权；后台任务防回收
5. **编码**：PowerShell 中文读写用 UTF-8（BOM）；Bash 中文路径用 `find -print0`/Python

## 5. Herschel 借鉴（布局/排版）

- 参考站 `F:\Herschel-blog` 的三栏布局（左标题树/中正文/右注释）、黑白模式切换、Navbar 吸顶（z-index 100）、标题树点击常亮、上下篇
- 借鉴时保持 OpenLink 自己的字体与现有功能（相册轮播、图片点击缩放等）
