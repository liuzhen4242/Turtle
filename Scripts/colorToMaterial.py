# -*- coding: utf-8 -*-
"""
Rhino 脚本：将对象颜色一键转换为材质（RenderMaterial 版，防重复）
用法：
  1. 在 Rhino 命令行输入 EditPythonScript (Rhino 6/7) 或 ScriptEditor (Rhino 8)
  2. 粘贴本脚本并运行 (F5)
  3. 若有选中的对象，只处理选中对象；若没有选中任何对象，则处理场景中所有对象

功能：
  - 读取每个对象的"实际显示颜色"（若图层颜色继承，也会正确取到）
  - 相同颜色的对象自动共用同一个材质，不会重复创建
  - 创建新材质前，会先检查文档里是否已存在同名材质（比如之前跑过一次
    本脚本、或者之前手动建过），有就直接复用，不会再新建重复的一份，
    这样反复运行本脚本也不会再产生重复材质
  - 材质使用 Rhino.Render.RenderMaterial（Basic Material），
    也就是材质库同款机制：无论从"材质面板"改材质球，
    还是从"属性面板"改选中物体的材质，其他共用该材质的物体都会联动
"""

import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino


def find_existing_render_material(doc, name):
    """在文档已有的 RenderMaterial 里查找同名材质，找到就返回它，找不到返回 None"""
    for mat in doc.RenderMaterials:
        if mat.Name == name:
            return mat
    return None


def color_to_material():
    doc = sc.doc

    # 优先使用选中对象，没有选中则处理全部对象
    selected = rs.SelectedObjects()
    obj_ids = selected if selected else rs.AllObjects()

    if not obj_ids:
        print("场景中没有找到任何对象。")
        return

    color_material_map = {}  # {(R,G,B): RenderMaterial}
    count = 0
    created_count = 0
    reused_count = 0

    for obj_id in obj_ids:
        rhobj = rs.coercerhinoobject(obj_id)
        if rhobj is None:
            continue

        # 获取对象的实际显示颜色（若按图层显示颜色，会自动取图层颜色）
        color = rhobj.Attributes.DrawColor(doc)
        key = (color.R, color.G, color.B)

        if key in color_material_map:
            mat = color_material_map[key]
        else:
            mat_name = "Color_{}_{}_{}".format(color.R, color.G, color.B)

            # 先看文档里有没有同名材质，有就直接复用，不新建
            existing_mat = find_existing_render_material(doc, mat_name)

            if existing_mat is not None:
                mat = existing_mat
                reused_count += 1
            else:
                # 创建 Basic Material（材质库同款的 RenderContent 对象）
                mat = Rhino.Render.RenderContentType.NewContentFromTypeId(
                    Rhino.Render.ContentUuids.BasicMaterialType, doc)
                mat.BeginChange(Rhino.Render.RenderContent.ChangeContexts.Program)
                mat.Fields.Set("diffuse", color)
                mat.EndChange()
                mat.Name = mat_name

                doc.RenderMaterials.Add(mat)
                created_count += 1

            color_material_map[key] = mat

        # 赋值给物体（RenderMaterial 属性走的是渲染内容系统，天然支持联动）
        rhobj.RenderMaterial = mat
        rhobj.CommitChanges()
        count += 1

    doc.Views.Redraw()
    print("完成：共处理 {} 个对象，涉及 {} 种颜色（新建 {} 个材质，复用已有 {} 个材质）。".format(
        count, len(color_material_map), created_count, reused_count))


color_to_material()
