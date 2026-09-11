# Turtle — Rhino 8 个人插件骨架

跨平台（Windows + Mac），C# 骨架 + 嵌入式 Python 脚本 + 工具栏。

## 目录结构

```
Turtle/
├── Turtle.sln            ← 双击用 Visual Studio 打开
├── Turtle.csproj         ← 项目文件（net7.0，跨平台）
├── TurtlePlugin.cs       ← 插件入口，负责解压嵌入的 Python 脚本
├── Commands/
│   ├── TurtleHello.cs    ← 测试命令（纯 C#，验证插件加载）
│   └── TurtleRun.cs      ← 调用 Python 脚本的命令模板
├── Scripts/
│   └── BlockTools.py      ← 示例 Python 脚本 ← 换成你自己的功能
├── Turtle.rui            ← 工具栏（两个按钮已绑好命令）
├── build.ps1              ← Windows 一键编译
└── build.command          ← Mac 双击编译
```

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
