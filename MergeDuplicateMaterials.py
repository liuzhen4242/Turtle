# -*- coding: utf-8 -*-
"""
Rhino 脚本：合并同色重复材质（安全版）
用法：ScriptEditor 粘贴后 F5，什么都不选处理全场景
原理：材质表里同名同色的多条材质，每个 RGB 只留一条主材质，
     把原本绑到重复材质的对象用 ModifyAttributes 改指到主材质。
"""
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino


def merge_duplicate_materials():
    doc = sc.doc

    # ── 第一步：按 RGB 颜色分组材质 ──
    color_to_indices = {}
    for i in range(doc.Materials.Count):
        m = doc.Materials[i]
        c = m.DiffuseColor
        key = (c.R, c.G, c.B)
        color_to_indices.setdefault(key, []).append(i)

    # 每个颜色组选第一个当主材质
    master_map = {}  # {重复索引: 主索引}
    for key, indices in color_to_indices.items():
        if len(indices) > 1:
            master = indices[0]
            for idx in indices[1:]:
                master_map[idx] = master

    if not master_map:
        print("没有发现重复材质，无需合并。")
        return

    print("发现 {} 组重复材质：".format(len(master_map)))
    for dup_idx, master_idx in sorted(master_map.items()):
        dup_m = doc.Materials[dup_idx]
        mas_m = doc.Materials[master_idx]
        print("  重复材质 [{}] {} RGB=({}) → 主材质 [{}] {}".format(
            dup_idx, dup_m.Name,
            "{},{},{}".format(dup_m.DiffuseColor.R, dup_m.DiffuseColor.G, dup_m.DiffuseColor.B),
            master_idx, mas_m.Name))

    # ── 第二步：遍历对象，用 ModifyAttributes 安全改指 ──
    obj_ids = rs.AllObjects()
    repointed = 0
    skipped = 0

    for obj_id in obj_ids:
        rhobj = doc.Objects.FindId(obj_id)
        if rhobj is None:
            continue

        attr = rhobj.Attributes
        # 只处理"来自对象"的材质
        if attr.MaterialSource != Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject:
            skipped += 1
            continue

        old_idx = attr.MaterialIndex
        if old_idx in master_map:
            new_idx = master_map[old_idx]
            # 复制一份属性，只改 MaterialIndex，其他不动
            new_attr = attr.Duplicate()
            new_attr.MaterialIndex = new_idx
            # 用官方接口写回
            doc.Objects.ModifyAttributes(rhobj, new_attr, True)
            repointed += 1

    doc.Views.Redraw()
    print("-" * 50)
    print("完成：改指 {} 个对象，跳过 {} 个（ByLayer/其他）".format(repointed, skipped))
    if repointed > 0:
        print("现在同色对象共用同一条材质了，改颜色会联动。")


merge_duplicate_materials()
