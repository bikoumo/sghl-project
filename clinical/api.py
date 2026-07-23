from ninja import Router, Query
from typing import List
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import ValidationError
from ninja.errors import HttpError
from django.db import models
from django.core.cache import cache
import authentication.models
from authentication.security import RoleBasedAuth
from authentication.roles import (
    STAFF_ROLES,
    CLINICAL_READ_ROLES,
    CLINICAL_WRITE_ROLES,
    BILLING_ROLES,
    PHARMACY_ROLES,
    SECRETARY_ROLES,
    ADMISSION_ROLES,
)
from .models import (
    Bed, Consultation, Hospitalization, Medication, Invoice, Appointment, Payment,
    Service, Room, PediatricRecord, MaternityRecord, ExamRequest, ExamResult,
    DeathRecord, ArchivedClinicalRecord,
)
from .schemas import (
    BedOutSchema, BedListItemSchema, BedAdmitSchema,
    ConsultationCreateSchema, ConsultationDetailSchema,
    PatientMedicalRecordSchema, PatientOutSchema, MedicationOutSchema,
    DispenseMedicationInputSchema, InvoiceOutSchema, AppointmentCreateSchema,
    AppointmentOutSchema, AppointmentStatusSchema, StatsOutSchema, PayInvoiceSchema,
    ServiceMapOutSchema, RoomOutSchema,
    PediatricRecordInSchema, PediatricRecordOutSchema,
    MaternityRecordInSchema, MaternityRecordOutSchema,
    HospitalizationOutSchema, ExamRequestInSchema, ExamRequestOutSchema, ExamResultInSchema,
    InvoiceCreateSchema, InvoiceLineSchema,
    DeathRecordCreateSchema, DeathRecordOutSchema, DeathStatsSchema, ArchivedRecordOutSchema,
)
import io
from django.http import HttpResponse
import csv
from datetime import date, datetime

router = Router(tags=["Gestion Clinique & Médicale"])


def _parse_iso_date(value: str, field_name: str) -> date:
    raw = (value or '').strip()
    if not raw:
        raise HttpError(400, f'{field_name} est obligatoire.')
    try:
        return date.fromisoformat(raw[:10])
    except ValueError as exc:
        raise HttpError(400, f'{field_name} invalide (format AAAA-MM-JJ).') from exc

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

    # Map to frontend expected keys (consultations, beds_occupied, beds_total, emergencies)
    from .models import Bed
    total_beds = Bed.objects.count()
    emergencies_count = 0
    today_consults = Consultation.objects.filter(date__date=today).count()
    if user.role == 'DOCTOR':
        today_consults = Consultation.objects.filter(date__date=today, doctor=user).count()
    # RDV urgences du jour
    emergencies_count = Appointment.objects.filter(
        appointment_date__date=today,
        service__code='URG',
    ).exclude(status='CANCELLED').count()

    patients_count = authentication.models.User.objects.filter(role='PATIENT').count()
    invoices_pending = Invoice.objects.filter(status='PENDING').count()

    result = {
        "date": today.isoformat(),
        "consultations": today_consults,
        "beds_occupied": hospitalized_qs.count(),
        "beds_total": total_beds,
        "emergencies": emergencies_count,
        "low_stock_count": low_stock_qs.count(),
        "appointments_count": appointments_qs.count(),
        "hospitalized_count": hospitalized_qs.count(),
        "patients_count": patients_count,
        "invoices_pending": invoices_pending,
    }
    cache.set(cache_key, result, timeout=60)
    return result


@router.get('/doctors', auth=RoleBasedAuth(allowed_roles=STAFF_ROLES))
def list_doctors(request):
    # Return a simple list of doctors for select inputs
    from authentication.models import User
    docs = User.objects.filter(role='DOCTOR').values('id', 'username', 'first_name', 'last_name')
    return [ { 'id': d['id'], 'username': d['username'], 'nom': d['last_name'], 'prenom': d['first_name'] } for d in docs ]


@router.get('/services', auth=RoleBasedAuth(allowed_roles=STAFF_ROLES))
@router.get('/services/', auth=RoleBasedAuth(allowed_roles=STAFF_ROLES))
def list_services_public(request):
    services = Service.objects.select_related('building').all()
    return [
        {
            'id': s.id,
            'name': s.name,
            'code': s.code,
            'building_name': s.building.name if s.building_id else None,
            'is_open_h24': s.is_open_h24,
            'location_lat': s.location_lat,
            'location_long': s.location_long,
        }
        for s in services
    ]


@router.get('/hospitalizations/', response=List[HospitalizationOutSchema], auth=RoleBasedAuth(allowed_roles=STAFF_ROLES))
def list_hospitalizations(request):
    user = request.auth_user
    qs = Hospitalization.objects.filter(is_active=True).select_related(
        'patient', 'doctor', 'bed__room__service',
    )
    if user.role == 'SECRETARY_SERVICE' and user.service_id:
        qs = qs.filter(bed__room__service_id=user.service_id)
    elif user.role == 'DOCTOR':
        qs = qs.filter(doctor=user)
    return [
        {
            'id': h.id,
            'patient_id': h.patient_id,
            'patient_name': f"{h.patient.first_name} {h.patient.last_name}".strip() or h.patient.username,
            'doctor_id': h.doctor_id,
            'doctor_name': (
                f"{h.doctor.first_name} {h.doctor.last_name}".strip() or h.doctor.username
            ) if h.doctor else None,
            'bed_id': h.bed_id,
            'bed_number': h.bed.number,
            'service_name': h.bed.room.service.name,
            'reason': h.reason,
            'start_date': h.start_date,
            'is_active': h.is_active,
        }
        for h in qs.order_by('-start_date')
    ]


def _serialize_exam(exam: ExamRequest) -> dict:
    result = getattr(exam, 'result', None)
    patient = exam.patient
    return {
        'id': exam.id,
        'patient_id': exam.patient_id,
        'patient_name': f"{patient.first_name} {patient.last_name}".strip() or patient.username,
        'title': exam.title,
        'description': exam.description or '',
        'status': exam.status,
        'requested_at': exam.requested_at,
        'result_text': result.result_text if result else None,
        'conclusion': result.conclusion if result else None,
    }


@router.get('/exams/', response=List[ExamRequestOutSchema], auth=RoleBasedAuth(allowed_roles=STAFF_ROLES))
def list_exams(request):
    qs = ExamRequest.objects.select_related('patient').prefetch_related('result').order_by('-requested_at')
    user = request.auth_user
    if user.role == 'DOCTOR':
        qs = qs.filter(requested_by=user)
    return [_serialize_exam(e) for e in qs]


