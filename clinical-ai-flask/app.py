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

from flask import Flask, render_template
from appointments import appointments_bp 
app = Flask(__name__)
app.register_blueprint(appointments_bp)


# ============================================================
# HOMEPAGE - INITIAL PROJECT SETUP
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


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
    return render_template("patient_dashboard.html")


# ============================================================
# FRONT DESK PORTAL - NICK
# Iteration 2: Front Desk Operations
# ============================================================

@app.route("/frontdesk-dashboard")
def frontdesk_dashboard():
    return render_template("frontdesk_dashboard.html")


# ============================================================
# ADMIN PORTAL - SIENNA
# Iteration 1: Role-Based Access Control
# ============================================================

@app.route("/admin-dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")


# ============================================================
# START FLASK APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)
