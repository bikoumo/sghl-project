from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from clinical.models import DeathRecord, ArchivedClinicalRecord
from django.contrib.auth import get_user_model
from clinical.models import Consultation, Hospitalization, Appointment, ExamRequest, ExamResult, Invoice, Payment
from django.db import transaction
from django.db.models import Sum

User = get_user_model()


class Command(BaseCommand):
    help = 'Archive clinical data for patients with a validated death record older than 7 days'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=7)
        records = DeathRecord.objects.filter(is_validated=True, validated_at__lte=cutoff)
        self.stdout.write(f"Found {records.count()} death records to archive.")

        for rec in records:
            patient = rec.patient
            self.stdout.write(f"Archiving patient id={patient.id} ({patient.username})")
            with transaction.atomic():
                # Collect anonymized statistics
                consultations = Consultation.objects.filter(patient=patient)
                num_consult = consultations.count()
                last_consult = consultations.order_by('-date').first()
                last_consult_date = last_consult.date.isoformat() if last_consult else None

                invoices = Invoice.objects.filter(patient=patient)
                agg = invoices.aggregate(total=Sum('total_amount'))
                total_invoices = float(agg.get('total') or 0.0)

            snapshot = {
                'num_consultations': num_consult,
                'last_consultation_date': last_consult_date,
                'total_invoices_amount': total_invoices,
                'cause_of_death': rec.cause,
            }

            # Create archived record
            ArchivedClinicalRecord.objects.create(
                original_patient_id=patient.id,
                date_of_death=rec.validated_at,
                snapshot=snapshot,
            )

            # Delete sensitive clinical data
            Consultation.objects.filter(patient=patient).delete()
            Hospitalization.objects.filter(patient=patient).delete()
            Appointment.objects.filter(patient=patient).delete()
            ExamResult.objects.filter(exam_request__patient=patient).delete()
            ExamRequest.objects.filter(patient=patient).delete()
            Invoice.objects.filter(patient=patient).delete()
            Payment.objects.filter(invoice__patient=patient).delete()

            # Anonymize user
            anonymized_email = f"archived+{patient.id}@archived.local"
            patient.email = anonymized_email
            patient.first_name = ''
            patient.last_name = ''
            patient.is_active = False
            patient.save()

            # Mark death record archived by deleting it (or you can mark it)
            rec.delete()

            self.stdout.write(f"Archived and anonymized patient {patient.id}")
