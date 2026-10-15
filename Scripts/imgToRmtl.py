# -*- coding: utf-8 -*-
# TextureToMaterial.py  (需要 Rhino 8.6 或更高版本)
# 选一张图片 -> 另存为 .rmtl（输入的文件名即材质名）
# 生成只设置了 BaseColor 贴图的 Physically Based 材质，其他属性保持默认。
# 贴图会嵌入 .rmtl 文件中。

import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import os
import re

STICKY_KEY = "TextureToMaterial_LastFolder"
TT = Rhino.DocObjects.TextureType


def safe_name(name):
    name = re.sub(r'[\\/:*?"<>|]', '_', name or "")
    return name.strip() or "Material"


def find_material(name):
    for rm in sc.doc.RenderMaterials:
        if rm.Name == name:
            return rm
    return None


def ensure_material(name, texture_path):
    """文档里已有同名材质就直接用，否则新建一个只有 BaseColor 贴图的 PBR 材质"""
    rm = find_material(name)
    if rm is not None:
        return rm

    mat = Rhino.DocObjects.Material()
    mat.Name = name
    mat.ToPhysicallyBased()
    pbr = mat.PhysicallyBased

    tex = Rhino.DocObjects.Texture()
    tex.FileName = texture_path
    pbr.SetTexture(tex, TT.PBR_BaseColor)

    src = getattr(pbr, "Material", None) or mat
    rm = Rhino.Render.RenderMaterial.FromMaterial(src, sc.doc)
    rm.Name = name
    sc.doc.RenderMaterials.Add(rm)
    return rm


def main():
    enum = getattr(Rhino.Render.RenderContent, "EmbedFilesChoice", None)
    if enum is None:
        print("此 Rhino 版本不支持 RenderContent.SaveToFile，请升级到 Rhino 8.6 或更高版本。")
        return

    tex_path = rs.OpenFileName(
        "选择贴图（BaseColor）",
        "Images (*.jpg;*.jpeg;*.png;*.tif;*.tiff;*.bmp)|*.jpg;*.jpeg;*.png;*.tif;*.tiff;*.bmp||")
    if not tex_path:
        return

    default = safe_name(os.path.splitext(os.path.basename(tex_path))[0])
    rmtl_path = rs.SaveFileName(
        "另存为材质（文件名即材质名）",
        "Rhino Material (*.rmtl)|*.rmtl||",
        sc.sticky.get(STICKY_KEY),
        default,
        "rmtl")
    if not rmtl_path:
        return
    if not rmtl_path.lower().endswith(".rmtl"):
        rmtl_path += ".rmtl"
    sc.sticky[STICKY_KEY] = os.path.dirname(rmtl_path)

    name = os.path.splitext(os.path.basename(rmtl_path))[0]

    try:
        rm = ensure_material(name, tex_path)
        ok = rm.SaveToFile(rmtl_path, enum.AlwaysEmbed)
    except Exception as e:
        print("创建或保存材质失败: {0}".format(e))
        return

    if ok:
        print("已保存: {0}".format(rmtl_path))
    else:
        print("保存失败: {0}".format(rmtl_path))
    sc.doc.Views.Redraw()


if __name__ == "__main__":
    main()