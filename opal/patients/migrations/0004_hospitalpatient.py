# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 3.2.13 on 2022-06-10 14:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add HospitalPatient model."""

    dependencies = [
        ('hospital_settings', '0005_add_site_direction_url'),
        ('patients', '0003_adjust_patient_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='HospitalPatient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mrn', models.CharField(max_length=10, verbose_name='Medical Record Number')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hospital_patients', to='patients.patient', verbose_name='Patient')),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hospital_patients', to='hospital_settings.site', verbose_name='Site')),
            ],
            options={
                'verbose_name': 'Hospital Patient',
                'verbose_name_plural': 'Hospital Patients',
                'unique_together': {('site', 'mrn')},
            },
        ),
    ]
