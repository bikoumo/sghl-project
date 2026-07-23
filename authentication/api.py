from ninja import Router
import os
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
    LoginInputSchema, LoginOutputSchema, VerifyMFAInputSchema, ResendMFAInputSchema,
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


def _smtp_credentials_ready() -> bool:
    """True uniquement si un envoi SMTP réel est possible."""
    backend = getattr(settings, 'EMAIL_BACKEND', '')
    if 'smtp.EmailBackend' not in backend:
        return False
    return bool(settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD and settings.EMAIL_HOST)


def _send_mfa_email(user, code: str, recipient: str | None = None) -> bool:
    """Envoie l'OTP par email. Retourne True si expédié, False sinon (sans planter)."""
    recipient = (recipient or user.email) or os.environ.get('TEST_MFA_RECIPIENT', None)
    if not recipient:
        return False

    # Backend console / file = pas de livraisons réelles → déclencher le fallback UI
    if not _smtp_credentials_ready():
        return False

    try:
        import smtplib
        from django.core.mail import send_mail

        subject = '[SGHL] Code de vérification (OTP)'
        message = (
            f"Bonjour {user.first_name or user.username},\n\n"
            f"Votre code de vérification est : {code}\n"
            f"Il est valable 5 minutes.\n\nSGHL"
        )
        sent = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
            [recipient],
            fail_silently=False,
        )
        return sent > 0
    except smtplib.SMTPAuthenticationError:
        print(
            "[SGHL MFA CRITIQUE] Authentification SMTP refusée par Gmail.\n"
            "  -> Vérifie que le mot de passe d'application dans .env est correct (sans espaces).\n"
            "  -> Le mot de passe standard Gmail ne fonctionne PAS, il faut un mot de passe d'application.\n"
            "  -> Va sur https://myaccount.google.com/apppasswords pour en générer un.",
            flush=True,
        )
        return False
    except smtplib.SMTPException as exc:
        print(f"[SGHL MFA ERREUR SMTP] {exc}", flush=True)
        return False
    except Exception as exc:
        print(
            f"[SGHL MFA ERREUR] Echec envoi email OTP vers {recipient}:\n"
            f"  Type: {type(exc).__name__}\n"
            f"  Detail: {exc}\n"
            f"  EMAIL_HOST={settings.EMAIL_HOST}\n"
            f"  EMAIL_PORT={settings.EMAIL_PORT}\n"
            f"  EMAIL_USE_TLS={settings.EMAIL_USE_TLS}\n"
            f"  EMAIL_HOST_USER={settings.EMAIL_HOST_USER}\n"
            f"  EMAIL_HOST_PASSWORD set={'OUI' if settings.EMAIL_HOST_PASSWORD else 'NON'}",
            flush=True,
        )
        return False


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

    if not user.check_password(data.password):
        raise HttpError(401, "Email ou mot de passe incorrect.")

    # Le rôle UI est uniquement vérifié (jamais écrit en base)
    from authentication.roles import canonicalize_role, role_label

    if data.role:
        requested_role = canonicalize_role(data.role)
        if requested_role and requested_role != user.role:
            raise HttpError(
                403,
                f"Rôle incorrect. Ce compte est enregistré en tant que {role_label(user.role)}.",
            )

    # Le service n'est plus réécrit au login (assignation admin / seed uniquement)
    if data.service and user.role == 'DOCTOR':
        requested = (data.service or '').strip()
        current = getattr(user.service, 'code', None) or getattr(user.service, 'name', None)
        if requested and current and requested.upper() not in {str(current).upper(), getattr(user.service, 'name', '').upper()}:
            raise HttpError(
                403,
                f"Service incorrect. Ce médecin est rattaché à {current}.",
            )

    if user.is_mfa_enabled:
        submitted_email = getattr(data, 'username', None) or user.email
        return _issue_mfa_challenge(user, recipient=submitted_email)

    return _issue_auth_response(user)


ADMIN_EMAIL = "bikoumoutheresa@gmail.com"


