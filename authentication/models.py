from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import datetime

# 1. Modèle Utilisateur Personnalisé avec Rôles (RBAC)
class User(AbstractUser):
    ROLE_CHOICES = [
        ('DG', 'Directeur Général'),
        ('SECRETARY_GENERAL', 'Secrétaire Générale'),
        ('SECRETARY_SERVICE', 'Secrétaire de Service'),
        ('DOCTOR', 'Médecin'),
        ('BIOLOGIST', 'Biologiste'),
        ('PATIENT', 'Patient'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PATIENT')
    service = models.ForeignKey('clinical.Service', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_mfa_enabled = models.BooleanField(default=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    groupe_sanguin = models.CharField(max_length=10, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    antecedents = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def has_service_access(self, obj):
        """Vérifie si l'utilisateur a accès à un objet selon son rôle et son service."""
        if self.role in ['DG', 'SECRETARY_GENERAL']:
            return True  # Accès complet
        if self.role == 'SECRETARY_SERVICE' and hasattr(obj, 'service'):
            return obj.service == self.service
        return False


# 2. Table pour la validation MFA (Code valable 5 minutes maximum)
class MFACode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mfa_codes')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        # Vérifie si le code a expiré (plus de 5 minutes) ou a déjà été utilisé
        expiry_time = self.created_at + datetime.timedelta(minutes=5)
        return not self.is_used and timezone.now() <= expiry_time

    def __str__(self):
        return f"MFA Code pour {self.user.username} - Valide: {self.is_valid()}"


# 3. Modèle pour les messages internes de communication d'urgence
class InternalMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_internal_messages')
    recipient_service = models.ForeignKey('clinical.Service', on_delete=models.CASCADE, related_name='internal_messages', null=True, blank=True)
    content = models.TextField()
    is_urgent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message de {self.sender.username} -> {self.recipient_service or 'Tous'}"


# 4. Modèle pour les commentaires médicaux
class CommentaireMedical(models.Model):
    # Relie le commentaire à un patient et au médecin qui l'a écrit
    patient = models.ForeignKey(User, related_name='commentaires_recus', on_delete=models.CASCADE, limit_choices_to={'role': 'PATIENT'})
    medecin = models.ForeignKey(User, related_name='commentaires_emis', on_delete=models.CASCADE, limit_choices_to={'role': 'DOCTOR'})
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commentaire pour {self.patient.username} par {self.medecin.username}"

# Mise à jour de ta méthode has_service_access pour inclure les nouveaux rôles
def has_service_access(self, obj):
    if self.role in ['DG', 'SECRETARY_GENERAL']:
        return True
    # Accès pour Médecins, Infirmiers, Biologistes : doivent appartenir au même service
    if self.role in ['DOCTOR', 'BIOLOGIST', 'SECRETARY_SERVICE'] and hasattr(obj, 'service'):
        return obj.service == self.service
    return False