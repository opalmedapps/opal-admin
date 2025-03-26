# Generated by Django 4.2.11 on 2024-04-17 17:10

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    """
    Initial migration for the usage statistics app.

    Creates the `DailyUserAppActivity` and `DailyPatientDataReceived` models.
    This can be further extended in the future.
    """

    initial = True

    dependencies = [
        ('patients', '0025_add_lab_result_delay_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyUserAppActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_login', models.DateTimeField(null=True, verbose_name='Last Login')),
                ('count_logins', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Count Logins')),
                ('count_checkins', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Count Checkins')),
                ('count_documents', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Count Documents')),
                ('count_educational_materials', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Count Educational Materials')),
                ('count_feedback', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Count Feedbacks')),
                ('count_questionnaires_complete', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Count Questionnaires')),
                ('count_labs', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Count Labs')),
                ('count_update_security_answers', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Count Security Answer Updates')),
                ('count_update_passwords', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Count Password Updates')),
                ('count_update_language', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Count Language Updates')),
                ('count_device_ios', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='IOS Devices')),
                ('count_device_android', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Android Devices')),
                ('count_device_browser', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Browser Devices')),
                ('date_added', models.DateField(default=django.utils.timezone.now, verbose_name='Date Added')),
                ('action_by_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_app_activities', to=settings.AUTH_USER_MODEL, verbose_name='User who triggered this action')),
                ('patient', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='patients.patient', verbose_name='Patient')),
                ('user_relationship_to_patient', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='daily_app_activities', to='patients.relationship', verbose_name='Relationship between user and patient')),
            ],
            options={
                'verbose_name': 'User App Activity',
                'verbose_name_plural': 'User App Activities',
                'indexes': [models.Index(fields=['date_added'], name='usage_stati_date_ad_ed9ba6_idx')],
            },
        ),
        migrations.CreateModel(
            name='DailyPatientDataReceived',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('next_appointment', models.DateTimeField(null=True, verbose_name='Next Appointment')),
                ('last_appointment_received', models.DateTimeField(null=True, verbose_name='Last Appointment Received')),
                ('appointments_received', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Appointments Received')),
                ('last_document_received', models.DateTimeField(null=True, verbose_name='Last Document Received')),
                ('documents_received', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Documents Received')),
                ('last_educational_material_received', models.DateTimeField(null=True, verbose_name='Last Educational Material Received')),
                ('educational_materials_received', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Educational Materials Received')),
                ('last_questionnaire_received', models.DateTimeField(null=True, verbose_name='Last Questionnaire Received')),
                ('questionnaires_received', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Questionnaires Received')),
                ('last_lab_received', models.DateTimeField(null=True, verbose_name='Last Lab Received')),
                ('labs_received', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Labs Received')),
                ('date_added', models.DateField(default=django.utils.timezone.now, verbose_name='Date Added')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_data_received', to='patients.patient', verbose_name='Patient')),
            ],
            options={
                'verbose_name': 'Patient Data Received',
                'verbose_name_plural': 'Patient Data Received Records',
                'indexes': [models.Index(fields=['date_added'], name='usage_stati_date_ad_9d6318_idx')],
            },
        ),
    ]
