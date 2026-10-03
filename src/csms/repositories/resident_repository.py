import sqlite3

from csms.models.resident import Resident


class ResidentRepository:
    def __init__(self, db_path):
        self.db_path = db_path
        self.initialize()

    def initialize(self):
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS residents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                address TEXT NOT NULL,
                contact_number TEXT NOT NULL,
                email TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )

        connection.commit()
        connection.close()

    def save(self, resident):
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO residents
                (first_name, last_name, address, contact_number, email, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (resident.first_name, resident.last_name, resident.address, resident.contact_number, resident.email, resident.status)
        )

        connection.commit()

        resident.id = cursor.lastrowid
        connection.close()

        return resident

    def find_by_id(self, resident_id):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, first_name, last_name, address, contact_number, email, status
            FROM residents
            WHERE id = ?
            """,
            (resident_id,)
        )

        row = cursor.fetchone()
        connection.close()

        if row is None:
            return None

        return Resident(
            id=row["id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            address=row["address"],
            contact_number=row["contact_number"],
            email=row["email"],
            status=row["status"],
        )

    def find_all(
        self,
    ) -> list[Resident]:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                first_name,
                last_name,
                address,
                contact_number,
                email,
                status
            FROM residents
            ORDER BY
                LOWER(last_name) ASC,
                LOWER(first_name) ASC,
                id ASC
            """
        )

        rows = cursor.fetchall()
        connection.close()

        return [
            Resident(
                id=row["id"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                address=row["address"],
                contact_number=row["contact_number"],
                email=row["email"],
                status=row["status"],
            )
            for row in rows
        ]        

    def search_by_name(
            self,
            search_term: str,
        ) -> list[Resident]:
            sql = """
                SELECT
                    id,
                    first_name,
                    last_name,
                    address,
                    contact_number,
                    email,
                    status
                FROM residents
                WHERE
                    LOWER(first_name) LIKE LOWER(?)
                    OR LOWER(last_name) LIKE LOWER(?)
                ORDER BY
                    LOWER(last_name) ASC,
                    LOWER(first_name) ASC,
                    id ASC
            """

            pattern = f"%{search_term}%"

            with sqlite3.connect(
                self.db_path
            ) as connection:
                connection.row_factory = sqlite3.Row

                rows = connection.execute(
                    sql,
                    (
                        pattern,
                        pattern,
                    ),
                ).fetchall()

            return [
                self._map_row_to_resident(row)
                for row in rows
            ]
    
    def _map_row_to_resident(
        self,
        row: sqlite3.Row,
    ) -> Resident:
        return Resident(
            id=row["id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            address=row["address"],
            contact_number=row["contact_number"],
            email=row["email"],
            status=row["status"],
        )
    
    def update(self, resident):
        connection = sqlite3.connect(self.db_path)

        try:
            cursor = connection.execute(
                """
                UPDATE residents
                SET
                    first_name = ?,
                    last_name = ?,
                    address = ?,
                    contact_number = ?,
                    email = ?
                WHERE id = ?
                """,
                (
                    resident.first_name,
                    resident.last_name,
                    resident.address,
                    resident.contact_number,
                    resident.email,
                    resident.id,
                ),
            )

            connection.commit()
            updated_rows = cursor.rowcount
        finally:
            connection.close()

        return updated_rows == 1

    def deactivate_by_id(self, resident_id):
        connection = sqlite3.connect(self.db_path)

        try:
            cursor = connection.execute(
                """
                UPDATE residents
                SET status = ?
                WHERE id = ?
                """,
                ("Inactive", resident_id),
            )

            connection.commit()
            updated_rows = cursor.rowcount
        finally:
            connection.close()

        return updated_rows == 1