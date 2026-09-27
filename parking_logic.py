import sqlite3

DB_NAME = "parking_system.db"

class SlotAllocator:
    """
    DSA Logic for MMU Parking System:
    - Array/Grid representation for slots
    - Dynamic tier rate lookup from database (Management configurable)
    - Automated VAT computation (16% statutory rate)
    """
    def __init__(self, total_slots=12):
        self.total_slots = total_slots

    @staticmethod
    def calculate_fee_and_vat(minutes: float) -> dict:
        """
        Dynamically fetches pricing tiers from SQLite database.
        Calculates:
          - Gross Amount Payable
          - 16% VAT portion for compliance and auditing
          - Net Parking Revenue
        """
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Pull sorted active rate tiers
        cursor.execute("SELECT max_minutes, rate FROM pricing_tiers ORDER BY max_minutes ASC")
        tiers = cursor.fetchall()
        conn.close()

        # Find applicable tier using linear search
        gross_rate = 500.0  # Fallback default if beyond max tier
        for max_mins, rate in tiers:
            if minutes <= max_mins:
                gross_rate = float(rate)
                break

        # Compute statutory 16% VAT breakdown: Net = Gross / 1.16, VAT = Gross - Net
        if gross_rate > 0:
            net_amount = round(gross_rate / 1.16, 2)
            vat_amount = round(gross_rate - net_amount, 2)
        else:
            net_amount = 0.0
            vat_amount = 0.0

        return {
            "gross_amount": gross_rate,
            "net_amount": net_amount,
            "vat_amount": vat_amount
        }