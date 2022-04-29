# Generated by Django 3.2.12 on 2022-04-13 15:30

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add a user patient relationship type model."""

    dependencies = [
        ('hospital_settings', '0005_add_site_direction_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='RelationshipType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25, verbose_name='Name')),
                ('name_en', models.CharField(max_length=25, null=True, verbose_name='Name')),
                ('name_fr', models.CharField(max_length=25, null=True, verbose_name='Name')),
                ('description', models.CharField(max_length=200, verbose_name='Description')),
                ('description_en', models.CharField(max_length=200, null=True, verbose_name='Description')),
                ('description_fr', models.CharField(max_length=200, null=True, verbose_name='Description')),
                ('start_age', models.PositiveIntegerField(help_text='Minimum age the relationship is allowed to start.', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(149)], verbose_name='Start age')),
                ('end_age', models.PositiveIntegerField(blank=True, help_text='Age at which the relationship ends automatically.', null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(150)], verbose_name='End age')),
                ('form_required', models.BooleanField(default=True, help_text='Whether the hospital form is required to be completed by the caregiver', verbose_name='Form required')),
            ],
            options={
                'verbose_name': 'Caregiver Relationship Type',
                'verbose_name_plural': 'Caregiver Relationship Types',
                'ordering': ['name'],
            },
        ),
    ]
