from datetime import datetime
from flask import Blueprint, jsonify, request

appointments_bp = Blueprint("appointments", __name__)

# In-memory store — replace with a DB in a later iteration
_appointments = []
_next_id = [1]

VALID_STATUSES = {"scheduled", "cancelled"}


def _find(appt_id):
    return next((a for a in _appointments if a["id"] == appt_id), None)


@appointments_bp.route("/api/appointments", methods=["GET"])
def list_appointments():
    return jsonify(_appointments)


@appointments_bp.route("/api/appointments", methods=["POST"])
def schedule_appointment():
    data = request.get_json(silent=True) or {}
    required = ("patient_name", "clinician", "datetime")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        dt = datetime.fromisoformat(data["datetime"])
    except ValueError:
        return jsonify({"error": "datetime must be ISO 8601 (YYYY-MM-DDTHH:MM)"}), 400

    # conflict check: same clinician, same time, not cancelled
    for a in _appointments:
        if (a["clinician"] == data["clinician"]
                and a["datetime"] == dt.isoformat()
                and a["status"] == "scheduled"):
            return jsonify({"error": "Clinician already booked at that time"}), 409

    appt = {
        "id": _next_id[0],
        "patient_name": data["patient_name"],
        "clinician": data["clinician"],
        "datetime": dt.isoformat(),
        "reason": data.get("reason", ""),
        "status": "scheduled",
    }
    _next_id[0] += 1
    _appointments.append(appt)
    return jsonify(appt), 201


@appointments_bp.route("/api/appointments/<int:appt_id>", methods=["PATCH"])
def reschedule_appointment(appt_id):
    appt = _find(appt_id)
    if not appt:
        return jsonify({"error": "Appointment not found"}), 404
    if appt["status"] == "cancelled":
        return jsonify({"error": "Cannot reschedule a cancelled appointment"}), 409

    data = request.get_json(silent=True) or {}
    new_dt = data.get("datetime")
    if not new_dt:
        return jsonify({"error": "datetime is required"}), 400
    try:
        datetime.fromisoformat(new_dt)
    except ValueError:
        return jsonify({"error": "datetime must be ISO 8601"}), 400

    appt["datetime"] = new_dt
    if "reason" in data:
        appt["reason"] = data["reason"]
    return jsonify(appt)


@appointments_bp.route("/api/appointments/<int:appt_id>", methods=["DELETE"])
def cancel_appointment(appt_id):
    appt = _find(appt_id)
    if not appt:
        return jsonify({"error": "Appointment not found"}), 404
    appt["status"] = "cancelled"
    return jsonify(appt)


@appointments_bp.route("/api/appointments/queue", methods=["GET"])
def receptionist_queue():
    """Today's scheduled appointments, ordered by time."""
    today = datetime.now().date().isoformat()
    queue = sorted(
        (a for a in _appointments
         if a["status"] == "scheduled" and a["datetime"].startswith(today)),
        key=lambda a: a["datetime"],
    )
    return jsonify(queue)