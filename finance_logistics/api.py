from ninja import Router, Schema
from typing import List, Optional
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from ninja.errors import HttpError
import csv

from authentication.security import RoleBasedAuth
from authentication.roles import ADMIN_ROLES, STAFF_ROLES, PHARMACY_ROLES
from clinical.models import Hospitalization
from .models import Medication, StockBatch, Invoice
from .services import (
    serialize_medication,
    process_pharmacy_purchase,
    available_stock,
)

router = Router(tags=['Finance & Pharmacie'])
User = get_user_model()


class PharmacyLineSchema(Schema):
    medication_id: int
    quantity: int


class PharmacyPurchaseSchema(Schema):
    patient_id: int
    items: List[PharmacyLineSchema]
    hospitalization_id: Optional[int] = None
    mark_paid: bool = False


class StockRestockSchema(Schema):
    medication_id: int
    quantity: int
    batch_number: str
    expiry_date: str  # YYYY-MM-DD


@router.get('/staff/', auth=RoleBasedAuth(allowed_roles=[*ADMIN_ROLES, 'SECRETARY_GENERAL']))
def list_staff(request):
    qs = User.objects.filter(role__in=STAFF_ROLES).order_by('last_name', 'first_name')
    return [
        {
            'id': u.id,
            'username': u.username,
            'email': u.email or '',
            'role': u.role,
            'full_name': f"{u.first_name} {u.last_name}".strip() or u.username,
            'is_active': u.is_active,
        }
        for u in qs
    ]


@router.get('/staff/export', auth=RoleBasedAuth(allowed_roles=[*ADMIN_ROLES, 'SECRETARY_GENERAL']))
def export_staff_csv(request):
    qs = User.objects.filter(role__in=STAFF_ROLES).order_by('id')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="staff.csv"'
    writer = csv.writer(response)
    writer.writerow(['id', 'username', 'email', 'role', 'is_active'])
    for u in qs:
        writer.writerow([u.id, u.username, u.email, u.role, u.is_active])
    return response


@router.get('/medications/', auth=RoleBasedAuth(allowed_roles=PHARMACY_ROLES))
def list_pharmacy_medications(request):
    meds = Medication.objects.all().order_by('name')
    return [serialize_medication(m) for m in meds]


@router.get('/medications/{medication_id}/batches', auth=RoleBasedAuth(allowed_roles=PHARMACY_ROLES))
def list_medication_batches(request, medication_id: int):
    from django.utils import timezone

    medication = get_object_or_404(Medication, id=medication_id)
    today = timezone.localdate()
    batches = StockBatch.objects.filter(medication=medication).order_by('expiry_date')
    return {
        'medication': serialize_medication(medication),
        'batches': [
            {
                'id': b.id,
                'batch_number': b.batch_number,
                'quantity_in_stock': b.quantity_in_stock,
                'expiry_date': b.expiry_date.isoformat(),
                'is_expired': b.expiry_date < today,
            }
            for b in batches
        ],
    }


@router.post('/pharmacy/purchase', auth=RoleBasedAuth(allowed_roles=PHARMACY_ROLES))
def pharmacy_purchase(request, payload: PharmacyPurchaseSchema):
    patient = get_object_or_404(User, id=payload.patient_id, role='PATIENT')
    hospitalization = None
    if payload.hospitalization_id:
        hospitalization = get_object_or_404(
            Hospitalization,
            id=payload.hospitalization_id,
            patient=patient,
            is_active=True,
        )

    items = [{'medication_id': line.medication_id, 'quantity': line.quantity} for line in payload.items]

    try:
        invoice, line_details = process_pharmacy_purchase(
            patient=patient,
            items=items,
            created_by=request.auth_user,
            hospitalization=hospitalization,
            mark_paid=payload.mark_paid,
        )
    except Medication.DoesNotExist:
        raise HttpError(404, 'Médicament introuvable.')
    except ValidationError as exc:
        message = '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)
        raise HttpError(400, message)

    return {
        'status': 'success',
        'message': 'Achat enregistré — stock mis à jour (FIFO).',
        'invoice': {
            'id': invoice.id,
            'patient_id': patient.id,
            'patient_username': patient.username,
            'total_amount': float(invoice.total_amount),
            'amount_paid': float(invoice.amount_paid),
            'status': invoice.status,
            'created_at': invoice.created_at.isoformat(),
        },
        'lines': line_details,
    }


@router.post('/pharmacy/restock', auth=RoleBasedAuth(allowed_roles=PHARMACY_ROLES))
def pharmacy_restock(request, payload: StockRestockSchema):
    from datetime import date

    if payload.quantity <= 0:
        raise HttpError(400, 'La quantité doit être positive.')
    try:
        expiry = date.fromisoformat(payload.expiry_date)
    except ValueError:
        raise HttpError(400, 'Date de péremption invalide (format YYYY-MM-DD).')

    from django.utils import timezone
    if expiry < timezone.localdate():
        raise HttpError(400, 'Impossible d’ajouter un lot déjà périmé.')

    medication = get_object_or_404(Medication, id=payload.medication_id)
    batch_number = (payload.batch_number or '').strip()
    if not batch_number:
        raise HttpError(400, 'Le numéro de lot est obligatoire.')

    batch, created = StockBatch.objects.get_or_create(
        medication=medication,
        batch_number=batch_number,
        defaults={
            'quantity_in_stock': payload.quantity,
            'expiry_date': expiry,
        },
    )
    if not created:
        if batch.expiry_date != expiry:
            raise HttpError(400, 'Ce numéro de lot existe déjà avec une autre date de péremption.')
        batch.quantity_in_stock += payload.quantity
        batch.save(update_fields=['quantity_in_stock'])

    return {
        'status': 'success',
        'message': 'Stock réapprovisionné.',
        'medication': serialize_medication(medication),
        'batch': {
            'id': batch.id,
            'batch_number': batch.batch_number,
            'quantity_in_stock': batch.quantity_in_stock,
            'expiry_date': batch.expiry_date.isoformat(),
        },
        'available_stock': available_stock(medication),
    }


@router.get('/pharmacy/invoices', auth=RoleBasedAuth(allowed_roles=PHARMACY_ROLES))
def list_pharmacy_invoices(request):
    qs = Invoice.objects.select_related('patient').prefetch_related('items__medication').order_by('-created_at')[:50]
    result = []
    for inv in qs:
        result.append({
            'id': inv.id,
            'patient_username': inv.patient.username if inv.patient_id else None,
            'total_amount': float(inv.total_amount),
            'amount_paid': float(inv.amount_paid),
            'status': inv.status,
            'created_at': inv.created_at.isoformat(),
            'items_count': inv.items.count(),
        })
    return result
