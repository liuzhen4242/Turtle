# -*- coding: utf-8 -*-
import scriptcontext as sc
import Rhino

def sync_layout_views():
    current_view = sc.doc.Views.ActiveView
    if not isinstance(current_view, Rhino.Display.RhinoPageView):
        print("Please run this command in a Layout view.")
        return

    # 提取当前 Layout 视口的完整 ViewportInfo
    src_vp = current_view.ActiveViewport
    vp_info = Rhino.DocObjects.ViewportInfo(src_vp)

    # 遍历并覆写所有其他 Layout
    for page in sc.doc.Views.GetPageViews():
        if page.MainViewport.Id != current_view.MainViewport.Id:
            page.ActiveViewport.SetViewProjection(vp_info, True)
            page.Redraw()

    sc.doc.Views.Redraw()
    print("All Layout views aligned successfully.")

if __name__ == "__main__":
    sync_layout_views()