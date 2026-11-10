import pytest
from csms.models.resident import Resident
from csms.repositories.resident_repository import ResidentRepository


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "t12_residents.sqlite")


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
    }
    data.update(overrides)
    res = Resident(**data)
    repo.save(res)
    return res


# Test 1 - Resident Management Page Loads Successfully
def test_resident_management_page_loads(app_client):
    response = app_client.get("/residents")
    assert response.status_code == 200
    assert b"Resident Management" in response.data


# Test 2 - Resident List Displays Persisted Residents
def test_resident_list_displays_persisted_residents(app_client, db_path):
    save_resident(db_path, first_name="Juan", last_name="Cruz")
    save_resident(db_path, first_name="Maria", last_name="Santos")

    response = app_client.get("/residents")
    assert response.status_code == 200
    assert b"Juan Cruz" in response.data
    assert b"Maria Santos" in response.data


# Test 3 - Resident Search Uses Existing Search Behavior
def test_resident_search_uses_existing_behavior(app_client, db_path):
    save_resident(db_path, first_name="Juan", last_name="Dela Cruz")
    save_resident(db_path, first_name="Maria", last_name="Santos")

    response = app_client.get("/residents?search=sAnT")
    assert response.status_code == 200
    assert b"Maria Santos" in response.data
    assert b"Juan Dela Cruz" not in response.data


# Test 4 - Blank Search Displays All Residents
def test_blank_search_displays_all_residents(app_client, db_path):
    save_resident(db_path, first_name="Juan", last_name="Cruz")
    save_resident(db_path, first_name="Maria", last_name="Santos")

    response = app_client.get("/residents?search=   ")
    assert response.status_code == 200
    assert b"Juan Cruz" in response.data
    assert b"Maria Santos" in response.data


# Test 5 - Registration Form Is Accessible
def test_registration_form_is_accessible(app_client):
    response = app_client.get("/residents/register")
    assert response.status_code == 200
    assert b"First Name" in response.data
    assert b"Contact Number" in response.data


# Test 6 - Valid Registration Persists Resident
def test_valid_registration_persists_resident(app_client, db_path):
    data = {
        "first_name": "Ana",
        "last_name": "Reyes",
        "address": "Barangay Santo Tomas",
        "contact_number": "09171234567",
        "email": "ana@example.com",
    }
    response = app_client.post("/residents/register", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Resident registered successfully." in response.data
    assert b"Ana Reyes" in response.data

    repo = ResidentRepository(db_path)
    all_res = repo.find_all()
    assert len(all_res) == 1
    assert all_res[0].status == "Active"


# Test 7 - Invalid Registration Shows Validation Feedback and Does Not Persist
def test_invalid_registration_shows_feedback(app_client, db_path):
    data = {
        "first_name": "",
        "last_name": "Reyes",
        "address": "Barangay Santo Tomas",
        "contact_number": "INVALID",
        "email": "ana.example.com",
    }
    response = app_client.post("/residents/register", data=data)
    assert response.status_code == 400
    assert b"first_name" in response.data or b"contact_number" in response.data

    repo = ResidentRepository(db_path)
    assert len(repo.find_all()) == 0


# Test 8 - Edit Form Displays Existing Resident Information
def test_edit_form_displays_existing_information(app_client, db_path):
    res = save_resident(db_path, first_name="Juan", last_name="Cruz")

    response = app_client.get(f"/residents/{res.id}/edit")
    assert response.status_code == 200
    assert b"Juan" in response.data
    assert b"Cruz" in response.data


# Test 9 - Valid Update Persists Changes
def test_valid_update_persists_changes(app_client, db_path):
    res = save_resident(db_path, first_name="Juan", last_name="Cruz")

    data = {
        "first_name": "Miguel",
        "last_name": "Santos",
        "address": "Barangay San Isidro",
        "contact_number": "09181234567",
        "email": "miguel@example.com",
    }
    response = app_client.post(f"/residents/{res.id}/edit", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Resident information updated successfully." in response.data
    assert b"Miguel Santos" in response.data

    repo = ResidentRepository(db_path)
    updated = repo.find_by_id(res.id)
    assert updated.first_name == "Miguel"
    assert updated.status == "Active"


# Test 10 - Invalid Update Does Not Modify Resident
def test_invalid_update_does_not_modify_resident(app_client, db_path):
    res = save_resident(db_path, first_name="Juan", last_name="Cruz")

    data = {
        "first_name": "",
        "last_name": "Santos",
        "address": "Barangay San Isidro",
        "contact_number": "09181234567",
        "email": "miguel@example.com",
    }
    response = app_client.post(f"/residents/{res.id}/edit", data=data)
    assert response.status_code == 400

    repo = ResidentRepository(db_path)
    original = repo.find_by_id(res.id)
    assert original.first_name == "Juan"


# Test 11 - Missing Resident Edit Is Handled Safely
def test_missing_resident_edit_handled_safely(app_client):
    response = app_client.get("/residents/999999/edit")
    assert response.status_code == 404
    assert b"Resident not found" in response.data


# Test 12 - Active Resident Can Be Deactivated Through Interface
def test_deactivate_active_resident(app_client, db_path):
    res = save_resident(db_path)

    response = app_client.post(f"/residents/{res.id}/deactivate", follow_redirects=True)
    assert response.status_code == 200
    assert b"Resident deactivated successfully." in response.data

    repo = ResidentRepository(db_path)
    deactivated = repo.find_by_id(res.id)
    assert deactivated.status == "Inactive"


# Test 13 - Inactive Resident Remains Visible
def test_inactive_resident_remains_visible(app_client, db_path):
    res = save_resident(db_path, status="Inactive")

    response = app_client.get("/residents")
    assert response.status_code == 200
    assert b"Juan Dela Cruz" in response.data
    assert b"Inactive" in response.data


# Test 14 - GET Requests Do Not Deactivate Residents
def test_get_requests_do_not_deactivate(app_client, db_path):
    res = save_resident(db_path)

    app_client.get(f"/residents/{res.id}/edit")
    app_client.get("/residents")

    repo = ResidentRepository(db_path)
    current = repo.find_by_id(res.id)
    assert current.status == "Active"