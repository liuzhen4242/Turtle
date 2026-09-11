# Turtle — Rhino 8 个人插件骨架

跨平台（Windows + Mac），C# 骨架 + 嵌入式 Python 脚本 + 工具栏 + Grasshopper 工具集（GHA 组件 + 用户对象混合）。

## 目录结构

```
Turtle/
├── Turtle.sln            ← 双击用 Visual Studio 打开
├── Turtle.csproj         ← 项目文件（net7.0，跨平台）
├── TurtlePlugin.cs       ← 插件入口：解压 Python 脚本 + 释放 GH 用户对象（带版本校验）
├── Commands/
│   ├── TurtleHello.cs    ← 测试命令（纯 C#，验证插件加载）
│   ├── TurtleRun.cs      ← 调用 Python 脚本的命令模板
│   ├── TurtleBlockToSu.cs ← 贴图轴 / exportToSu（调用 BlockToSU.py）
│   ├── TurtleOutline.cs   ← 轮廓线（调用 Outline.py）
│   └── TurtleClean.cs     ← 清理：删除释放到 GH 的 ghuser
├── Scripts/
│   ├── BlockToSU.py       ← SketchUp 导出脚本
│   └── Outline.py         ← 轮廓线脚本
├── Grasshopper/
│   ├── TurtleInfo.cs      ← GH 库信息 + 统一分类常量（Category = "Turtle"）
│   ├── TurtleHelloComponent.cs ← 示例 GH 组件（出现在 Turtle 标签页）
│   └── Arrows.ghuser      ← 用户对象（画箭头 cluster），安装时释放到 GH
├── Turtle.rui            ← 工具栏（按钮已绑好命令）
├── build.ps1              ← Windows 一键编译
└── build.command          ← Mac 双击编译
```

## Grasshopper 工具集（视觉合并方案）

插件的 GH 电池由两部分组成，**统一使用 `Category = "Turtle"`**（大写），
在 GH 面板里合并成同一个 Turtle 标签页：

| 来源 | 示例 | 分类 |
|---|---|---|
| 代码内 GH 组件（随 .rhp 加载） | TurtleHelloComponent | `Turtle`（TurtleInfo.Category 常量） |
| 释放的 ghuser 用户对象 | arrows（画箭头 cluster） | 文件内 Category 字段 = `Turtle` |

- **GHA 组件**：写在 `Grasshopper/` 下，构造时传 `TurtleInfo.Category` 即可。
- **ghuser 用户对象**：放在 `Grasshopper/Arrows.ghuser`，嵌入 .rhp。
  插件每次启动把嵌入版本释放到 GH 用户对象目录，**用 SHA-256 校验，
  内容不一致才覆盖**（插件升级后旧 ghuser 自动更新，一致则不写盘）。
- **释放位置**：`Grasshopper.Folders.DefaultUserObjectFolder`
  （Windows: `%APPDATA%\Grasshopper\UserObjects`；Mac: `~/Library/Application Support/Grasshopper/UserObjects`）。
- **保留炸开编辑**：ghuser 本质是 cluster（画箭头组件集群），
  拖进画布后右键 Explode 即可看到并修改内部电池参数——与原来方案 B 完全一致。

> 制作/修改 ghuser：在 GH 里做好 cluster 后 `File > Create User Object`，
> 属性窗口的 Category 填 `Turtle`，SubCategory 填 `箭头`，保存进 `Grasshopper/` 替换即可。
> 如需改文件内字段，可参考 `/tmp/ghapi/patch.py` 的 deflate 补丁思路。

## 卸载 / 清理

- Rhino 8 没有插件卸载回调，所以清理用命令实现：
  在 Rhino 命令行输入 **`_TurtleClean`**，删除插件释放的 ghuser。
- 注意：只要插件还在加载，下次启动会重新释放 ghuser；
  要彻底移除请先在 Plugin Manager 卸载插件，再跑 `_TurtleClean`（或手动删文件）。

## 编译

### Windows
```powershell
.uild.ps1
```

### Mac
双击 `build.command`（或终端里 `dotnet build -c Release`）

### 用 Visual Studio
打开 `Turtle.sln`，直接 F5（会自动启动 Rhino 8 调试）。

## 加载到 Rhino

1. 编译产物在 `bin/Release/net7.0/Turtle.rhp`
2. 把 **Turtle.rhp 和 Turtle.rui 放在同一文件夹**
3. 方式 A：直接把 .rhp 拖进 Rhino 窗口
4. 方式 B：Rhino 里输入 `_PluginManager` → Install

加载后在命令行输入：
- `TurtleHello` → 看到提示说明插件工作正常
- `TurtleRun` → 弹出 Python 脚本的 MessageBox
- `TurtleClean` → 清理释放的 ghuser

Grasshopper 里打开组件面板，能看到 **Turtle** 标签页：
- `TurtleHello`（代码组件）
- `Arrows`（ghuser 用户对象，可炸开编辑）

## 加载工具栏

Rhino 里输入 `_Toolbar`，找到 Turtle.rui 打开，
把 Turtle 工具栏拖到界面上即可。

## 添加新功能（四步）

1. 把 `xxx.py` 放进 `Scripts/` 文件夹（自动嵌入 .rhp）
2. 复制 `Commands/TurtleRun.cs`，改名 + 改脚本名 + 改命令名（如 `TurtleBox`）
3. 重新编译
4. 在 Turtle.rui 里加一个按钮（或在 Rhino 里 `_Toolbar` 编辑，更直观）

> 提示：脚本首次运行会解压到 `%APPDATA%\Turtle\Scripts`
> （Mac: `~/.config/Turtle/Scripts`）。已存在则跳过，
> 你可以直接编辑那里面的脚本调试，改完重启 Rhino 生效。

## 常见问题

**Q: 编译报错找不到 RhinoCommon？**
A: 确认装了 .NET 7 SDK（`dotnet --version`），且能访问 nuget.org。

**Q: Mac 上 .rhp 加载失败？**
A: 检查 csproj 里 TargetFramework 是不是 `net7.0`（不能带 `-windows`）。

**Q: 想强制还原脚本？**
A: 删掉 `%APPDATA%\Turtle\Scripts` 后重启 Rhino。

**Q: 升级插件后 ghuser 没更新？**
A: 插件启动时按 SHA-256 校验，内容不同会自动覆盖。
如果 GH 面板还显示旧电池，重启 Grasshopper（GH 启动时才扫描用户对象目录）。
