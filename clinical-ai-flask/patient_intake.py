# ============================================================
# CLINICAL AI SUITE - PATIENT DASHBOARD & INTAKE WORKFLOWS
# COMP231 - Software Development Project I (Group 1)
#
# Module Owner: Joel (Patient Experience Developer)
# Subsystem: Patient Experience & Intake Workflows
#
# Features:
#   - Patient demographic registration and validation
#   - Clinical pre-visit intake records management
#   - Intake status lifecycle (Pending -> In Progress -> Completed)
#   - Clinic intake metrics & statistics computation
#   - REST API endpoints and web UI views
# ============================================================

from datetime import datetime, date
from typing import Any, Dict, List, Optional
from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

patient_intake_bp = Blueprint("patient_intake", __name__)

# ============================================================
# IN-MEMORY DATA STORE (Zero-setup default with MySQL sync)
# ============================================================

_patients: List[Dict[str, Any]] = [
    {
        "patient_id": 1,
        "first_name": "Sarah",
        "last_name": "Jenkins",
        "date_of_birth": "1988-04-12",
        "sex": "Female",
        "phone": "(416) 555-0143",
        "email": "sarah.jenkins@example.com",
        "address": "120 Bremner Blvd, Toronto, ON",
        "emergency_contact_name": "Michael Jenkins (Spouse) - (416) 555-0199",
        "created_at": "2026-11-20 09:15:00",
    },
    {
        "patient_id": 2,
        "first_name": "David",
        "last_name": "Miller",
        "date_of_birth": "1975-09-23",
        "sex": "Male",
        "phone": "(416) 555-0284",
        "email": "david.miller@example.com",
        "address": "45 King St W, Toronto, ON",
        "emergency_contact_name": "Laura Miller (Sister) - (416) 555-0211",
        "created_at": "2026-11-21 11:30:00",
    },
    {
        "patient_id": 3,
        "first_name": "Elena",
        "last_name": "Rostova",
        "date_of_birth": "1994-01-15",
        "sex": "Female",
        "phone": "(647) 555-0371",
        "email": "elena.rostova@example.com",
        "address": "88 Queens Quay E, Toronto, ON",
        "emergency_contact_name": "Dmitri Rostov (Father) - (647) 555-0390",
        "created_at": "2026-11-22 08:45:00",
    },
]

_next_patient_id = [4]

_intakes: List[Dict[str, Any]] = [
    {
        "intake_id": 1,
        "patient_id": 1,
        "patient_name": "Sarah Jenkins",
        "first_name": "Sarah",
        "last_name": "Jenkins",
        "date_of_birth": "1988-04-12",
        "phone": "(416) 555-0143",
        "email": "sarah.jenkins@example.com",
        "reason_for_visit": "Persistent dry cough and mild chest tightness x 4 days",
        "symptoms": "Non-productive cough, low-grade fever, fatigue",
        "allergies": "Penicillin (rash)",
        "medications": "Salbutamol inhaler PRN",
        "intake_status": "Completed",
        "intake_date": "2026-11-20 09:30:00",
        "updated_at": "2026-11-20 10:15:00",
    },
    {
        "intake_id": 2,
        "patient_id": 2,
        "patient_name": "David Miller",
        "first_name": "David",
        "last_name": "Miller",
        "date_of_birth": "1975-09-23",
        "phone": "(416) 555-0284",
        "email": "david.miller@example.com",
        "reason_for_visit": "Hypertension routine follow-up and blood pressure check",
        "symptoms": "Occasional morning headaches, no dizziness",
        "allergies": "NKDA (No Known Drug Allergies)",
        "medications": "Amlodipine 5mg daily",
        "intake_status": "In Progress",
        "intake_date": "2026-11-21 11:45:00",
        "updated_at": "2026-11-21 12:00:00",
    },
    {
        "intake_id": 3,
        "patient_id": 3,
        "patient_name": "Elena Rostova",
        "first_name": "Elena",
        "last_name": "Rostova",
        "date_of_birth": "1994-01-15",
        "phone": "(647) 555-0371",
        "email": "elena.rostova@example.com",
        "reason_for_visit": "Right ankle inversion sprain sustained during soccer",
        "symptoms": "Localized lateral swelling, mild ecchymosis, weight bearing with limp",
        "allergies": "Sulfa drugs",
        "medications": "Ibuprofen 400mg PRN",
        "intake_status": "Pending",
        "intake_date": "2026-11-22 09:00:00",
        "updated_at": "2026-11-22 09:00:00",
    },
]

