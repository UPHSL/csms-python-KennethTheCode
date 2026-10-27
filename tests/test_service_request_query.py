from datetime import date
import pytest

from csms.models.resident import Resident
from csms.models.service_request import ServiceRequest
from csms.repositories.resident_repository import ResidentRepository
from csms.repositories.service_request_repository import ServiceRequestRepository
from csms.services.service_request_query_service import ServiceRequestQueryService


def make_setup(tmp_path):
    db_path = str(tmp_path / "t11-query.sqlite")
    resident_repository = ResidentRepository(db_path)
    request_repository = ServiceRequestRepository(db_path)
    query_service = ServiceRequestQueryService(request_repository)
    return resident_repository, request_repository, query_service


def save_resident(resident_repository) -> Resident:
    resident = Resident(
        first_name="Juan",
        last_name="Dela Cruz",
        address="Barangay Santo Tomas",
        contact_number="09171234567",
        email="juan@example.com",
    )
    resident_repository.save(resident)
    return resident


def save_service_request(
    request_repository,
    resident_id,
    service_type="Barangay Clearance",
    description="Employment requirement",
    date_requested=date(2026, 9, 15),
    status="Pending",
) -> ServiceRequest:
    request = ServiceRequest(
        resident_id=resident_id,
        service_type=service_type,
        description=description,
        date_requested=date_requested,
        status=status,
    )
    request_repository.save(request)
    return request


# ---------- Test 1 ----------
def test_list_all_persisted_service_requests(tmp_path):
    residents, requests, query_service = make_setup(tmp_path)
    resident = save_resident(residents)
    save_service_request(requests, resident.id, service_type="Clearance")
    save_service_request(requests, resident.id, service_type="Assistance")

    results = query_service.list_service_requests()
    assert len(results) == 2


# ---------- Test 2 ----------
def test_empty_listing_returns_an_empty_collection(tmp_path):
    _, _, query_service = make_setup(tmp_path)
    results = query_service.list_service_requests()
    assert results == []


# ---------- Test 3 ----------
def test_listing_uses_required_ordering(tmp_path):
    residents, requests, query_service = make_setup(tmp_path)
    resident = save_resident(residents)

    req1 = save_service_request(requests, resident.id, date_requested=date(2026, 9, 10))
    req2 = save_service_request(requests, resident.id, date_requested=date(2026, 9, 18))
    req3 = save_service_request(requests, resident.id, date_requested=date(2026, 9, 18))
    req4 = save_service_request(requests, resident.id, date_requested=date(2026, 9, 15))

    results = query_service.list_service_requests()
    ordered_ids = [r.id for r in results]

    assert ordered_ids == [req3.id, req2.id, req4.id, req1.id]


# ---------- Test 4 ----------
def test_view_existing_service_request_by_id(tmp_path):
    residents, requests, query_service = make_setup(tmp_path)
    resident = save_resident(residents)
    saved = save_service_request(requests, resident.id)

    retrieved = query_service.view_service_request(saved.id)
    assert retrieved is not None
    assert retrieved.id == saved.id
    assert retrieved.service_type == "Barangay Clearance"


# ---------- Test 5 ----------
def test_viewing_an_unknown_id_is_handled_safely(tmp_path):
    _, _, query_service = make_setup(tmp_path)
    result = query_service.view_service_request(999999)
    assert result is None


# ---------- Test 6 ----------
def test_partial_service_type_search_is_case_insensitive(tmp_path):
    residents, requests, query_service = make_setup(tmp_path)
    resident = save_resident(residents)
    save_service_request(requests, resident.id, service_type="Barangay Clearance")

    results = query_service.search_service_requests(search_term="cLeAr")
    assert len(results) == 1
    assert results[0].service_type == "Barangay Clearance"


# ---------- Test 7 ----------
def test_partial_description_search_is_case_insensitive(tmp_path):
    residents, requests, query_service = make_setup(tmp_path)
    resident = save_resident(residents)
    save_service_request(
        requests, resident.id, description="Requesting barangay clearance for employment requirements."
    )

    results = query_service.search_service_requests(search_term="EMPLOYMENT")
    assert len(results) == 1


