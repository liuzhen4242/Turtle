# -*- coding: utf-8 -*-
"""
vis_watch.py
Rhino 可见性历史管理脚本（不替换原生命令版）

原理：
    通过挂接 Rhino.Commands.Command.BeginCommand 事件，监听你正常使用的
    原生 Hide / Isolate / Show / EndIsolate / ShowSelected 命令。
    每次这些命令即将执行时，自动记录一次当前的显示/隐藏状态快照，
    压入历史栈。你完全按平时习惯用 H、I 就行，不需要改任何操作方式。

需要的操作（写入 Options > Aliases，或做成工具栏按钮）：

    watch    开启监听（每次重新打开 Rhino 后运行一次即可，一次会话内只需开一次）
    stop     关闭监听
    restore  恢复到上一次记录的可见性状态（核心功能，一个命令完成）
    status   查看当前监听状态和历史步数
    clear    清空历史栈

用法（命令行方式）：
    -_RunPythonScript "完整路径\\vis_watch.py" watch
    -_RunPythonScript "完整路径\\vis_watch.py" restore

进阶：如果想让 Rhino 一启动就自动开启监听，可以在 Rhino 快捷方式里加启动参数：
    "Rhino.exe" /runscript="-_RunPythonScript ""完整路径\\vis_watch.py"" watch"
"""

import sys
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino

STICKY_STACK = "VIS_HISTORY_STACK"
STICKY_HOOK_FLAG = "VIS_HISTORY_HOOK_ON"
MAX_DEPTH = 10  # 只保留最近10步可见性历史，超出的旧记录会被自动丢弃

# 会被自动记录快照的原生命令（英文命令名，不受语言界面影响）
WATCHED_COMMANDS = ("Hide", "Isolate", "Show", "EndIsolate", "ShowSelected")


def _get_stack():
    if STICKY_STACK not in sc.sticky:
        sc.sticky[STICKY_STACK] = []
    return sc.sticky[STICKY_STACK]


def _snapshot():
    state = {}
    for obj in sc.doc.Objects:
        state[obj.Id] = obj.IsHidden
    return state


def _push_snapshot():
    stack = _get_stack()
    stack.append(_snapshot())
    if len(stack) > MAX_DEPTH:
        stack.pop(0)


def _apply_snapshot(state):
    for obj_id, was_hidden in state.items():
        obj = sc.doc.Objects.Find(obj_id)
        if obj is None:
            continue
        if was_hidden and not obj.IsHidden:
            sc.doc.Objects.Hide(obj, True)
        elif not was_hidden and obj.IsHidden:
            sc.doc.Objects.Show(obj, True)
    sc.doc.Views.Redraw()


def _on_begin_command(sender, e):
    # Rhino 事件回调，命令即将执行时触发
    try:
        if e.CommandEnglishName in WATCHED_COMMANDS:
            _push_snapshot()
    except Exception:
        pass


def cmd_watch():
    if sc.sticky.get(STICKY_HOOK_FLAG):
        print("可见性监听已经在运行，无需重复开启。")
        return
    Rhino.Commands.Command.BeginCommand += _on_begin_command
    sc.sticky[STICKY_HOOK_FLAG] = True
    print("已开始监听原生 Hide / Isolate / Show / EndIsolate，正常使用即可，恢复请运行 restore。")


def cmd_stop():
    if sc.sticky.get(STICKY_HOOK_FLAG):
        Rhino.Commands.Command.BeginCommand -= _on_begin_command
        sc.sticky[STICKY_HOOK_FLAG] = False
        print("已停止监听。")
    else:
        print("监听尚未开启。")


def cmd_restore():
    if not sc.sticky.get(STICKY_HOOK_FLAG):
        print("提示：监听当前未开启，此次恢复只能用到之前已记录的历史（如果有的话）。")
    stack = _get_stack()
    if not stack:
        print("没有可恢复的可见性历史记录。")
        return
    last_state = stack.pop()
    _apply_snapshot(last_state)
    print("已恢复到上一次可见性状态，剩余历史步数：{}".format(len(stack)))


def cmd_clear():
    sc.sticky[STICKY_STACK] = []
    print("可见性历史已清空。")


def cmd_status():
    hooked = sc.sticky.get(STICKY_HOOK_FLAG, False)
    stack = _get_stack()
    print("监听状态：{}，当前历史步数：{}".format("开启" if hooked else "关闭", len(stack)))


ACTIONS = {
    "watch": cmd_watch,
    "stop": cmd_stop,
    "restore": cmd_restore,
    "clear": cmd_clear,
    "status": cmd_status,
}


def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    action = args[0].lower() if args else None

    if action not in ACTIONS:
        choice = rs.GetString("选择操作", "watch", list(ACTIONS.keys()))
        if choice is None:
            return
        action = choice.lower()

    if action in ACTIONS:
        ACTIONS[action]()
    else:
        print("未知操作参数：{}".format(action))


if __name__ == "__main__":
    main()
