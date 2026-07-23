"""Commande Django : seed_beds — Génère 120 lits réalistes dans l'hôpital.

Utilisation :
  python manage.py seed_beds

Crée les bâtiments, services, chambres et lits manquants sans dupliquer l'existant.
Peut être relancé sans risque (idempotent).
"""

from django.core.management.base import BaseCommand
from clinical.models import Building, Service, Room, Bed


class Command(BaseCommand):
    help = "Génère les structures hospitalières (bâtiments, services, chambres, 120+ lits)"

    def handle(self, *args, **options):
        self._create_buildings()
        self._recreate_hierarchy()
        self.stdout.write(self.style.SUCCESS(
            f"✅ Terminé — {Bed.objects.count()} lits au total."
        ))

    # ------------------------------------------------------------------
    # 1. Bâtiments
    # ------------------------------------------------------------------
    BUILDINGS = [
        ("Bloc Principal", "Bâtiment A — services généraux et urgences"),
        ("Maternité & Pédiatrie", "Bâtiment B — soins mère-enfant"),
        ("Centre de Diagnostic", "Bâtiment C — laboratoire, imagerie, consultations"),
    ]

    def _create_buildings(self):
        for name, desc in self.BUILDINGS:
            Building.objects.get_or_create(name=name, defaults={"description": desc})
        self.stdout.write("✓ Bâtiments prêts.")

    # ------------------------------------------------------------------
    # 2. Arbre : Building → Service → Rooms → Beds
    # ------------------------------------------------------------------
    # Format : (building_name, service_name, code, is_open_h24,
    #           [ (room_number, room_type, nb_beds), ... ])
    HIERARCHY = [
        # -- Bloc Principal ---------------------------------------------------
        ("Bloc Principal", "Urgences", "URG", True, [
            ("URG-01", "ICU", 6), ("URG-02", "ICU", 6), ("URG-03", "STANDARD", 4),
            ("URG-04", "STANDARD", 4), ("URG-05", "STANDARD", 4),
        ]),
        ("Bloc Principal", "Soins Intensifs (Réa)", "REA", True, [
            ("REA-01", "ICU", 4), ("REA-02", "ICU", 4), ("REA-03", "ICU", 4),
        ]),
        ("Bloc Principal", "Chirurgie", "CHR", False, [
            ("CHR-01", "VIP", 2), ("CHR-02", "STANDARD", 4), ("CHR-03", "STANDARD", 4),
            ("CHR-04", "STANDARD", 4),
        ]),
        ("Bloc Principal", "Cardiologie", "CAR", False, [
            ("CAR-01", "VIP", 2), ("CAR-02", "ICU", 4), ("CAR-03", "STANDARD", 4),
        ]),
        ("Bloc Principal", "Médecine Interne", "MED", False, [
            ("MED-01", "STANDARD", 4), ("MED-02", "STANDARD", 4), ("MED-03", "STANDARD", 4),
            ("MED-04", "STANDARD", 4),
        ]),
        # -- Maternité & Pédiatrie -------------------------------------------
        ("Maternité & Pédiatrie", "Maternité", "MAT", False, [
            ("MAT-01", "VIP", 2), ("MAT-02", "VIP", 2), ("MAT-03", "STANDARD", 4),
            ("MAT-04", "STANDARD", 4), ("MAT-05", "STANDARD", 4),
        ]),
        ("Maternité & Pédiatrie", "Pédiatrie", "PED", False, [
            ("PED-01", "STANDARD", 4), ("PED-02", "STANDARD", 4), ("PED-03", "STANDARD", 4),
            ("PED-04", "ICU", 4), ("PED-05", "ICU", 4),
        ]),
        ("Maternité & Pédiatrie", "Néonatalogie", "NEO", True, [
            ("NEO-01", "ICU", 4), ("NEO-02", "ICU", 4), ("NEO-03", "ICU", 4),
        ]),
        # -- Centre de Diagnostic --------------------------------------------
        ("Centre de Diagnostic", "Laboratoire", "LAB", True, [
            ("LAB-01", "STANDARD", 2),  # prélèvements
        ]),
        ("Centre de Diagnostic", "Imagerie Médicale", "IMG", False, [
            ("IMG-01", "STANDARD", 2),  # salles d'attente / boxes
        ]),
        ("Centre de Diagnostic", "Consultations Externes", "CST", False, [
            ("CST-01", "STANDARD", 4), ("CST-02", "STANDARD", 4),
            ("CST-03", "STANDARD", 4),
        ]),
        ("Centre de Diagnostic", "Pharmacie", "PHA", False, [
            ("PHA-01", "STANDARD", 2),
        ]),
    ]

    def _recreate_hierarchy(self):
        total_beds_before = Bed.objects.count()
        created_rooms = 0
        created_beds = 0

        for building_name, service_name, code, h24, rooms_data in self.HIERARCHY:
            building = Building.objects.filter(name=building_name).first()
            if not building:
                self.stderr.write(f"Bâtiment '{building_name}' introuvable, création ignorée.")
                continue

            service, _ = Service.objects.get_or_create(
                code=code,
                defaults={
                    "name": service_name,
                    "building": building,
                    "is_open_h24": h24,
                    "description": f"Service {service_name} — {building_name}",
                },
            )
            # Si le service existait déjà, s'assurer qu'il est bien lié au bon building
            if service.building_id != building.id:
                service.building = building
                service.is_open_h24 = h24
                service.save(update_fields=["building", "is_open_h24"])

            for room_number, room_type, nb_beds in rooms_data:
                room, created = Room.objects.get_or_create(
                    service=service,
                    number=room_number,
                    defaults={
                        "room_type": room_type,
                        "description": f"Salle {room_number} ({room_type}) — {service_name}",
                    },
                )
                if created:
                    created_rooms += 1

                # Créer les lits manquants (max 10 chars pour Bed.number)
                existing = Bed.objects.filter(room=room).count()
                for i in range(existing + 1, nb_beds + 1):
                    bed_letter = chr(64 + i)  # A, B, C, D...
                    Bed.objects.get_or_create(
                        room=room,
                        number=f"L{bed_letter}",
                        defaults={"is_occupied": False},
                    )
                    created_beds += 1

        total_beds_after = Bed.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"✓ {created_rooms} chambres créées, {created_beds} nouveaux lits "
            f"(total avant : {total_beds_before}, après : {total_beds_after})."
        ))

