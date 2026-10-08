import sqlite3
from datetime import date

from csms.models.service_request import ServiceRequest


class ServiceRequestRepository:
    def __init__(self, db_path):
        self.db_path = db_path
        self.initialize()

    def initialize(self):
        connection = sqlite3.connect(self.db_path)

        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS service_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resident_id INTEGER NOT NULL,
                    service_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    date_requested TEXT NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )
            connection.commit()
        finally:
            connection.close()

    def save(self, service_request):
        connection = sqlite3.connect(self.db_path)

        try:
            cursor = connection.execute(
                """
                INSERT INTO service_requests
                    (resident_id, service_type, description,
                     date_requested, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    service_request.resident_id,
                    service_request.service_type,
                    service_request.description,
                    service_request.date_requested.isoformat(),
                    service_request.status,
                ),
            )
            connection.commit()
            service_request.id = cursor.lastrowid
        finally:
            connection.close()

        return service_request

    def find_by_id(self, service_request_id):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row

        try:
            row = connection.execute(
                """
                SELECT
                    id,
                    resident_id,
                    service_type,
                    description,
                    date_requested,
                    status
                FROM service_requests
                WHERE id = ?
                """,
                (service_request_id,),
            ).fetchone()
        finally:
            connection.close()

        if row is None:
            return None

        return self._map_row_to_service_request(row)

    def _map_row_to_service_request(self, row):
        return ServiceRequest(
            id=row["id"],
            resident_id=row["resident_id"],
            service_type=row["service_type"],
            description=row["description"],
            date_requested=date.fromisoformat(row["date_requested"]),
            status=row["status"],
        )

    def update_status(self, service_request_id, status):
        connection = sqlite3.connect(self.db_path)

        try:
            cursor = connection.execute(
                """
                UPDATE service_requests
                SET status = ?
                WHERE id = ?
                """,
                (status, service_request_id),
            )

            connection.commit()
            updated_rows = cursor.rowcount
        finally:
            connection.close()

        return updated_rows == 1