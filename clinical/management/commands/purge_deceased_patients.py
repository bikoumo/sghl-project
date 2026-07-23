"""
Commande de purge automatique des dossiers de patients décédés.

Exécution manuelle :
    python manage.py purge_deceased_patients

Planification (cron) :
    0 3 * * * cd /chemin/projet && python manage.py purge_deceased_patients

Logique :
- Parcourt les DeathRecord où is_validated=True, is_dossier_purged=False
- et dont la date de création date d'au moins 7 jours
- Archive les données de soins dans ArchivedClinicalRecord
- Purge : Hospitalisations actives, RDV futurs
- Désactive le compte patient (is_active=False)
- Marque is_dossier_purged=True
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class Command(BaseCommand):
    help = "Purge automatique des dossiers patients décédés après 7 jours"

    def handle(self, *args, **options):
        from clinical.models import DeathRecord, ArchivedClinicalRecord
        from clinical.models import Hospitalization, Appointment, Consultation, Invoice
        from authentication.models import User

        now = timezone.now()
        cutoff = now - timedelta(days=7)
        purged_count = 0

        # Chercher les décès validés, non purgés, vieux d'au moins 7 jours
        to_purge = DeathRecord.objects.filter(
            is_validated=True,
            is_dossier_purged=False,
            created_at__lte=cutoff,
        ).select_related('patient', 'service')

        for record in to_purge:
            patient = record.patient
            if not patient:
                continue

            try:
                # 1. Constituer le snapshot des données de soins
                active_hosp = Hospitalization.objects.filter(
                    patient=patient, is_active=True
                ).first()

                consultations_count = Consultation.objects.filter(
                    patient=patient
                ).count()

                invoices_pending_count = Invoice.objects.filter(
                    patient=patient, status='PENDING'
                ).count()

                snapshot = {
                    "active_hospitalization_id": active_hosp.id if active_hosp else None,
                    "active_hospitalization_reason": active_hosp.reason if active_hosp else None,
                    "consultations_count": consultations_count,
                    "invoices_pending_count": invoices_pending_count,
                    "archived_at": now.isoformat(),
                }

                # 2. Créer l'archive
                ArchivedClinicalRecord.objects.create(
                    original_patient_id=patient.id,
                    original_username=patient.username,
                    original_matricule=patient.matricule or f"PT-{patient.id}",
                    patient_full_name=(
                        f"{patient.first_name} {patient.last_name}".strip()
                        or patient.username
                    ),
                    date_of_death=record.validated_at or record.created_at,
                    cause_of_death=record.cause or "",
                    service_name=record.service.name if record.service else "",
                    snapshot=snapshot,
                )

                # 3. Purger les hospitalisations actives → libérer les lits
                for hosp in Hospitalization.objects.filter(
                    patient=patient, is_active=True
                ):
                    hosp.discharge()

                # 4. Annuler les RDV futurs
                Appointment.objects.filter(
                    patient=patient,
                    appointment_date__gte=now,
                    status__in=['SCHEDULED', 'CONFIRMED'],
                ).update(status='CANCELLED')

                # 5. Désactiver le compte patient
                patient.is_active = False
                patient.save(update_fields=['is_active'])

                # 6. Marquer comme purgé
                record.is_dossier_purged = True
                record.save(update_fields=['is_dossier_purged', 'updated_at'])

                purged_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ Purge patient #{patient.id} ({patient.username}) "
                        f"- décédé le {record.created_at.date()}"
                    )
                )

            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ❌ Erreur purge patient #{patient.id}: {exc}"
                    )
                )

        if purged_count == 0:
            self.stdout.write(
                self.style.WARNING(
                    "Aucun dossier à purger (décès validés vieux de +7 jours)."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n🧹 Purge terminée : {purged_count} dossier(s) purgé(s)."
                )
            )

