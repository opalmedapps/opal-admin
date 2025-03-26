# Generated by Django 3.2.13 on 2022-05-19 14:44

from django.db import migrations, models


class Migration(migrations.Migration):
    """Remove the attribute blank from first_name and last_name for patient model."""

    dependencies = [
        ('patients', '0003_update_date_of_birth_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='first_name',
            field=models.CharField(max_length=150, verbose_name='First Name'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='last_name',
            field=models.CharField(max_length=150, verbose_name='Last Name'),
        ),
    ]