@router.post('/exams/', response=ExamRequestOutSchema, auth=RoleBasedAuth(allowed_roles=CLINICAL_WRITE_ROLES))
def create_exam(request, payload: ExamRequestInSchema):
    title = (payload.title or '').strip()
    if len(title) < 2:
        raise HttpError(400, 'Le titre de l\'examen est obligatoire (min. 2 caractères).')
    patient = get_object_or_404(authentication.models.User, id=payload.patient_id, role='PATIENT')
    exam = ExamRequest.objects.create(
        patient=patient,
        requested_by=request.auth_user,
        title=title,
        description=(payload.description or '').strip(),
    )
    return _serialize_exam(exam)


@router.post('/exams/{exam_id}/result', response=ExamRequestOutSchema, auth=RoleBasedAuth(allowed_roles=['DG', 'DOCTOR', 'BIOLOGIST']))
def submit_exam_result(request, exam_id: int, payload: ExamResultInSchema):
    exam = get_object_or_404(ExamRequest.objects.select_related('patient'), id=exam_id)
    result_text = (payload.result_text or '').strip()
    if len(result_text) < 2:
        raise HttpError(400, 'Le résultat doit contenir au moins 2 caractères.')
    result, _ = ExamResult.objects.update_or_create(
        exam_request=exam,
        defaults={
            'performed_by': request.auth_user,
            'result_text': result_text,
            'conclusion': (payload.conclusion or '').strip(),
        },
    )
    exam.status = 'COMPLETED'
    exam.save(update_fields=['status', 'updated_at'])
    return _serialize_exam(exam)


@router.get('/rooms/', response=List[RoomOutSchema], auth=RoleBasedAuth(allowed_roles=STAFF_ROLES))
def list_rooms(request):
    rooms = Room.objects.select_related('service').order_by('service__name', 'number')
    return [
        {
            'id': r.id,
            'number': r.number,
            'room_type': r.room_type,
            'service': r.service_id,
            'service_name': r.service.name,
        }
        for r in rooms
    ]


def _serialize_pediatric(record: PediatricRecord) -> dict:
    return {
        'id': record.id,
        'nom': record.nom,
        'date_naissance': record.date_naissance.isoformat(),
        'poids': float(record.poids),
        'taille': record.taille,
        'groupe_sanguin': record.groupe_sanguin or '',
        'vaccin_date': record.vaccin_date.isoformat(),
        'status': record.status,
    }


@router.get('/pediatrie/', response=List[PediatricRecordOutSchema], auth=RoleBasedAuth(allowed_roles=STAFF_ROLES))
def list_pediatrie(request):
    return [_serialize_pediatric(r) for r in PediatricRecord.objects.all()]


@router.post('/pediatrie/', response=PediatricRecordOutSchema, auth=RoleBasedAuth(allowed_roles=['DG', 'DOCTOR', 'SECRETARY_GENERAL', 'SECRETARY_SERVICE']))
def create_pediatrie(request, payload: PediatricRecordInSchema):
    nom = (payload.nom or '').strip()
    if len(nom) < 2:
        raise HttpError(400, 'Le nom est obligatoire (min. 2 caractères).')
    if payload.poids <= 0:
        raise HttpError(400, 'Le poids doit être supérieur à 0.')
    date_naissance = _parse_iso_date(payload.date_naissance, 'Date de naissance')
    vaccin_date = _parse_iso_date(payload.vaccin_date, 'Date de vaccin')
    if date_naissance > timezone.localdate():
        raise HttpError(400, 'La date de naissance ne peut pas être dans le futur.')
    record = PediatricRecord.objects.create(
        nom=nom,
        date_naissance=date_naissance,
        poids=payload.poids,
        taille=payload.taille,
        groupe_sanguin=(payload.groupe_sanguin or '').strip(),
        vaccin_date=vaccin_date,
    )
    return _serialize_pediatric(record)


def _serialize_maternity(record: MaternityRecord) -> dict:
    return {
        'id': record.id,
        'nom': record.nom,
        'prenom': record.prenom,
        'date_terme': record.date_terme.isoformat(),
        'next_visit': record.next_visit.isoformat(),
        'status': record.status,
        'notes': record.notes or '',
    }


@router.get('/maternity/', response=List[MaternityRecordOutSchema], auth=RoleBasedAuth(allowed_roles=STAFF_ROLES))
def list_maternity(request):
    return [_serialize_maternity(r) for r in MaternityRecord.objects.all()]


@router.post('/maternity/', response=MaternityRecordOutSchema, auth=RoleBasedAuth(allowed_roles=['DG', 'DOCTOR', 'SECRETARY_GENERAL', 'SECRETARY_SERVICE']))
def create_maternity(request, payload: MaternityRecordInSchema):
    nom = (payload.nom or '').strip()
    prenom = (payload.prenom or '').strip()
    if not nom or not prenom:
        raise HttpError(400, 'Nom et prénom sont obligatoires.')
    date_terme = _parse_iso_date(payload.date_terme, 'Date terme')
    next_visit = _parse_iso_date(payload.next_visit, 'Prochaine visite')
    if next_visit > date_terme:
        raise HttpError(400, 'La prochaine visite ne peut pas être après la date terme.')
    record = MaternityRecord.objects.create(
        nom=nom,
        prenom=prenom,
        date_terme=date_terme,
        next_visit=next_visit,
        status=(payload.status or 'Suivi en cours').strip(),
        notes=(payload.notes or '').strip(),
    )
    return _serialize_maternity(record)


@router.get('/invoices/', auth=RoleBasedAuth(allowed_roles=[*BILLING_ROLES, 'PATIENT', 'DOCTOR']))
def list_invoices(request):
    user = request.auth_user
    qs = Invoice.objects.select_related('patient', 'consultation').order_by('-created_at')
    if user.role == 'PATIENT':
        qs = qs.filter(patient=user)
    return [
        {
            'id': inv.id,
            'patient': {'id': inv.patient.id, 'username': inv.patient.username},
            'patient_username': inv.patient.username,
            'total_amount': float(inv.total_amount),
            'status': inv.status,
            'label': getattr(inv, 'label', 'Consultation'),
            'remaining': float(inv.remaining_amount()) if hasattr(inv, 'remaining_amount') else float(inv.total_amount),
            'created_at': inv.created_at.isoformat(),
            'consultation_id': inv.consultation_id,
        }
        for inv in qs
    ]

