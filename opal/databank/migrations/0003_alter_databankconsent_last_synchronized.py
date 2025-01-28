# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 4.1.9 on 2023-07-07 13:18

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add default value for databank patient's last_synchronized 1970-01-01."""

    dependencies = [
        ('databank', '0002_shared_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='databankconsent',
            name='last_synchronized',
            field=models.DateTimeField(default=datetime.datetime(1970, 1, 1, 5, 0, tzinfo=datetime.UTC), verbose_name='Last Synchronized'),
        ),
    ]
