# -*- coding: utf-8 -*-
"""
Rhino 脚本：根据 Layer States 批量 ViewCaptureToFile 到指定文件夹（正式版）
用法：
  1. 在 Rhino 命令行输入 EditPythonScript (Rhino 6/7) 或 ScriptEditor (Rhino 8)
  2. 粘贴本脚本并运行 (F5)
  3. 按提示：选择要处理的 Layer States → 选择输出文件夹 → 选择是否透明背景
  4. 脚本会依次恢复每个 Layer State，对当前活动视图截图，
     按 Layer State 名称保存为 PNG，全部完成后自动还原你原来的图层状态

本版改动：
  - 不再依赖命令行 "-LayerState"（确认该命令在新版面板下不存在）
  - 改用标准 RhinoCommon API: doc.NamedLayerStates
      .Names   -> 直接获取所有 Layer State 名称
      .Restore(name, properties) -> 直接恢复指定状态
    这套 API 从 Rhino 6.14 起就存在，稳定可靠
"""

import os
import re

import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import System


ILLEGAL_CHARS_PATTERN = re.compile(r'[\\/:*?"<>|]')


def sanitize_filename(name):
    """把文件名中的非法字符替换成下划线"""
    return ILLEGAL_CHARS_PATTERN.sub('_', name).strip()


def capture_active_view_to_file(filepath, transparent_bg):
    """截取当前活动视图，保存为 PNG"""
    doc = sc.doc
    view = doc.Views.ActiveView
    if view is None:
        return False

    rect = view.ClientRectangle
    width = max(rect.Width, 1)
    height = max(rect.Height, 1)

    capture = Rhino.Display.ViewCapture()
    capture.Width = width
    capture.Height = height
    capture.ScaleScreenItems = False
    capture.DrawAxes = False
    capture.DrawGrid = False
    capture.TransparentBackground = transparent_bg

    bmp = capture.CaptureToBitmap(view)
    if bmp is None:
        return False

    bmp.Save(filepath, System.Drawing.Imaging.ImageFormat.Png)
    return True


def batch_capture_by_layer_states():
    doc = sc.doc

    # ---------- 第一步：记录当前图层可见性/锁定状态，最后用于还原 ----------
    layer_snapshot = []
    for i in range(doc.Layers.Count):
        layer = doc.Layers[i]
        if layer is None or layer.IsDeleted:
            continue
        layer_snapshot.append((i, layer.IsVisible, layer.IsLocked))

    # ---------- 第二步：直接从 NamedLayerStates 读取所有状态名称 ----------
    names = list(doc.NamedLayerStates.Names)

    if not names:
        print("场景中没有已保存的 Layer State，脚本结束。")
        return

    # ---------- 第三步：多选列表，选择本次要处理的 Layer State ----------
    selected_names = rs.MultiListBox(
        names, "选择要批量截图的 Layer State（默认全选）", "Layer States", names)

    if not selected_names:
        print("未选择任何 Layer State，脚本结束。")
        return

    # ---------- 第四步：选择输出文件夹 ----------
    folder = rs.BrowseForFolder(message="选择保存截图的文件夹")
    if not folder:
        print("未选择文件夹，脚本结束。")
        return

    # ---------- 第五步：是否透明背景 ----------
    result = rs.MessageBox("是否使用透明背景截图？", 4, "透明背景")
    transparent_bg = (result == 6)  # 6 = Yes, 7 = No

    # ---------- 第六步：逐个恢复 Layer State 并截图 ----------
    success_count = 0
    fail_list = []

    for name in selected_names:
        restored = doc.NamedLayerStates.Restore(
            name, Rhino.DocObjects.Tables.RestoreLayerProperties.All)

        if not restored:
            print("恢复 Layer State '{}' 失败，跳过。".format(name))
            fail_list.append(name)
            continue

        doc.Views.Redraw()

        safe_name = sanitize_filename(name)
        if not safe_name:
            safe_name = "LayerState_{}".format(success_count + 1)

        filepath = os.path.join(folder, safe_name + ".png")

        ok = capture_active_view_to_file(filepath, transparent_bg)
        if ok:
            success_count += 1
            print("已保存: {}".format(filepath))
        else:
            print("截图失败: {}".format(name))
            fail_list.append(name)

    # ---------- 第七步：还原原来的图层状态 ----------
    for i, was_visible, was_locked in layer_snapshot:
        layer = doc.Layers[i]
        if layer is None or layer.IsDeleted:
            continue
        layer.IsVisible = was_visible
        layer.IsLocked = was_locked
        layer.CommitChanges()

    doc.Views.Redraw()

    print("完成：共成功导出 {} 张截图，保存在 {}".format(success_count, folder))
    if fail_list:
        print("以下 Layer State 处理失败：")
        for name in fail_list:
            print("  - {}".format(name))
    print("图层状态已还原为运行脚本前的样子。")


batch_capture_by_layer_states()
