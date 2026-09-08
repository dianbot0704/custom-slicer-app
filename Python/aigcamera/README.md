# AIGCamera APIs

A pure Python library providing a unified interface for AIGCamera hardware.

## Quick Start

```python
from aigcamera.backend.simulated import SimulatedCamera
from aigcamera.types import ConnectionInterface, ReturnCode

cam = SimulatedCamera()
cam.connect(ConnectionInterface.ETHERNET)

if cam.is_connected():
    print("Camera connected successfully!")

    return_code, status_info = cam.get_status_info()
    if return_code == ReturnCode.OK:
        print(f"CPU Temperature: {status_info.temperature_cpu}°C")

cam.disconnect()
```

## Examples

Run the Aim backend demo script (requires `AimTools` and the bundled
`AimPosition312.so`):

```bash
uv run python examples/aim_backend_demo.py
uv run python examples/aim_tool_self_calibration.py
uv run python examples/aim_tool_tip_calibration.py
uv run python examples/aim_tool_tip_pivot.py
```

Tooltip calibration examples support CLI arguments:

- `examples/aim_tool_tip_calibration.py`: `--tools-path`, `--board-tool-name`, `--tool-name`
- `examples/aim_tool_tip_pivot.py`: `--tools-path`, `--tool-name`

```bash
uv run python examples/aim_tool_tip_calibration.py --tools-path ./AimTools --board-tool-name cal --tool-name tool
uv run python examples/aim_tool_tip_pivot.py --tools-path ./AimTools --tool-name tool
```

## Architecture

The library uses a protocol-first design with two backends:

- **SimulatedCamera**: For testing and development with controllable state
- **AimCamera**: For production hardware interaction

## Types

All types are exported from `aigcamera.types`:

```python
from aigcamera.types import (
    ConnectionInterface,
    ReturnCode,
    ToolType,
    AcquiredDataType,
    CollisionStatus,
    HardwareStatus,
    MarkerBGLightStatus,
    EdgeWarnings,
    ToolInfo,
    CameraStatusInfo,
    MarkersInfo,
    CameraProtocol,
)
```

## Enums

### ConnectionInterface

| Value | Description |
|-------|-------------|
| `ETHERNET` | Ethernet connection |
| `USB` | USB connection |
| `WIFI` | WiFi connection |

### ToolType

| Value | Description |
|-------|-------------|
| `TOOL` | Standard tool |
| `CALIBRATION_BOARD` | Calibration board |

### AcquiredDataType

| Value | Description |
|-------|-------------|
| `NONE` | No data |
| `INFO` | Basic info |
| `MARKER_INFO_WITH_WIFI` | Marker info with WiFi |
| `STATUS_INFO` | Status information |
| `IMG_DUAL` | Dual image |
| `IMG_COLOR` | Color image |
| `INFO_IMG_DUAL` | Info with dual image |
| `INFO_IMG_COLOR` | Info with color image |
| `INFO_IMG_DUAL_COLOR` | Info with dual color image |

### CollisionStatus

| Value | Description |
|-------|-------------|
| `NONE` | No collision |
| `OCCURED` | Collision occurred |
| `DISABLED` | Collision detection disabled |

### HardwareStatus

| Value | Description |
|-------|-------------|
| `OK` | Hardware OK |
| `LCD_VOLTAGE_TOO_LOW` | LCD voltage too low |
| `LCD_VOLTAGE_TOO_HIGH` | LCD voltage too high |
| `IR_LEFT_VOLTAGE_TOO_LOW` | Left IR voltage too low |
| `IR_LEFT_VOLTAGE_TOO_HIGH` | Left IR voltage too high |
| `IR_RIGHT_VOLTAGE_TOO_LOW` | Right IR voltage too low |
| `IR_RIGHT_VOLTAGE_TOO_HIGH` | Right IR voltage too high |
| `GET_INIT_DATA_ERROR` | Error getting init data |

### MarkerBGLightStatus

| Value | Description |
|-------|-------------|
| `OK` | Background light OK |
| `ABNORMAL` | Background light abnormal |

### EdgeWarnings

| Value | Description |
|-------|-------------|
| `NONE` | No warnings |
| `COMMON` | Common warnings |
| `CRITICAL` | Critical warnings |

## Dataclasses

### ToolInfo

Contains information about a detected tool.

