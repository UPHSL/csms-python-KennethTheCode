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

    def find_all(self):
        """Lists all service requests ordered by date_requested DESC, id DESC."""
        return self.search_and_filter()

    def search_and_filter(self, search_term="", status_filter=None):
        """Persistence-level filtering with date_requested DESC, id DESC ordering."""
        sql = """
            SELECT
                id,
                resident_id,
                service_type,
                description,
                date_requested,
                status
            FROM service_requests
            WHERE 1=1
        """
        params = []

        if search_term and search_term.strip():
            clean_term = f"%{search_term.strip().lower()}%"
            sql += " AND (LOWER(service_type) LIKE ? OR LOWER(description) LIKE ?)"
            params.extend([clean_term, clean_term])

        if status_filter and status_filter.strip():
            sql += " AND status = ?"
            params.append(status_filter.strip())

        sql += " ORDER BY date_requested DESC, id DESC"

        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row

        try:
            rows = connection.execute(sql, params).fetchall()
        finally:
            connection.close()

        return [self._map_row_to_service_request(row) for row in rows]

    def count_all(self) -> int:
        """Count total persisted service requests at the database level."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM service_requests")
            return cursor.fetchone()[0]

    def count_by_status(self, status: str) -> int:
        """Count service requests matching a specific status at the database level."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM service_requests WHERE status = ?", (status,)
            )
            return cursor.fetchone()[0]

    def find_recent(self, limit: int = 5) -> list[ServiceRequest]:
        """Find the most recent service requests ordered by date_requested DESC, id DESC."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, resident_id, service_type, description, date_requested, status
                FROM service_requests
                ORDER BY date_requested DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            return [
                ServiceRequest(
                    id=row[0],
                    resident_id=row[1],
                    service_type=row[2],
                    description=row[3],
                    date_requested=row[4],
                    status=row[5],
                )
                for row in rows
            ]