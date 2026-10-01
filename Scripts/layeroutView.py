# -*- coding: utf-8 -*-

import Rhino
import scriptcontext as sc
import System


def sync_perspective_object_display_to_detail():
    doc = sc.doc

    print("")
    print("==========================================")
    print("Perspective to Detail")
    print("Object Display Mode Override")
    print("==========================================")

    # 1. 获取当前 Layout Page
    active_view = doc.Views.ActiveView
    if active_view is None:
        print("No active view.")
        return

    # 兼容处理：如果当前在 Detail 激活状态内部，找到所属的 PageView
    if not isinstance(active_view, Rhino.Display.RhinoPageView):
        page_view = None
        for v in doc.Views:
            if isinstance(v, Rhino.Display.RhinoPageView):
                # 检查激活视口是否属于该图纸页面
                active_id = doc.Views.ActiveView.ActiveViewport.Id
                for dt in v.GetDetailViews():
                    if dt.Viewport.Id == active_id:
                        page_view = v
                        break
                if page_view:
                    break
        if page_view is not None:
            active_view = page_view
        else:
            print("Current view is not a Layout page.")
            return

    # 2. 查找 Detail
    try:
        details = [d for d in active_view.GetDetailViews() if d is not None]
    except Exception as e:
        print("Cannot get Detail views: {}".format(e))
        return

    if len(details) == 0:
        print("No Detail found on current Layout.")
        return

    if len(details) != 1:
        print("Found {} Details. This version requires exactly one Detail.".format(len(details)))
        return

    detail = details[0]

    # 3. 目标 Detail Viewport
    try:
        target_viewport = detail.Viewport
    except Exception as e:
        print("Cannot get Detail viewport: {}".format(e))
        return

    if target_viewport is None:
        print("Detail viewport is None.")
        return

    target_id = target_viewport.Id
    print("\nTARGET DETAIL\n------------------------------------------")
    print("Viewport Name: {}".format(target_viewport.Name))
    print("Viewport ID: {}".format(target_id))

    # 4. 查找模型的透视视口 (Perspective)
    source_viewport = None
    print("\nSEARCH MODEL PERSPECTIVE\n------------------------------------------")
    for view in doc.Views:
        if isinstance(view, Rhino.Display.RhinoPageView):
            continue
        try:
            vp = view.ActiveViewport
            if vp is None:
                continue

            print("Viewport: {}  ID: {}  Perspective: {}".format(
                vp.Name, vp.Id, vp.IsPerspectiveProjection
            ))

            if vp.IsPerspectiveProjection:
                source_viewport = vp
                break
        except Exception:
            continue

    if source_viewport is None:
        print("Model Perspective not found.")
        return

    source_id = source_viewport.Id
    print("\nSOURCE\n------------------------------------------")
    print("Viewport Name: {}".format(source_viewport.Name))
    print("Viewport ID: {}".format(source_id))

    # 5. 同步显示覆盖属性
    copied = 0
    cleared = 0
    failed = 0

    print("\nSYNC OBJECT OVERRIDES\n------------------------------------------")
    for obj in doc.Objects:
        if obj is None:
            continue

        attr = obj.Attributes

        # 情况 A: 透视视图中有单独的显示模式覆盖
        if attr.HasDisplayModeOverride(source_id):
            mode_id = attr.GetDisplayModeOverride(source_id)
            if mode_id == System.Guid.Empty:
                continue

            mode = Rhino.Display.DisplayModeDescription.GetDisplayMode(mode_id)
            if mode is None:
                print("DisplayMode not found: {}".format(mode_id))
                failed += 1
                continue

            new_attr = attr.Duplicate()
            try:
                new_attr.SetDisplayModeOverride(mode, target_id)
                if new_attr.HasDisplayModeOverride(target_id):
                    result = doc.Objects.ModifyAttributes(obj.Id, new_attr, True)
                    if result:
                        copied += 1
                        print("COPIED: {} -> {}".format(obj.Id, mode.EnglishName))
                    else:
                        print("ModifyAttributes failed: {}".format(obj.Id))
                        failed += 1
                else:
                    print("Override was not created: {}".format(obj.Id))
                    failed += 1
            except Exception as e:
                print("Copy failed {}: {}".format(obj.Id, e))
                failed += 1

        # 情况 B: 透视视图中没有覆盖，清除 Detail 中可能残留的覆盖
        else:
            if attr.HasDisplayModeOverride(target_id):
                new_attr = attr.Duplicate()
                try:
                    new_attr.RemoveDisplayModeOverride(target_id)
                    if not new_attr.HasDisplayModeOverride(target_id):
                        result = doc.Objects.ModifyAttributes(obj.Id, new_attr, True)
                        if result:
                            cleared += 1
                            print("CLEARED: {}".format(obj.Id))
                        else:
                            failed += 1
                    else:
                        print("Override was not removed: {}".format(obj.Id))
                        failed += 1
                except Exception as e:
                    print("Clear failed {}: {}".format(obj.Id, e))
                    failed += 1

    # 6. 重绘并汇报结果
    doc.Views.Redraw()

    print("\n==========================================")
    print("SYNC COMPLETE")
    print("------------------------------------------")
    print("Copied Overrides: {}".format(copied))
    print("Cleared Overrides: {}".format(cleared))
    print("Failed: {}".format(failed))
    print("==========================================\n")


if __name__ == "__main__":
    sync_perspective_object_display_to_detail()