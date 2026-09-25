# -*- coding: utf-8 -*-

import Rhino
import rhinoscriptsyntax as rs
import Eto.Forms as forms
import Eto.Drawing as drawing


# ============================================================
# Object information
# ============================================================

def get_object_type_name(obj):

    if obj is None:
        return "Unknown"

    try:
        geo = obj.Geometry

        if isinstance(geo, Rhino.Geometry.Curve):
            return "Curve"

        if isinstance(geo, Rhino.Geometry.Brep):
            return "Brep"

        if isinstance(geo, Rhino.Geometry.Mesh):
            return "Mesh"

        if isinstance(geo, Rhino.Geometry.SubD):
            return "SubD"

        if isinstance(geo, Rhino.Geometry.Point):
            return "Point"

        if isinstance(geo, Rhino.Geometry.PointCloud):
            return "PointSet"

        if isinstance(geo, Rhino.Geometry.Extrusion):
            return "Extrusion"

        if isinstance(geo, Rhino.Geometry.AnnotationBase):
            return "Annotation"

        if isinstance(geo, Rhino.Geometry.Hatch):
            return "Hatch"

    except:
        pass

    return "Unknown"


def get_object_color(obj):

    try:
        return obj.Attributes.ObjectColor
    except:
        return None


def get_layer_name(doc, obj):

    try:
        layer_index = obj.Attributes.LayerIndex

        if layer_index >= 0:
            layer = doc.Layers[layer_index]

            if layer is not None:
                return layer.FullPath

    except:
        pass

    return ""


def get_linetype_name(doc, obj):

    try:
        index = obj.Attributes.LinetypeIndex

        if index >= 0:
            linetype = doc.Linetypes[index]

            if linetype is not None:
                return linetype.Name

    except:
        pass

    return ""


def get_lineweight(obj):

    try:
        return obj.Attributes.PlotWeight
    except:
        return -1.0


def get_material(obj):

    try:
        return obj.Attributes.MaterialIndex
    except:
        return -1


# ============================================================
# Comparison
# ============================================================

def colors_equal(c1, c2):

    if c1 is None or c2 is None:
        return False

    try:
        return (
            c1.R == c2.R and
            c1.G == c2.G and
            c1.B == c2.B and
            c1.A == c2.A
        )
    except:
        return False


def values_equal(a, b):

    try:
        return abs(float(a) - float(b)) < 0.0001
    except:
        return a == b


# ============================================================
# Object matching
# ============================================================

def object_matches(doc, reference, candidate, filters):

    if reference is None or candidate is None:
        return False

    # --------------------------------------------------------
    # Object Type
    # Always enabled
    # --------------------------------------------------------

    ref_type = get_object_type_name(reference)
    obj_type = get_object_type_name(candidate)

    if ref_type != obj_type:
        return False

    # --------------------------------------------------------
    # Color
    # --------------------------------------------------------

    if "Color" in filters:

        ref_color = get_object_color(reference)
        obj_color = get_object_color(candidate)

        if not colors_equal(ref_color, obj_color):
            return False

    # --------------------------------------------------------
    # Layer
    # --------------------------------------------------------

    if "Layer" in filters:

        ref_layer = get_layer_name(doc, reference)
        obj_layer = get_layer_name(doc, candidate)

        if ref_layer != obj_layer:
            return False

    # --------------------------------------------------------
    # Linetype
    # --------------------------------------------------------

    if "Linetype" in filters:

        ref_linetype = get_linetype_name(doc, reference)
        obj_linetype = get_linetype_name(doc, candidate)

        if ref_linetype != obj_linetype:
            return False

    # --------------------------------------------------------
    # Lineweight
    # --------------------------------------------------------

    if "Lineweight" in filters:

        ref_weight = get_lineweight(reference)
        obj_weight = get_lineweight(candidate)

        if not values_equal(ref_weight, obj_weight):
            return False

    # --------------------------------------------------------
    # Material
    # --------------------------------------------------------

    if "Material" in filters:

        ref_material = get_material(reference)
        obj_material = get_material(candidate)

        if ref_material != obj_material:
            return False

    return True


