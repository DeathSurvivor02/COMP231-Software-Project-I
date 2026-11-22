"""
Clinical Documentation Blueprint (Ean's Role)
Handles transcript entry, synthetic SOAP note draft generation, editing,
and mandatory clinician approval before finalization.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request

clinical_docs_bp = Blueprint("clinical_docs", __name__)

_SOAP_NOTES: List[Dict[str, Any]] = []


def _extract_section_lines(transcript: str, keywords: List[str]) -> str:
    lines = [ln.strip() for ln in transcript.splitlines() if ln.strip()]
    matched = [
        ln for ln in lines
        if any(re.search(rf"\b{kw}\b", ln, re.IGNORECASE) for kw in keywords)
    ]
    return " ".join(matched) if matched else ""


def generate_draft_soap(
    transcript: str,
    patient_name: str = "Synthetic Patient",
    encounter_type: str = "Outpatient Follow-up",
) -> Dict[str, Any]:
    clean_transcript = (transcript or "").strip()
    if not clean_transcript:
        raise ValueError("Transcript text is required to generate a draft SOAP note.")

    subj = _extract_section_lines(
        clean_transcript,
        ["pain", "feel", "symptom", "days", "week", "headache", "cough", "fever", "nausea", "reports", "complains"],
    ) or f"Patient ({patient_name}) presents for {encounter_type}. Summary: {clean_transcript[:220]}"

    obj = _extract_section_lines(
        clean_transcript,
        ["bp", "hr", "temp", "spo2", "vitals", "exam", "lungs", "heart", "afebrile", "mmhg", "bpm"],
    ) or "Vitals stable (synthetic baseline: BP 120/78 mmHg, HR 74 bpm, Temp 98.4 F, SpO2 99% RA)."

    assess = _extract_section_lines(
        clean_transcript,
        ["diagnosis", "assessment", "likely", "suspect", "differential", "consistent"],
    ) or "Acute symptom presentation under evaluation; differential includes viral syndrome vs. benign etiology."

    plan = _extract_section_lines(
        clean_transcript,
        ["plan", "prescribe", "follow", "rest", "hydrate", "ibuprofen", "acetaminophen", "return", "lab", "imaging"],
    ) or "1. Supportive care and hydration. 2. Symptomatic relief PRN. 3. Follow up in 1 week or sooner if worsening."

    note = {
        "note_id": f"SOAP-{uuid.uuid4().hex[:8].upper()}",
        "patient_name": patient_name.strip() or "Synthetic Patient",
        "encounter_type": encounter_type.strip() or "Outpatient Follow-up",
        "transcript": clean_transcript,
        "soap": {
            "subjective": subj,
            "objective": obj,
            "assessment": assess,
            "plan": plan,
        },
        "status": "DRAFT",
        "approved_by": None,
        "approved_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _SOAP_NOTES.append(note)
    return note


def update_draft_soap(note_id: str, updates: Dict[str, str]) -> Dict[str, Any]:
    for note in _SOAP_NOTES:
        if note["note_id"] == note_id:
            if note["status"] == "FINALIZED":
                raise PermissionError("Finalized SOAP notes are locked and cannot be edited.")
            for section in ("subjective", "objective", "assessment", "plan"):
                if section in updates and updates[section] is not None:
                    note["soap"][section] = str(updates[section]).strip()
            note["updated_at"] = datetime.now(timezone.utc).isoformat()
            return note
    raise KeyError(f"SOAP note '{note_id}' not found.")


def approve_and_finalize_soap(
    note_id: str,
    clinician_name: str,
    approval_confirmed: bool = False,
) -> Dict[str, Any]:
    if not approval_confirmed:
        raise ValueError("Clinician approval confirmation is required before finalization.")
    clinician = (clinician_name or "").strip()
    if not clinician:
        raise ValueError("Clinician name/signature is required to finalize.")

    for note in _SOAP_NOTES:
        if note["note_id"] == note_id:
            if note["status"] == "FINALIZED":
                return note
            note["status"] = "FINALIZED"
            note["approved_by"] = clinician
            note["approved_at"] = datetime.now(timezone.utc).isoformat()
            note["updated_at"] = note["approved_at"]
            return note
    raise KeyError(f"SOAP note '{note_id}' not found.")


@clinical_docs_bp.route("/api/soap/list", methods=["GET"])
def api_list_soap():
    return jsonify({"notes": _SOAP_NOTES}), 200


@clinical_docs_bp.route("/api/soap/generate", methods=["POST"])
def api_generate_soap():
    payload = request.get_json(silent=True) or {}
    try:
        note = generate_draft_soap(
            transcript=payload.get("transcript", ""),
            patient_name=payload.get("patient_name", "Synthetic Patient"),
            encounter_type=payload.get("encounter_type", "Outpatient Follow-up"),
        )
        return jsonify({"note": note}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@clinical_docs_bp.route("/api/soap/update", methods=["POST"])
def api_update_soap():
    payload = request.get_json(silent=True) or {}
    try:
        note = update_draft_soap(
            note_id=payload.get("note_id", ""),
            updates=payload.get("soap", {}),
        )
        return jsonify({"note": note}), 200
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404


@clinical_docs_bp.route("/api/soap/finalize", methods=["POST"])
def api_finalize_soap():
    payload = request.get_json(silent=True) or {}
    try:
        note = approve_and_finalize_soap(
            note_id=payload.get("note_id", ""),
            clinician_name=payload.get("clinician_name", ""),
            approval_confirmed=bool(payload.get("approval_confirmed", False)),
        )
        return jsonify({"note": note}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
