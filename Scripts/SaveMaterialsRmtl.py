# -*- coding: utf-8 -*-
# SaveMaterialsRmtl.py  (需要 Rhino 8.6 或更高版本)
# 选中物件 -> 对每个材质弹出"另存为"对话框 -> 保存为 .rmtl（可改文件名）
# 贴图会嵌入 .rmtl 文件中。多个物件共用同一材质时只保存一次。

import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import re
import os

STICKY_KEY = "SaveMaterialsRmtl_LastFolder"


def safe_name(name):
    name = re.sub(r'[\\/:*?"<>|]', '_', name or "")
    return name.strip() or "Material"


def get_embed_choice():
    """RenderContent.EmbedFilesChoice.AlwaysEmbed (8.6+)"""
    enum = getattr(Rhino.Render.RenderContent, "EmbedFilesChoice", None)
    if enum is None:
        return None
    return enum.AlwaysEmbed


def get_render_material(obj):
    """按材质来源查找 RenderMaterial：物件 -> 图层 -> 旧式 Material 转换"""
    rm = None

    # 1. 直接取（多数情况）
    try:
        rm = obj.GetRenderMaterial(True)
    except Exception:
        rm = None
    if rm is None:
        try:
            rm = obj.RenderMaterial
        except Exception:
            rm = None
    if rm is not None:
        return rm

    # 2. 按来源手动查找
    src = obj.Attributes.MaterialSource
    layer = sc.doc.Layers[obj.Attributes.LayerIndex]
    S = Rhino.DocObjects.ObjectMaterialSource

    if src == S.MaterialFromLayer:
        try:
            rm = layer.RenderMaterial
        except Exception:
            rm = None
    elif src == S.MaterialFromParent:
        # 图块内的物件等：退回图层材质
        try:
            rm = layer.RenderMaterial
        except Exception:
            rm = None
    if rm is not None:
        return rm

    # 3. 旧式 Material（没有 RenderMaterial 对象）-> 转成 RenderMaterial
    try:
        mat = obj.GetMaterial(True)
        if mat is not None and mat.Index >= 0:
            rm = Rhino.Render.RenderMaterial.FromMaterial(mat, sc.doc)
    except Exception:
        rm = None
    return rm


def describe(obj):
    src = obj.Attributes.MaterialSource
    layer = sc.doc.Layers[obj.Attributes.LayerIndex]
    print("  诊断: 材质来源={0}, 图层={1}, 物件材质索引={2}, 图层材质索引={3}".format(
        src, layer.FullPath, obj.Attributes.MaterialIndex, layer.RenderMaterialIndex))


def main():
    ids = rs.GetObjects("选择要保存材质的物件", preselect=True)
    if not ids:
        return

    choice = get_embed_choice()
    if choice is None:
        print("此 Rhino 版本不支持 RenderContent.SaveToFile，请升级到 Rhino 8.6 或更高版本。")
        return

    last_folder = sc.sticky.get(STICKY_KEY)
    seen = set()
    saved = 0

    for oid in ids:
        obj = sc.doc.Objects.FindId(oid)
        if obj is None:
            continue

        rm = get_render_material(obj)
        if rm is None:
            print("物件 {0} 没有可保存的材质（可能确实是默认材质），已跳过。".format(oid))
            describe(obj)
            continue
        if rm.Id in seen:
            continue
        seen.add(rm.Id)

        default_name = safe_name(rm.Name)
        path = rs.SaveFileName(
            "保存材质: {0}".format(rm.Name),
            "Rhino Material (*.rmtl)|*.rmtl||",
            last_folder,
            default_name,
            "rmtl",
        )
        if not path:                     # 用户取消：跳过这个材质
            print("已跳过: {0}".format(rm.Name))
            continue

        if not path.lower().endswith(".rmtl"):
            path += ".rmtl"
        last_folder = os.path.dirname(path)
        sc.sticky[STICKY_KEY] = last_folder

        ok = rm.SaveToFile(path, choice)
        if ok:
            saved += 1
            print("已保存: {0}".format(path))
        else:
            print("保存失败: {0}".format(path))

    print("完成，共保存 {0} 个材质。".format(saved))


if __name__ == "__main__":
    main()
