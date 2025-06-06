# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 4.1.12 on 2023-10-19 20:32

from django.db import migrations, models


class Migration(migrations.Migration):
    """Add viewed_at and viewed_by fields to indicate if a specific `QuantitySample` has been viewed in the ORMS."""

    dependencies = [
        ('health_data', '0003_add_blood_pressure_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='quantitysample',
            name='viewed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Viewed At'),
        ),
        migrations.AddField(
            model_name='quantitysample',
            name='viewed_by',
            field=models.CharField(blank=True, max_length=150, verbose_name='Viewed By'),
        ),
    ]
