# Generated manually — notes sur rendez-vous

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinical', '0009_archivedclinicalrecord_deathrecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='notes',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
