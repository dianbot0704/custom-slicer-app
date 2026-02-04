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


def resolve_aimtools_path() -> Path:
    candidates: list[Path] = []
    slicer_home = Path(slicer.app.slicerHome)
    share_dir = slicer_home / "share"
    app_name = getattr(slicer.app, "applicationName", None)
    app_version = getattr(slicer.app, "applicationVersion", None)
    if app_name and app_version:
        candidates.append(share_dir / f"{app_name}-{app_version}" / "AimTools")
    if share_dir.is_dir():
        candidates.extend(sorted(share_dir.glob("*/AimTools")))

    for parent in Path(__file__).resolve().parents:
        if (parent / "CMakeLists.txt").is_file() and (parent / "AimTools").is_dir():
            candidates.append(parent / "AimTools")
            break

    seen: set[Path] = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        if path.is_dir():
            print(f"found AimTools dir {path}")
            return path

    tried = "\n".join(str(path) for path in candidates)
    raise RuntimeError(f"AimTools directory not found. Tried:\n{tried}")


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
        ok_counter = 0
        debug_ok = False
        while not self._stop_evt.is_set():
            try:
                # The tool names are hardcoded in source code.
                ret, tools = self.api.find_valid_tools(["drb", "tool"], min_match_points=3)
                if ret is ReturnCode.OK:
                    for tool in tools:
                        if tool.tool_name == "tool":
                            with self.latest.lock:
                                self.latest.tool_info = tool
                                self.latest.ts = time.time()
                        elif tool.tool_name == "drb":
                            with self.latest.lock:
                                self.latest.ref_info = tool
                                self.latest.ts = time.time()
                        if debug_ok:
                            if tool.tool_name in ["tool", "drb"]:
                                ok_counter += 1
                            if ok_counter % 50 == 0:
                                print("Tool founds")
                                ok_counter = 0
                else:
                    print(f"api.find_valid_tools() return code is not OK: {ret}")
            except Exception as e:
                print(f"AIGCameraController.run() exception caught: {e}")
        print("AIGCameraController run() finished")

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
        self.toolToRef = self.toolToRef or slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", "ToolToRef")

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
        """
        Executed on every timer tick.
        The timer itself is configurable, for now it's default at 60 Hz or every ~16 ms
        """
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
    def _tool_pose_matrix(tool: ToolInfo) -> list[list[float]]:
        rotation = tool.rotation_matrix
        translation = tool.translation_vector
        return [
            [float(rotation[0]), float(rotation[1]), float(rotation[2]), float(translation[0])],
            [float(rotation[3]), float(rotation[4]), float(rotation[5]), float(translation[1])],
            [float(rotation[6]), float(rotation[7]), float(rotation[8]), float(translation[2])],
            [0.0, 0.0, 0.0, 1.0],
        ]

    @staticmethod
    def _toVtkMatrix(tool: ToolInfo) -> vtk.vtkMatrix4x4:
        M = vtk.vtkMatrix4x4()
        matrix = LiveTransformLogic._tool_pose_matrix(tool)
        for r in range(4):
            for c in range(4):
                M.SetElement(r, c, matrix[r][c])

        return M


class LiveTransformWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent):
        ScriptedLoadableModuleWidget.__init__(self, parent)

    def setup(self):
        print("LiveTransformWidget setup()")
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = LiveTransformLogic()
        self.aim = AimCamera()
        self.aim.connect(ConnectionInterface.ETHERNET)
        tools_path = resolve_aimtools_path()
        self.aim.set_tools_path(tools_path)
        self.logic.start(self.aim, 60)
        self._parameterNode = self.logic.getParameterNode()
        # self.setParameterNode(self._parameterNode)

    def cleanup(self):
        print("LiveTransformWidget cleanup()")
        if hasattr(self, "logic") and self.logic:
            self.logic.stop()

    def enter(self):
        print("LiveTransformWidget enter()")
        if self.logic:
            pass
            # self.setParameterNode(self.logic.getParameterNode())

    def exit(self):
        print("LiveTransformWidget exit()")
        pass
