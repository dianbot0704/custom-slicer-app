"""Drive real PythonQt widgets inside Slicer. Invoked only by verify-app.py."""

# ruff: noqa: S101, PLR2004 - assertions and literal expected values are the verification contract
from __future__ import annotations

import json
import os
import time
import traceback
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import qt
import slicer
import vtk
from vtk.util.numpy_support import vtk_to_numpy

OUTPUT = Path(os.environ["AKSARATOR_VERIFY_OUTPUT"])
SANDBOX = Path(os.environ["AKSARATOR_VERIFY_SANDBOX"])
REPORT = {"run_id": os.environ["AKSARATOR_VERIFY_RUN_ID"], "completed": False, "checks": [], "runtime": {}}


def save_report() -> None:
    temporary = OUTPUT / "scenario.json.tmp"
    temporary.write_text(json.dumps(REPORT, indent=2) + "\n", encoding="utf-8")
    temporary.replace(OUTPUT / "scenario.json")


def wait_for(predicate, description: str, timeout: float = 10.0) -> None:  # noqa: ANN001
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
    image = slicer.util.mainWindow().grab()
    if image.isNull() or not image.save(str(OUTPUT / filename), "PNG"):
        raise RuntimeError(f"Could not save {filename}")
    return filename


@contextmanager
def check(name: str) -> Iterator[dict]:
    entry = {"name": name, "status": "running"}
    REPORT["checks"].append(entry)
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


def click(widget) -> None:  # noqa: ANN001
    assert widget is not None, "Button is missing"
    assert widget.isVisible(), f"Button is not visible: {widget.objectName}"
    assert widget.isEnabled(), f"Button is disabled: {widget.objectName}"
    widget.click()
    slicer.app.processEvents()


def enter_pin(page, pin: str) -> None:  # noqa: ANN001
    buttons = slicer.util.findChildren(page, name="pinKey")
    keys = {str(button.text): button for button in buttons}
    for digit in pin:
        assert digit in keys, f"PIN key {digit} is missing"
        click(keys[digit])


def expect_page(widget, page) -> None:  # noqa: ANN001
    wait_for(lambda: widget.ui.pagesStackedWidget.currentWidget() == page, f"page {page.objectName}")
    assert page.isVisible(), f"Active page is hidden: {page.objectName}"


