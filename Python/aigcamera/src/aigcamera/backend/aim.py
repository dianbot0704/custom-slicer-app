from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import time

from aigcamera._native_loader import load_aimpos
from aigcamera.types import (
    ConnectionInterface,
    AcquiredDataType,
    ReturnCode,
    ToolInfo,
    ToolType,
    CameraStatusInfo,
    MarkersInfo,
    CollisionStatus,
    HardwareStatus,
    MarkerBGLightStatus,
    EdgeWarnings,
)


class _ToolMadeInfo(Protocol):
    """Protocol describing Aim tool creation progress info."""

    unValidMarkerFlag: bool
    madeRate: float
    isMadeProFinished: bool
    MadeError: float


class _ToolFixProInfo(Protocol):
    """Protocol describing Aim tool self-calibration progress info."""

    totalmarkcnt: int
    isValidFixCnt: int
    isCalibrateFinished: bool
    MatchError: float


class _ToolTipCalProInfo(Protocol):
    """Protocol describing Aim tooltip calibration progress info."""

    isBoardFind: bool
    isToolFind: bool
    isValidCalibrate: bool
    isCalibrateFinished: bool
    CalibrateError: float
    CalibrateRate: float
    CalRMSError: float


class _ToolTipPivotInfo(Protocol):
    """Protocol describing Aim tooltip pivot progress info."""

    isToolFind: bool
    isPivotFinished: bool
    pivotRate: float
    pivotMeanError: float


@dataclass
class ToolCreationProgress:
    """Progress information for Aim tool creation."""

    invalid_marker_flag: bool = False
    progress_rate: float = 0.0
    finished: bool = False
    error: float = 0.0


@dataclass
class ToolSelfCalibrationProgress:
    """Progress information for Aim tool self-calibration."""

    total_marker_count: int = 0
    valid_calibration_count: int = 0
    finished: bool = False
    match_error: float = 0.0


@dataclass
class ToolTipCalibrationProgress:
    """Progress information for Aim tooltip calibration with a board."""

    board_found: bool = False
    tool_found: bool = False
    valid_calibration: bool = False
    finished: bool = False
    calibration_error: float = 0.0
    progress_rate: float = 0.0
    rms_error: float = 0.0


@dataclass
class ToolTipPivotProgress:
    """Progress information for Aim tooltip pivot calibration."""

    tool_found: bool = False
    finished: bool = False
    progress_rate: float = 0.0
    mean_error: float = 0.0


