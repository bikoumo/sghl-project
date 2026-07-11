from django.core.cache import cache
from ninja import Router, Schema
from ninja.errors import HttpError
from typing import List, Optional
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import (
    Appointment, Consultation, Hospitalization, Provision,
    SupportTask, Service, Building, Room, Bed
)

User = get_user_model()
router = Router(tags=["Clinical - SGHL"])


# ==========================================
# SCHEMAS
# ==========================================
class StatsOutSchema(Schema):
    date: str
    appointments_count: int
    hospitalized_count: int
    low_stock_count: int


class ProvisionOutSchema(Schema):
    id: int
    name: str
    quantity: int
    min_quantity_alert: int
    service_name: str
    is_low_stock: bool


class AppointmentOutSchema(Schema):
    id: int
    patient__username: str
    doctor__username: str
    appointment_date: str
    status: str
    service__name: Optional[str] = None


class VerifyCodeResponseSchema(Schema):
    token: str
    role: str
    user_id: int
    username: str
    service_id: Optional[int] = None
    service_name: Optional[str] = None
    message: str


# ==========================================
# HELPER FUNCTION
# ==========================================
def get_filtered_queryset(model_qs, user):
    """Filtrer les données selon le rôle de l'utilisateur"""
    if user.role in ['DG', 'SECRETARY_GENERAL']:
        return model_qs
    elif user.role == 'SECRETARY_SERVICE':
        model_name = model_qs.model.__name__
        if model_name == 'Consultation':
            return model_qs.filter(doctor__service=user.service)
        elif model_name == 'Hospitalization':
            return model_qs.filter(bed__room__service=user.service)
        elif hasattr(model_qs.model, 'service'):
            return model_qs.filter(service=user.service)
    elif user.role == 'DOCTOR':
        if hasattr(model_qs.model, 'doctor'):
            return model_qs.filter(doctor=user)
    return model_qs.none()


# ==========================================
# API ENDPOINTS
# ==========================================

@router.post("/verify-code", response=VerifyCodeResponseSchema)
def verify_code(request, user_id: int, code: str):
    """Vérifier le code MFA et retourner le rôle + service_id"""
    stored_code = cache.get(f"mfa_code_{user_id}")
    
    if stored_code and str(code) == str(stored_code):
        try:
            user = User.objects.get(id=user_id)
            cache.delete(f"mfa_code_{user_id}")
            
            return VerifyCodeResponseSchema(
                token="jwt_token_placeholder",
                role=user.role,
                user_id=user.id,
                username=user.username,
                service_id=user.service_id if user.service else None,
                service_name=user.service.name if user.service else None,
                message="Authentification réussie"
            )
        except User.DoesNotExist:
            raise HttpError(404, "Utilisateur introuvable")
    
    raise HttpError(400, "Code incorrect ou expiré")


@router.get("/stats", response=StatsOutSchema)
def get_stats(request):
    """Récupérer les statistiques du dashboard"""
    user = request.auth_user
    today = timezone.now().date()
    
    # RDV confirmés du jour
    appointments_qs = Appointment.objects.filter(
        appointment_date__date=today,
        status='CONFIRMED'
    )
    if user.role == 'SECRETARY_SERVICE':
        appointments_qs = appointments_qs.filter(service=user.service)
    appointments_count = appointments_qs.count()
    
    # Hospitalisations actives
    hosp_qs = Hospitalization.objects.filter(is_active=True)
    if user.role == 'SECRETARY_SERVICE':
        hosp_qs = hosp_qs.filter(bed__room__service=user.service)
    hospitalized_count = hosp_qs.count()
    
    # Stocks faibles
    low_stock_qs = Provision.objects.filter(Q(quantity__lt=10))
    if user.role == 'SECRETARY_SERVICE':
        low_stock_qs = low_stock_qs.filter(service=user.service)
    low_stock_count = low_stock_qs.count()
    
    return StatsOutSchema(
        date=today.isoformat(),
        appointments_count=appointments_count,
        hospitalized_count=hospitalized_count,
        low_stock_count=low_stock_count
    )


@router.get("/appointments", response=List[AppointmentOutSchema])
def list_appointments(request):
    """Lister les rendez-vous avec filtrage par rôle"""
    user = request.auth_user
    
    qs = Appointment.objects.select_related('patient', 'doctor', 'service').all()
    qs = get_filtered_queryset(qs, user)
    
    return [
        AppointmentOutSchema(
            id=a.id,
            patient__username=a.patient.username,
            doctor__username=a.doctor.username,
            appointment_date=a.appointment_date.isoformat(),
            status=a.status,
            service__name=a.service.name if a.service else None
        )
        for a in qs.order_by('-appointment_date')
    ]


