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
            field=models.DateTimeField(default=datetime.datetime(1970, 1, 1, 5, 0, tzinfo=datetime.timezone.utc), verbose_name='Last Synchronized'),
        ),
    ]
