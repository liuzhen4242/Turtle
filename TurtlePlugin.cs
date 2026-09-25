using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using Rhino.PlugIns;

namespace Turtle
{
    ///<summary>Turtle 插件入口。所有命令通过 Rhino 命令行调用。</summary>
    [Guid("03AF9AC8-9667-47BF-8630-49E6B6F155D7")]
    public class TurtlePlugin : PlugIn
    {
        public static string ScriptDir { get; private set; }

        /// <summary>已释放到 GH 用户对象目录的 .ghuser 完整路径，供 _TurtleClean 删除。</summary>
        public static string InstalledGhUserPath { get; private set; }

        public TurtlePlugin()
        {
            Instance = this;
        }

        public static TurtlePlugin Instance { get; private set; }

        protected override LoadReturnCode OnLoad(ref string errorMessage)
        {
            try
            {
                ExtractEmbeddedScripts();
                ExtractTemplates();
                InstallAliases();
                InstallUserObjects();
                InstallDisplayModes();
                InstallMaterials();
                InstallToolbar();
            }
            catch (Exception ex)
            {
                errorMessage = "资源解压失败: " + ex.Message;
                return LoadReturnCode.ErrorShowDialog;
            }
            return LoadReturnCode.Success;
        }

        /// <summary>
        /// 把嵌入在 .rhp 里的 .py 脚本解压到本地缓存目录。
        /// 已存在的文件跳过 —— 方便你手动编辑脚本做调试。
        /// 想强制还原：删掉该目录后重启 Rhino。
        /// </summary>
        private static void ExtractEmbeddedScripts()
        {
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            ScriptDir = Path.Combine(appData, "Turtle", "Scripts");
            Directory.CreateDirectory(ScriptDir);

            var asm = Assembly.GetExecutingAssembly();
            string prefix = asm.GetName().Name + ".";   // 例如 "Turtle."

            foreach (string resName in asm.GetManifestResourceNames().Where(n => n.EndsWith(".py", StringComparison.OrdinalIgnoreCase)))
            {
                // "Turtle.Scripts.BlockToSU.py" -> "Scripts/BlockToSU/py"（点全变成路径分隔符）
                string rel = resName.Substring(prefix.Length).Replace('.', Path.DirectorySeparatorChar);
                // 修正扩展名：上面的 Replace 会把 ".py" 的点开锅，改回来
                rel = rel.Substring(0, rel.Length - 3) + ".py";
                // 去掉开头的 "Scripts/" 前缀，让脚本平铺在缓存目录下，
                // 命令类直接用 Path.Combine(ScriptDir, "xxx.py") 定位
                if (rel.StartsWith("Scripts" + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
                    rel = rel.Substring(("Scripts" + Path.DirectorySeparatorChar).Length);

                string path = Path.Combine(ScriptDir, rel);
                Directory.CreateDirectory(Path.GetDirectoryName(path));

                if (File.Exists(path))
                    continue;   // 保留用户本地修改

                using (Stream stream = asm.GetManifestResourceStream(resName))
                using (FileStream fs = new FileStream(path, FileMode.Create, FileAccess.Write))
                {
                    stream.CopyTo(fs);
                }
            }
        }

        /// <summary>
        /// 把嵌入的 Turtle 模板 3dm 释放到 Rhino 的模板目录（中英文都放），
        /// 新建文件时就能在模板列表里选 Turtle.3dm。
        /// </summary>
        private static void ExtractTemplates()
        {
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);

            // 中英文两个语言目录都放
            string[] locales = { "en-US", "zh-CN" };
            var destDirs = locales.Select(locale => Path.Combine(appData, "McNeel", "Rhinoceros", "8.0",
                "Localization", locale, "Template Files")).ToArray();
            foreach (var dir in destDirs)
                Directory.CreateDirectory(dir);

            var asm = Assembly.GetExecutingAssembly();
            string resName = asm.GetManifestResourceNames()
                .FirstOrDefault(n => n.EndsWith("Turtle.3dm", StringComparison.OrdinalIgnoreCase));
            if (resName == null)
                return;

            byte[] embedded;
            using (var stream = asm.GetManifestResourceStream(resName))
            using (var ms = new MemoryStream())
            {
                stream.CopyTo(ms);
                embedded = ms.ToArray();
            }

            foreach (var destDir in destDirs)
            {
                string dest = Path.Combine(destDir, "Turtle.3dm");
                if (File.Exists(dest) && HashEquals(File.ReadAllBytes(dest), embedded))
                    continue;
                File.WriteAllBytes(dest, embedded);
            }
        }

        /// <summary>
        /// 把嵌入的命令别名表（KeyTurtle.txt）逐条注册到 Rhino 的别名系统。
        /// 别名表每行格式："别名 宏"（Rhino 选项 > 别名 页面的导出格式）。
        /// 关键点：
        /// 1. KeyTurtle.txt 里的 "别名" 是命令别名（CommandAliasList），不是键盘快捷键
        ///    （ShortcutKeySettings 只支持 Ctrl+字母/F键 等固定组合，装不下 ZE/ZEA/ttc 这类多字符别名）；
        /// 2. 别名宏里的 {RHINO_SCRIPTS} 占位符在注册时替换为脚本缓存目录
        ///    （%AppData%\Turtle\Scripts），使 ttc/wa/NewAlias/stop 等脚本别名开箱即用；
        /// 3. 幂等：已存在且宏相同的别名跳过，宏不同的覆盖（插件升级后自动对齐），
        ///    不重复添加。
        /// </summary>
        private static void InstallAliases()
        {
            var asm = Assembly.GetExecutingAssembly();
            string resName = asm.GetManifestResourceNames()
                .FirstOrDefault(n => n.EndsWith("KeyTurtle.txt", StringComparison.OrdinalIgnoreCase));
            if (resName == null)
                return;

            string content;
            using (var stream = asm.GetManifestResourceStream(resName))
            using (var reader = new StreamReader(stream))
                content = reader.ReadToEnd();

            int added = 0, updated = 0, skipped = 0;
            foreach (string rawLine in content.Split(new[] { "\r\n", "\n" }, StringSplitOptions.None))
            {
                string line = rawLine.Trim();
                if (line.Length == 0)
                    continue;

                int sp = line.IndexOf(' ');
                if (sp <= 0 || sp == line.Length - 1)
                    continue;   // 无别名或无宏的异常行，跳过

                string alias = line.Substring(0, sp).Trim();
                string macro = line.Substring(sp + 1).Trim();
                macro = macro.Replace("{RHINO_SCRIPTS}", ScriptDir);

                try
                {
                    if (global::Rhino.ApplicationSettings.CommandAliasList.IsAlias(alias))
                    {
                        string existing = global::Rhino.ApplicationSettings.CommandAliasList.GetMacro(alias);
                        if (existing == macro)
                        {
                            skipped++;
                            continue;
                        }
                        global::Rhino.ApplicationSettings.CommandAliasList.SetMacro(alias, macro);
                        updated++;
                    }
                    else
                    {
                        global::Rhino.ApplicationSettings.CommandAliasList.Add(alias, macro);
                        added++;
                    }
                }
                catch
                {
                    // 单条别名注册失败不阻断整体，继续注册其余条目
                }
            }
        }

        /// <summary>
        /// 加载 Turtle.rui 工具栏文件，使工具列出现在 Rhino 界面。
        /// 关键点：
        /// 1. yak 安装只负责把 .rui 放进包目录，不会自动加载；
        ///    拖拽安装时 .rui 与 .rhp 同目录。这里按两种部署形态定位 rui：
        ///    - 拖拽/调试：rui 在 rhp 同目录（bin\Release\net7.0\Turtle.rui）
        ///    - yak 安装：rui 在包目录（%AppData%\McNeel\Rhinoceros\8.0\Packages\Turtle\<version>\Turtle.rui）
        /// 2. 用 RhinoApp.ToolbarFiles.Open() 打开 rui，已打开则跳过（幂等）；
        /// 3. 打开后把 rui 内的工具栏组设为可见（首次打开时组默认可能收起）。
        /// </summary>
        private static void InstallToolbar()
        {
            try
            {
                // 1) 定位 rui：先看 rhp 同目录（拖拽安装 / bin 调试），再看 yak 包目录
                string rhpDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
                string ruiPath = rhpDir != null ? Path.Combine(rhpDir, "Turtle.rui") : null;
                if (ruiPath == null || !File.Exists(ruiPath))
                    ruiPath = FindYakRuiPath();
                if (ruiPath == null || !File.Exists(ruiPath))
                    return;   // 找不到 rui，静默跳过（不阻断插件加载）

                // 2) 幂等打开：已打开则不动
                var toolbars = Rhino.RhinoApp.ToolbarFiles;
                bool alreadyOpen = false;
                for (int i = 0; i < toolbars.Count; i++)
                {
                    if (string.Equals(toolbars[i].Path, ruiPath, StringComparison.OrdinalIgnoreCase))
                    {
                        alreadyOpen = true;
                        break;
                    }
                }
                if (!alreadyOpen)
                    toolbars.Open(ruiPath);

                // 3) 找到同名工具栏组并设为可见（首次加载默认可能不显示）
                for (int i = 0; i < toolbars.Count; i++)
                {
                    var tf = toolbars[i];
                    if (!string.Equals(tf.Path, ruiPath, StringComparison.OrdinalIgnoreCase))
                        continue;
                    for (int g = 0; g < tf.GroupCount; g++)
                    {
                        var group = tf.GetGroup(g);
                        if (group != null && group.Name.IndexOf("Turtle", StringComparison.OrdinalIgnoreCase) >= 0)
                            group.Visible = true;
                    }
                }
            }
            catch
            {
                // 工具栏加载失败不影响插件主体功能
            }
        }

        /// <summary>
        /// 把嵌入的自定义显示模式 ini（Resources/DisplayStyles/*.ini）导入 Rhino。
        /// 流程：先释放到 %AppData%\Turtle\DisplayStyles\，再调用
        /// DisplayModeDescription.ImportFromFile() 导入到 Rhino 显示模式系统，
        /// 使 Arctic / OutLine / Shaded 等显示模式出现在视图面板下拉列表。
        /// 版本校验：SHA-256 不一致才重新导入，避免每次启动重复操作。
        /// </summary>
        private static void InstallDisplayModes()
        {
            var asm = Assembly.GetExecutingAssembly();
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            string destDir = Path.Combine(appData, "Turtle", "DisplayStyles");
            Directory.CreateDirectory(destDir);

            foreach (string resName in asm.GetManifestResourceNames()
                .Where(n => n.EndsWith(".ini", StringComparison.OrdinalIgnoreCase)))
            {
                int lastDot = resName.LastIndexOf('.');
                int prevDot = resName.LastIndexOf('.', lastDot - 1);
                string fileName = resName.Substring(prevDot + 1);

                byte[] embedded;
                using (var stream = asm.GetManifestResourceStream(resName))
                using (var ms = new MemoryStream())
                {
                    stream.CopyTo(ms);
                    embedded = ms.ToArray();
                }

                string dest = Path.Combine(destDir, fileName);
                // 文件不存在或内容变了才重新写入
                if (!File.Exists(dest) || !HashEquals(File.ReadAllBytes(dest), embedded))
                    File.WriteAllBytes(dest, embedded);

                // 每次启动都导入（幂等），确保即使第一次导入失败的文件也能重试
                try
                {
#if NET48
                    // RhinoCommon 8.7 只有单参数 ImportFromFile（已存在同名模式时会弹"是否替换"对话框）。
                    // 先按模式名判断是否已存在：已存在就跳过，避免打扰用户。
                    string modeName = GetDisplayModeNameFromIni(dest);
                    if (!string.IsNullOrEmpty(modeName) &&
                        global::Rhino.Display.DisplayModeDescription.FindByName(modeName) != null)
                        continue;
                    global::Rhino.Display.DisplayModeDescription.ImportFromFile(dest);
#else
                    global::Rhino.Display.DisplayModeDescription.ImportFromFile(dest, false);
#endif
                }
                catch
                {
                    // 导入失败不影响插件主体功能
                }
            }
        }

        /// <summary>从 Windows 风格显示模式 ini 文件里解析出 Name= 字段（用于 8.7 判断模式是否已存在）。</summary>
        private static string GetDisplayModeNameFromIni(string iniPath)
        {
            try
            {
                string text = File.ReadAllText(iniPath, System.Text.Encoding.Unicode);
                if (text.IndexOf("Name=", StringComparison.OrdinalIgnoreCase) < 0)
                    text = File.ReadAllText(iniPath, System.Text.Encoding.UTF8);
                string line = text.Split('\n')
                    .Select(l => l.Trim())
                    .FirstOrDefault(l => l.StartsWith("Name=", StringComparison.OrdinalIgnoreCase));
                return line?.Substring("Name=".Length).Trim();
            }
            catch
            {
                return null;
            }
        }

        /// <summary>
        /// 把嵌入的材质库文件（Resources/Materials/*.rmtl）释放到 Rhino 的
        /// Render Content 目录下的 Turtle 子目录（和 Architectural/Metal/Wood 等官方分类平级），
        /// 使材质出现在 Rhino 材质编辑器的 Turtle 分类下。
        /// 中英文两个目录都放（en-US + zh-CN），不管用户 Rhino 用什么语言都能识别。
        /// 版本校验：SHA-256 不一致才覆盖，避免每次启动无谓写盘。
        /// </summary>
        private static void InstallMaterials()
        {
            var asm = Assembly.GetExecutingAssembly();
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);

            // 中英文两个语言目录都放
            string[] locales = { "en-US", "zh-CN" };
            var destDirs = locales.Select(locale => Path.Combine(appData, "McNeel", "Rhinoceros", "8.0",
                "Localization", locale, "Render Content", "Turtle")).ToArray();
            foreach (var dir in destDirs)
                Directory.CreateDirectory(dir);

            foreach (string resName in asm.GetManifestResourceNames()
                .Where(n => n.EndsWith(".rmtl", StringComparison.OrdinalIgnoreCase)))
            {
                int lastDot = resName.LastIndexOf('.');
                int prevDot = resName.LastIndexOf('.', lastDot - 1);
                string fileName = resName.Substring(prevDot + 1);

                byte[] embedded;
                using (var stream = asm.GetManifestResourceStream(resName))
                using (var ms = new MemoryStream())
                {
                    stream.CopyTo(ms);
                    embedded = ms.ToArray();
                }

                foreach (var destDir in destDirs)
                {
                    string dest = Path.Combine(destDir, fileName);
                    if (File.Exists(dest) && HashEquals(File.ReadAllBytes(dest), embedded))
                        continue;
                    File.WriteAllBytes(dest, embedded);
                }
            }
        }

