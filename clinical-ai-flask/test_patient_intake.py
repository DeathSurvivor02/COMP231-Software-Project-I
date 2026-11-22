# ============================================================
# CLINICAL AI SUITE - PATIENT INTAKE & DASHBOARD TESTS
# COMP231 - Software Development Project I (Group 1)
#
# Module Owner: Joel (Patient Experience Developer)
# Subsystem: Patient Experience & Intake Workflows
# Covers:
#   - Patient registration with demographic validation (DOB checks)
#   - Clinical intake records creation and linking
#   - Intake lifecycle state transitions (Pending -> In Progress -> Completed)
#   - Aggregate statistics calculation
#   - Dashboard rendering with patient queue and metric cards
#   - Form-based workflows and flash alerts
# ============================================================

from datetime import date, timedelta
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from app import app
import patient_intake


class TestPatientIntakeWorkflows(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

        # Reset patient intake in-memory state before each test
        patient_intake._patients.clear()
        patient_intake._patients.extend([
            {
                "patient_id": 1,
                "first_name": "Sarah",
                "last_name": "Jenkins",
                "date_of_birth": "1988-04-12",
                "sex": "Female",
                "phone": "(416) 555-0143",
                "email": "sarah.jenkins@example.com",
                "address": "120 Bremner Blvd, Toronto, ON",
                "emergency_contact_name": "Michael Jenkins (Spouse)",
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
                "emergency_contact_name": "Laura Miller (Sister)",
                "created_at": "2026-11-21 11:30:00",
            },
        ])
        patient_intake._next_patient_id[0] = 3

        patient_intake._intakes.clear()
        patient_intake._intakes.extend([
            {
                "intake_id": 1,
                "patient_id": 1,
                "patient_name": "Sarah Jenkins",
                "first_name": "Sarah",
                "last_name": "Jenkins",
                "date_of_birth": "1988-04-12",
                "phone": "(416) 555-0143",
                "email": "sarah.jenkins@example.com",
                "reason_for_visit": "Persistent cough",
                "symptoms": "Fever and fatigue",
                "allergies": "Penicillin",
                "medications": "Salbutamol",
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
                "reason_for_visit": "Annual health checkup",
                "symptoms": "None",
                "allergies": "None",
                "medications": "Multivitamins",
                "intake_status": "Pending",
                "intake_date": "2026-11-21 11:45:00",
                "updated_at": "2026-11-21 11:45:00",
            },
        ])
        patient_intake._next_intake_id[0] = 3

    def test_patient_dashboard_renders_intake_table_and_metrics(self):
        res = self.client.get("/patient-dashboard")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Patient Intake Records", html)
        self.assertIn("Sarah Jenkins", html)
        self.assertIn("David Miller", html)
        self.assertIn("Total Patients", html)

    def test_intake_form_page_renders(self):
        res = self.client.get("/patient-intake-form")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("New Patient Intake Registration", html)
        self.assertIn("Chief Complaint", html)

    def test_api_get_patients(self):
        res = self.client.get("/api/patients")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["patients"][0]["first_name"], "Sarah")

    def test_api_create_patient_success(self):
        payload = {
            "first_name": "Marcus",
            "last_name": "Vance",
            "date_of_birth": "1990-06-15",
            "sex": "Male",
            "phone": "(416) 555-8899",
            "email": "marcus.v@example.com",
            "address": "200 University Ave, Toronto",
            "emergency_contact_name": "Clara Vance - (416) 555-8800",
        }
        res = self.client.post("/api/patients", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["patient"]["patient_id"], 3)
        self.assertEqual(data["patient"]["first_name"], "Marcus")

    def test_api_create_patient_missing_required_fields(self):
        payload = {
            "first_name": "Incomplete",
        }
        res = self.client.post("/api/patients", json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("required", data["error"])

    def test_api_create_patient_future_dob_rejected(self):
        future_date = (date.today() + timedelta(days=10)).strftime("%Y-%m-%d")
        payload = {
            "first_name": "Time",
            "last_name": "Traveler",
            "date_of_birth": future_date,
        }
        res = self.client.post("/api/patients", json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("cannot be in the future", data["error"])

    def test_api_get_intakes_and_filtering(self):
        res = self.client.get("/api/intakes")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["count"], 2)

        # Filter by status
        res_pending = self.client.get("/api/intakes?status=Pending")
        self.assertEqual(res_pending.status_code, 200)
        pending_data = res_pending.get_json()
        self.assertEqual(pending_data["count"], 1)
        self.assertEqual(pending_data["intakes"][0]["patient_name"], "David Miller")

    def test_api_create_intake_success(self):
        payload = {
            "patient_id": 1,
            "reason_for_visit": "Follow up consultation on blood test results",
            "symptoms": "Mild dizziness in morning",
            "allergies": "Penicillin",
            "medications": "Salbutamol",
        }
        res = self.client.post("/api/intakes", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["intake"]["intake_status"], "Pending")
        self.assertEqual(data["intake"]["patient_name"], "Sarah Jenkins")

    def test_api_create_intake_invalid_patient(self):
        payload = {
            "patient_id": 9999,
            "reason_for_visit": "General checkup",
        }
        res = self.client.post("/api/intakes", json=payload)
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("does not exist", data["error"])

    def test_api_update_intake_status_valid(self):
        res = self.client.patch("/api/intakes/2/status", json={"status": "In Progress"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["intake"]["intake_status"], "In Progress")

        # Now update to Completed
        res2 = self.client.patch("/api/intakes/2/status", json={"status": "Completed"})
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertEqual(data2["intake"]["intake_status"], "Completed")

    def test_api_update_intake_status_invalid_value(self):
        res = self.client.patch("/api/intakes/2/status", json={"status": "NonExistentStatus"})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Invalid status", data["error"])

    def test_api_intake_stats(self):
        res = self.client.get("/api/intakes/stats")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        stats = data["statistics"]
        self.assertEqual(stats["total_patients"], 2)
        self.assertEqual(stats["total_intakes"], 2)
        self.assertEqual(stats["completed_intakes"], 1)
        self.assertEqual(stats["pending_intakes"], 1)
        self.assertEqual(stats["in_progress_intakes"], 0)

    def test_web_form_submission_creates_patient_and_intake(self):
        form_data = {
            "first_name": "Robert",
            "last_name": "Chen",
            "date_of_birth": "1992-03-21",
            "sex": "Male",
            "phone": "(416) 555-7766",
            "email": "robert.chen@example.com",
            "address": "77 Front St, Toronto",
            "emergency_contact": "Lily Chen - (416) 555-7700",
            "reason_for_visit": "Persistent headache and eye strain",
            "symptoms": "Throbbing headache past 3 days",
            "allergies": "None",
            "medications": "Ibuprofen 400mg",
        }
        res = self.client.post("/patient-intake-form", data=form_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("submitted successfully", html)
        self.assertIn("Robert Chen", html)

    def test_web_form_submission_future_dob_rejected(self):
        future_date = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
        form_data = {
            "first_name": "Future",
            "last_name": "Baby",
            "date_of_birth": future_date,
            "reason_for_visit": "Checkup",
        }
        res = self.client.post("/patient-intake-form", data=form_data, follow_redirects=True)
        self.assertEqual(res.status_code, 400)
        html = res.get_data(as_text=True)
        self.assertIn("Date of birth cannot be in the future", html)

    def test_web_form_update_status(self):
        res = self.client.post(
            "/patient-intake/2/status",
            data={"intake_status": "Completed"},
            follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("updated to Completed", html)


if __name__ == "__main__":
    unittest.main()
