# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs

def RunMeshOutlineProcess():
    LinetypeName = 'Continuous3'
    objs = rs.GetObjects('Select objects to create mesh outline', preselect=True)
    if not objs:
        return
    # 保存原始图层（统一用第一个物体图层；如需各自图层可以再调整）
    sourceLayer = rs.ObjectLayer(objs[0])
    # 一次性批量执行，所有物件一起生成【整体外轮廓】
    idList = " ".join(["_SelID {}".format(o) for o in objs])
    rs.Command("_MeshOutline " + idList, echo=False)
    newCurves = rs.LastCreatedObjects()
    if not newCurves:
        return
    for crv in newCurves:
        rs.Command("_BringToFront _SelID {}".format(crv), echo=False)
        rs.ObjectLinetype(crv, LinetypeName)
        rs.ObjectLayer(crv, sourceLayer)

RunMeshOutlineProcess()