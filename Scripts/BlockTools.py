# -*- coding: utf-8 -*-
# BlockTools.py — MyTools 示例 Python 脚本
#
# 首次运行会被插件解压到本地缓存目录：
#   Windows: %APPDATA%\MyTools\Scripts
#   Mac:     ~/.config/MyTools/Scripts
# 之后直接编辑缓存里的副本即可调试（重启 Rhino 生效）。
# 想强制还原：删掉缓存目录后重启 Rhino。
#
# 把这个文件换成你自己的功能即可。

import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc

sc.doc = Rhino.RhinoDoc.ActiveDoc

# 弹一个提示框，验证 Python 脚本能被命令正确调用
Rhino.UI.Dialogs.ShowMessage(
    "MyTools 的 Python 脚本运行成功！\n\n把这里替换成你自己的功能即可。",
    "MyTools / BlockTools"
)
