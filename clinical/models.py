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
        if self.pk is None and self.bed_id and self.bed.is_occupied:
            raise ValidationError(f"Opération impossible : Le {self.bed} est déjà occupé.")

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.pk is None:
            self.bed.is_occupied = True
            self.bed.save(update_fields=['is_occupied', 'updated_at'])
        super().save(*args, **kwargs)

    def discharge(self):
        """Libère le lit et clôture l'hospitalisation active."""
        if not self.is_active:
            return
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])
        Bed.objects.filter(pk=self.bed_id, is_occupied=True).update(is_occupied=False)

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
    label = models.CharField(max_length=120, blank=True, default='Consultation')
    created_at = models.DateTimeField(auto_now_add=True)

    def amount_paid(self):
        return self.payments.aggregate(total=Sum('amount'))['total'] or 0

    def remaining_amount(self):
        return self.total_amount - self.amount_paid()


class ExamRequest(models.Model):
    STATUS_CHOICES = [('PENDING', 'En attente'), ('IN_PROGRESS', 'En cours'), ('COMPLETED', 'Terminé')]
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_requests', limit_choices_to={'role': 'PATIENT'})
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='exam_requests_created')
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.patient.username}"


class ExamResult(models.Model):
    exam_request = models.OneToOneField(ExamRequest, on_delete=models.CASCADE, related_name='result')
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='exam_results_performed')
    result_text = models.TextField(blank=True, null=True)
    conclusion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Résultat pour {self.exam_request.title}"


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('CASH', 'Paiement sur place (espèces)'),
        ('MTN', 'MTN Mobile Money'),
        ('AIRTEL', 'Airtel Money'),
        ('CARD', 'Carte bancaire'),
    ]
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    phone = models.CharField(max_length=30, blank=True, null=True)
    card_last_four = models.CharField(max_length=4, blank=True, null=True, help_text="4 derniers chiffres de la carte bancaire")
    card_expiry = models.CharField(max_length=5, blank=True, null=True, help_text="Date d'expiration MM/AA")
    transaction_ref = models.CharField(max_length=64, blank=True, null=True)
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_made',
    )
    date = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not self.invoice_id:
            return
        total_already_paid = (
            self.invoice.payments.exclude(pk=self.pk).aggregate(Sum('amount'))['amount__sum'] or 0
        )
        remaining = self.invoice.total_amount - total_already_paid
        if self.amount > remaining:
            raise ValidationError(
                f"Paiement refusé : montant supérieur au solde restant ({remaining})."
            )
        if self.method in {'MTN', 'AIRTEL'} and not (self.phone or '').strip():
            raise ValidationError("Le numéro de téléphone est obligatoire pour MTN / Airtel Money.")
        if self.method == 'CARD':
            if not self.card_last_four or len(self.card_last_four) != 4 or not self.card_last_four.isdigit():
                raise ValidationError("Les 4 derniers chiffres de la carte sont obligatoires.")
            if not self.card_expiry or len(self.card_expiry) != 5:
                raise ValidationError("La date d'expiration (MM/AA) est obligatoire.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        paid = self.invoice.amount_paid()
        if paid >= self.invoice.total_amount:
            self.invoice.status = 'PAID'
            self.invoice.save(update_fields=['status'])


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
    notes = models.CharField(max_length=255, blank=True, default='')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='appointments_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validation métier : blocage 2h avant et limite 10 RDV/jour"""
        if self.appointment_date < timezone.now() + timedelta(hours=2):
            raise ValidationError("Prise de rendez-vous impossible : moins de 2h avant le créneau.")
        
        # Limite 10 RDV par jour (exclure le RDV courant si mise à jour)
        # Ignorée pendant les migrations (table inexistante), le seed automatique,
        # ou si la base est vide — pour ne pas bloquer le déploiement sur Render.
        try:
            table_exists = Appointment.objects.exists()
        except Exception:
            table_exists = False

        if table_exists:
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


# ==========================================
# 6. GESTION DES DÉCÈS ET ARCHIVAGE
# ==========================================
class DeathRecord(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='death_records', limit_choices_to={'role': 'PATIENT'})
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='death_reports')
    service = models.ForeignKey('Service', on_delete=models.SET_NULL, null=True, blank=True, related_name='death_records', help_text="Service où le décès a eu lieu")
    cause = models.TextField(blank=True, null=True, help_text="Cause principale du décès")
    complications = models.TextField(blank=True, null=True, help_text="Complications ou détails supplémentaires")
    validated_at = models.DateTimeField(blank=True, null=True)
    is_validated = models.BooleanField(default=False)
    is_dossier_purged = models.BooleanField(default=False, help_text="True après purge automatique (7 jours)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['validated_at', 'is_validated']),
            models.Index(fields=['service']),
            models.Index(fields=['cause']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Décès #{self.id} - {self.patient} (validé={self.is_validated})"


class ArchivedClinicalRecord(models.Model):
    original_patient_id = models.IntegerField()
    original_username = models.CharField(max_length=150, blank=True, default='')
    original_matricule = models.CharField(max_length=32, blank=True, default='')
    patient_full_name = models.CharField(max_length=300, blank=True, default='')
    date_of_death = models.DateTimeField(blank=True, null=True)
    cause_of_death = models.TextField(blank=True, default='')
    service_name = models.CharField(max_length=100, blank=True, default='')
    snapshot = models.JSONField(default=dict, help_text="Copie des données de soins au moment de l'archivage")
    archived_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-archived_at']

    def __str__(self):
        return f"Archivé: {self.patient_full_name or self.original_username} (patient#{self.original_patient_id})"


# ==========================================
# 7. PÉDIATRIE & MATERNITÉ
# ==========================================
class PediatricRecord(models.Model):
    nom = models.CharField(max_length=120)
    date_naissance = models.DateField()
    poids = models.DecimalField(max_digits=5, decimal_places=2)
    taille = models.PositiveIntegerField(null=True, blank=True, help_text="cm")
    groupe_sanguin = models.CharField(max_length=5, blank=True, default='')
    vaccin_date = models.DateField()
    status = models.CharField(max_length=40, default='Suivi actif')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Pédiatrie: {self.nom}"


class MaternityRecord(models.Model):
    nom = models.CharField(max_length=80)
    prenom = models.CharField(max_length=80)
    date_terme = models.DateField()
    next_visit = models.DateField()
    status = models.CharField(max_length=40, default='Suivi en cours')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_visit']

    def __str__(self):
        return f"Maternité: {self.nom} {self.prenom}"
