# SPDX-FileCopyrightText: Copyright (C) 2026 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import model_utils.fields


class Migration(migrations.Migration):
    """Add `PatientReportedData` model to store patient-reported health data."""

    dependencies = [
        ('health_data', '0004_add_viewed_at_and_viewed_by_fields'),
        ('patients', '0026_add_patient_created_at_field'),
        ('patients', '0026_add_patient_created_at_field'),
        ('patients', '0026_add_patient_created_at_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='PatientReportedData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'created',
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name='created'
                    ),
                ),
                (
                    'modified',
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name='modified'
                    ),
                ),
                ('social_history', models.JSONField(blank=True, default=list, verbose_name='Social History')),
                (
                    'patient',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='patient_reported_data',
                        to='patients.patient',
                        verbose_name='Patient',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Patient Reported Data',
                'verbose_name_plural': 'Patient Reported Data',
            },
        ),
    ]
