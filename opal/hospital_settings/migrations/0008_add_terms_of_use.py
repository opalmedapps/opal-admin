# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 3.2.14 on 2022-08-18 19:00

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    """Update `Institution` model: add terms of use file (PDF) field."""

    dependencies = [
        ('hospital_settings', '0007_add_institution_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='institution',
            name='terms_of_use_en',
            field=models.FileField(
                null=True,
                upload_to='uploads/%Y/%m/%d/',
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf'])],
                verbose_name='Terms of use',
            ),
        ),
        migrations.AddField(
            model_name='institution',
            name='terms_of_use_fr',
            field=models.FileField(
                null=True,
                upload_to='uploads/%Y/%m/%d/',
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf'])],
                verbose_name='Terms of use',
            ),
        ),
        migrations.AddField(
            model_name='institution',
            name='terms_of_use',
            field=models.FileField(
                default=None,
                upload_to='uploads/%Y/%m/%d/',
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf'])],
                verbose_name='Terms of use',
            ),
            preserve_default=False,
        ),
    ]
