import sqlite3
from contextlib import closing
from datetime import date

import pytest

from csms.models.resident import Resident
from csms.models.service_request import ServiceRequest
from csms.repositories.resident_repository import ResidentRepository
from csms.repositories.service_request_repository import (
    ServiceRequestRepository,
)
from csms.services.request_service import ServiceRequestStatusService
from csms.services.service_request_submission_service import (
    ServiceRequestSubmissionService,
)
from csms.services.service_request_validator import ServiceRequestValidator


# ---------- helpers ----------

def change_status(status_service, service_request_id, target_status):
    return status_service.change_status(service_request_id, target_status)


# Paths that reach each status through the real workflow.
PATH_TO = {
    "Pending": [],
    "In Progress": ["In Progress"],
    "Completed": ["In Progress", "Completed"],
    "Cancelled": ["Cancelled"],
}


def make_setup(tmp_path):
    db_path = str(tmp_path / "t10.sqlite")
    resident_repository = ResidentRepository(db_path)
    request_repository = ServiceRequestRepository(db_path)
    submission_service = ServiceRequestSubmissionService(
        ServiceRequestValidator(),
        resident_repository,
        request_repository,
    )
    status_service = ServiceRequestStatusService(request_repository)
    return resident_repository, request_repository, submission_service, status_service


def submit_pending_request(
    resident_repository,
    submission_service,
    service_type="Barangay Clearance",
    description="Employment requirement",
    date_requested=date(2026, 9, 15),
) -> ServiceRequest:
    resident = Resident(
        first_name="Juan",
        last_name="Dela Cruz",
        address="Barangay Santo Tomas",
        contact_number="09171234567",
        email="juan@example.com",
    )
    resident_repository.save(resident)

    result = submission_service.submit_service_request(
        ServiceRequest(
            resident_id=resident.id,
            service_type=service_type,
            description=description,
            date_requested=date_requested,
        )
    )

    assert result.success is True
    return result.service_request


def reach_status(status_service, service_request_id, status):
    for step in PATH_TO[status]:
        result = change_status(status_service, service_request_id, step)
        assert result.success is True


def information_of(service_request) -> tuple:
    """Everything except status."""
    return (
        service_request.id,
        service_request.resident_id,
        service_request.service_type,
        service_request.description,
        service_request.date_requested,
    )


def count_service_requests(request_repository) -> int:
    with closing(sqlite3.connect(request_repository.db_path)) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM service_requests"
        ).fetchone()[0]


# ---------- Test 1 ----------

def test_pending_can_move_to_in_progress(tmp_path):
    residents, requests, submission, status = make_setup(tmp_path)
    created = submit_pending_request(residents, submission)

    result = change_status(status, created.id, "In Progress")

    assert result.success is True
    assert result.service_request.status == "In Progress"
    assert requests.find_by_id(created.id).status == "In Progress"


# ---------- Test 2 ----------

def test_pending_can_move_to_cancelled(tmp_path):
    residents, requests, submission, status = make_setup(tmp_path)
    created = submit_pending_request(residents, submission)

    result = change_status(status, created.id, "Cancelled")

    assert result.success is True
    assert requests.find_by_id(created.id).status == "Cancelled"


# ---------- Test 3 ----------

def test_in_progress_can_move_to_completed(tmp_path):
    residents, requests, submission, status = make_setup(tmp_path)
    created = submit_pending_request(residents, submission)
    reach_status(status, created.id, "In Progress")

    result = change_status(status, created.id, "Completed")

    assert result.success is True
    assert requests.find_by_id(created.id).status == "Completed"


# ---------- Test 4 ----------

def test_in_progress_can_move_to_cancelled(tmp_path):
    residents, requests, submission, status = make_setup(tmp_path)
    created = submit_pending_request(residents, submission)
    reach_status(status, created.id, "In Progress")

    result = change_status(status, created.id, "Cancelled")

    assert result.success is True
    assert requests.find_by_id(created.id).status == "Cancelled"


# ---------- Test 5 ----------

def test_pending_cannot_move_directly_to_completed(tmp_path):
    residents, requests, submission, status = make_setup(tmp_path)
    created = submit_pending_request(residents, submission)

    result = change_status(status, created.id, "Completed")

    assert result.success is False
    assert result.invalid_transition is True
    assert requests.find_by_id(created.id).status == "Pending"


# ---------- Test 6 ----------

