
# ============================================================
# SCRIBEFLOW - FLASK AUTHENTICATION ROUTE TESTS
# COMP231 - Software Development Project I
#
# Uses synthetic accounts and Flask's built-in test client.
# ============================================================

import unittest

from test_admin import app


class TestAuthenticationRoutes(unittest.TestCase):

    def setUp(self):
        """Create a fresh test client for each test."""
        app.config["TESTING"] = True
        self.client = app.test_client()

    def login(self, username, password):
        """Submit demonstration login credentials."""
        return self.client.post("/login", data={
            "username": username,
            "password": password
        })

    def test_admin_can_access_dashboard(self):
        self.login("admin_demo", "AdminDemo123!")

        response = self.client.get("/admin")

        self.assertEqual(response.status_code, 200)

    def test_patient_cannot_access_admin(self):
        self.login("patient_demo", "PatientDemo123!")

        response = self.client.get("/admin")

        self.assertEqual(response.status_code, 403)

    def test_clinician_cannot_access_admin(self):
        self.login("clinician_demo", "ClinicianDemo123!")

        response = self.client.get("/admin")

        self.assertEqual(response.status_code, 403)

    def test_patient_can_access_own_record(self):
        self.login("patient_demo", "PatientDemo123!")

        response = self.client.get("/patients/3")

        self.assertEqual(response.status_code, 200)

    def test_patient_cannot_access_other_record(self):
        self.login("patient_demo", "PatientDemo123!")

        response = self.client.get("/patients/4")

        self.assertEqual(response.status_code, 403)

    def test_logout_removes_access(self):
        self.login("admin_demo", "AdminDemo123!")

        self.client.post("/logout")

        response = self.client.get("/admin")

        self.assertEqual(response.status_code, 302)


if __name__ == "__main__":
    unittest.main(verbosity=2)
