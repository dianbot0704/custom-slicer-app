import os
import unittest
from pathlib import Path
from unittest.mock import patch

from aigcamera import _native_loader


class NativeLoaderPathTests(unittest.TestCase):
    def test_windows_binding_uses_pyd(self) -> None:
        path = _native_loader._aimpos_library_path("win32")

        self.assertEqual(path.name, "AimPosition312.pyd")

    def test_linux_binding_uses_shared_object(self) -> None:
        path = _native_loader._aimpos_library_path("linux")

        self.assertEqual(path.name, "AimPosition312.so")

    def test_unsupported_platform_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "not supported"):
            _native_loader._aimpos_library_path("darwin")

    def test_windows_dll_directories_include_native_and_npcap(self) -> None:
        native_dir = Path("C:/example/aigcamera/_native")
        with patch.dict(os.environ, {"SystemRoot": "C:/Windows"}, clear=True):
            directories = _native_loader._windows_dll_directories(native_dir)

        self.assertEqual(
            directories,
            [native_dir, Path("C:/Windows/System32/Npcap")],
        )


if __name__ == "__main__":
    unittest.main()