def test_in_progress_cannot_return_to_pending(tmp_path):
    residents, requests, submission, status = make_setup(tmp_path)
    created = submit_pending_request(residents, submission)
    reach_status(status, created.id, "In Progress")

    result = change_status(status, created.id, "Pending")

    assert result.success is False
    assert result.invalid_transition is True
    assert requests.find_by_id(created.id).status == "In Progress"


# ---------- Test 7 ----------

@pytest.mark.parametrize("target", ["Pending", "In Progress", "Cancelled"])
def test_completed_is_terminal(tmp_path, target):
    residents, requests, submission, status = make_setup(tmp_path)
    created = submit_pending_request(residents, submission)
    reach_status(status, created.id, "Completed")

    result = change_status(status, created.id, target)

    assert result.success is False
    assert result.invalid_transition is True
    assert requests.find_by_id(created.id).status == "Completed"


# ---------- Test 8 ----------

@pytest.mark.parametrize("target", ["Pending", "In Progress", "Completed"])
def test_cancelled_is_terminal(tmp_path, target):
    residents, requests, submission, status = make_setup(tmp_path)
    created = submit_pending_request(residents, submission)
    reach_status(status, created.id, "Cancelled")

    result = change_status(status, created.id, target)

    assert result.success is False
    assert result.invalid_transition is True
    assert requests.find_by_id(created.id).status == "Cancelled"


# ---------- Test 9 ----------

@pytest.mark.parametrize(
    "unsupported",
    ["Approved", "Rejected", "Processing", "Done", "Closed", "Archived", "On Hold"],
)
def test_unsupported_status_is_rejected(tmp_path, unsupported):
    residents, requests, submission, status = make_setup(tmp_path)
    created = submit_pending_request(residents, submission)

    result = change_status(status, created.id, unsupported)

    assert result.success is False
    assert result.unsupported_status is True
    assert result.invalid_transition is False
    assert requests.find_by_id(created.id).status == "Pending"


# ---------- Test 10 ----------

def test_nonexistent_service_request_is_handled_safely(tmp_path):
    residents, requests, submission, status = make_setup(tmp_path)
    existing = submit_pending_request(residents, submission)
    before = (information_of(existing), existing.status)
    count_before = count_service_requests(requests)

    result = change_status(status, 999999, "In Progress")

    stored = requests.find_by_id(existing.id)

    assert result.success is False
    assert result.not_found is True
    assert result.service_request is None
    assert requests.find_by_id(999999) is None
    assert count_service_requests(requests) == count_before
    assert (information_of(stored), stored.status) == before


# ---------- Test 11 ----------

def test_successful_transition_preserves_service_request_information(tmp_path):
    residents, requests, submission, status = make_setup(tmp_path)
    created = submit_pending_request(residents, submission)
    before = information_of(requests.find_by_id(created.id))

    change_status(status, created.id, "In Progress")

    after = requests.find_by_id(created.id)

    assert information_of(after) == before
    assert after.status == "In Progress"
    assert count_service_requests(requests) == 1


# ---------- Test 12 ----------

def test_invalid_transition_does_not_modify_persistence(tmp_path):
    residents, requests, submission, status = make_setup(tmp_path)
    created = submit_pending_request(residents, submission)
    before = requests.find_by_id(created.id)

    result = change_status(status, created.id, "Completed")

    after = requests.find_by_id(created.id)

    assert result.success is False
    assert after.status == before.status == "Pending"
    assert information_of(after) == information_of(before)


# ---------- Test 13 ----------

@pytest.mark.parametrize(
    "current", ["Pending", "In Progress", "Completed", "Cancelled"]
)
def test_same_status_request_is_rejected(tmp_path, current):
    residents, requests, submission, status = make_setup(tmp_path)
    created = submit_pending_request(residents, submission)
    reach_status(status, created.id, current)
    before = requests.find_by_id(created.id)

    result = change_status(status, created.id, current)

    after = requests.find_by_id(created.id)

    assert result.success is False
    assert result.invalid_transition is True
    assert after.status == current
    assert information_of(after) == information_of(before)


# ======================================================================
# STUDENT-DESIGNED TEST
# The ticket requires ONE test of your own design. Replace this example
# with your own idea if you can, and explain it in your checkpoint.
# ======================================================================

def test_updated_status_is_persisted(tmp_path):
    residents, requests, submission, status = make_setup(tmp_path)
    created = submit_pending_request(residents, submission)

    change_status(status, created.id, "In Progress")

    new_repository = ServiceRequestRepository(requests.db_path)
    stored = new_repository.find_by_id(created.id)

    assert stored is not None
    assert stored.id == created.id
    assert stored.status == "In Progress"