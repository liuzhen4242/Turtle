using System;
using System.IO;
using Rhino;
using Rhino.Commands;

namespace Turtle.Commands
{
    ///<summary>调用嵌入的 Python 脚本（示例：Scripts/BlockTools.py）。</summary>
    [CommandStyle(Style.ScriptRunner)]
    public class TurtleRun : Command
    {
        public override string EnglishName => "TurtleRun";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            // 以后每个功能一个命令类，脚本名换成你自己的即可
            string script = Path.Combine(TurtlePlugin.ScriptDir, "BlockTools.py");
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
