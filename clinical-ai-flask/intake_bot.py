# ============================================================
# CLINICAL AI SUITE - CONVERSATIONAL INTAKE & RECEPTIONIST BOT
# COMP231 - Software Development Project I (Group 1)
#
# Module Owner: Tanzeef Ahamed (@TanzeefAhamed)
# Responsibilities:
#   - Iteration 1 (Story 1.4): Guided symptom & medical history
#     intake questions, response handling, input validation, and
#     strict medical governance (no diagnosis/prescriptions).
#   - Iteration 2 (Story 4): Automated AI Receptionist bot for
#     clinic FAQs and conversational appointment booking,
#     rescheduling, and cancellation integrated with appointments.py.
# ============================================================

from datetime import datetime, timedelta
import re
from uuid import uuid4
from flask import Blueprint, jsonify, request, session

import appointments as appointments_store

intake_bot_bp = Blueprint("intake_bot", __name__)

# In-memory store for bot sessions and finalized clinical intake summaries
_sessions = {}
_intake_records = []
_next_intake_id = [1]

INTAKE_STEPS = [
    "patient_name",
    "chief_complaint",
    "duration_severity",
    "associated_symptoms",
    "medical_history",
    "completed",
]

INTAKE_PROMPTS = {
    "patient_name": (
        "Hello! I'm the Clinical AI Intake Assistant. I'll ask a few quick "
        "questions to prepare a summary for your clinician before your visit. "
        "First, what is your full name?"
    ),
    "chief_complaint": (
        "Thank you, {patient_name}. What main symptoms or health concerns are "
        "bringing you in for your visit today?"
    ),
    "duration_severity": (
        "Got it. How long have you been experiencing these symptoms, and how "
        "severe do they feel (for example, mild/moderate/severe or 1-10)?"
    ),
    "associated_symptoms": (
        "Thank you. Are you noticing any additional symptoms such as fever, "
        "chills, chest pain, or shortness of breath? (You can say 'none' if not.)"
    ),
    "medical_history": (
        "Almost done! Do you have any relevant past medical history, current "
        "medications, or allergies we should note for the clinician? "
        "(Say 'none' if none apply.)"
    ),
}

CLINIC_CLINICIANS = [
    {"name": "Dr. Chen", "specialty": "General Physician"},
    {"name": "Dr. Patel", "specialty": "Cardiology"},
    {"name": "Dr. Rivera", "specialty": "Neurology"},
]

CLINIC_FAQS = {
    "hours": (
        "Our clinic is open Monday to Friday from 8:00 AM to 6:00 PM, and "
        "Saturday from 9:00 AM to 2:00 PM. We are closed on Sundays."
    ),
    "location": (
        "We are located at 120 Progress Ave, Suite 200, Scarborough, ON "
        "(Centennial Health Campus). Free patient parking is available in Lot B."
    ),
    "doctors": (
        "Our available clinicians are Dr. Chen (General Physician), "
        "Dr. Patel (Cardiology), and Dr. Rivera (Neurology)."
    ),
    "policy": (
        "Please arrive 10 minutes before your scheduled appointment with a "
        "photo ID and health card. You may reschedule or cancel free of charge "
        "at least 24 hours in advance."
    ),
    "privacy": (
        "This Clinical AI Suite prototype runs strictly on synthetic test data "
        "with role-based access control. AI-generated summaries are always "
        "reviewed by an authorized clinician."
    ),
}

MEDICAL_ADVICE_PATTERNS = [
    r"\b(diagnose\s+me|can\s+you\s+diagnose|please\s+diagnose|give\s+(me\s+)?a\s+diagnosis|what\s+is\s+(my|the|your)\s+diagnosis)\b",
    r"\bwhat\s+(disease|illness|condition|infection)\b",
    r"\bwhat('s|\s+is)\s+wrong\s+with\s+me\b",
    r"\bdo\s+i\s+have\b",
    r"\bcould\s+(it|this)\s+be\b",
    r"\bis\s+(this|it)\s+(covid|flu|asthma|pneumonia|bronchitis|cancer|serious)\b",
    r"\b(can\s+you\s+prescribe|please\s+prescribe|prescribe\s+(me|something|anything|med|antibiotic)|write\s+(me\s+)?a\s+prescription|need\s+a\s+prescription|give\s+(me\s+)?a\s+prescription)\b",
    r"\bwhat\s+(medicine|medication|meds|drug|pill|antibiotic)s?\b",
    r"\bshould\s+i\s+take\b",
    r"\bcan\s+i\s+take\b",
    r"\bwhat\s+dosage\b",
    r"\bgive\s+me\s+antibiotic(s)?\b",
    r"\bmedical\s+advice\b",
    r"\bwhat\s+treatment\b",
    r"\btriage\s+me\b",
]

