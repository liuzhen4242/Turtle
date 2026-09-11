using System;
using System.Drawing;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Parameters;

namespace Turtle.Grasshopper
{
    ///<summary>
    /// 示例组件：输入名字，输出问候语，验证 Turtle GH 工具集工作。
    /// 复制这个类改成你自己的组件即可。
    /// </summary>
    public class TurtleHelloComponent : GH_Component
    {
        public TurtleHelloComponent()
            : base("TurtleHello", "THello", "测试 Turtle GH 工具集", "Turtle", "测试")
        {
        }

        public override Guid ComponentGuid => new Guid("B7E2C4A1-5D8F-4E6B-9A3C-2F0D1E8A4B5C");

        protected override Bitmap Icon => CreateIcon();

        public override bool IsPreviewCapable => false;

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddTextParameter("名字", "N", "要打招呼的名字", GH_ParamAccess.item);
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("问候", "G", "问候语", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            string name = "Turtle";
            DA.GetData(0, ref name);
            DA.SetData(0, "Hello, " + name + "!");
        }

        /// <summary>画一个简单的 24x24 图标（乌龟壳），后续可替换为嵌入 PNG。</summary>
        private static Bitmap CreateIcon()
        {
            var bmp = new Bitmap(24, 24);
            using (var g = Graphics.FromImage(bmp))
            {
                g.Clear(Color.Transparent);
                using (var shell = new SolidBrush(Color.FromArgb(255, 63, 141, 90)))
                {
                    g.FillEllipse(shell, 2, 6, 12, 12);   // 壳
                }
                using (var outline = new Pen(Color.FromArgb(255, 40, 96, 60), 1))
                {
                    g.DrawEllipse(outline, 2, 6, 12, 12); // 壳边
                    g.DrawLine(outline, 8, 6, 8, 18);     // 壳纹
                }
            }
            return bmp;
        }
    }
}