_next_intake_id = [4]

VALID_STATUSES = ("Pending", "In Progress", "Completed")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_statistics() -> Dict[str, int]:
    """Compute dashboard summary counts."""
    total_patients = len(_patients)
    total_intakes = len(_intakes)
    pending = sum(1 for i in _intakes if i["intake_status"] == "Pending")
    in_progress = sum(1 for i in _intakes if i["intake_status"] == "In Progress")
    completed = sum(1 for i in _intakes if i["intake_status"] == "Completed")
    return {
        "total_patients": total_patients,
        "total_intakes": total_intakes,
        "pending_intakes": pending,
        "in_progress_intakes": in_progress,
        "completed_intakes": completed,
    }


def find_patient_by_id(patient_id: int) -> Optional[Dict[str, Any]]:
    return next((p for p in _patients if p["patient_id"] == patient_id), None)


def find_intake_by_id(intake_id: int) -> Optional[Dict[str, Any]]:
    return next((i for i in _intakes if i["intake_id"] == intake_id), None)


# ============================================================
# REST API ENDPOINTS
# ============================================================

@patient_intake_bp.route("/api/patients", methods=["GET"])
def api_get_patients():
    """List all registered patients."""
    return jsonify({"success": True, "count": len(_patients), "patients": _patients}), 200


