using Rhino.Commands;
using Rhino;
using System;
using System.IO;
using System.Reflection;
using System.Linq;

namespace Turtle
{
    /// <summary>
    /// _TurtleNew 命令：用 Turtle 模板新建场景。
    /// 释放嵌入的 Turtle.3dm 到本地缓存目录，然后打开。
    /// </summary>
    public class TurtleNewCommand : Command
    {
        public override string EnglishName => "TurtleNew";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            try
            {
                string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
                string templatesDir = Path.Combine(appData, "Turtle", "Templates");
                Directory.CreateDirectory(templatesDir);
                string templatePath = Path.Combine(templatesDir, "Turtle.3dm");

                // 如果模板不存在，从嵌入资源释放
                if (!File.Exists(templatePath))
                {
                    var asm = Assembly.GetExecutingAssembly();
                    string resName = asm.GetManifestResourceNames()
                        .FirstOrDefault(n => n.EndsWith("Turtle.3dm", StringComparison.OrdinalIgnoreCase));
                    if (resName == null)
                    {
                        RhinoApp.WriteLine("未找到 Turtle 模板文件");
                        return Result.Failure;
                    }
                    using (var stream = asm.GetManifestResourceStream(resName))
                    using (var fs = new FileStream(templatePath, FileMode.Create, FileAccess.Write))
                    {
                        stream.CopyTo(fs);
                    }
                }

                // 打开模板文件
                RhinoApp.RunScript($"_-Open \"{templatePath}\"", false);
                return Result.Success;
            }
            catch (Exception ex)
            {
                RhinoApp.WriteLine($"打开模板失败: {ex.Message}");
                return Result.Failure;
            }
        }
    }
}
