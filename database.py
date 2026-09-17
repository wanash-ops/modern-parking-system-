import sqlite3

DB_NAME = "parking_system.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Dynamic table for parking slots
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_slots (
            slot_id INTEGER PRIMARY KEY,
            slot_number TEXT UNIQUE NOT NULL,
            is_occupied INTEGER DEFAULT 0,
            vehicle_plate TEXT
        )
    """)

    # Dynamic transaction log table for records
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_plate TEXT NOT NULL,
            slot_number TEXT NOT NULL,
            entry_time DATETIME NOT NULL,
            exit_time DATETIME,
            duration_minutes REAL,
            amount_paid REAL,
            status TEXT CHECK(status IN ('PARKED', 'PAID', 'EXITED')) DEFAULT 'PARKED'
        )
    """)

    # Seed 12 default slots (A1-A6, B1-B6) if empty
    cursor.execute("SELECT COUNT(*) FROM parking_slots")
    if cursor.fetchone()[0] == 0:
        default_slots = [
            (1, 'A1', 0, None), (2, 'A2', 0, None), (3, 'A3', 0, None),
            (4, 'A4', 0, None), (5, 'A5', 0, None), (6, 'A6', 0, None),
            (7, 'B1', 0, None), (8, 'B2', 0, None), (9, 'B3', 0, None),
            (10, 'B4', 0, None), (11, 'B5', 0, None), (12, 'B6', 0, None)
        ]
        cursor.executemany("INSERT INTO parking_slots VALUES (?, ?, ?, ?)", default_slots)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")