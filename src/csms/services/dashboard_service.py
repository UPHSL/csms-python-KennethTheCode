"""Dashboard query service for operational summary reporting."""

from csms.repositories.resident_repository import ResidentRepository
from csms.repositories.service_request_repository import ServiceRequestRepository


class DashboardService:
    """Coordinates dashboard operational metrics using persistence-level aggregate queries."""

    def __init__(
        self,
        resident_repository: ResidentRepository,
        service_request_repository: ServiceRequestRepository,
    ):
        self.resident_repository = resident_repository
        self.service_request_repository = service_request_repository

    def get_dashboard_summary(self) -> dict:
        """Fetch aggregate metrics and top 5 recent service requests."""
        # Resident Counts
        total_residents = self.resident_repository.count_all()
        active_residents = self.resident_repository.count_by_status("Active")
        inactive_residents = self.resident_repository.count_by_status("Inactive")

        # Service Request Counts
        total_requests = self.service_request_repository.count_all()
        pending_requests = self.service_request_repository.count_by_status("Pending")
        in_progress_requests = self.service_request_repository.count_by_status(
            "In Progress"
        )
        completed_requests = self.service_request_repository.count_by_status(
            "Completed"
        )
        cancelled_requests = self.service_request_repository.count_by_status(
            "Cancelled"
        )

        # Derived Metric: Open = Pending + In Progress
        open_requests = pending_requests + in_progress_requests

        # Recent Service Requests (Max 5)
        recent_requests = self.service_request_repository.find_recent(limit=5)

        return {
            "residents": {
                "total": total_residents,
                "active": active_residents,
                "inactive": inactive_residents,
            },
            "service_requests": {
                "total": total_requests,
                "open": open_requests,
                "pending": pending_requests,
                "in_progress": in_progress_requests,
                "completed": completed_requests,
                "cancelled": cancelled_requests,
            },
            "recent_service_requests": recent_requests,
        }