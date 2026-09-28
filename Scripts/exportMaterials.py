# -*- coding: utf-8 -*-
"""
exportMaterials.py
批量导出选中物体的材质为 .rmtl 文件（一键导出材质）。

- 材质来源优先级：物件自身材质 -> 图层材质
- 去重：同一材质只导出一次
- 自动清洗文件名中的非法字符（含中文材质名）
- 第三方渲染材质（V-Ray / Enscape）不支持 rmtl 导出，会单独提示失败
"""
import os

import Rhino
import scriptcontext as sc


def get_selected_objects():
    """获取当前选中物件（含预选）。ActiveView 没有 Selection 属性，
    必须用 Objects.GetSelectedObjects 获取。"""
    return sc.doc.Objects.GetSelectedObjects(False, False)


def BatchSaveObjectMaterials():
    objs = get_selected_objects()
    if len(objs) == 0:
        print("⚠️ 请先选中至少一个物体！")
        return

    mat_set = set()
    mat_list = []
    info_lines = []

    for obj in objs:
        mat = obj.RenderMaterial
        src = "物件材质"
        if mat is None:
            mat = obj.Layer.RenderMaterial
            src = "图层材质"
        if mat is None:
            continue
        if mat.Id not in mat_set:
            mat_set.add(mat.Id)
            mat_list.append((mat, src))
            info_lines.append("{} ({})".format(mat.Name, src))

    if not mat_list:
        print("⚠️ 选中物体均为默认材质，无材质可导出")
        return

    print("✅ 一共找到 {} 个唯一材质：".format(len(mat_list)))
    for line in info_lines:
        print("  - " + line)

    folder_dlg = Rhino.UI.BrowseFolderDialog()
    folder_dlg.Title = "选择材质保存文件夹"
    if not folder_dlg.ShowDialog():
        print("❌ 已取消")
        return
    out_folder = folder_dlg.SelectedPath

    success_count = 0
    fail_list = []
    for mat, src in mat_list:
        safe_name = mat.Name
        for c in r'\/:*?"<>|':
            safe_name = safe_name.replace(c, "_")
        save_path = os.path.join(out_folder, safe_name + ".rmtl")
        try:
            ok = mat.SaveToFile(save_path)
        except Exception:
            ok = False
        if ok:
            success_count += 1
            print("✅ 已保存：{}.rmtl".format(safe_name))
        else:
            fail_list.append("{} ({})".format(mat.Name, src))

    print("\n===== 导出完成 =====")
    print("成功导出：{} / {}".format(success_count, len(mat_list)))
    if fail_list:
        print("❌ 导出失败（多为第三方渲染材质，V-Ray/Enscape 材质不支持 rmtl 导出）：")
        for f in fail_list:
            print("  - " + f)


if __name__ == "__main__":
    BatchSaveObjectMaterials()