# ==========================================
# 1. LOGISTIQUE : LITS & ADMISSION
# ==========================================
def _serialize_bed(bed: Bed) -> dict:
    admission = (
        bed.admissions.filter(is_active=True)
        .select_related('patient', 'doctor')
        .order_by('-start_date')
        .first()
    )
    patient = admission.patient if admission else None
    doctor = admission.doctor if admission else None
    patient_name = None
    if patient:
        patient_name = f"{patient.first_name} {patient.last_name}".strip() or patient.username

    doctor_name = None
    if doctor:
        doctor_name = f"{doctor.first_name} {doctor.last_name}".strip() or doctor.username

    return {
        "id": bed.id,
        "number": bed.number,
        "is_occupied": bed.is_occupied,
        "status": "Occupé" if bed.is_occupied else "Libre",
        "room_id": bed.room_id,
        "room_number": bed.room.number,
        "room_type": bed.room.room_type,
        "service_name": bed.room.service.name,
        "service_code": bed.room.service.code,
        "patient_id": patient.id if patient else None,
        "patient_name": patient_name,
        "patient_matricule": getattr(patient, "matricule", None) if patient else None,
        "doctor_id": doctor.id if doctor else None,
        "doctor_name": doctor_name,
        "hospitalization_id": admission.id if admission else None,
        "admission_date": admission.start_date if admission else None,
        "reason": admission.reason if admission else None,
    }


def _beds_queryset_for_user(user):
    qs = Bed.objects.select_related('room__service__building').prefetch_related(
        models.Prefetch(
            'admissions',
            queryset=Hospitalization.objects.filter(is_active=True).select_related('patient', 'doctor'),
        )
    )
    if user.role == 'SECRETARY_SERVICE' and user.service_id:
        qs = qs.filter(room__service_id=user.service_id)
    elif user.role == 'DOCTOR' and user.service_id:
        qs = qs.filter(room__service_id=user.service_id)
    return qs.order_by('room__service__name', 'room__number', 'number')


@router.get("/beds/", response=List[BedListItemSchema], auth=RoleBasedAuth(allowed_roles=ADMISSION_ROLES))
def list_beds(request):
    beds = _beds_queryset_for_user(request.auth_user)
    return [_serialize_bed(bed) for bed in beds]


@router.get("/beds/available", response=List[BedOutSchema], auth=RoleBasedAuth(allowed_roles=ADMISSION_ROLES))
def list_available_beds(request):
    beds = _beds_queryset_for_user(request.auth_user).filter(is_occupied=False)
    return [
        {
            "id": b.id,
            "number": b.number,
            "is_occupied": b.is_occupied,
            "room_number": b.room.number,
            "service_name": b.room.service.name,
        }
        for b in beds
    ]


@router.post("/beds/{bed_id}/admit", response=BedListItemSchema, auth=RoleBasedAuth(allowed_roles=ADMISSION_ROLES))
def admit_patient_to_bed(request, bed_id: int, payload: BedAdmitSchema):
    user = request.auth_user
    reason = (payload.reason or "").strip()
    if len(reason) < 3:
        raise HttpError(400, "Le motif d'admission doit contenir au moins 3 caractères.")

    bed = get_object_or_404(
        Bed.objects.select_related('room__service'),
        id=bed_id,
    )

    # Restreindre au service du secrétaire / médecin rattaché
    if user.role in {'SECRETARY_SERVICE', 'DOCTOR'} and user.service_id:
        if bed.room.service_id != user.service_id:
            raise HttpError(403, "Ce lit n'appartient pas à votre service.")

    if bed.is_occupied:
        raise HttpError(400, "Ce lit est déjà occupé.")

    patient = get_object_or_404(authentication.models.User, id=payload.patient_id, role='PATIENT')

    if Hospitalization.objects.filter(patient=patient, is_active=True).exists():
        raise HttpError(400, "Ce patient a déjà une hospitalisation active.")

    doctor_id = payload.doctor_id
    if user.role == 'DOCTOR':
        doctor_id = user.id
    if not doctor_id:
        raise HttpError(400, "Un médecin référent est obligatoire pour l'admission.")

    doctor = get_object_or_404(authentication.models.User, id=doctor_id, role='DOCTOR')

    try:
        Hospitalization.objects.create(
            patient=patient,
            bed=bed,
            doctor=doctor,
            reason=reason,
            created_by=user,
        )
    except ValidationError as exc:
        raise HttpError(400, "; ".join(exc.messages) if hasattr(exc, 'messages') else str(exc))

    bed.refresh_from_db()
    return _serialize_bed(
        Bed.objects.select_related('room__service').prefetch_related(
            models.Prefetch(
                'admissions',
                queryset=Hospitalization.objects.filter(is_active=True).select_related('patient', 'doctor'),
            )
        ).get(pk=bed.pk)
    )


@router.post("/beds/{bed_id}/release", response=BedListItemSchema, auth=RoleBasedAuth(allowed_roles=ADMISSION_ROLES))
def release_bed(request, bed_id: int):
    user = request.auth_user
    bed = get_object_or_404(Bed.objects.select_related('room__service'), id=bed_id)

    if user.role in {'SECRETARY_SERVICE', 'DOCTOR'} and user.service_id:
        if bed.room.service_id != user.service_id:
            raise HttpError(403, "Ce lit n'appartient pas à votre service.")

    admission = (
        Hospitalization.objects.filter(bed=bed, is_active=True)
        .select_related('patient', 'doctor')
        .order_by('-start_date')
        .first()
    )
    if not admission:
        if bed.is_occupied:
            bed.is_occupied = False
            bed.save(update_fields=['is_occupied', 'updated_at'])
        else:
            raise HttpError(400, "Aucun patient n'est actuellement admis sur ce lit.")
    else:
        admission.discharge()

    bed.refresh_from_db()
    return _serialize_bed(
        Bed.objects.select_related('room__service').prefetch_related(
            models.Prefetch(
                'admissions',
                queryset=Hospitalization.objects.filter(is_active=True).select_related('patient', 'doctor'),
            )
        ).get(pk=bed.pk)
    )


