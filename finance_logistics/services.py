"""Services métier pharmacie : stock disponible, FIFO, vente."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import Invoice, InvoiceItem, Medication, StockBatch


def available_stock(medication: Medication) -> int:
    today = timezone.localdate()
    total = (
        StockBatch.objects.filter(
            medication=medication,
            quantity_in_stock__gt=0,
            expiry_date__gte=today,
        ).aggregate(total=Sum('quantity_in_stock'))['total']
        or 0
    )
    return int(total)


def next_expiry(medication: Medication):
    today = timezone.localdate()
    batch = (
        StockBatch.objects.filter(
            medication=medication,
            quantity_in_stock__gt=0,
            expiry_date__gte=today,
        )
        .order_by('expiry_date')
        .first()
    )
    return batch.expiry_date if batch else None


def serialize_medication(medication: Medication) -> dict:
    stock = available_stock(medication)
    expiry = next_expiry(medication)
    return {
        'id': medication.id,
        'name': medication.name,
        'code': medication.code,
        'unit_price': float(medication.unit_price),
        'description': medication.description or '',
        'stock_quantity': stock,
        'price_per_unit': float(medication.unit_price),
        'next_expiry': expiry.isoformat() if expiry else None,
        'is_low_stock': stock < 10,
        'is_out_of_stock': stock <= 0,
    }


def decrement_stock_fifo(medication: Medication, quantity: int) -> list[dict]:
    """Décrémente les lots non périmés (FIFO). Retourne le détail des mouvements."""
    if quantity <= 0:
        raise ValidationError('La quantité doit être positive.')

    today = timezone.localdate()
    remaining = quantity
    movements: list[dict] = []

    batches = (
        StockBatch.objects.select_for_update()
        .filter(
            medication=medication,
            quantity_in_stock__gt=0,
            expiry_date__gte=today,
        )
        .order_by('expiry_date', 'id')
    )

    for batch in batches:
        if remaining <= 0:
            break
        take = min(batch.quantity_in_stock, remaining)
        batch.quantity_in_stock -= take
        batch.save(update_fields=['quantity_in_stock'])
        movements.append({
            'batch_number': batch.batch_number,
            'quantity': take,
            'expiry_date': batch.expiry_date.isoformat(),
        })
        remaining -= take

    if remaining > 0:
        raise ValidationError(
            f"Stock insuffisant pour {medication.name} "
            f"(manque {remaining} unité(s) sur lots non périmés)."
        )
    return movements


@transaction.atomic
def process_pharmacy_purchase(
    *,
    patient,
    items: list[dict],
    created_by=None,
    hospitalization=None,
    mark_paid: bool = False,
) -> tuple[Invoice, list[dict]]:
    """
    Crée une facture pharmacie et décrémente le stock FIFO pour chaque ligne.
    items: [{'medication_id': int, 'quantity': int}, ...]
    """
    if not items:
        raise ValidationError('Le panier est vide.')

    # Agrégation des quantités par médicament (évite doubles lignes conflictuelles)
    aggregated: dict[int, int] = {}
    for raw in items:
        med_id = int(raw['medication_id'])
        qty = int(raw['quantity'])
        if qty <= 0:
            raise ValidationError('Chaque ligne doit avoir une quantité positive.')
        aggregated[med_id] = aggregated.get(med_id, 0) + qty

    invoice = Invoice.objects.create(
        patient=patient,
        hospitalization=hospitalization,
        total_amount=Decimal('0.00'),
        amount_paid=Decimal('0.00'),
        status='UNPAID',
        created_by=created_by,
    )

    line_details: list[dict] = []
    for med_id, qty in aggregated.items():
        medication = Medication.objects.select_for_update().get(pk=med_id)
        available = available_stock(medication)
        if available < qty:
            raise ValidationError(
                f"Stock insuffisant pour {medication.name} "
                f"(demandé: {qty}, disponible: {available})."
            )

        movements = decrement_stock_fifo(medication, qty)
        unit_price = medication.unit_price
        line_total = unit_price * qty

        # skip_stock=True : stock déjà décrémenté ci-dessus
        item = InvoiceItem(
            invoice=invoice,
            medication=medication,
            quantity=qty,
            unit_price=unit_price,
            total_price=line_total,
        )
        item.save(skip_stock=True)

        line_details.append({
            'medication_id': medication.id,
            'medication_name': medication.name,
            'quantity': qty,
            'unit_price': float(unit_price),
            'total_price': float(line_total),
            'batches_used': movements,
            'remaining_stock': available_stock(medication),
        })

    invoice.update_totals()

    if mark_paid:
        invoice.amount_paid = invoice.total_amount
        invoice.status = 'PAID'
        invoice.save(update_fields=['amount_paid', 'status'])

    return invoice, line_details
