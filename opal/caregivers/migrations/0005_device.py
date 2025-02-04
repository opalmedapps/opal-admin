# Generated by Django 3.2.14 on 2022-08-19 18:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add Device model."""

    dependencies = [
        ('caregivers', '0004_caregiverprofile_uuid'),
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('WEB', 'Browser'), ('IOS', 'iOS'), ('AND', 'Android')], max_length=3, verbose_name='Device Type')),
                ('device_id', models.CharField(max_length=100, verbose_name='Device ID')),
                ('is_trusted', models.BooleanField(default=False, verbose_name='Trusted Device')),
                ('caregiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devices', to='caregivers.caregiverprofile', verbose_name='Caregiver Profile')),
            ],
            options={
                'verbose_name': 'Device',
                'verbose_name_plural': 'Devices',
            },
        ),
        migrations.AddConstraint(
            model_name='device',
            constraint=models.CheckConstraint(check=models.Q(('type__in', ['WEB', 'IOS', 'AND'])), name='caregivers_device_type_valid'),
        ),
        migrations.AddConstraint(
            model_name='device',
            constraint=models.UniqueConstraint(fields=('caregiver_id', 'device_id'), name='caregivers_device_unique_caregiver_device'),
        ),
    ]
