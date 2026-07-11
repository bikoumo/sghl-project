from ninja import Schema
from datetime import datetime
from typing import Optional

# ==========================================
# 1. GESTION DES FACTURES
# ==========================================
class InvoiceOutSchema(Schema):
    id: int
    patient_username: str
    total_amount: float
    status: str
    created_at: datetime

# ==========================================
# 2. GESTION DES PAIEMENTS
# ==========================================
class PaymentCreateSchema(Schema):
    invoice_id: int
    amount: float
    method: str  # ex: "CASH", "CARD", "MOBILE_MONEY"

class PaymentOutSchema(Schema):
    id: int
    invoice_id: int
    amount: float
    method: str
    created_at: datetime
    created_by_username: str

# ==========================================
# 3. LOGISTIQUE & STOCKS
# ==========================================
class StockUpdateSchema(Schema):
    medication_id: int
    new_quantity: int
    reason: Optional[str] = None