DURATION_OR_SEVERITY_HINTS = re.compile(
    r"(\b\d+\s*(hour|hr|hrs|day|days|week|weeks|wk|wks|month|months|mo|year|years|yr|yrs)\b"
    r"|\b(today|yesterday|tonight|morning|evening|monday|tuesday|wednesday|thursday|friday|saturday|sunday|since|ago|week|days|hours)\b"
    r"|\b(mild|moderate|severe|light|slight|medium|intense|extreme|manageable|bearable|worsening|improving)\b"
    r"|\b([1-9]|10)\s*/\s*10\b"
    r"|\b([1-9]|10)\s*(out\s+of\s+10)\b"
    r"|\b(severity|level|scale)\s*[:\-]?\s*([1-9]|10)\b)",
    re.IGNORECASE,
)

VAGUE_NON_ANSWERS = {
    "hi", "hello", "hey", "ok", "okay", "yes", "yeah", "yep",
    "idk", "dunno", "not sure", "unsure", "maybe", "stuff",
    "things", "bad", "sick", "pain", "hurt", "hurts", "test",
    "asdf", "qwerty", "lol", "help", "?", "??", "???",
}

NONE_EQUIVALENTS = {
    "no", "none", "nope", "nothing", "n/a", "na", "nil",
    "no other symptoms", "no additional symptoms",
    "no allergies", "no medications", "no history", "none apply",
}


def _now_label():
    return datetime.now().strftime("%I:%M %p").lstrip("0")


def _new_session_state():
    return {
        "mode": "intake",
        "intake_step": "patient_name",
        "intake_data": {
            "patient_name": "",
            "chief_complaint": "",
            "duration_severity": "",
            "associated_symptoms": "",
            "medical_history": "",
        },
        "intake_submitted": False,
        "intake_record_id": None,
        "booking_draft": {
            "active": False,
            "step": None,
            "patient_name": "",
            "clinician": "",
            "datetime": "",
            "reason": "",
        },
        "last_receipt": None,
        "messages": [
            {
                "sender": "bot",
                "mode": "intake",
                "text": INTAKE_PROMPTS["patient_name"],
                "timestamp": _now_label(),
                "tag": "Guided Intake",
            }
        ],
    }


def _get_session_id(data=None):
    if data and data.get("session_id"):
        return str(data["session_id"])
    arg_sid = request.args.get("session_id")
    if arg_sid:
        return str(arg_sid)
    try:
        if "bot_session_id" not in session:
            session["bot_session_id"] = str(uuid4())
        return session["bot_session_id"]
    except RuntimeError:
        return "default"


def _get_state(session_id):
    if session_id not in _sessions:
        _sessions[session_id] = _new_session_state()
    return _sessions[session_id]


def _append_message(state, sender, text, mode, tag=None):
    msg = {
        "sender": sender,
        "mode": mode,
        "text": text,
        "timestamp": _now_label(),
    }
    if tag:
        msg["tag"] = tag
    state["messages"].append(msg)
    return msg


def _is_medical_advice_request(text):
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in MEDICAL_ADVICE_PATTERNS)


def _has_meaningful_letters(text):
    letters = re.findall(r"[a-zA-Z]", text)
    return len(letters) >= 2


def _looks_like_gibberish(text):
    cleaned = text.strip().lower()
    if not cleaned or not _has_meaningful_letters(cleaned):
        return True
    # Repeated single character or keyboard smash heuristic
    alpha_only = re.sub(r"[^a-z]", "", cleaned)
    if len(alpha_only) >= 4 and len(set(alpha_only)) <= 2:
        return True
    if cleaned in {"asdf", "asdfgh", "qwerty", "zxcv", "test123"}:
        return True
    return False