# ==========================================
# 2. CONSULTATIONS & DOSSIER MÉDICAL
# ==========================================
@router.post("/consultations", auth=RoleBasedAuth(allowed_roles=CLINICAL_WRITE_ROLES))
@router.post("/consultations/", auth=RoleBasedAuth(allowed_roles=CLINICAL_WRITE_ROLES))
def create_consultation(request, payload: ConsultationCreateSchema):
    from django.conf import settings
    from django.core.exceptions import ValidationError as DjangoValidationError
    from decimal import Decimal

    user = request.auth_user
    symptoms = (payload.symptoms or "").strip()
    diagnosis = (payload.diagnosis or "").strip()
    if len(symptoms) < 3:
        raise HttpError(400, "Les symptômes doivent contenir au moins 3 caractères.")
    if len(diagnosis) < 3:
        raise HttpError(400, "Le diagnostic doit contenir au moins 3 caractères.")

    patient = get_object_or_404(authentication.models.User, id=payload.patient_id, role="PATIENT")

    # Médecin ou Admin (DG) avec doctor_id
    if user.role == 'DOCTOR':
        doctor = user
    elif user.role == 'DG':
        if not payload.doctor_id:
            raise HttpError(400, "En tant qu'admin, précisez doctor_id pour la consultation.")
        doctor = get_object_or_404(authentication.models.User, id=payload.doctor_id, role='DOCTOR')
    else:
        raise HttpError(403, "Seuls les médecins ou l'administrateur peuvent créer une consultation.")

    if payload.requires_hospitalization and not payload.bed_id:
        raise HttpError(400, "Sélectionnez un lit pour l'hospitalisation.")

    consultation = Consultation.objects.create(
        patient=patient,
        doctor=doctor,
        symptoms=symptoms,
        diagnosis=diagnosis,
        prescription=(payload.prescription or "").strip() or None,
        created_by=user,
    )

    hospitalized = False
    if payload.requires_hospitalization and payload.bed_id:
        bed = get_object_or_404(Bed, id=payload.bed_id)
        if bed.is_occupied:
            raise HttpError(400, "Le lit sélectionné est déjà occupé.")
        if Hospitalization.objects.filter(patient=patient, is_active=True).exists():
            raise HttpError(400, "Ce patient a déjà une hospitalisation active.")
        try:
            Hospitalization.objects.create(
                patient=patient,
                bed=bed,
                doctor=doctor,
                reason=f"Diagnostic : {diagnosis}",
                created_by=user,
            )
            hospitalized = True
        except DjangoValidationError as exc:
            message = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
            raise HttpError(400, message)

    # Reçu / facture de consultation automatique
    fee = getattr(settings, 'CONSULTATION_FEE', Decimal('15000'))
    invoice = Invoice.objects.create(
        patient=patient,
        consultation=consultation,
        total_amount=fee,
        status='PENDING',
        label='Consultation médicale',
    )

    return {
        "id": consultation.id,
        "doctor_username": doctor.username,
        "date": consultation.date,
        "symptoms": consultation.symptoms,
        "diagnosis": consultation.diagnosis,
        "prescription": consultation.prescription,
        "requires_hospitalization": hospitalized,
        "invoice_id": invoice.id,
        "invoice_amount": float(invoice.total_amount),
        "receipt_url": f"/clinical/consultations/{consultation.id}/receipt/pdf",
    }


@router.get("/consultations/recent", auth=RoleBasedAuth(allowed_roles=CLINICAL_READ_ROLES))
def list_recent_consultations(request):
    user = request.auth_user
    qs = Consultation.objects.select_related('patient', 'doctor')
    if user.role == 'DOCTOR':
        qs = qs.filter(doctor=user)
    qs = qs.order_by('-date')[:30]
    return [
        {
            "id": c.id,
            "patient_id": c.patient_id,
            "patient_name": f"{c.patient.first_name} {c.patient.last_name}".strip() or c.patient.username,
            "doctor_username": c.doctor.username,
            "date": c.date.isoformat(),
            "symptoms": c.symptoms,
            "diagnosis": c.diagnosis,
            "prescription": c.prescription,
        }
        for c in qs
    ]


@router.get("/patients", response=List[PatientOutSchema], auth=RoleBasedAuth(allowed_roles=CLINICAL_READ_ROLES))
@router.get("/patients/", response=List[PatientOutSchema], auth=RoleBasedAuth(allowed_roles=CLINICAL_READ_ROLES))
def list_patients(request):
    patients_users = authentication.models.User.objects.filter(role="PATIENT").order_by("last_name", "first_name")
    return [
        {
            "id": p.id,
            "matricule": p.matricule or f"PT-{p.id}",
            "nom": p.last_name or "",
            "prenom": p.first_name or "",
            "genre": p.gender or "",
            "dateNaissance": p.birth_date.isoformat() if p.birth_date else "",
            "telephone": p.phone or "",
            "statut": "Externe",
        }
        for p in patients_users
    ]


@router.get("/patients/{patient_id}", auth=RoleBasedAuth(allowed_roles=CLINICAL_READ_ROLES))
@router.get("/patients/{patient_id}/", auth=RoleBasedAuth(allowed_roles=CLINICAL_READ_ROLES))
def get_patient_detail(request, patient_id: int):
    patient = get_object_or_404(authentication.models.User, id=patient_id, role="PATIENT")
    record = get_patient_medical_record(request, patient_id)
    active_hosp = (
        Hospitalization.objects.filter(patient=patient, is_active=True)
        .select_related('bed__room__service', 'doctor')
        .first()
    )
    return {
        "id": patient.id,
        "matricule": patient.matricule or f"PT-{patient.id}",
        "nom": patient.last_name or "",
        "prenom": patient.first_name or "",
        "username": patient.username,
        "genre": patient.gender or "",
        "birth_date": patient.birth_date.isoformat() if patient.birth_date else "",
        "dateNaissance": patient.birth_date.isoformat() if patient.birth_date else "",
        "phone": patient.phone or "",
        "telephone": patient.phone or "",
        "email": patient.email or "",
        "groupe_sanguin": patient.groupe_sanguin or "",
        "allergies": patient.allergies or "",
        "antecedents": patient.antecedents or "",
        "statut": "Hospitalisé" if active_hosp else "Externe",
        "hospitalization": None if not active_hosp else {
            "id": active_hosp.id,
            "bed": active_hosp.bed.number,
            "room": active_hosp.bed.room.number,
            "service": active_hosp.bed.room.service.name,
            "doctor": active_hosp.doctor.username,
            "reason": active_hosp.reason,
            "start_date": active_hosp.start_date.isoformat(),
        },
        "consultations": [
            {
                "id": c["id"],
                "date": c["date"].isoformat() if hasattr(c["date"], "isoformat") else c["date"],
                "diagnostic": c["diagnosis"],
                "diagnosis": c["diagnosis"],
                "symptoms": c["symptoms"],
                "prescription": c.get("prescription"),
                "doctor_username": c["doctor_username"],
            }
            for c in record["consultations"]
        ],
    }


