import sys

import qt
import slicer


def print_line(message):
    print(message)
    sys.stdout.flush()


def dump_render_window(label, render_window):
    print_line(f"=== {label} ===")
    if not render_window:
        print_line("RenderWindow: unavailable")
        return

    render_window.Render()
    print_line(f"RenderWindow class: {render_window.GetClassName()}")

    capabilities = render_window.ReportCapabilities()
    if capabilities:
        print_line(capabilities.rstrip())
    else:
        print_line("ReportCapabilities(): empty")


def run_probe():
    layout_manager = slicer.app.layoutManager()
    if not layout_manager:
        print_line("Layout manager: unavailable")
        qt.QTimer.singleShot(0, slicer.app.quit)
        return

    three_d_widget = layout_manager.threeDWidget(0)
    if three_d_widget:
        dump_render_window("3D view 0", three_d_widget.threeDView().renderWindow())
    else:
        print_line("=== 3D view 0 ===")
        print_line("3D widget: unavailable")

    slice_names = []
    try:
        slice_names = list(layout_manager.sliceViewNames())
    except Exception:
        slice_names = []

    preferred_slice = "Red" if "Red" in slice_names else (slice_names[0] if slice_names else None)
    if preferred_slice:
        dump_render_window(
            f"Slice view {preferred_slice}",
            layout_manager.sliceWidget(preferred_slice).sliceView().renderWindow(),
        )
    else:
        print_line("=== Slice view ===")
        print_line("Slice widget: unavailable")

    qt.QTimer.singleShot(0, slicer.app.quit)


qt.QTimer.singleShot(0, run_probe)