# ============================================================
# Filter Dialog
# ============================================================

class FilterDialog(forms.Dialog):

    def __init__(self):

        forms.Dialog.__init__(self)

        self.Title = "Filter Select"

        self.ClientSize = drawing.Size(300, 245)

        self.Padding = drawing.Padding(12)

        self.selected_filters = []

        self.result_ok = False

        # ----------------------------------------------------
        # Checkboxes
        # ----------------------------------------------------

        self.color_checkbox = forms.CheckBox()
        self.color_checkbox.Text = "Color"

        self.layer_checkbox = forms.CheckBox()
        self.layer_checkbox.Text = "Layer"

        self.linetype_checkbox = forms.CheckBox()
        self.linetype_checkbox.Text = "Linetype"

        self.lineweight_checkbox = forms.CheckBox()
        self.lineweight_checkbox.Text = "Lineweight"

        self.material_checkbox = forms.CheckBox()
        self.material_checkbox.Text = "Material"

        # ----------------------------------------------------
        # Buttons
        # ----------------------------------------------------

        self.ok_button = forms.Button()
        self.ok_button.Text = "OK"

        self.cancel_button = forms.Button()
        self.cancel_button.Text = "Cancel"

        self.ok_button.Click += self.on_ok
        self.cancel_button.Click += self.on_cancel

        # ----------------------------------------------------
        # Layout
        # ----------------------------------------------------

        layout = forms.DynamicLayout()

        layout.Spacing = drawing.Size(6, 6)

        layout.AddRow(self.color_checkbox)

        layout.AddRow(self.layer_checkbox)

        layout.AddRow(self.linetype_checkbox)

        layout.AddRow(self.lineweight_checkbox)

        layout.AddRow(self.material_checkbox)

        layout.AddRow(None)

        buttons = forms.StackLayout()

        buttons.Orientation = forms.Orientation.Horizontal

        buttons.Spacing = 8

        buttons.Items.Add(None)

        buttons.Items.Add(self.ok_button)

        buttons.Items.Add(self.cancel_button)

        layout.AddRow(buttons)

        self.Content = layout

        # ----------------------------------------------------
        # Enter / Escape
        #
        # Eto native handling
        # ----------------------------------------------------

        self.DefaultButton = self.ok_button

        self.AbortButton = self.cancel_button

        # ----------------------------------------------------
        # IMPORTANT
        #
        # We do NOT use KeyDown here.
        #
        # Space is intentionally not intercepted.
        # The OK button gets initial focus.
        # On macOS, Space can then activate the focused
        # native button without our code handling the event.
        # ----------------------------------------------------

        self.Shown += self.on_shown

    # ========================================================
    # Dialog shown
    # ========================================================

    def on_shown(self, sender, e):

        try:
            self.ok_button.Focus()
        except:
            pass

    # ========================================================
    # OK
    # ========================================================

    def on_ok(self, sender, e):

        self.selected_filters = []

        if self.color_checkbox.Checked:
            self.selected_filters.append("Color")

        if self.layer_checkbox.Checked:
            self.selected_filters.append("Layer")

        if self.linetype_checkbox.Checked:
            self.selected_filters.append("Linetype")

        if self.lineweight_checkbox.Checked:
            self.selected_filters.append("Lineweight")

        if self.material_checkbox.Checked:
            self.selected_filters.append("Material")

        # Object Type is always enabled
        self.selected_filters.append("ObjectType")

        self.result_ok = True

        self.Close()

    # ========================================================
    # Cancel
    # ========================================================

    def on_cancel(self, sender, e):

        self.result_ok = False

        self.selected_filters = []

        self.Close()


# ============================================================
# Show dialog
# ============================================================

def show_filter_dialog():

    dialog = FilterDialog()

    # IMPORTANT:
    # Do not pass RhinoView.
    # ShowModal() is stable on Rhino Mac.
    # --------------------------------------------------------

    dialog.ShowModal()

    if dialog.result_ok:
        return dialog.selected_filters

    return None


# ============================================================
# Real-time filtered GetObject
# ============================================================

