using Grasshopper.Kernel;

namespace Turtle.Grasshopper
{
    ///<summary>
    /// 确保 Grasshopper 加载时识别 Turtle 组件库。
    /// 组件注册由 GH 自动扫描本程序集中的 GH_Component 完成，
    /// 这里只负责初始化时机（需要时加逻辑即可）。
    /// </summary>
    public class TurtleAssemblyPriority : GH_AssemblyPriority
    {
        public override GH_LoadingInstruction PriorityLoad()
        {
            // 需要时在这里做组件库初始化
            return GH_LoadingInstruction.Proceed;
        }
    }
}
