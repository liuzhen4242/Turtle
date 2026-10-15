# -*- coding: utf-8 -*-
import math
import Rhino
import rhinoscriptsyntax as rs

def billboard_to_camera():
    # 1. 获取当前活动视口及相机方向
    view = Rhino.RhinoDoc.ActiveDoc.Views.ActiveView
    if not view:
        return
    vp = view.ActiveViewport
    
    # 获取从目标到相机的视线方向（平行投影或透视均适用）
    cam_dir = vp.CameraDirection
    # 我们希望物件正面逆着视线（即朝向相机），在水平面上的投影向量
    # 物件朝向相机的水平向量为 -cam_dir (只取 X, Y)
    target_dir = Rhino.Geometry.Vector3d(-cam_dir.X, -cam_dir.Y, 0)
    if not target_dir.Unitize():
        return

    # 2. 提示用户选择需要对齐的单面物件（曲面或网格）
    obj_ids = rs.GetObjects("选择要面向相机的单面面片/物件", filter=rs.filter.surface | rs.filter.mesh, preselect=True)
    if not obj_ids:
        return

    rs.EnableRedraw(False)

    for obj_id in obj_ids:
        # 获取几何中心作为旋转支点
        bbox = rs.BoundingBox(obj_id)
        if not bbox:
            continue
        center = (bbox[0] + bbox[6]) * 0.5
        center_pt = Rhino.Geometry.Point3d(center.X, center.Y, center.Z)

        # 获取当前面片的法线方向（在 XY 平面投影）
        current_normal = None
        if rs.IsSurface(obj_id):
            u_domain = rs.SurfaceDomain(obj_id, 0)
            v_domain = rs.SurfaceDomain(obj_id, 1)
            u_mid = (u_domain[0] + u_domain[1]) * 0.5
            v_mid = (v_domain[0] + v_domain[1]) * 0.5
            normal_vec = rs.SurfaceNormal(obj_id, (u_mid, v_mid))
            current_normal = Rhino.Geometry.Vector3d(normal_vec[0], normal_vec[1], 0)
        elif rs.IsMesh(obj_id):
            mesh_geom = rs.coercemesh(obj_id)
            mesh_geom.FaceNormals.ComputeFaceNormals()
            if mesh_geom.FaceNormals.Count > 0:
                fn = mesh_geom.FaceNormals[0]
                current_normal = Rhino.Geometry.Vector3d(fn.X, fn.Y, 0)

        # 如果法线无效（例如水平面），默认按 Y 轴正向作为参考
        if not current_normal or not current_normal.Unitize():
            current_normal = Rhino.Geometry.Vector3d(0, 1, 0)

        # 计算当前朝向与目标朝向之间的夹角 (围绕 Z 轴)
        angle = Rhino.Geometry.Vector3d.VectorAngle(current_normal, target_dir)
        cross_z = Rhino.Geometry.Vector3d.CrossProduct(current_normal, target_dir).Z
        if cross_z < 0:
            angle = -angle

        # 围绕中心点与垂直 Z 轴旋转
        angle_deg = math.degrees(angle)
        rs.RotateObject(obj_id, center, angle_deg, axis=[0, 0, 1])

    rs.EnableRedraw(True)
    print("已对齐 {} 个物件至相机视角。".format(len(obj_ids)))

if __name__ == "__main__":
    billboard_to_camera()