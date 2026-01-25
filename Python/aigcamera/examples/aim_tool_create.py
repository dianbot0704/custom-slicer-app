"""Example: Create a 4-point tool using the Aim backend.

This demonstrates the tool creation workflow:
1. Connect to the AimPosition device
2. Set the tools path
3. Initialize tool creation with marker count and name
4. Loop calling tool_create_process() until finished
5. Save or discard the tool file
6. Disconnect
"""

from pathlib import Path
import time

from aigcamera.backend.aim import AimCamera
from aigcamera.types import (
    AcquiredDataType,
    ConnectionInterface,
    ReturnCode,
)


if __name__ == "__main__":
    import os

    cam = AimCamera()
    cam.set_connection_interface(ConnectionInterface.ETHERNET)
    ret = cam.connect()
    if ret is not ReturnCode.OK:
        print(f"Failed to connect: {ret}")
        exit(1)
    print("Connected to AimPosition device")

    tools_path = Path(os.getcwd()).resolve() / "AimTools"
    if not tools_path.is_dir():
        print(f"Tools directory not found: {tools_path}")
        cam.disconnect()
        exit(1)
    cam.set_tools_path(tools_path)

    # Tool creation requires AcquiredDataType.NONE or INFO
    cam.set_acquired_data(AcquiredDataType.NONE)

    tool_name = "my_4pt_tool"
    marker_count = 4
    ret = cam.tool_create_init(marker_count, tool_name)
    if ret is not ReturnCode.OK:
        print(f"Failed to initialize tool creation: {ret}")
        cam.disconnect()
        exit(1)
    print(f"Initialized tool creation: {tool_name} ({marker_count} markers)")

    print("Hold tool steady in view. Press Ctrl+C to cancel.\n")
    try:
        while True:
            time.sleep(0.01)
            ret, progress = cam.tool_create_process()
            if ret is not ReturnCode.OK:
                continue
            print(f"Progress: {progress.progress_rate * 100:.1f}%", end="\r")
            if progress.finished:
                print(f"\nTool creation finished! Error: {progress.error:.4f} mm")
                break
    except KeyboardInterrupt:
        print("\nCancelled by user")
        cam.tool_create_finish(save=False)
        cam.disconnect()
        exit(0)

    ret = cam.tool_create_finish(save=True)
    if ret is ReturnCode.OK:
        print(f"Tool saved: {tool_name}.aimtool")
    else:
        print(f"Failed to save tool: {ret}")

    cam.disconnect()
    print("Disconnected")
