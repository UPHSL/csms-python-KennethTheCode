import pytest

from csms.database import initialize_database
from csms.repositories.resident_repository import ResidentRepository
from csms.models.resident import Resident


@pytest.fixture
def repository(tmp_path):
    db_path = tmp_path / "something.db"
    initialize_database(db_path)
    return ResidentRepository(db_path)


def make_valid_resident():
    return Resident(
        first_name="Juan",
        last_name="Dela Cruz",
        address="Barangay Santo Tomas",
        contact_number="09171234567",
        email="juan@example.com",
        status="Active",       
    )

def test_save_resident(repository):
    resident = make_valid_resident()

    saved_resident = repository.save(resident)

    assert saved_resident.id is not None

def test_resident_id_is_set_after_save(repository):
    resident = make_valid_resident()

    assert resident.id is None         

    repository.save(resident)

    assert resident.id is not None          

def test_find_by_id_finds_saved_resident(repository):
    resident = make_valid_resident()
    repository.save(resident)

    found_resident = repository.find_by_id(resident.id)

    assert found_resident is not None
    assert found_resident.id == resident.id

def test_find_by_id_returns_correct_resident_data(repository):
    resident = make_valid_resident()
    repository.save(resident)

    found_resident = repository.find_by_id(resident.id)

    assert found_resident.first_name == resident.first_name
    assert found_resident.last_name == resident.last_name
    assert found_resident.address == resident.address
    assert found_resident.contact_number == resident.contact_number
    assert found_resident.email == resident.email
    assert found_resident.status == resident.status

def test_find_by_id_returns_correct_resident_status(repository):
    resident = make_valid_resident()
    repository.save(resident)

    found_resident = repository.find_by_id(resident.id)

    assert found_resident.status == "Active"

def test_find_by_id_returns_none_for_nonexistent_id(repository):
    found_resident = repository.find_by_id(999)

    assert found_resident is None

def test_find_by_id_works_across_multiple_repository_instances(tmp_path):
    db_path = tmp_path / "test.db"
    initialize_database(db_path)

    first_repository = ResidentRepository(db_path)
    resident = make_valid_resident()
    first_repository.save(resident)

    second_repository = ResidentRepository(db_path)
    found_resident = second_repository.find_by_id(resident.id)

    assert found_resident is not None
    assert found_resident.id == resident.id
    assert found_resident.first_name == resident.first_name

def test_find_by_id_returns_correct_resident_data_for_multiple_residents(repository):
    resident_one = make_valid_resident()
    resident_two = Resident(
        first_name="Maria",
        last_name="Dela Cruz",
        address="Barangay San Isidro",
        contact_number="09177654321",
        email="maria@example.com",
        status="Active",
    )

    repository.save(resident_one)
    repository.save(resident_two)

    assert resident_one.id != resident_two.id