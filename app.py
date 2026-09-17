from flask import Flask, render_template, request, jsonify
import sqlite3
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
    cursor.execute("SELECT * FROM parking_slots ORDER BY slot_id ASC")
    slots = cursor.fetchall()
    
    cursor.execute("SELECT * FROM parking_records WHERE status = 'PARKED' ORDER BY entry_time DESC")
    active_vehicles = cursor.fetchall()
    conn.close()
    return render_template("index.html", slots=slots, active_vehicles=active_vehicles)

@app.route("/api/entry", methods=["POST"])
def vehicle_entry():
    data = request.json or {}
    plate = data.get("plate", "").strip().upper()
    if not plate:
        return jsonify({"success": False, "message": "Vehicle plate number required."}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Linear search / first-fit allocation for first available slot
    cursor.execute("SELECT * FROM parking_slots WHERE is_occupied = 0 ORDER BY slot_id ASC LIMIT 1")
    free_slot = cursor.fetchone()

    if not free_slot:
        conn.close()
        return jsonify({"success": False, "message": "Parking Lot is Full! Entry barrier closed."}), 400

    assigned_slot = free_slot["slot_number"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Update slot and insert entry record
    cursor.execute("UPDATE parking_slots SET is_occupied = 1, vehicle_plate = ? WHERE slot_number = ?", (plate, assigned_slot))
    cursor.execute("""
        INSERT INTO parking_records (vehicle_plate, slot_number, entry_time, status)
        VALUES (?, ?, ?, 'PARKED')
    """, (plate, assigned_slot, now))

    conn.commit()
    conn.close()
    return jsonify({
        "success": True, 
        "message": f"Welcome {plate}! Slot {assigned_slot} allocated. Barrier OPEN.",
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
    fee = SlotAllocator.calculate_fee(duration_mins)

    conn.close()
    return jsonify({
        "success": True,
        "plate": plate,
        "slot": record["slot_number"],
        "entry_time": record["entry_time"],
        "exit_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_mins": round(duration_mins, 2),
        "amount": fee
    })

@app.route("/api/confirm_exit", methods=["POST"])
def confirm_exit():
    data = request.json or {}
    plate = data.get("plate", "").strip().upper()
    amount = data.get("amount", 0)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parking_records WHERE vehicle_plate = ? AND status = 'PARKED'", (plate,))
    record = cursor.fetchone()

    if not record:
        conn.close()
        return jsonify({"success": False, "message": "Record not found."}), 404

    slot_number = record["slot_number"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Release slot back to available pool
    cursor.execute("UPDATE parking_slots SET is_occupied = 0, vehicle_plate = NULL WHERE slot_number = ?", (slot_number,))
    cursor.execute("""
        UPDATE parking_records 
        SET exit_time = ?, amount_paid = ?, status = 'EXITED'
        WHERE id = ?
    """, (now, amount, record["id"]))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Payment of Kshs. {amount} confirmed! Barrier OPEN. Safe journey!"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)