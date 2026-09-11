using System.IO;
using Rhino;
using Rhino.Commands;

namespace Turtle.Commands
{
    ///<summary>
    /// 清理命令：删除插件释放到 GH 用户对象目录的 .ghuser（卸载/还原用）。
    /// 用法：在 Rhino 命令行输入 _TurtleClean。
    /// 注意：已删除的 ghuser 会在下次插件加载时重新释放（除非先卸载插件本身）。
    /// </summary>
    public class TurtleClean : Command
    {
        public override string EnglishName => "TurtleClean";

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            string path = TurtlePlugin.InstalledGhUserPath;
            if (string.IsNullOrEmpty(path) || !File.Exists(path))
            {
                RhinoApp.WriteLine("Turtle: 未找到已释放的 ghuser，无需清理。");
                return Result.Success;
            }

            try
            {
                File.Delete(path);
                RhinoApp.WriteLine("Turtle: 已删除 " + path);
                RhinoApp.WriteLine("Turtle: 提示 - 若要在 Grasshopper 面板中移除 arrows 电池，请重启 Grasshopper。");
                return Result.Success;
            }
            catch (System.Exception ex)
            {
                RhinoApp.WriteLine("Turtle: 删除失败 - " + ex.Message);
                return Result.Failure;
            }
        }
    }
}
