# -*- coding: utf-8 -*-
import Rhino
import scriptcontext as sc
import rhinoscriptsyntax as rs
KEY = "orient_k"
def get_detail(did):
    return sc.doc.Objects.FindId(did)
def align_one(did, r1, k):
    # 解锁
    obj = get_detail(did)
    obj.DetailGeometry.IsProjectionLocked = False
    obj.CommitChanges()
    obj = get_detail(did)
    # 蓝 1 = 视口左上角，每张图各自计算
    bb = obj.Geometry.GetBoundingBox(True)
    b1x, b1y = bb.Min.X, bb.Max.Y
    c = bb.Center
    # 不旋转：相机中心 = 红1 - (蓝1 - 视口中心) * k
    tx = r1.X - (b1x - c.X) * k
    ty = r1.Y - (b1y - c.Y) * k
    target = Rhino.Geometry.Point3d(tx, ty, 0.0)
    vp = obj.Viewport
    vp.ChangeToParallelProjection(True)
    vp.SetCameraLocations(target, Rhino.Geometry.Point3d(tx, ty, 10000.0))
    vp.CameraUp = Rhino.Geometry.Vector3d(0, 1, 0)
    obj.CommitViewportChanges()
    # 最后设比例
    obj = get_detail(did)
    obj.DetailGeometry.SetScale(k, sc.doc.ModelUnitSystem, 1.0, sc.doc.PageUnitSystem)
    obj.CommitChanges()
    obj = get_detail(did)
    obj.DetailGeometry.IsProjectionLocked = True
    obj.CommitChanges()
def get_scale():
    """继承上一次比例；第一次运行时才询问一次。"""
    k = sc.sticky.get(KEY)
    if k is None:
        k = rs.GetReal("首次使用，请输入比例分母 (1:300 输入 300)", 300.0, 0.0001)
        if not k:
            return None
        sc.sticky[KEY] = k
    return k
def align_top_left():
    pv = sc.doc.Views.ActiveView
    if not isinstance(pv, Rhino.Display.RhinoPageView):
        print("请在 Layout 布局页面中运行！")
        return
    k = get_scale()
    if not k:
        return
    # 选视口；命令行可输入 "改比例" 重新设定
    go = Rhino.Input.Custom.GetObject()
    go.SetCommandPrompt("选择视口 (当前比例 1:{:g}，可选[改比例])".format(k))
    go.GeometryFilter = Rhino.DocObjects.ObjectType.Detail
    go.EnablePreSelect(True, True)
    opt_idx = go.AddOption("改比例")
    go.GetMultiple(1, 0)
    while go.CommandResult() == Rhino.Commands.Result.Success and go.Result() == Rhino.Input.GetResult.Option:
        if go.OptionIndex() == opt_idx:
            newk = rs.GetReal("新的比例分母", k, 0.0001)
            if newk:
                k = newk
                sc.sticky[KEY] = k
        go.SetCommandPrompt("选择视口 (当前比例 1:{:g}，可选[改比例])".format(k))
        go.GetMultiple(1, 0)
    if go.CommandResult() != Rhino.Commands.Result.Success or go.Result() != Rhino.Input.GetResult.Object:
        return
    dids = [go.Object(i).ObjectId for i in range(go.ObjectCount)]
    n = 0
    for did in dids:
        pv.SetActiveDetail(did)
        r1 = rs.GetPoint("在视口内点【红框左上角】(红 1)")
        pv.SetPageAsActive()
        if not r1:
            continue
        align_one(did, r1, k)
        n += 1
    sc.doc.Views.Redraw()
    print("已对齐 {} 个视口，比例 1:{:g}".format(n, k))
if __name__ == "__main__":
    align_top_left()