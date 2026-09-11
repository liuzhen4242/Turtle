"""
RhinoWorkspace Startup

Cross Platform

Auto locate Workspace

Support two run locations:

1. Development :
   RhinoWorkspace/
       workspace/
           scripts/
               RhinoWorkspaceStartup.py

2. Installed :
   Rhino 8.0/scripts/
       RhinoWorkspaceStartup.py
       RhinoWorkspace.path   (written by startup sync)

"""


from pathlib import Path
import sys



# =====================================================
# Auto locate Workspace
# =====================================================

def _find_workspace():

    current = (
        Path(__file__)
        .resolve()
        .parent
    )


    # -----------------------------
    # 1. sidecar 定位文件
    #    由 startup 模块安装时生成，
    #    内容为 Workspace 绝对路径
    # -----------------------------

    sidecar = current / "RhinoWorkspace.path"

    if sidecar.exists():

        try:

            path = (
                sidecar
                .read_text(encoding="utf-8")
                .strip()
            )

            if path:

                return Path(path)

        except Exception:

            pass


    # -----------------------------
    # 2. 开发位置自定位
    #
    #    RhinoWorkspace/
    #        workspace/
    #            scripts/
    #                RhinoWorkspaceStartup.py
    #
    #    上三级 = RhinoWorkspace
    # -----------------------------

    candidate = (
        current
        .parent
        .parent
        .parent
    )

    if (candidate / "workspace").exists():

        return candidate


    # -----------------------------
    # 3. 再上一级（脚本被放在
    #    workspace/scripts 外的
    #    备用位置）
    # -----------------------------

    candidate2 = (
        current
        .parent
        .parent
        .parent
        .parent
    )

    if (candidate2 / "workspace").exists():

        return candidate2


    return None



# =====================================================
# Boot
# =====================================================

WORKSPACE = _find_workspace()


if WORKSPACE is not None:

    if str(WORKSPACE) not in sys.path:

        sys.path.append(
            str(WORKSPACE)
        )


    print(
        "RhinoWorkspace Startup Loaded"
    )

    print(
        f"Workspace: {WORKSPACE}"
    )


    # -------------------------------------------------
    # Auto-load Toolbars (.rui)
    #
    #  macOS Rhino does NOT auto-discover .rui files
    #  from the UI folder.
    #
    #  We explicitly open them on idle to make sure
    #  Rhino is fully initialized first.
    # -------------------------------------------------

    def _load_toolbars(sender, args):

        import Rhino

        toolbar_folder = (
            WORKSPACE / "workspace" / "toolbar"
        )

        if toolbar_folder.exists():

            for rui in toolbar_folder.glob("*.rui"):

                cmd = (
                    '_-Toolbar _Open "{}"'
                    .format(rui)
                )

                print(
                    "Loading toolbar: {}".format(rui.name)
                )

                Rhino.RhinoApp.RunScript(cmd, False)


    try:

        import Rhino

        Rhino.RhinoApp.Idle += _load_toolbars

    except ImportError:

        print(
            "RhinoWorkspace: "
            "Not inside Rhino (dev mode)."
        )

else:

    print(
        "RhinoWorkspace Startup: "
        "Workspace not found. "
        "Run sync once to install workspace marker."
    )
