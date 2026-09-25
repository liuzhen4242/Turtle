# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs

def move_and_merge_layers_v4():
    layers_to_move = rs.GetLayers("步骤 1：请勾选需要移动的【源图层】")
    if not layers_to_move: 
        return
    
    target_group = rs.GetLayer("步骤 2：请选择【目标父图层】(如 cad 组)")
    if not target_group: 
        return

    rs.EnableRedraw(False)
    moved = 0
    merged = 0
    failed = []
    
    # 按照层级深度降序排序，由底向上处理
    layers_to_move.sort(key=lambda x: x.count("::"), reverse=True)

    for src in layers_to_move:
        if not rs.IsLayer(src) or src == target_group:
            continue
            
        short_name = src.split("::")[-1]
        expected_path = target_group + "::" + short_name
        
        # 判断：如果目标组内已经有这个图层 -> 合并
        if rs.IsLayer(expected_path) and src != expected_path:
            rs.LayerLocked(src, False)
            rs.LayerVisible(src, True)
            rs.LayerLocked(expected_path, False)
            rs.LayerVisible(expected_path, True)
            
            # 1. 先把子图层剥离转移
            children = rs.LayerChildren(src)
            if children:
                for child in children:
                    try: rs.ParentLayer(child, expected_path)
                    except: pass
            
            # 2. 用API强行转移图层上的所有普通物件
            objs = rs.ObjectsByLayer(src)
            if objs:
                rs.ObjectLayer(objs, expected_path)
                
            if rs.CurrentLayer() == src:
                rs.CurrentLayer(expected_path)
                
            # 3. 尝试直接删除空出来的源图层
            if not rs.DeleteLayer(src):
                # 如果删不掉(说明有CAD图块占用)，启用Rhino底层指令强杀
                cmd = '_-MergeLayer "{}" _Enter "{}"'.format(src, expected_path)
                rs.Command(cmd, False)
                
                # 检查是否真杀掉了
                if rs.IsLayer(src):
                    failed.append(src)
                else:
                    merged += 1
            else:
                merged += 1
                
        # 判断：如果目标组没有这个图层 -> 直接移入 (更改父级)
        else:
            try:
                rs.ParentLayer(src, target_group)
                moved += 1
            except:
                failed.append(src)

    rs.EnableRedraw(True)
    
    # 构建提示信息
    msg = "✅ 图层处理完成！\n\n"
    msg += "▶ 纯移入：{} 个图层 (目标组没同名)\n".format(moved)
    msg += "▶ 成功合并：{} 个图层 (目标组已有同名)\n".format(merged)
    if failed:
        msg += "\n❌ 失败图层：{} 个（遇到严重图块死锁，请全选模型使用 Explode 炸开图块后再试）".format(len(failed))
        
    print(msg)
    rs.MessageBox(msg, 64, "图层整理结果")

if __name__ == "__main__":
    move_and_merge_layers_v4()