# -*- coding: utf-8 -*-
import Rhino
import scriptcontext as sc
import rhinoscriptsyntax as rs
import math
def orient_detail_scale_input():
    page_view = sc.doc.Views.ActiveView
    if not isinstance(page_view, Rhino.Display.RhinoPageView):
        print("请在 Layout 布局页面中运行！")
        return
    detail_id = rs.GetObject("1. 选中视口外框 (蓝框)", rs.filter.detail)
    if not detail_id:
        return
    if not isinstance(sc.doc.Objects.FindId(detail_id), Rhino.DocObjects.DetailViewObject):
        print("选中的对象不是 DetailView！")
        return
    p_b1 = rs.GetPoint("2. 捕捉蓝框第 1 点 (蓝 1)")
    if not p_b1: return
    p_b2 = rs.GetPoint("3. 捕捉蓝框第 2 点 (蓝 2，只用于确定方向)", p_b1)
    if not p_b2: return
    page_view.SetActiveDetail(detail_id)
    p_r1 = rs.GetPoint("4. 捕捉模型红框第 1 点 (红 1)")
    p_r2 = rs.GetPoint("5. 捕捉模型红框第 2 点 (红 2，只用于确定方向)", p_r1) if p_r1 else None
    page_view.SetPageAsActive()
    if not p_r1 or not p_r2:
        return
    # 默认值 = 由两点距离推算的比例，回车即等同上一版
    page_len = math.hypot(p_b2.X - p_b1.X, p_b2.Y - p_b1.Y)
    model_len = math.hypot(p_r2.X - p_r1.X, p_r2.Y - p_r1.Y)
    if page_len < 1e-9 or model_len < 1e-9:
        print("两点距离为 0，无法计算")
        return
    default_k = round(model_len / page_len, 2)
    k = rs.GetReal("6. 输入比例分母 (1:300 输入 300，回车采用两点推算值)", default_k, 0.0001)
    if not k or k <= 0:
        return
    # 解锁
    obj = sc.doc.Objects.FindId(detail_id)
    obj.DetailGeometry.IsProjectionLocked = False
    obj.CommitChanges()
    obj = sc.doc.Objects.FindId(detail_id)
    # 旋转
    ang_b = math.atan2(p_b2.Y - p_b1.Y, p_b2.X - p_b1.X)
    ang_r = math.atan2(p_r2.Y - p_r1.Y, p_r2.X - p_r1.X)
    d = ang_b - ang_r
    ex = Rhino.Geometry.Vector3d(math.cos(d), -math.sin(d), 0)
    ey = Rhino.Geometry.Vector3d(math.sin(d),  math.cos(d), 0)
    bb = obj.Geometry.GetBoundingBox(True)
    pw = bb.Max.X - bb.Min.X
    c = bb.Center
    # 1) 先设相机：红1 落在蓝1 位置
    off = (ex * (p_b1.X - c.X) + ey * (p_b1.Y - c.Y)) * k
    target = Rhino.Geometry.Point3d(p_r1.X - off.X, p_r1.Y - off.Y, 0.0)
    vp = obj.Viewport
    vp.ChangeToParallelProjection(True)
    vp.SetCameraLocations(target, Rhino.Geometry.Point3d(target.X, target.Y, 10000.0))
    vp.CameraUp = ey
    obj.CommitViewportChanges()
    # 2) 最后设比例
    obj = sc.doc.Objects.FindId(detail_id)
    obj.DetailGeometry.SetScale(k, sc.doc.ModelUnitSystem, 1.0, sc.doc.PageUnitSystem)
    obj.CommitChanges()
    obj = sc.doc.Objects.FindId(detail_id)
    obj.DetailGeometry.IsProjectionLocked = True
    obj.CommitChanges()
    sc.doc.Views.Redraw()
    # 红2 在图纸上离蓝1 的距离（沿蓝1-2方向）
    r2_page_dist = model_len / k
    print("完成：比例 1:{:.2f}，旋转 {:.3f}°".format(k, math.degrees(d)))
    print("红2 落在蓝1-2 直线上，距蓝1 {:.2f}（蓝1-2 全长 {:.2f}）".format(r2_page_dist, page_len))
if __name__ == "__main__":
    orient_detail_scale_input()