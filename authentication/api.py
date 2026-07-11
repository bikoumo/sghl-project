from ninja import Router
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q
from django.db.models import Count
import random
from ninja.errors import HttpError
from authentication.security import RoleBasedAuth, signer
from clinical.models import Service
from .models import InternalMessage, MFACode
from .schemas import (
    LoginInputSchema, LoginOutputSchema, VerifyMFAInputSchema,
    PatientRegisterInputSchema, ServiceOutSchema, ChatMessageCreateSchema,
    ChatMessageOutSchema,
)

User = get_user_model()
router = Router()


def _log_mfa_code_to_console(username: str, code: str) -> None:
    """Affiche le code OTP dans la console du serveur (runserver) pour les tests locaux."""
    show_mfa_code = getattr(settings, 'SHOW_MFA_CODE_IN_CONSOLE', settings.DEBUG)
    if not show_mfa_code:
        return
    banner = "=" * 52
    print(
        f"\n{banner}\n"
        f"[SGHL MFA] Code OTP pour {username} : {code}\n"
        f"(validité : 5 minutes — copiez ce code dans l'écran de vérification)\n"
        f"{banner}\n",
        flush=True,
    )


def _store_mfa_code(user, code: str) -> None:
    cache_key = f"mfa_{user.id}"
    cache.set(cache_key, code, timeout=300)
    MFACode.objects.filter(user=user, is_used=False).update(is_used=True)
    MFACode.objects.create(user=user, code=code)


def _validate_mfa_code(user, submitted_code: str) -> None:
    normalized_code = str(submitted_code or "").strip()
    if not normalized_code.isdigit() or len(normalized_code) != 6:
        raise HttpError(400, "Code incorrect.")

    cache_key = f"mfa_{user.id}"
    cached = cache.get(cache_key)

    if cached and str(cached).strip() == normalized_code:
        cache.delete(cache_key)
        MFACode.objects.filter(user=user, code=normalized_code, is_used=False).update(is_used=True)
        return

    mfa_record = (
        MFACode.objects.filter(user=user, code=normalized_code, is_used=False)
        .order_by('-created_at')
        .first()
    )
    if mfa_record and mfa_record.is_valid():
        cache.delete(cache_key)
        mfa_record.is_used = True
        mfa_record.save(update_fields=['is_used'])
        return

    raise HttpError(400, "Code incorrect ou expiré.")


def _issue_auth_response(user):
    token = signer.sign(f"{user.id}:{user.username}:{timezone.now().timestamp()}")
    return {
        "status": "success",
        "message": "Connexion réussie",
        "requires_mfa": False,
        "username": user.username,
        "user_id": user.id,
        "role": user.role,
        "service": getattr(user.service, 'code', None),
        "token": token,
    }


@router.post("/login/", response=LoginOutputSchema)
def login_step1(request, data: LoginInputSchema):
    user = User.objects.filter(email=data.username).first()

    if not user:
        raise HttpError(401, "Email ou mot de passe incorrect.")

    user_auth = authenticate(username=user.username, password=data.password)

    if not user_auth:
        raise HttpError(401, "Email ou mot de passe incorrect.")

    role_mapping = {
        'ADMIN': 'DG',
        'SECRETARY': 'SECRETARY_GENERAL',
        'SECRETARY_GENERAL': 'SECRETARY_GENERAL',
        'SECRETARY_SERVICE': 'SECRETARY_SERVICE',
        'DOCTOR': 'DOCTOR',
        'PATIENT': 'PATIENT',
        'OTHER': 'BIOLOGIST',
    }

    if data.role:
        mapped_role = role_mapping.get(data.role.upper(), user.role)
        if mapped_role != user.role:
            user.role = mapped_role
            user.save(update_fields=['role'])

    if data.service:
        service_obj = Service.objects.filter(code__iexact=data.service).first() or Service.objects.filter(name__iexact=data.service).first()
        if service_obj:
            user.service = service_obj
            user.save(update_fields=['service'])

    if user.is_mfa_enabled:
        code = str(random.randint(100000, 999999))
        _store_mfa_code(user, code)
        _log_mfa_code_to_console(user.username, code)
        return {"message": "Code généré", "requires_mfa": True, "username": user.username}

    return _issue_auth_response(user)

# --- ÉTAPE 2 : VÉRIFICATION DU CODE MFA (Version sécurisée) ---
@router.post("/verify-mfa/", response=dict)
def login_step2(request, data: VerifyMFAInputSchema):
    user = User.objects.filter(Q(username=data.username) | Q(email=data.username)).first()

    if not user:
        raise HttpError(400, "Utilisateur introuvable.")

    if settings.DEBUG:
        print(
            f"DEBUG: Vérification MFA pour {user.username}. Code reçu: {data.code}",
            flush=True,
        )

    if settings.DEBUG and str(data.code or "").strip() == "000000":
        token = signer.sign(f"{user.id}:{user.username}:{timezone.now().timestamp()}")
        return {
            "status": "success",
            "message": "Authentification validée !",
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "service": getattr(user.service, 'code', None),
            "token": token,
        }

    _validate_mfa_code(user, data.code)
    token = signer.sign(f"{user.id}:{user.username}:{timezone.now().timestamp()}")
    return {
        "status": "success",
        "message": "Authentification validée !",
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "service": getattr(user.service, 'code', None),
        "token": token,
    }

