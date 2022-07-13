# Generated by Django 3.2.14 on 2022-07-13 18:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hospital_settings', '0006_add_gps_location'),
        ('patients', '0004_hospitalpatient'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hospitalpatient',
            name='site',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hospital_site', to='hospital_settings.site', verbose_name='Site'),
        ),
    ]
