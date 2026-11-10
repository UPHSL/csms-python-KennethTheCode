from dataclasses import dataclass

from csms.models.service_request import ServiceRequest
from csms.repositories.service_request_repository import (
    ServiceRequestRepository,
)

PENDING = "Pending"
IN_PROGRESS = "In Progress"
COMPLETED = "Completed"
CANCELLED = "Cancelled"

SUPPORTED_STATUSES = {
    PENDING,
    IN_PROGRESS,
    COMPLETED,
    CANCELLED,
}

# Each status maps to the statuses it is allowed to move to.
# Completed and Cancelled map to an empty set, so they are terminal.
# A status never lists itself, so a same-status request is not allowed.
ALLOWED_TRANSITIONS = {
    PENDING: {IN_PROGRESS, CANCELLED},
    IN_PROGRESS: {COMPLETED, CANCELLED},
    COMPLETED: set(),
    CANCELLED: set(),
}


@dataclass
class ServiceRequestStatusResult:
    success: bool
    service_request: ServiceRequest | None = None
    not_found: bool = False
    unsupported_status: bool = False
    invalid_transition: bool = False

    @classmethod
    def changed(
        cls, service_request: ServiceRequest
    ) -> "ServiceRequestStatusResult":
        return cls(success=True, service_request=service_request)

    @classmethod
    def for_missing_request(cls) -> "ServiceRequestStatusResult":
        return cls(success=False, not_found=True)

    @classmethod
    def for_unsupported_status(cls) -> "ServiceRequestStatusResult":
        return cls(success=False, unsupported_status=True)

    @classmethod
    def for_invalid_transition(cls) -> "ServiceRequestStatusResult":
        return cls(success=False, invalid_transition=True)


class ServiceRequestStatusService:
    def __init__(self, repository: ServiceRequestRepository) -> None:
        self.repository = repository

    def change_status(
        self,
        service_request_id: int,
        target_status: str,
    ) -> ServiceRequestStatusResult:
        existing = self.repository.find_by_id(service_request_id)

        if existing is None:
            return ServiceRequestStatusResult.for_missing_request()

        if not self._is_supported_status(target_status):
            return ServiceRequestStatusResult.for_unsupported_status()

        if not self._is_allowed_transition(existing.status, target_status):
            return ServiceRequestStatusResult.for_invalid_transition()

        if not self.repository.update_status(
            service_request_id, target_status
        ):
            return ServiceRequestStatusResult.for_missing_request()

        updated = self.repository.find_by_id(service_request_id)

        return ServiceRequestStatusResult.changed(updated)

    @staticmethod
    def _is_supported_status(status: object) -> bool:
        return isinstance(status, str) and status in SUPPORTED_STATUSES

    @staticmethod
    def _is_allowed_transition(current_status: str, target_status: str) -> bool:
        return target_status in ALLOWED_TRANSITIONS.get(current_status, set())