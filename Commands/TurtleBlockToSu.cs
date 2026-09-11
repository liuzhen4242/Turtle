using System;
using System.IO;
using Rhino;
using Rhino.Commands;

namespace Turtle.Commands
{
    ///<summary>调用嵌入的 Python 脚本 Scripts/BlockToSU.py（嵌套组转 Block 并导出 SketchUp）。</summary>
    [CommandStyle(Style.ScriptRunner)]
    public class TurtleBlockToSu : Command
    {
        public override string EnglishName => "TurtleBlockToSu";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            string script = Path.Combine(TurtlePlugin.ScriptDir, "BlockToSU.py");
            if (!File.Exists(script))
            {
                RhinoApp.WriteLine("找不到脚本: " + script);
                return Result.Failure;
            }

            // 通过 Rhino 命令行调用 Python 解释器执行脚本
            bool ok = RhinoApp.RunScript($"-RunPythonScript \"{script}\"", echo: false);
            return ok ? Result.Success : Result.Failure;
        }
    }
}
