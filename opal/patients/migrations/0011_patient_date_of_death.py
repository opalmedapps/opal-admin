# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 3.2.16 on 2022-12-01 20:51

import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add `date_of_death` field to Patient model."""

    dependencies = [
        ('patients', '0010_can_answer_questionnaire'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='date_of_death',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Date and Time of Death'),
        ),
        migrations.AddConstraint(
            model_name='patient',
            constraint=models.CheckConstraint(
                check=models.Q(('date_of_birth__lte', django.db.models.expressions.F('date_of_death'))),
                name='patients_patient_date_valid',
            ),
        ),
    ]
