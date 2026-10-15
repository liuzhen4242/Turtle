# -*- coding: utf-8 -*-
# SaveBaseColorAs.py  (Rhino 8)
# 选中物件 -> 对每个材质弹出"另存为"对话框 -> 只保存材质的 BaseColor 贴图（jpg/png 等，保持原格式）
# 多个物件共用同一材质时只保存一次。其他通道、材质参数一律忽略。

import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import re
import os
import shutil

STICKY_KEY = "SaveBaseColorAs_LastFolder"
TT = Rhino.DocObjects.TextureType


def safe_name(name):
    name = re.sub(r'[\\/:*?"<>|]', '_', name or "")
    return name.strip() or "Material"


def get_render_material(obj):
    """物件 -> 图层 -> 旧式 Material 转换，依次查找 RenderMaterial"""
    rm = None
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

    layer = sc.doc.Layers[obj.Attributes.LayerIndex]
    try:
        rm = layer.RenderMaterial
    except Exception:
        rm = None
    if rm is not None:
        return rm

    try:
        mat = obj.GetMaterial(True)
        if mat is not None and mat.Index >= 0:
            rm = Rhino.Render.RenderMaterial.FromMaterial(mat, sc.doc)
    except Exception:
        rm = None
    return rm


def base_color_file(rm):
    """返回 BaseColor 贴图的文件路径，找不到返回 None"""
    # 1. 模拟出的 Material：先取 PBR BaseColor，再退回旧式 Bitmap(漫反射)贴图
    try:
        mat = rm.SimulatedMaterial(Rhino.Render.RenderTexture.TextureGeneration.Allow)
    except Exception:
        mat = None
    if mat is not None:
        for t in (TT.PBR_BaseColor, TT.Bitmap):
            try:
                tex = mat.GetTexture(t)
            except Exception:
                tex = None
            if tex is not None and tex.FileName:
                return str(tex.FileName)

    # 2. 在材质子节点里找名字含 base/color/diffuse 的贴图槽
    child = None
    try:
        child = rm.FirstChild
    except Exception:
        pass
    while child is not None:
        try:
            slot = str(child.ChildSlotName).lower()
        except Exception:
            slot = ""
        if ("base" in slot and "color" in slot) or "diffuse" in slot:
            try:
                for f in child.FilesToEmbed:
                    if f:
                        return str(f)
            except Exception:
                pass
        try:
            child = child.NextSibling
        except Exception:
            child = None
    return None


def main():
    ids = rs.GetObjects("选择要保存 BaseColor 贴图的物件", preselect=True)
    if not ids:
        return

    last_folder = sc.sticky.get(STICKY_KEY)
    seen_materials = set()
    saved = 0

    for oid in ids:
        obj = sc.doc.Objects.FindId(oid)
        if obj is None:
            continue

        rm = get_render_material(obj)
        if rm is None:
            print("物件 {0} 没有可保存的材质（可能是默认材质），已跳过。".format(oid))
            continue
        if rm.Id in seen_materials:
            continue
        seen_materials.add(rm.Id)

        src = base_color_file(rm)
        if not src:
            print("材质 [{0}] 没有 BaseColor 贴图，已跳过。".format(rm.Name))
            continue
        if not os.path.isfile(src):
            print("材质 [{0}] 的贴图文件不存在: {1}".format(rm.Name, src))
            continue

        ext = os.path.splitext(src)[1].lstrip(".").lower() or "png"
        default_name = safe_name(rm.Name)
        path = rs.SaveFileName(
            "保存 BaseColor 贴图: {0}".format(rm.Name),
            "Image (*.{0})|*.{0}||".format(ext),
            last_folder,
            default_name,
            ext,
        )
        if not path:                     # 用户取消：跳过这个材质
            print("已跳过: {0}".format(rm.Name))
            continue

        if not path.lower().endswith("." + ext):
            path += "." + ext
        last_folder = os.path.dirname(path)
        sc.sticky[STICKY_KEY] = last_folder

        try:
            shutil.copy2(src, path)
            saved += 1
            print("已保存 [{0}]: {1}".format(rm.Name, path))
        except Exception as e:
            print("保存失败: {0} ({1})".format(path, e))

    print("完成，共保存 {0} 张贴图。".format(saved))


if __name__ == "__main__":
    main()