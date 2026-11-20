from functools import wraps
from flask import session, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

# User roles for the Clinical AI Suite
ROLE_ADMIN = "admin"
ROLE_CLINICIAN = "clinician"
ROLE_PATIENT = "patient"

VALID_ROLES = {
    ROLE_ADMIN,
    ROLE_CLINICIAN,
    ROLE_PATIENT
}

def login_user(user):
    """Store authenticated user information in the session."""

    session.clear()
    session["user_id"] = user["id"]
    session["role"] = user["role"]
    
def logout_user():
    """Remove the current user's session information."""
    session.clear()
    
def login_required(function):
    """Allow access only to logged-in users."""

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper

def role_required(*allowed_roles):
    """Restrict access to users with permitted roles."""

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):

            if "user_id" not in session:
                return redirect(url_for("login"))

            user_role = session.get("role")

            if user_role not in allowed_roles:
                return jsonify({
                    "error": "Access denied",
                    "message": "You do not have permission."
                }), 403

            return function(*args, **kwargs)

        return wrapper

    return decorator

def hash_password(password):
    """Generate a secure hash for a password."""
    return generate_password_hash(password)


def verify_password(stored_hash, entered_password):
    """Verify a password against its stored hash."""
    return check_password_hash(stored_hash, entered_password)


# ============================================================
# PATIENT RECORD ACCESS CONTROL
# ============================================================

def can_access_patient_record(user, patient_id):
    """
    Check whether a user is allowed to access a patient record.

    Patients: Their own records only.
    Clinicians: Records explicitly assigned to them.
    Administrators: No automatic clinical record access.
    """

    if not user:
        return False

    role = user.get("role")

    if role not in VALID_ROLES:
        return False

    if role == ROLE_PATIENT:
        return str(user.get("id")) == str(patient_id)

    if role == ROLE_CLINICIAN:
        assigned_patients = user.get("assigned_patient_ids", [])
        return str(patient_id) in {
            str(assigned_id) for assigned_id in assigned_patients
        }

    return False
