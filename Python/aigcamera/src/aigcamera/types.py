from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from pathlib import Path


class ConnectionInterface(Enum):
    ETHERNET = 0
    USB = 1
    WIFI = 2


class ReturnCode(Enum):
    # Camera-related
    ERROR = -1
    OK = 0
    CONNECT_ERROR = 1
    NOT_CONNECTED = 2
    READ_FAULT = 3
    WRITE_FAULT = 4
    STALE_DATA = 5
    INIT_FAILED = 6
    INVALID_HANDLE = 7


class ToolType(Enum):
    TOOL = 0
    CALIBRATION_BOARD = 1


class AcquiredDataType(Enum):
    NONE = 0
    INFO = 1
    MARKER_INFO_WITH_WIFI = 2
    STATUS_INFO = 3
    IMG_DUAL = 4
    IMG_COLOR = 5
    INFO_IMG_DUAL = 6
    INFO_IMG_COLOR = 7
    INFO_IMG_DUAL_COLOR = 8


class CollisionStatus(Enum):
    NONE = 0
    OCCURED = 1
    DISABLED = 2


class HardwareStatus(Enum):
    OK = 0
    LCD_VOLTAGE_TOO_LOW = 1
    LCD_VOLTAGE_TOO_HIGH = 2
    IR_LEFT_VOLTAGE_TOO_LOW = 3
    IR_LEFT_VOLTAGE_TOO_HIGH = 4
    IR_RIGHT_VOLTAGE_TOO_LOW = 5
    IR_RIGHT_VOLTAGE_TOO_HIGH = 6
    GET_INIT_DATA_ERROR = 7


class MarkerBGLightStatus(Enum):
    OK = 0
    ABNORMAL = 1


class EdgeWarnings(Enum):
    NONE = 0
    COMMON = 1
    CRITICAL = 2


@dataclass
class ToolInfo:
    tool_type: ToolType
    is_valid: bool
    tool_name: str
    mean_abs_error: float
    rms_error: float
    rotation_vector: list[float]
    quaternion: list[float]
    rotation_matrix: list[float]
    translation_vector: list[float]
    origin_coordinates: list[float]
    marker_points: list[float]


@dataclass
class CameraStatusInfo:
    temperature_cpu: float
    temperature_board: float
    temperature_left: float
    temperature_right: float
    fps_left: int
    fps_right: int
    fps_color: int
    fps_lcd: int
    exposure_time_left: int
    exposure_time_right: int
    collision_status: CollisionStatus
    hardware_status: HardwareStatus


@dataclass
class MarkersInfo:
    id: int
    marker_count: int
    marker_coordinates: list[float]
    phantom_marker_warnings: list[int]
    phantom_marker_group_count: int
    background_light_status: MarkerBGLightStatus
    marker_warnings: list[EdgeWarnings]
    left_out_warnings: list[EdgeWarnings]
    right_out_warnings: list[EdgeWarnings]


class CameraProtocol(Protocol):
    def connect(
        self, connection_interface: ConnectionInterface | None = None
    ) -> ReturnCode: ...
    def set_acquired_data(self, acquired_data: AcquiredDataType) -> ReturnCode: ...
    def set_connection_interface(self, interface: ConnectionInterface) -> None: ...
    def disconnect(self) -> ReturnCode: ...
    def is_connected(self) -> bool: ...
    def find_tool(
        self, tool_name: str, min_match_points: int
    ) -> tuple[ReturnCode, ToolInfo | None]: ...
    def tool_detected(
        self, tool_name: str, min_match_points: int
    ) -> tuple[ReturnCode, bool]: ...
    def find_tools(
        self, tool_names: list[str], min_match_points: int
    ) -> tuple[ReturnCode, list[ToolInfo]]: ...
    def find_valid_tools(
        self, tool_names: list[str], min_match_points: int
    ) -> tuple[ReturnCode, list[ToolInfo]]: ...
    def get_status_info(self) -> tuple[ReturnCode, CameraStatusInfo]: ...
    def get_markers_info(self) -> tuple[ReturnCode, MarkersInfo]: ...
    def get_tools_path(self) -> Path: ...
    def set_tools_path(self, path: Path) -> None: ...
