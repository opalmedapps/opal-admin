# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 3.2.13 on 2022-07-12 01:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add SecurityQuestion and SecurityAnswer models."""

    dependencies = [
        ('caregivers', '0002_registrationcode'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecurityQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='Title')),
                ('title_en', models.CharField(max_length=100, null=True, verbose_name='Title')),
                ('title_fr', models.CharField(max_length=100, null=True, verbose_name='Title')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
            ],
            options={
                'verbose_name': 'Security Question',
                'verbose_name_plural': 'Security Questions',
            },
        ),
        migrations.CreateModel(
            name='SecurityAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='security_answers',
                        to='caregivers.caregiverprofile',
                        verbose_name='Caregiver Profile',
                    ),
                ),
                ('question', models.CharField(max_length=100, verbose_name='Question')),
                ('answer', models.CharField(max_length=128, verbose_name='Answer')),
            ],
            options={
                'verbose_name': 'Security Answer',
                'verbose_name_plural': 'Security Answers',
            },
        ),
    ]
