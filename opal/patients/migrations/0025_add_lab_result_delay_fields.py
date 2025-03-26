# Generated by Django 4.1.11 on 2023-10-20 18:20

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add `interpretable_lab_result_delay` and `non_interpretable_lab_result_delay` fields to the `Patient` model."""

    dependencies = [
        ('patients', '0024_patient_non_unique_ramq'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='interpretable_lab_result_delay',
            field=models.PositiveIntegerField(default=0, help_text='Lab result delay for pediatric patients when clinician interpretation is not specified in lab setting.', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(99)], verbose_name='Interpretable Lab Result Delay'),
        ),
        migrations.AddField(
            model_name='patient',
            name='non_interpretable_lab_result_delay',
            field=models.PositiveIntegerField(default=0, help_text='Lab result delay for pediatric patients when clinician interpretation is recommended in lab setting.', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(99)], verbose_name='Non-Interpretable Lab Result Delay'),
        ),
    ]
