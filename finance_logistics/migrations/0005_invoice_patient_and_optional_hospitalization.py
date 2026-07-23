# Generated manually — pharmacie ambulatoire + traçabilité créateur

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clinical', '0009_archivedclinicalrecord_deathrecord'),
        ('finance_logistics', '0004_partnerschool'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='hospitalization',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='finance_invoices',
                to='clinical.hospitalization',
            ),
        ),
        migrations.AddField(
            model_name='invoice',
            name='patient',
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={'role': 'PATIENT'},
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='pharmacy_invoices',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='invoice',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='pharmacy_invoices_created',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
