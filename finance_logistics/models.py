from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from clinical.models import Hospitalization

# ==========================================
# 1. PARTIE PHARMACIE & STOCK
# ==========================================
class Medication(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=50, unique=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class StockBatch(models.Model):
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=50)
    quantity_in_stock = models.PositiveIntegerField()
    expiry_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['expiry_date', 'id']

    def __str__(self):
        return f"Lot {self.batch_number} - {self.medication.name} (Qté: {self.quantity_in_stock})"


class PartnerSchool(models.Model):
    """Représente un partenaire tiers-payant (école ou assurance)."""
    TYPE_CHOICES = [('SCHOOL', 'Ecole'), ('INSURANCE', 'Assurance')]
    name = models.CharField(max_length=200)
    partner_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='SCHOOL')
    contact_email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    contract_reference = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.get_partner_type_display()})"


# ==========================================
# 2. PARTIE FACTURATION (hospit + vente pharmacie)
# ==========================================
class Invoice(models.Model):
    STATUS_CHOICES = [
        ('UNPAID', 'Non payée'),
        ('PARTIAL', 'Partiellement payée'),
        ('PAID', 'Payée'),
    ]

    # Hospitalisation optionnelle (vente ambulatoire possible)
    hospitalization = models.ForeignKey(
        Hospitalization,
        on_delete=models.CASCADE,
        related_name='finance_invoices',
        null=True,
        blank=True,
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pharmacy_invoices',
        null=True,
        blank=True,
        limit_choices_to={'role': 'PATIENT'},
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNPAID')
    insurance_covered_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pharmacy_invoices_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not self.patient_id and not self.hospitalization_id:
            raise ValidationError('Une facture doit être liée à un patient ou une hospitalisation.')
        if self.hospitalization_id and not self.patient_id:
            self.patient = self.hospitalization.patient

    def update_totals(self):
        from decimal import Decimal
        medication_total = sum((item.total_price for item in self.items.all()), Decimal('0.00'))
        self.total_amount = medication_total

        if self.amount_paid >= self.total_amount and self.total_amount > 0:
            self.status = 'PAID'
        elif self.amount_paid > 0:
            self.status = 'PARTIAL'
        else:
            self.status = 'UNPAID'

        self.save(update_fields=['total_amount', 'status'])

    def __str__(self):
        who = self.patient.username if self.patient_id else 'N/A'
        return f"Facture #{self.id} - Patient: {who} (Total: {self.total_amount} FCFA)"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, skip_stock=False, **kwargs):
        self.total_price = self.quantity * self.unit_price

        if self.pk is None and not skip_stock:
            from finance_logistics.services import decrement_stock_fifo

            decrement_stock_fifo(self.medication, self.quantity)

        super().save(*args, **kwargs)
        self.invoice.update_totals()
