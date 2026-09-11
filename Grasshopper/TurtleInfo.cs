using System;
using System.Drawing;
using Grasshopper.Kernel;

namespace Turtle.Grasshopper
{
    ///<summary>Turtle GH 组件库信息（Grasshopper 组件面板里显示的库名）。</summary>
    public class TurtleInfo : GH_AssemblyInfo
    {
        public override string Name => "Turtle";
        public override Bitmap Icon => null;
        public override string Description => "Turtle - 个人 Rhino/Grasshopper 工具集";
        public override Guid Id => new Guid("6D51A3F8-2C4E-4B9A-9E2F-1A7B0C5D8E3F");
    }
}
