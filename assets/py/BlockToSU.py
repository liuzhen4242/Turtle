# -*- coding: utf-8 -*-
"""
block_and_export_skp.py (嵌套组件 - 修复组顺序版)

修复说明：
1. 修正 Rhino 中 rs.ObjectGroups 返回顺序颠倒的问题（由内到外 -> 颠倒为由外到内）。
2. 完美支持多层 Nested Group 识别，并在 SU 中保留层级结构。
"""

import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import os


def prepare_object_attributes(obj_id):
    """静默处理材质与颜色，转为 ByObject，避免 SU 里材质丢失"""
    try:
        rhobj = rs.coercerhinoobject(obj_id)
        if rhobj is None:
            return
        attrs = rhobj.Attributes

        # 材质烘焙
        if attrs.MaterialSource == Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer:
            layer = sc.doc.Layers[attrs.LayerIndex]
            attrs.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject
            attrs.MaterialIndex = layer.RenderMaterialIndex

        # 颜色烘焙
        if attrs.ColorSource == Rhino.DocObjects.ObjectColorSource.ColorFromLayer:
            layer = sc.doc.Layers[attrs.LayerIndex]
            attrs.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
            attrs.ObjectColor = layer.Color

        rhobj.CommitChanges()
    except Exception:
        pass


def make_unique_block_name(base_name):
    """生成唯一的 Block 名称，避免冲突"""
    block_name = base_name
    n = 1
    while rs.IsBlock(block_name):
        block_name = "{}_{}".format(base_name, n)
        n += 1
    return block_name


def process_group_tree(node, base_point, all_block_names):
    """
    递归处理组树状结构，自底向上生成嵌套 Block
    返回: (created_instances, inherited_layer)
    """
    created_instances = []
    inherited_layer = None

    # 1. 先处理所有子组 (递归深入最底层)
    for sub_gname, child_node in node["children"].items():
        sub_inst_ids, sub_layer = process_group_tree(child_node, base_point, all_block_names)
        if sub_inst_ids:
            if not inherited_layer and sub_layer:
                inherited_layer = sub_layer

            # 为子组创建中间层 Block
            blk_name = make_unique_block_name("Group_{}".format(sub_gname))
            def_name = rs.AddBlock(sub_inst_ids, base_point, blk_name, True)
            if def_name:
                inst_id = rs.InsertBlock(def_name, base_point)
                if inst_id:
                    if sub_layer:
                        rs.ObjectLayer(inst_id, sub_layer)
                    all_block_names.append(def_name)
                    created_instances.append(inst_id)

    # 2. 处理当前层级的 Brep 物体（创建内层组件）
    for j, child_id in enumerate(node["objects"]):
        child_layer = rs.ObjectLayer(child_id)
        if not inherited_layer and child_layer:
            inherited_layer = child_layer

        child_name = rs.ObjectName(child_id)
        base_child_name = child_name if child_name else "{}_sub_{}".format(node["name"], j)

        sub_def_name = rs.AddBlock([child_id], base_point, make_unique_block_name(base_child_name), True)
        if sub_def_name:
            sub_inst_id = rs.InsertBlock(sub_def_name, base_point)
            if sub_inst_id:
                rs.ObjectLayer(sub_inst_id, child_layer)
                all_block_names.append(sub_def_name)
                created_instances.append(sub_inst_id)

    return created_instances, inherited_layer


