from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Sum
from datetime import timedelta
from django.utils import timezone

# ==========================================
# 1. Structure Logistique & Hiérarchie
# ==========================================
class Building(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    def __str__(self): return self.name

class Service(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True, null=True)
    is_open_h24 = models.BooleanField(default=False, help_text="Ouvert 24h/24 (urgences, labo, etc.)")
    location_lat = models.FloatField(null=True, blank=True, help_text="Latitude GPS pour navigation")
    location_long = models.FloatField(null=True, blank=True, help_text="Longitude GPS pour navigation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['name']), models.Index(fields=['code'])]

    def __str__(self): 
        return f"{self.name} ({self.building.name})"

class Room(models.Model):
    ROOM_TYPES = [('STANDARD', 'Standard'), ('VIP', 'VIP'), ('ICU', 'Soins Intensifs')]
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='rooms')
    number = models.CharField(max_length=10)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='STANDARD')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['service', 'number']
    
    def __str__(self): 
        return f"Chambre {self.number} - {self.service.name}"

class Bed(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='beds')
    number = models.CharField(max_length=10)
    is_occupied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['room', 'number']
    
    def __str__(self): 
        return f"Lit {self.number} (Chambre {self.room.number})"

# ==========================================
# 2. Consultation & Profil Patient
# ==========================================
class Consultation(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_consultations', limit_choices_to={'role': 'PATIENT'})
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_consultations', limit_choices_to={'role': 'DOCTOR'})
    date = models.DateTimeField(auto_now_add=True)
    symptoms = models.TextField()
    diagnosis = models.TextField()
    prescription = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='consultations_created')
    updated_at = models.DateTimeField(auto_now=True)

class Hospitalization(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hospitalizations', limit_choices_to={'role': 'PATIENT'})
    bed = models.ForeignKey(Bed, on_delete=models.PROTECT, related_name='admissions')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='referred_patients', limit_choices_to={'role': 'DOCTOR'})
    start_date = models.DateTimeField(auto_now_add=True)
    expected_end_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    reason = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='hospitalizations_created')
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.pk is None and self.bed.is_occupied:
            raise ValidationError(f"Opération impossible : Le {self.bed} est déjà occupé.")

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.pk is None:
            self.bed.is_occupied = True
            self.bed.save()
        super().save(*args, **kwargs)

# ==========================================
# 3. Logistique & Support (Avec traçabilité)
# ==========================================
class Provision(models.Model):
    """Gestion des provisions/stocks avec alertes automatiques"""
    name = models.CharField(max_length=100)
    quantity = models.IntegerField(default=0)
    min_quantity_alert = models.IntegerField(default=10, help_text="Seuil d'alerte de stock faible")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='provisions')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='provisions_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('name', 'service')
    
    def is_stock_low(self):
        """Détecte si le stock est faible"""
        return self.quantity < self.min_quantity_alert
    
    def __str__(self):
        return f"{self.name} ({self.service.name}) - Qty: {self.quantity}"

class SupportTask(models.Model):
    TASK_TYPES = [('CLEANING', 'Propreté'), ('SECURITY', 'Sécurité'), ('MAINTENANCE', 'Maintenance')]
    STATUS_TYPES = [('PENDING', 'En attente'), ('IN_PROGRESS', 'En cours'), ('COMPLETED', 'Terminé'), ('CANCELLED', 'Annulé')]
    
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='support_tasks')
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    description = models.TextField(blank=True)
    location_lat = models.FloatField(null=True, blank=True, help_text="Latitude pour la localisation")
    location_long = models.FloatField(null=True, blank=True, help_text="Longitude pour la localisation")
    status = models.CharField(max_length=20, choices=STATUS_TYPES, default='PENDING')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='support_tasks_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_task_type_display()} - {self.service.name} ({self.get_status_display()})"

# ==========================================
# 4. PHARMACIE ET FACTURATION
# ==========================================
class Medication(models.Model):
    name = models.CharField(max_length=100, unique=True)
    stock_quantity = models.IntegerField(default=0)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

class Invoice(models.Model):
    STATUS_CHOICES = [('PENDING', 'En attente'), ('PAID', 'Payée')]
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invoices')
    consultation = models.OneToOneField('Consultation', on_delete=models.CASCADE, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    PAYMENT_METHODS = [('CASH', 'Espèces'), ('MOBILE', 'Mobile Money'), ('CARD', 'Carte Bancaire')]
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    date = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        total_already_paid = self.invoice.payments.exclude(pk=self.pk).aggregate(Sum('amount'))['amount__sum'] or 0
        remaining = self.invoice.total_amount - total_already_paid
        if self.amount > remaining:
            raise ValidationError(f"Paiement refusé : Montant insuffisant ou solde dépassé.")
        super().save()

# ==========================================
# 5. GESTION DES RENDEZ-VOUS (Logique mise à jour)
# ==========================================
class Appointment(models.Model):
    STATUS_CHOICES = [('SCHEDULED', 'Planifié'), ('CONFIRMED', 'Confirmé'), ('CANCELLED', 'Annulé'), ('COMPLETED', 'Terminé')]
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_appointments')
    appointment_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='appointments', null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='appointments_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validation métier : blocage 2h avant et limite 10 RDV/jour"""
        if self.appointment_date < timezone.now() + timedelta(hours=2):
            raise ValidationError("Prise de rendez-vous impossible : moins de 2h avant le créneau.")
        
        # Limite 10 RDV par jour (exclure le RDV courant si mise à jour)
        count = Appointment.objects.filter(
            appointment_date__date=self.appointment_date.date()
        ).exclude(pk=self.pk).count()
        
        if count >= 10:
            raise ValidationError("Capacité maximale de 10 rendez-vous par jour atteinte.")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    class Meta:
        indexes = [
            models.Index(fields=['appointment_date']),
            models.Index(fields=['status']),
            models.Index(fields=['doctor', 'appointment_date']),
        ]

    def __str__(self):
        return f"{self.patient.username} - {self.appointment_date}"
