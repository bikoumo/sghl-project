from django.db import models
from django.conf import settings
from clinical.models import Hospitalization

# ==========================================
# 1. PARTIE PHARMACIE & STOCK
# ==========================================
class Medication(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=50, unique=True) # Code barre ou identifiant unique
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class StockBatch(models.Model):
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=50) # Numéro de lot
    quantity_in_stock = models.PositiveIntegerField()
    expiry_date = models.DateField() # Date de péremption requise
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lot {self.batch_number} - {self.medication.name} (Qté: {self.quantity_in_stock})"


# ==========================================
# 2. PARTIE FACTURATION AUTOMATISÉE
# ==========================================
class Invoice(models.Model):
    STATUS_CHOICES = [
        ('UNPAID', 'Non payée'),
        ('PARTIAL', 'Partiellement payée'),
        ('PAID', 'Payée'),
    ]
    
    hospitalization = models.ForeignKey(Hospitalization, on_delete=models.CASCADE, related_name='invoices')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNPAID')
    insurance_covered_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) # Tiers-payant
    created_at = models.DateTimeField(auto_now_add=True)

    def update_totals(self):
        # Moteur de calcul automatisé des consommations (médicaments dispensés)
        medication_total = sum(item.total_price for item in self.items.all())
        
        # On pourrait ajouter ici le calcul des nuitées (tarif_chambre * nb_jours)
        self.total_amount = medication_total
        
        # Ajustement automatique du statut selon les paiements partiels/échelonnés
        if self.amount_paid >= self.total_amount:
            self.status = 'PAID'
        elif self.amount_paid > 0:
            self.status = 'PARTIAL'
        else:
            self.status = 'UNPAID'
            
        self.save()

    def __str__(self):
        return f"Facture #{self.id} - Patient: {self.hospitalization.patient.username} (Total: {self.total_amount} FCFA)"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # Calcul automatique de la ligne
        self.total_price = self.quantity * self.unit_price
        
        # Règle métier critique : Décrémentation automatique des stocks lors de la validation
        if self.pk is None: # Uniquement lors de la création initiale de la ligne
            remaining_qty = self.quantity
            # On cherche les lots du médicament non périmés, du plus ancien au plus récent (FIFO)
            batches = StockBatch.objects.filter(
                medication=self.medication, 
                quantity_in_stock__gt=0
            ).order_list = ['expiry_date']
            
            for batch in batches:
                if remaining_qty <= 0:
                    break
                if batch.quantity_in_stock >= remaining_qty:
                    batch.quantity_in_stock -= remaining_qty
                    remaining_qty = 0
                    batch.save()
                else:
                    remaining_qty -= batch.quantity_in_stock
                    batch.quantity_in_stock = 0
                    batch.save()
            
            if remaining_qty > 0:
                raise ValueError(f"Rupture de stock imminente pour {self.medication.name} ! Quantité manquante : {remaining_qty}")

        super().save(*args, **kwargs)
        # On met à jour le montant global de la facture parente
        self.invoice.update_totals()