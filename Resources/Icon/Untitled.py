# -*- coding: utf-8 -*-

import Rhino
import scriptcontext as sc
import System


def sync_perspective_object_display_to_detail():

    doc = sc.doc

    print("")
    print("==========================================")
    print("Perspective to Detail")
    print("Object Display Mode Override")
    print("==========================================")

    # =========================================================
    # 1. Current Layout
    # =========================================================

    active_view = doc.Views.ActiveView

    if active_view is None:

        print("No active view.")
        return

    if not isinstance(
        active_view,
        Rhino.Display.RhinoPageView
    ):

        print("")
        print("Current view is not a Layout page.")
        return

    # =========================================================
    # 2. Find Detail
    # =========================================================

    details = []

    try:

        for detail in active_view.GetDetailViews():

            if detail is not None:
                details.append(detail)

    except Exception as e:

        print(
            "Cannot get Detail views: {}".format(
                e
            )
        )

        return

    if len(details) == 0:

        print("")
        print("No Detail found on current Layout.")
        return

    if len(details) != 1:

        print("")
        print(
            "Found {} Details.".format(
                len(details)
            )
        )

        print(
            "This version requires exactly one Detail."
        )

        return

    detail = details[0]

    # =========================================================
    # 3. Target Detail Viewport
    # =========================================================

    try:

        target_viewport = detail.Viewport

    except Exception as e:

        print(
            "Cannot get Detail viewport: {}".format(
                e
            )
        )

        return

    if target_viewport is None:

        print("Detail viewport is None.")
        return

    target_id = target_viewport.Id

    print("")
    print("TARGET DETAIL")
    print("------------------------------------------")

    print(
        "Viewport Name: {}".format(
            target_viewport.Name
        )
    )

    print(
        "Viewport ID: {}".format(
            target_id
        )
    )

    # =========================================================
    # 4. Find Model Perspective
    # =========================================================

    source_viewport = None

    print("")
    print("SEARCH MODEL PERSPECTIVE")
    print("------------------------------------------")

    for view in doc.Views:

        if isinstance(
            view,
            Rhino.Display.RhinoPageView
        ):
            continue

        try:

            vp = view.ActiveViewport

            if vp is None:
                continue

            print(
                "Viewport: {}  ID: {}  Perspective: {}".format(
                    vp.Name,
                    vp.Id,
                    vp.IsPerspectiveProjection
                )
            )

            if vp.IsPerspectiveProjection:

                source_viewport = vp
                break

        except Exception:

            continue

    if source_viewport is None:

        print("")
        print("Model Perspective not found.")
        return

    source_id = source_viewport.Id

    print("")
    print("SOURCE")
    print("------------------------------------------")

    print(
        "Viewport Name: {}".format(
            source_viewport.Name
        )
    )

    print(
        "Viewport ID: {}".format(
            source_id
        )
    )

    # =========================================================
    # 5. Synchronize
    # =========================================================

    copied = 0
    cleared = 0
    failed = 0

    print("")
    print("SYNC OBJECT OVERRIDES")
    print("------------------------------------------")

    for obj in doc.Objects:

        if obj is None:
            continue

        attr = obj.Attributes

        # =====================================================
        # CASE A
        # Perspective has an Override
        # =====================================================

        if attr.HasDisplayModeOverride(source_id):

            mode_id = attr.GetDisplayModeOverride(
                source_id
            )

            if mode_id == System.Guid.Empty:

                continue

            mode = (
                Rhino.Display.DisplayModeDescription
                .GetDisplayMode(mode_id)
            )

            if mode is None:

                print(
                    "DisplayMode not found: {}".format(
                        mode_id
                    )
                )

                failed += 1
                continue

            new_attr = attr.Duplicate()

            try:

                # IMPORTANT:
                # Rhino 8 Mac may return False even when
                # the override was actually set.
                #
                # Therefore DO NOT use the return value.

                new_attr.SetDisplayModeOverride(
                    mode,
                    target_id
                )

                # Check actual state

                if new_attr.HasDisplayModeOverride(
                    target_id
                ):

                    result = doc.Objects.ModifyAttributes(
                        obj.Id,
                        new_attr,
                        True
                    )

                    if result:

                        copied += 1

                        print(
                            "COPIED: {} -> {}".format(
                                obj.Id,
                                mode.EnglishName
                            )
                        )

                    else:

                        print(
                            "ModifyAttributes failed: {}".format(
                                obj.Id
                            )
                        )

                        failed += 1

                else:

                    print(
                        "Override was not created: {}".format(
                            obj.Id
                        )
                    )

                    failed += 1

            except Exception as e:

                print(
                    "Copy failed {}: {}".format(
                        obj.Id,
                        e
                    )
                )

                failed += 1

        # =====================================================
        # CASE B
        # Perspective has NO Override
        #
        # Remove stale Detail Override
        # =====================================================

        else:

            if attr.HasDisplayModeOverride(
                target_id
            ):

                new_attr = attr.Duplicate()

                try:

                    new_attr.RemoveDisplayModeOverride(
                        target_id
                    )

                    # Check actual state

                    if not new_attr.HasDisplayModeOverride(
                        target_id
                    ):

                        result = doc.Objects.ModifyAttributes(
                            obj.Id,
                            new_attr,
                            True
                        )

                        if result:

                            cleared += 1

                            print(
                                "CLEARED: {}".format(
                                    obj.Id
                                )
                            )

                        else:

                            failed += 1

                    else:

                        print(
                            "Override was not removed: {}".format(
                                obj.Id
                            )
                        )

                        failed += 1

                except Exception as e:

                    print(
                        "Clear failed {}: {}".format(
                            obj.Id,
                            e
                        )
                    )

                    failed += 1

    # =========================================================
    # 6. Redraw
    # =========================================================

    doc.Views.Redraw()

    # =========================================================
    # 7. Result
    # =========================================================

    print("")
    print("==========================================")
    print("SYNC COMPLETE")
    print("------------------------------------------")

    print(
        "Copied Overrides: {}".format(
            copied
        )
    )

    print(
        "Cleared Overrides: {}".format(
            cleared
        )
    )

    print(
        "Failed: {}".format(
            failed
        )
    )

    print("==========================================")
    print("")


if __name__ == "__main__":

    sync_perspective_object_display_to_detail()