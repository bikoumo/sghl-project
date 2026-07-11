from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.db import OperationalError, ProgrammingError


class Command(BaseCommand):
    help = "Create or update the DG user with the DG role and secure credentials."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            type=str,
            help="Optional password for the DG user. If omitted, a secure password is generated.",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = "DG"
        email = "dg@sghl.com"
        password = options.get("password") or get_random_string(16)
        role = "DG"

        try:
            user = User.objects.filter(username=username).first()
            if not user:
                user = User.objects.filter(email=email).first()

            if user:
                user.username = username
                user.email = email
                user.role = role
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Updated existing DG user '{username}'."))
            else:
                defaults = {
                    "email": email,
                    "role": role,
                    "is_staff": True,
                    "is_superuser": True,
                    "is_active": True,
                }
                if hasattr(User.objects, "create_superuser"):
                    user = User.objects.create_superuser(username=username, email=email, password=password)
                    user.role = role
                    user.save()
                else:
                    user = User(username=username, **defaults)
                    user.set_password(password)
                    user.save()
                self.stdout.write(self.style.SUCCESS(f"Created DG user '{username}' with role '{role}'."))

            self.stdout.write(self.style.SUCCESS(f"Login email: {email}"))
            self.stdout.write(self.style.SUCCESS(f"Password: {password}"))
            self.stdout.write(self.style.SUCCESS("Use this password to connect with DG and change it after first login."))

        except (OperationalError, ProgrammingError) as exc:
            self.stderr.write("Database schema mismatch or migrations not applied.")
            self.stderr.write("Run 'python manage.py migrate' then relaunch 'python manage.py setup_sghl'.")
            self.stderr.write(str(exc))
        except Exception as exc:
            self.stderr.write(f"Failed to create or update DG user: {exc}")