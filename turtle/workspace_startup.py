import rhinoscriptsyntax as rs

import os


def import_aliases():


    folder = os.path.expanduser(
        "~/RhinoWorkspace/workspace/aliases"
    )


    files = os.listdir(folder)


    for f in files:


        if f.endswith(".txt"):


            path=os.path.join(
                folder,
                f
            )


            rs.Command(
                '_-ImportAlias "{}" _Enter'.format(path)
            )



import_aliases()