def _validate_intake_input(step, raw_text):
    text = (raw_text or "").strip()
    lowered = text.lower()

    if not text:
        return False, "", (
            "It looks like your message was blank. Please type a brief response "
            "so I can continue your intake."
        )

    if step == "duration_severity" and DURATION_OR_SEVERITY_HINTS.search(text):
        return True, text, ""

    if _looks_like_gibberish(text):
        return False, "", (
            "I couldn't quite understand that input. Could you please reply "
            "using a clear word or short phrase?"
        )

    if step == "patient_name":
        if lowered in VAGUE_NON_ANSWERS or lowered in NONE_EQUIVALENTS:
            return False, "", (
                "Hello! To get started, please enter your full name "
                "(for example, 'Sarah Jenkins')."
            )
        if re.search(r"\d", text):
            return False, "", (
                "Please enter a valid name using letters only "
                "(for example, 'Sarah Jenkins')."
            )
        if len(text) < 2:
            return False, "", "Please provide your full name (at least 2 characters)."
        return True, text.title() if text.islower() else text, ""

    if step == "chief_complaint":
        if lowered in VAGUE_NON_ANSWERS or lowered in NONE_EQUIVALENTS or len(text) < 4:
            return False, "", (
                "Could you describe your main symptoms in a little more detail? "
                "For example: 'dry cough and mild fever' or 'headache and sore throat'."
            )
        return True, text, ""

    if step == "duration_severity":
        if lowered in VAGUE_NON_ANSWERS or lowered in NONE_EQUIVALENTS:
            return False, "", (
                "Please share roughly how long the symptoms have lasted and/or "
                "how severe they feel (for example: '3 days, moderate 5/10')."
            )
        if not DURATION_OR_SEVERITY_HINTS.search(text):
            return False, "", (
                "Please include a timeframe or severity level (such as 'since Tuesday', "
                "'for 3 days', 'mild', 'moderate', or '6/10')."
            )
        return True, text, ""

    if step == "associated_symptoms":
        if lowered in NONE_EQUIVALENTS:
            return True, "Denies additional associated symptoms", ""
        if lowered in VAGUE_NON_ANSWERS or len(text) < 3:
            return False, "", (
                "Please let me know any extra symptoms (like fever, dizziness, or "
                "shortness of breath), or reply 'none' if you don't have any."
            )
        return True, text, ""

    if step == "medical_history":
        if lowered in NONE_EQUIVALENTS:
            return True, "No known allergies, medications, or prior history reported", ""
        if lowered in VAGUE_NON_ANSWERS or len(text) < 3:
            return False, "", (
                "Please share any medical conditions, medications, or allergies, "
                "or type 'none' if none apply."
            )
        return True, text, ""

    return True, text, ""


def _build_intake_summary(state):
    data = state["intake_data"]
    completed_count = sum(1 for key in INTAKE_STEPS[:-1] if data.get(key))
    is_complete = state["intake_step"] == "completed"
    return {
        "patient_name": data["patient_name"] or "Pending",
        "chief_complaint": data["chief_complaint"] or "Pending",
        "duration_severity": data["duration_severity"] or "Pending",
        "associated_symptoms": data["associated_symptoms"] or "Pending",
        "medical_history": data["medical_history"] or "Pending",
        "completed_steps": completed_count,
        "total_steps": len(INTAKE_STEPS) - 1,
        "current_step": state["intake_step"],
        "is_complete": is_complete,
        "status": "Ready for Clinician Review" if is_complete else "In Progress",
        "record_id": state.get("intake_record_id"),
    }


def _save_intake_record(state):
    summary = _build_intake_summary(state)
    record = {
        "id": _next_intake_id[0],
        "patient_name": summary["patient_name"],
        "chief_complaint": summary["chief_complaint"],
        "duration_severity": summary["duration_severity"],
        "associated_symptoms": summary["associated_symptoms"],
        "medical_history": summary["medical_history"],
        "status": "Ready for Clinician Review",
        "created_at": datetime.now().isoformat(timespec="minutes"),
    }
    _next_intake_id[0] += 1
    _intake_records.append(record)
    state["intake_submitted"] = True
    state["intake_record_id"] = record["id"]
    return record


def _available_slots(clinician_filter=None):
    """Return upcoming mock clinic slots that are not yet booked."""
    now = datetime.now()
    base_days = [
        (now + timedelta(days=1)).date(),
        (now + timedelta(days=2)).date(),
    ]
    times = [(9, 30), (11, 15), (14, 0), (15, 30)]
    clinicians = (
        [c["name"] for c in CLINIC_CLINICIANS if c["name"].lower() == clinician_filter.lower()]
        if clinician_filter
        else [c["name"] for c in CLINIC_CLINICIANS]
    )
    if not clinicians:
        clinicians = [c["name"] for c in CLINIC_CLINICIANS]

    booked = {
        (a["clinician"].lower(), a["datetime"])
        for a in appointments_store._appointments
        if a["status"] == "scheduled"
    }

    slots = []
    for day in base_days:
        for clinician in clinicians:
            for hour, minute in times:
                dt_iso = datetime(day.year, day.month, day.day, hour, minute).isoformat()
                if (clinician.lower(), dt_iso) not in booked:
                    label = datetime(day.year, day.month, day.day, hour, minute).strftime(
                        "%a %b %d at %I:%M %p"
                    ).replace(" 0", " ")
                    slots.append({
                        "clinician": clinician,
                        "datetime": dt_iso,
                        "label": f"{clinician} — {label}",
                    })
                if len(slots) >= 6:
                    return slots
    return slots


