# -*- coding: utf-8 -*-
import Rhino
import rhinoscriptsyntax as rs

def sync_width_with_scale():
    doc = Rhino.RhinoDoc.ActiveDoc
    BASE_FACTOR = 0.14  # 基准系数 (5.0px -> 0.7mm)

    # 命令行输入缩放比
    scale = rs.GetReal("输入线宽缩放比例 (输入 0 恢复 Default，1 恢复标准，>1 按比例加粗)", 1.0, 0.0)
    if scale is None:
        return

    # 1. 图层处理
    for layer in doc.Layers:
        if layer.IsDeleted or layer.LinetypeIndex < 0:
            continue
        lt = doc.Linetypes[layer.LinetypeIndex]
        if lt and lt.Width > 0:
            if scale == 0:
                layer.PlotWeight = 0.0  # 恢复 Default
            else:
                layer.PlotWeight = round(lt.Width * BASE_FACTOR * scale, 2)

    # 2. 物件处理（仅针对物件级别设置了线型的物体）
    for obj in doc.Objects:
        if obj.IsDeleted:
            continue
        attr = obj.Attributes
        if attr.LinetypeSource == Rhino.DocObjects.ObjectLinetypeSource.LinetypeFromObject:
            lt = doc.Linetypes[attr.LinetypeIndex]
            if lt and lt.Width > 0:
                new_attr = attr.Duplicate()
                if scale == 0:
                    new_attr.PlotWeightSource = Rhino.DocObjects.ObjectPlotWeightSource.PlotWeightFromLayer
                    new_attr.PlotWeight = 0.0
                else:
                    new_attr.PlotWeightSource = Rhino.DocObjects.ObjectPlotWeightSource.PlotWeightFromObject
                    new_attr.PlotWeight = round(lt.Width * BASE_FACTOR * scale, 2)
                doc.Objects.ModifyAttributes(obj, new_attr, True)

    doc.Views.Redraw()

if __name__ == "__main__":
    sync_width_with_scale()