# ---------- Test 8 ----------
def test_blank_search_returns_all_service_requests(tmp_path):
    residents, requests, query_service = make_setup(tmp_path)
    resident = save_resident(residents)
    save_service_request(requests, resident.id)
    save_service_request(requests, resident.id)

    listed = query_service.list_service_requests()
    searched = query_service.search_service_requests(search_term="      ")

    assert [r.id for r in searched] == [r.id for r in listed]


# ---------- Test 9 ----------
def test_no_text_match_returns_an_empty_collection(tmp_path):
    residents, requests, query_service = make_setup(tmp_path)
    resident = save_resident(residents)
    save_service_request(requests, resident.id)

    results = query_service.search_service_requests(search_term="NonExistentTerm")
    assert results == []


# ---------- Test 10 ----------
def test_status_filter_returns_only_matching_status(tmp_path):
    residents, requests, query_service = make_setup(tmp_path)
    resident = save_resident(residents)
    save_service_request(requests, resident.id, status="Pending")
    save_service_request(requests, resident.id, status="Completed")

    results = query_service.search_service_requests(status_filter="Pending")
    assert len(results) == 1
    assert results[0].status == "Pending"


# ---------- Test 11 ----------
def test_unfiltered_query_includes_all_statuses(tmp_path):
    residents, requests, query_service = make_setup(tmp_path)
    resident = save_resident(residents)
    save_service_request(requests, resident.id, status="Pending")
    save_service_request(requests, resident.id, status="In Progress")
    save_service_request(requests, resident.id, status="Completed")
    save_service_request(requests, resident.id, status="Cancelled")

    results = query_service.search_service_requests()
    assert len(results) == 4


# ---------- Test 12 ----------
def test_combined_text_search_and_status_filter(tmp_path):
    residents, requests, query_service = make_setup(tmp_path)
    resident = save_resident(residents)

    save_service_request(
        requests,
        resident.id,
        service_type="Barangay Clearance",
        description="Employment requirement",
        status="Pending",
    )
    save_service_request(
        requests,
        resident.id,
        service_type="Barangay Clearance",
        description="Scholarship requirement",
        status="Completed",
    )
    save_service_request(
        requests,
        resident.id,
        service_type="Community Assistance",
        description="Employment support",
        status="Pending",
    )

    results = query_service.search_service_requests(
        search_term="clearance", status_filter="Pending"
    )
    assert len(results) == 1
    assert results[0].service_type == "Barangay Clearance"
    assert results[0].status == "Pending"


# ---------- Test 13 ----------
def test_matching_service_request_is_not_duplicated(tmp_path):
    residents, requests, query_service = make_setup(tmp_path)
    resident = save_resident(residents)
    save_service_request(
        requests,
        resident.id,
        service_type="Community Assistance",
        description="Assistance requested for medical support",
    )

    results = query_service.search_service_requests(search_term="assistance")
    assert len(results) == 1


# ---------- Test 14 ----------
def test_query_result_preserves_complete_service_request_information(tmp_path):
    residents, requests, query_service = make_setup(tmp_path)
    resident = save_resident(residents)
    saved = save_service_request(
        requests,
        resident.id,
        service_type="Type A",
        description="Desc B",
        date_requested=date(2026, 9, 15),
        status="In Progress",
    )

    retrieved = query_service.search_service_requests(search_term="Type A")[0]

    assert retrieved.id == saved.id
    assert retrieved.resident_id == resident.id
    assert retrieved.service_type == "Type A"
    assert retrieved.description == "Desc B"
    assert retrieved.date_requested == date(2026, 9, 15)
    assert retrieved.status == "In Progress"


def test_unsupported_status_filter_raises_error(tmp_path):
    _, _, query_service = make_setup(tmp_path)
    with pytest.raises(ValueError):
        query_service.search_service_requests(status_filter="Approved")