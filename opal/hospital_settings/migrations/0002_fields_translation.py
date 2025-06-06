# SPDX-FileCopyrightText: Copyright (C) 2021 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Generated by Django 3.2.10 on 2021-12-22 16:04

from django.db import migrations, models


class Migration(migrations.Migration):
    """Make Institution and Site multilingual."""

    dependencies = [
        ('hospital_settings', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='institution',
            name='name_en',
            field=models.CharField(max_length=100, null=True, verbose_name='Name'),
        ),
        migrations.AddField(
            model_name='institution',
            name='name_fr',
            field=models.CharField(max_length=100, null=True, verbose_name='Name'),
        ),
        migrations.AddField(
            model_name='institution',
            name='parking_url_en',
            field=models.URLField(null=True, verbose_name='Parking Info'),
        ),
        migrations.AddField(
            model_name='institution',
            name='parking_url_fr',
            field=models.URLField(null=True, verbose_name='Parking Info'),
        ),
        migrations.AddField(
            model_name='site',
            name='name_en',
            field=models.CharField(max_length=100, null=True, verbose_name='Name'),
        ),
        migrations.AddField(
            model_name='site',
            name='name_fr',
            field=models.CharField(max_length=100, null=True, verbose_name='Name'),
        ),
        migrations.AddField(
            model_name='site',
            name='parking_url_en',
            field=models.URLField(null=True, verbose_name='Parking Info (URL)'),
        ),
        migrations.AddField(
            model_name='site',
            name='parking_url_fr',
            field=models.URLField(null=True, verbose_name='Parking Info (URL)'),
        ),
    ]
