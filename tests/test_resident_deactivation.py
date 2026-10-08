import sqlite3
from contextlib import closing

from csms.models.resident import Resident
from csms.repositories.resident_repository import ResidentRepository
from csms.services.resident_deactivation_service import (
    ResidentDeactivationService,
)
from csms.services.resident_query_service import ResidentQueryService
from csms.services.resident_update_service import ResidentUpdateService
from csms.services.resident_validator import ResidentValidator


# ---------- helpers ----------

def make_repository(tmp_path) -> ResidentRepository:
    return ResidentRepository(str(tmp_path / "t07-residents.sqlite"))


def make_deactivation_service(repository) -> ResidentDeactivationService:
    return ResidentDeactivationService(repository)


def make_resident(
    first_name="Juan",
    last_name="Dela Cruz",
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


def count_residents(repository) -> int:
    with closing(sqlite3.connect(repository.db_path)) as connection:
        return connection.execute("SELECT COUNT(*) FROM residents").fetchone()[0]


def information_of(resident) -> tuple:
    return (
        resident.id,
        resident.first_name,
        resident.last_name,
        resident.address,
        resident.contact_number,
        resident.email,
    )


# ---------- Test 1 ----------

def test_active_resident_can_be_deactivated(tmp_path):
    repository = make_repository(tmp_path)
    service = make_deactivation_service(repository)
    saved = save_resident(repository, make_resident())

    result = service.deactivate_resident(saved.id)

    assert result.success is True
    assert result.resident is not None
    assert result.already_inactive is False
    assert result.not_found is False


# ---------- Test 2 ----------

def test_status_becomes_inactive_in_persistence(tmp_path):
    repository = make_repository(tmp_path)
    service = make_deactivation_service(repository)
    saved = save_resident(repository, make_resident())

    service.deactivate_resident(saved.id)

    stored = repository.find_by_id(saved.id)

    assert stored.status == "Inactive"


# ---------- Test 3 ----------

def test_resident_id_is_preserved(tmp_path):
    repository = make_repository(tmp_path)
    service = make_deactivation_service(repository)
    saved = save_resident(repository, make_resident())
    original_id = saved.id

    result = service.deactivate_resident(original_id)

    assert result.resident.id == original_id
    assert repository.find_by_id(original_id).id == original_id
    assert count_residents(repository) == 1


# ---------- Test 4 ----------

def test_resident_information_is_preserved(tmp_path):
    repository = make_repository(tmp_path)
    service = make_deactivation_service(repository)
    saved = save_resident(repository, make_resident())
    before = information_of(repository.find_by_id(saved.id))

    service.deactivate_resident(saved.id)

    after = repository.find_by_id(saved.id)

    assert information_of(after) == before
    assert after.contact_number == "09171234567"  # leading zero kept
    assert after.status == "Inactive"


# ---------- Test 5 ----------

def test_deactivated_resident_remains_persisted_and_retrievable(tmp_path):
    repository = make_repository(tmp_path)
    service = make_deactivation_service(repository)
    saved = save_resident(repository, make_resident())

    service.deactivate_resident(saved.id)

    stored = repository.find_by_id(saved.id)

    assert stored is not None
    assert stored.status == "Inactive"
    assert count_residents(repository) == 1


# ---------- Test 6 ----------

def test_deactivated_resident_remains_available_through_t05(tmp_path):
    repository = make_repository(tmp_path)
    service = make_deactivation_service(repository)
    query_service = ResidentQueryService(repository)
    saved = save_resident(repository, make_resident("Juan", "Dela Cruz"))

    service.deactivate_resident(saved.id)

    searched = query_service.search_residents("Juan")
    listed = query_service.list_residents()

    assert [r.id for r in searched] == [saved.id]
    assert searched[0].status == "Inactive"
    assert [r.id for r in listed] == [saved.id]
    assert listed[0].status == "Inactive"


# ---------- Test 7 ----------

def test_already_inactive_resident_is_handled_safely(tmp_path):
    repository = make_repository(tmp_path)
    service = make_deactivation_service(repository)
    saved = save_resident(repository, make_resident(status="Inactive"))
    before = information_of(repository.find_by_id(saved.id))

    result = service.deactivate_resident(saved.id)

    after = repository.find_by_id(saved.id)

    assert result.success is True
    assert result.already_inactive is True
    assert result.not_found is False
    assert result.resident.id == saved.id
    assert after.status == "Inactive"
    assert information_of(after) == before
    assert count_residents(repository) == 1


# ---------- Test 8 ----------

def test_nonexistent_resident_is_handled_safely(tmp_path):
    repository = make_repository(tmp_path)
    service = make_deactivation_service(repository)

    result = service.deactivate_resident(999999)

    assert result.success is False
    assert result.not_found is True
    assert result.already_inactive is False
    assert result.resident is None


# ---------- Test 9 ----------

def test_nonexistent_deactivation_does_not_create_or_delete_records(tmp_path):
    repository = make_repository(tmp_path)
    service = make_deactivation_service(repository)
    saved = save_resident(repository, make_resident())
    before = information_of(repository.find_by_id(saved.id))
    count_before = count_residents(repository)

    service.deactivate_resident(999999)

    after = repository.find_by_id(saved.id)

    assert count_residents(repository) == count_before
    assert repository.find_by_id(999999) is None
    assert information_of(after) == before
    assert after.status == "Active"


# ---------- Test 10 ----------

def test_deactivating_one_resident_does_not_affect_another(tmp_path):
    repository = make_repository(tmp_path)
    service = make_deactivation_service(repository)
    target = save_resident(repository, make_resident("Juan", "Cruz"))
    other = save_resident(
        repository,
        make_resident(
            "Maria",
            "Santos",
            contact_number="09171234562",
            email="maria@example.com",
        ),
    )
    other_before = information_of(repository.find_by_id(other.id))

    service.deactivate_resident(target.id)

    target_after = repository.find_by_id(target.id)
    other_after = repository.find_by_id(other.id)

    assert target_after.status == "Inactive"
    assert other_after.status == "Active"
    assert information_of(other_after) == other_before


# ---------- Extra: repeated deactivation is idempotent ----------

def test_repeated_deactivation_leaves_resident_inactive(tmp_path):
    repository = make_repository(tmp_path)
    service = make_deactivation_service(repository)
    saved = save_resident(repository, make_resident())

    first = service.deactivate_resident(saved.id)
    second = service.deactivate_resident(saved.id)

    assert first.success is True
    assert first.already_inactive is False
    assert second.success is True
    assert second.already_inactive is True
    assert repository.find_by_id(saved.id).status == "Inactive"
    assert count_residents(repository) == 1


# ---------- Extra: T06 still preserves status ----------

def test_t06_update_still_preserves_inactive_status(tmp_path):
    repository = make_repository(tmp_path)
    deactivation_service = make_deactivation_service(repository)
    update_service = ResidentUpdateService(ResidentValidator(), repository)
    saved = save_resident(repository, make_resident())

    deactivation_service.deactivate_resident(saved.id)

    result = update_service.update_resident(
        saved.id,
        first_name="Miguel",
        last_name="Santos",
        address="Barangay San Isidro",
        contact_number="09181234567",
        email="miguel@example.com",
    )

    assert result.success is True
    assert result.resident.status == "Inactive"
    assert repository.find_by_id(saved.id).status == "Inactive"