from importlib.machinery import ExtensionFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType

_AIMPOS_MODULE_NAME = "aigcamera._aimpos"
_AIMPOS_INIT_NAME = "AimPosition"


def _aimpos_library_path() -> Path:
    return Path(__file__).parent / "_native" / "AimPosition312.so"


def load_aimpos(module_name: str = _AIMPOS_MODULE_NAME) -> ModuleType:
    """Load the AimPosition extension module from the bundled library.

    The extension exports the init symbol for "AimPosition", so we load it
    under that name and register any requested alias in sys.modules.
    """
    cached = sys.modules.get(module_name) or sys.modules.get(_AIMPOS_INIT_NAME)
    if cached is not None:
        return cached

    lib_path = _aimpos_library_path()
    if not lib_path.is_file():
        raise RuntimeError(f"AimPosition library not found at {lib_path}")

    loader = ExtensionFileLoader(_AIMPOS_INIT_NAME, str(lib_path))
    spec = spec_from_file_location(_AIMPOS_INIT_NAME, lib_path, loader=loader)
    if spec is None or spec.loader is None:
        raise RuntimeError("AimPosition library could not be loaded")

    module = module_from_spec(spec)
    sys.modules[_AIMPOS_INIT_NAME] = module
    spec.loader.exec_module(module)
    if module_name != _AIMPOS_INIT_NAME:
        sys.modules[module_name] = module
    return module
