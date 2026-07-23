# Generated manually for patient dossier fields (PostgreSQL-compatible)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0007_user_allergies_user_antecedents_user_groupe_sanguin_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='birth_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='gender',
            field=models.CharField(
                blank=True,
                choices=[('M', 'Masculin'), ('F', 'Féminin'), ('O', 'Autre')],
                max_length=1,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='matricule',
            field=models.CharField(blank=True, max_length=32, null=True, unique=True),
        ),
    ]
