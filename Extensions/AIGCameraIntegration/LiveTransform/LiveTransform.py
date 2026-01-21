import os
from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleWidget,
    ScriptedLoadableModuleLogic,
)
from aigcamera.backend.aim import AimCamera
from aigcamera.types import ToolInfo, ReturnCode, ConnectionInterface
import qt
import slicer
import vtk
import time
import threading
from pathlib import Path


class LiveTransform(ScriptedLoadableModule):
    def __init__(self, parent):
        parent.title = "Live Transform"
        parent.categories = ["Example"]
        parent.contributors = [""]


class _LatestPoses:
    def __init__(self):
        self.lock = threading.Lock()
        self.tool_info: ToolInfo | None = None
        self.ref_info: ToolInfo | None = None
        self.ts = 0.0


class AIGCameraController(threading.Thread):
    def __init__(self, latest: _LatestPoses, api):
        super().__init__(daemon=True)
        self.latest = latest
        self.api = api
        self._stop_evt = threading.Event()

    def run(self):
        while not self._stop_evt.is_set():
            ret, tools = self.api.find_valid_tools(["drb", "tool"], min_match_points=3)
            if ret is ReturnCode.OK:
                for tool in tools:
                    if tool.tool_name == "tool":
                        self.tool_info = tool
                    elif tool.tool_name == "drb":
                        self.ref_info = tool

    def stop(self):
        self._stop_evt.set()


class LiveTransformLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        super().__init__()
        self.latest = _LatestPoses()
        self.controller = None
        self.timer = None

        self.toolToTracker = None
        self.refToTracker = None
        self.toolToRef = None

    def start(self, api, hz=60):
        self.toolToTracker = self.toolToTracker or slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLTransformNode", "ToolToTracker"
        )
        self.refToTracker = self.refToTracker or slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLTransformNode", "RefToTracker"
        )

        self.controller = AIGCameraController(self.latest, api)
        self.controller.start()

        self.timer = qt.QTimer()
        self.timer.setInterval(int(1000 / hz))
        self.timer.timeout.connect(self._onTick)
        self.timer.start()

    def stop(self):
        if self.timer:
            self.timer.stop()
            self.timer = None
        if self.controller:
            self.controller.stop()
            self.controller = None

    def _onTick(self):
        with self.latest.lock:
            tool = self.latest.tool_info
            ref = self.latest.ref_info
        if tool is None or ref is None:
            return
        toolM = self._toVtkMatrix(tool)
        refM = self._toVtkMatrix(ref)

        refInv = vtk.vtkMatrix4x4()
        vtk.vtkMatrix4x4.Invert(refM, refInv)
        toolToRefM = vtk.vtkMatrix4x4()
        vtk.vtkMatrix4x4.Multiply4x4(refInv, toolM, toolToRefM)

        with slicer.util.NodeModify(self.toolToTracker):
            self.toolToTracker.SetMatrixTransformToParent(toolM)
        with slicer.util.NodeModify(self.refToTracker):
            self.refToTracker.SetMatrixTransformToParent(refM)
        with slicer.util.NodeModify(self.toolToRef):
            self.toolToRef.SetMatrixTransformToParent(toolToRefM)

    @staticmethod
    def _toVtkMatrix(tool: ToolInfo) -> vtk.vtkMatrix4x4:
        M = vtk.vtkMatrix4x4()
        for r in range(3):
            for c in range(3):
                ix = r * 3 + c
                M.SetElement(r, c, float(tool.rotation_matrix[ix]))
        for i in range(3):
            M.SetElement(3, i + 1, float(tool.translation_vector[i]))
        M.SetElement(0, 3, 0.0)
        M.SetElement(1, 3, 0.0)
        M.SetElement(2, 3, 0.0)
        M.SetElement(3, 3, 1.0)

        return M


class LiveTransformWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent):
        ScriptedLoadableModuleWidget.__init__(self, parent)

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = LiveTransformLogic()
        self.aim = AimCamera()
        self.aim.connect(ConnectionInterface.ETHERNET)
        self.aim.set_tools_path(Path(os.getcwd()) / "AimTools")
        self.logic.start(self.aim, 60)
        self._parameterNode = self.logic.getParameterNode()
        # self.setParameterNode(self._parameterNode)

    def cleanup(self):
        if hasattr(self, "logic") and self.logic:
            self.logic.stop()

    def enter(self):
        if self.logic:
            pass
            # self.setParameterNode(self.logic.getParameterNode())

    def exit(self):
        pass
