
# ============================================================
# CLINICAL AI SUITE - ADMIN AUTHENTICATION TEST APPLICATION
# COMP231 - Software Development Project I
#
# Purpose:
# Test login, logout, user roles, admin dashboard access,
# and patient record permissions.
#
# Uses synthetic accounts for local development only.
# ============================================================


# ============================================================
# 1. IMPORTS
# ============================================================

import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

from auth import (
    login_user,
    logout_user,
    role_required,
    hash_password,
    verify_password,
    can_access_patient_record,
    ROLE_ADMIN,
    ROLE_CLINICIAN,
    ROLE_PATIENT
)


# ============================================================
# 2. FLASK APPLICATION CONFIGURATION
# ============================================================

app = Flask(__name__)

# Local development only. Replace before deployment.
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "local-demo-only-replace-before-deployment"
)


# ============================================================
# 3. SYNTHETIC TEST USER ACCOUNTS
# ============================================================

demo_users = {

    "admin_demo": {
        "id": 1,
        "role": ROLE_ADMIN,
        "password_hash": hash_password("AdminDemo123!")
    },

    "clinician_demo": {
        "id": 2,
        "role": ROLE_CLINICIAN,
        "assigned_patient_ids": [3],
        "password_hash": hash_password("ClinicianDemo123!")
    },

    "patient_demo": {
        "id": 3,
        "role": ROLE_PATIENT,
        "password_hash": hash_password("PatientDemo123!")
    }

}


# ============================================================
# 4. SYNTHETIC PATIENT RECORDS
# ============================================================

demo_patient_records = {

    3: {
        "patient_id": 3,
        "patient_name": "Demo Patient",
        "record_type": "Synthetic demonstration record"
    }

}


# ============================================================
# 5. HOME ROUTE
# ============================================================

@app.route("/")
def home():
    """Redirect users to the login page."""

    return redirect(url_for("login"))


# ============================================================
# 6. LOGIN ROUTE
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate users and establish their sessions."""

    if request.method == "POST":

        # Retrieve submitted credentials
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Find the account
        user = demo_users.get(username)

        # Verify the password
        if user and verify_password(
            user["password_hash"], password
        ):

            # Create authenticated session
            login_user(user)

            # Redirect administrators
            if user["role"] == ROLE_ADMIN:
                return redirect(url_for("admin_dashboard"))

            # Other dashboards will be integrated later
            return (
                "Login successful. "
                "Your dashboard is not connected yet."
            )

        # Invalid credentials
        return render_template(
            "login.html",
            error="Invalid username or password."
        ), 401

    # Display login form
    return render_template("login.html")


# ============================================================
# 7. ADMIN DASHBOARD ROUTE
# ============================================================

@app.route("/admin")
@role_required(ROLE_ADMIN)
def admin_dashboard():
    """Display the admin dashboard to administrators only."""

    return render_template("admin_dashboard.html")


# ============================================================
# 8. PATIENT RECORD ACCESS ROUTE
# ============================================================

@app.route("/patients/<int:patient_id>")
def patient_record(patient_id):
    """
    Display a synthetic patient record only when the
    logged-in user has permission to access it.
    """

    # Step 1 - Check authentication
    user_id = session.get("user_id")

    if user_id is None:
        return jsonify({
            "error": "Authentication required"
        }), 401

    # Step 2 - Retrieve trusted user information
    user = next(
        (
            account
            for account in demo_users.values()
            if account["id"] == user_id
        ),
        None
    )

    if user is None:
        return jsonify({
            "error": "Authentication required"
        }), 401

    # Step 3 - Check patient record permissions
    if not can_access_patient_record(user, patient_id):
        return jsonify({
            "error": "Access denied",
            "message": "You do not have permission."
        }), 403

    # Step 4 - Retrieve synthetic patient record
    record = demo_patient_records.get(patient_id)

    if record is None:
        return jsonify({
            "error": "Patient record not found"
        }), 404

    # Step 5 - Return authorized record
    return jsonify(record), 200


# ============================================================
# 9. LOGOUT ROUTE
# ============================================================

@app.route("/logout", methods=["POST"])
def logout():
    """Clear the current user session."""

    logout_user()

    return redirect(url_for("login"))


# ============================================================
# 10. START FLASK APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)
