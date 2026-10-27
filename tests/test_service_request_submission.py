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
from csms.services.service_request_submission_service import (
    ServiceRequestSubmissionService,
)
from csms.services.service_request_validator import ServiceRequestValidator


# ---------- helpers ----------

def make_setup(tmp_path):
    db_path = str(tmp_path / "t09.sqlite")
    resident_repository = ResidentRepository(db_path)
    request_repository = ServiceRequestRepository(db_path)
    service = ServiceRequestSubmissionService(
        ServiceRequestValidator(),
        resident_repository,
        request_repository,
    )
    return resident_repository, request_repository, service


def save_resident(repository, status="Active") -> Resident:
    resident = Resident(
        first_name="Juan",
        last_name="Dela Cruz",
        address="Barangay Santo Tomas",
        contact_number="09171234567",
        email="juan@example.com",
        status=status,
    )
    repository.save(resident)
    return resident


def make_service_request(resident_id, **overrides) -> ServiceRequest:
    data = {
        "resident_id": resident_id,
        "service_type": "Barangay Clearance",
        "description": "Request for employment requirement",
        "date_requested": date(2026, 9, 15),
    }
    data.update(overrides)
    return ServiceRequest(**data)


def count_service_requests(request_repository) -> int:
    with closing(sqlite3.connect(request_repository.db_path)) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM service_requests"
        ).fetchone()[0]


def information_of(resident) -> tuple:
    return (
        resident.id,
        resident.first_name,
        resident.last_name,
        resident.address,
        resident.contact_number,
        resident.email,
        resident.status,
    )


# ---------- Test 1 ----------

def test_valid_service_request_submission_succeeds(tmp_path):
    resident_repository, _, service = make_setup(tmp_path)
    resident = save_resident(resident_repository)

    result = service.submit_service_request(make_service_request(resident.id))

    assert result.success is True
    assert result.service_request is not None
    assert result.errors == []
    assert result.resident_not_found is False
    assert result.resident_inactive is False


# ---------- Test 2 ----------

def test_submitted_service_request_receives_a_generated_id(tmp_path):
    resident_repository, _, service = make_setup(tmp_path)
    resident = save_resident(resident_repository)
    service_request = make_service_request(resident.id)

    assert service_request.id is None

    result = service.submit_service_request(service_request)

    assert result.service_request.id is not None
    assert isinstance(result.service_request.id, int)


# ---------- Test 3 ----------

def test_submitted_service_request_is_persisted_and_retrievable(tmp_path):
    resident_repository, request_repository, service = make_setup(tmp_path)
    resident = save_resident(resident_repository)

    result = service.submit_service_request(make_service_request(resident.id))

    stored = request_repository.find_by_id(result.service_request.id)

    assert stored is not None
    assert stored.id == result.service_request.id
    assert count_service_requests(request_repository) == 1


# ---------- Test 4 ----------

def test_submitted_service_request_information_is_preserved(tmp_path):
    resident_repository, request_repository, service = make_setup(tmp_path)
    resident = save_resident(resident_repository)

    result = service.submit_service_request(make_service_request(resident.id))

    stored = request_repository.find_by_id(result.service_request.id)

    assert stored.resident_id == resident.id
    assert stored.service_type == "Barangay Clearance"
    assert stored.description == "Request for employment requirement"
    assert stored.date_requested == date(2026, 9, 15)
    assert stored.status == "Pending"


# ---------- Test 5 ----------

def test_submitted_service_request_status_is_pending(tmp_path):
    resident_repository, request_repository, service = make_setup(tmp_path)
    resident = save_resident(resident_repository)

    result = service.submit_service_request(make_service_request(resident.id))

    assert result.service_request.status == "Pending"
    assert request_repository.find_by_id(result.service_request.id).status == "Pending"


# ---------- Test 6 ----------

@pytest.mark.parametrize("blank_value", ["", "   "])
def test_blank_service_type_fails_validation(tmp_path, blank_value):
    resident_repository, _, service = make_setup(tmp_path)
    resident = save_resident(resident_repository)

    result = service.submit_service_request(
        make_service_request(resident.id, service_type=blank_value)
    )

    assert result.success is False
    assert result.service_request is None
    assert "service_type" in result.errors


# ---------- Test 7 ----------

@pytest.mark.parametrize("blank_value", ["", "   "])
def test_blank_description_fails_validation(tmp_path, blank_value):
    resident_repository, _, service = make_setup(tmp_path)
    resident = save_resident(resident_repository)

    result = service.submit_service_request(
        make_service_request(resident.id, description=blank_value)
    )

    assert result.success is False
    assert result.service_request is None
    assert "description" in result.errors


