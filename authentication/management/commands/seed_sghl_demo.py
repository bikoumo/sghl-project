from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from authentication.models import InternalMessage
from clinical.models import (
    Appointment,
    Bed,
    Building,
    ExamRequest,
    ExamResult,
    Invoice,
    MaternityRecord,
    PediatricRecord,
    Provision,
    Room,
    Service,
)
from finance_logistics.models import Medication, PartnerSchool


class Command(BaseCommand):
    help = (
        "Peuple SGHL avec des comptes de démonstration prêts pour la soutenance "
        "(DG, Secrétaire, Docteur, Patient, Biologiste) et des données cliniques."
    )

    DEMO_PASSWORD = "demo1234"

    DEMO_USERS = [
        {
            "username": "admin_demo",
            "email": "admin@sghl.com",
            "first_name": "Marie",
            "last_name": "Nkounkou",
            "role": "DG",
            "service_code": None,
            "ui_role": "ADMIN",
            "dashboard": "/dashboard/admin",
            "is_staff": True,
            "is_superuser": True,
        },
        {
            "username": "secretary_demo",
            "email": "secretary@sghl.com",
            "first_name": "Grace",
            "last_name": "Mabiala",
            "role": "SECRETARY_GENERAL",
            "service_code": None,
            "ui_role": "SECRETARY",
            "dashboard": "/dashboard/secretary",
        },
        {
            "username": "secretary_ped_demo",
            "email": "secretary.ped@sghl.com",
            "first_name": "Sylvie",
            "last_name": "Okemba",
            "role": "SECRETARY_SERVICE",
            "service_code": "PED",
            "ui_role": "SECRETARY",
            "dashboard": "/dashboard/secretary",
        },
        {
            "username": "doctor_demo",
            "email": "doctor@sghl.com",
            "first_name": "Jean",
            "last_name": "Moukoko",
            "role": "DOCTOR",
            "service_code": "PED",
            "ui_role": "DOCTOR",
            "dashboard": "/dashboard/doctor",
        },
        {
            "username": "patient_demo",
            "email": "patient@sghl.com",
            "first_name": "Paul",
            "last_name": "Ngoma",
            "role": "PATIENT",
            "service_code": None,
            "ui_role": "PATIENT",
            "dashboard": "/dashboard/patient",
        },
        {
            "username": "biologist_demo",
            "email": "biologist@sghl.com",
            "first_name": "Alain",
            "last_name": "Kimbembe",
            "role": "BIOLOGIST",
            "service_code": "LAB",
            "ui_role": "OTHER",
            "dashboard": "/dashboard/doctor",
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            type=str,
            default=self.DEMO_PASSWORD,
            help="Mot de passe commun pour tous les comptes demo (defaut: demo1234).",
        )
        parser.add_argument(
            "--enable-mfa",
            action="store_true",
            help="Active le MFA sur les comptes demo (OTP visible en console en local).",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        password = options["password"]
        enable_mfa = options["enable_mfa"]

        services = self._seed_infrastructure()
        users = self._seed_users(User, services, password, enable_mfa)
        self._seed_clinical_data(users, services)
        self._seed_pediatric_maternity()
        self._seed_messages(users, services)
        self._print_final_summary(password, enable_mfa)

    def _seed_infrastructure(self):
        building, _ = Building.objects.get_or_create(
            name="Bloc Principal",
            defaults={"description": "Batiment principal du centre hospitalier SGHL"},
        )

        service_specs = [
            ("Pediatrie", "PED", "Service de pediatrie", True, 3.8720, 11.5180),
            ("Urgences", "URG", "Service d'urgence 24h/24", True, 3.8667, 11.5167),
            ("Laboratoire", "LAB", "Analyses biologiques", True, 3.8650, 11.5150),
            ("Banque", "BNQ", "Service financier", False, 3.8640, 11.5140),
            ("Logistique", "LOG", "Support logistique", False, 3.8630, 11.5130),
        ]

        services = {}
        for name, code, description, is_open, lat, lng in service_specs:
            service, created = Service.objects.get_or_create(
                code=code,
                defaults={
                    "building": building,
                    "name": name,
                    "description": description,
                    "is_open_h24": is_open,
                    "location_lat": lat,
                    "location_long": lng,
                },
            )
            if not created:
                service.location_lat = lat
                service.location_long = lng
                service.is_open_h24 = is_open
                service.save(update_fields=["location_lat", "location_long", "is_open_h24"])
            services[code] = service
            if created:
                self.stdout.write(self.style.SUCCESS(f"Service cree : {service.name} ({code})"))

        room, _ = Room.objects.get_or_create(
            service=services["PED"],
            number="101",
            defaults={"room_type": "STANDARD", "description": "Chambre pediatrie"},
        )
        bed_a, _ = Bed.objects.get_or_create(room=room, number="A", defaults={"is_occupied": False})
        bed_b, bed_b_created = Bed.objects.get_or_create(room=room, number="B", defaults={"is_occupied": False})
        if bed_b_created:
            self.stdout.write(self.style.SUCCESS("Lits de demo disponibles en pediatrie (101-A, 101-B)"))

        Provision.objects.get_or_create(
            name="Gants steriles",
            service=services["PED"],
            defaults={"quantity": 4, "min_quantity_alert": 10},
        )
        Provision.objects.get_or_create(
            name="Serum physiologique",
            service=services["URG"],
            defaults={"quantity": 25, "min_quantity_alert": 10},
        )

        return {**services, "_bed_a": bed_a, "_bed_b": bed_b}

    def _seed_users(self, User, services, password, enable_mfa):
        users = {}
        for spec in self.DEMO_USERS:
            service = services.get(spec["service_code"]) if spec["service_code"] else None
            user, created = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "email": spec["email"],
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "role": spec["role"],
                    "service": service,
                    "is_active": True,
                    "is_staff": spec.get("is_staff", False),
                    "is_superuser": spec.get("is_superuser", False),
                    "is_mfa_enabled": enable_mfa,
                },
            )

            user.email = spec["email"]
            user.first_name = spec["first_name"]
            user.last_name = spec["last_name"]
            user.role = spec["role"]
            user.service = service
            user.is_active = True
            user.is_staff = spec.get("is_staff", False)
            user.is_superuser = spec.get("is_superuser", False)
            user.is_mfa_enabled = enable_mfa
            user.set_password(password)
            user.save()

            users[spec["role"]] = user
            users[spec["username"]] = user
            action = "Cree" if created else "Mis a jour"
            self.stdout.write(self.style.SUCCESS(f"{action} : {spec['email']} ({spec['role']})"))

        return users

    def _seed_clinical_data(self, users, services):
        User = get_user_model()
        doctor = users["doctor_demo"]
        patient = users["patient_demo"]
        secretary = users["secretary_demo"]

        appointment_slots = [
            (patient, doctor, timezone.now() + timedelta(hours=3), "CONFIRMED", services["PED"]),
            (patient, doctor, timezone.now() + timedelta(hours=5), "SCHEDULED", services["PED"]),
            (patient, doctor, timezone.now() + timedelta(days=1, hours=2), "SCHEDULED", services["URG"]),
            (patient, doctor, timezone.now() + timedelta(days=1, hours=4), "CONFIRMED", services["PED"]),
            (patient, doctor, timezone.now() + timedelta(days=2, hours=1), "SCHEDULED", services["LAB"]),
        ]

        for patient_user, doctor_user, slot, status, service in appointment_slots:
            Appointment.objects.get_or_create(
                patient=patient_user,
                doctor=doctor_user,
                appointment_date=slot,
                defaults={
                    "status": status,
                    "service": service,
                    "created_by": doctor_user,
                },
            )

        # Ajouter des médecins supplémentaires (pour arriver à ~10 médecins)
        extra_docs = []
        for i in range(2, 11):
            uname = f'doctor_demo_{i}'
            email = f'doctor{i}@sghl.com'
            doc, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    'email': email,
                    'first_name': f'Doc{i}',
                    'last_name': 'Demo',
                    'role': 'DOCTOR',
                    'service': services.get('PED'),
                    'is_active': True,
                }
            )
            doc.set_password(self.DEMO_PASSWORD)
            doc.save()
            extra_docs.append(doc)

        # Générer 20 rendez-vous répartis entre plusieurs médecins
        import random as pyrandom
        doctors_pool = [doctor] + extra_docs
        # S'assurer que 'extra_patients' existe
        try:
            extra_patients
        except NameError:
            extra_patients = []
            for username, email, first_name, last_name in [
                ('patient_demo_2', 'patient2@sghl.com', 'Aude', 'Mouanda'),
                ('patient_demo_3', 'patient3@sghl.com', 'Rodolphe', 'Dienga'),
            ]:
                patient_user, _ = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'role': 'PATIENT',
                        'is_active': True,
                    },
                )
                patient_user.set_password(self.DEMO_PASSWORD)
                patient_user.save(update_fields=['password'])
                extra_patients.append(patient_user)

        patients_pool = [patient] + extra_patients
        for i in range(20):
            d = pyrandom.choice(doctors_pool)
            p = pyrandom.choice(patients_pool)
            slot = timezone.now() + timedelta(days=pyrandom.randint(0,5), hours=pyrandom.randint(3,72))
            status = pyrandom.choice(['SCHEDULED', 'CONFIRMED'])
            Appointment.objects.get_or_create(
                patient=p,
                doctor=d,
                appointment_date=slot,
                defaults={
                    'status': status,
                    'service': services['PED'],
                    'created_by': d,
                }
            )

        # Créer 50 médicaments si absent (finance_logistics.Medication) + lots de stock
        from datetime import date
        from finance_logistics.models import StockBatch

        med_names = [f'Medicament_{i}' for i in range(1, 51)]
        for i, name in enumerate(med_names, start=1):
            code = f'MED-{i:04d}'
            med, _ = Medication.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'unit_price': 500 + (i * 10),
                    'description': f'Fourniture de test {name}'
                }
            )
            # Au moins un lot non périmé pour les tests de vente
            StockBatch.objects.get_or_create(
                medication=med,
                batch_number=f'LOT-{code}-A',
                defaults={
                    'quantity_in_stock': 100,
                    'expiry_date': date.today().replace(year=date.today().year + 1),
                },
            )

        # Créer 3 ecoles/partenaires pour tests Tiers-Payant
        partners = [
            ('Lycée Saint-Pierre', 'SCHOOL', 'contact@lycee-stp.com'),
            ('Ecole Technique SGHL', 'SCHOOL', 'contact@et-sghl.com'),
            ('Assurance Nationale', 'INSURANCE', 'contact@assurnat.com'),
        ]
        for name, ptype, email in partners:
            PartnerSchool.objects.get_or_create(
                name=name,
                defaults={'partner_type': ptype, 'contact_email': email},
            )

        extra_patients = []
        for username, email, first_name, last_name in [
            ('patient_demo_2', 'patient2@sghl.com', 'Aude', 'Mouanda'),
            ('patient_demo_3', 'patient3@sghl.com', 'Rodolphe', 'Dienga'),
        ]:
            patient_user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'PATIENT',
                    'is_active': True,
                },
            )
            patient_user.set_password(self.DEMO_PASSWORD)
            patient_user.save(update_fields=['password'])
            extra_patients.append(patient_user)

        invoice_specs = [
            (patient, 35000, 'PAID'),
            (extra_patients[0], 18000, 'PENDING'),
            (extra_patients[1], 22000, 'PENDING'),
            (patient, 25000, 'PAID'),
        ]
        for patient_user, amount, status in invoice_specs:
            Invoice.objects.get_or_create(
                patient=patient_user,
                defaults={
                    'total_amount': amount,
                    'status': status,
                },
            )

        ExamRequest.objects.get_or_create(
            title='Analyse de sang standard',
            defaults={
                "patient": patient,
                "requested_by": doctor,
                "description": 'Bilan biologique pour contrôle général',
                "status": 'IN_PROGRESS',
            },
        )
        exam_request = ExamRequest.objects.filter(title='Analyse de sang standard').first()
        if exam_request and not hasattr(exam_request, 'result'):
            ExamResult.objects.create(
                exam_request=exam_request,
                performed_by=doctor,
                result_text='Globules rouges et plaquettes normales',
                conclusion='Aucune anomalie détectée',
            )

        self.stdout.write(self.style.SUCCESS("Données clinique de demo enrichies (RDV, patients, factures, urgence et labo)."))

    def _seed_messages(self, users, services):
        doctor = users["doctor_demo"]
        secretary = users["secretary_demo"]

        InternalMessage.objects.get_or_create(
            content="Un lit supplementaire est demande pour la pediatrie.",
            defaults={
                "sender": doctor,
                "recipient_service": services["PED"],
                "is_urgent": True,
            },
        )
        InternalMessage.objects.get_or_create(
            content="Transfert de stock valide pour le service banque.",
            defaults={
                "sender": secretary,
                "recipient_service": services["BNQ"],
                "is_urgent": False,
            },
        )
        InternalMessage.objects.get_or_create(
            content="Resultats labo disponibles pour le patient Ngoma.",
            defaults={
                "sender": users["biologist_demo"],
                "recipient_service": services["PED"],
                "is_urgent": False,
            },
        )

        self.stdout.write(self.style.SUCCESS("Messages internes de demo ajoutes."))

    def _seed_pediatric_maternity(self):
        from datetime import date, timedelta

        if not PediatricRecord.objects.exists():
            PediatricRecord.objects.create(
                nom="Ngoma Junior",
                date_naissance=date.today() - timedelta(days=120),
                poids="4.2",
                taille=58,
                groupe_sanguin="O+",
                vaccin_date=date.today() + timedelta(days=14),
            )
        if not MaternityRecord.objects.exists():
            MaternityRecord.objects.create(
                nom="Mbarga",
                prenom="Claire",
                date_terme=date.today() + timedelta(days=45),
                next_visit=date.today() + timedelta(days=7),
                status="Suivi en cours",
            )
        self.stdout.write(self.style.SUCCESS("Donnees pediatrie / maternite de demo ajoutees."))

    def _print_final_summary(self, password, enable_mfa):
        mfa_label = "OUI (OTP dans la console runserver en local)" if enable_mfa else "NON (connexion directe apres login)"

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 72))
        self.stdout.write(self.style.SUCCESS(" SGHL — COMPTES DE DEMONSTRATION (SOUTENANCE)"))
        self.stdout.write(self.style.SUCCESS("=" * 72))
        self.stdout.write(f" Mot de passe commun : {password}")
        self.stdout.write(f" MFA active          : {mfa_label}")
        self.stdout.write("")
        self.stdout.write(
            f" {'Role UI':<12} | {'Email':<26} | {'Role backend':<18} | {'Service':<10} | Dashboard"
        )
        self.stdout.write("-" * 72)

        for spec in self.DEMO_USERS:
            service = spec["service_code"] or "-"
            self.stdout.write(
                f" {spec['ui_role']:<12} | {spec['email']:<26} | {spec['role']:<18} | {service:<10} | {spec['dashboard']}"
            )

        self.stdout.write("")
        self.stdout.write(self.style.WARNING(" SCENARIO RECOMMANDE POUR LA SOUTENANCE"))
        self.stdout.write(" 1. Admin (admin@sghl.com)         -> vue globale /dashboard/admin")
        self.stdout.write(" 2. Docteur (doctor@sghl.com)      -> service PED, consultations")
        self.stdout.write(" 3. Secretaire (secretary@sghl.com) -> lecture seule, planning")
        self.stdout.write(" 4. Patient (patient@sghl.com)     -> espace patient")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING(" COMMANDES"))
        self.stdout.write(" Local  : python manage.py seed_sghl_demo")
        self.stdout.write(" + MFA  : python manage.py seed_sghl_demo --enable-mfa")
        self.stdout.write(" Render : lancer dans le Shell du service sghl-backend")
        self.stdout.write(self.style.SUCCESS("=" * 72))
