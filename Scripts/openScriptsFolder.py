# -*- coding: utf-8 -*-
"""
OpenScriptsFolder.py
在文件管理器中打开 Rhino 8 的 Python 脚本目录（跨平台）。

Windows:  explorer 打开 %APPDATA%\\McNeel\\Rhinoceros\\8.0\\scripts
macOS:    open 打开 ~/Library/Application Support/McNeel/Rhinoceros/8.0/Scripts
"""
import os
import subprocess
import sys


def open_scripts_folder():
    if sys.platform == "darwin":
        base = os.path.expanduser(
            "~/Library/Application Support/McNeel/Rhinoceros/8.0/Scripts"
        )
    else:
        appdata = os.environ.get("APPDATA")
        base = os.path.join(appdata or "", "McNeel", "Rhinoceros", "8.0", "scripts")

    if not os.path.isdir(base):
        print("脚本目录不存在: {}".format(base))
        return

    if sys.platform == "darwin":
        subprocess.Popen(["open", base])
    else:
        subprocess.Popen(["explorer", base])

    print("已打开脚本目录: {}".format(base))


if __name__ == "__main__":
    open_scripts_folder()
