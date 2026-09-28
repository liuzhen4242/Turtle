# -*- coding: utf-8 -*-
"""
SurfaceToHatch.py
功能：
    选择平面 Surface / Polysurface
    → 根据真实 Trim 边界生成 Hatch
    → 保留原物件属性
    → 隐藏原物件
特点：
    1. 使用 RhinoCommon Hatch.CreateFromBrep()
    2. 不需要 DuplicateSurfaceBorder()
    3. 支持 Trimmed Surface
    4. 支持带孔的 Surface
    5. 支持 Polysurface 中的平面 Face
    6. 保留 Layer / Color / Color Source / Name
    7. 不生成临时边界 Curve
"""
import rhinoscriptsyntax as rs
import Rhino
import System
# ============================================================
# 用户设置
# ============================================================
# Hatch Pattern
HATCH_PATTERN = "Solid"
# Hatch Rotation
# 单位：度
HATCH_ROTATION = 0.0
# Hatch Scale
HATCH_SCALE = 1.0
# 生成后是否隐藏原曲面
HIDE_SOURCE = True
# 是否将原曲面和 Hatch 放入同一个 Group
MAKE_GROUP = False
# ============================================================
# 获取 Hatch Pattern
# ============================================================
def get_hatch_pattern_index(pattern_name):
    doc = Rhino.RhinoDoc.ActiveDoc
    pattern_index = doc.HatchPatterns.Find(pattern_name, True)
    if pattern_index < 0:
        return -1
    return pattern_index
# ============================================================
# 获取物件 Brep
# ============================================================
def get_brep(obj_id):
    obj = Rhino.RhinoDoc.ActiveDoc.Objects.Find(obj_id)
    if obj is None:
        return None
    geometry = obj.Geometry
    if isinstance(geometry, Rhino.Geometry.Brep):
        return geometry
    # 有些 Surface 的 Geometry 可能直接是 Surface
    if isinstance(geometry, Rhino.Geometry.Surface):
        return Rhino.Geometry.Brep.CreateFromSurface(geometry)
    return None
# ============================================================
# 判断 Face 是否为平面
# ============================================================
def is_planar_face(face):
    if face is None:
        return False
    try:
        return face.IsPlanar
    except:
        return False
# ============================================================
# 获取原物件属性
# ============================================================
def duplicate_attributes(source_obj):
    try:
        return source_obj.Attributes.Duplicate()
    except:
        return Rhino.DocObjects.ObjectAttributes()
# ============================================================
# 创建 Hatch
# ============================================================
def create_hatch_from_face(face, pattern_index):
    doc = Rhino.RhinoDoc.ActiveDoc
    if face is None:
        return None
    if not is_planar_face(face):
        return None
    try:
        # ----------------------------------------------------
        # Hatch.CreateFromBrep()
        #
        # 直接从 Brep Face 创建 Hatch
        # 因此不需要：
        #
        # DuplicateSurfaceBorder()
        # AddHatch()
        #
        # Face 的 Trim 信息会直接参与 Hatch 创建
        # ----------------------------------------------------
        single_face_brep = face.DuplicateFace(False)
        if single_face_brep is None:
            return None
        hatch = Rhino.Geometry.Hatch.CreateFromBrep(
            single_face_brep,
            0,
            pattern_index,
            Rhino.RhinoMath.ToRadians(HATCH_ROTATION),
            HATCH_SCALE,
            Rhino.Geometry.Point3d.Unset
        )
        return hatch
    except Exception as e:
        print("Hatch 创建失败：{}".format(e))
        return None
# ============================================================
# 主程序
# ============================================================
def surface_to_hatch():
    doc = Rhino.RhinoDoc.ActiveDoc
    # --------------------------------------------------------
    # 选择物件
    # --------------------------------------------------------
    object_ids = rs.GetObjects(
        "选择要转换为 Hatch 的平面曲面",
        rs.filter.surface | rs.filter.polysurface,
        preselect=True,
        select=True
    )
    if not object_ids:
        return
    # --------------------------------------------------------
    # 获取 Hatch Pattern
    # --------------------------------------------------------
    pattern_index = get_hatch_pattern_index(HATCH_PATTERN)
    if pattern_index < 0:
        rs.MessageBox(
            "找不到 Hatch Pattern：{}".format(HATCH_PATTERN),
            0,
            "Surface To Hatch"
        )
        return
    # --------------------------------------------------------
    # 开始处理
    # --------------------------------------------------------
    rs.EnableRedraw(False)
    source_objects = []
    hatch_objects = []
    success_count = 0
    skip_count = 0
    try:
        for obj_id in object_ids:
            source_obj = doc.Objects.Find(obj_id)
            if source_obj is None:
                skip_count += 1
                continue
            # ------------------------------------------------
            # 获取 Brep
            # ------------------------------------------------
            brep = get_brep(obj_id)
            if brep is None:
                skip_count += 1
                continue
            # ------------------------------------------------
            # 获取原物件属性
            # ------------------------------------------------
            attributes = duplicate_attributes(source_obj)
            # ------------------------------------------------
            # 一个 Surface 通常只有一个 Face
            #
            # Polysurface 可能有多个 Face
            # 对每一个平面 Face 分别生成 Hatch
            # ------------------------------------------------
            face_count = brep.Faces.Count
            object_hatches = []
            for face_index in range(face_count):
                face = brep.Faces[face_index]
                # --------------------------------------------
                # 只处理平面 Face
                # --------------------------------------------
                if not is_planar_face(face):
                    skip_count += 1
                    continue
                # --------------------------------------------
                # 创建 Hatch
                # --------------------------------------------
                hatch = create_hatch_from_face(
                    face,
                    pattern_index
                )
                if hatch is None:
                    skip_count += 1
                    continue
                # --------------------------------------------
                # 给 Hatch 继承原物件属性
                # --------------------------------------------
                hatch_attributes = attributes.Duplicate()
                hatch_id = doc.Objects.AddHatch(
                    hatch,
                    hatch_attributes
                )
                if hatch_id == System.Guid.Empty:
                    skip_count += 1
                    continue
                object_hatches.append(hatch_id)
                hatch_objects.append(hatch_id)
                success_count += 1
            # ------------------------------------------------
            # 如果这个物件成功生成 Hatch
            # ------------------------------------------------
            if object_hatches:
                source_objects.append(obj_id)
                # --------------------------------------------
                # 建立 Group
                # --------------------------------------------
                if MAKE_GROUP:
                    group_name = rs.AddGroup()
                    if group_name:
                        rs.AddObjectsToGroup(
                            [obj_id] + object_hatches,
                            group_name
                        )
                # --------------------------------------------
                # 隐藏原物件
                # --------------------------------------------
                if HIDE_SOURCE:
                    rs.HideObject(obj_id)
    finally:
        rs.EnableRedraw(True)
        doc.Views.Redraw()
    # ========================================================
    # 完成提示
    # ========================================================
    message = (
        "Surface → Hatch 完成\n\n"
        "生成 Hatch：{}\n"
        "成功处理原物件：{}\n"
        "跳过 Face：{}"
    ).format(
        success_count,
        len(source_objects),
        skip_count
    )
    print(message)
    rs.MessageBox(
        message,
        0,
        "Surface To Hatch"
    )
# ============================================================
# Run
# ============================================================
if __name__ == "__main__":
    surface_to_hatch()
