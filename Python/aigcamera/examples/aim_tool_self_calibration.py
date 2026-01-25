"""Example: Self-calibrate an existing tool using the Aim backend.

This demonstrates the tool self-calibration workflow:
1. Connect to the AimPosition device
2. Set the tools path (required - tool must exist)
3. Initialize self-calibration with the tool name
4. Loop calling tool_self_calibration_process() until finished
5. Check calibration accuracy (match_error < 0.5mm recommended)
6. Save or discard the calibrated tool file
7. Disconnect
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

    # Self-calibration requires AcquiredDataType.NONE or INFO
    cam.set_acquired_data(AcquiredDataType.NONE)

    tool_name = "my_4pt_tool"
    ret, total_markers = cam.tool_self_calibration_init(tool_name)
    if ret is not ReturnCode.OK:
        print(f"Failed to initialize self-calibration: {ret}")
        print("Make sure the tool file exists in the tools directory.")
        cam.disconnect()
        exit(1)
    print(f"Initialized self-calibration: {tool_name} ({total_markers} markers)")

    print("Hold tool steady in view. Press Ctrl+C to cancel.\n")
    try:
        while True:
            time.sleep(0.01)
            ret, progress = cam.tool_self_calibration_process()
            if ret is not ReturnCode.OK:
                continue
            print(
                f"Valid calibrations: {progress.valid_calibration_count}",
                end="\r",
            )
            if progress.finished:
                print(
                    f"\nCalibration finished! Match error: {progress.match_error:.4f} mm"
                )
                break
    except KeyboardInterrupt:
        print("\nCancelled by user")
        cam.tool_self_calibration_finish(save=False)
        cam.disconnect()
        exit(0)

    # Only save if accuracy is acceptable (< 0.5mm recommended)
    if progress.match_error < 0.5:
        ret = cam.tool_self_calibration_finish(save=True)
        if ret is ReturnCode.OK:
            print(f"Calibrated tool saved: {tool_name}.aimtool")
        else:
            print(f"Failed to save calibrated tool: {ret}")
    else:
        print(
            f"Match error too high ({progress.match_error:.4f} mm), discarding calibration"
        )
        cam.tool_self_calibration_finish(save=False)

    cam.disconnect()
    print("Disconnected")
