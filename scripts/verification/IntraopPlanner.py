"""Verification-only discovery bootstrap, staged in a temporary module directory."""

import os
import sys
from pathlib import Path

_STAGED_MODULE_DIR = Path(__file__).resolve().parent
_SANDBOX_DIR = Path(os.environ["AKSARATOR_VERIFY_SANDBOX"]).resolve()
if _STAGED_MODULE_DIR.parent != _SANDBOX_DIR:
    raise RuntimeError("The verification bootstrap must run inside its temporary sandbox")
sys.path.insert(0, str(_STAGED_MODULE_DIR))

# Importing verification_support installs fixtures before Slicer creates widgets.
# The runtime classes come from the staged build, not the extension source checkout.
import verification_support  # noqa: E402, F401 - import for fixture installation
from Runtime import IntraopPlannerImpl as runtime  # noqa: E402

IntraopPlanner = runtime.IntraopPlanner
IntraopPlannerWidget = runtime.IntraopPlannerWidget
IntraopPlannerLogic = runtime.IntraopPlannerLogic
IntraopPlannerParameterNode = runtime.IntraopPlannerParameterNode
