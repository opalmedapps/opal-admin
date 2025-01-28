# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 3.2.16 on 2022-12-04 21:02

from django.db import migrations


class Migration(migrations.Migration):
    """Add `new permission` to the `Institution` model."""

    dependencies = [
        ('hospital_settings', '0009_institution_support_email'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='institution',
            options={'ordering': ['name'], 'permissions': (('can_manage_institutions', 'Can manage institutions'),), 'verbose_name': 'Institution', 'verbose_name_plural': 'Institutions'},
        ),
    ]