        /// <summary>在 yak 包安装目录下查找 Turtle.rui。
        /// yak 的实际安装路径：%APPDATA%\McNeel\Rhinoceros\packages\8.0\Turtle\<version>\（注意是 packages\8.0，不是 Rhinoceros\8.0\Packages）。</summary>
        private static string FindYakRuiPath()
        {
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            string yakRoot = Path.Combine(appData, "McNeel", "Rhinoceros", "packages", "8.0", "Turtle");
            if (!Directory.Exists(yakRoot))
                return null;
            var found = Directory.GetFiles(yakRoot, "Turtle.rui", SearchOption.AllDirectories)
                .FirstOrDefault();
            return found;
        }

        /// <summary>
        /// 把嵌入的 GH 用户对象（.ghuser）释放到 Grasshopper 的用户对象目录，
        /// 使 arrows 电池出现在 GH 面板的 turtle 分类下（与 GHA 组件合并成同一标签页）。
        /// 版本校验：用 SHA-256 对比嵌入资源与已安装文件，内容不一致才覆盖（插件升级后自动更新）。
        /// 已存在且一致的旧文件不触碰，避免每次启动无谓写盘。
        /// </summary>
        private static void InstallUserObjects()
        {
            var asm = Assembly.GetExecutingAssembly();
            string resName = asm.GetManifestResourceNames()
                .FirstOrDefault(n => n.EndsWith(".ghuser", StringComparison.OrdinalIgnoreCase));
            if (resName == null)
                return;

            byte[] embedded;
            using (var stream = asm.GetManifestResourceStream(resName))
            using (var ms = new MemoryStream())
            {
                stream.CopyTo(ms);
                embedded = ms.ToArray();
            }

            string ghDir;
            try
            {
                ghDir = global::Grasshopper.Folders.DefaultUserObjectFolder;
            }
            catch
            {
                // 退化：按平台找标准 GH 用户对象目录
                string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
                ghDir = Path.Combine(appData, "Grasshopper", "UserObjects");
            }
            Directory.CreateDirectory(ghDir);

            string dest = Path.Combine(ghDir, "Arrows.ghuser");   // 固定目标名，与 GH 面板显示名 arrows 对应
            InstalledGhUserPath = dest;

            // 版本校验：哈希不同才覆盖
            if (File.Exists(dest) && HashEquals(File.ReadAllBytes(dest), embedded))
                return;   // 已是最新，不动

            File.WriteAllBytes(dest, embedded);
        }

        private static bool HashEquals(byte[] a, byte[] b)
        {
            using (var sha = SHA256.Create())
            {
                byte[] ha = sha.ComputeHash(a);
                byte[] hb = sha.ComputeHash(b);
                return ha.SequenceEqual(hb);
            }
        }
    }
}
