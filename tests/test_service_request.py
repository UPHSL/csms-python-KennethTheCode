from datetime import date

from csms.models.service_request import ServiceRequest


# ---------- helper ----------

def make_service_request(
    resident_id=25,
    service_type="Barangay Clearance",
    description="Request for employment requirement",
    date_requested=date(2026, 3, 1),
    **overrides,
) -> ServiceRequest:
    return ServiceRequest(
        resident_id=resident_id,
        service_type=service_type,
        description=description,
        date_requested=date_requested,
        **overrides,
    )


# ---------- Test 1 ----------

def test_service_request_can_be_created():
    service_request = make_service_request()

    assert service_request is not None
    assert isinstance(service_request, ServiceRequest)


# ---------- Test 2 ----------

def test_service_request_information_is_accessible():
    requested_on = date(2026, 3, 1)

    service_request = ServiceRequest(
        resident_id=25,
        service_type="Barangay Clearance",
        description="Request for employment requirement",
        date_requested=requested_on,
    )

    assert service_request.resident_id == 25
    assert service_request.service_type == "Barangay Clearance"
    assert service_request.description == "Request for employment requirement"
    assert service_request.date_requested == requested_on


# ---------- Test 3 ----------

def test_resident_id_is_preserved():
    service_request = make_service_request(resident_id=25)

    assert service_request.resident_id == 25


# ---------- Test 4 ----------

def test_new_service_request_has_an_unassigned_id():
    service_request = make_service_request()

    assert service_request.id is None


# ---------- Test 5 ----------

def test_new_service_request_defaults_to_pending():
    service_request = make_service_request()

    assert service_request.status == "Pending"


# ---------- Test 6 ----------

def test_service_request_information_is_independent_between_objects():
    first = make_service_request(
        resident_id=25,
        service_type="Barangay Clearance",
        description="Employment requirement",
        date_requested=date(2026, 3, 1),
    )
    second = make_service_request(
        resident_id=40,
        service_type="Community Assistance",
        description="Medical assistance for a family member",
        date_requested=date(2026, 4, 15),
    )

    assert first.resident_id == 25
    assert first.service_type == "Barangay Clearance"
    assert first.description == "Employment requirement"
    assert first.date_requested == date(2026, 3, 1)

    assert second.resident_id == 40
    assert second.service_type == "Community Assistance"
    assert second.description == "Medical assistance for a family member"
    assert second.date_requested == date(2026, 4, 15)

    second.description = "Changed afterwards"

    assert first.description == "Employment requirement"


# ---------- Extra: an explicit status is respected ----------

def test_explicitly_supplied_status_is_respected():
    service_request = make_service_request(status="Completed")

    assert service_request.status == "Completed"


# ---------- Extra: the model does not validate ----------

def test_model_represents_data_without_validating_it():
    service_request = make_service_request(
        resident_id=999999,  # resident existence is not checked in T08
        service_type="",
        description="",
        date_requested="not a real date",
    )

    assert service_request.resident_id == 999999
    assert service_request.service_type == ""
    assert service_request.description == ""
    assert service_request.date_requested == "not a real date"
    assert service_request.status == "Pending"