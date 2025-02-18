# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 4.1.10 on 2023-08-20 19:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Use plural form for the `general_tests`, `observations` and `notes` related fields.

    Since the `GeneralTest` -> `Patient` has many-to-one relationship, the field's name should be in plural form.

    The same applies for the `Observation` -> `GeneralTest` and `Note` -> `GeneralTest`.

    The requests will have the following form:

    ```python
    Patient.objects.first().general_tests.all()
    GeneralTest.objects.first().observations.all()
    GeneralTest.objects.first().notes.all()
    ```
    """

    dependencies = [
        ('patients', '0023_patient_data_access'),
        ('test_results', '0002_add_reported_at_case_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generaltest',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='general_tests', to='patients.patient', verbose_name='Patient'),
        ),
        migrations.AlterField(
            model_name='note',
            name='general_test',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='test_results.generaltest', verbose_name='General Test'),
        ),
        migrations.AlterField(
            model_name='observation',
            name='general_test',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='observations', to='test_results.generaltest', verbose_name='General Test'),
        ),
    ]