| Field | Type | Description |
|-------|------|-------------|
| `tool_type` | `ToolType` | Type of tool |
| `is_valid` | `bool` | Whether the tool detection is valid |
| `tool_name` | `str` | Name of the tool |
| `mean_abs_error` | `float` | Mean absolute error |
| `rms_error` | `float` | Root mean square error |
| `rotation_vector` | `list[float]` | Rotation vector (3 elements) |
| `quaternion` | `list[float]` | Quaternion (4 elements) |
| `rotation_matrix` | `list[float]` | Rotation matrix (9 elements) |
| `translation_vector` | `list[float]` | Translation vector (3 elements) |
| `origin_coordinates` | `list[float]` | Origin coordinates (3 elements) |
| `marker_points` | `list[float]` | Marker points (variable length) |

### CameraStatusInfo

Contains camera status and hardware information.

| Field | Type | Description |
|-------|------|-------------|
| `temperature_cpu` | `float` | CPU temperature in Celsius |
| `temperature_board` | `float` | Board temperature in Celsius |
| `temperature_left` | `float` | Left camera temperature in Celsius |
| `temperature_right` | `float` | Right camera temperature in Celsius |
| `fps_left` | `int` | Left camera frames per second |
| `fps_right` | `int` | Right camera frames per second |
| `fps_color` | `int` | Color camera frames per second |
| `fps_lcd` | `int` | LCD frames per second |
| `exposure_time_left` | `int` | Left camera exposure time |
| `exposure_time_right` | `int` | Right camera exposure time |
| `collision_status` | `CollisionStatus` | Current collision status |
| `hardware_status` | `HardwareStatus` | Current hardware status |

### MarkersInfo

Contains marker detection information.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Marker ID |
| `marker_count` | `int` | Number of markers detected |
| `marker_coordinates` | `list[float]` | Marker coordinates |
| `phantom_marker_warnings` | `list[int]` | Phantom marker warnings |
| `phantom_marker_group_count` | `int` | Number of phantom marker groups |
| `background_light_status` | `MarkerBGLightStatus` | Background light status |
| `marker_warnings` | `list[EdgeWarnings]` | Marker edge warnings |
| `left_out_warnings` | `list[EdgeWarnings]` | Left camera edge warnings |
| `right_out_warnings` | `list[EdgeWarnings]` | Right camera edge warnings |

## Camera Protocol

The `CameraProtocol` defines the interface all camera implementations must follow:

```python
from aigcamera.types import CameraProtocol

cam: CameraProtocol = SimulatedCamera()
```

### Protocol Methods

| Method | Description |
|--------|-------------|
| `connect(interface)` | Connect to the camera |
| `disconnect()` | Disconnect from the camera |
| `is_connected()` | Check connection status |
| `set_acquired_data(data_type)` | Set the type of data to acquire |
| `set_connection_interface(interface)` | Set the connection interface |
| `find_tool(name, min_points)` | Find a specific tool |
| `find_tools(names, min_points)` | Find multiple tools |
| `find_valid_tools(names, min_points)` | Find multiple valid tools |
| `tool_detected(name, min_points)` | Check if a tool is detected |
| `get_status_info()` | Get camera status information |
| `get_markers_info()` | Get markers information |
| `get_tools_path()` | Get the tools directory path |
| `set_tools_path(path)` | Set the tools directory path |

## Aim Backend Advanced Workflows

`AimCamera` exposes additional calibration and tool workflows that are not part
of `CameraProtocol`:

| Method | Description |
|--------|-------------|
| `tool_create_init(marker_count, tool_name)` | Initialize tool creation |
| `tool_create_process()` | Advance tool creation progress |
| `tool_create_finish(save)` | Save or discard tool creation result |
| `tool_self_calibration_init(tool_name)` | Initialize self-calibration |
| `tool_self_calibration_process()` | Advance self-calibration progress |
| `tool_self_calibration_finish(save)` | Save or cancel self-calibration result |
| `tool_tip_calibration_init(board_tool_name, tool_name)` | Initialize tip calibration with board |
| `tool_tip_calibration_process()` | Advance tip calibration progress |
| `tool_tip_calibration_finish(save)` | Save or discard tip calibration result |
| `tool_tip_pivot_init(tool_name, clear_tip_mid=False)` | Initialize tip pivot calibration |
| `tool_tip_pivot_process()` | Advance tip pivot calibration progress |
| `tool_tip_pivot_finish(save)` | Save or discard tip pivot result |

For tool creation and calibration workflows, set acquired data to
`AcquiredDataType.NONE` or `AcquiredDataType.INFO` before processing.

## Native Library Loading

The Aim backend loads the platform-specific vendor extension from `aigcamera/_native`:

- Linux: `AimPosition312.so`
- Windows: `AimPosition312.pyd`

The loader uses `importlib` so the extension is available as `aigcamera._aimpos`. On Windows, it adds the package's
`_native` directory and the standard Npcap installation directory to Python's DLL search path. The Windows extension
also requires `libusb0.dll` beside the `.pyd` and an Npcap installation that provides `wpcap.dll`.

