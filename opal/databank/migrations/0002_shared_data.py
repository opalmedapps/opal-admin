# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 4.1.7 on 2023-04-26 16:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add SharedData & DataType models for databank app."""

    dependencies = [('databank', '0001_initial')]

    operations = [
        migrations.CreateModel(
            name='SharedData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sent_at', models.DateTimeField(auto_now=True, verbose_name='Sent At')),
                ('data_id', models.IntegerField(verbose_name='Data ID')),
                (
                    'data_type',
                    models.CharField(
                        choices=[
                            ('APPT', 'Appointments'),
                            ('DIAG', 'Diagnoses'),
                            ('DEMO', 'Demographics'),
                            ('LABS', 'Labs'),
                            ('QSTN', 'Questionnaires'),
                        ],
                        max_length=4,
                        verbose_name='Data Type',
                    ),
                ),
                (
                    'databank_consent',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='shared_data',
                        to='databank.databankconsent',
                        verbose_name='Databank Consent',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Shared Datum',
                'verbose_name_plural': 'Shared Data',
                'ordering': ('-sent_at',),
            },
        ),
        migrations.AddConstraint(
            model_name='shareddata',
            constraint=models.CheckConstraint(
                check=models.Q(
                    ('data_type__in', ['APPT', 'DIAG', 'DEMO', 'LABS', 'QSTN']),
                ),
                name='databank_shareddata_data_type_valid',
            ),
        ),
    ]
