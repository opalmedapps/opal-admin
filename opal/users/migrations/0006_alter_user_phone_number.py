# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.db import migrations

import phonenumber_field.modelfields


class Migration(migrations.Migration):
    """Change phone number field to use `PhoneNumberField`."""

    dependencies = [
        ('users', '0005_user_language_settings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True,
                max_length=128,
                region=None,
                verbose_name='Phone Number',
            ),
        ),
    ]