@router.get("/patients/{patient_id}/record", response=PatientMedicalRecordSchema, auth=RoleBasedAuth(allowed_roles=["DOCTOR", "DG", "BIOLOGIST"]))
def get_patient_medical_record(request, patient_id: int):
    consultations = Consultation.objects.filter(patient_id=patient_id).select_related('doctor', 'patient')
    if not consultations.exists():
        patient = get_object_or_404(authentication.models.User, id=patient_id, role="PATIENT")
        return {"patient_id": patient.id, "patient_username": patient.username, "consultations": []}
    history = [
        {
            "id": c.id,
            "doctor_username": c.doctor.username,
            "date": c.date,
            "symptoms": c.symptoms,
            "diagnosis": c.diagnosis,
            "prescription": c.prescription,
            "requires_hospitalization": Hospitalization.objects.filter(
                patient_id=patient_id, start_date__date=c.date.date()
            ).exists(),
        }
        for c in consultations
    ]
    return {
        "patient_id": consultations.first().patient.id,
        "patient_username": consultations.first().patient.username,
        "consultations": history,
    }

# ==========================================
# 3. PHARMACIE & 4. PLANNING & 7. FACTURES
# ==========================================
@router.get("/medications", response=List[MedicationOutSchema], auth=RoleBasedAuth(allowed_roles=PHARMACY_ROLES))
def list_medications(request):
    """Catalogue pharmacie = stock FIFO (finance_logistics), avec repli clinique."""
    from finance_logistics.models import Medication as FinMedication
    from finance_logistics.services import serialize_medication

    fin_meds = list(FinMedication.objects.all().order_by('name'))
    if fin_meds:
        return [
            {
                'id': m.id,
                'name': row['name'],
                'stock_quantity': row['stock_quantity'],
                'price_per_unit': row['price_per_unit'],
            }
            for m in fin_meds
            for row in [serialize_medication(m)]
        ]
    return [
        {
            'id': m.id,
            'name': m.name,
            'stock_quantity': m.stock_quantity,
            'price_per_unit': float(m.price_per_unit),
        }
        for m in Medication.objects.all().order_by('name')
    ]


@router.post("/pharmacy/dispense", auth=RoleBasedAuth(allowed_roles=PHARMACY_ROLES))
def dispense_medication(request, payload: DispenseMedicationInputSchema, patient_id: int):
    """Vente unitaire : décrémente le stock FIFO et crée une facture pharmacie."""
    from finance_logistics.services import process_pharmacy_purchase
    from django.core.exceptions import ValidationError as DjangoValidationError

    patient = get_object_or_404(authentication.models.User, id=patient_id, role="PATIENT")
    if payload.quantity <= 0:
        raise HttpError(400, "La quantité doit être positive.")

    try:
        invoice, lines = process_pharmacy_purchase(
            patient=patient,
            items=[{'medication_id': payload.medication_id, 'quantity': payload.quantity}],
            created_by=request.auth_user,
            mark_paid=False,
        )
    except DjangoValidationError as exc:
        message = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
        raise HttpError(400, message)
    except Exception as exc:
        raise HttpError(400, str(exc))

    return {
        'id': invoice.id,
        'patient_username': patient.username,
        'total_amount': float(invoice.total_amount),
        'status': invoice.status,
        'created_at': invoice.created_at,
        'lines': lines,
    }

@router.post("/appointments", response=AppointmentOutSchema, auth=RoleBasedAuth(allowed_roles=["PATIENT", "DOCTOR", *SECRETARY_ROLES, "DG"]))
@router.post("/appointments/", response=AppointmentOutSchema, auth=RoleBasedAuth(allowed_roles=["PATIENT", "DOCTOR", *SECRETARY_ROLES, "DG"]))
def create_appointment(request, payload: AppointmentCreateSchema):
    from django.core.exceptions import ValidationError as DjangoValidationError
    from .models import Service

    user = request.auth_user
    if payload.appointment_date < timezone.now():
        raise HttpError(400, "Impossible de prendre un rendez-vous dans le passé.")

    if user.role == "PATIENT":
        patient = user
    else:
        if not payload.patient_id:
            raise HttpError(400, "Le patient est obligatoire.")
        patient = get_object_or_404(authentication.models.User, id=payload.patient_id, role="PATIENT")

    doctor = get_object_or_404(authentication.models.User, id=payload.doctor_id, role="DOCTOR")
    service = None
    if payload.service_id:
        service = get_object_or_404(Service, id=payload.service_id)

    try:
        appointment = Appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=payload.appointment_date,
            service=service,
            notes=(payload.notes or "").strip(),
            status="SCHEDULED",
            created_by=user,
        )
        appointment.save()
    except DjangoValidationError as exc:
        message = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
        raise HttpError(400, message)

    return {
        "id": appointment.id,
        "patient_username": appointment.patient.username,
        "doctor_username": appointment.doctor.username,
        "appointment_date": appointment.appointment_date,
        "notes": appointment.notes,
        "status": appointment.status,
        "created_at": appointment.created_at,
        "service_name": appointment.service.name if appointment.service else None,
    }


@router.get("/appointments/my-schedule", response=List[AppointmentOutSchema], auth=RoleBasedAuth(allowed_roles=["DOCTOR", "PATIENT"]))
def get_my_appointments(request):
    user = request.auth_user
    appointments = Appointment.objects.filter(doctor=user) if user.role == "DOCTOR" else Appointment.objects.filter(patient=user)
    appointments = appointments.select_related('patient', 'doctor', 'service').order_by('-appointment_date')
    return [
        {
            "id": a.id,
            "patient_username": a.patient.username,
            "doctor_username": a.doctor.username,
            "appointment_date": a.appointment_date,
            "notes": a.notes,
            "status": a.status,
            "created_at": a.created_at,
            "service_name": a.service.name if a.service else None,
        }
        for a in appointments
    ]


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
            "notes": appointment.notes,
        })

    return {"appointments": appointments}


