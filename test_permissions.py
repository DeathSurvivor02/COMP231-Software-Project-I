
# ============================================================
# SCRIBEFLOW - PATIENT RECORD PERMISSION TESTS
# COMP231 - Synthetic test users only
# ============================================================

import unittest

from auth import (
    can_access_patient_record,
    ROLE_ADMIN,
    ROLE_CLINICIAN,
    ROLE_PATIENT
)


class TestPatientPermissions(unittest.TestCase):

    def setUp(self):
        """Create fictional users for each test."""

        self.patient = {
            "id": 3,
            "role": ROLE_PATIENT
        }

        self.clinician = {
            "id": 2,
            "role": ROLE_CLINICIAN,
            "assigned_patient_ids": [3, 5]
        }

        self.admin = {
            "id": 1,
            "role": ROLE_ADMIN
        }

    def test_patient_own_record(self):
        """Patients can access their own records."""
        self.assertTrue(
            can_access_patient_record(self.patient, 3)
        )

    def test_patient_other_record(self):
        """Patients cannot access another patient's records."""
        self.assertFalse(
            can_access_patient_record(self.patient, 4)
        )

    def test_clinician_assigned_record(self):
        """Clinicians can access assigned patient records."""
        self.assertTrue(
            can_access_patient_record(self.clinician, 5)
        )

    def test_clinician_unassigned_record(self):
        """Clinicians cannot access unassigned records."""
        self.assertFalse(
            can_access_patient_record(self.clinician, 6)
        )

    def test_admin_clinical_record(self):
        """Administrators have no automatic clinical access."""
        self.assertFalse(
            can_access_patient_record(self.admin, 3)
        )

    def test_unauthenticated_user(self):
        """Unknown users cannot access patient records."""
        self.assertFalse(
            can_access_patient_record(None, 3)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
