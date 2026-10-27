from datetime import date, datetime

from csms.models.service_request import ServiceRequest


class ServiceRequestValidator:
    def validate(self, service_request: ServiceRequest) -> list[str]:
        errors = []

        if service_request.id is not None:
            errors.append("id")

        if not self._is_valid_resident_id(service_request.resident_id):
            errors.append("resident_id")

        if self._is_blank(service_request.service_type):
            errors.append("service_type")

        if self._is_blank(service_request.description):
            errors.append("description")

        if not self._is_valid_date(service_request.date_requested):
            errors.append("date_requested")

        if service_request.status != "Pending":
            errors.append("status")

        return errors

    def is_valid(self, service_request: ServiceRequest) -> bool:
        return len(self.validate(service_request)) == 0

    @staticmethod
    def _is_valid_resident_id(value: object) -> bool:
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
            and value > 0
        )

    @staticmethod
    def _is_blank(value: object) -> bool:
        return not isinstance(value, str) or not value.strip()

    @staticmethod
    def _is_valid_date(value: object) -> bool:
        return isinstance(value, date) and not isinstance(value, datetime)