def _issue_mfa_challenge(user, recipient: str | None = None) -> dict:
    code = str(random.randint(100000, 999999))
    _store_mfa_code(user, code)

    submitted_email = recipient or user.email

    # --- MFA INTELLIGENTE ---
    # Pour l'admin (bikoumoutheresa@gmail.com) : tenter l'envoi SMTP réel
    # Si l'envoi échoue, afficher le code dans la console (fallback)
    # Pour les autres utilisateurs : affichage console uniquement (fallback UI)
    is_admin = (user.email or "").strip().lower() == ADMIN_EMAIL

    if is_admin:
        # Tentative d'envoi SMTP réel pour l'admin
        email_sent = _send_mfa_email(user, code, recipient=submitted_email)
        if not email_sent:
            # Si SMTP échoue, fallback console pour ne pas bloquer l'admin
            _log_mfa_code_to_console(user.username, code)
        return {
            "message": "Code envoyé par email" if email_sent else "Code généré (fallback console)",
            "requires_mfa": True,
            "username": user.username,
            "email_sent": email_sent,
            "fallback_code": None if email_sent else code,
        }
    else:
        # Autres utilisateurs : comportement actuel (code visible dans console/UI)
        _log_mfa_code_to_console(user.username, code)
        email_sent = _send_mfa_email(user, code, recipient=submitted_email)
        return {
            "message": "Code généré" if not email_sent else "Code envoyé par email",
            "requires_mfa": True,
            "username": user.username,
            "email_sent": email_sent,
            "fallback_code": None if email_sent else code,
        }


@router.post("/resend-mfa/", response=LoginOutputSchema)
def resend_mfa(request, data: ResendMFAInputSchema):
    """Renvoie un nouveau code OTP (email ou fallback UI)."""
    user = User.objects.filter(Q(username=data.username) | Q(email=data.username)).first()
    if not user:
        raise HttpError(400, "Utilisateur introuvable.")
    if not user.is_mfa_enabled:
        raise HttpError(400, "MFA non activée pour ce compte.")
    return _issue_mfa_challenge(user, recipient=user.email)


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

    dev_bypass = os.environ.get('DEV_MFA_BYPASS', '').strip().lower() in {'1', 'true', 'yes'}
    if dev_bypass and str(data.code or "").strip() == "000000":
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


@router.post(
    "/register-patient/",
    auth=RoleBasedAuth(allowed_roles=["DG", "SECRETARY_GENERAL", "SECRETARY_SERVICE", "DOCTOR"]),
)
def register_patient(request, payload: PatientRegisterInputSchema):
    username = (payload.username or "").strip()
    if not username:
        raise HttpError(400, "Le nom d'utilisateur est obligatoire.")
    if User.objects.filter(username=username).exists():
        raise HttpError(400, "Ce nom d'utilisateur est déjà pris.")

    gender = (payload.gender or "").strip().upper()
    if gender not in {"M", "F", "O"}:
        raise HttpError(400, "Genre invalide. Utilisez M, F ou O.")

    if payload.birth_date > timezone.localdate():
        raise HttpError(400, "La date de naissance ne peut pas être dans le futur.")

    if len(payload.password or "") < 6:
        raise HttpError(400, "Le mot de passe doit contenir au moins 6 caractères.")

    email = (getattr(payload, 'email', None) or '').strip() or None
    if email and User.objects.filter(email=email).exists():
        raise HttpError(400, "Cet email est déjà utilisé.")

    patient = User.objects.create_user(
        username=username,
        password=payload.password,
        email=email,
        first_name=(payload.first_name or "").strip(),
        last_name=(payload.last_name or "").strip(),
        role="PATIENT",
        gender=gender,
        birth_date=payload.birth_date,
        phone=(payload.phone or "").strip() or None,
        is_active=True,
        is_mfa_enabled=False,
    )

    patient.matricule = f"PT-{timezone.now().year}-{patient.id:04d}"
    patient.save(update_fields=["matricule"])

    return {
        "status": "success",
        "message": "Dossier Patient créé avec succès.",
        "patient": {
            "id": patient.id,
            "matricule": patient.matricule,
            "username": patient.username,
            "gender": patient.gender,
            "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
        },
    }