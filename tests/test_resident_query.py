from csms.models.resident import Resident
from csms.repositories.resident_repository import (
    ResidentRepository,
)
from csms.services.resident_query_service import (
    ResidentQueryService,
)

def make_repository(
    tmp_path,
) -> ResidentRepository:
    database_path = (
        tmp_path / "t05-residents.sqlite"
    )

    return ResidentRepository(
        str(database_path)
    )

def make_query_service(
    repository: ResidentRepository,
) -> ResidentQueryService:
    return ResidentQueryService(
        repository
    )

def make_resident(
    first_name: str,
    last_name: str,
    contact_number: str,
    email: str,
    status: str = "Active",
) -> Resident:
    resident = Resident(
        first_name=first_name,
        last_name=last_name,
        address="Barangay Santo Tomas",
        contact_number=contact_number,
        email=email,
    )

    if status != "Active":
        resident.status = status

    return resident

 
def save_resident(
    repository: ResidentRepository,
    resident: Resident,
) -> Resident:
    repository.save(
        resident
    )

    return resident

def test_lists_all_persisted_residents(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_query_service(
        repository
    )

    save_resident(
        repository,
        make_resident(
            "Juan",
            "Cruz",
            "09171234561",
            "juan@example.com",
        ),
    )

    save_resident(
        repository,
        make_resident(
            "Maria",
            "Santos",
            "09171234562",
            "maria@example.com",
        ),
    )

    save_resident(
        repository,
        make_resident(
            "Ana",
            "Reyes",
            "09171234563",
            "ana@example.com",
        ),
    )

    residents = (
        service.list_residents()
    )

    assert len(residents) == 3

def test_empty_listing_returns_empty_list(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_query_service(
        repository
    )

    residents = (
        service.list_residents()
    )

    assert residents is not None

    assert residents == []

def test_listing_uses_required_ordering(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_query_service(
        repository
    )

    save_resident(
        repository,
        make_resident(
            "Ana",
            "Santos",
            "09171234561",
            "ana.santos@example.com",
        ),
    )

    save_resident(
        repository,
        make_resident(
            "Pedro",
            "Cruz",
            "09171234562",
            "pedro.cruz@example.com",
        ),
    )

    save_resident(
        repository,
        make_resident(
            "Maria",
            "Andres",
            "09171234563",
            "maria.andres@example.com",
        ),
    )

    save_resident(
        repository,
        make_resident(
            "Juan",
            "Cruz",
            "09171234564",
            "juan.cruz@example.com",
        ),
    )

    residents = (
        service.list_residents()
    )

    names = [
        (
            resident.last_name,
            resident.first_name,
        )
        for resident in residents
    ]

    assert names == [
        ("Andres", "Maria"),
        ("Cruz", "Juan"),
        ("Cruz", "Pedro"),
        ("Santos", "Ana"),
    ]

def test_searches_partial_first_name_case_insensitively(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_query_service(
        repository
    )

    save_resident(
        repository,
        make_resident(
            "Juan",
            "Dela Cruz",
            "09171234561",
            "juan@example.com",
        ),
    )

    save_resident(
        repository,
        make_resident(
            "Maria",
            "Santos",
            "09171234562",
            "maria@example.com",
        ),
    )

    results = service.search_residents(
        "jUa"
    )

    assert len(results) == 1

    assert (
        results[0].first_name
        == "Juan"
    )

def test_searches_partial_last_name_case_insensitively(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_query_service(
        repository
    )

    save_resident(
        repository,
        make_resident(
            "Juan",
            "Dela Cruz",
            "09171234561",
            "juan@example.com",
        ),
    )

    save_resident(
        repository,
        make_resident(
            "Maria",
            "Santos",
            "09171234562",
            "maria@example.com",
        ),
    )

    results = service.search_residents(
        "cRuZ"
    )

    assert len(results) == 1

    assert (
        results[0].last_name
        == "Dela Cruz"
    )

def test_blank_search_returns_all_residents(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_query_service(
        repository
    )

    save_resident(
        repository,
        make_resident(
            "Juan",
            "Cruz",
            "09171234561",
            "juan@example.com",
        ),
    )

    save_resident(
        repository,
        make_resident(
            "Maria",
            "Santos",
            "09171234562",
            "maria@example.com",
        ),
    )

    listed = service.list_residents()

    searched = service.search_residents(
        "      "
    )

    assert len(searched) == len(
        listed
    )

    assert [
        resident.id
        for resident in searched
    ] == [
        resident.id
        for resident in listed
    ]

def test_search_with_no_match_returns_empty_list(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_query_service(
        repository
    )

    save_resident(
        repository,
        make_resident(
            "Juan",
            "Cruz",
            "09171234561",
            "juan@example.com",
        ),
    )

    results = service.search_residents(
        "ZzzUnknownResident"
    )

    assert results is not None

    assert results == []

def test_search_result_preserves_resident_information(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_query_service(
        repository
    )

    saved = save_resident(
        repository,
        make_resident(
            "Juan",
            "Dela Cruz",
            "09171234567",
            "juan@example.com",
        ),
    )

    results = service.search_residents(
        "Juan"
    )

    assert len(results) == 1

    resident = results[0]

    assert resident.id == saved.id

    assert (
        resident.first_name
        == "Juan"
    )

    assert (
        resident.last_name
        == "Dela Cruz"
    )

    assert (
        resident.address
        == "Barangay Santo Tomas"
    )

    assert (
        resident.contact_number
        == "09171234567"
    )

    assert (
        resident.email
        == "juan@example.com"
    )

    assert (
        resident.status
        == "Active"
    )

def test_listing_includes_active_and_inactive_residents(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_query_service(
        repository
    )

    save_resident(
        repository,
        make_resident(
            "Juan",
            "Cruz",
            "09171234561",
            "juan@example.com",
        ),
    )

    save_resident(
        repository,
        make_resident(
            "Maria",
            "Santos",
            "09171234562",
            "maria@example.com",
            status="Inactive",
        ),
    )

    residents = (
        service.list_residents()
    )

    statuses = {
        resident.status
        for resident in residents
    }

    assert "Active" in statuses

    assert "Inactive" in statuses

def test_matching_resident_appears_only_once(
    tmp_path,
):
    repository = make_repository(
        tmp_path
    )

    service = make_query_service(
        repository
    )

    saved = save_resident(
        repository,
        make_resident(
            "Ana",
            "Anaya",
            "09171234561",
            "ana@example.com",
        ),
    )

    results = service.search_residents(
        "ana"
    )

    assert len(results) == 1

    assert results[0].id == saved.id