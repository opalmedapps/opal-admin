# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


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
            name='QuantitySample',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField(verbose_name='Start Date')),
                (
                    'device',
                    models.CharField(
                        help_text='The device that was used to take the measurement',
                        max_length=255,
                        verbose_name='Device',
                    ),
                ),
                (
                    'source',
                    models.CharField(
                        choices=[('P', 'Patient'), ('C', 'Clinician')],
                        help_text='The source that provided this sample, for example, the patient if it is patient-reported data',
                        max_length=1,
                        verbose_name='Source',
                    ),
                ),
                ('added_at', models.DateTimeField(auto_now_add=True, verbose_name='Added At')),
                (
                    'value',
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=7,
                        validators=[django.core.validators.MinValueValidator(Decimal(0))],
                        verbose_name='Value',
                    ),
                ),
                (
                    'type',
                    models.CharField(
                        choices=[
                            ('BM', 'Body Mass (kg)'),
                            ('TMP', 'Body Temperature (°C)'),
                            ('HR', 'Heart Rate (bpm)'),
                            ('HRV', 'Heart Rate Variability (ms)'),
                            ('SPO2', 'Oxygen Saturation (%)'),
                        ],
                        max_length=4,
                        verbose_name='Type',
                    ),
                ),
                (
                    'patient',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='quantity_samples',
                        to='patients.patient',
                        verbose_name='Patient',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Quantity Sample',
                'verbose_name_plural': 'Quantity Samples',
                'ordering': ('-start_date',),
                'abstract': False,
            },
        ),
        migrations.AddConstraint(
            model_name='quantitysample',
            constraint=models.CheckConstraint(
                condition=models.Q(('source__in', ['P', 'C'])), name='health_data_quantitysample_source_valid'
            ),
        ),
        migrations.AddConstraint(
            model_name='quantitysample',
            constraint=models.CheckConstraint(
                condition=models.Q(('type__in', ['BM', 'TMP', 'HR', 'HRV', 'SPO2'])),
                name='health_data_quantitysample_type_valid',
            ),
        ),
    ]
