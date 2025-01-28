# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 3.2.13 on 2022-05-17 20:08

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.expressions


class Migration(migrations.Migration):
    """Adds the patient and relationship models."""

    dependencies = [
        ('caregivers', '0001_caregiverprofile'),
        ('patients', '0001_relationshiptype'),
    ]

    operations = [
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='First Name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='Last Name')),
                ('day_of_birth', models.DateField()),
                ('legacy_id', models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Legacy ID')),
            ],
            options={
                'verbose_name': 'Patient',
                'verbose_name_plural': 'Patients',
            },
        ),
        migrations.CreateModel(
            name='Relationship',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PEN', 'Pending'), ('CON', 'Confirmed'), ('DEN', 'Denied'), ('EXP', 'Expired'), ('REV', 'Revoked')], default='PEN', max_length=3, verbose_name='Relationship Status')),
                ('request_date', models.DateField(verbose_name='Relationship Request Date')),
                ('start_date', models.DateField(verbose_name='Relationship Start Date')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='Relationship End Date')),
                ('caregiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relationships', to='caregivers.caregiverprofile', verbose_name='Caregiver')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relationships', to='patients.patient', verbose_name='Patient')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relationship', to='patients.relationshiptype', verbose_name='Relationship Type')),
            ],
            options={
                'verbose_name': 'Relationship',
                'verbose_name_plural': 'Relationships',
            },
        ),
        migrations.AddField(
            model_name='patient',
            name='caregivers',
            field=models.ManyToManyField(related_name='patients', through='patients.Relationship', to='caregivers.CaregiverProfile', verbose_name='Caregivers'),
        ),
        migrations.AddConstraint(
            model_name='relationship',
            constraint=models.CheckConstraint(check=models.Q(('status__in', ['PEN', 'CON', 'DEN', 'EXP', 'REV'])), name='patients_relationship_status_valid'),
        ),
        migrations.AddConstraint(
            model_name='relationship',
            constraint=models.CheckConstraint(check=models.Q(('start_date__lt', django.db.models.expressions.F('end_date'))), name='patients_relationship_date_valid'),
        ),
    ]
