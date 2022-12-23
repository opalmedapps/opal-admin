# Generated by Django 3.2.16 on 2022-11-24 21:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """Questionnaire profile migration that creates a table for tracking saved questionnaires per-user."""

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('questionnaires', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionnaireProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('questionnaire_list', models.JSONField(blank=True, default=dict, verbose_name='Questionnaire List')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Questionnaire Profile',
                'verbose_name_plural': 'Questionnaire Profiles',
            },
        ),
    ]
