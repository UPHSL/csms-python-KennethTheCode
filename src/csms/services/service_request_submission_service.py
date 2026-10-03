from csms.models.service_request import ServiceRequest
from csms.repositories.resident_repository import ResidentRepository
from csms.repositories.service_request_repository import (
    ServiceRequestRepository,
)
from csms.services.service_request_submission_result import (
    ServiceRequestSubmissionResult,
)
from csms.services.service_request_validator import (
    ServiceRequestValidator,
)


class ServiceRequestSubmissionService:
    def __init__(
        self,
        validator: ServiceRequestValidator,
        resident_repository: ResidentRepository,
        service_request_repository: ServiceRequestRepository,
    ) -> None:
        self.validator = validator
        self.resident_repository = resident_repository
        self.service_request_repository = service_request_repository

    def submit_service_request(
        self,
        service_request: ServiceRequest,
    ) -> ServiceRequestSubmissionResult:
        errors = self.validator.validate(service_request)

        if errors:
            return ServiceRequestSubmissionResult.validation_failed(errors)

        resident = self.resident_repository.find_by_id(
            service_request.resident_id
        )

        if resident is None:
            return ServiceRequestSubmissionResult.for_missing_resident()

        if resident.status != "Active":
            return ServiceRequestSubmissionResult.for_inactive_resident()

        saved = self.service_request_repository.save(service_request)

        return ServiceRequestSubmissionResult.submitted(saved)