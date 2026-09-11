using Rhino;
using Rhino.Commands;

namespace Turtle.Commands
{
    ///<summary>测试命令：纯 C#，验证插件加载正常。</summary>
    public class TurtleHello : Command
    {
        public override string EnglishName => "TurtleHello";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            RhinoApp.WriteLine("Turtle 插件工作正常！Hello from Turtle.");
            return Result.Success;
        }
    }
}
