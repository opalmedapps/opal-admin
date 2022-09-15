# Generated by Django 3.2.14 on 2022-09-05 22:43

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    """Rename field health insurance number to ramq."""

    dependencies = [
        ('patients', '0006_relationship_reason'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patient',
            name='health_insurance_number',
        ),
        migrations.AddField(
            model_name='patient',
            name='ramq',
            field=models.CharField(blank=True, max_length=12, null=True, unique=True, validators=[django.core.validators.MinLengthValidator(12), django.core.validators.RegexValidator(message='Enter a valid RAMQ number consisting of 4 letters followed by 8 digits', regex='^[A-Z]{4}[0-9]{8}$')], verbose_name='RAMQ Number'),
        ),
    ]
