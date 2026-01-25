from pathlib import Path
from aigcamera.types import (
    CameraProtocol,
    ConnectionInterface,
    AcquiredDataType,
    ReturnCode,
    ToolInfo,
    CameraStatusInfo,
    MarkersInfo,
    CollisionStatus,
    HardwareStatus,
    MarkerBGLightStatus,
)


class SimulatedCamera:
    def __init__(self):
        self.conn_interface = ConnectionInterface.ETHERNET
        self.acquired_data = AcquiredDataType.NONE
        self.tools_path = Path("AimTools")
        self._connected = False
        self._simulated_tools: dict[str, ToolInfo] = {}
        self._status_info = CameraStatusInfo(
            temperature_cpu=45.0,
            temperature_board=42.0,
            temperature_left=38.5,
            temperature_right=39.0,
            fps_left=30,
            fps_right=30,
            fps_color=15,
            fps_lcd=60,
            exposure_time_left=1000,
            exposure_time_right=1000,
            collision_status=CollisionStatus.NONE,
            hardware_status=HardwareStatus.OK,
        )
        self._markers_info = MarkersInfo(
            id=1,
            marker_count=4,
            marker_coordinates=[
                0.0,
                0.0,
                0.0,
                10.0,
                0.0,
                0.0,
                0.0,
                10.0,
                0.0,
                10.0,
                10.0,
                0.0,
            ],
            phantom_marker_warnings=[],
            phantom_marker_group_count=0,
            background_light_status=MarkerBGLightStatus.OK,
            marker_warnings=[],
            left_out_warnings=[],
            right_out_warnings=[],
        )

    def set_connection_interface(self, interface: ConnectionInterface) -> None:
        self.conn_interface = interface

    def set_acquired_data(self, acquired_data: AcquiredDataType) -> ReturnCode:
        self.acquired_data = acquired_data
        return ReturnCode.OK

    def connect(
        self, connection_interface: ConnectionInterface | None = None
    ) -> ReturnCode:
        if connection_interface is not None:
            self.conn_interface = connection_interface
        self._connected = True
        return ReturnCode.OK

    def is_connected(self) -> bool:
        return self._connected

    def sim_set_connected(self, connected: bool) -> None:
        self._connected = connected

    def disconnect(self) -> ReturnCode:
        self._connected = False
        return ReturnCode.OK

    def find_tool(
        self, tool_name: str, min_match_points: int
    ) -> tuple[ReturnCode, ToolInfo | None]:
        if tool_name in self._simulated_tools:
            return (ReturnCode.OK, self._simulated_tools[tool_name])
        return (ReturnCode.OK, None)

    def find_tools(
        self, tool_names: list[str], min_match_points: int
    ) -> tuple[ReturnCode, list[ToolInfo]]:
        results = []
        for name in tool_names:
            if name in self._simulated_tools:
                results.append(self._simulated_tools[name])
        return (ReturnCode.OK, results)

    def find_valid_tools(
        self, tool_names: list[str], min_match_points: int
    ) -> tuple[ReturnCode, list[ToolInfo]]:
        return_code, tools = self.find_tools(tool_names, min_match_points)
        if return_code is not ReturnCode.OK:
            return (return_code, [])
        valid_tools = [t for t in tools if t.is_valid]
        return (ReturnCode.OK, valid_tools)

    def tool_detected(
        self, tool_name: str, min_match_points: int
    ) -> tuple[ReturnCode, bool]:
        detected = tool_name in self._simulated_tools
        return (ReturnCode.OK, detected)

    def sim_add_tool(self, tool_info: ToolInfo) -> None:
        self._simulated_tools[tool_info.tool_name] = tool_info

    def sim_remove_tool(self, tool_name: str) -> None:
        self._simulated_tools.pop(tool_name, None)

    def sim_clear_all_tools(self) -> None:
        self._simulated_tools.clear()

    def get_status_info(self) -> tuple[ReturnCode, CameraStatusInfo]:
        return (ReturnCode.OK, self._status_info)

    def get_markers_info(self) -> tuple[ReturnCode, MarkersInfo]:
        return (ReturnCode.OK, self._markers_info)

    def sim_set_status_info(self, status_info: CameraStatusInfo) -> None:
        self._status_info = status_info

    def sim_set_markers_info(self, markers_info: MarkersInfo) -> None:
        self._markers_info = markers_info

    def set_tools_path(self, path: Path) -> None:
        self.tools_path = path

    def get_tools_path(self) -> Path:
        return self.tools_path


if __name__ == "__main__":
    cam: CameraProtocol = SimulatedCamera()
