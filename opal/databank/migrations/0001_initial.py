from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    """Add DatabankConsent model for databank app."""

    initial = True

    dependencies = [
        ('patients', '0019_add_remaining_default_relationshiptypes'),
    ]

    operations = [
        migrations.CreateModel(
            name='DatabankConsent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appointments', models.BooleanField(default=True, verbose_name='Checked-In Appointments')),
                ('diagnosis', models.BooleanField(default=True, verbose_name='Diagnosis')),
                ('demographics', models.BooleanField(default=True, verbose_name='Demographics')),
                ('labs', models.BooleanField(default=True, verbose_name='Labs')),
                ('questionnaires', models.BooleanField(default=True, verbose_name='Questionnaires')),
                ('consent_granted', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Consent Granted')),
                ('consent_updated', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Consent Updated')),
                ('last_synchronized', models.DateTimeField(verbose_name='Last Synchronized Crontime')),
                ('patient', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='databank_consent', to='patients.patient', verbose_name='Patient')),
            ],
            options={
                'verbose_name': 'Databank Consent',
                'verbose_name_plural': 'Databank Consents',
            },
        ),
    ]
