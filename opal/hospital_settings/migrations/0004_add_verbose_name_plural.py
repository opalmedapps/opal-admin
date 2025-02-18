# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 3.2.12 on 2022-03-08 21:32

from django.db import migrations


class Migration(migrations.Migration):
    """Add a human-readable name for the `Institution` and `Site` models."""

    dependencies = [
        ('hospital_settings', '0003_add_ordering_and_unique_codes'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='institution',
            options={'ordering': ['name'], 'verbose_name': 'Institution', 'verbose_name_plural': 'Institutions'},
        ),
        migrations.AlterModelOptions(
            name='site',
            options={'ordering': ['name'], 'verbose_name': 'Site', 'verbose_name_plural': 'Sites'},
        ),
    ]
