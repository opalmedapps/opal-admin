# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 3.2.13 on 2022-06-15 17:01

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add registration code model."""

    dependencies = [
        ('patients', '0004_hospitalpatient'),
        ('caregivers', '0001_caregiverprofile'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistrationCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'relationship',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='registration_codes',
                        to='patients.relationship',
                        verbose_name='Relationship',
                    ),
                ),
                (
                    'code',
                    models.CharField(
                        max_length=12,
                        unique=True,
                        validators=[django.core.validators.MinLengthValidator(12)],
                        verbose_name='Code',
                    ),
                ),
                (
                    'status',
                    models.CharField(
                        choices=[('NEW', 'New'), ('REG', 'Registered'), ('EXP', 'Expired'), ('BLK', 'Blocked')],
                        default='NEW',
                        max_length=3,
                        verbose_name='Status',
                    ),
                ),
                ('attempts', models.PositiveIntegerField(default=0, verbose_name='Attempts')),
                (
                    'email_verification_code',
                    models.CharField(
                        max_length=6,
                        validators=[django.core.validators.MinLengthValidator(6)],
                        verbose_name='Email Verification Code',
                    ),
                ),
                ('creation_date', models.DateField(auto_now_add=True, verbose_name='Creation Date')),
            ],
            options={
                'verbose_name': 'Registration Code',
                'verbose_name_plural': 'Registration Codes',
            },
        ),
        migrations.AddConstraint(
            model_name='registrationcode',
            constraint=models.CheckConstraint(
                check=models.Q(('status__in', ['NEW', 'REG', 'EXP', 'BLK'])),
                name='caregivers_registrationcode_status_valid',
            ),
        ),
    ]