class FilteredGetObject(Rhino.Input.Custom.GetObject):

    def __init__(self, doc, reference, filters):

        Rhino.Input.Custom.GetObject.__init__(self)

        self.doc = doc

        self.reference = reference

        self.filters = filters

    # ========================================================
    # Real-time filter
    # ========================================================

    def CustomGeometryFilter(
        self,
        rhino_object,
        geometry,
        component_index
    ):

        try:

            if rhino_object is None:
                return False

            return object_matches(
                self.doc,
                self.reference,
                rhino_object,
                self.filters
            )

        except:

            return False


# ============================================================
# Main command
# ============================================================

def FilterSelectV2():

    doc = Rhino.RhinoDoc.ActiveDoc

    if doc is None:
        return

    # ========================================================
    # STEP 1
    # Get reference object
    # ========================================================

    selected = rs.SelectedObjects()

    reference = None

    # --------------------------------------------------------
    # If exactly one object is already selected,
    # use it as reference.
    # --------------------------------------------------------

    if selected and len(selected) == 1:

        reference_id = selected[0]

        reference = doc.Objects.Find(reference_id)

    else:

        reference_id = rs.GetObject(
            "Select reference object",
            preselect=False,
            select=True
        )

        if not reference_id:
            return

        reference = doc.Objects.Find(reference_id)

    if reference is None:
        return

    # ========================================================
    # Print reference information
    # ========================================================

    print("")
    print("Filter Select")
    print("------------------------------")

    print(
        "Reference Type: {}".format(
            get_object_type_name(reference)
        )
    )

    print(
        "Reference Layer: {}".format(
            get_layer_name(doc, reference)
        )
    )

    print(
        "Reference Linetype: {}".format(
            get_linetype_name(doc, reference)
        )
    )

    print(
        "Reference Lineweight: {}".format(
            get_lineweight(reference)
        )
    )

    print(
        "Reference Material Index: {}".format(
            get_material(reference)
        )
    )

    # ========================================================
    # STEP 2
    # Clear reference selection
    # ========================================================

    rs.UnselectAllObjects()

    # ========================================================
    # STEP 3
    # Show filter dialog
    # ========================================================

    filters = show_filter_dialog()

    if filters is None:
        return

    print("")
    print("Filters:")

    for f in filters:
        print("  " + f)

    # ========================================================
    # STEP 4
    # Create filtered GetObject
    # ========================================================

    go = FilteredGetObject(
        doc,
        reference,
        filters
    )

    go.SetCommandPrompt(
        "Select matching objects"
    )

    # --------------------------------------------------------
    # Selection settings
    # --------------------------------------------------------

    go.SubObjectSelect = False

    go.GroupSelect = True

    go.EnablePreSelect(True, True)

    go.EnablePostSelect(True)

    go.EnableAlreadySelectedObjectSelect = True

    # --------------------------------------------------------
    # Keep selection after finishing
    # --------------------------------------------------------

    go.EnableUnselectObjectsOnExit(False)

    go.EnableClearObjectsOnEntry(False)

    go.DeselectAllBeforePostSelect = False

    # ========================================================
    # STEP 5
    # Real-time selection
    #
    # Minimum = 1
    # Maximum = 0 = unlimited
    # ========================================================

    result = go.GetMultiple(1, 0)

    # ========================================================
    # Check command result
    # ========================================================

    if go.CommandResult() != Rhino.Commands.Result.Success:
        return

    if result != Rhino.Input.GetResult.Object:
        return

    # ========================================================
    # STEP 6
    # Get selected objects
    # ========================================================

    objects = go.Objects()

    if objects is None:
        return

    # ========================================================
    # Explicitly select returned objects
    # ========================================================

    count = 0

    for objref in objects:

        try:

            obj = objref.Object()

            if obj is not None:

                obj.Select(True)

                count += 1

        except:

            pass

    # ========================================================
    # Redraw
    # ========================================================

    doc.Views.Redraw()

    # ========================================================
    # Result
    # ========================================================

    print("")
    print("------------------------------")
    print(
        "Matched objects: {}".format(count)
    )
    print("------------------------------")
    print("")


# ============================================================
# Run
# ============================================================

FilterSelectV2()