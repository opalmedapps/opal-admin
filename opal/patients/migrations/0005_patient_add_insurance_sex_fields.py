# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 4.0.6 on 2022-07-13 15:22

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Add `health_insurance_number` and `sex` to `Patient` model.

    The one-off defaults are `UNDEFINED` and `U` (for unknown).
    """

    dependencies = [
        ('patients', '0004_hospitalpatient'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='health_insurance_number',
            field=models.CharField(
                blank=True, null=True, max_length=12, unique=True, verbose_name='Health Insurance Number'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='patient',
            name='sex',
            field=models.CharField(
                choices=[('F', 'Female'), ('M', 'Male'), ('O', 'Other'), ('U', 'Unknown')],
                default='U',
                max_length=1,
                verbose_name='Sex',
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='patient',
            name='date_of_birth',
            field=models.DateField(verbose_name='Date of Birth'),
        ),
        migrations.AddConstraint(
            model_name='patient',
            constraint=models.CheckConstraint(
                check=models.Q(('sex__in', ['F', 'M', 'O', 'U'])), name='patients_patient_sex_valid'
            ),
        ),
    ]