@router.patch("/appointments/{appointment_id}", auth=RoleBasedAuth(allowed_roles=["DG", "SECRETARY_GENERAL", "SECRETARY_SERVICE", "DOCTOR"]))
@router.patch("/appointments/{appointment_id}/", auth=RoleBasedAuth(allowed_roles=["DG", "SECRETARY_GENERAL", "SECRETARY_SERVICE", "DOCTOR"]))
def update_appointment_status(request, appointment_id: int, payload: AppointmentStatusSchema):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    status = (payload.status or "").upper()
    allowed = {c[0] for c in Appointment.STATUS_CHOICES}
    if status not in allowed:
        raise HttpError(400, f"Statut invalide. Valeurs : {', '.join(sorted(allowed))}")
    user = request.auth_user
    if user.role == 'DOCTOR' and appointment.doctor_id != user.id:
        raise HttpError(403, "Vous ne pouvez modifier que vos propres rendez-vous.")
    appointment.status = status
    appointment.save(update_fields=['status', 'updated_at'])
    return {
        "id": appointment.id,
        "status": appointment.status,
        "message": "Rendez-vous mis à jour.",
    }

def _assert_can_access_patient(user, patient_id: int):
    if user.role == 'DG':
        return
    if user.role == 'PATIENT' and user.id == int(patient_id):
        return
    if user.role in {'DOCTOR', 'BIOLOGIST', 'SECRETARY_GENERAL', 'SECRETARY_SERVICE'}:
        return
    raise HttpError(403, "Accès refusé au dossier patient.")


def _serialize_invoice(inv: Invoice) -> dict:
    return {
        'id': inv.id,
        'patient_username': inv.patient.username,
        'patient': {'id': inv.patient.id, 'username': inv.patient.username},
        'total_amount': float(inv.total_amount),
        'status': inv.status,
        'label': inv.label,
        'remaining': float(inv.remaining_amount()),
        'created_at': inv.created_at.isoformat() if hasattr(inv.created_at, 'isoformat') else inv.created_at,
        'consultation_id': inv.consultation_id,
    }


@router.get("/me/invoices", auth=RoleBasedAuth(allowed_roles=["PATIENT", "DG"]))
def my_invoices(request):
    user = request.auth_user
    if user.role == 'PATIENT':
        qs = Invoice.objects.filter(patient=user)
    else:
        qs = Invoice.objects.all()
    qs = qs.select_related('patient', 'consultation').order_by('-created_at')[:100]
    return [_serialize_invoice(inv) for inv in qs]


@router.get('/patients/search', auth=RoleBasedAuth(allowed_roles=CLINICAL_READ_ROLES))
def search_patients(request, q: str = Query('')):
    """Recherche textuelle de patients par nom, prénom, email ou matricule."""
    query = (q or '').strip()
    if len(query) < 1:
        return list_patients(request)

    users_qs = authentication.models.User.objects.filter(role='PATIENT')
    from django.db.models import Q
    users_qs = users_qs.filter(
        Q(last_name__icontains=query) |
        Q(first_name__icontains=query) |
        Q(email__icontains=query) |
        Q(username__icontains=query) |
        Q(matricule__icontains=query) |
        Q(phone__icontains=query)
    ).order_by('last_name', 'first_name')[:20]

    results = []
    for p in users_qs:
        active_hosp = (
            Hospitalization.objects.filter(patient=p, is_active=True)
            .select_related('bed__room__service', 'doctor')
            .first()
        )
        results.append({
            "id": p.id,
            "matricule": p.matricule or f"PT-{p.id}",
            "nom": p.last_name or "",
            "prenom": p.first_name or "",
            "username": p.username,
            "genre": p.gender or "",
            "telephone": p.phone or "",
            "email": p.email or "",
            "groupe_sanguin": p.groupe_sanguin or "",
            "allergies": p.allergies or "",
            "antecedents": p.antecedents or "",
            "statut": "Hospitalisé" if active_hosp else "Externe",
            "hospitalization": None if not active_hosp else {
                "id": active_hosp.id,
                "bed": active_hosp.bed.number,
                "room": active_hosp.bed.room.number,
                "service": active_hosp.bed.room.service.name,
                "doctor": active_hosp.doctor.username,
                "reason": active_hosp.reason,
                "start_date": active_hosp.start_date.isoformat(),
            },
        })
    return results


@router.post('/invoices/create', auth=RoleBasedAuth(allowed_roles=[*BILLING_ROLES, 'DG']))
def create_manual_invoice(request, payload: InvoiceCreateSchema):
    """Crée une facture manuelle avec plusieurs lignes (hors consultation/pharmacie)."""
    from decimal import Decimal

    patient = get_object_or_404(authentication.models.User, id=payload.patient_id, role='PATIENT')
    if not payload.lines:
        raise HttpError(400, "Ajoutez au moins une ligne à la facture.")

    total = Decimal('0.00')
    for line in payload.lines:
        if line.quantity <= 0 or line.unit_price <= 0:
            raise HttpError(400, "Quantité et prix unitaire doivent être positifs.")
        total += Decimal(str(line.quantity)) * Decimal(str(line.unit_price))

    invoice = Invoice.objects.create(
        patient=patient,
        total_amount=total,
        status='PENDING',
        label=(payload.label or 'Facture').strip(),
    )
    return {
        'id': invoice.id,
        'patient_username': patient.username,
        'total_amount': float(total),
        'status': invoice.status,
        'label': invoice.label,
        'created_at': invoice.created_at.isoformat(),
        'lines': [
            {
                'label': line.label,
                'quantity': line.quantity,
                'unit_price': float(line.unit_price),
                'total': float(Decimal(str(line.quantity)) * Decimal(str(line.unit_price))),
            }
            for line in payload.lines
        ],
    }


