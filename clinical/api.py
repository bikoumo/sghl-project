from ninja import Router
from typing import List
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja.errors import HttpError
from django.db import models
from django.core.cache import cache
import authentication.models
from authentication.security import RoleBasedAuth
from .models import Bed, Consultation, Hospitalization, Medication, Invoice, Appointment, Payment
from .schemas import (
    BedOutSchema, ConsultationCreateSchema, ConsultationDetailSchema,
    PatientMedicalRecordSchema, PatientOutSchema, MedicationOutSchema,
    DispenseMedicationInputSchema, InvoiceOutSchema, AppointmentCreateSchema,
    AppointmentOutSchema, StatsOutSchema
)

router = Router(tags=["Gestion Clinique & Médicale"])

@router.get("/stats/", response=StatsOutSchema, auth=RoleBasedAuth(allowed_roles=["DG", "SECRETARY_GENERAL", "SECRETARY_SERVICE", "DOCTOR", "PATIENT", "BIOLOGIST"]))
def get_dashboard_stats(request):
    user = request.auth_user
    today = timezone.now().date()
    cache_key = f"dashboard-stats:{user.id}:{user.role}:{user.service_id or 0}:{today}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    appointments_qs = Appointment.objects.filter(appointment_date__date=today, status='CONFIRMED')
    if user.role == 'SECRETARY_SERVICE':
        appointments_qs = appointments_qs.filter(service=user.service)
    elif user.role == 'DOCTOR':
        appointments_qs = appointments_qs.filter(doctor=user)

    hospitalized_qs = Hospitalization.objects.filter(is_active=True)
    if user.role == 'SECRETARY_SERVICE':
        hospitalized_qs = hospitalized_qs.filter(bed__room__service=user.service)
    elif user.role == 'DOCTOR':
        hospitalized_qs = hospitalized_qs.filter(doctor=user)

    low_stock_qs = authentication.models.User.objects.none()
    from .models import Provision
    low_stock_qs = Provision.objects.filter(quantity__lt=10)
    if user.role == 'SECRETARY_SERVICE':
        low_stock_qs = low_stock_qs.filter(service=user.service)

    result = {
        "date": today.isoformat(),
        "appointments_count": appointments_qs.count(),
        "hospitalized_count": hospitalized_qs.count(),
        "low_stock_count": low_stock_qs.count(),
    }
    cache.set(cache_key, result, timeout=60)
    return result

# ==========================================
# 1. LOGISTIQUE : LITS
# ==========================================
@router.get("/beds/available", response=List[BedOutSchema], auth=RoleBasedAuth(allowed_roles=["DOCTOR", "RECEPCIONIST", "ADMIN"]))
def list_available_beds(request):
    beds = Bed.objects.filter(is_occupied=False).select_related('room__service__building')
    return [{"id": b.id, "number": b.number, "is_occupied": b.is_occupied, "room_number": b.room.number, "service_name": b.room.service.name} for b in beds]

# ==========================================
# 2. CONSULTATIONS & DOSSIER MÉDICAL
# ==========================================
@router.post("/consultations", response=ConsultationDetailSchema, auth=RoleBasedAuth(allowed_roles=["DOCTOR"]))
def create_consultation(request, payload: ConsultationCreateSchema):
    user = request.auth_user
    consultation = Consultation.objects.create(
        patient_id=payload.patient_id, doctor=user, symptoms=payload.symptoms, 
        diagnosis=payload.diagnosis, prescription=payload.prescription, created_by=user
    )
    if payload.requires_hospitalization and payload.bed_id:
        bed = get_object_or_404(Bed, id=payload.bed_id)
        Hospitalization.objects.create(patient_id=payload.patient_id, bed=bed, doctor=user, reason=f"Diagnostic : {payload.diagnosis}", created_by=user)
    return {"id": consultation.id, "doctor_username": user.username, "date": consultation.date, "symptoms": consultation.symptoms, "diagnosis": consultation.diagnosis, "prescription": consultation.prescription, "requires_hospitalization": payload.requires_hospitalization}

@router.get("/patients", response=List[PatientOutSchema], auth=RoleBasedAuth(allowed_roles=["DOCTOR", "RECEPCIONIST", "ADMIN"]))
def list_patients(request):
    patients_users = authentication.models.User.objects.filter(role="PATIENT")
    return [{"id": p.id, "matricule": getattr(p, "matricule", f"PT-{p.id}"), "nom": p.last_name, "prenom": p.first_name, "genre": "M/F", "dateNaissance": "01/01/2000", "telephone": "000", "statut": "Externe"} for p in patients_users]

