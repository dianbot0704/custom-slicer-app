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

from Core.camera_worker import CameraBackgroundWorker
from Pages.login.pin_policy import hash_pin
from Pages.login.surgeon_database import SurgeonLoginRecord
from Pages.scan_patient.dicom_receiver_service import DicomReceiverService
from Runtime import IntraopPlannerImpl as runtime

FIXTURE_PIN = "246810"
PASSWORD_HASH, SALT = hash_pin(FIXTURE_PIN)
SURGEON = SurgeonLoginRecord(
    surgeon_id=101,
    username="ui-verification",
    password_hash=PASSWORD_HASH,
    salt=SALT,
    name="Automation User",
    specialization="UI verification fixture",
)
DISABLED_CALLS = {"camera_start": 0, "receiver_start": 0}
LOG_ERRORS = []
CALLBACK_ERRORS = []


class ErrorRecorder(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        LOG_ERRORS.append(self.format(record))


def record_callback_error(exc_type, exc_value, exc_traceback) -> None:  # noqa: ANN001
    CALLBACK_ERRORS.append("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def blocked_database_connect(*_args, **_kwargs):
    raise RuntimeError("Disk databases and migrations are forbidden in UI verification")


class EmptyPatientStore:
    """An empty, read-only patient list. No patient or case is persisted."""

    def close_open_cases(self, _status: str, _reason: str) -> None:
        pass

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
        pass


class UiRegistrationManager(runtime.RegistrationManager):
    def initialize(self) -> None:
        # The real constructor creates a repository object but does not open it.
        self._database = EmptyPatientStore()


class FixtureSurgeonStore:
    """A single synthetic account consumed by the real SurgeonManager."""

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    def get_all_surgeons(self) -> list:
        return [SURGEON]

    def get_surgeon_by_username(self, username: str):  # noqa: ANN201
        return SURGEON if username == SURGEON.username else None

    def get_surgeon_by_id(self, surgeon_id: int):  # noqa: ANN201
        return SURGEON if surgeon_id == SURGEON.surgeon_id else None

    def increment_login_attempts(self, _surgeon_id: int) -> None:
        SURGEON.login_attempts += 1

    def reset_login_attempts(self, _surgeon_id: int) -> None:
        SURGEON.login_attempts = 0

    def update_last_login(self, _surgeon_id: int) -> None:
        pass


class UiSurgeonManager(runtime.SurgeonManager):
    def __init__(self, _database_path: str) -> None:
        self._db = FixtureSurgeonStore()
        self._fernet = None


def camera_start(_self) -> None:
    DISABLED_CALLS["camera_start"] += 1


def receiver_start(_self) -> None:
    DISABLED_CALLS["receiver_start"] += 1


def blocked_hardware(*_args, **_kwargs):
    raise RuntimeError("Native camera access is forbidden in UI verification")


# Fail closed if this module somehow resolves from outside the copied runtime.
if Path(runtime.__file__).resolve().parent.parent != Path(__file__).resolve().parent.parent:
    raise RuntimeError("Verification resolved the runtime outside its sandbox")
logging.getLogger().addHandler(ErrorRecorder(level=logging.ERROR))
sys.excepthook = record_callback_error
sqlite3.connect = blocked_database_connect
runtime.RegistrationManager = UiRegistrationManager
runtime.SurgeonManager = UiSurgeonManager
CameraBackgroundWorker.start = camera_start
CameraBackgroundWorker._initCameraLibrary = blocked_hardware
CameraBackgroundWorker._initCamera = blocked_hardware
DicomReceiverService.start = receiver_start
