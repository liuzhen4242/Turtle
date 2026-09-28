# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import Rhino

def is_planar_surface(srf):
    """安全判断物件是否为平面（兼容 Surface / Polysurface，无效 GUID 返回 False）
    替代 rs.IsSurfacePlanar —— 后者内部 coercesurface 只能处理纯 Surface，
    遇到多重曲面或失效 GUID 会直接抛异常。"""
    obj = Rhino.RhinoDoc.ActiveDoc.Objects.Find(srf)
    if obj is None:
        return False
    geo = obj.Geometry
    if isinstance(geo, Rhino.Geometry.Brep):
        return geo.IsPlanar
    if isinstance(geo, Rhino.Geometry.Surface):
        return geo.IsPlanar
    return False

def surface_to_solid_hatch():
    # 允许选择曲面与多重曲面
    srfs = rs.GetObjects("选择要转换为填充的纯平曲面", rs.filter.surface | rs.filter.polysurface, preselect=True)
    if not srfs:
        return
    
    rs.EnableRedraw(False)
    processed_srfs = []
    
    for srf in srfs:
        # 仅处理纯平面（安全判定，不再抛异常）
        if not is_planar_surface(srf):
            continue
        
        # 获取原物件属性
        color = rs.ObjectColor(srf)
        layer = rs.ObjectLayer(srf)
        color_source = rs.ObjectColorSource(srf)
        
        # 提取表面边界线并创建 Solid 填充
        border = rs.DuplicateSurfaceBorder(srf)
        if border:
            hatch = rs.AddHatch(border, "Solid")
            if hatch:
                # 继承图层与颜色属性
                rs.ObjectLayer(hatch, layer)
                rs.ObjectColorSource(hatch, color_source)
                if color_source == 1:  # By Object
                    rs.ObjectColor(hatch, color)
            
            # 删除临时生成的边界曲线
            rs.DeleteObject(border)
            processed_srfs.append(srf)
            
    # 打组并隐藏原曲面
    if processed_srfs:
        group_name = rs.AddGroup()
        rs.AddObjectsToGroup(processed_srfs, group_name)
        rs.HideObjects(processed_srfs)
        
    rs.EnableRedraw(True)

if __name__ == "__main__":
    surface_to_solid_hatch()
