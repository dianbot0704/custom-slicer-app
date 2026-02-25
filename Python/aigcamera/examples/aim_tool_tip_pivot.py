"""Example: Calibrate tool tip by pivoting around a fixed point with Aim backend.

CLI args: --tools-path, --tool-name.
"""

import argparse
from pathlib import Path
import time

from aigcamera.backend.aim import AimCamera
from aigcamera.types import (
    AcquiredDataType,
    ConnectionInterface,
    ReturnCode,
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calibrate tool tip by pivoting around a fixed point with Aim backend."
    )
    parser.add_argument(
        "--tool-name",
        default="tool",
        help="Tool ID to calibrate.",
    )
    parser.add_argument(
        "--tools-path",
        default="AimTools",
        help="Path to the AimTools directory.",
    )
    args = parser.parse_args()

    cam = AimCamera()
    cam.set_connection_interface(ConnectionInterface.ETHERNET)
    ret = cam.connect()
    if ret is not ReturnCode.OK:
        print(f"Failed to connect: {ret}")
        exit(1)
    print("Connected to AimPosition device")

    tools_path = Path(args.tools_path).expanduser().resolve()
    if not tools_path.is_dir():
        print(f"Tools directory not found: {tools_path}")
        cam.disconnect()
        exit(1)
    cam.set_tools_path(tools_path)

    cam.set_acquired_data(AcquiredDataType.NONE)

    tool_name = args.tool_name
    ret = cam.tool_tip_pivot_init(tool_name, clear_tip_mid=True)
    if ret is not ReturnCode.OK:
        print(f"Failed to initialize pivot calibration: {ret}")
        cam.disconnect()
        exit(1)
    print(f"Initialized pivot calibration: tool={tool_name}")

    print("Rotate tool tip around fixed point. Press Ctrl+C to cancel.\n")
    try:
        while True:
            time.sleep(0.05)
            ret, progress = cam.tool_tip_pivot_process()
            if ret is not ReturnCode.OK:
                continue
            print(f"Progress: {progress.progress_rate * 100:.1f}%", end="\r")
            if progress.finished:
                print(f"\nPivot finished! Mean error: {progress.mean_error:.4f} mm")
                break
    except KeyboardInterrupt:
        print("\nCancelled by user")
        cam.tool_tip_pivot_finish(save=False)
        cam.disconnect()
        exit(0)

    if progress.mean_error < 1.0:
        ret = cam.tool_tip_pivot_finish(save=True)
        if ret is ReturnCode.OK:
            print(f"Pivot calibration saved to: {tool_name}.aimtool")
        else:
            print(f"Failed to save pivot calibration: {ret}")
    else:
        print(f"Mean error too high ({progress.mean_error:.4f} mm), discarding calibration")
        cam.tool_tip_pivot_finish(save=False)

    cam.disconnect()
    print("Disconnected")