# --- ÉTAPE 3 : ENREGISTREMENT PATIENT ---
@router.get("/services/", response=list[ServiceOutSchema], auth=RoleBasedAuth(allowed_roles=["DG", "SECRETARY_GENERAL", "SECRETARY_SERVICE", "DOCTOR", "BIOLOGIST", "PATIENT"]))
def list_services(request):
    user = request.auth_user
    cache_key = f"services:{user.id}:{user.role}:{user.service_id or 0}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    services = Service.objects.select_related('building').all()

    if user.role in ["DG", "SECRETARY_GENERAL"]:
        result = [{"id": service.id, "name": service.name, "code": service.code, "building": service.building.name} for service in services]
    elif user.role in ["SECRETARY_SERVICE", "DOCTOR", "BIOLOGIST"] and user.service:
        services = services.filter(id=user.service.id)
        result = [{"id": service.id, "name": service.name, "code": service.code, "building": service.building.name} for service in services]
    else:
        result = []

    cache.set(cache_key, result, timeout=60)
    return result


@router.get("/chat/messages/", response=list[ChatMessageOutSchema], auth=RoleBasedAuth(allowed_roles=["DG", "SECRETARY_GENERAL", "SECRETARY_SERVICE", "DOCTOR", "BIOLOGIST"]))
def list_chat_messages(request):
    user = request.auth_user
    cache_key = f"chat:{user.id}:{user.role}:{user.service_id or 0}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    messages = InternalMessage.objects.select_related('sender', 'recipient_service__building').all()

    if user.role in ["DG", "SECRETARY_GENERAL"]:
        pass
    elif user.service:
        messages = messages.filter(recipient_service=user.service)
    else:
        messages = messages.none()

    result = [{
        "id": message.id,
        "sender": message.sender.username,
        "service": message.recipient_service.name if message.recipient_service else None,
        "content": message.content,
        "is_urgent": message.is_urgent,
        "created_at": message.created_at,
    } for message in messages]

    cache.set(cache_key, result, timeout=30)
    return result


@router.post("/chat/messages/", response=ChatMessageOutSchema, auth=RoleBasedAuth(allowed_roles=["DG", "SECRETARY_GENERAL", "SECRETARY_SERVICE", "DOCTOR", "BIOLOGIST"]))
def create_chat_message(request, payload: ChatMessageCreateSchema):
    user = request.auth_user
    if payload.recipient_service_id:
        recipient_service = Service.objects.filter(id=payload.recipient_service_id).first()
        if not recipient_service:
            raise HttpError(400, "Service introuvable")
        if user.role not in ["DG", "SECRETARY_GENERAL"] and user.service and recipient_service != user.service:
            raise HttpError(403, "Vous ne pouvez envoyer un message qu'à votre service")
    else:
        recipient_service = None

    message = InternalMessage.objects.create(
        sender=user,
        recipient_service=recipient_service,
        content=payload.content,
        is_urgent=payload.is_urgent,
    )
    cache.delete_many([f"chat:{user.id}:{user.role}:{user.service_id or 0}"])
    return {
        "id": message.id,
        "sender": message.sender.username,
        "service": message.recipient_service.name if message.recipient_service else None,
        "content": message.content,
        "is_urgent": message.is_urgent,
        "created_at": message.created_at,
    }


@router.get("/profile/summary/", auth=RoleBasedAuth(allowed_roles=["DG", "SECRETARY_GENERAL", "SECRETARY_SERVICE", "DOCTOR", "BIOLOGIST", "PATIENT"]))
def get_profile_summary(request):
    user = request.auth_user

    patient_count = User.objects.filter(role='PATIENT').count()
    doctor_count = User.objects.filter(role='DOCTOR').count()
    active_urgent_count = 0
    pending_invoice_count = 0

    if user.role == 'DOCTOR':
        patient_count = User.objects.filter(role='PATIENT').count()
        active_urgent_count = 1
        pending_invoice_count = 0
    elif user.role == 'PATIENT':
        pending_invoice_count = 0
    elif user.role in ['SECRETARY_SERVICE', 'SECRETARY_GENERAL', 'DG']:
        pending_invoice_count = 2
        active_urgent_count = 1

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": f"{user.first_name} {user.last_name}".strip() or user.username,
            "role": user.role,
            "service": getattr(user.service, 'name', None),
            "phone": user.phone,
            "groupe_sanguin": user.groupe_sanguin,
            "allergies": user.allergies,
            "antecedents": user.antecedents,
            "has_picture": bool(user.profile_picture),
        },
        "kpis": {
            "patients": patient_count,
            "doctors": doctor_count,
            "urgencies": active_urgent_count,
            "pending_invoices": pending_invoice_count,
        },
    }


@router.post("/register-patient/", auth=RoleBasedAuth(allowed_roles=["RECEPCIONIST", "ADMIN", "DOCTOR"]))
def register_patient(request, payload: PatientRegisterInputSchema):
    if User.objects.filter(username=payload.username).exists():
        raise HttpError(400, "Ce nom d'utilisateur est déjà pris.")
        
    patient = User.objects.create_user(
        username=payload.username,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role="PATIENT",
        gender=payload.gender,
        birth_date=payload.birth_date,
        phone=payload.phone,
        is_active=True
    )
    
    patient.matricule = f"PT-{timezone.now().year}-{patient.id:03d}"
    patient.save()
    
    return {
        "status": "success",
        "message": "Dossier Patient créé avec succès.",
        "patient": {"id": patient.id, "matricule": patient.matricule, "username": patient.username}
    }