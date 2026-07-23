from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Vérifie PostgreSQL et crée/met à jour le compte DG Theresa."

    def handle(self, *args, **options):
        self.stdout.write("Vérification connexion base de données...")
        try:
            connection.ensure_connection()
            vendor = connection.vendor
            self.stdout.write(self.style.SUCCESS(f"Connexion OK ({vendor})"))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Échec connexion : {exc}"))
            self.stdout.write(
                "Corrigez DB_PASSWORD dans .env (pgAdmin → utilisateur postgres) "
                "puis : python manage.py migrate && python manage.py ensure_theresa_user"
            )
            return

        User = get_user_model()
        email = "bikoumoutheresa@gmail.com"
        user = User.objects.filter(email=email).first()
        if user:
            user.set_password("theresa123")
            user.role = "DG"
            user.is_mfa_enabled = True
            user.is_active = True
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Compte mis à jour : {email} (DG, MFA activée)"))
        else:
            user = User.objects.create_user(
                username="bikoumoutheresa",
                email=email,
                password="theresa123",
                role="DG",
                first_name="Theresa",
                last_name="Bikoumou",
            )
            user.is_mfa_enabled = True
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Compte créé : {email} (DG, MFA activée)"))
