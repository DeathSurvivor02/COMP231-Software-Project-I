
# ============================================================
# CLINICAL AI SUITE - APPOINTMENTS & SCHEDULING MODULE
# COMP231 - Software Development Project I (Group 1)
#
# Module Owner: Nick (Front Desk Developer)
# Subsystem: Front Desk Operations & Scheduling
# Covers:
#   - Appointment creation and validation
#   - Scheduling conflict detection (double-booking prevention)
#   - Rescheduling and cancellation workflows
#   - Receptionist "Today's Queue" generation
#   - MySQL database integration for persistent storage
#   - REST API endpoints serving JSON to the front desk UI
# ============================================================

from flask import Blueprint, jsonify, request
from datetime import datetime
import mysql.connector
#pip install mysql-connector-python
appointments_bp = Blueprint("appointments", __name__)

def get_db_connection():
    # Connect to your local MySQL Workbench
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="MySqlPoopybut@1234",
        database="scribeflow_db"
    )

@appointments_bp.route("/api/appointments", methods=["GET"])
def list_appointments():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM appointments')
    appts = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(appts)

@appointments_bp.route("/api/appointments", methods=["POST"])
def schedule_appointment():
    data = request.get_json(silent=True) or {}
    required = ("patient_name", "clinician", "datetime")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        dt = datetime.fromisoformat(data["datetime"])
    except (ValueError, TypeError):
        return jsonify({"error": "datetime must be ISO 8601 (YYYY-MM-DDTHH:MM)"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check for conflicts
    cursor.execute(
        'SELECT id FROM appointments WHERE clinician = %s AND datetime = %s AND status = "scheduled"',
        (data["clinician"], dt.strftime("%Y-%m-%d %H:%M:%S"))
    )
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "Clinician already booked at that time"}), 409

    # Insert new appointment
    cursor.execute(
        'INSERT INTO appointments (patient_name, clinician, datetime, reason, status) VALUES (%s, %s, %s, %s, %s)',
        (data["patient_name"], data["clinician"], dt.strftime("%Y-%m-%d %H:%M:%S"), data.get("reason", ""), "scheduled")
    )
    conn.commit()
    new_id = cursor.lastrowid

    cursor.execute('SELECT * FROM appointments WHERE id = %s', (new_id,))
    new_appt = cursor.fetchone()
    cursor.close()
    conn.close()

    return jsonify(new_appt), 201

@appointments_bp.route("/api/appointments/<int:appt_id>", methods=["PATCH"])
def reschedule_appointment(appt_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM appointments WHERE id = %s', (appt_id,))
    appt = cursor.fetchone()

    if not appt:
        cursor.close()
        conn.close()
        return jsonify({"error": "Appointment not found"}), 404
    if appt["status"] == "cancelled":
        cursor.close()
        conn.close()
        return jsonify({"error": "Cannot reschedule a cancelled appointment"}), 409

    data = request.get_json(silent=True) or {}
    new_dt = data.get("datetime")
    if not new_dt:
        cursor.close()
        conn.close()
        return jsonify({"error": "datetime is required"}), 400
    try:
        new_dt = datetime.fromisoformat(new_dt)
    except (ValueError, TypeError):
        cursor.close()
        conn.close()
        return jsonify({"error": "datetime must be ISO 8601"}), 400

    # Update the appointment
    cursor.execute(
        'UPDATE appointments SET datetime = %s, reason = %s WHERE id = %s',
        (new_dt.strftime("%Y-%m-%d %H:%M:%S"), data.get("reason", appt["reason"]), appt_id)
    )
    conn.commit()

    cursor.execute('SELECT * FROM appointments WHERE id = %s', (appt_id,))
    updated_appt = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(updated_appt)

@appointments_bp.route("/api/appointments/<int:appt_id>", methods=["DELETE"])
def cancel_appointment(appt_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM appointments WHERE id = %s', (appt_id,))
    appt = cursor.fetchone()

    if not appt:
        cursor.close()
        conn.close()
        return jsonify({"error": "Appointment not found"}), 404

    cursor.execute('UPDATE appointments SET status = "cancelled" WHERE id = %s', (appt_id,))
    conn.commit()

    cursor.execute('SELECT * FROM appointments WHERE id = %s', (appt_id,))
    updated_appt = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(updated_appt)

@appointments_bp.route("/api/appointments/queue", methods=["GET"])
def receptionist_queue():
    today = datetime.now().date()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get today's scheduled appointments ordered by time
    cursor.execute(
        'SELECT * FROM appointments WHERE status = "scheduled" AND DATE(datetime) = %s ORDER BY datetime',
        (today,)
    )
    queue = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(queue)