from dataclasses import dataclass, field

from csms.models.service_request import ServiceRequest


@dataclass
class ServiceRequestSubmissionResult:
    success: bool
    service_request: ServiceRequest | None = None
    errors: list[str] = field(default_factory=list)
    resident_not_found: bool = False
    resident_inactive: bool = False

    @classmethod
    def submitted(
        cls, service_request: ServiceRequest
    ) -> "ServiceRequestSubmissionResult":
        return cls(success=True, service_request=service_request)

    @classmethod
    def validation_failed(
        cls, errors: list[str]
    ) -> "ServiceRequestSubmissionResult":
        return cls(success=False, errors=list(errors))

    @classmethod
    def for_missing_resident(cls) -> "ServiceRequestSubmissionResult":
        return cls(success=False, resident_not_found=True)

    @classmethod
    def for_inactive_resident(cls) -> "ServiceRequestSubmissionResult":
        return cls(success=False, resident_inactive=True)