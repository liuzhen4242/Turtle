# -*- coding: utf-8 -*-
"""
Rhino 脚本：选中一个物体，改它的材质颜色，所有同材质物体一起变
用法：
  1. 选中一个物体
  2. 运行本脚本
  3. 弹出颜色选择器，选新颜色，点确定
  4. 所有和这个物体共用同一条材质的物体全部更新
"""
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino


def change_material_color():
    # 让用户选一个物体
    obj_id = rs.GetObject("选择一个要改颜色的物体", preselect=True)
    if obj_id is None:
        return

    rhobj = rs.coercerhinoobject(obj_id)
    doc = sc.doc

    # 取这个物体的材质索引
    attr = rhobj.Attributes
    if attr.MaterialSource != Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject:
        print("这个物体的材质不是'来自对象'，无法修改。")
        print("请先运行 ColorToSharedMaterial.py 把颜色转成材质。")
        return

    mat_idx = attr.MaterialIndex
    if mat_idx < 0 or mat_idx >= doc.Materials.Count:
        print("物体没有绑定有效材质。")
        return

    mat = doc.Materials[mat_idx]
    old_color = mat.DiffuseColor

    print("当前材质: {} (索引 {})".format(mat.Name, mat_idx))
    print("当前颜色: RGB({},{},{})".format(old_color.R, old_color.G, old_color.B))

    # 弹颜色选择器
    # 用 Rhino 原生颜色对话框
    rc, new_color = Rhino.UI.Dialogs.ShowColorDialog(old_color)
    if not rc:
        print("取消了。")
        return

    # 直接改材质表中的主定义 —— 所有引用此材质的对象都会联动
    mat.DiffuseColor = new_color
    mat.CommitChanges()

    doc.Views.Redraw()
    print("已改为 RGB({},{},{})".format(new_color.R, new_color.G, new_color.B))
    print("所有使用材质 [{}] 的物体已一起更新。".format(mat.Name))


change_material_color()
