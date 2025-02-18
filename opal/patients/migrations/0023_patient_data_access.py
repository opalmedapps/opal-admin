# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 4.1.7 on 2023-05-30 19:19

from django.db import migrations, models


class Migration(migrations.Migration):
    """Add `data_access` to the `Patient` model to reflect the patient's desired level for data access."""

    dependencies = [
        ('patients', '0022_alter_relationship_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='data_access',
            field=models.CharField(
                choices=[('ALL', 'All'), ('NTK', 'Need To Know')],
                default='ALL',
                max_length=3,
                verbose_name='Data Access Level',
            ),
        ),
        migrations.AddConstraint(
            model_name='patient',
            constraint=models.CheckConstraint(
                check=models.Q(('data_access__in', ['ALL', 'NTK'])),
                name='patients_patient_access_level_valid',
            ),
        ),
    ]
