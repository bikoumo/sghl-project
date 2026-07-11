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

# ==========================================
# 4. SCHÉMAS POUR LES RENDEZ-VOUS (PLANNING)
# ==========================================
class AppointmentCreateSchema(Schema):
    doctor_id: int
    appointment_date: datetime
    reason: str

class AppointmentOutSchema(Schema):
    id: int
    patient_username: str
    doctor_username: str
    appointment_date: datetime
    reason: str
    status: str
    created_at: datetime

class StatsOutSchema(Schema):
    date: str
    appointments_count: int
    hospitalized_count: int
    low_stock_count: int