"""Module wrapper that exposes the AimPosition extension."""

import sys

from ._native_loader import load_aimpos

_module = load_aimpos(__name__)
sys.modules[__name__] = _module
