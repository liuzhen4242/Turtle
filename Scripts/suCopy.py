# -*- coding: utf-8 -*-
import os
import time
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino

DIR  = os.path.join(os.path.expanduser("~"), "su_rhino_bridge")
path = os.path.join(DIR, "clip.skp")
meta = os.path.join(DIR, "clip.txt")

def fmt_age(sec):
    if sec < 60:
        return "{} 秒前".format(int(sec))
    if sec < 3600:
        return "{} 分钟前".format(int(sec // 60))
    return "{} 小时前".format(int(sec // 3600))

def main():
    if not os.path.exists(path):
        print("没有找到文件：" + path)
        return
    if not os.path.exists(meta):
        print("没有找到基点信息，请重启 SU 并重新复制（需要更新后的插件）")
        return

    print("剪贴板内容复制于 " + fmt_age(time.time() - os.path.getmtime(path)))
    ox, oy, oz, su_diag = [float(v) for v in open(meta).read().split()]

    before = set(rs.AllObjects() or [])
    rs.EnableRedraw(False)
    rs.Command('-_Import "{}" _Enter'.format(path), False)
    new_objs = [o for o in (rs.AllObjects() or []) if o not in before]
    rs.EnableRedraw(True)

    if not new_objs:
        print("没有导入新物件（可能取消了导入选项对话框）")
        return

    # 量出导入物件的实际包围盒，反推 SU 基点现在在哪
    box = rs.BoundingBox(new_objs)
    p_min, p_max = box[0], box[6]
    rh_diag = rs.Distance(p_min, p_max)
    if su_diag > 1e-9 and rh_diag > 1e-9:
        s = rh_diag / su_diag          # SU 英寸 -> Rhino 当前单位
    else:
        s = Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Inches, sc.doc.ModelUnitSystem)

    base = Rhino.Geometry.Point3d(p_min[0] - ox * s,
                                  p_min[1] - oy * s,
                                  p_min[2] - oz * s)

    # 动态预览：物件跟着光标走，不画任何连线
    objs = [sc.doc.Objects.FindId(g) for g in new_objs]
    gp = Rhino.Input.Custom.GetPoint()
    gp.SetCommandPrompt("指定粘贴点（基点对齐到这里）")
    gp.SetBasePoint(base, False)
    # 不调用 DrawLineFromPoint，所以没有橡皮筋连线

    def dyn(sender, e):
        xf = Rhino.Geometry.Transform.Translation(e.CurrentPoint - base)
        for o in objs:
            e.Display.DrawObject(o, xf)
    gp.DynamicDraw += dyn

    rs.UnselectAllObjects()
    rs.SelectObjects(new_objs)
    result = gp.Get()
    if result != Rhino.Input.GetResult.Point:
        rs.DeleteObjects(new_objs)
        print("已取消粘贴")
        return

    pt = gp.Point()
    rs.MoveObjects(new_objs, pt - base)
    sc.doc.Views.Redraw()
    print("已粘贴 {} 个物件".format(len(new_objs)))

main()