@router.post("/invoices/{invoice_id}/pay", auth=RoleBasedAuth(allowed_roles=[*BILLING_ROLES, 'PATIENT', 'DOCTOR']))
def pay_invoice(request, invoice_id: int, payload: PayInvoiceSchema):
    """Paiement CASH (sur place), MTN Mobile Money, Airtel Money ou Carte bancaire."""
    import uuid
    from decimal import Decimal
    from django.core.exceptions import ValidationError as DjangoValidationError

    user = request.auth_user
    invoice = get_object_or_404(Invoice.objects.select_related('patient'), id=invoice_id)

    if user.role == 'PATIENT' and invoice.patient_id != user.id:
        raise HttpError(403, "Vous ne pouvez payer que vos propres factures.")

    method = (payload.method or '').strip().upper()
    if method not in {'CASH', 'MTN', 'AIRTEL', 'CARD'}:
        raise HttpError(400, "Méthode invalide. Utilisez CASH, MTN, AIRTEL ou CARD.")

    remaining = invoice.remaining_amount()
    if remaining <= 0 or invoice.status == 'PAID':
        raise HttpError(400, "Cette facture est déjà soldée.")

    amount = Decimal(str(payload.amount)) if payload.amount is not None else remaining
    if amount <= 0:
        raise HttpError(400, "Le montant doit être positif.")
    if amount > remaining:
        raise HttpError(400, f"Montant supérieur au solde restant ({remaining} FCFA).")

    phone = (payload.phone or '').strip() or None
    card_last_four = (payload.card_last_four or '').strip() or None
    card_expiry = (payload.card_expiry or '').strip() or None

    if method in {'MTN', 'AIRTEL'}:
        if not phone or len(phone) < 8:
            raise HttpError(400, "Numéro de téléphone obligatoire pour MTN / Airtel Money.")

    if method == 'CARD':
        if not card_last_four or len(card_last_four) != 4 or not card_last_four.isdigit():
            raise HttpError(400, "Les 4 derniers chiffres de la carte sont obligatoires.")
        if not card_expiry or len(card_expiry) != 5:
            raise HttpError(400, "La date d'expiration (MM/AA) est obligatoire.")

    prefix = {'CASH': 'CSH', 'MTN': 'MTN', 'AIRTEL': 'AIR', 'CARD': 'CRD'}[method]
    transaction_ref = f"{prefix}-{uuid.uuid4().hex[:10].upper()}"

    try:
        payment = Payment(
            invoice=invoice,
            amount=amount,
            method=method,
            phone=phone,
            card_last_four=card_last_four,
            card_expiry=card_expiry,
            transaction_ref=transaction_ref,
            paid_by=user,
        )
        payment.save()
    except DjangoValidationError as exc:
        message = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
        raise HttpError(400, message)

    invoice.refresh_from_db()
    return {
        'status': 'success',
        'message': f"Paiement {method} enregistré.",
        'invoice_id': invoice.id,
        'invoice_status': invoice.status,
        'amount': float(amount),
        'method': method,
        'phone': phone,
        'card_last_four': card_last_four,
        'transaction_ref': transaction_ref,
        'remaining': float(invoice.remaining_amount()),
    }


@router.get('/invoices/{invoice_id}/pdf', auth=RoleBasedAuth(allowed_roles=[*BILLING_ROLES, *PHARMACY_ROLES, 'PATIENT', 'DOCTOR']))
def invoice_pdf(request, invoice_id: int):
    invoice = get_object_or_404(Invoice.objects.select_related('patient', 'consultation'), id=invoice_id)
    user = request.auth_user
    if user.role == 'PATIENT' and invoice.patient_id != user.id:
        raise HttpError(403, "Accès refusé.")
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception:
        raise HttpError(501, 'Installez reportlab pour générer les PDF (pip install reportlab).')

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.setFont('Helvetica-Bold', 14)
    p.drawString(50, 800, f"SGHL — Facture / Reçu #{invoice.id}")
    p.setFont('Helvetica', 11)
    p.drawString(50, 775, f"Patient: {invoice.patient.get_full_name() or invoice.patient.username}")
    p.drawString(50, 755, f"Libellé: {invoice.label}")
    p.drawString(50, 735, f"Montant: {invoice.total_amount} FCFA")
    p.drawString(50, 715, f"Statut: {invoice.status}")
    y = 690
    for pay in invoice.payments.all():
        p.drawString(50, y, f"- {pay.method} {pay.amount} FCFA ({pay.transaction_ref or 'N/A'})")
        y -= 16
    p.showPage()
    p.save()
    buffer.seek(0)
    return HttpResponse(
        buffer.read(),
        content_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="facture_{invoice.id}.pdf"'},
    )


@router.get('/invoices/export', auth=RoleBasedAuth(allowed_roles=["DG", "SECRETARY_GENERAL"]))
def invoices_export_csv(request):
    qs = Invoice.objects.all().select_related('patient')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="invoices.csv"'
    writer = csv.writer(response)
    writer.writerow(['id', 'patient', 'label', 'total_amount', 'status', 'created_at'])
    for inv in qs:
        writer.writerow([inv.id, inv.patient.username, inv.label, str(inv.total_amount), inv.status, inv.created_at.isoformat()])
    return response


@router.get('/consultations/{consultation_id}/receipt/pdf', auth=RoleBasedAuth(allowed_roles=[*CLINICAL_READ_ROLES, 'PATIENT']))
def consultation_receipt_pdf(request, consultation_id: int):
    from clinical.exports import build_consultation_receipt_pdf

    consultation = get_object_or_404(
        Consultation.objects.select_related('patient', 'doctor'),
        id=consultation_id,
    )
    user = request.auth_user
    if user.role == 'PATIENT' and consultation.patient_id != user.id:
        raise HttpError(403, "Accès refusé à ce reçu.")
    invoice = getattr(consultation, 'invoice', None)
    try:
        pdf_bytes = build_consultation_receipt_pdf(consultation, invoice)
    except Exception:
        raise HttpError(501, 'Installez reportlab pour générer les PDF (pip install reportlab).')
    return HttpResponse(
        pdf_bytes,
        content_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="recu_consultation_{consultation_id}.pdf"'},
    )


@router.get('/patients/{patient_id}/record/pdf', auth=RoleBasedAuth(allowed_roles=["DOCTOR", "DG", "BIOLOGIST", "PATIENT", *SECRETARY_ROLES]))
def patient_record_pdf(request, patient_id: int):
    from clinical.exports import build_patient_record_pdf

    user = request.auth_user
    _assert_can_access_patient(user, patient_id)
    patient = get_object_or_404(authentication.models.User, id=patient_id, role='PATIENT')
    consultations = list(
        Consultation.objects.filter(patient_id=patient_id).select_related('doctor').order_by('-date')
    )
    try:
        pdf_bytes = build_patient_record_pdf(patient, consultations)
    except Exception:
        raise HttpError(501, 'Installez reportlab pour générer les PDF (pip install reportlab).')
    return HttpResponse(
        pdf_bytes,
        content_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="dossier_{patient_id}.pdf"'},
    )


@router.get('/patients/{patient_id}/record/excel', auth=RoleBasedAuth(allowed_roles=["DOCTOR", "DG", "BIOLOGIST", "PATIENT", *SECRETARY_ROLES]))
def patient_record_excel(request, patient_id: int):
    from clinical.exports import build_patient_record_excel_response

    user = request.auth_user
    _assert_can_access_patient(user, patient_id)
    patient = get_object_or_404(authentication.models.User, id=patient_id, role='PATIENT')
    consultations = list(
        Consultation.objects.filter(patient_id=patient_id).select_related('doctor').order_by('-date')
    )
    return build_patient_record_excel_response(patient, consultations)


