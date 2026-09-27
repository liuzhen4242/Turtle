# -*- coding: utf-8 -*-
"""
Rhino 脚本：对象颜色 → 真正共享的 RenderMaterial（RenderContent 系统）
用法：什么都不选 F5（全场景），或先选对象再跑
原理：
  - 用 Rhino.Render.RenderContent 创建材质（材质库同款机制）
  - 相同 RGB 的对象共用同一个 RenderMaterial 实例
  - 用 rhobj.RenderMaterial = mat 赋值（不是旧版 MaterialIndex）
  - 改色时无论在材质面板还是属性面板，都会真正联动
"""
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import System


def color_to_shared_material():
    doc = sc.doc

    # ── 第一步：扫描已有 RenderMaterials，按颜色建映射 ──
    # 避免重复创建同色材质
    color_mat = {}  # (R,G,B) -> RenderMaterial 对象

    for rm in doc.RenderMaterials:
        name = rm.Name or ""
        # 尝试从名字解析颜色
        if name.startswith("Color_"):
            parts = name.split("_")
            if len(parts) == 4:
                try:
                    r, g, b = int(parts[1]), int(parts[2]), int(parts[3])
                    color_mat[(r, g, b)] = rm
                except ValueError:
                    pass

    print("启动：已有 {} 条 Color_R_G_B 材质可复用".format(len(color_mat)))

    # ── 第二步：确定要处理的对象 ──
    selected = rs.SelectedObjects()
    obj_ids = selected if selected else rs.AllObjects()
    if not obj_ids:
        print("场景中没有对象。")
        return

    count = 0
    reused = 0
    created = 0

    for obj_id in obj_ids:
        rhobj = rs.coercerhinoobject(obj_id)
        if rhobj is None:
            continue

        # 取对象实际显示色（含图层继承）
        color = rhobj.Attributes.DrawColor(doc)
        key = (color.R, color.G, color.B)

        if key in color_mat:
            mat = color_mat[key]
            reused += 1
        else:
            # 创建 RenderContent 材质（材质库同款机制）
            mat = Rhino.Render.RenderContentType.NewContentFromTypeId(
                Rhino.Render.ContentUuids.BasicMaterialType, doc)
            mat.BeginChange(Rhino.Render.RenderContent.ChangeContexts.Program)
            mat.Fields.Set("diffuse", System.Drawing.Color.FromArgb(
                color.R, color.G, color.B))
            mat.EndChange()
            mat.Name = "Color_{}_{}_{}".format(color.R, color.G, color.B)
            doc.RenderMaterials.Add(mat)
            color_mat[key] = mat
            created += 1

        # 用 RenderMaterial 属性赋值（关键：不是旧版 MaterialIndex）
        rhobj.RenderMaterial = mat
        rhobj.CommitChanges()
        count += 1

    doc.Views.Redraw()
    print("=" * 50)
    print("完成：处理 {} 个对象".format(count))
    print("  复用已有材质：{} 次".format(reused))
    print("  新建材质：{} 条".format(created))
    print("  共享材质总数：{} 条".format(len(color_mat)))
    print("=" * 50)
    print("现在选一个物体在属性面板改材质颜色，所有同色物体应联动。")


color_to_shared_material()