@router.get("/patients/{patient_id}/record", response=PatientMedicalRecordSchema, auth=RoleBasedAuth(allowed_roles=["DOCTOR", "ADMIN"]))
def get_patient_medical_record(request, patient_id: int):
    consultations = Consultation.objects.filter(patient_id=patient_id).select_related('doctor', 'patient')
    if not consultations.exists():
        patient = get_object_or_404(authentication.models.User, id=patient_id, role="PATIENT")
        return {"patient_id": patient.id, "patient_username": patient.username, "consultations": []}
    history = [{"id": c.id, "doctor_username": c.doctor.username, "date": c.date, "symptoms": c.symptoms, "diagnosis": c.diagnosis, "prescription": c.prescription, "requires_hospitalization": Hospitalization.objects.filter(patient_id=patient_id, start_date__date=c.date.date()).exists()} for c in consultations]
    return {"patient_id": consultations.first().patient.id, "patient_username": consultations.first().patient.username, "consultations": history}

# ==========================================
# 3. PHARMACIE & 4. PLANNING & 7. FACTURES
# ==========================================
@router.get("/medications", response=List[MedicationOutSchema], auth=RoleBasedAuth(allowed_roles=["DOCTOR", "PHARMACIST", "ADMIN"]))
def list_medications(request):
    return Medication.objects.all()

@router.post("/pharmacy/dispense", response=InvoiceOutSchema, auth=RoleBasedAuth(allowed_roles=["PHARMACIST"]))
def dispense_medication(request, payload: DispenseMedicationInputSchema, patient_id: int):
    user = request.auth_user
    patient = get_object_or_404(authentication.models.User, id=patient_id, role="PATIENT")
    medication = get_object_or_404(Medication, id=payload.medication_id)
    if medication.stock_quantity < payload.quantity:
        raise HttpError(400, "Stock insuffisant")
    medication.stock_quantity -= payload.quantity
    medication.save()
    invoice = Invoice.objects.create(patient=patient, total_amount=float(medication.price_per_unit) * payload.quantity, status="PENDING", created_by=user)
    return {"id": invoice.id, "patient_username": invoice.patient.username, "total_amount": float(invoice.total_amount), "status": invoice.status, "created_at": invoice.created_at}

@router.post("/appointments", response=AppointmentOutSchema, auth=RoleBasedAuth(allowed_roles=["PATIENT", "RECEPCIONIST"]))
def create_appointment(request, payload: AppointmentCreateSchema):
    if payload.appointment_date < timezone.now():
        raise HttpError(400, "Impossible de prendre un rendez-vous dans le passé.")
    user = request.auth_user
    patient = user if user.role == "PATIENT" else get_object_or_404(authentication.models.User, id=request.GET.get('patient_id'), role="PATIENT")
    appointment = Appointment.objects.create(patient=patient, doctor_id=payload.doctor_id, appointment_date=payload.appointment_date, reason=payload.reason, status="SCHEDULED", created_by=user)
    return {"id": appointment.id, "patient_username": appointment.patient.username, "doctor_username": appointment.doctor.username, "appointment_date": appointment.appointment_date, "reason": appointment.reason, "status": appointment.status, "created_at": appointment.created_at}

@router.get("/appointments/my-schedule", response=List[AppointmentOutSchema], auth=RoleBasedAuth(allowed_roles=["DOCTOR", "PATIENT"]))
def get_my_appointments(request):
    user = request.auth_user
    appointments = Appointment.objects.filter(doctor=user) if user.role == "DOCTOR" else Appointment.objects.filter(patient=user)
    return [{"id": a.id, "patient_username": a.patient.username, "doctor_username": a.doctor.username, "appointment_date": a.appointment_date, "reason": a.reason, "status": a.status, "created_at": a.created_at} for a in appointments]

@router.get("/appointments/", auth=RoleBasedAuth(allowed_roles=["DG", "SECRETARY_GENERAL", "SECRETARY_SERVICE", "DOCTOR", "PATIENT", "BIOLOGIST"]))
def list_appointments_json(request):
    user = request.auth_user
    appointments_qs = Appointment.objects.select_related("patient", "doctor", "service").order_by("-appointment_date")

    if user.role == "DOCTOR":
        appointments_qs = appointments_qs.filter(doctor=user)
    elif user.role == "PATIENT":
        appointments_qs = appointments_qs.filter(patient=user)
    elif user.role == "SECRETARY_SERVICE" and user.service_id:
        appointments_qs = appointments_qs.filter(service=user.service)

    appointments = []
    for appointment in appointments_qs:
        appointments.append({
            "id": appointment.id,
            "patient__username": appointment.patient.username,
            "doctor__username": appointment.doctor.username,
            "appointment_date": appointment.appointment_date.isoformat(),
            "status": appointment.status,
            "service__name": appointment.service.name if appointment.service else None,
        })

    return {"appointments": appointments}

@router.post("/invoices/{invoice_id}/pay", auth=RoleBasedAuth(allowed_roles=["RECEPCIONIST", "ADMIN"]))
def mark_invoice_as_paid(request, invoice_id: int):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    invoice.status = 'PAID'
    invoice.save()
    return {"message": "Facture marquée comme payée avec succès.", "invoice_id": invoice.id, "status": invoice.status}