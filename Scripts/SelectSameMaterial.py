# -*- coding: utf-8 -*-
#
# Select Same Material (simple version)
#
# 1. Pick one reference object (or use the current selection,
#    if exactly one object is already selected).
# 2. Every object in the document that shares the same material
#    is selected automatically. No window pick needed.

import Rhino
import rhinoscriptsyntax as rs


# ============================================================
# Material identity
# ============================================================
#
# Rhino has two material systems that can both be in play:
#
#   1) The modern "Render Material" (PBR / render content,
#      assigned via the Materials panel). This is the default
#      workflow since Rhino 6, and what most scenes actually
#      use.
#
#   2) The legacy "simple material" table, addressed via
#      Attributes.MaterialIndex (object) or
#      Layer.RenderMaterialIndex (layer).
#
# We prefer the RenderMaterial's persistent Id, since that is
# what is actually shared across objects/layers that use the
# same material. We fall back to the legacy index only when
# there is no RenderMaterial.
# ============================================================

def get_material_key(doc, obj):

    try:
        source = obj.Attributes.MaterialSource
    except:
        source = None

    render_material = None
    legacy_index = -1

    try:

        if source == Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer:

            layer_index = obj.Attributes.LayerIndex

            if layer_index >= 0:

                layer = doc.Layers[layer_index]

                if layer is not None:

                    try:
                        render_material = layer.RenderMaterial
                    except:
                        render_material = None

                    legacy_index = layer.RenderMaterialIndex

        else:

            # MaterialFromObject, MaterialFromParent, or unknown:
            # treat as the object's own assignment.

            try:
                render_material = obj.RenderMaterial
            except:
                render_material = None

            legacy_index = obj.Attributes.MaterialIndex

    except:
        pass

    if render_material is not None:

        try:
            return ("render", render_material.Id)
        except:
            pass

    return ("legacy", legacy_index)


# ============================================================
# Main command
# ============================================================

def SelectSameMaterial():

    doc = Rhino.RhinoDoc.ActiveDoc

    if doc is None:
        return

    # --------------------------------------------------------
    # STEP 1: Get reference object
    # --------------------------------------------------------

    selected = rs.SelectedObjects()

    if selected and len(selected) == 1:

        reference_id = selected[0]
        reference = doc.Objects.Find(reference_id)

    else:

        reference_id = rs.GetObject(
            "Select reference object (material to match)",
            preselect=False,
            select=True
        )

        if not reference_id:
            return

        reference = doc.Objects.Find(reference_id)

    if reference is None:
        return

    reference_key = get_material_key(doc, reference)

    # --------------------------------------------------------
    # STEP 2: Clear current selection
    # --------------------------------------------------------

    rs.UnselectAllObjects()

    # --------------------------------------------------------
    # STEP 3: Walk every object in the document and select
    # the ones with a matching material.
    # --------------------------------------------------------

    matched_ids = []

    for obj in doc.Objects:

        try:

            if obj is None:
                continue

            if not obj.IsSelectable(True, False, False, False):
                continue

            if get_material_key(doc, obj) == reference_key:

                obj.Select(True)
                matched_ids.append(obj.Id)

        except:
            continue

    doc.Views.Redraw()

    # --------------------------------------------------------
    # STEP 4: Report
    # --------------------------------------------------------

    print("")
    print("Select Same Material")
    print("------------------------------")
    print("Reference Material: {}".format(reference_key))
    print("Matched objects: {}".format(len(matched_ids)))
    print("------------------------------")


SelectSameMaterial()
