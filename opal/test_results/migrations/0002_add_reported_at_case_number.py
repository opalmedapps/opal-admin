# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add two missing fields based on mockup: case_number (Report identifier) and reported_at (Additional timestamp)."""

    dependencies = [
        ('test_results', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='generaltest',
            name='case_number',
            field=models.CharField(
                blank=True, help_text='HL7 Filler Field 1 identifier', max_length=60, verbose_name='Case Number'
            ),
        ),
        migrations.AddField(
            model_name='generaltest',
            name='reported_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Reported At'),
            preserve_default=False,
        ),
        # Fix spelling of 'Abnormal Flag'
        migrations.AlterField(
            model_name='observation',
            name='value_abnormal',
            field=models.CharField(
                choices=[('L', 'Low'), ('N', 'Normal'), ('H', 'High')],
                default='N',
                max_length=1,
                verbose_name='Abnormal Flag',
            ),
        ),
    ]
