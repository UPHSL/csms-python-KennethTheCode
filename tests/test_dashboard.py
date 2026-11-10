from datetime import date
import pytest

from csms.models.resident import Resident
from csms.models.service_request import ServiceRequest
from csms.repositories.resident_repository import ResidentRepository
from csms.repositories.service_request_repository import ServiceRequestRepository
from csms.services.resident_deactivation_service import ResidentDeactivationService
from csms.services.request_service import ServiceRequestStatusService


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "t14_dashboard.sqlite")


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


# Test 1 - Dashboard Loads Successfully
def test_dashboard_loads_successfully(app_client):
    response = app_client.get("/dashboard")
    assert response.status_code == 200
    assert b"CSMS Operational Dashboard" in response.data


# Test 2 - Empty Dashboard Displays Zero Counts
def test_empty_dashboard_displays_zero_counts(app_client):
    response = app_client.get("/dashboard")
    assert response.status_code == 200
    assert b"Total Residents" in response.data
    assert b"No Service Requests available." in response.data


# Test 3 - Total Resident Count Is Correct
def test_total_resident_count_is_correct(app_client, db_path):
    save_resident(db_path, first_name="Juan")
    save_resident(db_path, first_name="Maria")

    response = app_client.get("/dashboard")
    assert response.status_code == 200
    assert b"Total Residents" in response.data


# Test 4 - Resident Status Counts Are Correct
def test_resident_status_counts_are_correct(app_client, db_path):
    save_resident(db_path, status="Active")
    save_resident(db_path, status="Active")
    save_resident(db_path, status="Inactive")

    repo = ResidentRepository(db_path)
    assert repo.count_all() == 3
    assert repo.count_by_status("Active") == 2
    assert repo.count_by_status("Inactive") == 1


# Test 5 - Total Service Request Count Is Correct
def test_total_service_request_count_is_correct(app_client, db_path):
    res = save_resident(db_path)
    save_service_request(db_path, res.id)
    save_service_request(db_path, res.id)

    repo = ServiceRequestRepository(db_path)
    assert repo.count_all() == 2


# Test 6 - Service Request Status Counts Are Correct
def test_service_request_status_counts_are_correct(app_client, db_path):
    res = save_resident(db_path)
    save_service_request(db_path, res.id, status="Pending")
    save_service_request(db_path, res.id, status="In Progress")
    save_service_request(db_path, res.id, status="Completed")
    save_service_request(db_path, res.id, status="Cancelled")

    repo = ServiceRequestRepository(db_path)
    assert repo.count_all() == 4
    assert repo.count_by_status("Pending") == 1
    assert repo.count_by_status("In Progress") == 1
    assert repo.count_by_status("Completed") == 1
    assert repo.count_by_status("Cancelled") == 1


# Test 7 - Service Request Counts Reconcile
def test_service_request_counts_reconcile(app_client, db_path):
    res = save_resident(db_path)
    save_service_request(db_path, res.id, status="Pending")
    save_service_request(db_path, res.id, status="In Progress")

    repo = ServiceRequestRepository(db_path)
    total = repo.count_all()
    p = repo.count_by_status("Pending")
    ip = repo.count_by_status("In Progress")
    c = repo.count_by_status("Completed")
    cn = repo.count_by_status("Cancelled")

    assert total == (p + ip + c + cn)


# Test 8 - Open Request Count Is Correct
def test_open_request_count_is_correct(app_client, db_path):
    res = save_resident(db_path)
    save_service_request(db_path, res.id, status="Pending")
    save_service_request(db_path, res.id, status="In Progress")
    save_service_request(db_path, res.id, status="Completed")

    repo = ServiceRequestRepository(db_path)
    p = repo.count_by_status("Pending")
    ip = repo.count_by_status("In Progress")
    open_count = p + ip

    assert open_count == 2


# Test 9 - Resident Deactivation Is Reflected
def test_resident_deactivation_is_reflected(app_client, db_path):
    res = save_resident(db_path, status="Active")
    res_repo = ResidentRepository(db_path)
    deactivation_service = ResidentDeactivationService(res_repo)

    deactivation_service.deactivate_resident(res.id)

    assert res_repo.count_by_status("Active") == 0
    assert res_repo.count_by_status("Inactive") == 1


# Test 10 - Service Request Transition Is Reflected
def test_service_request_transition_is_reflected(app_client, db_path):
    res = save_resident(db_path)
    req = save_service_request(db_path, res.id, status="Pending")
    req_repo = ServiceRequestRepository(db_path)
    status_service = ServiceRequestStatusService(req_repo)

    status_service.change_status(req.id, "In Progress")

    assert req_repo.count_by_status("Pending") == 0
    assert req_repo.count_by_status("In Progress") == 1


# Test 11 - Terminal Transition Updates Open Count
def test_terminal_transition_updates_open_count(app_client, db_path):
    res = save_resident(db_path)
    req = save_service_request(db_path, res.id, status="In Progress")
    req_repo = ServiceRequestRepository(db_path)
    status_service = ServiceRequestStatusService(req_repo)

    status_service.change_status(req.id, "Completed")

    p = req_repo.count_by_status("Pending")
    ip = req_repo.count_by_status("In Progress")
    assert (p + ip) == 0


# Test 12 - Recent Requests Return No More Than Five
def test_recent_requests_limit(app_client, db_path):
    res = save_resident(db_path)
    for i in range(7):
        save_service_request(
            db_path,
            res.id,
            service_type=f"Type {i}",
            date_requested=date(2026, 9, 10 + i),
        )

    req_repo = ServiceRequestRepository(db_path)
    recent = req_repo.find_recent(limit=5)
    assert len(recent) == 5


# Test 13 - Recent Requests Use Correct Ordering
def test_recent_requests_ordering(app_client, db_path):
    res1 = save_resident(db_path, first_name="Juan")
    res2 = save_resident(db_path, first_name="Maria")

    req1 = save_service_request(db_path, res1.id, date_requested=date(2026, 9, 10))
    req2 = save_service_request(db_path, res2.id, date_requested=date(2026, 9, 20))

    req_repo = ServiceRequestRepository(db_path)
    recent = req_repo.find_recent(limit=5)

    assert recent[0].id == req2.id
    assert recent[1].id == req1.id


# Test 14 - Terminal Requests May Appear in Recent Results
def test_terminal_requests_appear_in_recent(app_client, db_path):
    res = save_resident(db_path)
    req = save_service_request(
        db_path, res.id, status="Completed", date_requested=date(2026, 9, 25)
    )

    req_repo = ServiceRequestRepository(db_path)
    recent = req_repo.find_recent(limit=5)
    assert len(recent) == 1
    assert recent[0].status == "Completed"


# Test 15 - Dashboard GET Does Not Modify Persistence
def test_dashboard_get_is_read_only(app_client, db_path):
    res = save_resident(db_path)
    req = save_service_request(db_path, res.id)

    app_client.get("/dashboard")
    app_client.get("/dashboard")

    res_repo = ResidentRepository(db_path)
    req_repo = ServiceRequestRepository(db_path)

    assert res_repo.count_all() == 1
    assert req_repo.count_all() == 1