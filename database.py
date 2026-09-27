import sqlite3

DB_NAME = "parking_system.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Parking Slots Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_slots (
            slot_id INTEGER PRIMARY KEY,
            slot_number TEXT UNIQUE NOT NULL,
            is_occupied INTEGER DEFAULT 0,
            vehicle_plate TEXT
        )
    """)

    # 2. Dynamic Pricing Tiers Table (Management can update rates without code changes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pricing_tiers (
            tier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            max_minutes INTEGER,
            rate REAL NOT NULL,
            description TEXT
        )
    """)

    # 3. Auditable Parking Records Table (Includes Payment Method, Net, and 16% VAT)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_plate TEXT NOT NULL,
            slot_number TEXT NOT NULL,
            entry_time DATETIME NOT NULL,
            exit_time DATETIME,
            duration_minutes REAL,
            net_amount REAL DEFAULT 0,
            vat_amount REAL DEFAULT 0,
            amount_paid REAL DEFAULT 0,
            payment_method TEXT CHECK(payment_method IN ('M-PESA', 'CARD', 'CASH', NULL)),
            status TEXT CHECK(status IN ('PARKED', 'PAID', 'EXITED')) DEFAULT 'PARKED'
        )
    """)

    # Seed 12 default slots (A1-A6, B1-B6) if table is empty
    cursor.execute("SELECT COUNT(*) FROM parking_slots")
    if cursor.fetchone()[0] == 0:
        default_slots = [
            (1, 'A1', 0, None), (2, 'A2', 0, None), (3, 'A3', 0, None),
            (4, 'A4', 0, None), (5, 'A5', 0, None), (6, 'A6', 0, None),
            (7, 'B1', 0, None), (8, 'B2', 0, None), (9, 'B3', 0, None),
            (10, 'B4', 0, None), (11, 'B5', 0, None), (12, 'B6', 0, None)
        ]
        cursor.executemany("INSERT INTO parking_slots VALUES (?, ?, ?, ?)", default_slots)

    # Seed default MMU pricing tiers if table is empty
    cursor.execute("SELECT COUNT(*) FROM pricing_tiers")
    if cursor.fetchone()[0] == 0:
        default_tiers = [
            (30, 0, "Up to 30 mins (Grace Period)"),
            (120, 50, "Up to 2 hours"),
            (240, 100, "Up to 4 hours"),
            (360, 300, "Up to 6 hours"),
            (999999, 500, "Above 6 hours (Flat Rate)")
        ]
        cursor.executemany("INSERT INTO pricing_tiers (max_minutes, rate, description) VALUES (?, ?, ?)", default_tiers)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database updated with pricing tiers and VAT audit fields successfully.")