def _create_appointment_record(patient_name, clinician, dt_str, reason=""):
    patient_name = (patient_name or "").strip()
    clinician = (clinician or "").strip()
    dt_str = (dt_str or "").strip()
    reason = (reason or "").strip()

    if not patient_name or not clinician or not dt_str:
        return None, "Patient name, clinician, and date/time are required.", 400

    try:
        dt = datetime.fromisoformat(dt_str)
    except ValueError:
        return None, "Date and time must be ISO 8601 (YYYY-MM-DDTHH:MM).", 400

    normalized_iso = dt.isoformat()
    for a in appointments_store._appointments:
        if (
            a["clinician"].lower() == clinician.lower()
            and a["datetime"] == normalized_iso
            and a["status"] == "scheduled"
        ):
            return None, f"{clinician} is already booked at that time. Please pick another slot.", 409

    appt = {
        "id": appointments_store._next_id[0],
        "patient_name": patient_name,
        "clinician": clinician,
        "datetime": normalized_iso,
        "reason": reason or "Booked via AI Receptionist",
        "status": "scheduled",
    }
    appointments_store._next_id[0] += 1
    appointments_store._appointments.append(appt)

    receipt = {
        "confirmation_code": f"CAI-{8800 + appt['id']}",
        "appointment_id": appt["id"],
        "patient_name": appt["patient_name"],
        "clinician": appt["clinician"],
        "datetime": appt["datetime"],
        "formatted_datetime": dt.strftime("%a, %b %d, %Y at %I:%M %p").replace(" 0", " "),
        "reason": appt["reason"],
        "status": appt["status"],
    }
    return receipt, "", 201


def _match_clinician(text):
    lowered = text.lower()
    for doc in CLINIC_CLINICIANS:
        surname = doc["name"].split()[-1].lower()
        if surname in lowered or doc["name"].lower() in lowered:
            return doc["name"]
    return ""


def _parse_natural_datetime(text):
    """Parse ISO strings or common conversational date/time phrases."""
    iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2})\b", text)
    if iso_match:
        return iso_match.group(1).replace(" ", "T")

    lowered = text.lower()
    target_date = None
    if "today" in lowered:
        target_date = datetime.now().date()
    elif "tomorrow" in lowered:
        target_date = (datetime.now() + timedelta(days=1)).date()
    else:
        day_names = [
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday",
        ]
        for idx, day_name in enumerate(day_names):
            if day_name in lowered:
                today_idx = datetime.now().weekday()
                delta = (idx - today_idx) % 7 or 7
                target_date = (datetime.now() + timedelta(days=delta)).date()
                break

    time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", lowered)
    if not time_match:
        time_match_24 = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", lowered)
        if time_match_24 and target_date:
            hour = int(time_match_24.group(1))
            minute = int(time_match_24.group(2))
            return datetime(target_date.year, target_date.month, target_date.day, hour, minute).isoformat()
        return ""

    hour = int(time_match.group(1))
    minute = int(time_match.group(2) or 0)
    meridiem = time_match.group(3)
    if hour == 12:
        hour = 0 if meridiem == "am" else 12
    elif meridiem == "pm":
        hour += 12

    if not target_date:
        target_date = (datetime.now() + timedelta(days=1)).date()

    return datetime(target_date.year, target_date.month, target_date.day, hour, minute).isoformat()


def _detect_faq(text):
    lowered = text.lower()
    if any(k in lowered for k in ("hour", "open", "close", "closing", "schedule hours")):
        return CLINIC_FAQS["hours"]
    if any(k in lowered for k in ("where", "location", "address", "parking", "directions")):
        return CLINIC_FAQS["location"]
    if any(k in lowered for k in ("doctor", "clinician", "specialist", "physician", "who works")):
        return CLINIC_FAQS["doctors"]
    if any(k in lowered for k in ("policy", "policies", "bring", "insurance", "health card", "fee")):
        return CLINIC_FAQS["policy"]
    if any(k in lowered for k in ("privacy", "hipaa", "phi", "data", "security")):
        return CLINIC_FAQS["privacy"]
    return ""


def _quick_replies_for_state(state):
    if state["mode"] == "intake":
        step = state["intake_step"]
        if step == "patient_name":
            return ["Sarah Jenkins", "Alex Morgan", "John Doe"]
        if step == "chief_complaint":
            return [
                "Dry cough and mild fever",
                "Sore throat and fatigue",
                "Persistent headache",
            ]
        if step == "duration_severity":
            return [
                "Since Tuesday, mild (4/10)",
                "For 3 days, moderate (6/10)",
                "Started yesterday morning, mild",
            ]
        if step == "associated_symptoms":
            return [
                "Mild chills, no chest pain",
                "Fatigue and nasal congestion",
                "None",
            ]
        if step == "medical_history":
            return [
                "Mild asthma, no known drug allergies",
                "Penicillin allergy, no daily meds",
                "None",
            ]
        return ["Switch to AI Receptionist", "Start new intake"]

    # Receptionist mode quick replies
    draft = state["booking_draft"]
    if draft["active"]:
        if draft["step"] == "clinician":
            return ["Dr. Chen", "Dr. Patel", "Dr. Rivera"]
        if draft["step"] == "datetime":
            slots = _available_slots(draft.get("clinician"))
            return [s["label"] for s in slots[:3]]
        if draft["step"] == "reason":
            return ["Follow-up consultation", "New symptom check-up", "Routine physical"]

    return [
        "What are your clinic hours?",
        "Where are you located?",
        "Show available appointment slots",
        "Book an appointment",
        "Cancel an appointment",
    ]


