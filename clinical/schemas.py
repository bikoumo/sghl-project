from ninja import Schema
from datetime import datetime
from typing import List, Optional

# ==========================================
# 1. SCHÉMAS POUR LES LITS
# ==========================================
class BedOutSchema(Schema):
    id: int
    number: str
    is_occupied: bool
    room_number: str
    service_name: str


class BedListItemSchema(Schema):
    id: int
    number: str
    is_occupied: bool
    status: str
    room_id: Optional[int] = None
    room_number: str
    room_type: Optional[str] = None
    service_name: str
    service_code: Optional[str] = None
    patient_id: Optional[int] = None
    patient_name: Optional[str] = None
    patient_matricule: Optional[str] = None
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    hospitalization_id: Optional[int] = None
    admission_date: Optional[datetime] = None
    reason: Optional[str] = None


class BedAdmitSchema(Schema):
    patient_id: int
    doctor_id: Optional[int] = None
    reason: str

# ==========================================
# 2. SCHÉMAS POUR LES CONSULTATIONS & PATIENTS
# ==========================================
class ConsultationCreateSchema(Schema):
    patient_id: int
    symptoms: str
    diagnosis: str
    prescription: Optional[str] = None
    requires_hospitalization: bool = False
    bed_id: Optional[int] = None
    doctor_id: Optional[int] = None


class ConsultationDetailSchema(Schema):
    id: int
    doctor_username: str
    date: datetime
    symptoms: str
    diagnosis: str
    prescription: Optional[str] = None
    requires_hospitalization: bool


class PatientMedicalRecordSchema(Schema):
    patient_id: int
    patient_username: str
    consultations: List[ConsultationDetailSchema]


class PatientOutSchema(Schema):
    id: int
    matricule: str
    nom: str
    prenom: str
    genre: str
    dateNaissance: str
    telephone: str
    statut: str


# ==========================================
# 3. SCHÉMAS POUR LA PHARMACIE & FACTURATION
# ==========================================
class MedicationOutSchema(Schema):
    id: int
    name: str
    stock_quantity: int
    price_per_unit: float


class DispenseMedicationInputSchema(Schema):
    medication_id: int
    quantity: int


class InvoiceOutSchema(Schema):
    id: int
    patient_username: str
    total_amount: float
    status: str
    created_at: datetime
    label: Optional[str] = None
    remaining: Optional[float] = None


class PayInvoiceSchema(Schema):
    method: str
    phone: Optional[str] = None
    amount: Optional[float] = None
    card_last_four: Optional[str] = None
    card_expiry: Optional[str] = None


class InvoiceLineSchema(Schema):
    label: str
    quantity: int = 1
    unit_price: float


class InvoiceCreateSchema(Schema):
    patient_id: int
    label: str = 'Facture'
    lines: List[InvoiceLineSchema]


# ==========================================
# 4. SCHÉMAS POUR LES RENDEZ-VOUS (PLANNING)
# ==========================================
class AppointmentCreateSchema(Schema):
    doctor_id: int
    appointment_date: datetime
    patient_id: Optional[int] = None
    service_id: Optional[int] = None
    notes: Optional[str] = None


class AppointmentStatusSchema(Schema):
    status: str


class AppointmentOutSchema(Schema):
    id: int
    patient_username: str
    doctor_username: str
    appointment_date: datetime
    notes: Optional[str] = None
    status: str
    created_at: datetime
    service_name: Optional[str] = None


class StatsOutSchema(Schema):
    date: str
    consultations: int = 0
    beds_occupied: int = 0
    beds_total: int = 0
    emergencies: int = 0
    low_stock_count: int = 0
    appointments_count: int = 0
    hospitalized_count: int = 0
    patients_count: int = 0
    invoices_pending: int = 0


class ServiceMapOutSchema(Schema):
    id: int
    name: str
    code: str
    building_name: Optional[str] = None
    is_open_h24: bool = False
    location_lat: Optional[float] = None
    location_long: Optional[float] = None


class RoomOutSchema(Schema):
    id: int
    number: str
    room_type: str
    service: int
    service_name: Optional[str] = None


class PediatricRecordInSchema(Schema):
    nom: str
    date_naissance: str
    poids: float
    taille: Optional[int] = None
    groupe_sanguin: Optional[str] = None
    vaccin_date: str


class PediatricRecordOutSchema(Schema):
    id: int
    nom: str
    date_naissance: str
    poids: float
    taille: Optional[int] = None
    groupe_sanguin: Optional[str] = None
    vaccin_date: str
    status: str


class MaternityRecordInSchema(Schema):
    nom: str
    prenom: str
    date_terme: str
    next_visit: str
    status: Optional[str] = 'Suivi en cours'
    notes: Optional[str] = None


class MaternityRecordOutSchema(Schema):
    id: int
    nom: str
    prenom: str
    date_terme: str
    next_visit: str
    status: str
    notes: Optional[str] = None


class HospitalizationOutSchema(Schema):
    id: int
    patient_id: int
    patient_name: str
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    bed_id: int
    bed_number: str
    service_name: str
    reason: str
    start_date: datetime
    is_active: bool


class ExamRequestInSchema(Schema):
    patient_id: int
    title: str
    description: Optional[str] = None


class ExamResultInSchema(Schema):
    result_text: str
    conclusion: Optional[str] = None


class ExamRequestOutSchema(Schema):
    id: int
    patient_id: int
    patient_name: str
    title: str
    description: Optional[str] = None
    status: str
    requested_at: datetime
    result_text: Optional[str] = None
    conclusion: Optional[str] = None


# ==========================================
# 8. SCHÉMAS POUR LA GESTION DES DÉCÈS
# ==========================================
class DeathRecordCreateSchema(Schema):
    patient_id: int
    cause: str
    service_id: Optional[int] = None
    complications: Optional[str] = None


class DeathRecordOutSchema(Schema):
    id: int
    patient_id: int
    patient_name: str
    patient_matricule: str
    reported_by_name: Optional[str] = None
    service_id: Optional[int] = None
    service_name: Optional[str] = None
    cause: Optional[str] = None
    complications: Optional[str] = None
    is_validated: bool
    is_dossier_purged: bool
    validated_at: Optional[datetime] = None
    created_at: datetime


class DeathStatsSchema(Schema):
    total_deaths: int = 0
    deaths_this_month: int = 0
    deaths_today: int = 0
    by_service: List[dict] = []
    top_causes: List[dict] = []


class ArchivedRecordOutSchema(Schema):
    id: int
    original_username: str
    original_matricule: str
    patient_full_name: str
    date_of_death: Optional[datetime] = None
    cause_of_death: str
    service_name: str
    archived_at: datetime
