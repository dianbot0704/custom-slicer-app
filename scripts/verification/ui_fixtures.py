"""UI-only dependencies. No disk database, migration, receiver, or camera connection.

Imported only by the sandbox discovery bootstrap. Real widget controllers,
PIN hashing/verification, session state, workflow gates, and rendering remain
unchanged. Unsupported persistence operations fail rather than pretending to
save data. This is not a database or hardware integration test.
"""

import logging
import sqlite3
import sys
import traceback
from pathlib import Path
from typing import Optional

from Core.camera_worker import CameraBackgroundWorker
from Pages.login.pin_policy import hash_pin
from Pages.login.surgeon_database import SurgeonLoginRecord
from Pages.scan_patient.dicom_receiver_service import DicomReceiverService
from Runtime import IntraopPlannerImpl as runtime

FIXTURE_PIN = "246810"
FIXTURE_PIN_HASH, FIXTURE_PIN_SALT = hash_pin(FIXTURE_PIN)
FIXTURE_SURGEON = SurgeonLoginRecord(
    surgeon_id=101,
    username="ui-verification",
    password_hash=FIXTURE_PIN_HASH,
    salt=FIXTURE_PIN_SALT,
    name="Automation User",
    specialization="UI verification fixture",
)
DISABLED_START_CALLS = {"camera_start": 0, "receiver_start": 0}
APPLICATION_LOG_ERRORS: list[str] = []
PYTHON_CALLBACK_ERRORS: list[str] = []


class ErrorRecorder(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        APPLICATION_LOG_ERRORS.append(self.format(record))


def record_callback_error(exc_type, exc_value, exc_traceback) -> None:  # noqa: ANN001
    formatted_error = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    PYTHON_CALLBACK_ERRORS.append(formatted_error)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def block_sqlite_connections(*_args, **_kwargs):
    raise RuntimeError("Disk databases and migrations are forbidden in UI verification")


class EmptyPatientStore:
    """An empty, read-only patient list. No patient or case is persisted."""

    def close_open_cases(self, _status: str, _reason: str) -> None:
        """There are no persisted cases to recover or close."""

    def get_all_patients(self) -> list:
        return []

    def get_patients_for_surgeon(self, _surgeon_id: int) -> list:
        return []

    def get_patient_by_id(self, _patient_id: str) -> None:
        return None

    def get_patient_by_uid(self, _patient_uid: int) -> None:
        return None

    def get_series_for_case(self, _case_id: int) -> list:
        return []

    def get_fluoro_captures_for_case(self, _case_id: int) -> list:
        return []

    def validate_patient_fields(self, _record) -> None:
        raise RuntimeError("Patient writes are outside the UI verification scope")

    def close(self) -> None:
        """There is no connection to release."""


class UiRegistrationManager(runtime.RegistrationManager):
    def initialize(self) -> None:
        # The real constructor creates a repository object but does not open it.
        self._database = EmptyPatientStore()


class FixtureSurgeonStore:
    """A single synthetic account consumed by the real SurgeonManager."""

    def open(self) -> None:
        """The fixture account is already available in memory."""

    def close(self) -> None:
        """There is no connection to release."""

    def get_all_surgeons(self) -> list[SurgeonLoginRecord]:
        return [FIXTURE_SURGEON]

    def get_surgeon_by_username(self, username: str) -> Optional[SurgeonLoginRecord]:
        return FIXTURE_SURGEON if username == FIXTURE_SURGEON.username else None

    def get_surgeon_by_id(self, surgeon_id: int) -> Optional[SurgeonLoginRecord]:
        return FIXTURE_SURGEON if surgeon_id == FIXTURE_SURGEON.surgeon_id else None

    def increment_login_attempts(self, _surgeon_id: int) -> None:
        FIXTURE_SURGEON.login_attempts += 1

    def reset_login_attempts(self, _surgeon_id: int) -> None:
        FIXTURE_SURGEON.login_attempts = 0

    def update_last_login(self, _surgeon_id: int) -> None:
        """Login timestamps are outside this fixture's persistence-free scope."""


class UiSurgeonManager(runtime.SurgeonManager):
    def __init__(self, _database_path: str) -> None:
        self._db = FixtureSurgeonStore()
        self._fernet = None


def record_camera_start(_worker) -> None:
    DISABLED_START_CALLS["camera_start"] += 1


def record_receiver_start(_receiver) -> None:
    DISABLED_START_CALLS["receiver_start"] += 1


def block_native_camera_access(*_args, **_kwargs):
    raise RuntimeError("Native camera access is forbidden in UI verification")


# Fail closed before changing dependencies if imports escaped the staged module.
_RUNTIME_ROOT = Path(runtime.__file__).resolve().parent.parent
_STAGED_MODULE_ROOT = Path(__file__).resolve().parent.parent
if _RUNTIME_ROOT != _STAGED_MODULE_ROOT:
    raise RuntimeError("Verification resolved the runtime outside its sandbox")

# Record Python errors from setup and Qt callbacks as verification failures.
logging.getLogger().addHandler(ErrorRecorder(level=logging.ERROR))
sys.excepthook = record_callback_error

# Replace storage before any widget can open a database or run migrations.
sqlite3.connect = block_sqlite_connections
runtime.RegistrationManager = UiRegistrationManager
runtime.SurgeonManager = UiSurgeonManager

# Start calls remain observable, but no SDK is loaded and no receiver listens.
CameraBackgroundWorker.start = record_camera_start
CameraBackgroundWorker._initCameraLibrary = block_native_camera_access
CameraBackgroundWorker._initCamera = block_native_camera_access
DicomReceiverService.start = record_receiver_start
