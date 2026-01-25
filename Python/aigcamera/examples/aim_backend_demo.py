from pathlib import Path
import time

from aigcamera.backend.aim import AimCamera
from aigcamera.types import (
    AcquiredDataType,
    CameraProtocol,
    ConnectionInterface,
    ReturnCode,
)


if __name__ == "__main__":
    import os

    cam: CameraProtocol = AimCamera()
    cam.set_connection_interface(ConnectionInterface.ETHERNET)
    ret = cam.connect()
    if ret is ReturnCode.OK:
        print("AIG Camera is connected using Aim backend!")
    else:
        print(f"AIG Camera failed to connect. Error: {ret}")

    tools_path = Path(os.getcwd()).resolve() / "AimTools"
    if tools_path.is_dir():
        cam.set_tools_path(Path(tools_path))
        cam.set_acquired_data(AcquiredDataType.INFO)

        tool_names = ["cal", "tool", "drb"]
        iteration = 0

        print("Starting continuous tool detection loop...")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                iteration += 1
                print(f"\n{'#' * 60}")
                print(f"Iteration {iteration}")
                print(f"{'#' * 60}\n")

                cam.set_acquired_data(AcquiredDataType.INFO)
                ret, found = cam.find_valid_tools(tool_names, min_match_points=3)
                if ret is ReturnCode.OK:
                    print(f"find_tools returned {len(found)} tools\n")

                    for i, tool in enumerate(found, 1):
                        print(f"{'=' * 60}")
                        print(f"Tool #{i}: {tool.tool_name}")
                        print(f"{'=' * 60}")
                        print(f"  Valid:           {tool.is_valid}")
                        print(f"  Type:            {tool.tool_type}")
                        print(f"  Mean Abs Error:  {tool.mean_abs_error:.6f} mm")
                        print(f"  RMS Error:       {tool.rms_error:.6f} mm")
                        print("\n  Rotation Vector (deg):")
                        print(
                            f"    {[v * 180 / 3.14159 for v in tool.rotation_vector]}"
                        )
                        print("\n  Rotation Matrix (3x3):")
                        for row in range(3):
                            start = row * 3
                            print(
                                f"    [{tool.rotation_matrix[start]:8.5f}, {tool.rotation_matrix[start + 1]:8.5f}, {tool.rotation_matrix[start + 2]:8.5f}]"
                            )

                        print(
                            "\n  Translation Vector (Tto - transformation component):"
                        )
                        print(
                            f"    [{tool.translation_vector[0]:8.3f}, {tool.translation_vector[1]:8.3f}, {tool.translation_vector[2]:8.3f}]"
                        )

                        print(
                            "\n  Origin Coordinates (OriginCoor - position in camera space):"
                        )
                        print(
                            f"    [{tool.origin_coordinates[0]:8.3f}, {tool.origin_coordinates[1]:8.3f}, {tool.origin_coordinates[2]:8.3f}]"
                        )

                        print("\n  Marker Points (detected positions):")
                        num_markers = len(tool.marker_points) // 3
                        for pt_idx in range(num_markers):
                            base = pt_idx * 3
                            print(
                                f"    Marker {pt_idx}: [{tool.marker_points[base]:7.2f}, {tool.marker_points[base + 1]:7.2f}, {tool.marker_points[base + 2]:7.2f}]"
                            )
                        print()

                    # Cross-tool comparison
                    if len(found) > 1:
                        print(f"{'=' * 60}")
                        print("Cross-Tool Analysis")
                        print(f"{'=' * 60}")

                        valid_tools = [t for t in found if t.is_valid]
                        if len(valid_tools) > 1:
                            # Compare translation vectors (Tto)
                            tto_unique = len(
                                set(tuple(t.translation_vector) for t in valid_tools)
                            )
                            print(
                                f"  Translation vectors (Tto): {tto_unique}/{len(valid_tools)} unique"
                            )
                            if tto_unique == 1:
                                print(
                                    f"    ⚠️  All tools have SAME Tto: {valid_tools[0].translation_vector}"
                                )
                            else:
                                print("    ✓ Tools have different Tto values")

                            # Compare origin coordinates
                            origin_unique = len(
                                set(tuple(t.origin_coordinates) for t in valid_tools)
                            )
                            print(
                                f"  Origin coordinates: {origin_unique}/{len(valid_tools)} unique"
                            )
                            if origin_unique == 1:
                                print(
                                    f"    ⚠️  WARNING: All tools at SAME position: {valid_tools[0].origin_coordinates}"
                                )
                            else:
                                print("    ✓ Tools have different positions (expected)")
                else:
                    print(f"find_tools failed with error: {ret}")

                # Small delay to avoid overwhelming the output
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n\nReceived Ctrl+C - stopping tool detection loop...")
            print(f"Completed {iteration} iterations")
    else:
        print(
            f"AimTools directory is not found in currently working directory ({tools_path})"
        )

    # Clean shutdown
    print("\nDisconnecting camera...")
    cam.disconnect()
    print("Shutdown complete")
