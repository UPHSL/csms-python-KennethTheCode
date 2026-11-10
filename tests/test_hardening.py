from datetime import date
import pytest

from csms.models.resident import Resident
from csms.models.service_request import ServiceRequest
from csms.repositories.resident_repository import ResidentRepository
from csms.repositories.service_request_repository import ServiceRequestRepository
from csms.services.resident_deactivation_service import ResidentDeactivationService


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "t15_hardening.sqlite")


@pytest.fixture
def app_client(db_path):
    from csms import create_app

    app = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": db_path,
            "SECRET_KEY": "test-key",
            "APP_NAME": "CSMS",
            "APP_VERSION": "0.1.0",
            "CURRENT_SPRINT": "Sprint 5",
        }
    )
    return app.test_client()


def save_resident(db_path, **overrides) -> Resident:
    repo = ResidentRepository(db_path)
    data = {
        "first_name": "Juan",
        "last_name": "Dela Cruz",
        "address": "Barangay Santo Tomas",
        "contact_number": "09171234567",
        "email": "juan@example.com",
        "status": "Active",
    }
    data.update(overrides)
    res = Resident(**data)
    repo.save(res)
    return res


def save_service_request(db_path, resident_id, **overrides) -> ServiceRequest:
    repo = ServiceRequestRepository(db_path)
    data = {
        "resident_id": resident_id,
        "service_type": "Barangay Clearance",
        "description": "Employment requirement",
        "date_requested": date(2026, 9, 15),
        "status": "Pending",
    }
    data.update(overrides)
    req = ServiceRequest(**data)
    repo.save(req)
    return req


# Category 1: Invalid or Malformed Input (Malformed Route Identifier)
def test_category_1_malformed_route_identifier_handled_safely(app_client):
    """
    Verifies that malformed non-numeric route identifiers (e.g., /residents/abc/edit)
    return a controlled 404 response rather than raising an unhandled server error.
    """
    response_res = app_client.get("/residents/abc/edit")
    assert response_res.status_code == 404

    response_req = app_client.get("/service-requests/not-a-number")
    assert response_req.status_code == 404


# Category 2: Rejected Mutation Protects Persistence
def test_category_2_rejected_update_leaves_persistence_unchanged(app_client, db_path):
    """
    Verifies that an invalid update request with a blank first_name fails
    and leaves the original persisted resident data untouched.
    """
    res = save_resident(db_path, first_name="Juan", last_name="Dela Cruz")

    data = {
        "first_name": "   ",
        "last_name": "Santos",
        "address": "New Address",
        "contact_number": "09170000000",
        "email": "juan.new@example.com",
    }
    response = app_client.post(f"/residents/{res.id}/edit", data=data)
    assert response.status_code == 400

    repo = ResidentRepository(db_path)
    persisted = repo.find_by_id(res.id)
    assert persisted.first_name == "Juan"
    assert persisted.last_name == "Dela Cruz"


# Category 3: Read-Only Request Safety
def test_category_3_read_only_get_requests_do_not_mutate_persistence(app_client, db_path):
    """
    Verifies that visiting read-only pages (dashboard, listing, details)
    does not alter resident or service request counts or data.
    """
    res = save_resident(db_path)
    req = save_service_request(db_path, res.id)

    app_client.get("/dashboard")
    app_client.get("/residents")
    app_client.get("/service-requests")
    app_client.get(f"/service-requests/{req.id}")

    res_repo = ResidentRepository(db_path)
    req_repo = ServiceRequestRepository(db_path)

    assert res_repo.count_all() == 1
    assert req_repo.count_all() == 1
    assert req_repo.find_by_id(req.id).status == "Pending"


# Category 4: Cross-Feature Regression
def test_category_4_resident_deactivation_affects_service_request_submission_eligibility(
    app_client, db_path
):
    """
    Verifies cross-feature interaction: Deactivating an Active resident immediately
    prevents new service requests from being submitted for that resident.
    """
    res = save_resident(db_path, status="Active")
    res_repo = ResidentRepository(db_path)

    # Deactivate Resident
    deactivation_service = ResidentDeactivationService(res_repo)
    deactivation_service.deactivate_resident(res.id)

    # Attempt Submission
    data = {
        "resident_id": str(res.id),
        "service_type": "Clearance",
        "description": "Employment requirement",
        "date_requested": "2026-09-15",
    }
    response = app_client.post("/service-requests/new", data=data)
    assert response.status_code == 400
    assert b"Inactive Residents cannot submit new Service Requests." in response.data

    req_repo = ServiceRequestRepository(db_path)
    assert req_repo.count_all() == 0


# Category 5: Repeatability or Boundary Behavior
def test_category_5_terminal_service_requests_cannot_be_reopened_or_modified(
    app_client, db_path
):
    """
    Verifies boundary protection for terminal requests: Attempting to change status
    of a Completed or Cancelled service request fails and retains the terminal status.
    """
    res = save_resident(db_path)
    req_completed = save_service_request(db_path, res.id, status="Completed")
    req_cancelled = save_service_request(db_path, res.id, status="Cancelled")

    # Attempt to reopen Completed request to In Progress
    resp1 = app_client.post(
        f"/service-requests/{req_completed.id}/status",
        data={"target_status": "In Progress"},
        follow_redirects=True,
    )
    assert resp1.status_code == 200

    # Attempt to transition Cancelled request to Completed
    resp2 = app_client.post(
        f"/service-requests/{req_cancelled.id}/status",
        data={"target_status": "Completed"},
        follow_redirects=True,
    )
    assert resp2.status_code == 200

    req_repo = ServiceRequestRepository(db_path)
    assert req_repo.find_by_id(req_completed.id).status == "Completed"
    assert req_repo.find_by_id(req_cancelled.id).status == "Cancelled"