def build_nested_blocks(dup_ids):
    """
    构建多层嵌套 Block 结构
    """
    outer_instance_ids = []
    all_block_names = []
    base_point = (0, 0, 0)

    root_groups = {}
    ungrouped_objs = []

    # 1. 解析组路径并构建多级树
    for obj_id in dup_ids:
        raw_groups = rs.ObjectGroups(obj_id)
        if raw_groups:
            # 关键修改：Rhino 返回的组顺序是从内到外，必须反转为 [最外层组, 中间组, 最内层组]
            groups = list(reversed(raw_groups))
            
            curr_dict = root_groups
            target_node = None
            
            for g_name in groups:
                if g_name not in curr_dict:
                    curr_dict[g_name] = {
                        "name": g_name,
                        "children": {},
                        "objects": []
                    }
                target_node = curr_dict[g_name]
                curr_dict = target_node["children"]
            
            if target_node:
                target_node["objects"].append(obj_id)
        else:
            ungrouped_objs.append(obj_id)

    # 2. 处理有组的对象（递归构建 Block）
    for g_name, node in root_groups.items():
        top_sub_insts, top_layer = process_group_tree(node, base_point, all_block_names)
        
        if top_sub_insts:
            parent_block_name = make_unique_block_name("Group_{}".format(g_name))
            parent_def_name = rs.AddBlock(top_sub_insts, base_point, parent_block_name, True)
            if parent_def_name:
                parent_inst_id = rs.InsertBlock(parent_def_name, base_point)
                if parent_inst_id:
                    if top_layer:
                        rs.ObjectLayer(parent_inst_id, top_layer)
                    
                    outer_instance_ids.append(parent_inst_id)
                    all_block_names.append(parent_def_name)

    # 3. 处理未分组的对象
    for i, obj_id in enumerate(ungrouped_objs):
        orig_layer = rs.ObjectLayer(obj_id)
        name = rs.ObjectName(obj_id)
        base_name = name if name else "export_blk_{}".format(i)

        def_name = rs.AddBlock([obj_id], base_point, make_unique_block_name(base_name), True)
        if def_name:
            instance_id = rs.InsertBlock(def_name, base_point)
            if instance_id:
                rs.ObjectLayer(instance_id, orig_layer)
                outer_instance_ids.append(instance_id)
                all_block_names.append(def_name)

    return outer_instance_ids, all_block_names


def export_as_skp(obj_ids, file_path):
    """静默导出 Block 实例"""
    rs.UnselectAllObjects()
    rs.SelectObjects(obj_ids)

    if not file_path.lower().endswith(".skp"):
        file_path += ".skp"

    doc = sc.doc
    cmd = '-_Export "{}" MinimumFaceCount=2 _Enter _Enter'.format(file_path)
    rs.Command(cmd, echo=False)

    if os.path.exists(file_path):
        return True

    success = doc.ExportSelected(file_path)
    return os.path.exists(file_path) or success


def cleanup(instance_ids, block_names):
    """静默清理所有临时 Block 实例和块定义"""
    if instance_ids:
        rs.DeleteObjects(instance_ids)
    for name in block_names:
        try:
            rs.PurgeBlock(name)
        except Exception:
            pass


def main():
    obj_ids = rs.SelectedObjects()
    if not obj_ids:
        print("提示：请先选中需要导出的物体，然后再运行脚本。")
        return

    file_path = rs.SaveFileName("导出为 SketchUp 文件", "SketchUp Files (*.skp)|*.skp||")
    if not file_path:
        print("已取消导出。")
        return

    rs.EnableRedraw(False)

    try:
        dup_ids = rs.CopyObjects(obj_ids)
        if not dup_ids:
            print("复制对象失败，导出中止。")
            return

        for d in dup_ids:
            prepare_object_attributes(d)

        outer_instance_ids, all_block_names = build_nested_blocks(dup_ids)

        if not outer_instance_ids:
            print("转换 Block 失败，已中止。")
            rs.DeleteObjects(dup_ids)
            return

        ok = export_as_skp(outer_instance_ids, file_path)
        cleanup(outer_instance_ids, all_block_names)

    finally:
        rs.EnableRedraw(True)
        rs.Redraw()

    if ok:
        print("导出成功！多层组嵌套已成功识别，文件保存在: {}".format(file_path))
    else:
        print("警告：导出未能正常完成，请检查文件路径或权限。")


if __name__ == "__main__":
    main()