import sqlite3

from csms.models.resident import Resident


class ResidentRepository:
    def __init__(self, db_path):
        self.db_path = db_path

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

    