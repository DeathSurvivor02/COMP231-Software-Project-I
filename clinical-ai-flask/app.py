# ============================================================
# CLINICAL AI SUITE
# COMP231 - Software Development Project I
# Centennial College - Group 1
# ============================================================
#
# PROJECT TEAM
#
# Haris Maleji - Agile Customer
#   Planning, requirements, priorities and acceptance testing
#
# Ean - Clinical Documentation Developer
#   Consultation transcripts, SOAP drafting, clinician approval
#
# Sienna - Security and Administration Developer
#   Authentication, RBAC, user permissions and security testing
#
# Joel - Patient Experience Developer
#   Patient interface, intake workflow and intake summaries
#
# Tanzeef - Conversational Intake Developer
#   Chatbot questions, response handling and validation
#
# Nick - Front Desk Developer
#   Appointments, scheduling and receptionist workflows
#
# ============================================================
# INITIAL FLASK PROJECT SETUP - HARIS MALEJI
# Application initialization and route scaffolding
# These routes are placeholders, not completed modules.
# ============================================================


import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for
)

from appointments import appointments_bp
from clinical_docs import clinical_docs_bp
from intake_bot import intake_bot_bp
from patient_intake import patient_intake_bp, get_statistics, _intakes

# SIENNA - Authentication and Role-Based Access Control
from auth import (
    login_user,
    logout_user,
    role_required,
    hash_password,
    verify_password,
    ROLE_ADMIN,
    ROLE_CLINICIAN,
    ROLE_PATIENT
)


app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "local-demo-only-replace-before-deployment",
)
app.register_blueprint(appointments_bp)
app.register_blueprint(clinical_docs_bp)
app.register_blueprint(intake_bot_bp)
app.register_blueprint(patient_intake_bp)


# ============================================================
# SIENNA - SYNTHETIC AUTHENTICATION ACCOUNTS
# Local testing only - no real users or patient information
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
# HOMEPAGE - INITIAL PROJECT SETUP
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# SIENNA - LOGIN AND LOGOUT
# Iteration 1: Authentication
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = demo_users.get(username)

        if user and verify_password(user["password_hash"], password):

            login_user(user)

            if user["role"] == ROLE_ADMIN:
                return redirect(url_for("admin_dashboard"))

            if user["role"] == ROLE_CLINICIAN:
                return redirect(url_for("clinician_dashboard"))

            if user["role"] == ROLE_PATIENT:
                return redirect(url_for("patient_dashboard"))

        return render_template(
            "login.html",
            error="Invalid username or password."
        ), 401

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():

    logout_user()

    return redirect(url_for("login"))



# ============================================================
# CLINICIAN PORTAL - EAN
# Iteration 1: Clinical Documentation
# ============================================================

@app.route("/clinician-dashboard")
def clinician_dashboard():
    return render_template("clinician_dashboard.html")


# ============================================================
# PATIENT PORTAL - JOEL AND TANZEEF
# Iteration 1: Conversational Patient Intake
# ============================================================

@app.route("/patient-dashboard")
def patient_dashboard():
    return render_template(
        "patient_dashboard.html",
        statistics=get_statistics(),
        intakes=_intakes,
    )


# ============================================================
# FRONT DESK PORTAL - NICK
# Iteration 2: Front Desk Operations
# ============================================================

@app.route("/frontdesk-dashboard")
def frontdesk_dashboard():
    return render_template("frontdesk_dashboard.html")


# ============================================================
# SIENNA - ADMIN DASHBOARD
# Iteration 1: Role-Based Access Control
# ============================================================

@app.route("/admin-dashboard")
@app.route("/admin")
@role_required(ROLE_ADMIN)
def admin_dashboard():

    return render_template("admin_dashboard.html")



# ============================================================
# START FLASK APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)