@router.post("/appointments")
def create_appointment(request, patient_id: int, doctor_id: int, appointment_date: str, service_id: Optional[int] = None):
    """Créer un nouveau rendez-vous avec validation métier"""
    user = request.auth_user
    
    # Vérifier les permissions
    if user.role not in ['DG', 'SECRETARY_GENERAL', 'SECRETARY_SERVICE', 'DOCTOR']:
        raise HttpError(403, "Permissions insuffisantes")
    
    # Parser la date
    from datetime import datetime
    try:
        apt_date = datetime.fromisoformat(appointment_date)
    except:
        raise HttpError(400, "Format date invalide")
    
    # Créer et valider l'appointment
    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=apt_date,
        service_id=service_id,
        created_by=user
    )
    
    try:
        appointment.full_clean()
        appointment.save()
        return {"id": appointment.id, "message": "Rendez-vous créé avec succès"}
    except Exception as e:
        raise HttpError(400, str(e))


@router.get("/provisions", response=List[ProvisionOutSchema])
def list_provisions(request):
    """Lister les provisions avec alertes stocks"""
    user = request.auth_user
    
    qs = Provision.objects.select_related('service').all()
    qs = get_filtered_queryset(qs, user)
    
    return [
        ProvisionOutSchema(
            id=p.id,
            name=p.name,
            quantity=p.quantity,
            min_quantity_alert=p.min_quantity_alert,
            service_name=p.service.name,
            is_low_stock=p.quantity < p.min_quantity_alert
        )
        for p in qs
    ]


@router.post("/provisions")
def create_provision(request, name: str, quantity: int, min_quantity_alert: int, service_id: int):
    """Créer une nouvelle provision"""
    user = request.auth_user
    
    if user.role not in ['DG', 'SECRETARY_GENERAL', 'SECRETARY_SERVICE']:
        raise HttpError(403, "Permissions insuffisantes")
    
    provision = Provision(
        name=name,
        quantity=quantity,
        min_quantity_alert=min_quantity_alert,
        service_id=service_id,
        created_by=user
    )
    provision.save()
    
    return {"id": provision.id, "message": "Provision créée avec succès"}


@router.get("/hospitalizations")
def list_hospitalizations(request):
    """Lister les hospitalisations actives"""
    user = request.auth_user
    
    qs = Hospitalization.objects.select_related(
        'patient', 'doctor', 'bed__room__service'
    ).filter(is_active=True)
    qs = get_filtered_queryset(qs, user)
    
    return [
        {
            "id": h.id,
            "patient__username": h.patient.username,
            "doctor__username": h.doctor.username,
            "bed__number": h.bed.number,
            "service_name": h.bed.room.service.name,
            "start_date": h.start_date.isoformat(),
            "reason": h.reason
        }
        for h in qs.order_by('-start_date')
    ]


@router.get("/support-tasks")
def list_support_tasks(request):
    """Lister les tâches de support"""
    user = request.auth_user
    
    qs = SupportTask.objects.select_related('service', 'assigned_to').all()
    qs = get_filtered_queryset(qs, user)
    
    return [
        {
            "id": t.id,
            "task_type": t.get_task_type_display(),
            "status": t.get_status_display(),
            "service_name": t.service.name,
            "assigned_to": t.assigned_to.username if t.assigned_to else None,
            "location_lat": t.location_lat,
            "location_long": t.location_long,
            "created_at": t.created_at.isoformat()
        }
        for t in qs.order_by('-created_at')
    ]


@router.get("/consultations")
def list_consultations(request):
    """Lister les consultations"""
    user = request.auth_user
    
    qs = Consultation.objects.select_related('patient', 'doctor').all()
    qs = get_filtered_queryset(qs, user)
    
    return [
        {
            "id": c.id,
            "patient__username": c.patient.username,
            "doctor__username": c.doctor.username,
            "date": c.date.isoformat(),
            "symptoms": c.symptoms,
            "diagnosis": c.diagnosis,
            "prescription": c.prescription
        }
        for c in qs.order_by('-date')
    ]


# NOTES IMPORTANTES :
# - Les endpoints sont sécurisés par auth (RoleBasedAuth en place)
# - Le filtrage par rôle est automatique via get_filtered_queryset()
# - Tous les creates sont tracés (created_by)
# - Les validations métier (2h, quota) se font dans le model.clean()
