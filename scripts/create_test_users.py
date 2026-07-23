import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sghl_backend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()


def run():
    """Crée/Met à jour des comptes de test en utilisant les alias + pour recevoir les OTP.

    Utilisation :
      python scripts/create_test_users.py
    """
    # Utiliser des alias dynamiques : local_part+role@domain
    alias_local = os.environ.get('EMAIL_ALIAS_LOCAL_PART', 'projet')
    alias_domain = os.environ.get('EMAIL_ALIAS_DOMAIN', 'gmail.com')

    specs = [
        ('admin', f"{alias_local}+admin@{alias_domain}", 'DG'),
        ('doctor', f"{alias_local}+doctor@{alias_domain}", 'DOCTOR'),
        ('secretary', f"{alias_local}+secretary@{alias_domain}", 'SECRETARY_GENERAL'),
        # Le rôle finance est mappé par défaut à DG pour accès aux tableaux de facturation
        ('finance', f"{alias_local}+finance@{alias_domain}", 'DG'),
    ]

    PASSWORD = os.environ.get('SGHL_TEST_PASSWORD', 'Test1234!')

    for name, email, role in specs:
        user, created = User.objects.get_or_create(email=email, defaults={
            'username': email.split('@')[0],
            'email': email,
            'first_name': name.capitalize(),
            'last_name': 'Test',
            'role': role,
            'is_active': True,
            'is_mfa_enabled': True,
        })

        # Mettre à jour les champs importants
        user.email = email
        user.username = email.split('@')[0]
        user.role = role
        user.is_active = True
        user.is_mfa_enabled = True
        user.set_password(PASSWORD)
        user.save()

        verb = 'Créé' if created else 'Mis à jour'
        print(f"{verb} utilisateur {role} -> {email} (pwd: {PASSWORD})")


if __name__ == '__main__':
    run()
