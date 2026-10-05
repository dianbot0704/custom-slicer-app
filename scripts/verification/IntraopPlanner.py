"""Verification-only discovery bootstrap, staged in a temporary module directory."""

import os
import sys
from pathlib import Path

_MODULE_DIR = Path(__file__).resolve().parent
_SANDBOX = Path(os.environ["AKSARATOR_VERIFY_SANDBOX"]).resolve()
if _MODULE_DIR.parent != _SANDBOX:
    raise RuntimeError("The verification bootstrap must run inside its temporary sandbox")
sys.path.insert(0, str(_MODULE_DIR))

# These are copies of the built runtime, including Nuitka extensions, not
# imports from the extension source checkout.
import verification_support  # noqa: E402, F401 - install fixtures before widget setup
from Runtime import IntraopPlannerImpl  # noqa: E402

IntraopPlanner = IntraopPlannerImpl.IntraopPlanner
IntraopPlannerWidget = IntraopPlannerImpl.IntraopPlannerWidget
IntraopPlannerLogic = IntraopPlannerImpl.IntraopPlannerLogic
IntraopPlannerParameterNode = IntraopPlannerImpl.IntraopPlannerParameterNode
