import sqlite3

def initialize_database(db_path):
    connection = sqlite3.connect(db_path)
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