def _handle_intake_message(state, text):
    step = state["intake_step"]
    lowered = text.strip().lower()
    if step == "completed":
        if "receptionist" in lowered:
            state["mode"] = "receptionist"
            return (
                "Switched to AI Receptionist mode. Ask about clinic hours, location, "
                "available doctors, or say 'Book an appointment'.",
                True,
                "Receptionist Ready",
            )
        if "new intake" in lowered or "reset" in lowered:
            fresh = _new_session_state()
            fresh["messages"] = []
            state.clear()
            state.update(fresh)
            return INTAKE_PROMPTS["patient_name"], True, "Guided Intake"
        return (
            "Your pre-visit intake summary is already complete and ready for "
            "your clinician. Click 'Start New Intake' to reset or switch to "
            "'AI Receptionist' to book an appointment or ask clinic questions.",
            True,
            "Completed",
        )

    valid, cleaned_value, error_msg = _validate_intake_input(step, text)
    if not valid:
        return error_msg, False, "Validation Prompt"

    state["intake_data"][step] = cleaned_value
    next_index = INTAKE_STEPS.index(step) + 1
    next_step = INTAKE_STEPS[next_index]
    state["intake_step"] = next_step

    if next_step == "completed":
        record = _save_intake_record(state)
        reply = (
            f"Thank you, {record['patient_name']}! Your pre-visit intake is complete "
            f"(Intake #{record['id']}). I've prepared a structured summary on the right "
            f"panel for your clinician to review. You can also switch to AI Receptionist "
            f"if you need to book or manage an appointment."
        )
        return reply, True, "Intake Complete"

    prompt = INTAKE_PROMPTS[next_step].format(**state["intake_data"])
    return prompt, True, "Guided Intake"


def _handle_receptionist_booking_flow(state, text):
    draft = state["booking_draft"]
    lowered = text.lower()

    if any(word in lowered for word in ("stop", "nevermind", "abort", "exit booking")):
        draft.update({
            "active": False,
            "step": None,
            "patient_name": "",
            "clinician": "",
            "datetime": "",
            "reason": "",
        })
        return "No problem — I've cancelled that booking flow. How else can I help?", True, "Receptionist"

    if draft["step"] == "patient_name":
        if _looks_like_gibberish(text) or lowered in VAGUE_NON_ANSWERS or re.search(r"\d", text):
            return "Please enter the patient's full name (e.g., 'Sarah Jenkins').", False, "Validation Prompt"
        draft["patient_name"] = text.title() if text.islower() else text.strip()
        if not draft["clinician"]:
            draft["step"] = "clinician"
            return (
                f"Got it, {draft['patient_name']}. Which clinician would you like to see: "
                "Dr. Chen, Dr. Patel, or Dr. Rivera?",
                True,
                "Booking",
            )
        draft["step"] = "datetime"
        slots = _available_slots(draft["clinician"])
        slot_preview = ", ".join(s["label"].split(" — ")[1] for s in slots[:3])
        return (
            f"Which date and time works best with {draft['clinician']}? "
            f"Next open times: {slot_preview}.",
            True,
            "Booking",
        )

    if draft["step"] == "clinician":
        clinician = _match_clinician(text)
        if not clinician:
            return (
                "Please choose one of our clinic doctors: Dr. Chen, Dr. Patel, or Dr. Rivera.",
                False,
                "Validation Prompt",
            )
        draft["clinician"] = clinician
        draft["step"] = "datetime"
        slots = _available_slots(clinician)
        slot_preview = ", ".join(s["label"].split(" — ")[1] for s in slots[:3])
        return (
            f"Great, {clinician}. What date and time would you like? "
            f"Available options include: {slot_preview}.",
            True,
            "Booking",
        )

    if draft["step"] == "datetime":
        matched_slot = next((s for s in _available_slots() if s["label"].lower() == lowered), None)
        dt_iso = matched_slot["datetime"] if matched_slot else _parse_natural_datetime(text)
        if not dt_iso:
            return (
                "Please provide a valid date and time (for example, 'tomorrow at 10:00 AM' "
                "or pick one of the suggested slot buttons below).",
                False,
                "Validation Prompt",
            )
        draft["datetime"] = dt_iso
        draft["step"] = "reason"
        return "What is the brief reason for the visit? (Or say 'routine checkup'.)", True, "Booking"

    if draft["step"] == "reason":
        reason = "Routine check-up" if lowered in NONE_EQUIVALENTS else text.strip()
        if _looks_like_gibberish(reason):
            return "Please provide a brief visit reason (or say 'none').", False, "Validation Prompt"
        draft["reason"] = reason
        receipt, err, _status = _create_appointment_record(
            draft["patient_name"], draft["clinician"], draft["datetime"], draft["reason"]
        )
        draft.update({
            "active": False,
            "step": None,
            "patient_name": "",
            "clinician": "",
            "datetime": "",
            "reason": "",
        })
        if err:
            return f"Unable to finalize booking: {err}", False, "Scheduling Conflict"
        state["last_receipt"] = receipt
        return (
            f"Booking confirmed! Confirmation #{receipt['confirmation_code']} for "
            f"{receipt['patient_name']} with {receipt['clinician']} on "
            f"{receipt['formatted_datetime']}. It is now synced with the Front Desk queue.",
            True,
            "Booking Confirmed",
        )

    return "Let's try that again. How can I assist you?", False, "Receptionist"


