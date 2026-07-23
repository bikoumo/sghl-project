from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime

# =====================================================================
# ÉTAPE 1 : CONNEXION CLASSIQUE
# =====================================================================

class LoginInputSchema(BaseModel):
    username: str
    password: str
    role: Optional[str] = None
    service: Optional[str] = None

class LoginOutputSchema(BaseModel):
    message: str
    requires_mfa: bool
    username: str
    status: Optional[str] = None
    role: Optional[str] = None
    service: Optional[str] = None
    token: Optional[str] = None
    user_id: Optional[int] = None
    # MFA : True si l'OTP a été expédié par email ; sinon fallback UI
    email_sent: Optional[bool] = None
    # Code OTP affiché uniquement quand l'email a échoué (secours)
    fallback_code: Optional[str] = None

# =====================================================================
# ÉTAPE 2 : VÉRIFICATION DU CODE (MFA)
# =====================================================================

class VerifyMFAInputSchema(BaseModel):
    username: str
    code: str


class ResendMFAInputSchema(BaseModel):
    username: str

# =====================================================================
# ENREGISTREMENT PATIENT
# =====================================================================

class PatientRegisterInputSchema(BaseModel):
    username: str
    password: str         # Ajouté ici pour correspondre à votre API
    first_name: str
    last_name: str
    gender: str           # M ou F
    birth_date: date      # Utilisation du type 'date' pour une meilleure validation
    phone: Optional[str] = None
    email: Optional[str] = None

class ServiceOutSchema(BaseModel):
    id: int
    name: str
    code: str
    building: Optional[str] = None

class ChatMessageCreateSchema(BaseModel):
    content: str
    recipient_service_id: Optional[int] = None
    is_urgent: bool = False

class ChatMessageOutSchema(BaseModel):
    id: int
    sender: str
    service: Optional[str] = None
    content: str
    is_urgent: bool
    created_at: datetime