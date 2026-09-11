using System;
using System.Drawing;
using Grasshopper.Kernel;

namespace Turtle.Grasshopper
{
    ///<summary>Turtle GH 组件库信息（Grasshopper 组件面板里显示的库名）。</summary>
    public class TurtleInfo : GH_AssemblyInfo
    {
        /// <summary>统一分类名。GHA 组件和释放的 ghuser 都用它，保证面板里合并成一个 turtle 标签页。</summary>
        public const string Category = "turtle";

        /// <summary>统一子分类。</summary>
        public const string SubCategory = "箭头";

        public override string Name => "Turtle";
        public override Bitmap Icon => null;
        public override string Description => "Turtle - 个人 Rhino/Grasshopper 工具集";
        public override Guid Id => new Guid("6D51A3F8-2C4E-4B9A-9E2F-1A7B0C5D8E3F");
    }
}
