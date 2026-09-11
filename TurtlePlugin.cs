using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using Rhino.PlugIns;

namespace Turtle
{
    ///<summary>Turtle 插件入口。所有命令通过 Rhino 命令行调用。</summary>
    [Guid("03AF9AC8-9667-47BF-8630-49E6B6F155D7")]
    public class TurtlePlugin : PlugIn
    {
        public static string ScriptDir { get; private set; }

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
            }
            catch (Exception ex)
            {
                errorMessage = "脚本解压失败: " + ex.Message;
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
    }
}
