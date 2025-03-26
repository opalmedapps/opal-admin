import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Add initial models for health data app.

    Includes `HealthDataStore` and quantity samples.
    This can be further extended in the future.
    """

    initial = True

    dependencies = [
        ('patients', '0012_add_manage_relationship_permission'),
    ]

    operations = [
        migrations.CreateModel(
            name='HealthDataStore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='health_data_store', to='patients.patient', verbose_name='Patient')),
            ],
            options={
                'verbose_name': 'Health Data Store',
                'verbose_name_plural': 'Health Data Stores',
            },
        ),
        migrations.CreateModel(
            name='QuantitySample',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField(verbose_name='Start Date')),
                ('device', models.CharField(help_text='The device that was used to take the measurement', max_length=255, verbose_name='Device')),
                ('source', models.CharField(choices=[('P', 'Patient'), ('C', 'Clinician')], help_text='The source that provided this sample, for example, the patient if it is patient-reported data', max_length=1, verbose_name='Source')),
                ('added_at', models.DateTimeField(auto_now_add=True, verbose_name='Added At')),
                ('value', models.DecimalField(decimal_places=2, max_digits=7, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Value')),
                ('type', models.CharField(choices=[('BM', 'Body Mass (kg)'), ('TMP', 'Body Temperature (°C)'), ('HR', 'Heart Rate (bpm)'), ('HRV', 'Heart Rate Variability (ms)'), ('SPO2', 'Oxygen Saturation (%)')], max_length=4, verbose_name='Type')),
                ('data_store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quantity_samples', to='health_data.healthdatastore', verbose_name='Health Data Store')),
            ],
            options={
                'verbose_name': 'Quantity Sample',
                'verbose_name_plural': 'Quantity Samples',
            },
        ),
        migrations.AddConstraint(
            model_name='quantitysample',
            constraint=models.CheckConstraint(check=models.Q(('type__in', ['BM', 'TMP', 'HR', 'HRV', 'SPO2'])), name='health_data_quantitysample_type_valid'),
        ),
        migrations.AddConstraint(
            model_name='healthdatastore',
            constraint=models.UniqueConstraint(fields=('patient',), name='health_data_healthdatastore_unique_patient'),
        ),
    ]
