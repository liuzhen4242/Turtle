# -*- coding: utf-8 -*-
"""
Rhino 脚本：根据 Snapshots 批量 ViewCaptureToFile 到指定文件夹
用法：
  1. 在 Rhino 命令行输入 EditPythonScript (Rhino 6/7) 或 ScriptEditor (Rhino 8)
  2. 粘贴本脚本并运行 (F5)
  3. 按提示：选择要处理的 Snapshots → 选择输出文件夹 → 选择是否透明背景
  4. 脚本会依次恢复每个 Snapshot，对当前活动视图截图，
     按 Snapshot 名称保存为 PNG

说明：
  - 名称枚举用标准 API：sc.doc.Snapshots.Names
  - 恢复用命令行：-Snapshots Restore "名称"（这是 McNeel 官方论坛给出的
    确认可行方案，Snapshots 这块没有直接的 RhinoCommon Restore() 方法）
  - Snapshots 能记录的内容比 Layer States 更全（视图、物体位置等），
    本脚本结束后只会还原"图层可见性/锁定状态"，不保证完全还原视图角度、
    物体位置——如果你需要，建议跑完后手动在 Snapshots 面板里点回原状态
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


def batch_capture_by_snapshots():
    doc = sc.doc

    # ---------- 第一步：记录当前图层可见性/锁定状态，最后用于还原 ----------
    layer_snapshot = []
    for i in range(doc.Layers.Count):
        layer = doc.Layers[i]
        if layer is None or layer.IsDeleted:
            continue
        layer_snapshot.append((i, layer.IsVisible, layer.IsLocked))

    # ---------- 第二步：读取所有 Snapshot 名称 ----------
    names = list(doc.Snapshots.Names)

    if not names:
        print("场景中没有已保存的 Snapshot，脚本结束。")
        return

    # ---------- 第三步：多选列表，选择本次要处理的 Snapshot ----------
    selected_names = rs.MultiListBox(
        names, "选择要批量截图的 Snapshot（默认全选）", "Snapshots", names)

    if not selected_names:
        print("未选择任何 Snapshot，脚本结束。")
        return

    # ---------- 第四步：选择输出文件夹 ----------
    folder = rs.BrowseForFolder(message="选择保存截图的文件夹")
    if not folder:
        print("未选择文件夹，脚本结束。")
        return

    # ---------- 第五步：是否透明背景 ----------
    result = rs.MessageBox("是否使用透明背景截图？", 4, "透明背景")
    transparent_bg = (result == 6)  # 6 = Yes, 7 = No

    # ---------- 第六步：逐个恢复 Snapshot 并截图 ----------
    success_count = 0
    fail_list = []

    for name in selected_names:
        restored = rs.Command(
            '-Snapshots Restore "{}" _Enter _Enter'.format(name), False)

        if not restored:
            print("恢复 Snapshot '{}' 失败，跳过。".format(name))
            fail_list.append(name)
            continue

        doc.Views.Redraw()

        safe_name = sanitize_filename(name)
        if not safe_name:
            safe_name = "Snapshot_{}".format(success_count + 1)

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
        print("以下 Snapshot 处理失败：")
        for name in fail_list:
            print("  - {}".format(name))
    print("图层可见性/锁定状态已还原；视图角度、物体位置等如有需要请手动核对。")


batch_capture_by_snapshots()
