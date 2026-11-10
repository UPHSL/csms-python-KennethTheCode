from csms.repositories.resident_repository import ResidentRepository
from csms.services.resident_deactivation_result import (
    ResidentDeactivationResult,
)


class ResidentDeactivationService:
    def __init__(self, repository: ResidentRepository) -> None:
        self.repository = repository

    def deactivate_resident(
        self,
        resident_id: int,
    ) -> ResidentDeactivationResult:
        existing = self.repository.find_by_id(resident_id)

        if existing is None:
            return ResidentDeactivationResult.resident_not_found()

        if existing.status == "Inactive":
            return ResidentDeactivationResult.was_already_inactive(existing)

        if not self.repository.deactivate_by_id(resident_id):
            return ResidentDeactivationResult.resident_not_found()

        updated = self.repository.find_by_id(resident_id)

        return ResidentDeactivationResult.deactivated(updated)