# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Split Observations into separate inherited models to better suit Lab and Pathology data differences."""

    dependencies = [
        ('test_results', '0004_observation_value_text_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='LabObservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'identifier_code',
                    models.CharField(
                        help_text='Test component code.', max_length=20, verbose_name='Observation Identifier'
                    ),
                ),
                (
                    'identifier_text',
                    models.CharField(
                        help_text='Test component text.', max_length=199, verbose_name='Observation Identifier Text'
                    ),
                ),
                (
                    'observed_at',
                    models.DateTimeField(
                        help_text='When this specific observation segment was entered into the source system.',
                        verbose_name='Observed At',
                    ),
                ),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('value', models.FloatField(verbose_name='Value')),
                ('value_units', models.CharField(blank=True, max_length=20, verbose_name='Value Units')),
                ('value_min_range', models.FloatField(blank=True, null=True, verbose_name='Minimum Value Range')),
                ('value_max_range', models.FloatField(blank=True, null=True, verbose_name='Maximum Value Range')),
                (
                    'value_abnormal',
                    models.CharField(
                        choices=[('L', 'Low'), ('N', 'Normal'), ('H', 'High')],
                        default='N',
                        max_length=1,
                        verbose_name='Abnormal Flag',
                    ),
                ),
                (
                    'general_test',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='lab_observations',
                        to='test_results.generaltest',
                        verbose_name='General Test',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Lab Observation',
                'verbose_name_plural': 'Lab Observations',
            },
        ),
        migrations.CreateModel(
            name='PathologyObservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'identifier_code',
                    models.CharField(
                        help_text='Test component code.', max_length=20, verbose_name='Observation Identifier'
                    ),
                ),
                (
                    'identifier_text',
                    models.CharField(
                        help_text='Test component text.', max_length=199, verbose_name='Observation Identifier Text'
                    ),
                ),
                (
                    'observed_at',
                    models.DateTimeField(
                        help_text='When this specific observation segment was entered into the source system.',
                        verbose_name='Observed At',
                    ),
                ),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('value', models.TextField(verbose_name='Value')),
                (
                    'general_test',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='pathology_observations',
                        to='test_results.generaltest',
                        verbose_name='General Test',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Pathology Observation',
                'verbose_name_plural': 'Pathology Observations',
            },
        ),
        migrations.DeleteModel(
            name='Observation',
        ),
    ]
