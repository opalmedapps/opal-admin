# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 4.1.11 on 2023-09-27 21:01

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    """Change the ramq field of the `Patient` model to be non-unique and non-nullable."""

    dependencies = [
        ('patients', '0023_patient_data_access'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='ramq',
            field=models.CharField(
                blank=True,
                default='',
                max_length=12,
                validators=[
                    django.core.validators.MinLengthValidator(12),
                    django.core.validators.RegexValidator(
                        message='Enter a valid RAMQ number consisting of 4 letters followed by 8 digits',
                        regex='^[A-Z]{4}[0-9]{8}$',
                    ),
                ],
                verbose_name='RAMQ Number',
            ),
            preserve_default=False,
        ),
    ]
