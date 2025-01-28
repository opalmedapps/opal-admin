# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 4.0.3 on 2022-05-02 14:29

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """Add caregiver profile model to store extra data."""

    dependencies = [
        ('users', '0004_user_phone_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='CaregiverProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('legacy_id', models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Legacy ID')),
                ('user', models.OneToOneField(limit_choices_to={'type': 'CAREGIVER'}, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Caregiver Profile',
                'verbose_name_plural': 'Caregiver Profiles',
            },
        ),
    ]
