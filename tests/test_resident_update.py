import sqlite3
from contextlib import closing

from csms.models.resident import Resident
from csms.repositories.resident_repository import ResidentRepository
from csms.services.resident_query_service import ResidentQueryService
from csms.services.resident_update_service import ResidentUpdateService
from csms.services.resident_validator import ResidentValidator


# ---------- helpers ----------

def make_repository(tmp_path) -> ResidentRepository:
    return ResidentRepository(str(tmp_path / "t06-residents.sqlite"))


def make_update_service(repository) -> ResidentUpdateService:
    return ResidentUpdateService(ResidentValidator(), repository)


def make_resident(
    first_name="Juan",
    last_name="Cruz",
    contact_number="09171234567",
    email="juan@example.com",
    status="Active",
) -> Resident:
    return Resident(
        first_name=first_name,
        last_name=last_name,
        address="Barangay Santo Tomas",
        contact_number=contact_number,
        email=email,
        status=status,
    )


def save_resident(repository, resident) -> Resident:
    repository.save(resident)
    return resident


def valid_changes(**overrides) -> dict:
    changes = {
        "first_name": "Miguel",
        "last_name": "Santos",
        "address": "Barangay San Isidro",
        "contact_number": "09181234567",
        "email": "miguel.santos@example.com",
    }
    changes.update(overrides)
    return changes


def count_residents(repository) -> int:
    with closing(sqlite3.connect(repository.db_path)) as connection:
        return connection.execute("SELECT COUNT(*) FROM residents").fetchone()[0]


# ---------- Test 1 ----------

def test_valid_resident_update_succeeds(tmp_path):
    repository = make_repository(tmp_path)
    service = make_update_service(repository)
    saved = save_resident(repository, make_resident())

    result = service.update_resident(saved.id, **valid_changes())

    assert result.success is True
    assert result.resident is not None
    assert result.errors == []
    assert result.not_found is False


# ---------- Test 2 ----------

def test_resident_id_is_preserved(tmp_path):
    repository = make_repository(tmp_path)
    service = make_update_service(repository)
    saved = save_resident(repository, make_resident())
    original_id = saved.id

    result = service.update_resident(original_id, **valid_changes())

    assert result.success is True
    assert result.resident.id == original_id
    assert count_residents(repository) == 1


# ---------- Test 3 ----------

def test_permitted_information_is_persisted(tmp_path):
    repository = make_repository(tmp_path)
    service = make_update_service(repository)
    saved = save_resident(repository, make_resident())

    service.update_resident(saved.id, **valid_changes())

    stored = repository.find_by_id(saved.id)

    assert stored is not None
    assert stored.first_name == "Miguel"
    assert stored.last_name == "Santos"
    assert stored.address == "Barangay San Isidro"
    assert stored.contact_number == "09181234567"
    assert stored.email == "miguel.santos@example.com"


# ---------- Test 4 ----------

def test_active_status_is_preserved(tmp_path):
    repository = make_repository(tmp_path)
    service = make_update_service(repository)
    saved = save_resident(repository, make_resident(status="Active"))

    result = service.update_resident(saved.id, **valid_changes())

    assert result.success is True
    assert result.resident.status == "Active"
    assert repository.find_by_id(saved.id).status == "Active"


def test_inactive_status_is_preserved(tmp_path):
    repository = make_repository(tmp_path)
    service = make_update_service(repository)
    saved = save_resident(repository, make_resident(status="Inactive"))

    result = service.update_resident(saved.id, **valid_changes())

    assert result.success is True
    assert result.resident.status == "Inactive"
    assert repository.find_by_id(saved.id).status == "Inactive"


# ---------- Test 5 ----------

def test_invalid_update_fails(tmp_path):
    repository = make_repository(tmp_path)
    service = make_update_service(repository)
    saved = save_resident(repository, make_resident())

    result = service.update_resident(saved.id, **valid_changes(first_name=""))

    assert result.success is False
    assert result.resident is None
    assert "first_name" in result.errors
    assert result.not_found is False


# ---------- Test 6 ----------

def test_invalid_update_does_not_modify_persisted_information(tmp_path):
    repository = make_repository(tmp_path)
    service = make_update_service(repository)
    saved = save_resident(repository, make_resident())

    result = service.update_resident(
        saved.id,
        **valid_changes(first_name="", contact_number="ABC"),
    )

    stored = repository.find_by_id(saved.id)

    assert result.success is False
    assert stored.first_name == "Juan"
    assert stored.last_name == "Cruz"  # valid-looking field was NOT saved
    assert stored.address == "Barangay Santo Tomas"
    assert stored.contact_number == "09171234567"
    assert stored.email == "juan@example.com"


# ---------- Test 7 ----------

def test_updating_nonexistent_resident_is_handled_safely(tmp_path):
    repository = make_repository(tmp_path)
    service = make_update_service(repository)

    result = service.update_resident(999999, **valid_changes())

    assert result.success is False
    assert result.not_found is True
    assert result.resident is None
    assert result.errors == []


# ---------- Test 8 ----------

def test_nonexistent_update_does_not_create_a_resident(tmp_path):
    repository = make_repository(tmp_path)
    service = make_update_service(repository)
    save_resident(repository, make_resident())

    count_before = count_residents(repository)

    service.update_resident(999999, **valid_changes())

    assert count_residents(repository) == count_before
    assert repository.find_by_id(999999) is None


# ---------- Test 9 ----------

def test_updated_resident_is_visible_through_t05_querying(tmp_path):
    repository = make_repository(tmp_path)
    update_service = make_update_service(repository)
    query_service = ResidentQueryService(repository)
    saved = save_resident(repository, make_resident("Juan", "Cruz"))

    update_service.update_resident(
        saved.id,
        **valid_changes(first_name="Miguel", last_name="Santos"),
    )

    found = query_service.search_residents("Miguel")
    listed = query_service.list_residents()

    assert [r.id for r in found] == [saved.id]
    assert query_service.search_residents("Cruz") == []
    assert [(r.first_name, r.last_name) for r in listed] == [("Miguel", "Santos")]


# ---------- Test 10 ----------

def test_updated_information_and_contact_number_are_preserved(tmp_path):
    repository = make_repository(tmp_path)
    service = make_update_service(repository)
    saved = save_resident(repository, make_resident(status="Inactive"))

    service.update_resident(saved.id, **valid_changes(contact_number="09181234567"))

    stored = repository.find_by_id(saved.id)

    assert stored.first_name == "Miguel"
    assert stored.last_name == "Santos"
    assert stored.address == "Barangay San Isidro"
    assert stored.email == "miguel.santos@example.com"
    assert stored.contact_number == "09181234567"  # leading zero kept
    assert stored.id == saved.id
    assert stored.status == "Inactive"


# ---------- Extra: other residents are not modified ----------

def test_update_does_not_modify_other_residents(tmp_path):
    repository = make_repository(tmp_path)
    service = make_update_service(repository)
    target = save_resident(repository, make_resident("Juan", "Cruz"))
    other = save_resident(
        repository,
        make_resident(
            "Maria",
            "Reyes",
            contact_number="09171234562",
            email="maria@example.com",
        ),
    )

    service.update_resident(target.id, **valid_changes())

    untouched = repository.find_by_id(other.id)

    assert untouched.first_name == "Maria"
    assert untouched.last_name == "Reyes"
    assert untouched.contact_number == "09171234562"
    assert untouched.email == "maria@example.com"
    assert untouched.status == "Active"