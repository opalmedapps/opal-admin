# Generated by Django 4.2.13 on 2024-05-24 18:25

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add `created_at` field to the `Patient` model."""

    dependencies = [
        ('patients', '0025_add_lab_result_delay_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created At'),
        ),
    ]
