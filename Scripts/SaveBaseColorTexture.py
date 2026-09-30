# -*- coding: utf-8 -*-
# SaveBaseColorTexture.py  (Rhino 8)
# 选中物件 -> 选择文件夹 -> 只把材质的 BaseColor 贴图复制到该文件夹。
# 支持保存时自定义输出文件名（回车则沿用原文件名；多文件自动追加 _1/_2 序号）。
import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import os
import shutil

STICKY_KEY = "SaveBaseColorTexture_LastFolder"
TT = Rhino.DocObjects.TextureType


def get_render_material(obj):
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


def unique_path(folder, filename):
    base, ext = os.path.splitext(filename)
    path = os.path.join(folder, filename)
    i = 1
    while os.path.exists(path):
        path = os.path.join(folder, "{0}_{1}{2}".format(base, i, ext))
        i += 1
    return path


def main():
    ids = rs.GetObjects("选择要导出 BaseColor 贴图的物件", preselect=True)
    if not ids:
        return

    folder = rs.BrowseForFolder(sc.sticky.get(STICKY_KEY), "选择保存贴图的文件夹")
    if not folder:
        return
    sc.sticky[STICKY_KEY] = folder

    # 保存时自定义名称（可含扩展名，回车则用原文件名）
    custom = rs.GetString(
        "保存名称（可含扩展名，回车则用原文件名）", "", 0, "重命名导出贴图"
    )
    custom = (custom or "").strip()

    seen_materials = set()
    seen_files = set()
    copied = 0
    for oid in ids:
        obj = sc.doc.Objects.FindId(oid)
        if obj is None:
            continue
        rm = get_render_material(obj)
        if rm is None:
            print("物件 {0} 没有指定材质，已跳过。".format(oid))
            continue
        if rm.Id in seen_materials:
            continue
        seen_materials.add(rm.Id)

        path = base_color_file(rm)
        if not path:
            print("材质 [{0}] 没有 BaseColor 贴图。".format(rm.Name))
            continue
        key = os.path.normcase(os.path.abspath(path))
        if key in seen_files:
            continue
        seen_files.add(key)

        if not os.path.isfile(path):
            print("材质 [{0}] 的贴图文件不存在: {1}".format(rm.Name, path))
            continue

        # 自定义名称：加上原扩展名；空则用原文件名
        if custom:
            orig_ext = os.path.splitext(path)[1]
            fname = custom + orig_ext
        else:
            fname = os.path.basename(path)

        dst = unique_path(folder, fname)
        try:
            shutil.copy2(path, dst)
            copied += 1
            print("已保存 [{0}]: {1}".format(rm.Name, dst))
        except Exception as e:
            print("复制失败: {0} ({1})".format(path, e))

    print("完成，共保存 {0} 个 BaseColor 贴图到 {1}".format(copied, folder))


if __name__ == "__main__":
    main()
