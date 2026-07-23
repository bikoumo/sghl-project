# Generated manually — paiements MTN/Airtel + libellé facture

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clinical', '0010_appointment_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='label',
            field=models.CharField(blank=True, default='Consultation', max_length=120),
        ),
        migrations.AlterField(
            model_name='payment',
            name='method',
            field=models.CharField(
                choices=[
                    ('CASH', 'Paiement sur place (espèces)'),
                    ('MTN', 'MTN Mobile Money'),
                    ('AIRTEL', 'Airtel Money'),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='phone',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='transaction_ref',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='paid_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payments_made',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
