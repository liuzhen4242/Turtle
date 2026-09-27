# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import scriptcontext as sc

def shift_camera_universal():
    # 1. 获取当前活动视口（透视、轴测通用）
    active_view = rs.CurrentView()
    if not active_view:
        print("Error: No active viewport found.")
        return

    # 2. 从 sticky 中读取历史记录，若首次运行则使用初始默认值 (距离 100，轴向 X)
    last_distance = sc.sticky.get("CAMERA_SHIFT_LAST_DIST", "100")
    last_axis = sc.sticky.get("CAMERA_SHIFT_LAST_AXIS", "X")

    current_axis = last_axis
    prompt_msg = "Enter offset distance (e.g. 100, -100) [Axis={0}]".format(current_axis)

    # 将上一次的数值作为默认值传入 GetString
    user_input = rs.GetString(prompt_msg, last_distance, ["Axis"])
    if not user_input:
        return

    # 允许点击命令行切换 Axis
    while user_input.upper() == "AXIS":
        current_axis = "Y" if current_axis == "X" else "X"
        prompt_msg = "Enter offset distance (e.g. 100, -100) [Axis={0}]".format(current_axis)
        user_input = rs.GetString(prompt_msg, last_distance, ["Axis"])
        if not user_input:
            return

    # 3. 解析数值
    raw_str = user_input.strip().replace(" ", "")
    try:
        val = float(raw_str)
    except ValueError:
        print("Invalid input. Please enter a valid number (e.g. 100, -100).")
        return

    # 4. 记住本次输入的数值与轴向，供下一次作为默认值
    str_val = "{0:g}".format(val)
    sc.sticky["CAMERA_SHIFT_LAST_DIST"] = str_val
    sc.sticky["CAMERA_SHIFT_LAST_AXIS"] = current_axis

    if current_axis == "X":
        offset_vec = [val, 0.0, 0.0]
    else:
        offset_vec = [0.0, val, 0.0]

    # 5. 保存基准视角 move00 (0)
    existing_views = rs.NamedViews() or []
    if "move00 (0)" not in existing_views:
        rs.AddNamedView("move00 (0)", active_view)

    # 6. 计算自增编号 (move01, move02, ...)
    index = 1
    while True:
        prefix = "move{0:02d} ".format(index)
        already_exists = any(v.startswith(prefix) for v in existing_views)
        if not already_exists:
            break
        index += 1

    # 7. 平移 Camera 与 Target
    cam = rs.ViewCamera(active_view)
    target = rs.ViewTarget(active_view)

    new_cam = [cam[0] + offset_vec[0], cam[1] + offset_vec[1], cam[2] + offset_vec[2]]
    new_target = [target[0] + offset_vec[0], target[1] + offset_vec[1], target[2] + offset_vec[2]]

    rs.ViewCameraTarget(active_view, new_cam, new_target)

    # 8. 保存新视图：格式如 move01 (100)
    view_name = "move{0:02d} ({1})".format(index, str_val)
    rs.AddNamedView(view_name, active_view)

    print("Success: Viewport shifted by {0}. Saved as '{1}'.".format(str_val, view_name))

if __name__ == "__main__":
    shift_camera_universal()