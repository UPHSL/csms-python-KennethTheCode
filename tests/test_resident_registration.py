import sqlite3

from csms.models.resident import Resident
from csms.repositories.resident_repository import (
    ResidentRepository,
)
from csms.services.resident_registration_service import (
    ResidentRegistrationService,
)
from csms.services.resident_validator import (
    ResidentValidator,
)

def make_repository(
    tmp_path,
) -> ResidentRepository:
    database_path = (
        tmp_path / "residents.sqlite"
    )

    return ResidentRepository(
        str(database_path)
    )
def make_registration_service(
    repository,
) -> ResidentRegistrationService:
    validator = ResidentValidator()

    return ResidentRegistrationService(
        validator,
        repository,
    )

def make_valid_resident() -> Resident:
    return Resident(
        first_name="Juan",
        last_name="Dela Cruz",
        address="Barangay Santo Tomas",
        contact_number="09171234567",
        email="juan@example.com",
    )

def make_resident_with_missing_first_name(
) -> Resident:
    return Resident(
        first_name="",
        last_name="Dela Cruz",
        address="Barangay Santo Tomas",
        contact_number="09171234567",
        email="juan@example.com",
    )

def test_registers_valid_resident(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_registration_service(
        repository
    )

    resident = make_valid_resident()

    result = service.register_resident(
        resident
    )

    assert result.success is True

    assert result.resident is not None

    assert result.errors == []

def test_registered_resident_receives_identifier(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_registration_service(
        repository
    )

    resident = make_valid_resident()

    assert resident.id is None

    result = service.register_resident(
        resident
    )

    assert result.success is True

    assert result.resident is not None

    assert result.resident.id is not None

def test_registered_resident_is_persisted(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_registration_service(
        repository
    )

    resident = make_valid_resident()

    result = service.register_resident(
        resident
    )

    assert result.success is True
    assert result.resident is not None
    assert result.resident.id is not None

    stored_resident = (
        repository.find_by_id(
            result.resident.id
        )
    )

    assert stored_resident is not None

    assert (
        stored_resident.id
        == result.resident.id
    )

def test_registered_resident_information_is_preserved(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_registration_service(
        repository
    )

    resident = make_valid_resident()

    result = service.register_resident(
        resident
    )

    stored_resident = (
        repository.find_by_id(
            result.resident.id
        )
    )

    assert stored_resident is not None

    assert (
        stored_resident.first_name
        == "Juan"
    )

    assert (
        stored_resident.last_name
        == "Dela Cruz"
    )

    assert (
        stored_resident.address
        == "Barangay Santo Tomas"
    )

    assert (
        stored_resident.contact_number
        == "09171234567"
    )

    assert (
        stored_resident.email
        == "juan@example.com"
    )

    assert (
        stored_resident.status
        == "Active"
    )

def test_registration_preserves_default_active_status(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_registration_service(
        repository
    )

    resident = make_valid_resident()

    assert resident.status == "Active"

    result = service.register_resident(
        resident
    )

    assert result.success is True

    assert result.resident is not None

    assert (
        result.resident.status
        == "Active"
    )

def test_invalid_resident_registration_fails(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_registration_service(
        repository
    )

    resident = (
        make_resident_with_missing_first_name()
    )

    result = service.register_resident(
        resident
    )

    assert result.success is False

    assert result.resident is None

    assert result.errors

def count_residents(
    database_path,
) -> int:
    with sqlite3.connect(
        database_path
    ) as connection:
        cursor = connection.execute(
            """
            SELECT COUNT(*)
            FROM residents
            """
        )

        row = cursor.fetchone()

        return int(
            row[0]
        )

def test_invalid_resident_is_not_persisted(
    tmp_path,
):
    database_path = (
        tmp_path / "residents.sqlite"
    )

    repository = ResidentRepository(
        str(database_path)
    )

    service = make_registration_service(
        repository
    )

    resident = (
        make_resident_with_missing_first_name()
    )

    count_before = count_residents(
        str(database_path)
    )

    result = service.register_resident(
        resident
    )

    count_after = count_residents(
        str(database_path)
    )

    assert result.success is False

    assert (
        count_after
        == count_before
    )

def test_registration_identifies_validation_failure(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_registration_service(
        repository
    )

    resident = (
        make_resident_with_missing_first_name()
    )

    result = service.register_resident(
        resident
    )

    assert result.success is False

    assert (
        "first_name"
        in result.errors
    )
 