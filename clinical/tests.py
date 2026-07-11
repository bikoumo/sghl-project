from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from authentication.security import signer
from clinical.models import Appointment, Bed, Building, Hospitalization, Provision, Room, Service

User = get_user_model()


class ClinicalStatsTests(TestCase):
    def test_stats_endpoint_returns_counts(self):
        building = Building.objects.create(name='Bloc Test')
        service = Service.objects.create(building=building, name='Pédiatrie', code='PEDT')
        doctor = User.objects.create_user(username='doctor_stats', email='doctor_stats@example.com', password='secret', role='DOCTOR')
        patient = User.objects.create_user(username='patient_stats', email='patient_stats@example.com', password='secret', role='PATIENT')

        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=timezone.now() + timedelta(hours=3),
            service=service,
            status='CONFIRMED',
            created_by=doctor,
        )

        room = Room.objects.create(service=service, number='101')
        bed = Bed.objects.create(room=room, number='1')
        Hospitalization.objects.create(patient=patient, bed=bed, doctor=doctor, reason='Observation', is_active=True, created_by=doctor)
        Provision.objects.create(name='Paracétamol', quantity=2, min_quantity_alert=5, service=service)

        token = signer.sign(f'{doctor.id}:{doctor.username}:{timezone.now().timestamp()}')
        response = self.client.get('/api/v2/clinical/stats/', HTTP_AUTHORIZATION=f'Bearer {token}')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['appointments_count'], 1)
        self.assertEqual(data['hospitalized_count'], 1)
        self.assertEqual(data['low_stock_count'], 1)


class ClinicalAppointmentsTests(TestCase):
    def test_appointments_endpoint_returns_json_payload(self):
        building = Building.objects.create(name='Bloc RDV')
        service = Service.objects.create(building=building, name='Cardiologie', code='CARD')
        doctor = User.objects.create_user(username='doctor_rdv', email='doctor_rdv@example.com', password='secret', role='DOCTOR')
        patient = User.objects.create_user(username='patient_rdv', email='patient_rdv@example.com', password='secret', role='PATIENT')

        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=timezone.now() + timedelta(hours=3),
            service=service,
            status='SCHEDULED',
            created_by=doctor,
        )

        token = signer.sign(f'{doctor.id}:{doctor.username}:{timezone.now().timestamp()}')
        response = self.client.get('/api/v2/clinical/appointments/', HTTP_AUTHORIZATION=f'Bearer {token}')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('appointments', data)
        self.assertGreaterEqual(len(data['appointments']), 1)