@patient_intake_bp.route("/api/patients", methods=["POST"])
def api_create_patient():
    """Register a new patient with demographic details."""
    data = request.get_json(silent=True) or {}
    first_name = str(data.get("first_name", "")).strip()
    last_name = str(data.get("last_name", "")).strip()
    dob_str = str(data.get("date_of_birth", "")).strip()

    if not first_name or not last_name or not dob_str:
        return jsonify({"success": False, "error": "first_name, last_name, and date_of_birth are required."}), 400

    try:
        parsed_dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        if parsed_dob > date.today():
            return jsonify({"success": False, "error": "Date of birth cannot be in the future."}), 400
    except ValueError:
        return jsonify({"success": False, "error": "date_of_birth must follow YYYY-MM-DD format."}), 400

    new_patient = {
        "patient_id": _next_patient_id[0],
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": dob_str,
        "sex": str(data.get("sex", "")).strip() or "Not Specified",
        "phone": str(data.get("phone", "")).strip(),
        "email": str(data.get("email", "")).strip(),
        "address": str(data.get("address", "")).strip(),
        "emergency_contact_name": str(data.get("emergency_contact_name", "")).strip(),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    _next_patient_id[0] += 1
    _patients.append(new_patient)
    return jsonify({"success": True, "patient": new_patient}), 201


@patient_intake_bp.route("/api/intakes", methods=["GET"])
def api_get_intakes():
    """List all intake records, optionally filtered by status."""
    status_filter = request.args.get("status")
    if status_filter:
        filtered = [i for i in _intakes if i["intake_status"].lower() == status_filter.lower()]
        return jsonify({"success": True, "count": len(filtered), "intakes": filtered}), 200
    return jsonify({"success": True, "count": len(_intakes), "intakes": _intakes}), 200


@patient_intake_bp.route("/api/intakes", methods=["POST"])
def api_create_intake():
    """Create a new patient intake record."""
    data = request.get_json(silent=True) or {}
    patient_id = data.get("patient_id")
    reason = str(data.get("reason_for_visit", "")).strip()

    if not patient_id or not reason:
        return jsonify({"success": False, "error": "patient_id and reason_for_visit are required."}), 400

    patient = find_patient_by_id(int(patient_id))
    if not patient:
        return jsonify({"success": False, "error": f"Patient with ID {patient_id} does not exist."}), 404

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_intake = {
        "intake_id": _next_intake_id[0],
        "patient_id": patient["patient_id"],
        "patient_name": f"{patient['first_name']} {patient['last_name']}",
        "first_name": patient["first_name"],
        "last_name": patient["last_name"],
        "date_of_birth": patient["date_of_birth"],
        "phone": patient.get("phone", ""),
        "email": patient.get("email", ""),
        "reason_for_visit": reason,
        "symptoms": str(data.get("symptoms", "")).strip(),
        "allergies": str(data.get("allergies", "")).strip(),
        "medications": str(data.get("medications", "")).strip(),
        "intake_status": "Pending",
        "intake_date": now_str,
        "updated_at": now_str,
    }
    _next_intake_id[0] += 1
    _intakes.append(new_intake)
    return jsonify({"success": True, "intake": new_intake}), 201


@patient_intake_bp.route("/api/intakes/<int:intake_id>/status", methods=["PATCH"])
def api_update_intake_status(intake_id: int):
    """Update status of a patient intake record."""
    data = request.get_json(silent=True) or {}
    new_status = str(data.get("status", "")).strip()

    if new_status not in VALID_STATUSES:
        return jsonify({"success": False, "error": f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"}), 400

    intake = find_intake_by_id(intake_id)
    if not intake:
        return jsonify({"success": False, "error": f"Intake record {intake_id} not found."}), 404

    intake["intake_status"] = new_status
    intake["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return jsonify({"success": True, "intake": intake}), 200


@patient_intake_bp.route("/api/intakes/stats", methods=["GET"])
def api_get_stats():
    """Return clinic-wide intake metrics."""
    return jsonify({"success": True, "statistics": get_statistics()}), 200


# ============================================================
# WEB UI VIEWS & FORM HANDLING
# ============================================================

@patient_intake_bp.route("/patient-intake-form", methods=["GET", "POST"])
def intake_form_page():
    """Render and process the comprehensive Patient Intake web form."""
    if request.method == "GET":
        return render_template("patient_intake.html")

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    dob_str = request.form.get("date_of_birth", "").strip()
    sex = request.form.get("sex", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    emergency_contact = request.form.get("emergency_contact", "").strip()

    reason = request.form.get("reason_for_visit", "").strip()
    symptoms = request.form.get("symptoms", "").strip()
    allergies = request.form.get("allergies", "").strip()
    medications = request.form.get("medications", "").strip()

    if not all([first_name, last_name, dob_str, reason]):
        flash("Please complete all required fields (marked with *).", "error")
        return render_template("patient_intake.html"), 400

    try:
        parsed_dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        if parsed_dob > date.today():
            flash("Date of birth cannot be in the future.", "error")
            return render_template("patient_intake.html"), 400
    except ValueError:
        flash("Please enter a valid date of birth (YYYY-MM-DD).", "error")
        return render_template("patient_intake.html"), 400

    # Create patient
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_patient = {
        "patient_id": _next_patient_id[0],
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": dob_str,
        "sex": sex or "Not Specified",
        "phone": phone,
        "email": email,
        "address": address,
        "emergency_contact_name": emergency_contact,
        "created_at": now_str,
    }
    _next_patient_id[0] += 1
    _patients.append(new_patient)

    # Create intake
    new_intake = {
        "intake_id": _next_intake_id[0],
        "patient_id": new_patient["patient_id"],
        "patient_name": f"{first_name} {last_name}",
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": dob_str,
        "phone": phone,
        "email": email,
        "reason_for_visit": reason,
        "symptoms": symptoms,
        "allergies": allergies,
        "medications": medications,
        "intake_status": "Pending",
        "intake_date": now_str,
        "updated_at": now_str,
    }
    _next_intake_id[0] += 1
    _intakes.append(new_intake)

    flash(f"Patient intake for {first_name} {last_name} submitted successfully!", "success")
    return redirect(url_for("patient_dashboard"))


@patient_intake_bp.route("/patient-intake/<int:intake_id>/status", methods=["POST"])
def update_intake_status_form(intake_id: int):
    """Update intake record status from the dashboard table."""
    new_status = request.form.get("intake_status", "").strip()
    if new_status not in VALID_STATUSES:
        flash("Invalid status selected.", "error")
        return redirect(url_for("patient_dashboard"))

    intake = find_intake_by_id(intake_id)
    if not intake:
        flash(f"Intake record #{intake_id} not found.", "error")
        return redirect(url_for("patient_dashboard"))

    intake["intake_status"] = new_status
    intake["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    flash(f"Status for intake #{intake_id} ({intake['patient_name']}) updated to {new_status}.", "success")
    return redirect(url_for("patient_dashboard"))
