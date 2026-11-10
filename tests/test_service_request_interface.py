from datetime import date
import pytest

from csms.models.resident import Resident
from csms.models.service_request import ServiceRequest
from csms.repositories.resident_repository import ResidentRepository
from csms.repositories.service_request_repository import ServiceRequestRepository


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "t13_csms.sqlite")


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
            "CURRENT_SPRINT": "Sprint 4",
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


# Test 1 - Service Request Management Page Loads
def test_service_request_management_page_loads(app_client):
    response = app_client.get("/service-requests")
    assert response.status_code == 200
    assert b"Service Request Management" in response.data


# Test 2 - Persisted Service Requests Are Displayed
def test_persisted_service_requests_displayed(app_client, db_path):
    res = save_resident(db_path)
    save_service_request(db_path, res.id, service_type="Barangay Clearance")
    save_service_request(db_path, res.id, service_type="Community Assistance")

    response = app_client.get("/service-requests")
    assert response.status_code == 200
    assert b"Barangay Clearance" in response.data
    assert b"Community Assistance" in response.data


# Test 3 - Required Ordering Is Preserved
def test_required_ordering_is_preserved(app_client, db_path):
    res1 = save_resident(db_path, first_name="Juan")
    res2 = save_resident(db_path, first_name="Maria")
    res3 = save_resident(db_path, first_name="Pedro")

    req1 = save_service_request(db_path, res1.id, date_requested=date(2026, 9, 10))
    req2 = save_service_request(db_path, res2.id, date_requested=date(2026, 9, 18))
    req3 = save_service_request(db_path, res3.id, date_requested=date(2026, 9, 25))

    response = app_client.get("/service-requests")
    data = response.data.decode("utf-8")

    # Match the unique Resident IDs to establish row appearance order
    pos1 = data.find(f"<td>{res1.id}</td>")
    pos2 = data.find(f"<td>{res2.id}</td>")
    pos3 = data.find(f"<td>{res3.id}</td>")

    # Order required: dateRequested DESC, then id DESC
    # req3 (Sep 25) must appear first, then req2 (Sep 18), then req1 (Sep 10)
    assert pos3 < pos2 < pos1


# Test 4 - Text Search Uses T11 Behavior
def test_text_search_uses_t11_behavior(app_client, db_path):
    res = save_resident(db_path)
    save_service_request(db_path, res.id, service_type="Barangay Clearance")
    save_service_request(db_path, res.id, service_type="Medical Aid")

    response = app_client.get("/service-requests?search=cLeAr")
    assert response.status_code == 200
    assert b"Barangay Clearance" in response.data
    assert b"Medical Aid" not in response.data


# Test 5 - Status Filter Uses T11 Behavior
def test_status_filter_uses_t11_behavior(app_client, db_path):
    res = save_resident(db_path)
    save_service_request(db_path, res.id, service_type="Type A", status="Pending")
    save_service_request(db_path, res.id, service_type="Type B", status="Completed")

    response = app_client.get("/service-requests?status=Pending")
    assert response.status_code == 200
    assert b"Type A" in response.data
    assert b"Type B" not in response.data


# Test 6 - Combined Search and Status Filter Works
def test_combined_search_and_status_filter(app_client, db_path):
    res = save_resident(db_path)
    save_service_request(db_path, res.id, service_type="Clearance", status="Pending")
    save_service_request(db_path, res.id, service_type="Clearance", status="Completed")
    save_service_request(db_path, res.id, service_type="Assistance", status="Pending")

    response = app_client.get("/service-requests?search=clearance&status=Pending")
    assert response.status_code == 200
    assert b"Clearance" in response.data
    assert b'<span class="badge badge-Pending">Pending</span>' in response.data
    assert b'<span class="badge badge-Completed">Completed</span>' not in response.data
    assert b"Assistance" not in response.data


# Test 7 - Submission Form Is Accessible
def test_submission_form_is_accessible(app_client):
    response = app_client.get("/service-requests/new")
    assert response.status_code == 200
    assert b"Resident ID" in response.data
    assert b"Service Type" in response.data
    assert b"Description" in response.data