# ---------- Test 8 ----------

def test_invalid_request_does_not_reach_persistence(tmp_path):
    resident_repository, request_repository, service = make_setup(tmp_path)
    resident = save_resident(resident_repository)
    count_before = count_service_requests(request_repository)

    result = service.submit_service_request(
        make_service_request(resident.id, service_type="", description="")
    )

    assert result.success is False
    assert count_service_requests(request_repository) == count_before


# ---------- Test 9 ----------

def test_nonexistent_resident_prevents_submission(tmp_path):
    _, request_repository, service = make_setup(tmp_path)

    result = service.submit_service_request(make_service_request(999999))

    assert result.success is False
    assert result.resident_not_found is True
    assert result.resident_inactive is False
    assert result.errors == []
    assert result.service_request is None
    assert count_service_requests(request_repository) == 0


# ---------- Test 10 ----------

def test_inactive_resident_cannot_submit_a_new_service_request(tmp_path):
    resident_repository, request_repository, service = make_setup(tmp_path)
    resident = save_resident(resident_repository, status="Inactive")

    result = service.submit_service_request(make_service_request(resident.id))

    assert result.success is False
    assert result.resident_inactive is True
    assert result.resident_not_found is False
    assert result.service_request is None
    assert resident_repository.find_by_id(resident.id).status == "Inactive"
    assert count_service_requests(request_repository) == 0


# ---------- Test 11 ----------

@pytest.mark.parametrize("bad_status", ["In Progress", "Completed", "Cancelled"])
def test_non_pending_initial_status_is_rejected(tmp_path, bad_status):
    resident_repository, request_repository, service = make_setup(tmp_path)
    resident = save_resident(resident_repository)

    result = service.submit_service_request(
        make_service_request(resident.id, status=bad_status)
    )

    assert result.success is False
    assert "status" in result.errors
    assert count_service_requests(request_repository) == 0


# ---------- Test 12 ----------

def test_service_request_persists_across_repository_access(tmp_path):
    resident_repository, request_repository, service = make_setup(tmp_path)
    resident = save_resident(resident_repository)

    result = service.submit_service_request(make_service_request(resident.id))

    second_repository = ServiceRequestRepository(request_repository.db_path)
    stored = second_repository.find_by_id(result.service_request.id)

    assert stored is not None
    assert stored.resident_id == resident.id
    assert stored.service_type == "Barangay Clearance"
    assert stored.date_requested == date(2026, 9, 15)


# ---------- Test 13 ----------

def test_submission_does_not_modify_the_resident(tmp_path):
    resident_repository, _, service = make_setup(tmp_path)
    resident = save_resident(resident_repository)
    before = information_of(resident_repository.find_by_id(resident.id))

    service.submit_service_request(make_service_request(resident.id))

    after = information_of(resident_repository.find_by_id(resident.id))

    assert after == before
    assert after[-1] == "Active"


# ---------- Date validation ----------

@pytest.mark.parametrize("bad_date", [None, "not a date"])
def test_invalid_or_missing_date_cannot_be_persisted(tmp_path, bad_date):
    resident_repository, request_repository, service = make_setup(tmp_path)
    resident = save_resident(resident_repository)

    result = service.submit_service_request(
        make_service_request(resident.id, date_requested=bad_date)
    )

    assert result.success is False
    assert "date_requested" in result.errors
    assert count_service_requests(request_repository) == 0


# ---------- Extra: validator rules on their own ----------

def test_validator_accepts_a_valid_new_service_request():
    service_request = make_service_request(25)

    assert ServiceRequestValidator().validate(service_request) == []


def test_request_with_an_assigned_id_is_not_a_new_submission(tmp_path):
    resident_repository, request_repository, service = make_setup(tmp_path)
    resident = save_resident(resident_repository)

    result = service.submit_service_request(
        make_service_request(resident.id, id=17)
    )

    assert result.success is False
    assert "id" in result.errors
    assert count_service_requests(request_repository) == 0


@pytest.mark.parametrize("bad_resident_id", [None, 0, -5])
def test_structurally_invalid_resident_id_fails_validation(
    tmp_path, bad_resident_id
):
    _, request_repository, service = make_setup(tmp_path)

    result = service.submit_service_request(
        make_service_request(bad_resident_id)
    )

    assert result.success is False
    assert "resident_id" in result.errors
    assert result.resident_not_found is False
    assert count_service_requests(request_repository) == 0