def run() -> None:  # noqa: PLR0915
    with check("startup-and-page-construction") as entry:
        # Do not select the module here: startup must have selected it itself.
        wait_for(lambda: slicer.util.selectedModule() == "IntraopPlanner", "default IntraopPlanner selection")
        module_path = Path(slicer.util.modulePath("IntraopPlanner")).resolve()
        assert module_path.parent == SANDBOX / "module", f"Wrong runtime selected: {module_path}"
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
        REPORT["runtime"] = {
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
        click(widget.splashWidget.findChild(qt.QPushButton, "startButton"))
        expect_page(widget, widget.generalPinWidget)
        enter_pin(widget.generalPinWidget, "999999")
        expect_page(widget, widget.generalPinWidget)
        assert "Wrong PIN" in widget.generalPinStep.ui.pinErrorLabel.text
        assert widget.generalPinStep.ui.pinInput.text == "", "Rejected PIN was not cleared"
        screenshot("general-pin-rejected")
        click(widget.generalPinStep.ui.pinBackButton)
        expect_page(widget, widget.splashWidget)

    for target, page, header in (
        ("patient", widget.patientSettingsWidget, widget.patientSettingsHeader),
        ("surgeon", widget.surgeonSettingsWidget, widget.surgeonSettingsHeader),
    ):
        with check(f"{target}-settings-pin-and-return"):
            click(widget.splashWidget.findChild(qt.QPushButton, "settingsButton"))
            menu = widget.splashStep.settingsMenu
            click(menu.patientSettingsRow if target == "patient" else menu.surgeonSettingsRow)
            expect_page(widget, widget.generalPinWidget)
            enter_pin(widget.generalPinWidget, "000000")
            expect_page(widget, page)
            screenshot(f"{target}-settings-page")
            click(header.backButton)
            expect_page(widget, widget.splashWidget)

    with check("surgeon-picker-search"):
        click(widget.splashWidget.findChild(qt.QPushButton, "startButton"))
        enter_pin(widget.generalPinWidget, "000000")
        expect_page(widget, widget.preloginWidget)
        search = widget.preloginStep.ui.searchSurgeonInput
        search.setText("no-matching-account")
        slicer.app.processEvents()
        assert not slicer.util.findChildren(widget.preloginWidget, name="surgeonCard"), "Search did not filter cards"
        search.setText("Automation")
        slicer.app.processEvents()
        cards = slicer.util.findChildren(widget.preloginWidget, name="surgeonCard")
        assert len(cards) == 1, "Synthetic account not found"
        click(cards[0])
        expect_page(widget, widget.loginWidget)
        assert widget.loginStep.ui.loginNameLabel.text == "Automation User"

    with check("surgeon-pin-reject"):
        enter_pin(widget.loginWidget, "999999")
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
                agree = next(
                    button
                    for button in slicer.util.findChildren(dialog)
                    if isinstance(button, qt.QPushButton) and button.text == "Agree"
                )
                if not dialog_state["seen"]:
                    assert not agree.isEnabled(), "Agree was enabled before scrolling"
                    dialog_state["seen"] = True
                    entry["disclaimer_screenshot"] = screenshot("disclaimer")
                    scroll = dialog.findChild(qt.QScrollArea, "appPopupScroll").verticalScrollBar()
                    scroll.setValue(scroll.maximum)
                    return
                assert agree.isEnabled(), "Agree did not become enabled after scrolling"
                timer.stop()
                agree.click()
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
        assert widget.sessionManager.session.username == ui_fixtures.SURGEON.username
        expect_page(widget, widget.workflow_page)
        assert ui_fixtures.DISABLED_CALLS["camera_start"] > 0, "Camera start did not pass through the safety fixture"
        assert widget.cameraWorker._camera is None, "Native camera was unexpectedly initialized"

    with check("intraop-navigation-and-scan-gate"):
        starts = slicer.util.findChildren(widget.workflow_page, name="wfStartButton")
        click(next(button for button in starts if button.property("accent") == "blue"))
        expect_page(widget, widget.levelSelectionWidget)
        assert widget._activeWorkflowId == "intraop"
        assert len(widget._stepHeaders) == 5
        click(widget._stepHeaders[0].nextButton)
        expect_page(widget, widget.verificationWidget)
        click(widget._stepHeaders[1].nextButton)
        expect_page(widget, widget.scanPatientWidget)
        assert not widget._stepHeaders[2].nextButton.isEnabled(), "Plan is available without a registered CT"
        widget._stepHeaders[2].nextButton.click()
        expect_page(widget, widget.scanPatientWidget)

    with check("plan-preview-synthetic-render") as entry:
        entry["scope"] = "Direct page preview, not a clinical workflow; Scan Patient gate remains unmodified"
        source = vtk.vtkRTAnalyticSource()
        source.SetWholeExtent(0, 48, 0, 48, 0, 48)
        source.SetCenter(24, 24, 24)
        source.Update()
        volume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", "VerificationSyntheticCT")
        volume.SetOrigin(-24, -24, -24)
        volume.SetAndObserveImageData(source.GetOutput())
        volume.CreateDefaultDisplayNodes()
        volume.GetDisplayNode().AutoWindowLevelOff()
        volume.GetDisplayNode().SetWindowLevel(250, 125)
        # Page preview is explicit: never weaken canAdvance() to get past the
        # registration gate. Exercise Plan's real onEnter and MRML view setup.
        widget._switchToPage(widget._planIndex)
        expect_page(widget, widget.planWidget)
        plan = widget.planStep
        assert plan.viewsCreated, "Plan's independent views were not created"
        assert len(plan.mrmlWidgets) == 4, "Plan did not create all four views"
        assert plan.loaded_volume_node == volume, "Plan did not pick up the synthetic volume"
        # Plan schedules a second CT camera setup after 500 ms. Drain that
        # documented delayed work before framing the synthetic model as well.
        camera_ready_at = time.monotonic() + 0.75
        wait_for(lambda: time.monotonic() >= camera_ready_at, "Plan's deferred camera setup")
        for frame in ("frame_axial", "frame_sagittal", "frame_coronal"):
            composite = plan.mrmlWidgets[frame].sliceLogic().GetSliceCompositeNode()
            assert composite.GetBackgroundVolumeID(), f"No volume displayed in {frame}"
        sphere = vtk.vtkSphereSource()
        sphere.SetRadius(12)
        sphere.SetCenter(70, 0, 0)  # Outside the opaque volume, so both must render.
        sphere.Update()
        model = slicer.modules.models.logic().AddModel(sphere.GetOutputPort())
        model.SetName("VerificationSyntheticSphere")
        model.GetDisplayNode().SetColor(0.9, 0.2, 0.1)
        model.GetDisplayNode().SetViewNodeIDs([plan._threeDViewNode.GetID()])
        view = plan._threeDWidget.threeDView()
        slicer.app.processEvents()
        window = view.renderWindow()
        window.GetRenderers().GetFirstRenderer().ResetCamera()
        plan.fitSlicesToWindow()
        slicer.app.processEvents()
        # Qt owns vtkGenericOpenGLRenderWindow's context. Its SupportsOpenGL()
        # flag is unset in this build even with a valid context; verify pixels.
        view.forceRender()
        slicer.app.processEvents()
        capture = vtk.vtkWindowToImageFilter()
        capture.SetInput(window)
        capture.ReadFrontBufferOff()
        capture.Update()
        image = capture.GetOutput()
        pixels = vtk_to_numpy(image.GetPointData().GetScalars())
        assert image.GetDimensions()[0] > 100, "3D render is too narrow"
        assert image.GetDimensions()[1] > 100, "3D render is too short"
        assert np.std(pixels) > 2, "3D render is blank"
        red_pixels = int(np.count_nonzero((pixels[:, 0] > pixels[:, 1] * 1.5) & (pixels[:, 0] > 100)))
        gray_pixels = int(np.count_nonzero((np.ptp(pixels, axis=1) < 3) & (pixels[:, 0] > 50)))
        entry["red_pixels"] = red_pixels
        entry["gray_pixels"] = gray_pixels
        assert red_pixels > 100, f"Sphere not rendered ({red_pixels} red pixels)"
        assert gray_pixels > 100, f"Synthetic volume not rendered ({gray_pixels} gray pixels)"
        writer = vtk.vtkPNGWriter()
        writer.SetFileName(str(OUTPUT / "synthetic-3d.png"))
        writer.SetInputData(image)
        writer.Write()
        entry["render_screenshot"] = "synthetic-3d.png"
        REPORT["runtime"]["opengl_capabilities"] = window.ReportCapabilities()
        plan_view_id = plan._threeDViewNode.GetID()

    with check("navigate-preview-and-independent-views") as entry:
        entry["scope"] = "Direct preview following Plan; no registration or navigation accuracy claim"
        click(widget._stepHeaders[3].nextButton)
        expect_page(widget, widget.navigateWidget)
        assert widget.navigateStep.viewsCreated
        assert len(widget.navigateStep.mrmlWidgets) == 4
        assert widget.navigateStep._threeDViewNode.GetID() != plan_view_id, "Navigate reused Plan's view node"
        assert not widget._stepHeaders[4].nextButton.isVisible(), "Last step still has a forward button"
        screenshot("navigate-preview-page")
        click(widget._stepHeaders[4].homeButton)
        expect_page(widget, widget.workflow_page)
        assert widget._activeWorkflowId == "", "Home did not end the workflow"
        assert slicer.mrmlScene.GetFirstNodeByName("VerificationSyntheticCT") is None, "Session data was not cleared"

    with check("fluoroscopy-navigation-and-capture-gate"):
        starts = slicer.util.findChildren(widget.workflow_page, name="wfStartButton")
        click(next(button for button in starts if button.property("accent") == "purple"))
        expect_page(widget, widget.levelSelectionWidget)
        assert widget._activeWorkflowId == "fluoroscopy"
        assert len(widget._stepHeaders) == 4
        click(widget._stepHeaders[0].nextButton)
        expect_page(widget, widget.verificationWidget)
        click(widget._stepHeaders[1].nextButton)
        expect_page(widget, widget.fluoroCaptureWidget)
        assert not widget._stepHeaders[2].nextButton.isEnabled(), "Navigate is available without assigned captures"
        widget._stepHeaders[2].nextButton.click()
        expect_page(widget, widget.fluoroCaptureWidget)
        screenshot("fluoroscopy-capture-page")
        click(widget._stepHeaders[2].homeButton)
        expect_page(widget, widget.workflow_page)

    with check("logout-and-safety-invariants") as entry:
        click(widget.workflow_page.header.logoutButton)
        expect_page(widget, widget.splashWidget)
        assert widget.sessionManager.session is None, "Logout left a session active"
        assert widget.loginStep.ui.pinInput.text == "", "Logout retained the PIN"
        assert widget.cameraWorker._camera is None
        assert not list(SANDBOX.rglob("*.db")), "Verification unexpectedly created a database"
        assert not getattr(slicer, "dicomDatabase", None), "Verification initialized DICOM storage"
        assert not ui_fixtures.CALLBACK_ERRORS, "\n".join(ui_fixtures.CALLBACK_ERRORS)
        assert not ui_fixtures.LOG_ERRORS, "\n".join(ui_fixtures.LOG_ERRORS)
        entry["disabled_calls"] = dict(ui_fixtures.DISABLED_CALLS)
    REPORT["completed"] = True
    save_report()


try:
    run()
except Exception:
    REPORT["error"] = traceback.format_exc()
    traceback.print_exc()
    save_report()
    # Slicer --testing exits nonzero when the Python script raises.
    raise
