# -*- coding: utf-8 -*-
"""
Rhino 脚本：诊断对象材质绑定情况
用法：什么都不选就跑（处理全场景），或先选几个可疑对象再跑
输出每个对象的：图层名、MaterialSource、MaterialIndex、材质名、DiffuseColor
并按 MaterialIndex 分组，看谁和谁真的共享同一条材质
"""
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino


def diagnose_materials():
    doc = sc.doc

    selected = rs.SelectedObjects()
    obj_ids = selected if selected else rs.AllObjects()
    if not obj_ids:
        print("场景中没有找到任何对象。")
        return

    # 先列出材质表里所有材质，方便对照
    print("=" * 70)
    print("【材质表】共 {} 条材质：".format(doc.Materials.Count))
    for i in range(doc.Materials.Count):
        m = doc.Materials[i]
        c = m.DiffuseColor
        print("  [{}] {}  RGB=({},{},{})".format(
            i, m.Name, c.R, c.G, c.B))
    print("=" * 70)

    # 按 MaterialIndex 分组统计
    groups = {}  # {mat_index: [(obj_desc, material_source_str)]}

    for obj_id in obj_ids:
        rhobj = rs.coercerhinoobject(obj_id)
        if rhobj is None:
            continue

        attr = rhobj.Attributes
        src = attr.MaterialSource
        idx = attr.MaterialIndex
        layer_name = rhobj.Attributes.LayerName

        if idx >= 0 and idx < doc.Materials.Count:
            m = doc.Materials[idx]
            mname = m.Name
            mc = m.DiffuseColor
            mcolor_str = "RGB=({},{},{})".format(mc.R, mc.G, mc.B)
        else:
            mname = "(无材质)"
            mcolor_str = ""

        obj_desc = "图层={} 对象={}".format(layer_name, rs.ObjectName(obj_id) or "(未命名)")

        src_str = {
            Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer: "FromLayer(来自图层)",
            Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject: "FromObject(来自对象)",
            Rhino.DocObjects.ObjectMaterialSource.MaterialFromParent: "FromParent(来自父级)",
        }.get(src, str(src))

        print("对象: {}".format(obj_desc))
        print("  MaterialSource = {}".format(src_str))
        print("  MaterialIndex  = {} → 材质名: {}  {}".format(idx, mname, mcolor_str))
        print()

        groups.setdefault(idx, []).append((obj_desc, src_str))

    # 汇总：哪些材质被多个对象共用
    print("=" * 70)
    print("【共享情况汇总】")
    shared_count = 0
    for idx, users in sorted(groups.items()):
        if len(users) > 1:
            shared_count += 1
            if idx >= 0 and idx < doc.Materials.Count:
                m = doc.Materials[idx]
                print("\n材质 [{}] {} 被 {} 个对象共用：".format(
                    idx, m.Name, len(users)))
            else:
                print("\n无材质索引 [{}] 被 {} 个对象引用：".format(idx, len(users)))
            for desc, s in users:
                print("    - {}  [{}]".format(desc, s))

    if shared_count == 0:
        print("\n⚠️ 没有任何材质被多个对象共用！")
        print("   这说明每个对象都绑了独立材质（或 ByLayer），改一个不会影响别人。")
        print("   请运行 ColorToSharedMaterial.py 重新分配共享材质。")
    else:
        print("\n✅ 以上 {} 组材质是真正共享的（同 MaterialIndex）。".format(shared_count))

    print("=" * 70)


diagnose_materials()
