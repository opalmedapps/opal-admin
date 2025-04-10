# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 3.2.16 on 2022-10-14 05:11

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Add EmailVerification model.

    Remove field email_verification_code from model RegistrationCode
    """

    dependencies = [
        ('caregivers', '0005_device'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='registrationcode',
            name='email_verification_code',
        ),
        migrations.CreateModel(
            name='EmailVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'caregiver',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='email_verifications',
                        to='caregivers.caregiverprofile',
                        verbose_name='Caregiver Profile',
                    ),
                ),
                (
                    'code',
                    models.CharField(
                        max_length=6,
                        validators=[django.core.validators.MinLengthValidator(6)],
                        verbose_name='Verification Code',
                    ),
                ),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('is_verified', models.BooleanField(default=False, verbose_name='Verified')),
                ('sent_at', models.DateTimeField(null=True)),
            ],
            options={
                'verbose_name': 'Email Verification',
                'verbose_name_plural': 'Email Verifications',
            },
        ),
    ]
