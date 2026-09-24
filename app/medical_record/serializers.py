"""Serializers para converter modelos ORM em dicionários JSON-serializáveis."""

from typing import Optional


def _serialize_user(user) -> Optional[dict]:
    if not user:
        return None
    return {
        "public_id": str(user.public_id),
        "full_name": user.full_name,
        "email": user.email,
        "status": user.status.value if hasattr(user.status, "value") else str(user.status),
    }


def _serialize_patient(patient) -> Optional[dict]:
    if not patient:
        return None
    return {
        "public_id": str(patient.public_id),
        "cellphone": patient.cellphone,
        "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
        "gender": patient.gender.value if hasattr(patient.gender, "value") else str(patient.gender),
        "user": _serialize_user(patient.user) if patient.user else None,
    }


def _serialize_doctor(doctor) -> Optional[dict]:
    if not doctor:
        return None
    return {
        "public_id": str(doctor.public_id),
        "CRM": doctor.CRM,
        "specialty": doctor.specialty.value if hasattr(doctor.specialty, "value") else str(doctor.specialty),
        "user": _serialize_user(doctor.user) if doctor.user else None,
    }


def _serialize_prescription_item(item) -> dict:
    return {
        "id": item.id,
        "medication_name": item.medication_name,
        "dosage": item.dosage,
        "frequency": item.frequency,
        "treatment_duration": item.treatment_duration,
    }


def _serialize_prescription(prescription) -> Optional[dict]:
    if not prescription:
        return None
    items = []
    if prescription.items:
        items = [_serialize_prescription_item(i) for i in prescription.items]
    return {
        "id": prescription.id,
        "items": items,
    }


def serialize_medical_record_with_relations(medical_record) -> Optional[dict]:
    """Serializa MedicalRecordModel com patient e doctor, sem consultation/diagnostic/certificate."""
    if not medical_record:
        return None
    return {
        "id": medical_record.id,
        "public_id": str(medical_record.public_id),
        "created_date": medical_record.created_date.isoformat() if medical_record.created_date else None,
        "updated_date": medical_record.updated_date.isoformat() if medical_record.updated_date else None,
        "hash": medical_record.hash,
        "blockchain_tx_id": medical_record.blockchain_tx_id,
        "doctor_id": str(medical_record.doctor_id) if medical_record.doctor_id else None,
        "patient_id": str(medical_record.patient_id) if medical_record.patient_id else None,
        "patient": _serialize_patient(medical_record.patient) if medical_record.patient else None,
        "doctor": _serialize_doctor(medical_record.doctor) if medical_record.doctor else None,
    }


def serialize_consultation(consultation) -> dict:
    """Serializa ConsultationModel para dict."""
    if not consultation:
        return {}
    medical_record = consultation.medical_record if hasattr(consultation, "medical_record") else None
    prescription = consultation.prescription if hasattr(consultation, "prescription") else None
    return {
        "id": consultation.id,
        "chief_complaint": consultation.chief_complaint,
        "history_of_present_illness": consultation.history_of_present_illness,
        "diagnosis": consultation.diagnosis,
        "treatment_plan": consultation.treatment_plan,
        "created_date": consultation.created_date.isoformat() if consultation.created_date else None,
        "updated_date": consultation.updated_date.isoformat() if consultation.updated_date else None,
        "medical_record_id": consultation.medical_record_id,
        "medical_record": serialize_medical_record_with_relations(medical_record) if medical_record else None,
        "prescription": _serialize_prescription(prescription) if prescription else None,
    }


def serialize_diagnostic(diagnostic) -> dict:
    """Serializa DiagnosticModel para dict."""
    if not diagnostic:
        return {}
    medical_record = diagnostic.medical_record if hasattr(diagnostic, "medical_record") else None
    return {
        "id": diagnostic.id,
        "description": diagnostic.description,
        "issue_date": diagnostic.issue_date.isoformat() if hasattr(diagnostic.issue_date, "isoformat") else str(diagnostic.issue_date),
        "result": diagnostic.result,
        "medical_record_id": diagnostic.medical_record_id,
        "medical_record": serialize_medical_record_with_relations(medical_record) if medical_record else None,
    }


def serialize_medical_certificate(certificate) -> dict:
    """Serializa MedicalCertificatedModel para dict."""
    if not certificate:
        return {}
    medical_record = certificate.medical_record if hasattr(certificate, "medical_record") else None
    return {
        "id": certificate.id,
        "purpose": certificate.purpose,
        "period_of_leave": certificate.period_of_leave,
        "created_date": certificate.created_date.isoformat() if certificate.created_date else None,
        "updated_date": certificate.updated_date.isoformat() if certificate.updated_date else None,
        "medical_record_id": certificate.medical_record_id,
        "medical_record": serialize_medical_record_with_relations(medical_record) if medical_record else None,
    }


def serialize_medical_record_basic(medical_record) -> Optional[dict]:
    """Serializa MedicalRecordModel básico (sem relações profundas)."""
    if not medical_record:
        return None
    return {
        "id": medical_record.id,
        "public_id": str(medical_record.public_id),
        "created_date": medical_record.created_date.isoformat() if medical_record.created_date else None,
        "updated_date": medical_record.updated_date.isoformat() if medical_record.updated_date else None,
        "hash": medical_record.hash,
        "blockchain_tx_id": medical_record.blockchain_tx_id,
        "doctor_id": str(medical_record.doctor_id) if medical_record.doctor_id else None,
        "patient_id": str(medical_record.patient_id) if medical_record.patient_id else None,
    }


def serialize_medical_record_full(medical_record) -> dict:
    """Serializa MedicalRecordModel completo com consultation, diagnostic, certificate."""
    if not medical_record:
        return {}
    consultation = medical_record.consultation if hasattr(medical_record, "consultation") else None
    diagnostic = medical_record.diagnostic if hasattr(medical_record, "diagnostic") else None
    certificate = medical_record.certificate if hasattr(medical_record, "certificate") else None

    result = {
        "id": medical_record.id,
        "public_id": str(medical_record.public_id),
        "created_date": medical_record.created_date.isoformat() if medical_record.created_date else None,
        "updated_date": medical_record.updated_date.isoformat() if medical_record.updated_date else None,
        "hash": medical_record.hash,
        "blockchain_tx_id": medical_record.blockchain_tx_id,
        "doctor_id": str(medical_record.doctor_id) if medical_record.doctor_id else None,
        "patient_id": str(medical_record.patient_id) if medical_record.patient_id else None,
        "patient": _serialize_patient(medical_record.patient) if medical_record.patient else None,
        "doctor": _serialize_doctor(medical_record.doctor) if medical_record.doctor else None,
        "consultation": serialize_consultation(consultation) if consultation else None,
        "diagnostic": serialize_diagnostic(diagnostic) if diagnostic else None,
        "certificate": serialize_medical_certificate(certificate) if certificate else None,
    }
    return result