def _handle_receptionist_message(state, text):
    cleaned = (text or "").strip()
    lowered = cleaned.lower()

    if not cleaned:
        return (
            "Please enter a question or scheduling request (for example: "
            "'What are your hours?' or 'Book an appointment').",
            False,
            "Validation Prompt",
        )

    # Continue active booking conversation if already started
    if state["booking_draft"]["active"]:
        return _handle_receptionist_booking_flow(state, cleaned)

    if _looks_like_gibberish(cleaned):
        return (
            "I didn't understand that message. You can ask about clinic hours, "
            "location, doctors, or ask to book, reschedule, or cancel an appointment.",
            False,
            "Validation Prompt",
        )

    # Check FAQs first
    faq_answer = _detect_faq(cleaned)
    if faq_answer:
        return faq_answer, True, "Clinic FAQ"

    # Available slots query
    if any(k in lowered for k in ("slot", "opening", "openings", "available", "availability")):
        clinician = _match_clinician(cleaned)
        slots = _available_slots(clinician or None)
        if not slots:
            return "There are currently no open slots available.", True, "Scheduling"
        summary_lines = ", ".join(s["label"] for s in slots[:4])
        return (
            f"Here are the next available openings: {summary_lines}. "
            f"Say 'Book an appointment' or select a slot below to schedule.",
            True,
            "Available Slots",
        )

    # Cancel appointment intent
    if "cancel" in lowered:
        scheduled = [a for a in appointments_store._appointments if a["status"] == "scheduled"]
        if not scheduled:
            return "There are currently no active scheduled appointments to cancel.", True, "Receptionist"

        target = None
        id_match = re.search(r"#?(\d+)", cleaned)
        if id_match:
            appt_id = int(id_match.group(1))
            target = next((a for a in scheduled if a["id"] == appt_id), None)
        if not target:
            target = next(
                (a for a in scheduled if a["patient_name"].lower() in lowered),
                None,
            )
        if not target and len(scheduled) == 1:
            target = scheduled[0]

        if not target:
            appt_list = "; ".join(
                f"#{a['id']} {a['patient_name']} ({a['clinician']} at {a['datetime']})"
                for a in scheduled
            )
            return (
                f"Which appointment would you like to cancel? Active bookings: {appt_list}. "
                f"Reply with 'cancel #<id>' (for example, 'cancel #{scheduled[0]['id']}').",
                True,
                "Cancel Appointment",
            )

        target["status"] = "cancelled"
        if state.get("last_receipt") and state["last_receipt"]["appointment_id"] == target["id"]:
            state["last_receipt"]["status"] = "cancelled"
        return (
            f"Appointment #{target['id']} for {target['patient_name']} with "
            f"{target['clinician']} has been cancelled and updated in the Front Desk queue.",
            True,
            "Cancelled",
        )

    # Reschedule appointment intent
    if "reschedule" in lowered:
        scheduled = [a for a in appointments_store._appointments if a["status"] == "scheduled"]
        if not scheduled:
            return "There are currently no active scheduled appointments to reschedule.", True, "Receptionist"

        target = None
        id_match = re.search(r"#?(\d+)", cleaned)
        if id_match:
            appt_id = int(id_match.group(1))
            target = next((a for a in scheduled if a["id"] == appt_id), None)
        if not target:
            target = next(
                (a for a in scheduled if a["patient_name"].lower() in lowered),
                None,
            )
        if not target and len(scheduled) == 1:
            target = scheduled[0]

        new_dt = _parse_natural_datetime(cleaned)
        if not target:
            appt_list = "; ".join(
                f"#{a['id']} {a['patient_name']} ({a['clinician']})"
                for a in scheduled
            )
            return (
                f"Please specify which appointment ID to reschedule and the new date/time. "
                f"Active bookings: {appt_list}.",
                True,
                "Reschedule",
            )
        if not new_dt:
            return (
                f"What new date and time would you like for appointment #{target['id']} "
                f"({target['patient_name']} with {target['clinician']})? "
                f"Example: 'reschedule #{target['id']} to tomorrow at 2:00 PM'.",
                False,
                "Reschedule",
            )

        for other in appointments_store._appointments:
            if (
                other["id"] != target["id"]
                and other["clinician"].lower() == target["clinician"].lower()
                and other["datetime"] == new_dt
                and other["status"] == "scheduled"
            ):
                return f"{target['clinician']} already has another booking at that time.", False, "Conflict"

        target["datetime"] = new_dt
        formatted = datetime.fromisoformat(new_dt).strftime("%a, %b %d, %Y at %I:%M %p").replace(" 0", " ")
        if state.get("last_receipt") and state["last_receipt"]["appointment_id"] == target["id"]:
            state["last_receipt"]["datetime"] = new_dt
            state["last_receipt"]["formatted_datetime"] = formatted
        return (
            f"Appointment #{target['id']} for {target['patient_name']} with "
            f"{target['clinician']} has been rescheduled to {formatted}.",
            True,
            "Rescheduled",
        )

    # Book appointment intent (either full one-liner or start guided booking)
    if any(k in lowered for k in ("book", "schedule", "appointment", "visit", "see dr")):
        known_name = state["intake_data"].get("patient_name", "")
        clinician = _match_clinician(cleaned)
        dt_iso = _parse_natural_datetime(cleaned)

        if known_name and clinician and dt_iso:
            receipt, err, _status = _create_appointment_record(
                known_name, clinician, dt_iso,
                state["intake_data"].get("chief_complaint") or "Consultation",
            )
            if err:
                return err, False, "Scheduling Conflict"
            state["last_receipt"] = receipt
            return (
                f"Booking confirmed! Confirmation #{receipt['confirmation_code']} for "
                f"{receipt['patient_name']} with {receipt['clinician']} on "
                f"{receipt['formatted_datetime']}.",
                True,
                "Booking Confirmed",
            )

        draft = state["booking_draft"]
        draft["active"] = True
        draft["patient_name"] = known_name
        draft["clinician"] = clinician
        draft["datetime"] = dt_iso
        draft["reason"] = ""

        if not draft["patient_name"]:
            draft["step"] = "patient_name"
            return "I'd be happy to book an appointment! What is the patient's full name?", True, "Booking"
        if not draft["clinician"]:
            draft["step"] = "clinician"
            return (
                f"Sure, {draft['patient_name']}. Which clinician would you like to book with: "
                "Dr. Chen, Dr. Patel, or Dr. Rivera?",
                True,
                "Booking",
            )
        if not draft["datetime"]:
            draft["step"] = "datetime"
            slots = _available_slots(draft["clinician"])
            slot_preview = ", ".join(s["label"].split(" — ")[1] for s in slots[:3])
            return (
                f"Which date and time works best with {draft['clinician']}? "
                f"Next open times: {slot_preview}.",
                True,
                "Booking",
            )
        draft["step"] = "reason"
        return "What is the brief reason for the visit?", True, "Booking"

    return (
        "I can help with clinic hours, location & parking, available doctors, "
        "or booking, rescheduling, and cancelling appointments. What would you like to do?",
        True,
        "Receptionist",
    )


