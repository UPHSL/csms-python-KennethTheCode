VALID_SERVICE_REQUEST_STATUSES = {"Pending", "In Progress", "Completed", "Cancelled"}


class ServiceRequestQueryService:
    def __init__(self, repository):
        self.repository = repository

    def list_service_requests(self):
        """Retrieves all persisted Service Requests ordered by date_requested DESC, id DESC."""
        return self.repository.find_all()

    def view_service_request(self, service_request_id):
        """Retrieves a single Service Request by ID safely without throwing unhandled exceptions."""
        if service_request_id is None:
            return None
        return self.repository.find_by_id(service_request_id)

    def search_service_requests(self, search_term=None, status_filter=None):
        """Coordinates term normalization, status validation, and delegates query to persistence."""
        normalized_term = search_term.strip() if search_term else ""

        normalized_status = None
        if status_filter and status_filter.strip():
            clean_status = status_filter.strip()
            if clean_status not in VALID_SERVICE_REQUEST_STATUSES:
                raise ValueError(f"Unsupported status filter: {status_filter}")
            normalized_status = clean_status

        return self.repository.search_and_filter(
            search_term=normalized_term,
            status_filter=normalized_status,
        )