@router.get('/me/record/pdf', auth=RoleBasedAuth(allowed_roles=["PATIENT"]))
def my_record_pdf(request):
    return patient_record_pdf(request, request.auth_user.id)


@router.get('/me/record/excel', auth=RoleBasedAuth(allowed_roles=["PATIENT"]))
def my_record_excel(request):
    return patient_record_excel(request, request.auth_user.id)


# ==========================================
# 9. GESTION DES DÉCÈS — ENDPOINTS API
# ==========================================


def _serialize_death(record: DeathRecord) -> dict:
    patient = record.patient
    return {
        "id": record.id,
        "patient_id": patient.id,
        "patient_name": f"{patient.first_name} {patient.last_name}".strip() or patient.username,
        "patient_matricule": patient.matricule or f"PT-{patient.id}",
        "reported_by_name": record.reported_by.username if record.reported_by else None,
        "service_id": record.service_id,
        "service_name": record.service.name if record.service else None,
        "cause": record.cause or "",
        "complications": record.complications or "",
        "is_validated": record.is_validated,
        "is_dossier_purged": record.is_dossier_purged,
        "validated_at": record.validated_at,
        "created_at": record.created_at,
    }


@router.post(
    "/death-records/",
    response=DeathRecordOutSchema,
    auth=RoleBasedAuth(allowed_roles=["DG", "SECRETARY_GENERAL", "DOCTOR"]),
)
def create_death_record(request, payload: DeathRecordCreateSchema):
    """Déclarer un décès : patient, cause, service, complications."""
    patient = get_object_or_404(
        authentication.models.User, id=payload.patient_id, role="PATIENT"
    )

    cause = (payload.cause or "").strip()
    if len(cause) < 3:
        raise HttpError(400, "La cause du décès doit contenir au moins 3 caractères.")

    # Vérifier qu'il n'y a pas déjà un DeathRecord non purgé pour ce patient
    existing = DeathRecord.objects.filter(
        patient=patient, is_dossier_purged=False
    ).first()
    if existing:
        raise HttpError(
            400,
            f"Un décès est déjà déclaré pour ce patient (ID #{existing.id}). "
            f"Purge automatique dans 7 jours.",
        )

    service = None
    if payload.service_id:
        service = get_object_or_404(Service, id=payload.service_id)

    record = DeathRecord.objects.create(
        patient=patient,
        reported_by=request.auth_user,
        service=service,
        cause=cause,
        complications=(payload.complications or "").strip() or None,
    )

    return _serialize_death(record)


@router.get(
    "/death-records/",
    response=List[DeathRecordOutSchema],
    auth=RoleBasedAuth(allowed_roles=["DG", "SECRETARY_GENERAL", "SECRETARY_SERVICE", "DOCTOR"]),
)
def list_death_records(request):
    """Lister les décès déclarés. SECRETARY_SERVICE ne voit que son service."""
    user = request.auth_user
    qs = DeathRecord.objects.select_related(
        "patient", "reported_by", "service"
    ).order_by("-created_at")

    if user.role == "SECRETARY_SERVICE" and user.service_id:
        qs = qs.filter(service_id=user.service_id)

    return [_serialize_death(r) for r in qs]


@router.get(
    "/death-records/{record_id}",
    response=DeathRecordOutSchema,
    auth=RoleBasedAuth(allowed_roles=["DG", "SECRETARY_GENERAL", "SECRETARY_SERVICE", "DOCTOR"]),
)
def get_death_record(request, record_id: int):
    """Détail d'un décès."""
    record = get_object_or_404(
        DeathRecord.objects.select_related("patient", "reported_by", "service"),
        id=record_id,
    )
    return _serialize_death(record)


@router.post(
    "/death-records/{record_id}/validate",
    response=DeathRecordOutSchema,
    auth=RoleBasedAuth(allowed_roles=["DG", "SECRETARY_GENERAL"]),
)
def validate_death_record(request, record_id: int):
    """Valider un décès (DG ou Secrétaire Générale). Déclenche le délai de 7 jours avant purge."""
    record = get_object_or_404(
        DeathRecord.objects.select_related("patient", "reported_by", "service"),
        id=record_id,
    )
    if record.is_validated:
        raise HttpError(400, "Ce décès est déjà validé.")

    record.is_validated = True
    record.validated_at = timezone.now()
    record.save(update_fields=["is_validated", "validated_at", "updated_at"])

    return _serialize_death(record)


@router.get(
    "/death-records/stats",
    response=DeathStatsSchema,
    auth=RoleBasedAuth(allowed_roles=["DG", "SECRETARY_GENERAL", "SECRETARY_SERVICE", "DOCTOR"]),
)
def death_stats(request):
    """Dashboard mortalité : total, par service, causes principales."""
    from django.db.models import Count

    today = timezone.now().date()
    now = timezone.now()
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    qs = DeathRecord.objects.filter(is_validated=True)
    user = request.auth_user

    if user.role == "SECRETARY_SERVICE" and user.service_id:
        qs = qs.filter(service_id=user.service_id)

    total_deaths = qs.count()
    deaths_this_month = qs.filter(created_at__gte=first_of_month).count()
    deaths_today = qs.filter(created_at__date=today).count()

    # Par service
    by_service_qs = (
        qs.values("service__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    by_service = [
        {"service": item["service__name"] or "Non spécifié", "count": item["count"]}
        for item in by_service_qs
    ]

    # Causes principales (top 10)
    top_causes_qs = (
        qs.values("cause")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    top_causes = [
        {"cause": item["cause"] or "Non spécifiée", "count": item["count"]}
        for item in top_causes_qs
    ]

    return {
        "total_deaths": total_deaths,
        "deaths_this_month": deaths_this_month,
        "deaths_today": deaths_today,
        "by_service": by_service,
        "top_causes": top_causes,
    }


@router.get(
    "/death-records/archived",
    response=List[ArchivedRecordOutSchema],
    auth=RoleBasedAuth(allowed_roles=["DG", "SECRETARY_GENERAL"]),
)
def list_archived_records(request):
    """Lister les dossiers patients archivés (après purge automatique)."""
    qs = ArchivedClinicalRecord.objects.all().order_by("-archived_at")[:100]
    return [
        {
            "id": r.id,
            "original_username": r.original_username,
            "original_matricule": r.original_matricule,
            "patient_full_name": r.patient_full_name,
            "date_of_death": r.date_of_death,
            "cause_of_death": r.cause_of_death,
            "service_name": r.service_name,
            "archived_at": r.archived_at,
        }
        for r in qs
    ]