@intake_bot_bp.route("/api/bot/state", methods=["GET"])
def get_bot_state():
    sid = _get_session_id()
    state = _get_state(sid)
    return jsonify({
        "session_id": sid,
        "mode": state["mode"],
        "intake_summary": _build_intake_summary(state),
        "messages": state["messages"],
        "quick_replies": _quick_replies_for_state(state),
        "available_slots": _available_slots(),
        "clinicians": CLINIC_CLINICIANS,
        "last_receipt": state["last_receipt"],
    })


@intake_bot_bp.route("/api/bot/mode", methods=["POST"])
def switch_bot_mode():
    data = request.get_json(silent=True) or {}
    sid = _get_session_id(data)
    state = _get_state(sid)
    requested_mode = data.get("mode")
    if requested_mode not in ("intake", "receptionist"):
        return jsonify({"error": "mode must be 'intake' or 'receptionist'"}), 400

    if requested_mode != state["mode"]:
        state["mode"] = requested_mode
        if requested_mode == "receptionist":
            _append_message(
                state,
                "bot",
                "Switched to AI Receptionist mode. Ask about clinic hours, location, "
                "available doctors, or say 'Book an appointment'.",
                "receptionist",
                tag="Receptionist Ready",
            )
        else:
            step = state["intake_step"]
            resume_text = (
                "Switched back to Pre-Visit Intake mode. Your intake summary is complete."
                if step == "completed"
                else f"Switched back to Pre-Visit Intake mode. {INTAKE_PROMPTS[step].format(**state['intake_data'])}"
            )
            _append_message(state, "bot", resume_text, "intake", tag="Guided Intake")

    return jsonify({
        "session_id": sid,
        "mode": state["mode"],
        "intake_summary": _build_intake_summary(state),
        "messages": state["messages"],
        "quick_replies": _quick_replies_for_state(state),
        "available_slots": _available_slots(),
        "last_receipt": state["last_receipt"],
    })