The native files are proprietary and are staged separately rather than committed with the Python source.

## Simulated Camera

The `SimulatedCamera` class provides a fully controllable simulated camera for testing:

```python
from aigcamera.backend.simulated import SimulatedCamera
from aigcamera.types import (
    ConnectionInterface,
    ReturnCode,
    ToolType,
    ToolInfo,
)
```

### Creating a Simulated Camera

```python
cam = SimulatedCamera()
```

### Connection Management

```python
cam.connect(ConnectionInterface.ETHERNET)
# or
cam.connect(ConnectionInterface.USB)
# or
cam.connect(ConnectionInterface.WIFI)

if cam.is_connected():
    print("Connected!")

cam.disconnect()
```

### Setting Configuration

```python
cam.set_connection_interface(ConnectionInterface.ETHERNET)
cam.set_acquired_data(AcquiredDataType.STATUS_INFO)
```

### Tool Management

```python
from aigcamera.types import ToolType

# Create a tool info object
tool = ToolInfo(
    tool_type=ToolType.TOOL,
    is_valid=True,
    tool_name="drb",
    mean_abs_error=0.1,
    rms_error=0.05,
    rotation_vector=[0.1, 0.2, 0.3],
    quaternion=[0.9, 0.1, 0.2, 0.3],
    rotation_matrix=[1, 0, 0, 0, 1, 0, 0, 0, 1],
    translation_vector=[1.0, 2.0, 3.0],
    origin_coordinates=[100.0, 200.0, 300.0],
    marker_points=[0.0, 0.0, 0.0, 10.0, 0.0, 0.0, 0.0, 10.0, 0.0],
)

# Add tool to simulation
cam.sim_add_tool(tool)

# Find the tool
return_code, found_tool = cam.find_tool("drb", min_match_points=3)
if found_tool:
    print(f"Found tool: {found_tool.tool_name}")

# Check if tool is detected
return_code, detected = cam.tool_detected("drb", min_match_points=3)

# Find multiple tools
return_code, tools = cam.find_tools(["drb", "effector"], min_match_points=3)

# Find multiple valid tools only (convenience method)
return_code, valid_tools = cam.find_valid_tools(["drb", "effector"], min_match_points=3)

# Remove a tool
cam.sim_remove_tool("drb")

# Clear all tools
cam.sim_clear_all_tools()
```

### Status and Markers

```python
return_code, status_info = cam.get_status_info()
if return_code == ReturnCode.OK:
    print(f"CPU Temp: {status_info.temperature_cpu}°C")
    print(f"Left FPS: {status_info.fps_left}")
    print(f"Collision Status: {status_info.collision_status}")

return_code, markers_info = cam.get_markers_info()
if return_code == ReturnCode.OK:
    print(f"Marker Count: {markers_info.marker_count}")
```

### Simulation Control Methods

The `SimulatedCamera` provides special methods prefixed with `sim_` for testing:

```python
cam.sim_set_connected(True)           # Set connection state
cam.sim_add_tool(tool)                # Add a tool
cam.sim_remove_tool("name")           # Remove a tool
cam.sim_clear_all_tools()             # Remove all tools
cam.sim_set_status_info(info)         # Set status info
cam.sim_set_markers_info(info)        # Set markers info
```

### Tools Path

```python
from pathlib import Path

cam.set_tools_path(Path("/path/to/tools"))
tools_path = cam.get_tools_path()
```

## Error Handling

All methods return a `ReturnCode` enum value. Never use exceptions for error handling.

```python
return_code, result = cam.find_tool("drb", min_match_points=3)

if return_code == ReturnCode.OK:
    # Success
    process_tool(result)
elif return_code == ReturnCode.CONNECT_ERROR:
    # Handle connection error
    attempt_reconnect()
elif return_code == ReturnCode.READ_FAULT:
    # Handle read error
    retry_or_fail()
else:
    # Handle other errors
    log_error(return_code)
```

## Return Codes

| Code | Value | Description |
|------|-------|-------------|
| `ReturnCode.OK` | 0 | Success |
| `ReturnCode.ERROR` | -1 | General error |
| `ReturnCode.CONNECT_ERROR` | 1 | Connection error |
| `ReturnCode.NOT_CONNECTED` | 2 | Not connected |
| `ReturnCode.READ_FAULT` | 3 | Read fault |
| `ReturnCode.WRITE_FAULT` | 4 | Write fault |
| `ReturnCode.STALE_DATA` | 5 | Stale data |
| `ReturnCode.INIT_FAILED` | 6 | Initialization failed |
| `ReturnCode.INVALID_HANDLE` | 7 | Invalid handle |
