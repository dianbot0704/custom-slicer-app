"""Drive real PythonQt widgets inside Slicer. Invoked only by verify-app.py."""

# ruff: noqa: S101, PLR2004 - assertions and literal expected values are the verification contract
from __future__ import annotations

import json
import os
import time
import traceback
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import qt
import slicer
import vtk
from vtk.util.numpy_support import vtk_to_numpy

OUTPUT_DIR = Path(os.environ["AKSARATOR_VERIFY_OUTPUT"])
SANDBOX_DIR = Path(os.environ["AKSARATOR_VERIFY_SANDBOX"])
SCENARIO_REPORT = {"run_id": os.environ["AKSARATOR_VERIFY_RUN_ID"], "completed": False, "checks": [], "runtime": {}}

GENERAL_ACCESS_PIN = "000000"
REJECTED_PIN = "999999"


def save_report() -> None:
    checkpoint_path = OUTPUT_DIR / "scenario.json"
    temporary_path = checkpoint_path.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(SCENARIO_REPORT, indent=2) + "\n", encoding="utf-8")
    temporary_path.replace(checkpoint_path)


def wait_for(predicate: Callable[[], bool], description: str, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        slicer.app.processEvents()
        if predicate():
            return
        time.sleep(0.02)
    raise RuntimeError(f"Timed out waiting for {description}")


def screenshot(name: str) -> str:
    slicer.app.processEvents()
    filename = f"{name}.png"
    window_image = slicer.util.mainWindow().grab()
    if window_image.isNull() or not window_image.save(str(OUTPUT_DIR / filename), "PNG"):
        raise RuntimeError(f"Could not save {filename}")
    return filename


@contextmanager
def check(name: str) -> Iterator[dict]:
    entry = {"name": name, "status": "running"}
    SCENARIO_REPORT["checks"].append(entry)
    save_report()
    start = time.monotonic()
    try:
        yield entry
        entry["screenshot"] = screenshot(name)
        entry["status"] = "passed"
        print(f"PASS {name}", flush=True)
    except Exception:
        entry["status"] = "failed"
        entry["error"] = traceback.format_exc()
        try:
            entry["screenshot"] = screenshot(f"{name}-failed")
        except Exception as exc:
            entry["screenshot_error"] = str(exc)
        raise
    finally:
        entry["duration_seconds"] = round(time.monotonic() - start, 3)
        save_report()


def click(button: qt.QPushButton) -> None:
    assert button is not None, "Button is missing"
    assert button.isVisible(), f"Button is not visible: {button.objectName}"
    assert button.isEnabled(), f"Button is disabled: {button.objectName}"
    button.click()
    slicer.app.processEvents()


def enter_pin(page: qt.QWidget, pin: str) -> None:
    buttons = slicer.util.findChildren(page, name="pinKey")
    digit_buttons = {str(button.text): button for button in buttons}
    for digit in pin:
        assert digit in digit_buttons, f"PIN key {digit} is missing"
        click(digit_buttons[digit])


def expect_page(module_widget, page: qt.QWidget) -> None:  # noqa: ANN001
    page_stack = module_widget.ui.pagesStackedWidget
    wait_for(lambda: page_stack.currentWidget() == page, f"page {page.objectName}")
    assert page.isVisible(), f"Active page is hidden: {page.objectName}"


def click_to_page(module_widget, button: qt.QPushButton, page: qt.QWidget) -> None:  # noqa: ANN001
    """Click a visible, enabled button and verify the resulting page."""
    click(button)
    expect_page(module_widget, page)


def expect_forward_blocked(
    module_widget,  # noqa: ANN001 - Slicer's dynamically loaded IntraopPlannerWidget
    next_button: qt.QPushButton,
    page: qt.QWidget,
    reason: str,
) -> None:
    """A disabled Next button must also leave the current page unchanged."""
    assert not next_button.isEnabled(), reason
    next_button.click()
    expect_page(module_widget, page)


def run() -> None:  # noqa: PLR0915
    with check("startup-and-page-construction") as entry:
        # Do not select the module here: startup must have selected it itself.
        wait_for(lambda: slicer.util.selectedModule() == "IntraopPlanner", "default IntraopPlanner selection")
        module_path = Path(slicer.util.modulePath("IntraopPlanner")).resolve()
        assert module_path.parent == SANDBOX_DIR / "module", f"Wrong runtime selected: {module_path}"
        import verification_support as ui_fixtures  # noqa: PLC0415 - verify sandbox selection before import
        from Runtime import IntraopPlannerImpl as runtime  # noqa: PLC0415

        widget = slicer.modules.intraopplanner.widgetRepresentation().self()
        assert widget is not None, "IntraopPlanner widget did not initialize"
        expect_page(widget, widget.splashWidget)
        main_window = slicer.util.mainWindow()
        main_window.showNormal()
        main_window.resize(1920, 1080)
        slicer.app.processEvents()
        controllers = (
            "splashStep",
            "generalPinStep",
            "preloginStep",
            "loginStep",
            "dummySpineStep",
            "toolsVerificationStep",
            "scanPatientStep",
            "fluoroCaptureStep",
            "planStep",
            "navigateStep",
            "patientSettingsStep",
            "surgeonSettingsStep",
        )
        for controller in controllers:
            assert getattr(widget, controller, None) is not None, f"Controller failed to initialize: {controller}"
        assert len(widget._pageHeaders) == 6, "Not all workflow pages have navigation headers"
        assert widget.registrationManager.patient_database.get_all_patients() == []
        assert getattr(slicer, "dicomDatabase", None) is None, "DICOM database unexpectedly initialized"
        SCENARIO_REPORT["runtime"] = {
            "application_version": str(slicer.app.applicationVersion),
            "python_runtime": str(runtime.__file__),
            "compiled_runtime": any(Path(runtime.__file__).parent.glob("IntraopPlannerImpl*.so")),
            "import_spec": str(runtime.__spec__),
            "module_path": str(module_path),
        }
        entry["controllers"] = list(controllers)
        if os.environ.get("AKSARATOR_VERIFY_FORCE_FAILURE") == "1":
            raise RuntimeError("Intentional verification failure (--force-failure)")

    with check("general-pin-reject-and-cancel"):
        start_button = widget.splashWidget.findChild(qt.QPushButton, "startButton")
        click_to_page(widget, start_button, widget.generalPinWidget)
        enter_pin(widget.generalPinWidget, REJECTED_PIN)
        expect_page(widget, widget.generalPinWidget)
        assert "Wrong PIN" in widget.generalPinStep.ui.pinErrorLabel.text
        assert widget.generalPinStep.ui.pinInput.text == "", "Rejected PIN was not cleared"
        screenshot("general-pin-rejected")
        click_to_page(widget, widget.generalPinStep.ui.pinBackButton, widget.splashWidget)

    for target, page, header in (
        ("patient", widget.patientSettingsWidget, widget.patientSettingsHeader),
        ("surgeon", widget.surgeonSettingsWidget, widget.surgeonSettingsHeader),
    ):
        with check(f"{target}-settings-pin-and-return"):
            click(widget.splashWidget.findChild(qt.QPushButton, "settingsButton"))
            menu = widget.splashStep.settingsMenu
            settings_row = menu.patientSettingsRow if target == "patient" else menu.surgeonSettingsRow
            click_to_page(widget, settings_row, widget.generalPinWidget)
            enter_pin(widget.generalPinWidget, GENERAL_ACCESS_PIN)
            expect_page(widget, page)
            screenshot(f"{target}-settings-page")
            click_to_page(widget, header.backButton, widget.splashWidget)

    with check("surgeon-picker-search"):
        click(widget.splashWidget.findChild(qt.QPushButton, "startButton"))
        enter_pin(widget.generalPinWidget, GENERAL_ACCESS_PIN)
        expect_page(widget, widget.preloginWidget)
        search = widget.preloginStep.ui.searchSurgeonInput
        search.setText("no-matching-account")
        slicer.app.processEvents()
        assert not slicer.util.findChildren(widget.preloginWidget, name="surgeonCard"), "Search did not filter cards"
        search.setText("Automation")
        slicer.app.processEvents()
        cards = slicer.util.findChildren(widget.preloginWidget, name="surgeonCard")
        assert len(cards) == 1, "Synthetic account not found"
        click_to_page(widget, cards[0], widget.loginWidget)
        assert widget.loginStep.ui.loginNameLabel.text == "Automation User"

    with check("surgeon-pin-reject"):
        enter_pin(widget.loginWidget, REJECTED_PIN)
        expect_page(widget, widget.loginWidget)
        assert "Wrong PIN" in widget.loginStep.ui.pinErrorLabel.text
        assert widget.sessionManager.session is None, "Failed login created a session"
        assert widget.loginStep.ui.pinInput.text == "", "Rejected PIN was not cleared"

    with check("surgeon-login-and-disclaimer") as entry:
        # The sixth digit opens a modal dialog. Drive it from a bounded timer
        # running in that dialog's event loop. Do not bypass its Agree gate.
        dialog_state = {"seen": False, "agreed": False, "error": None}
        deadline = time.monotonic() + 10
        timer = qt.QTimer()

        def handle_disclaimer() -> None:
            dialog = qt.QApplication.activeModalWidget()
            try:
                assert time.monotonic() < deadline, "Disclaimer did not become ready within 10s"
                if dialog is None or dialog.objectName != "disclaimerDialog":
                    return
                agree_button = next(
                    button
                    for button in slicer.util.findChildren(dialog)
                    if isinstance(button, qt.QPushButton) and button.text == "Agree"
                )
                if not dialog_state["seen"]:
                    assert not agree_button.isEnabled(), "Agree was enabled before scrolling"
                    dialog_state["seen"] = True
                    entry["disclaimer_screenshot"] = screenshot("disclaimer")
                    scroll_area = dialog.findChild(qt.QScrollArea, "appPopupScroll")
                    scroll_bar = scroll_area.verticalScrollBar()
                    scroll_bar.setValue(scroll_bar.maximum)
                    return
                assert agree_button.isEnabled(), "Agree did not become enabled after scrolling"
                timer.stop()
                agree_button.click()
                dialog_state["agreed"] = True
            except Exception:
                dialog_state["error"] = traceback.format_exc()
                timer.stop()
                if dialog:
                    dialog.reject()

        timer.timeout.connect(handle_disclaimer)
        timer.start(50)
        try:
            enter_pin(widget.loginWidget, ui_fixtures.FIXTURE_PIN)
        finally:
            timer.stop()
        assert not dialog_state["error"], dialog_state["error"]
        assert dialog_state["seen"], "Disclaimer was not shown"
        assert dialog_state["agreed"], "Disclaimer was not accepted through its button"
        assert widget.sessionManager.session.username == ui_fixtures.FIXTURE_SURGEON.username
        expect_page(widget, widget.workflow_page)
        assert ui_fixtures.DISABLED_START_CALLS["camera_start"] > 0, (
            "Camera start did not pass through the safety fixture"
        )
        assert widget.cameraWorker._camera is None, "Native camera was unexpectedly initialized"

    with check("intraop-navigation-and-scan-gate"):
        workflow_buttons = slicer.util.findChildren(widget.workflow_page, name="wfStartButton")
        intraop_button = next(button for button in workflow_buttons if button.property("accent") == "blue")
        click_to_page(widget, intraop_button, widget.levelSelectionWidget)
        assert widget._activeWorkflowId == "intraop"
        assert len(widget._stepHeaders) == 5
        level_header, verification_header, scan_header, plan_header, navigate_header = widget._stepHeaders

        click_to_page(widget, level_header.nextButton, widget.verificationWidget)
        click_to_page(widget, verification_header.nextButton, widget.scanPatientWidget)
        expect_forward_blocked(
            widget, scan_header.nextButton, widget.scanPatientWidget, "Plan is available without a registered CT"
        )

    with check("plan-preview-synthetic-render") as entry:
        entry["scope"] = "Direct page preview, not a clinical workflow; Scan Patient gate remains unmodified"

        # Generate a volume with a known scalar range and no patient data.
        volume_source = vtk.vtkRTAnalyticSource()
        volume_source.SetWholeExtent(0, 48, 0, 48, 0, 48)
        volume_source.SetCenter(24, 24, 24)
        volume_source.Update()
        synthetic_volume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", "VerificationSyntheticCT")
        synthetic_volume.SetOrigin(-24, -24, -24)
        synthetic_volume.SetAndObserveImageData(volume_source.GetOutput())
        synthetic_volume.CreateDefaultDisplayNodes()
        volume_display = synthetic_volume.GetDisplayNode()
        volume_display.AutoWindowLevelOff()
        volume_display.SetWindowLevel(250, 125)

        # Page preview is explicit: never weaken canAdvance() to get past the
        # registration gate. Exercise Plan's real onEnter and MRML view setup.
        widget._switchToPage(widget._planIndex)
        expect_page(widget, widget.planWidget)
        plan_step = widget.planStep
        assert plan_step.viewsCreated, "Plan's independent views were not created"
        assert len(plan_step.mrmlWidgets) == 4, "Plan did not create all four views"
        assert plan_step.loaded_volume_node == synthetic_volume, "Plan did not pick up the synthetic volume"

        # Plan schedules a second CT camera setup after 500 ms. Drain that
        # documented delayed work before framing the synthetic model as well.
        camera_ready_at = time.monotonic() + 0.75
        wait_for(lambda: time.monotonic() >= camera_ready_at, "Plan's deferred camera setup")
        for frame in ("frame_axial", "frame_sagittal", "frame_coronal"):
            slice_logic = plan_step.mrmlWidgets[frame].sliceLogic()
            composite_node = slice_logic.GetSliceCompositeNode()
            assert composite_node.GetBackgroundVolumeID(), f"No volume displayed in {frame}"

        # Place the sphere outside the opaque volume so both objects are visible.
        sphere_source = vtk.vtkSphereSource()
        sphere_source.SetRadius(12)
        sphere_source.SetCenter(70, 0, 0)
        sphere_source.Update()
        sphere_model = slicer.modules.models.logic().AddModel(sphere_source.GetOutputPort())
        sphere_model.SetName("VerificationSyntheticSphere")
        sphere_display = sphere_model.GetDisplayNode()
        sphere_display.SetColor(0.9, 0.2, 0.1)
        sphere_display.SetViewNodeIDs([plan_step._threeDViewNode.GetID()])

        three_d_view = plan_step._threeDWidget.threeDView()
        slicer.app.processEvents()
        render_window = three_d_view.renderWindow()
        render_window.GetRenderers().GetFirstRenderer().ResetCamera()
        plan_step.fitSlicesToWindow()
        slicer.app.processEvents()

        # Qt owns vtkGenericOpenGLRenderWindow's context. Its SupportsOpenGL()
        # flag is unset in this build even with a valid context; verify pixels.
        three_d_view.forceRender()
        slicer.app.processEvents()
        window_capture = vtk.vtkWindowToImageFilter()
        window_capture.SetInput(render_window)
        window_capture.ReadFrontBufferOff()
        window_capture.Update()
        rendered_image = window_capture.GetOutput()

        # Check image size, variation, and evidence of each synthetic object.
        render_width, render_height, _depth = rendered_image.GetDimensions()
        pixels = vtk_to_numpy(rendered_image.GetPointData().GetScalars())
        assert render_width > 100, "3D render is too narrow"
        assert render_height > 100, "3D render is too short"
        assert np.std(pixels) > 2, "3D render is blank"

        red_channel = pixels[:, 0]
        green_channel = pixels[:, 1]
        sphere_pixel_mask = (red_channel > green_channel * 1.5) & (red_channel > 100)
        volume_pixel_mask = (np.ptp(pixels, axis=1) < 3) & (red_channel > 50)
        red_pixel_count = int(np.count_nonzero(sphere_pixel_mask))
        gray_pixel_count = int(np.count_nonzero(volume_pixel_mask))
        entry["red_pixels"] = red_pixel_count
        entry["gray_pixels"] = gray_pixel_count
        assert red_pixel_count > 100, f"Sphere not rendered ({red_pixel_count} red pixels)"
        assert gray_pixel_count > 100, f"Synthetic volume not rendered ({gray_pixel_count} gray pixels)"

        png_writer = vtk.vtkPNGWriter()
        png_writer.SetFileName(str(OUTPUT_DIR / "synthetic-3d.png"))
        png_writer.SetInputData(rendered_image)
        png_writer.Write()
        entry["render_screenshot"] = "synthetic-3d.png"
        SCENARIO_REPORT["runtime"]["opengl_capabilities"] = render_window.ReportCapabilities()
        plan_view_id = plan_step._threeDViewNode.GetID()

    with check("navigate-preview-and-independent-views") as entry:
        entry["scope"] = "Direct preview following Plan; no registration or navigation accuracy claim"
        click_to_page(widget, plan_header.nextButton, widget.navigateWidget)
        assert widget.navigateStep.viewsCreated
        assert len(widget.navigateStep.mrmlWidgets) == 4
        assert widget.navigateStep._threeDViewNode.GetID() != plan_view_id, "Navigate reused Plan's view node"
        assert not navigate_header.nextButton.isVisible(), "Last step still has a forward button"
        screenshot("navigate-preview-page")
        # Home constructs a new Welcome page, so look it up after the click.
        click(navigate_header.homeButton)
        expect_page(widget, widget.workflow_page)
        assert widget._activeWorkflowId == "", "Home did not end the workflow"
        assert slicer.mrmlScene.GetFirstNodeByName("VerificationSyntheticCT") is None, "Session data was not cleared"

    with check("fluoroscopy-navigation-and-capture-gate"):
        workflow_buttons = slicer.util.findChildren(widget.workflow_page, name="wfStartButton")
        fluoro_button = next(button for button in workflow_buttons if button.property("accent") == "purple")
        click_to_page(widget, fluoro_button, widget.levelSelectionWidget)
        assert widget._activeWorkflowId == "fluoroscopy"
        assert len(widget._stepHeaders) == 4
        level_header, verification_header, capture_header, _navigate_header = widget._stepHeaders

        click_to_page(widget, level_header.nextButton, widget.verificationWidget)
        click_to_page(widget, verification_header.nextButton, widget.fluoroCaptureWidget)
        expect_forward_blocked(
            widget,
            capture_header.nextButton,
            widget.fluoroCaptureWidget,
            "Navigate is available without assigned captures",
        )
        screenshot("fluoroscopy-capture-page")
        click(capture_header.homeButton)
        expect_page(widget, widget.workflow_page)

    with check("logout-and-safety-invariants") as entry:
        click_to_page(widget, widget.workflow_page.header.logoutButton, widget.splashWidget)
        assert widget.sessionManager.session is None, "Logout left a session active"
        assert widget.loginStep.ui.pinInput.text == "", "Logout retained the PIN"
        assert widget.cameraWorker._camera is None
        assert not list(SANDBOX_DIR.rglob("*.db")), "Verification unexpectedly created a database"
        assert not getattr(slicer, "dicomDatabase", None), "Verification initialized DICOM storage"
        assert not ui_fixtures.PYTHON_CALLBACK_ERRORS, "\n".join(ui_fixtures.PYTHON_CALLBACK_ERRORS)
        assert not ui_fixtures.APPLICATION_LOG_ERRORS, "\n".join(ui_fixtures.APPLICATION_LOG_ERRORS)
        entry["disabled_calls"] = dict(ui_fixtures.DISABLED_START_CALLS)
    SCENARIO_REPORT["completed"] = True
    save_report()


try:
    run()
except Exception:
    SCENARIO_REPORT["error"] = traceback.format_exc()
    traceback.print_exc()
    save_report()
    # Slicer --testing exits nonzero when the Python script raises.
    raise