@intake_bot_bp.route("/api/bot/message", methods=["POST"])
def post_bot_message():
    data = request.get_json(silent=True) or {}
    sid = _get_session_id(data)
    state = _get_state(sid)

    requested_mode = data.get("mode")
    if requested_mode in ("intake", "receptionist") and requested_mode != state["mode"]:
        state["mode"] = requested_mode
        if requested_mode == "receptionist":
            _append_message(
                state,
                "bot",
                "Switched to AI Receptionist mode. Ask me about clinic hours, location, "
                "doctors, or say 'Book an appointment'.",
                "receptionist",
                tag="Receptionist Ready",
            )

    raw_text = data.get("message", "")
    trimmed = raw_text.strip() if isinstance(raw_text, str) else ""
    mode = state["mode"]

    if trimmed:
        _append_message(state, "patient", trimmed, mode)

    # Strict medical safety guardrail in both modes
    if trimmed and _is_medical_advice_request(trimmed):
        guardrail_msg = (
            "Safety Notice: I cannot diagnose conditions, provide medical advice, "
            "perform triage, or prescribe medications. Your information is recorded "
            "strictly for review by an authorized clinician. If you have a medical "
            "emergency, please call 911 or alert clinic staff immediately."
        )
        if mode == "intake" and state["intake_step"] != "completed":
            current_prompt = INTAKE_PROMPTS[state["intake_step"]].format(**state["intake_data"])
            guardrail_msg = f"{guardrail_msg}\n\nTo continue your intake: {current_prompt}"
        _append_message(state, "bot", guardrail_msg, mode, tag="Safety Guardrail")
        return jsonify({
            "session_id": sid,
            "mode": mode,
            "reply": guardrail_msg,
            "valid": False,
            "guardrail_triggered": True,
            "intake_summary": _build_intake_summary(state),
            "messages": state["messages"],
            "quick_replies": _quick_replies_for_state(state),
            "available_slots": _available_slots(),
            "last_receipt": state["last_receipt"],
        })

    if mode == "intake":
        reply, is_valid, tag = _handle_intake_message(state, trimmed)
    else:
        reply, is_valid, tag = _handle_receptionist_message(state, trimmed)

    _append_message(state, "bot", reply, state["mode"], tag=tag)

    return jsonify({
        "session_id": sid,
        "mode": state["mode"],
        "reply": reply,
        "valid": is_valid,
        "guardrail_triggered": False,
        "intake_summary": _build_intake_summary(state),
        "messages": state["messages"],
        "quick_replies": _quick_replies_for_state(state),
        "available_slots": _available_slots(),
        "last_receipt": state["last_receipt"],
    })


@intake_bot_bp.route("/api/bot/reset", methods=["POST"])
def reset_bot():
    data = request.get_json(silent=True) or {}
    sid = _get_session_id(data)
    requested_mode = data.get("mode", "intake")
    state = _new_session_state()
    if requested_mode == "receptionist":
        state["mode"] = "receptionist"
        state["messages"] = [
            {
                "sender": "bot",
                "mode": "receptionist",
                "text": (
                    "Hello! I'm the Clinical AI Receptionist. Ask me about clinic hours, "
                    "location, clinicians, or say 'Book an appointment' to schedule a visit."
                ),
                "timestamp": _now_label(),
                "tag": "AI Receptionist",
            }
        ]
    _sessions[sid] = state
    return jsonify({
        "session_id": sid,
        "mode": state["mode"],
        "intake_summary": _build_intake_summary(state),
        "messages": state["messages"],
        "quick_replies": _quick_replies_for_state(state),
        "available_slots": _available_slots(),
        "last_receipt": state["last_receipt"],
    })


@intake_bot_bp.route("/api/bot/book", methods=["POST"])
def quick_book_appointment():
    data = request.get_json(silent=True) or {}
    sid = _get_session_id(data)
    state = _get_state(sid)

    patient_name = data.get("patient_name") or state["intake_data"].get("patient_name", "")
    clinician = data.get("clinician", "")
    dt_str = data.get("datetime", "")
    reason = data.get("reason") or state["intake_data"].get("chief_complaint", "")

    receipt, err, status_code = _create_appointment_record(
        patient_name, clinician, dt_str, reason
    )
    if err:
        return jsonify({"error": err}), status_code

    state["last_receipt"] = receipt
    confirm_msg = (
        f"Appointment confirmed via Receptionist Bot! Confirmation #{receipt['confirmation_code']} "
        f"for {receipt['patient_name']} with {receipt['clinician']} on "
        f"{receipt['formatted_datetime']}."
    )
    _append_message(state, "bot", confirm_msg, state["mode"], tag="Booking Confirmed")

    return jsonify({
        "receipt": receipt,
        "messages": state["messages"],
        "available_slots": _available_slots(),
    }), 201


@intake_bot_bp.route("/api/bot/intakes", methods=["GET"])
def list_intake_records():
    """Return finalized synthetic intake summaries for clinician/Joel review."""
    return jsonify(_intake_records)
