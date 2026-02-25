"""Example: Calibrate tool tip with a calibration board using Aim backend.

CLI args: --tools-path, --board-tool-name, --tool-name.
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
        description="Calibrate tool tip with a calibration board using Aim backend."
    )
    parser.add_argument(
        "--board-tool-name",
        default="cal",
        help="Calibration board tool ID.",
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

    board_tool_name = args.board_tool_name
    tool_name = args.tool_name
    ret = cam.tool_tip_calibration_init(board_tool_name, tool_name)
    if ret is not ReturnCode.OK:
        print(f"Failed to initialize tooltip calibration: {ret}")
        cam.disconnect()
        exit(1)
    print(f"Initialized tooltip calibration: board={board_tool_name}, tool={tool_name}")

    print("Move tool and board in view. Press Ctrl+C to cancel.\n")
    try:
        while True:
            time.sleep(0.01)
            ret, progress = cam.tool_tip_calibration_process()
            if ret is not ReturnCode.OK:
                continue
            print(f"Progress: {progress.progress_rate * 100:.1f}%", end="\r")
            if progress.finished:
                print(f"\nCalibration finished! RMS error: {progress.rms_error:.4f} mm")
                break
    except KeyboardInterrupt:
        print("\nCancelled by user")
        cam.tool_tip_calibration_finish(save=False)
        cam.disconnect()
        exit(0)

    if progress.rms_error < 0.5:
        ret = cam.tool_tip_calibration_finish(save=True)
        if ret is ReturnCode.OK:
            print(f"Tooltip calibration saved to: {tool_name}.aimtool")
        else:
            print(f"Failed to save tooltip calibration: {ret}")
    else:
        print(
            f"RMS error too high ({progress.rms_error:.4f} mm), discarding calibration"
        )
        cam.tool_tip_calibration_finish(save=False)

    cam.disconnect()
    print("Disconnected")
