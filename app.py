from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from datetime import datetime
from parking_logic import SlotAllocator

app = Flask(__name__)
DB_NAME = "parking_system.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Fetch visual parking bays
    cursor.execute("SELECT * FROM parking_slots ORDER BY slot_id ASC")
    slots = cursor.fetchall()
    
    # 2. Fetch active parked vehicles
    cursor.execute("SELECT * FROM parking_records WHERE status = 'PARKED' ORDER BY entry_time DESC")
    active_vehicles = cursor.fetchall()

    # 3. Entrance Display Totals (Live slot availability count)
    total_slots = len(slots)
    occupied_slots = sum(1 for s in slots if s["is_occupied"] == 1)
    available_slots = total_slots - occupied_slots

    # 4. Configurable Rate Tiers
    cursor.execute("SELECT * FROM pricing_tiers ORDER BY max_minutes ASC")
    tiers = cursor.fetchall()

    # 5. Auditable Financial Reconciliation (Gross, VAT, Net, Payment methods)
    cursor.execute("""
        SELECT 
            COUNT(*) as total_transactions,
            COALESCE(SUM(amount_paid), 0) as total_gross,
            COALESCE(SUM(vat_amount), 0) as total_vat,
            COALESCE(SUM(net_amount), 0) as total_net
        FROM parking_records 
        WHERE status = 'EXITED'
    """)
    finance_summary = cursor.fetchone()

    # Audit transaction trail
    cursor.execute("""
        SELECT vehicle_plate, slot_number, entry_time, exit_time, duration_minutes,
               net_amount, vat_amount, amount_paid, payment_method
        FROM parking_records
        WHERE status = 'EXITED'
        ORDER BY exit_time DESC
        LIMIT 10
    """)
    recent_transactions = cursor.fetchall()

    conn.close()
    return render_template(
        "index.html",
        slots=slots,
        active_vehicles=active_vehicles,
        total_slots=total_slots,
        available_slots=available_slots,
        occupied_slots=occupied_slots,
        tiers=tiers,
        finance=finance_summary,
        transactions=recent_transactions
    )

@app.route("/api/entry", methods=["POST"])
def vehicle_entry():
    data = request.json or {}
    plate = data.get("plate", "").strip().upper()
    if not plate:
        return jsonify({"success": False, "message": "Vehicle plate number required."}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Prevent duplicate entry if vehicle is already parked
    cursor.execute("SELECT id FROM parking_records WHERE vehicle_plate = ? AND status = 'PARKED'", (plate,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "message": f"Vehicle {plate} is already inside."}), 400

    # Linear search for first vacant slot
    cursor.execute("SELECT * FROM parking_slots WHERE is_occupied = 0 ORDER BY slot_id ASC LIMIT 1")
    free_slot = cursor.fetchone()

    if not free_slot:
        conn.close()
        return jsonify({"success": False, "message": "Parking Lot is Full! Entry barrier locked."}), 400

    assigned_slot = free_slot["slot_number"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("UPDATE parking_slots SET is_occupied = 1, vehicle_plate = ? WHERE slot_number = ?", (plate, assigned_slot))
    cursor.execute("""
        INSERT INTO parking_records (vehicle_plate, slot_number, entry_time, status)
        VALUES (?, ?, ?, 'PARKED')
    """, (plate, assigned_slot, now))

    conn.commit()
    conn.close()
    return jsonify({
        "success": True,
        "message": f"Welcome {plate}! Bay {assigned_slot} allocated. Barrier OPEN.",
        "slot": assigned_slot
    })

@app.route("/api/calculate_exit", methods=["POST"])
def calculate_exit():
    data = request.json or {}
    plate = data.get("plate", "").strip().upper()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parking_records WHERE vehicle_plate = ? AND status = 'PARKED'", (plate,))
    record = cursor.fetchone()

    if not record:
        conn.close()
        return jsonify({"success": False, "message": "No active vehicle found with that plate."}), 404

    entry_time = datetime.strptime(record["entry_time"], "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    duration_mins = max((now - entry_time).total_seconds() / 60.0, 1.0)

    # Dynamic pricing & statutory VAT calculation
    breakdown = SlotAllocator.calculate_fee_and_vat(duration_mins)

    conn.close()
    return jsonify({
        "success": True,
        "plate": plate,
        "slot": record["slot_number"],
        "entry_time": record["entry_time"],
        "exit_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_mins": round(duration_mins, 2),
        "gross_amount": breakdown["gross_amount"],
        "net_amount": breakdown["net_amount"],
        "vat_amount": breakdown["vat_amount"]
    })

@app.route("/api/confirm_exit", methods=["POST"])
def confirm_exit():
    data = request.json or {}
    plate = data.get("plate", "").strip().upper()
    payment_method = data.get("payment_method", "M-PESA")
    gross_amount = float(data.get("gross_amount", 0))
    net_amount = float(data.get("net_amount", 0))
    vat_amount = float(data.get("vat_amount", 0))

    if payment_method not in ["M-PESA", "CARD", "CASH"]:
        return jsonify({"success": False, "message": "Invalid payment method selected."}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parking_records WHERE vehicle_plate = ? AND status = 'PARKED'", (plate,))
    record = cursor.fetchone()

    if not record:
        conn.close()
        return jsonify({"success": False, "message": "Active record not found."}), 404

    slot_number = record["slot_number"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry_time = datetime.strptime(record["entry_time"], "%Y-%m-%d %H:%M:%S")
    duration_mins = round(max((datetime.now() - entry_time).total_seconds() / 60.0, 1.0), 2)

    # 1. Free the slot back to available state
    cursor.execute("UPDATE parking_slots SET is_occupied = 0, vehicle_plate = NULL WHERE slot_number = ?", (slot_number,))

    # 2. Persist auditable payment record
    cursor.execute("""
        UPDATE parking_records 
        SET exit_time = ?, duration_minutes = ?, net_amount = ?, vat_amount = ?, 
            amount_paid = ?, payment_method = ?, status = 'EXITED'
        WHERE id = ?
    """, (now, duration_mins, net_amount, vat_amount, gross_amount, payment_method, record["id"]))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"Payment of Kshs. {gross_amount:.2f} via {payment_method} verified! Exit Barrier OPEN."
    })

@app.route("/api/update_rate", methods=["POST"])
def update_rate():
    """Allows management to update pricing tiers without software changes."""
    data = request.json or {}
    tier_id = data.get("tier_id")
    new_rate = data.get("rate")

    try:
        new_rate = float(new_rate)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid rate value."}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE pricing_tiers SET rate = ? WHERE tier_id = ?", (new_rate, tier_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Pricing tier updated successfully."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)