# Test 8 - Valid Submission Persists a Pending Request
def test_valid_submission_persists_pending_request(app_client, db_path):
    res = save_resident(db_path)
    data = {
        "resident_id": str(res.id),
        "service_type": "Permit Request",
        "description": "Business permit requirement",
        "date_requested": "2026-09-15",
    }
    response = app_client.post("/service-requests/new", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Service Request submitted successfully." in response.data
    assert b"Permit Request" in response.data

    repo = ServiceRequestRepository(db_path)
    all_reqs = repo.search_and_filter()
    assert len(all_reqs) == 1
    assert all_reqs[0].status == "Pending"


# Test 9 - Invalid Submission Shows Validation Feedback
def test_invalid_submission_shows_feedback(app_client, db_path):
    res = save_resident(db_path)
    data = {
        "resident_id": str(res.id),
        "service_type": "",
        "description": "",
        "date_requested": "2026-09-15",
    }
    response = app_client.post("/service-requests/new", data=data)
    assert response.status_code == 400
    assert b"service_type" in response.data or b"description" in response.data

    repo = ServiceRequestRepository(db_path)
    assert len(repo.search_and_filter()) == 0


# Test 10 - Missing Resident Submission Is Rejected
def test_missing_resident_submission_rejected(app_client, db_path):
    data = {
        "resident_id": "999999",
        "service_type": "Clearance",
        "description": "Work requirement",
        "date_requested": "2026-09-15",
    }
    response = app_client.post("/service-requests/new", data=data)
    assert response.status_code == 400
    assert b"Resident not found." in response.data


# Test 11 - Inactive Resident Submission Is Rejected
def test_inactive_resident_submission_rejected(app_client, db_path):
    res = save_resident(db_path, status="Inactive")
    data = {
        "resident_id": str(res.id),
        "service_type": "Clearance",
        "description": "Work requirement",
        "date_requested": "2026-09-15",
    }
    response = app_client.post("/service-requests/new", data=data)
    assert response.status_code == 400
    assert b"Inactive Residents cannot submit new Service Requests." in response.data


# Test 12 - Existing Service Request Details Can Be Viewed
def test_view_existing_service_request_details(app_client, db_path):
    res = save_resident(db_path)
    req = save_service_request(db_path, res.id, description="Detailed info text")

    response = app_client.get(f"/service-requests/{req.id}")
    assert response.status_code == 200
    assert b"Detailed info text" in response.data


# Test 13 - Missing Service Request View Is Handled Safely
def test_missing_service_request_view_handled_safely(app_client):
    response = app_client.get("/service-requests/999999")
    assert response.status_code == 404
    assert b"Service Request not found" in response.data


# Test 14 - Pending Request Can Start Processing
def test_pending_request_can_start_processing(app_client, db_path):
    res = save_resident(db_path)
    req = save_service_request(db_path, res.id, status="Pending")

    data = {"target_status": "In Progress"}
    response = app_client.post(f"/service-requests/{req.id}/status", data=data, follow_redirects=True)
    assert response.status_code == 200

    repo = ServiceRequestRepository(db_path)
    assert repo.find_by_id(req.id).status == "In Progress"


# Test 15 - Pending Request Can Be Cancelled
def test_pending_request_can_be_cancelled(app_client, db_path):
    res = save_resident(db_path)
    req = save_service_request(db_path, res.id, status="Pending")

    data = {"target_status": "Cancelled"}
    response = app_client.post(f"/service-requests/{req.id}/status", data=data, follow_redirects=True)
    assert response.status_code == 200

    repo = ServiceRequestRepository(db_path)
    assert repo.find_by_id(req.id).status == "Cancelled"


# Test 16 - In-Progress Request Can Be Completed
def test_in_progress_request_can_be_completed(app_client, db_path):
    res = save_resident(db_path)
    req = save_service_request(db_path, res.id, status="In Progress")

    data = {"target_status": "Completed"}
    response = app_client.post(f"/service-requests/{req.id}/status", data=data, follow_redirects=True)
    assert response.status_code == 200

    repo = ServiceRequestRepository(db_path)
    assert repo.find_by_id(req.id).status == "Completed"


# Test 17 - In-Progress Request Can Be Cancelled
def test_in_progress_request_can_be_cancelled(app_client, db_path):
    res = save_resident(db_path)
    req = save_service_request(db_path, res.id, status="In Progress")

    data = {"target_status": "Cancelled"}
    response = app_client.post(f"/service-requests/{req.id}/status", data=data, follow_redirects=True)
    assert response.status_code == 200

    repo = ServiceRequestRepository(db_path)
    assert repo.find_by_id(req.id).status == "Cancelled"


# Test 18 - Invalid Direct Transition Is Still Rejected
def test_invalid_direct_transition_rejected(app_client, db_path):
    res = save_resident(db_path)
    req = save_service_request(db_path, res.id, status="Pending")

    data = {"target_status": "Completed"}
    response = app_client.post(f"/service-requests/{req.id}/status", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid status transition" in response.data

    repo = ServiceRequestRepository(db_path)
    assert repo.find_by_id(req.id).status == "Pending"


# Test 19 - Completed and Cancelled Requests Remain Visible
def test_terminal_requests_remain_visible(app_client, db_path):
    res = save_resident(db_path)
    req1 = save_service_request(db_path, res.id, service_type="CompletedReq", status="Completed")
    req2 = save_service_request(db_path, res.id, service_type="CancelledReq", status="Cancelled")

    response = app_client.get("/service-requests")
    assert response.status_code == 200
    assert b"CompletedReq" in response.data
    assert b"CancelledReq" in response.data


# Test 20 - GET Requests Do Not Change Service Request State
def test_get_requests_do_not_change_state(app_client, db_path):
    res = save_resident(db_path)
    req = save_service_request(db_path, res.id, status="Pending")

    app_client.get("/service-requests")
    app_client.get(f"/service-requests/{req.id}")
    app_client.get("/service-requests/new")

    repo = ServiceRequestRepository(db_path)
    assert repo.find_by_id(req.id).status == "Pending"