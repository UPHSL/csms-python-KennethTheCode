from datetime import date
import pytest

from csms.models.resident import Resident
from csms.models.service_request import ServiceRequest
from csms.repositories.resident_repository import ResidentRepository
from csms.repositories.service_request_repository import ServiceRequestRepository
from csms.services.resident_deactivation_service import ResidentDeactivationService
from csms.services.request_service import ServiceRequestStatusService
from csms.services.dashboard_service import DashboardService


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "t16_final_release.sqlite")


@pytest.fixture
def app_client(db_path):
    from csms import create_app

    app = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": db_path,
            "SECRET_KEY": "test-key",
            "APP_NAME": "Community Services Management System",
            "APP_SHORT_NAME": "CSMS",
            "APP_VERSION": "1.0.0",
        }
    )
    return app.test_client()


# Part G: Release Version Verification Test (/health and UI)
def test_release_version_verification(app_client):
    """
    Automated verification proving that both the /health endpoint and the UI
    consistently report release version 1.0.0.
    """
    response_health = app_client.get("/health")
    assert response_health.status_code == 200
    json_data = response_health.get_json()
    assert json_data["version"] == "1.0.0"

    response_dashboard = app_client.get("/dashboard")
    assert response_dashboard.status_code == 200
    assert b"v1.0.0" in response_dashboard.data


# Part F: Student-Designed Final Examination Integration Test
def test_integrated_resident_lifecycle_service_request_workflow_and_dashboard_reporting(
    app_client, db_path
):
    """
    Cross-module Integration Test:
    1. Resident Lifecycle (Registration & Deactivation)
    2. Service Request Workflow (Pending -> In Progress -> Completed)
    3. Persistence-Level Dashboard Aggregation
    """
    res_repo = ResidentRepository(db_path)
    req_repo = ServiceRequestRepository(db_path)

    # Step A: Register Active Resident
    res = Resident(
        first_name="Juan",
        last_name="Dela Cruz",
        address="123 Mabini St",
        contact_number="09171234567",
        email="juan@example.com",
        status="Active",
    )
    res_repo.save(res)

    # Step B: Submit Request & Progress Workflow
    req = ServiceRequest(
        resident_id=res.id,
        service_type="Clearance",
        description="Requirement for employment",
        date_requested=date(2026, 11, 1),
        status="Pending",
    )
    req_repo.save(req)

    status_service = ServiceRequestStatusService(req_repo)
    status_service.change_status(req.id, "In Progress")
    status_service.change_status(req.id, "Completed")

    # Step C: Verify Dashboard Summarizes Completed State
    dash_service = DashboardService(res_repo, req_repo)
    summary_before = dash_service.get_dashboard_summary()

    assert summary_before["residents"]["active"] == 1
    assert summary_before["residents"]["inactive"] == 0
    assert summary_before["service_requests"]["completed"] == 1
    assert summary_before["service_requests"]["open"] == 0

    # Step D: Deactivate Resident and Verify Aggregate Dashboard Update
    deactivation_service = ResidentDeactivationService(res_repo)
    deactivation_service.deactivate_resident(res.id)

    summary_after = dash_service.get_dashboard_summary()
    assert summary_after["residents"]["active"] == 0
    assert summary_after["residents"]["inactive"] == 1
    assert summary_after["residents"]["total"] == 1

    # Step E: Attempt Submission for Inactive Resident (Rejection & Persistence Protection)
    submit_data = {
        "resident_id": str(res.id),
        "service_type": "Indigency",
        "description": "Financial assistance",
        "date_requested": "2026-11-05",
    }
    resp = app_client.post("/service-requests/new", data=submit_data)
    assert resp.status_code == 400
    assert req_repo.count_all() == 1