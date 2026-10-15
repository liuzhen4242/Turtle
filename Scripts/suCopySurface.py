# -*- coding: utf-8 -*-
import os
import time
import System
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino

DIR  = os.path.join(os.path.expanduser("~"), "su_rhino_bridge")
path = os.path.join(DIR, "clip.skp")
meta = os.path.join(DIR, "clip.txt")

EXPLODE_BLOCKS       = True    # 先把块炸开，才能转换里面的 mesh
MERGE_COPLANAR       = True    # 转换后合并共面的面
MESH_LIMIT           = 5000    # 单个 mesh 面数超过这个值会跳过转换，保留为 mesh
PUT_ON_CURRENT_LAYER = False   # True：粘贴的物件放到当前图层（会丢掉 SU 的图层信息）
GROUP_PASTED         = True    # True：每次粘贴的物件自动打成一个新群组

def fmt_age(sec):
    if sec < 60:
        return "{} 秒前".format(int(sec))
    if sec < 3600:
        return "{} 分钟前".format(int(sec // 60))
    return "{} 小时前".format(int(sec // 3600))

def explode_all_blocks(ids, used_defs):
    """反复炸开块，直到没有块实例为止；记录用过的块定义名"""
    result = list(ids)
    for _ in range(20):
        blocks = [o for o in result if rs.IsBlockInstance(o)]
        if not blocks:
            break
        result = [o for o in result if o not in blocks]
        for b in blocks:
            name = rs.BlockInstanceName(b)
            if name:
                used_defs.add(name)
            parts = rs.ExplodeBlockInstance(b)
            if parts:
                result.extend(parts)
    return result

def meshes_to_breps(ids):
    tol = sc.doc.ModelAbsoluteTolerance
    out = []
    skipped = 0
    for oid in ids:
        obj = sc.doc.Objects.FindId(oid)
        if obj is None or not isinstance(obj.Geometry, Rhino.Geometry.Mesh):
            out.append(oid)
            continue
        mesh = obj.Geometry
        if mesh.Faces.Count > MESH_LIMIT:
            skipped += 1
            out.append(oid)
            continue
        brep = Rhino.Geometry.Brep.CreateFromMesh(mesh, False)
        if brep is None:
            out.append(oid)
            continue
        if MERGE_COPLANAR:
            brep.MergeCoplanarFaces(tol)
        new_id = sc.doc.Objects.AddBrep(brep, obj.Attributes)
        if new_id == System.Guid.Empty:
            out.append(oid)
            continue
        sc.doc.Objects.Delete(oid, True)
        out.append(new_id)
    if skipped:
        print("有 {} 个 mesh 面数过多，已保留为 mesh".format(skipped))
    return out

def delete_defs(names):
    for n in names:
        try:
            rs.DeleteBlock(n)
        except:
            pass

def main():
    if not os.path.exists(path):
        print("没有找到文件：" + path)
        return
    if not os.path.exists(meta):
        print("没有找到基点信息，请重启 SU 并重新复制（需要更新后的插件）")
        return

    print("剪贴板内容复制于 " + fmt_age(time.time() - os.path.getmtime(path)))
    ox, oy, oz, su_diag = [float(v) for v in open(meta).read().split()]

    before = set(rs.AllObjects() or [])
    rs.EnableRedraw(False)
    rs.Command('-_Import "{}" _Enter'.format(path), False)
    new_objs = [o for o in (rs.AllObjects() or []) if o not in before]

    if not new_objs:
        rs.EnableRedraw(True)
        print("没有导入新物件（可能取消了导入选项对话框）")
        return

    # 先用导入的原始物件反推基点
    box = rs.BoundingBox(new_objs)
    p_min, p_max = box[0], box[6]
    rh_diag = rs.Distance(p_min, p_max)
    if su_diag > 1e-9 and rh_diag > 1e-9:
        s = rh_diag / su_diag
    else:
        s = Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Inches, sc.doc.ModelUnitSystem)

    base = Rhino.Geometry.Point3d(p_min[0] - ox * s,
                                  p_min[1] - oy * s,
                                  p_min[2] - oz * s)

    used_defs = set()
    if EXPLODE_BLOCKS:
        new_objs = explode_all_blocks(new_objs, used_defs)
        new_objs = meshes_to_breps(new_objs)
        # 炸开后删除块定义，避免下次导入同名时复用旧定义
        delete_defs(used_defs)
    else:
        stamp = time.strftime("%H%M%S")
        for i, o in enumerate(list(new_objs)):
            if rs.IsBlockInstance(o):
                old = rs.BlockInstanceName(o)
                try:
                    rs.RenameBlock(old, "SU_{}_{}".format(stamp, i))
                except:
                    pass

    if PUT_ON_CURRENT_LAYER:
        rs.ObjectLayer(new_objs, rs.CurrentLayer())

    # 把这一批物件打成一个新群组
    if GROUP_PASTED and len(new_objs) > 1:
        grp_name = rs.AddGroup()
        if grp_name:
            rs.AddObjectsToGroup(new_objs, grp_name)

    rs.EnableRedraw(True)

    # 动态预览：物件跟着光标走，不画连线
    objs = [sc.doc.Objects.FindId(g) for g in new_objs]
    objs = [o for o in objs if o is not None]
    gp = Rhino.Input.Custom.GetPoint()
    gp.SetCommandPrompt("指定粘贴点（基点对齐到这里）")
    gp.SetBasePoint(base, False)

    def dyn(sender, e):
        xf = Rhino.Geometry.Transform.Translation(e.CurrentPoint - base)
        for o in objs:
            e.Display.DrawObject(o, xf)
    gp.DynamicDraw += dyn

    rs.UnselectAllObjects()
    rs.SelectObjects(new_objs)
    result = gp.Get()
    if result != Rhino.Input.GetResult.Point:
        rs.DeleteObjects(new_objs)
        print("已取消粘贴")
        return

    pt = gp.Point()
    rs.MoveObjects(new_objs, pt - base)
    sc.doc.Views.Redraw()
    print("已粘贴 {} 个物件".format(len(new_objs)))

main()