# ============================================================
# CLINICAL AI SUITE - CONVERSATIONAL INTAKE & RECEPTIONIST TESTS
# COMP231 - Software Development Project I (Group 1)
#
# Module Owner: Tanzeef Ahamed (@TanzeefAhamed)
# Covers:
#   - Story 1.4: Guided intake, missing/unexpected input validation,
#     medical advice guardrail, and summary generation
#   - Story 4: AI Receptionist FAQs and booking/reschedule/cancel
#     synced with Nick's appointments blueprint
# ============================================================

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

import appointments as appointments_store
import intake_bot
from app import app


class TestIntakeAndReceptionistBot(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        intake_bot._sessions.clear()
        intake_bot._intake_records.clear()
        intake_bot._next_intake_id[0] = 1
        appointments_store._appointments.clear()
        appointments_store._next_id[0] = 1

    def test_patient_dashboard_renders(self):
        res = self.client.get("/patient-dashboard")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Patient Portal", html)
        self.assertIn("Pre-Visit Intake", html)
        self.assertIn("AI Receptionist", html)

    def test_guided_intake_full_flow_and_summary(self):
        sid = "test-intake-full"

        r1 = self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "intake", "message": "Sarah Jenkins"
        }).get_json()
        self.assertTrue(r1["valid"])
        self.assertEqual(r1["intake_summary"]["current_step"], "chief_complaint")

        r2 = self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "intake", "message": "Dry cough and sore throat"
        }).get_json()
        self.assertTrue(r2["valid"])
        self.assertEqual(r2["intake_summary"]["current_step"], "duration_severity")

        r3 = self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "intake", "message": "Since Tuesday, mild (4/10)"
        }).get_json()
        self.assertTrue(r3["valid"])
        self.assertEqual(r3["intake_summary"]["current_step"], "associated_symptoms")

        r4 = self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "intake", "message": "none"
        }).get_json()
        self.assertTrue(r4["valid"])
        self.assertEqual(r4["intake_summary"]["current_step"], "medical_history")

        r5 = self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "intake",
            "message": "Previously diagnosed with mild asthma, uses prescription inhaler"
        }).get_json()
        self.assertTrue(r5["valid"])
        self.assertFalse(r5["guardrail_triggered"])
        self.assertTrue(r5["intake_summary"]["is_complete"])
        self.assertEqual(r5["intake_summary"]["status"], "Ready for Clinician Review")

        intakes = self.client.get("/api/bot/intakes").get_json()
        self.assertEqual(len(intakes), 1)
        self.assertEqual(intakes[0]["patient_name"], "Sarah Jenkins")
        self.assertEqual(intakes[0]["chief_complaint"], "Dry cough and sore throat")

    def test_missing_and_unexpected_inputs_do_not_advance_step(self):
        sid = "test-validation"

        # Blank input on name
        blank_res = self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "intake", "message": "   "
        }).get_json()
        self.assertFalse(blank_res["valid"])
        self.assertEqual(blank_res["intake_summary"]["current_step"], "patient_name")

        # Digits in name
        num_res = self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "intake", "message": "12345"
        }).get_json()
        self.assertFalse(num_res["valid"])
        self.assertEqual(num_res["intake_summary"]["current_step"], "patient_name")

        # Valid name advances to chief_complaint
        self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "intake", "message": "Alex Morgan"
        })

        # Vague/gibberish symptom fails
        vague_res = self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "intake", "message": "idk"
        }).get_json()
        self.assertFalse(vague_res["valid"])
        self.assertEqual(vague_res["intake_summary"]["current_step"], "chief_complaint")

        # Valid symptom advances to duration_severity
        self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "intake", "message": "Persistent headache"
        })

        # Missing timeframe and severity fails
        no_dur_res = self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "intake", "message": "feeling unwell"
        }).get_json()
        self.assertFalse(no_dur_res["valid"])
        self.assertEqual(no_dur_res["intake_summary"]["current_step"], "duration_severity")

    def test_medical_advice_guardrail_blocks_diagnosis_and_prescriptions(self):
        sid = "test-guardrail"
        self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "intake", "message": "Jordan Lee"
        })

        for unsafe_prompt in (
            "What medicine should I take?",
            "Can you prescribe antibiotics for me?",
            "Diagnose me, do I have pneumonia?",
        ):
            res = self.client.post("/api/bot/message", json={
                "session_id": sid, "mode": "intake", "message": unsafe_prompt
            }).get_json()
            self.assertTrue(res["guardrail_triggered"])
            self.assertFalse(res["valid"])
            self.assertIn("cannot diagnose", res["reply"].lower())
            self.assertEqual(res["intake_summary"]["current_step"], "chief_complaint")

    def test_receptionist_faqs_and_conversational_scheduling_sync(self):
        sid = "test-receptionist"

        mode_res = self.client.post("/api/bot/mode", json={
            "session_id": sid, "mode": "receptionist"
        })
        self.assertEqual(mode_res.status_code, 200)

        hours_res = self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "receptionist", "message": "What are your clinic hours?"
        }).get_json()
        self.assertIn("monday to friday", hours_res["reply"].lower())

        loc_res = self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "receptionist", "message": "Where are you located?"
        }).get_json()
        self.assertIn("120 progress ave", loc_res["reply"].lower())

        # Guided booking flow via chat
        b1 = self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "receptionist", "message": "Book an appointment"
        }).get_json()
        self.assertIn("full name", b1["reply"].lower())

        self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "receptionist", "message": "Sarah Jenkins"
        })
        self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "receptionist", "message": "Dr. Chen"
        })
        self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "receptionist", "message": "2026-12-01T10:00"
        })
        confirm = self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "receptionist", "message": "Dry cough checkup"
        }).get_json()
        self.assertIn("booking confirmed", confirm["reply"].lower())
        self.assertIsNotNone(confirm["last_receipt"])
        self.assertEqual(confirm["last_receipt"]["clinician"], "Dr. Chen")

        # Verify appointment is synced in Nick's /api/appointments store
        appts = self.client.get("/api/appointments").get_json()
        self.assertEqual(len(appts), 1)
        self.assertEqual(appts[0]["patient_name"], "Sarah Jenkins")
        self.assertEqual(appts[0]["status"], "scheduled")

        # Conflict check via quick-book endpoint
        conflict_res = self.client.post("/api/bot/book", json={
            "session_id": sid,
            "patient_name": "Alex Morgan",
            "clinician": "Dr. Chen",
            "datetime": "2026-12-01T10:00",
        })
        self.assertEqual(conflict_res.status_code, 409)

        # Reschedule via chat
        resched = self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "receptionist",
            "message": "reschedule #1 to 2026-12-02T14:30"
        }).get_json()
        self.assertIn("rescheduled", resched["reply"].lower())
        appts_after_resched = self.client.get("/api/appointments").get_json()
        self.assertEqual(appts_after_resched[0]["datetime"], "2026-12-02T14:30")

        # Cancel via chat
        cancel = self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "receptionist",
            "message": "cancel #1"
        }).get_json()
        self.assertIn("cancelled", cancel["reply"].lower())
        appts_after_cancel = self.client.get("/api/appointments").get_json()
        self.assertEqual(appts_after_cancel[0]["status"], "cancelled")

    def test_reset_clears_conversation_state(self):
        sid = "test-reset"
        self.client.post("/api/bot/message", json={
            "session_id": sid, "mode": "intake", "message": "John Doe"
        })
        reset_res = self.client.post("/api/bot/reset", json={
            "session_id": sid, "mode": "intake"
        }).get_json()
        self.assertEqual(reset_res["intake_summary"]["current_step"], "patient_name")
        self.assertEqual(reset_res["intake_summary"]["patient_name"], "Pending")


if __name__ == "__main__":
    unittest.main(verbosity=2)