class AimCamera:
    """AimPosition backend implementation of CameraProtocol.

    Loads the AimPosition shared library and exposes device APIs using
    ReturnCode-based error handling.
    """

    def __init__(self):
        """Initialize the AimPosition backend and load the shared library.

        Raises:
            RuntimeError: If the AimPosition library cannot be loaded.
        """
        self._ap = load_aimpos()

        self.conn_interface = ConnectionInterface.ETHERNET
        self.acquired_data = AcquiredDataType.NONE
        self._tools_path: Path | None = None
        self._tools_path_str: str | None = None
        self._tool_path_set = False
        self._connected = False
        self._handle = None
        self._pos_data = self._ap.T_AIMPOS_DATAPARA()
        self._tool_create_info: _ToolMadeInfo | None = None
        self._tool_create_initialized = False
        self._tool_self_cal_info: _ToolFixProInfo | None = None
        self._tool_self_cal_initialized = False
        self._tool_tip_cal_info: _ToolTipCalProInfo | None = None
        self._tool_tip_cal_initialized = False
        self._tool_tip_pivot_info: _ToolTipPivotInfo | None = None
        self._tool_tip_pivot_initialized = False

    def _to_aim_connection_interface(self, interface: ConnectionInterface):
        if interface is ConnectionInterface.ETHERNET:
            return self._ap.I_ETHERNET
        elif interface is ConnectionInterface.USB:
            return self._ap.I_USB
        elif interface is ConnectionInterface.WIFI:
            return self._ap.I_WIFI
        return self._ap.I_ETHERNET

    def _from_aim_return_code(self, aim_code: int) -> ReturnCode:
        if aim_code == self._ap.AIMOOE_OK:
            return ReturnCode.OK
        elif aim_code == self._ap.AIMOOE_NOT_REFLASH:
            return ReturnCode.STALE_DATA
        elif aim_code == self._ap.AIMOOE_CONNECT_ERROR:
            return ReturnCode.CONNECT_ERROR
        elif aim_code == self._ap.AIMOOE_NOT_CONNECT:
            return ReturnCode.NOT_CONNECTED
        elif aim_code == self._ap.AIMOOE_READ_FAULT:
            return ReturnCode.READ_FAULT
        elif aim_code == self._ap.AIMOOE_WRITE_FAULT:
            return ReturnCode.WRITE_FAULT
        elif aim_code == self._ap.AIMOOE_INITIAL_FAIL:
            return ReturnCode.INIT_FAILED
        elif aim_code == self._ap.AIMOOE_HANDLE_IS_NULL:
            return ReturnCode.INVALID_HANDLE
        return ReturnCode.ERROR

    def _from_aim_collision_status(self, aim_status: int) -> CollisionStatus:
        if aim_status == self._ap.E_CollisionStatus.COLLISION_OCCURRED:
            return CollisionStatus.OCCURED
        if aim_status == self._ap.E_CollisionStatus.COLLISION_NOT_START:
            return CollisionStatus.DISABLED
        return CollisionStatus.NONE

    def _from_aim_hardware_status(self, aim_status: int) -> HardwareStatus:
        if aim_status == self._ap.E_HardwareStatus.HW_LCD_VOLTAGE_TOO_LOW:
            return HardwareStatus.LCD_VOLTAGE_TOO_LOW
        if aim_status == self._ap.E_HardwareStatus.HW_LCD_VOLTAGE_TOO_HIGH:
            return HardwareStatus.LCD_VOLTAGE_TOO_HIGH
        if aim_status == self._ap.E_HardwareStatus.HW_IR_LEFT_VOLTAGE_TOO_LOW:
            return HardwareStatus.IR_LEFT_VOLTAGE_TOO_LOW
        if aim_status == self._ap.E_HardwareStatus.HW_IR_LEFT_VOLTAGE_TOO_HIGH:
            return HardwareStatus.IR_LEFT_VOLTAGE_TOO_HIGH
        if aim_status == self._ap.E_HardwareStatus.HW_IR_RIGHT_VOLTAGE_TOO_LOW:
            return HardwareStatus.IR_RIGHT_VOLTAGE_TOO_LOW
        if aim_status == self._ap.E_HardwareStatus.HW_IR_RIGHT_VOLTAGE_TOO_HIGH:
            return HardwareStatus.IR_RIGHT_VOLTAGE_TOO_HIGH
        if aim_status == self._ap.E_HardwareStatus.HW_GET_INITIAL_DATA_ERROR:
            return HardwareStatus.GET_INIT_DATA_ERROR
        return HardwareStatus.OK

    def _from_aim_bg_light_status(self, aim_status: int) -> MarkerBGLightStatus:
        if aim_status == self._ap.E_BackgroundLightStatus.BG_LIGHT_ABNORMAL:
            return MarkerBGLightStatus.ABNORMAL
        return MarkerBGLightStatus.OK

    def _from_aim_edge_warning(self, aim_warning: int) -> EdgeWarnings:
        if aim_warning == self._ap.E_MarkWarnType.eWarn_Common:
            return EdgeWarnings.COMMON
        if aim_warning == self._ap.E_MarkWarnType.eWarn_Critical:
            return EdgeWarnings.CRITICAL
        return EdgeWarnings.NONE

    def _to_aim_acquired_data_type(self, data_type: AcquiredDataType):
        if data_type is AcquiredDataType.NONE:
            return self._ap.E_DataType.DT_NONE
        elif data_type is AcquiredDataType.INFO:
            return self._ap.E_DataType.DT_INFO
        elif data_type is AcquiredDataType.MARKER_INFO_WITH_WIFI:
            return self._ap.E_DataType.DT_MARKER_INFO_WITH_WIFI
        elif data_type is AcquiredDataType.STATUS_INFO:
            return self._ap.E_DataType.DT_STATUS_INFO
        elif data_type is AcquiredDataType.IMG_DUAL:
            return self._ap.E_DataType.DT_IMGDUAL
        elif data_type is AcquiredDataType.IMG_COLOR:
            return self._ap.E_DataType.DT_IMGCOLOR
        elif data_type is AcquiredDataType.INFO_IMG_DUAL:
            return self._ap.E_DataType.DT_INFO_IMGDUAL
        elif data_type is AcquiredDataType.INFO_IMG_COLOR:
            return self._ap.E_DataType.DT_INFO_IMGCOLOR
        elif data_type is AcquiredDataType.INFO_IMG_DUAL_COLOR:
            return self._ap.E_DataType.DT_INFO_IMGDUAL_IMGCOLOR
        return self._ap.E_DataType.DT_NONE

    def connect(
        self,
        connection_interface: ConnectionInterface | None = None,
    ) -> ReturnCode:
        """Connect to the Aim device and initialize handles.

        Applies any configured tools path after connecting.

        Args:
            connection_interface: Optional override for the connection interface.
                Currently ignored; call set_connection_interface before connect.

        Returns:
            ReturnCode: Result of the connection attempt.
        """
        if self._handle is None:
            self._handle = self._ap.Aim_API_Initial()

        connection_interface = self._to_aim_connection_interface(self.conn_interface)
        ret = self._ap.Aim_ConnectDevice(
            self._handle,
            connection_interface,
            self._pos_data,
        )
        return_code = self._from_aim_return_code(ret)
        self._connected = return_code is ReturnCode.OK
        if self._connected and self._tools_path_str is not None:
            tool_path_ret = self._ap.Aim_SetToolInfoFilePath(
                self._handle,
                self._tools_path_str,
                True,
            )
            self._tool_path_set = (
                self._from_aim_return_code(tool_path_ret) is ReturnCode.OK
            )
        else:
            self._tool_path_set = False
        return return_code

    def set_connection_interface(self, interface: ConnectionInterface) -> None:
        """Set the connection interface used for future connections.

        Args:
            interface: Connection interface such as Ethernet, USB, or WiFi.
        """
        self.conn_interface = interface

    def set_acquired_data(self, acquired_data: AcquiredDataType) -> ReturnCode:
        """Configure which data types the Aim backend should acquire.

        Args:
            acquired_data: Data type selection for the Aim device.

        Returns:
            ReturnCode: Result from the Aim_SetAcquireData call.
        """
        self.acquired_data = acquired_data
        interface = self._to_aim_connection_interface(self.conn_interface)
        aim_data_type = self._to_aim_acquired_data_type(acquired_data)
        ret = self._ap.Aim_SetAcquireData(
            self._handle,
            interface,
            aim_data_type,
        )
        return self._from_aim_return_code(ret)

    def disconnect(self) -> ReturnCode:
        """Disconnect from the Aim device and clear handles.

        Returns:
            ReturnCode: Result from Aim_API_Close, or INVALID_HANDLE if uninitialized.
        """
        if self._handle is None:
            return ReturnCode.INVALID_HANDLE
        return_code = self._from_aim_return_code(self._ap.Aim_API_Close(self._handle))
        self._connected = False
        self._handle = None
        self._tool_path_set = False
        return return_code

    def tool_create_init(
        self,
        marker_count: int,
        tool_name: str,
    ) -> ReturnCode:
        """Initialize a tool creation session for the Aim device.

        Use marker_count=4 for four-point tool creation.

        Args:
            marker_count: Number of markers expected for the tool.
            tool_name: Tool name used when saving the file.

        Returns:
            ReturnCode: Result from Aim_InitToolMadeInfo.
        """
        if not self._connected:
            self._tool_create_info = None
            self._tool_create_initialized = False
            return ReturnCode.NOT_CONNECTED
        if self._handle is None:
            self._tool_create_info = None
            self._tool_create_initialized = False
            return ReturnCode.INVALID_HANDLE
        if marker_count <= 0:
            self._tool_create_info = None
            self._tool_create_initialized = False
            return ReturnCode.ERROR

        ret = self._ap.Aim_InitToolMadeInfo(self._handle, marker_count, tool_name)
        return_code = self._from_aim_return_code(ret)
        if return_code is ReturnCode.OK:
            self._tool_create_info = self._ap.t_ToolMadeProInfo()
            self._tool_create_initialized = True
        else:
            self._tool_create_info = None
            self._tool_create_initialized = False
        return return_code

    def tool_create_process(self) -> tuple[ReturnCode, ToolCreationProgress]:
        """Capture markers and advance tool creation progress.

        Call after tool_create_init until finished is True. Requires acquired data
        set to NONE or INFO.

        Returns:
            tuple[ReturnCode, ToolCreationProgress]: ReturnCode and progress info.
        """
        empty_progress = ToolCreationProgress()
        if not self._connected:
            return (ReturnCode.NOT_CONNECTED, empty_progress)
        if self._handle is None:
            return (ReturnCode.INVALID_HANDLE, empty_progress)
        tool_create_info = self._tool_create_info
        if not self._tool_create_initialized or tool_create_info is None:
            return (ReturnCode.ERROR, empty_progress)
        if self.acquired_data not in (AcquiredDataType.INFO, AcquiredDataType.NONE):
            return (ReturnCode.STALE_DATA, empty_progress)

        interface = self._to_aim_connection_interface(self.conn_interface)
        marker_info = self._ap.T_MarkerInfo()
        status_info = self._ap.T_AimPosStatusInfo()
        ret = self._ap.Aim_GetMarkerAndStatusFromHardware(
            self._handle,
            interface,
            marker_info,
            status_info,
        )
        attempts = 0
        while ret == self._ap.AIMOOE_NOT_REFLASH and attempts < 5:
            time.sleep(0.01)
            ret = self._ap.Aim_GetMarkerAndStatusFromHardware(
                self._handle,
                interface,
                marker_info,
                status_info,
            )
            attempts += 1
        return_code = self._from_aim_return_code(ret)
        if return_code is not ReturnCode.OK:
            return (return_code, empty_progress)

        ret = self._ap.Aim_ProceedToolMade(
            self._handle,
            marker_info,
            tool_create_info,
        )
        return_code = self._from_aim_return_code(ret)
        if return_code is not ReturnCode.OK:
            return (return_code, empty_progress)

        progress = ToolCreationProgress(
            invalid_marker_flag=bool(tool_create_info.unValidMarkerFlag),
            progress_rate=float(tool_create_info.madeRate),
            finished=bool(tool_create_info.isMadeProFinished),
            error=float(tool_create_info.MadeError),
        )
        return (ReturnCode.OK, progress)

    def tool_create_finish(self, save: bool) -> ReturnCode:
        """Finalize tool creation and optionally save the result.

        Call after tool_create_process reports finished.

        Args:
            save: Whether to persist the created tool file.

        Returns:
            ReturnCode: Result from Aim_SaveToolMadeRlt.
        """
        if not self._connected:
            self._tool_create_info = None
            self._tool_create_initialized = False
            return ReturnCode.NOT_CONNECTED
        if self._handle is None:
            self._tool_create_info = None
            self._tool_create_initialized = False
            return ReturnCode.INVALID_HANDLE
        if not self._tool_create_initialized:
            self._tool_create_info = None
            self._tool_create_initialized = False
            return ReturnCode.ERROR

        ret = self._ap.Aim_SaveToolMadeRlt(self._handle, bool(save))
        return_code = self._from_aim_return_code(ret)
        self._tool_create_info = None
        self._tool_create_initialized = False
        return return_code

    def is_connected(self) -> bool:
        """Return whether the Aim device is connected."""
        return self._connected

    def find_tool(
        self,
        tool_name: str,
        min_match_points: int,
    ) -> tuple[ReturnCode, ToolInfo | None]:
        """Find a single tool by name.

        Requires acquired data to be INFO or NONE and a configured tools path.

        Args:
            tool_name: Name of the tool to locate.
            min_match_points: Minimum marker points required for a match.

        Returns:
            tuple[ReturnCode, ToolInfo | None]: ReturnCode and tool info if found.
        """
        return_code, tools = self.find_tools([tool_name], min_match_points)
        if return_code is not ReturnCode.OK:
            return (return_code, None)
        if not tools:
            return (ReturnCode.OK, None)
        tool_info = tools[0]
        if not tool_info.is_valid:
            return (ReturnCode.OK, None)
        return (ReturnCode.OK, tool_info)

    def tool_detected(
        self,
        tool_name: str,
        min_match_points: int,
    ) -> tuple[ReturnCode, bool]:
        """Check whether a tool is detected by the Aim backend.

        Args:
            tool_name: Name of the tool to query.
            min_match_points: Minimum marker points required for a match.

        Returns:
            tuple[ReturnCode, bool]: ReturnCode and True if a tool is detected.
        """
        return_code, tool_info = self.find_tool(tool_name, min_match_points)
        detected = tool_info is not None
        return (return_code, detected)

    def find_tools(
        self,
        tool_names: list[str],
        min_match_points: int,
    ) -> tuple[ReturnCode, list[ToolInfo]]:
        """Find multiple tools by name.

        Requires a connected device, a configured tools path, and acquired data
        set to INFO or NONE.

        Args:
            tool_names: List of tool names to locate.
            min_match_points: Minimum marker points required for a match.

        Returns:
            tuple[ReturnCode, list[ToolInfo]]: ReturnCode and detected tool list.
        """
        if not self._connected:
            return (ReturnCode.NOT_CONNECTED, [])
        if self._handle is None:
            return (ReturnCode.INVALID_HANDLE, [])
        if not self._tool_path_set:
            return (ReturnCode.ERROR, [])
        if not tool_names:
            return (ReturnCode.OK, [])

        if self.acquired_data not in (AcquiredDataType.INFO, AcquiredDataType.NONE):
            return (ReturnCode.STALE_DATA, [])

        interface = self._to_aim_connection_interface(self.conn_interface)

        marker_info = self._ap.T_MarkerInfo()
        status_info = self._ap.T_AimPosStatusInfo()
        ret = self._ap.Aim_GetMarkerAndStatusFromHardware(
            self._handle,
            interface,
            marker_info,
            status_info,
        )
        attempts = 0
        while ret == self._ap.AIMOOE_NOT_REFLASH and attempts < 5:
            time.sleep(0.01)
            ret = self._ap.Aim_GetMarkerAndStatusFromHardware(
                self._handle,
                interface,
                marker_info,
                status_info,
            )
            attempts += 1
        return_code = self._from_aim_return_code(ret)
        if return_code is not ReturnCode.OK:
            return (return_code, [])

        tool_name_vector = self._ap.StringVector(tool_names)
        tool_results = self._ap.T_AimToolDataResult()
        ret = self._ap.Aim_FindSpecificToolInfo(
            self._handle,
            marker_info,
            tool_name_vector,
            tool_results,
            min_match_points,
        )
        return_code = self._from_aim_return_code(ret)
        if return_code is not ReturnCode.OK:
            return (return_code, [])

        tools: list[ToolInfo] = []
        marker_count = int(marker_info.MarkerNumber)
        result_node = tool_results
        while result_node is not None:
            tool_type = ToolType.TOOL
            if result_node.type == self._ap.E_AimToolType.ePosCalBoard:
                tool_type = ToolType.CALIBRATION_BOARD

            rotation_matrix = [float(value) for row in result_node.Rto for value in row]
            translation_vector = [
                float(result_node.Tto[0]),
                float(result_node.Tto[1]),
                float(result_node.Tto[2]),
            ]
            marker_points: list[float] = []
            for tool_index in result_node.toolptidx:
                tool_index_value = int(tool_index)
                if tool_index_value < 0 or tool_index_value >= marker_count:
                    marker_points.extend([0.0, 0.0, 0.0])
                else:
                    base = tool_index_value * 3
                    marker_points.extend(
                        [
                            float(marker_info.MarkerCoordinate[base]),
                            float(marker_info.MarkerCoordinate[base + 1]),
                            float(marker_info.MarkerCoordinate[base + 2]),
                        ]
                    )

            tools.append(
                ToolInfo(
                    tool_type=tool_type,
                    is_valid=bool(result_node.validflag),
                    tool_name=str(result_node.toolname),
                    mean_abs_error=float(result_node.MeanError),
                    rms_error=float(result_node.Rms),
                    rotation_vector=[
                        float(value) for value in result_node.rotationvector
                    ],
                    quaternion=[float(value) for value in result_node.Qoxyz],
                    rotation_matrix=rotation_matrix,
                    translation_vector=translation_vector,
                    origin_coordinates=[
                        float(value) for value in result_node.OriginCoor
                    ],
                    marker_points=marker_points,
                )
            )
            next_node = result_node.next
            del result_node
            result_node = next_node
        tool_results = None
        return (ReturnCode.OK, tools)

    def find_valid_tools(
        self,
        tool_names: list[str],
        min_match_points: int,
    ) -> tuple[ReturnCode, list[ToolInfo]]:
        """Find multiple valid tools by name.

        Requires a connected device, a configured tools path, and acquired data
        set to INFO or NONE.

        Args:
            tool_names: List of tool names to locate.
            min_match_points: Minimum marker points required for a match.

        Returns:
            tuple[ReturnCode, list[ToolInfo]]: ReturnCode and detected valid tool list.
        """
        return_code, tools = self.find_tools(tool_names, min_match_points)
        if return_code is not ReturnCode.OK:
            return (return_code, [])
        valid_tools = [t for t in tools if t.is_valid]
        return (ReturnCode.OK, valid_tools)

    def get_status_info(self) -> tuple[ReturnCode, CameraStatusInfo]:
        """Fetch camera status information from the Aim device.

        Returns:
            tuple[ReturnCode, CameraStatusInfo]: ReturnCode and status info.
            Returns an empty info object when not connected.
        """
        empty_info = CameraStatusInfo(
            temperature_cpu=0.0,
            temperature_board=0.0,
            temperature_left=0.0,
            temperature_right=0.0,
            fps_left=0,
            fps_right=0,
            fps_color=0,
            fps_lcd=0,
            exposure_time_left=0,
            exposure_time_right=0,
            collision_status=CollisionStatus.NONE,
            hardware_status=HardwareStatus.OK,
        )
        if not self._connected:
            return (ReturnCode.NOT_CONNECTED, empty_info)
        if self._handle is None:
            return (ReturnCode.INVALID_HANDLE, empty_info)

        interface = self._to_aim_connection_interface(self.conn_interface)
        marker_info = self._ap.T_MarkerInfo()
        status_info = self._ap.T_AimPosStatusInfo()
        ret = self._ap.Aim_GetMarkerAndStatusFromHardware(
            self._handle,
            interface,
            marker_info,
            status_info,
        )
        attempts = 0
        while ret == self._ap.AIMOOE_NOT_REFLASH and attempts < 5:
            time.sleep(0.01)
            ret = self._ap.Aim_GetMarkerAndStatusFromHardware(
                self._handle,
                interface,
                marker_info,
                status_info,
            )
            attempts += 1
        return_code = self._from_aim_return_code(ret)
        if return_code is not ReturnCode.OK:
            return (return_code, empty_info)

        info = CameraStatusInfo(
            temperature_cpu=float(status_info.Tcpu),
            temperature_board=float(status_info.Tpcb),
            temperature_left=float(status_info.TLeftCam),
            temperature_right=float(status_info.TRightCam),
            fps_left=int(status_info.LeftCamFps),
            fps_right=int(status_info.RightCamFps),
            fps_color=int(status_info.ColorCamFps),
            fps_lcd=int(status_info.LCDFps),
            exposure_time_left=int(status_info.ExposureTimeLeftCam),
            exposure_time_right=int(status_info.ExposureTimeRightCam),
            collision_status=self._from_aim_collision_status(
                status_info.CollisionStatus
            ),
            hardware_status=self._from_aim_hardware_status(status_info.HardwareStatus),
        )
        return (ReturnCode.OK, info)

    def get_markers_info(self) -> tuple[ReturnCode, MarkersInfo]:
        """Fetch marker coordinate information from the Aim device.

        Returns:
            tuple[ReturnCode, MarkersInfo]: ReturnCode and marker info.
            Returns an empty info object when not connected.
        """
        empty_info = MarkersInfo(
            id=0,
            marker_count=0,
            marker_coordinates=[],
            phantom_marker_warnings=[],
            phantom_marker_group_count=0,
            background_light_status=MarkerBGLightStatus.OK,
            marker_warnings=[],
            left_out_warnings=[],
            right_out_warnings=[],
        )
        if not self._connected:
            return (ReturnCode.NOT_CONNECTED, empty_info)
        if self._handle is None:
            return (ReturnCode.INVALID_HANDLE, empty_info)

        interface = self._to_aim_connection_interface(self.conn_interface)
        marker_info = self._ap.T_MarkerInfo()
        status_info = self._ap.T_AimPosStatusInfo()
        ret = self._ap.Aim_GetMarkerAndStatusFromHardware(
            self._handle,
            interface,
            marker_info,
            status_info,
        )
        attempts = 0
        while ret == self._ap.AIMOOE_NOT_REFLASH and attempts < 5:
            time.sleep(0.01)
            ret = self._ap.Aim_GetMarkerAndStatusFromHardware(
                self._handle,
                interface,
                marker_info,
                status_info,
            )
            attempts += 1
        return_code = self._from_aim_return_code(ret)
        if return_code is not ReturnCode.OK:
            return (return_code, empty_info)

        marker_count = int(marker_info.MarkerNumber)
        if marker_count < 0:
            marker_count = 0
        marker_coordinates = [
            float(marker_info.MarkerCoordinate[index])
            for index in range(marker_count * 3)
        ]
        phantom_marker_warnings = [
            int(marker_info.PhantomMarkerWarning[index])
            for index in range(marker_count)
        ]
        marker_warnings = [
            self._from_aim_edge_warning(marker_info.MarkWarn[index])
            for index in range(marker_count)
        ]
        left_out_warnings = [self._from_aim_edge_warning(marker_info.bLeftOutWarnning)]
        right_out_warnings = [self._from_aim_edge_warning(marker_info.bRightOutWarning)]

        info = MarkersInfo(
            id=int(marker_info.ID),
            marker_count=marker_count,
            marker_coordinates=marker_coordinates,
            phantom_marker_warnings=phantom_marker_warnings,
            phantom_marker_group_count=int(marker_info.PhantomMarkerGroupNumber),
            background_light_status=self._from_aim_bg_light_status(
                marker_info.MarkerBGLightStatus
            ),
            marker_warnings=marker_warnings,
            left_out_warnings=left_out_warnings,
            right_out_warnings=right_out_warnings,
        )
        return (ReturnCode.OK, info)

    def get_tools_path(self) -> Path:
        """Return the configured tools file path.

        Returns:
            Path: Configured tools path, or an empty Path if unset.
        """
        if self._tools_path is None:
            return Path()
        return self._tools_path

    def set_tools_path(self, path: Path) -> None:
        """Configure the tools file path for Aim lookups.

        Args:
            path: Path to the Aim tools definition file or directory.
        """
        self._tools_path = path
        self._tools_path_str = str(path)
        if self._connected and self._handle is not None:
            ret = self._ap.Aim_SetToolInfoFilePath(
                self._handle,
                self._tools_path_str,
                True,
            )
            self._tool_path_set = self._from_aim_return_code(ret) is ReturnCode.OK
        else:
            self._tool_path_set = False

    def tool_self_calibration_init(
        self,
        tool_name: str,
    ) -> tuple[ReturnCode, int]:
        """Initialize a tool self-calibration session for an existing tool.

        Self-calibration refines the marker positions of an existing tool file
        to improve tracking accuracy.

        Args:
            tool_name: Name of the existing tool to calibrate.

        Returns:
            tuple[ReturnCode, int]: ReturnCode and total marker count for the tool.
                Returns -1 for marker count on failure.
        """
        if not self._connected:
            self._tool_self_cal_info = None
            self._tool_self_cal_initialized = False
            return (ReturnCode.NOT_CONNECTED, -1)
        if self._handle is None:
            self._tool_self_cal_info = None
            self._tool_self_cal_initialized = False
            return (ReturnCode.INVALID_HANDLE, -1)
        if not self._tool_path_set:
            self._tool_self_cal_info = None
            self._tool_self_cal_initialized = False
            return (ReturnCode.ERROR, -1)

        total_marker_count = self._ap.Aim_InitToolSelfCalibrationWithToolId(
            self._handle,
            tool_name,
        )
        if total_marker_count == -1:
            self._tool_self_cal_info = None
            self._tool_self_cal_initialized = False
            return (ReturnCode.ERROR, -1)

        self._tool_self_cal_info = self._ap.t_ToolFixProInfo()
        self._tool_self_cal_info.totalmarkcnt = total_marker_count
        self._tool_self_cal_initialized = True
        return (ReturnCode.OK, total_marker_count)

    def tool_self_calibration_process(
        self,
    ) -> tuple[ReturnCode, ToolSelfCalibrationProgress]:
        """Capture markers and advance tool self-calibration progress.

        Call after tool_self_calibration_init until finished is True.
        Requires acquired data set to NONE or INFO.

        Returns:
            tuple[ReturnCode, ToolSelfCalibrationProgress]: ReturnCode and progress info.
        """
        empty_progress = ToolSelfCalibrationProgress()
        if not self._connected:
            return (ReturnCode.NOT_CONNECTED, empty_progress)
        if self._handle is None:
            return (ReturnCode.INVALID_HANDLE, empty_progress)
        tool_self_cal_info = self._tool_self_cal_info
        if not self._tool_self_cal_initialized or tool_self_cal_info is None:
            return (ReturnCode.ERROR, empty_progress)
        if self.acquired_data not in (AcquiredDataType.INFO, AcquiredDataType.NONE):
            return (ReturnCode.STALE_DATA, empty_progress)

        interface = self._to_aim_connection_interface(self.conn_interface)
        marker_info = self._ap.T_MarkerInfo()
        status_info = self._ap.T_AimPosStatusInfo()
        ret = self._ap.Aim_GetMarkerAndStatusFromHardware(
            self._handle,
            interface,
            marker_info,
            status_info,
        )
        attempts = 0
        while ret == self._ap.AIMOOE_NOT_REFLASH and attempts < 5:
            time.sleep(0.01)
            ret = self._ap.Aim_GetMarkerAndStatusFromHardware(
                self._handle,
                interface,
                marker_info,
                status_info,
            )
            attempts += 1
        return_code = self._from_aim_return_code(ret)
        if return_code is not ReturnCode.OK:
            return (return_code, empty_progress)

        ret = self._ap.Aim_ProceedToolSelfCalibration(
            self._handle,
            marker_info,
            tool_self_cal_info,
        )
        return_code = self._from_aim_return_code(ret)
        if return_code is not ReturnCode.OK:
            return (return_code, empty_progress)

        progress = ToolSelfCalibrationProgress(
            total_marker_count=int(tool_self_cal_info.totalmarkcnt),
            valid_calibration_count=int(tool_self_cal_info.isValidFixCnt),
            finished=bool(tool_self_cal_info.isCalibrateFinished),
            match_error=float(tool_self_cal_info.MatchError),
        )
        return (ReturnCode.OK, progress)

    def tool_self_calibration_finish(self, save: bool) -> ReturnCode:
        """Finalize tool self-calibration and optionally save the result.

        Call after tool_self_calibration_process reports finished.

        Args:
            save: Whether to persist the calibrated tool file.

        Returns:
            ReturnCode: Result from Aim_SaveToolSelfCalibration.
        """
        if not self._connected:
            self._tool_self_cal_info = None
            self._tool_self_cal_initialized = False
            return ReturnCode.NOT_CONNECTED
        if self._handle is None:
            self._tool_self_cal_info = None
            self._tool_self_cal_initialized = False
            return ReturnCode.INVALID_HANDLE
        if not self._tool_self_cal_initialized:
            self._tool_self_cal_info = None
            self._tool_self_cal_initialized = False
            return ReturnCode.ERROR

        if save:
            fix_result = self._ap.E_ToolFixRlt.eToolFixSave
        else:
            fix_result = self._ap.E_ToolFixRlt.eToolFixCancle
        ret = self._ap.Aim_SaveToolSelfCalibration(self._handle, fix_result)
        return_code = self._from_aim_return_code(ret)
        self._tool_self_cal_info = None
        self._tool_self_cal_initialized = False
        return return_code

    def tool_tip_calibration_init(
        self,
        calibration_board_tool_name: str,
        tool_name: str,
    ) -> ReturnCode:
        """Initialize tooltip calibration with a calibration board and tool.

        Args:
            calibration_board_tool_name: Registration board tool ID.
            tool_name: Tool ID whose tip will be calibrated.

        Returns:
            ReturnCode: Result from Aim_InitToolTipCalibrationWithToolId.
        """
        if not self._connected:
            self._tool_tip_cal_info = None
            self._tool_tip_cal_initialized = False
            return ReturnCode.NOT_CONNECTED
        if self._handle is None:
            self._tool_tip_cal_info = None
            self._tool_tip_cal_initialized = False
            return ReturnCode.INVALID_HANDLE
        if not self._tool_path_set:
            self._tool_tip_cal_info = None
            self._tool_tip_cal_initialized = False
            return ReturnCode.ERROR
        if not calibration_board_tool_name or not tool_name:
            self._tool_tip_cal_info = None
            self._tool_tip_cal_initialized = False
            return ReturnCode.ERROR

        ret = self._ap.Aim_InitToolTipCalibrationWithToolId(
            self._handle,
            calibration_board_tool_name,
            tool_name,
        )
        return_code = self._from_aim_return_code(ret)
        if return_code is ReturnCode.OK:
            self._tool_tip_cal_info = self._ap.t_ToolTipCalProInfo()
            self._tool_tip_cal_initialized = True
        else:
            self._tool_tip_cal_info = None
            self._tool_tip_cal_initialized = False
        return return_code

    def tool_tip_calibration_process(
        self,
    ) -> tuple[ReturnCode, ToolTipCalibrationProgress]:
        """Capture markers and advance tooltip calibration progress.

        Returns:
            tuple[ReturnCode, ToolTipCalibrationProgress]: ReturnCode and progress.
        """
        empty_progress = ToolTipCalibrationProgress()
        if not self._connected:
            return (ReturnCode.NOT_CONNECTED, empty_progress)
        if self._handle is None:
            return (ReturnCode.INVALID_HANDLE, empty_progress)
        tool_tip_cal_info = self._tool_tip_cal_info
        if not self._tool_tip_cal_initialized or tool_tip_cal_info is None:
            return (ReturnCode.ERROR, empty_progress)
        if self.acquired_data not in (AcquiredDataType.INFO, AcquiredDataType.NONE):
            return (ReturnCode.STALE_DATA, empty_progress)

        interface = self._to_aim_connection_interface(self.conn_interface)
        marker_info = self._ap.T_MarkerInfo()
        status_info = self._ap.T_AimPosStatusInfo()
        ret = self._ap.Aim_GetMarkerAndStatusFromHardware(
            self._handle,
            interface,
            marker_info,
            status_info,
        )
        attempts = 0
        while ret == self._ap.AIMOOE_NOT_REFLASH and attempts < 5:
            time.sleep(0.01)
            ret = self._ap.Aim_GetMarkerAndStatusFromHardware(
                self._handle,
                interface,
                marker_info,
                status_info,
            )
            attempts += 1
        return_code = self._from_aim_return_code(ret)
        if return_code is not ReturnCode.OK:
            return (return_code, empty_progress)

        ret = self._ap.Aim_ProceedToolTipCalibration(
            self._handle,
            marker_info,
            tool_tip_cal_info,
        )
        return_code = self._from_aim_return_code(ret)
        if return_code is not ReturnCode.OK:
            return (return_code, empty_progress)

        progress = ToolTipCalibrationProgress(
            board_found=bool(tool_tip_cal_info.isBoardFind),
            tool_found=bool(tool_tip_cal_info.isToolFind),
            valid_calibration=bool(tool_tip_cal_info.isValidCalibrate),
            finished=bool(tool_tip_cal_info.isCalibrateFinished),
            calibration_error=float(tool_tip_cal_info.CalibrateError),
            progress_rate=float(tool_tip_cal_info.CalibrateRate),
            rms_error=float(tool_tip_cal_info.CalRMSError),
        )
        return (ReturnCode.OK, progress)

    def tool_tip_calibration_finish(self, save: bool) -> ReturnCode:
        """Finalize tooltip calibration and optionally save the result.

        Args:
            save: Whether to persist the calibrated tooltip data to the tool file.

        Returns:
            ReturnCode: Save result, or OK when calibration is discarded.
        """
        if not self._connected:
            self._tool_tip_cal_info = None
            self._tool_tip_cal_initialized = False
            return ReturnCode.NOT_CONNECTED
        if self._handle is None:
            self._tool_tip_cal_info = None
            self._tool_tip_cal_initialized = False
            return ReturnCode.INVALID_HANDLE
        if not self._tool_tip_cal_initialized:
            self._tool_tip_cal_info = None
            self._tool_tip_cal_initialized = False
            return ReturnCode.ERROR

        if save:
            ret = self._ap.Aim_SaveToolTipCalibration(self._handle)
            return_code = self._from_aim_return_code(ret)
        else:
            return_code = ReturnCode.OK
        self._tool_tip_cal_info = None
        self._tool_tip_cal_initialized = False
        return return_code

    def tool_tip_pivot_init(
        self,
        tool_name: str,
        clear_tip_mid: bool = False,
    ) -> ReturnCode:
        """Initialize tooltip pivot calibration for a tool.

        Args:
            tool_name: Tool ID whose tip will be calibrated by pivoting.
            clear_tip_mid: Whether to clear existing tip-mid data before pivoting.

        Returns:
            ReturnCode: Result from Aim_InitToolTipPivotWithToolId.
        """
        if not self._connected:
            self._tool_tip_pivot_info = None
            self._tool_tip_pivot_initialized = False
            return ReturnCode.NOT_CONNECTED
        if self._handle is None:
            self._tool_tip_pivot_info = None
            self._tool_tip_pivot_initialized = False
            return ReturnCode.INVALID_HANDLE
        if not self._tool_path_set:
            self._tool_tip_pivot_info = None
            self._tool_tip_pivot_initialized = False
            return ReturnCode.ERROR
        if not tool_name:
            self._tool_tip_pivot_info = None
            self._tool_tip_pivot_initialized = False
            return ReturnCode.ERROR

        ret = self._ap.Aim_InitToolTipPivotWithToolId(
            self._handle,
            tool_name,
            bool(clear_tip_mid),
        )
        return_code = self._from_aim_return_code(ret)
        if return_code is ReturnCode.OK:
            self._tool_tip_pivot_info = self._ap.T_ToolTipPivotInfo()
            self._tool_tip_pivot_initialized = True
        else:
            self._tool_tip_pivot_info = None
            self._tool_tip_pivot_initialized = False
        return return_code

    def tool_tip_pivot_process(self) -> tuple[ReturnCode, ToolTipPivotProgress]:
        """Capture markers and advance tooltip pivot calibration progress.

        Returns:
            tuple[ReturnCode, ToolTipPivotProgress]: ReturnCode and pivot progress.
        """
        empty_progress = ToolTipPivotProgress()
        if not self._connected:
            return (ReturnCode.NOT_CONNECTED, empty_progress)
        if self._handle is None:
            return (ReturnCode.INVALID_HANDLE, empty_progress)
        tool_tip_pivot_info = self._tool_tip_pivot_info
        if not self._tool_tip_pivot_initialized or tool_tip_pivot_info is None:
            return (ReturnCode.ERROR, empty_progress)
        if self.acquired_data not in (AcquiredDataType.INFO, AcquiredDataType.NONE):
            return (ReturnCode.STALE_DATA, empty_progress)

        interface = self._to_aim_connection_interface(self.conn_interface)
        marker_info = self._ap.T_MarkerInfo()
        status_info = self._ap.T_AimPosStatusInfo()
        ret = self._ap.Aim_GetMarkerAndStatusFromHardware(
            self._handle,
            interface,
            marker_info,
            status_info,
        )
        attempts = 0
        while ret == self._ap.AIMOOE_NOT_REFLASH and attempts < 5:
            time.sleep(0.01)
            ret = self._ap.Aim_GetMarkerAndStatusFromHardware(
                self._handle,
                interface,
                marker_info,
                status_info,
            )
            attempts += 1
        return_code = self._from_aim_return_code(ret)
        if return_code is not ReturnCode.OK:
            return (return_code, empty_progress)

        ret = self._ap.Aim_ProceedToolTipPivot(
            self._handle,
            marker_info,
            tool_tip_pivot_info,
        )
        return_code = self._from_aim_return_code(ret)
        if return_code is not ReturnCode.OK:
            return (return_code, empty_progress)

        progress = ToolTipPivotProgress(
            tool_found=bool(tool_tip_pivot_info.isToolFind),
            finished=bool(tool_tip_pivot_info.isPivotFinished),
            progress_rate=float(tool_tip_pivot_info.pivotRate),
            mean_error=float(tool_tip_pivot_info.pivotMeanError),
        )
        return (ReturnCode.OK, progress)

    def tool_tip_pivot_finish(self, save: bool) -> ReturnCode:
        """Finalize tooltip pivot calibration and optionally save the result.

        Args:
            save: Whether to persist the pivot-calibrated tooltip data.

        Returns:
            ReturnCode: Save result, or OK when calibration is discarded.
        """
        if not self._connected:
            self._tool_tip_pivot_info = None
            self._tool_tip_pivot_initialized = False
            return ReturnCode.NOT_CONNECTED
        if self._handle is None:
            self._tool_tip_pivot_info = None
            self._tool_tip_pivot_initialized = False
            return ReturnCode.INVALID_HANDLE
        if not self._tool_tip_pivot_initialized:
            self._tool_tip_pivot_info = None
            self._tool_tip_pivot_initialized = False
            return ReturnCode.ERROR

        if save:
            save_cmd = int(self._ap.E_ToolFixRlt.eToolFixSave.value)
            ret = self._ap.Aim_SaveToolTipPivot(self._handle, save_cmd)
            return_code = self._from_aim_return_code(ret)
        else:
            return_code = ReturnCode.OK
        self._tool_tip_pivot_info = None
        self._tool_tip_pivot_initialized = False
        return return_code
