import os
import sys
from contextlib import ExitStack
from importlib.machinery import ExtensionFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

_AIMPOS_MODULE_NAME = "aigcamera._aimpos"
_AIMPOS_INIT_NAME = "AimPosition"
_AIMPOS_LINUX_FILENAME = "AimPosition312.so"
_AIMPOS_WINDOWS_FILENAME = "AimPosition312.pyd"


def _aimpos_library_path(platform: str | None = None) -> Path:
    selected_platform = platform or sys.platform
    if selected_platform == "win32":
        filename = _AIMPOS_WINDOWS_FILENAME
    elif selected_platform.startswith("linux"):
        filename = _AIMPOS_LINUX_FILENAME
    else:
        raise RuntimeError(
            f"AimPosition is not supported on platform {selected_platform!r}"
        )
    return Path(__file__).parent / "_native" / filename


def _windows_dll_directories(native_dir: Path) -> list[Path]:
    directories = [native_dir]
    system_root = os.environ.get("SystemRoot") or os.environ.get("WINDIR")
    if system_root:
        directories.append(Path(system_root) / "System32" / "Npcap")
    return directories


def load_aimpos(module_name: str = _AIMPOS_MODULE_NAME) -> ModuleType:
    """Load the platform-specific AimPosition extension module.

    The extension exports the init symbol for ``AimPosition``. The loaded
    module is also registered under the internal ``aigcamera._aimpos`` alias.
    """
    cached = sys.modules.get(module_name) or sys.modules.get(_AIMPOS_INIT_NAME)
    if cached is not None:
        sys.modules.setdefault(module_name, cached)
        return cached

    lib_path = _aimpos_library_path()
    if not lib_path.is_file():
        raise RuntimeError(f"AimPosition library not found at {lib_path}")

    loader = ExtensionFileLoader(_AIMPOS_INIT_NAME, str(lib_path))
    spec = spec_from_file_location(_AIMPOS_INIT_NAME, lib_path, loader=loader)
    if spec is None or spec.loader is None:
        raise RuntimeError("AimPosition library could not be loaded")

    try:
        with ExitStack() as dll_directories:
            if sys.platform == "win32":
                for directory in _windows_dll_directories(lib_path.parent):
                    if directory.is_dir():
                        dll_directories.enter_context(
                            os.add_dll_directory(str(directory))
                        )

            module = module_from_spec(spec)
            sys.modules[_AIMPOS_INIT_NAME] = module
            spec.loader.exec_module(module)
    except (ImportError, OSError) as exc:
        sys.modules.pop(_AIMPOS_INIT_NAME, None)
        detail = ""
        if sys.platform == "win32":
            detail = " Ensure libusb0.dll is bundled and Npcap provides wpcap.dll."
        raise RuntimeError(
            f"AimPosition library could not be loaded from {lib_path}.{detail}"
        ) from exc

    if module_name != _AIMPOS_INIT_NAME:
        sys.modules[module_name] = module
    return module
