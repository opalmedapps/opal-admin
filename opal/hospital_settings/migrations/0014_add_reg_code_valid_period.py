# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 4.1.11 on 2023-10-05 17:36

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add `registration_code_valid_period` field to the `Institution` model."""

    dependencies = [
        ('hospital_settings', '0013_add_address_fields_for_site'),
    ]

    operations = [
        migrations.AddField(
            model_name='institution',
            name='registration_code_valid_period',
            field=models.PositiveIntegerField(default=72, help_text='Valid period of a registration code generated by the QR code generator.', validators=[django.core.validators.MinValueValidator(0)], verbose_name='Registration Code Valid Period'),
        ),
    ]
